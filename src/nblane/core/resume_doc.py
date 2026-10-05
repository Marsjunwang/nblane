"""Structured resume document (``resume-source.yaml``).

One module owns the resume shape so the career form, the public site, the
Markdown import and the HTML/PDF exports agree on it:

``normalize_resume``
    Tolerant coercion of a loaded/edited mapping into the canonical shape.
    Unknown top-level keys are preserved; legacy record aliases
    (``org``/``title``) are folded into the canonical fields.
``render_resume_markdown``
    Canonical Markdown (``# 姓名 | 头衔``, ``### 单位 | 职位 | 时间``,
    ``**分组**`` + bullets). It round-trips through ``parse_resume_markdown``.
``render_resume_html``
    Print-ready A4 page (screen preview + PDF source) built from Markdown,
    with an optional photo in the header.
``render_resume_pdf``
    Headless Chromium ``--print-to-pdf`` of the HTML page.

Canonical shape (every field optional except ``basics.name``)::

    basics: {name, title, tagline, location, phone, email, website, photo}
    summary: str
    skill_groups: [{label, text}]
    skills: [str]                         # flat list (legacy / simple)
    experiences: [{company, role, start, end, location, summary,
                   bullets: [str], groups: [{label, bullets: [str]}]}]
    projects: [{name, role, start, end, summary, bullets, groups}]
    outputs: [{title, ...same body fields}]
    education: [{school, degree, start, end, summary, bullets}]
    honors: [str]
    extra_sections: [{title, body}]       # imported sections we could not map
    section_titles: {summary, skills, experiences, projects, outputs,
                     education, honors}
    lang: zh | en
"""

from __future__ import annotations

import base64
import html
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

SECTION_KEYS = ("summary", "skills", "experiences", "projects", "outputs", "education", "honors")
RECORD_SECTIONS = ("experiences", "projects", "outputs", "education")

DEFAULT_SECTION_TITLES = {
    "zh": {
        "summary": "个人概要",
        "skills": "专业技能",
        "experiences": "工作经历",
        "projects": "项目经历",
        "outputs": "成果",
        "education": "教育经历",
        "honors": "荣誉与其他",
    },
    "en": {
        "summary": "Summary",
        "skills": "Skills",
        "experiences": "Experience",
        "projects": "Projects",
        "outputs": "Outputs",
        "education": "Education",
        "honors": "Honors",
    },
}

# (org field, role field, aliases folded into org, aliases folded into role)
_RECORD_FIELDS: dict[str, tuple[str, str, tuple[str, ...], tuple[str, ...]]] = {
    "experiences": ("company", "role", ("org", "organization", "name"), ("title", "position")),
    "projects": ("name", "role", ("title", "org", "company"), ()),
    "outputs": ("title", "role", ("name",), ()),
    "education": ("school", "degree", ("org", "company", "institution"), ("title", "role", "major")),
}

_BASICS_FIELDS = ("name", "title", "tagline", "location", "phone", "email", "website", "photo")
_CJK_RE = re.compile(r"[一-鿿]")
_YEAR_RE = re.compile(r"(?:19|20)\d{2}")
_EMAIL_RE = re.compile(r"^[\w.+-]+@\s*[\w-]+(?:\.[\w-]+)+$")
_PHONE_RE = re.compile(r"^\+?[\d\s()-]{7,}$")
_URL_RE = re.compile(r"^(?:https?://|www\.)\S+$|^[\w-]+(?:\.[\w-]+)+/\S*$", re.I)
_GROUP_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")
_SKILL_GROUP_RE = re.compile(r"^\*\*(.+?)\*\*\s*[:：]\s*(.*)$")
_BULLET_RE = re.compile(r"^\s*[-*+]\s+(.*)$")


# --- Normalization -----------------------------------------------------------


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "\n".join(_text(v) for v in value if _text(v))
    return str(value).strip()


def _str_list(value: object) -> list[str]:
    if isinstance(value, str):
        value = value.splitlines()
    if not isinstance(value, (list, tuple)):
        return []
    return [text for text in (_text(v) for v in value) if text]


