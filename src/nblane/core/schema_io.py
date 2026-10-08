"""Schema file I/O and raw schema helpers.

Schema lookup is a single resolver (:func:`schema_path`): the data dir
(``<NBLANE_ROOT>/schemas``, :data:`nblane.core.paths.SCHEMAS_DIR`) first, so
admins can add or override a domain by dropping a YAML there, then the
schemas shipped with the code (the ``schemas`` package).
"""

from __future__ import annotations

import importlib.util
import re
from functools import lru_cache
from pathlib import Path

from nblane.core.models import Schema
from nblane.core.paths import SCHEMAS_DIR
from nblane.core.yaml_io import _load_yaml_file

_SCHEMA_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


@lru_cache(maxsize=1)
def builtin_schemas_dir() -> Path:
    """Directory of the schemas shipped with the code checkout / wheel."""
    try:
        spec = importlib.util.find_spec("schemas")
    except (ImportError, ValueError):
        spec = None
    if spec is not None and spec.origin:
        candidate = Path(spec.origin).resolve().parent
        if any(candidate.glob("*.yaml")):
            return candidate
    return Path(__file__).resolve().parents[3] / "schemas"


def is_valid_schema_name(name: object) -> bool:
    """True for ASCII ``[a-z0-9_-]`` names (no path separators or dots)."""
    return isinstance(name, str) and bool(_SCHEMA_NAME_RE.match(name))


def _search_dirs(data_dir: Path | None = None) -> list[tuple[str, Path]]:
    data = data_dir if data_dir is not None else SCHEMAS_DIR
    builtin = builtin_schemas_dir()
    try:
        same = builtin.resolve() == Path(data).resolve()
    except OSError:
        same = False
    if same:
        # Running from the checkout with NBLANE_ROOT = repo: one directory.
        return [("builtin", builtin)]
    return [("data", data), ("builtin", builtin)]


def _resolve(
    schema_name: str, data_dir: Path | None = None
) -> tuple[str, Path] | None:
    if not is_valid_schema_name(schema_name):
        return None
    for source, directory in _search_dirs(data_dir):
        path = directory / f"{schema_name}.yaml"
        if path.is_file():
            return source, path
    return None


def schema_path(
    schema_name: str, data_dir: Path | None = None
) -> Path | None:
    """Path of ``<schema_name>.yaml`` (data dir first, then built-in).

    Returns None for invalid names or when no such schema exists.
    *data_dir* overrides :data:`SCHEMAS_DIR` (used by the ``io`` facade).
    """
    found = _resolve(schema_name, data_dir)
    return found[1] if found else None


def load_schema(
    schema_name: str, data_dir: Path | None = None
) -> Schema | None:
    """Load a schema by name as a Schema object."""
    raw = load_schema_raw(schema_name, data_dir)
    if raw is None:
        return None
    return Schema.from_dict(raw)


def load_schema_raw(
    schema_name: str, data_dir: Path | None = None
) -> dict | None:
    """Load a schema by name as a raw dict."""
    path = schema_path(schema_name, data_dir)
    if path is None:
        return None
    raw = _load_yaml_file(path)
    if raw is None:
        return None
    return raw


def list_schemas(data_dir: Path | None = None) -> list[str]:
    """Available schema names (data dir ∪ built-in, sorted)."""
    names: set[str] = set()
    for _source, directory in _search_dirs(data_dir):
        if not directory.is_dir():
            continue
        names.update(
            p.stem
            for p in directory.glob("*.yaml")
            if is_valid_schema_name(p.stem)
        )
    return sorted(names)


def list_schema_infos(data_dir: Path | None = None) -> list[dict]:
    """Summary per available schema.

    Each item: ``{name, domain, description, node_count, source}`` where
    source is ``"data"`` (data dir) or ``"builtin"`` (shipped with code).
    Unreadable files are skipped.
    """
    out: list[dict] = []
    for name in list_schemas(data_dir):
        found = _resolve(name, data_dir)
        if found is None:
            continue
        source, path = found
        try:
            raw = _load_yaml_file(path)
        except Exception:  # noqa: BLE001 - one broken file must not hide others
            continue
        if not isinstance(raw, dict):
            continue
        nodes = raw.get("nodes") or []
        out.append(
            {
                "name": name,
                "domain": str(raw.get("domain") or name),
                "description": " ".join(
                    str(raw.get("description") or "").split()
                ),
                "node_count": sum(
                    1 for n in nodes if isinstance(n, dict) and n.get("id")
                ),
                "source": source,
            }
        )
    return out


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
