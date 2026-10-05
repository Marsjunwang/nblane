"""Career workspace AI: JD match, tailored resume, resume field recognition.

Inputs are the resume, the JD, the user's notes and (optionally) the
profile's *evidence pool* as a fact source. Claims, the skill tree, kanban
and SKILL.md are deliberately not read. Every result is a candidate the UI
shows for review; nothing here writes profile files.
"""

from __future__ import annotations

import re
from typing import Any

from nblane.core import llm as llm_client
from nblane.core import profile_io, resume_doc
from nblane.core.ai.structured import extract_json_value

RESUME_MAX_CHARS = 12_000
JD_MAX_CHARS = 12_000
NOTES_MAX_CHARS = 2_000
EVIDENCE_MAX_ITEMS = 25
EVIDENCE_SUMMARY_CHARS = 220

_LLM_ERROR_PREFIXES = ("LLM error:", "AI features not configured.")
_VERDICTS = ("match", "partial", "missing")
_STRENGTH_RANK = {"high_trust": 0, "strong": 1, "medium": 2, "weak": 3}


class CareerAIError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def llm_available() -> bool:
    return llm_client.is_configured()


def _require_llm() -> None:
    if not llm_available():
        raise CareerAIError("career_ai_unavailable", "未配置 LLM（LLM_API_KEY），AI 功能不可用。")


def _chat(system: str, user: str, *, temperature: float) -> str:
    raw = llm_client.chat(system, user, temperature=temperature, enable_thinking=False)
    if raw.startswith(_LLM_ERROR_PREFIXES):
        raise CareerAIError("career_ai_failed", raw)
    return raw


