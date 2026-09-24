"""OpenClaw host/gateway health checks ("doctor").

Scripts the layered prerequisites from ``docs/zh/guides/openclaw-integration.md``
and the deep-integration plan (§5.4): Node version, systemd linger, gateway
port, MCP registration, WeChat plugin, automations drift, backup schedule.

Every check is read-only and takes an injectable ``runner`` (see
:mod:`nblane.core.openclaw_automations`) so tests never spawn real
processes.  ``openclaw doctor`` is never invoked — it restarts the gateway.

Exit-code convention: :func:`doctor_exit_code` returns 1 when any check with
``severity == "error"`` fails; warnings never affect the exit code.
"""

from __future__ import annotations

import getpass
import json
import os
import re
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from nblane.core.openclaw_automations import (
    ACTION_ADD,
    ACTION_KEEP,
    ACTION_PRUNE_CANDIDATE,
    ACTION_SKIP_FOREIGN,
    ACTION_UPDATE,
    CommandResult,
    Runner,
    automations_file_path,
    fetch_live_automations,
    load_automations_file,
    plan_reconcile,
    run_command,
)

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"

GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 18789

# docs/zh/guides/openclaw-integration.md: Node >=24.16.0 <25 or >=26.1.0.
_MIN_NODE_24 = (24, 16, 0)
_MIN_NODE_26 = (26, 1, 0)

_VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


@dataclass(frozen=True)
class DoctorCheck:
    """One doctor check outcome."""

    id: str
    ok: bool
    severity: str
    detail: str
    hint: str = ""


def _check(
    check_id: str,
    ok: bool,
    severity: str,
    detail: str,
    hint: str = "",
) -> DoctorCheck:
    return DoctorCheck(
        id=check_id, ok=ok, severity=severity, detail=detail, hint=hint
    )


# -- individual checks -------------------------------------------------------


def check_openclaw_version(runner: Runner = run_command) -> DoctorCheck:
    """The ``openclaw`` CLI must be on PATH and report a version."""

    result = runner(["openclaw", "--version"])
    if not result.ok:
        return _check(
            "openclaw_version",
            False,
            SEVERITY_ERROR,
            f"openclaw CLI 不可用: {result.output or f'exit {result.returncode}'}",
            "按接入指南 A 层安装 OpenClaw（curl -fsSL https://openclaw.ai/install.sh | bash）",
        )
    first_line = (result.stdout.strip().splitlines() or [""])[0]
    match = _VERSION_RE.search(first_line)
    detail = first_line if not match else f"OpenClaw {match.group(0).lstrip('v')}"
    return _check("openclaw_version", True, SEVERITY_INFO, detail or "已安装")


def check_node_version(runner: Runner = run_command) -> DoctorCheck:
    """Node must be >=24.16.0 <25 or >=26.1.0 (node:sqlite WAL requirement)."""

    result = runner(["node", "-v"])
    if not result.ok:
        return _check(
            "node_version",
            False,
            SEVERITY_ERROR,
            f"node 不可用: {result.output or f'exit {result.returncode}'}",
            "安装 Node 24 LTS（OpenClaw 要求 >=24.16 或 >=26.1）",
        )
    match = _VERSION_RE.search(result.stdout)
    if not match:
        return _check(
            "node_version",
            False,
            SEVERITY_ERROR,
            f"无法解析 node 版本: {result.stdout.strip()!r}",
            "确认 `node -v` 输出形如 v24.16.0",
        )
    version = tuple(int(part) for part in match.groups())
    major = version[0]
    ok = (
        (major == 24 and version >= _MIN_NODE_24)
        or (major >= 26 and version >= _MIN_NODE_26)
    )
    text = ".".join(str(part) for part in version)
    if ok:
        return _check("node_version", True, SEVERITY_INFO, f"Node v{text}")
    return _check(
        "node_version",
        False,
        SEVERITY_ERROR,
        f"Node v{text} 不受支持（需 >=24.16 且 <25，或 >=26.1）",
        "升级 Node 到 24 LTS 最新版或 26.1+",
    )


def check_linger(runner: Runner = run_command) -> DoctorCheck:
    """systemd user linger must be on so the gateway survives SSH logout."""

    user = os.environ.get("USER") or getpass.getuser()
    result = runner(["loginctl", "show-user", user, "-p", "Linger"])
    if not result.ok:
        return _check(
            "linger",
            False,
            SEVERITY_WARNING,
            f"无法确认 linger 状态: {result.output or f'exit {result.returncode}'}",
            "无图形登录的主机需要 `sudo loginctl enable-linger \"$USER\"`",
        )
    if "Linger=yes" in result.stdout:
        return _check("linger", True, SEVERITY_INFO, "Linger=yes")
    return _check(
        "linger",
        False,
        SEVERITY_ERROR,
        f"用户 {user} 的 linger 未启用，SSH 断开后用户服务会停止",
        'sudo loginctl enable-linger "$USER"',
    )


