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
import base64
import binascii
import re
from typing import Any

from nblane.core import llm as llm_client
from nblane.core import public_site, visual_candidate_store, visual_generation
from nblane.core.ai.messages import friendly_error
from nblane.core.ai_blog_prompts import get_prompt

REWRITE_OPERATIONS = ("polish", "shorten", "expand", "tone", "translate")

# Selections longer than this are refused rather than silently truncated:
# a rewrite that drops the tail of the user's text would be data loss.
SELECTION_MAX_CHARS = 6000
_CONTEXT_CHARS = 1800
_META_BODY_CHARS = 6000


_LANG_NAMES = {"zh": "简体中文", "en": "English"}
_LANG_NAMES_EN = {"zh": "Simplified Chinese", "en": "English"}
_CJK_CHAR = re.compile(r"[一-鿿]")
_LATIN_WORD = re.compile(r"[A-Za-z]+")


def script_language(text: str) -> str:
    """Main language of *text* by script share ('zh' or 'en').

    Unlike ``llm.reply_language`` (any CJK character means Chinese), an
    English post that mentions one Chinese term stays English, and a Chinese
    paragraph full of English acronyms stays Chinese.
    """
    cjk = len(_CJK_CHAR.findall(text))
    latin = len(_LATIN_WORD.findall(text))
    return "zh" if cjk >= latin else "en"


def article_language(text: str) -> str:
    """Prompt language for content AI: a fixed LLM_REPLY_LANG wins, else the text's."""
    mode = llm_client.reply_language_mode()
    return mode if mode in ("zh", "en") else script_language(text)


def translation_target(text: str) -> str:
    """Translate into the *other* language of the selection.

    The reply-language setting cannot be the target: in ``auto`` mode it
    follows the selection, so Chinese text was "translated" into Chinese.
    """
    return "en" if script_language(text) == "zh" else "zh"


def target_language_name(text: str, *, prompt_lang: str = "zh") -> str:
    names = _LANG_NAMES_EN if prompt_lang == "en" else _LANG_NAMES
    return names[translation_target(text)]


# Field labels inside the user prompt, in the prompt's language: English
# posts used to get Chinese labels and the model then drifted into Chinese.
_LABELS = {
    "zh": {
        "target_lang": "目标语言",
        "extra": "用户补充要求",
        "title": "文章标题",
        "context": "上下文（仅供参考，不要改写）",
        "target": "目标文本",
        "cur_title": "当前标题",
        "cur_summary": "当前摘要",
        "cur_tags": "当前标签",
        "body": "正文",
        "body_cut": "正文（较长，已省略中间部分）",
        "outline": "全文提纲",
        "omitted": "[……中间省略……]",
        "here": "[目标文本位置]",
    },
    "en": {
        "target_lang": "Target language",
        "extra": "Additional instructions",
        "title": "Article title",
        "context": "Context (for reference only; do not rewrite)",
        "target": "Target text",
        "cur_title": "Current title",
        "cur_summary": "Current summary",
        "cur_tags": "Current tags",
        "body": "Article",
        "body_cut": "Article (long; the middle is omitted)",
        "outline": "Outline",
        "omitted": "[... middle omitted ...]",
        "here": "[target text goes here]",
    },
}


def _label(lang: str, key: str) -> str:
    """``标签：`` / ``Label: `` for one prompt field."""
    labels = _LABELS["en" if lang == "en" else "zh"]
    return labels[key] + ("：" if lang != "en" else ": ")