def detect_lang(resume: dict[str, Any]) -> str:
    lang = _text(resume.get("lang")).lower()
    if lang in DEFAULT_SECTION_TITLES:
        return lang
    basics = resume.get("basics") if isinstance(resume.get("basics"), dict) else {}
    probe = " ".join([_text(basics.get("name")), _text(basics.get("title")), _text(resume.get("summary"))])
    return "zh" if _CJK_RE.search(probe) else "en"


def _normalize_groups(raw: object) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    groups = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = _text(item.get("label"))
        bullets = _str_list(item.get("bullets"))
        if label or bullets:
            groups.append({"label": label, "bullets": bullets})
    return groups


def _normalize_record(section: str, raw: dict[str, Any]) -> dict[str, Any]:
    org_key, role_key, org_aliases, role_aliases = _RECORD_FIELDS[section]
    record = dict(raw)
    for key, aliases in ((org_key, org_aliases), (role_key, role_aliases)):
        value = _text(record.get(key))
        for alias in aliases:
            alias_value = _text(record.pop(alias, ""))
            if not value and alias_value:
                value = alias_value
        record[key] = value
    for key in ("start", "end", "location", "summary"):
        record[key] = _text(record.get(key))
    record["bullets"] = _str_list(record.get("bullets"))
    record["groups"] = _normalize_groups(record.get("groups"))
    return record


def normalize_resume(data: dict[str, Any] | None, *, profile: str = "") -> dict[str, Any]:
    """Coerce *data* into the canonical shape; unknown keys are preserved."""
    raw = dict(data or {})
    out: dict[str, Any] = dict(raw)
    out["profile"] = _text(raw.get("profile")) or profile
    visibility = _text(raw.get("visibility")) or "private"
    out["visibility"] = visibility if visibility in {"private", "public"} else "private"
    basics_raw = raw.get("basics") if isinstance(raw.get("basics"), dict) else {}
    basics = dict(basics_raw)
    for key in _BASICS_FIELDS:
        basics[key] = _text(basics_raw.get(key))
    if not basics["name"]:
        basics["name"] = out["profile"]
    out["basics"] = basics
    out["summary"] = _text(raw.get("summary"))
    out["skills"] = _str_list(raw.get("skills"))
    skill_groups = []
    for item in raw.get("skill_groups") or []:
        if isinstance(item, dict) and (_text(item.get("label")) or _text(item.get("text"))):
            skill_groups.append({"label": _text(item.get("label")), "text": _text(item.get("text"))})
    out["skill_groups"] = skill_groups
    for section in RECORD_SECTIONS:
        rows = raw.get(section)
        if isinstance(rows, list):
            out[section] = [
                _normalize_record(section, row if isinstance(row, dict) else {_RECORD_FIELDS[section][0]: _text(row)})
                for row in rows
                if isinstance(row, dict) or _text(row)
            ]
        else:
            out[section] = []
    out["honors"] = _str_list(raw.get("honors"))
    extras = []
    for item in raw.get("extra_sections") or []:
        if isinstance(item, dict) and (_text(item.get("title")) or _text(item.get("body"))):
            extras.append({"title": _text(item.get("title")), "body": str(item.get("body") or "").strip()})
    out["extra_sections"] = extras
    titles_raw = raw.get("section_titles") if isinstance(raw.get("section_titles"), dict) else {}
    out["section_titles"] = {key: _text(titles_raw.get(key)) for key in SECTION_KEYS if _text(titles_raw.get(key))}
    lang = _text(raw.get("lang")).lower()
    if lang in DEFAULT_SECTION_TITLES:
        out["lang"] = lang
    else:
        out.pop("lang", None)
    return out


def section_title(resume: dict[str, Any], key: str) -> str:
    titles = resume.get("section_titles") if isinstance(resume.get("section_titles"), dict) else {}
    return _text(titles.get(key)) or DEFAULT_SECTION_TITLES[detect_lang(resume)][key]


