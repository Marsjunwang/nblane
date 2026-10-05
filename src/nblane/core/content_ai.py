"""AI helpers for the SPA content workspace (blog editor).

Every helper returns a *candidate* and never writes the post: the editor shows
the result, and only an explicit user action (accept / use as cover) changes
the document. Inputs are limited to the post itself (title, summary, tags,
body, selection) — no evidence, claims, skill tree or kanban are read, per the
content-workspace boundary in docs/zh/dev/public-output-workspaces-design.md.

Three capabilities:

* ``rewrite_selection`` — polish / shorten / expand / tone / translate one
  selected passage, reusing the blog editor prompts in ``ai_blog_prompts``.
* ``suggest_meta`` — structured title / summary / tag candidates (JSON), so
  the UI can offer click-to-apply chips instead of free-form Markdown.
* ``generate_cover_candidates`` / ``promote_cover`` / ``discard_cover`` —
  DashScope cover images staged under ``blog/.candidates`` until accepted.
"""

from __future__ import annotations

import uuid
from typing import Any

from nblane.core import llm as llm_client
from nblane.core import public_site, visual_candidate_store, visual_generation
from nblane.core.ai.structured import extract_json_value
from nblane.core.ai_blog_prompts import get_prompt

REWRITE_OPERATIONS = ("polish", "shorten", "expand", "tone", "translate")

# Selections longer than this are refused rather than silently truncated:
# a rewrite that drops the tail of the user's text would be data loss.
SELECTION_MAX_CHARS = 6000
_CONTEXT_CHARS = 1800
_META_BODY_CHARS = 6000

_LLM_ERROR_PREFIXES = ("LLM error:", "AI features not configured.")


