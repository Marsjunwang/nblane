"""Contract tests for the SPA research source intake API (web_api/research.py).

Profiles live in a tmp root (PROFILES_DIR patched in paths / profile_io /
io / research_sources / project_board); connector adapters are stubbed so
nothing touches the network.
"""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import auth as auth_core
from nblane.core.research_connectors import ADAPTERS, ConnectorAdapter, ConnectorItem
from nblane.core.research_sources import load_research_sources
from nblane.web_api import create_app
from nblane.web_api import jobs as jobs_module

PASSWORD = "correct horse battery staple"

SOURCES = {
    "schema_version": "1.0",
    "profile": "alice",
    "sources": [
        {
            "id": "src:001",
            "kind": "paper",
            "title": "SLAM survey",
            "status": "reading",
            "url": "https://example.org/slam",
            "captured_at": "2026-09-18",
            "tags": ["robotics"],
            "metadata": {"last_read_page": 3, "last_read_at": "2026-09-18T10:00:00+00:00"},
        },
        {
            "id": "src:002",
            "kind": "web",
            "title": "Grasp tooling post",
            "status": "inbox",
            "url": "https://blog.example.com/grasp/",
            "captured_at": "2026-09-19",
        },
    ],
}


class StubAdapter(ConnectorAdapter):
    provider = "arxiv"

    def __init__(self, items=None, error: Exception | None = None) -> None:
        self.items = items or []
        self.error = error
        self.calls = 0

    def discover(self, config):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return list(self.items)


