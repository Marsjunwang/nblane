"""Helpers for editing the human-owned parts of ``SKILL.md``."""

from __future__ import annotations

import re

IDENTITY_FIELDS: tuple[str, ...] = (
    "Name",
    "Domain",
    "Journey",
    "Current Role",
    "North Star",
)

LONG_NARRATIVE_SECTIONS: tuple[str, ...] = (
    "Research Fingerprint",
    "Thinking & Communication Style",
    "Growth Log",
    "Influence & Output",
)

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


def apply_profile_context_structured_edits(
    text: str,
    *,
    identity_fields: dict[str, str] | None = None,
    narrative_sections: dict[str, str] | None = None,
) -> str:
    """Apply human-owned Profile Context edits to ``SKILL.md``.

    Generated blocks are not part of this write path. Narrative updates are
    limited to the long-form sections owned by the human author.
    """
    next_text = text
    if identity_fields:
        next_text = update_identity_fields(next_text, identity_fields)
    for title, body in (narrative_sections or {}).items():
        if title not in LONG_NARRATIVE_SECTIONS:
            continue
        next_text = replace_section_body(next_text, title, body)
    return next_text
