"""Git-backed backup targets and their private remotes.

nblane's own data root (``NBLANE_ROOT``) and each connected personal agent's
workspace are **separate** git repositories: the backup is unified (one
Settings panel, one daily timer), the repositories are not. Agent episodic
memory stays owned by the agent; nblane only registers, snapshots and pushes
it (docs/zh/guides/assistant.md).

Per target this module reports remote/push freshness and drives the guided
remote setup: generate a per-repository deploy key (GitHub deploy keys are
one-repository-only), validate the SSH URL, refuse anonymously visible
(public) GitHub repositories, test read+write with ``git ls-remote`` and
``git push --dry-run``, then save the remote and push.

Commit policy differs per target: an agent workspace is snapshotted with
``git add -A`` (the agent writes freely); ``nblane-data`` is ``push_only``
because the app already commits every write (``core/git_backup.py``) and
untracked leftovers there should be looked at, not swept in.

All git invocations are argv lists (no shell); URLs are whitelisted by regex
and never start with ``-``. Tests patch ``_network_visibility`` and
``validate_remote_url`` to drive local bare repositories.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nblane.core import paths

TARGET_NBLANE_DATA = "nblane-data"
TARGET_OPENCLAW_WORKSPACE = "openclaw-workspace"
COMMIT_ALL = "all"
COMMIT_PUSH_ONLY = "push_only"
DEFAULT_UNIT = "nblane-backup"
ON_CALENDAR = "*-*-* 03:30:00"
_GIT_TIMEOUT = 30.0
_PUSH_TIMEOUT = 600.0

_SSH_SHORT_RE = re.compile(
    r"^git@(?P<host>[A-Za-z0-9][A-Za-z0-9.-]*):"
    r"(?P<owner>[A-Za-z0-9][A-Za-z0-9._-]*)/(?P<repo>[A-Za-z0-9][A-Za-z0-9._-]*?)(?:\.git)?$"
)
_SSH_SCHEME_RE = re.compile(
    r"^ssh://git@(?P<host>[A-Za-z0-9][A-Za-z0-9.-]*)(?::\d{1,5})?/"
    r"(?P<owner>[A-Za-z0-9][A-Za-z0-9._-]*)/(?P<repo>[A-Za-z0-9][A-Za-z0-9._-]*?)(?:\.git)?$"
)

DATA_GITIGNORE = """\
.env
.env.*
!.env.example
.reader-token-secret
__pycache__/
*.pyc
*.lock
"""

WORKSPACE_GITIGNORE = """\
# Rebuildable / machine-local (recreated by nblane connect or install.sh)
skills/.venv/
**/__pycache__/
tmp/
# Derived nblane corpus (re-rendered from profiles/ on connect)
memory/nblane/
"""

WORKSPACE_UNTRACK = ("skills/.venv", "memory/nblane")

_STATE_LOCK = threading.RLock()


class BackupError(RuntimeError):
    """User-facing backup failure (message is shown in Settings)."""


@dataclass(frozen=True)
class BackupTarget:
    """One git repository that the daily backup snapshots and pushes."""

    id: str
    label: str
    description: str
    path: Path
    commit_mode: str
    gitignore: str
    untrack: tuple[str, ...] = ()


# --------------------------------------------------------------- locations


def _clean_env(name: str) -> str:
    return str(os.getenv(name, "") or "").strip()


def key_dir() -> Path:
    value = _clean_env("NBLANE_BACKUP_KEY_DIR")
    return Path(value).expanduser() if value else Path.home() / ".ssh"


def state_dir() -> Path:
    value = _clean_env("NBLANE_BACKUP_STATE_DIR")
    if value:
        return Path(value).expanduser()
    return Path.home() / ".local" / "share" / "nblane" / "backup"


def backups_dir() -> Path:
    """Where pre-change archives (tarballs) go; outside every git target."""

    value = _clean_env("NBLANE_BACKUP_DIR")
    if value:
        return Path(value).expanduser()
    srv = Path("/srv/backups")
    agents = srv / "agents"
    # /srv/backups is root-owned in production; an operator-created
    # agents/ subdirectory owned by the service user is enough.
    if (agents.is_dir() and os.access(agents, os.W_OK)) or (srv.is_dir() and os.access(srv, os.W_OK)):
        return agents
    return Path.home() / ".local" / "share" / "nblane" / "backups"


def unit_name() -> str:
    value = _clean_env("NBLANE_BACKUP_UNIT") or DEFAULT_UNIT
    safe = "".join(ch for ch in value if ch.isalnum() or ch in "-_")
    return safe or DEFAULT_UNIT


def _systemd_user_dir() -> Path:
    base = _clean_env("XDG_CONFIG_HOME")
    root = Path(base).expanduser() if base else Path.home() / ".config"
    return root / "systemd" / "user"


# ----------------------------------------------------------------- targets


def list_targets() -> list[BackupTarget]:
    """Return the registered targets (agent targets only when present)."""

    targets = [
        BackupTarget(
            id=TARGET_NBLANE_DATA,
            label="nblane 数据",
            description="档案、技能树、证据、看板等结构化数据（每次写入由应用自动提交）。",
            path=Path(paths.REPO_ROOT),
            commit_mode=COMMIT_PUSH_ONLY,
            gitignore=DATA_GITIGNORE,
        )
    ]
    from nblane.core import openclaw_setup

    workspace = openclaw_setup.workspace_path()
    if workspace is not None:
        targets.append(
            BackupTarget(
                id=TARGET_OPENCLAW_WORKSPACE,
                label="OpenClaw 工作区",
                description="OpenClaw 的记忆与人格文件（MEMORY.md、USER.md、memory/ 日记等），每日整体快照。",
                path=workspace,
                commit_mode=COMMIT_ALL,
                gitignore=WORKSPACE_GITIGNORE,
                untrack=WORKSPACE_UNTRACK,
            )
        )
    return targets


def get_target(target_id: str) -> BackupTarget:
    for target in list_targets():
        if target.id == target_id:
            return target
    raise BackupError("未知的备份目标。")


# --------------------------------------------------------------------- git


def _run(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: float = _GIT_TIMEOUT,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError as exc:
        raise BackupError(f"找不到命令 {args[0]}。") from exc
    except subprocess.TimeoutExpired as exc:
        raise BackupError(f"{' '.join(args[:3])} 执行超时。") from exc


def _git(repo: Path, *args: str, env: dict[str, str] | None = None, timeout: float = _GIT_TIMEOUT):
    return _run(["git", "-C", str(repo), *args], env=env, timeout=timeout)


def _out(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout.strip() if result.returncode == 0 else ""


def _last_line(result: subprocess.CompletedProcess[str]) -> str:
    """The most informative output line (git puts the cause on fatal:/ERROR:)."""

    lines = [line.strip() for line in (result.stderr or result.stdout or "").splitlines() if line.strip()]
    for line in lines:
        if line.lower().startswith(("fatal:", "error:", "remote: error", "! [rejected]")):
            return line[:300]
    return (lines[-1] if lines else f"exit {result.returncode}")[:300]


def is_repo(path: Path) -> bool:
    return path.is_dir() and (path / ".git").exists()


def _identity_args(repo: Path) -> list[str]:
    """Fallback committer identity when the repository has none."""

    if _out(_git(repo, "config", "user.email")):
        return []
    return ["-c", "user.name=nblane-backup", "-c", f"user.email=nblane-backup@{socket.gethostname() or 'localhost'}"]


def _ssh_command(key: Path) -> str:
    return f"ssh -i {key} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"


def _ssh_env(key: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["GIT_SSH_COMMAND"] = _ssh_command(key) + " -o BatchMode=yes -o ConnectTimeout=15"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _configured_key(repo: Path) -> Path | None:
    command = _out(_git(repo, "config", "--get", "core.sshCommand"))
    match = re.search(r"-i\s+(\S+)", command)
    return Path(match.group(1)).expanduser() if match else None


def default_key_path(target_id: str) -> Path:
    return key_dir() / f"nblane_backup_{target_id.replace('-', '_')}_ed25519"


def key_path(target: BackupTarget) -> Path:
    if is_repo(target.path):
        configured = _configured_key(target.path)
        if configured is not None:
            return configured
    return default_key_path(target.id)


# ------------------------------------------------------------------- state


def _state_path() -> Path:
    return state_dir() / "state.json"


def _load_state() -> dict[str, Any]:
    try:
        data = json.loads(_state_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _record_run(target_id: str, **fields: Any) -> None:
    with _STATE_LOCK:
        data = _load_state()
        runs = data.setdefault("runs", {})
        runs[target_id] = {"at": datetime.now(timezone.utc).isoformat(), **fields}
        path = _state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(path)


# ------------------------------------------------------------------ status


def target_status(target: BackupTarget) -> dict[str, Any]:
    """Display-ready snapshot of one target (cheap local git calls only)."""

    repo = target.path
    key = key_path(target)
    pub = key.with_name(key.name + ".pub")
    data: dict[str, Any] = {
        "id": target.id,
        "label": target.label,
        "description": target.description,
        "path": str(repo),
        "commit_mode": target.commit_mode,
        "exists": repo.is_dir(),
        "is_git": is_repo(repo),
        "remote_url": "",
        "branch": "",
        "upstream": "",
        "ahead": 0,
        "dirty": 0,
        "has_commits": False,
        "last_commit_at": "",
        "last_commit_subject": "",
        "key_path": str(key),
        "key_ready": key.is_file() and pub.is_file(),
        "public_key": pub.read_text(encoding="utf-8").strip() if pub.is_file() else "",
        "last_run": (_load_state().get("runs") or {}).get(target.id) or {},
    }
    if not data["is_git"]:
        return data
    data["remote_url"] = _out(_git(repo, "remote", "get-url", "origin"))
    data["branch"] = _out(_git(repo, "rev-parse", "--abbrev-ref", "HEAD"))
    log = _out(_git(repo, "log", "-1", "--format=%cI%x00%s"))
    if log:
        data["has_commits"] = True
        when, _, subject = log.partition("\x00")
        data["last_commit_at"], data["last_commit_subject"] = when, subject[:120]
    data["upstream"] = _out(_git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"))
    if data["upstream"]:
        count = _out(_git(repo, "rev-list", "--count", "@{u}..HEAD"))
        data["ahead"] = int(count) if count.isdigit() else 0
    elif data["has_commits"]:
        count = _out(_git(repo, "rev-list", "--count", "HEAD"))
        data["ahead"] = int(count) if count.isdigit() else 0
    porcelain = _git(repo, "status", "--porcelain")
    data["dirty"] = len([line for line in porcelain.stdout.splitlines() if line.strip()]) if porcelain.returncode == 0 else 0
    return data


def autocommit_flags() -> dict[str, bool]:
    from nblane.core import git_backup

    return {"autocommit": git_backup.autocommit_enabled(), "autopush": git_backup.autopush_enabled()}


def status() -> dict[str, Any]:
    return {
        "targets": [target_status(target) for target in list_targets()],
        "timer": timer_status(),
        "backups_dir": str(backups_dir()),
        "data_git": autocommit_flags(),
    }


# ------------------------------------------------------------ repo + keys


def ensure_gitignore(repo: Path, template: str) -> None:
    """Append template lines missing from the repo's ``.gitignore``."""

    path = repo / ".gitignore"
    current = path.read_text(encoding="utf-8") if path.is_file() else ""
    have = {line.strip() for line in current.splitlines()}
    missing = [line for line in template.splitlines() if line.strip() and line.strip() not in have]
    if not missing:
        return
    prefix = current if not current or current.endswith("\n") else current + "\n"
    path.write_text(prefix + "\n".join(missing) + "\n", encoding="utf-8")


