"""OpenClaw automations-as-code: declare, reconcile, apply.

``profiles/<name>/assistant/automations.yaml`` is the declarative source of
truth for the OpenClaw jobs that nblane manages.  nblane only ever touches
jobs whose ``declarationKey`` starts with ``nblane:`` — system jobs and
hand-made jobs (for example ``personal-assistant:*``) are reported as
``skip_foreign`` and never modified.

Migration path for existing foreign jobs (plan §5.2): either rename the key
to the ``nblane:`` prefix, or declare the existing key with ``adopt: true``.
An adopted key is managed exactly like an ``nblane:`` key while declared —
add/update/keep as usual — and is eligible for prune candidacy (callers pass
``adopted_keys`` to :func:`plan_reconcile` when the declaration was removed;
by default the adopted keys of the current specs are used).  Adoption is a
deliberate, per-entry opt-in: a foreign key without ``adopt: true`` is a
loader error, never silently taken over.

Safety rules baked in here:

- Every ``openclaw`` invocation goes through an injectable *runner* callable
  (``Callable[[list[str]], CommandResult]``), so tests never spawn the real
  CLI and production runs can be audited command by command.
- :func:`apply_reconcile` defaults to ``dry_run=True`` and never executes
  ``prune_candidate`` actions unless ``include_prune=True`` — undeclared
  ``nblane:`` jobs are reported, never auto-deleted.

Drift semantics: ``cron`` / ``tz`` / ``session`` / delivery / message are
always compared; ``model`` / ``fallbacks`` / ``timeout_seconds`` are only
compared when the declaration sets them, so gateway-side defaults do not
oscillate the plan.  Message comparison strips surrounding whitespace so a
trailing newline in the prompt file does not cause permanent drift.

The ``automations edit`` / ``automations rm`` flag surface is assumed to
accept ``--declaration-key`` as the selector plus the same field flags as
``automations add`` (only ``add`` was verified end-to-end against OpenClaw
2026.9.4).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import yaml

from nblane.core.paths import REPO_ROOT
from nblane.core.profile_io import safe_profile_dir
from nblane.core.yaml_io import fast_safe_load

MANAGED_KEY_PREFIX = "nblane:"
ASSISTANT_DIRNAME = "assistant"
AUTOMATIONS_FILENAME = "automations.yaml"
SCHEMA_VERSION = 1

ACTION_ADD = "add"
ACTION_UPDATE = "update"
ACTION_KEEP = "keep"
ACTION_SKIP_FOREIGN = "skip_foreign"
ACTION_PRUNE_CANDIDATE = "prune_candidate"
ACTION_KINDS = (
    ACTION_ADD,
    ACTION_UPDATE,
    ACTION_KEEP,
    ACTION_PRUNE_CANDIDATE,
    ACTION_SKIP_FOREIGN,
)
_KIND_ORDER = {kind: rank for rank, kind in enumerate(ACTION_KINDS)}
_KIND_LABELS = {
    ACTION_ADD: "新增",
    ACTION_UPDATE: "更新",
    ACTION_KEEP: "一致",
    ACTION_PRUNE_CANDIDATE: "待清理",
    ACTION_SKIP_FOREIGN: "外部跳过",
}
_KIND_MARKS = {
    ACTION_ADD: "+",
    ACTION_UPDATE: "~",
    ACTION_KEEP: "=",
    ACTION_PRUNE_CANDIDATE: "!",
    ACTION_SKIP_FOREIGN: "·",
}

_TOP_LEVEL_KEYS = {"version", "defaults", "automations"}
_DEFAULTS_KEYS = {
    "tz",
    "model",
    "fallbacks",
    "session",
    "timeout_seconds",
    "deliver",
}
_DELIVER_KEYS = {"channel", "to"}
_AUTOMATION_KEYS = {
    "key",
    "name",
    "cron",
    "prompt",
    "tz",
    "session",
    "model",
    "fallbacks",
    "timeout_seconds",
    "deliver",
    "adopt",
}
_REQUIRED_ENTRY_KEYS = ("key", "cron", "prompt")
_SESSIONS = ("isolated", "main")

_ENV_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

Runner = Callable[..., "CommandResult"]


# -- runner ------------------------------------------------------------------


@dataclass(frozen=True)
class CommandResult:
    """Minimal result of one external command invocation."""

    ok: bool
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def output(self) -> str:
        """Return combined stdout/stderr for error messages."""

        return "\n".join(
            part for part in (self.stdout.strip(), self.stderr.strip()) if part
        ).strip()


def run_command(
    argv: Sequence[str],
    *,
    input: str | None = None,
    timeout: float = 15.0,
) -> CommandResult:
    """Run *argv* with captured output; never raises for missing binaries.

    ``input`` is fed to the process's stdin (used by
    ``openclaw config patch --stdin``).
    """

    try:
        proc = subprocess.run(
            list(argv),
            input=input,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return CommandResult(
            ok=False,
            returncode=127,
            stderr=f"command not found: {argv[0]}",
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            ok=False,
            returncode=124,
            stderr=f"timeout after {timeout}s: {argv[0]}",
        )
    return CommandResult(
        ok=proc.returncode == 0,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


# -- dataclasses -------------------------------------------------------------


@dataclass(frozen=True)
class AutomationSpec:
    """One declared automation, defaults merged and prompt resolved."""

    key: str
    name: str
    cron: str
    tz: str
    session: str
    model: str
    fallbacks: tuple[str, ...]
    timeout_seconds: int | None
    deliver_channel: str
    deliver_to: str
    prompt_text: str
    adopted: bool = False


@dataclass(frozen=True)
class ReconcileAction:
    """One planned reconcile step; ``spec`` is set for add/update/keep."""

    kind: str
    key: str
    reason: str
    spec: AutomationSpec | None = None


@dataclass(frozen=True)
class ApplyResult:
    """Outcome of one action; ``executed`` is False in dry-run mode."""

    action: ReconcileAction
    argv: tuple[str, ...]
    executed: bool
    ok: bool
    output: str = ""


# -- paths -------------------------------------------------------------------


def automations_file_path(name_or_dir: str | Path) -> Path:
    """Return ``profiles/<name>/assistant/automations.yaml`` (or a dir-based path)."""

    if isinstance(name_or_dir, Path):
        return name_or_dir / ASSISTANT_DIRNAME / AUTOMATIONS_FILENAME
    return safe_profile_dir(name_or_dir) / ASSISTANT_DIRNAME / AUTOMATIONS_FILENAME


# -- loader ------------------------------------------------------------------


def _default_env() -> Mapping[str, str]:
    """Return the process environment with the repo ``.env`` layered in."""

    try:
        from dotenv import load_dotenv

        load_dotenv(REPO_ROOT / ".env", override=False)
    except ImportError:
        pass
    return os.environ


def _unknown_keys(mapping: Mapping[str, Any], allowed: set[str], where: str) -> None:
    unknown = sorted(str(k) for k in mapping if k not in allowed)
    if unknown:
        raise ValueError(
            f"{where}: unknown keys: {', '.join(unknown)} "
            f"(allowed: {', '.join(sorted(allowed))})"
        )


def _substitute_env(value: Any, env: Mapping[str, str], where: str) -> Any:
    """Replace ``${VAR}`` references in strings; fail loudly when unset."""

    if isinstance(value, str):

        def _replace(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in env:
                raise ValueError(
                    f"{where}: environment variable ${{{name}}} is not set"
                )
            return env[name]

        return _ENV_REF_RE.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _substitute_env(v, env, where) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env(item, env, where) for item in value]
    return value


def substitute_env_text(
    text: str,
    *,
    env: Mapping[str, str] | None = None,
    where: str = "text",
) -> str:
    """Replace ``${VAR}`` references in raw *text*; fail loudly when unset.

    Same semantics as the ``automations.yaml`` loader (``_substitute_env``):
    an unset variable raises ``ValueError``.  *env* defaults to the process
    environment with the repo ``.env`` layered in (``_default_env``).  Used by
    the OpenClaw install overlay path, where the payload is raw JSON5 text
    that cannot be parsed before substitution.
    """

    env_map = _default_env() if env is None else env
    return _substitute_env(text, env_map, where)


def _require_str(value: Any, field: str, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}: field '{field}' must be a non-empty string")
    return value.strip()


def _optional_str(value: Any, field: str, where: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{where}: field '{field}' must be a string")
    return value.strip()


def _parse_fallbacks(value: Any, where: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValueError(f"{where}: field 'fallbacks' must be a list of strings")
    return tuple(item.strip() for item in value)


def _parse_timeout(value: Any, where: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(
            f"{where}: field 'timeout_seconds' must be a positive integer"
        )
    return value


def _parse_adopt(value: Any, where: str) -> bool:
    if value is None:
        return False
    if not isinstance(value, bool):
        raise ValueError(f"{where}: field 'adopt' must be a boolean")
    return value


def _parse_deliver(value: Any, where: str) -> tuple[str, str]:
    """Return (channel, to); both empty means delivery ``none``."""

    if value is None:
        return "", ""
    if not isinstance(value, dict):
        raise ValueError(f"{where}: field 'deliver' must be a mapping")
    _unknown_keys(value, _DELIVER_KEYS, f"{where}.deliver")
    channel = _optional_str(value.get("channel"), "channel", f"{where}.deliver")
    to = _optional_str(value.get("to"), "to", f"{where}.deliver")
    if bool(channel) != bool(to):
        raise ValueError(
            f"{where}.deliver: 'channel' and 'to' must be set together"
        )
    return channel, to


def _resolve_prompt(base_dir: Path, prompt_rel: str, where: str) -> str:
    """Read the prompt file relative to the automations file directory."""

    candidate = (base_dir / prompt_rel).resolve()
    try:
        candidate.relative_to(base_dir)
    except ValueError as exc:
        raise ValueError(
            f"{where}: prompt path '{prompt_rel}' escapes the assistant directory"
        ) from exc
    if not candidate.is_file():
        raise ValueError(f"{where}: prompt file not found: {prompt_rel}")
    return candidate.read_text(encoding="utf-8")


def load_automations_file(
    path: str | Path,
    *,
    env: Mapping[str, str] | None = None,
) -> list[AutomationSpec]:
    """Load and strictly validate an ``automations.yaml`` declaration file.

    Unknown keys, missing required fields, foreign (non-``nblane:``) keys
    without ``adopt: true``, escaping prompt paths, and unset ``${VAR}``
    references all raise ``ValueError``.
    """

    path = Path(path)
    if not path.is_file():
        raise ValueError(f"automations file not found: {path}")
    try:
        raw = fast_safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: document must be a mapping")
    _unknown_keys(raw, _TOP_LEVEL_KEYS, str(path))
    if raw.get("version") != SCHEMA_VERSION:
        raise ValueError(
            f"{path}: field 'version' must be {SCHEMA_VERSION}, "
            f"got {raw.get('version')!r}"
        )

    defaults = raw.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise ValueError(f"{path}: field 'defaults' must be a mapping")
    _unknown_keys(defaults, _DEFAULTS_KEYS, f"{path} defaults")

    entries = raw.get("automations")
    if not isinstance(entries, list):
        raise ValueError(f"{path}: field 'automations' must be a list")

    env_map = _default_env() if env is None else env
    base_dir = path.resolve().parent
    specs: list[AutomationSpec] = []
    seen_keys: set[str] = set()
    for index, entry in enumerate(entries):
        where = f"automations[{index}]"
        if not isinstance(entry, dict):
            raise ValueError(f"{where}: each automation must be a mapping")
        _unknown_keys(entry, _AUTOMATION_KEYS, where)
        for required in _REQUIRED_ENTRY_KEYS:
            if required not in entry:
                raise ValueError(
                    f"{where}: missing required field '{required}'"
                )

        merged: dict[str, Any] = {**defaults, **entry}
        merged = {
            str(k): _substitute_env(v, env_map, f"{where}.{k}")
            for k, v in merged.items()
        }

        key = _require_str(merged.get("key"), "key", where)
        adopt = _parse_adopt(merged.get("adopt"), where)
        if not key.startswith(MANAGED_KEY_PREFIX) and not adopt:
            raise ValueError(
                f"{where}: key '{key}' must start with "
                f"'{MANAGED_KEY_PREFIX}' (nblane only manages its own jobs), "
                f"or set 'adopt: true' to take over this existing job"
            )
        adopted = adopt and not key.startswith(MANAGED_KEY_PREFIX)
        if key in seen_keys:
            raise ValueError(f"{where}: duplicate key '{key}'")
        seen_keys.add(key)

        name = _optional_str(merged.get("name"), "name", where)
        cron = _require_str(merged.get("cron"), "cron", where)
        if len(cron.split()) != 5:
            raise ValueError(
                f"{where}: cron '{cron}' must have 5 fields"
            )
        tz = _require_str(merged.get("tz"), "tz", where)
        session = _optional_str(merged.get("session"), "session", where)
        if session not in _SESSIONS:
            raise ValueError(
                f"{where}: session must be one of {_SESSIONS}, got {session!r}"
            )
        model = _optional_str(merged.get("model"), "model", where)
        fallbacks = _parse_fallbacks(merged.get("fallbacks"), where)
        timeout_seconds = _parse_timeout(merged.get("timeout_seconds"), where)
        channel, to = _parse_deliver(merged.get("deliver"), where)
        if session == "main":
            # OpenClaw 2026.9: main-session jobs are system events — the
            # gateway rejects announce delivery and silently drops the
            # agent-turn fields (model/fallbacks/timeoutSeconds). Normalize
            # all of them away to keep reconcile drift-free.
            channel, to = "", ""
            model, fallbacks, timeout_seconds = "", (), None
        prompt_text = _resolve_prompt(
            base_dir, _require_str(merged.get("prompt"), "prompt", where), where
        )

        specs.append(
            AutomationSpec(
                key=key,
                name=name or key.split(":", 1)[-1],
                cron=cron,
                tz=tz,
                session=session,
                model=model,
                fallbacks=fallbacks,
                timeout_seconds=timeout_seconds,
                deliver_channel=channel,
                deliver_to=to,
                prompt_text=prompt_text,
                adopted=adopted,
            )
        )
    return specs


# -- live state --------------------------------------------------------------


def fetch_live_automations(runner: Runner) -> list[dict[str, Any]]:
    """Return ``openclaw automations list --all --json`` as raw mappings."""

    result = runner(["openclaw", "automations", "list", "--all", "--json"])
    if not result.ok:
        raise RuntimeError(
            "openclaw automations list failed: "
            f"{result.output or f'exit {result.returncode}'}"
        )
    try:
        data = json.loads(result.stdout or "")
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "cannot parse `openclaw automations list --all --json` output "
            f"as JSON: {exc}"
        ) from exc
    if isinstance(data, dict):
        # Older CLI wraps in "automations"; OpenClaw 2026.9 uses "jobs".
        data = data.get("automations") or data.get("jobs") or []
    if not isinstance(data, list):
        raise RuntimeError(
            "unexpected `automations list --json` shape: expected a list"
        )
    return [job for job in data if isinstance(job, dict)]


def _normalize_live_job(job: Mapping[str, Any]) -> dict[str, Any]:
    """Flatten one live job mapping into the fields reconcile compares."""

    schedule = job.get("schedule")
    cron = tz = ""
    if isinstance(schedule, Mapping):
        # Newer CLI: {"kind": "cron", "expr": ...} / {"kind": "every", "everyMs": ...}
        cron = str(
            schedule.get("cron") or schedule.get("every") or schedule.get("expr") or ""
        )
        tz = str(schedule.get("tz") or "")
    elif isinstance(schedule, str):
        cron = schedule
    tz = tz or str(job.get("tz") or "")

    delivery = job.get("delivery")
    announce = False
    channel = to = ""
    if isinstance(delivery, Mapping):
        mode = str(delivery.get("mode") or "").strip().lower()
        announce = mode == "announce" or delivery.get("announce") is True
        channel = str(delivery.get("channel") or "")
        to = str(delivery.get("to") or "")
    elif isinstance(delivery, str):
        announce = delivery.strip().lower() == "announce"
    channel = channel or str(job.get("channel") or "")
    to = to or str(job.get("to") or "")

    fallbacks_raw = job.get("fallbacks") or []
    timeout_raw = job.get("timeoutSeconds")
    payload = job.get("payload")
    if not isinstance(payload, Mapping):
        payload = {}
    # 2026.9 nests agent-turn fields (model/fallbacks/timeoutSeconds) and the
    # message text inside the payload object.
    model = str(job.get("model") or payload.get("model") or "")
    if not fallbacks_raw and isinstance(payload.get("fallbacks"), list):
        fallbacks_raw = payload["fallbacks"]
    if timeout_raw is None:
        timeout_raw = payload.get("timeoutSeconds")
    return {
        "key": str(job.get("declarationKey") or job.get("name") or ""),
        "cron": cron,
        "tz": tz,
        "session": str(job.get("session") or job.get("sessionTarget") or ""),
        "model": model,
        "fallbacks": [str(item) for item in fallbacks_raw]
        if isinstance(fallbacks_raw, list)
        else [],
        "timeout_seconds": timeout_raw if isinstance(timeout_raw, int) else None,
        "announce": announce,
        "channel": channel,
        "to": to,
        "message": str(
            job.get("message")
            or job.get("prompt")
            # 2026.9 nests the payload: agentTurn.message / systemEvent.text
            or payload.get("message")
            or payload.get("text")
            or ""
        ),
    }


def _drifted_fields(spec: AutomationSpec, live: Mapping[str, Any]) -> list[str]:
    """Return the compared field names where the live job differs."""

    drifted: list[str] = []
    if live["cron"] != spec.cron:
        drifted.append("cron")
    if live["tz"] != spec.tz:
        drifted.append("tz")
    if live["session"] != spec.session:
        drifted.append("session")
    live_announce = live["announce"] or bool(live["channel"])
    if live_announce != bool(spec.deliver_channel):
        drifted.append("delivery")
    elif spec.deliver_channel and (
        live["channel"] != spec.deliver_channel or live["to"] != spec.deliver_to
    ):
        drifted.append("delivery")
    if live["message"].strip() != spec.prompt_text.strip():
        drifted.append("message")
    if spec.model and live["model"] != spec.model:
        drifted.append("model")
    if spec.fallbacks and live["fallbacks"] != list(spec.fallbacks):
        drifted.append("fallbacks")
    if spec.timeout_seconds is not None and (
        live["timeout_seconds"] != spec.timeout_seconds
    ):
        drifted.append("timeout_seconds")
    return drifted


def plan_reconcile(
    specs: Sequence[AutomationSpec],
    live_jobs: Sequence[Mapping[str, Any]],
    *,
    adopted_keys: Iterable[str] | None = None,
) -> list[ReconcileAction]:
    """Plan reconciliation; pure and deterministic.

    Declared-only → ``add``; both sides but drifted → ``update``; identical
    → ``keep``; live ``nblane:`` jobs with no declaration →
    ``prune_candidate`` (never auto-deleted); anything else →
    ``skip_foreign`` (never touched).  Output is sorted by kind then key.

    Adopted (foreign-but-``adopt: true``) keys are managed exactly like
    ``nblane:`` keys while declared.  *adopted_keys* controls their prune
    candidacy after the declaration is removed: pass the previously adopted
    key set to have those live jobs reported as ``prune_candidate`` instead
    of reverting to ``skip_foreign``.  Defaults to the adopted keys of the
    current *specs* (so a key still declared is never pruned anyway).
    """

    if adopted_keys is None:
        adopted = {spec.key for spec in specs if spec.adopted}
    else:
        adopted = set(adopted_keys)

    live_by_key: dict[str, dict[str, Any]] = {}
    for job in live_jobs:
        view = _normalize_live_job(job)
        live_by_key.setdefault(view["key"], view)

    actions: list[ReconcileAction] = []
    declared: set[str] = set()
    for spec in specs:
        declared.add(spec.key)
        live = live_by_key.get(spec.key)
        if live is None:
            actions.append(
                ReconcileAction(
                    ACTION_ADD, spec.key, "声明存在但运行时缺失", spec
                )
            )
            continue
        drifted = _drifted_fields(spec, live)
        if drifted:
            actions.append(
                ReconcileAction(
                    ACTION_UPDATE,
                    spec.key,
                    "字段漂移: " + ", ".join(drifted),
                    spec,
                )
            )
        else:
            actions.append(
                ReconcileAction(ACTION_KEEP, spec.key, "与声明一致", spec)
            )

    for key in live_by_key:
        if key in declared:
            continue
        if key.startswith(MANAGED_KEY_PREFIX) or key in adopted:
            actions.append(
                ReconcileAction(
                    ACTION_PRUNE_CANDIDATE,
                    key,
                    "运行时存在但声明已移除（默认不删除，--prune 才执行）",
                )
            )
        else:
            actions.append(
                ReconcileAction(
                    ACTION_SKIP_FOREIGN,
                    key,
                    "非 nblane: 前缀，nblane 不触碰",
                )
            )

    actions.sort(key=lambda action: (_KIND_ORDER[action.kind], action.key))
    return actions


# -- apply -------------------------------------------------------------------


def _spec_field_argv(spec: AutomationSpec) -> list[str]:
    argv = [
        "--cron",
        spec.cron,
        "--tz",
        spec.tz,
        "--exact",
        "--agent",
        "main",
        "--session",
        spec.session,
        # OpenClaw 2026.9 requires an explicit job name; keep it slug-like
        # (declaration key with ':' -> '-') and carry the human label via
        # --display-name.
        "--name",
        spec.key.replace(":", "-"),
        "--display-name",
        spec.name,
    ]
    if spec.model:
        argv += ["--model", spec.model]
    if spec.fallbacks:
        argv += ["--fallbacks", ",".join(spec.fallbacks)]
    if spec.timeout_seconds is not None:
        argv += ["--timeout-seconds", str(spec.timeout_seconds)]
    if spec.deliver_channel and spec.session != "main":
        # 2026.9 rejects --announce on main-session jobs; a main-session
        # system event already lands in the owner's chat.
        argv += [
            "--announce",
            "--best-effort-deliver",
            "--channel",
            spec.deliver_channel,
            "--to",
            spec.deliver_to,
        ]
    if spec.session == "main":
        # 2026.9 rejects --message for main-session jobs; the payload must
        # arrive as a system event instead.
        argv += ["--system-event", spec.prompt_text]
    else:
        argv += ["--message", spec.prompt_text]
    return argv


def build_action_argv(action: ReconcileAction) -> list[str] | None:
    """Build the exact ``openclaw automations`` argv for one action.

    Returns ``None`` for ``keep`` / ``skip_foreign`` (no command needed).
    """

    if action.kind in (ACTION_ADD, ACTION_UPDATE):
        assert action.spec is not None
        verb = "add" if action.kind == ACTION_ADD else "edit"
        return [
            "openclaw",
            "automations",
            verb,
            "--declaration-key",
            action.key,
            *_spec_field_argv(action.spec),
        ]
    if action.kind == ACTION_PRUNE_CANDIDATE:
        return [
            "openclaw",
            "automations",
            "rm",
            "--declaration-key",
            action.key,
        ]
    return None


def apply_reconcile(
    actions: Sequence[ReconcileAction],
    runner: Runner,
    *,
    dry_run: bool = True,
    include_prune: bool = False,
) -> list[ApplyResult]:
    """Execute the plan through *runner* unless ``dry_run`` (the default).

    ``prune_candidate`` actions build their ``rm`` argv for display but are
    only executed when both ``dry_run=False`` and ``include_prune=True``.
    """

    results: list[ApplyResult] = []
    for action in actions:
        argv = build_action_argv(action)
        if argv is None:
            results.append(ApplyResult(action, (), executed=False, ok=True))
            continue
        if action.kind == ACTION_PRUNE_CANDIDATE and not include_prune:
            results.append(
                ApplyResult(
                    action,
                    tuple(argv),
                    executed=False,
                    ok=True,
                    output="未启用 --prune，跳过",
                )
            )
            continue
        if dry_run:
            results.append(
                ApplyResult(
                    action, tuple(argv), executed=False, ok=True, output="dry-run"
                )
            )
            continue
        result = runner(list(argv))
        results.append(
            ApplyResult(
                action,
                tuple(argv),
                executed=True,
                ok=result.ok,
                output=result.output,
            )
        )
    return results


# -- summary -----------------------------------------------------------------


def compute_drift_summary(plan: Sequence[ReconcileAction]) -> str:
    """Render a human-readable Chinese summary of the reconcile plan."""

    counts = {kind: 0 for kind in ACTION_KINDS}
    for action in plan:
        counts[action.kind] += 1
    header = "自动化对账：" + " · ".join(
        f"{_KIND_LABELS[kind]} {counts[kind]}" for kind in ACTION_KINDS
    )
    lines = [header]
    if not plan:
        lines.append("  （无声明任务，运行时也无需管理的任务）")
    for action in plan:
        lines.append(
            f"  {_KIND_MARKS[action.kind]} [{_KIND_LABELS[action.kind]}] "
            f"{action.key} — {action.reason}"
        )
    return "\n".join(lines)
