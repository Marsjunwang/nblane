"""Tests for the Public Build slice (validate / build / publish-and-build).

Covers the overview read (init gate, validation, drafts, output-dir state,
ETag header), the synchronous static-site build (validation/visibility/base
-URL 422 gates, If-Match 412 contract, server-pinned output directory), the
publish-and-build flow (per-slug publish gate, partial-publish semantics),
the traversal-guarded artifact download endpoint, and the in-memory site
preview (page list JSON + per-page HTML). Builds land under the patched
``routes_v1.REPO_ROOT`` tmp dir — never the real ``dist/``.
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
        {"id": "proj-1", "title": "Robot Arm", "status": "published"},
    ],
}


def _template_profile(
    root: Path,
    name: str = "alice",
    *,
    public_layer: bool = True,
    visibility: str = "private",
) -> Path:
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
        return profile
    (profile / "claims.yaml").write_text(
        yaml.safe_dump(CLAIMS_FIXTURE, allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "evidence-pool.yaml").write_text(
        yaml.safe_dump(EVIDENCE_POOL_FIXTURE, allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "public-profile.yaml").write_text(
        yaml.safe_dump(
            {"profile": name, "visibility": visibility, "public_name": name},
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (profile / "projects.yaml").write_text(
        yaml.safe_dump(PROJECTS_FIXTURE, allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "outputs.yaml").write_text(
        yaml.safe_dump({"outputs": []}, allow_unicode=True),
        encoding="utf-8",
    )
    blog_dir = profile / "blog"
    blog_dir.mkdir(exist_ok=True)
    (blog_dir / "hello.md").write_text(BLOG_POST_FIXTURE, encoding="utf-8")
    (blog_dir / "ready.md").write_text(PUBLISHABLE_POST_FIXTURE, encoding="utf-8")
    return profile


class PublicBuildTestBase(unittest.TestCase):
    """Shared env patching: profile roots, build output root, git backup off.

    ``routes_v1.REPO_ROOT`` is patched to the tmp root so every build lands
    in ``<tmp>/dist/public/<name>`` — never the repository's real ``dist/``.
    """

    def _client(self, root: Path) -> TestClient:
        for target, value in (
            ("nblane.core.profile_io.PROFILES_DIR", root),
            ("nblane.core.io.PROFILES_DIR", root),
            ("nblane.web_api.routes_v1.REPO_ROOT", root),
        ):
            patcher = patch(target, value)
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

    @staticmethod
    def _overview_etag(client: TestClient) -> str:
        response = client.get("/api/v1/profiles/alice/public-build")
        assert response.status_code == 200
        return response.headers["ETag"]


class TestPublicBuildGet(PublicBuildTestBase):
    """GET /public-build: init gate, validation, drafts, build state, ETag."""

    def test_get_overview_initialized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/public-build")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["ETag"].startswith('W/"'))
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        self.assertTrue(payload["initialized"])
        self.assertTrue(payload["validation"]["ok"])
        self.assertEqual(payload["validation"]["errors"], [])
        drafts = {draft["slug"]: draft for draft in payload["drafts"]}
        self.assertEqual(sorted(drafts), ["hello", "ready"])
        self.assertEqual(drafts["ready"]["title"], "Ready post")
        build = payload["build"]
        self.assertFalse(build["exists"])
        self.assertEqual(build["total_files"], 0)
        self.assertTrue(build["output_dir"].endswith("dist/public/alice"))

    def test_get_overview_uninitialized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, public_layer=False)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/public-build")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["initialized"])
        self.assertIsNone(payload["validation"])
        self.assertEqual(payload["drafts"], [])

    def test_get_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/nobody/public-build")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "profile_not_found")


class TestPublicBuildBuild(PublicBuildTestBase):
    """POST /public-build/build: gates, 412 contract, pinned output dir."""

    def test_build_success_include_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            etag = self._overview_etag(client)
            response = client.post(
                "/api/v1/profiles/alice/public-build/build",
                json={"include_drafts": True, "base_url": ""},
                headers={"If-Match": etag},
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.headers["ETag"].startswith('W/"'))
            payload = response.json()
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["published"], [])
            self.assertIn("index.html", payload["pages"])
            self.assertGreater(payload["page_count"], 0)
            output_dir = root / "dist" / "public" / "alice"
            self.assertEqual(payload["output_dir"], str(output_dir.resolve()))
            self.assertTrue((output_dir / "index.html").is_file())
            self.assertTrue((output_dir / "assets" / "site.css").is_file())
            # The overview now reflects the built output.
            overview = client.get("/api/v1/profiles/alice/public-build").json()
            self.assertTrue(overview["build"]["exists"])
            self.assertTrue(overview["build"]["built_at"])
            artifact_paths = {a["path"] for a in overview["build"]["artifacts"]}
            self.assertIn("index.html", artifact_paths)

    def test_build_success_public_visibility(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, visibility="public")
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/public-build/build",
                json={"include_drafts": False, "base_url": "https://example.com/site"},
            )
            self.assertEqual(response.status_code, 200)
            output_dir = root / "dist" / "public" / "alice"
            self.assertTrue((output_dir / "sitemap.xml").is_file())
            sitemap = (output_dir / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("https://example.com/site", sitemap)

    def test_build_private_without_drafts_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, visibility="private")
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/public-build/build",
                json={"include_drafts": False, "base_url": ""},
            )
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json()["code"], "public_build_blocked")
            self.assertIn("visibility", response.json()["message"])
            self.assertFalse((root / "dist").exists())

    def test_build_validation_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            (profile / "public-profile.yaml").write_text(
                yaml.safe_dump({"profile": "alice", "visibility": "private"}),
                encoding="utf-8",
            )
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/public-build/build",
                json={"include_drafts": True, "base_url": ""},
            )
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json()["code"], "public_build_blocked")
            self.assertIn("public_name", response.json()["message"])
            self.assertFalse((root / "dist").exists())

    def test_build_invalid_base_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/public-build/build",
                json={"include_drafts": True, "base_url": "not-a-url"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "public_build_blocked")
        self.assertIn("base-url", response.json()["message"])

    def test_build_etag_mismatch_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/public-build/build",
                json={"include_drafts": True, "base_url": ""},
                headers={"If-Match": 'W/"stale"'},
            )
        self.assertEqual(response.status_code, 412)
        self.assertEqual(response.json()["code"], "etag_mismatch")
        self.assertTrue(response.headers["ETag"].startswith('W/"'))

    def test_build_uninitialized_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, public_layer=False)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/public-build/build",
                json={"include_drafts": True, "base_url": ""},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "public_layer_not_initialized")


class TestPublicBuildPublishAndBuild(PublicBuildTestBase):
    """POST /public-build/publish-and-build: per-slug gate, then build."""

    def test_publish_and_build_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            etag = self._overview_etag(client)
            response = client.post(
                "/api/v1/profiles/alice/public-build/publish-and-build",
                json={"slugs": ["ready"], "include_drafts": True, "base_url": ""},
                headers={"If-Match": etag},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["published"], ["ready"])
            text = (profile / "blog" / "ready.md").read_text(encoding="utf-8")
            self.assertIn("status: published", text)
            self.assertTrue((root / "dist" / "public" / "alice" / "index.html").is_file())
            overview = client.get("/api/v1/profiles/alice/public-build").json()
            self.assertEqual(
                [draft["slug"] for draft in overview["drafts"]], ["hello"]
            )

    def test_publish_and_build_empty_slugs_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/public-build/publish-and-build",
                json={"slugs": [], "include_drafts": True, "base_url": ""},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_public_publish")

    def test_publish_and_build_blocked_slug_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/public-build/publish-and-build",
                json={"slugs": ["hello"], "include_drafts": True, "base_url": ""},
            )
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json()["code"], "public_publish_failed")
            self.assertIn("hello", response.json()["message"])
            # The failed slug stays a draft and nothing is built.
            text = (profile / "blog" / "hello.md").read_text(encoding="utf-8")
            self.assertIn("status: draft", text)
            self.assertFalse((root / "dist").exists())

    def test_publish_and_build_unknown_slug_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/public-build/publish-and-build",
                json={"slugs": ["ghost"], "include_drafts": True, "base_url": ""},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "public_publish_failed")
        self.assertIn("ghost", response.json()["message"])

    def test_publish_and_build_etag_mismatch_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/public-build/publish-and-build",
                json={"slugs": ["ready"], "include_drafts": True, "base_url": ""},
                headers={"If-Match": 'W/"stale"'},
            )
            self.assertEqual(response.status_code, 412)
            self.assertEqual(response.json()["code"], "etag_mismatch")
            text = (profile / "blog" / "ready.md").read_text(encoding="utf-8")
            self.assertIn("status: draft", text)


class TestPublicBuildArtifacts(PublicBuildTestBase):
    """GET /public-build/artifacts/{path}: download with traversal guard."""

    @staticmethod
    def _build(client: TestClient) -> None:
        response = client.post(
            "/api/v1/profiles/alice/public-build/build",
            json={"include_drafts": True, "base_url": ""},
        )
        assert response.status_code == 200

    def test_artifact_served_after_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            self._build(client)
            response = client.get(
                "/api/v1/profiles/alice/public-build/artifacts/index.html"
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("text/html", response.headers["Content-Type"])
            self.assertIn("<html", response.text)
            css = client.get(
                "/api/v1/profiles/alice/public-build/artifacts/assets/site.css"
            )
            self.assertEqual(css.status_code, 200)

    def test_artifact_missing_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            self._build(client)
            response = client.get(
                "/api/v1/profiles/alice/public-build/artifacts/nope.txt"
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "public_build_artifact_not_found")

    def test_artifact_no_build_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get(
                "/api/v1/profiles/alice/public-build/artifacts/index.html"
            )
        self.assertEqual(response.status_code, 404)

    def test_artifact_traversal_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            self._build(client)
            secret = (profile / "claims.yaml").read_text(encoding="utf-8")
            for sneaky in (
                "..%2F..%2Fclaims.yaml",
                "%2E%2E%2F%2E%2E%2Fclaims.yaml",
                "..%2F..%2F..%2Fpyproject.toml",
            ):
                response = client.get(
                    f"/api/v1/profiles/alice/public-build/artifacts/{sneaky}"
                )
                self.assertEqual(response.status_code, 404, sneaky)
                self.assertNotIn(secret, response.text)


class TestPublicBuildPreview(PublicBuildTestBase):
    """GET /public-build/preview[...]: page list JSON + per-page HTML."""

    def test_preview_page_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/public-build/preview")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["include_drafts"])
        pages = {page["path"]: page for page in payload["pages"]}
        self.assertIn("index.html", pages)
        self.assertIn("warnings", payload)

    def test_preview_page_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get(
                "/api/v1/profiles/alice/public-build/preview/page",
                params={"path": "index.html", "include_drafts": True},
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["Content-Type"])
        self.assertIn("<html", response.text)
        self.assertIn("alice", response.text)

    def test_preview_page_unknown_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get(
                "/api/v1/profiles/alice/public-build/preview/page",
                params={"path": "ghost/index.html"},
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "public_preview_page_not_found")

    def test_preview_uninitialized_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, public_layer=False)
            client = self._client(root)
            for url in (
                "/api/v1/profiles/alice/public-build/preview",
                "/api/v1/profiles/alice/public-build/preview/page",
            ):
                response = client.get(url)
                self.assertEqual(response.status_code, 422, url)
                self.assertEqual(response.json()["code"], "public_layer_not_initialized")


if __name__ == "__main__":
    unittest.main()
