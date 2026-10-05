"""Tests for the career workspace API and career AI (LLM mocked, no network).

Covers: read-only overview, structured save (normalize, ETag 412, autosave
skipping backup), photo upload not touching the resume, import preview never
writing, draft create/409/update/412/delete with the JD sidecar, export
returning bytes without rewriting the draft, and the AI job kinds reading the
evidence pool (deprecated rows excluded, unknown refs dropped) but not claims.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import career_ai, git_backup
from nblane.core.paths import REPO_ROOT
from nblane.web_api import app
from nblane.web_api import jobs as jobs_module

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"
PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)
RESUME_MD = """# 张三 | 算法工程师

✉️ zhangsan@example.com

## 工作概要

做 VLA。

## 工作经历

### 示例公司 | 工程师 | 2025/04 – 至今

- 主导 PI0.5 复现。
"""
BASE = "/api/v1/profiles/alice/career"


class CareerApiTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.profile = self.root / "alice"
        shutil.copytree(TEMPLATE_DIR, self.profile)
        (self.profile / "resume-source.yaml").unlink(missing_ok=True)
        for target in (
            "nblane.core.paths.PROFILES_DIR",
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, self.root)
            patcher.start()
            self.addCleanup(patcher.stop)
        backup = patch("nblane.core.career_workspace.git_backup.record_change")
        self.record_change = backup.start()
        self.addCleanup(backup.stop)
        self.client = TestClient(app)

    def _save(self, resume: dict, etag: str, **params) -> object:
        return self.client.put(f"{BASE}/resume", json={"resume": resume}, headers={"If-Match": etag}, params=params)

    def _import(self) -> dict:
        response = self.client.post(f"{BASE}/import", files={"file": ("resume.md", RESUME_MD.encode(), "text/markdown")})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_overview_is_read_only(self) -> None:
        data = self.client.get(BASE).json()
        self.assertFalse(data["has_resume"])
        self.assertEqual(data["resume"]["basics"]["name"], "alice")
        self.assertFalse((self.profile / "resume-source.yaml").exists())

    def test_import_preview_writes_nothing_then_save(self) -> None:
        preview = self._import()
        self.assertEqual(preview["method"], "markdown")
        self.assertEqual(preview["resume"]["experiences"][0]["company"], "示例公司")
        self.assertFalse((self.profile / "resume-source.yaml").exists())
        etag = self.client.get(BASE).json()["resume_etag"]
        saved = self._save(preview["resume"], etag)
        self.assertEqual(saved.status_code, 200, saved.text)
        body = saved.json()
        self.assertTrue(body["has_resume"])
        self.assertIn("### 示例公司 | 工程师 | 2025/04 – 至今", body["resume_markdown"])
        on_disk = yaml.safe_load((self.profile / "resume-source.yaml").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["summary"], "做 VLA。")
        # Stale ETag is a conflict, not an overwrite.
        stale = self._save({**preview["resume"], "summary": "x"}, etag)
        self.assertEqual(stale.status_code, 412)
        self.assertEqual(on_disk["summary"], "做 VLA。")

    def test_html_paste_import(self) -> None:
        html = "<html><body><h1>李四</h1><h2>工作经历</h2><h3>甲 · 乙 <span class='meta'>2020 – 2021</span></h3><h2>教育经历</h2><ul><li>丙大学</li></ul></body></html>"
        preview = self.client.post(f"{BASE}/import/text", json={"text": html}).json()
        self.assertEqual(preview["resume"]["basics"]["name"], "李四")
        self.assertEqual(preview["resume"]["experiences"][0]["role"], "乙")

    def test_autosave_skips_backup(self) -> None:
        etag = self.client.get(BASE).json()["resume_etag"]
        seen: list[bool] = []
        self.record_change.side_effect = lambda *a, **k: seen.append(git_backup._deferred_changes.get() is not None)
        response = self._save({"basics": {"name": "alice"}, "summary": "hi"}, etag, autosave=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(seen, [True])

    def test_photo_upload_does_not_touch_resume(self) -> None:
        response = self.client.post(f"{BASE}/resume/photo", files={"file": ("me.png", PNG_BYTES, "image/png")})
        self.assertEqual(response.status_code, 200, response.text)
        path = response.json()["path"]
        self.assertTrue(path.startswith("media/resume/photo-"))
        self.assertTrue((self.profile / path).is_file())
        self.assertFalse((self.profile / "resume-source.yaml").exists())
        served = self.client.get(response.json()["url"])
        self.assertEqual(served.content, PNG_BYTES)
        bad = self.client.post(f"{BASE}/resume/photo", files={"file": ("me.svg", b"<svg/>", "image/svg+xml")})
        self.assertEqual(bad.status_code, 422)

    def test_draft_lifecycle(self) -> None:
        created = self.client.post(
            f"{BASE}/drafts", json={"target": "VLA 算法", "markdown": "# 张三\n", "jd_text": "需要 VLA"}
        )
        self.assertEqual(created.status_code, 201, created.text)
        draft = created.json()
        self.assertEqual(draft["id"], "VLA-算法")
        self.assertEqual(draft["jd_text"], "需要 VLA")
        dup = self.client.post(f"{BASE}/drafts", json={"target": "VLA 算法", "markdown": "# x\n"})
        self.assertEqual(dup.status_code, 409)
        updated = self.client.put(
            f"{BASE}/drafts/{draft['id']}",
            json={"markdown": "# 张三\n\n改过\n", "notes": "强调 PI0.5"},
            headers={"If-Match": draft["etag"]},
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["notes"], "强调 PI0.5")
        stale = self.client.put(
            f"{BASE}/drafts/{draft['id']}", json={"markdown": "# 覆盖\n"}, headers={"If-Match": draft["etag"]}
        )
        self.assertEqual(stale.status_code, 412)
        listed = self.client.get(BASE).json()["drafts"]
        self.assertEqual([d["id"] for d in listed], ["VLA-算法"])  # meta sidecar is not a draft
        self.assertEqual(self.client.delete(f"{BASE}/drafts/{draft['id']}").status_code, 200)
        left = [p.name for p in (self.profile / "resumes" / "generated").glob("VLA*") if p.suffix != ".lock"]
        self.assertEqual(left, [])
        self.assertEqual(self.client.get(f"{BASE}/drafts/..%2Fresume-source").status_code, 404)

    def test_export_does_not_rewrite_draft(self) -> None:
        draft = self.client.post(f"{BASE}/drafts", json={"target": "t1", "markdown": RESUME_MD}).json()
        path = self.profile / "resumes" / "generated" / "t1.md"
        before = path.read_bytes()
        for fmt, media in (("md", "text/markdown"), ("html", "text/html")):
            response = self.client.post(f"{BASE}/export", json={"draft_id": draft["id"], "format": fmt})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertTrue(response.headers["content-type"].startswith(media))
            self.assertIn("attachment", response.headers["content-disposition"])
        self.assertIn("示例公司", response.text)
        self.assertEqual(path.read_bytes(), before)
        names = sorted(p.name for p in path.parent.iterdir() if p.suffix != ".lock" and p.name != ".gitkeep")
        self.assertEqual(names, ["t1.md", "t1.meta.yaml"])

    def test_pdf_unavailable_is_503(self) -> None:
        with patch("nblane.core.resume_doc.find_chromium", return_value=""):
            response = self.client.post(f"{BASE}/export", json={"markdown": RESUME_MD, "format": "pdf"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "pdf_unavailable")


class CareerAITest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.profile = self.root / "alice"
        shutil.copytree(TEMPLATE_DIR, self.profile)
        (self.profile / "evidence-pool.yaml").write_text(
            yaml.safe_dump(
                {
                    "profile": "alice",
                    "evidence_entries": [
                        {"id": "ev_old", "type": "project", "title": "Old repro", "deprecated": True},
                        {"id": "ev_pi05", "type": "project", "title": "PI0.5 on Piper", "summary": "20%→95%",
                         "strength": "strong", "review_status": "reviewed", "date": "2026-06-21"},
                    ],
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        (self.profile / "claims.yaml").write_text(
            yaml.safe_dump({"claims": [{"id": "c1", "text": "SECRET CLAIM", "status": "accepted"}]}), encoding="utf-8"
        )
        for target in (
            "nblane.core.paths.PROFILES_DIR",
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, self.root)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = TestClient(app)

    def _llm(self, reply: str, configured: bool = True):
        stack = [
            patch("nblane.core.llm.is_configured", return_value=configured),
            patch("nblane.core.llm.chat", return_value=reply),
        ]
        mocks = [p.start() for p in stack]
        for p in stack:
            self.addCleanup(p.stop)
        return mocks[1]

    def _run_job(self, kind: str, job_input: dict) -> dict:
        created = self.client.post("/api/v1/profiles/alice/jobs", json={"kind": kind, "input": job_input})
        self.assertEqual(created.status_code, 202, created.text)
        job_id = created.json()["job_id"]
        deadline = time.monotonic() + 10
        while True:
            payload = self.client.get(f"/api/v1/profiles/alice/jobs/{job_id}").json()
            if payload["job"]["status"] in jobs_module.FINAL_STATUSES:
                return payload
            if time.monotonic() > deadline:
                self.fail("job did not finish")
            time.sleep(0.05)

    def test_evidence_items_skip_deprecated(self) -> None:
        self.assertEqual([i["id"] for i in career_ai.evidence_items("alice")], ["ev_pi05"])

    def test_match_reads_evidence_not_claims(self) -> None:
        reply = json.dumps(
            {
                "score": 72,
                "summary": "较匹配",
                "requirements": [
                    {"requirement": "VLA 经验", "verdict": "match", "basis": "PI0.5", "evidence_refs": ["ev_pi05", "ev_fake"]},
                    {"requirement": "C++", "verdict": "weird", "basis": "简历未体现"},
                ],
                "strengthen": ["写上 95%"],
                "gaps": ["C++"],
                "keywords": ["VLA"],
                "interview_questions": [{"question": "为什么 95%？", "answer_hint": "数据配方"}],
            },
            ensure_ascii=False,
        )
        chat = self._llm(f"```json\n{reply}\n```")
        payload = self._run_job("career-match", {"resume_md": RESUME_MD, "jd_text": "需要 VLA 和 C++"})
        self.assertEqual(payload["job"]["status"], "done", payload)
        result = payload["result"]
        self.assertEqual(result["score"], 72)
        self.assertEqual(result["requirements"][0]["evidence_refs"], ["ev_pi05"])
        self.assertEqual(result["requirements"][1]["verdict"], "partial")
        self.assertEqual([e["id"] for e in result["evidence"]], ["ev_pi05"])
        prompt = chat.call_args.args[1]
        self.assertIn("[ev_pi05]", prompt)
        self.assertNotIn("ev_old", prompt)
        self.assertNotIn("SECRET CLAIM", prompt)

    def test_match_without_evidence(self) -> None:
        chat = self._llm('{"score": 10, "requirements": [{"requirement": "x", "verdict": "missing"}]}')
        payload = self._run_job("career-match", {"resume_md": "a", "jd_text": "b", "use_evidence": False})
        self.assertEqual(payload["result"]["evidence_used"], 0)
        self.assertNotIn("工作证据", chat.call_args.args[1])

    def test_tailor_strips_fence_and_requires_heading(self) -> None:
        self._llm("```markdown\n# 张三 | 工程师\n\n## 工作经历\n```")
        payload = self._run_job("career-tailor", {"resume_md": RESUME_MD, "jd_text": "VLA"})
        self.assertEqual(payload["result"]["markdown"], "# 张三 | 工程师\n\n## 工作经历\n")
        self._llm("抱歉，我无法完成")
        failed = self._run_job("career-tailor", {"resume_md": RESUME_MD, "jd_text": "VLA"})
        self.assertEqual(failed["job"]["error"]["code"], "career_ai_failed")

    def test_structure_and_unavailable(self) -> None:
        self._llm(json.dumps({"basics": {"name": "张三"}, "experiences": [{"company": "甲", "role": "乙", "bullets": ["做事"]}]}))
        payload = self._run_job("career-structure", {"text": "张三 甲公司 乙职位 做事" * 5})
        self.assertEqual(payload["result"]["resume"]["experiences"][0]["company"], "甲")
        self._llm("x", configured=False)
        failed = self._run_job("career-match", {"resume_md": "a", "jd_text": "b"})
        self.assertEqual(failed["job"]["error"]["code"], "career_ai_unavailable")

    def test_rejects_empty_pair(self) -> None:
        response = self.client.post(
            "/api/v1/profiles/alice/jobs", json={"kind": "career-match", "input": {"resume_md": " ", "jd_text": "x"}}
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
