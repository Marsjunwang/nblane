"""Tests for POST /ai-exceptions/dismiss (bulk AI-exception dismissal).

Failed agent-activity items flip to ``dismissed``; run/job ids land in the
profile's dismissal list; unknown id kinds are reported as skipped.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from nblane.core import agent_activity
from nblane.core.ai.exceptions import load_dismissed_ids
from nblane.core.paths import REPO_ROOT
from nblane.web_api import app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"


def _template_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    shutil.copytree(TEMPLATE_DIR, profile)
    for file_path in profile.rglob("*"):
        if file_path.is_file():
            text = file_path.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            text = text.replace("{YYYY-MM-DD}", "2026-09-19")
            file_path.write_text(text, encoding="utf-8")
    return profile


def _seed_failed_item(title: str) -> str:
    """Persist one failed AI-run activity item; return its id."""
    stored = agent_activity.append_activity_item(
        "alice",
        {
            "kind": "writeback",
            "candidate_type": "kanban_ai",
            "source_page": "kanban_ai",
            "target_owner": "kanban",
            "status": "failed",
            "title": title,
            "error": "bad input",
        },
    )
    return str(stored["id"])


class TestAIExceptionsDismiss(unittest.TestCase):
    def _client(self, root: Path) -> TestClient:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        return TestClient(app)

    def test_bulk_dismiss_ai_exceptions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            first_id = _seed_failed_item("Failed run one")
            second_id = _seed_failed_item("Failed run two")

            response = client.post(
                "/api/v1/profiles/alice/ai-exceptions/dismiss",
                json={"ids": [f"activity:{first_id}", f"activity:{second_id}", "run:old", "bogus:1"]},
            )

            stored = agent_activity.load_agent_activity(profile)
            dismissed_ids = load_dismissed_ids(profile)
        self.assertEqual(response.status_code, 200)
        # Two activity items plus the run id; unknown kinds stay skipped.
        self.assertEqual(response.json()["dismissed"], 3)
        self.assertEqual(response.json()["skipped"], ["bogus:1"])
        self.assertEqual(dismissed_ids, {"run:old"})
        statuses = {item["id"]: item["status"] for item in stored["items"]}
        self.assertEqual(statuses[first_id], "dismissed")
        self.assertEqual(statuses[second_id], "dismissed")
