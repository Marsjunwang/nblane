"""Internal experience-case facts for nblane profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
import re

import yaml

from nblane.core import git_backup
from nblane.core.file_write import atomic_write_text
from nblane.core.paths import PROFILES_DIR
from nblane.core.yaml_io import _load_yaml_dict

EXPERIENCE_FILENAME = "experience.yaml"
EXPERIENCE_STATUSES = ("active", "completed", "archived")
EXPERIENCE_VISIBILITIES = ("private", "public")


def profile_dir(name: str) -> Path:
    """Return path to ``profiles/{name}``."""
    return PROFILES_DIR / name


def _profile_file_path(name_or_dir: str | Path) -> Path:
    """Resolve a profile-scoped experience path."""
    if isinstance(name_or_dir, Path):
        if name_or_dir.suffix in (".yaml", ".yml"):
            return name_or_dir
        return name_or_dir / EXPERIENCE_FILENAME
    raw = name_or_dir.strip()
    path = Path(raw)
    if (
        path.suffix in (".yaml", ".yml")
        or "/" in raw
        or raw.startswith(".")
        or path.exists()
    ):
        return path if path.suffix else path / EXPERIENCE_FILENAME
    return profile_dir(raw) / EXPERIENCE_FILENAME


def _profile_name(name_or_dir: str | Path) -> str:
    if isinstance(name_or_dir, Path):
        return name_or_dir.stem if name_or_dir.suffix else name_or_dir.name
    return Path(name_or_dir).stem if "/" in name_or_dir else str(name_or_dir)


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _clean_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = value.replace("\n", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        raw_items = []
        for item in value:
            if isinstance(item, str):
                raw_items.extend(item.replace("\n", ",").split(","))
            else:
                raw_items.append(_clean_text(item))
    else:
        raw_items = [_clean_text(value)]
    out: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        clean = _clean_text(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _clean_choice(value: object, options: tuple[str, ...], default: str) -> str:
    clean = _clean_text(value)
    return clean if clean in options else default


def _slug_id(value: str, *, fallback: str = "experience") -> str:
    clean = value.strip().lower()
    clean = re.sub(r"[^a-z0-9\u4e00-\u9fff._~-]+", "-", clean)
    clean = clean.strip(".-")
    return clean or fallback


def _next_experience_id(cases: list["ExperienceCase"], label: str) -> str:
    base = f"experience:{_slug_id(label)}"
    existing = {case.id for case in cases if case.id}
    if base not in existing:
        return base
    index = 2
    while f"{base}-{index}" in existing:
        index += 1
    return f"{base}-{index}"


def _find_case(book: "ExperienceBook", case_id: str) -> "ExperienceCase":
    clean_id = _clean_text(case_id)
    for case in book.experience_cases:
        if case.id == clean_id:
            return case
    raise KeyError(f"Unknown experience case: {clean_id}")


@dataclass
class ExperienceCase:
    """One internal experience case for resume/project context."""

    id: str
    organization: str
    role: str = ""
    location: str = ""
    status: str = "active"
    time_range: str = ""
    summary: str = ""
    project_refs: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    visibility: str = "private"
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "ExperienceCase":
        """Build an experience case from YAML."""
        if not isinstance(data, dict):
            return cls(id="", organization="")
        return cls(
            id=_clean_text(data.get("id")),
            organization=_clean_text(data.get("organization")),
            role=_clean_text(data.get("role")),
            location=_clean_text(data.get("location")),
            status=_clean_choice(data.get("status"), EXPERIENCE_STATUSES, "active"),
            time_range=_clean_text(data.get("time_range")),
            summary=_clean_text(data.get("summary")),
            project_refs=_clean_list(data.get("project_refs")),
            source_refs=_clean_list(data.get("source_refs")),
            visibility=_clean_choice(
                data.get("visibility"),
                EXPERIENCE_VISIBILITIES,
                "private",
            ),
            notes=_clean_text(data.get("notes")),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize for YAML output."""
        out: dict[str, object] = {
            "id": self.id,
            "organization": self.organization,
            "status": self.status,
            "visibility": self.visibility,
        }
        for key in (
            "role",
            "location",
            "time_range",
            "summary",
            "notes",
        ):
            value = getattr(self, key)
            if value:
                out[key] = value
        for key in ("project_refs", "source_refs"):
            values = getattr(self, key)
            if values:
                out[key] = list(values)
        return out


