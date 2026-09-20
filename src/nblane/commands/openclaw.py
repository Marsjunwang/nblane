"""OpenClaw integration commands: doctor, automations-as-code sync, daily sync."""

from __future__ import annotations

import json
import shlex
import shutil
import sys
from pathlib import Path

from nblane.commands.common import _require_profile
from nblane.core.mcp_client_config import build_mcp_server_entry
from nblane.core.notify import (
    NotifyConfig,
    NotifyConfigError,
    build_payload,
    resolve_hook_token,
    resolve_hook_url,
    send_notification,
)
from nblane.core.openclaw_automations import (
    ACTION_ADD,
    ACTION_PRUNE_CANDIDATE,
    ACTION_UPDATE,
    Runner,
    apply_reconcile,
    automations_file_path,
    build_action_argv,
    compute_drift_summary,
    fetch_live_automations,
    load_automations_file,
    plan_reconcile,
    run_command,
    substitute_env_text,
)
from nblane.core.openclaw_corpus import (
    check_corpus_drift,
    default_out_dir,
    render_profile_corpus,
)
from nblane.core.openclaw_ops import (
    SEVERITY_ERROR,
    SEVERITY_WARNING,
    doctor_exit_code,
    run_doctor,
)
from nblane.core.paths import REPO_ROOT
from nblane.core.profile_io import list_profiles

_MARKS = {True: "[OK]", False: "[失败]"}
_MARK_WARNING = "[提醒]"

SKILLS_SRC_DIR = REPO_ROOT / "scripts" / "openclaw" / "skills"
PLUGIN_SRC_DIR = (
    REPO_ROOT / "scripts" / "openclaw" / "plugins" / "weixin-task-bridge"
)
OVERLAY_FILENAME = "openclaw.overlay.json5"


def _openclaw_home() -> Path:
    """Return the OpenClaw home directory (``~/.openclaw``)."""
    return Path.home() / ".openclaw"


def cmd_doctor(profile: str | None = None) -> None:
    """Run read-only OpenClaw health checks; exit 1 on any error failure."""

    checks = run_doctor(profile_name=profile)
    print("OpenClaw 体检：")
    for check in checks:
        if check.ok:
            mark = _MARKS[True]
        elif check.severity == SEVERITY_ERROR:
            mark = _MARKS[False]
        elif check.severity == SEVERITY_WARNING:
            mark = _MARK_WARNING
        else:
            mark = "[信息]"
        print(f"{mark} {check.id}: {check.detail}")
        if not check.ok and check.hint:
            print(f"     提示: {check.hint}")
    code = doctor_exit_code(checks)
    print("体检通过。" if code == 0 else "存在失败项，请按提示修复后重试。")
    sys.exit(code)


