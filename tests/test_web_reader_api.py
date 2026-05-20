"""Tests for the FastAPI Paper Reader sidecar."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

from fastapi.testclient import TestClient

from nblane.core.auth import mint_reader_token
from nblane.core.reader_actions import ReaderActionResult
from nblane.core.research_papers import (
    PaperPage,
    PaperSegment,
    import_paper_pdf,
    save_paper_pages,
    save_paper_segments,
    text_hash,
    upsert_paper_translations,
)
from nblane.core.research_sources import (
    ResearchSourceInbox,
    add_research_source,
    load_research_sources,
    save_research_sources,
)
from nblane.web_reader_api import app

PDF_BYTES = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>
endobj
trailer
<< /Root 1 0 R >>
%%EOF
"""


class TestWebReaderApi(unittest.TestCase):
    def _profile(self, root: Path) -> Path:
        profile = root / "alice"
        profile.mkdir()
        source_id = "source:paper:grounded"
        inbox = ResearchSourceInbox(profile="alice")
        add_research_source(
            inbox,
            "Grounded Claims",
            source_id=source_id,
            kind="paper",
            visibility="private",
        )
        with patch("nblane.core.research_sources.git_backup.record_change"):
            save_research_sources(profile, inbox)
        with (
            patch.dict(os.environ, {"NBLANE_RESEARCH_ASSET_ROOT": str(root / "assets")}, clear=False),
            patch("nblane.core.research_sources.git_backup.record_change"),
        ):
            import_paper_pdf(profile, source_id, PDF_BYTES, "paper.pdf")
        with patch("nblane.core.research_papers.git_backup.record_change"):
            save_paper_pages(
                profile,
                source_id,
                [PaperPage(source_id=source_id, page=1, text="Page 1", text_hash=text_hash("Page 1"))],
            )
        return profile

    def _client(self, profile: Path) -> TestClient:
        patcher = patch("nblane.web_reader_api.profile_dir", return_value=profile)
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)

    def test_view_token_sets_cookie_and_payload_uses_cookie(self) -> None:
        source_id = "source:paper:grounded"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            token = mint_reader_token("local", "alice", source_id)

            response = client.get(
                f"/reader/view/{quote(source_id, safe='')}?token={quote(token, safe='')}",
                follow_redirects=False,
            )
            payload = client.get(f"/reader/api/{quote(source_id, safe='')}/payload")

        self.assertEqual(response.status_code, 200)
        self.assertIn("nblane_reader_session", response.headers.get("set-cookie", ""))
        self.assertIn("readerToken", response.text)
        self.assertIn("X-Reader-Token", response.text)
        self.assertEqual(payload.status_code, 200)
        self.assertEqual(payload.json()["page_previews"], [])
        self.assertEqual(payload.json()["pdf_url"], f"/reader/api/{quote(source_id, safe='')}/pdf")
        self.assertIn("reader_preparation", payload.json())
        self.assertEqual(payload.json()["settings"]["overscan_pages"], 3)
        self.assertEqual(payload.json()["settings"]["render_cache_max_pages"], 36)

    def test_payload_uses_current_page_window_for_reader_context(self) -> None:
        source_id = "source:paper:grounded"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            pages = [
                PaperPage(source_id=source_id, page=index, text=f"Page {index}", text_hash=text_hash(f"Page {index}"))
                for index in range(1, 9)
            ]
            segments = [
                PaperSegment(
                    segment_id=f"seg:{index}",
                    source_id=source_id,
                    page=index,
                    order=index,
                    text=f"Segment {index}",
                    text_hash=text_hash(f"Segment {index}"),
                )
                for index in range(1, 9)
            ]
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_pages(profile, source_id, pages)
                save_paper_segments(profile, source_id, segments)
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "segment_id": segment.segment_id,
                            "source_hash": segment.text_hash,
                            "source_text": segment.text,
                            "target_lang": "zh",
                            "translated_text": f"zh {segment.page}",
                        }
                        for segment in segments
                    ],
                )
            client = self._client(profile)
            client.cookies.set(
                "nblane_reader_session",
                mint_reader_token("local", "alice", source_id),
            )

            response = client.get(f"/reader/api/{quote(source_id, safe='')}/payload?page=5")
            payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["context_window"]["pages"], [4, 5, 6])
        self.assertEqual({row["page"] for row in payload["segments"]}, {4, 5, 6})
        self.assertEqual({row["page"] for row in payload["translations"]}, {4, 5, 6})
        self.assertNotIn(1, {row["page"] for row in payload["segments"]})

    def test_payload_accepts_reader_token_query_fallback(self) -> None:
        source_id = "source:paper:grounded"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            token = mint_reader_token("local", "alice", source_id)

            payload = client.get(
                f"/reader/api/{quote(source_id, safe='')}/payload?reader_token={quote(token, safe='')}"
            )

        self.assertEqual(payload.status_code, 200)
        self.assertEqual(payload.json()["source"]["id"], source_id)

    def test_view_without_token_or_cookie_is_401(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            response = client.get("/reader/view/source%3Apaper%3Agrounded")

        self.assertEqual(response.status_code, 401)

    def test_view_with_cookie_renders_standalone_reader_html(self) -> None:
        source_id = "source:paper:grounded"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            client.cookies.set(
                "nblane_reader_session",
                mint_reader_token("local", "alice", source_id),
            )
            response = client.get(f"/reader/view/{quote(source_id, safe='')}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("/reader/assets/pdf.min.js", response.text)
        self.assertIn("source:paper:grounded", response.text)
        self.assertIn("for (let pageNumber = 1; pageNumber <= count", response.text)
        self.assertIn("window.pdfjsLib.renderTextLayer", response.text)
        self.assertIn("pr-action-status", response.text)
        self.assertIn("actionState", response.text)
        self.assertIn("setActionState", response.text)
        self.assertIn("startReaderTask", response.text)
        self.assertIn("watchReaderTask", response.text)
        self.assertIn("prepare_reader_artifacts", response.text)
        self.assertIn("reader_preparation", response.text)
        self.assertIn("PDF ready", response.text)
        self.assertIn("Structured text ready", response.text)
        self.assertIn("Fallback text ready", response.text)
        self.assertIn("Preparation failed", response.text)
        self.assertIn("translation_units", response.text)
        self.assertIn("renderTranslationPage", response.text)
        self.assertIn("syncCompareScroll", response.text)
        self.assertIn("annotationPopover", response.text)
        self.assertIn("panelResize", response.text)
        self.assertIn("compare_split_ratio", response.text)
        self.assertIn("Deep Read", response.text)
        self.assertNotIn('tabButton("translation"', response.text)
        self.assertNotIn("streamlit:setComponentValue", response.text)

    def test_pdf_range_and_page_preview(self) -> None:
        source_id = "source:paper:grounded"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            token = mint_reader_token("local", "alice", source_id)
            client.cookies.set("nblane_reader_session", token)

            pdf = client.get(
                f"/reader/api/{quote(source_id, safe='')}/pdf",
                headers={"Range": "bytes=0-3"},
            )
            with patch(
                "nblane.web_reader_api.render_paper_page_preview",
                return_value={"page": 1, "data_url": "data:image/png;base64,x"},
            ) as preview:
                page_preview = client.get(f"/reader/api/{quote(source_id, safe='')}/page-preview/1")

        self.assertEqual(pdf.status_code, 206)
        self.assertEqual(pdf.headers["content-range"], f"bytes 0-3/{len(PDF_BYTES)}")
        self.assertEqual(pdf.content, PDF_BYTES[:4])
        self.assertEqual(page_preview.status_code, 200)
        self.assertEqual(page_preview.json()["page"], 1)
        preview.assert_called_once()

    def test_mutating_endpoint_rejects_cross_origin(self) -> None:
        source_id = "source:paper:grounded"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            token = mint_reader_token("local", "alice", source_id)
            client.cookies.set("nblane_reader_session", token)

            rejected = client.post(
                f"/reader/api/{quote(source_id, safe='')}/progress",
                headers={"Origin": "http://evil.example"},
                json={"page": 2},
            )
            accepted = client.post(
                f"/reader/api/{quote(source_id, safe='')}/progress",
                headers={"Origin": "http://testserver"},
                json={"page": 2},
            )
            source = load_research_sources(profile).by_id()[source_id]

        self.assertEqual(rejected.status_code, 403)
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(source.metadata["last_read_page"], 2)

    def test_reader_task_endpoints_run_snapshot_and_sse(self) -> None:
        source_id = "source:paper:grounded"
        task_id = "reader-task-api-progress"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            token = mint_reader_token("local", "alice", source_id)
            client.cookies.set("nblane_reader_session", token)

            with patch(
                "nblane.core.reader_tasks.handle_reader_action",
                return_value=ReaderActionResult(
                    data={"answer": "Because."},
                    message="Answered.",
                    changed_ids={"note": "x"},
                ),
            ):
                started = client.post(
                    f"/reader/api/{quote(source_id, safe='')}/tasks",
                    headers={"Origin": "http://testserver"},
                    json={
                        "task_id": task_id,
                        "action": "ask_paper",
                        "payload": {"question": "Why?", "event_id": "evt-task-api"},
                    },
                )
                snap = {}
                for _ in range(20):
                    status = client.get(f"/reader/api/{quote(source_id, safe='')}/tasks/{task_id}")
                    snap = status.json()
                    if snap.get("status") in {"done", "failed", "cancelled"}:
                        break
                    time.sleep(0.02)
                events = client.get(f"/reader/api/{quote(source_id, safe='')}/tasks/{task_id}/events")

        self.assertEqual(started.status_code, 202)
        self.assertTrue(started.json()["ok"])
        self.assertEqual(started.json()["task"]["task_id"], task_id)
        self.assertEqual(started.json()["task"]["event_id"], "evt-task-api")
        self.assertEqual(snap["status"], "done")
        self.assertTrue(snap["refresh"]["payload"])
        self.assertEqual(snap["result"]["data"], {"answer": "Because."})
        self.assertEqual(snap["changed_ids"], {"note": "x"})
        self.assertEqual(events.status_code, 200)
        self.assertIn("text/event-stream", events.headers["content-type"])
        self.assertIn("event: snapshot", events.text)
        self.assertIn('"status": "done"', events.text)

    def test_reader_task_unknown_returns_lost_snapshot(self) -> None:
        source_id = "source:paper:grounded"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            client.cookies.set(
                "nblane_reader_session",
                mint_reader_token("local", "alice", source_id),
            )

            response = client.get(f"/reader/api/{quote(source_id, safe='')}/tasks/missing-task")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "failed")
        self.assertIn("lost", response.json()["error"])

    def test_reader_task_supports_prepare_reader_artifacts(self) -> None:
        source_id = "source:paper:grounded"
        task_id = "reader-task-prepare"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            client.cookies.set(
                "nblane_reader_session",
                mint_reader_token("local", "alice", source_id),
            )

            with patch(
                "nblane.core.reader_tasks.handle_reader_action",
                return_value=ReaderActionResult(
                    data={"summary": {"ready": True, "status": "ready", "pages": 1, "segments": 2}},
                    message="Structured text ready",
                ),
            ):
                started = client.post(
                    f"/reader/api/{quote(source_id, safe='')}/tasks",
                    headers={"Origin": "http://testserver"},
                    json={
                        "task_id": task_id,
                        "action": "prepare_reader_artifacts",
                        "payload": {"page": 1, "prefer_grobid": True, "event_id": "evt-prepare"},
                    },
                )
                snap = {}
                for _ in range(20):
                    status = client.get(f"/reader/api/{quote(source_id, safe='')}/tasks/{task_id}")
                    snap = status.json()
                    if snap.get("status") in {"done", "failed", "cancelled"}:
                        break
                    time.sleep(0.02)

        self.assertEqual(started.status_code, 202)
        self.assertEqual(started.json()["task"]["action"], "prepare_reader_artifacts")
        self.assertEqual(started.json()["task"]["event_id"], "evt-prepare")
        self.assertEqual(snap["status"], "done")
        self.assertTrue(snap["refresh"]["payload"])
        self.assertEqual(snap["progress"]["label"], "Structured text ready")

    def test_reader_task_start_validates_action_and_identity(self) -> None:
        source_id = "source:paper:grounded"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            client.cookies.set(
                "nblane_reader_session",
                mint_reader_token("local", "alice", source_id),
            )

            denied_action = client.post(
                f"/reader/api/{quote(source_id, safe='')}/tasks",
                headers={"Origin": "http://testserver"},
                json={"action": "page_changed", "payload": {"page": 2}},
            )
            denied_source = client.post(
                f"/reader/api/{quote(source_id, safe='')}/tasks",
                headers={"Origin": "http://testserver"},
                json={"action": "ask_paper", "payload": {"source_id": "source:paper:other", "question": "Why?"}},
            )

        self.assertEqual(denied_action.status_code, 400)
        self.assertEqual(denied_source.status_code, 400)

    def test_reader_task_mutations_require_session_and_same_origin(self) -> None:
        source_id = "source:paper:grounded"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            no_cookie = client.post(
                f"/reader/api/{quote(source_id, safe='')}/tasks",
                headers={"Origin": "http://testserver"},
                json={"action": "ask_paper", "payload": {"question": "Why?"}},
            )
            client.cookies.set(
                "nblane_reader_session",
                mint_reader_token("local", "alice", source_id),
            )
            rejected_post = client.post(
                f"/reader/api/{quote(source_id, safe='')}/tasks",
                headers={"Origin": "http://evil.example"},
                json={"action": "ask_paper", "payload": {"question": "Why?"}},
            )
            rejected_delete = client.delete(
                f"/reader/api/{quote(source_id, safe='')}/tasks/not-here",
                headers={"Origin": "http://evil.example"},
            )

        self.assertEqual(no_cookie.status_code, 401)
        self.assertEqual(rejected_post.status_code, 403)
        self.assertEqual(rejected_delete.status_code, 403)

    def test_reader_task_delete_cancels_unknown_as_lost_snapshot(self) -> None:
        source_id = "source:paper:grounded"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            client.cookies.set(
                "nblane_reader_session",
                mint_reader_token("local", "alice", source_id),
            )

            response = client.delete(
                f"/reader/api/{quote(source_id, safe='')}/tasks/not-here",
                headers={"Origin": "http://testserver"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(response.json()["task"]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
