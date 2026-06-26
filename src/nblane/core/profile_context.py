"""Helpers for editing the human-owned parts of ``SKILL.md``."""

from __future__ import annotations

import re

IDENTITY_FIELDS: tuple[str, ...] = (
    "Name",
    "Domain",
    "Journey",
    "Current Role",
    "North Star",
    "North Star Brief",
    "North Star Visibility",
)

NORTH_STAR_VISIBILITIES: tuple[str, ...] = (
    "visible",
    "discreet",
    "hidden",
    "private",
)
DEFAULT_NORTH_STAR_VISIBILITY = "discreet"

LONG_NARRATIVE_SECTIONS: tuple[str, ...] = (
    "Research Fingerprint",
    "Thinking & Communication Style",
    "Growth Log",
    "Influence & Output",
)

CORE_COMPETENCIES_SECTION = "Core Competencies"
COMPETENCY_STATUSES: tuple[str, ...] = (
    "locked",
    "learning",
    "solid",
    "expert",
)
_COMPETENCY_HEADER = ("Area", "Status", "Notes")

GENERATED_BLOCKS: tuple[str, ...] = (
    "skill_tree",
    "current_focus",
)

_HEADING_RE = re.compile(r"^#{1,3}\s")
_IDENTITY_BULLET_RE = re.compile(
    r"^(?P<prefix>\s*-\s+\*\*(?P<label>[^*]+)\*\*:\s*)"
    r"(?P<value>.*?)(?P<newline>\r?\n?)$"
)
_GENERATED_BLOCK_RE = re.compile(
    r"<!--\s*BEGIN GENERATED:(?P<name>[A-Za-z0-9_-]+)\s*-->"
    r".*?"
    r"<!--\s*END GENERATED:(?P=name)\s*-->",
    re.DOTALL,
)


def parse_skill_md_sections(text: str) -> list[tuple[str, str]]:
    """Split Markdown into ``(heading, body)`` pairs.

    Content before the first heading is stored under ``"(header)"``. Heading
    text includes the leading ``#`` markers so it can be rejoined losslessly.
    """
    parts: list[tuple[str, str]] = []
    current_heading = "(header)"
    buf: list[str] = []

    for line in text.splitlines(keepends=True):
        if _HEADING_RE.match(line):
            parts.append((current_heading, "".join(buf)))
            current_heading = line.strip()
            buf = []
            continue
        buf.append(line)

    parts.append((current_heading, "".join(buf)))
    return parts


def rejoin_sections(sections: list[tuple[str, str]]) -> str:
    """Reassemble parsed sections into Markdown."""
    parts: list[str] = []
    for heading, body in sections:
        if heading != "(header)":
            parts.append(heading + "\n")
        parts.append(body)
    return "".join(parts)


def section_title(heading: str) -> str:
    """Return a normalized title for a Markdown heading."""
    return re.sub(r"^#{1,3}\s*", "", heading).strip()


def section_body(text: str, title: str) -> str:
    """Return the body for a section title, or ``""`` if absent."""
    for heading, body in parse_skill_md_sections(text):
        if section_title(heading) == title:
            return body
    return ""


def normalize_north_star_visibility(value: object) -> str:
    """Normalize the Identity North Star display preference."""
    raw = str(value or "").strip().lower()
    if raw == "public":
        raw = "visible"
    return (
        raw
        if raw in NORTH_STAR_VISIBILITIES
        else DEFAULT_NORTH_STAR_VISIBILITY
    )


def _compact_text(value: object, max_chars: int = 120) -> str:
    """Return a single-line display summary without writing it back."""
    text = " ".join(str(value or "").split())
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 3)].rstrip() + "..."


def north_star_payload_from_identity(
    identity: dict[str, str],
    *,
    ui: dict[str, str] | None = None,
) -> dict[str, object]:
    """Return a privacy-aware North Star payload for UI read models."""
    full = str(identity.get("North Star", "") or "").strip()
    brief = str(identity.get("North Star Brief", "") or "").strip()
    visibility = normalize_north_star_visibility(
        identity.get("North Star Visibility")
    )
    is_set = bool(full or brief)

    def text(key: str, fallback: str) -> str:
        if not ui:
            return fallback
        return str(ui.get(key, fallback) or fallback)

    if not is_set:
        display = text("north_star_empty", "No North Star set")
    elif visibility == "visible":
        display = full or brief
    elif visibility == "discreet":
        display = brief or _compact_text(full)
    elif visibility == "hidden":
        display = text("north_star_hidden_display", "North Star set")
    else:
        display = ""

    return {
        "visibility": visibility,
        "display_text": display,
        "is_set": is_set,
        "locked": visibility == "private",
        "has_brief": bool(brief),
    }


