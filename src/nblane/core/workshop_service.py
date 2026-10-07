"""Manage the workshop web terminal (ttyd + a dedicated tmux server).

Settings → 车间 installs ttyd (pinned release, checksum-verified), writes a
dedicated tmux config, a start script and a ``systemd --user`` unit, and
adjusts terminal options without root.

Isolation: the tmux server runs on its own socket (``tmux -L <socket> -f
<service dir>/tmux.conf``), so it never reads or changes ``~/.tmux.conf``
or the user's other tmux sessions.

Survival: the unit uses ``KillMode=process`` — restarting ttyd (after a
settings change) never kills the tmux server, so agents running in the
workshop keep going and browsers simply reconnect.

The SPA page talks to the terminal two ways: the browser loads ttyd through
the authenticated ``/terminal/`` proxy (``web_api/workshop_terminal.py``),
and the mobile key bar / input box inject keys with ``tmux send-keys`` /
``paste-buffer`` (whitelisted key names only).
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


TTYD_VERSION = "1.7.7"
# sha256 of the release assets (github.com/tsl0922/ttyd/releases/1.7.7, SHA256SUMS).
TTYD_SHA256 = {
    "x86_64": "8a217c968aba172e0dbf3f34447218dc015bc4d5e59bf51db2f2cd12b7be4f55",
    "aarch64": "b38acadd89d1d396a0f5649aa52c539edbad07f4bc7348b27b4f4b7219dd4165",
}
TTYD_URL = "https://github.com/tsl0922/ttyd/releases/download/{version}/ttyd.{arch}"
DEFAULT_UNIT = "nblane-workshop"
DEFAULT_PORT = 7668
DEFAULT_SOCKET = "nblane-workshop"
SESSION = "workshop"
MANAGED_MARKER = "# Managed by nblane (Settings → 车间)"
RENDERERS = ("canvas", "webgl", "dom")
MAX_INPUT_CHARS = 16000

# Terminal palette: the SPA's indigo chrome, so the frame has no seam.
THEME = {
    "background": "#0f172a",
    "foreground": "#e2e8f0",
    "cursor": "#e2e8f0",
    "selectionBackground": "#334155",
}

# Defaults chosen from the 2026-09 phone trials (phase0.5-remote-terminal.md)
# and the 2026-10 column measurements: on a 412px phone font 24 leaves only
# 25 columns (Claude Code's layout breaks), 16 gives ~37 and stays legible;
# canvas renderer + glyph rescale fixed the garbled CJK glyphs on Android GPUs;
# mouse off + no alternate screen is the only combination where touch
# scrolling reaches history. escape_time 10ms: tmux's 500ms default makes Esc
# lag in Claude Code / Codex.
DEFAULTS: dict[str, Any] = {
    "font_size_mobile": 16,
    "font_size_desktop": 15,
    "scrollback": 10000,
    "renderer": "canvas",
    "rescale_glyphs": True,
    "history_limit": 50000,
    "mouse": False,
    "native_scroll": True,
    "escape_time_ms": 10,
    "status_bar": True,
    "cwd": "",
}
_INT_LIMITS = {
    "font_size_mobile": (10, 40),
    "font_size_desktop": (10, 40),
    "scrollback": (1000, 100000),
    "history_limit": (1000, 200000),
    "escape_time_ms": (0, 500),
}
_BOOLS = ("rescale_glyphs", "mouse", "native_scroll", "status_bar")
# Options that live in the ttyd command line (a change restarts ttyd);
# the font sizes travel in the iframe URL instead.
_TTYD_KEYS = ("scrollback", "renderer", "rescale_glyphs", "cwd")

# Key bar: name → steps; each step is one ``tmux send-keys`` call. Double Esc
# is two steps so the agent sees two presses, not one ESC-ESC sequence.
KEYS: dict[str, list[list[str]]] = {
    "esc": [["Escape"]],
    "esc2": [["Escape"], ["Escape"]],
    "tab": [["Tab"]],
    "shift_tab": [["BTab"]],
    "enter": [["Enter"]],
    "up": [["Up"]],
    "down": [["Down"]],
    "left": [["Left"]],
    "right": [["Right"]],
    "page_up": [["PPage"]],
    "page_down": [["NPage"]],
    "ctrl_c": [["C-c"]],
    "ctrl_d": [["C-d"]],
    "ctrl_j": [["C-j"]],
    "ctrl_l": [["C-l"]],
    "ctrl_o": [["C-o"]],
    "ctrl_r": [["C-r"]],
    "ctrl_t": [["C-t"]],
    "ctrl_z": [["C-z"]],
}
_STEP_DELAY_SECONDS = 0.15


class WorkshopServiceError(RuntimeError):
    """User-facing workshop management failure (message is safe to show)."""


# ------------------------------------------------------------------ config


def _clean_env(name: str) -> str:
    return str(os.getenv(name, "") or "").strip()


def service_dir() -> Path:
    value = _clean_env("NBLANE_WORKSHOP_SERVICE_DIR")
    if value:
        return Path(value).expanduser()
    return Path.home() / ".local" / "share" / "nblane" / "workshop"


def unit_name() -> str:
    value = _clean_env("NBLANE_WORKSHOP_UNIT") or DEFAULT_UNIT
    safe = "".join(ch for ch in value if ch.isalnum() or ch in "-_")
    return safe or DEFAULT_UNIT


def port() -> int:
    try:
        value = int(_clean_env("NBLANE_WORKSHOP_PORT") or DEFAULT_PORT)
    except ValueError:
        return DEFAULT_PORT
    return value if 1024 <= value <= 65535 else DEFAULT_PORT


def upstream_url() -> str:
    """Loopback address of ttyd (the proxy target and liveness probe)."""

    value = _clean_env("NBLANE_WORKSHOP_PROBE_URL")
    return (value or f"http://127.0.0.1:{port()}").rstrip("/")


def tmux_socket() -> str:
    value = _clean_env("NBLANE_WORKSHOP_TMUX_SOCKET") or DEFAULT_SOCKET
    safe = "".join(ch for ch in value if ch.isalnum() or ch in "-_")
    return safe or DEFAULT_SOCKET


def autostart_enabled() -> bool:
    """Start the unit at boot (off for isolated dev stacks)."""

    return _clean_env("NBLANE_WORKSHOP_AUTOSTART").lower() not in {"0", "false", "no", "off"}


def unit_path() -> Path:
    base = Path(_clean_env("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "systemd" / "user" / f"{unit_name()}.service"


def tmux_conf_path() -> Path:
    return service_dir() / "tmux.conf"


def start_script_path() -> Path:
    return service_dir() / "start.sh"


def ttyd_path() -> Path:
    return service_dir() / "bin" / "ttyd"


def _settings_path() -> Path:
    return service_dir() / "settings.json"


def caddyfile_path() -> Path:
    return Path(_clean_env("NBLANE_CADDYFILE") or "/etc/caddy/Caddyfile")


def machine_arch() -> str:
    raw = platform.machine().lower()
    return {"amd64": "x86_64", "arm64": "aarch64"}.get(raw, raw)


# ---------------------------------------------------------------- settings


def _coerce(key: str, value: Any, *, strict: bool) -> Any:
    """Validate one setting; strict raises, lenient falls back to default."""

    def bad(message: str) -> Any:
        if strict:
            raise WorkshopServiceError(message)
        return DEFAULTS[key]

    if key in _INT_LIMITS:
        low, high = _INT_LIMITS[key]
        if isinstance(value, bool):
            return bad(f"{key} 必须是整数。")
        try:
            number = int(value)
        except (TypeError, ValueError):
            return bad(f"{key} 必须是整数。")
        if not low <= number <= high:
            return bad(f"{key} 需在 {low}–{high} 之间。")
        return number
    if key in _BOOLS:
        if isinstance(value, bool):
            return value
        return bad(f"{key} 必须是开关值。")
    if key == "renderer":
        clean = str(value or "").strip().lower()
        return clean if clean in RENDERERS else bad("未知的渲染方式。")
    if key == "cwd":
        clean = str(value or "").strip()
        if not clean:
            return ""
        path = Path(clean).expanduser()
        if not path.is_absolute() or not path.is_dir():
            return bad("工作目录必须是服务器上已存在的绝对路径。")
        return str(path)
    return bad(f"未知设置项 {key}。")


def settings() -> dict[str, Any]:
    """Current settings (stored values over defaults; invalid ones dropped)."""

    try:
        stored = json.loads(_settings_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        stored = {}
    if not isinstance(stored, dict):
        stored = {}
    return {key: _coerce(key, stored.get(key, default), strict=False) for key, default in DEFAULTS.items()}


def _write_atomic(path: Path, text: str, *, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    if mode is not None:
        tmp.chmod(mode)
    tmp.replace(path)


def save_settings(patch: dict[str, Any]) -> dict[str, Any]:
    """Validate and store *patch*; apply it live when the service is managed.

    Returns what had to happen: ``tmux_reloaded`` (tmux options sourced into
    the running server), ``ttyd_restarted`` (ttyd options changed; the tmux
    sessions survive), ``reattach_needed`` (scroll mode only reaches clients
    that attach after the change — reload the workshop page).
    """

    unknown = sorted(set(patch) - set(DEFAULTS))
    if unknown:
        raise WorkshopServiceError(f"未知设置项：{', '.join(unknown)}。")
    current = settings()
    merged = dict(current)
    for key, value in patch.items():
        merged[key] = _coerce(key, value, strict=True)
    _write_atomic(_settings_path(), json.dumps(merged, ensure_ascii=False, indent=1))
    result = {"tmux_reloaded": False, "ttyd_restarted": False, "reattach_needed": False}
    if not is_managed():
        return result
    if tmux_conf_text(merged) != tmux_conf_text(current):
        write_tmux_conf(merged)
        result["tmux_reloaded"] = reload_tmux()
        result["reattach_needed"] = merged["native_scroll"] != current["native_scroll"]
    # The start script always mirrors the settings (e.g. the desktop font size
    # used by direct /terminal/ visits); ttyd only restarts for its own options.
    write_start_script(merged)
    if any(merged[key] != current[key] for key in _TTYD_KEYS):
        if _unit_state()["active_state"] in {"active", "activating"}:
            restart()
            result["ttyd_restarted"] = True
    return result


# ------------------------------------------------------------- subprocesses


def _user_env() -> dict[str, str]:
    """Environment that reaches the service user's systemd and tmux."""

    env = dict(os.environ)
    uid = os.getuid()
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{uid}")
    env.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path=/run/user/{uid}/bus")
    # Never inherit a TMUX of whoever started the API: -L picks the server.
    env.pop("TMUX", None)
    return env


