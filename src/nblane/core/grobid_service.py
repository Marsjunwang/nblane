"""Manage a self-hosted GROBID container as a rootless Podman user service.

The admin Settings page installs, starts, stops and monitors GROBID without
root: the container is described by a Podman Quadlet file in
``~/.config/containers/systemd/<unit>.container`` and run by the service
user's own ``systemd --user`` instance (requires ``loginctl enable-linger``).

The PDF structure backend choice (``auto`` / ``grobid`` / ``pymupdf``) made in
the UI is stored in ``<service dir>/settings.json`` and takes precedence over
``NBLANE_RESEARCH_PDF_BACKEND`` so the Reader sidecar and the SPA backend
always agree, whatever their unit files say.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


IMAGE = "docker.io/grobid/grobid:0.9.0-crf"
IMAGE_DIGEST = "sha256:24ba90eb1c959f65d812bcdb2cf79c677fa5fd7b95235de616b8bc9fa1317849"
IMAGE_SIZE_BYTES = 1_690_000_000
MIN_RAM_MB = 3072
DEFAULT_UNIT = "nblane-grobid"
DEFAULT_URL = "http://127.0.0.1:8070"
BACKENDS = ("auto", "grobid", "pymupdf")
_LOOPBACK = {"127.0.0.1", "localhost", "::1"}


class GrobidServiceError(RuntimeError):
    """User-facing GROBID management failure (message is safe to show)."""


# ------------------------------------------------------------------ config


def _clean_env(name: str) -> str:
    return str(os.getenv(name, "") or "").strip()


def service_dir() -> Path:
    value = _clean_env("NBLANE_GROBID_SERVICE_DIR")
    if value:
        return Path(value).expanduser()
    return Path.home() / ".local" / "share" / "nblane" / "grobid"


def unit_name() -> str:
    value = _clean_env("NBLANE_GROBID_UNIT") or DEFAULT_UNIT
    safe = "".join(ch for ch in value if ch.isalnum() or ch in "-_")
    return safe or DEFAULT_UNIT


def service_url() -> str:
    """Return the configured GROBID URL (ignores the backend switch)."""

    value = _clean_env("NBLANE_GROBID_URL")
    if not value or value.lower() in {"off", "none"}:
        return DEFAULT_URL
    return value.rstrip("/")


def managed_port() -> int | None:
    """Return the host port nblane may manage, or None for remote URLs."""

    parsed = urlparse(service_url())
    if parsed.hostname not in _LOOPBACK:
        return None
    return parsed.port or 8070


def autostart_enabled() -> bool:
    """Start the managed unit at boot (off for isolated dev stacks)."""

    return _clean_env("NBLANE_GROBID_AUTOSTART").lower() not in {"0", "false", "no", "off"}


def quadlet_path() -> Path:
    base = Path(_clean_env("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "containers" / "systemd" / f"{unit_name()}.container"


def _settings_path() -> Path:
    return service_dir() / "settings.json"


_SETTINGS_CACHE: dict[str, Any] = {"key": None, "value": {}}


def _settings() -> dict[str, Any]:
    path = _settings_path()
    try:
        key = (str(path), path.stat().st_mtime_ns)
    except OSError:
        return {}
    if _SETTINGS_CACHE["key"] != key:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        _SETTINGS_CACHE.update(key=key, value=data if isinstance(data, dict) else {})
    return dict(_SETTINGS_CACHE["value"])


def backend_override() -> str:
    """Return the UI-selected PDF backend, or "" when none was chosen."""

    value = str(_settings().get("pdf_backend") or "").strip().lower()
    return value if value in BACKENDS else ""


def set_backend(value: str) -> None:
    clean = str(value or "").strip().lower()
    if clean and clean not in BACKENDS:
        raise GrobidServiceError("未知的 PDF 结构后端。")
    data = _settings()
    data["pdf_backend"] = clean
    data["updated"] = time.time()
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(path)
    _SETTINGS_CACHE.update(key=None, value={})


# ------------------------------------------------------------- subprocesses


def _user_env() -> dict[str, str]:
    """Environment that reaches the service user's systemd/podman."""

    env = dict(os.environ)
    uid = os.getuid()
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{uid}")
    env.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path=/run/user/{uid}/bus")
    return env


