"""Shared helpers for the Research Studio UI."""
from __future__ import annotations

import os
import html
import json
import time
import urllib.request
from urllib.parse import quote, urlencode, urlparse

import streamlit as st

from nblane.core.auth import mint_reader_token
from nblane.core.research_papers import (
    paper_rows,
    ensure_paper_pdf_downloaded,
)
from nblane.web_auth import sidecar_auth_handoff_token
from nblane.web_cache import load_research_sources

from .context import ResearchContext


def _l(ui: dict[str, str], key: str, default: str) -> str:
    return ui.get(key, default)


_PENDING_IMPORT_WARNINGS_KEY = "research:pending_pdf_import_warnings"


_PAPER_ROWS_CACHE_KEY = "research:paper_rows_cache"


def _text_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _lines_text(values: object) -> str:
    if not isinstance(values, list):
        return ""
    return "\n".join(str(item).strip() for item in values if str(item).strip())


def _tags_text(values: object) -> str:
    if not isinstance(values, list):
        return ""
    return ", ".join(str(item).strip() for item in values if str(item).strip())


def _tags(value: str) -> list[str]:
    return [
        item.strip()
        for item in value.replace("\n", ",").split(",")
        if item.strip()
    ]


def _short_text(value: object, limit: int = 160) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _unique_text(values: list[str]) -> list[str]:
    out = []
    seen = set()
    for value in values:
        clean = str(value or "").strip()
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _normalized_title(value: str) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def _status_label(ctx, status: str) -> str:
    ui = ctx.ui
    return ui.get(f"status_{status}", status)


def _paper_sources(inbox) -> list:
    return [source for source in inbox.sources if source.kind == "paper"]


def _source_label(inbox, source_id: str) -> str:
    source = next((source for source in inbox.sources if source.id == source_id), None)
    if source is None:
        return source_id
    label = source.title or source.id
    duplicate_titles = sum(1 for row in inbox.sources if (row.title or row.id) == label)
    if duplicate_titles > 1:
        label = f"{label} · {source.id}"
    return label


def _node_options(ctx, *, include_unsorted: bool = True, include_trashed: bool = False) -> dict[str, str]:
    _pdir = ctx.pdir
    ui = ctx.ui
    tree = load_paper_library_tree(_pdir)
    paths = paper_library_paths(_pdir)
    options: dict[str, str] = {}
    if include_unsorted:
        options[""] = _l(ui, "unsorted_inbox", "Unsorted Inbox")
    for node in sorted(tree.nodes, key=lambda item: (paths.get(item.id, item.title).lower(), item.order, item.id)):
        if node.status == "trashed" and not include_trashed:
            continue
        options[node.id] = paths.get(node.id, node.title)
    return options


def _node_select_index(options: dict[str, str], wanted: str) -> int:
    keys = list(options)
    clean = str(wanted or "").strip()
    return keys.index(clean) if clean in options else 0


def _paper_library_key(ctx, name: str) -> str:
    selected = ctx.selected
    return f"paper_library:{selected}:{name}"


def _sidecar_base_for_same_origin_mode() -> str:
    """Resolve ``NBLANE_READER_API_BASE=0`` into a browser-facing sidecar base."""

    try:
        current_url = str(getattr(st.context, "url", "") or "").strip()
    except Exception:
        current_url = ""
    if current_url:
        parsed = urlparse(current_url)
        host = (parsed.hostname or "").strip().lower()
        if parsed.scheme in {"http", "https"} and host in {"localhost", "127.0.0.1"}:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            sidecar_port = {8501: 8502, 8503: 8502, 18503: 18502}.get(port)
            if sidecar_port:
                return f"{parsed.scheme}://{parsed.hostname}:{sidecar_port}"
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return os.getenv("NBLANE_STREAMLIT_BASE_URL", "").strip().rstrip("/")