def _write_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    (profile / "research").mkdir(parents=True)
    (profile / "research" / "sources.yaml").write_text(
        yaml.safe_dump(dict(SOURCES, profile=name), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (profile / "kanban.md").write_text(
        f"# {name} · Kanban\n\n## Doing\n\n- (empty)\n\n---\n\n## Done\n\n- (empty)\n\n---\n\n"
        "## Queue\n\n- (empty)\n\n---\n\n## Someday / Maybe\n\n- (empty)\n\n---\n",
        encoding="utf-8",
    )
    return profile


def _write_users(path: Path) -> Path:
    stored = auth_core.hash_password(PASSWORD, iterations=100_000, salt=b"research-test-salt")
    path.write_text(
        yaml.safe_dump(
            {
                "users": {
                    "wang": {
                        "display_name": "Wang",
                        "password_hash": stored,
                        "role": "member",
                        "profiles": ["wang"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return path


class ResearchApiBase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.root = self.base / "profiles"
        self.root.mkdir()
        self.pdir = _write_profile(self.root)
        for target in (
            "nblane.core.paths.PROFILES_DIR",
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
            "nblane.core.research_sources.PROFILES_DIR",
            "nblane.core.project_board.PROFILES_DIR",
        ):
            patcher = patch(target, self.root)
            patcher.start()
            self.addCleanup(patcher.stop)
        # Never record git backups from tests.
        backup = patch("nblane.core.git_backup.record_change", return_value=None)
        backup.start()
        self.addCleanup(backup.stop)

    def client(self, *, auth: bool = False) -> TestClient:
        env = {"NBLANE_AUTH_FILE": ""}
        if auth:
            _write_profile(self.root, "wang")
            env = {
                "NBLANE_AUTH_FILE": str(_write_users(self.base / "users.yaml")),
                "NBLANE_AUTH_SESSION_SECRET": "research-test-secret",
            }
        env_patch = patch.dict(os.environ, env)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        return TestClient(create_app())

    def stub_adapter(self, adapter: StubAdapter) -> StubAdapter:
        patcher = patch.dict(ADAPTERS, {"arxiv": adapter})
        patcher.start()
        self.addCleanup(patcher.stop)
        return adapter

    def wait_job(self, client: TestClient, job_id: str, timeout: float = 10.0) -> dict:
        deadline = time.monotonic() + timeout
        while True:
            payload = client.get(f"/api/v1/profiles/alice/jobs/{job_id}").json()
            if payload["job"]["status"] in jobs_module.FINAL_STATUSES:
                return payload
            if time.monotonic() > deadline:
                self.fail(f"job {job_id} did not finish")
            time.sleep(0.05)


class TestSourceInbox(ResearchApiBase):
    def test_list_returns_all_sources_with_counts_and_filters(self) -> None:
        client = self.client()
        response = client.get("/api/v1/profiles/alice/research/sources")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 2)
        self.assertEqual([row["id"] for row in body["sources"]], ["src:002", "src:001"])
        self.assertEqual(body["status_counts"], {"reading": 1, "inbox": 1})
        self.assertIn("paper", body["options"]["kinds"])
        self.assertTrue(body["sources"][0]["etag"].startswith('W/"'))
        self.assertTrue(response.headers["ETag"].startswith('W/"'))

        filtered = client.get("/api/v1/profiles/alice/research/sources?status=reading&kind=paper").json()
        self.assertEqual([row["id"] for row in filtered["sources"]], ["src:001"])
        self.assertEqual(filtered["total"], 2)  # counts stay unfiltered
        searched = client.get("/api/v1/profiles/alice/research/sources?q=grasp").json()
        self.assertEqual([row["id"] for row in searched["sources"]], ["src:002"])

    def test_unknown_profile_404_and_bad_name_400(self) -> None:
        client = self.client()
        self.assertEqual(client.get("/api/v1/profiles/nobody/research/sources").status_code, 404)
        self.assertEqual(client.get("/api/v1/profiles/..%2Fetc/research/sources").status_code, 404)
        self.assertEqual(client.get("/api/v1/profiles/a%5Cb/research/sources").status_code, 400)

    def test_create_source_persists_manual_origin(self) -> None:
        client = self.client()
        response = client.post(
            "/api/v1/profiles/alice/research/sources",
            json={
                "title": "Diffusion policy",
                "url": "https://arxiv.org/abs/2303.04137",
                "kind": "paper",
                "tags": ["policy", "diffusion"],
                "summary": "Visuomotor policy learning.",
                "visibility": "public",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        source = response.json()["source"]
        self.assertEqual(source["origin"], "manual")
        self.assertEqual(source["status"], "inbox")
        stored = load_research_sources(self.pdir).by_id()[source["id"]]
        self.assertEqual(stored.tags, ["policy", "diffusion"])
        self.assertEqual(stored.visibility, "public")

    def test_create_duplicate_url_409(self) -> None:
        client = self.client()
        response = client.post(
            "/api/v1/profiles/alice/research/sources",
            # Canonical match: trailing slash and host case differ.
            json={"title": "Same post", "url": "https://BLOG.example.com/grasp"},
        )
        self.assertEqual(response.status_code, 409)
        body = response.json()
        self.assertEqual(body["code"], "duplicate_research_source")
        self.assertEqual(body["duplicate_source_id"], "src:002")
        self.assertEqual(len(load_research_sources(self.pdir).sources), 2)

    def test_create_validation_422(self) -> None:
        client = self.client()
        blank = client.post("/api/v1/profiles/alice/research/sources", json={"title": ""})
        self.assertEqual(blank.status_code, 422)
        bad_kind = client.post(
            "/api/v1/profiles/alice/research/sources", json={"title": "x", "kind": "video"}
        )
        self.assertEqual(bad_kind.status_code, 422)
        self.assertEqual(bad_kind.json()["code"], "invalid_research_source")

    def test_patch_updates_fields_and_keeps_reader_state(self) -> None:
        client = self.client()
        listing = client.get("/api/v1/profiles/alice/research/sources").json()
        etag = next(row["etag"] for row in listing["sources"] if row["id"] == "src:001")
        response = client.patch(
            "/api/v1/profiles/alice/research/sources/src:001",
            json={"status": "summarized", "tags": ["robotics", "slam"], "visibility": "public"},
            headers={"If-Match": etag},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["source"]["status"], "summarized")
        stored = load_research_sources(self.pdir).by_id()["src:001"]
        self.assertEqual(stored.tags, ["robotics", "slam"])
        self.assertEqual(stored.metadata.get("last_read_page"), 3)
        self.assertEqual(stored.title, "SLAM survey")

    def test_patch_stale_etag_412_and_reader_progress_does_not_invalidate(self) -> None:
        client = self.client()
        listing = client.get("/api/v1/profiles/alice/research/sources").json()
        etag = next(row["etag"] for row in listing["sources"] if row["id"] == "src:001")
        # Passive Reader progress write: must not invalidate the row ETag.
        inbox = load_research_sources(self.pdir)
        inbox.by_id()["src:001"].metadata["last_read_page"] = 9
        from nblane.core.research_sources import save_research_sources

        save_research_sources(self.pdir, inbox)
        ok = client.patch(
            "/api/v1/profiles/alice/research/sources/src:001",
            json={"title": "SLAM survey (2026)"},
            headers={"If-Match": etag},
        )
        self.assertEqual(ok.status_code, 200, ok.text)
        stale = client.patch(
            "/api/v1/profiles/alice/research/sources/src:001",
            json={"title": "Another"},
            headers={"If-Match": etag},
        )
        self.assertEqual(stale.status_code, 412)
        self.assertEqual(stale.json()["source"]["title"], "SLAM survey (2026)")

    def test_patch_unknown_404_bad_status_422_duplicate_url_409(self) -> None:
        client = self.client()
        self.assertEqual(
            client.patch("/api/v1/profiles/alice/research/sources/nope", json={"status": "inbox"}).status_code,
            404,
        )
        bad = client.patch("/api/v1/profiles/alice/research/sources/src:001", json={"status": "done"})
        self.assertEqual(bad.status_code, 422)
        dup = client.patch(
            "/api/v1/profiles/alice/research/sources/src:001",
            json={"url": "https://blog.example.com/grasp"},
        )
        self.assertEqual(dup.status_code, 409)
        self.assertEqual(dup.json()["duplicate_source_id"], "src:002")

    def test_create_linked_task(self) -> None:
        client = self.client()
        response = client.post("/api/v1/profiles/alice/research/sources/src:002/task")
        self.assertEqual(response.status_code, 201, response.text)
        self.assertIn("Grasp tooling post", response.json()["title"])
        kanban = (self.pdir / "kanban.md").read_text(encoding="utf-8")
        self.assertIn("Grasp tooling post", kanban)


class TestConnectors(ResearchApiBase):
    def _save_connector(self, client: TestClient, **extra) -> str:
        response = client.put(
            "/api/v1/profiles/alice/research/connectors",
            json={"provider": "arxiv", "connector_id": "arxiv:vla", "query": "vla", **extra},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return "arxiv:vla"

    def test_get_empty_and_upsert(self) -> None:
        client = self.client()
        empty = client.get("/api/v1/profiles/alice/research/connectors").json()
        self.assertEqual(empty["connectors"], [])
        self.assertIn("arxiv", empty["providers"])
        self._save_connector(client, options={"limit": 5})
        body = client.get("/api/v1/profiles/alice/research/connectors").json()
        self.assertEqual(body["connectors"][0]["id"], "arxiv:vla")
        self.assertEqual(body["connectors"][0]["options"], {"limit": 5})

    def test_upsert_rejects_secrets_and_unknown_provider(self) -> None:
        client = self.client()
        secret = client.put(
            "/api/v1/profiles/alice/research/connectors",
            json={"provider": "github", "options": {"auth": {"api_token": "x"}}},
        )
        self.assertEqual(secret.status_code, 422)
        self.assertEqual(secret.json()["code"], "connector_secret_rejected")
        self.assertFalse((self.pdir / "research" / "connectors.yaml").exists())
        unknown = client.put("/api/v1/profiles/alice/research/connectors", json={"provider": "rss"})
        self.assertEqual(unknown.status_code, 422)

    def test_preview_job_marks_duplicates_and_import_job_writes(self) -> None:
        self.stub_adapter(
            StubAdapter(
                items=[
                    ConnectorItem(provider="arxiv", title="VLA paper", url="https://arxiv.org/abs/1", kind="paper", external_id="1"),
                    ConnectorItem(provider="arxiv", title="SLAM survey", url="https://example.org/slam", kind="paper", external_id="2"),
                ]
            )
        )
        client = self.client()
        connector_id = self._save_connector(client)
        created = client.post(f"/api/v1/profiles/alice/research/connectors/{connector_id}/preview")
        self.assertEqual(created.status_code, 202, created.text)
        final = self.wait_job(client, created.json()["job_id"])
        self.assertEqual(final["job"]["status"], "done", final)
        preview = final["result"]
        self.assertEqual(preview["discovered"], 2)
        self.assertEqual(preview["skipped"], 1)
        fresh = [row for row in preview["candidates"] if not row["duplicate"]["is_duplicate"]]
        self.assertEqual(len(fresh), 1)
        # Preview never writes source facts.
        self.assertEqual(len(load_research_sources(self.pdir).sources), 2)

        imported = client.post(
            f"/api/v1/profiles/alice/research/connectors/{connector_id}/import",
            json={"fingerprints": [fresh[0]["fingerprint"]]},
        )
        self.assertEqual(imported.status_code, 202, imported.text)
        done = self.wait_job(client, imported.json()["job_id"])
        self.assertEqual(done["job"]["status"], "done", done)
        self.assertEqual(done["result"]["imported"], 1)
        sources = load_research_sources(self.pdir).sources
        self.assertEqual(len(sources), 3)
        self.assertEqual(sources[-1].origin, "connector")

    def test_preview_network_failure_is_structured(self) -> None:
        self.stub_adapter(StubAdapter(error=OSError("Network is unreachable")))
        client = self.client()
        connector_id = self._save_connector(client)
        created = client.post(f"/api/v1/profiles/alice/research/connectors/{connector_id}/preview")
        final = self.wait_job(client, created.json()["job_id"])
        self.assertEqual(final["job"]["status"], "failed")
        self.assertEqual(final["job"]["error"]["code"], "connector_unreachable")

    def test_unknown_connector_404_and_bad_target_422(self) -> None:
        client = self.client()
        self.assertEqual(client.post("/api/v1/profiles/alice/research/connectors/nope/preview").status_code, 404)
        connector_id = self._save_connector(client)
        bad = client.post(
            f"/api/v1/profiles/alice/research/connectors/{connector_id}/import",
            json={"fingerprints": ["x"], "target": {"kind": "collection", "node_id": "missing"}},
        )
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(bad.json()["code"], "invalid_import_target")

    def test_manual_preview_and_import(self) -> None:
        client = self.client()
        raw = "https://example.org/new-post\nhttps://blog.example.com/grasp"
        preview = client.post(
            "/api/v1/profiles/alice/research/connectors/manual/preview",
            json={"provider": "x_twitter", "raw_items": raw},
        )
        self.assertEqual(preview.status_code, 200, preview.text)
        body = preview.json()
        self.assertEqual(body["discovered"], 2)
        self.assertEqual(body["skipped"], 1)
        pick = [row["fingerprint"] for row in body["candidates"] if row["selected"]]
        result = client.post(
            "/api/v1/profiles/alice/research/connectors/manual/import",
            json={"provider": "x_twitter", "raw_items": raw, "fingerprints": pick},
        )
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["imported"], 1)
        self.assertEqual(len(load_research_sources(self.pdir).sources), 3)
        none = client.post(
            "/api/v1/profiles/alice/research/connectors/manual/import",
            json={"provider": "x_twitter", "raw_items": raw, "fingerprints": []},
        )
        self.assertEqual(none.status_code, 422)


class TestResearchAIConfig(ResearchApiBase):
    def test_get_put_roundtrip_only_research_actions(self) -> None:
        client = self.client()
        body = client.get("/api/v1/profiles/alice/research/ai-config").json()
        actions = {row["action"]: row for row in body["actions"]}
        self.assertIn("research.paper_translate", actions)
        self.assertTrue(all(name.startswith("research.") for name in actions))
        self.assertEqual(actions["research.paper_qa"]["default_backend"], "codex")

        saved = client.put(
            "/api/v1/profiles/alice/research/ai-config",
            json={"actions": {"research.paper_translate": {"backend": "llm", "llm_model": "qwen-plus"}}},
        )
        self.assertEqual(saved.status_code, 200, saved.text)
        row = next(r for r in saved.json()["actions"] if r["action"] == "research.paper_translate")
        self.assertEqual((row["backend"], row["llm_model"]), ("llm", "qwen-plus"))
        prefs = yaml.safe_load((self.pdir / "web-preferences.yaml").read_text(encoding="utf-8"))
        self.assertEqual(prefs["ai"]["actions"]["research.paper_translate"]["llm_model"], "qwen-plus")

        foreign = client.put(
            "/api/v1/profiles/alice/research/ai-config",
            json={"actions": {"kanban.subtasks": {"backend": "codex"}}},
        )
        self.assertEqual(foreign.status_code, 422)
        bad_backend = client.put(
            "/api/v1/profiles/alice/research/ai-config",
            json={"actions": {"research.paper_qa": {"backend": "gemini"}}},
        )
        self.assertEqual(bad_backend.status_code, 422)

    def test_codex_effort_roundtrip_and_validation(self) -> None:
        client = self.client()
        saved = client.put(
            "/api/v1/profiles/alice/research/ai-config",
            json={
                "actions": {
                    "research.paper_deep_read_codex": {
                        "codex_model": "gpt-6.1-sol",
                        "codex_effort": "medium",
                    }
                }
            },
        )
        self.assertEqual(saved.status_code, 200, saved.text)
        row = next(r for r in saved.json()["actions"] if r["action"] == "research.paper_deep_read_codex")
        self.assertEqual((row["codex_model"], row["codex_effort"]), ("gpt-6.1-sol", "medium"))
        prefs = yaml.safe_load((self.pdir / "web-preferences.yaml").read_text(encoding="utf-8"))
        self.assertEqual(prefs["ai"]["actions"]["research.paper_deep_read_codex"]["codex_effort"], "medium")
        self.assertIn("gpt-6.1-sol", saved.json()["codex_model_suggestions"])

        bad_effort = client.put(
            "/api/v1/profiles/alice/research/ai-config",
            json={"actions": {"research.paper_deep_read_codex": {"codex_effort": "max"}}},
        )
        self.assertEqual(bad_effort.status_code, 422)


class TestResearchAuth(ResearchApiBase):
    def test_unauthenticated_401_and_foreign_profile_403(self) -> None:
        client = self.client(auth=True)
        self.assertEqual(client.get("/api/v1/profiles/alice/research/sources").status_code, 401)
        login = client.post("/api/v1/auth/login", json={"username": "wang", "password": PASSWORD})
        self.assertEqual(login.status_code, 200)
        for method, url, payload in (
            ("get", "/api/v1/profiles/alice/research/sources", None),
            ("post", "/api/v1/profiles/alice/research/sources", {"title": "x"}),
            ("patch", "/api/v1/profiles/alice/research/sources/src:001", {"status": "inbox"}),
            ("put", "/api/v1/profiles/alice/research/connectors", {"provider": "arxiv"}),
            ("put", "/api/v1/profiles/alice/research/ai-config", {"actions": {}}),
        ):
            response = getattr(client, method)(url, **({"json": payload} if payload is not None else {}))
            self.assertEqual(response.status_code, 403, f"{method} {url}")
        own = client.get("/api/v1/profiles/wang/research/sources")
        self.assertEqual(own.status_code, 200)


if __name__ == "__main__":
    unittest.main()