def ensure_repo(
    repo: Path,
    template: str,
    *,
    untrack: tuple[str, ...] = (),
    message: str = "chore: initial backup snapshot",
) -> bool:
    """Make *repo* a git repository with a sane ``.gitignore``; True if created."""

    if not repo.is_dir():
        raise BackupError(f"目录不存在：{repo}")
    created = False
    if not is_repo(repo):
        result = _git(repo, "init", "-q", "-b", "main")
        if result.returncode != 0:
            raise BackupError("git init 失败：" + _last_line(result))
        created = True
    ensure_gitignore(repo, template)
    # Previously committed rebuildable dirs (e.g. a skills venv) leave the index.
    for pattern in untrack:
        if (repo / pattern).exists():
            _git(repo, "rm", "-r", "-q", "--cached", "--ignore-unmatch", pattern)
    # Fresh repos (ours, or one OpenClaw onboarding git-inited) get a first snapshot.
    if created or not _out(_git(repo, "rev-parse", "--verify", "-q", "HEAD")):
        _commit_all(repo, message)
    return created


def init_target(target_id: str) -> None:
    target = get_target(target_id)
    ensure_repo(target.path, target.gitignore, untrack=target.untrack)


def generate_key(target_id: str) -> str:
    """Create the target's deploy key once (never overwritten); return the public key."""

    target = get_target(target_id)
    key = key_path(target)
    pub = key.with_name(key.name + ".pub")
    if not key.is_file():
        key.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(key.parent, 0o700)
        comment = f"nblane-backup-{target.id}@{socket.gethostname() or 'host'}"
        result = _run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", comment, "-f", str(key)])
        if result.returncode != 0:
            raise BackupError("生成密钥失败：" + _last_line(result))
    os.chmod(key, 0o600)
    return pub.read_text(encoding="utf-8").strip()


