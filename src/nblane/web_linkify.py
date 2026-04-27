"""Turn plain-text URLs into safe HTML anchors for Streamlit markdown."""

from __future__ import annotations

import html
import re
from urllib.parse import urlparse

# Match http(s) and mailto; stop at common delimiters.
_URL_RE = re.compile(
    r"(https?://[^\s<>\")'\\\[\]]+|mailto:[^\s<>\")'\\\[\]]+)",
    re.IGNORECASE,
)


def _href_allowed(url: str) -> bool:
    """Return True only for http, https, and mailto schemes."""
    u = url.strip()
    if u.lower().startswith("mailto:"):
        return "@" in u
    parsed = urlparse(u)
    return parsed.scheme in ("http", "https")


def linkify_plain_to_html(text: str) -> str:
    """Escape *text* and wrap allowed URLs in anchor tags.

    Returns HTML safe to embed in ``st.markdown(..., unsafe_allow_html=True)``.
    """
    if text is None:
        return ""
    if not text:
        return ""

    parts: list[str] = []
    pos = 0
    for m in _URL_RE.finditer(text):
        parts.append(html.escape(text[pos : m.start()]))
        raw_url = m.group(0)
        if _href_allowed(raw_url):
            esc_url = html.escape(raw_url, quote=True)
            esc_vis = html.escape(raw_url)
            parts.append(
                '<a href="'
                + esc_url
                + '" target="_blank" rel="noopener noreferrer">'
                + esc_vis
                + "</a>"
            )
        else:
            parts.append(html.escape(raw_url))
        pos = m.end()
    parts.append(html.escape(text[pos:]))
    return "".join(parts)


def text_contains_linkified_url(text: str) -> bool:
    """Return True if *text* contains at least one allowed URL."""
    if not text or not text.strip():
        return False
    for m in _URL_RE.finditer(text):
        if _href_allowed(m.group(0)):
            return True
    return False


def extract_plain_urls(text: str) -> list[str]:
    """Return allowed plain-text URLs in first-seen order."""
    if not text or not text.strip():
        return []
    out: list[str] = []
    seen: set[str] = set()
    for m in _URL_RE.finditer(text):
        raw = m.group(0).rstrip(".,;:")
        if not _href_allowed(raw):
            continue
        if raw in seen:
            continue
        seen.add(raw)
        out.append(raw)
    return out
