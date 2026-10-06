"""Installable local translation models served by llama.cpp.

Admins pick a model from a small curated catalog in the SPA settings page.
The installer downloads a pinned llama.cpp CPU runtime and a pinned GGUF file
(SHA-256 verified, resumable, honoring ``https_proxy``) into
``NBLANE_LOCAL_MODELS_DIR``. The active model id is deployment config stored
in ``<models dir>/active.json`` (``NBLANE_LOCAL_MT_MODEL`` is the default).

At translation time :func:`ensure_server` lazily starts ``llama-server`` on
``127.0.0.1:NBLANE_LOCAL_MT_PORT`` with an idle sleep, so the model only
holds RAM while it is being used. The server is shared by the Reader sidecar
and the SPA backend through a pid/state file guarded by ``flock``.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import secrets
import shutil
import signal
import subprocess
import tarfile
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator


ACTIVE_MODEL_ENV = "NBLANE_LOCAL_MT_MODEL"
DEFAULT_PORT = 8505
DEFAULT_IDLE_SECONDS = 300
_CHUNK = 1024 * 1024


@dataclass(frozen=True)
class LocalModelSpec:
    """One curated, pinned GGUF translation model."""

    id: str
    name: str
    tier: str  # "fit" (runs on the current small server) or "quality"
    description: str
    repo: str
    revision: str
    filename: str
    size: int
    sha256: str
    min_ram_mb: int
    runtime_ram_mb: int
    license: str
    homepage: str

    def download_url(self) -> str:
        return f"{_hf_endpoint()}/{self.repo}/resolve/{self.revision}/{self.filename}"


@dataclass(frozen=True)
class RuntimeSpec:
    """Pinned llama.cpp CPU build used to serve the models."""

    tag: str
    url: str
    sha256: str
    size: int
    dirname: str


CATALOG: tuple[LocalModelSpec, ...] = (
    LocalModelSpec(
        id="hy-mt2-1.8b-q4",
        name="Hy-MT2 1.8B · Q4_K_M",
        tier="fit",
        description="腾讯混元翻译模型，2 核 4GB 机器可用；段落约 5–9 秒，术语准确、无漏译。",
        repo="tencent/Hy-MT2-1.8B-GGUF",
        revision="a0c709d9fac510f2c807aa3af52872340dc37a4a",
        filename="Hy-MT2-1.8B-Q4_K_M.gguf",
        size=1133080448,
        sha256="dc5f44fcf1fa496ee7ad725982c0c8c553a4de00259b53af84c4b89fb0c06699",
        min_ram_mb=3072,
        runtime_ram_mb=2100,
        license="Apache-2.0",
        homepage="https://huggingface.co/tencent/Hy-MT2-1.8B-GGUF",
    ),
    LocalModelSpec(
        id="hy-mt2-7b-q4",
        name="Hy-MT2 7B · Q4_K_M",
        tier="quality",
        description="同系列 7B，译文更稳；需要 8GB 以上内存，建议服务器升级后使用。",
        repo="tencent/Hy-MT2-7B-GGUF",
        revision="ab8472660ac61fac25f1af43fac2599d52a8a775",
        filename="Hy-MT2-7B-Q4_K_M.gguf",
        size=4624648896,
        sha256="9f96256500f3fc1ab4d64336b58f52a949a95ad7516b0c229476eef782f9f77b",
        min_ram_mb=7168,
        runtime_ram_mb=5600,
        license="Apache-2.0",
        homepage="https://huggingface.co/tencent/Hy-MT2-7B-GGUF",
    ),
)

RUNTIME = RuntimeSpec(
    tag="b11433",
    url="https://github.com/ggml-org/llama.cpp/releases/download/b11433/llama-b11433-bin-ubuntu-x64.tar.gz",
    sha256="d6ff12a557793e302ddbba9660a0f045c403e2f67ab5dcdc1254b343c560c015",
    size=17693586,
    dirname="llama-b11433",
)

# Official Hy-MT2 prompt template (model card). No system prompt.
_ZH_PROMPT = "将以下文本翻译为{lang}，注意只需要输出翻译后的结果，不要额外解释：\n\n{text}"
_EN_PROMPT = (
    "Translate the following text into {lang}. Note that you should only output "
    "the translated result without any additional explanation:\n\n{text}"
)
_TARGET_LANGS: dict[str, tuple[str, str]] = {
    "zh": ("zh", "中文"),
    "zh-cn": ("zh", "中文"),
    "zh-hans": ("zh", "中文"),
    "zh-tw": ("zh", "繁体中文"),
    "zh-hant": ("zh", "繁体中文"),
    "en": ("en", "English"),
    "ja": ("en", "Japanese"),
    "ko": ("en", "Korean"),
    "fr": ("en", "French"),
    "de": ("en", "German"),
    "es": ("en", "Spanish"),
    "ru": ("en", "Russian"),
}


class LocalModelError(RuntimeError):
    """User-facing local model failure (message is safe to show)."""


# ---------------------------------------------------------------- paths/config


def _clean_env(name: str) -> str:
    return str(os.getenv(name, "") or "").strip()


def _hf_endpoint() -> str:
    return (_clean_env("NBLANE_HF_ENDPOINT") or _clean_env("HF_ENDPOINT") or "https://huggingface.co").rstrip("/")


def models_dir() -> Path:
    value = _clean_env("NBLANE_LOCAL_MODELS_DIR")
    if value:
        return Path(value).expanduser()
    return Path.home() / ".local" / "share" / "nblane" / "local-models"


def server_port() -> int:
    try:
        port = int(_clean_env("NBLANE_LOCAL_MT_PORT") or DEFAULT_PORT)
    except ValueError:
        port = DEFAULT_PORT
    return port if 1024 <= port <= 65535 else DEFAULT_PORT


def _idle_seconds() -> int:
    try:
        value = int(_clean_env("NBLANE_LOCAL_MT_IDLE_SECONDS") or DEFAULT_IDLE_SECONDS)
    except ValueError:
        value = DEFAULT_IDLE_SECONDS
    return max(30, min(86400, value))


def _threads() -> int:
    try:
        value = int(_clean_env("NBLANE_LOCAL_MT_THREADS") or 0)
    except ValueError:
        value = 0
    if value <= 0:
        value = os.cpu_count() or 2
    return max(1, min(16, value))


def get_spec(model_id: str) -> LocalModelSpec | None:
    clean = str(model_id or "").strip()
    return next((spec for spec in CATALOG if spec.id == clean), None)


def model_path(spec: LocalModelSpec) -> Path:
    return models_dir() / "models" / spec.filename


def is_installed(spec: LocalModelSpec) -> bool:
    path = model_path(spec)
    return path.is_file() and path.stat().st_size == spec.size


def runtime_dir() -> Path:
    return models_dir() / "runtime" / RUNTIME.dirname


def server_binary() -> Path | None:
    override = _clean_env("NBLANE_LLAMA_SERVER_BIN")
    if override:
        path = Path(override).expanduser()
        return path if path.is_file() else None
    path = runtime_dir() / "llama-server"
    return path if path.is_file() else None


def runtime_supported() -> bool:
    if _clean_env("NBLANE_LLAMA_SERVER_BIN"):
        return True
    return os.uname().sysname == "Linux" and os.uname().machine in {"x86_64", "amd64"}


def _active_path() -> Path:
    return models_dir() / "active.json"


def active_model_id() -> str:
    """Return the selected model id.

    The selection lives next to the models (``active.json``) so the SPA
    backend and the Reader sidecar share it without a restart.
    ``NBLANE_LOCAL_MT_MODEL`` is only a default when nothing was chosen.
    """

    try:
        data = json.loads(_active_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _clean_env(ACTIVE_MODEL_ENV)
    return str(data.get("model_id") or "").strip() if isinstance(data, dict) else ""


def active_spec() -> LocalModelSpec | None:
    """Return the active catalog model when it is installed and runnable."""

    spec = get_spec(active_model_id())
    if spec is None or not is_installed(spec) or server_binary() is None:
        return None
    return spec


def set_active_model(model_id: str) -> None:
    """Persist the active model id (empty string disables local translation)."""

    clean = str(model_id or "").strip()
    if clean:
        spec = get_spec(clean)
        if spec is None:
            raise LocalModelError("未知的本地模型。")
        if not is_installed(spec):
            raise LocalModelError("模型尚未安装完成。")
        if server_binary() is None:
            raise LocalModelError("llama.cpp 运行时未安装。")
        ram = total_ram_mb()
        if ram and ram < spec.min_ram_mb:
            raise LocalModelError(f"内存不足：需要约 {round(spec.min_ram_mb / 1024)}GB 以上。")
    path = _active_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"model_id": clean, "updated": time.time()}), encoding="utf-8")
    tmp.replace(path)
    current = _read_server_state()
    if current and current.get("model_id") != clean:
        stop_server()


# ------------------------------------------------------------------ resources


def total_ram_mb() -> int:
    return _meminfo_mb("MemTotal")


def available_ram_mb() -> int:
    return _meminfo_mb("MemAvailable")


def _meminfo_mb(field: str) -> int:
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{field}:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        return 0
    return 0


def free_disk_mb() -> int:
    target = models_dir()
    probe = target
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    try:
        return shutil.disk_usage(probe).free // (1024 * 1024)
    except OSError:
        return 0


def cpu_summary() -> dict[str, Any]:
    flags = ""
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("flags"):
                flags = line
                break
    except OSError:
        pass
    return {"cores": os.cpu_count() or 0, "avx2": " avx2" in flags, "avx512": " avx512f" in flags}


def resources() -> dict[str, Any]:
    return {
        "total_ram_mb": total_ram_mb(),
        "available_ram_mb": available_ram_mb(),
        "free_disk_mb": free_disk_mb(),
        "models_dir": str(models_dir()),
        **cpu_summary(),
    }


def install_blocker(spec: LocalModelSpec) -> str:
    """Return why ``spec`` cannot be installed here (empty when it can)."""

    if not runtime_supported():
        return "当前平台没有预编译的 llama.cpp，请设置 NBLANE_LLAMA_SERVER_BIN。"
    ram = total_ram_mb()
    if ram and ram < spec.min_ram_mb:
        return f"需要约 {round(spec.min_ram_mb / 1024)}GB 以上内存，当前 {ram / 1024:.1f}GB。"
    needed = (0 if is_installed(spec) else spec.size) + (0 if server_binary() else RUNTIME.size * 4)
    if needed and free_disk_mb() < needed // (1024 * 1024) + 1024:
        return f"磁盘空间不足：需要约 {needed / 1e9 + 1:.1f}GB 可用空间。"
    return ""


# ------------------------------------------------------------------ installer


_INSTALLS: dict[str, dict[str, Any]] = {}
_INSTALL_LOCK = threading.RLock()


def install_state(model_id: str) -> dict[str, Any]:
    with _INSTALL_LOCK:
        return dict(_INSTALLS.get(model_id) or {})


def start_install(model_id: str) -> dict[str, Any]:
    """Start a background install for ``model_id``; idempotent while running."""

    spec = get_spec(model_id)
    if spec is None:
        raise LocalModelError("未知的本地模型。")
    blocker = install_blocker(spec)
    if blocker:
        raise LocalModelError(blocker)
    with _INSTALL_LOCK:
        current = _INSTALLS.get(spec.id)
        if current and current.get("status") == "running":
            return dict(current)
        state = {
            "status": "running",
            "phase": "runtime",
            "downloaded": 0,
            "total": spec.size,
            "error": "",
            "started_at": time.time(),
            "cancel": False,
        }
        _INSTALLS[spec.id] = state
    thread = threading.Thread(target=_run_install, args=(spec,), name=f"local-model-{spec.id}", daemon=True)
    thread.start()
    return dict(state)


def cancel_install(model_id: str) -> None:
    with _INSTALL_LOCK:
        state = _INSTALLS.get(model_id)
        if state and state.get("status") == "running":
            state["cancel"] = True


def _update_install(model_id: str, **fields: Any) -> None:
    with _INSTALL_LOCK:
        _INSTALLS.setdefault(model_id, {}).update(fields)


def _cancelled(model_id: str) -> bool:
    with _INSTALL_LOCK:
        return bool((_INSTALLS.get(model_id) or {}).get("cancel"))


def _run_install(spec: LocalModelSpec) -> None:
    try:
        if server_binary() is None:
            _update_install(spec.id, phase="runtime", downloaded=0, total=RUNTIME.size)
            install_runtime(
                progress=lambda done, total: _update_install(spec.id, downloaded=done, total=total),
                cancelled=lambda: _cancelled(spec.id),
            )
        if not is_installed(spec):
            _update_install(spec.id, phase="model", downloaded=0, total=spec.size)
            target = model_path(spec)
            _download_verified(
                spec.download_url(),
                target,
                size=spec.size,
                sha256=spec.sha256,
                progress=lambda done, total: _update_install(spec.id, downloaded=done, total=total),
                cancelled=lambda: _cancelled(spec.id),
            )
        _update_install(spec.id, status="done", phase="done", error="")
    except Exception as exc:  # surfaced to the admin UI
        message = str(exc) if isinstance(exc, LocalModelError) else f"安装失败：{exc}"
        _update_install(spec.id, status="cancelled" if _cancelled(spec.id) else "failed", error=message[:300])


def install_runtime(
    *,
    progress: Callable[[int, int], None] | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> Path:
    """Download and unpack the pinned llama.cpp CPU runtime."""

    if not runtime_supported():
        raise LocalModelError("当前平台没有预编译的 llama.cpp。")
    archive = models_dir() / "runtime" / f"{RUNTIME.dirname}.tar.gz"
    _download_verified(
        RUNTIME.url, archive, size=RUNTIME.size, sha256=RUNTIME.sha256,
        progress=progress, cancelled=cancelled,
    )
    dest_root = archive.parent
    staging = dest_root / f".{RUNTIME.dirname}.staging"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(staging, filter="data")
    extracted = staging / RUNTIME.dirname
    if not (extracted / "llama-server").is_file():
        shutil.rmtree(staging, ignore_errors=True)
        raise LocalModelError("llama.cpp 压缩包缺少 llama-server。")
    final = runtime_dir()
    shutil.rmtree(final, ignore_errors=True)
    extracted.rename(final)
    shutil.rmtree(staging, ignore_errors=True)
    archive.unlink(missing_ok=True)
    return final / "llama-server"


def _download_verified(
    url: str,
    target: Path,
    *,
    size: int,
    sha256: str,
    progress: Callable[[int, int], None] | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> Path:
    """Download ``url`` to ``target`` with resume and SHA-256 verification."""

    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".part")
    digest = hashlib.sha256()
    done = 0
    if part.exists():
        if part.stat().st_size > size:
            part.unlink()
        else:
            with part.open("rb") as handle:
                for chunk in iter(lambda: handle.read(_CHUNK), b""):
                    digest.update(chunk)
                    done += len(chunk)
    if progress:
        progress(done, size)
    attempts = 0
    while done < size:
        request = urllib.request.Request(url, headers={"User-Agent": "nblane-local-models"})
        if done:
            request.add_header("Range", f"bytes={done}-")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                if done and response.status != 206:
                    # Server ignored the range: start over.
                    part.unlink(missing_ok=True)
                    digest, done = hashlib.sha256(), 0
                with part.open("ab") as handle:
                    while True:
                        if cancelled and cancelled():
                            raise LocalModelError("已取消安装。")
                        chunk = response.read(_CHUNK)
                        if not chunk:
                            break
                        handle.write(chunk)
                        digest.update(chunk)
                        done += len(chunk)
                        if progress:
                            progress(done, size)
            attempts = 0
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            if isinstance(exc, LocalModelError):
                raise
            attempts += 1
            if attempts >= 5:
                raise LocalModelError(f"下载失败：{exc}（可检查代理 https_proxy 或 NBLANE_HF_ENDPOINT 镜像）") from exc
            time.sleep(min(30, 2 ** attempts))
            continue
        if done < size and attempts == 0:
            # Stream ended early; loop resumes with a Range request.
            attempts += 1
    if done != size or digest.hexdigest() != sha256:
        part.unlink(missing_ok=True)
        raise LocalModelError("文件校验失败（SHA-256 不一致），已删除，请重试。")
    part.rename(target)
    return target


def delete_model(model_id: str) -> None:
    spec = get_spec(model_id)
    if spec is None:
        raise LocalModelError("未知的本地模型。")
    with _INSTALL_LOCK:
        if (_INSTALLS.get(spec.id) or {}).get("status") == "running":
            raise LocalModelError("正在安装，请先取消。")
        _INSTALLS.pop(spec.id, None)
    if active_model_id() == spec.id:
        set_active_model("")
    state = _read_server_state()
    if state and state.get("model_id") == spec.id:
        stop_server()
    model_path(spec).unlink(missing_ok=True)
    model_path(spec).with_name(spec.filename + ".part").unlink(missing_ok=True)


# --------------------------------------------------------------------- server


def _run_dir() -> Path:
    return models_dir() / "run"


def _state_path() -> Path:
    return _run_dir() / f"llama-{server_port()}.json"


@contextmanager
def _server_lock() -> Iterator[None]:
    _run_dir().mkdir(parents=True, exist_ok=True)
    with (_run_dir() / f"llama-{server_port()}.lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _read_server_state() -> dict[str, Any] | None:
    try:
        data = json.loads(_state_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not _pid_alive(int(data.get("pid") or 0)):
        return None
    return data


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return True
    return b"llama-server" in cmdline


def _reap(pid: int) -> None:
    """Collect an exited llama-server started by this process (no zombie)."""

    try:
        os.waitpid(pid, os.WNOHANG)
    except (ChildProcessError, OSError):
        pass


def _health(port: int, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(
            urllib.request.Request(f"http://127.0.0.1:{port}/health"), timeout=timeout,
        ) as response:
            return response.status == 200
    except Exception:
        return False


def server_status() -> dict[str, Any]:
    state = _read_server_state()
    if not state:
        return {"running": False, "port": server_port(), "model_id": "", "rss_mb": 0}
    rss = 0
    try:
        for line in Path(f"/proc/{state['pid']}/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                rss = int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        pass
    return {
        "running": True,
        "port": int(state.get("port") or server_port()),
        "model_id": str(state.get("model_id") or ""),
        "rss_mb": rss,
        # llama-server unloads weights while sleeping; RSS drops to ~50MB.
        "sleeping": 0 < rss < 200,
    }


def stop_server() -> None:
    with _server_lock():
        state = _read_server_state()
        if state:
            pid = int(state.get("pid") or 0)
            try:
                os.killpg(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
            for _ in range(50):
                _reap(pid)
                if not _pid_alive(pid):
                    break
                time.sleep(0.1)
        _state_path().unlink(missing_ok=True)


def ensure_server(spec: LocalModelSpec, *, timeout: float = 90.0) -> tuple[str, str]:
    """Return ``(base_url, api_key)`` of a running server for ``spec``."""

    binary = server_binary()
    if binary is None:
        raise LocalModelError("llama.cpp 运行时未安装。")
    if not is_installed(spec):
        raise LocalModelError("模型尚未安装。")
    port = server_port()
    with _server_lock():
        state = _read_server_state()
        if state and state.get("model_id") == spec.id and _health(port):
            return f"http://127.0.0.1:{port}", str(state.get("api_key") or "")
        if state:
            try:
                os.killpg(int(state["pid"]), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, KeyError, ValueError):
                pass
            time.sleep(0.5)
            _reap(int(state.get("pid") or 0))
        if _health(port, timeout=0.5):
            raise LocalModelError(f"端口 {port} 已被其他服务占用，请设置 NBLANE_LOCAL_MT_PORT。")
        api_key = secrets.token_urlsafe(24)
        _run_dir().mkdir(parents=True, exist_ok=True)
        log = (_run_dir() / f"llama-{port}.log").open("ab")
        env = dict(os.environ)
        env["LLAMA_API_KEY"] = api_key  # keep the key out of argv/ps
        env["LD_LIBRARY_PATH"] = f"{binary.parent}:{env.get('LD_LIBRARY_PATH', '')}".rstrip(":")
        process = subprocess.Popen(
            [
                str(binary), "-m", str(model_path(spec)),
                "--host", "127.0.0.1", "--port", str(port),
                "-t", str(_threads()), "-c", "4096", "-np", "1",
                "--no-webui", "--alias", spec.id,
                "--sleep-idle-seconds", str(_idle_seconds()),
            ],
            stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            env=env, start_new_session=True, close_fds=True,
        )
        log.close()
        state_path = _state_path()
        state_path.write_text(
            json.dumps({"pid": process.pid, "port": port, "model_id": spec.id, "api_key": api_key, "started": time.time()}),
            encoding="utf-8",
        )
        os.chmod(state_path, 0o600)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if process.poll() is not None:
                state_path.unlink(missing_ok=True)
                raise LocalModelError(f"llama-server 启动失败（退出码 {process.returncode}），见 {_run_dir()}/llama-{port}.log")
            if _health(port, timeout=1.0):
                return f"http://127.0.0.1:{port}", api_key
            time.sleep(0.5)
        raise LocalModelError("llama-server 启动超时。")


# ----------------------------------------------------------------- translation


def build_prompt(text: str, target_lang: str) -> str:
    lang = _TARGET_LANGS.get(str(target_lang or "zh").strip().lower())
    if lang is None:
        raise LocalModelError(f"本地模型不支持目标语言 {target_lang}。")
    template = _ZH_PROMPT if lang[0] == "zh" else _EN_PROMPT
    return template.format(lang=lang[1], text=text)


def translate_text(spec: LocalModelSpec, text: str, *, target_lang: str = "zh", timeout: float = 240.0) -> str:
    """Translate one passage with the local server (starts it if needed)."""

    prompt = build_prompt(text, target_lang)
    base_url, api_key = ensure_server(spec)
    body = json.dumps(
        {
            "model": spec.id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "top_p": 0.6,
            "top_k": 20,
            "repeat_penalty": 1.05,
            "max_tokens": max(64, min(2048, len(text) // 2 + 64)),
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise LocalModelError(f"本地模型请求失败：HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LocalModelError(f"本地模型请求失败：{exc}") from exc
    try:
        content = str(payload["choices"][0]["message"]["content"] or "")
    except (KeyError, IndexError, TypeError) as exc:
        raise LocalModelError("本地模型返回格式异常。") from exc
    return content.strip()


# -------------------------------------------------------------------- summary


def catalog_status() -> dict[str, Any]:
    active = active_model_id()
    server = server_status()
    models = []
    for spec in CATALOG:
        data = asdict(spec)
        data.pop("sha256", None)
        install = install_state(spec.id)
        install.pop("cancel", None)
        data.update(
            installed=is_installed(spec),
            active=active == spec.id,
            install_blocker=install_blocker(spec),
            install=install,
            fits_ram=not total_ram_mb() or total_ram_mb() >= spec.min_ram_mb,
        )
        models.append(data)
    return {
        "resources": resources(),
        "runtime": {
            "tag": RUNTIME.tag,
            "installed": server_binary() is not None,
            "supported": runtime_supported(),
        },
        "server": server,
        "active_model_id": active,
        "active_ready": active_spec() is not None,
        "models": models,
    }


__all__ = [
    "ACTIVE_MODEL_ENV",
    "CATALOG",
    "LocalModelError",
    "LocalModelSpec",
    "RUNTIME",
    "active_model_id",
    "active_spec",
    "build_prompt",
    "cancel_install",
    "catalog_status",
    "delete_model",
    "ensure_server",
    "get_spec",
    "install_blocker",
    "is_installed",
    "models_dir",
    "server_status",
    "set_active_model",
    "start_install",
    "stop_server",
    "translate_text",
]