# ------------------------------------------------------------------ remote


def validate_remote_url(url: str) -> dict[str, str]:
    """Parse an SSH remote URL; raise :class:`BackupError` when not allowed."""

    clean = (url or "").strip()
    match = _SSH_SHORT_RE.match(clean) or _SSH_SCHEME_RE.match(clean)
    if not match or clean.startswith("-"):
        raise BackupError("请填写 SSH 地址，形如 git@github.com:用户名/仓库名.git（部署密钥只支持 SSH）。")
    return {"url": clean, "host": match.group("host").lower(), "owner": match.group("owner"), "repo": match.group("repo")}


def _network_visibility(info: dict[str, str]) -> str:
    """``public`` / ``hidden`` (not anonymously visible) / ``unknown``."""

    if info["host"] != "github.com" or os.environ.get("NBLANE_DISABLE_NETWORK_LOOKUPS"):
        return "unknown"
    try:
        import httpx

        response = httpx.get(
            f"https://api.github.com/repos/{info['owner']}/{info['repo']}",
            timeout=8.0,
            headers={"Accept": "application/vnd.github+json"},
        )
    except Exception:
        return "unknown"
    if response.status_code == 404:
        return "hidden"
    if response.status_code == 200:
        try:
            return "hidden" if response.json().get("private") else "public"
        except ValueError:
            return "unknown"
    return "unknown"


