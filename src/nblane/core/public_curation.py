"""Curation helpers for turning atomic evidence into public drafts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from nblane.core import git_backup
from nblane.core.profile_io import profile_dir
from nblane.core.public_site import (
    BLOG_DIRNAME,
    OUTPUTS_FILENAME,
    PROJECTS_FILENAME,
    PublicSiteError,
)

EVIDENCE_POOL_FILENAME = "evidence-pool.yaml"
SKILL_TREE_FILENAME = "skill-tree.yaml"


@dataclass
class EvidenceContext:
    """One evidence record plus its public curation context."""

    id: str
    type: str
    title: str
    summary: str = ""
    date: str = ""
    skill_refs: list[str] = field(default_factory=list)
    used_by_projects: list[str] = field(default_factory=list)
    used_by_outputs: list[str] = field(default_factory=list)
    used_by_posts: list[str] = field(default_factory=list)

    @property
    def is_used(self) -> bool:
        """Return True when any public-layer object references this evidence."""
        return bool(
            self.used_by_projects
            or self.used_by_outputs
            or self.used_by_posts
        )

    def to_dict(self) -> dict:
        """Serialize for CLI and Streamlit display."""
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "summary": self.summary,
            "date": self.date,
            "skill_refs": list(self.skill_refs),
            "used_by_projects": list(self.used_by_projects),
            "used_by_outputs": list(self.used_by_outputs),
            "used_by_posts": list(self.used_by_posts),
        }


@dataclass
class SuggestedGroup:
    """A deterministic project/output grouping suggestion."""

    id: str
    title: str
    reason: str
    evidence_refs: list[str]
    skill_refs: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize for CLI output."""
        return {
            "id": self.id,
            "title": self.title,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
            "skill_refs": list(self.skill_refs),
            "tags": list(self.tags),
        }