def north_star_context_from_identity(
    identity: dict[str, str],
    *,
    for_agent: bool = False,
) -> str:
    """Return North Star text allowed for matching or agent prompts."""
    full = str(identity.get("North Star", "") or "").strip()
    brief = str(identity.get("North Star Brief", "") or "").strip()
    visibility = normalize_north_star_visibility(
        identity.get("North Star Visibility")
    )
    if visibility == "private":
        return ""
    if for_agent:
        return full or brief
    if visibility == "visible":
        return full or brief
    if visibility == "discreet":
        return brief or _compact_text(full)
    return ""


def replace_section_body(text: str, title: str, body: str) -> str:
    """Replace one Markdown section body by exact heading title."""
    sections = parse_skill_md_sections(text)
    replaced = False
    next_sections: list[tuple[str, str]] = []
    for heading, current_body in sections:
        if section_title(heading) == title:
            next_sections.append((heading, body))
            replaced = True
        else:
            next_sections.append((heading, current_body))
    if replaced:
        return rejoin_sections(next_sections)
    suffix = "" if text.endswith("\n") else "\n"
    return f"{text}{suffix}\n## {title}\n{body}"


def parse_identity_fields_from_body(body: str) -> dict[str, str]:
    """Parse short ``Identity`` bullet fields from a section body."""
    values = {field: "" for field in IDENTITY_FIELDS}
    for line in body.splitlines(keepends=True):
        match = _IDENTITY_BULLET_RE.match(line)
        if not match:
            continue
        label = match.group("label").strip()
        if label in values:
            values[label] = match.group("value").strip()
    return values


def parse_identity_fields(text: str) -> dict[str, str]:
    """Parse short ``Identity`` fields from a full ``SKILL.md`` document."""
    return parse_identity_fields_from_body(section_body(text, "Identity"))


def update_identity_fields_in_body(
    body: str,
    updates: dict[str, str],
) -> str:
    """Update only exact Identity bullet rows in a section body.

    Missing known fields are inserted before the section's horizontal rule when
    possible. This keeps generated blocks and unrelated prose untouched.
    """
    clean_updates = {
        field: str(updates[field]).strip()
        for field in IDENTITY_FIELDS
        if field in updates
    }
    if not clean_updates:
        return body

    seen: set[str] = set()
    out: list[str] = []
    for line in body.splitlines(keepends=True):
        match = _IDENTITY_BULLET_RE.match(line)
        if not match:
            out.append(line)
            continue
        label = match.group("label").strip()
        if label not in clean_updates:
            out.append(line)
            continue
        newline = match.group("newline") or "\n"
        out.append(f"{match.group('prefix')}{clean_updates[label]}{newline}")
        seen.add(label)

    missing = [field for field in clean_updates if field not in seen]
    if not missing:
        return "".join(out)

    insert_at = len(out)
    for idx, line in enumerate(out):
        if re.match(r"^\s*---+\s*$", line):
            insert_at = idx
            break
    lines_to_insert = [
        f"- **{field}**: {clean_updates[field]}\n"
        for field in missing
    ]
    out[insert_at:insert_at] = lines_to_insert
    return "".join(out)


def update_identity_fields(text: str, updates: dict[str, str]) -> str:
    """Update short ``Identity`` fields in a full ``SKILL.md`` document."""
    body = section_body(text, "Identity")
    updated = update_identity_fields_in_body(body, updates)
    return replace_section_body(text, "Identity", updated)


def extract_generated_blocks(text: str) -> dict[str, str]:
    """Return generated block name -> full block text including markers."""
    blocks: dict[str, str] = {}
    for match in _GENERATED_BLOCK_RE.finditer(text):
        blocks[match.group("name")] = match.group(0).strip()
    return blocks


def _split_table_row(line: str) -> list[str]:
    """Split a Markdown table row into trimmed, unescaped cells.

    Splits only on unescaped ``|`` so that ``\\|`` inside a cell is preserved.
    """
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|") and not stripped.endswith("\\|"):
        stripped = stripped[:-1]
    cells = re.split(r"(?<!\\)\|", stripped)
    return [cell.replace("\\|", "|").strip() for cell in cells]


