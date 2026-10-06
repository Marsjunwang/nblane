"""Install, connect and relocate a local OpenClaw from the Settings page.

nblane does not embed OpenClaw; it drives the public ``openclaw`` CLI
(``--json`` where available) the same way ``commands/openclaw.py`` does, so a
replaced or upgraded agent never breaks nblane's own data. Three jobs run in
a background thread of the single-worker SPA backend and are polled by the
UI:

- ``install`` — ``npm install -g openclaw@<pinned>`` (user prefix, no sudo),
  then ``openclaw onboard --non-interactive`` with the workspace placed under
  the agent data root and, optionally, nblane's own AI connection as the
  model (the key reaches onboarding through ``CUSTOM_API_KEY`` in the child
  environment, never on the command line), then ``connect``.
- ``connect`` — idempotent wiring for an existing install: workspace git
  repo, repo skills + their ``nblane_api`` runner, the nblane MCP server, the read-only
  profile corpus under ``memory/nblane/``. Model routing is never touched.
- ``migrate`` — move the workspace into the agent data root
  (``/srv/agent-data/openclaw/workspace``): tar the whole state dir first,
  stop the gateway, move, leave a symlink at the old path, repoint the
  config, start the gateway; any failure after the move rolls back.

``NBLANE_OPENCLAW_PROFILE`` selects an isolated OpenClaw profile
(``~/.openclaw-<name>``, its own gateway unit and port) so the isolated dev
stack can exercise every job without touching the production gateway.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nblane.core import paths

PINNED_VERSION = "2026.9.4"
DEFAULT_GATEWAY_PORT = 18789
WEIXIN_PLUGIN_SPEC = "@tencent-weixin/openclaw-weixin"
CUSTOM_PROVIDER_ID = "nblane"
JOB_KINDS = ("install", "connect", "migrate", "weixin")
_MAX_LOG = 300

def _repo_scripts() -> Path:
    """``scripts/openclaw`` of the installed code checkout.

    ``paths.REPO_ROOT`` follows ``NBLANE_ROOT`` (the *data* root in
    production), so resolve from this file first (src layout).
    """

    code_root = Path(__file__).resolve().parents[3]
    for root in (code_root, paths.REPO_ROOT):
        candidate = root / "scripts" / "openclaw"
        if (candidate / "skills").is_dir():
            return candidate
    return code_root / "scripts" / "openclaw"


REPO_SCRIPTS = _repo_scripts()


class OpenClawSetupError(RuntimeError):
    """User-facing failure (shown verbatim in Settings)."""


# --------------------------------------------------------------- locations


def _clean_env(name: str) -> str:
    return str(os.getenv(name, "") or "").strip()


def profile_name() -> str:
    value = _clean_env("NBLANE_OPENCLAW_PROFILE")
    return "".join(ch for ch in value if ch.isalnum() or ch in "-_")


def cli_prefix() -> list[str]:
    name = profile_name()
    return ["openclaw", "--profile", name] if name else ["openclaw"]


def state_dir() -> Path:
    name = profile_name()
    return Path.home() / (f".openclaw-{name}" if name else ".openclaw")


def config_path() -> Path:
    override = _clean_env("OPENCLAW_CONFIG_PATH")
    return Path(override).expanduser() if override and not profile_name() else state_dir() / "openclaw.json"


def gateway_port() -> int:
    raw = _clean_env("NBLANE_OPENCLAW_GATEWAY_PORT")
    try:
        return int(raw) if raw else DEFAULT_GATEWAY_PORT
    except ValueError:
        return DEFAULT_GATEWAY_PORT


def gateway_unit() -> str:
    name = profile_name()
    return f"openclaw-gateway-{name}.service" if name else "openclaw-gateway.service"


def agent_data_root() -> Path:
    """Root that holds agent workspaces (``/srv/agent-data`` in production)."""

    value = _clean_env("NBLANE_AGENT_DATA_ROOT")
    if value:
        return Path(value).expanduser()
    srv = Path("/srv/agent-data")
    if srv.is_dir() and os.access(srv, os.W_OK):
        return srv
    return Path.home() / ".local" / "share" / "nblane" / "agent-data"


def target_workspace() -> Path:
    return agent_data_root() / "openclaw" / "workspace"


def _setup_state_path() -> Path:
    from nblane.core.backup_targets import state_dir as backup_state_dir

    suffix = f"-{profile_name()}" if profile_name() else ""
    return backup_state_dir() / f"openclaw{suffix}.json"


def pinned_version() -> str:
    return _clean_env("NBLANE_OPENCLAW_VERSION") or PINNED_VERSION


# ------------------------------------------------------------- subprocess


def _child_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    uid = os.getuid()
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{uid}")
    env.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path=/run/user/{uid}/bus")
    env["NO_COLOR"] = "1"
    if extra:
        env.update(extra)
    return env


def _run(
    args: list[str],
    *,
    timeout: float = 60.0,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run one command (argv list, no shell). Tests patch this function."""

    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_child_env(env),
            cwd=str(cwd) if cwd else None,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError as exc:
        raise OpenClawSetupError(f"找不到命令 {args[0]}。") from exc
    except subprocess.TimeoutExpired as exc:
        raise OpenClawSetupError(f"{' '.join(args[:4])} 执行超时。") from exc