class ContentAIError(RuntimeError):
    """Structured failure with a stable ``code`` for API error mapping."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def _trim(text: str, limit: int) -> str:
    clean = _clean(text)
    return clean if len(clean) <= limit else clean[:limit].rstrip() + "…"


def _strip_fence(text: str) -> str:
    raw = _clean(text)
    if raw.startswith("```") and raw.endswith("```"):
        lines = raw.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return raw


def llm_available() -> bool:
    return llm_client.is_configured()


def cover_available() -> bool:
    """True when an image provider is configured (no network call)."""
    try:
        return bool(visual_generation.current_config(mask_key=True)["configured"])
    except Exception:
        return False


def _require_llm() -> None:
    if not llm_client.is_configured():
        raise ContentAIError(
            "content_ai_unavailable",
            "AI 功能需要配置 LLM（LLM_API_KEY / LLM_BASE_URL）。",
        )


def _chat(system: str, user: str, *, temperature: float, thinking: bool | None) -> str:
    raw = llm_client.chat(system, user, temperature=temperature, enable_thinking=thinking)
    if raw.startswith(_LLM_ERROR_PREFIXES):
        raise ContentAIError("content_ai_failed", raw)
    return raw


# --- Rewrite selection -------------------------------------------------------


def rewrite_selection(
    *,
    operation: str,
    selection: str,
    title: str = "",
    context: str = "",
    instruction: str = "",
) -> dict[str, Any]:
    """Return ``{operation, original, text}`` for one selected passage."""
    op = _clean(operation).lower()
    if op not in REWRITE_OPERATIONS:
        raise ContentAIError("invalid_content_ai_request", f"Unsupported operation: {operation!r}")
    original = _clean(selection)
    if not original:
        raise ContentAIError("invalid_content_ai_request", "请先选中要改写的文字。")
    if len(original) > SELECTION_MAX_CHARS:
        raise ContentAIError(
            "invalid_content_ai_request",
            f"选中内容过长（上限 {SELECTION_MAX_CHARS} 字），请分段改写。",
        )
    _require_llm()
    lang = llm_client.reply_language(text=original)
    system = get_prompt("inline_system", lang)
    task = get_prompt(op, lang)
    extra = _clean(instruction)
    user = "\n\n".join(
        part
        for part in (
            task,
            f"用户补充要求：{extra}" if extra else "",
            f"文章标题：{_clean(title)}" if _clean(title) else "",
            f"上下文（仅供参考，不要改写）：\n{_trim(context, _CONTEXT_CHARS)}" if _clean(context) else "",
            f"目标文本：\n{original}",
        )
        if part
    )
    text = _strip_fence(
        _chat(system, user, temperature=0.3, thinking=False if op != "expand" else None)
    )
    if not text:
        raise ContentAIError("content_ai_failed", "模型没有返回内容，请重试。")
    return {"operation": op, "original": original, "text": text}


# --- Title / summary / tag suggestions -----------------------------------------

_META_SYSTEM_ZH = (
    "你是博客编辑助手。只依据给定的文章内容给出建议，不编造文中没有的事实、数字或经历。"
    "只返回一个 JSON 对象，不要任何解释。"
)
_META_SYSTEM_EN = (
    "You are a blog editing assistant. Base every suggestion only on the given article; "
    "never invent facts, numbers or experiences. Return a single JSON object and nothing else."
)
_META_TASK_ZH = (
    "为这篇文章给出：\n"
    '- "titles"：3 个标题备选，简洁具体，不超过 30 字；\n'
    '- "summaries"：3 个摘要备选，每个 1–2 句、60–120 字，说明文章讲什么、读者能得到什么；\n'
    '- "tags"：3–6 个标签，短词。\n'
    '输出格式：{"titles": [...], "summaries": [...], "tags": [...]}'
)
_META_TASK_EN = (
    "For this article provide:\n"
    '- "titles": 3 concise, specific title options (max 80 characters);\n'
    '- "summaries": 3 summary options, 1-2 sentences each, saying what the post covers and what the reader gets;\n'
    '- "tags": 3-6 short tags.\n'
    'Output: {"titles": [...], "summaries": [...], "tags": [...]}'
)


def _string_list(value: object, *, limit: int, max_len: int) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = _clean(item).strip("#").strip()
        if text and len(text) <= max_len and text not in out:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def suggest_meta(*, title: str, summary: str, tags: list[str], body: str) -> dict[str, Any]:
    """Return ``{titles, summaries, tags}`` candidate lists for the post."""
    text = _clean(body)
    if len(text) < 40:
        raise ContentAIError("invalid_content_ai_request", "正文太短，先写一些内容再生成建议。")
    _require_llm()
    lang = llm_client.reply_language(text=text)
    system = _META_SYSTEM_ZH if lang == "zh" else _META_SYSTEM_EN
    task = _META_TASK_ZH if lang == "zh" else _META_TASK_EN
    user = "\n\n".join(
        part
        for part in (
            task,
            f"当前标题：{_clean(title)}" if _clean(title) else "",
            f"当前摘要：{_clean(summary)}" if _clean(summary) else "",
            f"当前标签：{', '.join(tags)}" if tags else "",
            f"正文：\n{_trim(text, _META_BODY_CHARS)}",
        )
        if part
    )
    data = extract_json_value(_chat(system, user, temperature=0.5, thinking=False))
    if not isinstance(data, dict):
        raise ContentAIError("content_ai_failed", "模型返回格式不正确，请重试。")
    result = {
        "titles": _string_list(data.get("titles"), limit=3, max_len=120),
        "summaries": _string_list(data.get("summaries"), limit=3, max_len=400),
        "tags": _string_list(data.get("tags"), limit=6, max_len=30),
    }
    if not any(result.values()):
        raise ContentAIError("content_ai_failed", "模型没有给出可用的建议，请重试。")
    return result


# --- Cover images -------------------------------------------------------------


def generate_cover_candidates(
    profile: str,
    slug: str,
    *,
    brief: str = "",
    style: str = "",
    title: str | None = None,
    summary: str | None = None,
    tags: list[str] | None = None,
    body: str | None = None,
) -> list[dict[str, Any]]:
    """Generate cover images into the candidate store (post untouched).

    Live editor values (title/summary/body) override the saved post so the
    prompt reflects what the writer currently sees.
    """
    if not cover_available():
        raise ContentAIError(
            "cover_unavailable",
            "封面生成需要配置图像服务（VISUAL_API_KEY / DASHSCOPE_API_KEY）。",
        )
    post = public_site.load_blog_post(profile, slug)
    try:
        assets = visual_generation.generate_visual_asset(
            "cover",
            _clean(brief),
            style=_clean(style),
            title=post.title if title is None else _clean(title),
            summary=post.summary if summary is None else _clean(summary),
            tags=list(tags) if tags is not None else [str(t) for t in (post.meta.get("tags") or [])],
            body=post.body if body is None else str(body or ""),
        )
    except visual_generation.VisualGenerationError as exc:
        raise ContentAIError("cover_generation_failed", str(exc)) from exc
    patch_id = f"cover-{uuid.uuid4().hex[:10]}"
    rows: list[dict[str, Any]] = []
    for asset in assets:
        candidate = visual_candidate_store.write_candidate(
            profile,
            post.slug,
            patch_id,
            data=asset.data,
            filename=visual_generation.generated_filename("cover", asset.data, asset.extension),
            kind="image",
            alt=post.title,
            provider=asset.provider,
            model=asset.model,
            prompt=asset.prompt.positive_prompt,
        )
        rows.append(
            {
                "candidate_path": candidate.relative_path,
                "filename": candidate.filename,
                "provider": asset.provider,
                "model": asset.model,
            }
        )
    if not rows:
        raise ContentAIError("cover_generation_failed", "图像服务没有返回图片，请重试。")
    return rows


def promote_cover(profile: str, slug: str, candidate_path: str) -> dict[str, Any]:
    """Move one cover candidate into ``media/blog/<slug>/``; return the media row.

    The post's ``cover`` field is *not* written here: the editor sets it in
    its draft, and the next save persists it (keeps the editor's ETag valid).
    """
    post = public_site.load_blog_post(profile, slug)
    try:
        result = visual_candidate_store.promote_candidate(
            profile, post.slug, candidate_path, kind="image", alt=post.title
        )
    except FileNotFoundError as exc:
        raise ContentAIError("cover_candidate_not_found", str(exc)) from exc
    return {"path": result.relative_path, "snippet": result.snippet}


def discard_cover(profile: str, candidate_path: str) -> bool:
    return visual_candidate_store.discard_candidate(profile, candidate_path)
