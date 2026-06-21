"""Data classes for nblane domain objects."""

from __future__ import annotations

from dataclasses import dataclass, field

EVIDENCE_TYPES = frozenset(
    {"project", "paper", "course", "practice", "learning"}
)
EVIDENCE_STRENGTHS = ("weak", "medium", "strong", "high_trust")
EVIDENCE_CONFIDENCES = ("low", "medium", "high")
EVIDENCE_REVIEW_STATUSES = ("needs_review", "reviewed")
EVIDENCE_PUBLIC_READINESS = (
    "private",
    "draftable",
    "public_ready",
    "published",
)
# v2 provenance: where an evidence row came from (distinct from `type`,
# which is the proof category). See evidence architecture v2 plan.
EVIDENCE_ORIGINS = (
    "kanban_task",
    "resume_parse",
    "output",
    "manual_daily",
    "paper",
    "research_source",
)
# Language of the normalized fields (title/summary/formatted_content) and,
# separately, the detected language of original_content.
EVIDENCE_LANGUAGES = ("en", "zh", "mixed", "unknown")
# Pool schema version. v2 introduces provenance + full-content fields.
EVIDENCE_POOL_SCHEMA_VERSION = "2.0"
CLAIM_TYPES = (
    "achievement",
    "skill",
    "impact",
    "role",
    "learning",
    "project",
)
CLAIM_STATUSES = ("draft", "accepted", "deprecated", "dismissed")
CLAIM_REFRESH_STATUSES = ("current", "needs_refresh")


@dataclass
class Evidence:
    """Structured proof attached to a skill-tree node."""

    type: str
    title: str
    date: str = ""
    url: str = ""
    summary: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> Evidence:
        """Build from a YAML-loaded dict."""
        if not isinstance(d, dict):
            return cls(type="practice", title="")
        return cls(
            type=str(d.get("type", "practice") or "practice"),
            title=str(d.get("title", "") or ""),
            date=str(d.get("date", "") or ""),
            url=str(d.get("url", "") or ""),
            summary=str(d.get("summary", "") or ""),
        )

    def to_dict(self) -> dict:
        """Serialize for YAML output."""
        out: dict = {
            "type": self.type,
            "title": self.title,
        }
        if self.date:
            out["date"] = self.date
        if self.url:
            out["url"] = self.url
        if self.summary:
            out["summary"] = self.summary
        return out


