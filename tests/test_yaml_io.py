from __future__ import annotations

import os

from nblane.core import yaml_io
from nblane.core.file_write import atomic_write_text


def test_cached_load_returns_independent_copies(tmp_path):
    path = tmp_path / "sources.yaml"
    path.write_text("sources:\n  - id: a\n    metadata: {page: 1}\n", encoding="utf-8")

    first = yaml_io.load_yaml_dict_cached(path)
    first["sources"][0]["metadata"]["page"] = 99
    second = yaml_io.load_yaml_dict_cached(path)

    assert second == {"sources": [{"id": "a", "metadata": {"page": 1}}]}


def test_cached_load_skips_reparse_while_unchanged(tmp_path, monkeypatch):
    path = tmp_path / "sources.yaml"
    path.write_text("a: 1\n", encoding="utf-8")
    calls = []
    real = yaml_io._load_yaml_dict
    monkeypatch.setattr(yaml_io, "_load_yaml_dict", lambda p: calls.append(p) or real(p))

    yaml_io.load_yaml_dict_cached(path)
    yaml_io.load_yaml_dict_cached(path)

    assert len(calls) == 1


def test_cached_load_sees_atomic_replace(tmp_path):
    path = tmp_path / "sources.yaml"
    path.write_text("a: 1\n", encoding="utf-8")
    assert yaml_io.load_yaml_dict_cached(path) == {"a": 1}

    # Same size, and force the same mtime: only the inode changes.
    stat = path.stat()
    atomic_write_text(path, "a: 2\n")
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))

    assert yaml_io.load_yaml_dict_cached(path) == {"a": 2}


def test_cached_load_missing_or_non_mapping(tmp_path):
    assert yaml_io.load_yaml_dict_cached(tmp_path / "missing.yaml") is None
    path = tmp_path / "list.yaml"
    path.write_text("- a\n- b\n", encoding="utf-8")
    assert yaml_io.load_yaml_dict_cached(path) is None
