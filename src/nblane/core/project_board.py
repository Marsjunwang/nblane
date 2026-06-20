"""Internal project-case facts for nblane profiles."""

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

PROJECT_BOARD_FILENAME = "project-board.yaml"
PROJECT_STATUSES = ("active", "paused", "completed", "archived")
PROJECT_KINDS = ("internal", "research", "work", "side_project", "learning")
PROJECT_VISIBILITIES = ("private", "public")
MILESTONE_STATUSES = ("planned", "active", "completed", "archived")


def profile_dir(name: str) -> Path:
    """Return path to ``profiles/{name}``."""
    return PROFILES_DIR / name


def _profile_file_path(name_or_dir: str | Path) -> Path:
    """Resolve a profile-scoped project-board path."""
    if isinstance(name_or_dir, Path):
        if name_or_dir.suffix in (".yaml", ".yml"):
            return name_or_dir
        return name_or_dir / PROJECT_BOARD_FILENAME
    raw = name_or_dir.strip()
    path = Path(raw)
    if (
        path.suffix in (".yaml", ".yml")
        or "/" in raw
        or raw.startswith(".")
        or path.exists()
    ):
        return path if path.suffix else path / PROJECT_BOARD_FILENAME
    return profile_dir(raw) / PROJECT_BOARD_FILENAME


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


def _slug_id(value: str, *, fallback: str = "project") -> str:
    clean = value.strip().lower()
    clean = re.sub(r"[^a-z0-9\u4e00-\u9fff._~-]+", "-", clean)
    clean = clean.strip(".-")
    return clean or fallback


def _next_project_id(cases: list["ProjectCase"], title: str) -> str:
    base = f"project:{_slug_id(title)}"
    existing = {case.id for case in cases if case.id}
    if base not in existing:
        return base
    index = 2
    while f"{base}-{index}" in existing:
        index += 1
    return f"{base}-{index}"


def _find_case(board: "ProjectBoard", case_id: str) -> "ProjectCase":
    clean_id = _clean_text(case_id)
    for case in board.project_cases:
        if case.id == clean_id:
            return case
    raise KeyError(f"Unknown project case: {clean_id}")


