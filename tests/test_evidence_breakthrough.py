"""Tests for the evidence ``breakthrough`` flag (round-trip + edit whitelist).

Covers the parsed-model path (``EvidenceRecord.from_dict``/``to_dict``),
the raw-dict path (``profile_io.load_evidence_pool_raw`` /
``update_evidence_pool``), and the single-entry edit endpoint
(``POST /profiles/{name}/evidence/{entry_id}/edit``) accepting
``breakthrough`` as a bool flag ("true"/"false", "" clears, invalid 422).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import profile_io
from nblane.core.models import EvidenceRecord
from nblane.web_api import app

POOL_FIXTURE = {
    "profile": "alice",
    "evidence_entries": [
        {"id": "ev_plain", "type": "project", "title": "Plain demo"},
        {
            "id": "ev_landmark",
            "type": "project",
            "title": "Landmark",
            "strength": "strong",
            "breakthrough": True,
        },
    ],
}


def _write_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "evidence-pool.yaml").write_text(
        yaml.safe_dump(dict(POOL_FIXTURE, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    return profile


class TestBreakthroughModelRoundTrip(unittest.TestCase):
    """Parsed model: default false, reads and re-serializes the flag."""

    def test_default_false(self) -> None:
        record = EvidenceRecord.from_dict(
            {"id": "ev", "type": "practice", "title": "T"}
        )
        self.assertFalse(record.breakthrough)
        self.assertNotIn("breakthrough", record.to_dict())

    def test_true_round_trips(self) -> None:
        record = EvidenceRecord.from_dict(
            {"id": "ev", "type": "practice", "title": "T",
             "breakthrough": True}
        )
        self.assertTrue(record.breakthrough)
        self.assertIs(record.to_dict()["breakthrough"], True)
        reloaded = EvidenceRecord.from_dict(record.to_dict())
        self.assertTrue(reloaded.breakthrough)

    def test_pool_loader_paths_agree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            patcher = patch("nblane.core.profile_io.PROFILES_DIR", root)
            self.addCleanup(patcher.stop)
            patcher.start()
            pool = profile_io.load_evidence_pool(pdir)
            raw = profile_io.load_evidence_pool_raw(pdir)
        by_id = pool.by_id()
        self.assertFalse(by_id["ev_plain"].breakthrough)
        self.assertTrue(by_id["ev_landmark"].breakthrough)
        raw_rows = {row["id"]: row for row in raw["evidence_entries"]}
        self.assertNotIn("breakthrough", raw_rows["ev_plain"])
        self.assertIs(raw_rows["ev_landmark"]["breakthrough"], True)


class TestBreakthroughEditWhitelist(unittest.TestCase):
    """POST /evidence/{entry_id}/edit: breakthrough as a bool flag."""

    def _client(self, root: Path) -> TestClient:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        patcher = patch("nblane.core.git_backup.record_change")
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)

    def _edit(self, client: TestClient, entry_id: str, value: str):
        return client.post(
            f"/api/v1/profiles/alice/evidence/{entry_id}/edit",
            json={"fields": {"breakthrough": value}},
        )

    def _raw_row(self, pdir: Path, entry_id: str) -> dict:
        raw = yaml.safe_load(
            (pdir / "evidence-pool.yaml").read_text(encoding="utf-8")
        )
        return next(row for row in raw["evidence_entries"]
                    if row["id"] == entry_id)

    def test_set_and_clear_via_edit_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            set_resp = self._edit(client, "ev_plain", "true")
            row_after_set = self._raw_row(pdir, "ev_plain")
            detail = client.get("/api/v1/profiles/alice/evidence/ev_plain")
            # Parsed-model view agrees with the raw file.
            pool = profile_io.load_evidence_pool(pdir)
            record = pool.by_id()["ev_plain"]
            clear_resp = self._edit(client, "ev_plain", "false")
            row_after_clear = self._raw_row(pdir, "ev_plain")
        self.assertEqual(set_resp.status_code, 200)
        self.assertEqual(set_resp.json()["changed"], 1)
        self.assertIs(row_after_set["breakthrough"], True)
        self.assertTrue(record.breakthrough)
        self.assertTrue(record.to_dict()["breakthrough"])
        self.assertTrue(detail.json()["breakthrough"])
        self.assertEqual(clear_resp.status_code, 200)
        self.assertNotIn("breakthrough", row_after_clear)

    def test_empty_string_clears(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            response = self._edit(client, "ev_landmark", "")
            row = self._raw_row(pdir, "ev_landmark")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("breakthrough", row)

    def test_invalid_value_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            response = self._edit(client, "ev_plain", "yes")
            row = self._raw_row(pdir, "ev_plain")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_edit_value")
        self.assertNotIn("breakthrough", row)

    def test_list_view_exposes_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/evidence")
        self.assertEqual(response.status_code, 200)
        items = {item["id"]: item for item in response.json()["items"]}
        self.assertFalse(items["ev_plain"]["breakthrough"])
        self.assertTrue(items["ev_landmark"]["breakthrough"])


if __name__ == "__main__":
    unittest.main()