def has_content(resume: dict[str, Any]) -> bool:
    """True when the resume holds more than a bare name (used to guard imports)."""
    doc = normalize_resume(resume)
    basics = doc["basics"]
    if any(basics[key] for key in ("title", "tagline", "phone", "email", "website", "location")):
        return True
    return bool(
        doc["summary"]
        or doc["skills"]
        or doc["skill_groups"]
        or doc["honors"]
        or doc["extra_sections"]
        or any(doc[section] for section in RECORD_SECTIONS)
    )


# --- Markdown rendering --------------------------------------------------------


def _period(record: dict[str, Any]) -> str:
    start, end = _text(record.get("start")), _text(record.get("end"))
    if start and end:
        return f"{start} – {end}"
    return start or end


def _record_heading(section: str, record: dict[str, Any]) -> str:
    org_key, role_key, _, _ = _RECORD_FIELDS[section]
    parts = [_text(record.get(org_key)), _text(record.get(role_key)), _period(record)]
    return " | ".join(part for part in parts if part)


def _record_has_body(record: dict[str, Any]) -> bool:
    return bool(record.get("summary") or record.get("bullets") or record.get("groups"))


def _append_record_body(lines: list[str], record: dict[str, Any]) -> None:
    if record.get("summary"):
        lines += [record["summary"], ""]
    if record.get("bullets"):
        lines += [f"- {bullet}" for bullet in record["bullets"]]
        lines.append("")
    for group in record.get("groups") or []:
        if group.get("label"):
            lines += [f"**{group['label']}**", ""]
        if group.get("bullets"):
            lines += [f"- {bullet}" for bullet in group["bullets"]]
            lines.append("")


def render_resume_markdown(resume_source: dict[str, Any]) -> str:
    """Render a resume mapping into canonical Markdown."""
    doc = normalize_resume(resume_source)
    zh = detect_lang(doc) == "zh"
    basics = doc["basics"]
    head = basics["name"] or doc["profile"]
    if basics["title"]:
        head = f"{head} | {basics['title']}"
    lines = [f"# {head}", ""]
    contact = [basics[key] for key in ("tagline", "location", "phone", "email", "website") if basics[key]]
    if contact:
        lines += [" | ".join(contact), ""]
    if doc["summary"]:
        lines += [f"## {section_title(doc, 'summary')}", "", doc["summary"], ""]
    if doc["skill_groups"] or doc["skills"]:
        lines += [f"## {section_title(doc, 'skills')}", ""]
        sep = "：" if zh else ": "
        for group in doc["skill_groups"]:
            if group["label"]:
                lines.append(f"- **{group['label']}**{sep}{group['text']}".rstrip("：: "))
            else:
                lines.append(f"- {group['text']}")
        lines += [f"- {skill}" for skill in doc["skills"]]
        lines.append("")
    for section in RECORD_SECTIONS:
        records = [r for r in doc[section] if _record_heading(section, r) or _record_has_body(r)]
        if not records:
            continue
        lines += [f"## {section_title(doc, section)}", ""]
        compact = [r for r in records if not _record_has_body(r)]
        if len(compact) == len(records):
            # Pure one-liners (typical for education / outputs): a list.
            lines += [f"- {_record_heading(section, r)}" for r in records]
            lines.append("")
            continue
        for record in records:
            heading = _record_heading(section, record)
            if heading:
                lines += [f"### {heading}", ""]
            _append_record_body(lines, record)
    if doc["honors"]:
        lines += [f"## {section_title(doc, 'honors')}", ""]
        lines += [f"- {item}" for item in doc["honors"]]
        lines.append("")
    for extra in doc["extra_sections"]:
        if extra["title"]:
            lines += [f"## {extra['title']}", ""]
        if extra["body"]:
            lines += [extra["body"], ""]
    return "\n".join(lines).rstrip() + "\n"


# --- Markdown import -----------------------------------------------------------

