"""JD (job description) match analysis and one-page resume tailoring.

Builds an evidence-grounded match analysis between a target JD and the
profile's existing resume + work evidence, then generates a one-page
tailored resume. All LLM calls go through ``nblane.core.llm`` which returns
an error *string* (never raises) on failure, so callers can render directly.
"""

from __future__ import annotations

from pathlib import Path

from nblane.core import io
from nblane.core import llm as llm_client
from nblane.core.claims import accepted_claims_for_profile
from nblane.core.public_site import (
    GENERATED_RESUME_DIRNAME,
    RESUMES_DIRNAME,
    _profile_path,
)

_RESUME_LEADING_SKILL_MD = 1500
_RESUME_INPUT_MAX_CHARS = 8000
_CONTEXT_SOURCE_FILES = (
    "evidence-pool.yaml",
    "claims.yaml",
    "skill-tree.yaml",
    "SKILL.md",
)

# (name, max_evidence, max_chars) -> (fingerprint, rendered context)
_context_cache: dict[tuple[str, int, int], tuple[str, str]] = {}


def _clip_to_boundary(text: str, max_chars: int, *, marker: str = "") -> str:
    """Truncate at the last newline before ``max_chars`` to avoid mid-line cuts."""
    if len(text) <= max_chars:
        return text
    head = text[:max_chars]
    cut = head.rfind("\n")
    if cut > max_chars // 2:
        head = head[:cut]
    return head.rstrip() + marker


def _profile_fingerprint(name: str) -> str:
    """Cheap change token: concat of source-file mtimes (ns)."""
    pdir = _profile_path(name)
    parts: list[str] = []
    for filename in _CONTEXT_SOURCE_FILES:
        try:
            parts.append(f"{filename}:{(pdir / filename).stat().st_mtime_ns}")
        except OSError:
            parts.append(f"{filename}:0")
    return "|".join(parts)


def list_resume_md_files(name: str) -> list[Path]:
    """Return ``resume.md`` files under profiles/<name>/resumes/, excluding generated/."""
    root = _profile_path(name) / RESUMES_DIRNAME
    if not root.exists():
        return []
    out: list[Path] = []
    for path in sorted(root.rglob("resume.md")):
        if GENERATED_RESUME_DIRNAME in path.parts:
            continue
        out.append(path)
    return out



def read_resume_md(path: str | Path) -> str:
    """Read a resume markdown file, returning '' when missing."""
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def _evidence_lines(name: str, max_evidence: int) -> list[str]:
    """Format evidence-pool entries, strongest first."""
    pool = io.load_evidence_pool(name)
    if pool is None or not pool.evidence_entries:
        return []
    rank = {"high_trust": 0, "strong": 1, "medium": 2, "weak": 3, "": 4}
    entries = sorted(
        pool.evidence_entries,
        key=lambda e: rank.get(e.strength, 4),
    )
    lines: list[str] = []
    for e in entries[:max_evidence]:
        title = (e.title or "").strip()
        if not title:
            continue
        summary = " ".join((e.summary or "").split())
        if len(summary) > 240:
            summary = summary[:237].rstrip() + "..."
        suffix = f" ({e.strength})" if e.strength else ""
        bit = f"- [{e.type}] {title}"
        if summary:
            bit += f" — {summary}"
        lines.append(bit + suffix)
    return lines


def _claim_lines(name: str) -> list[str]:
    """Format accepted claims as bullet text."""
    lines: list[str] = []
    for claim in accepted_claims_for_profile(name):
        text = " ".join(str(claim.get("text", "") or "").split())
        if text:
            lines.append(f"- {text}")
    return lines


def _skill_lines(name: str) -> tuple[list[str], list[str]]:
    """Return (proven, in_progress) skill label lists from skill-tree."""
    tree = io.load_skill_tree_raw(name)
    if tree is None:
        return [], []
    schema_name = tree.get("schema", "") or ""
    schema = io.load_schema_raw(schema_name) if schema_name else None
    index = io.schema_node_index(schema) if schema else {}
    proven: list[str] = []
    in_progress: list[str] = []
    for node in tree.get("nodes") or []:
        nid = node.get("id", "")
        if not nid:
            continue
        label = index.get(nid, {}).get("label", nid)
        status = node.get("status", "locked")
        if status in ("solid", "expert"):
            proven.append(f"{label} ({status})")
        elif status == "learning":
            in_progress.append(f"{label} (learning)")
    return proven, in_progress