def _is_table_divider(cells: list[str]) -> bool:
    """True when every cell is a Markdown table divider like ``---`` / ``:--:``."""
    return bool(cells) and all(
        re.fullmatch(r":?-{1,}:?", cell or "") for cell in cells
    )


def _normalize_competency_status(value: object) -> str:
    """Lowercase the status; keep unknown values verbatim for the UI to flag."""
    raw = str(value or "").strip()
    lowered = raw.lower()
    return lowered if lowered in COMPETENCY_STATUSES else raw


def parse_core_competencies(text: str) -> list[dict[str, str]]:
    """Parse the ``Core Competencies`` table into ``[{area,status,notes}]`` rows.

    Skips HTML comments, blank lines, the header row and the ``|---|`` divider.
    Only the first three columns are kept; extra columns are dropped. ``status``
    is lowercased and left verbatim when it is not a known status so the editor
    can flag it. Rows with no Area and no Notes are ignored.
    """
    body = section_body(text, CORE_COMPETENCIES_SECTION)
    rows: list[dict[str, str]] = []
    seen_header = False
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--") or "|" not in stripped:
            continue
        cells = _split_table_row(line)
        if _is_table_divider(cells):
            continue
        if not seen_header:
            # The first table row is the header; remember it and skip.
            seen_header = True
            if [c.lower() for c in cells[:3]] == [
                h.lower() for h in _COMPETENCY_HEADER
            ]:
                continue
        area = cells[0] if len(cells) > 0 else ""
        status = cells[1] if len(cells) > 1 else ""
        notes = cells[2] if len(cells) > 2 else ""
        if not area and not notes:
            continue
        rows.append(
            {
                "area": area,
                "status": _normalize_competency_status(status),
                "notes": notes,
            }
        )
    return rows


def _competency_comment_lines(body: str) -> list[str]:
    """Return the HTML comment lines that precede the table, to preserve them."""
    comments: list[str] = []
    for line in body.splitlines():
        if line.strip().startswith("<!--"):
            comments.append(line.rstrip("\n"))
    return comments


def _render_competency_table(rows: list[dict[str, str]]) -> list[str]:
    """Render rows as Markdown table lines (header + divider + body rows)."""
    def cell(value: object) -> str:
        return str(value or "").replace("|", "\\|").strip()

    lines = [
        "| " + " | ".join(_COMPETENCY_HEADER) + " |",
        "|" + "|".join(["------"] * len(_COMPETENCY_HEADER)) + "|",
    ]
    for row in rows:
        area = cell(row.get("area"))
        status = _normalize_competency_status(row.get("status"))
        notes = cell(row.get("notes"))
        if not area and not notes and not status:
            continue
        lines.append(f"| {area} | {cell(status)} | {notes} |")
    return lines


def update_core_competencies(text: str, rows: list[dict[str, str]]) -> str:
    """Rebuild the ``Core Competencies`` table from structured rows.

    Preserves the HTML comment lines above the table and the section's spacing
    conventions; only the table body is replaced. An empty ``rows`` writes a
    header-only table rather than deleting the section.
    """
    body = section_body(text, CORE_COMPETENCIES_SECTION)
    comments = _competency_comment_lines(body)
    table = _render_competency_table(rows)
    parts: list[str] = [""]
    parts.extend(comments)
    parts.append("")
    parts.extend(table)
    parts.append("")
    new_body = "\n".join(parts) + "\n"
    return replace_section_body(text, CORE_COMPETENCIES_SECTION, new_body)


def apply_profile_context_structured_edits(
    text: str,
    *,
    identity_fields: dict[str, str] | None = None,
    narrative_sections: dict[str, str] | None = None,
    core_competencies: list[dict[str, str]] | None = None,
) -> str:
    """Apply human-owned Profile Context edits to ``SKILL.md``.

    Generated blocks are not part of this write path. Narrative updates are
    limited to the long-form sections owned by the human author. ``core_competencies``
    rewrites the Core Competencies table when provided.
    """
    next_text = text
    if identity_fields:
        next_text = update_identity_fields(next_text, identity_fields)
    for title, body in (narrative_sections or {}).items():
        if title not in LONG_NARRATIVE_SECTIONS:
            continue
        next_text = replace_section_body(next_text, title, body)
    if core_competencies is not None:
        next_text = update_core_competencies(next_text, core_competencies)
    return next_text
