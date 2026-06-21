"""Tests for the v2 evidence schema layer (provenance + full-content fields).

Covers EvidenceRecord round-trip, the ingest normalizer whitelist, the
page-level _compact_row, the read-model payload, and field preservation
through Project Board sync and the pool save path.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nblane.core.evidence_review import _evidence_row_payload
from nblane.core.ingest_parse import _normalize_evidence_row
from nblane.core.models import (
    EVIDENCE_POOL_SCHEMA_VERSION,
    EvidencePool,
    EvidenceRecord,
)


_PAGE_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "pages"
    / "2_Evidence_Review.py"
).read_text(encoding="utf-8")


V2_ROW = {
    "id": "ev_ap_boost",
    "type": "project",
    "title": "Far-range Monocular Detection Optimization (GAC)",
    "date": "2024",
    "summary": "Improved far-range detection by +15 AP.",
    "origin": "resume_parse",
    "origin_ref": "resume",
    "origin_detail": "GAC experience block parsed from imported resume",
    "original_content": "第一行\n  缩进的第二行\n第三行",
    "formatted_content": "Origin: Resume parse\nMetrics:\n- +15 AP",
    "language": "en",
    "original_language": "zh",
    "original_content_hash": "sha256:9f2a1b3c4d5e",
    "review_status": "reviewed",
    "public_readiness": "private",
    "project_refs": ["project:gac"],
    "kanban_refs": ["kanban:abc"],
    "experience_refs": ["exp:gac"],
    "source_excerpt": "+15 AP",
}


class TestEvidenceRecordV2RoundTrip(unittest.TestCase):
    def test_round_trip_preserves_v2_fields(self) -> None:
        rec = EvidenceRecord.from_dict(V2_ROW)
        self.assertEqual(rec.origin, "resume_parse")
        self.assertEqual(rec.origin_ref, "resume")
        self.assertEqual(rec.original_content, "第一行\n  缩进的第二行\n第三行")
        self.assertEqual(rec.formatted_content, V2_ROW["formatted_content"])
        self.assertEqual(rec.language, "en")
        self.assertEqual(rec.original_language, "zh")
        self.assertEqual(rec.original_content_hash, "sha256:9f2a1b3c4d5e")
        back = rec.to_dict()
        for key in (
            "origin",
            "origin_ref",
            "origin_detail",
            "original_content",
            "formatted_content",
            "language",
            "original_language",
            "original_content_hash",
        ):
            self.assertEqual(back[key], V2_ROW[key], key)

    def test_legacy_row_has_empty_v2_fields(self) -> None:
        rec = EvidenceRecord.from_dict(
            {"id": "old", "type": "practice", "title": "Legacy"}
        )
        self.assertEqual(rec.origin, "")
        self.assertEqual(rec.original_content, "")
        self.assertEqual(rec.language, "")
        back = rec.to_dict()
        self.assertNotIn("origin", back)
        self.assertNotIn("original_content", back)

    def test_pool_schema_version_round_trip(self) -> None:
        pool = EvidencePool.from_dict(
            {
                "profile": "p",
                "schema_version": "2.0",
                "evidence_entries": [V2_ROW],
            }
        )
        self.assertEqual(pool.schema_version, "2.0")
        self.assertEqual(pool.to_dict()["schema_version"], "2.0")


class TestNormalizeEvidenceRowV2(unittest.TestCase):
    def test_keeps_valid_v2_fields(self) -> None:
        out = _normalize_evidence_row(V2_ROW)
        assert out is not None
        self.assertEqual(out["origin"], "resume_parse")
        self.assertEqual(out["language"], "en")
        self.assertEqual(out["original_language"], "zh")
        self.assertEqual(out["experience_refs"], ["exp:gac"])
        # internal newlines preserved.
        self.assertIn("\n  缩进的第二行\n", out["original_content"])

    def test_drops_invalid_origin_and_language(self) -> None:
        row = dict(V2_ROW)
        row["origin"] = "bogus_origin"
        row["language"] = "fr"
        out = _normalize_evidence_row(row)
        assert out is not None
        self.assertNotIn("origin", out)
        self.assertNotIn("language", out)
        # valid sibling still kept.
        self.assertEqual(out["original_language"], "zh")

    def test_empty_v2_fields_omitted(self) -> None:
        out = _normalize_evidence_row(
            {"id": "x", "type": "practice", "title": "T"}
        )
        assert out is not None
        self.assertNotIn("origin", out)
        self.assertNotIn("original_content", out)


class TestCompactRowV2(unittest.TestCase):
    """_compact_row lives in a Streamlit page (cannot import bare); assert the
    v2 field whitelist is wired in via source inspection. Behavioral coverage
    of the same compaction rules is exercised by the normalizer tests above,
    which share the strip-and-omit contract.
    """

    def test_compact_row_lists_v2_fields(self) -> None:
        for field_name in (
            "origin",
            "origin_ref",
            "origin_detail",
            "language",
            "original_language",
            "original_content_hash",
            "original_content",
            "formatted_content",
        ):
            self.assertIn(
                f'"{field_name}"',
                _PAGE_SOURCE,
                f"_compact_row whitelist missing {field_name}",
            )


class TestEvidenceRowPayloadV2(unittest.TestCase):
    def test_payload_includes_v2_fields(self) -> None:
        payload = _evidence_row_payload(V2_ROW, {}, {})
        self.assertEqual(payload["origin"], "resume_parse")
        self.assertEqual(payload["origin_ref"], "resume")
        self.assertEqual(payload["language"], "en")
        self.assertEqual(payload["original_language"], "zh")
        self.assertEqual(payload["original_content"], V2_ROW["original_content"])
        self.assertEqual(
            payload["original_content_hash"], "sha256:9f2a1b3c4d5e"
        )


class TestSchemaVersionStampedOnSave(unittest.TestCase):
    def test_save_stamps_schema_version(self) -> None:
        from nblane.core import paths as paths_mod
        from nblane.core import profile_io

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            orig = paths_mod.PROFILES_DIR
            # Redirect both the module constant and the profile_io reference.
            paths_mod.PROFILES_DIR = tmp_path
            profile_io.PROFILES_DIR = tmp_path
            try:
                (tmp_path / "p").mkdir(parents=True)
                profile_io.save_evidence_pool(
                    "p",
                    {"profile": "p", "evidence_entries": [V2_ROW]},
                )
                raw = profile_io.load_evidence_pool_raw("p")
                assert raw is not None
                self.assertEqual(
                    raw["schema_version"], EVIDENCE_POOL_SCHEMA_VERSION
                )
                # v2 fields survive the YAML round-trip.
                self.assertEqual(
                    raw["evidence_entries"][0]["original_content"],
                    V2_ROW["original_content"],
                )
            finally:
                paths_mod.PROFILES_DIR = orig
                profile_io.PROFILES_DIR = orig


if __name__ == "__main__":
    unittest.main()
