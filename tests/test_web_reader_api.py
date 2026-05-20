"""Tests for the FastAPI Paper Reader sidecar."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

from fastapi.testclient import TestClient

from nblane.core.auth import mint_reader_token
from nblane.core.research_papers import (
    PaperPage,
    import_paper_pdf,
    save_paper_pages,
    text_hash,
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

        self.assertEqual(response.status_code, 303)
        self.assertIn("nblane_reader_session", response.headers.get("set-cookie", ""))
        self.assertEqual(payload.status_code, 200)
        self.assertEqual(payload.json()["page_previews"], [])
        self.assertEqual(payload.json()["pdf_url"], f"/reader/api/{quote(source_id, safe='')}/pdf")
        self.assertEqual(payload.json()["settings"]["overscan_pages"], 3)
        self.assertEqual(payload.json()["settings"]["render_cache_max_pages"], 36)

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


if __name__ == "__main__":
    unittest.main()