def _openclaw(*args: str, timeout: float = 60.0, env: dict[str, str] | None = None):
    return _run([*cli_prefix(), *args], timeout=timeout, env=env)


def _tail(result: subprocess.CompletedProcess[str], lines: int = 1) -> str:
    text = [line for line in (result.stderr or "").splitlines() + (result.stdout or "").splitlines() if line.strip()]
    return " / ".join(text[-lines:])[:400] if text else f"exit {result.returncode}"


def _check(result: subprocess.CompletedProcess[str], what: str) -> subprocess.CompletedProcess[str]:
    if result.returncode != 0:
        raise OpenClawSetupError(f"{what}失败：{_tail(result, 2)}")
    return result


# ---------------------------------------------------------------- config


def read_config() -> dict[str, Any] | None:
    """Parse the OpenClaw config file (JSON) without spawning the CLI."""

    path = config_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _workspace_from_config(config: dict[str, Any]) -> Path | None:
    agents = config.get("agents") if isinstance(config.get("agents"), dict) else {}
    entries = agents.get("entries") if isinstance(agents.get("entries"), dict) else {}
    main = entries.get("main") if isinstance(entries.get("main"), dict) else {}
    defaults = agents.get("defaults") if isinstance(agents.get("defaults"), dict) else {}
    raw = main.get("workspace") or defaults.get("workspace")
    return Path(str(raw)).expanduser() if raw else None


def workspace_path() -> Path | None:
    """The main agent's workspace, or None when OpenClaw is not set up."""

    config = read_config()
    if config is not None:
        found = _workspace_from_config(config)
        if found is not None:
            return found
        default = state_dir() / "workspace"
        return default if default.exists() else None
    if not config_path().exists():
        return None
    # Non-JSON (JSON5) config: ask the CLI.
    try:
        result = _openclaw("config", "get", "agents.defaults.workspace", "--json", timeout=20)
        if result.returncode == 0:
            return Path(json.loads(result.stdout)).expanduser()
    except (OpenClawSetupError, ValueError, TypeError):
        pass
    return None


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _mcp_entry(config: dict[str, Any] | None) -> dict[str, Any] | None:
    if not config:
        return None
    servers = ((config.get("mcp") or {}).get("servers") or {}) if isinstance(config.get("mcp"), dict) else {}
    entry = servers.get("nblane")
    return entry if isinstance(entry, dict) else None


def _plugin_enabled(config: dict[str, Any] | None, plugin_id: str) -> bool:
    entries = (((config or {}).get("plugins") or {}).get("entries") or {})
    entry = entries.get(plugin_id) if isinstance(entries, dict) else None
    return isinstance(entry, dict) and entry.get("enabled", True) is not False


