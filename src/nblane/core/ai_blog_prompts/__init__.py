"""Central prompt registry for blog-editor AI actions."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files

PROMPT_LANGS = ("zh", "en")

PROMPT_ALIASES = {
    "formula": "nl_to_latex",
    "latex": "nl_to_latex",
    "diagram_prompt": "diagram",
}

REQUIRED_PROMPTS = (
    "inline_system",
    "polish",
    "rewrite",
    "shorten",
    "expand",
    "continue",
    "translate",
    "tone",
    "outline",
    "nl_to_latex",
    "diagram",
    "caption",
    "visual",
    "meta",
    "check",
    "scaffold",
    "scaffold_title",
    "scaffold_evidence",
    "scaffold_kanban_done",
)


def normalize_lang(lang: str | None) -> str:
    """Return a supported prompt language code."""
    return "zh" if str(lang or "").strip().lower() == "zh" else "en"


def normalize_prompt_name(name: str) -> str:
    """Normalize prompt aliases to file names."""
    clean = str(name or "").strip().lower().replace("-", "_").replace("/", "_")
    return PROMPT_ALIASES.get(clean, clean)


@lru_cache(maxsize=256)
def get_prompt(name: str, lang: str | None = None) -> str:
    """Return a prompt by *name* and language.

    Prompt files live under ``ai_blog_prompts/{zh,en}`` and are the single
    source for blog editor AI instructions. Missing non-English prompts fall
    back to English for runtime resilience; ``validate_prompt_sets`` can be
    used in tests or CI to enforce bilingual parity.
    """
    prompt_name = normalize_prompt_name(name)
    prompt_lang = normalize_lang(lang)
    for candidate_lang in (prompt_lang, "en"):
        path = files(__package__).joinpath(candidate_lang, f"{prompt_name}.md")
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
        if candidate_lang == "en":
            break
    raise KeyError(f"Unknown blog AI prompt: {prompt_name!r}")


def available_prompts(lang: str | None = None) -> set[str]:
    """Return prompt file stems available for *lang*."""
    prompt_lang = normalize_lang(lang)
    root = files(__package__).joinpath(prompt_lang)
    if not root.is_dir():
        return set()
    return {
        path.name.removesuffix(".md")
        for path in root.iterdir()
        if path.is_file() and path.name.endswith(".md")
    }


def validate_prompt_sets(
    required: tuple[str, ...] = REQUIRED_PROMPTS,
) -> dict[str, list[str]]:
    """Return missing prompt names by language."""
    missing: dict[str, list[str]] = {}
    normalized_required = {normalize_prompt_name(name) for name in required}
    for lang in PROMPT_LANGS:
        present = available_prompts(lang)
        absent = sorted(normalized_required - present)
        if absent:
            missing[lang] = absent
    return missing
