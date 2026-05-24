"""Optional Codex CLI and Codex Cloud integration.

The adapter keeps Codex as an external harness. It only edits Codex CLI
``config.toml`` through explicit Web configuration helpers and never applies
Codex Cloud diffs locally.
"""

from __future__ import annotations

import json
import hashlib
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Any, Callable

import yaml

from nblane.core import git_backup
from nblane.core.agent_tasks import (
    find_agent_task,
    render_agent_handoff,
    submit_agent_task_candidate,
    update_agent_task_remote,
    update_agent_task_status,
)
from nblane.core.file_write import atomic_write_text
from nblane.core.paths import REPO_ROOT
from nblane.core.profile_io import profile_dir
from nblane.core.yaml_io import _load_yaml_dict

_ENV_FILE = REPO_ROOT / ".env"

try:
    from dotenv import load_dotenv

    load_dotenv(_ENV_FILE, override=False)
except ImportError:
    pass

_DEFAULT_CODEX_BIN = "codex"
_DEFAULT_ATTEMPTS = 1
_DEFAULT_TIMEOUT_SECONDS = 180.0
_DEFAULT_LOCAL_SANDBOX = "workspace-write"
_DEFAULT_LOCAL_WORKTREE_ROOT = Path("/tmp/nblane-codex-runs")
_DEFAULT_PROFILE_CODEX_HOME_ROOT = "~/.nblane/codex/profiles"
_CODEX_HOME_POLICY_DEFAULT = "default"
_CODEX_HOME_POLICY_PROFILE = "profile"
_READONLY_SANDBOX = "read-only"
_MAX_LOCAL_OUTPUT_CHARS = 50_000
_MAX_LOCAL_DIFF_CHARS = 200_000
_INSTALL_PACKAGE = "@openai/codex"
_INSTALL_PACKAGE_LATEST = "@openai/codex@latest"
CODEX_PROFILE_CONFIG_FILENAME = "codex.yaml"
CODEX_PROFILE_CONFIG_SCHEMA_VERSION = "1.0"
CODEX_CLI_CONFIG_FILENAME = "config.toml"
CODEX_AUTH_FILENAME = "auth.json"
_SECRET_CONFIG_KEY_RE = re.compile(
    r"(api[_-]?key|access[_-]?token|token|secret|password|authorization)",
    re.IGNORECASE,
)

_RUNTIME_OVERRIDES: dict[str, str | int | float] = {}

_CODEX_ENV_KEYS = (
    "NBLANE_CODEX_HOME",
    "NBLANE_CODEX_BIN",
    "NBLANE_CODEX_CLOUD_ENV_ID",
    "NBLANE_CODEX_MODEL",
    "NBLANE_CODEX_ATTEMPTS",
    "NBLANE_CODEX_BRANCH",
    "NBLANE_CODEX_TIMEOUT_SECONDS",
)


@dataclass(frozen=True)
class CodexConfig:
    """Runtime Codex settings owned by nblane."""

    bin_path: str = _DEFAULT_CODEX_BIN
    cloud_env_id: str = ""
    model: str = ""
    attempts: int = _DEFAULT_ATTEMPTS
    branch: str = ""
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS
    codex_home: str = ""


@dataclass
class CodexCommandResult:
    """Result of one external Codex/npm command."""

    ok: bool
    command: str
    returncode: int
    stdout: str = ""
    stderr: str = ""
    error: str = ""

    @property
    def output(self) -> str:
        """Return combined sanitized command output."""

        return "\n".join(
            part for part in (self.stdout.strip(), self.stderr.strip()) if part
        ).strip()