def gather_profile_context(
    name: str,
    *,
    max_evidence: int = 25,
    max_chars: int = 6000,
) -> str:
    """Assemble evidence + claims + skills + SKILL.md into one bounded block.

    Memoized by profile source-file mtimes so repeated analyze/generate calls
    within a session avoid re-reading and re-formatting the same files.
    """
    cache_key = (name, max_evidence, max_chars)
    fingerprint = _profile_fingerprint(name)
    cached = _context_cache.get(cache_key)
    if cached is not None and cached[0] == fingerprint:
        return cached[1]

    sections: list[str] = []

    ev = _evidence_lines(name, max_evidence)
    if ev:
        sections.append("## Work evidence\n" + "\n".join(ev))

    claims = _claim_lines(name)
    if claims:
        sections.append("## Accepted claims\n" + "\n".join(claims))

    proven, in_progress = _skill_lines(name)
    skill_bits: list[str] = []
    if proven:
        skill_bits.append("Proven: " + ", ".join(proven))
    if in_progress:
        skill_bits.append("In progress: " + ", ".join(in_progress))
    if skill_bits:
        sections.append("## Skills\n" + "\n".join(skill_bits))

    skill_md = io.load_skill_md(name).strip()
    if skill_md:
        clipped = _clip_to_boundary(skill_md, _RESUME_LEADING_SKILL_MD)
        sections.append("## Profile\n" + clipped)

    text = "\n\n".join(sections).strip()
    text = _clip_to_boundary(text, max_chars, marker="\n...[truncated]")
    result = text or "(no profile evidence available)"
    _context_cache[cache_key] = (fingerprint, result)
    return result


_ANALYZE_SYS_ZH = """\
你是一位资深技术招聘与简历顾问。你会收到一份目标 JD、候选人的现有简历，\
以及候选人的工作证据（evidence / claims / 技能树 / 档案）。

请严格基于提供的简历与证据进行分析，**不得编造任何经历、指标或技能**；\
若证据不足以支撑某项 JD 要求，判定为"部分符合"或"不符合"。

按以下结构输出 Markdown（用中文）：

## 匹配分析
一个 Markdown 表格，列为 `| JD要求 | 判定 | 依据 |`。\
从 JD 中逐条抽取关键要求，每条一行。\
判定只能是：✅ 符合 / ⚠️ 部分符合 / ❌ 不符合。\
依据要引用候选人简历或证据中的具体事实（无依据则写"简历未体现"）。

## 缺失的 Top 技能
列出 JD 需要但候选人尚缺或薄弱的 3-6 项关键技能，按重要性排序，\
每项给一句可执行的学习/补齐指引。

## 简历优化建议
3-6 条具体、基于证据的修改建议（如调整措辞、突出某段经历、量化某指标）。

## 面试问答知识点
针对该 JD 与候选人背景，给出 5-8 个高概率面试问题及简要作答要点（Q/A 形式）。

简明、具体、可操作。紧扣 JD 与候选人真实背景。"""

_ANALYZE_SYS_EN = """\
You are a senior technical recruiter and resume advisor. You receive a target \
JD, the candidate's current resume, and the candidate's work evidence \
(evidence / claims / skill tree / profile).

Analyze strictly from the provided resume and evidence. **Never fabricate \
experience, metrics, or skills.** If evidence is insufficient for a JD \
requirement, mark it "partial" or "no match".

Output Markdown with this structure (in English):

## Match Analysis
A Markdown table with columns `| JD Requirement | Verdict | Basis |`. \
Extract each key requirement from the JD, one row each. \
Verdict must be one of: ✅ Match / ⚠️ Partial / ❌ No match. \
The basis must cite concrete facts from the resume or evidence \
(write "not shown in resume" when absent).

## Missing Top Skills
List 3-6 key skills the JD needs but the candidate lacks or is weak in, \
ranked by importance, each with one actionable learning pointer.

## Resume Optimization Suggestions
3-6 concrete, evidence-grounded edits (rewording, emphasis, quantification).

## Interview Q&A Knowledge Points
5-8 high-probability interview questions with concise answer points (Q/A).

Be concise, specific, and actionable. Stay grounded in the real background."""


_RESUME_SYS_ZH = """\
你是一位简历定制专家。基于候选人的现有简历、工作证据，以及针对目标 JD 的\
匹配分析，生成一份**针对该 JD 优化的一页纸简历**。

硬性要求：
- 只输出简历 Markdown 本身，不要任何解释说明，不要代码围栏。
- 单页篇幅：总长 ≤ 约 55 行 / ≤ 约 3500 字符。
- 结构：标题(姓名+目标岗位) → 工作概要(3-4 句) → 核心技能 → 工作经历\
(最多 3 段，每段最多 3 条要点) → 教育/项目(仅在有空间时保留)。
- 每条要点 ≤ 2 行，尽量量化，并按 JD 调整措辞与关键词顺序。
- **不得编造**简历或证据中没有的经历与指标。"""

_RESUME_SYS_EN = """\
You are a resume tailoring expert. Using the candidate's current resume, work \
evidence, and the JD match analysis, produce a **one-page resume optimized \
for the target JD**.

Hard requirements:
- Output only the resume Markdown itself — no commentary, no code fences.
- One page: total ≤ ~55 lines / ≤ ~3500 characters.
- Structure: heading (name + target role) → summary (3-4 sentences) → core \
skills → experience (max 3 entries, max 3 bullets each) → education/projects \
(only if space remains).
- Each bullet ≤ 2 lines, quantified where possible, reworded/reordered to the JD.
- **Never fabricate** experience or metrics absent from the resume/evidence."""