# ---------------------------------------------------------------- status


def _version() -> str:
    if shutil.which("openclaw") is None:
        return ""
    try:
        result = _run(["openclaw", "--version"], timeout=10)
    except OpenClawSetupError:
        return ""
    text = result.stdout.strip()
    return text.split()[1] if result.returncode == 0 and len(text.split()) > 1 else text


def _node_version() -> str:
    if shutil.which("node") is None:
        return ""
    try:
        result = _run(["node", "--version"], timeout=10)
    except OpenClawSetupError:
        return ""
    return result.stdout.strip().lstrip("v") if result.returncode == 0 else ""


def node_supported(version: str) -> bool:
    try:
        parts = tuple(int(x) for x in version.split(".")[:3])
    except ValueError:
        return False
    return (parts[0] == 24 and parts >= (24, 16, 0)) or parts >= (26, 1, 0)


def _port_open(port: int) -> bool:
    with contextlib.suppress(OSError), socket.create_connection(("127.0.0.1", port), timeout=1.0):
        return True
    return False


def _service_active() -> str:
    if shutil.which("systemctl") is None:
        return ""
    try:
        result = _run(["systemctl", "--user", "is-active", gateway_unit()], timeout=10)
    except OpenClawSetupError:
        return ""
    return result.stdout.strip()