def _run(args: list[str], *, timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args, capture_output=True, text=True, timeout=timeout,
            env=_user_env(), stdin=subprocess.DEVNULL, check=False,
        )
    except FileNotFoundError as exc:
        raise GrobidServiceError(f"找不到命令 {args[0]}。") from exc
    except subprocess.TimeoutExpired as exc:
        raise GrobidServiceError(f"{args[0]} 执行超时。") from exc


def _systemctl(*args: str, timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    return _run(["systemctl", "--user", *args], timeout=timeout)


def podman_available() -> bool:
    return shutil.which("podman") is not None


def user_manager_running() -> bool:
    if shutil.which("systemctl") is None:
        return False
    try:
        result = _systemctl("is-system-running", timeout=10)
    except GrobidServiceError:
        return False
    return result.stdout.strip() in {"running", "degraded", "starting"}


def image_present() -> bool:
    if not podman_available():
        return False
    try:
        return _run(["podman", "image", "exists", IMAGE], timeout=20).returncode == 0
    except GrobidServiceError:
        return False


# ------------------------------------------------------------------ status


def _unit_state() -> dict[str, Any]:
    if not quadlet_path().is_file() or shutil.which("systemctl") is None:
        return {"installed": False, "active_state": "", "sub_state": "", "memory_mb": 0, "since": "", "restarts": 0}
    try:
        result = _systemctl(
            "show", f"{unit_name()}.service",
            "-p", "LoadState,ActiveState,SubState,MemoryCurrent,ActiveEnterTimestamp,NRestarts,Result",
            timeout=10,
        )
    except GrobidServiceError:
        return {"installed": True, "active_state": "unknown", "sub_state": "", "memory_mb": 0, "since": "", "restarts": 0}
    props = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    try:
        memory_mb = int(props.get("MemoryCurrent") or 0) // (1024 * 1024)
    except ValueError:
        memory_mb = 0  # "[not set]"
    try:
        restarts = int(props.get("NRestarts") or 0)
    except ValueError:
        restarts = 0
    return {
        "installed": props.get("LoadState") == "loaded",
        "active_state": props.get("ActiveState", ""),
        "sub_state": props.get("SubState", ""),
        "result": props.get("Result", ""),
        "memory_mb": memory_mb,
        "since": props.get("ActiveEnterTimestamp", ""),
        "restarts": restarts,
    }


def _probe(url: str, path: str, timeout: float = 3.0) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(f"{url}{path}", timeout=timeout) as response:
            body = response.read(200).decode("utf-8", errors="ignore").strip()
            return response.status < 500, body
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False, ""


def _version(url: str) -> str:
    raw = _probe(url, "/api/version")[1]
    try:
        data = json.loads(raw)
    except ValueError:
        return raw[:40]
    return str(data.get("version") or "")[:40] if isinstance(data, dict) else ""


def effective_backend() -> str:
    """Return the backend actually used (UI override > env > auto)."""

    override = backend_override()
    if override:
        return override
    raw = _clean_env("NBLANE_RESEARCH_PDF_BACKEND").lower()
    backend = raw if raw in BACKENDS else "auto"
    if backend == "auto" and _clean_env("NBLANE_GROBID_URL").lower() in {"off", "none"}:
        backend = "pymupdf"
    return backend


def status() -> dict[str, Any]:
    """Return a display-ready snapshot for the admin Settings page."""

    url = service_url()
    alive, body = _probe(url, "/api/isalive")
    alive = alive and (not body or "true" in body.lower())
    version = _version(url) if alive else ""
    unit = _unit_state()
    port = managed_port()
    managed_active = unit["installed"] and unit["active_state"] in {"active", "activating", "reloading"}
    if unit["installed"] and unit["active_state"] == "activating":
        state = "starting"
    elif alive and managed_active:
        state = "running"
    elif alive:
        state = "external"  # healthy, but not run by our unit (e.g. root Docker)
    elif unit["installed"] and unit["active_state"] == "failed":
        state = "failed"
    elif managed_active:
        state = "starting"  # container up, JVM still loading models
    elif unit["installed"]:
        state = "stopped"
    else:
        state = "not_installed"
    from nblane.core.ai.local_models import available_ram_mb, total_ram_mb

    job = install_state()
    return {
        "state": state,
        "alive": alive,
        "version": version,
        "url": url,
        "manageable": port is not None,
        "port": port or 0,
        "unit": unit_name(),
        "unit_state": unit,
        "image": IMAGE,
        "image_present": image_present(),
        "podman_available": podman_available(),
        "user_manager": user_manager_running(),
        "backend": effective_backend(),
        "backend_override": backend_override(),
        "env_backend": _clean_env("NBLANE_RESEARCH_PDF_BACKEND").lower(),
        "total_ram_mb": total_ram_mb(),
        "available_ram_mb": available_ram_mb(),
        "min_ram_mb": MIN_RAM_MB,
        "install": job,
        "blocker": install_blocker(alive=alive),
    }


def install_blocker(*, alive: bool | None = None) -> str:
    """Return why the managed service cannot be installed (empty if it can)."""

    if managed_port() is None:
        return "GROBID 地址不是本机，只能监控，不能在这里安装。"
    if not podman_available():
        return "服务器未安装 Podman（sudo apt-get install -y podman）。"
    if not user_manager_running():
        return "服务用户的 systemd --user 未运行，需要 sudo loginctl enable-linger <用户>。"
    return ""


def logs(lines: int = 60) -> str:
    """Return the tail of the unit journal (admin-only troubleshooting)."""

    if not quadlet_path().is_file():
        return ""
    try:
        result = _run(
            ["journalctl", "--user", "-u", f"{unit_name()}.service", "-n", str(max(1, min(200, lines))),
             "--no-pager", "-o", "cat"],
            timeout=10,
        )
    except GrobidServiceError:
        return ""
    return result.stdout[-20000:]


# ------------------------------------------------------------- lifecycle


def quadlet_text() -> str:
    port = managed_port()
    if port is None:
        raise GrobidServiceError("GROBID 地址不是本机，不能托管。")
    return (
        "# Managed by nblane (Settings → GROBID). Edits are overwritten on reinstall.\n"
        "[Unit]\n"
        "Description=nblane GROBID (PDF structure extraction)\n"
        "After=network-online.target\n\n"
        "[Container]\n"
        f"Image={IMAGE}\n"
        f"ContainerName={unit_name()}\n"
        f"PublishPort=127.0.0.1:{port}:8070\n"
        "Pull=never\n\n"
        "[Service]\n"
        "# The JVM exits 143 on SIGTERM; a normal stop is not a failure.\n"
        "SuccessExitStatus=143\n"
        "Restart=on-failure\n"
        "RestartSec=10\n"
        "TimeoutStartSec=300\n"
        + ("\n[Install]\nWantedBy=default.target\n" if autostart_enabled() else "")
    )


def _port_in_use_by_other() -> bool:
    port = managed_port()
    if port is None:
        return False
    unit = _unit_state()
    if unit["installed"] and unit["active_state"] in {"active", "activating"}:
        return False
    alive, _ = _probe(service_url(), "/api/isalive", timeout=1.0)
    return alive


def write_unit() -> Path:
    path = quadlet_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(quadlet_text(), encoding="utf-8")
    result = _systemctl("daemon-reload")
    if result.returncode != 0:
        raise GrobidServiceError(f"systemctl --user daemon-reload 失败：{result.stderr.strip()[:200]}")
    return path


def start() -> None:
    blocker = install_blocker()
    if blocker:
        raise GrobidServiceError(blocker)
    if not quadlet_path().is_file():
        raise GrobidServiceError("尚未安装，请先点「安装」。")
    # Units written by an older nblane get the current template on start.
    if quadlet_path().read_text(encoding="utf-8") != quadlet_text():
        write_unit()
    _systemctl("reset-failed", f"{unit_name()}.service", timeout=10)
    if _port_in_use_by_other():
        raise GrobidServiceError(
            f"端口 {managed_port()} 已有其他 GROBID 在运行（不是由 nblane 管理，例如 root Docker 容器）。"
            "请先停掉它再启动。"
        )
    # --no-block: the JVM needs ~45s; the UI polls status instead of waiting.
    result = _systemctl("start", "--no-block", f"{unit_name()}.service")
    if result.returncode != 0:
        raise GrobidServiceError(f"启动失败：{result.stderr.strip()[:200]}")


def stop() -> None:
    if not quadlet_path().is_file():
        raise GrobidServiceError("GROBID 不是由 nblane 管理的，无法在这里停止。")
    result = _systemctl("stop", f"{unit_name()}.service", timeout=60)
    if result.returncode != 0:
        raise GrobidServiceError(f"停止失败：{result.stderr.strip()[:200]}")


def restart() -> None:
    if not quadlet_path().is_file():
        raise GrobidServiceError("GROBID 不是由 nblane 管理的，无法在这里重启。")
    result = _systemctl("restart", "--no-block", f"{unit_name()}.service")
    if result.returncode != 0:
        raise GrobidServiceError(f"重启失败：{result.stderr.strip()[:200]}")


def uninstall() -> None:
    """Stop the unit and remove its Quadlet file (the image is kept)."""

    path = quadlet_path()
    if not path.is_file():
        return
    _systemctl("stop", f"{unit_name()}.service", timeout=60)
    path.unlink(missing_ok=True)
    _systemctl("daemon-reload")


# --------------------------------------------------------------- installer


_INSTALL: dict[str, Any] = {}
_INSTALL_LOCK = threading.RLock()


def install_state() -> dict[str, Any]:
    with _INSTALL_LOCK:
        return dict(_INSTALL)


def start_install(*, autostart: bool = True) -> dict[str, Any]:
    """Pull the image if needed, write the unit and optionally start it."""

    blocker = install_blocker()
    if blocker:
        raise GrobidServiceError(blocker)
    with _INSTALL_LOCK:
        if _INSTALL.get("status") == "running":
            return dict(_INSTALL)
        _INSTALL.clear()
        _INSTALL.update(status="running", phase="image", error="", started_at=time.time())
    thread = threading.Thread(target=_run_install, args=(autostart,), name="grobid-install", daemon=True)
    thread.start()
    return install_state()


def _update(**fields: Any) -> None:
    with _INSTALL_LOCK:
        _INSTALL.update(fields)


def _run_install(autostart: bool) -> None:
    try:
        if not image_present():
            _update(phase="image")
            # Docker Hub through the service proxy; ~1.7GB, can take minutes.
            result = _run(["podman", "pull", IMAGE], timeout=3600)
            if result.returncode != 0:
                raise GrobidServiceError(
                    "拉取镜像失败：" + (result.stderr.strip().splitlines() or ["未知错误"])[-1][:200]
                    + "（检查服务的 https_proxy 或 Docker Hub 镜像源）"
                )
        _update(phase="unit")
        write_unit()
        if autostart:
            _update(phase="start")
            start()
        _update(status="done", phase="done")
    except Exception as exc:  # surfaced to the admin UI
        message = str(exc) if isinstance(exc, GrobidServiceError) else f"安装失败：{exc}"
        _update(status="failed", error=message[:300])


__all__ = [
    "BACKENDS",
    "GrobidServiceError",
    "IMAGE",
    "backend_override",
    "effective_backend",
    "install_blocker",
    "logs",
    "managed_port",
    "quadlet_path",
    "quadlet_text",
    "restart",
    "service_url",
    "set_backend",
    "start",
    "start_install",
    "status",
    "stop",
    "uninstall",
    "unit_name",
]