def _run(
    args: list[str], *, timeout: float = 30.0, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args, capture_output=True, text=True, timeout=timeout, env=_user_env(),
            input=input_text, stdin=None if input_text is not None else subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError as exc:
        raise WorkshopServiceError(f"找不到命令 {args[0]}。") from exc
    except subprocess.TimeoutExpired as exc:
        raise WorkshopServiceError(f"{args[0]} 执行超时。") from exc


def _systemctl(*args: str, timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    return _run(["systemctl", "--user", *args], timeout=timeout)


def tmux_binary() -> str:
    return shutil.which("tmux") or ""


def _tmux(*args: str, timeout: float = 10.0, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    binary = tmux_binary()
    if not binary:
        raise WorkshopServiceError("服务器未安装 tmux。")
    return _run([binary, "-L", tmux_socket(), *args], timeout=timeout, input_text=input_text)


def user_manager_running() -> bool:
    if shutil.which("systemctl") is None:
        return False
    try:
        result = _systemctl("is-system-running", timeout=10)
    except WorkshopServiceError:
        return False
    return result.stdout.strip() in {"running", "degraded", "starting"}


def session_alive() -> bool:
    if not tmux_binary():
        return False
    try:
        return _tmux("has-session", "-t", f"={SESSION}").returncode == 0
    except WorkshopServiceError:
        return False


def _version_of(args: list[str]) -> str:
    try:
        result = _run(args, timeout=10)
    except WorkshopServiceError:
        return ""
    text = (result.stdout or result.stderr).strip().splitlines()
    return text[0][:60] if text else ""


# ------------------------------------------------------------- generation


def tmux_conf_text(values: dict[str, Any] | None = None) -> str:
    s = values or settings()
    overrides = "xterm*:Tc:smcup@:rmcup@" if s["native_scroll"] else "xterm*:Tc"
    return "\n".join([
        f"{MANAGED_MARKER}. Regenerated on save; edits are overwritten.",
        f"# Dedicated server: tmux -L {tmux_socket()} -f <this file>; ~/.tmux.conf is not read.",
        'set -g default-terminal "tmux-256color"',
        "# Tc: true colour. smcup@/rmcup@ (scroll mode): paint into xterm.js's normal",
        "# buffer so browser scrolling (wheel and touch) reaches history.",
        f"set -g terminal-overrides '{overrides}'",
        f"set -sg escape-time {s['escape_time_ms']}",
        f"set -g history-limit {s['history_limit']}",
        f"set -g mouse {'on' if s['mouse'] else 'off'}",
        f"set -g status {'on' if s['status_bar'] else 'off'}",
        "set -g focus-events on",
        "set -g window-size latest",
        "# prefix + R: force a full redraw when a resize leaves stale frames.",
        "bind R refresh-client",
        "",
    ])


def ttyd_command(values: dict[str, Any] | None = None, *, binary: str | None = None) -> list[str]:
    s = values or settings()
    tmux = tmux_binary() or "tmux"
    command = [
        binary or str(ttyd_path()),
        "-W",
        "-i", "127.0.0.1",
        "-p", str(port()),
        "-t", f"fontSize={s['font_size_desktop']}",
        "-t", f"scrollback={s['scrollback']}",
        "-t", f"rendererType={s['renderer']}",
        "-t", f"rescaleOverlappingGlyphs={'true' if s['rescale_glyphs'] else 'false'}",
        # tmux keeps the session; the "leave site?" prompt only gets in the way.
        "-t", "disableLeaveAlert=true",
        "-t", "theme=" + json.dumps(THEME, separators=(",", ":")),
        "--",
        tmux, "-L", tmux_socket(), "-f", str(tmux_conf_path()),
        "new-session", "-A", "-s", SESSION,
    ]
    if s["cwd"]:
        command += ["-c", s["cwd"]]
    return command


def start_script_text(values: dict[str, Any] | None = None) -> str:
    s = values or settings()
    tmux = tmux_binary() or "tmux"
    reload_cmd = shlex.join([tmux, "-L", tmux_socket(), "source-file", str(tmux_conf_path())])
    return (
        "#!/bin/sh\n"
        f"{MANAGED_MARKER}. Regenerated on save; edits are overwritten.\n"
        "# A tmux server that outlived a restart picks up the current config.\n"
        f"{reload_cmd} >/dev/null 2>&1 || true\n"
        f"exec {shlex.join(ttyd_command(s))}\n"
    )


def unit_text() -> str:
    return (
        f"{MANAGED_MARKER}. Edits are overwritten on reinstall.\n"
        "[Unit]\n"
        "Description=nblane workshop web terminal (ttyd + tmux)\n"
        "After=network-online.target\n\n"
        "[Service]\n"
        "Type=simple\n"
        f'ExecStart="{start_script_path()}"\n'
        "Restart=always\n"
        "RestartSec=3\n"
        "# Stop/restart only ttyd: the tmux server and the agents in it keep running.\n"
        "KillMode=process\n"
        + ("\n[Install]\nWantedBy=default.target\n" if autostart_enabled() else "")
    )


def write_tmux_conf(values: dict[str, Any] | None = None) -> None:
    _write_atomic(tmux_conf_path(), tmux_conf_text(values))


def write_start_script(values: dict[str, Any] | None = None) -> None:
    _write_atomic(start_script_path(), start_script_text(values), mode=0o755)


def reload_tmux() -> bool:
    """Source the config into a running workshop tmux server (if any)."""

    if not session_alive():
        return False
    try:
        return _tmux("source-file", str(tmux_conf_path())).returncode == 0
    except WorkshopServiceError:
        return False


# ------------------------------------------------------------------ status


def _unit_file_text() -> str:
    try:
        return unit_path().read_text(encoding="utf-8")
    except OSError:
        return ""


def is_managed() -> bool:
    return MANAGED_MARKER in _unit_file_text()


def _unit_state() -> dict[str, Any]:
    empty = {"installed": False, "active_state": "", "sub_state": "", "since": "", "restarts": 0}
    if not unit_path().is_file() or shutil.which("systemctl") is None:
        return empty
    try:
        result = _systemctl(
            "show", f"{unit_name()}.service",
            "-p", "LoadState,ActiveState,SubState,ActiveEnterTimestamp,NRestarts",
            timeout=10,
        )
    except WorkshopServiceError:
        return {**empty, "installed": True, "active_state": "unknown"}
    props = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    try:
        restarts = int(props.get("NRestarts") or 0)
    except ValueError:
        restarts = 0
    return {
        "installed": props.get("LoadState") == "loaded",
        "active_state": props.get("ActiveState", ""),
        "sub_state": props.get("SubState", ""),
        "since": props.get("ActiveEnterTimestamp", ""),
        "restarts": restarts,
    }


def probe(timeout: float = 2.0) -> bool:
    """Any HTTP answer from ttyd's port means the process is up."""

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"{upstream_url()}/", timeout=timeout) as response:
            return 100 <= response.status < 600
    except urllib.error.HTTPError:
        return True
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pinned_sha() -> str:
    return TTYD_SHA256.get(machine_arch(), "")


def ttyd_installed() -> bool:
    path = ttyd_path()
    return path.is_file() and bool(_pinned_sha()) and _sha256(path) == _pinned_sha()


def caddy_legacy_route() -> bool:
    """True when Caddy still proxies straight to ttyd (old basic_auth entry)."""

    try:
        text = caddyfile_path().read_text(encoding="utf-8")
    except OSError:
        return False
    return re.search(rf"reverse_proxy\s+(127\.0\.0\.1|localhost):{port()}\b", text) is not None


def happy_status() -> dict[str, Any]:
    """Happy Coder CLI presence (status only; pairing happens in a terminal)."""

    binary = shutil.which("happy") or ""
    if not binary:
        candidate = Path.home() / ".local" / "npm-global" / "bin" / "happy"
        binary = str(candidate) if candidate.is_file() else ""
    home = Path(_clean_env("HAPPY_HOME_DIR") or Path.home() / ".happy").expanduser()
    daemon_running = False
    try:
        state = json.loads((home / "daemon.state.json").read_text(encoding="utf-8"))
        pid = int(state.get("pid") or 0) if isinstance(state, dict) else 0
        if pid > 0:
            os.kill(pid, 0)
            daemon_running = True
    except (OSError, ValueError, TypeError):
        daemon_running = False
    return {
        "installed": bool(binary),
        "path": binary,
        "paired": (home / "access.key").is_file(),
        "daemon_running": daemon_running,
    }


def status() -> dict[str, Any]:
    """Display-ready snapshot for the admin Settings page."""

    unit = _unit_state()
    managed = is_managed()
    legacy = unit_path().is_file() and not managed
    reachable = probe()
    active = unit["active_state"]
    if legacy:
        state = "legacy"
    elif managed and active == "failed":
        state = "failed"
    elif managed and active in {"active", "activating", "reloading"}:
        state = "running" if reachable else "starting"
    elif managed:
        state = "stopped"
    elif reachable:
        state = "external"
    else:
        state = "not_installed"
    tmux = tmux_binary()
    return {
        "state": state,
        "reachable": reachable,
        "managed": managed,
        "unit": unit_name(),
        "unit_state": unit,
        "port": port(),
        "upstream": upstream_url(),
        "ttyd_version": TTYD_VERSION,
        "ttyd_installed": ttyd_installed(),
        "ttyd_path": str(ttyd_path()),
        "ttyd_download_url": TTYD_URL.format(version=TTYD_VERSION, arch=machine_arch()),
        "ttyd_sha256": _pinned_sha(),
        "arch": machine_arch(),
        "tmux_path": tmux,
        "tmux_version": _version_of([tmux, "-V"]) if tmux else "",
        "tmux_socket": tmux_socket(),
        "session": SESSION,
        "session_alive": session_alive(),
        "user_manager": user_manager_running(),
        "autostart": autostart_enabled(),
        "service_dir": str(service_dir()),
        "caddy_legacy_route": caddy_legacy_route(),
        "settings": settings(),
        "defaults": dict(DEFAULTS),
        "install": install_state(),
        "blocker": install_blocker(),
        "happy": happy_status(),
    }


def install_blocker() -> str:
    """Why the managed service cannot be installed here (empty if it can)."""

    if not tmux_binary():
        return "服务器未安装 tmux（sudo apt-get install -y tmux）。"
    if shutil.which("systemctl") is None or not user_manager_running():
        return "服务用户的 systemd --user 未运行，需要 sudo loginctl enable-linger <用户>。"
    if not ttyd_path().is_file() and not _pinned_sha():
        return f"没有适用于 {machine_arch()} 的 ttyd 预编译包，请手动安装后放到 {ttyd_path()}。"
    return ""


def logs(lines: int = 60) -> str:
    if not unit_path().is_file():
        return ""
    try:
        result = _run(
            ["journalctl", "--user", "-u", f"{unit_name()}.service", "-n", str(max(1, min(200, lines))),
             "--no-pager", "-o", "cat"],
            timeout=10,
        )
    except WorkshopServiceError:
        return ""
    return result.stdout[-20000:]


# ------------------------------------------------------------- lifecycle


def _require_managed(verb: str) -> None:
    if not is_managed():
        raise WorkshopServiceError(f"车间终端不是由 nblane 管理的，无法在这里{verb}。请先「安装 / 接管」。")


def write_unit() -> None:
    write_tmux_conf()
    write_start_script()
    _write_atomic(unit_path(), unit_text())
    result = _systemctl("daemon-reload")
    if result.returncode != 0:
        raise WorkshopServiceError(f"systemctl --user daemon-reload 失败：{result.stderr.strip()[:200]}")
    if autostart_enabled():
        _systemctl("enable", f"{unit_name()}.service")


def start() -> None:
    _require_managed("启动")
    _systemctl("reset-failed", f"{unit_name()}.service", timeout=10)
    result = _systemctl("start", f"{unit_name()}.service")
    if result.returncode != 0:
        raise WorkshopServiceError(f"启动失败：{result.stderr.strip()[:200]}")


def stop() -> None:
    _require_managed("停止")
    result = _systemctl("stop", f"{unit_name()}.service", timeout=30)
    if result.returncode != 0:
        raise WorkshopServiceError(f"停止失败：{result.stderr.strip()[:200]}")


def restart() -> None:
    _require_managed("重启")
    result = _systemctl("restart", "--no-block", f"{unit_name()}.service")
    if result.returncode != 0:
        raise WorkshopServiceError(f"重启失败：{result.stderr.strip()[:200]}")


def end_sessions() -> None:
    """Kill the dedicated tmux server (everything running in the workshop)."""

    if tmux_binary():
        _tmux("kill-server")


def uninstall(*, end_running_sessions: bool = False) -> None:
    """Stop and remove the unit; the binary and settings stay for reinstall."""

    _require_managed("移除")
    _systemctl("stop", f"{unit_name()}.service", timeout=30)
    _systemctl("disable", f"{unit_name()}.service")
    unit_path().unlink(missing_ok=True)
    _systemctl("daemon-reload")
    if end_running_sessions:
        end_sessions()


# --------------------------------------------------------------- key input


def _require_session() -> None:
    if not session_alive():
        raise WorkshopServiceError("车间 tmux 会话未运行：先打开车间终端，或在设置里启动车间服务。")


def send_keys(names: list[str]) -> None:
    """Send whitelisted keys to the active pane of the workshop session."""

    if not names or len(names) > 20:
        raise WorkshopServiceError("按键数量需在 1–20 之间。")
    unknown = [name for name in names if name not in KEYS]
    if unknown:
        raise WorkshopServiceError(f"不支持的按键：{', '.join(unknown)}。")
    _require_session()
    first = True
    for name in names:
        for step in KEYS[name]:
            if not first:
                time.sleep(_STEP_DELAY_SECONDS)
            first = False
            result = _tmux("send-keys", "-t", f"={SESSION}:", *step)
            if result.returncode != 0:
                raise WorkshopServiceError(f"发送按键失败：{result.stderr.strip()[:200]}")


def send_text(text: str, *, submit: bool) -> None:
    """Paste *text* like a terminal paste (bracketed when the app asks), then Enter."""

    clean = str(text or "").replace("\r\n", "\n")
    if not clean and not submit:
        raise WorkshopServiceError("没有要发送的内容。")
    if len(clean) > MAX_INPUT_CHARS:
        raise WorkshopServiceError(f"一次最多发送 {MAX_INPUT_CHARS} 个字符。")
    _require_session()
    if clean:
        buffer = "nblane-input"
        loaded = _tmux("load-buffer", "-b", buffer, "-", input_text=clean)
        if loaded.returncode != 0:
            raise WorkshopServiceError(f"写入输入缓冲失败：{loaded.stderr.strip()[:200]}")
        pasted = _tmux("paste-buffer", "-d", "-p", "-b", buffer, "-t", f"={SESSION}:")
        if pasted.returncode != 0:
            raise WorkshopServiceError(f"输入失败：{pasted.stderr.strip()[:200]}")
    if submit:
        if clean:
            # Let the app finish the paste before Enter (Claude Code collapses
            # long pastes and would otherwise swallow the keypress).
            time.sleep(_STEP_DELAY_SECONDS)
        result = _tmux("send-keys", "-t", f"={SESSION}:", "Enter")
        if result.returncode != 0:
            raise WorkshopServiceError(f"发送回车失败：{result.stderr.strip()[:200]}")


# --------------------------------------------------------------- installer


_INSTALL: dict[str, Any] = {}
_INSTALL_LOCK = threading.RLock()


def install_state() -> dict[str, Any]:
    with _INSTALL_LOCK:
        return dict(_INSTALL)


def _update(**fields: Any) -> None:
    with _INSTALL_LOCK:
        _INSTALL.update(fields)


def _download(url: str) -> bytes:
    """Fetch the release asset (honours the service's https_proxy)."""

    import httpx

    response = httpx.get(url, follow_redirects=True, timeout=180.0)
    response.raise_for_status()
    return response.content


def _ttyd_candidates() -> list[Path]:
    found = [shutil.which("ttyd"), str(Path.home() / ".local" / "bin" / "ttyd")]
    return [Path(item) for item in found if item and Path(item).is_file()]


def ensure_ttyd() -> str:
    """Place the pinned ttyd at ttyd_path(); returns how it got there."""

    target = ttyd_path()
    pinned = _pinned_sha()
    if ttyd_installed():
        return "present"
    if not pinned:
        if target.is_file():
            return "present"  # manually placed binary on an unpinned arch
        raise WorkshopServiceError(install_blocker() or "没有可用的 ttyd。")
    target.parent.mkdir(parents=True, exist_ok=True)
    for candidate in _ttyd_candidates():
        if _sha256(candidate) == pinned:
            shutil.copyfile(candidate, target)
            target.chmod(0o755)
            return "copied"
    url = _clean_env("NBLANE_WORKSHOP_TTYD_URL") or TTYD_URL.format(version=TTYD_VERSION, arch=machine_arch())
    try:
        data = _download(url)
    except Exception as exc:
        raise WorkshopServiceError(
            f"下载 ttyd 失败（{type(exc).__name__}）。检查服务的 https_proxy，"
            f"或按设置页的手动步骤把 ttyd {TTYD_VERSION} 放到 {target}。"
        ) from exc
    if hashlib.sha256(data).hexdigest() != pinned:
        raise WorkshopServiceError("下载的 ttyd 校验和不匹配，已丢弃。")
    tmp = target.with_name("ttyd.tmp")
    tmp.write_bytes(data)
    tmp.chmod(0o755)
    tmp.replace(target)
    return "downloaded"


def start_install() -> dict[str, Any]:
    """Install (or take over): binary → config + unit → start."""

    blocker = install_blocker()
    if blocker:
        raise WorkshopServiceError(blocker)
    with _INSTALL_LOCK:
        if _INSTALL.get("status") == "running":
            return dict(_INSTALL)
        _INSTALL.clear()
        _INSTALL.update(status="running", phase="binary", error="", started_at=time.time())
    thread = threading.Thread(target=_run_install, name="workshop-install", daemon=True)
    thread.start()
    return install_state()


def _run_install() -> None:
    try:
        _update(phase="binary")
        ensure_ttyd()
        _update(phase="unit")
        took_over = unit_path().is_file() and not is_managed()
        if took_over:
            # A hand-written unit holds the port; stop it before replacing it.
            _systemctl("stop", f"{unit_name()}.service", timeout=30)
        write_unit()
        _update(phase="start")
        start()
        _update(status="done", phase="done")
    except Exception as exc:  # surfaced to the admin UI
        message = str(exc) if isinstance(exc, WorkshopServiceError) else f"安装失败：{exc}"
        _update(status="failed", error=message[:300])


__all__ = [
    "DEFAULTS",
    "KEYS",
    "SESSION",
    "WorkshopServiceError",
    "end_sessions",
    "ensure_ttyd",
    "install_blocker",
    "is_managed",
    "logs",
    "probe",
    "restart",
    "save_settings",
    "send_keys",
    "send_text",
    "settings",
    "start",
    "start_install",
    "status",
    "stop",
    "tmux_conf_text",
    "ttyd_command",
    "uninstall",
    "unit_text",
    "upstream_url",
]