_SECTION_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("summary", ("概要", "摘要", "简介", "总结", "自我评价", "个人优势", "summary", "profile", "about")),
    ("skills", ("技能", "技术栈", "skill")),
    ("projects", ("项目", "project")),
    ("education", ("教育", "学历", "education")),
    ("outputs", ("论文", "成果", "发表", "专利", "publication", "output", "patent")),
    ("honors", ("荣誉", "奖", "其他", "honor", "award", "other")),
    ("experiences", ("经历", "经验", "工作", "实习", "experience", "employment", "work")),
)


def _section_key(title: str) -> str:
    lowered = title.lower()
    for key, words in _SECTION_KEYWORDS:
        if any(word in lowered for word in words):
            return key
    return ""


def _clean_contact_part(part: str) -> str:
    kept = [
        ch
        for ch in part
        if unicodedata.category(ch) not in ("So", "Sk", "Cf", "Cs") and ch not in "️‍"
    ]
    return "".join(kept).strip(" :：")


def _split_parts(text: str) -> list[str]:
    parts = [p.strip() for p in text.split("|")]
    if len(parts) == 1 and " · " in text:
        parts = [p.strip() for p in text.split(" · ")]
    return [p for p in parts if p]


def _split_period(text: str) -> tuple[str, str]:
    match = re.match(r"^(.*?)\s*[–—~～]\s*(.+)$", text) or re.match(r"^(.*?\d)\s+-\s+(.+)$", text)
    if not match:
        match = re.match(r"^(\d{4}[^-]*?)-(\d{4}.*|至今|现在|今|present|now)$", text, re.I)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return text.strip(), ""


def _record_from_heading(section: str, heading: str) -> dict[str, Any]:
    org_key, role_key, _, _ = _RECORD_FIELDS[section]
    parts = _split_parts(heading)
    record: dict[str, Any] = {org_key: "", role_key: "", "start": "", "end": ""}
    if parts and _YEAR_RE.search(parts[-1]) and len(parts) > 1:
        record["start"], record["end"] = _split_period(parts.pop())
    if parts:
        record[org_key] = parts[0]
    if len(parts) > 1:
        record[role_key] = " | ".join(parts[1:])
    return record


