"""Environment checks for ``nblane doctor`` and the setup wizard.

Each check reports one thing about the machine or the data root and, when
it is not fine, a one-line fix hint. Only ``fail`` means nblane cannot run;
``warn`` marks a missing optional feature and ``info`` is plain context.
Network probes (the LLM call) run only when asked for.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

OK = "ok"
WARN = "warn"
FAIL = "fail"
INFO = "info"

_MARKS = {OK: "✓", WARN: "!", FAIL: "✗", INFO: "·"}

DEFAULT_PORTS = {"SPA + API": 8504, "Reader API": 8502}


@dataclass
class Check:
    """One doctor finding."""

    name: str
    status: str
    detail: str
    hint: str = ""


def _env_file() -> Path:
    from nblane.core import llm

    return llm._ENV_FILE


def check_python() -> Check:
    version = ".".join(str(part) for part in sys.version_info[:3])
    if sys.version_info >= (3, 11):
        return Check("Python", OK, version)
    return Check("Python", FAIL, version, "需要 Python ≥ 3.11")


def check_binary(name: str, label: str, *, required: bool, purpose: str, hint: str) -> Check:
    path = shutil.which(name)
    if path:
        return Check(label, OK, path)
    return Check(label, FAIL if required else WARN, f"未找到（{purpose}）", hint)


def check_chromium() -> Check:
    from nblane.core.resume_doc import find_chromium

    path = find_chromium()
    if path and (Path(path).exists() or shutil.which(path)):
        return Check("Chromium", OK, path)
    return Check(
        "Chromium",
        WARN,
        "未找到（简历 PDF、小红书 / X 分享卡片要用）",
        "npm install && npm run test:e2e:install（国内用 :cn），或 apt install chromium",
    )


def check_data_root() -> list[Check]:
    from nblane.core.paths import PROFILES_DIR, REPO_ROOT
    from nblane.core.profile_io import list_profiles

    checks = [Check("数据目录", INFO, str(REPO_ROOT))]
    if not PROFILES_DIR.is_dir():
        checks.append(Check("档案", FAIL, f"{PROFILES_DIR} 不存在", "运行 nblane setup，或设置 NBLANE_ROOT"))
        return checks
    names = list_profiles()
    if names:
        checks.append(Check("档案", OK, "、".join(names)))
    else:
        checks.append(Check("档案", WARN, "还没有档案", "运行 nblane setup 或 nblane init <name>"))
    return checks


def check_llm(*, online: bool = False) -> list[Check]:
    from nblane.core import llm

    env_file = _env_file()
    checks: list[Check] = []
    if env_file.exists():
        mode = env_file.stat().st_mode & 0o777
        if mode & 0o077:
            checks.append(Check(".env", WARN, f"{env_file}（权限 {mode:o}）", f"chmod 600 {env_file}"))
        else:
            checks.append(Check(".env", OK, str(env_file)))
    else:
        checks.append(Check(".env", INFO, f"{env_file} 不存在（不用 AI 时可以没有）"))

    llm.reload_env_if_changed()
    if not llm.is_configured():
        checks.append(
            Check("AI 服务", WARN, "未配置 API Key，AI 功能不可用", "运行 nblane setup，或在「设置 → AI 服务」里填写")
        )
        return checks
    label = f"{llm._MODEL} @ {llm._BASE_URL}"
    if not online:
        checks.append(Check("AI 服务", OK, f"{label}（未测试连接，加 --online 测试）"))
        return checks
    reply = llm.chat("Reply with OK.", "ping", max_tokens=16, timeout=30, max_retries=0)
    if reply.startswith("LLM error:"):
        checks.append(Check("AI 服务", FAIL, f"{label} 连接失败：{reply[10:].strip()[:160]}", "检查 Key、Base URL、模型名和代理"))
    else:
        checks.append(Check("AI 服务", OK, f"{label}（连接正常）"))
    return checks


def check_auth() -> list[Check]:
    from nblane.core import auth

    path = auth.auth_file_path()
    if path is None:
        return [Check("登录", INFO, "未开启（本机单人使用可以不开；上服务器必须开）")]
    if not path.exists():
        return [Check("登录", FAIL, f"NBLANE_AUTH_FILE 指向的 {path} 不存在", "运行 nblane setup 创建管理员")]
    checks = [Check("登录", OK, str(path))]
    if not os.getenv("NBLANE_READER_TOKEN_SECRET", "").strip():
        checks.append(
            Check(
                "会话密钥",
                FAIL,
                "开了登录但没有 NBLANE_READER_TOKEN_SECRET",
                "运行 nblane setup 生成，或在 .env 里设置一个随机串",
            )
        )
    return checks


def check_data_git() -> Check:
    from nblane.core import git_backup
    from nblane.core.paths import PROFILES_DIR

    repo = git_backup._find_git_root(PROFILES_DIR if PROFILES_DIR.exists() else PROFILES_DIR.parent)
    if repo is None:
        return Check("数据备份", WARN, "数据目录不是 Git 仓库，没有历史可回退", "见 docs/zh/architecture/storage.md")
    ignored = git_backup._run_git(repo, ["check-ignore", "-q", str(PROFILES_DIR / "x")]).returncode == 0
    if ignored:
        return Check(
            "数据备份",
            INFO,
            "档案放在代码仓库里且被 gitignore，不进 Git；长期使用建议把数据目录单独建仓库（NBLANE_ROOT）",
        )
    remote = git_backup._run_git(repo, ["remote"]).stdout.strip()
    if not remote:
        return Check("数据备份", WARN, f"{repo} 没有配置远端，只在本机", "git remote add origin <私有仓库>")
    flags = "自动提交" if git_backup.autocommit_enabled() else "未开自动提交"
    if git_backup.autocommit_enabled():
        flags += "、自动推送" if git_backup.autopush_enabled() else "、未开自动推送"
    return Check("数据备份", OK, f"{repo}（远端 {remote.splitlines()[0]}，{flags}）")


def _port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def check_ports(ports: dict[str, int] | None = None) -> list[Check]:
    checks = []
    for label, port in (ports or DEFAULT_PORTS).items():
        state = "已在监听" if _port_open(port) else "空闲（服务没在跑）"
        checks.append(Check(f"端口 {port}", INFO, f"{label}：{state}"))
    return checks


def check_grobid() -> Check | None:
    if os.getenv("NBLANE_RESEARCH_PDF_BACKEND", "").strip().lower() != "grobid":
        return None
    from nblane.core import grobid_service

    url = grobid_service.service_url()
    alive, _body = grobid_service._probe(url, "/api/isalive")
    if alive:
        return Check("GROBID", OK, url)
    return Check("GROBID", WARN, f"{url} 连不上，论文结构化会降级", "在「设置 → 本地服务」里安装或启动")


UNIT_ENV_MARKER = "NBLANE_DOCTOR_UNIT"

_ENV_FILE_RE = re.compile(r"(\S+) \(ignore_errors=(yes|no)\)")


class UnitEnvError(RuntimeError):
    """The systemd unit cannot be read."""


def parse_unit_show(text: str) -> tuple[dict[str, str], list[tuple[str, bool]], str]:
    """Parse ``systemctl show -p Environment -p EnvironmentFiles -p WorkingDirectory``.

    Returns ``(environment, [(env_file, ignore_errors)], working_directory)``.
    """
    env: dict[str, str] = {}
    files: list[tuple[str, bool]] = []
    workdir = ""
    for line in text.splitlines():
        key, _sep, value = line.partition("=")
        if key == "Environment" and value:
            for item in shlex.split(value):
                name, eq, val = item.partition("=")
                if eq and name:
                    env[name] = val
        elif key == "EnvironmentFiles" and value:
            files += [(path, flag == "yes") for path, flag in _ENV_FILE_RE.findall(value)]
        elif key == "WorkingDirectory":
            workdir = value
    return env, files, workdir


def unit_environment(unit: str) -> tuple[dict[str, str], str]:
    """Environment a systemd unit's process gets, plus its working directory.

    ``EnvironmentFile=`` values override ``Environment=``, as in systemd.
    Values are never printed; only the doctor checks look at them.
    """
    if not shutil.which("systemctl"):
        raise UnitEnvError("没有 systemctl")
    args = ["systemctl", "show", unit, "-p", "LoadState", "-p", "Environment", "-p", "EnvironmentFiles", "-p", "WorkingDirectory"]
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0 or "LoadState=not-found" in result.stdout:
        raise UnitEnvError(f"找不到 systemd 单元 {unit}")
    env, files, workdir = parse_unit_show(result.stdout)
    from dotenv import dotenv_values

    for path, ignore_errors in files:
        try:
            with open(path, encoding="utf-8") as handle:
                values = dotenv_values(stream=handle)
        except OSError as exc:
            if ignore_errors:
                continue
            raise UnitEnvError(f"读不了 {path}：{exc.strerror}") from exc
        env.update({key: value for key, value in values.items() if value is not None})
    return env, workdir


def run_checks(*, online: bool = False, ports: bool = True) -> list[Check]:
    """Run every check in display order."""
    unit = os.getenv(UNIT_ENV_MARKER, "").strip()
    checks: list[Check] = [Check("服务环境", INFO, f"按 systemd 单元 {unit} 的环境检查")] if unit else []
    checks += [
        check_python(),
        check_binary("git", "Git", required=True, purpose="数据备份和历史", hint="apt install git"),
        check_binary("tmux", "tmux", required=False, purpose="scripts/dev-web.sh 用它托管服务", hint="apt install tmux"),
        check_chromium(),
        check_binary("node", "Node.js", required=False, purpose="只在改前端或跑 e2e 时需要", hint="https://nodejs.org"),
    ]
    checks += check_data_root()
    checks += check_llm(online=online)
    checks += check_auth()
    checks.append(check_data_git())
    grobid = check_grobid()
    if grobid is not None:
        checks.append(grobid)
    if ports:
        checks += check_ports()
    return checks


def _width(text: str) -> int:
    """Terminal columns: CJK and other wide characters take two."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def format_checks(checks: list[Check]) -> str:
    width = max((_width(check.name) for check in checks), default=0)
    lines = []
    for check in checks:
        pad = " " * (width - _width(check.name))
        lines.append(f"{_MARKS[check.status]} {check.name}{pad}  {check.detail}")
        if check.hint and check.status in (WARN, FAIL):
            lines.append(f"  {' ' * width}  → {check.hint}")
    failed = sum(check.status == FAIL for check in checks)
    warned = sum(check.status == WARN for check in checks)
    if failed:
        lines.append(f"\n{failed} 项必须修复，{warned} 项可选功能未就绪。")
    elif warned:
        lines.append(f"\n可以运行；{warned} 项可选功能未就绪。")
    else:
        lines.append("\n一切就绪。")
    return "\n".join(lines)


def has_failures(checks: list[Check]) -> bool:
    return any(check.status == FAIL for check in checks)