@dataclass
class CodexStatus:
    """Current Codex CLI and Codex Cloud readiness."""

    installed: bool
    bin_path: str
    resolved_path: str = ""
    version: str = ""
    logged_in: bool = False
    login_status: str = ""
    cloud_env_id: str = ""
    cloud_env_configured: bool = False
    install_command: str = ""
    upgrade_command: str = ""
    error: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable status mapping."""

        return {
            "installed": self.installed,
            "bin_path": self.bin_path,
            "resolved_path": self.resolved_path,
            "version": self.version,
            "logged_in": self.logged_in,
            "login_status": self.login_status,
            "cloud_env_id": self.cloud_env_id,
            "cloud_env_configured": self.cloud_env_configured,
            "install_command": self.install_command,
            "upgrade_command": self.upgrade_command,
            "error": self.error,
        }


@dataclass
class CodexCloudResult:
    """Result of a Codex Cloud task operation."""

    ok: bool
    task_id: str
    profile: str
    command: str = ""
    cloud_task_id: str = ""
    status: str = ""
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    changed_paths: list[str] = field(default_factory=list)
    remote: dict[str, Any] = field(default_factory=dict)

    @property
    def output(self) -> str:
        """Return combined sanitized command output."""

        return "\n".join(
            part for part in (self.stdout.strip(), self.stderr.strip()) if part
        ).strip()


@dataclass
class CodexLocalResult:
    """Result of one local Codex CLI task run."""

    ok: bool
    task_id: str
    profile: str
    command: str = ""
    status: str = ""
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    changed_paths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    diff: str = ""
    diff_stat: str = ""
    worktree_path: str = ""
    result_payload: dict[str, Any] = field(default_factory=dict)

    @property
    def output(self) -> str:
        """Return combined sanitized command output."""

        return "\n".join(
            part for part in (self.stdout.strip(), self.stderr.strip()) if part
        ).strip()


@dataclass
class CodexReadonlyResult:
    """Result of one read-only local Codex planning prompt."""

    ok: bool
    profile: str
    command: str = ""
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    last_message: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def output(self) -> str:
        """Return the final assistant text, falling back to command output."""

        if self.last_message.strip():
            return self.last_message.strip()
        return "\n".join(
            part for part in (self.stdout.strip(), self.stderr.strip()) if part
        ).strip()


def readable_codex_error(*values: object, limit: int = 500) -> str:
    """Return a short human-readable Codex failure without retaining run logs."""

    def clean_text(value: object) -> str:
        return str(value or "").strip()

    def shorten(value: object) -> str:
        text = " ".join(clean_text(value).split())
        if len(text) <= limit:
            return text
        return text[: max(0, limit - 1)].rstrip() + "..."

    text = "\n".join(clean_text(value) for value in values if clean_text(value))
    text = _sanitize(text)
    if not text:
        return "codex_readonly_failed"
    timeout_match = re.search(r"command_timeout[^.\n]*", text, flags=re.IGNORECASE)
    if timeout_match:
        return shorten(timeout_match.group(0))
    for line in text.splitlines():
        clean = clean_text(line)
        if "ERROR:" not in clean:
            continue
        payload = clean.split("ERROR:", 1)[1].strip()
        if payload.startswith("{"):
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = {}
            if isinstance(data, dict) and clean_text(data.get("error")):
                return shorten(data["error"])
        return shorten(clean)
    patterns = (
        r"No file descriptors available \(os error \d+\)",
        r"config(?:uration)?[^.\n]{0,120}(?:failed|error)",
        r"端点/[^.\n]{0,120}未配置模型[^.\n]*",
        r"model [`'\"]?[^`'\"\n]+[`'\"]? does not exist[^.\n]*",
        r"authentication required[^.\n]*",
        r"api key auth is not supported",
        r"Error code:\s*\d+[^.\n]*",
        r"codex_not_found[^.\n]*",
        r"command_timeout[^.\n]*",
        r"command_error[^.\n]*",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return shorten(match.group(0))
    for line in text.splitlines():
        clean = shorten(line)
        if not clean:
            continue
        if clean.startswith("OpenAI Codex ") or clean.startswith("--------"):
            continue
        if clean in {"user", "assistant"}:
            continue
        if " WARN " in clean and "failed" not in clean.casefold():
            continue
        return clean
    return shorten(text)


def configure(
    *,
    bin_path: str | None = None,
    cloud_env_id: str | None = None,
    model: str | None = None,
    attempts: int | str | None = None,
    branch: str | None = None,
    timeout_seconds: float | str | None = None,
    codex_home: str | None = None,
) -> None:
    """Override Codex settings for the current Python process."""

    if bin_path is not None:
        _RUNTIME_OVERRIDES["bin_path"] = str(bin_path).strip()
    if cloud_env_id is not None:
        _RUNTIME_OVERRIDES["cloud_env_id"] = str(cloud_env_id).strip()
    if model is not None:
        _RUNTIME_OVERRIDES["model"] = str(model).strip()
    if attempts is not None:
        _RUNTIME_OVERRIDES["attempts"] = _coerce_int(
            attempts,
            _DEFAULT_ATTEMPTS,
            minimum=1,
        )
    if branch is not None:
        _RUNTIME_OVERRIDES["branch"] = str(branch).strip()
    if timeout_seconds is not None:
        _RUNTIME_OVERRIDES["timeout_seconds"] = _coerce_float(
            timeout_seconds,
            _DEFAULT_TIMEOUT_SECONDS,
            minimum=5.0,
        )
    if codex_home is not None:
        _RUNTIME_OVERRIDES["codex_home"] = str(codex_home).strip()


def current_config(
    profile: str | None = None,
    *,
    include_runtime: bool = True,
    codex_home_policy: str | None = None,
) -> CodexConfig:
    """Return Codex config from runtime overrides, environment, and defaults.

    ``profile`` still selects profile-owned non-secret preferences from
    ``profiles/<name>/codex.yaml``.  The Codex CLI home is deployment-level by
    default so Web, terminal, plugin, Kanban, Paper Library, and local agent
    runs share the same warmed, trusted Codex runtime.  The older
    profile-isolated home is available only when explicitly requested.
    """

    profile_values = _profile_config_values(profile)
    runtime_home = (
        str(_RUNTIME_OVERRIDES.get("codex_home") or "").strip()
        if include_runtime
        else ""
    )
    policy = _codex_home_policy(codex_home_policy)
    profile_home = (
        str(profile_codex_home(profile)).strip()
        if profile and policy == _CODEX_HOME_POLICY_PROFILE
        else ""
    )
    default_home = runtime_home or profile_home or str(codex_home())
    return CodexConfig(
        bin_path=str(
            _codex_value(
                "bin_path",
                "NBLANE_CODEX_BIN",
                _DEFAULT_CODEX_BIN,
                profile_values,
                include_runtime,
            )
        ).strip()
        or _DEFAULT_CODEX_BIN,
        cloud_env_id=str(
            _codex_value(
                "cloud_env_id",
                "NBLANE_CODEX_CLOUD_ENV_ID",
                "",
                profile_values,
                include_runtime,
            )
        ).strip(),
        model=str(
            _codex_value(
                "model",
                "NBLANE_CODEX_MODEL",
                "",
                profile_values,
                include_runtime,
            )
        ).strip(),
        attempts=_coerce_int(
            _codex_value(
                "attempts",
                "NBLANE_CODEX_ATTEMPTS",
                "",
                profile_values,
                include_runtime,
            ),
            _DEFAULT_ATTEMPTS,
            minimum=1,
        ),
        branch=str(
            _codex_value(
                "branch",
                "NBLANE_CODEX_BRANCH",
                "",
                profile_values,
                include_runtime,
            )
        ).strip(),
        timeout_seconds=_coerce_float(
            _codex_value(
                "timeout_seconds",
                "NBLANE_CODEX_TIMEOUT_SECONDS",
                "",
                profile_values,
                include_runtime,
            ),
            _DEFAULT_TIMEOUT_SECONDS,
            minimum=5.0,
        ),
        codex_home=default_home,
    )


def current_config_dict(
    profile: str | None = None,
    *,
    include_runtime: bool = True,
) -> dict[str, str | int | float]:
    """Return the current config as Streamlit-friendly scalars."""

    cfg = current_config(profile=profile, include_runtime=include_runtime)
    return {
        "bin_path": cfg.bin_path,
        "cloud_env_id": cfg.cloud_env_id,
        "model": cfg.model,
        "attempts": cfg.attempts,
        "branch": cfg.branch,
        "timeout_seconds": cfg.timeout_seconds,
        "codex_home": cfg.codex_home,
    }


def install_command(*, upgrade: bool = False) -> str:
    """Return the official npm install command for Codex CLI."""

    package = _INSTALL_PACKAGE_LATEST if upgrade else _INSTALL_PACKAGE
    return f"npm i -g {package}"


def codex_home() -> Path:
    """Return the service-level Codex CLI home used by nblane.

    ``NBLANE_CODEX_HOME`` is nblane's deployment-level override.  ``CODEX_HOME``
    remains supported so local development follows the normal Codex CLI
    convention.  If neither is set, Codex's default ``~/.codex`` is used.
    """

    raw = os.getenv("NBLANE_CODEX_HOME") or os.getenv("CODEX_HOME") or "~/.codex"
    return Path(raw).expanduser()


def profile_codex_home(profile: str | None) -> Path:
    """Return the legacy profile-isolated Codex home for diagnostics."""

    clean_profile = str(profile or "").strip()
    root = Path(
        os.getenv("NBLANE_CODEX_HOME_ROOT") or _DEFAULT_PROFILE_CODEX_HOME_ROOT
    ).expanduser()
    if not clean_profile:
        return root / "profile-empty"
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", clean_profile).strip("-").lower()
    safe = safe[:48] or "profile"
    digest = hashlib.sha1(clean_profile.encode("utf-8")).hexdigest()[:12]
    return root / f"{safe}-{digest}"


def _codex_home_from_config(
    *,
    profile: str | None = None,
    config: CodexConfig | None = None,
    codex_home_policy: str | None = None,
) -> Path:
    if config is not None and str(config.codex_home or "").strip():
        return Path(str(config.codex_home)).expanduser()
    if profile and _codex_home_policy(codex_home_policy) == _CODEX_HOME_POLICY_PROFILE:
        return profile_codex_home(profile)
    return codex_home()


def codex_auth_path(
    profile: str | None = None,
    *,
    config: CodexConfig | None = None,
    codex_home_policy: str | None = None,
) -> Path:
    """Return the Codex CLI auth file path.

    The auth document is owned by Codex CLI. nblane may write to it only by
    delegating to ``codex login --with-api-key``; it does not display raw auth.
    """

    return (
        _codex_home_from_config(
            profile=profile,
            config=config,
            codex_home_policy=codex_home_policy,
        )
        / CODEX_AUTH_FILENAME
    )


def codex_cli_config_path(
    profile: str | None = None,
    *,
    config: CodexConfig | None = None,
    codex_home_policy: str | None = None,
) -> Path:
    """Return the Codex CLI ``config.toml`` path."""

    return (
        _codex_home_from_config(
            profile=profile,
            config=config,
            codex_home_policy=codex_home_policy,
        )
        / CODEX_CLI_CONFIG_FILENAME
    )


def codex_cli_config_template() -> str:
    """Return a minimal editable Codex CLI config template."""

    return (
        "# Codex CLI config. Auth stays in auth.json via `codex login`.\n"
        "# Example:\n"
        '# model = "gpt-5.1-codex"\n'
    )


def load_codex_cli_config_text(
    profile: str | None = None,
    *,
    config: CodexConfig | None = None,
    codex_home_policy: str | None = None,
) -> str:
    """Load editable Codex CLI ``config.toml`` text or a template."""

    path = codex_cli_config_path(
        profile=profile,
        config=config,
        codex_home_policy=codex_home_policy,
    )
    if path.exists():
        return path.read_text(encoding="utf-8")
    return codex_cli_config_template()


def validate_codex_cli_config_text(text: str) -> dict[str, Any]:
    """Validate editable ``config.toml`` text and return parsed TOML."""

    body = str(text or "")
    try:
        return tomllib.loads(body)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Invalid TOML: {exc}") from exc


def save_codex_cli_config_text(
    text: str,
    profile: str | None = None,
    *,
    config: CodexConfig | None = None,
    codex_home_policy: str | None = None,
) -> Path:
    """Persist raw editable Codex CLI config without git backup."""

    validate_codex_cli_config_text(text)
    path = codex_cli_config_path(
        profile=profile,
        config=config,
        codex_home_policy=codex_home_policy,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_name(f"{path.name}.nblane.bak")
        atomic_write_text(backup, path.read_text(encoding="utf-8"))
    body = str(text or "")
    if not body.endswith("\n"):
        body += "\n"
    atomic_write_text(path, body)
    return path


def profile_config_path(profile: str) -> Path:
    """Return the profile-scoped Codex config path."""

    return profile_dir(profile) / CODEX_PROFILE_CONFIG_FILENAME


def profile_config_template(profile: str) -> str:
    """Return an editable profile-scoped Codex config template."""

    payload = {
        "schema_version": CODEX_PROFILE_CONFIG_SCHEMA_VERSION,
        "profile": profile,
        "updated": "",
        "codex": {
            "bin_path": _DEFAULT_CODEX_BIN,
            "cloud_env_id": "",
            "model": "",
            "attempts": _DEFAULT_ATTEMPTS,
            "branch": "",
            "timeout_seconds": int(_DEFAULT_TIMEOUT_SECONDS),
        },
    }
    body = yaml.dump(
        payload,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    return (
        "# Optional profile-scoped Codex settings.\n"
        "# Auth stays in Codex CLI (`codex login`); do not store tokens here.\n\n"
        + body
    )


def load_profile_config(profile: str) -> dict[str, Any]:
    """Load one profile's optional Codex config document."""

    path = profile_config_path(profile)
    raw = _load_yaml_dict(path) or {}
    codex = raw.get("codex") if isinstance(raw.get("codex"), dict) else raw
    cfg = _config_from_mapping(codex if isinstance(codex, dict) else {})
    return {
        "schema_version": str(
            raw.get("schema_version") or CODEX_PROFILE_CONFIG_SCHEMA_VERSION
        ),
        "profile": str(raw.get("profile") or profile),
        "updated": str(raw.get("updated") or ""),
        "codex": cfg,
    }


