"""Tests for the Output Studio slice (blog CRUD/status flow + candidates).

Covers the studio overview read (posts/counters/options, ETag header),
public-layer init, blog detail/create/save/publish with the weak-ETag
``If-Match`` 412 contract, the publish-readiness check, evidence/claim
candidate preview + draft creation (rule fallback — no LLM calls), and the
JD match 422 degradation contract. ``llm.is_configured`` is pinned off in
the base class so no test can hit the network even when the dev .env has a
key configured.
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


class TestStudioGet(StudioTestBase):
    """GET /studio: posts, counters, options, ETag."""

    def test_get_studio_lists_posts_and_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/studio")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["ETag"].startswith('W/"'))
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        self.assertTrue(payload["initialized"])

        posts = {post["slug"]: post for post in payload["posts"]}
        self.assertEqual(sorted(posts), ["hello", "ready"])
        hello = posts["hello"]
        self.assertEqual(hello["title"], "First post")
        self.assertEqual(hello["status"], "draft")
        self.assertEqual(hello["tags"], ["robotics"])
        self.assertEqual(payload["summary"]["status_counts"], {"draft": 2})
        self.assertEqual(payload["summary"]["total_posts"], 2)

        options = payload["options"]
        # Only the accepted claim is offered.
        self.assertEqual([row["id"] for row in options["claims"]], ["claim-1"])
        self.assertEqual([row["id"] for row in options["evidence"]], ["ev-1"])
        self.assertEqual([row["id"] for row in options["projects"]], ["proj-1"])

    def test_get_studio_uninitialized_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, public_layer=False)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/studio")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["initialized"])
        self.assertEqual(payload["posts"], [])
        self.assertEqual(payload["summary"]["total_posts"], 0)

    def test_get_studio_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/nobody/studio")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "profile_not_found")


class TestStudioInit(StudioTestBase):
    """POST /studio/init: idempotent public-layer creation."""

    def test_init_creates_public_layer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root, public_layer=False)
            client = self._client(root)
            before = client.get("/api/v1/profiles/alice/studio")
            response = client.post(
                "/api/v1/profiles/alice/studio/init",
                headers={"If-Match": before.headers["ETag"]},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["created_paths"])
            self.assertTrue((profile / "public-profile.yaml").exists())
            self.assertTrue((profile / "blog").is_dir())

            again = client.post("/api/v1/profiles/alice/studio/init")
            self.assertEqual(again.status_code, 200)
            self.assertEqual(again.json()["created_paths"], [])
            after = client.get("/api/v1/profiles/alice/studio")
            self.assertTrue(after.json()["initialized"])

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


class TestStudioBlogCrud(StudioTestBase):
    """Blog detail/create/save/check/publish with ETag semantics."""

    def test_get_post_detail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/studio/blog/hello")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["ETag"].startswith('W/"'))
        payload = response.json()
        self.assertEqual(payload["slug"], "hello")
        self.assertEqual(payload["title"], "First post")
        self.assertEqual(payload["status"], "draft")
        self.assertIn("Hello **world**.", payload["body"])
        self.assertFalse(payload["has_math"])
        self.assertEqual(payload["related_claims"], ["claim-1"])
        self.assertEqual(payload["meta"]["date"], "2026-09-10")

    def test_get_post_unknown_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/studio/blog/nope")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "blog_post_not_found")

    def test_create_post_201_and_persists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            before = client.get("/api/v1/profiles/alice/studio")
            response = client.post(
                "/api/v1/profiles/alice/studio/blog",
                json={"title": "New Post", "tags": ["note"]},
                headers={"If-Match": before.headers["ETag"]},
            )
            self.assertEqual(response.status_code, 201)
            payload = response.json()
            self.assertTrue(payload["ok"])
            post = payload["post"]
            self.assertEqual(post["title"], "New Post")
            self.assertEqual(post["status"], "draft")
            md_path = profile / "blog" / f"{post['slug']}.md"
            self.assertTrue(md_path.exists())
            self.assertIn("status: draft", md_path.read_text(encoding="utf-8"))

    def test_create_post_blank_title_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/blog",
                json={"title": "   "},
            )
        self.assertEqual(response.status_code, 422)

    def test_save_post_updates_meta_and_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            detail = client.get("/api/v1/profiles/alice/studio/blog/hello")
            etag = detail.headers["ETag"]
            response = client.post(
                "/api/v1/profiles/alice/studio/blog/hello/save",
                json={
                    "summary": "Updated summary.",
                    "tags": ["robotics", "demo"],
                    "body": "Edited body.\n",
                },
                headers={"If-Match": etag},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["ok"])
            post = payload["post"]
            self.assertEqual(post["summary"], "Updated summary.")
            self.assertEqual(post["tags"], ["robotics", "demo"])
            self.assertEqual(post["body"], "Edited body.\n")
            # Untouched meta fields survive (round-trip through full meta).
            self.assertEqual(post["related_claims"], ["claim-1"])
            self.assertNotEqual(response.headers["ETag"], etag)
            text = (profile / "blog" / "hello.md").read_text(encoding="utf-8")
            self.assertIn("Updated summary.", text)
            self.assertIn("Edited body.", text)

    def test_save_post_status_transition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            detail = client.get("/api/v1/profiles/alice/studio/blog/hello")
            response = client.post(
                "/api/v1/profiles/alice/studio/blog/hello/save",
                json={"status": "archived"},
                headers={"If-Match": detail.headers["ETag"]},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["post"]["status"], "archived")

    def test_save_post_invalid_status_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/blog/hello/save",
                json={"status": "review"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_blog_status")

    def test_save_post_etag_mismatch_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/blog/hello/save",
                json={"summary": "stale write"},
                headers={"If-Match": 'W/"stale"'},
            )
        self.assertEqual(response.status_code, 412)
        self.assertEqual(response.json()["code"], "etag_mismatch")
        self.assertTrue(response.headers["ETag"].startswith('W/"'))

    def test_check_reports_missing_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/blog/hello/check", json={}
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertFalse(payload["ok"])
            self.assertTrue(payload["errors"])

    def test_check_accepts_unsaved_edits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/blog/ready/check", json={}
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"], response.json())

    def test_publish_blocked_by_validation_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            detail = client.get("/api/v1/profiles/alice/studio/blog/hello")
            response = client.post(
                "/api/v1/profiles/alice/studio/blog/hello/publish",
                json={},
                headers={"If-Match": detail.headers["ETag"]},
            )
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json()["code"], "blog_publish_blocked")
            # Nothing was written: the post is still a draft on disk.
            detail = client.get("/api/v1/profiles/alice/studio/blog/hello")
            self.assertEqual(detail.json()["status"], "draft")

    def test_publish_sets_status_published(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            detail = client.get("/api/v1/profiles/alice/studio/blog/ready")
            response = client.post(
                "/api/v1/profiles/alice/studio/blog/ready/publish",
                json={},
                headers={"If-Match": detail.headers["ETag"]},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["post"]["status"], "published")
            text = (profile / "blog" / "ready.md").read_text(encoding="utf-8")
            self.assertIn("status: published", text)

    def test_publish_etag_mismatch_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/blog/ready/publish",
                json={},
                headers={"If-Match": 'W/"stale"'},
            )
        self.assertEqual(response.status_code, 412)
        self.assertEqual(response.json()["code"], "etag_mismatch")


class TestStudioCandidates(StudioTestBase):
    """Candidate preview + draft creation (rule fallback, no LLM)."""

    def test_preview_blog_from_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/candidates/preview",
                json={
                    "target": "blog",
                    "source": "evidence",
                    "evidence_id": "ev-1",
                },
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["kind"], "blog")
        candidate = payload["candidate"]
        self.assertEqual(candidate["title"], "Arm demo video")
        self.assertIn("What happened", candidate["body"])
        self.assertEqual(candidate["related_evidence"], ["ev-1"])

    def test_preview_resume_requires_claims_source_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/candidates/preview",
                json={
                    "target": "resume",
                    "source": "evidence",
                    "evidence_id": "ev-1",
                },
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_studio_candidate")

    def test_preview_project_requires_project_id_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/candidates/preview",
                json={"target": "project", "source": "claims", "claim_ids": ["claim-1"]},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_studio_candidate")

    def test_preview_unknown_evidence_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/candidates/preview",
                json={
                    "target": "blog",
                    "source": "evidence",
                    "evidence_id": "missing",
                },
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "studio_candidate_failed")

    def test_create_blog_draft_from_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            before = client.get("/api/v1/profiles/alice/studio")
            response = client.post(
                "/api/v1/profiles/alice/studio/candidates/create",
                json={
                    "target": "blog",
                    "source": "claims",
                    "claim_ids": ["claim-1"],
                },
                headers={"If-Match": before.headers["ETag"]},
            )
            self.assertEqual(response.status_code, 201)
            payload = response.json()
            self.assertEqual(payload["kind"], "blog")
            self.assertTrue(payload["slug"])
            md_path = profile / "blog" / f"{payload['slug']}.md"
            self.assertTrue(md_path.exists())
            text = md_path.read_text(encoding="utf-8")
            self.assertIn("status: draft", text)
            self.assertIn("claim-1", text)
            # The writeback is recorded to Agent Activity for provenance.
            activity_path = profile / "agent-activity.yaml"
            self.assertTrue(activity_path.exists())
            activity = yaml.safe_load(activity_path.read_text(encoding="utf-8"))
            items = activity.get("items") or []
            self.assertTrue(
                any(
                    item.get("source_ref") == "output_studio:blog_from_claims"
                    for item in items
                )
            )

    def test_create_resume_draft_preview_only_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/candidates/create",
                json={
                    "target": "resume",
                    "source": "claims",
                    "claim_ids": ["claim-1"],
                },
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "studio_draft_preview_only")

    def test_create_project_update_from_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/candidates/create",
                json={
                    "target": "project",
                    "source": "claims",
                    "claim_ids": ["claim-1"],
                    "project_id": "proj-1",
                },
            )
            self.assertEqual(response.status_code, 201)
            payload = response.json()
            self.assertEqual(payload["kind"], "project_update")
            projects = yaml.safe_load(
                (profile / "projects.yaml").read_text(encoding="utf-8")
            )
            updates = projects["projects"][0].get("draft_updates") or []
            self.assertEqual(len(updates), 1)
            self.assertEqual(updates[0]["status"], "draft")


class TestStudioJdMatch(StudioTestBase):
    """JD match: LLM degradation contract."""

    def test_jd_match_unavailable_without_llm_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/studio/jd-match",
                json={"resume_md": "# Resume", "jd_text": "Robotics engineer"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "studio_jd_match_unavailable")

    def test_jd_match_success_with_mocked_llm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            with (
                patch("nblane.core.llm.is_configured", return_value=True),
                patch(
                    "nblane.core.jd_match.analyze_jd",
                    return_value="## Match analysis\n\nStrong fit.",
                ),
            ):
                response = client.post(
                    "/api/v1/profiles/alice/studio/jd-match",
                    json={
                        "resume_md": "# Resume",
                        "jd_text": "Robotics engineer",
                    },
                )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Strong fit.", response.json()["analysis"])

    def test_jd_match_empty_inputs_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            with patch("nblane.core.llm.is_configured", return_value=True):
                response = client.post(
                    "/api/v1/profiles/alice/studio/jd-match",
                    json={"resume_md": "", "jd_text": "  "},
                )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_jd_match_request")


if __name__ == "__main__":
    unittest.main()