_RESUME_STRICTER_ZH = (
    "\n\n注意：上一版偏长。请进一步精简到严格的一页（≤ 45 行 / ≤ 3000 字符），"
    "合并次要要点，只保留与 JD 最相关的内容。"
)
_RESUME_STRICTER_EN = (
    "\n\nNote: the previous version was too long. Compress further to a strict "
    "single page (≤ 45 lines / ≤ 3000 chars); merge minor bullets and keep only "
    "the most JD-relevant content."
)

_FOLLOWUP_SYS_ZH = """\
你是该候选人的简历与求职顾问。基于之前的 JD 匹配分析与简历内容，\
根据用户反馈进一步优化分析、建议或简历。只用已知的真实背景，不要编造。\
回复用中文，简明可操作。"""

_FOLLOWUP_SYS_EN = """\
You are the candidate's resume and job-search advisor. Building on the prior \
JD match analysis and resume, refine the analysis, suggestions, or resume per \
the user's feedback. Use only the known real background; do not fabricate. \
Reply in English, concise and actionable."""


def _lang() -> str:
    """Return the configured reply language ('zh' or 'en')."""
    return llm_client.reply_language()


def _clip_resume(resume_md: str) -> str:
    """Bound the pasted resume so an oversized paste can't blow up the prompt."""
    text = (resume_md or "").strip()
    if not text:
        return "(empty)"
    return _clip_to_boundary(text, _RESUME_INPUT_MAX_CHARS, marker="\n...[truncated]")


def analyze_jd(
    name: str,
    *,
    resume_md: str,
    jd_text: str,
    temperature: float = 0.3,
) -> str:
    """Run JD match analysis; returns Markdown (or llm error string)."""
    zh = _lang() == "zh"
    system = _ANALYZE_SYS_ZH if zh else _ANALYZE_SYS_EN
    context = gather_profile_context(name)
    user = (
        f"# Target JD\n{jd_text.strip()}\n\n"
        f"# Current resume\n{_clip_resume(resume_md)}\n\n"
        f"# Candidate evidence\n{context}"
    )
    return llm_client.chat(system, user, temperature=temperature)


def generate_one_page_resume_md(
    name: str,
    *,
    resume_md: str,
    jd_text: str,
    analysis_md: str,
    feedback_notes: str = "",
    stricter: bool = False,
    temperature: float = 0.2,
) -> str:
    """Generate a JD-tailored one-page resume Markdown (or llm error string).

    ``feedback_notes`` carries the user's chat feedback so refinement requests
    actually flow into the regenerated resume.
    """
    zh = _lang() == "zh"
    system = _RESUME_SYS_ZH if zh else _RESUME_SYS_EN
    context = gather_profile_context(name)
    user = (
        f"# Target JD\n{jd_text.strip()}\n\n"
        f"# Current resume\n{_clip_resume(resume_md)}\n\n"
        f"# Candidate evidence\n{context}\n\n"
        f"# JD match analysis\n{analysis_md.strip()}"
    )
    if feedback_notes.strip():
        label = "# 需要纳入的用户反馈" if zh else "# User feedback to incorporate"
        user += f"\n\n{label}\n{feedback_notes.strip()}"
    if stricter:
        user += _RESUME_STRICTER_ZH if zh else _RESUME_STRICTER_EN
    out = llm_client.chat(system, user, temperature=temperature)
    return _strip_code_fence(out)


def followup_system_prompt(lang: str) -> str:
    """Return the base feedback-refinement system prompt for the given language."""
    return _FOLLOWUP_SYS_ZH if str(lang).lower() == "zh" else _FOLLOWUP_SYS_EN


def build_followup_system(
    name: str,
    *,
    resume_md: str,
    jd_text: str,
    analysis_md: str,
    resume_preview: str = "",
) -> str:
    """Followup system prompt with the full JD/resume/evidence context baked in.

    The visible chat stays clean (only the analysis + user turns); the model
    still receives everything it needs to give grounded, resume-aware advice.
    """
    zh = _lang() == "zh"
    base = followup_system_prompt("zh" if zh else "en")
    context = gather_profile_context(name)
    blocks = [
        base,
        f"# Target JD\n{jd_text.strip()}",
        f"# Current resume\n{_clip_resume(resume_md)}",
        f"# Candidate evidence\n{context}",
        f"# Prior JD match analysis\n{analysis_md.strip()}",
    ]
    if resume_preview.strip():
        header = "# 当前生成的一页纸简历" if zh else "# Current generated one-page resume"
        blocks.append(f"{header}\n{_clip_resume(resume_preview)}")
    return "\n\n".join(blocks)



def _strip_code_fence(text: str) -> str:
    """Drop a leading/trailing markdown code fence if the model added one."""
    clean = text.strip()
    if clean.startswith("```"):
        lines = clean.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        clean = "\n".join(lines).strip()
    return clean