def _default_connect(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_gateway_port(
    connect: Callable[[str, int], bool] | None = None,
) -> DoctorCheck:
    """The gateway should listen on 127.0.0.1:18789 (loopback only)."""

    probe = connect or _default_connect
    if probe(GATEWAY_HOST, GATEWAY_PORT):
        return _check(
            "gateway_port",
            True,
            SEVERITY_INFO,
            f"{GATEWAY_HOST}:{GATEWAY_PORT} 正在监听",
        )
    return _check(
        "gateway_port",
        False,
        SEVERITY_ERROR,
        f"{GATEWAY_HOST}:{GATEWAY_PORT} 未监听",
        "systemctl --user status openclaw-gateway；不要绑定 0.0.0.0",
    )


def check_nblane_mcp_registered(runner: Runner = run_command) -> DoctorCheck:
    """``openclaw mcp list`` must contain the nblane server entry."""

    result = runner(["openclaw", "mcp", "list", "--json"])
    if not result.ok:
        return _check(
            "nblane_mcp_registered",
            False,
            SEVERITY_ERROR,
            f"openclaw mcp list 失败: {result.output or f'exit {result.returncode}'}",
            "确认 Gateway 在运行，并按 L0.2 用 `openclaw config patch` 注入 nblane MCP",
        )
    try:
        data = json.loads(result.stdout or "")
    except json.JSONDecodeError:
        # Older CLI without --json: degrade to a text match.
        if re.search(r"\bnblane\b", result.stdout):
            return _check(
                "nblane_mcp_registered",
                True,
                SEVERITY_INFO,
                "mcp list 文本输出中包含 nblane（--json 不可用，降级匹配）",
            )
        return _check(
            "nblane_mcp_registered",
            False,
            SEVERITY_ERROR,
            "mcp list 输出中未找到 nblane（--json 不可用，文本降级匹配）",
            "nblane sync-agent-harness --target openclaw --profile <name> 生成配置后注入",
        )
    entries: Any = data
    if isinstance(data, Mapping):
        entries = data.get("servers", data.get("mcp"))
        if entries is None:
            # Newer CLI prints the servers mapping directly at top level.
            entries = list(data.keys())
    if isinstance(entries, Mapping):
        entries = list(entries.keys())
    names = {
        entry.get("name")
        if isinstance(entry, Mapping)
        else entry
        for entry in (entries or [])
    }
    if "nblane" in names:
        return _check(
            "nblane_mcp_registered",
            True,
            SEVERITY_INFO,
            "mcp.servers 已注册 nblane",
        )
    return _check(
        "nblane_mcp_registered",
        False,
        SEVERITY_ERROR,
        f"mcp.servers 中没有 nblane（现有: {sorted(str(n) for n in names) or '无'}）",
        "nblane sync-agent-harness --target openclaw --profile <name> 生成配置后注入",
    )


def check_weixin_plugin(runner: Runner = run_command) -> DoctorCheck:
    """The openclaw-weixin plugin must be installed and enabled."""

    result = runner(["openclaw", "plugins", "list"])
    if not result.ok:
        return _check(
            "weixin_plugin",
            False,
            SEVERITY_ERROR,
            f"openclaw plugins list 失败: {result.output or f'exit {result.returncode}'}",
            "确认 Gateway 在运行",
        )
    lines = [
        line
        for line in result.stdout.splitlines()
        if "openclaw-weixin" in line.lower()
    ]
    if not lines:
        return _check(
            "weixin_plugin",
            False,
            SEVERITY_ERROR,
            "未安装 openclaw-weixin 插件",
            'openclaw plugins install "@tencent-weixin/openclaw-weixin"',
        )
    lowered = "\n".join(lines).lower()
    if "disabled" in lowered or re.search(r"\b(off|false)\b", lowered):
        return _check(
            "weixin_plugin",
            False,
            SEVERITY_ERROR,
            "openclaw-weixin 已安装但未启用",
            "在 openclaw.json 设置 plugins.entries.openclaw-weixin.enabled=true",
        )
    if "enabled" in lowered or re.search(r"\b(on|true)\b", lowered):
        return _check(
            "weixin_plugin",
            True,
            SEVERITY_INFO,
            "openclaw-weixin 已启用",
        )
    return _check(
        "weixin_plugin",
        False,
        SEVERITY_WARNING,
        "找到 openclaw-weixin 但无法确认启用状态",
        "openclaw plugins inspect openclaw-weixin --runtime --json 进一步确认",
    )


def check_automations_in_sync(
    runner: Runner = run_command,
    *,
    profile_name: str | None = None,
    automations_path: Path | None = None,
    live_jobs: Sequence[Mapping[str, Any]] | None = None,
) -> DoctorCheck:
    """Declared automations must match the live gateway (drift = error)."""

    if automations_path is None:
        if not profile_name:
            return _check(
                "automations_in_sync",
                True,
                SEVERITY_INFO,
                "未指定 profile，跳过自动化对账",
            )
        automations_path = automations_file_path(profile_name)
    if not automations_path.is_file():
        return _check(
            "automations_in_sync",
            True,
            SEVERITY_INFO,
            f"未声明 {automations_path.name}，跳过自动化对账",
        )
    try:
        specs = load_automations_file(automations_path)
    except ValueError as exc:
        return _check(
            "automations_in_sync",
            False,
            SEVERITY_ERROR,
            f"automations.yaml 无效: {exc}",
            "修正声明文件后重试",
        )
    if live_jobs is None:
        try:
            live_jobs = fetch_live_automations(runner)
        except RuntimeError as exc:
            return _check(
                "automations_in_sync",
                False,
                SEVERITY_ERROR,
                str(exc),
                "确认 Gateway 在运行后重试",
            )
    plan = plan_reconcile(specs, live_jobs)
    changes = sum(1 for a in plan if a.kind in (ACTION_ADD, ACTION_UPDATE))
    prunes = sum(1 for a in plan if a.kind == ACTION_PRUNE_CANDIDATE)
    keeps = sum(1 for a in plan if a.kind == ACTION_KEEP)
    skips = sum(1 for a in plan if a.kind == ACTION_SKIP_FOREIGN)
    detail = (
        f"声明 {len(specs)} 条；一致 {keeps}，待新增/更新 {changes}，"
        f"待清理 {prunes}，外部跳过 {skips}"
    )
    if changes:
        return _check(
            "automations_in_sync",
            False,
            SEVERITY_ERROR,
            detail,
            f"nblane openclaw automations sync {profile_name or '<profile>'}"
            "（先 dry-run，确认后 --apply）",
        )
    if prunes:
        return _check(
            "automations_in_sync",
            False,
            SEVERITY_WARNING,
            detail,
            "确认后用 --apply --prune 删除已下线的 nblane: 任务",
        )
    return _check("automations_in_sync", True, SEVERITY_INFO, detail)


_BACKUP_ID_RE = re.compile(r"(?:^|[\s:/_-])backup(?:[\s:/_-]|$)", re.IGNORECASE)


def _is_scheduled_job(job: Mapping[str, Any]) -> bool:
    """True when the live job carries a cron/every schedule."""
    schedule = job.get("schedule")
    if isinstance(schedule, Mapping):
        if schedule.get("cron") or schedule.get("every"):
            return True
        # Newer CLI shape: {"kind": "every"|"cron", "everyMs"/"expr": ...}
        return schedule.get("kind") in ("cron", "every")
    return bool(str(schedule or "").strip())


def check_backup_schedule(
    runner: Runner = run_command,
    *,
    live_jobs: Sequence[Mapping[str, Any]] | None = None,
) -> DoctorCheck:
    """A backup automation must exist (L0.4: ``openclaw backup enable``).

    Matching is deliberately strict: the job identifier (declarationKey or
    name) must contain ``backup`` at a segment boundary (``system:backup``,
    ``backup-daily``) **and** the job must carry a schedule — a job that
    merely mentions "backup" in free text does not count.
    """

    if live_jobs is None:
        try:
            live_jobs = fetch_live_automations(runner)
        except RuntimeError as exc:
            return _check(
                "backup_schedule",
                False,
                SEVERITY_ERROR,
                str(exc),
                "确认 Gateway 在运行后重试",
            )
    for job in live_jobs:
        identifier = " ".join(
            str(job.get(field) or "") for field in ("declarationKey", "name")
        )
        if _BACKUP_ID_RE.search(identifier) and _is_scheduled_job(job):
            return _check(
                "backup_schedule",
                True,
                SEVERITY_INFO,
                f"备份调度存在: {job.get('declarationKey') or job.get('name')}",
            )
    return _check(
        "backup_schedule",
        False,
        SEVERITY_ERROR,
        "未找到备份调度自动化（需带 cron/every 调度且标识含 backup）",
        "openclaw backup enable --every 24h（重复执行为更新）",
    )


# -- aggregate ---------------------------------------------------------------


def run_doctor(
    profile_name: str | None = None,
    *,
    runner: Runner | None = None,
    connect: Callable[[str, int], bool] | None = None,
) -> list[DoctorCheck]:
    """Run all doctor checks in a fixed order."""

    runner = runner or run_command
    live_jobs: list[dict[str, Any]] | None = None
    try:
        live_jobs = fetch_live_automations(runner)
    except RuntimeError:
        live_jobs = None  # dependent checks fetch themselves and report
    return [
        check_openclaw_version(runner),
        check_node_version(runner),
        check_linger(runner),
        check_gateway_port(connect=connect),
        check_nblane_mcp_registered(runner),
        check_weixin_plugin(runner),
        check_automations_in_sync(
            runner, profile_name=profile_name, live_jobs=live_jobs
        ),
        check_backup_schedule(runner, live_jobs=live_jobs),
    ]


def doctor_exit_code(checks: Sequence[DoctorCheck]) -> int:
    """0 when no error-severity check fails, else 1."""

    return (
        1
        if any(
            not check.ok and check.severity == SEVERITY_ERROR
            for check in checks
        )
        else 0
    )