@dataclass
class ProjectMilestone:
    """One milestone inside an internal project case."""

    id: str
    title: str
    status: str = "planned"
    target: str = ""
    date: str = ""
    summary: str = ""
    task_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    output_refs: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectMilestone":
        """Build a milestone from YAML."""
        if not isinstance(data, dict):
            return cls(id="", title="")
        return cls(
            id=_clean_text(data.get("id")),
            title=_clean_text(data.get("title")),
            status=_clean_choice(
                data.get("status"),
                MILESTONE_STATUSES,
                "planned",
            ),
            target=_clean_text(data.get("target")),
            date=_clean_text(data.get("date")),
            summary=_clean_text(data.get("summary")),
            task_refs=_clean_list(data.get("task_refs")),
            evidence_refs=_clean_list(data.get("evidence_refs")),
            source_refs=_clean_list(data.get("source_refs")),
            output_refs=_clean_list(data.get("output_refs")),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize for YAML output."""
        out: dict[str, object] = {
            "id": self.id,
            "title": self.title,
            "status": self.status,
        }
        for key in ("target", "date", "summary"):
            value = getattr(self, key)
            if value:
                out[key] = value
        for key in (
            "task_refs",
            "evidence_refs",
            "source_refs",
            "output_refs",
        ):
            values = _clean_list(getattr(self, key))
            if values:
                out[key] = list(values)
        return out


@dataclass
class ProjectCase:
    """One internal project case used to group work and evidence."""

    id: str
    title: str
    status: str = "active"
    kind: str = "internal"
    time_range: str = ""
    summary: str = ""
    goal_refs: list[str] = field(default_factory=list)
    task_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    experience_refs: list[str] = field(default_factory=list)
    output_refs: list[str] = field(default_factory=list)
    milestones: list[ProjectMilestone] = field(default_factory=list)
    visibility: str = "private"
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectCase":
        """Build a project case from YAML."""
        if not isinstance(data, dict):
            return cls(id="", title="")
        return cls(
            id=_clean_text(data.get("id")),
            title=_clean_text(data.get("title")),
            status=_clean_choice(data.get("status"), PROJECT_STATUSES, "active"),
            kind=_clean_choice(data.get("kind"), PROJECT_KINDS, "internal"),
            time_range=_clean_text(data.get("time_range")),
            summary=_clean_text(data.get("summary")),
            goal_refs=_clean_list(data.get("goal_refs")),
            task_refs=_clean_list(data.get("task_refs")),
            evidence_refs=_clean_list(data.get("evidence_refs")),
            source_refs=_clean_list(data.get("source_refs")),
            experience_refs=_clean_list(data.get("experience_refs")),
            output_refs=_clean_list(data.get("output_refs")),
            milestones=[
                ProjectMilestone.from_dict(item)
                for item in (data.get("milestones") or [])
                if isinstance(item, dict)
            ]
            if isinstance(data.get("milestones"), list)
            else [],
            visibility=_clean_choice(
                data.get("visibility"),
                PROJECT_VISIBILITIES,
                "private",
            ),
            notes=_clean_text(data.get("notes")),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize for YAML output."""
        out: dict[str, object] = {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "kind": self.kind,
            "visibility": self.visibility,
        }
        for key in (
            "time_range",
            "summary",
            "notes",
        ):
            value = getattr(self, key)
            if value:
                out[key] = value
        for key in (
            "goal_refs",
            "task_refs",
            "evidence_refs",
            "source_refs",
            "experience_refs",
            "output_refs",
        ):
            values = _clean_list(getattr(self, key))
            if values:
                out[key] = list(values)
        if self.milestones:
            out["milestones"] = [
                milestone.to_dict()
                for milestone in self.milestones
                if milestone.id and milestone.title
            ]
        return out


@dataclass
class ProjectBoard:
    """Profile-level project-case document."""

    profile: str = ""
    updated: str = ""
    schema_version: str = "1.0"
    project_cases: list[ProjectCase] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectBoard":
        """Build a project board from YAML."""
        if not isinstance(data, dict):
            return cls()
        raw_cases = data.get("project_cases") or []
        cases: list[ProjectCase] = []
        if isinstance(raw_cases, list):
            for item in raw_cases:
                if isinstance(item, dict):
                    cases.append(ProjectCase.from_dict(item))
        return cls(
            profile=_clean_text(data.get("profile")),
            updated=_clean_text(data.get("updated")),
            schema_version=_clean_text(data.get("schema_version")) or "1.0",
            project_cases=cases,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the document for YAML output."""
        return {
            "schema_version": self.schema_version or "1.0",
            "profile": self.profile,
            "updated": self.updated,
            "project_cases": [case.to_dict() for case in self.project_cases],
        }

    def by_id(self) -> dict[str, ProjectCase]:
        """Return case id -> case."""
        return {case.id: case for case in self.project_cases if case.id}


def load_project_board(name_or_dir: str | Path) -> ProjectBoard:
    """Load ``project-board.yaml`` into a typed document."""
    path = _profile_file_path(name_or_dir)
    raw = _load_yaml_dict(path)
    if raw is None:
        return ProjectBoard(profile=_profile_name(name_or_dir))
    board = ProjectBoard.from_dict(raw)
    if not board.profile:
        board.profile = path.parent.name
    return board


def load_project_board_raw(name_or_dir: str | Path) -> dict | None:
    """Load ``project-board.yaml`` as a raw mapping."""
    return _load_yaml_dict(_profile_file_path(name_or_dir))


def add_project_case(
    board: ProjectBoard,
    title: str,
    *,
    case_id: str = "",
    status: str = "active",
    kind: str = "internal",
    time_range: str = "",
    summary: str = "",
    goal_refs: object = None,
    task_refs: object = None,
    source_refs: object = None,
    evidence_refs: object = None,
    experience_refs: object = None,
    output_refs: object = None,
    milestones: object = None,
    visibility: str = "private",
    notes: str = "",
) -> ProjectCase:
    """Add one project case to an in-memory board."""
    clean_title = _clean_text(title)
    if not clean_title:
        raise ValueError("Project case title cannot be blank.")
    clean_id = _clean_text(case_id) or _next_project_id(
        board.project_cases,
        clean_title,
    )
    if any(case.id == clean_id for case in board.project_cases):
        raise ValueError(f"Duplicate project case id: {clean_id}")
    case = ProjectCase(
        id=clean_id,
        title=clean_title,
        status=_clean_choice(status, PROJECT_STATUSES, "active"),
        kind=_clean_choice(kind, PROJECT_KINDS, "internal"),
        time_range=_clean_text(time_range),
        summary=_clean_text(summary),
        goal_refs=_clean_list(goal_refs),
        task_refs=_clean_list(task_refs),
        evidence_refs=_clean_list(evidence_refs),
        source_refs=_clean_list(source_refs),
        experience_refs=_clean_list(experience_refs),
        output_refs=_clean_list(output_refs),
        milestones=[
            item
            if isinstance(item, ProjectMilestone)
            else ProjectMilestone.from_dict(item)
            for item in (milestones or [])
            if isinstance(item, (ProjectMilestone, dict))
        ],
        visibility=_clean_choice(visibility, PROJECT_VISIBILITIES, "private"),
        notes=_clean_text(notes),
    )
    board.project_cases.append(case)
    return case


def update_project_case(
    board: ProjectBoard,
    case_id: str,
    **fields: object,
) -> ProjectCase:
    """Update one project case in an in-memory board."""
    case = _find_case(board, case_id)
    if "title" in fields:
        title = _clean_text(fields["title"])
        if not title:
            raise ValueError("Project case title cannot be blank.")
        case.title = title
    if "status" in fields:
        case.status = _clean_choice(fields["status"], PROJECT_STATUSES, case.status)
    if "kind" in fields:
        case.kind = _clean_choice(fields["kind"], PROJECT_KINDS, case.kind)
    if "visibility" in fields:
        case.visibility = _clean_choice(
            fields["visibility"],
            PROJECT_VISIBILITIES,
            case.visibility,
        )
    for key in ("time_range", "summary", "notes"):
        if key in fields:
            setattr(case, key, _clean_text(fields[key]))
    for key in (
        "goal_refs",
        "task_refs",
        "evidence_refs",
        "source_refs",
        "experience_refs",
        "output_refs",
    ):
        if key in fields:
            setattr(case, key, _clean_list(fields[key]))
    if "milestones" in fields:
        raw_milestones = fields["milestones"]
        if isinstance(raw_milestones, list):
            case.milestones = [
                item
                if isinstance(item, ProjectMilestone)
                else ProjectMilestone.from_dict(item)
                for item in raw_milestones
                if isinstance(item, (ProjectMilestone, dict))
            ]
    return case


def archive_project_case(board: ProjectBoard, case_id: str) -> ProjectCase:
    """Mark one project case archived."""
    return update_project_case(board, case_id, status="archived")


def save_project_board(name_or_dir: str | Path, data: ProjectBoard | dict) -> None:
    """Write ``project-board.yaml`` with today's date updated."""
    path = _profile_file_path(name_or_dir)
    board = data if isinstance(data, ProjectBoard) else ProjectBoard.from_dict(data)
    board.profile = board.profile or path.parent.name
    board.updated = date.today().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# Internal project cases for {board.profile or path.parent.name}\n"
        "# Public project output remains in projects.yaml.\n\n"
    )
    body = yaml.dump(
        board.to_dict(),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    atomic_write_text(path, header + body)
    git_backup.record_change(
        [path],
        action=f"update {path.parent.name}/project-board.yaml",
    )


__all__ = [
    "PROJECT_BOARD_FILENAME",
    "PROJECT_KINDS",
    "MILESTONE_STATUSES",
    "PROJECT_STATUSES",
    "PROJECT_VISIBILITIES",
    "ProjectBoard",
    "ProjectCase",
    "ProjectMilestone",
    "add_project_case",
    "archive_project_case",
    "load_project_board",
    "load_project_board_raw",
    "save_project_board",
    "update_project_case",
]
