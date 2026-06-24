"""Tests for the typed workspace graph read model."""

from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from nblane.core.home_dashboard import dashboard_payload
from nblane.core.growth_graph_contract import growth_graph_node_type_roles, growth_graph_roles
from nblane.core.workspace_graph import (
    workspace_graph_layers,
    workspace_graph_node_types,
)
from schemas.workspace_graph import WorkspaceGraphPayload, graph_to_dict


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def test_workspace_graph_empty_profile_returns_full_layer_skeleton() -> None:
    """Even an empty profile exposes the stable Growth Graph skeleton."""
    with tempfile.TemporaryDirectory() as tmp_s:
        profile = Path(tmp_s) / "empty"
        profile.mkdir()
        payload = dashboard_payload(profile)

    graph = payload["graph"]
    assert graph["layers"] == list(workspace_graph_layers())
    nodes = {node["id"]: node for node in graph["nodes"]}
    assert nodes["north_star"]["layer"] == "direction"
    assert nodes["north_star"]["placeholder"] is True
    assert nodes["goal:missing"]["layer"] == "objective"
    assert nodes["goal:missing"]["placeholder"] is True
    assert nodes["project_case:planned"]["layer"] == "work_context"
    assert nodes["source:inbox"]["layer"] == "source"
    assert nodes["source:inbox"]["placeholder"] is True
    assert nodes["source:inbox"]["primary_action"]["label"] == "Capture source"
    assert nodes["source:inbox"]["primary_action"]["event"]["payload"]["path"] == "pages/7_Research.py"
    assert nodes["source:inbox"]["secondary_actions"][0]["label"] == "Open Research"
    assert nodes["evidence_candidate:pending"]["layer"] == "evidence"
    assert nodes["claim:planned"]["layer"] == "claim"
    assert nodes["skill:lit"]["layer"] == "capability"
    assert nodes["output"]["layer"] == "output"
    assert nodes["feedback:planned"]["layer"] == "feedback"
    assert nodes["health"]["layer"] == "governance"
    assert nodes["capacity:planned"]["layer"] == "governance"
    for node in nodes.values():
        assert node["type"] in workspace_graph_node_types()
        assert "implemented" in node
        assert "placeholder" in node

    # Every node carries a visual role consistent with the contract type->role
    # map; roles are one of the 8 star-tree prototypes or "" (out of tree).
    valid_roles = set(growth_graph_roles()) | {""}
    type_roles = growth_graph_node_type_roles()
    for node in nodes.values():
        assert node["role"] in valid_roles
        assert node["role"] == type_roles.get(node["type"], "")
    assert nodes["north_star"]["role"] == "trunk"
    assert nodes["goal:missing"]["role"] == "direction"
    assert nodes["project_case:planned"]["role"] == "branch"
    assert nodes["source:inbox"]["role"] == "sand"
    assert nodes["atomic_evidence:pool"]["role"] == "fruit"
    assert nodes["claim:planned"]["role"] == "constellation"
    assert nodes["skill:lit"]["role"] == "star"
    assert nodes["output"]["role"] == "leaf"
    assert nodes["health"]["role"] == ""
    sand_placeholders = [
        node
        for node in nodes.values()
        if node.get("item_kind") == "runtime_sand"
    ]
    assert len(sand_placeholders) >= 30
    assert all(node["placeholder"] and node["suggested"] for node in sand_placeholders)
    output_placeholders = [
        node
        for node in nodes.values()
        if node.get("item_kind") == "runtime_output"
    ]
    assert len(output_placeholders) == 3
    assert all(
        node["placeholder"] and node["suggested"] and node.get("synthetic")
        for node in output_placeholders
    )