@dataclass
class EvidenceRecord:
    """One catalogued evidence row in profiles/.../evidence-pool.yaml."""

    id: str
    type: str
    title: str
    date: str = ""
    url: str = ""
    summary: str = ""
    strength: str = ""
    confidence: str = ""
    review_status: str = ""
    public_readiness: str = ""
    source_refs: list[str] = field(default_factory=list)
    project_refs: list[str] = field(default_factory=list)
    experience_refs: list[str] = field(default_factory=list)
    kanban_refs: list[str] = field(default_factory=list)
    source_excerpt: str = ""
    # v2 provenance + full-content fields.
    origin: str = ""
    origin_ref: str = ""
    origin_detail: str = ""
    original_content: str = ""
    formatted_content: str = ""
    language: str = ""
    original_language: str = ""
    original_content_hash: str = ""
    deprecated: bool = False
    replaced_by: str = ""

    def to_evidence(self) -> Evidence:
        """Map pool fields to inline Evidence (for gap/context)."""
        return Evidence(
            type=self.type,
            title=self.title,
            date=self.date,
            url=self.url,
            summary=self.summary,
        )

    @classmethod
    def from_dict(cls, d: dict) -> EvidenceRecord:
        """Build from a YAML-loaded dict."""
        if not isinstance(d, dict):
            return cls(id="", type="practice", title="")
        return cls(
            id=str(d.get("id", "") or ""),
            type=str(d.get("type", "practice") or "practice"),
            title=str(d.get("title", "") or ""),
            date=str(d.get("date", "") or ""),
            url=str(d.get("url", "") or ""),
            summary=str(d.get("summary", "") or ""),
            strength=str(d.get("strength", "") or ""),
            confidence=str(d.get("confidence", "") or ""),
            review_status=str(d.get("review_status", "") or ""),
            public_readiness=str(d.get("public_readiness", "") or ""),
            source_refs=[
                str(item).strip()
                for item in (d.get("source_refs") or [])
                if item is not None and str(item).strip()
            ]
            if isinstance(d.get("source_refs"), list)
            else [],
            project_refs=[
                str(item).strip()
                for item in (d.get("project_refs") or [])
                if item is not None and str(item).strip()
            ]
            if isinstance(d.get("project_refs"), list)
            else [],
            experience_refs=[
                str(item).strip()
                for item in (d.get("experience_refs") or [])
                if item is not None and str(item).strip()
            ]
            if isinstance(d.get("experience_refs"), list)
            else [],
            kanban_refs=[
                str(item).strip()
                for item in (d.get("kanban_refs") or [])
                if item is not None and str(item).strip()
            ]
            if isinstance(d.get("kanban_refs"), list)
            else [],
            source_excerpt=str(d.get("source_excerpt", "") or ""),
            origin=str(d.get("origin", "") or ""),
            origin_ref=str(d.get("origin_ref", "") or ""),
            origin_detail=str(d.get("origin_detail", "") or ""),
            original_content=str(d.get("original_content", "") or ""),
            formatted_content=str(d.get("formatted_content", "") or ""),
            language=str(d.get("language", "") or ""),
            original_language=str(d.get("original_language", "") or ""),
            original_content_hash=str(d.get("original_content_hash", "") or ""),
            deprecated=bool(d.get("deprecated", False)),
            replaced_by=str(d.get("replaced_by", "") or ""),
        )

    def to_dict(self) -> dict:
        """Serialize for YAML output."""
        out: dict = {
            "id": self.id,
            "type": self.type,
            "title": self.title,
        }
        if self.date:
            out["date"] = self.date
        if self.url:
            out["url"] = self.url
        if self.summary:
            out["summary"] = self.summary
        if self.strength:
            out["strength"] = self.strength
        if self.confidence:
            out["confidence"] = self.confidence
        if self.review_status:
            out["review_status"] = self.review_status
        if self.public_readiness:
            out["public_readiness"] = self.public_readiness
        if self.source_refs:
            out["source_refs"] = list(self.source_refs)
        if self.project_refs:
            out["project_refs"] = list(self.project_refs)
        if self.experience_refs:
            out["experience_refs"] = list(self.experience_refs)
        if self.kanban_refs:
            out["kanban_refs"] = list(self.kanban_refs)
        if self.source_excerpt:
            out["source_excerpt"] = self.source_excerpt
        if self.origin:
            out["origin"] = self.origin
        if self.origin_ref:
            out["origin_ref"] = self.origin_ref
        if self.origin_detail:
            out["origin_detail"] = self.origin_detail
        if self.original_content:
            out["original_content"] = self.original_content
        if self.formatted_content:
            out["formatted_content"] = self.formatted_content
        if self.language:
            out["language"] = self.language
        if self.original_language:
            out["original_language"] = self.original_language
        if self.original_content_hash:
            out["original_content_hash"] = self.original_content_hash
        if self.deprecated:
            out["deprecated"] = True
        if self.replaced_by:
            out["replaced_by"] = self.replaced_by
        return out


@dataclass
class EvidencePool:
    """Profile-level evidence library (one file per profile)."""

    profile: str = ""
    updated: str = ""
    schema_version: str = ""
    evidence_entries: list[EvidenceRecord] = field(default_factory=list)
    claims: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> EvidencePool:
        """Build from a YAML-loaded dict."""
        raw = d.get("evidence_entries") or []
        entries: list[EvidenceRecord] = []
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    entries.append(EvidenceRecord.from_dict(item))
        return cls(
            profile=str(d.get("profile", "") or ""),
            updated=str(d.get("updated", "") or ""),
            schema_version=str(d.get("schema_version", "") or ""),
            evidence_entries=entries,
            claims=[
                dict(item)
                for item in (d.get("claims") or [])
                if isinstance(item, dict)
            ],
        )

    def to_dict(self) -> dict:
        """Serialize for YAML output."""
        out: dict = {
            "profile": self.profile,
            "updated": self.updated,
            "evidence_entries": [
                e.to_dict() for e in self.evidence_entries
            ],
        }
        if self.schema_version:
            out["schema_version"] = self.schema_version
        if self.claims:
            out["claims"] = [dict(item) for item in self.claims]
        return out

    def by_id(self) -> dict[str, EvidenceRecord]:
        """Stable id -> record (last wins on duplicate ids)."""
        out: dict[str, EvidenceRecord] = {}
        for e in self.evidence_entries:
            if e.id:
                out[e.id] = e
        return out


