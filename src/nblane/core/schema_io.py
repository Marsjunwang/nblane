"""Schema file I/O and raw schema helpers."""

from __future__ import annotations

from nblane.core.models import Schema
from nblane.core.paths import SCHEMAS_DIR
from nblane.core.yaml_io import _load_yaml_file


def load_schema(schema_name: str) -> Schema | None:
    """Load schemas/{schema_name}.yaml as a Schema object."""
    path = SCHEMAS_DIR / f"{schema_name}.yaml"
    raw = _load_yaml_file(path)
    if raw is None:
        return None
    return Schema.from_dict(raw)


def load_schema_raw(schema_name: str) -> dict | None:
    """Load schemas/{schema_name}.yaml as a raw dict."""
    path = SCHEMAS_DIR / f"{schema_name}.yaml"
    raw = _load_yaml_file(path)
    if raw is None:
        return None
    return raw


def list_schemas() -> list[str]:
    """Return available schema names (without .yaml extension)."""
    return sorted(p.stem for p in SCHEMAS_DIR.glob("*.yaml"))


def schema_node_index(schema_data: dict) -> dict[str, dict]:
    """Return id -> schema-node dict from a raw schema dict.

    Kept for backward compatibility with code that still works on
    raw dicts (Streamlit pages during migration).
    """
    return {
        n["id"]: n
        for n in schema_data.get("nodes") or []
        if "id" in n
    }


def status_by_node_id(tree_data: dict | None) -> dict[str, str]:
    """Map node id -> status from a raw skill-tree dict."""
    if tree_data is None:
        return {}
    out: dict[str, str] = {}
    for node in tree_data.get("nodes") or []:
        nid = node.get("id")
        if nid is None:
            continue
        out[nid] = node.get("status", "locked")
    return out