def test_workspace_graph_schema_validates_aliases_and_no_dangling_edges() -> None:
    """The graph payload is schema-valid and serializes edge `from` aliases."""
    with tempfile.TemporaryDirectory() as tmp_s:
        profile = Path(tmp_s) / "alice"
        profile.mkdir()
        _write_yaml(
            profile / "goals.yaml",
            {
                "schema_version": "1.0",
                "profile": "alice",
                "current_goal_id": "g1",
                "goals": [
                    {
                        "id": "g1",
                        "title": "Private launch goal",
                        "status": "active",
                        "ui_visibility": "private",
                        "skill_links": [
                            {"node_id": "secret_skill", "label": "Secret Skill"}
                        ],
                    }
                ],
            },
        )
        _write_yaml(
            profile / "evidence-pool.yaml",
            {
                "profile": "alice",
                "evidence_entries": [
                    {
                        "id": "ev_1",
                        "title": "Atomic row",
                        "project_refs": ["project:secret"],
                        "source_refs": ["source:research:20260513-001"],
                    }
                ],
            },
        )
        _write_yaml(
            profile / "project-board.yaml",
            {
                "schema_version": "1.0",
                "profile": "alice",
                "project_cases": [
                    {
                        "id": "project:secret",
                        "title": "Sensitive project title",
                        "status": "active",
                        "visibility": "private",
                        "goal_refs": ["g1"],
                        "task_refs": ["task_active"],
                        "evidence_refs": ["ev_1"],
                        "source_refs": ["source:research:20260513-001"],
                    }
                ],
            },
        )
        (profile / "research").mkdir()
        _write_yaml(
            profile / "research" / "sources.yaml",
            {
                "schema_version": "1.0",
                "profile": "alice",
                "sources": [
                    {
                        "id": "source:research:20260513-001",
                        "title": "Sensitive source title",
                        "status": "inbox",
                    }
                ],
            },
        )
        (profile / "kanban.md").write_text(
            "# alice · Kanban\n\n"
            "## Doing\n\n"
            "- [ ] Active task\n"
            "  - id: task_active\n"
            "  - project_id: project:secret\n"
            "## Queue\n\n"
            "## Done\n\n"
            "- [x] Needs review\n\n",
            encoding="utf-8",
        )
        (profile / "SKILL.md").write_text(
            "# Alice · nblane Profile\n\n"
            "## Identity\n\n"
            "- **North Star**: Sensitive north star.\n"
            "- **North Star Visibility**: private\n\n"
            "---\n",
            encoding="utf-8",
        )
        payload = dashboard_payload(profile)

    graph = payload["graph"]
    validated = WorkspaceGraphPayload.model_validate(graph)
    dumped = graph_to_dict(validated)
    assert dumped["edges"]
    assert "from" in dumped["edges"][0]
    node_ids = {node["id"] for node in dumped["nodes"]}
    for edge in dumped["edges"]:
        assert edge["from"] in node_ids
        assert edge["to"] in node_ids
    text = yaml.dump(dumped, allow_unicode=True)
    assert "Private launch goal" not in text
    assert "Secret Skill" not in text
    assert "Sensitive north star" not in text
    assert "Sensitive project title" not in text
    assert "Sensitive source title" not in text
    nodes = {node["id"]: node for node in dumped["nodes"]}
    assert nodes["project:secret"]["layer"] == "work_context"
    assert nodes["project:secret"]["owner_path"] == "pages/11_Project_Board.py"
    assert nodes["source:inbox"]["owner_path"] == "pages/7_Research.py"
    assert nodes["source:inbox"]["primary_action"]["label"] == "Review source"
    assert nodes["source:inbox"]["secondary_actions"][0]["id"] == "open_research"
    assert nodes["evidence_candidate:pending"]["metric"] == "1"
    assert nodes["atomic_evidence:pool"]["metric"] == "2"
    assert (
        nodes["atomic_evidence:pool"]["owner_path"]
        == "pages/2_Evidence_Review.py"
    )
    edges = {
        (edge["from"], edge["to"], edge["type"])
        for edge in dumped["edges"]
    }
    assert ("goal:g1", "project:secret", "contains") in edges
    assert ("project:secret", "task:task_active", "contains") in edges
    assert ("project:secret", "atomic_evidence:pool", "supports") in edges
    assert ("project:secret", "source:inbox", "contains") in edges


