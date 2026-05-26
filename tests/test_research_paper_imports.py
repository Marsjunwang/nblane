"""Tests for the High-priority paper-import improvements.

Covers:
- Crossref / arXiv metadata enrichment (with cache + opt-out env).
- Title-similarity duplicate detection.
- ``upload_paper_library_pdf`` SHA fingerprint reuse.
- ``/papers/{id}/pdf-retry`` endpoint behavior.
- Structured error responses on PDF upload + URL import.
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

from fastapi.testclient import TestClient

from nblane.core.research_papers import (
    PaperImportError,
    PaperSearchResult,
    _metadata_cache_clear,
    _result_from_url,
    fetch_arxiv_metadata,
    fetch_crossref_metadata,
    find_paper_source_by_pdf_digest,
    import_paper_pdf,
    import_paper_search_results,
    upload_paper_library_pdf,
)
from nblane.core.research_sources import (
    ResearchSourceInbox,
    add_research_source,
    load_research_sources,
    save_research_sources,
)
from nblane.web_reader_api import app

PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>\nendobj\n"
    b"trailer\n<< /Root 1 0 R >>\n%%EOF\n"
)


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args, **kwargs) -> None:
        return None

    def read(self) -> bytes:
        return self._body


class TestMetadataLookups(unittest.TestCase):
    def setUp(self) -> None:
        _metadata_cache_clear()
        os.environ.pop("NBLANE_DISABLE_NETWORK_LOOKUPS", None)

    def tearDown(self) -> None:
        _metadata_cache_clear()
        os.environ.pop("NBLANE_DISABLE_NETWORK_LOOKUPS", None)

    def test_crossref_returns_empty_when_disabled(self) -> None:
        os.environ["NBLANE_DISABLE_NETWORK_LOOKUPS"] = "1"
        with patch("urllib.request.urlopen") as opened:
            self.assertEqual(fetch_crossref_metadata("10.1000/test"), {})
        opened.assert_not_called()

    def test_crossref_parses_payload_and_caches(self) -> None:
        payload = json.dumps(
            {
                "message": {
                    "title": ["A Study of Things"],
                    "abstract": "<jats:p>An <i>abstract</i>.</jats:p>",
                    "author": [
                        {"given": "Ada", "family": "Lovelace"},
                        {"name": "Anonymous"},
                    ],
                    "issued": {"date-parts": [[2024, 5]]},
                    "container-title": ["Journal of Examples"],
                    "URL": "https://doi.org/10.1000/test",
                }
            }
        ).encode("utf-8")
        with patch("urllib.request.urlopen", return_value=_FakeResponse(payload)) as opened:
            result = fetch_crossref_metadata("10.1000/test")
            cached = fetch_crossref_metadata("10.1000/test")
        self.assertEqual(opened.call_count, 1)
        self.assertEqual(result["title"], "A Study of Things")
        self.assertEqual(result["abstract"], "An abstract.")
        self.assertEqual(result["authors"], ["Ada Lovelace", "Anonymous"])
        self.assertEqual(result["year"], "2024")
        self.assertEqual(result["venue"], "Journal of Examples")
        self.assertEqual(cached, result)

    def test_arxiv_parses_atom_feed(self) -> None:
        atom = """<?xml version='1.0'?>
        <feed xmlns='http://www.w3.org/2005/Atom'>
          <entry>
            <title>Sample Paper Title</title>
            <summary>A short abstract.</summary>
            <published>2023-04-12T00:00:00Z</published>
            <author><name>Alice Researcher</name></author>
            <author><name>Bob Researcher</name></author>
            <link rel='alternate' href='https://arxiv.org/abs/2304.00001'/>
            <link title='pdf' href='https://arxiv.org/pdf/2304.00001'/>
          </entry>
        </feed>
        """.encode("utf-8")
        with patch("urllib.request.urlopen", return_value=_FakeResponse(atom)):
            result = fetch_arxiv_metadata("2304.00001")
        self.assertEqual(result["title"], "Sample Paper Title")
        self.assertEqual(result["year"], "2023")
        self.assertEqual(result["authors"], ["Alice Researcher", "Bob Researcher"])
        self.assertEqual(result["pdf_url"], "https://arxiv.org/pdf/2304.00001")
        self.assertEqual(result["canonical_url"], "https://arxiv.org/abs/2304.00001")

    def test_result_from_url_enriches_arxiv_when_available(self) -> None:
        atom = """<?xml version='1.0'?>
        <feed xmlns='http://www.w3.org/2005/Atom'>
          <entry>
            <title>Enriched Title</title>
            <summary>Enriched abstract.</summary>
            <published>2022-01-01T00:00:00Z</published>
            <author><name>Researcher One</name></author>
            <link rel='alternate' href='https://arxiv.org/abs/2201.99999'/>
            <link title='pdf' href='https://arxiv.org/pdf/2201.99999'/>
          </entry>
        </feed>
        """.encode("utf-8")
        with patch("urllib.request.urlopen", return_value=_FakeResponse(atom)):
            result = _result_from_url("https://arxiv.org/abs/2201.99999")
        self.assertEqual(result.title, "Enriched Title")
        self.assertEqual(result.abstract, "Enriched abstract.")
        self.assertEqual(result.authors, ["Researcher One"])
        self.assertEqual(result.year, "2022")
        self.assertEqual(result.pdf_url, "https://arxiv.org/pdf/2201.99999")

    def test_result_from_url_no_network_falls_back(self) -> None:
        os.environ["NBLANE_DISABLE_NETWORK_LOOKUPS"] = "1"
        result = _result_from_url("https://arxiv.org/abs/2201.99999")
        self.assertEqual(result.arxiv_id, "2201.99999")
        self.assertTrue(result.pdf_url.endswith("2201.99999"))
        self.assertEqual(result.title, "arXiv 2201.99999")
        self.assertFalse(result.abstract)


class TestUploadHelper(unittest.TestCase):
    def _profile(self, root: Path) -> Path:
        profile = root / "alice"
        profile.mkdir()
        inbox = ResearchSourceInbox(profile="alice")
        add_research_source(
            inbox,
            "Existing Paper",
            source_id="source:paper:existing",
            kind="paper",
            visibility="private",
        )
        with patch("nblane.core.research_sources.git_backup.record_change"):
            save_research_sources(profile, inbox)
        return profile

    def test_invalid_pdf_raises_paper_import_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")},
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            with self.assertRaises(PaperImportError) as ctx:
                upload_paper_library_pdf(profile, b"not a pdf", "junk.pdf", {"title": "Junk"})
        self.assertEqual(ctx.exception.code, "invalid_pdf")
        self.assertFalse(ctx.exception.retryable)

    def test_sha_fingerprint_reuses_existing_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")},
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            with patch("nblane.core.research_sources.git_backup.record_change"):
                import_paper_pdf(profile, "source:paper:existing", PDF_BYTES, "first.pdf")
            with patch("nblane.core.research_sources.git_backup.record_change"):
                outcome = upload_paper_library_pdf(
                    profile, PDF_BYTES, "second.pdf", {"title": "Should be skipped"}
                )
            sources = load_research_sources(profile).sources
        self.assertTrue(outcome["duplicate"])
        self.assertEqual(outcome["source_id"], "source:paper:existing")
        self.assertEqual(
            sum(1 for s in sources if s.kind == "paper"),
            1,
            "duplicate upload must not create a new source",
        )

    def test_allow_duplicates_overrides_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")},
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            with patch("nblane.core.research_sources.git_backup.record_change"):
                import_paper_pdf(profile, "source:paper:existing", PDF_BYTES, "first.pdf")
            with patch("nblane.core.research_sources.git_backup.record_change"):
                outcome = upload_paper_library_pdf(
                    profile,
                    PDF_BYTES,
                    "second.pdf",
                    {"title": "Force new", "allow_duplicates": True},
                )
        self.assertFalse(outcome["duplicate"])
        self.assertNotEqual(outcome["source_id"], "source:paper:existing")

    def test_find_paper_source_by_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")},
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            with patch("nblane.core.research_sources.git_backup.record_change"):
                asset = import_paper_pdf(profile, "source:paper:existing", PDF_BYTES, "x.pdf")
            self.assertEqual(
                find_paper_source_by_pdf_digest(profile, asset.sha256),
                "source:paper:existing",
            )
            self.assertEqual(find_paper_source_by_pdf_digest(profile, "0" * 64), "")


class TestTitleSimilarityDedupe(unittest.TestCase):
    def _profile(self, root: Path) -> Path:
        profile = root / "alice"
        profile.mkdir()
        inbox = ResearchSourceInbox(profile="alice")
        add_research_source(
            inbox,
            "Attention is All You Need",
            source_id="source:paper:attn",
            kind="paper",
            visibility="private",
            published="2017",
        )
        with patch("nblane.core.research_sources.git_backup.record_change"):
            save_research_sources(profile, inbox)
        return profile

    def test_near_identical_title_blocks_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"NBLANE_DISABLE_NETWORK_LOOKUPS": "1"}, clear=False
        ):
            profile = self._profile(Path(tmp))
            candidate_dict = PaperSearchResult(
                title="Attention is All You Need.",  # extra punctuation
                year="2017",
                provider_refs=["arxiv"],
            ).to_dict()
            with patch("nblane.core.research_sources.git_backup.record_change"):
                imported = import_paper_search_results(
                    profile,
                    [candidate_dict],
                    [candidate_dict["candidate_id"]],
                    {"download_pdf": False},
                )
        self.assertEqual(imported, [], "duplicate title should be filtered")

    def test_year_mismatch_allows_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"NBLANE_DISABLE_NETWORK_LOOKUPS": "1"}, clear=False
        ):
            profile = self._profile(Path(tmp))
            candidate_dict = PaperSearchResult(
                title="Attention is All You Need",
                year="2023",
                provider_refs=["arxiv"],
            ).to_dict()
            with patch("nblane.core.research_sources.git_backup.record_change"):
                imported = import_paper_search_results(
                    profile,
                    [candidate_dict],
                    [candidate_dict["candidate_id"]],
                    {"download_pdf": False},
                )
        self.assertEqual(len(imported), 1)


class TestRetryEndpoint(unittest.TestCase):
    def _profile(self, root: Path) -> Path:
        profile = root / "alice"
        profile.mkdir()
        inbox = ResearchSourceInbox(profile="alice")
        add_research_source(
            inbox,
            "Failed Download",
            source_id="source:paper:failed",
            kind="paper",
            visibility="private",
            url="https://example.com/paper.pdf",
            metadata={
                "open_access_pdf_url": "https://example.com/paper.pdf",
                "pdf_download_status": "failed",
                "pdf_download_error": "previous failure",
            },
        )
        with patch("nblane.core.research_sources.git_backup.record_change"):
            save_research_sources(profile, inbox)
        return profile

    def _client(self, profile: Path) -> TestClient:
        patcher = patch("nblane.web_reader_api.profile_dir", return_value=profile)
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)

    def test_retry_endpoint_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            with (
                patch("nblane.core.research_papers.download_paper_pdf") as fake_download,
                patch("nblane.core.research_sources.git_backup.record_change"),
            ):
                fake_download.return_value = type(
                    "_A",
                    (),
                    {
                        "asset_ref": "papers/abcdef-foo.pdf",
                        "byte_size": len(PDF_BYTES),
                        "page_count": 1,
                    },
                )()
                response = client.post(
                    f"/api/research/alice/papers/{quote('source:paper:failed', safe='')}/pdf-retry",
                    headers={"Origin": "http://testserver"},
                    json={},
                )
            body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["status"], "downloaded")
        self.assertTrue(body["ok"])

    def test_retry_endpoint_failure_carries_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            with (
                patch(
                    "nblane.core.research_papers.download_paper_pdf",
                    side_effect=TimeoutError("timed out after 5s"),
                ),
                patch("nblane.core.research_sources.git_backup.record_change"),
            ):
                response = client.post(
                    f"/api/research/alice/papers/{quote('source:paper:failed', safe='')}/pdf-retry",
                    headers={"Origin": "http://testserver"},
                    json={},
                )
            body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(body["ok"])
        self.assertEqual(body["status"], "failed")
        self.assertIn("timed out", body["error"])


class TestStructuredErrors(unittest.TestCase):
    def _profile(self, root: Path) -> Path:
        profile = root / "alice"
        profile.mkdir()
        inbox = ResearchSourceInbox(profile="alice")
        add_research_source(
            inbox,
            "Existing",
            source_id="source:paper:existing",
            kind="paper",
            visibility="private",
        )
        with patch("nblane.core.research_sources.git_backup.record_change"):
            save_research_sources(profile, inbox)
        return profile

    def _client(self, profile: Path) -> TestClient:
        patcher = patch("nblane.web_reader_api.profile_dir", return_value=profile)
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)

    def test_invalid_pdf_returns_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
            },
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            with patch("nblane.core.research_sources.git_backup.record_change"):
                response = client.post(
                    "/api/research/alice/paper-library/upload",
                    headers={"Origin": "http://testserver"},
                    data={"title": "Bad", "status": "reading"},
                    files={"file": ("garbage.pdf", b"not a pdf", "application/pdf")},
                )
            body = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(body["detail"]["code"], "invalid_pdf")
        self.assertFalse(body["detail"]["retryable"])


if __name__ == "__main__":
    unittest.main()