@dataclass
class GroupProjectResult:
    """Result of writing a manually confirmed project draft."""

    path: Path
    project: dict
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize for CLI output."""
        return {
            "path": str(self.path),
            "project": self.project,
            "warnings": list(self.warnings),
        }


@dataclass
class HydrateDraftResult:
    """Result of previewing or writing obvious one-to-one output drafts."""

    path: Path
    outputs: list[dict]
    warnings: list[str] = field(default_factory=list)
    written: bool = False

    def to_dict(self) -> dict:
        """Serialize for CLI output."""
        return {
            "path": str(self.path),
            "written": self.written,
            "outputs": list(self.outputs),
            "warnings": list(self.warnings),
        }


def _read_yaml_mapping(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(
            data,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _profile_path(name: str) -> Path:
    root = profile_dir(name)
    if not root.exists():
        raise FileNotFoundError(f"Profile '{name}' does not exist: {root}")
    return root


def _as_string_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text:
            out.append(text)
    return out


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _slug_id(value: str, *, fallback: str = "draft") -> str:
    clean = value.strip().lower()
    clean = re.sub(r"[^a-z0-9\u4e00-\u9fff._~-]+", "-", clean)
    clean = clean.strip(".-")
    return clean or fallback


def evidence_index(name: str) -> dict[str, dict]:
    """Return evidence id -> raw record from evidence-pool.yaml."""
    raw = _read_yaml_mapping(_profile_path(name) / EVIDENCE_POOL_FILENAME)
    entries = raw.get("evidence_entries") or []
    out: dict[str, dict] = {}
    if not isinstance(entries, list):
        return out
    for item in entries:
        if not isinstance(item, dict):
            continue
        eid = str(item.get("id", "") or "").strip()
        if eid:
            out[eid] = item
    return out


def _evidence_skill_refs(name: str) -> dict[str, list[str]]:
    raw = _read_yaml_mapping(_profile_path(name) / SKILL_TREE_FILENAME)
    nodes = raw.get("nodes") or []
    reverse: dict[str, list[str]] = {}
    if not isinstance(nodes, list):
        return reverse
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id", "") or "").strip()
        if not node_id:
            continue
        for ref in _as_string_list(node.get("evidence_refs")):
            reverse.setdefault(ref, [])
            if node_id not in reverse[ref]:
                reverse[ref].append(node_id)
    return reverse


def _load_projects(name: str) -> list[dict]:
    raw = _read_yaml_mapping(_profile_path(name) / PROJECTS_FILENAME)
    projects = raw.get("projects") or []
    return [p for p in projects if isinstance(p, dict)]


def _load_outputs(name: str) -> list[dict]:
    raw = _read_yaml_mapping(_profile_path(name) / OUTPUTS_FILENAME)
    outputs = raw.get("outputs") or []
    return [o for o in outputs if isinstance(o, dict)]


def _blog_evidence_usage(name: str) -> dict[str, list[str]]:
    root = _profile_path(name)
    blog_dir = root / BLOG_DIRNAME
    usage: dict[str, list[str]] = {}
    if not blog_dir.exists():
        return usage
    for path in sorted(blog_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta = _parse_front_matter(text)
        for ref in _as_string_list(meta.get("related_evidence")):
            usage.setdefault(ref, []).append(path.stem)
    return usage


def _parse_front_matter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    raw = yaml.safe_load(text[4:end]) or {}
    return raw if isinstance(raw, dict) else {}


def _usage_index(name: str) -> dict[str, dict[str, list[str]]]:
    usage: dict[str, dict[str, list[str]]] = {}
    for project in _load_projects(name):
        pid = str(project.get("id", "") or "").strip()
        if not pid:
            continue
        for ref in _as_string_list(project.get("evidence_refs")):
            usage.setdefault(ref, {}).setdefault("projects", []).append(pid)
    for output in _load_outputs(name):
        oid = str(output.get("id", "") or "").strip()
        if not oid:
            continue
        for ref in _as_string_list(output.get("evidence_refs")):
            usage.setdefault(ref, {}).setdefault("outputs", []).append(oid)
    for ref, posts in _blog_evidence_usage(name).items():
        usage.setdefault(ref, {}).setdefault("posts", []).extend(posts)
    return usage


def evidence_contexts(name: str) -> list[EvidenceContext]:
    """Return evidence records with skill refs and public usage markers."""
    skills = _evidence_skill_refs(name)
    usage = _usage_index(name)
    contexts: list[EvidenceContext] = []
    for eid, record in evidence_index(name).items():
        if bool(record.get("deprecated", False)):
            continue
        used = usage.get(eid, {})
        contexts.append(
            EvidenceContext(
                id=eid,
                type=str(record.get("type", "") or ""),
                title=str(record.get("title", "") or ""),
                summary=str(record.get("summary", "") or ""),
                date=str(record.get("date", "") or ""),
                skill_refs=list(skills.get(eid, [])),
                used_by_projects=list(used.get("projects", [])),
                used_by_outputs=list(used.get("outputs", [])),
                used_by_posts=list(used.get("posts", [])),
            )
        )
    return sorted(contexts, key=lambda c: (c.date, c.id), reverse=True)


def _record_text(record: dict) -> str:
    return " ".join(
        str(record.get(key, "") or "")
        for key in ("id", "type", "title", "summary", "date")
    ).lower()


def _keyword_hits(text: str, keywords: tuple[str, ...]) -> int:
    hits = 0
    for keyword in keywords:
        key = keyword.lower()
        if re.fullmatch(r"[a-z0-9.+-]{1,3}", key):
            pattern = rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])"
            if re.search(pattern, text):
                hits += 1
            continue
        if key in text:
            hits += 1
    return hits


_GROUP_SPECS = (
    {
        "id": "piper-home-robot",
        "title": "Piper / 家庭整理机器人项目",
        "tags": ["robotics", "imitation-learning", "home-robot"],
        "seed_ids": {
            "ev_piper_repro",
            "ev_piper_demo_fix",
            "ev_shoe_benchmark_new",
        },
        "keywords": (
            "piper",
            "pi0",
            "pi0.5",
            "openpi",
            "desktop",
            "investor demo",
            "object收纳",
        ),
        "reason": (
            "Piper arm, demo repair, and home manipulation benchmark traces "
            "can become one reviewed home-robot project narrative."
        ),
    },
    {
        "id": "pose-shoe-output-line",
        "title": "6D 位姿与鞋子摆放成果线",
        "tags": ["6d-pose", "robot-manipulation", "outputs"],
        "seed_ids": {
            "ev_pose_paper",
            "ev_shoe_patent",
            "ev_shoe_benchmark",
        },
        "keywords": (
            "pose",
            "6d",
            "iup",
            "patent",
            "专利",
            "位姿",
            "鞋子摆放",
            "feature matching",
        ),
        "reason": (
            "Pose-estimation paper, patent/IP trace, and benchmark notes "
            "share the same 6D pose and shoe-placement evidence line."
        ),
    },
    {
        "id": "perception-model-optimization",
        "title": "自动驾驶 / 感知模型优化项目",
        "tags": ["perception", "optimization", "autonomous-driving"],
        "seed_ids": {
            "ev_ap_boost",
            "ev_training_speedup",
            "ev_gaussian_3d",
        },
        "keywords": (
            "ap",
            "training",
            "speedup",
            "gaussian",
            "monocular",
            "pretraining",
            "perception model",
            "detection",
        ),
        "reason": (
            "Detection AP, training acceleration, and 3D pretraining traces "
            "can be reviewed as one perception-model optimization project."
        ),
    },
    {
        "id": "robotics-vla-architecture",
        "title": "机器人感知 / VLA 系统架构项目",
        "tags": ["ros", "vla", "system-architecture"],
        "seed_ids": {
            "ev_ros_arch",
            "ev_spatial_forcing_vggt",
        },
        "keywords": (
            "ros",
            "architecture",
            "vla",
            "vggt",
            "spatial",
            "sensor fusion",
            "perception system",
        ),
        "reason": (
            "Robot perception architecture and VLA spatial supervision traces "
            "can be curated into one reviewed system-architecture story."
        ),
    },
)


def _skill_union(
    refs: list[str],
    skill_by_evidence: dict[str, list[str]],
) -> list[str]:
    skills: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        for skill in skill_by_evidence.get(ref, []):
            if skill not in seen:
                seen.add(skill)
                skills.append(skill)
    return skills


def suggest_groups(name: str) -> list[SuggestedGroup]:
    """Suggest deterministic evidence groupings without writing files."""
    records = evidence_index(name)
    skills = _evidence_skill_refs(name)
    suggestions: list[SuggestedGroup] = []
    seen_signatures: set[tuple[str, ...]] = set()

    for spec in _GROUP_SPECS:
        seed_ids = set(spec["seed_ids"])
        keywords = tuple(str(k).lower() for k in spec["keywords"])
        refs: list[str] = []
        for eid, record in records.items():
            if bool(record.get("deprecated", False)):
                continue
            text = _record_text(record)
            if eid in seed_ids or _keyword_hits(text, keywords) >= 2:
                refs.append(eid)
        refs = _dedupe(refs)
        if len(refs) < 2:
            continue
        signature = tuple(sorted(refs))
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        suggestions.append(
            SuggestedGroup(
                id=str(spec["id"]),
                title=str(spec["title"]),
                reason=str(spec["reason"]),
                evidence_refs=refs,
                skill_refs=_skill_union(refs, skills),
                tags=list(spec["tags"]),
            )
        )

    suggestions.extend(
        _shared_skill_suggestions(records, skills, seen_signatures)
    )
    return suggestions


def _shared_skill_suggestions(
    records: dict[str, dict],
    skills: dict[str, list[str]],
    seen_signatures: set[tuple[str, ...]],
) -> list[SuggestedGroup]:
    by_skill: dict[str, list[str]] = {}
    for eid, skill_refs in skills.items():
        if eid not in records:
            continue
        if bool(records[eid].get("deprecated", False)):
            continue
        for skill in skill_refs:
            by_skill.setdefault(skill, []).append(eid)

    suggestions: list[SuggestedGroup] = []
    for skill, refs in sorted(by_skill.items()):
        refs = _dedupe(refs)
        if len(refs) < 2:
            continue
        signature = tuple(sorted(refs))
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        suggestions.append(
            SuggestedGroup(
                id=_slug_id(f"{skill}-evidence"),
                title=f"{skill} evidence group",
                reason=(
                    "Multiple evidence records share the same skill node; "
                    "review whether they form a coherent public project."
                ),
                evidence_refs=refs,
                skill_refs=[skill],
                tags=[skill],
            )
        )
        if len(suggestions) >= 5:
            break
    return suggestions


def group_project(
    name: str,
    *,
    project_id: str,
    title: str,
    evidence_ids: list[str],
    summary: str = "",
    tags: list[str] | None = None,
) -> GroupProjectResult:
    """Write a reviewed evidence grouping into projects.yaml as a draft."""
    clean_id = project_id.strip()
    clean_title = title.strip()
    if not clean_id:
        raise PublicSiteError("project id is required")
    if not clean_title:
        raise PublicSiteError("project title is required")

    root = _profile_path(name)
    path = root / PROJECTS_FILENAME
    raw = _read_yaml_mapping(path)
    projects = raw.get("projects") or []
    if not isinstance(projects, list):
        raise PublicSiteError(f"{PROJECTS_FILENAME}: projects must be a list")

    for item in projects:
        if isinstance(item, dict) and str(item.get("id", "") or "") == clean_id:
            raise PublicSiteError(f"project id already exists: {clean_id}")

    refs = _dedupe(evidence_ids)
    if not refs:
        raise PublicSiteError("at least one evidence id is required")

    known = evidence_index(name)
    missing = [ref for ref in refs if ref not in known]
    if missing:
        raise PublicSiteError(
            "unknown evidence id(s): " + ", ".join(sorted(missing))
        )

    warnings: list[str] = []
    existing_project_usage: dict[str, list[str]] = {}
    for project in projects:
        if not isinstance(project, dict):
            continue
        pid = str(project.get("id", "") or "")
        for ref in _as_string_list(project.get("evidence_refs")):
            existing_project_usage.setdefault(ref, []).append(pid)

    kept_refs: list[str] = []
    for ref in refs:
        used_by = existing_project_usage.get(ref, [])
        if used_by:
            warnings.append(
                f"evidence '{ref}' is already used by project(s): "
                + ", ".join(used_by)
            )
            continue
        kept_refs.append(ref)
    if not kept_refs:
        raise PublicSiteError(
            "all requested evidence refs are already used by projects"
        )

    skill_refs = _skill_union(kept_refs, _evidence_skill_refs(name))
    project_summary = summary.strip()
    if not project_summary:
        project_summary = (
            "Draft project aggregated from reviewed evidence. "
            "Write a public summary before publishing."
        )
    project = {
        "id": clean_id,
        "title": clean_title,
        "status": "draft",
        "summary": project_summary,
        "tags": tags or [],
        "evidence_refs": kept_refs,
        "skill_refs": skill_refs,
        "links": {},
        "featured": False,
        "public_angle": "",
        "review_notes": (
            "Created by nblane public group from evidence_refs. "
            "Confirm wording, privacy, links, and metrics before publishing."
        ),
    }
    projects.append(project)
    _write_yaml(path, {"projects": projects})
    git_backup.record_change(
        [path],
        action=f"group {name} public project {clean_id}",
    )
    return GroupProjectResult(path=path, project=project, warnings=warnings)


def hydrate_public_drafts(
    name: str,
    *,
    write_drafts: bool = False,
) -> HydrateDraftResult:
    """Preview or write obvious paper/patent output drafts.

    This function intentionally does not merge multiple evidence records into
    project drafts. Multi-evidence grouping remains a human confirmation step.
    """
    root = _profile_path(name)
    path = root / OUTPUTS_FILENAME
    raw = _read_yaml_mapping(path)
    outputs = raw.get("outputs") or []
    if not isinstance(outputs, list):
        raise PublicSiteError(f"{OUTPUTS_FILENAME}: outputs must be a list")

    existing_ids = {
        str(item.get("id", "") or "")
        for item in outputs
        if isinstance(item, dict)
    }
    used_refs: set[str] = set()
    for output in outputs:
        if not isinstance(output, dict):
            continue
        used_refs.update(_as_string_list(output.get("evidence_refs")))

    drafts: list[dict] = []
    warnings: list[str] = []
    for eid, record in evidence_index(name).items():
        if bool(record.get("deprecated", False)):
            continue
        output_type = _output_type_for_evidence(record)
        if output_type is None:
            continue
        if eid in used_refs:
            warnings.append(f"evidence '{eid}' is already used by an output")
            continue
        oid = _slug_id(f"out-{eid.removeprefix('ev_')}", fallback=f"out-{eid}")
        if oid in existing_ids:
            warnings.append(f"output id already exists: {oid}")
            continue
        draft = {
            "id": oid,
            "type": output_type,
            "title": str(record.get("title", "") or eid),
            "status": "draft",
            "year": str(record.get("date", "") or ""),
            "summary": str(record.get("summary", "") or ""),
            "evidence_refs": [eid],
            "links": _links_from_evidence(record),
            "featured": False,
            "review_notes": (
                "Auto-hydrated as a one-to-one draft output. "
                "Confirm publication details before publishing."
            ),
        }
        drafts.append(draft)
        existing_ids.add(oid)

    if write_drafts and drafts:
        outputs.extend(drafts)
        _write_yaml(path, {"outputs": outputs})
        git_backup.record_change(
            [path],
            action=f"hydrate {name} public output drafts",
        )
    return HydrateDraftResult(
        path=path,
        outputs=drafts,
        warnings=warnings,
        written=write_drafts and bool(drafts),
    )


def _output_type_for_evidence(record: dict) -> str | None:
    text = _record_text(record)
    raw_type = str(record.get("type", "") or "").strip().lower()
    if "patent" in text or "专利" in text:
        return "patent"
    if raw_type == "paper" or "paper" in text or "论文" in text:
        return "paper"
    return None


def _links_from_evidence(record: dict) -> dict:
    url = str(record.get("url", "") or "").strip()
    if not url:
        return {}
    return {"source": url}