def test_workspace_graph_lifecycle_refs_and_runtime_placeholders() -> None:
    """Graph renders all task states, archived goals, inferred edges, placeholders."""
    with tempfile.TemporaryDirectory() as tmp_s:
        profile = Path(tmp_s) / "alice"
        profile.mkdir()
        _write_yaml(
            profile / "goals.yaml",
            {
                "schema_version": "1.0",
                "profile": "alice",
                "current_goal_id": "g1",
                "goals": [
                    {"id": "g1", "title": "Ship demo", "status": "active"},
                    {"id": "g_old", "title": "Old demo", "status": "archived"},
                ],
            },
        )
        (profile / "kanban.md").write_text(
            "# alice · Kanban\n\n"
            "## Doing\n\n"
            "- [ ] Active 1\n"
            "  - id: task_active_1\n"
            "  - project_id: project:demo\n"
            "- [ ] Active 2\n"
            "  - id: task_active_2\n"
            "- [ ] Active 3\n"
            "  - id: task_active_3\n"
            "- [ ] Active 4\n"
            "  - id: task_active_4\n"
            "## Queue\n\n"
            "- [ ] Queued\n"
            "  - id: task_queued\n"
            "## Done\n\n"
            "- [x] Done task\n"
            "  - id: task_done\n"
            "  - project_id: project:demo\n"
            "## Someday / Maybe\n\n"
            "- Someday task\n"
            "  - id: task_someday\n",
            encoding="utf-8",
        )
        (profile / "kanban-archive.md").write_text(
            "# alice · Kanban archive\n\n"
            "## Archived · 2026-05-01\n\n"
            "- [x] Archived task\n"
            "  - id: task_archived\n"
            "  - project_id: project:demo\n",
            encoding="utf-8",
        )
        _write_yaml(
            profile / "project-board.yaml",
            {
                "schema_version": "1.0",
                "profile": "alice",
                "project_cases": [
                    {
                        "id": "project:demo",
                        "title": "Demo",
                        "status": "active",
                        "goal_refs": ["g1"],
                        "task_refs": ["task_done"],
                        "evidence_refs": ["ev_done"],
                    }
                ],
            },
        )
        _write_yaml(
            profile / "evidence-pool.yaml",
            {
                "profile": "alice",
                "evidence_entries": [
                    {
                        "id": "ev_done",
                        "title": "Done evidence",
                        "review_status": "reviewed",
                        "project_refs": ["project:demo"],
                        "skill_refs": ["ros2_basics"],
                        "kanban_refs": ["kanban:task_done"],
                    },
                    {
                        "id": "ev_orphan",
                        "title": "Orphan evidence",
                        "review_status": "reviewed",
                    },
                ],
            },
        )
        _write_yaml(
            profile / "skill-tree.yaml",
            {
                "profile": "alice",
                "schema": "robotics-engineer",
                "nodes": [
                    {
                        "id": "ros2_basics",
                        "status": "solid",
                        "evidence_refs": ["ev_done"],
                    }
                ],
            },
        )
        _write_yaml(
            profile / "claims.yaml",
            {
                "schema_version": "1.0",
                "profile": "alice",
                "claims": [
                    {
                        "id": "claim:done",
                        "status": "accepted",
                        "text": "Done evidence supports ROS 2 skill.",
                        "evidence_refs": ["ev_done"],
                        "skill_refs": ["ros2_basics"],
                    }
                ],
            },
        )

        payload = dashboard_payload(profile)

    graph = payload["graph"]
    nodes = {node["id"]: node for node in graph["nodes"]}
    assert nodes["goal:g_old"]["status"] == "archived"
    task_ids = {
        node["id"]
        for node in graph["nodes"]
        if node["type"] == "task"
    }
    assert {
        "task:task_active_1",
        "task:task_active_2",
        "task:task_active_3",
        "task:task_active_4",
        "task:task_queued",
        "task:task_done",
        "task:task_someday",
        "task:task_archived",
    }.issubset(task_ids)
    assert nodes["task:task_done"]["status"] == "done"
    assert nodes["task:task_archived"]["status"] == "archived"

    edges = {
        (edge["from"], edge["to"], edge["type"])
        for edge in graph["edges"]
    }
    assert ("task:task_done", "atomic_evidence:ev_done", "generated_by") in edges
    assert ("project:demo", "atomic_evidence:ev_done", "supports") in edges
    assert ("atomic_evidence:ev_done", "claim:item:claim:done", "supports") in edges
    assert ("claim:item:claim:done", "skill:ros2_basics", "supports") in edges
    assert ("atomic_evidence:ev_done", "skill:ros2_basics", "supports") in edges
    assert any(
        edge["to"] == "atomic_evidence:ev_orphan"
        and edge["relation"] == "layout_anchor"
        and edge["suggested"]
        for edge in graph["edges"]
    )

    node_ids = set(nodes)
    for edge in graph["edges"]:
        assert edge["from"] in node_ids
        assert edge["to"] in node_ids

    output_placeholders = [
        node for node in graph["nodes"] if node.get("item_kind") == "runtime_output"
    ]
    assert len(output_placeholders) == 3
    assert all(node["placeholder"] and node.get("synthetic") for node in output_placeholders)
    sand_placeholders = [
        node for node in graph["nodes"] if node.get("item_kind") == "runtime_sand"
    ]
    assert sand_placeholders
    assert all(node["placeholder"] and node.get("synthetic") for node in sand_placeholders)