def _parse_records(section: str, body: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    group: dict[str, Any] | None = None
    fresh = False  # first content line after a heading may be a legacy meta line
    for raw in body:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped == "---":
            continue
        if stripped.startswith("### "):
            current = _record_from_heading(section, stripped[4:].strip())
            current.update({"summary": "", "bullets": [], "groups": []})
            records.append(current)
            group = None
            fresh = True
            continue
        bullet = _BULLET_RE.match(line)
        if current is None:
            # Lines before any ### heading: each bullet is a one-line record.
            text = bullet.group(1).strip() if bullet else stripped
            row = _record_from_heading(section, text)
            row.update({"summary": "", "bullets": [], "groups": []})
            records.append(row)
            continue
        group_match = _GROUP_RE.match(stripped)
        if group_match and not bullet:
            group = {"label": group_match.group(1).strip(), "bullets": []}
            current["groups"].append(group)
            fresh = False
            continue
        if bullet:
            target = group["bullets"] if group is not None else current["bullets"]
            target.append(bullet.group(1).strip())
            fresh = False
            continue
        if raw.startswith(("  ", "\t")) and (current["bullets"] or group):
            target = group["bullets"] if group is not None else current["bullets"]
            if target:
                target[-1] = f"{target[-1]} {stripped}"
                continue
        org_key = _RECORD_FIELDS[section][0]
        if fresh and _YEAR_RE.search(stripped) and not current["start"]:
            # Legacy renderer meta line: "org · 2020 - 2021".
            parts = _split_parts(stripped)
            if parts and _YEAR_RE.search(parts[-1]):
                current["start"], current["end"] = _split_period(parts.pop())
            if parts and not current[org_key]:
                current[org_key] = parts[0]
            fresh = False
            continue
        current["summary"] = f"{current['summary']}\n{stripped}".strip()
        fresh = False
    return records


def _parse_bullets(body: list[str]) -> list[str]:
    items: list[str] = []
    for raw in body:
        stripped = raw.strip()
        if not stripped or stripped == "---":
            continue
        bullet = _BULLET_RE.match(raw)
        if bullet:
            items.append(bullet.group(1).strip())
        elif raw.startswith(("  ", "\t")) and items:
            items[-1] = f"{items[-1]} {stripped}"
        else:
            items.append(stripped)
    return items


def _parse_paragraphs(body: list[str]) -> str:
    paragraphs: list[str] = []
    current: list[str] = []
    for raw in body:
        stripped = raw.strip()
        if not stripped or stripped == "---":
            if current:
                paragraphs.append("\n".join(current))
                current = []
            continue
        current.append(stripped)
    if current:
        paragraphs.append("\n".join(current))
    return "\n\n".join(paragraphs)


def _parse_header(lines: list[str], resume: dict[str, Any]) -> None:
    basics = resume["basics"]
    tagline: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped == "---":
            continue
        if stripped.startswith("# ") and not basics["name"]:
            parts = _split_parts(stripped[2:].strip())
            basics["name"] = parts[0] if parts else ""
            if len(parts) > 1:
                basics["title"] = " | ".join(parts[1:])
            continue
        emphasis = re.match(r"^(\*\*|\*|_)(.+?)\1$", stripped)
        if emphasis and not basics["title"]:
            basics["title"] = emphasis.group(2).strip()
            continue
        for part in _split_parts(stripped):
            clean = _clean_contact_part(part)
            if not clean:
                continue
            compact = clean.replace(" ", "")
            if not basics["email"] and _EMAIL_RE.match(compact):
                basics["email"] = compact
            elif not basics["phone"] and _PHONE_RE.match(clean) and sum(c.isdigit() for c in clean) >= 7:
                basics["phone"] = clean
            elif not basics["website"] and _URL_RE.match(compact):
                basics["website"] = compact
            else:
                tagline.append(clean)
    basics["tagline"] = " | ".join(tagline)


def parse_resume_markdown(text: str, *, profile: str = "") -> dict[str, Any]:
    """Parse resume Markdown (canonical or hand-written) into the structured shape.

    Deterministic: ``# 姓名 | 头衔`` header, a contact line, ``## 段落`` mapped
    by keyword, ``### 单位 | 职位 | 时间`` records with ``**分组**`` bullets.
    Sections that match no known key are kept verbatim in ``extra_sections``.
    """
    clean = re.sub(r"<!--.*?-->", "", str(text or ""), flags=re.S)
    fence = re.match(r"^\s*```(?:markdown|md)?\s*\n(.*?)\n```\s*$", clean, re.S)
    if fence:
        clean = fence.group(1)
    resume: dict[str, Any] = {
        "profile": profile,
        "visibility": "private",
        "basics": {key: "" for key in _BASICS_FIELDS},
        "summary": "",
        "skills": [],
        "skill_groups": [],
        "experiences": [],
        "projects": [],
        "outputs": [],
        "education": [],
        "honors": [],
        "extra_sections": [],
        "section_titles": {},
    }
    header: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    for line in clean.splitlines():
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif sections:
            sections[-1][1].append(line)
        else:
            header.append(line)
    _parse_header(header, resume)
    for title, body in sections:
        key = _section_key(title)
        if not key or (key in resume["section_titles"]):
            resume["extra_sections"].append({"title": title, "body": "\n".join(body).strip()})
            continue
        resume["section_titles"][key] = title
        if key == "summary":
            resume["summary"] = _parse_paragraphs(body)
        elif key == "skills":
            for item in _parse_bullets(body):
                match = _SKILL_GROUP_RE.match(item)
                if match:
                    resume["skill_groups"].append({"label": match.group(1).strip(), "text": match.group(2).strip()})
                else:
                    resume["skills"].append(item)
        elif key == "honors":
            resume["honors"] = _parse_bullets(body)
        else:
            resume[key] = _parse_records(key, body)
    resume["lang"] = detect_lang(resume)
    return normalize_resume(resume, profile=profile)


def looks_like_markdown_resume(text: str) -> bool:
    """Heuristic: the deterministic parser applies when there are ## sections."""
    return len(re.findall(r"^##\s+\S", str(text or ""), re.M)) >= 2


# --- HTML / PDF --------------------------------------------------------------

RESUME_CSS = """
@page { size: A4; margin: 8mm 13mm; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html { background: #e9ecf2; }
body {
  font-family: "Noto Sans CJK SC", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #1a1a1a; font-size: 9.2pt; line-height: 1.36;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.page { background: #fff; width: 210mm; min-height: 297mm; margin: 12px auto; padding: 8mm 13mm;
  box-shadow: 0 2px 14px rgba(15, 23, 42, 0.18); }
@media print {
  html { background: #fff; }
  .page { width: auto; min-height: 0; margin: 0; padding: 0; box-shadow: none; }
}
header { display: flex; justify-content: space-between; align-items: center;
  border-bottom: 2px solid #2563eb; padding-bottom: 7px; margin-bottom: 7px; }
.head-left { flex: 1; padding-right: 14px; }
h1 { font-size: 17pt; color: #111; letter-spacing: 1px; }
.subtitle { font-size: 10.5pt; color: #2563eb; font-weight: 600; margin-top: 3px; }
.contact { font-size: 8.4pt; color: #555; margin-top: 5px; line-height: 1.5; }
.photo { width: 25mm; height: 33.3mm; object-fit: cover; display: block; border-radius: 2px;
  padding: 2px; background: #fff; border: 1px solid #c3d0ea; box-shadow: 0 2px 6px rgba(37,99,235,0.18); }
h2 { font-size: 10.2pt; color: #2563eb; margin: 7px 0 3px;
  padding-bottom: 2px; border-bottom: 1px solid #d4d4d4; letter-spacing: 0.3px; }
h3 { font-size: 9.5pt; color: #111; margin: 5px 0 2px;
  display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
h3 .meta { font-size: 8pt; color: #666; font-weight: 500; white-space: nowrap; }
.group { font-size: 8.8pt; font-weight: 700; color: #333; margin: 4px 0 1px; }
p { margin-bottom: 3px; text-align: justify; }
ul { list-style: none; margin: 1px 0 3px; }
li { position: relative; padding-left: 12px; margin-bottom: 2px; }
li::before { content: "\\25AA"; position: absolute; left: 0; color: #2563eb; font-size: 7pt; top: 1.5px; }
strong { color: #1d4ed8; font-weight: 700; }
.group strong, h1 strong, h3 strong { color: inherit; }
em { color: #444; }
ul.inline li { display: inline; padding-left: 0; margin-right: 0; }
ul.inline li::before { content: none; }
ul.inline li + li::before { content: "|"; position: static; color: #9aa4b2; font-size: inherit; margin: 0 8px; }
.summary { background: #f5f8ff; border-left: 3px solid #2563eb; padding: 5px 10px; border-radius: 2px; }
"""


def _markdown_html(text: str) -> str:
    import markdown as markdown_lib

    from nblane.core.public_site import _sanitize_html_url_attrs

    rendered = markdown_lib.markdown(text, extensions=["extra", "sane_lists"], output_format="html5")
    return _sanitize_html_url_attrs(rendered)


def _decorate_body(body: str, *, summary_title: str, inline_titles: tuple[str, ...] = ()) -> tuple[str, str]:
    """Split rendered Markdown into (header inner HTML, rest) and add classes."""

    def h1(match: re.Match[str]) -> str:
        inner = match.group(1)
        if " | " in inner:
            name, title = inner.split(" | ", 1)
            return f'<h1>{name}</h1>\n<div class="subtitle">{title}</div>'
        return match.group(0)

    def h3(match: re.Match[str]) -> str:
        parts = match.group(1).split(" | ")
        if len(parts) > 1 and _YEAR_RE.search(parts[-1]):
            return f'<h3><span>{" · ".join(parts[:-1])}</span> <span class="meta">{parts[-1]}</span></h3>'
        return f'<h3>{" · ".join(parts)}</h3>'

    body = re.sub(r"<h1>(.*?)</h1>", h1, body, count=1, flags=re.S)
    body = re.sub(r"<h3>(.*?)</h3>", h3, body, flags=re.S)
    body = re.sub(r"<p><strong>([^<]*)</strong></p>", r'<p class="group">\1</p>', body)
    if summary_title:
        body = re.sub(
            rf"(<h2>{re.escape(html.escape(summary_title, quote=False))}</h2>\s*)<p>",
            r'\1<p class="summary">',
            body,
            count=1,
        )
    for inline_title in inline_titles:
        if not inline_title:
            continue
        # Short one-line lists (education, honors) flow inline like a hand-made resume.
        body = re.sub(
            rf"(<h2>{re.escape(html.escape(inline_title, quote=False))}</h2>\s*)<ul>",
            r'\1<ul class="inline">',
            body,
            count=1,
        )
    cut = body.find("<h2")
    head, rest = (body[:cut], body[cut:]) if cut >= 0 else (body, "")
    if "<h1" not in head:
        return "", body
    # The first paragraph after the title block is the contact line.
    head = re.sub(r"<p>", '<p class="contact">', head, count=1)
    return head, rest


def render_resume_html(
    markdown_text: str,
    *,
    title: str = "Resume",
    photo_src: str = "",
    lang: str = "zh",
    summary_title: str = "",
    inline_titles: tuple[str, ...] = (),
) -> str:
    """Standalone A4 resume page from Markdown; *photo_src* goes in the header.

    Lists right under *inline_titles* headings render inline (``a | b | c``).
    """
    head, rest = _decorate_body(
        _markdown_html(markdown_text), summary_title=summary_title, inline_titles=inline_titles
    )
    photo = f'<img class="photo" src="{html.escape(photo_src)}" alt="" />' if photo_src else ""
    header = f'<header><div class="head-left">{head}</div>{photo}</header>' if head or photo else ""
    html_lang = "zh-CN" if lang == "zh" else "en"
    return (
        f'<!DOCTYPE html>\n<html lang="{html_lang}">\n<head>\n<meta charset="utf-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(title)}</title>\n<style>{RESUME_CSS}</style>\n</head>\n"
        f'<body><div class="page">\n{header}\n{rest}\n</div></body>\n</html>\n'
    )


def photo_data_uri(path: Path | None) -> str:
    """Inline the photo so exported HTML/PDF files are self-contained."""
    if path is None or not path.is_file():
        return ""
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


class ResumePdfUnavailable(RuntimeError):
    """No headless Chromium could be found or it failed to print."""


def find_chromium() -> str:
    """Locate a Chromium binary for ``--print-to-pdf`` (env override first).

    Playwright's headless shell is preferred over a snap ``chromium`` because
    snap confinement cannot read files outside ``$HOME``.
    """
    override = os.environ.get("NBLANE_PDF_CHROMIUM", "").strip()
    if override:
        return override
    cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "") or Path.home() / ".cache" / "ms-playwright")
    shells = sorted(cache.glob("chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell"))
    if shells:
        return str(shells[-1])
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        found = shutil.which(name)
        if found:
            return found
    return ""


