"""Compatibility page for the former Public Site workspace."""

from __future__ import annotations

import streamlit as st

from nblane.core import llm as llm_client
from nblane.web_auth import require_login
from nblane.web_shared import (
    apply_ui_language_from_session,
    render_current_goal_strip,
    render_git_backup_notices,
    render_page_help,
    select_profile,
)

apply_ui_language_from_session()


def _ui() -> dict[str, str]:
    if llm_client.ui_language() == "zh":
        return {
            "title": "Public Site 已拆分",
            "caption": "公开输出生产与站点构建现在是两个独立入口。",
            "page_help_short": "使用说明",
            "page_help_body": (
                "### Public Site 入口变化\n\n"
                "旧的 Public Site 页面已拆成两个工作台：\n\n"
                "1. **Output Studio**：编辑 Profile、Blog、Resume、Known Info，并从 evidence / claim 生成输出候选。\n"
                "2. **Public Build**：校验、预览和构建静态公开站点。\n\n"
                "这样可以避免“内容生成”和“发布构建”混在一个页面里。"
            ),
            "output": "打开 Output Studio",
            "build": "打开 Public Build",
            "output_help": "编辑 Profile、Blog、Resume、Known Info，并从 evidence / claim 生成输出。",
            "build_help": "校验、预览和构建静态公开站点。",
        }
    return {
            "title": "Public Site has moved",
            "caption": "Public output production and static-site build now live in separate workspaces.",
            "page_help_short": "Guide",
            "page_help_body": (
                "### Public Site split\n\n"
                "The old Public Site page has been split into two workspaces:\n\n"
                "1. **Output Studio** edits Profile, Blog, Resume, Known Info, and generates candidates from evidence / claims.\n"
                "2. **Public Build** validates, previews, and builds the static public site.\n\n"
                "This keeps content generation separate from release/build operations."
            ),
            "output": "Open Output Studio",
        "build": "Open Public Build",
        "output_help": "Edit Profile, Blog, Resume, Known Info, and generate output from evidence / claims.",
        "build_help": "Validate, preview, and build the static public site.",
    }


ui = _ui()
require_login()
selected = select_profile()
ui = _ui()
render_git_backup_notices()

head_l, head_goal = st.columns([5, 2], gap="medium", vertical_alignment="top")
with head_l:
    st.title(ui["title"])
    st.caption(ui["caption"])
with head_goal:
    render_current_goal_strip(selected, compact=True, align="right")
render_page_help(
    ui,
    key=f"public_site_help:{selected}",
    docs_path="docs/zh/guides/public-build.md",
)

c1, c2 = st.columns(2)
with c1:
    st.page_link(
        "pages/6_Output_Studio.py",
        label=ui["output"],
        help=ui["output_help"],
        icon=":material/edit_note:",
    )
with c2:
    st.page_link(
        "pages/10_Public_Build.py",
        label=ui["build"],
        help=ui["build_help"],
        icon=":material/rocket_launch:",
    )
