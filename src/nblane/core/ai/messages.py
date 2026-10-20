"""User-facing wording for AI gateway failures (shared by content and career AI)."""

from __future__ import annotations


def friendly_error(error: str) -> str:
    """Map a gateway error onto a message the writer can act on."""

    low = error.casefold()
    if "timed out" in low or "timeout" in low:
        return "AI 响应超时，请重试，或缩短选中的内容。"
    if "401" in low or "403" in low or "auth" in low or "api key" in low:
        return "模型服务鉴权失败，请到「设置 → AI 服务」检查 LLM 配置。"
    if "429" in low or "rate limit" in low or "quota" in low:
        return "模型服务繁忙（限流或额度不足），请稍后重试。"
    if error.startswith("output_truncated"):
        return error.split(":", 1)[1].strip()
    if error.startswith("validation_error"):
        return "模型返回格式不正确，请重试。"
    if error.startswith("ai_not_configured"):
        return "AI 功能需要配置 LLM（LLM_API_KEY / LLM_BASE_URL）。"
    return "AI 调用失败，请重试。如持续失败，可在首页「AI 异常」查看详情。"
