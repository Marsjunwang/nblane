"""Structured tag helpers for personal workflow facets."""

from __future__ import annotations

from dataclasses import dataclass, field


KNOWN_TAG_NAMESPACES = (
    "flow",
    "company",
    "person",
    "project",
    "habit",
)


def _clean_text(value: object) -> str:
    """Return a stripped string representation."""
    return str(value or "").strip()


def _normalize_tag_list(value: object) -> list[str]:
    """Coerce a scalar or sequence into a de-duplicated tag list."""
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = value.replace("\n", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        raw_items: list[str] = []
        for item in value:
            if isinstance(item, str):
                raw_items.extend(item.replace("\n", ",").split(","))
            else:
                clean = _clean_text(item)
                if clean:
                    raw_items.append(clean)
    else:
        clean = _clean_text(value)
        raw_items = [clean] if clean else []

    out: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        clean = _clean_text(item)
        if not clean:
            continue
        key = clean.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(clean)
    return out


def tag_namespace(tag: str) -> str:
    """Return the namespace portion of a tag when present."""
    clean = _clean_text(tag)
    if "/" not in clean:
        return ""
    namespace, _value = clean.split("/", 1)
    return namespace.casefold()


def tag_value(tag: str) -> str:
    """Return the value portion of a namespaced tag when present."""
    clean = _clean_text(tag)
    if "/" not in clean:
        return clean
    _namespace, value = clean.split("/", 1)
    return value.strip()


@dataclass
class TagFacets:
    """Structured view over namespaced workflow tags."""

    flow: str = ""
    companies: list[str] = field(default_factory=list)
    people: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    habits: list[str] = field(default_factory=list)
    other: list[str] = field(default_factory=list)

    def to_tags(self) -> list[str]:
        """Serialize the structured facets back into plain tag strings."""
        out: list[str] = []
        if self.flow:
            out.append(f"flow/{_clean_text(self.flow)}")
        out.extend(
            f"company/{value}"
            for value in _normalize_tag_list(self.companies)
        )
        out.extend(
            f"person/{value}"
            for value in _normalize_tag_list(self.people)
        )
        out.extend(
            f"project/{value}"
            for value in _normalize_tag_list(self.projects)
        )
        out.extend(
            f"habit/{value}"
            for value in _normalize_tag_list(self.habits)
        )
        out.extend(_normalize_tag_list(self.other))
        return _normalize_tag_list(out)


def parse_tag_facets(tags: object) -> TagFacets:
    """Group raw tags into workflow facets and plain leftovers."""
    facets = TagFacets()
    for tag in _normalize_tag_list(tags):
        namespace = tag_namespace(tag)
        value = tag_value(tag)
        if namespace == "flow" and value and not facets.flow:
            facets.flow = value
        elif namespace == "company" and value:
            facets.companies = _normalize_tag_list(
                [*facets.companies, value]
            )
        elif namespace == "person" and value:
            facets.people = _normalize_tag_list([*facets.people, value])
        elif namespace == "project" and value:
            facets.projects = _normalize_tag_list(
                [*facets.projects, value]
            )
        elif namespace == "habit" and value:
            facets.habits = _normalize_tag_list([*facets.habits, value])
        else:
            facets.other = _normalize_tag_list([*facets.other, tag])
    return facets


def merge_tag_facets(
    *,
    flow: str = "",
    companies: object = None,
    people: object = None,
    projects: object = None,
    habits: object = None,
    other: object = None,
) -> list[str]:
    """Build a raw tag list from structured facet inputs."""
    return TagFacets(
        flow=_clean_text(flow),
        companies=_normalize_tag_list(companies),
        people=_normalize_tag_list(people),
        projects=_normalize_tag_list(projects),
        habits=_normalize_tag_list(habits),
        other=_normalize_tag_list(other),
    ).to_tags()


__all__ = [
    "KNOWN_TAG_NAMESPACES",
    "TagFacets",
    "merge_tag_facets",
    "parse_tag_facets",
    "tag_namespace",
    "tag_value",
]