@dataclass
class SkillNode:
    """One node in a person's skill-tree overlay."""

    id: str
    status: str = "locked"
    note: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> SkillNode:
        """Build from a YAML-loaded dict."""
        raw_ev = d.get("evidence") or []
        evidence_list: list[Evidence] = []
        if isinstance(raw_ev, list):
            for item in raw_ev:
                if isinstance(item, dict):
                    evidence_list.append(Evidence.from_dict(item))
        raw_refs = d.get("evidence_refs") or []
        refs: list[str] = []
        seen_r: set[str] = set()
        if isinstance(raw_refs, list):
            for x in raw_refs:
                if isinstance(x, str) and x.strip():
                    key = x.strip()
                    if key not in seen_r:
                        seen_r.add(key)
                        refs.append(key)
        return cls(
            id=d.get("id", ""),
            status=d.get("status", "locked"),
            note=d.get("note", ""),
            evidence=evidence_list,
            evidence_refs=refs,
        )

    def to_dict(self) -> dict:
        """Serialize for YAML output (omit empty optional fields)."""
        out: dict = {"id": self.id, "status": self.status}
        if self.note:
            out["note"] = self.note
        if self.evidence:
            out["evidence"] = [e.to_dict() for e in self.evidence]
        if self.evidence_refs:
            out["evidence_refs"] = list(self.evidence_refs)
        return out


@dataclass
class SkillTree:
    """A person's skill-tree snapshot."""

    profile: str = ""
    schema: str = ""
    updated: str = ""
    nodes: list[SkillNode] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> SkillTree:
        """Build from a YAML-loaded dict."""
        raw_nodes = d.get("nodes") or []
        return cls(
            profile=d.get("profile", ""),
            schema=d.get("schema", ""),
            updated=d.get("updated", ""),
            nodes=[SkillNode.from_dict(n) for n in raw_nodes],
        )

    def to_dict(self) -> dict:
        """Serialize for YAML output."""
        return {
            "profile": self.profile,
            "schema": self.schema,
            "updated": self.updated,
            "nodes": [n.to_dict() for n in self.nodes],
        }

    def status_by_id(self) -> dict[str, str]:
        """Map node id -> status string."""
        return {n.id: n.status for n in self.nodes if n.id}


@dataclass
class SchemaNode:
    """One node in a domain skill-tree schema."""

    id: str
    label: str = ""
    level: int = 0
    category: str = ""
    requires: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> SchemaNode:
        """Build from a YAML-loaded dict."""
        return cls(
            id=d.get("id", ""),
            label=d.get("label", ""),
            level=d.get("level", 0),
            category=d.get("category", ""),
            requires=d.get("requires") or [],
        )


@dataclass
class Schema:
    """A full domain skill-tree schema."""

    schema_version: str = ""
    domain: str = ""
    description: str = ""
    nodes: list[SchemaNode] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> Schema:
        """Build from a YAML-loaded dict."""
        raw_nodes = d.get("nodes") or []
        return cls(
            schema_version=d.get("schema_version", ""),
            domain=d.get("domain", ""),
            description=d.get("description", ""),
            nodes=[SchemaNode.from_dict(n) for n in raw_nodes],
        )

    def node_index(self) -> dict[str, SchemaNode]:
        """Build id -> SchemaNode lookup."""
        return {n.id: n for n in self.nodes if n.id}


@dataclass
class KanbanSubtask:
    """Checkbox sub-item under a kanban task."""

    title: str
    done: bool = False


@dataclass
class KanbanTask:
    """One task entry in a kanban board."""

    title: str
    done: bool = False
    id: str = ""
    context: str = ""
    why: str = ""
    blocked_by: str = ""
    outcome: str = ""
    started_on: str | None = None
    completed_on: str | None = None
    crystallized: bool = False
    project_id: str = ""
    milestone_id: str = ""
    tags: str = ""
    subtasks: list[KanbanSubtask] = field(default_factory=list)
    details: list[str] = field(default_factory=list)


@dataclass
class GapResult:
    """Structured output of a gap analysis run."""

    task: str = ""
    top_matches: list[dict] = field(default_factory=list)
    closure: list[dict] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    strong: list[str] = field(default_factory=list)
    can_solve: bool = False
    next_steps: list[str] = field(default_factory=list)
    error: str | None = None
    error_key: str | None = None
    roots_from_rule: list[str] = field(default_factory=list)
    roots_from_llm: list[str] = field(default_factory=list)
    learned_merged: bool = False
    source_kind: str = ""
    source_id: str = ""
    source_label: str = ""
    context_refs: dict[str, list[str]] = field(default_factory=dict)
    goal_context_used: bool = False
