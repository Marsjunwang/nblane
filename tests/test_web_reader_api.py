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

from nblane.core.auth import (
    AUTH_SESSION_COOKIE_NAME,
    hash_password,
    mint_auth_handoff_token,
    mint_reader_token,
)
from nblane.core.paper_library_workspace import PaperLibraryEventResult
from nblane.core.reader_actions import ReaderActionResult
from nblane.core.research_papers import (
    PaperSearchResult,
    PaperPage,
    PaperSegment,
    create_paper_annotation,
    import_paper_pdf,
    paper_pdf_asset_path,
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

    def _auth_file(self, root: Path) -> Path:
        path = root / "auth" / "users.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        password_hash = hash_password("secret", iterations=100_000, salt=b"0123456789abcdef")
        path.write_text(
            (
                "users:\n"
                "  alice:\n"
                "    display_name: Alice\n"
                f"    password_hash: {password_hash}\n"
                "    role: member\n"
                "    profiles:\n"
                "      - alice\n"
            ),
            encoding="utf-8",
        )
        return path

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
        self.assertEqual(payload.json()["settings"]["overscan_pages"], "auto")
        self.assertEqual(payload.json()["settings"]["render_cache_max_pages"], "auto")
        self.assertEqual(payload.json()["settings"]["reader_mode"], "pdf")
        self.assertEqual(payload.json()["settings"]["translation_layout"], "overlay")
        self.assertIn("outline", payload.json())
        self.assertFalse(payload.json()["settings"]["debug_overlay_enabled"])
        self.assertFalse(payload.json()["settings"]["full_translation_context"])
        self.assertEqual(payload.json()["settings"]["active_left_tab"], "outline")
        self.assertEqual(payload.json()["settings"]["translation_overflow_policy"], "fixed-expand")

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
                    section_path=[f"Section {index}"],
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

            response = client.get(
                f"/reader/api/{quote(source_id, safe='')}/payload?page=5&full_document=0"
            )
            payload = response.json()
            expanded = client.get(
                f"/reader/api/{quote(source_id, safe='')}/payload?page=5&pages=2,8&full_document=0"
            )
            expanded_payload = expanded.json()
            full = client.get(
                f"/reader/api/{quote(source_id, safe='')}/payload?page=5&full_translation=1"
            )
            full_payload = full.json()
            # Default (no full_document param) returns the whole document.
            default_resp = client.get(f"/reader/api/{quote(source_id, safe='')}/payload?page=5")
            default_payload = default_resp.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["context_window"]["pages"], [4, 5, 6])
        self.assertEqual({row["page"] for row in payload["segments"]}, {4, 5, 6})
        self.assertEqual({row["page"] for row in payload["translations"]}, {4, 5, 6})
        self.assertTrue(payload["outline"])
        self.assertIn("target_anchor_id", payload["outline"][0])
        self.assertNotIn("text", payload["outline"][0])
        self.assertNotIn(1, {row["page"] for row in payload["segments"]})
        self.assertEqual(expanded.status_code, 200)
        self.assertEqual(expanded_payload["context_window"]["pages"], [2, 4, 5, 6, 8])
        self.assertEqual({row["page"] for row in expanded_payload["segments"]}, {2, 4, 5, 6, 8})
        self.assertEqual(full.status_code, 200)
        self.assertEqual(full_payload["context_window"]["pages"], list(range(1, 9)))
        self.assertEqual({row["page"] for row in full_payload["segments"]}, set(range(1, 9)))
        self.assertTrue(full_payload["settings"]["full_translation_context"])
        self.assertEqual(default_resp.status_code, 200)
        self.assertEqual(default_payload["context_window"]["pages"], list(range(1, 9)))
        self.assertTrue(default_payload["settings"]["full_document_payload"])
        self.assertTrue(default_resp.headers.get("etag", "").startswith('W/"'))

    def test_payload_returns_304_when_etag_matches(self) -> None:
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

            first = client.get(f"/reader/api/{quote(source_id, safe='')}/payload?page=1")
            etag = first.headers.get("etag")
            second = client.get(
                f"/reader/api/{quote(source_id, safe='')}/payload?page=1",
                headers={"If-None-Match": etag or ""},
            )

        self.assertEqual(first.status_code, 200)
        self.assertTrue(etag and etag.startswith('W/"'))
        self.assertEqual(second.status_code, 304)
        self.assertEqual(second.headers.get("etag"), etag)

    def test_translations_bulk_returns_all_segments_with_etag(self) -> None:
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
                for index in range(1, 4)
            ]
            segments = [
                PaperSegment(
                    segment_id=f"seg:{index}",
                    source_id=source_id,
                    page=index,
                    order=index,
                    section_path=[f"Section {index}"],
                    text=f"Segment body {index}",
                    text_hash=text_hash(f"Segment body {index}"),
                )
                for index in range(1, 4)
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
                            "translated_text": f"译文 {segment.page}",
                            "rects": [{"x": 0.1, "y": 0.2, "w": 0.4, "h": 0.05, "page": segment.page}],
                        }
                        for segment in segments
                    ],
                )
            client = self._client(profile)
            client.cookies.set(
                "nblane_reader_session",
                mint_reader_token("local", "alice", source_id),
            )
            first = client.get(f"/reader/api/{quote(source_id, safe='')}/translations/bulk")
            etag = first.headers.get("etag")
            second = client.get(
                f"/reader/api/{quote(source_id, safe='')}/translations/bulk",
                headers={"If-None-Match": etag or ""},
            )

        self.assertEqual(first.status_code, 200)
        body = first.json()
        self.assertEqual(body["paper_id"], source_id)
        self.assertEqual(body["segment_count"], 3)
        self.assertEqual({seg["page"] for seg in body["segments"]}, {1, 2, 3})
        self.assertTrue(body["content_hash"])
        self.assertTrue(etag and etag.startswith('W/"'))
        self.assertEqual(second.status_code, 304)
        self.assertEqual(second.headers.get("etag"), etag)

    def test_translations_bulk_unauthorized_without_token(self) -> None:
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
            response = client.get(f"/reader/api/{quote(source_id, safe='')}/translations/bulk")

        self.assertEqual(response.status_code, 401)

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
        self.assertIn("skeletonWindowForPage", response.text)
        self.assertIn("pr-page-spacer", response.text)
        self.assertIn("window.pdfjsLib.renderTextLayer", response.text)
        self.assertIn("pr-action-status", response.text)
        self.assertIn("actionState", response.text)
        self.assertIn("setActionState", response.text)
        self.assertIn("startReaderTask", response.text)
        self.assertIn("watchReaderTask", response.text)
        self.assertIn("schedulePayloadRefresh", response.text)
        self.assertIn('params.set("pages", requestedPages.join(","))', response.text)
        self.assertIn('params.set("full_translation", "1")', response.text)
        self.assertIn("maybeRefreshTranslationProgress", response.text)
        self.assertIn("pagePreviewBatchLimit", response.text)
        self.assertIn("fetchTranslationsBulk", response.text)
        self.assertIn("hasBulkTranslationsLoaded", response.text)
        self.assertIn("translationProgressShell", response.text)
        self.assertIn("toggleCompareLock", response.text)
        self.assertIn("compareDualScrollLockEnabled", response.text)
        self.assertIn("prepare_reader_artifacts", response.text)
        self.assertIn("reader_preparation", response.text)
        self.assertIn("PDF ready", response.text)
        self.assertIn("Structured text ready", response.text)
        self.assertIn("Fallback text ready", response.text)
        self.assertIn("Preparation failed", response.text)
        self.assertIn("page_models", response.text)
        self.assertIn("outline", response.text)
        self.assertIn("pr-left-rail", response.text)
        self.assertIn("railTabButton(\"outline\"", response.text)
        self.assertIn("railTabButton(\"pages\"", response.text)
        self.assertIn("railTabButton(\"search\"", response.text)
        self.assertIn("data-rail-tab", response.text)
        self.assertIn("translation_units", response.text)
        self.assertIn("translationFlowHtml", response.text)
        self.assertIn("translationUnitGroups", response.text)
        self.assertIn("activeSegmentFromViewport", response.text)
        self.assertIn("buildAnchorIndex", response.text)
        self.assertIn("setActiveAnchor", response.text)
        self.assertIn("preferredTranslationClickPage", response.text)
        self.assertIn("lockUserAnchor", response.text)
        self.assertIn("userAnchorLocked", response.text)
        self.assertIn("userAnchorIntent", response.text)
        self.assertIn("performUserAnchorJump", response.text)
        self.assertIn("waitForScrollSettled", response.text)
        self.assertIn("translationHoverMuted", response.text)
        self.assertIn("viewportAnchorSyncMuted() || userAnchorLocked()", response.text)
        self.assertIn('action === "save_progress" || action === "reader_state_changed"', response.text)
        self.assertIn('emitAction("reader_state_changed", readerStatePayload())', response.text)
        self.assertIn("activeTranslationAnchorFromState", response.text)
        self.assertIn("unitPage === currentPage", response.text)
        self.assertIn("wrapBox.top - viewerBox.top", response.text)
        self.assertIn("renderTranslationPage", response.text)
        self.assertIn("translationOverflowPolicy", response.text)
        self.assertIn("fitTranslationBlocks", response.text)
        self.assertIn("debugOverlayEnabled", response.text)
        self.assertIn("debugOverlayActive", response.text)
        self.assertIn("showTranslationUnitDock", response.text)
        self.assertIn("translationPageBaseSize", response.text)
        self.assertIn("scaleForTranslationPage", response.text)
        self.assertIn("normalizedRect", response.text)
        self.assertIn("pr-translation-page-shell", response.text)
        self.assertIn("pr-translation-layer", response.text)
        self.assertIn("pr-translation-fallback", response.text)
        self.assertIn("layoutOverlayUnitsForPage", response.text)
        self.assertIn("fallbackUnitsForPage", response.text)
        self.assertIn("isPositionedTranslationScope", response.text)
        self.assertIn("!isPositionedTranslationScope(obj.scope_type) || !hasRectGeometry(obj)", response.text)
        self.assertIn("if (isPositionedTranslationScope(obj.scope_type)) return obj.display_source === true ? flowText(obj.source_text) : \"\";", response.text)
        self.assertIn('data-scope-type', response.text)
        self.assertIn('scope_strategy: "structure"', response.text)
        self.assertNotIn('if (text(obj.scope_type) === "layout") return "";', response.text)
        self.assertNotIn("pr-translation-block.layout.empty", response.text)
        self.assertNotIn(".layout.missing", response.text)
        self.assertNotIn(".layout.failed", response.text)
        self.assertIn("pollReaderTask(taskId, action), 2500", response.text)
        self.assertIn("scope_refs: isPositionedTranslationScope(scopeType)", response.text)
        self.assertIn("syncCompareScroll", response.text)
        self.assertIn("annotationPopover", response.text)
        self.assertIn('mode: "read"', response.text)
        self.assertIn("data-annotation-popover-edit", response.text)
        self.assertIn("dock_position", response.text)
        self.assertIn("dock_pinned", response.text)
        self.assertIn("dock_layout", response.text)
        self.assertIn("panelResize", response.text)
        self.assertIn("compare_split_ratio", response.text)
        self.assertIn("Analyze Paper", response.text)
        self.assertIn('data-action="analyzePaper"', response.text)
        self.assertIn('tabButton("translation"', response.text)
        self.assertIn('tabButton("review"', response.text)
        # Notes panel chips (color dot + tag chips + quote/note rendering)
        self.assertIn("pr-color-dot", response.text)
        self.assertIn("pr-tag-chip", response.text)
        self.assertIn("pr-quote-text", response.text)
        self.assertIn("pr-note-text", response.text)
        # Default to All (not current page) for notes filter
        self.assertIn("let notesFilterCurrentPage = false;", response.text)
        # Clickable cited refs in review panel
        self.assertIn("pr-ref-chip", response.text)
        self.assertIn("data-jump-ref", response.text)
        self.assertIn("data-jump-segment", response.text)
        self.assertIn("refButtonHtml", response.text)
        self.assertIn("refIdText", response.text)
        # PDF skeleton shimmer
        self.assertIn("startupPdfSkeletonHtml", response.text)
        self.assertIn("data-shell-placeholder", response.text)
        self.assertIn("pr-skeleton-shimmer", response.text)
        self.assertIn(".pr-page-wrap.loading::before", response.text)
        # Translation overlay CJK sizing / default page scale
        self.assertIn("font-size: clamp(.8rem, var(--pr-translation-font, 1rem), 1.85rem);", response.text)
        self.assertIn("const widthSpace = Math.max(220, rawWidth - 28);", response.text)
        self.assertIn("return Math.max(.35, Math.min(2.4, scale));", response.text)
        self.assertIn("let low = 10;", response.text)
        # Translation reader auto-fits container width on resize.
        self.assertIn("ensureTranslationResizeObserver", response.text)
        self.assertIn(".pr-workspace.reader-mode-translation .pr-translation-page-preview", response.text)
        self.assertNotIn('<button class="pr-button primary" data-action="translateFull"', response.text)
        self.assertNotIn('<button class="pr-button" data-action="ask"', response.text)
        self.assertNotIn('data-action="reviewCard"', response.text)
        self.assertNotIn('<div class="pr-panel-head">Debug</div>${debugPanelHtml()}', response.text)
        self.assertNotIn('create_chunk: "Chunk"', response.text)
        self.assertNotIn('create_citation: "Cite"', response.text)
        self.assertNotIn("Ask about this", response.text)
        self.assertNotIn("streamlit:setComponentValue", response.text)

    def test_paper_library_standalone_page_api_and_events(self) -> None:
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

            page = client.get("/paper-library?profile=alice")
            payload = client.get(
                "/api/research/alice/paper-library"
                "?detail_id=source%3Apaper%3Agrounded&focus=artifacts&action=run_extraction"
                "&return_to=overview&return_url=http%3A%2F%2F127.0.0.1%3A8503%2FResearch"
            )
            with (
                patch("nblane.core.research_papers.git_backup.record_change"),
                patch("nblane.core.research_sources.git_backup.record_change"),
            ):
                created = client.post(
                    "/api/research/alice/paper-library/events",
                    headers={"Origin": "http://testserver"},
                    json={
                        "action": "paper_library_create_collection",
                        "payload": {"title": "Workspace"},
                        "state": {"view": "all", "sort_mode": "recent"},
                    },
                )
                node_id = created.json()["result"]["changed"]["nodes"][0]
                moved = client.post(
                    "/api/research/alice/paper-library/events",
                    headers={"Origin": "http://testserver"},
                    json={
                        "action": "paper_library_drop_papers_to_collection",
                        "payload": {
                            "node_id": node_id,
                            "paper_ids": [source_id],
                        },
                        "state": {
                            "view": "all",
                            "node_id": node_id,
                            "detail_id": source_id,
                            "sort_mode": "recent",
                            "focus": "artifacts",
                            "action": "run_extraction",
                            "return_to": "overview",
                            "return_url": "http://127.0.0.1:8503/Research",
                        },
                    },
                )
            with patch(
                "nblane.core.paper_library_workspace.ensure_paper_reading_artifacts",
                return_value={
                    "source_id": source_id,
                    "ready": True,
                    "status": "ready",
                    "pages": 1,
                    "segments": 3,
                    "warnings": [],
                },
            ):
                extracted = client.post(
                    "/api/research/alice/paper-library/events",
                    headers={"Origin": "http://testserver"},
                    json={
                        "action": "paper_library_run_extraction",
                        "payload": {"paper_ids": [source_id]},
                        "state": {
                            "view": "needs_extraction",
                            "detail_id": source_id,
                            "focus": "artifacts",
                            "action": "run_extraction",
                        },
                    },
                )
            reader_token = client.post(
                f"/api/research/alice/papers/{quote(source_id, safe='')}/reader-token"
            )

        self.assertEqual(page.status_code, 200)
        self.assertIn("NBLANE_PAPER_LIBRARY_BOOTSTRAP", page.text)
        self.assertEqual(payload.status_code, 200)
        self.assertEqual(payload.json()["payload"]["metrics"]["papers"], 1)
        self.assertEqual(payload.json()["payload"]["focus"], "artifacts")
        self.assertEqual(payload.json()["payload"]["action"], "run_extraction")
        self.assertEqual(payload.json()["payload"]["return_to"], "overview")
        self.assertEqual(payload.json()["payload"]["return_url"], "http://127.0.0.1:8503/Research")
        self.assertEqual(created.status_code, 200)
        self.assertEqual(moved.status_code, 200)
        self.assertEqual(moved.json()["payload"]["active_node_id"], node_id)
        self.assertEqual(moved.json()["payload"]["detail"]["primary_node_id"], node_id)
        self.assertEqual(moved.json()["payload"]["focus"], "artifacts")
        self.assertEqual(moved.json()["payload"]["action"], "run_extraction")
        self.assertEqual(moved.json()["payload"]["return_to"], "overview")
        self.assertEqual(moved.json()["payload"]["return_url"], "http://127.0.0.1:8503/Research")
        self.assertEqual(extracted.status_code, 200)
        self.assertIn("Extraction ready", extracted.json()["result"]["message"])
        self.assertEqual(extracted.json()["result"]["data"]["extraction_summaries"][0]["segments"], 3)
        self.assertEqual(extracted.json()["payload"]["focus"], "artifacts")
        self.assertEqual(extracted.json()["payload"]["action"], "")
        self.assertEqual(reader_token.status_code, 200)
        self.assertIn("/reader/view/source%3Apaper%3Agrounded", reader_token.json()["reader_url"])

    def test_paper_library_standalone_requires_auth_cookie_when_auth_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.dict(
                os.environ,
                {
                    "NBLANE_AUTH_FILE": str(self._auth_file(root)),
                    "NBLANE_READER_TOKEN_SECRET": "test-secret",
                    "NBLANE_RESEARCH_ASSET_ROOT": str(root / "assets"),
                },
                clear=False,
            ):
                profile = self._profile(root)
                client = self._client(profile)

                page = client.get("/paper-library?profile=alice")
                payload = client.get("/api/research/alice/paper-library")

        self.assertEqual(page.status_code, 401)
        self.assertEqual(payload.status_code, 401)

    def test_paper_library_auth_handoff_sets_cookie_and_checks_profile_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.dict(
                os.environ,
                {
                    "NBLANE_AUTH_FILE": str(self._auth_file(root)),
                    "NBLANE_READER_TOKEN_SECRET": "test-secret",
                    "NBLANE_RESEARCH_ASSET_ROOT": str(root / "assets"),
                },
                clear=False,
            ):
                profile = self._profile(root)
                client = self._client(profile)
                handoff = mint_auth_handoff_token("alice")

                page = client.get(
                    f"/paper-library?profile=alice&auth_handoff={quote(handoff, safe='')}"
                )
                payload = client.get("/api/research/alice/paper-library")
                reader_token = client.post(
                    "/api/research/alice/papers/source%3Apaper%3Agrounded/reader-token"
                )
                forbidden = client.get("/paper-library?profile=bob")

        self.assertEqual(page.status_code, 200)
        self.assertIn(AUTH_SESSION_COOKIE_NAME, page.headers.get("set-cookie", ""))
        self.assertEqual(payload.status_code, 200)
        self.assertEqual(payload.json()["payload"]["metrics"]["papers"], 1)
        self.assertEqual(reader_token.status_code, 200)
        self.assertIn("/reader/view/source%3Apaper%3Agrounded", reader_token.json()["reader_url"])
        self.assertEqual(forbidden.status_code, 403)

    def test_paper_library_search_and_import_require_pdf_candidates(self) -> None:
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
            preflight = client.options(
                "/api/research/alice/paper-library/search",
                headers={
                    "Origin": "null",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )
            missing_query = client.post(
                "/api/research/alice/paper-library/search",
                headers={"Origin": "null"},
                json={"mode": "codex", "query": ""},
            )
            rows = [
                PaperSearchResult(
                    title="Portable PDF Candidate",
                    canonical_url="https://example.com/paper",
                    pdf_url="https://example.com/paper.pdf",
                    provider_refs=["openalex:anything"],
                    abstract="PDF-backed candidate from an arbitrary provider.",
                ),
                PaperSearchResult(
                    title="Metadata Only Candidate",
                    canonical_url="https://example.com/no-pdf",
                    provider_refs=["semantic_scholar:metadata"],
                ),
            ]

            self.assertEqual(preflight.status_code, 204)
            self.assertEqual(preflight.headers["access-control-allow-origin"], "null")
            self.assertEqual(missing_query.status_code, 400)
            self.assertEqual(missing_query.headers["access-control-allow-origin"], "null")

            with (
                patch("nblane.web_reader_api.search_papers_with_codex", return_value=rows) as search,
                patch("nblane.core.research_sources.git_backup.record_change"),
            ):
                found = client.post(
                    "/api/research/alice/paper-library/search",
                    headers={"Origin": "http://testserver"},
                    json={"mode": "codex", "query": "robot memory", "limit": 10},
                )
                candidates = found.json()["candidates"]
                imported = client.post(
                    "/api/research/alice/paper-library/import",
                    headers={"Origin": "http://testserver"},
                    json={
                        "candidates": candidates,
                        "selected_ids": [candidates[0]["candidate_id"]],
                        "download_pdf": False,
                    },
                )
            sources = load_research_sources(profile).by_id()

        self.assertEqual(found.status_code, 200)
        search.assert_called_once()
        self.assertEqual(search.call_args.kwargs["filters"]["codex_budget_mode"], "auto")
        self.assertEqual(search.call_args.kwargs["filters"]["codex_timeout_seconds"], 180.0)
        self.assertEqual(search.call_args.kwargs["filters"]["codex_idle_timeout_seconds"], 60.0)
        self.assertEqual(search.call_args.kwargs["filters"]["codex_reasoning_effort"], "medium")
        self.assertEqual(search.call_args.kwargs["filters"]["codex_search_depth"], "quick")
        self.assertEqual(search.call_args.kwargs["filters"]["codex_home_policy"], "default")
        self.assertEqual(search.call_args.kwargs["filters"]["provider_timeout_seconds"], 4.0)
        self.assertEqual([row["title"] for row in candidates], ["Portable PDF Candidate"])
        self.assertEqual(candidates[0]["provider_refs"], ["openalex:anything"])
        self.assertEqual(imported.status_code, 200)
        imported_ids = imported.json()["imported"]
        self.assertEqual(len(imported_ids), 1)
        self.assertIn(imported_ids[0], sources)
        self.assertEqual(sources[imported_ids[0]].metadata["open_access_pdf_url"], "https://example.com/paper.pdf")

    def test_paper_library_import_reports_pdf_download_warning(self) -> None:
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
            candidate = {
                "candidate_id": "candidate-slow",
                "title": "Slow Download Candidate",
                "canonical_url": "https://example.com/slow",
                "pdf_url": "https://example.com/slow.pdf",
            }
            with (
                patch("nblane.core.research_sources.git_backup.record_change"),
                patch("nblane.core.research_papers.download_paper_pdf", side_effect=TimeoutError("network too slow")),
            ):
                response = client.post(
                    "/api/research/alice/paper-library/import",
                    headers={"Origin": "http://testserver"},
                    json={
                        "candidates": [candidate],
                        "selected_ids": ["candidate-slow"],
                        "download_pdf": True,
                    },
                )
            body = response.json()
            sources = load_research_sources(profile).by_id()
            imported_id = body["imported"][0]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(body["warnings"])
        self.assertIn("PDF needs attention", body["message"])
        self.assertEqual(sources[imported_id].metadata["pdf_download_status"], "failed")

    def test_paper_library_import_url_creates_manual_paper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
                "NBLANE_DISABLE_NETWORK_LOOKUPS": "1",
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            with patch("nblane.core.research_sources.git_backup.record_change"):
                response = client.post(
                    "/api/research/alice/paper-library/import-url",
                    headers={"Origin": "http://testserver"},
                    json={
                        "url": "https://arxiv.org/abs/2401.12345",
                        "title": "Manual arXiv Paper",
                        "status": "reading",
                        "visibility": "private",
                        "download_pdf": False,
                    },
                )
            body = response.json()
            source_id = body["source_id"]
            source = load_research_sources(profile).by_id()[source_id]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["imported"], [source_id])
        self.assertEqual(body["payload"]["detail"]["source_id"], source_id)
        self.assertEqual(source.title, "Manual arXiv Paper")
        self.assertEqual(source.status, "reading")
        self.assertEqual(source.url, "https://arxiv.org/abs/2401.12345")
        self.assertEqual(source.metadata["open_access_pdf_url"], "https://arxiv.org/pdf/2401.12345")

    def test_paper_library_upload_creates_paper_source_with_pdf(self) -> None:
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
            unique_pdf = PDF_BYTES + b"\n%fresh-payload-" + os.urandom(4)
            with patch("nblane.core.research_sources.git_backup.record_change"):
                response = client.post(
                    "/api/research/alice/paper-library/upload",
                    headers={"Origin": "http://testserver"},
                    data={
                        "title": "Local Upload Paper",
                        "status": "reading",
                        "visibility": "private",
                    },
                    files={"file": ("local-upload.pdf", unique_pdf, "application/pdf")},
                )
            body = response.json()
            source_id = body["source_id"]
            source = load_research_sources(profile).by_id()[source_id]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["message"], "Uploaded and imported PDF.")
        self.assertFalse(body["duplicate"])
        self.assertEqual(body["payload"]["detail"]["source_id"], source_id)
        self.assertTrue(body["payload"]["detail"]["has_pdf"])
        self.assertEqual(source.title, "Local Upload Paper")
        self.assertEqual(source.status, "reading")
        self.assertEqual(source.metadata["pdf_download_status"], "downloaded")
        self.assertTrue(source.metadata["pdf_asset_ref"].endswith("local-upload.pdf"))

    def test_paper_library_upload_returns_existing_source_for_duplicate_pdf(self) -> None:
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
            with patch("nblane.core.research_sources.git_backup.record_change"):
                response = client.post(
                    "/api/research/alice/paper-library/upload",
                    headers={"Origin": "http://testserver"},
                    data={
                        "title": "Local Upload Paper",
                        "status": "reading",
                        "visibility": "private",
                    },
                    files={"file": ("local-upload.pdf", PDF_BYTES, "application/pdf")},
                )
            body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(body["duplicate"])
        self.assertIn("Already imported", body["message"])
        self.assertEqual(body["source_id"], "source:paper:grounded")

    def test_paper_library_pdf_upload_attaches_local_file(self) -> None:
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
            with patch("nblane.core.research_sources.git_backup.record_change"):
                response = client.post(
                    f"/api/research/alice/papers/{quote(source_id, safe='')}/pdf-upload",
                    headers={"Origin": "http://testserver"},
                    files={"file": ("local-paper.pdf", PDF_BYTES, "application/pdf")},
                )
            body = response.json()
            source = load_research_sources(profile).by_id()[source_id]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["message"], "Uploaded PDF.")
        self.assertTrue(body["payload"]["detail"]["has_pdf"])
        self.assertEqual(source.metadata["pdf_download_status"], "downloaded")
        self.assertEqual(source.metadata["pdf_download_error"], "")
        self.assertTrue(source.metadata["pdf_asset_ref"].endswith("local-paper.pdf"))

    def test_paper_library_codex_deep_search_uses_xhigh_and_auto_budget(self) -> None:
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
            rows = [
                PaperSearchResult(
                    title="Deep PDF Candidate",
                    canonical_url="https://example.com/deep",
                    pdf_url="https://example.com/deep.pdf",
                    provider_refs=["openreview"],
                )
            ]

            with patch("nblane.web_reader_api.search_papers_with_codex", return_value=rows) as search:
                found = client.post(
                    "/api/research/alice/paper-library/search",
                    headers={"Origin": "http://testserver"},
                    json={
                        "mode": "codex",
                        "query": "VLA steering",
                        "limit": 5,
                        "codex_search_depth": "deep",
                    },
                )

        self.assertEqual(found.status_code, 200)
        self.assertEqual(found.json()["codex_search_depth"], "deep")
        self.assertEqual(found.json()["codex_reasoning_effort"], "xhigh")
        self.assertEqual(found.json()["codex_home_policy"], "default")
        self.assertEqual(found.json()["codex_budget_mode"], "auto")
        self.assertEqual(found.json()["codex_timeout_seconds"], 220.0)
        self.assertEqual(found.json()["codex_idle_timeout_seconds"], 90.0)
        search.assert_called_once()
        self.assertEqual(search.call_args.kwargs["filters"]["codex_budget_mode"], "auto")
        self.assertEqual(search.call_args.kwargs["filters"]["codex_timeout_seconds"], 220.0)
        self.assertEqual(search.call_args.kwargs["filters"]["codex_reasoning_effort"], "xhigh")
        self.assertEqual(search.call_args.kwargs["filters"]["codex_search_depth"], "deep")
        self.assertEqual(search.call_args.kwargs["filters"]["codex_home_policy"], "default")

    def test_paper_library_codex_search_can_request_profile_codex_home(self) -> None:
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
            with patch("nblane.web_reader_api.search_papers_with_codex", return_value=[]) as search:
                found = client.post(
                    "/api/research/alice/paper-library/search",
                    headers={"Origin": "http://testserver"},
                    json={
                        "mode": "codex",
                        "query": "vla最新论文",
                        "limit": 1,
                        "codex_home_policy": "profile",
                    },
                )

        self.assertEqual(found.status_code, 200)
        self.assertEqual(found.json()["codex_home_policy"], "profile")
        self.assertEqual(found.json()["reply_language"], "zh")
        search.assert_called_once()
        self.assertEqual(search.call_args.kwargs["filters"]["codex_home_policy"], "profile")
        self.assertEqual(search.call_args.kwargs["filters"]["reply_language"], "zh")

    def test_paper_library_search_job_reports_progress_and_result(self) -> None:
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
            rows = [
                PaperSearchResult(
                    title="Job PDF Candidate",
                    canonical_url="https://example.com/job",
                    pdf_url="https://example.com/job.pdf",
                    provider_refs=["arxiv"],
                )
            ]

            with patch("nblane.web_reader_api.search_papers_with_codex", return_value=rows) as search:
                started = client.post(
                    "/api/research/alice/paper-library/search/jobs",
                    headers={"Origin": "http://testserver"},
                    json={"mode": "codex", "query": "robot memory", "limit": 5},
                )
                job_id = started.json()["job_id"]
                status = None
                for _ in range(30):
                    status = client.get(f"/api/research/alice/paper-library/search/jobs/{job_id}")
                    if status.json()["job"]["status"] == "done":
                        break
                    time.sleep(0.05)

        self.assertEqual(started.status_code, 200)
        self.assertIsNotNone(status)
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["job"]["status"], "done")
        self.assertIn("elapsed_ms", status.json()["job"])
        self.assertTrue(status.json()["job"]["events"])
        self.assertTrue(any(event.get("event") == "phase" for event in status.json()["job"]["events"]))
        self.assertEqual(status.json()["result"]["candidates"][0]["title"], "Job PDF Candidate")
        search.assert_called_once()

    def test_paper_library_search_job_stream_reports_progress_and_result(self) -> None:
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
            rows = [
                PaperSearchResult(
                    title="Stream PDF Candidate",
                    canonical_url="https://example.com/stream",
                    pdf_url="https://example.com/stream.pdf",
                    provider_refs=["arxiv"],
                )
            ]

            with patch("nblane.web_reader_api.search_papers_with_codex", return_value=rows):
                started = client.post(
                    "/api/research/alice/paper-library/search/jobs",
                    headers={"Origin": "http://testserver"},
                    json={"mode": "codex", "query": "robot memory", "limit": 5},
                )
                job_id = started.json()["job_id"]
                chunks: list[str] = []
                with client.stream(
                    "GET",
                    f"/api/research/alice/paper-library/search/jobs/{job_id}/stream",
                ) as stream:
                    self.assertEqual(stream.status_code, 200)
                    self.assertIn("text/event-stream", stream.headers.get("content-type", ""))
                    for text in stream.iter_text():
                        chunks.append(text)
                        if "event: result" in "".join(chunks):
                            break

        payload = "".join(chunks)
        self.assertIn("event: job", payload)
        self.assertIn("event: progress", payload)
        self.assertIn("event: result", payload)
        self.assertIn('"status":"done"', payload)
        self.assertIn("Stream PDF Candidate", payload)

    def test_paper_library_search_job_can_be_cancelled(self) -> None:
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

            def slow_search(_profile_path, _query, *, filters=None, **_kwargs):
                cancel_check = (filters or {}).get("_cancel_check")
                for _ in range(100):
                    if callable(cancel_check) and cancel_check():
                        return []
                    time.sleep(0.02)
                return []

            with patch("nblane.web_reader_api.search_papers_with_codex", side_effect=slow_search):
                started = client.post(
                    "/api/research/alice/paper-library/search/jobs",
                    headers={"Origin": "http://testserver"},
                    json={"mode": "codex", "query": "robot memory", "limit": 5},
                )
                job_id = started.json()["job_id"]
                cancelled = client.post(
                    f"/api/research/alice/paper-library/search/jobs/{job_id}/cancel",
                    headers={"Origin": "http://testserver"},
                    json={},
                )
                status = None
                for _ in range(30):
                    status = client.get(f"/api/research/alice/paper-library/search/jobs/{job_id}")
                    if status.json()["job"]["status"] == "cancelled":
                        break
                    time.sleep(0.05)

        self.assertEqual(started.status_code, 200)
        self.assertEqual(cancelled.status_code, 200)
        self.assertIsNotNone(status)
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["job"]["status"], "cancelled")
        self.assertTrue(any(event.get("event") == "cancel_requested" for event in status.json()["job"]["events"]))

    def test_paper_library_event_job_reports_translation_progress_and_payload(self) -> None:
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

            def fake_handle(profile_path, body, *, progress_callback=None):
                if progress_callback is not None:
                    progress_callback(
                        {
                            "phase": "translation",
                            "source_id": source_id,
                            "target_lang": "zh",
                            "mode": "missing_or_stale",
                            "scope": "structure",
                            "batches": 2,
                            "batches_completed": 1,
                            "segments_selected": 4,
                            "segments_processed": 2,
                            "updated": 1,
                            "warnings": 0,
                        }
                    )
                    progress_callback(
                        {
                            "phase": "translation",
                            "source_id": source_id,
                            "target_lang": "zh",
                            "mode": "missing_or_stale",
                            "scope": "structure",
                            "batches": 2,
                            "batches_completed": 2,
                            "segments_selected": 4,
                            "segments_processed": 4,
                            "updated": 2,
                            "warnings": 1,
                        }
                    )
                return PaperLibraryEventResult(
                    message="Translation retry finished: updated 2 row(s); 0 stale remaining.",
                    changed={"sources": [source_id], "translations": [source_id]},
                    next={"detail_id": source_id, "focus": "translations", "action": ""},
                    data={"translation_summaries": [{"updated": 2}]},
                )

            with patch("nblane.web_reader_api.handle_paper_library_event", side_effect=fake_handle) as handle:
                started = client.post(
                    "/api/research/alice/paper-library/events/jobs",
                    headers={"Origin": "http://testserver"},
                    json={
                        "action": "paper_library_retry_translation",
                        "payload": {"paper_ids": [source_id]},
                        "state": {"view": "all", "detail_id": source_id},
                    },
                )
                job_id = started.json()["job_id"]
                status = None
                for _ in range(30):
                    status = client.get(f"/api/research/alice/paper-library/events/jobs/{job_id}")
                    if status.json()["job"]["status"] == "done":
                        break
                    time.sleep(0.05)

        self.assertEqual(started.status_code, 200)
        self.assertIsNotNone(status)
        self.assertEqual(status.status_code, 200)
        data = status.json()
        self.assertEqual(data["job"]["status"], "done")
        self.assertEqual(data["job"]["batches"], 2)
        self.assertEqual(data["job"]["batches_completed"], 2)
        self.assertEqual(data["job"]["segments_processed"], 4)
        self.assertEqual(data["job"]["warning_count"], 1)
        self.assertIn("elapsed_ms", data["job"])
        self.assertEqual(data["result"]["result"]["message"], "Translation retry finished: updated 2 row(s); 0 stale remaining.")
        self.assertEqual(data["result"]["payload"]["detail_id"], source_id)
        handle.assert_called_once()
        self.assertTrue(callable(handle.call_args.kwargs["progress_callback"]))

    def test_dashboard_standalone_page_and_payload_api(self) -> None:
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

            page = client.get("/dashboard?profile=alice")
            payload = client.get("/api/dashboard/payload?profile=alice")

        self.assertEqual(page.status_code, 200)
        self.assertIn("Dashboard Canvas", page.text)
        self.assertEqual(payload.status_code, 200)
        data = payload.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["payload"]["profile"], "alice")
        self.assertIn("focus_path", data["payload"]["graph"])
        self.assertIn("contract", data["payload"]["graph"])

    def test_paper_library_api_previews_and_deletes_paper_record(self) -> None:
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
            asset_path = paper_pdf_asset_path(profile, source_id)

            with (
                patch("nblane.core.research_papers.git_backup.record_change"),
                patch("nblane.core.research_sources.git_backup.record_change"),
            ):
                preview = client.post(
                    "/api/research/alice/paper-library/events",
                    headers={"Origin": "http://testserver"},
                    json={
                        "action": "paper_library_delete_paper_preview",
                        "payload": {"paper_ids": [source_id]},
                        "state": {"view": "all", "detail_id": source_id, "sort_mode": "recent"},
                    },
                )
                deleted = client.post(
                    "/api/research/alice/paper-library/events",
                    headers={"Origin": "http://testserver"},
                    json={
                        "action": "paper_library_delete_paper_record",
                        "payload": {"paper_ids": [source_id], "confirm": source_id},
                        "state": {"view": "all", "detail_id": source_id, "sort_mode": "recent"},
                    },
                )
            sources = load_research_sources(profile).by_id()

            self.assertEqual(preview.status_code, 200)
            preview_payload = preview.json()["result"]["data"]["delete_preview"]
            self.assertTrue(preview_payload["can_delete"])
            self.assertEqual(preview_payload["totals"]["papers"], 1)
            self.assertGreaterEqual(preview_payload["totals"]["artifact_files"], 1)
            self.assertEqual(deleted.status_code, 200)
            self.assertEqual(deleted.json()["result"]["changed"]["sources"], [source_id])
            self.assertEqual(deleted.json()["result"]["changed"]["pdf_assets"], [])
            self.assertEqual(deleted.json()["payload"]["metrics"]["papers"], 0)
            self.assertNotIn(source_id, sources)
            self.assertTrue(asset_path.exists())

    def test_paper_library_api_blocks_referenced_delete(self) -> None:
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
            with (
                patch("nblane.core.research_papers.git_backup.record_change"),
                patch("nblane.core.research_sources.git_backup.record_change"),
            ):
                annotation = create_paper_annotation(profile, source_id, "Important quote.", page=1)
                preview = client.post(
                    "/api/research/alice/paper-library/events",
                    headers={"Origin": "http://testserver"},
                    json={
                        "action": "paper_library_delete_paper_preview",
                        "payload": {"paper_ids": [source_id]},
                        "state": {"view": "all", "detail_id": source_id, "sort_mode": "recent"},
                    },
                )
                blocked = client.post(
                    "/api/research/alice/paper-library/events",
                    headers={"Origin": "http://testserver"},
                    json={
                        "action": "paper_library_delete_paper_record",
                        "payload": {"paper_ids": [source_id], "confirm": source_id},
                        "state": {"view": "all", "detail_id": source_id, "sort_mode": "recent"},
                    },
                )
            sources = load_research_sources(profile).by_id()

            self.assertEqual(preview.status_code, 200)
            blockers = preview.json()["result"]["data"]["delete_preview"]["blocking_refs"]
            self.assertIn(annotation.id, [row["id"] for row in blockers])
            self.assertEqual(blocked.status_code, 400)
            self.assertIn("blocked", blocked.json()["detail"])
            self.assertIn(source_id, sources)

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

    def test_reader_task_supports_analyze_paper(self) -> None:
        source_id = "source:paper:grounded"
        task_id = "reader-task-analyze"
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
                    data={
                        "analysis": {
                            "scores": {"overall": 7},
                            "cited_segment_refs": ["seg:1"],
                        }
                    },
                    message="Analysis saved",
                ),
            ):
                started = client.post(
                    f"/reader/api/{quote(source_id, safe='')}/tasks",
                    headers={"Origin": "http://testserver"},
                    json={
                        "task_id": task_id,
                        "action": "analyze_paper",
                        "payload": {"page": 1, "event_id": "evt-analyze"},
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
        self.assertEqual(started.json()["task"]["action"], "analyze_paper")
        self.assertEqual(started.json()["task"]["event_id"], "evt-analyze")
        self.assertEqual(snap["status"], "done")
        self.assertTrue(snap["refresh"]["payload"])
        self.assertEqual(snap["progress"]["label"], "Analysis saved")

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
