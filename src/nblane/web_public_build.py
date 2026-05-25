"""Public Build Streamlit page."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from nblane.core.public_site import (
    OUTPUTS_FILENAME,
    PROJECTS_FILENAME,
    PUBLIC_PROFILE_FILENAME,
    RESUME_SOURCE_FILENAME,
    build_public_site,
    init_public_layer,
    render_public_site_preview,
    validate_public_layer,
)
from nblane.core.io import profile_dir
from nblane.core.paths import REPO_ROOT
from nblane.web_auth import require_login
from nblane.web_cache import clear_web_cache
from nblane.web_shared import (
    apply_ui_language_from_session,
    ensure_file_snapshot,
    render_current_goal_strip,
    render_git_backup_notices,
    render_page_help,
    select_profile,
    stash_git_backup_results,
)
from nblane.core import llm as llm_client

apply_ui_language_from_session()


def _ui() -> dict[str, str]:
    if llm_client.ui_language() == "zh":
        return {
            "page_title": "Public Build · nblane",
            "title": "公开构建",
            "caption": "校验、预览并构建静态公开站点。",
            "page_help_short": "使用说明",
            "page_help_body": (
                "### 公开构建使用流程\n\n"
                "1. 输出工作台负责编辑公开资料和草稿；本页负责校验、预览和构建静态站点。\n"
                "2. 构建前先运行校验，处理错误后再生成站点。\n"
                "3. 预览可包含草稿 / 私有内容，但生产构建前应关闭该选项。\n"
                "4. 基准 URL 用生产域名或子路径，避免站内链接在部署后失效。\n"
                "5. 构建结果写入输出目录，部署脚本再把静态文件发布出去。\n\n"
                "公开构建是最后一道发布闸门，不负责生成新内容。"
            ),
            "init_needed": "此档案尚未初始化公开层。",
            "init": "初始化公开层",
            "include_drafts": "包含草稿 / 私有内容（预览）",
            "output_dir": "输出目录",
            "base_url": "基准 URL",
            "base_url_help": "生产部署域名，可包含子路径，例如 https://www.example.com/site。",
            "validate": "校验",
            "build_site": "构建静态站",
            "public_errors": "公开层校验错误",
            "public_ok": "公开层校验通过。",
            "validation_warnings": "校验警告",
            "site_preview": "整站预览",
            "preview_page": "预览页面",
            "preview_warnings": "预览提示",
            "built": "已构建：{path}",
        }
    return {
            "page_title": "Public Build · nblane",
            "title": "Public Build",
            "caption": "Validate, preview, and build the static public site.",
            "page_help_short": "Guide",
            "page_help_body": (
                "### Public Build workflow\n\n"
                "1. Output Studio edits public source files and drafts; this page validates, previews, and builds the static site.\n"
                "2. Run validation before build, fix errors, then build.\n"
                "3. Preview may include drafts/private content, but production builds should usually disable that option.\n"
                "4. Set Base URL to the production domain or sub-path so links remain valid after deployment.\n"
                "5. The build output goes to the selected directory; deployment scripts publish those static files.\n\n"
                "Public Build is the release gate, not a content generator."
            ),
            "init_needed": "This profile has not initialized its public layer.",
        "init": "Initialize public layer",
        "include_drafts": "Include drafts / private content for preview",
        "output_dir": "Output directory",
        "base_url": "Base URL",
        "base_url_help": "Production site URL, optionally with a sub-path, e.g. https://www.example.com/site.",
        "validate": "Validate",
        "build_site": "Build static site",
        "public_errors": "Public layer validation errors",
        "public_ok": "Public layer validation passed.",
        "validation_warnings": "Validation warnings",
        "site_preview": "Site preview",
        "preview_page": "Preview page",
        "preview_warnings": "Preview warnings",
        "built": "Built: {path}",
    }


def _preview_label(page: str, titles: dict[str, str]) -> str:
    title = titles.get(page, page)
    if page == "index.html":
        return f"{title} /"
    clean = page.removesuffix("index.html").rstrip("/")
    return f"{title} /{clean}/"


def _render_validation(selected: str, *, include_drafts: bool, ui: dict[str, str]) -> bool:
    result = validate_public_layer(selected, include_drafts=include_drafts)
    if result.warnings:
        with st.expander(ui["validation_warnings"], expanded=True):
            for warning in result.warnings:
                st.write(f"- {warning}")
    if result.errors:
        st.error(ui["public_errors"])
        for error in result.errors:
            st.write(f"- {error}")
        return False
    st.success(ui["public_ok"])
    return True


def _render_site_preview(selected: str, *, include_drafts: bool, ui: dict[str, str]) -> None:
    st.subheader(ui["site_preview"])
    try:
        preview = render_public_site_preview(selected, include_drafts=include_drafts)
    except Exception as exc:
        st.error(str(exc))
        return
    if preview.warnings:
        with st.expander(ui["preview_warnings"]):
            for warning in preview.warnings[:20]:
                st.write(f"- {warning}")
    pages = list(preview.pages)
    if not pages:
        st.info("-")
        return
    selected_page = st.selectbox(
        ui["preview_page"],
        pages,
        format_func=lambda page: _preview_label(page, preview.page_titles),
    )
    components.html(preview.pages[selected_page], height=760, scrolling=True)


def main() -> None:
    ui = _ui()
    require_login()
    selected = select_profile()
    ui = _ui()
    render_git_backup_notices()

    root = profile_dir(selected)
    required_paths = [
        root / PUBLIC_PROFILE_FILENAME,
        root / RESUME_SOURCE_FILENAME,
        root / PROJECTS_FILENAME,
        root / OUTPUTS_FILENAME,
    ]

    head_l, head_goal = st.columns([5, 2], gap="medium", vertical_alignment="top")
    with head_l:
        st.title(ui["title"])
        st.caption(ui["caption"])
    with head_goal:
        render_current_goal_strip(selected, compact=True, align="right")
    render_page_help(
        ui,
        key=f"public_build_help:{selected}",
        docs_path="docs/zh/guides/public-build.md",
    )

    if not all(path.exists() for path in required_paths):
        st.warning(ui["init_needed"])
        if st.button(ui["init"]):
            init_public_layer(selected)
            stash_git_backup_results()
            clear_web_cache()
            st.rerun()
        st.stop()

    for path in required_paths:
        ensure_file_snapshot(path)

    include_drafts = st.checkbox(ui["include_drafts"])
    out_dir = st.text_input(
        ui["output_dir"],
        value=str(REPO_ROOT / "dist" / "public" / selected),
    )
    base_url = st.text_input(ui["base_url"], value="", help=ui["base_url_help"])

    c_validate, c_build = st.columns(2)
    with c_validate:
        if st.button(ui["validate"]):
            _render_validation(selected, include_drafts=include_drafts, ui=ui)
    with c_build:
        if st.button(ui["build_site"], type="primary"):
            if _render_validation(selected, include_drafts=include_drafts, ui=ui):
                try:
                    result = build_public_site(
                        selected,
                        out_dir=out_dir,
                        include_drafts=include_drafts,
                        base_url=base_url,
                    )
                    st.success(ui["built"].format(path=result.output_dir))
                except Exception as exc:
                    st.error(str(exc))

    st.divider()
    _render_site_preview(selected, include_drafts=include_drafts, ui=ui)


if __name__ == "__main__":
    main()