def test_remote(target_id: str, url: str) -> dict[str, Any]:
    """Check URL, visibility, read and write access without changing anything."""

    target = get_target(target_id)
    result: dict[str, Any] = {
        "ok": False,
        "visibility": "unknown",
        "reachable": False,
        "writable": False,
        "remote_empty": False,
        "message": "",
    }
    try:
        info = validate_remote_url(url)
    except BackupError as exc:
        result["message"] = str(exc)
        return result
    if not is_repo(target.path):
        result["message"] = "目标目录还不是 git 仓库，请先初始化。"
        return result
    key = key_path(target)
    if not key.is_file():
        result["message"] = "请先生成部署密钥，并添加到远端仓库。"
        return result
    result["visibility"] = _network_visibility(info)
    if result["visibility"] == "public":
        result["message"] = "这个仓库是公开的。工作区包含个人记忆，请在仓库设置里改为 Private 后再试。"
        return result
    env = _ssh_env(key)
    listing = _run(["git", "ls-remote", "--", info["url"]], cwd=target.path, env=env, timeout=60)
    if listing.returncode != 0:
        result["message"] = "连不上远端：" + _last_line(listing) + "（确认部署密钥已添加、地址无误）"
        return result
    result["reachable"] = True
    result["remote_empty"] = not listing.stdout.strip()
    branch = _out(_git(target.path, "rev-parse", "--abbrev-ref", "HEAD")) or "main"
    if _out(_git(target.path, "log", "-1", "--format=%H")):
        dry = _run(
            ["git", "push", "--dry-run", "--porcelain", "--", info["url"], f"HEAD:refs/heads/{branch}"],
            cwd=target.path,
            env=env,
            timeout=90,
        )
        if dry.returncode != 0:
            text = (dry.stderr + dry.stdout).lower()
            if "denied" in text or "read only" in text or "read-only" in text or "403" in text:
                result["message"] = "部署密钥没有写权限：在仓库的 Deploy keys 里勾选 Allow write access。"
            elif "rejected" in text or "fetch first" in text or "non-fast-forward" in text:
                result["message"] = "远端已有不同的历史记录。请换一个新建的空仓库。"
            else:
                result["message"] = "写入测试失败：" + _last_line(dry)
            return result
    result["writable"] = True
    result["ok"] = True
    if result["visibility"] == "unknown":
        result["message"] = "连接正常。无法自动确认仓库是否私有，请在远端设置里再确认一次。"
    else:
        result["message"] = "连接正常，仓库为私有，可以保存。"
    return result


