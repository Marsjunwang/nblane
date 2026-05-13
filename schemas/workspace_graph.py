"""Schema for nblane workspace graph payloads."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


WorkspaceGraphLayer = Literal[
    "direction",
    "objective",
    "work_context",
    "activity",
    "source",
    "evidence",
    "claim",
    "capability",
    "output",
    "feedback",
    "governance",
]

WorkspaceGraphNodeType = Literal[
    "north_star",
    "goal",
    "project_case",
    "task",
    "daily_work",
    "research",
    "agent_run",
    "source",
    "evidence_candidate",
    "atomic_evidence",
    "composite_evidence",
    "claim",
    "skill",
    "gap",
    "next_action",
    "output",
    "feedback",
    "capacity",
    "health",
]

WorkspaceGraphEdgeType = Literal[
    "alignment",
    "contains",
    "generated_by",
    "source_to_candidate",
    "review",
    "derives",
    "supports",
    "drives",
    "produces",
    "feedback",
    "watches",
]


class WorkspaceGraphNode(BaseModel):
    """One node in the workspace graph read model."""

    model_config = ConfigDict(extra="allow")

    id: str
    type: WorkspaceGraphNodeType
    layer: WorkspaceGraphLayer
    label: str = ""
    metric: str = ""
    status: str = ""
    record_id: str = ""
    owner_path: str = ""
    implemented: bool = True
    placeholder: bool = False
    locked: bool = False
    suggested: bool = False
    is_primary: bool = False
    meta: dict[str, Any] = Field(default_factory=dict)


class WorkspaceGraphEdge(BaseModel):
    """One directed relation in the workspace graph read model."""

    model_config = ConfigDict(extra="allow")

    from_: str = Field(alias="from")
    to: str
    type: WorkspaceGraphEdgeType
    relation: str = ""
    suggested: bool = False
    placeholder: bool = False
    meta: dict[str, Any] = Field(default_factory=dict)


class WorkspaceGraphPayload(BaseModel):
    """Workspace graph payload shared by Home and future graph surfaces."""

    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = "1.0"
    view: str = "context"
    layers: list[WorkspaceGraphLayer] = Field(default_factory=list)
    nodes: list[WorkspaceGraphNode] = Field(default_factory=list)
    edges: list[WorkspaceGraphEdge] = Field(default_factory=list)


def graph_to_dict(graph: WorkspaceGraphPayload) -> dict[str, Any]:
    """Dump a graph payload with JSON-safe aliases."""
    return graph.model_dump(mode="json", by_alias=True, exclude_none=True)