class ContentAIError(RuntimeError):
    """Structured failure with a stable ``code`` for API error mapping."""

    def __init__(self, code: str, message: str, *, run_id: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        # Gateway run behind the failure (ai-runs.yaml), so the AI exceptions
        # panel can show one row instead of the run and its job.
        self.run_id = run_id


def _clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def _trim(text: str, limit: int) -> str:
    clean = _clean(text)
    return clean if len(clean) <= limit else clean[:limit].rstrip() + "…"


def _omitted(lang: str) -> str:
    return "\n\n" + _LABELS["en" if lang == "en" else "zh"]["omitted"] + "\n\n"


def _excerpt(text: str, limit: int, *, lang: str = "zh") -> tuple[str, bool]:
    """Fit a long body into *limit* chars without losing its ending.

    Keeps the heading outline, the opening (~60%) and the closing (~40%),
    cut at paragraph breaks where possible. Returns ``(text, truncated)``.
    """
    clean = _clean(text)
    if len(clean) <= limit:
        return clean, False
    headings = [line.strip() for line in clean.splitlines() if re.match(r"^#{1,3}\s+\S", line.strip())]
    outline = ""
    if len(headings) > 1:
        outline = _label(lang, "outline").rstrip() + "\n" + "\n".join(headings)
        if len(outline) > limit // 5:
            outline = ""
    marker = _omitted(lang)
    budget = max(limit - len(outline) - len(marker) * 2, limit // 2)
    head_len = int(budget * 0.6)
    tail_len = budget - head_len
    head = clean[:head_len]
    cut = head.rfind("\n\n")
    if cut > head_len // 2:
        head = head[:cut]
    tail = clean[-tail_len:]
    cut = tail.find("\n\n")
    if 0 <= cut < tail_len // 2:
        tail = tail[cut + 2 :]
    body = head.rstrip() + marker + tail.lstrip()
    return (f"{outline}\n\n{body}" if outline else body), True


def _context_window(context: str, selection: str, limit: int, *, lang: str = "zh") -> str:
    """Keep the paragraphs around the selection, not just the head.

    The editor sends neighbouring blocks *including* the selection; the
    selection itself is sent separately, so it is replaced by a marker here.
    """
    clean = _clean(context)
    target = _clean(selection)
    index = clean.find(target) if target else -1
    if index < 0:
        if len(clean) <= limit:
            return clean
        half = limit // 2
        return clean[:half].rstrip() + _omitted(lang) + clean[-half:].lstrip()
    half = limit // 2
    before = clean[:index][-half:]
    after = clean[index + len(target) :][:half]
    here = _LABELS["en" if lang == "en" else "zh"]["here"]
    return (before.rstrip() + f"\n\n{here}\n\n" + after.lstrip()).strip()


def _strip_fence(text: str, *, original: str = "") -> str:
    """Drop a fence the model wrapped around its whole reply.

    A selection that is itself a fenced block keeps its fence: the model
    returning it intact is correct, and stripping would turn code into prose.
    """
    raw = _clean(text)
    if _clean(original).startswith(("```", "~~~")):
        return raw
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


# One LLM call per content job, sized to finish inside that job's timeout in
# web_api/jobs.py (job timeout minus ~15s). No SDK retries: the default two
# silent retries could run up to 3x90s long after the job had already been
# reported as timed out, still billing.
REWRITE_LLM_TIMEOUT_SECONDS = 135.0
META_LLM_TIMEOUT_SECONDS = 105.0
SOCIAL_LLM_TIMEOUT_SECONDS = 135.0


def _run(
    action: str,
    system: str,
    user: str,
    *,
    profile: str,
    thinking: bool | None,
    timeout: float,
):
    """Run one content action through the AI gateway (run log + exceptions)."""

    from nblane.core.ai.gateway import run_ai_action

    result = run_ai_action(
        action,
        {
            "system": system,
            "user": user,
            "llm_timeout_seconds": timeout,
            "llm_max_retries": 0,
            "enable_thinking": thinking,
        },
        profile=profile or None,
        require_review=False,
    )
    if not result.ok:
        raise ContentAIError(
            "content_ai_failed", friendly_error(result.error or result.content), run_id=result.run_id
        )
    return result


_ERROR_PREFIX = re.compile(r"^[a-z_]+_error:\s*")


def generate_images(profile: str, asset_type: str, prompt: str, **options: Any) -> list[Any]:
    """Run one content image generation through the AI gateway.

    Returns the provider's ``GeneratedVisualAsset`` list; raises
    ``VisualGenerationError`` with the provider message on failure, so
    callers keep their existing error handling. Each call lands in
    ``ai-runs.yaml`` (metadata only) and failures in the AI exceptions panel.
    """

    from nblane.core.ai.gateway import run_ai_action

    result = run_ai_action(
        "content.image",
        {"asset_type": asset_type, "prompt": prompt, **options},
        profile=profile or None,
        require_review=False,
    )
    if not result.ok:
        message = _ERROR_PREFIX.sub("", result.error or "") or "图像生成失败，请重试。"
        error = visual_generation.VisualGenerationError(message)
        error.run_id = result.run_id  # type: ignore[attr-defined]
        raise error
    return list(result.artifacts)


def validate_reference_image(value: object) -> str:
    """Keep complete data URLs; never silently truncate image bytes."""
    clean = _clean(value)
    if len(clean) > 16 * 1024 * 1024:
        raise ContentAIError("invalid_reference_image", "参考图过大，请使用 12 MB 以内的图片。")
    if clean.startswith("data:"):
        try:
            header, encoded = clean.split(",", 1)
            if header not in {"data:image/png;base64", "data:image/jpeg;base64", "data:image/webp;base64", "data:image/gif;base64"}:
                raise ValueError("unsupported image")
            if not base64.b64decode(encoded, validate=True):
                raise ValueError("empty image")
        except (ValueError, binascii.Error) as exc:
            raise ContentAIError("invalid_reference_image", "参考图数据不完整或格式不支持。") from exc
    return clean


# --- Rewrite selection -------------------------------------------------------


def rewrite_selection(
    *,
    operation: str,
    selection: str,
    title: str = "",
    context: str = "",
    instruction: str = "",
    profile: str = "",
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
    lang = article_language(original)
    system = get_prompt("inline_system", lang)
    task = get_prompt(op, lang)
    extra = _clean(instruction)
    window = _context_window(context, original, _CONTEXT_CHARS, lang=lang) if _clean(context) else ""
    user = "\n\n".join(
        part
        for part in (
            task,
            _label(lang, "target_lang") + target_language_name(original, prompt_lang=lang) if op == "translate" else "",
            _label(lang, "extra") + extra if extra else "",
            _label(lang, "title") + _clean(title) if _clean(title) else "",
            _label(lang, "context").rstrip() + "\n" + window if window else "",
            _label(lang, "target").rstrip() + "\n" + original,
        )
        if part
    )
    result = _run(
        "content.rewrite",
        system,
        user,
        profile=profile,
        thinking=False if op != "expand" else None,
        timeout=REWRITE_LLM_TIMEOUT_SECONDS,
    )
    truncated = next((w for w in result.warnings if w.startswith("output_truncated")), "")
    if truncated:
        # A cut-off rewrite would replace the writer's text with half of it.
        raise ContentAIError(
            "content_ai_output_truncated",
            "AI 输出被截断，结果不完整，没有采用。请缩短选中的内容后重试；"
            + truncated.split(":", 1)[1].split("；", 1)[-1].strip(),
            run_id=result.run_id,
        )
    text = _strip_fence(result.content, original=original)
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


def suggest_meta(
    *, title: str, summary: str, tags: list[str], body: str, profile: str = ""
) -> dict[str, Any]:
    """Return ``{titles, summaries, tags}`` candidate lists for the post."""
    text = _clean(body)
    if len(text) < 40:
        raise ContentAIError("invalid_content_ai_request", "正文太短，先写一些内容再生成建议。")
    _require_llm()
    lang = article_language(text)
    system = _META_SYSTEM_ZH if lang == "zh" else _META_SYSTEM_EN
    task = _META_TASK_ZH if lang == "zh" else _META_TASK_EN
    excerpt, truncated = _excerpt(text, _META_BODY_CHARS, lang=lang)
    user = "\n\n".join(
        part
        for part in (
            task,
            _label(lang, "cur_title") + _clean(title) if _clean(title) else "",
            _label(lang, "cur_summary") + _clean(summary) if _clean(summary) else "",
            _label(lang, "cur_tags") + ", ".join(tags) if tags else "",
            _label(lang, "body_cut" if truncated else "body").rstrip() + "\n" + excerpt,
        )
        if part
    )
    data = _run(
        "content.meta", system, user, profile=profile, thinking=False, timeout=META_LLM_TIMEOUT_SECONDS
    ).structured
    if not isinstance(data, dict):
        raise ContentAIError("content_ai_failed", "模型返回格式不正确，请重试。")
    result = {
        "titles": _string_list(data.get("titles"), limit=3, max_len=120),
        "summaries": _string_list(data.get("summaries"), limit=3, max_len=400),
        "tags": _string_list(data.get("tags"), limit=6, max_len=30),
        "truncated": truncated,
    }
    if not (result["titles"] or result["summaries"] or result["tags"]):
        raise ContentAIError("content_ai_failed", "模型没有给出可用的建议，请重试。")
    return result


# --- Share copy (Xiaohongshu / X) ---------------------------------------------

_SOCIAL_SYSTEM = (
    "你是社交平台文案助手。只依据给定的文章内容写文案，不编造文中没有的事实、数字或经历，"
    "保持作者原本的语气，不要营销腔、不要堆砌感叹号和表情。只返回一个 JSON 对象，不要任何解释。"
)
_SOCIAL_SYSTEM_EN = (
    "You write share copy for social platforms. Use only the given article; never invent facts, "
    "numbers or experiences. Keep the author's voice: no marketing tone, no piles of exclamation "
    "marks or emoji. Return a single JSON object and nothing else."
)
_SOCIAL_TASK = (
    "为这篇文章准备分享文案：\n"
    '- "cover_titles"：3 个封面大标题备选，每个不超过 16 字，可用 \\n 分成 2–3 行；\n'
    '- "cover_subtitles"：3 句封面引文，从原文中逐字摘取（原样复制，不改写），每句不超过 40 字；\n'
    '- "xhs_title"：小红书笔记标题，不超过 20 字；\n'
    '- "xhs_body"：小红书正文，{xhs_length}，分 2–4 段，结尾附 3–5 个话题标签（#标签）；\n'
    '- "x_text"：X（Twitter）单条推文，不超过 120 个汉字，不带链接和话题标签。\n'
    '输出格式：{{"cover_titles": [...], "cover_subtitles": [...], "xhs_title": "", "xhs_body": "", "x_text": ""}}'
)
# English posts: the cover card and X follow the article; Xiaohongshu is a
# Chinese-language platform, so its title and body stay in Simplified Chinese.
_SOCIAL_TASK_EN = (
    "Prepare share copy for this article:\n"
    '- "cover_titles": 3 cover headline options in English, max 40 characters each; you may use \\n for 2-3 lines;\n'
    '- "cover_subtitles": 3 quotes copied word for word from the article (do not paraphrase), max 120 characters each;\n'
    '- "xhs_title": a Xiaohongshu note title in Simplified Chinese, max 20 Chinese characters;\n'
    '- "xhs_body": the Xiaohongshu note body in Simplified Chinese, {xhs_length}, 2-4 paragraphs, '
    "ending with 3-5 topic tags (#tag);\n"
    '- "x_text": one X (Twitter) post in English, max 260 characters, no links or hashtags.\n'
    'Output: {{"cover_titles": [...], "cover_subtitles": [...], "xhs_title": "", "xhs_body": "", "x_text": ""}}'
)
_SOCIAL_BODY_CHARS = 8000
# Below this the article is too short for a 200-500 字 note: asking for one
# made the model pad it with things the post never said.
_XHS_FULL_BODY_MIN_CHARS = 600
_QUOTE_NOISE = re.compile(r"[\W_]+", re.UNICODE)


def _xhs_length(text: str, lang: str) -> str:
    if len(text) >= _XHS_FULL_BODY_MIN_CHARS:
        return "200–500 字" if lang == "zh" else "200-500 Chinese characters"
    cap = max(60, len(text) // 2) if lang == "zh" else max(60, len(text) // 4)
    return (
        f"不超过 {cap} 字，只复述原文已有的内容"
        if lang == "zh"
        else f"at most {cap} Chinese characters, restating only what the article says"
    )


def _verbatim_quotes(quotes: list[str], source: str) -> list[str]:
    """Keep only quotes that really appear in the article.

    Compared without whitespace and punctuation, so a quote whose comma or
    full stop the model changed still counts; reworded ones are dropped.
    """
    haystack = _QUOTE_NOISE.sub("", source).casefold()
    kept: list[str] = []
    for quote in quotes:
        needle = _QUOTE_NOISE.sub("", quote).casefold()
        if len(needle) >= 4 and needle in haystack:
            kept.append(quote)
    return kept


def suggest_social_copy(*, title: str, body: str, profile: str = "") -> dict[str, Any]:
    """Return cover title/quote candidates plus Xiaohongshu and X copy."""
    text = _clean(body)
    if len(text) < 40:
        raise ContentAIError("invalid_content_ai_request", "正文太短，先写一些内容再生成文案。")
    _require_llm()
    lang = article_language(text)
    excerpt, truncated = _excerpt(text, _SOCIAL_BODY_CHARS, lang=lang)
    task = (_SOCIAL_TASK if lang == "zh" else _SOCIAL_TASK_EN).format(xhs_length=_xhs_length(text, lang))
    user = "\n\n".join(
        part
        for part in (
            task,
            _label(lang, "title") + _clean(title) if _clean(title) else "",
            _label(lang, "body_cut" if truncated else "body").rstrip() + "\n" + excerpt,
        )
        if part
    )
    data = _run(
        "content.social",
        _SOCIAL_SYSTEM if lang == "zh" else _SOCIAL_SYSTEM_EN,
        user,
        profile=profile,
        thinking=False,
        timeout=SOCIAL_LLM_TIMEOUT_SECONDS,
    ).structured
    if not isinstance(data, dict):
        raise ContentAIError("content_ai_failed", "模型返回格式不正确，请重试。")
    result = {
        "cover_titles": _string_list(data.get("cover_titles"), limit=3, max_len=60 if lang == "zh" else 80),
        "cover_subtitles": _verbatim_quotes(
            _string_list(data.get("cover_subtitles"), limit=3, max_len=120 if lang == "zh" else 200), text
        ),
        "xhs_title": _trim(_clean(data.get("xhs_title")), 40),
        "xhs_body": _trim(_clean(data.get("xhs_body")), 2000),
        "x_text": _trim(_clean(data.get("x_text")), 1000),
        "truncated": truncated,
        "lang": lang,
    }
    if not (result["cover_titles"] or result["xhs_body"] or result["x_text"]):
        raise ContentAIError("content_ai_failed", "模型没有给出可用的文案，请重试。")
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
    reference_image: str = "",
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
        assets = generate_images(
            profile,
            "cover",
            _clean(brief),
            style=_clean(style),
            title=post.title if title is None else _clean(title),
            summary=post.summary if summary is None else _clean(summary),
            tags=list(tags) if tags is not None else [str(t) for t in (post.meta.get("tags") or [])],
            body=post.body if body is None else str(body or ""),
            reference_image=_clean(reference_image),
        )
    except visual_generation.VisualGenerationError as exc:
        raise ContentAIError(
            "cover_generation_failed", str(exc), run_id=str(getattr(exc, "run_id", "") or "")
        ) from exc
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