def _reader_api_base() -> str:
    """Return the sidecar base used for Paper Library and Reader links."""
    raw = (
        os.getenv("NBLANE_READER_API_BASE", "").strip()
        or os.getenv("NBLANE_PAPER_LIBRARY_BASE", "").strip()
        or "http://127.0.0.1:8502"
    )
    if raw.lower() in {"0", "false", "off", "none"}:
        return _sidecar_base_for_same_origin_mode()
    return raw.rstrip("/")


def _research_overview_url() -> str:
    """Return the browser-facing Research Overview URL for 8502 back links."""

    explicit = os.getenv("NBLANE_RESEARCH_OVERVIEW_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    try:
        current_url = str(getattr(st.context, "url", "") or "").strip()
    except Exception:
        current_url = ""
    if current_url:
        parsed = urlparse(current_url)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            path = parsed.path if parsed.path.strip("/") else "/Research"
            return f"{parsed.scheme}://{parsed.netloc}{path}"
        if current_url.startswith("/") and not current_url.startswith("//"):
            return current_url.split("?", 1)[0].split("#", 1)[0] or "/Research"
    base = os.getenv("NBLANE_STREAMLIT_BASE_URL", "").strip().rstrip("/")
    if base:
        return f"{base}/Research"
    return "/Research"


def _reader_view_url(ctx, source_id: str) -> str:
    selected = ctx.selected
    user = ctx.user
    token = mint_reader_token(user.id, selected, source_id)
    base = _reader_api_base()
    encoded_source = quote(source_id, safe="")
    encoded_token = quote(token, safe="")
    path = f"/reader/view/{encoded_source}?token={encoded_token}"
    return f"{base}{path}" if base else path


def _paper_library_workspace_url(ctx, 
    *,
    view: str = "",
    node_id: str = "",
    query: str = "",
    sort: str = "",
    detail_id: str = "",
    focus: str = "",
    action: str = "",
    return_to: str = "",
    return_url: str = "",
) -> str:
    selected = ctx.selected
    base = _reader_api_base()
    params = {"profile": selected}
    clean_return_to = str(return_to or "").strip()
    clean_return_url = str(return_url or "").strip()
    if clean_return_to == "overview" and not clean_return_url:
        clean_return_url = _research_overview_url()
    optional = {
        "view": view,
        "node_id": node_id,
        "query": query,
        "sort": sort,
        "detail_id": detail_id,
        "focus": focus,
        "action": action,
        "return_to": clean_return_to,
        "return_url": clean_return_url,
    }
    params.update(
        {key: str(value).strip() for key, value in optional.items() if str(value or "").strip()}
    )
    path = f"/paper-library?{urlencode(params)}"
    return f"{base}{path}" if base else path


def _paper_library_target_url(ctx, target: dict[str, object], *, fallback_detail_id: str = "") -> str:
    if not isinstance(target, dict) or str(target.get("surface") or "") != "paper_library":
        return ""
    return _paper_library_workspace_url(ctx, 
        view=str(target.get("view") or ""),
        node_id=str(target.get("node_id") or ""),
        query=str(target.get("query") or ""),
        sort=str(target.get("sort") or ""),
        detail_id=str(target.get("detail_id") or fallback_detail_id or ""),
        focus=str(target.get("focus") or ""),
        action=str(target.get("action") or ""),
        return_to=str(target.get("return_to") or "overview"),
        return_url=str(target.get("return_url") or ""),
    )


def _paper_library_workspace_status(ctx, workspace_url: str) -> tuple[bool | None, str]:
    parsed = urlparse(workspace_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None, ""
    try:
        timeout = max(0.1, float(os.getenv("NBLANE_PAPER_LIBRARY_HEALTH_TIMEOUT", "2.5")))
    except ValueError:
        timeout = 2.5
    cache_key = _paper_library_key(ctx, f"workspace_status:{workspace_url}")
    now = time.time()
    cached = st.session_state.get(cache_key)
    if isinstance(cached, dict) and now - float(cached.get("checked_at", 0)) < 15:
        return bool(cached.get("ok")), str(cached.get("message") or "")
    try:
        request = urllib.request.Request(
            workspace_url,
            method="GET",
            headers={"User-Agent": "nblane-paper-library-runtime-check/1.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(getattr(response, "status", 200))
            marker = str(response.headers.get("X-Nblane-Sidecar") or "").strip()
            body = response.read(256).decode("utf-8", errors="ignore")
            ok = 200 <= status < 400 and (
                marker == "reader-api" or "nblane sidecar ok" in body
            )
            message = "" if ok else f"unexpected sidecar health response: HTTP {status}".strip()
    except Exception as exc:
        ok = False
        message = str(exc)
    st.session_state[cache_key] = {"checked_at": now, "ok": ok, "message": message}
    return ok, message


def _paper_library_sidecar_status(ctx) -> tuple[bool | None, str]:
    base = _reader_api_base()
    if not base:
        return None, ""
    health_url = f"{base}/auth/session-ok"
    try:
        timeout = max(0.1, float(os.getenv("NBLANE_PAPER_LIBRARY_HEALTH_TIMEOUT", "2.5")))
    except ValueError:
        timeout = 2.5
    cache_key = _paper_library_key(ctx, f"sidecar_status:{health_url}")
    now = time.time()
    cached = st.session_state.get(cache_key)
    if isinstance(cached, dict) and now - float(cached.get("checked_at", 0)) < 15:
        return bool(cached.get("ok")), str(cached.get("message") or "")
    try:
        request = urllib.request.Request(
            health_url,
            method="GET",
            headers={"User-Agent": "nblane-paper-library-sidecar-check/1.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            ok = 200 <= int(getattr(response, "status", 200)) < 400
            message = "" if ok else f"HTTP {getattr(response, 'status', '')}".strip()
    except Exception as exc:
        ok = False
        message = str(exc)
    st.session_state[cache_key] = {"checked_at": now, "ok": ok, "message": message}
    return ok, message


def _paper_library_sidecar_unavailable(ctx) -> tuple[bool, str]:
    """Return whether browser-facing 8502 links should be paused."""
    ok, message = _paper_library_sidecar_status(ctx)
    return ok is False, message


def _paper_library_sidecar_disabled_help(ctx, message: str = "") -> str:
    ui = ctx.ui
    help_text = _l(ui, 
        "paper_library_sidecar_link_disabled_help",
        "Start or forward the 8502 Paper Library sidecar to use this link.",
    )
    if message:
        help_text = f"{help_text} {message}"
    return help_text


def _render_sidecar_link_button(ctx, 
    label: str,
    url: str,
    *,
    key: str | None = None,
    icon: str | None = None,
    type: str = "secondary",
    use_container_width: bool | None = None,
    width: str = "content",
    help: str | None = None,
    disabled: bool = False,
) -> None:
    ui = ctx.ui
    unavailable, message = _paper_library_sidecar_unavailable(ctx)
    is_disabled = disabled or unavailable
    help_text = help or (_paper_library_sidecar_disabled_help(ctx, message) if unavailable else None)
    try:
        st.link_button(
            label,
            url,
            key=key,
            icon=icon,
            type=type,
            use_container_width=use_container_width,
            width=width,
            help=help_text,
            disabled=is_disabled,
        )
    except Exception:
        if is_disabled:
            st.button(
                label,
                key=key,
                icon=icon,
                type=type,
                use_container_width=use_container_width,
                width=width,
                help=help_text,
                disabled=True,
            )
        else:
            st.caption(f"{_l(ui, 'paper_library_workspace_url', 'Workspace')}: `{url}`")


def _render_research_sidecar_status(ctx) -> None:
    ui = ctx.ui
    base = _reader_api_base()
    if not base:
        st.warning(
            _l(ui, 
                "research_sidecar_disabled",
                "Paper Library sidecar links are disabled; Reader and 8502 workspace buttons will use relative URLs.",
            )
        )
        return
    ok, message = _paper_library_sidecar_status(ctx)
    env_base = os.getenv("NBLANE_READER_API_BASE", "").strip()
    origin = (
        _l(ui, "same_origin", "same-origin")
        if env_base.strip().lower() in {"0", "false", "off", "none"}
        else
        _l(ui, "configured", "configured")
        if env_base
        else _l(ui, "auto_detected", "auto-detected")
    )
    if ok is False:
        st.warning(
            _l(ui, 
                "research_sidecar_unavailable",
                "8502 Paper Library sidecar is not reachable; Reader and Paper Library links are temporarily disabled for {base}.",
            ).format(base=base)
            + (f" `{message}`" if message else "")
        )
        return
    st.caption(
        _l(ui, 
            "research_sidecar_connected",
            "Paper Library sidecar: {origin} · {base}",
        ).format(origin=origin, base=base)
    )


def _render_authenticated_iframe(src: str, *, token: str, height: int, scrolling: bool) -> None:
    base = _reader_api_base()
    auth_url = f"{base}/auth/session" if base else "/auth/session"
    escaped_auth_url = html.escape(auth_url, quote=True)
    src_json = json.dumps(src).replace("</", "<\\/")
    escaped_token = html.escape(token, quote=True)
    frame_height = max(100, int(height or 800) - 2)
    wrapper = f"""
<!doctype html>
<html>
  <body style="margin:0;overflow:hidden">
    <iframe name="nblaneAuthTarget" title="nblane auth" style="display:none;width:0;height:0;border:0"></iframe>
    <form id="nblaneAuthForm" action="{escaped_auth_url}" method="post" target="nblaneAuthTarget" style="display:none">
      <input type="hidden" name="token" value="{escaped_token}">
    </form>
    <iframe id="nblaneContentFrame" title="nblane" style="width:100%;height:{frame_height}px;border:0" loading="eager"></iframe>
    <script>
      const content = document.getElementById("nblaneContentFrame");
      const form = document.getElementById("nblaneAuthForm");
      let loaded = false;
      const loadContent = () => {{
        if (loaded || !content) return;
        loaded = true;
        content.src = {src_json};
      }};
      const target = document.querySelector('iframe[name="nblaneAuthTarget"]');
      if (target) target.addEventListener("load", loadContent, {{ once: true }});
      if (form) form.submit();
      window.setTimeout(loadContent, 1200);
    </script>
  </body>
</html>
"""
    st.components.v1.html(wrapper, height=height, scrolling=scrolling)


def _render_iframe(ctx, src: str, *, height: int, scrolling: bool) -> None:
    user = ctx.user
    token = sidecar_auth_handoff_token(user)
    if token:
        _render_authenticated_iframe(src, token=token, height=height, scrolling=scrolling)
        return
    if hasattr(st, "iframe"):
        st.iframe(src, height=height)
    else:
        st.components.v1.iframe(src, height=height, scrolling=scrolling)


def _paper_rows_cache_signature(profile_path) -> tuple:
    """Return a cache signature based on the mtime of the canonical inputs.

    paper_rows reads sources.yaml plus per-paper annotation/translation jsonl
    files. Tracking the directory mtimes captures the common edit paths without
    walking every file on every render.
    """

    candidates = [
        profile_path / "research" / "sources.yaml",
        profile_path / "research" / "annotations",
        profile_path / "research" / "translations",
        profile_path / "research" / "paper-segments",
    ]
    parts: list[tuple[str, int]] = []
    for path in candidates:
        try:
            stat = path.stat()
            parts.append((str(path), int(stat.st_mtime_ns)))
        except FileNotFoundError:
            parts.append((str(path), 0))
        except OSError:
            parts.append((str(path), -1))
    return tuple(parts)


def _cached_paper_rows(profile_path, *, view: str = "all", node_id: str = "") -> list[dict[str, object]]:
    """Memoize paper_rows for the current Streamlit run when inputs are unchanged."""

    cache = st.session_state.get(_PAPER_ROWS_CACHE_KEY)
    if not isinstance(cache, dict):
        cache = {}
    signature = _paper_rows_cache_signature(profile_path)
    cache_key = (str(profile_path), view, node_id)
    cached = cache.get(cache_key)
    if isinstance(cached, dict) and cached.get("signature") == signature:
        return list(cached.get("rows") or [])
    rows = paper_rows(profile_path, view=view, node_id=node_id)
    cache[cache_key] = {"signature": signature, "rows": list(rows)}
    # Cap cache to recent entries to bound memory.
    if len(cache) > 16:
        for stale_key in list(cache.keys())[:-16]:
            cache.pop(stale_key, None)
    st.session_state[_PAPER_ROWS_CACHE_KEY] = cache
    return rows


def _queue_pdf_import_warnings(source_ids: list[str], *, key_prefix: str = "import") -> None:
    """Stash imported source ids so warnings render on the next page load."""

    clean = [str(s) for s in source_ids if str(s).strip()]
    if not clean:
        return
    existing = list(st.session_state.get(_PENDING_IMPORT_WARNINGS_KEY) or [])
    existing.append({"prefix": key_prefix, "source_ids": clean})
    st.session_state[_PENDING_IMPORT_WARNINGS_KEY] = existing[-5:]  # cap memory


def _render_pdf_import_warnings(ctx, profile_path) -> None:
    """Render pending import warnings (queued before a rerun) with Retry buttons."""
    ui = ctx.ui

    queued = list(st.session_state.get(_PENDING_IMPORT_WARNINGS_KEY) or [])
    if not queued:
        return
    refreshed = load_research_sources(profile_path).by_id()
    surviving: list[dict[str, object]] = []
    for batch_index, batch in enumerate(queued):
        prefix = str(batch.get("prefix") or "import")
        source_ids = list(batch.get("source_ids") or [])
        new_batch_ids: list[str] = []
        for source_index, source_id in enumerate(source_ids):
            source = refreshed.get(source_id)
            if source is None:
                continue
            metadata = source.metadata or {}
            status = str(metadata.get("pdf_download_status") or "").strip()
            if status in ("", "downloaded"):
                continue
            new_batch_ids.append(source_id)
            title = source.title or source_id
            error = str(metadata.get("pdf_download_error") or "").strip()
            st.warning(f"{title} · {status.replace('_', ' ')}{' · ' + error if error else ''}")
            if status in {"failed", "skipped_no_pdf_url", "skipped_needs_link_check"}:
                button_key = f"retry_pdf:{prefix}:{batch_index}:{source_index}:{source_id}"
                if st.button(_l(ui, "retry_pdf_download", "Retry download"), key=button_key):
                    with st.spinner(_l(ui, "retrying_pdf_download", "Retrying PDF download...")):
                        outcome = ensure_paper_pdf_downloaded(
                            profile_path,
                            source_id,
                            error_prefix="PDF retry failed",
                        )
                    if outcome.get("status") == "downloaded":
                        st.success(_l(ui, "retry_pdf_succeeded", "Download succeeded."))
                        st.rerun()
                    else:
                        st.error(str(outcome.get("error") or status))
        if new_batch_ids:
            surviving.append({"prefix": prefix, "source_ids": new_batch_ids})
    st.session_state[_PENDING_IMPORT_WARNINGS_KEY] = surviving


def _render_research_help(ctx) -> None:
    ui = ctx.ui
    st.markdown(_l(ui, "research_help_body", ""))


def _payload_text(payload: dict, *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _payload_list(payload: dict, *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            values.extend(_tags(value))
        elif isinstance(value, (list, tuple, set)):
            values.extend(str(item).strip() for item in value if str(item).strip())
        elif value is not None and str(value).strip():
            values.append(str(value).strip())
    return _unique_text(values)


def _payload_int(payload: dict, key: str, default: int = 0) -> int:
    try:
        return int(payload.get(key) or default)
    except (TypeError, ValueError):
        return default


