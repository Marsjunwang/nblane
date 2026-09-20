"""Tests for the FastAPI SPA backend skeleton (M0 spike)."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from nblane.web_api import app

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"


class TestWebApi(unittest.TestCase):
    """Read-only v1 endpoints against a tmp profile root."""

    def _client(self, root: Path) -> TestClient:
        # profile_health resolves profiles through the core.io compat facade,
        # which binds its own PROFILES_DIR, so both must be patched.
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        return TestClient(app)

    def _profile(self, root: Path, name: str = "alice") -> Path:
        profile = root / name
        shutil.copytree(TEMPLATE_DIR, profile)
        for file_path in profile.rglob("*"):
            if file_path.is_file():
                text = file_path.read_text(encoding="utf-8")
                text = text.replace("{Name}", name)
                text = text.replace("{YYYY-MM-DD}", "2026-03-21")
                file_path.write_text(text, encoding="utf-8")
        (profile / "skill-tree.yaml").write_text(
            (
                f'profile: "{name}"\n'
                'schema: "robotics-engineer"\n'
                'updated: "2026-03-21"\n'
                "nodes:\n"
                "  - id: ros2_basics\n"
                "    status: solid\n"
                "  - id: moveit2\n"
                "    status: learning\n"
            ),
            encoding="utf-8",
        )
        return profile

    def test_health(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp))
            response = client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["version"])

    def test_list_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        row = payload[0]
        self.assertEqual(row["name"], "alice")
        self.assertGreater(row["skill_node_count"], 0)
        self.assertIn("skill_schema", row)
        self.assertIn("skill_tree_updated", row)
        self.assertIn("current_goal_title", row)

    def test_list_profiles_empty_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp))
            response = client.get("/api/v1/profiles")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_profile_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/summary")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        self.assertGreater(payload["skill_tree"]["node_count"], 0)
        self.assertTrue(payload["skill_tree"]["status_counts"])
        self.assertIn("section_counts", payload["kanban"])
        self.assertEqual(
            payload["kanban"]["total"],
            sum(payload["kanban"]["section_counts"].values()),
        )
        self.assertIn("entries", payload["evidence"])
        self.assertIn("claims", payload["evidence"])

    def test_profile_summary_unknown_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/nobody/summary")
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["code"], "profile_not_found")
        self.assertIn("nobody", payload["message"])

    def test_profile_health(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        self.assertIn("can_publish_context", payload)
        self.assertIn("error", payload["summary_counts"])
        self.assertIn("warning", payload["summary_counts"])
        self.assertIn("info", payload["summary_counts"])
        for issue in payload["issues"]:
            self.assertIn(issue["severity"], ("error", "warning", "info"))
            self.assertTrue(issue["category"])
            self.assertTrue(issue["title"])
        # The report must describe the tmp profile, not the repo's real one.
        self.assertFalse(
            any("skill-tree.yaml missing" in i["detail"] for i in payload["issues"])
        )

    def test_profile_health_unknown_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/nobody/health")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "profile_not_found")

    def test_dotdot_name_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/%2E%2E/summary")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_profile_name")

    def test_path_separator_name_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/bad%5Cname/summary")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_profile_name")

    def test_openapi_schema_paths(self) -> None:
        schema = app.openapi()
        paths = schema["paths"]
        for path in (
            "/api/v1/health",
            "/api/v1/profiles",
            "/api/v1/profiles/{name}/summary",
            "/api/v1/profiles/{name}/health",
        ):
            self.assertIn(path, paths)
            self.assertIn("get", paths[path])
        self.assertEqual(schema["info"]["title"], "nblane API")
        self.assertTrue(schema["info"]["version"])
        for component in (
            "HealthResponse",
            "ProfileSummary",
            "ProfileDetailSummary",
            "HealthReportModel",
            "ErrorResponse",
        ):
            self.assertIn(component, schema["components"]["schemas"])
        summary_get = paths["/api/v1/profiles/{name}/summary"]["get"]
        self.assertIn("404", summary_get["responses"])
        self.assertIn("400", summary_get["responses"])


if __name__ == "__main__":
    unittest.main()
