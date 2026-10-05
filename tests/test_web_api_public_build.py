"""Tests for the public-site console API (``/profiles/{name}/public-site``).

Covers the overview (init gate, intro from the master resume, post rows
with their public/live state, works, Chinese validation messages, live
diff), the settings switches, per-post public toggles, the works list
(If-Match 412), work media upload, deploy (never includes drafts, keeps the
previous build) + rollback, and the in-memory preview. Deploys land under
the patched ``routes_v1.REPO_ROOT`` tmp dir — never the real ``dist/``.
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



BASE = "/api/v1/profiles/alice/public-site"


def _write(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _read(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


class TestPublicSiteOverview(PublicBuildTestBase):
    def test_overview_initialized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            resume = _read(profile / "resume-source.yaml")
            resume["basics"].update({"title": "Robot engineer", "phone": "13800000000"})
            resume["summary"] = "Builds robots."
            _write(profile / "resume-source.yaml", resume)
            client = self._client(root)
            response = client.get(BASE)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["initialized"])
        self.assertEqual(payload["visibility"], "private")
        self.assertFalse(payload["settings"]["show_phone"])
        self.assertFalse(payload["settings"]["show_projects"])
        self.assertEqual(payload["intro"]["title"], "Robot engineer")
        self.assertEqual(payload["intro"]["summary"], "Builds robots.")
        self.assertTrue(payload["intro"]["has_resume"])
        posts = {row["slug"]: row for row in payload["posts"]}
        self.assertEqual(sorted(posts), ["hello", "ready"])
        self.assertFalse(posts["ready"]["public"])
        self.assertFalse(posts["ready"]["live"])
        self.assertEqual(payload["projects_count"], 1)
        live = payload["live"]
        self.assertFalse(live["exists"])
        self.assertFalse(live["has_previous"])
        self.assertTrue(live["output_dir"].endswith("dist/public/alice"))
        self.assertIn("index.html", [row["path"] for row in live["added"]])

    def test_overview_uninitialized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, public_layer=False)
            response = self._client(root).get(BASE)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["initialized"])
        self.assertIsNone(response.json()["live"])

    def test_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            response = self._client(root).get("/api/v1/profiles/nobody/public-site")
        self.assertEqual(response.status_code, 404)

    def test_validation_errors_are_chinese(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            _write(profile / "outputs.yaml", {"outputs": [{"id": "w1", "status": "published"}]})
            payload = self._client(root).get(BASE).json()
        self.assertTrue(payload["errors"])
        self.assertTrue(any("作品「w1」" in e and "缺少必填字段" in e for e in payload["errors"]), payload["errors"])


class TestPublicSiteSettingsAndPosts(PublicBuildTestBase):
    def test_settings_merge_keeps_other_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.patch(
                f"{BASE}/settings",
                json={"show_email": True, "visibility": "public", "base_url": "https://example.com/"},
            )
            self.assertEqual(response.status_code, 200, response.text)
            payload = response.json()
            self.assertTrue(payload["settings"]["show_email"])
            self.assertFalse(payload["settings"]["show_phone"])
            self.assertEqual(payload["settings"]["base_url"], "https://example.com")
            self.assertEqual(payload["visibility"], "public")
            data = _read(profile / "public-profile.yaml")
            self.assertEqual(data["public_name"], "alice")
            self.assertTrue(data["site"]["show_email"])

    def test_settings_invalid_base_url_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            response = self._client(root).patch(f"{BASE}/settings", json={"base_url": "ftp://x"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_base_url")

    def test_post_toggle_publishes_and_unpublishes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.put(f"{BASE}/posts/ready", json={"public": True})
            self.assertEqual(response.status_code, 200, response.text)
            posts = {row["slug"]: row for row in response.json()["posts"]}
            self.assertTrue(posts["ready"]["public"])
            self.assertIn("status: published", (profile / "blog" / "ready.md").read_text(encoding="utf-8"))
            response = client.put(f"{BASE}/posts/ready", json={"public": False})
            posts = {row["slug"]: row for row in response.json()["posts"]}
            self.assertFalse(posts["ready"]["public"])
            self.assertIn("status: draft", (profile / "blog" / "ready.md").read_text(encoding="utf-8"))

    def test_post_toggle_blocked_by_publish_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            response = self._client(root).put(f"{BASE}/posts/hello", json={"public": True})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "post_not_publishable")
        self.assertIn("这篇还不能公开", response.json()["message"])

    def test_post_toggle_unknown_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            response = self._client(root).put(f"{BASE}/posts/ghost", json={"public": True})
        self.assertEqual(response.status_code, 404)

    def test_library_private_post_is_reported_and_toggled_public(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            text = (profile / "blog" / "ready.md").read_text(encoding="utf-8")
            (profile / "blog" / "ready.md").write_text(
                text.replace("status: draft", "status: published"), encoding="utf-8"
            )
            _write(
                profile / "public-library.yaml",
                {
                    "version": 1,
                    "profile": "alice",
                    "nodes": [
                        {"id": "root", "type": "root", "title": "Public Library"},
                        {"id": "post_ready", "type": "post", "title": "Ready post", "parent_id": "root",
                         "visibility": "private", "ref": "blog/ready.md"},
                    ],
                },
            )
            client = self._client(root)
            posts = {row["slug"]: row for row in client.get(BASE).json()["posts"]}
            self.assertTrue(posts["ready"]["library_hidden"])
            self.assertFalse(posts["ready"]["public"])
            response = client.put(f"{BASE}/posts/ready", json={"public": True})
            posts = {row["slug"]: row for row in response.json()["posts"]}
            self.assertTrue(posts["ready"]["public"])
            nodes = _read(profile / "public-library.yaml")["nodes"]
            self.assertEqual(nodes[1]["visibility"], "public")


class TestPublicSiteWorks(PublicBuildTestBase):
    WORK = {
        "title": "Grasp demo",
        "type": "video",
        "year": "2026",
        "video": "https://www.bilibili.com/video/BV1xx411c7mD",
        "links": [{"label": "论文", "url": "https://arxiv.org/abs/1"}],
        "status": "published",
    }

    def test_works_save_assigns_ids_and_writes_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            etag = client.get(BASE).json()["works_etag"]
            response = client.put(f"{BASE}/works", json={"works": [self.WORK]}, headers={"If-Match": etag})
            self.assertEqual(response.status_code, 200, response.text)
            works = response.json()["works"]
            self.assertEqual(len(works), 1)
            self.assertTrue(works[0]["id"])
            self.assertEqual(works[0]["links"], [{"label": "论文", "url": "https://arxiv.org/abs/1"}])
            row = _read(profile / "outputs.yaml")["outputs"][0]
            self.assertEqual(row["links"], {"论文": "https://arxiv.org/abs/1"})
            self.assertEqual(row["video"], self.WORK["video"])

    def test_works_stale_etag_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            response = self._client(root).put(
                f"{BASE}/works", json={"works": [self.WORK]}, headers={"If-Match": '"stale"'}
            )
        self.assertEqual(response.status_code, 412)

    def test_works_require_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            response = self._client(root).put(f"{BASE}/works", json={"works": [{"title": " "}]})
        self.assertEqual(response.status_code, 422)

    def test_work_media_upload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.post(
                f"{BASE}/works/media", files={"file": ("cover.png", b"\x89PNG fake", "image/png")}
            )
            self.assertEqual(response.status_code, 200, response.text)
            rel = response.json()["path"]
            self.assertTrue(rel.startswith("media/works/cover-"))
            self.assertTrue((profile / rel).is_file())
            bad = client.post(f"{BASE}/works/media", files={"file": ("x.exe", b"MZ", "application/octet-stream")})
            self.assertEqual(bad.status_code, 422)


class TestPublicSiteDeploy(PublicBuildTestBase):
    def _public(self, root: Path) -> Path:
        profile = _template_profile(root, visibility="public")
        text = (profile / "blog" / "ready.md").read_text(encoding="utf-8")
        (profile / "blog" / "ready.md").write_text(text.replace("status: draft", "status: published"), encoding="utf-8")
        return profile

    def test_deploy_builds_published_only_and_keeps_previous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._public(root)
            client = self._client(root)
            response = client.post(f"{BASE}/deploy")
            self.assertEqual(response.status_code, 200, response.text)
            live = root / "dist" / "public" / "alice"
            self.assertTrue((live / "blog" / "ready" / "index.html").is_file())
            self.assertFalse((live / "blog" / "hello").exists())
            self.assertFalse((live / "projects").exists())
            overview = client.get(BASE).json()
            self.assertTrue(overview["live"]["exists"])
            self.assertTrue(overview["live"]["in_sync"], overview["live"])
            posts = {row["slug"]: row for row in overview["posts"]}
            self.assertTrue(posts["ready"]["live"])
            # A second deploy keeps the first one for rollback.
            client.put(f"{BASE}/posts/ready", json={"public": False})
            self.assertFalse(client.get(BASE).json()["live"]["in_sync"])
            self.assertEqual(client.post(f"{BASE}/deploy").status_code, 200)
            self.assertFalse((live / "blog" / "ready").exists())
            self.assertTrue(client.get(BASE).json()["live"]["has_previous"])
            self.assertEqual(client.post(f"{BASE}/rollback").status_code, 200)
            self.assertTrue((live / "blog" / "ready" / "index.html").is_file())

    def test_deploy_private_site_blocked_in_chinese(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            # The overview reports the private gate before the deploy button.
            self.assertTrue(any("网站公开" in e for e in client.get(BASE).json()["errors"]))
            response = client.post(f"{BASE}/deploy")
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json()["code"], "deploy_blocked")
            self.assertIn("网站公开", response.json()["message"])
            self.assertFalse((root / "dist").exists())

    def test_rollback_without_previous_409(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._public(root)
            response = self._client(root).post(f"{BASE}/rollback")
        self.assertEqual(response.status_code, 409)

    def test_deploy_uninitialized_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, public_layer=False)
            response = self._client(root).post(f"{BASE}/deploy")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "public_layer_not_initialized")


class TestPublicSitePreview(PublicBuildTestBase):
    def test_preview_defaults_to_live_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            live_pages = {row["path"] for row in client.get(f"{BASE}/preview").json()["pages"]}
            draft_pages = {
                row["path"]
                for row in client.get(f"{BASE}/preview", params={"include_drafts": True}).json()["pages"]
            }
        self.assertIn("index.html", live_pages)
        self.assertNotIn("blog/ready/index.html", live_pages)
        self.assertIn("blog/ready/index.html", draft_pages)

    def test_preview_page_html_and_unknown_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get(f"{BASE}/preview/page", params={"path": "index.html"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("text/html", response.headers["Content-Type"])
            self.assertIn("<html", response.text)
            missing = client.get(f"{BASE}/preview/page", params={"path": "ghost/index.html"})
            self.assertEqual(missing.status_code, 404)

    def test_preview_uninitialized_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, public_layer=False)
            client = self._client(root)
            for url in (f"{BASE}/preview", f"{BASE}/preview/page"):
                response = client.get(url)
                self.assertEqual(response.status_code, 422, url)


if __name__ == "__main__":
    unittest.main()
