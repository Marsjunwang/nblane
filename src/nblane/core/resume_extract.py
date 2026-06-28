"""Extract plain text from resume uploads (PDF / DOCX / TXT).

Used by the dashboard "Resume → AI ingest" path so users can paste *or* upload
their CV. Failure modes are converted to friendly messages: a missing optional
dependency surfaces as a hint rather than a stack trace, and a fully-unreadable
upload returns an empty string + the reason so the UI can stay open.
"""

from __future__ import annotations

import io


def extract_resume_text(filename: str, data: bytes) -> tuple[str, str]:
    """Return ``(text, error_message)`` for a resume upload.

    Either field can be empty; the caller decides whether ``text`` alone is
    enough. ``error_message`` is human-readable (not a traceback).
    """
    if not data:
        return "", "empty file"
    name = (filename or "").strip().lower()
    if name.endswith(".pdf"):
        return _extract_pdf(data)
    if name.endswith(".docx"):
        return _extract_docx(data)
    if name.endswith(".doc"):
        return (
            "",
            "Legacy .doc is not supported — save as .docx or paste the text.",
        )
    # Fall through: treat as UTF-8 text.
    try:
        return data.decode("utf-8"), ""
    except UnicodeDecodeError:
        try:
            return data.decode("latin-1"), ""
        except Exception as exc:  # pragma: no cover - latin-1 should never fail
            return "", f"could not decode as text: {exc}"


def _extract_pdf(data: bytes) -> tuple[str, str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        return "", "pypdf is not installed — run `pip install pypdf` to enable PDF resume upload."
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        return "", f"could not open PDF: {exc}"
    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    text = "\n\n".join(p.strip() for p in parts if p.strip())
    if not text:
        return "", "PDF had no extractable text (likely a scanned image)."
    return text, ""


def _extract_docx(data: bytes) -> tuple[str, str]:
    try:
        import docx  # type: ignore
    except ImportError:
        return "", "python-docx is not installed — run `pip install python-docx` to enable DOCX resume upload."
    try:
        document = docx.Document(io.BytesIO(data))
    except Exception as exc:
        return "", f"could not open DOCX: {exc}"
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text and p.text.strip()]
    if not paragraphs:
        return "", "DOCX appeared to be empty."
    return "\n\n".join(paragraphs), ""
