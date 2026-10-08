"""Tests for schema lookup (data dir → built-in) and the shipped schemas."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core import io as io_facade
from nblane.core import schema_io

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILTIN = REPO_ROOT / "schemas"
STARMAP_ZH = {
    "基础", "控制", "影响力", "领导力", "学习力", "运动", "操作", "中间件",
    "导航", "感知", "研究", "仿真", "战略", "系统", "规划", "安全",
}


def _schema(domain: str, ids: list[str]) -> dict:
    return {
        "schema_version": "1.0",
        "domain": domain,
        "description": "d",
        "nodes": [{"id": i, "label": i, "level": 1, "category": "foundations"} for i in ids],
    }


class TestSchemaLookup(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.data = Path(tmp.name) / "schemas"
        self.data.mkdir()
        patcher = patch("nblane.core.schema_io.SCHEMAS_DIR", self.data)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _write(self, name: str, data: dict) -> None:
        (self.data / f"{name}.yaml").write_text(
            yaml.safe_dump(data, allow_unicode=True), encoding="utf-8"
        )

    def test_builtin_found_when_data_dir_lacks_it(self) -> None:
        self.assertEqual(
            schema_io.schema_path("robotics-engineer"),
            BUILTIN / "robotics-engineer.yaml",
        )
        schema = schema_io.load_schema("autonomous-driving")
        assert schema is not None
        self.assertIn("自动驾驶", schema.domain)

    def test_data_dir_overrides_builtin(self) -> None:
        self._write("robotics-engineer", _schema("Override", ["only_node"]))
        self.assertEqual(
            schema_io.schema_path("robotics-engineer"),
            self.data / "robotics-engineer.yaml",
        )
        schema = schema_io.load_schema("robotics-engineer")
        assert schema is not None
        self.assertEqual([n.id for n in schema.nodes], ["only_node"])

    def test_invalid_names_rejected(self) -> None:
        (self.data.parent / "outside.yaml").write_text("domain: x\n", encoding="utf-8")
        for bad in ["../outside", "a/b", "a\\b", "", ".hidden", "UPPER", "名字", "x.y", None]:
            self.assertIsNone(schema_io.schema_path(bad), bad)  # type: ignore[arg-type]
            self.assertIsNone(schema_io.load_schema_raw(bad), bad)  # type: ignore[arg-type]

    def test_list_union_and_infos(self) -> None:
        self._write("custom-domain", _schema("Custom / 自定义", ["a", "b"]))
        self._write("robotics-engineer", _schema("Override", ["a"]))
        (self.data / "Bad Name.yaml").write_text("domain: x\n", encoding="utf-8")
        names = schema_io.list_schemas()
        self.assertEqual(names, ["autonomous-driving", "custom-domain", "robotics-engineer"])
        infos = {i["name"]: i for i in schema_io.list_schema_infos()}
        self.assertEqual(
            infos["custom-domain"],
            {"name": "custom-domain", "domain": "Custom / 自定义", "description": "d",
             "node_count": 2, "source": "data"},
        )
        self.assertEqual(infos["robotics-engineer"]["source"], "data")
        self.assertEqual(infos["autonomous-driving"]["source"], "builtin")
        self.assertEqual(infos["autonomous-driving"]["node_count"], 82)

    def test_python_modules_in_schemas_package_are_not_schemas(self) -> None:
        self.assertNotIn("__init__", schema_io.list_schemas())
        self.assertNotIn("ai_patch", schema_io.list_schemas())

    def test_io_facade_delegates_with_its_own_dir(self) -> None:
        other = self.data.parent / "other"
        other.mkdir()
        (other / "demo.yaml").write_text(
            yaml.safe_dump(_schema("Demo", ["x"])), encoding="utf-8"
        )
        with patch("nblane.core.io.SCHEMAS_DIR", other):
            self.assertIn("demo", io_facade.list_schemas())
            self.assertIn("robotics-engineer", io_facade.list_schemas())
            self.assertIsNotNone(io_facade.load_schema("demo"))

    def test_builtins_resolve_with_empty_data_root(self) -> None:
        with tempfile.TemporaryDirectory() as data_root:
            result = subprocess.run(
                [sys.executable, "-c",
                 "from nblane.core import schema_io;print(','.join(schema_io.list_schemas()))"],
                capture_output=True, text=True, check=True,
                env={**os.environ, "NBLANE_ROOT": data_root},
            )
        self.assertEqual(result.stdout.strip(), "autonomous-driving,robotics-engineer")


class TestShippedSchemas(unittest.TestCase):
    def _check(self, name: str) -> dict:
        raw = yaml.safe_load((BUILTIN / f"{name}.yaml").read_text(encoding="utf-8"))
        nodes = raw["nodes"]
        ids = [n["id"] for n in nodes]
        self.assertEqual(len(ids), len(set(ids)), "duplicate ids")
        index = set(ids)
        cats = raw.get("categories") or {}
        for node in nodes:
            self.assertRegex(node["id"], r"^[a-z0-9_]+$")
            self.assertIn(node["level"], (1, 2, 3, 4), node["id"])
            self.assertIn(node["category"], cats, node["id"])
            for req in node.get("requires") or []:
                self.assertIn(req, index, f"{node['id']} requires unknown {req}")
        # DAG: no requires cycles
        graph = {n["id"]: list(n.get("requires") or []) for n in nodes}
        state: dict[str, int] = {}

        def visit(nid: str) -> None:
            self.assertNotEqual(state.get(nid), 1, f"cycle at {nid}")
            if state.get(nid) == 2:
                return
            state[nid] = 1
            for dep in graph[nid]:
                visit(dep)
            state[nid] = 2

        for nid in graph:
            visit(nid)
        # every category used and named with a starmap-known zh name
        self.assertEqual(set(cats), {n["category"] for n in nodes})
        for zh in cats.values():
            self.assertIn(zh, STARMAP_ZH)
        return raw

    def test_autonomous_driving_schema(self) -> None:
        raw = self._check("autonomous-driving")
        self.assertEqual(raw["domain"], "Autonomous Driving Engineer / 自动驾驶工程师")
        self.assertEqual(len(raw["categories"]), 13)
        self.assertEqual(raw["categories"]["planning"], "规划")
        self.assertEqual(raw["categories"]["safety"], "安全")
        ids = {n["id"] for n in raw["nodes"]}
        self.assertIn("adas_productization", ids)
        self.assertNotIn("robot_productization", ids)
        for shared in ("linux_basics", "python_core", "edge_inference", "industry_trust",
                       "team_building", "ecosystem_leverage"):
            self.assertIn(shared, ids)

    def test_robotics_schema_categories_match_fallback_table(self) -> None:
        from nblane.core.starmap_snapshot import CATEGORY_ZH

        raw = self._check("robotics-engineer")
        for cat, zh in raw["categories"].items():
            self.assertEqual(CATEGORY_ZH[cat], zh)

    def test_schema_model_category_name(self) -> None:
        from nblane.core.models import Schema
        from nblane.core.starmap_snapshot import category_display_name

        schema = Schema.from_dict({"categories": {"x": "叉"}, "nodes": []})
        self.assertEqual(schema.categories, {"x": "叉"})
        self.assertEqual(category_display_name(schema, "x"), "叉")
        self.assertEqual(category_display_name(schema, "planning"), "规划")
        self.assertEqual(category_display_name(None, "zzz"), "zzz")


if __name__ == "__main__":
    unittest.main()