def connect_remote(target_id: str, url: str) -> dict[str, Any]:
    """Re-test, save ``origin`` + ``core.sshCommand`` and push the history."""

    check = test_remote(target_id, url)
    if not check["ok"]:
        raise BackupError(check["message"] or "远端测试未通过。")
    target = get_target(target_id)
    key = key_path(target)
    clean = validate_remote_url(url)["url"]
    existing = _out(_git(target.path, "remote", "get-url", "origin"))
    verb = "set-url" if existing else "add"
    result = _git(target.path, "remote", verb, "origin", clean)
    if result.returncode != 0:
        raise BackupError("保存远端失败：" + _last_line(result))
    _git(target.path, "config", "core.sshCommand", _ssh_command(key))
    push = _git(target.path, "push", "-u", "origin", "HEAD", env=_ssh_env(key), timeout=_PUSH_TIMEOUT)
    if push.returncode != 0:
        _record_run(target.id, ok=False, committed=False, pushed=False, error=_last_line(push))
        raise BackupError("首次推送失败：" + _last_line(push))
    _record_run(target.id, ok=True, committed=False, pushed=True, error="")
    return target_status(target)


# ------------------------------------------------------------------ backup


def _commit_all(repo: Path, message: str) -> bool:
    add = _git(repo, "add", "-A")
    if add.returncode != 0:
        raise BackupError("git add 失败：" + _last_line(add))
    if _git(repo, "diff", "--cached", "--quiet").returncode == 0 and _out(_git(repo, "log", "-1", "--format=%H")):
        return False
    commit = _run(["git", "-C", str(repo), *_identity_args(repo), "commit", "-q", "-m", message])
    if commit.returncode != 0:
        raise BackupError("git commit 失败：" + _last_line(commit))
    return True


def backup_target(target: BackupTarget) -> dict[str, Any]:
    """Snapshot (for ``all`` targets) and push one target; never raises."""

    outcome: dict[str, Any] = {"id": target.id, "ok": False, "committed": False, "pushed": False, "error": ""}
    try:
        if not is_repo(target.path):
            raise BackupError("不是 git 仓库。")
        if target.commit_mode == COMMIT_ALL:
            stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
            outcome["committed"] = _commit_all(target.path, f"backup: snapshot {stamp}")
        if not _out(_git(target.path, "remote", "get-url", "origin")):
            raise BackupError("还没有配置远端，只在本机提交。")
        key = key_path(target)
        env = _ssh_env(key) if key.is_file() else None
        push = _git(target.path, "push", "-u", "origin", "HEAD", env=env, timeout=_PUSH_TIMEOUT)
        if push.returncode != 0:
            raise BackupError("推送失败：" + _last_line(push))
        outcome["pushed"] = True
        outcome["ok"] = True
    except BackupError as exc:
        outcome["error"] = str(exc)
    _record_run(target.id, **{k: v for k, v in outcome.items() if k != "id"})
    return outcome