def save_profile_config(
    profile: str,
    config: CodexConfig | None = None,
) -> Path:
    """Persist non-auth Codex config under ``profiles/<name>/codex.yaml``."""

    cfg = config or current_config(profile=profile)
    path = profile_config_path(profile)
    payload = {
        "schema_version": CODEX_PROFILE_CONFIG_SCHEMA_VERSION,
        "profile": profile,
        "updated": _now(),
        "codex": {
            "bin_path": cfg.bin_path,
            "cloud_env_id": cfg.cloud_env_id,
            "model": cfg.model,
            "attempts": cfg.attempts,
            "branch": cfg.branch,
            "timeout_seconds": cfg.timeout_seconds,
        },
    }
    body = yaml.dump(
        payload,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    atomic_write_text(
        path,
        f"# Codex config for {profile}. Auth stays in Codex CLI; no tokens here.\n\n"
        + body,
    )
    git_backup.record_change([path], action=f"update {profile}/codex.yaml")
    return path


def validate_profile_config_text(text: str) -> dict[str, Any]:
    """Validate editable ``codex.yaml`` text and return parsed YAML."""

    try:
        raw = yaml.safe_load(str(text or ""))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML: {exc}") from exc
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("Codex config must be a YAML mapping.")
    _reject_secret_config_keys(raw)
    codex = raw.get("codex") if "codex" in raw else raw
    if not isinstance(codex, dict):
        raise ValueError("Codex config field `codex` must be a mapping.")
    _validate_raw_numeric_field(codex, "attempts", int)
    _validate_raw_numeric_field(codex, "timeout_seconds", float)
    return raw


def save_profile_config_text(profile: str, text: str) -> Path:
    """Persist raw editable ``codex.yaml`` text without reformatting it."""

    validate_profile_config_text(text)
    path = profile_config_path(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = str(text or "")
    if not body.endswith("\n"):
        body += "\n"
    atomic_write_text(path, body)
    git_backup.record_change([path], action=f"update {profile}/codex.yaml")
    return path


def install_codex(*, upgrade: bool = False) -> CodexCommandResult:
    """Install or upgrade Codex CLI through npm."""

    npm = shutil.which("npm")
    command = install_command(upgrade=upgrade)
    if not npm:
        return CodexCommandResult(
            ok=False,
            command=command,
            returncode=127,
            error="npm_not_found: install Node.js/npm first.",
        )
    package = _INSTALL_PACKAGE_LATEST if upgrade else _INSTALL_PACKAGE
    return _run([npm, "i", "-g", package], timeout=600.0)


def login_with_api_key(
    api_key: str,
    *,
    config: CodexConfig | None = None,
) -> CodexCommandResult:
    """Store a Codex API key through Codex CLI without exposing it in args."""

    key = str(api_key or "").strip()
    if not key:
        return CodexCommandResult(
            ok=False,
            command="codex login --with-api-key",
            returncode=2,
            error="codex_api_key_missing",
        )
    cfg = config or current_config()
    binary = _resolve_binary(cfg.bin_path)
    if not binary:
        return CodexCommandResult(
            ok=False,
            command="codex login --with-api-key",
            returncode=127,
            error="codex_not_found: install Codex CLI first.",
        )
    return _run(
        [binary, "login", "--with-api-key"],
        timeout=cfg.timeout_seconds,
        stdin=f"{key}\n",
        env=_codex_command_env(cfg),
    )


def codex_status(config: CodexConfig | None = None) -> CodexStatus:
    """Check Codex CLI install, login, and cloud env readiness."""

    cfg = config or current_config()
    install = install_command()
    upgrade = install_command(upgrade=True)
    resolved = _resolve_binary(cfg.bin_path)
    if not resolved:
        return CodexStatus(
            installed=False,
            bin_path=cfg.bin_path,
            cloud_env_id=cfg.cloud_env_id,
            cloud_env_configured=bool(cfg.cloud_env_id),
            install_command=install,
            upgrade_command=upgrade,
            error="codex_not_found",
        )

    codex_env = _codex_command_env(cfg)
    version = _run(
        [resolved, "--version"],
        timeout=cfg.timeout_seconds,
        env=codex_env,
    )
    login = _run(
        [resolved, "login", "status"],
        timeout=cfg.timeout_seconds,
        env=codex_env,
    )
    login_text = login.output
    return CodexStatus(
        installed=True,
        bin_path=cfg.bin_path,
        resolved_path=resolved,
        version=version.output,
        logged_in=login.ok and "logged in" in login_text.lower(),
        login_status=login_text,
        cloud_env_id=cfg.cloud_env_id,
        cloud_env_configured=bool(cfg.cloud_env_id),
        install_command=install,
        upgrade_command=upgrade,
        error=version.error or login.error,
    )


def save_config_to_env(
    config: CodexConfig | None = None,
    *,
    env_path: Path | None = None,
) -> Path:
    """Persist non-auth ``NBLANE_CODEX_*`` settings to ``.env``."""

    cfg = config or current_config()
    path = env_path or _ENV_FILE
    values = {
        "NBLANE_CODEX_HOME": cfg.codex_home,
        "NBLANE_CODEX_BIN": cfg.bin_path,
        "NBLANE_CODEX_CLOUD_ENV_ID": cfg.cloud_env_id,
        "NBLANE_CODEX_MODEL": cfg.model,
        "NBLANE_CODEX_ATTEMPTS": str(cfg.attempts),
        "NBLANE_CODEX_BRANCH": cfg.branch,
        "NBLANE_CODEX_TIMEOUT_SECONDS": str(cfg.timeout_seconds),
    }
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = existing.splitlines()
    out: list[str] = []
    written: set[str] = set()
    pattern = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")
    for line in lines:
        match = pattern.match(line)
        key = match.group(1) if match else ""
        if key in values:
            if key not in written:
                out.append(f"{key}={_env_value(values[key])}")
                written.add(key)
            continue
        out.append(line)
    missing = [key for key in _CODEX_ENV_KEYS if key not in written]
    if missing:
        if out and out[-1].strip():
            out.append("")
        out.append("# Optional Codex Cloud integration for nblane.")
        for key in missing:
            out.append(f"{key}={_env_value(values[key])}")
    atomic_write_text(path, "\n".join(out).rstrip() + "\n")
    return path


def submit_codex_cloud_task(
    profile: str,
    task_id: str,
    *,
    config: CodexConfig | None = None,
) -> CodexCloudResult:
    """Submit one nblane agent task to Codex Cloud."""

    cfg = config or current_config(profile=profile)
    found = find_agent_task(task_id, profile=profile)
    if found is None:
        return CodexCloudResult(
            ok=False,
            task_id=task_id,
            profile=profile,
            error=f"unknown_agent_task: {task_id}",
        )
    found_profile, task = found
    if not cfg.cloud_env_id:
        return CodexCloudResult(
            ok=False,
            task_id=task_id,
            profile=found_profile,
            error="codex_cloud_env_missing: set NBLANE_CODEX_CLOUD_ENV_ID.",
        )
    binary = _resolve_binary(cfg.bin_path)
    if not binary:
        return CodexCloudResult(
            ok=False,
            task_id=task_id,
            profile=found_profile,
            error="codex_not_found: install Codex CLI first.",
        )

    prompt = render_agent_handoff(task, profile=found_profile, target="codex")
    args = [
        binary,
        "cloud",
        "exec",
        *_codex_config_args(cfg),
        "--env",
        cfg.cloud_env_id,
        "--attempts",
        str(cfg.attempts),
    ]
    if cfg.branch:
        args.extend(["--branch", cfg.branch])
    args.append(prompt)
    result = _run(args, timeout=cfg.timeout_seconds, env=_codex_command_env(cfg))
    if not result.ok:
        return CodexCloudResult(
            ok=False,
            task_id=task_id,
            profile=found_profile,
            command=result.command,
            stdout=result.stdout,
            stderr=result.stderr,
            error=result.error or "codex_cloud_submit_failed",
        )

    output = result.output
    cloud_task_id = parse_cloud_task_id(output)
    status = "running" if cloud_task_id else "handed_off"
    remote = {
        "provider": "codex_cloud",
        "cloud_task_id": cloud_task_id,
        "env_id": cfg.cloud_env_id,
        "branch": cfg.branch,
        "attempts": cfg.attempts,
        "submitted_at": _now(),
        "submit_raw": output,
    }
    summary = (
        f"Submitted to Codex Cloud: {cloud_task_id}"
        if cloud_task_id
        else "Submitted to Codex Cloud; task id was not parsed."
    )
    update_agent_task_remote(
        found_profile,
        task_id,
        remote,
        status=status,
        result_summary=summary,
    )
    return CodexCloudResult(
        ok=True,
        task_id=task_id,
        profile=found_profile,
        command=result.command,
        cloud_task_id=cloud_task_id,
        status=status,
        stdout=result.stdout,
        stderr=result.stderr,
        remote=remote,
    )


def refresh_codex_cloud_task(
    profile: str,
    task_id: str,
    *,
    include_diff: bool = False,
    config: CodexConfig | None = None,
) -> CodexCloudResult:
    """Refresh Codex Cloud status and optionally pull a diff candidate."""

    cfg = config or current_config(profile=profile)
    found = find_agent_task(task_id, profile=profile)
    if found is None:
        return CodexCloudResult(
            ok=False,
            task_id=task_id,
            profile=profile,
            error=f"unknown_agent_task: {task_id}",
        )
    found_profile, task = found
    remote = task.get("remote") if isinstance(task.get("remote"), dict) else {}
    cloud_task_id = str(remote.get("cloud_task_id") or "").strip()
    if not cloud_task_id:
        return CodexCloudResult(
            ok=False,
            task_id=task_id,
            profile=found_profile,
            error="codex_cloud_task_missing: submit the task first.",
        )
    binary = _resolve_binary(cfg.bin_path)
    if not binary:
        return CodexCloudResult(
            ok=False,
            task_id=task_id,
            profile=found_profile,
            cloud_task_id=cloud_task_id,
            error="codex_not_found: install Codex CLI first.",
        )

    status_result = _run(
        [binary, "cloud", "status", *_codex_config_args(cfg), cloud_task_id],
        timeout=cfg.timeout_seconds,
        env=_codex_command_env(cfg),
    )
    if not status_result.ok:
        return CodexCloudResult(
            ok=False,
            task_id=task_id,
            profile=found_profile,
            cloud_task_id=cloud_task_id,
            command=status_result.command,
            stdout=status_result.stdout,
            stderr=status_result.stderr,
            error=status_result.error or "codex_cloud_status_failed",
        )

    status_raw = status_result.output
    remote_patch: dict[str, Any] = {
        "provider": "codex_cloud",
        "cloud_task_id": cloud_task_id,
        "status_raw": status_raw,
        "status_checked_at": _now(),
    }
    inferred_status = _agent_status_from_cloud_status(status_raw)
    update_agent_task_remote(
        found_profile,
        task_id,
        remote_patch,
        status=inferred_status,
    )

    if not include_diff:
        return CodexCloudResult(
            ok=True,
            task_id=task_id,
            profile=found_profile,
            command=status_result.command,
            cloud_task_id=cloud_task_id,
            status=inferred_status or str(task.get("status") or ""),
            stdout=status_result.stdout,
            stderr=status_result.stderr,
            remote={**remote, **remote_patch},
        )

    diff_result = _run(
        [binary, "cloud", "diff", *_codex_config_args(cfg), cloud_task_id],
        timeout=cfg.timeout_seconds,
        env=_codex_command_env(cfg),
    )
    if not diff_result.ok:
        return CodexCloudResult(
            ok=False,
            task_id=task_id,
            profile=found_profile,
            command=diff_result.command,
            cloud_task_id=cloud_task_id,
            status=inferred_status or str(task.get("status") or ""),
            stdout=diff_result.stdout,
            stderr=diff_result.stderr,
            error=diff_result.error or "codex_cloud_diff_failed",
            remote={**remote, **remote_patch},
        )

    diff_text = diff_result.output
    changed_paths = parse_diff_changed_paths(diff_text)
    diff_remote = {
        **remote_patch,
        "diff": diff_text,
        "diff_checked_at": _now(),
    }
    update_agent_task_remote(
        found_profile,
        task_id,
        diff_remote,
        changed_paths=changed_paths,
        result_summary="Codex Cloud diff ready for review.",
    )
    warnings = [] if changed_paths else ["Codex Cloud diff contained no parsed paths."]
    payload = {
        "provider": "codex_cloud",
        "cloud_task_id": cloud_task_id,
        "status_raw": status_raw,
        "diff": diff_text,
    }
    submit_agent_task_candidate(
        found_profile,
        task_id,
        summary="Codex Cloud diff ready for review.",
        changed_paths=changed_paths,
        warnings=warnings,
        result_payload=payload,
    )
    return CodexCloudResult(
        ok=True,
        task_id=task_id,
        profile=found_profile,
        command=diff_result.command,
        cloud_task_id=cloud_task_id,
        status="candidate_ready",
        stdout=diff_result.stdout,
        stderr=diff_result.stderr,
        changed_paths=changed_paths,
        remote={**remote, **diff_remote},
    )


def run_readonly_codex_prompt(
    profile: str,
    prompt: str,
    *,
    config: CodexConfig | None = None,
    cwd: Path | None = None,
    timeout_seconds: float | None = None,
    enable_search: bool = False,
    reasoning_effort: str = "",
    progress_callback: Callable[[dict[str, object]], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
    idle_timeout_seconds: float | None = None,
) -> CodexReadonlyResult:
    """Run ``codex exec`` as a read-only planning helper.

    This helper is for richer reasoning/search drafts, not patch generation.
    It does not create an agent task, does not collect diffs, and asks Codex to
    run with the CLI's read-only sandbox.
    """

    cfg = config or current_config(profile=profile)
    binary = _resolve_binary(cfg.bin_path)
    if not binary:
        return CodexReadonlyResult(
            ok=False,
            profile=profile,
            error="codex_not_found: install Codex CLI first.",
        )

    with tempfile.TemporaryDirectory(prefix="nblane-codex-readonly-") as tmp:
        last_message_path = Path(tmp) / "last-message.txt"
        args_prefix = [binary]
        if enable_search:
            args_prefix.append("--search")
        args = [
            *args_prefix,
            "exec",
            *_codex_config_args(cfg),
            *_codex_reasoning_args(reasoning_effort),
            "--cd",
            str(cwd or REPO_ROOT),
            "--sandbox",
            _READONLY_SANDBOX,
            "--ephemeral",
            "--color",
            "never",
            "--output-last-message",
            str(last_message_path),
            "-",
        ]
        runner_timeout = timeout_seconds or cfg.timeout_seconds
        if progress_callback is not None or cancel_check is not None or idle_timeout_seconds:
            result = _run_streaming(
                args,
                timeout=runner_timeout,
                stdin=str(prompt or ""),
                env=_codex_command_env(cfg),
                progress_callback=progress_callback,
                cancel_check=cancel_check,
                idle_timeout_seconds=idle_timeout_seconds,
            )
        else:
            result = _run(
                args,
                timeout=runner_timeout,
                stdin=str(prompt or ""),
                env=_codex_command_env(cfg),
            )
        warnings: list[str] = []
        stdout, stdout_truncated = _truncate_text(
            result.stdout,
            _MAX_LOCAL_OUTPUT_CHARS,
        )
        stderr, stderr_truncated = _truncate_text(
            result.stderr,
            _MAX_LOCAL_OUTPUT_CHARS,
        )
        last_message, last_truncated = _truncate_text(
            _read_optional_text(last_message_path),
            _MAX_LOCAL_OUTPUT_CHARS,
        )
        if stdout_truncated or stderr_truncated or last_truncated:
            warnings.append("Codex read-only output was truncated.")
        return CodexReadonlyResult(
            ok=result.ok,
            profile=profile,
            command=result.command,
            stdout=stdout,
            stderr=stderr,
            error=result.error,
            last_message=last_message,
            warnings=warnings,
        )


def run_local_codex_task(
    profile: str,
    task_id: str,
    *,
    config: CodexConfig | None = None,
    sandbox: str = _DEFAULT_LOCAL_SANDBOX,
    keep_worktree: bool = False,
    worktree_root: Path | None = None,
) -> CodexLocalResult:
    """Run one nblane agent task through local ``codex exec``.

    The task runs in a temporary git worktree so Codex never writes directly
    into the main checkout. The resulting diff is stored as an Agent Activity
    candidate for review.
    """

    cfg = config or current_config(profile=profile)
    found = find_agent_task(task_id, profile=profile)
    if found is None:
        return CodexLocalResult(
            ok=False,
            task_id=task_id,
            profile=profile,
            error=f"unknown_agent_task: {task_id}",
            status="failed",
        )
    found_profile, task = found
    binary = _resolve_binary(cfg.bin_path)
    if not binary:
        result = CodexLocalResult(
            ok=False,
            task_id=task_id,
            profile=found_profile,
            error="codex_not_found: install Codex CLI first.",
            status="failed",
        )
        _record_local_codex_failure(found_profile, task_id, result)
        return result
    git = shutil.which("git")
    if not git:
        result = CodexLocalResult(
            ok=False,
            task_id=task_id,
            profile=found_profile,
            error="git_not_found: install git first.",
            status="failed",
        )
        _record_local_codex_failure(found_profile, task_id, result)
        return result

    warnings: list[str] = []
    if _main_worktree_dirty(git):
        warnings.append(
            "Local Codex ran in an isolated clean HEAD worktree; "
            "uncommitted main checkout changes were not included."
        )
    root = _local_worktree_root(worktree_root)
    root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    worktree_path = root / (
        f"{_safe_path_segment(found_profile)}-"
        f"{_safe_path_segment(task_id)}-{run_id}"
    )
    last_message_path = root / f"{worktree_path.name}.last-message.txt"
    worktree_created = False
    command = ""
    try:
        add_result = _run(
            [git, "worktree", "add", "--detach", str(worktree_path), "HEAD"],
            timeout=60.0,
        )
        if not add_result.ok:
            result = CodexLocalResult(
                ok=False,
                task_id=task_id,
                profile=found_profile,
                command=add_result.command,
                stdout=add_result.stdout,
                stderr=add_result.stderr,
                error=add_result.error or "local_codex_worktree_failed",
                status="failed",
                warnings=warnings,
                worktree_path=str(worktree_path),
            )
            _record_local_codex_failure(found_profile, task_id, result)
            return result
        worktree_created = True
        worktree_path.mkdir(parents=True, exist_ok=True)
        _copy_profile_context(found_profile, worktree_path)
        prompt = _local_codex_prompt(task, profile=found_profile)
        args = [
            binary,
            "exec",
            *_codex_config_args(cfg),
            "--cd",
            str(worktree_path),
            "--sandbox",
            sandbox or _DEFAULT_LOCAL_SANDBOX,
            "--color",
            "never",
            "--output-last-message",
            str(last_message_path),
            "-",
        ]
        run_result = _run(
            args,
            timeout=cfg.timeout_seconds,
            stdin=prompt,
            env=_codex_command_env(cfg),
        )
        command = run_result.command
        last_message = _read_optional_text(last_message_path)
        diff_stat = _git_diff_stat(git, worktree_path)
        tracked_diff = _git_tracked_diff(git, worktree_path)
        untracked_diff = _git_untracked_diff(git, worktree_path)
        diff = _combine_diff_parts(tracked_diff, untracked_diff)
        changed_paths = _git_changed_paths(git, worktree_path)
        if not changed_paths:
            changed_paths = parse_diff_changed_paths(diff)
        payload_warnings = list(warnings)
        diff, diff_truncated = _truncate_text(diff, _MAX_LOCAL_DIFF_CHARS)
        if diff_truncated:
            payload_warnings.append("Local Codex diff was truncated in Activity.")
        stdout, stdout_truncated = _truncate_text(
            run_result.stdout,
            _MAX_LOCAL_OUTPUT_CHARS,
        )
        stderr, stderr_truncated = _truncate_text(
            run_result.stderr,
            _MAX_LOCAL_OUTPUT_CHARS,
        )
        if stdout_truncated or stderr_truncated:
            payload_warnings.append("Local Codex command output was truncated.")
        if run_result.ok and not changed_paths:
            payload_warnings.append("Local Codex completed without repository changes.")
        payload = {
            "provider": "local_codex",
            "worktree_path": str(worktree_path),
            "sandbox": sandbox or _DEFAULT_LOCAL_SANDBOX,
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "last_message": _truncate_text(last_message, _MAX_LOCAL_OUTPUT_CHARS)[0],
            "diff_stat": diff_stat,
            "diff": diff,
            "main_worktree_dirty": bool(warnings),
        }
        if run_result.ok:
            summary = _local_codex_summary(last_message, changed_paths)
            submit_agent_task_candidate(
                found_profile,
                task_id,
                summary=summary,
                changed_paths=changed_paths,
                warnings=payload_warnings,
                result_payload=payload,
            )
            return CodexLocalResult(
                ok=True,
                task_id=task_id,
                profile=found_profile,
                command=command,
                status="candidate_ready",
                stdout=stdout,
                stderr=stderr,
                changed_paths=changed_paths,
                warnings=payload_warnings,
                diff=diff,
                diff_stat=diff_stat,
                worktree_path=str(worktree_path),
                result_payload=payload,
            )

        result = CodexLocalResult(
            ok=False,
            task_id=task_id,
            profile=found_profile,
            command=command,
            status="failed",
            stdout=stdout,
            stderr=stderr,
            error=run_result.error or "local_codex_failed",
            changed_paths=changed_paths,
            warnings=payload_warnings,
            diff=diff,
            diff_stat=diff_stat,
            worktree_path=str(worktree_path),
            result_payload=payload,
        )
        _record_local_codex_failure(found_profile, task_id, result)
        return result
    finally:
        if not keep_worktree and worktree_created:
            _cleanup_local_worktree(git, worktree_path)
        try:
            last_message_path.unlink()
        except FileNotFoundError:
            pass


def parse_cloud_task_id(text: str) -> str:
    """Best-effort Codex Cloud task id extraction."""

    clean = str(text or "").strip()
    if not clean:
        return ""
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        data = None
    found = _find_task_id_in_json(data)
    if found:
        return found
    patterns = (
        r"(?i)\b(?:cloud\s+task|task)\s*(?:id)?\s*[:#]\s*([A-Za-z0-9][A-Za-z0-9_-]{5,})\b",
        r"\b((?:task|ctask|codex_task|codex)[_-][A-Za-z0-9_-]{6,})\b",
        r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b",
    )
    for pattern in patterns:
        match = re.search(pattern, clean)
        if match:
            return match.group(1)
    return ""


def parse_diff_changed_paths(diff_text: str) -> list[str]:
    """Extract changed file paths from a unified diff."""

    paths: list[str] = []
    seen: set[str] = set()

    def _add(path: str) -> None:
        clean = path.strip().strip('"')
        if clean.startswith("a/") or clean.startswith("b/"):
            clean = clean[2:]
        if not clean or clean == "/dev/null" or clean in seen:
            return
        seen.add(clean)
        paths.append(clean)

    for line in str(diff_text or "").splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                _add(parts[3])
            continue
        if line.startswith("+++ "):
            _add(line[4:])
    return paths


def _run_streaming(
    args: list[str],
    *,
    timeout: float,
    cwd: Path | None = None,
    stdin: str | None = None,
    env: dict[str, str] | None = None,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
    idle_timeout_seconds: float | None = None,
) -> CodexCommandResult:
    command = _display_command(args)
    started = time.monotonic()

    def emit(event: dict[str, object]) -> None:
        if progress_callback is None:
            return
        payload = {
            **event,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        }
        try:
            progress_callback(payload)
        except Exception:
            pass

    try:
        process = subprocess.Popen(
            args,
            cwd=cwd or REPO_ROOT,
            env=env,
            stdin=subprocess.PIPE if stdin is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError as exc:
        return CodexCommandResult(
            ok=False,
            command=command,
            returncode=127,
            error=f"command_not_found: {exc}",
        )
    except OSError as exc:
        return CodexCommandResult(
            ok=False,
            command=command,
            returncode=1,
            error=f"command_error: {exc}",
        )

    emit({"event": "command_started", "phase": "codex", "message": "Codex process started."})

    if stdin is not None and process.stdin is not None:
        try:
            process.stdin.write(stdin)
            process.stdin.close()
        except OSError:
            pass

    output_queue: Queue[tuple[str, str]] = Queue()

    def read_stream(name: str, stream: Any) -> None:
        if stream is None:
            return
        try:
            for line in iter(stream.readline, ""):
                output_queue.put((name, line))
        finally:
            try:
                stream.close()
            except Exception:
                pass

    stdout_thread = Thread(target=read_stream, args=("stdout", process.stdout), daemon=True)
    stderr_thread = Thread(target=read_stream, args=("stderr", process.stderr), daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    last_activity = time.monotonic()
    timed_out = False
    idle_timed_out = False
    cancelled = False

    def progress_output_payload(stream_name: str, clean_line: str) -> dict[str, object]:
        payload: dict[str, object] = {
            "event": "output",
            "phase": "codex",
            "stream": stream_name,
            "message": clean_line[:240],
            "output_kind": "log",
        }
        lower = clean_line.casefold()
        if lower.startswith("web search:"):
            detail = clean_line.split(":", 1)[1].strip()
            message = "Searching the web."
            if detail:
                message = (
                    f"Opening web result: {detail[:200]}"
                    if re.match(r"https?://", detail, flags=re.IGNORECASE)
                    else f"Searching web: {detail[:200]}"
                )
            payload.update(
                {
                    "phase": "codex_search",
                    "message": message,
                    "output_kind": "web_search",
                    "detail": detail[:500],
                }
            )
            return payload
        if stream_name != "stderr" and clean_line.startswith("{") and '"results"' in clean_line and '"query"' in clean_line:
            payload.update(
                {
                    "phase": "codex_synthesis",
                    "message": "Codex returned structured candidates; parsing and ranking them.",
                    "output_kind": "structured_result",
                }
            )
            return payload
        if stream_name == "stderr" and clean_line.startswith("{") and '"results"' in clean_line and '"query"' in clean_line:
            payload.update({"message": "Codex CLI is starting.", "output_kind": "startup", "visible": False})
            return payload
        if stream_name == "stderr" and (
            clean_line in {"{", "}", "[", "]", "codex"}
            or clean_line.startswith('"')
            or clean_line.startswith(
                (
                    "You are the nblane AI Gateway.",
                    "You receive business payloads",
                    "Return only the requested output contract.",
                    "Use English for all natural-language field values",
                    "All writebacks are review-first candidates",
                    "Find paper candidates for import.",
                )
            )
        ):
            payload.update({"message": "Codex CLI is starting.", "output_kind": "startup", "visible": False})
            return payload
        if clean_line.startswith("warning: Codex could not find bubblewrap"):
            payload.update(
                {
                    "message": "Codex sandbox warning; using bundled fallback.",
                    "output_kind": "setup_warning",
                    "visible": False,
                }
            )
            return payload
        if (
            "codex_core_plugins" in lower
            or "curated plugin" in lower
            or "codex_file_watcher" in lower
            or "fatal: early eof" in lower
            or "git_binary=\"git\"" in lower
            or ("plugin" in lower and (" warn " in lower or "failed" in lower or "error=" in lower))
        ):
            payload.update(
                {
                    "message": "Codex plugin cache warning; search continues.",
                    "output_kind": "plugin_warning",
                }
            )
            return payload
        if clean_line == "tokens used" or re.fullmatch(r"[\d,]+", clean_line):
            payload.update({"message": "Codex reported token usage.", "output_kind": "usage", "visible": False})
            return payload
        if (
            clean_line in {"--------", "user", "assistant"}
            or clean_line.startswith("OpenAI Codex ")
            or clean_line.startswith(
                (
                    "workdir:",
                    "model:",
                    "provider:",
                    "approval:",
                    "sandbox:",
                    "reasoning effort:",
                    "reasoning summaries:",
                    "session id:",
                    "Boundaries:",
                    "Task:",
                    "Acceptance rules:",
                    "Return this strict JSON shape",
                    "Compact search payload:",
                    "System instruction summary:",
                )
            )
            or clean_line.startswith("- ")
        ):
            payload.update({"message": "Codex CLI is starting.", "output_kind": "startup", "visible": False})
            return payload
        return payload

    def append_output(stream_name: str, line: str) -> None:
        nonlocal last_activity
        sanitized = _sanitize(line)
        if stream_name == "stderr":
            stderr_parts.append(sanitized)
        else:
            stdout_parts.append(sanitized)
        clean_line = " ".join(sanitized.split())
        if not clean_line:
            return
        last_activity = time.monotonic()
        emit(progress_output_payload(stream_name, clean_line))

    def drain_available() -> None:
        while True:
            try:
                stream_name, line = output_queue.get_nowait()
            except Empty:
                return
            append_output(stream_name, line)

    def stop_process() -> None:
        if process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except OSError:
                pass
        except OSError:
            pass

    while True:
        try:
            stream_name, line = output_queue.get(timeout=0.15)
        except Empty:
            stream_name = ""
            line = ""
        if stream_name:
            append_output(stream_name, line)

        returncode = process.poll()
        if returncode is not None:
            drain_available()
            break

        now = time.monotonic()
        if cancel_check is not None:
            try:
                cancelled = bool(cancel_check())
            except Exception:
                cancelled = False
            if cancelled:
                emit({"event": "cancelled", "phase": "codex", "message": "Codex search cancellation requested."})
                stop_process()
                break
        if timeout > 0 and now - started >= timeout:
            timed_out = True
            emit({"event": "timeout", "phase": "codex", "message": f"Codex exceeded {timeout:g}s."})
            stop_process()
            break
        if idle_timeout_seconds and idle_timeout_seconds > 0 and now - last_activity >= idle_timeout_seconds:
            idle_timed_out = True
            emit(
                {
                    "event": "idle_timeout",
                    "phase": "codex",
                    "message": f"Codex had no output for {idle_timeout_seconds:g}s.",
                }
            )
            stop_process()
            break

    drain_available()
    stdout_thread.join(timeout=1)
    stderr_thread.join(timeout=1)
    drain_available()
    returncode = process.poll()
    if returncode is None:
        returncode = 124 if timed_out or idle_timed_out else 130 if cancelled else 1
    stdout = _sanitize("".join(stdout_parts))
    stderr = _sanitize("".join(stderr_parts))
    if cancelled:
        error = "command_cancelled"
    elif timed_out:
        error = f"command_timeout: exceeded {timeout:g}s"
    elif idle_timed_out:
        error = f"command_idle_timeout: no output for {idle_timeout_seconds:g}s"
    else:
        error = "" if returncode == 0 else _summarize_error(stdout, stderr)
    emit(
        {
            "event": "command_finished",
            "phase": "codex",
            "status": "ok" if returncode == 0 and not error else "failed",
            "message": "Codex finished search; parsing and ranking candidates." if returncode == 0 and not error else error,
            "returncode": returncode,
        }
    )
    return CodexCommandResult(
        ok=returncode == 0 and not error,
        command=command,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        error=error,
    )


def _run(
    args: list[str],
    *,
    timeout: float,
    cwd: Path | None = None,
    stdin: str | None = None,
    env: dict[str, str] | None = None,
) -> CodexCommandResult:
    command = _display_command(args)
    try:
        completed = subprocess.run(
            args,
            cwd=cwd or REPO_ROOT,
            env=env,
            input=stdin,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return CodexCommandResult(
            ok=False,
            command=command,
            returncode=127,
            error=f"command_not_found: {exc}",
        )
    except subprocess.TimeoutExpired as exc:
        return CodexCommandResult(
            ok=False,
            command=command,
            returncode=124,
            stdout=_sanitize(exc.stdout or ""),
            stderr=_sanitize(exc.stderr or ""),
            error=f"command_timeout: exceeded {timeout:g}s",
        )
    except OSError as exc:
        return CodexCommandResult(
            ok=False,
            command=command,
            returncode=1,
            error=f"command_error: {exc}",
        )
    stdout = _sanitize(completed.stdout)
    stderr = _sanitize(completed.stderr)
    error = "" if completed.returncode == 0 else _summarize_error(stdout, stderr)
    return CodexCommandResult(
        ok=completed.returncode == 0,
        command=command,
        returncode=completed.returncode,
        stdout=stdout,
        stderr=stderr,
        error=error,
    )


def _codex_command_env(config: CodexConfig) -> dict[str, str]:
    env = os.environ.copy()
    home = _codex_home_from_config(config=config)
    home.mkdir(parents=True, exist_ok=True)
    env["CODEX_HOME"] = str(home)
    return env


def _main_worktree_dirty(git: str) -> bool:
    result = _run(
        [git, "status", "--porcelain", "--untracked-files=normal"],
        timeout=30.0,
    )
    return bool(result.ok and result.output.strip())


def _local_worktree_root(path: Path | None) -> Path:
    raw = path or Path(
        os.getenv("NBLANE_CODEX_LOCAL_WORKTREE_ROOT")
        or str(_DEFAULT_LOCAL_WORKTREE_ROOT)
    )
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate


def _safe_path_segment(value: object) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "").strip()).strip("._")
    return text[:80] or "run"


def _copy_profile_context(profile: str, worktree_path: Path) -> None:
    source = profile_dir(profile)
    if not source.exists():
        return
    target = worktree_path / "profiles" / profile
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        target,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )


def _local_codex_prompt(task: dict[str, Any], *, profile: str) -> str:
    handoff = render_agent_handoff(task, profile=profile, target="codex")
    note = """
## Local Codex Runner Note
You are running via nblane's local Codex runner in an isolated git worktree.
Make any code changes in this worktree. If MCP tools are unavailable, use the
files in the worktree and the copied profile context under `profiles/`.
nblane will collect the resulting git diff and put it into Agent Activity as a
candidate, so do not call `codex cloud apply` or make changes outside this
worktree.
"""
    return handoff.rstrip() + "\n\n" + note.strip() + "\n"


def _read_optional_text(path: Path) -> str:
    try:
        return _sanitize(path.read_text(encoding="utf-8"))
    except OSError:
        return ""


def _git_diff_stat(git: str, worktree_path: Path) -> str:
    result = _run(
        [git, "diff", "--stat"],
        timeout=30.0,
        cwd=worktree_path,
    )
    return result.output if result.ok else ""


def _git_tracked_diff(git: str, worktree_path: Path) -> str:
    result = _run(
        [git, "diff", "--no-ext-diff", "--binary"],
        timeout=30.0,
        cwd=worktree_path,
    )
    return result.output if result.ok else ""


def _git_untracked_files(git: str, worktree_path: Path) -> list[str]:
    result = _run(
        [git, "ls-files", "--others", "--exclude-standard"],
        timeout=30.0,
        cwd=worktree_path,
    )
    if not result.ok:
        return []
    return [
        line.strip()
        for line in result.output.splitlines()
        if line.strip()
    ]


def _git_untracked_diff(git: str, worktree_path: Path) -> str:
    parts: list[str] = []
    for rel_path in _git_untracked_files(git, worktree_path):
        result = _run(
            [git, "diff", "--no-index", "--binary", "--", "/dev/null", rel_path],
            timeout=30.0,
            cwd=worktree_path,
        )
        if result.output:
            parts.append(result.output)
    return "\n\n".join(parts).strip()


def _combine_diff_parts(*parts: str) -> str:
    return "\n\n".join(part.strip() for part in parts if part.strip()).strip()


def _git_changed_paths(git: str, worktree_path: Path) -> list[str]:
    result = _run(
        [git, "status", "--porcelain", "--untracked-files=all"],
        timeout=30.0,
        cwd=worktree_path,
    )
    if not result.ok:
        return []
    paths: list[str] = []
    seen: set[str] = set()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path and path not in seen:
            seen.add(path)
            paths.append(path)
    return paths


def _truncate_text(text: str, limit: int) -> tuple[str, bool]:
    value = str(text or "")
    if len(value) <= limit:
        return value, False
    return value[:limit] + "\n\n[truncated]", True


def _local_codex_summary(last_message: str, changed_paths: list[str]) -> str:
    clean = str(last_message or "").strip()
    first_line = next((line.strip() for line in clean.splitlines() if line.strip()), "")
    if first_line:
        return first_line[:500]
    if changed_paths:
        return f"Local Codex produced changes in {len(changed_paths)} path(s)."
    return "Local Codex completed without repository changes."


def _record_local_codex_failure(
    profile: str,
    task_id: str,
    result: CodexLocalResult,
) -> None:
    payload = dict(result.result_payload or {})
    payload.setdefault("provider", "local_codex")
    payload.setdefault("worktree_path", result.worktree_path)
    payload.setdefault("command", result.command)
    payload.setdefault("stdout", result.stdout)
    payload.setdefault("stderr", result.stderr)
    payload.setdefault("diff", result.diff)
    payload.setdefault("diff_stat", result.diff_stat)
    try:
        update_agent_task_status(
            profile,
            task_id,
            "failed",
            error=result.error,
            warnings=result.warnings,
            changed_paths=result.changed_paths,
            result_summary=result.error or "Local Codex failed.",
            result_payload=payload,
        )
    except Exception:
        return


def _cleanup_local_worktree(git: str, worktree_path: Path) -> None:
    _run(
        [git, "worktree", "remove", "--force", str(worktree_path)],
        timeout=60.0,
    )
    if worktree_path.exists():
        shutil.rmtree(worktree_path, ignore_errors=True)


def _resolve_binary(bin_path: str) -> str:
    clean = str(bin_path or "").strip() or _DEFAULT_CODEX_BIN
    if "/" in clean:
        candidate = Path(clean).expanduser()
        return str(candidate) if candidate.exists() else ""
    return shutil.which(clean) or ""


def _codex_config_args(config: CodexConfig) -> list[str]:
    args: list[str] = []
    if config.model:
        args.extend(["-c", f"model={json.dumps(config.model)}"])
    return args


def _codex_reasoning_args(reasoning_effort: str) -> list[str]:
    clean = str(reasoning_effort or "").strip().lower()
    if clean not in {"low", "medium", "high", "xhigh"}:
        return []
    return ["-c", f"model_reasoning_effort={json.dumps(clean)}"]


def _display_command(args: list[str]) -> str:
    display: list[str] = []
    for index, arg in enumerate(args):
        text = str(arg)
        if index == len(args) - 1 and len(text) > 240:
            text = "<prompt>"
        display.append(shlex.quote(_sanitize(text)))
    return " ".join(display)


def _sanitize(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"\b(sk-[A-Za-z0-9_-]{4})[A-Za-z0-9_*-]+", r"\1***", text)
    text = re.sub(
        r"(?i)\b(api[_-]?key|access[_-]?token|authorization|bearer)\s*[:=]\s*\S+",
        r"\1=***",
        text,
    )
    return text


def _summarize_error(stdout: str, stderr: str) -> str:
    text = (stderr or stdout or "").strip()
    if not text:
        return "command_failed"
    return text.splitlines()[0][:500]


def _coerce_int(value: object, default: int, *, minimum: int) -> int:
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, parsed)


def _coerce_float(value: object, default: float, *, minimum: float) -> float:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, parsed)


def _codex_home_policy(value: object = None) -> str:
    clean = str(
        value
        or os.getenv("NBLANE_CODEX_HOME_POLICY")
        or ""
    ).strip().lower()
    if clean in {"profile", "isolated", "profile_isolated", "web_profile"}:
        return _CODEX_HOME_POLICY_PROFILE
    return _CODEX_HOME_POLICY_DEFAULT


def _config_from_mapping(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "bin_path": str(data.get("bin_path") or data.get("bin") or "").strip(),
        "cloud_env_id": str(
            data.get("cloud_env_id") or data.get("env_id") or ""
        ).strip(),
        "model": str(data.get("model") or "").strip(),
        "attempts": _coerce_int(data.get("attempts"), _DEFAULT_ATTEMPTS, minimum=1),
        "branch": str(data.get("branch") or "").strip(),
        "timeout_seconds": _coerce_float(
            data.get("timeout_seconds"),
            _DEFAULT_TIMEOUT_SECONDS,
            minimum=5.0,
        ),
    }


def _reject_secret_config_keys(value: Any, *, path: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            current_path = f"{path}.{key_text}" if path else key_text
            if _SECRET_CONFIG_KEY_RE.search(key_text):
                raise ValueError(
                    f"Codex profile config must not store secret field `{current_path}`."
                )
            _reject_secret_config_keys(child, path=current_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_config_keys(child, path=f"{path}[{index}]")


def _validate_raw_numeric_field(
    data: dict[str, Any],
    key: str,
    parser: type[int] | type[float],
) -> None:
    if key not in data or data.get(key) in (None, ""):
        return
    try:
        parsed = parser(str(data.get(key)).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Codex config field `{key}` must be numeric.") from exc
    minimum = 1 if parser is int else 5.0
    if parsed < minimum:
        raise ValueError(f"Codex config field `{key}` must be at least {minimum:g}.")


def _profile_config_values(profile: str | None) -> dict[str, Any]:
    if not profile:
        return {}
    path = profile_config_path(profile)
    if not path.exists():
        return {}
    try:
        raw = _load_yaml_dict(path) or {}
        data = raw.get("codex") if isinstance(raw.get("codex"), dict) else raw
        if not isinstance(data, dict):
            return {}
        return _profile_overrides_from_mapping(data)
    except Exception:
        return {}


def _profile_overrides_from_mapping(data: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    if "bin_path" in data or "bin" in data:
        values["bin_path"] = str(data.get("bin_path") or data.get("bin") or "").strip()
    if "cloud_env_id" in data or "env_id" in data:
        values["cloud_env_id"] = str(
            data.get("cloud_env_id") or data.get("env_id") or ""
        ).strip()
    if "model" in data:
        values["model"] = str(data.get("model") or "").strip()
    if "attempts" in data and data.get("attempts") not in (None, ""):
        values["attempts"] = _coerce_int(
            data.get("attempts"),
            _DEFAULT_ATTEMPTS,
            minimum=1,
        )
    if "branch" in data:
        values["branch"] = str(data.get("branch") or "").strip()
    if "timeout_seconds" in data and data.get("timeout_seconds") not in (None, ""):
        values["timeout_seconds"] = _coerce_float(
            data.get("timeout_seconds"),
            _DEFAULT_TIMEOUT_SECONDS,
            minimum=5.0,
        )
    return values


def _codex_value(
    key: str,
    env_name: str,
    default: object,
    profile_values: dict[str, Any],
    include_runtime: bool = True,
) -> object:
    if include_runtime and key in _RUNTIME_OVERRIDES:
        return _RUNTIME_OVERRIDES[key]
    profile_value = profile_values.get(key)
    if profile_value not in (None, ""):
        return profile_value
    return os.getenv(env_name, default)


def _env_value(value: object) -> str:
    text = str(value or "")
    if not text or re.fullmatch(r"[A-Za-z0-9_./:@+-]+", text):
        return text
    return json.dumps(text)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _find_task_id_in_json(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("cloud_task_id", "task_id", "id"):
            candidate = str(value.get(key) or "").strip()
            if candidate:
                return candidate
        for child in value.values():
            candidate = _find_task_id_in_json(child)
            if candidate:
                return candidate
    if isinstance(value, list):
        for child in value:
            candidate = _find_task_id_in_json(child)
            if candidate:
                return candidate
    return ""


def _agent_status_from_cloud_status(text: str) -> str | None:
    clean = str(text or "").lower()
    if re.search(r"\b(failed|failure|cancelled|canceled)\b", clean):
        return "failed"
    return None


__all__ = [
    "CodexCloudResult",
    "CodexCommandResult",
    "CodexConfig",
    "CodexLocalResult",
    "CodexReadonlyResult",
    "CodexStatus",
    "CODEX_PROFILE_CONFIG_FILENAME",
    "codex_auth_path",
    "codex_cli_config_path",
    "codex_home",
    "codex_status",
    "configure",
    "current_config",
    "current_config_dict",
    "install_codex",
    "install_command",
    "load_codex_cli_config_text",
    "load_profile_config",
    "login_with_api_key",
    "parse_cloud_task_id",
    "parse_diff_changed_paths",
    "profile_codex_home",
    "profile_config_template",
    "profile_config_path",
    "readable_codex_error",
    "refresh_codex_cloud_task",
    "run_local_codex_task",
    "run_readonly_codex_prompt",
    "save_codex_cli_config_text",
    "save_config_to_env",
    "save_profile_config",
    "save_profile_config_text",
    "submit_codex_cloud_task",
    "validate_codex_cli_config_text",
    "validate_profile_config_text",
]