def _clip(text: str, limit: int) -> str:
    clean = str(text or "").strip()
    if len(clean) <= limit:
        return clean
    head = clean[:limit]
    cut = head.rfind("\n")
    return (head[:cut] if cut > limit // 2 else head).rstrip() + "\n…[已截断]"


def _strip_fence(text: str) -> str:
    clean = str(text or "").strip()
    match = re.match(r"^```(?:markdown|md)?\s*\n(.*?)\n?```$", clean, re.S)
    return match.group(1).strip() if match else clean


# --- Evidence context ------------------------------------------------------------


def evidence_items(name: str, *, limit: int = EVIDENCE_MAX_ITEMS) -> list[dict[str, str]]:
    """Strongest non-deprecated evidence rows as ``{id, type, title, summary, date}``.

    Reviewed and breakthrough entries come first, then by strength and date.
    """
    pool = profile_io.load_evidence_pool(name)
    if pool is None:
        return []
    rows = [e for e in pool.evidence_entries if e.title.strip() and not e.deprecated]

    def rank(e: Any) -> tuple:
        return (
            0 if e.breakthrough else 1,
            0 if e.review_status == "reviewed" else 1,
            _STRENGTH_RANK.get(e.strength, 4),
        )

    # Newest first, then the stable sort keeps that order within each rank.
    rows.sort(key=lambda e: e.date or "", reverse=True)
    out = []
    for entry in sorted(rows, key=rank)[:limit]:
        summary = " ".join((entry.summary or "").split())
        if len(summary) > EVIDENCE_SUMMARY_CHARS:
            summary = summary[: EVIDENCE_SUMMARY_CHARS - 1].rstrip() + "…"
        out.append(
            {
                "id": entry.id,
                "type": entry.type,
                "title": entry.title.strip(),
                "summary": summary,
                "date": entry.date,
            }
        )
    return out


def _evidence_block(items: list[dict[str, str]]) -> str:
    lines = []
    for item in items:
        line = f"- [{item['id']}] ({item['type']}{', ' + item['date'] if item['date'] else ''}) {item['title']}"
        if item["summary"]:
            line += f" — {item['summary']}"
        lines.append(line)
    return "\n".join(lines)


# --- JD match ------------------------------------------------------------------

_MATCH_SYSTEM = """\
你是资深技术招聘顾问。根据候选人的简历、可选的“工作证据”（候选人自己记录并审阅过的事实）\
和目标 JD，给出结构化的匹配分析。

铁律：
- 只依据提供的简历与证据判断，不得编造经历、指标或技能。
- 依据（basis）引用简历或证据里的具体事实；引用证据时在 evidence_refs 里写证据 id（方括号里的值）。
- 证据里有而简历没写的事实，放进 strengthen，并注明来自哪条证据。
- 回复语言与 JD 一致（中文 JD 用中文）。

只输出一个 JSON 对象，不要任何解释，格式：
{
  "score": 0-100 的整数,
  "summary": "两三句总体判断",
  "requirements": [
    {"requirement": "JD 中的一条关键要求", "verdict": "match|partial|missing",
     "basis": "依据（简历/证据中的事实，没有则写“简历未体现”）", "evidence_refs": ["证据 id"]}
  ],
  "strengthen": ["建议在简历中加强的具体内容（基于事实）"],
  "gaps": ["真实缺口：JD 需要但简历和证据都无法支撑的能力"],
  "keywords": ["建议在简历中自然出现的 JD 关键词"],
  "de_emphasize": ["与该岗位关系弱、可以弱化或删减的内容"],
  "interview_questions": [{"question": "高概率面试问题", "answer_hint": "基于候选人真实经历的作答要点"}]
}
requirements 6-12 条，按 JD 重要性排序；strengthen 3-6 条；interview_questions 5-8 条。"""


def _string_list(value: object, *, limit: int, max_len: int = 400) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text and text not in out:
            out.append(text[:max_len])
        if len(out) >= limit:
            break
    return out


def analyze_match(
    name: str,
    *,
    resume_md: str,
    jd_text: str,
    notes: str = "",
    use_evidence: bool = True,
) -> dict[str, Any]:
    """Structured JD match (LLM). Unknown evidence ids in the reply are dropped."""
    resume = str(resume_md or "").strip()
    jd = str(jd_text or "").strip()
    if not resume or not jd:
        raise CareerAIError("invalid_career_match_request", "简历和 JD 都不能为空。")
    _require_llm()
    evidence = evidence_items(name) if use_evidence else []
    known = {item["id"] for item in evidence}
    parts = [f"# 目标 JD\n{_clip(jd, JD_MAX_CHARS)}", f"# 候选人简历\n{_clip(resume, RESUME_MAX_CHARS)}"]
    if evidence:
        parts.append(f"# 工作证据\n{_evidence_block(evidence)}")
    if str(notes or "").strip():
        parts.append(f"# 候选人补充说明\n{_clip(notes, NOTES_MAX_CHARS)}")
    data = extract_json_value(_chat(_MATCH_SYSTEM, "\n\n".join(parts), temperature=0.2))
    if not isinstance(data, dict):
        raise CareerAIError("career_ai_failed", "模型返回格式不正确，请重试。")
    requirements = []
    for row in data.get("requirements") or []:
        if not isinstance(row, dict) or not str(row.get("requirement") or "").strip():
            continue
        verdict = str(row.get("verdict") or "").strip().lower()
        refs = [ref for ref in _string_list(row.get("evidence_refs"), limit=6, max_len=80) if ref in known]
        requirements.append(
            {
                "requirement": str(row["requirement"]).strip()[:300],
                "verdict": verdict if verdict in _VERDICTS else "partial",
                "basis": str(row.get("basis") or "").strip()[:500],
                "evidence_refs": refs,
            }
        )
    questions = []
    for row in data.get("interview_questions") or []:
        if isinstance(row, dict) and str(row.get("question") or "").strip():
            questions.append(
                {
                    "question": str(row["question"]).strip()[:300],
                    "answer_hint": str(row.get("answer_hint") or "").strip()[:600],
                }
            )
    try:
        score = max(0, min(100, int(round(float(data.get("score"))))))
    except (TypeError, ValueError):
        weights = {"match": 1.0, "partial": 0.5, "missing": 0.0}
        score = round(100 * sum(weights[r["verdict"]] for r in requirements) / max(len(requirements), 1))
    if not requirements:
        raise CareerAIError("career_ai_failed", "模型没有给出可用的匹配分析，请重试。")
    return {
        "method": "llm",
        "score": score,
        "summary": str(data.get("summary") or "").strip()[:800],
        "requirements": requirements,
        "strengthen": _string_list(data.get("strengthen"), limit=8),
        "gaps": _string_list(data.get("gaps"), limit=8),
        "keywords": _string_list(data.get("keywords"), limit=15, max_len=40),
        "de_emphasize": _string_list(data.get("de_emphasize"), limit=6),
        "interview_questions": questions[:8],
        "evidence": [item for item in evidence if item["id"] in {r for row in requirements for r in row["evidence_refs"]}],
        "evidence_used": len(evidence),
    }


# --- Tailored resume -------------------------------------------------------------

_TAILOR_SYSTEM = """\
你是资深简历顾问，为候选人针对目标 JD 改写一份定制简历。

铁律：
- 只使用简历、工作证据和候选人补充说明里的事实；不得编造公司、时间、职位、指标、论文或链接。
- 可以重排顺序、改写措辞、突出与 JD 相关的经历、补入证据中有据可查的成果、弱化无关内容。
- 保持一页纸篇幅；保留原简历的姓名、联系方式和时间线。
- 证据摘要若是英文，改写成与简历一致的语言，不要照搬。

输出格式：只输出 Markdown 正文，不要代码块、不要解释，并严格使用以下结构：
# 姓名 | 求职头衔
联系方式一行（用 | 分隔）
## 段落标题
### 单位 | 职位 | 起止时间
**分组标题**（可选）
- 条目"""


def tailor_resume(
    name: str,
    *,
    resume_md: str,
    jd_text: str,
    analysis: dict[str, Any] | None = None,
    notes: str = "",
    current_draft: str = "",
    use_evidence: bool = True,
) -> dict[str, Any]:
    """Return ``{markdown}``: a JD-tailored resume candidate (LLM)."""
    resume = str(resume_md or "").strip()
    jd = str(jd_text or "").strip()
    if not resume or not jd:
        raise CareerAIError("invalid_career_match_request", "简历和 JD 都不能为空。")
    _require_llm()
    evidence = evidence_items(name) if use_evidence else []
    parts = [f"# 目标 JD\n{_clip(jd, JD_MAX_CHARS)}", f"# 候选人主简历\n{_clip(resume, RESUME_MAX_CHARS)}"]
    if evidence:
        parts.append(f"# 工作证据\n{_evidence_block(evidence)}")
    if analysis:
        hints = []
        for key, label in (("strengthen", "建议加强"), ("de_emphasize", "建议弱化"), ("keywords", "关键词")):
            values = analysis.get(key) or []
            if values:
                hints.append(f"{label}：" + "；".join(str(v) for v in values))
        if hints:
            parts.append("# 匹配分析要点\n" + "\n".join(hints))
    if str(notes or "").strip():
        parts.append(f"# 候选人补充说明与修改要求\n{_clip(notes, NOTES_MAX_CHARS)}")
    if str(current_draft or "").strip():
        parts.append(
            "# 当前定制稿（候选人可能手改过，保留其有意的改动）\n" + _clip(current_draft, RESUME_MAX_CHARS)
        )
    markdown = _strip_fence(_chat(_TAILOR_SYSTEM, "\n\n".join(parts), temperature=0.3))
    if not markdown.lstrip().startswith("#"):
        raise CareerAIError("career_ai_failed", "模型没有返回简历正文，请重试。")
    return {"markdown": markdown.rstrip() + "\n"}


# --- Resume field recognition ----------------------------------------------------

_STRUCTURE_SYSTEM = """\
你把一份简历的纯文本（可能来自 PDF 提取，换行和顺序可能错乱）整理成结构化 JSON。
只搬运原文里的事实，不改写、不补充、不翻译；看不清的字段留空字符串。
只输出一个 JSON 对象：
{
  "basics": {"name": "", "title": "求职头衔", "tagline": "年龄/学历等抬头补充", "location": "",
             "phone": "", "email": "", "website": ""},
  "summary": "个人概要",
  "skill_groups": [{"label": "技能分类", "text": "该类技能，顿号分隔"}],
  "experiences": [{"company": "", "role": "", "start": "", "end": "", "bullets": [""],
                   "groups": [{"label": "分组标题", "bullets": [""]}]}],
  "projects": [{"name": "", "role": "", "start": "", "end": "", "bullets": [""]}],
  "education": [{"school": "", "degree": "专业 学位", "start": "", "end": ""}],
  "honors": [""]
}
经历内有“小标题 + 条目”的用 groups，否则用 bullets；没有的段落给空数组。"""


def structure_resume(name: str, text: str) -> dict[str, Any]:
    """LLM field recognition for unstructured resume text (PDF/DOCX extracts)."""
    clean = str(text or "").strip()
    if len(clean) < 40:
        raise CareerAIError("invalid_import", "简历文本太短，无法识别。")
    _require_llm()
    data = extract_json_value(_chat(_STRUCTURE_SYSTEM, _clip(clean, 20_000), temperature=0.0))
    if not isinstance(data, dict):
        raise CareerAIError("career_ai_failed", "模型返回格式不正确，请重试。")
    resume = resume_doc.normalize_resume(data, profile=name)
    resume["lang"] = resume_doc.detect_lang(resume)
    if not resume_doc.has_content(resume):
        raise CareerAIError("career_ai_failed", "没有识别出简历内容，请检查文本。")
    return resume
