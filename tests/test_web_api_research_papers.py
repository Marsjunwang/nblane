"""Tests for the SPA paper overview endpoint and its analysis job kinds.

Covers ``GET /profiles/{name}/research/papers/{source_id}`` (metadata,
abstract + cached translation, progress, notes, refs resolved to pages) and
``POST .../analysis-jobs`` with the ``paper-quick-analysis`` /
``paper-deep-read`` kinds. The Reader action entry point and the backend
readiness probe are always patched — tests never reach an LLM, Codex or the
network.
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

from nblane.core.reader_actions import ReaderActionResult
from nblane.core.research_papers import (
    PaperAnnotation,
    PaperSegment,
    PaperStructureUnit,
    PaperTranslation,
    load_paper_analysis,
    save_paper_analysis,
    save_paper_annotations,
    save_paper_segments,
    save_paper_structure_units,
    save_paper_translations,
    text_hash,
)
from nblane.web_api import app
from nblane.web_api import jobs as jobs_module
from nblane.web_api import research_papers as module

SOURCE_ID = "source:paper:demo"
ABSTRACT = "We propose a demo architecture that relies on attention only."
BODY = "The encoder maps an input sequence to continuous representations."

SKILL_MD = "# SKILL — alice\n\n## Identity\n\n- **Name**: Alice\n"


def _write_profile(root: Path, asset_root: Path, *, with_pdf: bool = True) -> Path:
    profile = root / "alice"
    (profile / "research").mkdir(parents=True)
    (profile / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    sources = {
        "schema_version": "1.0",
        "profile": "alice",
        "sources": [
            {
                "id": SOURCE_ID,
                "kind": "paper",
                "title": "Demo Paper",
                "status": "reading",
                "url": "https://arxiv.org/abs/1706.03762",
                "authors": ["Ada Lovelace", "Alan Turing"],
                "published": "2017-06-12",
                "tags": ["nlp"],
                "metadata": {
                    "arxiv_id": "1706.03762",
                    "doi": "10.0000/demo",
                    "venue": "NeurIPS",
                    "pdf_asset_ref": "papers/demo.pdf",
                    "pdf_download_status": "downloaded",
                    "page_count": 4,
                    "last_read_page": 3,
                    "last_read_at": "2026-10-05T10:00:00+08:00",
                    "reading_artifacts_status": "ready",
                    "structure_backend": "grobid",
                },
            },
            {"id": "src:web", "kind": "web", "title": "Not a paper"},
        ],
    }
    (profile / "research" / "sources.yaml").write_text(
        yaml.safe_dump(sources, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    if with_pdf:
        pdf = asset_root / "profiles" / "alice" / "papers" / "demo.pdf"
        pdf.parent.mkdir(parents=True, exist_ok=True)
        pdf.write_bytes(b"%PDF-1.4 test")
    return profile


def _seed_reading_files(profile: Path) -> None:
    with patch("nblane.core.research_papers.git_backup.record_change"):
        save_paper_segments(
            profile,
            SOURCE_ID,
            [
                PaperSegment(
                    segment_id="seg:demo:00001",
                    source_id=SOURCE_ID,
                    page=2,
                    order=1,
                    text=BODY,
                    text_hash=text_hash(BODY),
                )
            ],
        )
        save_paper_structure_units(
            profile,
            SOURCE_ID,
            [
                PaperStructureUnit(
                    unit_id="psu:abstract-head",
                    source_id=SOURCE_ID,
                    kind="heading",
                    page_start=1,
                    page_end=1,
                    order=1,
                    text="Abstract",
                    text_hash=text_hash("Abstract"),
                    section_path=["Abstract"],
                    rects=[{"page": 1, "x": 10, "y": 10, "w": 50, "h": 10}],
                ),
                PaperStructureUnit(
                    unit_id="psu:abstract",
                    source_id=SOURCE_ID,
                    kind="paragraph",
                    page_start=1,
                    page_end=1,
                    order=2,
                    text=ABSTRACT,
                    text_hash=text_hash(ABSTRACT),
                    section_path=["Abstract"],
                    rects=[{"page": 1, "x": 10, "y": 30, "w": 200, "h": 40}],
                ),
                PaperStructureUnit(
                    unit_id="psu:body",
                    source_id=SOURCE_ID,
                    kind="paragraph",
                    page_start=3,
                    page_end=3,
                    order=3,
                    text=BODY,
                    text_hash=text_hash(BODY),
                    section_path=["Model"],
                    rects=[{"page": 3, "x": 10, "y": 30, "w": 200, "h": 40}],
                ),
            ],
        )
        save_paper_translations(
            profile,
            SOURCE_ID,
            [
                PaperTranslation(
                    id="tr:abstract",
                    source_id=SOURCE_ID,
                    scope_type="structure",
                    scope_ref="psu:abstract",
                    page=1,
                    source_hash=text_hash(ABSTRACT),
                    source_text=ABSTRACT,
                    translated_text="我们提出一个只依赖注意力的演示架构。",
                    status="translated",
                )
            ],
        )
        save_paper_annotations(
            profile,
            SOURCE_ID,
            [
                PaperAnnotation(
                    id="ann:demo:0001",
                    source_id=SOURCE_ID,
                    page=3,
                    selected_text="continuous representations",
                    note="与项目的编码器设计对照",
                    updated="2026-10-05T09:00:00+00:00",
                ),
                PaperAnnotation(
                    id="ann:demo:0002",
                    source_id=SOURCE_ID,
                    page=1,
                    selected_text="deleted quote",
                    status="deleted",
                ),
            ],
        )
        save_paper_analysis(
            profile,
            SOURCE_ID,
            {
                "tldr": "A demo transformer.",
                "key_points": [
                    {"text": "Attention only.", "refs": ["seg:demo:00001", "psu:abstract"]},
                ],
                "method": [{"text": "Encoder-decoder.", "refs": ["ann:demo:0001"]}],
                "experiments": [],
                "limitations": ["No long-sequence study."],
                "usefulness": "[{'text': 'Foundational.', 'refs': ['seg:demo:00001']}]",
                "scores": {"novelty": 5, "overall": 4},
                "score_rationale": [
                    {"metric": "novelty", "reason": "First of its kind.", "refs": ["seg:demo:00001"]}
                ],
                "warnings": [],
                "cited_segment_refs": ["seg:demo:00001"],
                "codex_deep_read": {
                    "takeaway": "Attention suffices.",
                    "problem": [{"text": "Recurrence is slow.", "refs": ["seg:demo:00001"]}],
                    "terms": [{"term": "Attention", "definition": "Weighted lookup.", "refs": []}],
                    "warnings": ["rule_fallback used deterministic candidate generation."],
                    "section_summaries": [{"section": "Model", "summary": "Stacks."}],
                },
                "codex_deep_read_updated": "2026-10-04T12:00:00+08:00",
            },
        )


class _PaperApiBase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        self.root = base / "profiles"
        self.asset_root = base / "assets"
        self.root.mkdir()
        # Temp-profile isolation: every PROFILES_DIR binding must point at
        # the tmp tree, otherwise core.io reads the real repo profiles.
        for target in (
            "nblane.core.paths.PROFILES_DIR",
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, self.root)
            self.addCleanup(patcher.stop)
            patcher.start()
        env = patch.dict(os.environ, {"NBLANE_RESEARCH_ASSET_ROOT": str(self.asset_root)})
        self.addCleanup(env.stop)
        env.start()
        backup = patch("nblane.core.git_backup.record_change")
        self.addCleanup(backup.stop)
        backup.start()
        module._ACTIVE_JOBS.clear()
        self.client = TestClient(app)

    def _wait_final(self, job_id: str, timeout: float = 10.0) -> dict:
        deadline = time.monotonic() + timeout
        while True:
            response = self.client.get(f"/api/v1/profiles/alice/jobs/{job_id}")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            if payload["job"]["status"] in jobs_module.FINAL_STATUSES:
                return payload
            if time.monotonic() > deadline:
                self.fail(f"job {job_id} did not finish within {timeout}s")
            time.sleep(0.05)


class TestPaperOverview(_PaperApiBase):
    URL = "/api/v1/profiles/alice/research/papers/source:paper:demo"

    def test_overview_projects_metadata_progress_and_notes(self) -> None:
        profile = _write_profile(self.root, self.asset_root)
        _seed_reading_files(profile)

        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["source"]["title"], "Demo Paper")
        self.assertEqual(body["source"]["authors"], ["Ada Lovelace", "Alan Turing"])
        self.assertEqual(body["source"]["year"], "2017")
        self.assertEqual(body["source"]["venue"], "NeurIPS")
        self.assertEqual(body["source"]["arxiv_id"], "1706.03762")
        self.assertEqual(body["abstract"]["text"], ABSTRACT)
        self.assertEqual(body["abstract"]["translation"], "我们提出一个只依赖注意力的演示架构。")
        self.assertEqual(body["abstract"]["translation_status"], "translated")
        self.assertTrue(body["reader_available"])
        self.assertTrue(body["pdf"]["available"])
        self.assertEqual(body["progress"], {"last_page": 3, "page_count": 4, "last_read_at": "2026-10-05T10:00:00+08:00", "mode": ""})
        # Canonical structure: heading + abstract + body, one translated.
        self.assertEqual(body["translation"]["translated"], 1)
        self.assertEqual(body["translation"]["total"], 3)
        self.assertEqual(body["translation"]["status"], "partial")
        # Deleted annotations never show up as notes.
        self.assertEqual(body["notes"]["annotation_count"], 1)
        self.assertEqual(body["notes"]["recent"][0]["quote"], "continuous representations")
        self.assertEqual(body["notes"]["recent"][0]["note"], "与项目的编码器设计对照")
        # No claim/evidence fields leak into the reading payload.
        self.assertNotIn("claims", body)
        self.assertNotIn("evidence", str(sorted(body.keys())))

    def test_analysis_refs_resolve_to_pages(self) -> None:
        profile = _write_profile(self.root, self.asset_root)
        _seed_reading_files(profile)

        body = self.client.get(self.URL).json()

        quick = body["quick_analysis"]
        self.assertEqual(quick["tldr"], "A demo transformer.")
        refs = quick["key_points"][0]["refs"]
        self.assertEqual(
            refs,
            [{"ref": "seg:demo:00001", "page": 2}, {"ref": "psu:abstract", "page": 1}],
        )
        self.assertEqual(quick["method"][0]["refs"], [{"ref": "ann:demo:0001", "page": 3}])
        # Legacy repr-string usefulness is parsed into items, not echoed raw.
        self.assertEqual(quick["usefulness"][0]["text"], "Foundational.")
        self.assertEqual(quick["limitations"][0]["text"], "No long-sequence study.")
        self.assertEqual(quick["score_rationale"][0]["label"], "novelty")
        self.assertTrue(quick["scores_evaluated"])
        self.assertEqual(quick["coverage"]["pages"], [1, 2, 3])

        deep = body["deep_read"]
        self.assertEqual(deep["takeaway"], "Attention suffices.")
        self.assertEqual(deep["updated"], "2026-10-04T12:00:00+08:00")
        self.assertTrue(deep["fallback"])
        self.assertEqual(deep["status"], "needs_review")
        labels = [section["label"] for section in deep["sections"]]
        self.assertIn("问题与动机", labels)
        self.assertIn("关键术语", labels)
        self.assertEqual(deep["coverage"]["sections"], ["Model"])

    def test_deep_read_v2_notes_map_to_sections(self) -> None:
        profile = _write_profile(self.root, self.asset_root)
        _seed_reading_files(profile)
        analysis = load_paper_analysis(profile, SOURCE_ID)
        analysis["codex_deep_read"] = {
            "schema_version": "2",
            "verdict": {
                "summary": "注意力替代循环。",
                "worth_reading": "must_read",
                "audience": "做序列建模的人",
                "refs": ["seg:demo:00001"],
            },
            "method": {
                "components": [{"name": "多头注意力", "what": "并行检索", "why": "去掉循环", "refs": ["ann:demo:0001"]}],
                "equations": [{"label": "(1)", "latex": "\\\\mathrm{softmax}(QK^T)V", "meaning": "加权求和", "refs": []}],
            },
            "experiments": {"tables": [{"label": "Table 2", "key_numbers": "BLEU 28.4", "takeaway": "超过基线", "refs": []}]},
            "claims": [{"claim": "训练更快", "support": "partial", "caveat": "只测了翻译", "refs": []}],
            "sections": [{"section": "Model Architecture", "summary": "编码器解码器", "refs": []}],
            "terms": [{"term": "attention", "translation": "注意力", "definition": "加权查找"}],
            "next": [{"kind": "reading", "text": "读后续 BERT"}],
            "cited_segment_refs": ["seg:demo:00001"],
            "warnings": [],
        }
        save_paper_analysis(profile, SOURCE_ID, analysis)

        deep = self.client.get(self.URL).json()["deep_read"]

        self.assertEqual(deep["takeaway"], "注意力替代循环。")
        self.assertEqual(deep["worth_reading"], "必读")
        self.assertEqual(deep["audience"], "做序列建模的人")
        self.assertEqual(deep["takeaway_refs"], [{"ref": "seg:demo:00001", "page": 2}])
        self.assertFalse(deep["fallback"])
        by_key = {section["key"]: section for section in deep["sections"]}
        self.assertEqual(
            list(by_key),
            ["components", "equations", "tables", "claims", "sections", "terms", "next"],
        )
        component = by_key["components"]["items"][0]
        self.assertEqual(component["label"], "多头注意力")
        self.assertEqual(component["text"], "做什么：并行检索；为什么：去掉循环")
        self.assertEqual(component["refs"], [{"ref": "ann:demo:0001", "page": 3}])
        self.assertEqual(by_key["equations"]["items"][0]["latex"], "\\\\mathrm{softmax}(QK^T)V")
        self.assertEqual(by_key["claims"]["items"][0]["badge"], "部分支撑")
        self.assertEqual(by_key["terms"]["items"][0]["label"], "attention · 注意力")
        self.assertEqual(by_key["next"]["items"][0]["badge"], "延伸阅读")
        self.assertEqual(deep["coverage"]["sections"], ["Model Architecture"])

    def test_paper_without_analysis_or_pdf(self) -> None:
        _write_profile(self.root, self.asset_root, with_pdf=False)

        body = self.client.get(self.URL).json()

        self.assertIsNone(body["quick_analysis"])
        self.assertIsNone(body["deep_read"])
        self.assertFalse(body["reader_available"])
        self.assertTrue(body["reader_unavailable_reason"])
        self.assertEqual(body["abstract"]["text"], "")

    def test_unknown_or_non_paper_source_404(self) -> None:
        _write_profile(self.root, self.asset_root)
        missing = self.client.get("/api/v1/profiles/alice/research/papers/source:nope")
        web = self.client.get("/api/v1/profiles/alice/research/papers/src:web")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["code"], "paper_not_found")
        self.assertEqual(web.status_code, 404)

    def test_unknown_profile_and_unsafe_name(self) -> None:
        _write_profile(self.root, self.asset_root)
        self.assertEqual(
            self.client.get("/api/v1/profiles/nobody/research/papers/x").status_code, 404
        )
        self.assertEqual(
            self.client.get("/api/v1/profiles/a%5Cb/research/papers/x").status_code,
            400,
        )


class TestPaperAnalysisJobs(_PaperApiBase):
    URL = "/api/v1/profiles/alice/research/papers/source:paper:demo/analysis-jobs"

    def _ok_action(self, ctx, action, payload, *, progress_callback=None, cancel_callback=None):
        self.calls.append((ctx.source_id, action, dict(payload)))
        if progress_callback is not None:
            progress_callback({"phase": "scoring", "label": "x", "current": 2, "total": 5})
        return ReaderActionResult(ok=True, message="Analysis saved")

    def setUp(self) -> None:
        super().setUp()
        self.calls: list[tuple[str, str, dict]] = []

    def test_quick_analysis_job_runs_reader_action(self) -> None:
        _write_profile(self.root, self.asset_root)
        with patch.object(module, "backend_problem", return_value=None), patch.object(
            module, "handle_reader_action", side_effect=self._ok_action
        ):
            response = self.client.post(self.URL, json={"kind": "paper-quick-analysis"})
            self.assertEqual(response.status_code, 202, response.text)
            job_id = response.json()["job_id"]
            final = self._wait_final(job_id)

        self.assertEqual(final["job"]["status"], "done")
        self.assertEqual(final["job"]["kind"], "paper-quick-analysis")
        self.assertEqual(final["result"]["source_id"], SOURCE_ID)
        self.assertEqual(self.calls[0][0], SOURCE_ID)
        self.assertEqual(self.calls[0][1], "analyze_paper")
        self.assertTrue(self.calls[0][2]["full_paper"])

    def test_deep_read_job_maps_to_codex_deep_read(self) -> None:
        _write_profile(self.root, self.asset_root)
        with patch.object(module, "backend_problem", return_value=None), patch.object(
            module, "handle_reader_action", side_effect=self._ok_action
        ):
            job_id = self.client.post(self.URL, json={"kind": "paper-deep-read"}).json()["job_id"]
            final = self._wait_final(job_id)
        self.assertEqual(final["job"]["status"], "done")
        self.assertEqual(self.calls[0][1], "codex_deep_read")

    def test_missing_backend_fails_with_clear_error(self) -> None:
        _write_profile(self.root, self.asset_root)
        problem = ("codex_unavailable", "深度研读使用 Codex CLI，但当前环境未安装 Codex。")
        with patch.object(module, "backend_problem", return_value=problem), patch.object(
            module, "handle_reader_action", side_effect=self._ok_action
        ):
            job_id = self.client.post(self.URL, json={"kind": "paper-deep-read"}).json()["job_id"]
            final = self._wait_final(job_id)

        self.assertEqual(final["job"]["status"], "failed")
        self.assertEqual(final["job"]["error"]["code"], "codex_unavailable")
        self.assertIn("Codex", final["job"]["error"]["message"])
        self.assertEqual(self.calls, [])

    def test_failed_reader_result_becomes_job_error(self) -> None:
        _write_profile(self.root, self.asset_root)

        def failing(ctx, action, payload, **_kwargs):
            return ReaderActionResult(ok=False, message="Analysis did not return structured output.")

        with patch.object(module, "backend_problem", return_value=None), patch.object(
            module, "handle_reader_action", side_effect=failing
        ):
            job_id = self.client.post(self.URL, json={"kind": "paper-quick-analysis"}).json()["job_id"]
            final = self._wait_final(job_id)
        self.assertEqual(final["job"]["status"], "failed")
        self.assertEqual(final["job"]["error"]["code"], "paper_analysis_failed")

    def test_fallback_result_does_not_replace_saved_analysis(self) -> None:
        profile = _write_profile(self.root, self.asset_root)
        _seed_reading_files(profile)

        def fallback(ctx, action, payload, **_kwargs):
            # Mimic the Reader action persisting a deterministic fallback.
            save_paper_analysis(ctx.profile_path, ctx.source_id, {"tldr": "Introduction", "key_points": []})
            return ReaderActionResult(
                ok=True,
                warnings=["direct_llm failed (provider_error: timed out); used rule_fallback."],
            )

        with patch.object(module, "backend_problem", return_value=None), patch.object(
            module, "handle_reader_action", side_effect=fallback
        ):
            job_id = self.client.post(self.URL, json={"kind": "paper-quick-analysis"}).json()["job_id"]
            final = self._wait_final(job_id)
        overview = self.client.get("/api/v1/profiles/alice/research/papers/source:paper:demo").json()

        self.assertEqual(final["job"]["status"], "failed")
        self.assertEqual(final["job"]["error"]["code"], "paper_analysis_fallback")
        self.assertEqual(overview["quick_analysis"]["tldr"], "A demo transformer.")

    def test_fallback_is_kept_when_nothing_was_saved_before(self) -> None:
        _write_profile(self.root, self.asset_root)

        def fallback(ctx, action, payload, **_kwargs):
            save_paper_analysis(ctx.profile_path, ctx.source_id, {"tldr": "Skeleton", "warnings": ["AI fallback used deterministic candidate generation."]})
            return ReaderActionResult(ok=True, warnings=["x used rule_fallback."])

        with patch.object(module, "backend_problem", return_value=None), patch.object(
            module, "handle_reader_action", side_effect=fallback
        ):
            job_id = self.client.post(self.URL, json={"kind": "paper-quick-analysis"}).json()["job_id"]
            final = self._wait_final(job_id)
        overview = self.client.get("/api/v1/profiles/alice/research/papers/source:paper:demo").json()
        self.assertEqual(final["job"]["status"], "done")
        self.assertTrue(overview["quick_analysis"]["fallback"])
        self.assertEqual(overview["quick_analysis"]["status"], "needs_review")

    def test_running_job_is_reused_instead_of_duplicated(self) -> None:
        _write_profile(self.root, self.asset_root)
        import threading

        release = threading.Event()

        def slow(ctx, action, payload, **_kwargs):
            release.wait(5)
            return ReaderActionResult(ok=True)

        with patch.object(module, "backend_problem", return_value=None), patch.object(
            module, "handle_reader_action", side_effect=slow
        ):
            first = self.client.post(self.URL, json={"kind": "paper-quick-analysis"}).json()
            second = self.client.post(self.URL, json={"kind": "paper-quick-analysis"}).json()
            overview = self.client.get(
                "/api/v1/profiles/alice/research/papers/source:paper:demo"
            ).json()
            release.set()
            self._wait_final(first["job_id"])

        self.assertEqual(first["job_id"], second["job_id"])
        self.assertEqual(
            [job["job_id"] for job in overview["active_jobs"]], [first["job_id"]]
        )

    def test_missing_pdf_fails_job(self) -> None:
        _write_profile(self.root, self.asset_root, with_pdf=False)
        with patch.object(module, "backend_problem", return_value=None), patch.object(
            module, "handle_reader_action", side_effect=self._ok_action
        ):
            job_id = self.client.post(self.URL, json={"kind": "paper-quick-analysis"}).json()["job_id"]
            final = self._wait_final(job_id)
        self.assertEqual(final["job"]["error"]["code"], "paper_pdf_missing")
        self.assertEqual(self.calls, [])

    def test_invalid_kind_and_unknown_paper(self) -> None:
        _write_profile(self.root, self.asset_root)
        bad_kind = self.client.post(self.URL, json={"kind": "gap-analysis"})
        unknown = self.client.post(
            "/api/v1/profiles/alice/research/papers/source:nope/analysis-jobs",
            json={"kind": "paper-quick-analysis"},
        )
        self.assertEqual(bad_kind.status_code, 422)
        self.assertEqual(bad_kind.json()["code"], "invalid_paper_job")
        self.assertEqual(unknown.status_code, 404)

    def test_kinds_registered_in_job_registry(self) -> None:
        self.assertIn("paper-quick-analysis", jobs_module._KINDS)
        self.assertIn("paper-deep-read", jobs_module._KINDS)


class TestBackendProblem(unittest.TestCase):
    def test_llm_backend_without_key(self) -> None:
        with patch.object(module, "_effective_backend", return_value="llm"), patch.object(
            module.llm_client, "reload_env_if_changed"
        ), patch.object(module.llm_client, "is_configured", return_value=False):
            problem = module.backend_problem("alice", module.KIND_PAPER_QUICK_ANALYSIS)
        self.assertEqual(problem[0], "ai_not_configured")

    def test_codex_backend_not_installed(self) -> None:
        status = module.codex_adapter.CodexStatus(installed=False, bin_path="codex")
        with patch.object(module, "_effective_backend", return_value="codex"), patch.object(
            module.codex_adapter, "codex_status", return_value=status
        ), patch.object(module.codex_adapter, "current_config"):
            problem = module.backend_problem("alice", module.KIND_PAPER_DEEP_READ)
        self.assertEqual(problem[0], "codex_unavailable")

    def test_codex_backend_ready(self) -> None:
        status = module.codex_adapter.CodexStatus(installed=True, bin_path="codex", logged_in=True)
        with patch.object(module, "_effective_backend", return_value="codex"), patch.object(
            module.codex_adapter, "codex_status", return_value=status
        ), patch.object(module.codex_adapter, "current_config"):
            self.assertIsNone(module.backend_problem("alice", module.KIND_PAPER_DEEP_READ))


if __name__ == "__main__":
    unittest.main()