def render_resume_pdf(page_html: str, *, timeout: float = 60.0) -> bytes:
    """Print *page_html* to an A4 PDF with headless Chromium."""
    binary = find_chromium()
    if not binary:
        raise ResumePdfUnavailable("未找到 Chromium，无法导出 PDF；可下载 HTML 后用浏览器打印。")
    scratch = Path.home() / ".cache" / "nblane" / "resume-pdf"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as tmp:
        src = Path(tmp) / "resume.html"
        out = Path(tmp) / "resume.pdf"
        src.write_text(page_html, encoding="utf-8")
        cmd = [
            binary,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={out}",
            src.as_uri(),
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ResumePdfUnavailable(f"PDF 导出失败：{exc}") from exc
        if not out.is_file() or out.stat().st_size == 0:
            raise ResumePdfUnavailable("PDF 导出失败：Chromium 未生成文件。")
        return out.read_bytes()


# --- HTML import ---------------------------------------------------------------


class _HtmlToMarkdown:
    """Tiny stdlib HTML → Markdown converter for hand-made resume pages.

    Handles the tags resume pages actually use (h1–h3, p, div, li, strong,
    em, br, span.meta, .subtitle/.contact/.group classes) and drops styles,
    scripts and images. ``&nbsp;|&nbsp;`` separated list items are split.
    """

    def __init__(self) -> None:
        from html.parser import HTMLParser

        outer = self
        self.blocks: list[tuple[str, str]] = []
        self._buf: list[str] = []
        self._kind = ""
        self._skip = 0

        class _Parser(HTMLParser):
            def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                outer._start(tag, dict(attrs))

            def handle_endtag(self, tag: str) -> None:
                outer._end(tag)

            def handle_data(self, data: str) -> None:
                outer._data(data)

        self._parser = _Parser(convert_charrefs=True)

    def _flush(self) -> None:
        # "&nbsp;|&nbsp;" separates items packed into one <li>; keep it as \x00.
        raw = re.sub(r"[ \t\u00a0]*\u00a0\|\u00a0[ \t\u00a0]*", "\x00", "".join(self._buf))
        text = re.sub(r"[ \t\r\n\u00a0]+", " ", raw).strip()
        if text:
            self.blocks.append((self._kind or "p", text))
        self._buf = []
        self._kind = ""

    def _start(self, tag: str, attrs: dict[str, str | None]) -> None:
        cls = str(attrs.get("class") or "")
        if tag in ("style", "script", "head", "title"):
            self._skip += 1
            return
        if tag in ("h1", "h2", "h3", "p", "li", "div"):
            self._flush()
            self._kind = tag
            if "subtitle" in cls:
                self._kind = "subtitle"
            elif "group" in cls:
                self._kind = "group"
            elif "contact" in cls:
                self._kind = "p"
        elif tag in ("strong", "b"):
            self._buf.append("**")
        elif tag in ("em", "i"):
            self._buf.append("*")
        elif tag == "br":
            self._buf.append(" ")
        elif tag == "span" and "meta" in cls:
            self._buf.append(" | ")

    def _end(self, tag: str) -> None:
        if tag in ("style", "script", "head", "title"):
            self._skip = max(0, self._skip - 1)
            return
        if tag in ("strong", "b"):
            self._buf.append("**")
        elif tag in ("em", "i"):
            self._buf.append("*")
        elif tag in ("h1", "h2", "h3", "p", "li", "div"):
            self._flush()

    def _data(self, data: str) -> None:
        if not self._skip:
            self._buf.append(data)

    def convert(self, text: str) -> str:
        self._parser.feed(text)
        self._parser.close()
        self._flush()
        lines: list[str] = []
        title_seen = False
        for kind, text in self.blocks:
            text = re.sub(r"\*\*\s+\*\*", " ", text).replace("** **", " ")
            if kind == "h1":
                lines += [f"# {text}"]
                title_seen = True
            elif kind == "subtitle" and title_seen and lines and lines[-1].startswith("# "):
                lines[-1] = f"{lines[-1]} | {text}"
            elif kind == "h2":
                lines += ["", f"## {text}", ""]
            elif kind == "h3":
                lines += ["", f"### {text.replace(' · ', ' | ')}", ""]
            elif kind == "group":
                lines += ["", f"**{text}**", ""]
            elif kind == "li":
                for part in text.split("\x00"):
                    if part.strip():
                        lines.append(f"- {part.strip().replace(' · ', ' | ')}")
            else:
                lines += ["", text.replace("\x00", " | "), ""]
        out = "\n".join(lines).replace("\x00", " | ")
        return re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"


def html_resume_to_markdown(text: str) -> str:
    """Convert a hand-made resume HTML page into importable Markdown."""
    return _HtmlToMarkdown().convert(str(text or ""))
