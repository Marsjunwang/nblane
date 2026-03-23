"""Add one inline evidence row to a skill-tree node."""

from __future__ import annotations

from nblane.core.io import (
    load_schema_raw,
    load_skill_tree_raw,
    save_skill_tree,
    schema_node_index,
)
from nblane.core.models import EVIDENCE_TYPES


def add_inline_evidence(
    profile: str,
    skill_id: str,
    *,
    type_: str,
    title: str,
    date: str = "",
    url: str = "",
    summary: str = "",
) -> None:
    """Append one evidence dict to ``nodes[].evidence`` for *skill_id*.

    Creates a minimal node at *learning* if the id was absent.

    Raises:
        ValueError: Unknown skill id, empty title, or missing schema/tree.
    """
    tree = load_skill_tree_raw(profile)
    if tree is None:
        raise ValueError("skill-tree.yaml not found.")

    schema_name = tree.get("schema")
    if not schema_name:
        raise ValueError("skill-tree.yaml has no 'schema' field.")

    schema_data = load_schema_raw(str(schema_name))
    if schema_data is None:
        raise ValueError(f"Schema not found: {schema_name!r}")

    index = schema_node_index(schema_data)
    if skill_id not in index:
        raise ValueError(
            f"Unknown skill id (not in schema): {skill_id!r}"
        )

    if not title.strip():
        raise ValueError("title must be non-empty.")

    et = type_ if type_ in EVIDENCE_TYPES else "practice"

    nodes = list(tree.get("nodes") or [])
    found: dict | None = None
    for n in nodes:
        if n.get("id") == skill_id:
            found = n
            break

    ev_item: dict = {
        "type": et,
        "title": title.strip(),
    }
    if date.strip():
        ev_item["date"] = date.strip()
    if url.strip():
        ev_item["url"] = url.strip()
    if summary.strip():
        ev_item["summary"] = summary.strip()

    if found is None:
        nodes.append(
            {
                "id": skill_id,
                "status": "learning",
                "evidence": [ev_item],
            }
        )
    else:
        evs = found.setdefault("evidence", [])
        evs.append(ev_item)

    tree["nodes"] = nodes
    save_skill_tree(profile, tree)