@dataclass
class ExperienceBook:
    """Profile-level experience-case document."""

    profile: str = ""
    updated: str = ""
    schema_version: str = "1.0"
    experience_cases: list[ExperienceCase] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ExperienceBook":
        """Build an experience book from YAML."""
        if not isinstance(data, dict):
            return cls()
        raw_cases = data.get("experience_cases") or []
        cases: list[ExperienceCase] = []
        if isinstance(raw_cases, list):
            for item in raw_cases:
                if isinstance(item, dict):
                    cases.append(ExperienceCase.from_dict(item))
        return cls(
            profile=_clean_text(data.get("profile")),
            updated=_clean_text(data.get("updated")),
            schema_version=_clean_text(data.get("schema_version")) or "1.0",
            experience_cases=cases,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the document for YAML output."""
        return {
            "schema_version": self.schema_version or "1.0",
            "profile": self.profile,
            "updated": self.updated,
            "experience_cases": [
                case.to_dict() for case in self.experience_cases
            ],
        }

    def by_id(self) -> dict[str, ExperienceCase]:
        """Return case id -> case."""
        return {case.id: case for case in self.experience_cases if case.id}


def load_experience_book(name_or_dir: str | Path) -> ExperienceBook:
    """Load ``experience.yaml`` into a typed document."""
    path = _profile_file_path(name_or_dir)
    raw = _load_yaml_dict(path)
    if raw is None:
        return ExperienceBook(profile=_profile_name(name_or_dir))
    book = ExperienceBook.from_dict(raw)
    if not book.profile:
        book.profile = path.parent.name
    return book


def load_experience_book_raw(name_or_dir: str | Path) -> dict | None:
    """Load ``experience.yaml`` as a raw mapping."""
    return _load_yaml_dict(_profile_file_path(name_or_dir))


def add_experience_case(
    book: ExperienceBook,
    organization: str,
    *,
    case_id: str = "",
    role: str = "",
    location: str = "",
    status: str = "active",
    time_range: str = "",
    summary: str = "",
    project_refs: object = None,
    source_refs: object = None,
    visibility: str = "private",
    notes: str = "",
) -> ExperienceCase:
    """Add one experience case to an in-memory book."""
    clean_org = _clean_text(organization)
    if not clean_org:
        raise ValueError("Experience organization cannot be blank.")
    label = " ".join(part for part in (clean_org, _clean_text(role)) if part)
    clean_id = _clean_text(case_id) or _next_experience_id(
        book.experience_cases,
        label,
    )
    if any(case.id == clean_id for case in book.experience_cases):
        raise ValueError(f"Duplicate experience case id: {clean_id}")
    case = ExperienceCase(
        id=clean_id,
        organization=clean_org,
        role=_clean_text(role),
        location=_clean_text(location),
        status=_clean_choice(status, EXPERIENCE_STATUSES, "active"),
        time_range=_clean_text(time_range),
        summary=_clean_text(summary),
        project_refs=_clean_list(project_refs),
        source_refs=_clean_list(source_refs),
        visibility=_clean_choice(visibility, EXPERIENCE_VISIBILITIES, "private"),
        notes=_clean_text(notes),
    )
    book.experience_cases.append(case)
    return case


def update_experience_case(
    book: ExperienceBook,
    case_id: str,
    **fields: object,
) -> ExperienceCase:
    """Update one experience case in an in-memory book."""
    case = _find_case(book, case_id)
    if "organization" in fields:
        organization = _clean_text(fields["organization"])
        if not organization:
            raise ValueError("Experience organization cannot be blank.")
        case.organization = organization
    if "status" in fields:
        case.status = _clean_choice(fields["status"], EXPERIENCE_STATUSES, case.status)
    if "visibility" in fields:
        case.visibility = _clean_choice(
            fields["visibility"],
            EXPERIENCE_VISIBILITIES,
            case.visibility,
        )
    for key in ("role", "location", "time_range", "summary", "notes"):
        if key in fields:
            setattr(case, key, _clean_text(fields[key]))
    for key in ("project_refs", "source_refs"):
        if key in fields:
            setattr(case, key, _clean_list(fields[key]))
    return case


def archive_experience_case(book: ExperienceBook, case_id: str) -> ExperienceCase:
    """Mark one experience case archived."""
    return update_experience_case(book, case_id, status="archived")


def save_experience_book(name_or_dir: str | Path, data: ExperienceBook | dict) -> None:
    """Write ``experience.yaml`` with today's date updated."""
    path = _profile_file_path(name_or_dir)
    book = data if isinstance(data, ExperienceBook) else ExperienceBook.from_dict(data)
    book.profile = book.profile or path.parent.name
    book.updated = date.today().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# Internal experience cases for {book.profile or path.parent.name}\n"
        "# Resume output remains in resume-source.yaml.\n\n"
    )
    body = yaml.dump(
        book.to_dict(),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    atomic_write_text(path, header + body)
    git_backup.record_change(
        [path],
        action=f"update {path.parent.name}/experience.yaml",
    )


__all__ = [
    "EXPERIENCE_FILENAME",
    "EXPERIENCE_STATUSES",
    "EXPERIENCE_VISIBILITIES",
    "ExperienceBook",
    "ExperienceCase",
    "add_experience_case",
    "archive_experience_case",
    "load_experience_book",
    "load_experience_book_raw",
    "save_experience_book",
    "update_experience_case",
]