def _load_setup_state() -> dict[str, Any]:
    try:
        data = json.loads(_setup_state_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_setup_state(**fields: Any) -> None:
    data = _load_setup_state()
    data.update(fields)
    path = _setup_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def connected_profile() -> str:
    return str(_load_setup_state().get("profile") or "")


def status() -> dict[str, Any]:
    """Display-ready snapshot for the Settings「个人 Agent」card."""

    version = _version()
    node = _node_version()
    config = read_config()
    configured = config_path().exists()
    workspace = workspace_path() if configured else None
    mcp = _mcp_entry(config)
    corpus_dir = workspace / "memory" / "nblane" if workspace else None
    port = gateway_port()
    from nblane.core import llm as llm_client

    llm = llm_client.current_config(mask_key=True)
    return {
        "installed": bool(version),
        "version": version,
        "pinned_version": pinned_version(),
        "npm_available": shutil.which("npm") is not None,
        "node_version": node,
        "node_supported": node_supported(node) if node else False,
        "profile": profile_name(),
        "state_dir": str(state_dir()),
        "configured": configured,
        "workspace": str(workspace) if workspace else "",
        "workspace_exists": bool(workspace and workspace.is_dir()),
        "workspace_in_agent_root": bool(workspace and _is_within(workspace, agent_data_root())),
        "agent_data_root": str(agent_data_root()),
        "target_workspace": str(target_workspace()),
        "gateway_port": port,
        "gateway_unit": gateway_unit(),
        "gateway_service": _service_active(),
        "gateway_reachable": _port_open(port),
        "mcp_registered": mcp is not None,
        "mcp_profile": str((mcp or {}).get("env", {}).get("NBLANE_PROFILE") or ""),
        "connected_profile": connected_profile(),
        "foreign_root": foreign_root(),
        "corpus_present": bool(corpus_dir and corpus_dir.is_dir() and any(corpus_dir.glob("*.md"))),
        "weixin_installed": _plugin_enabled(config, "openclaw-weixin"),
        "weixin_login_command": " ".join([*cli_prefix(), "channels", "login", "--channel", "openclaw-weixin"]),
        "llm_reusable": bool(llm.get("configured") and llm.get("base_url") and llm.get("model")),
        "llm_model": str(llm.get("model") or ""),
        "llm_base_url": str(llm.get("base_url") or ""),
        "mcp_entry": build_mcp_entry(connected_profile() or None),
        "job": job_state(),
    }


# -------------------------------------------------------------------- jobs

_JOB: dict[str, Any] = {}
_JOB_LOCK = threading.RLock()


def job_state() -> dict[str, Any]:
    with _JOB_LOCK:
        data = dict(_JOB)
        data["log"] = list(_JOB.get("log") or [])
        return data


def _log(line: str) -> None:
    with _JOB_LOCK:
        log = _JOB.setdefault("log", [])
        for part in str(line).splitlines() or [""]:
            log.append(part[:500])
        del log[:-_MAX_LOG]


def _phase(phase: str, message: str) -> None:
    with _JOB_LOCK:
        _JOB["phase"] = phase
    _log(f"▶ {message}")


def start_job(kind: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Start one background job; only one may run at a time."""

    if kind not in JOB_KINDS:
        raise OpenClawSetupError("未知的操作。")
    options = dict(options or {})
    blocker = job_blocker(kind, options)
    if blocker:
        raise OpenClawSetupError(blocker)
    with _JOB_LOCK:
        if _JOB.get("status") == "running":
            raise OpenClawSetupError("已有任务在运行，请等它完成。")
        _JOB.clear()
        _JOB.update(kind=kind, status="running", phase="", error="", log=[], started_at=time.time(), finished_at=0)
    thread = threading.Thread(target=_run_job, args=(kind, options), name=f"openclaw-{kind}", daemon=True)
    thread.start()
    return job_state()


def foreign_root() -> str:
    """NBLANE_ROOT of another deployment this OpenClaw is wired to, else "".

    Guards against a dev stack (``NBLANE_ROOT=.dev-data``) reconfiguring or
    restarting the production gateway when the isolation env is missing.
    """

    entry = _mcp_entry(read_config())
    other = str(((entry or {}).get("env") or {}).get("NBLANE_ROOT") or "")
    if not other:
        return ""
    try:
        same = Path(other).expanduser().resolve() == Path(paths.REPO_ROOT).resolve()
    except OSError:
        same = False
    return "" if same else other


def _foreign_message(other: str) -> str:
    return (
        f"这个 OpenClaw 已接入另一个 nblane 数据目录（{other}），这里不能修改它。"
        "开发环境请用 scripts/dev-web.sh --isolated 启动（独立 OpenClaw profile）。"
    )


def job_blocker(kind: str, options: dict[str, Any]) -> str:
    installed = shutil.which("openclaw") is not None
    if kind != "install" and (other := foreign_root()):
        return _foreign_message(other)
    if kind == "install":
        if installed and config_path().exists():
            return "本机已安装并配置 OpenClaw，请用「接入 nblane」。"
        if not installed and shutil.which("npm") is None:
            return "服务器没有 npm，无法安装 OpenClaw。"
        node = _node_version()
        if not node_supported(node):
            return f"OpenClaw 需要 Node 24.16+ 或 26.1+，当前为 {node or '未安装'}。"
        if target_workspace().exists() and any(target_workspace().iterdir()):
            return f"目标工作区 {target_workspace()} 已存在且非空。"
    elif not installed or not config_path().exists():
        return "本机还没有可用的 OpenClaw。"
    if kind in {"install", "connect"}:
        profile = str(options.get("profile") or "")
        from nblane.core.profile_io import list_profiles

        if profile not in list_profiles():
            return "请选择要接入的档案。"
    if kind == "migrate":
        workspace = workspace_path()
        if workspace is None or not workspace.is_dir():
            return "找不到当前工作区。"
        if _is_within(workspace, agent_data_root()):
            return "工作区已经在统一数据目录下。"
        if target_workspace().exists():
            return f"目标位置 {target_workspace()} 已存在，请先处理。"
    return ""


def _run_job(kind: str, options: dict[str, Any]) -> None:
    try:
        if kind == "install":
            _do_install(options)
        elif kind == "connect":
            _do_connect(str(options["profile"]))
        elif kind == "migrate":
            _do_migrate()
        elif kind == "weixin":
            _do_weixin()
        with _JOB_LOCK:
            _JOB.update(status="done", phase="done", finished_at=time.time())
        _log("✔ 完成")
    except Exception as exc:  # surfaced to the admin UI
        message = str(exc) if isinstance(exc, OpenClawSetupError) else f"意外错误：{exc}"
        _log(f"✘ {message}")
        with _JOB_LOCK:
            _JOB.update(status="failed", error=message[:400], finished_at=time.time())


# ----------------------------------------------------------------- install


def _onboard_args(workspace: Path, *, reuse_llm: bool) -> tuple[list[str], dict[str, str]]:
    args = [
        "onboard", "--non-interactive", "--accept-risk", "--mode", "local",
        "--workspace", str(workspace),
        "--gateway-bind", "loopback", "--gateway-port", str(gateway_port()),
        "--install-daemon", "--daemon-runtime", "node",
        "--skip-channels", "--skip-skills", "--skip-search", "--skip-ui",
        "--suppress-gateway-token-output", "--secret-input-mode", "plaintext", "--json",
    ]
    env: dict[str, str] = {}
    if reuse_llm:
        from nblane.core import llm as llm_client

        config = llm_client.current_config(mask_key=False)
        base_url, model, key = (str(config.get(k) or "") for k in ("base_url", "model", "api_key"))
        if not (base_url and model and key):
            raise OpenClawSetupError("nblane 的 AI 连接还没配好，无法复用。")
        args += [
            "--auth-choice", "custom-api-key", "--custom-base-url", base_url,
            "--custom-model-id", model, "--custom-provider-id", CUSTOM_PROVIDER_ID,
            "--custom-compatibility", "openai",
        ]
        env["CUSTOM_API_KEY"] = key  # read from env by onboarding; never on argv
    else:
        args += ["--auth-choice", "skip"]
    return args, env


def _do_install(options: dict[str, Any]) -> None:
    if shutil.which("openclaw") is None:
        _phase("npm", f"安装 OpenClaw {pinned_version()}（npm 全局，用户目录）")
        result = _run(["npm", "install", "-g", f"openclaw@{pinned_version()}"], timeout=1800)
        _log(_tail(result, 3))
        _check(result, "npm 安装")
        if shutil.which("openclaw") is None:
            raise OpenClawSetupError("npm 安装完成但找不到 openclaw 命令：检查服务 PATH 是否包含 npm 全局 bin 目录。")
    workspace = target_workspace()
    workspace.parent.mkdir(parents=True, exist_ok=True)
    _phase("onboard", f"初始化配置与网关（工作区 {workspace}，端口 {gateway_port()}）")
    args, env = _onboard_args(workspace, reuse_llm=bool(options.get("reuse_llm")))
    result = _openclaw(*args, timeout=900, env=env)
    _log(_tail(result, 4))
    _check(result, "初始化")
    _do_connect(str(options["profile"]))


# ----------------------------------------------------------------- connect


def build_mcp_entry(profile: str | None) -> dict[str, Any]:
    from nblane.core.mcp_client_config import build_mcp_server_entry

    sibling = Path(sys.executable).parent / "nblane-mcp"
    return build_mcp_server_entry(profile, executable=str(sibling) if sibling.is_file() else None)


def _sync_repo_skills(workspace: Path) -> None:
    from nblane.commands.openclaw import _sync_skills

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        _sync_skills(REPO_SCRIPTS / "skills", workspace / "skills", check=False)
    for line in buffer.getvalue().splitlines()[-6:]:
        _log(line)


def _ensure_skills_runner(workspace: Path) -> None:
    """Write ``skills/bin/nblane_api`` running nblane's own interpreter.

    nblane already depends on httpx, so no per-workspace venv (and no index
    access) is needed; it also avoids the venv's absolute symlinks that make
    ``openclaw backup create`` fail. An existing ``skills/.venv`` is left
    alone (gitignored).
    """

    wrapper = workspace / "skills" / "bin" / "nblane_api"
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    wrapper.write_text(
        "#!/usr/bin/env bash\n"
        "# Generated by nblane connect — runs nblane_api.py with nblane's python.\n"
        'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        f'exec "{sys.executable}" "${{HERE}}/nblane_api.py" "$@"\n',
        encoding="utf-8",
    )
    wrapper.chmod(0o755)


def refresh_corpus(profile: str, workspace: Path | None = None) -> Path:
    from nblane.core.openclaw_corpus import render_profile_corpus

    workspace = workspace or workspace_path()
    if workspace is None:
        raise OpenClawSetupError("找不到 OpenClaw 工作区。")
    out_dir = workspace / "memory" / "nblane"
    render_profile_corpus(profile, out_dir=out_dir)
    return out_dir


def _ensure_extra_path(out_dir: Path) -> None:
    config = read_config() or {}
    current = (((config.get("memory") or {}).get("search") or {}).get("extraPaths") or [])
    if not isinstance(current, list):
        current = []
    resolved = {str(Path(str(item)).expanduser()) for item in current}
    if str(out_dir) in resolved:
        return
    value = json.dumps([*current, str(out_dir)], ensure_ascii=False)
    _check(_openclaw("config", "set", "memory.search.extraPaths", value, "--strict-json", timeout=60), "配置记忆检索路径")


def _do_connect(profile: str) -> None:
    from nblane.core import backup_targets

    workspace = workspace_path()
    if workspace is None or not workspace.is_dir():
        raise OpenClawSetupError("找不到 OpenClaw 工作区。")
    _phase("git", "工作区纳入 git 备份")
    created = backup_targets.ensure_repo(
        workspace, backup_targets.WORKSPACE_GITIGNORE, untrack=backup_targets.WORKSPACE_UNTRACK
    )
    _log("已初始化 git 仓库" if created else "git 仓库已就绪")
    _phase("skills", "同步 nblane 技能")
    _sync_repo_skills(workspace)
    _ensure_skills_runner(workspace)
    _phase("mcp", f"注册 nblane MCP（档案 {profile}）")
    entry = build_mcp_entry(profile)
    if _mcp_entry(read_config()) != entry:
        _check(_openclaw("mcp", "set", "nblane", json.dumps(entry, ensure_ascii=False), timeout=60), "注册 MCP")
        _log("已写入 mcp.servers.nblane")
    else:
        _log("MCP 已是最新")
    _phase("corpus", "生成只读档案语料（memory/nblane/）")
    out_dir = refresh_corpus(profile, workspace)
    _ensure_extra_path(out_dir)
    if _plugin_enabled(read_config(), "openclaw-weixin") and not _plugin_enabled(read_config(), "weixin-task-bridge"):
        _install_task_bridge()
    _save_setup_state(profile=profile, connected_at=datetime.now(timezone.utc).isoformat())


def _install_task_bridge() -> None:
    plugin = REPO_SCRIPTS / "plugins" / "weixin-task-bridge"
    if not plugin.is_dir():
        return
    _phase("plugin", "安装 weixin-task-bridge 插件")
    _check(_openclaw("plugins", "install", str(plugin), "--force", "--accept-capabilities", timeout=300), "安装插件")


def _do_weixin() -> None:
    config = read_config()
    if not _plugin_enabled(config, "openclaw-weixin"):
        _phase("weixin", f"安装微信渠道插件 {WEIXIN_PLUGIN_SPEC}（腾讯维护的第三方插件）")
        result = _openclaw("plugins", "install", WEIXIN_PLUGIN_SPEC, "--pin", "--accept-capabilities", timeout=900)
        _log(_tail(result, 3))
        _check(result, "安装微信插件")
    else:
        _log("微信渠道插件已安装")
    if not _plugin_enabled(read_config(), "weixin-task-bridge"):
        _install_task_bridge()
    _phase("restart", "重启网关以加载插件")
    _check(_openclaw("gateway", "restart", "--safe", timeout=300), "重启网关")


# ----------------------------------------------------------------- migrate


def _archive_state(dest_dir: Path) -> Path:
    """Tar the whole OpenClaw state dir (symlinks stored as links)."""

    dest_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(dest_dir, 0o700)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = dest_dir / f"{state_dir().name.lstrip('.')}-pre-migrate-{stamp}.tgz"
    workspace = workspace_path()
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(state_dir(), arcname=state_dir().name)
        if workspace and workspace.is_dir() and not _is_within(workspace, state_dir()):
            tar.add(workspace, arcname="workspace-external")
    os.chmod(archive, 0o600)
    return archive


def _wait_port(port: int, *, up: bool, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _port_open(port) == up:
            return True
        time.sleep(1.0)
    return False


def _set_workspace(value: Path, agent_ids: list[str]) -> None:
    _check(_openclaw("config", "set", "agents.defaults.workspace", str(value), timeout=60), "更新工作区配置")
    for agent_id in agent_ids:
        _check(_openclaw("config", "set", f"agents.entries.{agent_id}.workspace", str(value), timeout=60), "更新工作区配置")


def _do_migrate() -> None:
    from nblane.core import backup_targets

    old = workspace_path()
    if old is None:
        raise OpenClawSetupError("找不到当前工作区。")
    old = old.resolve()
    new = target_workspace()
    config = read_config() or {}
    entries = ((config.get("agents") or {}).get("entries") or {})
    agent_ids = [
        agent_id
        for agent_id, entry in entries.items()
        if isinstance(entry, dict) and entry.get("workspace") and Path(str(entry["workspace"])).expanduser().resolve() == old
    ]
    _phase("archive", "备份整个 OpenClaw 状态目录")
    archive = _archive_state(backup_targets.backups_dir())
    shutil.copy2(config_path(), archive.with_suffix(".openclaw.json"))
    _log(f"已备份到 {archive}")
    _phase("stop", "停止网关（微信渠道会短暂断开）")
    # The CLI refuses a non-interactive stop without --force; the admin
    # confirmed the outage in the UI before this job started.
    _check(_openclaw("gateway", "stop", "--force", timeout=120), "停止网关")
    _wait_port(gateway_port(), up=False, timeout=30)
    moved = False
    try:
        _phase("move", f"移动工作区 {old} → {new}")
        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old), str(new))
        moved = True
        old.symlink_to(new, target_is_directory=True)
        _log("旧路径已改为指向新位置的软链接")
        _set_workspace(new, agent_ids)
        _phase("git", "工作区纳入 git 备份")
        backup_targets.ensure_repo(new, backup_targets.WORKSPACE_GITIGNORE, untrack=backup_targets.WORKSPACE_UNTRACK)
    except Exception:
        _log("出错，回滚中…")
        if moved:
            with contextlib.suppress(OSError):
                if old.is_symlink():
                    old.unlink()
                shutil.move(str(new), str(old))
            with contextlib.suppress(OSError):
                shutil.copy2(archive.with_suffix(".openclaw.json"), config_path())
        _openclaw("gateway", "start", timeout=120)
        raise
    _phase("start", "启动网关")
    _check(_openclaw("gateway", "start", timeout=120), "启动网关")
    if not _wait_port(gateway_port(), up=True, timeout=90):
        raise OpenClawSetupError("网关 90 秒内没有恢复监听，请到车间终端查看 openclaw gateway status。")
    _log(f"网关已恢复（端口 {gateway_port()}）")


def gateway_action(action: str) -> None:
    if action not in {"start", "stop", "restart"}:
        raise OpenClawSetupError("未知的网关操作。")
    if other := foreign_root():
        raise OpenClawSetupError(_foreign_message(other))
    # stop needs --force outside a TTY; restart waits for active work to drain.
    extra = {"stop": ["--force"], "restart": ["--safe"]}.get(action, [])
    _check(_openclaw("gateway", action, *extra, timeout=300), f"网关 {action} ")


__all__ = [
    "OpenClawSetupError",
    "PINNED_VERSION",
    "agent_data_root",
    "build_mcp_entry",
    "connected_profile",
    "foreign_root",
    "gateway_action",
    "job_blocker",
    "job_state",
    "node_supported",
    "read_config",
    "refresh_corpus",
    "start_job",
    "status",
    "target_workspace",
    "workspace_path",
]