def run_backup(target_id: str | None = None) -> list[dict[str, Any]]:
    targets = [get_target(target_id)] if target_id else list_targets()
    return [backup_target(target) for target in targets if target.path.is_dir()]


# ------------------------------------------------------------------- timer


def _user_env() -> dict[str, str]:
    env = dict(os.environ)
    uid = os.getuid()
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{uid}")
    env.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path=/run/user/{uid}/bus")
    return env


def _systemctl(*args: str, timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    return _run(["systemctl", "--user", *args], env=_user_env(), timeout=timeout)


_PASSTHROUGH_ENV = (
    "NBLANE_ROOT",
    "NBLANE_OPENCLAW_PROFILE",
    "NBLANE_AGENT_DATA_ROOT",
    "NBLANE_BACKUP_KEY_DIR",
    "NBLANE_BACKUP_STATE_DIR",
    "NBLANE_BACKUP_DIR",
    "PATH",
)


def service_text() -> str:
    env_lines = []
    for name in _PASSTHROUGH_ENV:
        value = os.environ.get(name, "")
        if name == "NBLANE_ROOT" and not value:
            value = str(paths.REPO_ROOT)
        if value and "\n" not in value:
            env_lines.append(f'Environment="{name}={value}"')
    import sys

    return (
        "# Managed by nblane (Settings → 数据备份). Edits are overwritten.\n"
        "[Unit]\n"
        "Description=nblane daily backup (commit + push data repositories)\n\n"
        "[Service]\n"
        "Type=oneshot\n"
        + "\n".join(env_lines)
        + f"\nExecStart={sys.executable} -m nblane.cli backup run\n"
    )


def timer_text() -> str:
    return (
        "# Managed by nblane (Settings → 数据备份).\n"
        "[Unit]\n"
        "Description=nblane daily backup timer\n\n"
        "[Timer]\n"
        f"OnCalendar={ON_CALENDAR}\n"
        "Persistent=true\n"
        "RandomizedDelaySec=300\n\n"
        "[Install]\n"
        "WantedBy=timers.target\n"
    )


def timer_status() -> dict[str, Any]:
    unit = unit_name()
    installed = (_systemd_user_dir() / f"{unit}.timer").is_file()
    data: dict[str, Any] = {"unit": unit, "installed": installed, "enabled": False, "next_run": "", "schedule": "每天 03:30"}
    if not installed or shutil.which("systemctl") is None:
        return data
    try:
        enabled = _systemctl("is-enabled", f"{unit}.timer", timeout=10)
        data["enabled"] = enabled.stdout.strip() == "enabled"
        show = _systemctl("show", f"{unit}.timer", "-p", "NextElapseUSecRealtime", "--value", timeout=10)
        data["next_run"] = show.stdout.strip() if show.returncode == 0 else ""
    except BackupError:
        pass
    return data


def set_timer(enabled: bool) -> dict[str, Any]:
    unit = unit_name()
    directory = _systemd_user_dir()
    if enabled:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{unit}.service").write_text(service_text(), encoding="utf-8")
        (directory / f"{unit}.timer").write_text(timer_text(), encoding="utf-8")
        reload = _systemctl("daemon-reload")
        if reload.returncode != 0:
            raise BackupError("systemctl --user daemon-reload 失败：" + _last_line(reload))
        result = _systemctl("enable", "--now", f"{unit}.timer")
        if result.returncode != 0:
            raise BackupError("启用定时备份失败：" + _last_line(result))
    elif (directory / f"{unit}.timer").is_file():
        _systemctl("disable", "--now", f"{unit}.timer")
    return timer_status()



__all__ = [
    "BackupError",
    "BackupTarget",
    "COMMIT_ALL",
    "COMMIT_PUSH_ONLY",
    "TARGET_NBLANE_DATA",
    "TARGET_OPENCLAW_WORKSPACE",
    "WORKSPACE_GITIGNORE",
    "WORKSPACE_UNTRACK",
    "backups_dir",
    "connect_remote",
    "ensure_repo",
    "generate_key",
    "get_target",
    "init_target",
    "list_targets",
    "run_backup",
    "set_timer",
    "status",
    "target_status",
    "test_remote",
    "timer_status",
    "validate_remote_url",
]
