"""Tests for shared YAML loader behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.io import (
    load_evidence_pool,
    load_evidence_pool_raw,
    load_schema,
    load_schema_raw,
    load_skill_tree,
    load_skill_tree_raw,
)


class TestIoLoaders(unittest.TestCase):
    """Raw and typed loaders preserve public behavior."""

    def test_skill_tree_loaders_accept_name_and_path(self) -> None:
        """Skill tree raw and typed loaders share path resolution."""
        raw = {
            "profile": "u1",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [{"id": "ros2_basics", "status": "solid"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "u1"
            prof.mkdir()
            (prof / "skill-tree.yaml").write_text(
                yaml.dump(raw, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            with patch("nblane.core.io.profile_dir", lambda _n: prof):
                self.assertEqual(load_skill_tree_raw("u1"), raw)

            tree = load_skill_tree(prof)

        self.assertIsNotNone(tree)
        assert tree is not None
        self.assertEqual(tree.profile, "u1")
        self.assertEqual(tree.nodes[0].id, "ros2_basics")

    def test_evidence_pool_non_mapping_returns_none(self) -> None:
        """Evidence loaders keep rejecting non-mapping YAML documents."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "u1"
            prof.mkdir()
            (prof / "evidence-pool.yaml").write_text(
                "- not-a-mapping\n",
                encoding="utf-8",
            )

            self.assertIsNone(load_evidence_pool_raw(prof))
            self.assertIsNone(load_evidence_pool(prof))

    def test_schema_loaders_share_yaml_read(self) -> None:
        """Schema raw and typed loaders read the same document."""
        raw = {
            "schema": "demo",
            "nodes": [{"id": "ros2_basics", "label": "ROS 2"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            schemas = Path(tmp)
            (schemas / "demo.yaml").write_text(
                yaml.dump(raw, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            with patch("nblane.core.io.SCHEMAS_DIR", schemas):
                self.assertEqual(load_schema_raw("demo"), raw)
                schema = load_schema("demo")

        self.assertIsNotNone(schema)
        assert schema is not None
        self.assertEqual(schema.nodes[0].id, "ros2_basics")


if __name__ == "__main__":
    unittest.main()
