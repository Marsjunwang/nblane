"""Streamlit UI strings for ``UI_LANG`` (en / zh).

Centralizes copy so all pages stay consistent with Gap Analysis.

Set ``NBLANE_UI_EMOJI=0`` (or ``false`` / ``no`` / ``off``) to drop
emoji prefixes in metrics and skill-status rows (see ``web_shared``).

Translation tables live as YAML files under ``nblane/i18n/<lang>/<section>.yaml``
and are loaded lazily on first access via ``importlib.resources``.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources

import yaml

from nblane.core import llm as llm_client


PRODUCT_POOL_KEYS: tuple[str, ...] = (
    "problem_pool",
    "project_pool",
    "evidence_pool",
    "method_pool",
    "decision_pool",
)


@lru_cache(maxsize=None)
def _section(name: str, lang: str) -> dict[str, str]:
    """Load a flat ``key -> value`` section for the given language.

    Falls back to English if the requested language file is missing.
    Returns an empty dict when neither language ships the section.
    """
    pkg = f"nblane.i18n.{lang}"
    try:
        text = resources.files(pkg).joinpath(f"{name}.yaml").read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        if lang != "en":
            return _section(name, "en")
        return {}
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def _load(name: str, lang: str) -> dict[str, str]:
    """Return the section for ``lang``, falling back to English."""
    table = _section(name, lang)
    if not table and lang != "en":
        return _section(name, "en")
    return table


def _lang() -> str:
    """Return ``en`` or ``zh``."""
    return llm_client.ui_language()


def _merged(*sections: str) -> dict[str, str]:
    lg = _lang()
    out: dict[str, str] = {}
    for sec in sections:
        out.update(_load(sec, lg))
    return out


def common_ui() -> dict[str, str]:
    """Strings shared by sidebar and several pages."""
    return dict(_load("common", _lang()))


def gap_ui() -> dict[str, str]:
    """Gap Analysis page (includes common status labels)."""
    return _merged("common", "gap")


def skill_tree_ui() -> dict[str, str]:
    """Skill Tree page."""
    return _merged("common", "skill_tree")


def evidence_review_ui() -> dict[str, str]:
    """Evidence Review page."""
    return _merged("common", "evidence_review")


def kanban_ui() -> dict[str, str]:
    """Kanban page."""
    return _merged("common", "kanban")


def team_ui() -> dict[str, str]:
    """Team View page."""
    return _merged("common", "team")


def profile_health_ui() -> dict[str, str]:
    """Profile Health page."""
    return _merged("common", "profile_health")


def review_ui() -> dict[str, str]:
    """Review page."""
    return _merged("common", "review")


def agent_activity_ui() -> dict[str, str]:
    """Agent Activity page."""
    return _merged("common", "agent_activity")


def project_board_ui() -> dict[str, str]:
    """Project Board page."""
    return _merged("common", "project_board")


def research_ui() -> dict[str, str]:
    """Research Source Inbox page."""
    return _merged("common", "research")


def home_ui() -> dict[str, str]:
    """Home (`app.py`) -- overview and SKILL.md editors."""
    lg = _lang()
    merged = dict(_load("common", lg))
    st_lines = _load("skill_tree", lg)
    for key in (
        "metric_expert",
        "metric_solid",
        "metric_learning",
        "metric_locked",
        "metric_lit_rate",
        "progress_overall",
    ):
        merged[key] = st_lines[key]
    merged.update(_load("home", lg))
    return merged


def status_label(ui: dict[str, str], raw: str) -> str:
    """Map schema status value to a display label."""
    return ui.get(f"status_{raw}", raw)


def kanban_section_label(section: str) -> str:
    """Display label for a kanban column key."""
    return _load("kanban_sec", _lang()).get(section, section)


def pool_label(pool_key: str) -> str:
    """Display label for a product-pool key."""
    return _load("pool_label", _lang()).get(pool_key, pool_key)


def all_pool_keys() -> tuple[str, ...]:
    """Stable key order for product-pool tabs."""
    return PRODUCT_POOL_KEYS


def kanban_move_option_label(opt: str, ui: dict[str, str]) -> str:
    """Label for move-to selectbox (stay or section key)."""
    if opt == "(stay)":
        return ui["kb_stay"]
    return kanban_section_label(opt)
