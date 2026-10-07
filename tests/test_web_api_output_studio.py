"""Tests for POST /studio/init (idempotent public-layer creation).

The rest of the Output Studio API was removed; blog CRUD lives under
``/content`` (see test_web_api_content_workspace.py). ``llm.is_configured``
is pinned off in the base class so no test can hit the network.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core.paths import REPO_ROOT
from nblane.web_api import app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"

BLOG_POST_FIXTURE = """---
title: First post
date: 2026-09-10
status: draft
summary: ""
tags:
  - robotics
related_claims:
  - claim-1
---

Hello **world**.
"""

PUBLISHABLE_POST_FIXTURE = """---
title: Ready post
date: 2026-09-11
status: draft
summary: A publishable summary.
tags:
  - robotics
cover: ""
related_evidence: []
related_kanban: []
---

A complete body with enough prose to read like a real public post.
"""

CLAIMS_FIXTURE = {
    "profile": "alice",
    "claims": [
        {
            "id": "claim-1",
            "text": "Reproduced the piper arm stack",
            "status": "accepted",
            "evidence_refs": ["ev-1"],
        },
        {
            "id": "claim-2",
            "text": "Pending claim",
            "status": "candidate",
        },
    ],
}

EVIDENCE_POOL_FIXTURE = {
    "profile": "alice",
    "updated": "2026-09-19",
    "evidence_entries": [
        {
            "id": "ev-1",
            "title": "Arm demo video",
            "type": "practice",
            "review_status": "reviewed",
            "summary": "Demoed the arm pick-and-place.",
            "date": "2026-09-12",
        },
    ],
}

PROJECTS_FIXTURE = {
    "projects": [
        {"id": "proj-1", "title": "Robot Arm"},
    ],
}


def _template_profile(root: Path, name: str = "alice", *, public_layer: bool = True) -> Path:
    profile = root / name
    shutil.copytree(TEMPLATE_DIR, profile)
    for file_path in profile.rglob("*"):
        if file_path.is_file():
            text = file_path.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            file_path.write_text(text, encoding="utf-8")
    if not public_layer:
        for filename in (
            "public-profile.yaml",
            "resume-source.yaml",
            "projects.yaml",
            "outputs.yaml",
        ):
            path = profile / filename
            if path.exists():
                path.unlink()
    (profile / "claims.yaml").write_text(
        yaml.safe_dump(CLAIMS_FIXTURE, allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "evidence-pool.yaml").write_text(
        yaml.safe_dump(EVIDENCE_POOL_FIXTURE, allow_unicode=True),
        encoding="utf-8",
    )
    if public_layer:
        (profile / "public-profile.yaml").write_text(
            yaml.safe_dump({"profile": name, "visibility": "private"}),
            encoding="utf-8",
        )
        (profile / "projects.yaml").write_text(
            yaml.safe_dump(PROJECTS_FIXTURE, allow_unicode=True),
            encoding="utf-8",
        )
        blog_dir = profile / "blog"
        blog_dir.mkdir(exist_ok=True)
        (blog_dir / "hello.md").write_text(BLOG_POST_FIXTURE, encoding="utf-8")
        (blog_dir / "ready.md").write_text(
            PUBLISHABLE_POST_FIXTURE, encoding="utf-8"
        )
    return profile


class StudioTestBase(unittest.TestCase):
    """Shared env patching: profile roots, git backup, and LLM off.

    The dev .env at the repo root configures a real LLM key, and the core
    candidate generators call ``llm.chat`` whenever one is configured; pin
    ``is_configured`` off so candidate generation exercises the deterministic
    rule fallback instead of the network.
    """

    def _client(self, root: Path) -> TestClient:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        for target in (
            "nblane.core.profile_io.git_backup.record_change",
            "nblane.core.llm.is_configured",
        ):
            patcher = (
                patch(target)
                if target.endswith("record_change")
                else patch(target, return_value=False)
            )
            self.addCleanup(patcher.stop)
            patcher.start()
        return TestClient(app)


class TestStudioInit(StudioTestBase):
    """POST /studio/init: idempotent public-layer creation."""

    def test_init_creates_public_layer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root, public_layer=False)
            client = self._client(root)
            response = client.post("/api/v1/profiles/alice/studio/init")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["created_paths"])
            self.assertTrue((profile / "public-profile.yaml").exists())
            self.assertTrue((profile / "blog").is_dir())

            again = client.post("/api/v1/profiles/alice/studio/init")
            self.assertEqual(again.status_code, 200)
            self.assertEqual(again.json()["created_paths"], [])

    def test_init_etag_mismatch_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, public_layer=False)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/init",
                headers={"If-Match": 'W/"stale"'},
            )
        self.assertEqual(response.status_code, 412)
        self.assertEqual(response.json()["code"], "etag_mismatch")