def cmd_automations_sync(
    name: str,
    *,
    apply: bool = False,
    prune: bool = False,
    runner: Runner | None = None,
) -> None:
    """Reconcile assistant/automations.yaml with the live gateway.

    Default is dry-run: print the plan and the exact commands without
    executing anything. ``--apply`` executes add/edit; ``--prune``
    additionally removes undeclared ``nblane:`` jobs.
    """

    _require_profile(name)
    path = automations_file_path(name)
    if not path.is_file():
        print(
            f"ERROR: 未找到 {path}\n"
            f"参考 profiles/template/assistant/automations.yaml 创建声明文件。",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        specs = load_automations_file(path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    runner = runner or run_command
    try:
        live_jobs = fetch_live_automations(runner)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    plan = plan_reconcile(specs, live_jobs)
    print(compute_drift_summary(plan))

    drift = sum(1 for a in plan if a.kind in (ACTION_ADD, ACTION_UPDATE))
    prunes = sum(1 for a in plan if a.kind == ACTION_PRUNE_CANDIDATE)

    if prune and not apply:
        print(
            "[提醒] --prune 只在 --apply 时生效；当前 dry-run 不会删除任何任务。",
            file=sys.stderr,
        )

    if not apply:
        planned = [
            (action, argv)
            for action in plan
            if (argv := build_action_argv(action)) is not None
        ]
        if planned:
            print("\n将执行的命令（dry-run，未执行）：")
            for action, argv in planned:
                note = (
                    "（需 --prune）"
                    if action.kind == ACTION_PRUNE_CANDIDATE and not prune
                    else ""
                )
                print(f"  $ {shlex.join(argv)} {note}".rstrip())
        print("\ndry-run：未做任何变更。确认后加 --apply 执行。")
        if prunes and not prune:
            print(f"有 {prunes} 个待清理任务；--apply --prune 才会删除。")
        sys.exit(1 if drift else 0)

    results = apply_reconcile(plan, runner, dry_run=False, include_prune=prune)
    failed = 0
    executed = 0
    for result in results:
        if not result.executed:
            continue
        executed += 1
        if result.ok:
            print(f"[OK] {result.action.kind} {result.action.key}")
        else:
            failed += 1
            print(
                f"[失败] {result.action.kind} {result.action.key}: "
                f"{result.output or '命令失败'}",
                file=sys.stderr,
            )
    if prunes and not prune:
        print(f"仍有 {prunes} 个待清理任务未删除（--prune 才删除）。")
    print(f"已执行 {executed} 项变更，失败 {failed} 项。")
    sys.exit(1 if failed else 0)


# -- daily sync ---------------------------------------------------------------


def _resolve_sync_profile(profile: str | None) -> str:
    """Return *profile*, or the single existing profile when omitted."""
    if profile:
        return profile
    names = list_profiles()
    if len(names) == 1:
        return names[0]
    if names:
        detail = f"（现有: {', '.join(names)}）"
    else:
        detail = "（尚无 profile，先运行 nblane init <name>）"
    print(f"ERROR: 请用 --profile 指定 profile {detail}", file=sys.stderr)
    sys.exit(1)


def _iter_skill_files(src: Path) -> list[Path]:
    """List files under *src* (sorted), excluding ``__pycache__``."""
    return [
        path
        for path in sorted(src.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    ]


def _sync_corpus(profile: str, out_dir: Path, *, check: bool) -> bool:
    """Render or diff the memory corpus; return True when drifted."""
    if check:
        drifted = check_corpus_drift(profile, out_dir=out_dir)
        if drifted:
            print(f"[检查] 语料漂移（{out_dir}）：")
            for name in drifted:
                print(f"  ~ {name}")
            return True
        print(f"[OK] 语料一致（{out_dir}）")
        return False
    result = render_profile_corpus(profile, out_dir=out_dir)
    print(f"语料渲染 → {result.out_dir}")
    for path in result.written:
        print(f"  [写入] {path.name}")
    for path in result.removed:
        print(f"  [删除] {path.name}（源已移除，清理过期产物）")
    for reason in result.skipped:
        print(f"  [跳过] {reason}")
    return False


def _stale_skill_files(src: Path, dst: Path, files: list[Path]) -> list[Path]:
    """Files under *dst* managed by this sync but absent from *src*.

    Ownership is scoped to the top-level entries present in *src* (e.g.
    ``codex-dev/``, ``kimi-dev/``, ``bin/``): anything else in *dst* is a
    foreign skill tree and is never reported or removed.
    """
    if not dst.is_dir():
        return []
    src_rels = {path.relative_to(src) for path in files}
    managed_roots = {rel.parts[0] for rel in src_rels}
    stale: list[Path] = []
    for path in sorted(dst.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(dst)
        if rel in src_rels or rel.parts[0] not in managed_roots:
            continue
        stale.append(rel)
    return stale


def _remove_empty_skill_dirs(dst: Path, managed_roots: set[str]) -> None:
    """Remove directories left empty by stale-file cleanup (never *dst*)."""
    dirs = sorted(
        (path for path in dst.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for path in dirs:
        if path.relative_to(dst).parts[0] not in managed_roots:
            continue
        if not any(path.iterdir()):
            path.rmdir()


def _sync_skills(src: Path, dst: Path, *, check: bool) -> bool:
    """Copy (or diff) the repo skills tree into the workspace skills dir.

    Sync is no longer add-only: files under the managed top-level entries
    that disappeared from *src* are deleted (reported as ``-`` drift in
    ``--check`` mode). Foreign skill trees in *dst* stay untouched.
    """
    files = _iter_skill_files(src)
    if not files:
        print(f"{_MARK_WARNING} 技能源目录为空: {src}")
    drift = False
    wrote = 0
    removed = 0
    label = "[检查] 技能对账" if check else "技能同步"
    print(f"{label} {src} → {dst}")
    for path in files:
        rel = path.relative_to(src)
        target = dst / rel
        if not target.exists():
            action = "+"
            drift = True
        elif path.read_bytes() != target.read_bytes():
            action = "~"
            drift = True
        else:
            action = "="
        if action != "=":
            print(f"  {action} {rel}")
        if not check and action != "=":
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            wrote += 1
    stale = _stale_skill_files(src, dst, files)
    for rel in stale:
        drift = True
        print(f"  - {rel}")
        if not check:
            (dst / rel).unlink()
            removed += 1
    if not check and stale:
        managed_roots = {path.relative_to(src).parts[0] for path in files}
        _remove_empty_skill_dirs(dst, managed_roots)
    if check:
        if drift:
            return True
        print(f"  = 全部一致（{len(files)} 个文件）")
        return False
    print(f"  共 {len(files)} 个文件，写入 {wrote} 个，删除 {removed} 个。")
    return False


def _sync_automations(profile: str, runner: Runner, *, check: bool) -> bool:
    """Plan-only automations reconcile; return True when drifted."""
    path = automations_file_path(profile)
    if not path.is_file():
        print(f"[提醒] 未找到 {path}，跳过自动化对账。")
        return False
    try:
        specs = load_automations_file(path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    try:
        live_jobs = fetch_live_automations(runner)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    plan = plan_reconcile(specs, live_jobs)
    print(compute_drift_summary(plan))
    drift = any(a.kind in (ACTION_ADD, ACTION_UPDATE) for a in plan)
    if drift and not check:
        print(
            f"自动化存在漂移；本命令不做变更，"
            f"请运行 nblane openclaw automations sync {profile} --apply。"
        )
    return drift


def cmd_sync(
    profile: str | None = None,
    *,
    check: bool = False,
    corpus_out_dir: Path | None = None,
    skills_src: Path | None = None,
    openclaw_home: Path | None = None,
    runner: Runner | None = None,
) -> None:
    """Daily drift reconcile: corpus render, skills copy, automations plan.

    Default mode writes the derived artifacts (memory corpus, skills tree)
    and prunes their stale counterparts — generated corpus files whose
    sources disappeared and skills files under the managed top-level
    entries that are gone from the repo tree (foreign trees in the
    workspace stay untouched). Automations changes are never applied here —
    those stay plan-only and point at ``nblane openclaw automations sync
    --apply``.  ``--check`` writes nothing and exits 1 when any of the
    three sections drifted, stale files included (aligning with ``nblane
    sync --check``).  Write mode also exits 1 on remaining automations
    drift, matching the dry-run convention.
    """
    home = Path(openclaw_home) if openclaw_home is not None else _openclaw_home()
    if not home.is_dir():
        print(
            f"ERROR: 未找到 {home} —— 本机尚未安装 OpenClaw。\n"
            f"先按接入指南安装 OpenClaw，再运行 nblane openclaw doctor 体检。",
            file=sys.stderr,
        )
        sys.exit(1)
    profile = _resolve_sync_profile(profile)
    _require_profile(profile)

    out_dir = (
        Path(corpus_out_dir) if corpus_out_dir is not None else default_out_dir()
    )
    src = Path(skills_src) if skills_src is not None else SKILLS_SRC_DIR
    dst = home / "workspace" / "skills"

    drift = False
    drift |= _sync_corpus(profile, out_dir, check=check)
    drift |= _sync_skills(src, dst, check=check)
    drift |= _sync_automations(profile, runner or run_command, check=check)

    if check:
        print("存在漂移。" if drift else "全部一致。")
    sys.exit(1 if drift else 0)


# -- install (one-command setup, plan §5.4) -----------------------------------


def _build_overlay_patches(
    overlay_text: str, mcp_entry: dict
) -> list[tuple[str, str]]:
    """Build ``config patch`` payloads with the nblane MCP entry merged in.

    The overlay is JSON5 and the repo has no JSON5 parser.  When the overlay
    happens to be pure JSON (a valid JSON5 subset — the shipped template is),
    the MCP entry is merged in memory and a single patch is emitted.
    Otherwise the overlay is passed through verbatim as the first patch and
    a generated JSON patch carrying only ``mcp.servers.nblane`` follows;
    ``openclaw config patch`` merges recursively, so the two compose.
    Returns ``(label, payload)`` pairs in application order.
    """

    try:
        data = json.loads(overlay_text)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict):
        mcp = data.get("mcp")
        if not isinstance(mcp, dict):
            mcp = {}
            data["mcp"] = mcp
        servers = mcp.get("servers")
        if not isinstance(servers, dict):
            servers = {}
            mcp["servers"] = servers
        servers["nblane"] = mcp_entry
        payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        return [("overlay + MCP 注入（合并为单补丁）", payload)]
    mcp_payload = (
        json.dumps(
            {"mcp": {"servers": {"nblane": mcp_entry}}},
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    return [
        ("overlay 原文（非纯 JSON，原样透传）", overlay_text),
        ("MCP 注入（生成的 JSON 补丁）", mcp_payload),
    ]


def _install_plugin(plugin_src: Path, runner: Runner, *, apply: bool) -> bool:
    """Step 2: install the weixin-task-bridge plugin; True on success/skip."""

    if not plugin_src.is_dir():
        print(f"[跳过] 未找到插件目录 {plugin_src}，跳过插件安装。")
        return True
    argv = [
        "openclaw",
        "plugins",
        "install",
        str(plugin_src.resolve()),
        "--force",
        "--accept-capabilities",
    ]
    if not apply:
        print(f"  $ {shlex.join(argv)}  （dry-run，未执行）")
        return True
    result = runner(argv)
    if result.ok:
        print("[OK] 插件安装完成（幂等，重跑即更新）。")
        return True
    print(
        f"[失败] 插件安装失败: {result.output or f'exit {result.returncode}'}",
        file=sys.stderr,
    )
    return False


def _install_overlay(
    profile: str, overlay_path: Path, runner: Runner, *, apply: bool
) -> bool:
    """Step 3: patch the config overlay (+ MCP entry) into the gateway.

    ``${VAR}`` references in the overlay are substituted from the
    environment (same semantics as the automations loader: an unset variable
    is an error, never patched through verbatim).
    """

    if not overlay_path.is_file():
        print(
            f"[跳过] 未找到 {overlay_path}，跳过配置 overlay"
            f"（MCP 注入也随之跳过）。"
        )
        return True
    try:
        overlay_text = substitute_env_text(
            overlay_path.read_text(encoding="utf-8"), where=str(overlay_path)
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return False
    mcp_entry = build_mcp_server_entry(profile)
    patches = _build_overlay_patches(overlay_text, mcp_entry)
    ok = True
    for label, payload in patches:
        argv = ["openclaw", "config", "patch", "--stdin"]
        if not apply:
            argv.append("--dry-run")
        print(f"  $ {shlex.join(argv)}  # stdin: {label}")
        indented = "\n".join(f"    {line}" for line in payload.rstrip().splitlines())
        print(indented)
        result = runner(argv, input=payload)
        if result.ok:
            note = "校验通过（dry-run）" if not apply else "已应用"
            print(f"  [OK] config patch {note}。")
        else:
            ok = False
            print(
                f"  [失败] config patch 失败: "
                f"{result.output or f'exit {result.returncode}'}",
                file=sys.stderr,
            )
    return ok


def _install_automations(profile: str, runner: Runner, *, apply: bool) -> bool:
    """Step 4: automations reconcile; plan-only unless *apply*."""

    path = automations_file_path(profile)
    if not path.is_file():
        print(f"[跳过] 未找到 {path}，跳过自动化对账。")
        return True
    try:
        specs = load_automations_file(path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return False
    try:
        live_jobs = fetch_live_automations(runner)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return False
    plan = plan_reconcile(specs, live_jobs)
    print(compute_drift_summary(plan))

    if not apply:
        planned = [
            (action, argv)
            for action in plan
            if (argv := build_action_argv(action)) is not None
        ]
        if planned:
            print("将执行的命令（dry-run，未执行）：")
            for action, argv in planned:
                note = "（不会自动删除）" if action.kind == ACTION_PRUNE_CANDIDATE else ""
                print(f"  $ {shlex.join(argv)} {note}".rstrip())
        print("dry-run：未执行自动化变更；--apply 执行 add/edit（不含删除）。")
        return True

    results = apply_reconcile(plan, runner, dry_run=False, include_prune=False)
    failed = 0
    for result in results:
        if not result.executed:
            continue
        if result.ok:
            print(f"[OK] {result.action.kind} {result.action.key}")
        else:
            failed += 1
            print(
                f"[失败] {result.action.kind} {result.action.key}: "
                f"{result.output or '命令失败'}",
                file=sys.stderr,
            )
    return failed == 0


def cmd_install(
    profile: str | None = None,
    *,
    apply: bool = False,
    runner: Runner | None = None,
    openclaw_home: Path | None = None,
    corpus_out_dir: Path | None = None,
    skills_src: Path | None = None,
    plugin_dir: Path | None = None,
) -> None:
    """One-command idempotent OpenClaw setup (plan §5.4).

    Default is ``--dry-run``: print the full action plan and change nothing
    (skills/corpus are diffed, the config patch runs with its own
    ``--dry-run``, plugin install and automations mutations are printed
    only).  ``--apply`` executes every step.  Steps whose inputs are missing
    (plugin dir, overlay, automations file) are skipped with a note.
    Automations are never pruned here — deletion stays behind
    ``nblane openclaw automations sync --apply --prune``.
    """

    home = Path(openclaw_home) if openclaw_home is not None else _openclaw_home()
    if not home.is_dir():
        print(
            f"ERROR: 未找到 {home} —— 本机尚未安装 OpenClaw。\n"
            f"先按接入指南安装 OpenClaw，再运行 nblane openclaw doctor 体检。",
            file=sys.stderr,
        )
        sys.exit(1)
    profile = _resolve_sync_profile(profile)
    _require_profile(profile)
    runner = runner or run_command

    out_dir = (
        Path(corpus_out_dir) if corpus_out_dir is not None else default_out_dir()
    )
    src = Path(skills_src) if skills_src is not None else SKILLS_SRC_DIR
    dst = home / "workspace" / "skills"
    plugin_src = Path(plugin_dir) if plugin_dir is not None else PLUGIN_SRC_DIR

    mode = "apply" if apply else "dry-run"
    print(f"OpenClaw 一键安装（{mode}）：profile={profile}")

    print("\n[1/4] 技能与记忆语料")
    if apply:
        _sync_corpus(profile, out_dir, check=False)
        _sync_skills(src, dst, check=False)
    else:
        print("（dry-run：只报告差异，不写入；--apply 时写入）")
        _sync_corpus(profile, out_dir, check=True)
        _sync_skills(src, dst, check=True)

    print("\n[2/4] weixin-task-bridge 插件")
    ok = _install_plugin(plugin_src, runner, apply=apply)

    print("\n[3/4] 配置 overlay + nblane MCP 注入")
    overlay_path = automations_file_path(profile).parent / OVERLAY_FILENAME
    ok &= _install_overlay(profile, overlay_path, runner, apply=apply)

    print("\n[4/4] 自动化对账")
    ok &= _install_automations(profile, runner, apply=apply)

    print("\n提示：安装完成后运行 nblane openclaw doctor 体检。")
    if not apply:
        print("当前为 dry-run：除自动化的只读对账与 config patch --dry-run 外，未做任何变更。")
        print("确认后加 --apply 执行。")
    sys.exit(0 if ok else 1)


# -- notify (reverse push) ----------------------------------------------------


def cmd_notify(
    text: str,
    *,
    dry_run: bool = False,
    http_post=None,
) -> None:
    """Push *text* to WeChat via the OpenClaw inbound webhook.

    ``--dry-run`` prints the URL and payload without sending and never
    requires the token. Exit code: 0 on success, 1 otherwise.
    """
    if dry_run:
        print(f"[dry-run] POST {resolve_hook_url()}")
        print(
            "[dry-run] payload: "
            + json.dumps(build_payload(text), ensure_ascii=False)
        )
        token_state = "已配置" if resolve_hook_token() else "未设置"
        print(f"[dry-run] token: {token_state}（永不打印明文）")
        print("dry-run：未发送。")
        return
    try:
        config = NotifyConfig.from_env()
    except NotifyConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    result = send_notification(text, config=config, http_post=http_post)
    if result["ok"]:
        print(f"[OK] 已推送（HTTP {result['status']}）。")
        sys.exit(0)
    print(f"[失败] 推送失败：{result['error']}", file=sys.stderr)
    sys.exit(1)


__all__ = [
    "cmd_automations_sync",
    "cmd_doctor",
    "cmd_install",
    "cmd_notify",
    "cmd_sync",
]
