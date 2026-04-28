"""Public site, blog, and resume management page."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
import yaml

from nblane.core import llm as llm_client

try:
    from streamlit_crepe import st_milkdown
except Exception:  # pragma: no cover - optional Streamlit component
    st_milkdown = None

try:
    from nblane.public_blog_editor_component import (
        st_blocknote_markdown,
        st_public_blog_editor,
    )
except Exception:  # pragma: no cover - optional Streamlit component
    st_blocknote_markdown = None
    st_public_blog_editor = None

from nblane.core import git_backup
from nblane.core.public_curation import (
    evidence_contexts,
    group_project,
    suggest_groups,
)
from nblane.core.public_site import (
    BLOG_DIRNAME,
    BLOG_IMAGE_EXTENSIONS,
    BLOG_IMAGE_MAX_BYTES,
    BLOG_INSERT_MARKER,
    BLOG_VIDEO_EXTENSIONS,
    BLOG_VIDEO_MAX_BYTES,
    MEDIA_DIRNAME,
    OUTPUTS_FILENAME,
    PROJECTS_FILENAME,
    PUBLIC_PROFILE_FILENAME,
    PublicSiteError,
    RESUME_SOURCE_FILENAME,
    add_blog_media_bytes,
    blog_candidate_from_evidence,
    blog_candidate_from_kanban_done,
    blog_candidate_from_title,
    build_public_site,
    create_blog_draft,
    draft_blog_from_evidence,
    draft_blog_from_kanban_done,
    draft_project_update,
    draft_resume_for_target,
    format_blog_document,
    init_public_layer,
    insert_blog_snippet,
    load_blog_posts,
    load_public_profile,
    load_projects,
    load_resume_source,
    markdown_contains_math,
    parse_blog_post,
    render_public_site_preview,
    render_resume_markdown,
    save_blog_post,
    validate_blog_text_for_publish,
    validate_public_layer,
)
from nblane.core.io import profile_dir
from nblane.core.paths import REPO_ROOT
from nblane.web_auth import require_login
from nblane.web_cache import clear_web_cache
from nblane.web_shared import (
    apply_ui_language_from_session,
    assert_files_current,
    ensure_file_snapshot,
    refresh_file_snapshots,
    render_git_backup_notices,
    select_profile,
    stash_git_backup_results,
)

apply_ui_language_from_session()


def _ui() -> dict[str, str]:
    if llm_client.ui_language() == "zh":
        return {
            "page_title": "公开站点 · nblane",
            "title": "公开站点",
            "caption": "管理个人网站、博客、公开简历与发布构建。",
            "init_needed": "此档案尚未初始化公开层。",
            "init": "初始化公开层",
            "profile": "Profile",
            "blog": "Blog",
            "resume": "Resume",
            "curation": "Known Info",
            "build": "Build",
            "save": "保存",
            "saved": "已保存。",
            "validate": "校验",
            "build_site": "构建静态站",
            "include_drafts": "包含草稿 / 私有内容（预览）",
            "public_errors": "公开层校验错误",
            "public_ok": "公开层校验通过。",
            "new_blog": "新建博客草稿",
            "title_label": "标题",
            "create": "创建",
            "publish": "发布",
            "preview": "预览",
            "post": "文章",
            "status": "状态",
            "all_statuses": "全部状态",
            "date": "日期",
            "summary": "摘要",
            "cover": "封面",
            "body": "正文",
            "blocknote_unavailable": "BlockNote 组件不可用，已降级为 Markdown 富文本编辑器。",
            "rich_editor_unavailable": "未安装 streamlit-crepe，已降级为 Markdown 文本编辑。",
            "math_safe_mode": "公式安全模式",
            "math_safe_help": "使用 Markdown 源码编辑器，避免公式在 BlockNote 转换中被改写。",
            "math_safe_notice": "检测到公式，已使用 Markdown 源码编辑器。",
            "tags_help": "用逗号分隔",
            "related_evidence": "关联 evidence",
            "related_kanban": "关联看板项",
            "insert_marker": "插入位置标记",
            "media": "媒体",
            "upload_media": "上传图片或短视频",
            "media_kind": "媒体类型",
            "alt_text": "替代文本",
            "caption": "说明",
            "set_cover": "设为封面",
            "insert_into_post": "插入正文",
            "add_media": "添加媒体",
            "video_url": "视频 URL",
            "insert_video_url": "插入视频 URL",
            "snippet": "可粘贴片段",
            "publish_ready": "发布前检查通过。",
            "site_post_preview": "公开页预览",
            "draft_from_evidence": "从 evidence 生成博客草稿",
            "draft_from_done": "从 Done 生成博客草稿",
            "evidence_id": "Evidence ID",
            "target": "目标岗位 / 方向",
            "draft_resume": "生成定制简历草稿",
            "project_id": "Project ID",
            "draft_update": "生成项目更新草稿",
            "output_dir": "输出目录",
            "base_url": "Base URL",
            "base_url_help": "生产部署域名，可包含子路径，例如 https://www.example.com/site。",
            "avatar_upload": "上传头像",
            "profile_fields": "公开资料",
            "visibility": "可见性",
            "public_name": "公开姓名",
            "english_name": "英文名",
            "headline": "一句话标题",
            "bio_short": "简介",
            "avatar_path": "头像路径",
            "contact_email": "邮箱",
            "contact_wechat": "微信",
            "contact_github": "GitHub",
            "contact_linkedin": "LinkedIn",
            "contact_google_scholar": "Google Scholar",
            "contact_zhihu": "知乎",
            "contact_website": "个人网站",
            "raw_yaml": "原始 YAML",
            "site_preview": "整站预览",
            "preview_page": "预览页面",
            "preview_warnings": "预览提示",
            "save_profile": "保存公开资料",
            "curation_caption": "把零散 evidence 人工聚合成公开项目草稿。",
            "evidence": "Evidence",
            "suggest_groups": "推荐分组",
            "create_project_group": "生成项目草稿",
            "project_summary": "项目摘要",
            "tags": "标签（逗号分隔）",
            "current_projects": "当前公开项目",
            "keep_evidence_refs": "保留的 evidence_refs",
            "update_project_refs": "更新项目 evidence_refs",
            "articles": "文章",
            "editor": "编辑器",
            "tools": "工具",
            "meta": "Meta",
            "ai": "AI",
            "check": "Check",
            "left_panel": "文章栏",
            "right_panel": "工具栏",
            "focus_mode": "专注",
            "exit_focus": "退出专注",
            "public_preview": "公开预览",
            "media_library": "媒体库",
            "selected_media": "所选媒体",
            "use_selected_media": "插入所选媒体",
            "no_media": "暂无媒体",
            "unreferenced_media": "未引用媒体",
            "ai_candidate": "候选内容",
            "draft_from_title": "根据当前标题生成完整候选",
            "generate_candidate": "生成候选",
            "insert_candidate": "插入标记处",
            "append_candidate": "追加到文末",
            "apply_candidate_meta": "应用摘要和标签",
            "use_full_candidate": "使用完整候选",
            "discard_candidate": "丢弃候选",
            "candidate_empty": "候选内容为空。",
            "cover_prompt": "封面 Prompt",
            "candidate_warnings": "候选风险提示",
            "validation_errors": "校验错误",
            "validation_warnings": "校验警告",
            "quality_warnings": "内容质量提醒",
            "no_issues": "暂无问题。",
            "missing_summary": "缺少摘要。",
            "missing_cover": "缺少封面。",
            "missing_tags": "缺少标签。",
            "leftover_insert_marker": "正文仍包含插入位置标记。",
            "privacy_hint": "正文疑似引用了内部原始文件或私密路径。",
            "markdown_downgrade": "当前使用 Markdown 兼容编辑器；块级编辑会在 React / BlockNote 组件落地后启用。",
            "candidate_saved": "候选已写入正文。",
            "compact_layout": "窄屏模式",
        }
    return {
        "page_title": "Public Site · nblane",
        "title": "Public Site",
        "caption": "Manage your personal website, blog, public resume, and build output.",
        "init_needed": "This profile has not initialized its public layer.",
        "init": "Initialize public layer",
        "profile": "Profile",
        "blog": "Blog",
        "resume": "Resume",
        "curation": "Known Info",
        "build": "Build",
        "save": "Save",
        "saved": "Saved.",
        "validate": "Validate",
        "build_site": "Build static site",
        "include_drafts": "Include drafts / private content for preview",
        "public_errors": "Public layer validation errors",
        "public_ok": "Public layer validation passed.",
        "new_blog": "New blog draft",
        "title_label": "Title",
        "create": "Create",
        "publish": "Publish",
        "preview": "Preview",
        "post": "Post",
        "status": "Status",
        "all_statuses": "All statuses",
        "date": "Date",
        "summary": "Summary",
        "cover": "Cover",
        "body": "Body",
        "blocknote_unavailable": "BlockNote component is unavailable; using the rich Markdown editor.",
        "rich_editor_unavailable": "streamlit-crepe is not installed; using the Markdown text editor.",
        "math_safe_mode": "Math-safe mode",
        "math_safe_help": "Use the Markdown source editor so formulas are not rewritten by BlockNote conversion.",
        "math_safe_notice": "Formulas detected; using the Markdown source editor.",
        "tags_help": "Comma-separated",
        "related_evidence": "Related evidence",
        "related_kanban": "Related kanban",
        "insert_marker": "Insert marker",
        "media": "Media",
        "upload_media": "Upload image or short video",
        "media_kind": "Media kind",
        "alt_text": "Alt text",
        "caption": "Caption",
        "set_cover": "Use as cover",
        "insert_into_post": "Insert into post",
        "add_media": "Add media",
        "video_url": "Video URL",
        "insert_video_url": "Insert video URL",
        "snippet": "Snippet",
        "publish_ready": "Publish check passed.",
        "site_post_preview": "Public page preview",
        "draft_from_evidence": "Draft blog from evidence",
        "draft_from_done": "Draft blog from Done",
        "evidence_id": "Evidence ID",
        "target": "Target role / direction",
        "draft_resume": "Draft targeted resume",
        "project_id": "Project ID",
        "draft_update": "Draft project update",
        "output_dir": "Output directory",
        "base_url": "Base URL",
        "base_url_help": "Production site URL, optionally with a sub-path, e.g. https://www.example.com/site.",
        "avatar_upload": "Upload avatar",
        "profile_fields": "Public profile fields",
        "visibility": "Visibility",
        "public_name": "Public name",
        "english_name": "English name",
        "headline": "Headline",
        "bio_short": "Short bio",
        "avatar_path": "Avatar path",
        "contact_email": "Email",
        "contact_wechat": "WeChat",
        "contact_github": "GitHub",
        "contact_linkedin": "LinkedIn",
        "contact_google_scholar": "Google Scholar",
        "contact_zhihu": "Zhihu",
        "contact_website": "Website",
        "raw_yaml": "Raw YAML",
        "site_preview": "Site preview",
        "preview_page": "Preview page",
        "preview_warnings": "Preview warnings",
        "save_profile": "Save public profile",
        "curation_caption": "Manually aggregate atomic evidence into public project drafts.",
        "evidence": "Evidence",
        "suggest_groups": "Suggested groups",
        "create_project_group": "Create project draft",
        "project_summary": "Project summary",
        "tags": "Tags (comma-separated)",
        "current_projects": "Current projects",
        "keep_evidence_refs": "Evidence refs to keep",
        "update_project_refs": "Update project evidence_refs",
        "articles": "Articles",
        "editor": "Editor",
        "tools": "Tools",
        "meta": "Meta",
        "ai": "AI",
        "check": "Check",
        "left_panel": "Article panel",
        "right_panel": "Tool drawer",
        "focus_mode": "Focus",
        "exit_focus": "Exit focus",
        "public_preview": "Public preview",
        "media_library": "Media library",
        "selected_media": "Selected media",
        "use_selected_media": "Insert selected media",
        "no_media": "No media yet",
        "unreferenced_media": "Unreferenced media",
        "ai_candidate": "Candidate",
        "draft_from_title": "Generate full candidate from current title",
        "generate_candidate": "Generate candidate",
        "insert_candidate": "Insert at marker",
        "append_candidate": "Append to end",
        "apply_candidate_meta": "Apply summary and tags",
        "use_full_candidate": "Use full candidate",
        "discard_candidate": "Discard candidate",
        "candidate_empty": "Candidate is empty.",
        "cover_prompt": "Cover prompt",
        "candidate_warnings": "Candidate warnings",
        "validation_errors": "Validation errors",
        "validation_warnings": "Validation warnings",
        "quality_warnings": "Quality warnings",
        "no_issues": "No issues.",
        "missing_summary": "Summary is missing.",
        "missing_cover": "Cover is missing.",
        "missing_tags": "Tags are missing.",
        "leftover_insert_marker": "Body still contains the insert marker.",
        "privacy_hint": "Body may reference internal raw files or private paths.",
        "markdown_downgrade": "Using the Markdown-compatible editor; block editing will be enabled by the future React / BlockNote component.",
        "candidate_saved": "Candidate was written into the body.",
        "compact_layout": "Compact layout",
    }


def _path(name: str, filename: str) -> Path:
    return profile_dir(name) / filename


def _save_text(
    path: Path,
    content: str,
    *,
    action: str,
    message: str,
) -> None:
    assert_files_current([path])
    path.write_text(content, encoding="utf-8")
    git_backup.record_change([path], action=action)
    refresh_file_snapshots([path])
    stash_git_backup_results()
    clear_web_cache()
    st.success(message)
    st.rerun()


def _render_yaml_editor(
    *,
    key: str,
    path: Path,
    label: str,
    selected: str,
    ui: dict[str, str],
) -> None:
    ensure_file_snapshot(path)
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    edited = st.text_area(
        label,
        value=content,
        height=360,
        key=key,
    )
    if st.button(ui["save"], key=f"{key}_save"):
        _save_text(
            path,
            edited,
            action=f"update {selected}/{path.name}",
            message=ui["saved"],
        )


def _first_existing_avatar(root: Path) -> str:
    """Return a conventional avatar path if an uploaded file already exists."""
    media_dir = root / MEDIA_DIRNAME
    for suffix in ("jpg", "jpeg", "png", "webp"):
        path = media_dir / f"avatar.{suffix}"
        if path.exists() and path.is_file():
            return f"{MEDIA_DIRNAME}/{path.name}"
    return ""


def _local_media_path(root: Path, rel: str) -> Path | None:
    """Resolve a profile media path for preview if it is local and safe."""
    clean = rel.strip()
    if not clean or clean.startswith(("http://", "https://")):
        return None
    media_root = (root / MEDIA_DIRNAME).resolve()
    target = (root / clean).resolve()
    try:
        target.relative_to(media_root)
    except ValueError:
        return None
    if target.exists() and target.is_file():
        return target
    return None


def _profile_contacts(profile_data: dict) -> dict:
    contacts = profile_data.get("contacts") or {}
    return contacts if isinstance(contacts, dict) else {}


def _profile_widget_key(selected: str, field: str) -> str:
    return f"public_profile:{selected}:{field}"


def _render_profile_form(
    *,
    selected: str,
    root: Path,
    ui: dict[str, str],
) -> tuple[dict, dict[str, bytes]]:
    """Render structured public-profile.yaml controls."""
    public_path = _path(selected, PUBLIC_PROFILE_FILENAME)
    profile_data = load_public_profile(selected)
    contacts = _profile_contacts(profile_data)
    avatar_value = str(
        profile_data.get("avatar", "") or _first_existing_avatar(root)
    )

    st.subheader(ui["profile_fields"])
    visibility_options = ["private", "public"]
    visibility = str(profile_data.get("visibility", "private") or "private")
    if visibility not in visibility_options:
        visibility = "private"
    new_visibility = st.selectbox(
        ui["visibility"],
        visibility_options,
        index=visibility_options.index(visibility),
        key=_profile_widget_key(selected, "visibility"),
    )
    new_public_name = st.text_input(
        ui["public_name"],
        value=str(profile_data.get("public_name", "") or selected),
        key=_profile_widget_key(selected, "public_name"),
    )
    new_english_name = st.text_input(
        ui["english_name"],
        value=str(profile_data.get("english_name", "") or ""),
        key=_profile_widget_key(selected, "english_name"),
    )
    new_headline = st.text_input(
        ui["headline"],
        value=str(profile_data.get("headline", "") or ""),
        key=_profile_widget_key(selected, "headline"),
    )
    new_bio = st.text_area(
        ui["bio_short"],
        value=str(profile_data.get("bio_short", "") or ""),
        height=120,
        key=_profile_widget_key(selected, "bio_short"),
    )
    new_avatar = st.text_input(
        ui["avatar_path"],
        value=avatar_value,
        key=_profile_widget_key(selected, "avatar"),
    )
    uploaded = st.file_uploader(
        ui["avatar_upload"],
        type=["png", "jpg", "jpeg", "webp"],
        key=_profile_widget_key(selected, "avatar_upload"),
    )
    c1, c2 = st.columns(2)
    with c1:
        email = st.text_input(
            ui["contact_email"],
            value=str(contacts.get("email", "") or ""),
            key=_profile_widget_key(selected, "email"),
        )
        wechat = st.text_input(
            ui["contact_wechat"],
            value=str(contacts.get("wechat", "") or ""),
            key=_profile_widget_key(selected, "wechat"),
        )
        github = st.text_input(
            ui["contact_github"],
            value=str(contacts.get("github", "") or ""),
            key=_profile_widget_key(selected, "github"),
        )
        linkedin = st.text_input(
            ui["contact_linkedin"],
            value=str(contacts.get("linkedin", "") or ""),
            key=_profile_widget_key(selected, "linkedin"),
        )
    with c2:
        google_scholar = st.text_input(
            ui["contact_google_scholar"],
            value=str(contacts.get("google_scholar", "") or ""),
            key=_profile_widget_key(selected, "google_scholar"),
        )
        zhihu = st.text_input(
            ui["contact_zhihu"],
            value=str(contacts.get("zhihu", "") or ""),
            key=_profile_widget_key(selected, "zhihu"),
        )
        website = st.text_input(
            ui["contact_website"],
            value=str(contacts.get("website", "") or ""),
            key=_profile_widget_key(selected, "website"),
        )

    avatar_path: Path | None = None
    media_overrides: dict[str, bytes] = {}
    if uploaded is not None:
        suffix = Path(uploaded.name).suffix.lower() or ".jpg"
        if suffix not in (".png", ".jpg", ".jpeg", ".webp"):
            suffix = ".jpg"
        avatar_path = root / MEDIA_DIRNAME / f"avatar{suffix}"
        new_avatar = f"{MEDIA_DIRNAME}/{avatar_path.name}"
        media_overrides[new_avatar] = uploaded.getvalue()

    profile_override = {
        "profile": selected,
        "visibility": new_visibility,
        "public_name": new_public_name.strip() or selected,
        "english_name": new_english_name.strip(),
        "headline": new_headline.strip(),
        "avatar": new_avatar.strip(),
        "bio_short": new_bio.strip(),
        "contacts": {
            "email": email.strip(),
            "wechat": wechat.strip(),
            "github": github.strip(),
            "linkedin": linkedin.strip(),
            "google_scholar": google_scholar.strip(),
            "zhihu": zhihu.strip(),
            "website": website.strip(),
        },
        "featured": profile_data.get(
            "featured",
            {"projects": [], "outputs": [], "posts": []},
        ),
    }

    if st.button(ui["save_profile"], type="primary"):
        assert_files_current([public_path])
        latest = load_public_profile(selected)
        latest.update(profile_override)
        latest.setdefault("featured", {"projects": [], "outputs": [], "posts": []})

        changed_paths = [public_path]
        if avatar_path is not None:
            avatar_path.parent.mkdir(parents=True, exist_ok=True)
            avatar_path.write_bytes(media_overrides[new_avatar])
            changed_paths.append(avatar_path)
        public_path.write_text(
            yaml.dump(
                latest,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        git_backup.record_change(
            changed_paths,
            action=f"update {selected} public profile",
        )
        refresh_file_snapshots([public_path])
        stash_git_backup_results()
        clear_web_cache()
        st.success(ui["saved"])
        st.rerun()

    return profile_override, media_overrides


def _preview_label(page: str, titles: dict[str, str]) -> str:
    title = titles.get(page, page)
    if page == "index.html":
        return f"{title} /"
    clean = page.removesuffix("index.html").rstrip("/")
    return f"{title} /{clean}/"


def _render_site_preview(
    *,
    selected: str,
    profile_override: dict,
    media_overrides: dict[str, bytes],
    ui: dict[str, str],
) -> None:
    """Render the in-memory public site preview."""
    st.subheader(ui["site_preview"])
    try:
        preview = render_public_site_preview(
            selected,
            include_drafts=True,
            public_profile_override=profile_override,
            media_overrides=media_overrides,
        )
    except Exception as exc:
        st.error(str(exc))
        return
    if preview.warnings:
        with st.expander(ui["preview_warnings"]):
            for warning in preview.warnings[:20]:
                st.write(f"- {warning}")
            if len(preview.warnings) > 20:
                st.write(f"- ... {len(preview.warnings) - 20} more")
    pages = list(preview.pages)
    if not pages:
        st.info("-")
        return
    selected_page = st.selectbox(
        ui["preview_page"],
        pages,
        format_func=lambda page: _preview_label(page, preview.page_titles),
        key=f"public_site_preview_page:{selected}",
    )
    components.html(
        preview.pages[selected_page],
        height=760,
        scrolling=True,
    )


def _render_validation(
    selected: str,
    *,
    include_drafts: bool,
    ui: dict[str, str],
) -> bool:
    result = validate_public_layer(
        selected,
        include_drafts=include_drafts,
    )
    if result.errors:
        st.error(ui["public_errors"])
        for error in result.errors:
            st.write(f"- {error}")
        return False
    st.success(ui["public_ok"])
    return True


def _blog_publish_candidate(text: str) -> str:
    """Return Markdown with front matter status set to published."""
    meta: dict = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            loaded = yaml.safe_load(parts[1]) or {}
            if isinstance(loaded, dict):
                meta = loaded
                body = parts[2].lstrip()
    meta["status"] = "published"
    return (
        "---\n"
        + yaml.dump(
            meta,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
        + "---\n\n"
        + body
    )


def _csv_values(value: object) -> list[str]:
    """Return a compact list from comma/newline-separated UI text."""
    if isinstance(value, list):
        raw = ",".join(str(item) for item in value)
    else:
        raw = str(value or "")
    return [
        item.strip()
        for chunk in raw.splitlines()
        for item in chunk.split(",")
        if item.strip()
    ]


def _csv_text(values: object) -> str:
    """Render list-like front matter values as editable CSV text."""
    if not isinstance(values, list):
        return ""
    return ", ".join(str(item) for item in values if str(item).strip())


def _blog_editor_key(selected: str, slug: str, field: str) -> str:
    return f"blog_editor:{selected}:{slug}:{field}"


def _blog_status_index(status: str) -> int:
    options = ["draft", "published", "archived"]
    return options.index(status) if status in options else 0


_BLOG_RIGHT_TABS = ("Meta", "Media", "AI", "Check")
_BLOG_RIGHT_TAB_ICONS = {
    "Meta": "M",
    "Media": "▧",
    "AI": "AI",
    "Check": "✓",
}


def _blog_layout_storage_key(selected: str, slug: str) -> str:
    return f"public_blog_editor:{selected}:{slug}"


def _default_blog_layout_state() -> dict:
    return {
        "left_open": True,
        "right_open": True,
        "active_right_tab": "Meta",
        "focus_mode": False,
        "preview_open": False,
    }


def _coerce_blog_layout_state(raw: object) -> dict:
    state = _default_blog_layout_state()
    if not isinstance(raw, dict):
        return state
    for key in ("left_open", "right_open", "focus_mode", "preview_open"):
        if key in raw:
            state[key] = bool(raw.get(key))
    active_tab = str(raw.get("active_right_tab", state["active_right_tab"]))
    if active_tab in _BLOG_RIGHT_TABS:
        state["active_right_tab"] = active_tab
    for key in ("left_before_focus", "right_before_focus"):
        if key in raw:
            state[key] = bool(raw.get(key))
    return state


def _read_blog_layout_query_state(storage_key: str) -> dict:
    try:
        raw = st.query_params.get(storage_key)
    except Exception:
        raw = None
    if isinstance(raw, list):
        raw = raw[-1] if raw else None
    if not raw:
        return {}
    try:
        loaded = json.loads(str(raw))
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _blog_layout_state(selected: str, slug: str) -> dict:
    storage_key = _blog_layout_storage_key(selected, slug)
    if storage_key not in st.session_state:
        st.session_state[storage_key] = _coerce_blog_layout_state(
            _read_blog_layout_query_state(storage_key)
        )
    return _coerce_blog_layout_state(st.session_state.get(storage_key))


def _persist_blog_layout_state(
    selected: str,
    slug: str,
    state: dict,
) -> None:
    storage_key = _blog_layout_storage_key(selected, slug)
    clean_state = _coerce_blog_layout_state(state)
    st.session_state[storage_key] = clean_state
    payload = json.dumps(clean_state, ensure_ascii=False, separators=(",", ":"))
    try:
        st.query_params[storage_key] = payload
    except Exception:
        pass
    components.html(
        """
<script>
try {
  window.localStorage.setItem(%s, JSON.stringify(%s));
} catch (err) {}
</script>
"""
        % (json.dumps(storage_key), payload),
        height=0,
    )


def _rerun_with_blog_layout(
    selected: str,
    slug: str,
    state: dict,
) -> None:
    _persist_blog_layout_state(selected, slug, state)
    st.rerun()


def _set_right_blog_tab(
    selected: str,
    slug: str,
    state: dict,
    tab: str,
) -> None:
    next_state = dict(state)
    if next_state.get("right_open") and next_state.get("active_right_tab") == tab:
        next_state["right_open"] = False
    else:
        next_state["right_open"] = True
        next_state["active_right_tab"] = tab
    next_state["focus_mode"] = False
    _rerun_with_blog_layout(selected, slug, next_state)


def _toggle_focus_blog_layout(
    selected: str,
    slug: str,
    state: dict,
) -> None:
    next_state = dict(state)
    if next_state.get("focus_mode"):
        next_state["focus_mode"] = False
        next_state["left_open"] = bool(next_state.get("left_before_focus", True))
        next_state["right_open"] = bool(next_state.get("right_before_focus", True))
    else:
        next_state["left_before_focus"] = bool(next_state.get("left_open", True))
        next_state["right_before_focus"] = bool(next_state.get("right_open", True))
        next_state["focus_mode"] = True
        next_state["left_open"] = False
        next_state["right_open"] = False
    _rerun_with_blog_layout(selected, slug, next_state)


def _blog_check_state_key(selected: str, slug: str) -> str:
    return _blog_editor_key(selected, slug, "check_state")


def _blog_ai_candidate_key(selected: str, slug: str) -> str:
    return _blog_editor_key(selected, slug, "ai_candidate")


def _blog_shell_key(selected: str, slug: str, field: str) -> str:
    return _blog_editor_key(selected, slug, f"shell_{field}")


def _blog_shell_source_token(meta: dict, body: str) -> str:
    text = format_blog_document(meta, body)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _blog_shell_prepare_state(
    selected: str,
    slug: str,
    meta: dict,
    body: str,
) -> tuple[dict, str]:
    """Return the current shell draft meta/body, initializing from disk."""
    token = _blog_shell_source_token(meta, body)
    source_key = _blog_shell_key(selected, slug, "source")
    dirty_key = _blog_shell_key(selected, slug, "dirty")
    meta_key = _blog_shell_key(selected, slug, "meta")
    body_key = _blog_shell_key(selected, slug, "body")
    if (
        st.session_state.get(source_key) != token
        and not st.session_state.get(dirty_key, False)
    ):
        st.session_state[source_key] = token
        st.session_state[meta_key] = dict(meta)
        st.session_state[body_key] = body
    st.session_state.setdefault(meta_key, dict(meta))
    st.session_state.setdefault(body_key, body)
    return dict(st.session_state.get(meta_key) or {}), str(
        st.session_state.get(body_key) or ""
    )


def _blog_shell_store_draft(
    selected: str,
    slug: str,
    meta: dict,
    body: str,
    *,
    dirty: bool,
) -> None:
    """Persist an in-browser React shell draft into session state."""
    st.session_state[_blog_shell_key(selected, slug, "meta")] = dict(meta)
    st.session_state[_blog_shell_key(selected, slug, "body")] = body
    st.session_state[_blog_shell_key(selected, slug, "dirty")] = dirty


def _blog_shell_clear_draft(selected: str, slug: str) -> None:
    for field in ("source", "meta", "body", "dirty"):
        key = _blog_shell_key(selected, slug, field)
        if key in st.session_state:
            del st.session_state[key]


def _blog_shell_posts_payload(posts: list) -> list[dict]:
    """Return compact post rows for the React shell."""
    return [
        {
            "slug": post.slug,
            "title": post.title,
            "date": post.date,
            "status": post.status,
            "summary": post.summary,
        }
        for post in posts
    ]


def _blog_shell_ai_candidates(selected: str, slug: str) -> list[dict]:
    """Return candidate rows stored by the Streamlit AI helpers."""
    candidate = str(st.session_state.get(_blog_ai_candidate_key(selected, slug), "") or "")
    meta_key = _blog_editor_key(selected, slug, "ai_candidate_meta")
    candidate_meta = st.session_state.get(meta_key)
    if not candidate.strip() and not isinstance(candidate_meta, dict):
        return []
    row = {
        "id": "current",
        "body": candidate,
    }
    if isinstance(candidate_meta, dict):
        row.update(candidate_meta)
    return [row]


def _blog_shell_event_payload(
    event: dict,
    fallback_meta: dict,
    fallback_body: str,
) -> tuple[str, dict, str, bool]:
    """Extract action/meta/body/dirty from a React shell event."""
    action = str(event.get("action") or "")
    payload = event.get("payload")
    payload = payload if isinstance(payload, dict) else {}
    meta = payload.get("meta")
    if not isinstance(meta, dict):
        meta = fallback_meta
    body = payload.get("markdown")
    if not isinstance(body, str):
        body = event.get("markdown")
    if not isinstance(body, str):
        body = fallback_body
    dirty = bool(payload.get("dirty", event.get("dirty", False)))
    return action, dict(meta), body, dirty


def _blog_media_library(root: Path, slug: str, meta: dict, body: str) -> list[dict]:
    """Return local media rows for one blog post."""
    media_dir = root / MEDIA_DIRNAME / BLOG_DIRNAME / slug
    if not media_dir.exists():
        return []
    cover = str(meta.get("cover", "") or "")
    rows: list[dict] = []
    for path in sorted(media_dir.iterdir()):
        if not path.is_file():
            continue
        ext = path.suffix.lower().lstrip(".")
        if ext in BLOG_IMAGE_EXTENSIONS:
            kind = "image"
        elif ext in BLOG_VIDEO_EXTENSIONS:
            kind = "video"
        else:
            continue
        rel = path.resolve().relative_to(root.resolve()).as_posix()
        rows.append(
            {
                "name": path.name,
                "kind": kind,
                "path": path,
                "relative_path": rel,
                "size_kb": round(path.stat().st_size / 1024, 1),
                "referenced": rel in body or rel == cover,
            }
        )
    return rows


def _media_snippet(kind: str, rel: str, alt: str = "", caption: str = "") -> str:
    if kind == "image":
        return f"![{alt or caption}]({rel})"
    return f"::video[{caption or alt}]({rel})"


def _blog_quality_warnings(
    *,
    meta: dict,
    body: str,
    media_rows: list[dict],
    ui: dict[str, str],
) -> list[str]:
    warnings: list[str] = []
    if not str(meta.get("summary", "") or "").strip():
        warnings.append(ui["missing_summary"])
    if not str(meta.get("cover", "") or "").strip():
        warnings.append(ui["missing_cover"])
    tags = meta.get("tags")
    if not isinstance(tags, list) or not [tag for tag in tags if str(tag).strip()]:
        warnings.append(ui["missing_tags"])
    if BLOG_INSERT_MARKER in body:
        warnings.append(ui["leftover_insert_marker"])
    private_markers = (
        "profiles/",
        "evidence-pool.yaml",
        "agent-profile.yaml",
        "skill-tree.yaml",
        "kanban.md",
        "auth/users.yaml",
        "resume-source.yaml",
    )
    if any(marker in body for marker in private_markers):
        warnings.append(ui["privacy_hint"])
    for row in media_rows:
        if not row["referenced"]:
            warnings.append(f"{ui['unreferenced_media']}: {row['name']}")
    if st_blocknote_markdown is None and st_milkdown is None:
        warnings.append(ui["markdown_downgrade"])
    return warnings


def _run_blog_publish_check(
    *,
    selected: str,
    post_path: Path,
    slug: str,
    meta: dict,
    body: str,
    media_rows: list[dict],
    ui: dict[str, str],
) -> dict:
    candidate = format_blog_document(meta, body)
    result = validate_blog_text_for_publish(selected, post_path, candidate)
    check_state = {
        "errors": list(result.errors),
        "warnings": list(result.warnings),
        "quality": _blog_quality_warnings(
            meta=meta,
            body=body,
            media_rows=media_rows,
            ui=ui,
        ),
    }
    st.session_state[_blog_check_state_key(selected, slug)] = check_state
    return check_state


def _render_body_editor(
    *,
    selected: str,
    slug: str,
    body: str,
    ui: dict[str, str],
) -> str:
    """Render the preferred rich Markdown editor with text-area fallback."""
    key = _blog_editor_key(selected, slug, "body")
    body_token = hashlib.sha1(body.encode("utf-8")).hexdigest()[:12]
    math_key = _blog_editor_key(selected, slug, "math_safe")
    math_detected = markdown_contains_math(body)
    if math_detected:
        st.session_state[math_key] = True
    math_safe = st.checkbox(
        ui["math_safe_mode"],
        value=bool(st.session_state.get(math_key, False)),
        key=math_key,
        help=ui["math_safe_help"],
        disabled=math_detected,
    )
    if math_detected or math_safe:
        if math_detected:
            st.info(ui["math_safe_notice"])
        return st.text_area(
            ui["body"],
            value=body,
            height=520,
            key=f"{key}:math_safe:{body_token}",
        )
    if st_blocknote_markdown is not None:
        edited = st_blocknote_markdown(
            initial_markdown=body,
            document_id=f"{selected}:{slug}",
            height=560,
            key=f"{key}:blocknote",
        )
        if isinstance(edited, str):
            return edited
    else:
        st.info(ui["blocknote_unavailable"])
    if st_milkdown is not None:
        try:
            edited = st_milkdown(
                default_value=body,
                min_height=520,
                features={
                    "image": True,
                    "link": True,
                    "table": True,
                    "codeblock": True,
                    "math": False,
                },
                key=key,
            )
            return edited if isinstance(edited, str) else body
        except Exception as exc:
            st.warning(f"{ui['rich_editor_unavailable']} {exc}")
    else:
        st.info(ui["rich_editor_unavailable"])
    return st.text_area(
        ui["body"],
        value=body,
        height=520,
        key=f"{key}:fallback:{body_token}",
    )


def _blog_page_preview(selected: str, slug: str, ui: dict[str, str]) -> None:
    """Render the generated public blog detail page preview."""
    st.subheader(ui["site_post_preview"])
    try:
        preview = render_public_site_preview(
            selected,
            include_drafts=True,
        )
    except Exception as exc:
        st.error(str(exc))
        return
    page = f"blog/{slug}/index.html"
    if page not in preview.pages:
        st.info("-")
        return
    components.html(
        preview.pages[page],
        height=760,
        scrolling=True,
    )


def _persist_blog_editor(
    *,
    selected: str,
    post_path: Path,
    meta: dict,
    body: str,
    ui: dict[str, str],
) -> None:
    """Save one structured blog editor state."""
    assert_files_current([post_path])
    saved, changed = save_blog_post(
        selected,
        post_path.stem,
        meta,
        body,
        action=f"update {selected}/blog/{post_path.name}",
    )
    refresh_file_snapshots([saved, *changed])
    stash_git_backup_results()
    clear_web_cache()
    st.success(ui["saved"])


def _save_blog_editor(
    *,
    selected: str,
    post_path: Path,
    meta: dict,
    body: str,
    ui: dict[str, str],
) -> None:
    """Save one structured blog editor state and rerun."""
    _persist_blog_editor(
        selected=selected,
        post_path=post_path,
        meta=meta,
        body=body,
        ui=ui,
    )
    _blog_shell_clear_draft(selected, post_path.stem)
    st.rerun()


def _render_blog_react_shell(
    *,
    selected: str,
    root: Path,
    posts: list,
    latest_post,
    original_meta: dict,
    layout_state: dict,
    ui: dict[str, str],
) -> bool:
    """Render the React Blog Editor shell and dispatch returned actions."""
    if st_public_blog_editor is None:
        return False

    draft_meta, draft_body = _blog_shell_prepare_state(
        selected,
        latest_post.slug,
        original_meta,
        latest_post.body,
    )
    media_rows = _blog_media_library(
        root,
        latest_post.slug,
        draft_meta,
        draft_body,
    )
    check_state = st.session_state.get(
        _blog_check_state_key(selected, latest_post.slug),
        {"errors": [], "warnings": [], "quality": []},
    )
    math_safe = markdown_contains_math(draft_body)
    event = st_public_blog_editor(
        posts=_blog_shell_posts_payload(posts),
        active_slug=latest_post.slug,
        initial_markdown=draft_body,
        active_post_meta=draft_meta,
        media_items=media_rows,
        ai_candidates=_blog_shell_ai_candidates(selected, latest_post.slug),
        validation_state=check_state,
        layout_state=layout_state,
        ui_labels=ui,
        document_id=f"{selected}:{latest_post.slug}",
        layout_storage_key=_blog_layout_storage_key(selected, latest_post.slug),
        key=_blog_editor_key(selected, latest_post.slug, "react_shell"),
        height=760,
        editable=True,
        math_safe=math_safe,
        source_mode=math_safe,
    )

    with st.expander(ui["new_blog"], expanded=False):
        new_title = st.text_input(
            ui["title_label"],
            key=f"react_new_blog_title:{selected}",
        )
        if st.button(ui["create"], key=f"react_create_blog:{selected}"):
            if new_title.strip():
                path = create_blog_draft(
                    selected,
                    title=new_title.strip(),
                    body=f"{BLOG_INSERT_MARKER}\n\n",
                    summary="",
                )
                st.session_state[f"blog_post_slug_select:{selected}"] = path.stem
                stash_git_backup_results()
                clear_web_cache()
                st.rerun()
            st.warning(ui["title_label"])
        evidence_id = st.text_input(
            ui["evidence_id"],
            key=f"react_blog_evidence_id:{selected}",
        )
        draft_cols = st.columns(2)
        with draft_cols[0]:
            if st.button(
                ui["draft_from_evidence"],
                key=f"react_blog_draft_from_evidence:{selected}",
                use_container_width=True,
            ):
                try:
                    path = draft_blog_from_evidence(selected, evidence_id.strip())
                    st.session_state[f"blog_post_slug_select:{selected}"] = path.stem
                    stash_git_backup_results()
                    clear_web_cache()
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with draft_cols[1]:
            if st.button(
                ui["draft_from_done"],
                key=f"react_blog_draft_from_done:{selected}",
                use_container_width=True,
            ):
                try:
                    path = draft_blog_from_kanban_done(selected)
                    st.session_state[f"blog_post_slug_select:{selected}"] = path.stem
                    stash_git_backup_results()
                    clear_web_cache()
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with st.expander(ui["upload_media"], expanded=False):
        _render_blog_media_panel(
            selected=selected,
            root=root,
            latest_post=latest_post,
            edited_meta=draft_meta,
            edited_body=draft_body,
            media_rows=media_rows,
            ui=ui,
        )

    if not isinstance(event, dict):
        return True

    action, event_meta, event_body, dirty = _blog_shell_event_payload(
        event,
        draft_meta,
        draft_body,
    )
    event_layout = event.get("layout_state")
    if isinstance(event_layout, dict):
        _persist_blog_layout_state(selected, latest_post.slug, event_layout)

    if action in {
        "markdown_changed",
        "layout_state_changed",
        "insert_media",
        "insert_candidate",
        "apply_candidate_meta",
    }:
        _blog_shell_store_draft(
            selected,
            latest_post.slug,
            event_meta,
            event_body,
            dirty=dirty,
        )
        return True

    if action == "select_post":
        _blog_shell_store_draft(
            selected,
            latest_post.slug,
            event_meta,
            event_body,
            dirty=dirty,
        )
        payload = event.get("payload")
        payload = payload if isinstance(payload, dict) else {}
        slug = str(payload.get("slug", "") or "")
        if slug and slug != latest_post.slug:
            st.session_state[f"blog_post_slug_select:{selected}"] = slug
            st.rerun()
        return True

    if action == "generate_ai_candidate":
        try:
            candidate = blog_candidate_from_title(
                selected,
                str(event_meta.get("title", "") or latest_post.title),
            )
            st.session_state[
                _blog_ai_candidate_key(selected, latest_post.slug)
            ] = candidate.body
            st.session_state[
                _blog_editor_key(selected, latest_post.slug, "ai_candidate_meta")
            ] = candidate.to_dict()
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
        return True

    if action == "run_check":
        _blog_shell_store_draft(
            selected,
            latest_post.slug,
            event_meta,
            event_body,
            dirty=dirty,
        )
        _run_blog_publish_check(
            selected=selected,
            post_path=latest_post.path,
            slug=latest_post.slug,
            meta=event_meta,
            body=event_body,
            media_rows=media_rows,
            ui=ui,
        )
        next_state = dict(layout_state)
        next_state["right_open"] = True
        next_state["active_right_tab"] = "Check"
        next_state["focus_mode"] = False
        _rerun_with_blog_layout(selected, latest_post.slug, next_state)
        return True

    if action == "save_post":
        _blog_shell_store_draft(
            selected,
            latest_post.slug,
            event_meta,
            event_body,
            dirty=dirty,
        )
        try:
            _persist_blog_editor(
                selected=selected,
                post_path=latest_post.path,
                meta=event_meta,
                body=event_body,
                ui=ui,
            )
            _blog_shell_clear_draft(selected, latest_post.slug)
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
        return True

    if action == "publish_request":
        publish_meta = dict(event_meta)
        publish_meta["status"] = "published"
        _blog_shell_store_draft(
            selected,
            latest_post.slug,
            publish_meta,
            event_body,
            dirty=True,
        )
        final_media_rows = _blog_media_library(
            root,
            latest_post.slug,
            publish_meta,
            event_body,
        )
        check = _run_blog_publish_check(
            selected=selected,
            post_path=latest_post.path,
            slug=latest_post.slug,
            meta=publish_meta,
            body=event_body,
            media_rows=final_media_rows,
            ui=ui,
        )
        if check["errors"]:
            next_state = dict(layout_state)
            next_state["right_open"] = True
            next_state["active_right_tab"] = "Check"
            next_state["focus_mode"] = False
            _rerun_with_blog_layout(selected, latest_post.slug, next_state)
        try:
            _persist_blog_editor(
                selected=selected,
                post_path=latest_post.path,
                meta=publish_meta,
                body=event_body,
                ui=ui,
            )
            _blog_shell_clear_draft(selected, latest_post.slug)
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
        return True

    return True


def _blog_meta_from_state(
    selected: str,
    slug: str,
    original_meta: dict,
    *,
    fallback_title: str,
) -> dict:
    """Build editable blog front matter from current widget state."""
    return {
        "title": str(
            st.session_state.get(
                _blog_editor_key(selected, slug, "title"),
                original_meta.get("title", "") or fallback_title,
            )
            or ""
        ).strip()
        or fallback_title,
        "date": str(
            st.session_state.get(
                _blog_editor_key(selected, slug, "date"),
                original_meta.get("date", ""),
            )
            or ""
        ).strip(),
        "status": str(
            st.session_state.get(
                _blog_editor_key(selected, slug, "status"),
                original_meta.get("status", "draft"),
            )
            or "draft"
        ),
        "tags": _csv_values(
            st.session_state.get(
                _blog_editor_key(selected, slug, "tags"),
                _csv_text(original_meta.get("tags")),
            )
        ),
        "summary": str(
            st.session_state.get(
                _blog_editor_key(selected, slug, "summary"),
                original_meta.get("summary", ""),
            )
            or ""
        ).strip(),
        "cover": str(
            st.session_state.get(
                _blog_editor_key(selected, slug, "cover"),
                original_meta.get("cover", ""),
            )
            or ""
        ).strip(),
        "related_evidence": _csv_values(
            st.session_state.get(
                _blog_editor_key(selected, slug, "related_evidence"),
                _csv_text(original_meta.get("related_evidence")),
            )
        ),
        "related_kanban": _csv_values(
            st.session_state.get(
                _blog_editor_key(selected, slug, "related_kanban"),
                _csv_text(original_meta.get("related_kanban")),
            )
        ),
    }


def _render_blog_toolbar(
    *,
    selected: str,
    slug: str,
    title: str,
    status: str,
    date_value: str,
    state: dict,
    ui: dict[str, str],
) -> tuple[bool, bool, bool]:
    """Render the sticky-feeling editor toolbar."""
    title_col, action_col, panel_col = st.columns([1.55, 1.2, 1.2])
    with title_col:
        st.markdown(f"### {title}")
        st.caption(f"{status} · {date_value or '-'} · {selected}/{slug}")
    with action_col:
        save_col, preview_col, check_col, publish_col = st.columns(4)
        with save_col:
            save_clicked = st.button(
                ui["save"],
                key=_blog_editor_key(selected, slug, "toolbar_save"),
                type="primary",
                use_container_width=True,
            )
        with preview_col:
            if st.button(
                ui["preview"],
                key=_blog_editor_key(selected, slug, "toolbar_preview"),
                use_container_width=True,
            ):
                next_state = dict(state)
                next_state["preview_open"] = not bool(state.get("preview_open"))
                _rerun_with_blog_layout(selected, slug, next_state)
        with check_col:
            check_clicked = st.button(
                ui["validate"],
                key=_blog_editor_key(selected, slug, "toolbar_check"),
                use_container_width=True,
            )
        with publish_col:
            publish_clicked = st.button(
                ui["publish"],
                key=_blog_editor_key(selected, slug, "toolbar_publish"),
                use_container_width=True,
            )
    with panel_col:
        left_col, right_col, focus_col, public_col = st.columns(4)
        with left_col:
            if st.button(
                "☰",
                help=ui["left_panel"],
                key=_blog_editor_key(selected, slug, "toggle_left"),
                use_container_width=True,
            ):
                next_state = dict(state)
                next_state["left_open"] = not bool(state.get("left_open"))
                next_state["focus_mode"] = False
                _rerun_with_blog_layout(selected, slug, next_state)
        with right_col:
            if st.button(
                "▣",
                help=ui["right_panel"],
                key=_blog_editor_key(selected, slug, "toggle_right"),
                use_container_width=True,
            ):
                next_state = dict(state)
                next_state["right_open"] = not bool(state.get("right_open"))
                next_state["focus_mode"] = False
                _rerun_with_blog_layout(selected, slug, next_state)
        with focus_col:
            focus_label = (
                ui["exit_focus"] if state.get("focus_mode") else ui["focus_mode"]
            )
            if st.button(
                focus_label,
                key=_blog_editor_key(selected, slug, "toggle_focus"),
                use_container_width=True,
            ):
                _toggle_focus_blog_layout(selected, slug, state)
        with public_col:
            if st.button(
                ui["public_preview"],
                key=_blog_editor_key(selected, slug, "toolbar_public_preview"),
                use_container_width=True,
            ):
                next_state = dict(state)
                next_state["preview_open"] = True
                next_state["right_open"] = True
                next_state["active_right_tab"] = "Check"
                next_state["focus_mode"] = False
                _rerun_with_blog_layout(selected, slug, next_state)
    _persist_blog_layout_state(selected, slug, state)
    return save_clicked, check_clicked, publish_clicked


def _render_blog_article_panel(
    *,
    selected: str,
    posts: list,
    selected_slug: str,
    ui: dict[str, str],
) -> None:
    """Render the collapsible article navigation panel."""
    with st.expander(ui["new_blog"], expanded=True):
        new_title = st.text_input(
            ui["title_label"],
            key=f"new_blog_title:{selected}",
        )
        if st.button(ui["create"], key=f"create_blog:{selected}"):
            if new_title.strip():
                path = create_blog_draft(
                    selected,
                    title=new_title.strip(),
                    body=f"{BLOG_INSERT_MARKER}\n\n",
                    summary="",
                )
                st.session_state[f"blog_post_slug_select:{selected}"] = path.stem
                stash_git_backup_results()
                clear_web_cache()
                st.rerun()
            st.warning(ui["title_label"])

    with st.expander(ui["draft_from_evidence"]):
        evidence_id = st.text_input(
            ui["evidence_id"],
            key=f"blog_left_evidence_id:{selected}",
        )
        if st.button(
            ui["draft_from_evidence"],
            key=f"blog_left_draft_from_evidence:{selected}",
        ):
            try:
                path = draft_blog_from_evidence(selected, evidence_id.strip())
                st.session_state[f"blog_post_slug_select:{selected}"] = path.stem
                stash_git_backup_results()
                clear_web_cache()
                st.success(str(path))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if st.button(ui["draft_from_done"], key=f"blog_left_draft_from_done:{selected}"):
        try:
            path = draft_blog_from_kanban_done(selected)
            st.session_state[f"blog_post_slug_select:{selected}"] = path.stem
            stash_git_backup_results()
            clear_web_cache()
            st.success(str(path))
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    st.selectbox(
        ui["status"],
        [ui["all_statuses"], "draft", "published", "archived"],
        key=f"blog_status_filter:{selected}",
    )

    if posts:
        options = [post.slug for post in posts]
        if selected_slug not in options:
            selected_slug = options[0]
        st.selectbox(
            ui["post"],
            options,
            index=options.index(selected_slug),
            format_func=lambda slug: next(
                (
                    f"{post.date} · {post.status} · {post.title}"
                    for post in posts
                    if post.slug == slug
                ),
                slug,
            ),
            key=f"blog_post_slug_select:{selected}",
        )


def _render_blog_meta_panel(
    *,
    selected: str,
    slug: str,
    meta: dict,
    ui: dict[str, str],
) -> None:
    """Render front matter controls in the right drawer."""
    status = str(meta.get("status", "draft") or "draft")
    st.selectbox(
        ui["status"],
        ["draft", "published", "archived"],
        index=_blog_status_index(status),
        key=_blog_editor_key(selected, slug, "status"),
    )
    st.text_input(
        ui["date"],
        value=str(meta.get("date", "") or ""),
        key=_blog_editor_key(selected, slug, "date"),
    )
    st.text_area(
        ui["summary"],
        value=str(meta.get("summary", "") or ""),
        height=96,
        key=_blog_editor_key(selected, slug, "summary"),
    )
    st.text_input(
        ui["tags"],
        value=_csv_text(meta.get("tags")),
        help=ui["tags_help"],
        key=_blog_editor_key(selected, slug, "tags"),
    )
    st.text_input(
        ui["cover"],
        value=str(meta.get("cover", "") or ""),
        key=_blog_editor_key(selected, slug, "cover"),
    )
    st.text_input(
        ui["related_evidence"],
        value=_csv_text(meta.get("related_evidence")),
        key=_blog_editor_key(selected, slug, "related_evidence"),
    )
    st.text_input(
        ui["related_kanban"],
        value=_csv_text(meta.get("related_kanban")),
        key=_blog_editor_key(selected, slug, "related_kanban"),
    )


def _render_blog_media_panel(
    *,
    selected: str,
    root: Path,
    latest_post,
    edited_meta: dict,
    edited_body: str,
    media_rows: list[dict],
    ui: dict[str, str],
) -> None:
    """Render media library, upload, and insertion actions."""
    st.caption(f"{ui['insert_marker']}: `{BLOG_INSERT_MARKER}`")
    if media_rows:
        st.dataframe(
            [
                {
                    "file": row["name"],
                    "kind": row["kind"],
                    "size_kb": row["size_kb"],
                    "referenced": row["referenced"],
                }
                for row in media_rows
            ],
            use_container_width=True,
            hide_index=True,
        )
        options = [row["relative_path"] for row in media_rows]
        selected_media_key = _blog_editor_key(
            selected,
            latest_post.slug,
            "selected_media",
        )
        if st.session_state.get(selected_media_key) not in options:
            st.session_state[selected_media_key] = options[0]
        selected_rel = st.selectbox(
            ui["selected_media"],
            options,
            key=selected_media_key,
        )
        selected_row = next(
            row for row in media_rows if row["relative_path"] == selected_rel
        )
        alt = st.text_input(
            ui["alt_text"],
            key=_blog_editor_key(selected, latest_post.slug, "library_alt"),
        )
        caption = st.text_input(
            ui["caption"],
            key=_blog_editor_key(selected, latest_post.slug, "library_caption"),
        )
        insert_col, cover_col = st.columns(2)
        with insert_col:
            if st.button(
                ui["use_selected_media"],
                key=_blog_editor_key(selected, latest_post.slug, "insert_library"),
                use_container_width=True,
            ):
                snippet = _media_snippet(
                    selected_row["kind"],
                    selected_rel,
                    alt=alt.strip(),
                    caption=caption.strip(),
                )
                try:
                    _save_blog_editor(
                        selected=selected,
                        post_path=latest_post.path,
                        meta=edited_meta,
                        body=insert_blog_snippet(edited_body, snippet),
                        ui=ui,
                    )
                except Exception as exc:
                    st.error(str(exc))
        with cover_col:
            if st.button(
                ui["set_cover"],
                key=_blog_editor_key(selected, latest_post.slug, "cover_library"),
                use_container_width=True,
                disabled=selected_row["kind"] != "image",
            ):
                next_meta = dict(edited_meta)
                next_meta["cover"] = selected_rel
                try:
                    _save_blog_editor(
                        selected=selected,
                        post_path=latest_post.path,
                        meta=next_meta,
                        body=edited_body,
                        ui=ui,
                    )
                except Exception as exc:
                    st.error(str(exc))
    else:
        st.info(ui["no_media"])

    uploaded = st.file_uploader(
        ui["upload_media"],
        type=sorted(BLOG_IMAGE_EXTENSIONS | BLOG_VIDEO_EXTENSIONS),
        key=f"blog_media_upload:{selected}:{latest_post.slug}",
    )
    media_kind = st.selectbox(
        ui["media_kind"],
        ["image", "video"],
        key=f"blog_media_kind:{selected}:{latest_post.slug}",
    )
    media_alt = st.text_input(
        ui["alt_text"],
        key=f"blog_media_alt:{selected}:{latest_post.slug}",
    )
    media_caption = st.text_input(
        ui["caption"],
        key=f"blog_media_caption:{selected}:{latest_post.slug}",
    )
    insert_media = st.checkbox(
        ui["insert_into_post"],
        value=True,
        key=f"blog_media_insert:{selected}:{latest_post.slug}",
    )
    cover_media = st.checkbox(
        ui["set_cover"],
        value=False,
        key=f"blog_media_cover:{selected}:{latest_post.slug}",
    )
    if st.button(
        ui["add_media"],
        key=f"blog_add_media:{selected}:{latest_post.slug}",
    ):
        if uploaded is None:
            st.warning(ui["upload_media"])
        elif cover_media and media_kind != "image":
            st.error(ui["set_cover"])
        else:
            try:
                result = add_blog_media_bytes(
                    selected,
                    latest_post.slug,
                    data=uploaded.getvalue(),
                    filename=uploaded.name,
                    kind=media_kind,
                    alt=media_alt.strip(),
                    caption=media_caption.strip(),
                )
                next_meta = dict(edited_meta)
                next_body = edited_body
                if insert_media:
                    next_body = insert_blog_snippet(next_body, result.snippet)
                if cover_media:
                    if media_kind != "image":
                        raise PublicSiteError(ui["set_cover"])
                    next_meta["cover"] = result.relative_path
                if insert_media or cover_media:
                    assert_files_current([latest_post.path])
                    saved, changed = save_blog_post(
                        selected,
                        latest_post.slug,
                        next_meta,
                        next_body,
                        action=(
                            f"update {selected}/blog/"
                            f"{latest_post.path.name} media"
                        ),
                    )
                    refresh_file_snapshots([saved, result.path, *changed])
                else:
                    refresh_file_snapshots([result.path])
                stash_git_backup_results()
                clear_web_cache()
                st.success(result.snippet)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    video_url = st.text_input(
        ui["video_url"],
        key=f"blog_video_url:{selected}:{latest_post.slug}",
    )
    if st.button(
        ui["insert_video_url"],
        key=f"blog_insert_video_url:{selected}:{latest_post.slug}",
    ):
        if not video_url.strip():
            st.warning(ui["video_url"])
        else:
            snippet = f"::video[{media_caption.strip()}]({video_url.strip()})"
            try:
                _save_blog_editor(
                    selected=selected,
                    post_path=latest_post.path,
                    meta=edited_meta,
                    body=insert_blog_snippet(edited_body, snippet),
                    ui=ui,
                )
            except Exception as exc:
                st.error(str(exc))

    if uploaded is not None:
        max_mb = (
            BLOG_IMAGE_MAX_BYTES
            if media_kind == "image"
            else BLOG_VIDEO_MAX_BYTES
        ) // (1024 * 1024)
        st.caption(f"{ui['media_kind']}: {media_kind} · max {max_mb}MB")


def _append_candidate_to_body(body: str, candidate: str) -> str:
    clean = candidate.strip()
    if not clean:
        return body
    base = body.rstrip()
    return f"{base}\n\n{clean}\n" if base else f"{clean}\n"


def _render_blog_ai_panel(
    *,
    selected: str,
    latest_post,
    edited_meta: dict,
    edited_body: str,
    ui: dict[str, str],
) -> None:
    """Render candidate-first AI writing helpers."""
    candidate_key = _blog_ai_candidate_key(selected, latest_post.slug)
    clear_key = _blog_editor_key(selected, latest_post.slug, "ai_candidate_clear")
    meta_key = _blog_editor_key(selected, latest_post.slug, "ai_candidate_meta")
    if st.session_state.pop(clear_key, False):
        st.session_state[candidate_key] = ""
        st.session_state[meta_key] = {}
    st.session_state.setdefault(candidate_key, "")
    st.session_state.setdefault(meta_key, {})

    if st.button(
        ui["draft_from_title"],
        key=_blog_editor_key(selected, latest_post.slug, "ai_generate_title"),
        use_container_width=True,
    ):
        try:
            candidate = blog_candidate_from_title(
                selected,
                str(edited_meta.get("title", "") or latest_post.title),
            )
            st.session_state[candidate_key] = candidate.body
            st.session_state[meta_key] = candidate.to_dict()
            st.success(ui["ai_candidate"])
        except Exception as exc:
            st.error(str(exc))

    with st.expander(ui["draft_from_evidence"], expanded=True):
        evidence_id = st.text_input(
            ui["evidence_id"],
            key=_blog_editor_key(selected, latest_post.slug, "ai_evidence_id"),
        )
        if st.button(
            ui["generate_candidate"],
            key=_blog_editor_key(
                selected,
                latest_post.slug,
                "ai_generate_evidence",
            ),
        ):
            try:
                candidate = blog_candidate_from_evidence(
                    selected,
                    evidence_id.strip(),
                )
                st.session_state[candidate_key] = candidate.body
                st.session_state[meta_key] = candidate.to_dict()
                st.success(ui["ai_candidate"])
            except Exception as exc:
                st.error(str(exc))

    if st.button(
        ui["draft_from_done"],
        key=_blog_editor_key(selected, latest_post.slug, "ai_generate_done"),
    ):
        try:
            candidate = blog_candidate_from_kanban_done(selected)
            st.session_state[candidate_key] = candidate.body
            st.session_state[meta_key] = candidate.to_dict()
            st.success(ui["ai_candidate"])
        except Exception as exc:
            st.error(str(exc))

    candidate_meta = st.session_state.get(meta_key)
    if isinstance(candidate_meta, dict) and candidate_meta:
        st.caption(
            " · ".join(
                value
                for value in (
                    str(candidate_meta.get("title", "") or ""),
                    str(candidate_meta.get("summary", "") or ""),
                )
                if value
            )
        )
        if str(candidate_meta.get("cover_prompt", "") or "").strip():
            with st.expander(ui["cover_prompt"]):
                st.write(str(candidate_meta.get("cover_prompt", "") or ""))
        warnings = [
            str(item).strip()
            for item in candidate_meta.get("warnings", [])
            if str(item).strip()
        ] if isinstance(candidate_meta.get("warnings"), list) else []
        if warnings:
            with st.expander(ui["candidate_warnings"], expanded=True):
                for warning in warnings:
                    st.write(f"- {warning}")
    candidate_text = st.text_area(
        ui["ai_candidate"],
        height=300,
        key=candidate_key,
    )
    insert_col, append_col, meta_col = st.columns(3)
    with insert_col:
        if st.button(
            ui["insert_candidate"],
            key=_blog_editor_key(selected, latest_post.slug, "ai_insert"),
            use_container_width=True,
        ):
            if not candidate_text.strip():
                st.warning(ui["candidate_empty"])
            else:
                try:
                    _save_blog_editor(
                        selected=selected,
                        post_path=latest_post.path,
                        meta=edited_meta,
                        body=insert_blog_snippet(edited_body, candidate_text),
                        ui=ui,
                    )
                except Exception as exc:
                    st.error(str(exc))
    with append_col:
        if st.button(
            ui["append_candidate"],
            key=_blog_editor_key(selected, latest_post.slug, "ai_append"),
            use_container_width=True,
        ):
            if not candidate_text.strip():
                st.warning(ui["candidate_empty"])
            else:
                try:
                    _save_blog_editor(
                        selected=selected,
                        post_path=latest_post.path,
                        meta=edited_meta,
                        body=_append_candidate_to_body(edited_body, candidate_text),
                        ui=ui,
                    )
                except Exception as exc:
                    st.error(str(exc))
    with meta_col:
        if st.button(
            ui["apply_candidate_meta"],
            key=_blog_editor_key(selected, latest_post.slug, "ai_apply_meta"),
            use_container_width=True,
        ):
            if not isinstance(candidate_meta, dict) or not candidate_meta:
                st.warning(ui["candidate_empty"])
            else:
                next_meta = dict(edited_meta)
                for field_name in ("title", "summary"):
                    value = str(candidate_meta.get(field_name, "") or "").strip()
                    if value:
                        next_meta[field_name] = value
                for field_name in ("tags", "related_evidence", "related_kanban"):
                    values = candidate_meta.get(field_name)
                    if isinstance(values, list):
                        next_meta[field_name] = [
                            str(item).strip()
                            for item in values
                            if str(item).strip()
                        ]
                try:
                    _save_blog_editor(
                        selected=selected,
                        post_path=latest_post.path,
                        meta=next_meta,
                        body=edited_body,
                        ui=ui,
                    )
                except Exception as exc:
                    st.error(str(exc))

    full_col, discard_col = st.columns(2)
    with full_col:
        if st.button(
            ui["use_full_candidate"],
            key=_blog_editor_key(selected, latest_post.slug, "ai_use_full"),
            use_container_width=True,
        ):
            if not candidate_text.strip():
                st.warning(ui["candidate_empty"])
            else:
                next_meta = dict(edited_meta)
                if isinstance(candidate_meta, dict):
                    for field_name in ("title", "summary"):
                        value = str(candidate_meta.get(field_name, "") or "").strip()
                        if value:
                            next_meta[field_name] = value
                    for field_name in (
                        "tags",
                        "related_evidence",
                        "related_kanban",
                    ):
                        values = candidate_meta.get(field_name)
                        if isinstance(values, list):
                            next_meta[field_name] = [
                                str(item).strip()
                                for item in values
                                if str(item).strip()
                            ]
                try:
                    _save_blog_editor(
                        selected=selected,
                        post_path=latest_post.path,
                        meta=next_meta,
                        body=candidate_text,
                        ui=ui,
                    )
                except Exception as exc:
                    st.error(str(exc))
    with discard_col:
        if st.button(
            ui["discard_candidate"],
            key=_blog_editor_key(selected, latest_post.slug, "ai_discard"),
            use_container_width=True,
        ):
            st.session_state[clear_key] = True
            st.rerun()


def _render_blog_check_messages(title: str, messages: list[str]) -> None:
    if not messages:
        return
    st.markdown(f"**{title}**")
    for message in messages:
        st.write(f"- {message}")


def _render_blog_check_panel(
    *,
    selected: str,
    latest_post,
    edited_meta: dict,
    edited_body: str,
    media_rows: list[dict],
    ui: dict[str, str],
) -> None:
    """Render publish validation, quality hints, and preview."""
    if st.button(
        ui["validate"],
        key=_blog_editor_key(selected, latest_post.slug, "check_tab_run"),
        use_container_width=True,
    ):
        _run_blog_publish_check(
            selected=selected,
            post_path=latest_post.path,
            slug=latest_post.slug,
            meta=edited_meta,
            body=edited_body,
            media_rows=media_rows,
            ui=ui,
        )
    check_state = st.session_state.get(
        _blog_check_state_key(selected, latest_post.slug),
        {"errors": [], "warnings": [], "quality": []},
    )
    errors = list(check_state.get("errors") or [])
    warnings = list(check_state.get("warnings") or [])
    quality = list(check_state.get("quality") or [])
    if errors:
        st.error(ui["public_errors"])
    elif warnings:
        st.warning(ui["validation_warnings"])
    elif quality:
        st.info(ui["quality_warnings"])
    else:
        st.success(ui["publish_ready"])
    _render_blog_check_messages(ui["validation_errors"], errors)
    _render_blog_check_messages(ui["validation_warnings"], warnings)
    _render_blog_check_messages(ui["quality_warnings"], quality)
    if not errors and not warnings and not quality:
        st.write(ui["no_issues"])
    _blog_page_preview(selected, latest_post.slug, ui)


def _render_blog_right_panel(
    *,
    selected: str,
    root: Path,
    latest_post,
    edited_meta: dict,
    edited_body: str,
    media_rows: list[dict],
    state: dict,
    ui: dict[str, str],
) -> None:
    """Render the right drawer tab strip and active tool."""
    tab_cols = st.columns(len(_BLOG_RIGHT_TABS))
    for tab_col, tab in zip(tab_cols, _BLOG_RIGHT_TABS):
        with tab_col:
            if st.button(
                _BLOG_RIGHT_TAB_ICONS[tab],
                help=ui[tab.lower()],
                key=_blog_editor_key(selected, latest_post.slug, f"right_{tab}"),
                use_container_width=True,
            ):
                _set_right_blog_tab(selected, latest_post.slug, state, tab)
    active_tab = str(state.get("active_right_tab", "Meta"))
    st.subheader(ui[active_tab.lower()])
    if active_tab == "Meta":
        _render_blog_meta_panel(
            selected=selected,
            slug=latest_post.slug,
            meta=edited_meta,
            ui=ui,
        )
    elif active_tab == "Media":
        _render_blog_media_panel(
            selected=selected,
            root=root,
            latest_post=latest_post,
            edited_meta=edited_meta,
            edited_body=edited_body,
            media_rows=media_rows,
            ui=ui,
        )
    elif active_tab == "AI":
        _render_blog_ai_panel(
            selected=selected,
            latest_post=latest_post,
            edited_meta=edited_meta,
            edited_body=edited_body,
            ui=ui,
        )
    else:
        _render_blog_check_panel(
            selected=selected,
            latest_post=latest_post,
            edited_meta=edited_meta,
            edited_body=edited_body,
            media_rows=media_rows,
            ui=ui,
        )


def _render_blog_tab(
    *,
    selected: str,
    root: Path,
    ui: dict[str, str],
) -> None:
    """Render the public blog writing workflow."""
    blog_dir = root / BLOG_DIRNAME
    blog_dir.mkdir(parents=True, exist_ok=True)

    status_key = f"blog_status_filter:{selected}"
    status_filter = st.session_state.get(status_key, ui["all_statuses"])
    posts = load_blog_posts(
        selected,
        include_drafts=True,
        include_archived=True,
    )
    if status_filter != ui["all_statuses"]:
        posts = [post for post in posts if post.status == status_filter]

    selected_slug_key = f"blog_post_slug_select:{selected}"
    selected_slug = str(st.session_state.get(selected_slug_key, "") or "")
    post_by_slug = {post.slug: post for post in posts}
    if posts and selected_slug not in post_by_slug:
        selected_slug = posts[0].slug
        st.session_state[selected_slug_key] = selected_slug

    if not posts:
        left_col, edit_col = st.columns([0.35, 1])
        with left_col:
            _render_blog_article_panel(
                selected=selected,
                posts=[],
                selected_slug="",
                ui=ui,
            )
        with edit_col:
            st.info("-")
        return

    selected_post = post_by_slug[selected_slug]
    ensure_file_snapshot(selected_post.path)
    latest_post = parse_blog_post(selected_post.path)
    original_meta = dict(latest_post.meta)
    layout_state = _blog_layout_state(selected, latest_post.slug)

    if _render_blog_react_shell(
        selected=selected,
        root=root,
        posts=posts,
        latest_post=latest_post,
        original_meta=original_meta,
        layout_state=layout_state,
        ui=ui,
    ):
        return

    save_clicked, check_clicked, publish_clicked = _render_blog_toolbar(
        selected=selected,
        slug=latest_post.slug,
        title=latest_post.title,
        status=latest_post.status,
        date_value=latest_post.date,
        state=layout_state,
        ui=ui,
    )

    if layout_state.get("focus_mode"):
        column_weights = [1.0]
    else:
        column_weights = [
            0.32 if layout_state.get("left_open") else 0.06,
            1.0,
            0.42 if layout_state.get("right_open") else 0.06,
        ]
    columns = st.columns(column_weights)

    if layout_state.get("focus_mode"):
        edit_col = columns[0]
    else:
        left_col, edit_col, right_col = columns
        with left_col:
            if layout_state.get("left_open"):
                _render_blog_article_panel(
                    selected=selected,
                    posts=posts,
                    selected_slug=latest_post.slug,
                    ui=ui,
                )
            elif st.button(
                "☰",
                help=ui["left_panel"],
                key=_blog_editor_key(selected, latest_post.slug, "left_icon_open"),
                use_container_width=True,
            ):
                next_state = dict(layout_state)
                next_state["left_open"] = True
                _rerun_with_blog_layout(selected, latest_post.slug, next_state)

    with edit_col:
        st.text_input(
            ui["title_label"],
            value=str(original_meta.get("title", "") or latest_post.title),
            key=_blog_editor_key(selected, latest_post.slug, "title"),
        )
        edited_body = _render_body_editor(
            selected=selected,
            slug=latest_post.slug,
            body=latest_post.body,
            ui=ui,
        )
        edited_meta = _blog_meta_from_state(
            selected,
            latest_post.slug,
            original_meta,
            fallback_title=latest_post.title,
        )
        with st.expander(ui["raw_yaml"]):
            st.code(
                format_blog_document(edited_meta, edited_body),
                language="markdown",
            )
        if layout_state.get("preview_open"):
            _blog_page_preview(selected, latest_post.slug, ui)

    edited_meta = _blog_meta_from_state(
        selected,
        latest_post.slug,
        original_meta,
        fallback_title=latest_post.title,
    )
    media_rows = _blog_media_library(
        root,
        latest_post.slug,
        edited_meta,
        edited_body,
    )

    if not layout_state.get("focus_mode"):
        with right_col:
            if layout_state.get("right_open"):
                _render_blog_right_panel(
                    selected=selected,
                    root=root,
                    latest_post=latest_post,
                    edited_meta=edited_meta,
                    edited_body=edited_body,
                    media_rows=media_rows,
                    state=layout_state,
                    ui=ui,
                )
            else:
                for tab in _BLOG_RIGHT_TABS:
                    if st.button(
                        _BLOG_RIGHT_TAB_ICONS[tab],
                        help=ui[tab.lower()],
                        key=_blog_editor_key(
                            selected,
                            latest_post.slug,
                            f"right_icon_{tab}",
                        ),
                        use_container_width=True,
                    ):
                        _set_right_blog_tab(
                            selected,
                            latest_post.slug,
                            layout_state,
                            tab,
                        )

    final_meta = _blog_meta_from_state(
        selected,
        latest_post.slug,
        original_meta,
        fallback_title=latest_post.title,
    )
    final_media_rows = _blog_media_library(
        root,
        latest_post.slug,
        final_meta,
        edited_body,
    )

    if save_clicked:
        try:
            _save_blog_editor(
                selected=selected,
                post_path=latest_post.path,
                meta=final_meta,
                body=edited_body,
                ui=ui,
            )
        except Exception as exc:
            st.error(str(exc))

    if check_clicked:
        _run_blog_publish_check(
            selected=selected,
            post_path=latest_post.path,
            slug=latest_post.slug,
            meta=final_meta,
            body=edited_body,
            media_rows=final_media_rows,
            ui=ui,
        )
        next_state = dict(layout_state)
        next_state["right_open"] = True
        next_state["active_right_tab"] = "Check"
        next_state["focus_mode"] = False
        _rerun_with_blog_layout(selected, latest_post.slug, next_state)

    if publish_clicked:
        publish_meta = dict(final_meta)
        publish_meta["status"] = "published"
        check_state = _run_blog_publish_check(
            selected=selected,
            post_path=latest_post.path,
            slug=latest_post.slug,
            meta=publish_meta,
            body=edited_body,
            media_rows=final_media_rows,
            ui=ui,
        )
        if check_state["errors"]:
            next_state = dict(layout_state)
            next_state["right_open"] = True
            next_state["active_right_tab"] = "Check"
            next_state["focus_mode"] = False
            _rerun_with_blog_layout(selected, latest_post.slug, next_state)
        try:
            _save_blog_editor(
                selected=selected,
                post_path=latest_post.path,
                meta=publish_meta,
                body=edited_body,
                ui=ui,
            )
        except Exception as exc:
            st.error(str(exc))


ui = _ui()

st.set_page_config(
    page_title=ui["page_title"],
    layout="wide",
    initial_sidebar_state="expanded",
)

require_login()
selected = select_profile()
render_git_backup_notices()

root = profile_dir(selected)
required_paths = [
    _path(selected, PUBLIC_PROFILE_FILENAME),
    _path(selected, RESUME_SOURCE_FILENAME),
    _path(selected, PROJECTS_FILENAME),
    _path(selected, OUTPUTS_FILENAME),
]

st.title(ui["title"])
st.caption(ui["caption"])

if not all(path.exists() for path in required_paths):
    st.warning(ui["init_needed"])
    if st.button(ui["init"]):
        init_public_layer(selected)
        stash_git_backup_results()
        clear_web_cache()
        st.rerun()
    st.stop()

for file_path in required_paths:
    ensure_file_snapshot(file_path)

tab_profile, tab_blog, tab_resume, tab_curation, tab_build = st.tabs(
    [
        ui["profile"],
        ui["blog"],
        ui["resume"],
        ui["curation"],
        ui["build"],
    ]
)

with tab_profile:
    edit_col, preview_col = st.columns([0.95, 1.25])
    with edit_col:
        profile_override, media_overrides = _render_profile_form(
            selected=selected,
            root=root,
            ui=ui,
        )
        with st.expander(ui["raw_yaml"]):
            _render_yaml_editor(
                key="public_profile_yaml",
                path=_path(selected, PUBLIC_PROFILE_FILENAME),
                label=PUBLIC_PROFILE_FILENAME,
                selected=selected,
                ui=ui,
            )
    with preview_col:
        _render_site_preview(
            selected=selected,
            profile_override=profile_override,
            media_overrides=media_overrides,
            ui=ui,
        )

with tab_blog:
    _render_blog_tab(selected=selected, root=root, ui=ui)

with tab_resume:
    _render_yaml_editor(
        key="resume_source_yaml",
        path=_path(selected, RESUME_SOURCE_FILENAME),
        label=RESUME_SOURCE_FILENAME,
        selected=selected,
        ui=ui,
    )
    source = load_resume_source(selected)
    st.subheader(ui["preview"])
    st.markdown(render_resume_markdown(source))
    with st.expander(ui["draft_resume"]):
        target = st.text_input(ui["target"])
        if st.button(ui["draft_resume"]):
            if not target.strip():
                st.warning(ui["target"])
            else:
                html_path, md_path = draft_resume_for_target(
                    selected,
                    target.strip(),
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(f"{html_path}\n{md_path}")

with tab_curation:
    st.caption(ui["curation_caption"])
    project_path = _path(selected, PROJECTS_FILENAME)
    ensure_file_snapshot(project_path)
    contexts = evidence_contexts(selected)
    rows = [
        {
            "id": ctx.id,
            "type": ctx.type,
            "date": ctx.date,
            "title": ctx.title,
            "skills": ", ".join(ctx.skill_refs),
            "used_by_projects": ", ".join(ctx.used_by_projects),
            "used_by_outputs": ", ".join(ctx.used_by_outputs),
            "used_by_posts": ", ".join(ctx.used_by_posts),
        }
        for ctx in contexts
    ]
    st.subheader(ui["evidence"])
    st.dataframe(rows, use_container_width=True, hide_index=True)

    with st.expander(ui["suggest_groups"]):
        groups = suggest_groups(selected)
        if groups:
            st.code(
                yaml.dump(
                    [group.to_dict() for group in groups],
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                ),
                language="yaml",
            )
        else:
            st.write("-")

    with st.form("create_project_group"):
        evidence_options = [ctx.id for ctx in contexts]
        selected_evidence = st.multiselect(
            ui["evidence"],
            options=evidence_options,
        )
        new_project_id = st.text_input(ui["project_id"])
        new_project_title = st.text_input(ui["title_label"])
        new_project_summary = st.text_area(
            ui["project_summary"],
            height=120,
        )
        raw_tags = st.text_input(ui["tags"])
        submitted = st.form_submit_button(ui["create_project_group"])
        if submitted:
            tags = [
                tag.strip()
                for tag in raw_tags.split(",")
                if tag.strip()
            ]
            try:
                assert_files_current([project_path])
                result = group_project(
                    selected,
                    project_id=new_project_id,
                    title=new_project_title,
                    evidence_ids=selected_evidence,
                    summary=new_project_summary,
                    tags=tags,
                )
                refresh_file_snapshots([project_path])
                stash_git_backup_results()
                clear_web_cache()
                if result.warnings:
                    st.warning("\n".join(result.warnings))
                st.success(ui["saved"])
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    st.subheader(ui["current_projects"])
    projects = load_projects(selected)
    project_rows = [
        {
            "id": str(project.get("id", "") or ""),
            "status": str(project.get("status", "") or ""),
            "title": str(project.get("title", "") or ""),
            "evidence_refs": ", ".join(
                str(ref)
                for ref in (project.get("evidence_refs") or [])
                if str(ref).strip()
            ),
        }
        for project in projects
        if isinstance(project, dict)
    ]
    st.dataframe(project_rows, use_container_width=True, hide_index=True)

    draft_projects = [
        project
        for project in projects
        if isinstance(project, dict)
        and str(project.get("status", "draft") or "draft") == "draft"
    ]
    if draft_projects:
        project_to_edit = st.selectbox(
            ui["update_project_refs"],
            draft_projects,
            format_func=lambda p: str(
                p.get("title", "") or p.get("id", "")
            ),
        )
        old_refs = [
            str(ref).strip()
            for ref in (project_to_edit.get("evidence_refs") or [])
            if str(ref).strip()
        ]
        refs_to_keep = st.multiselect(
            ui["keep_evidence_refs"],
            options=old_refs,
            default=old_refs,
        )
        if st.button(ui["update_project_refs"]):
            try:
                assert_files_current([project_path])
                raw = yaml.safe_load(
                    project_path.read_text(encoding="utf-8")
                ) or {}
                raw_projects = raw.get("projects") or []
                for project in raw_projects:
                    if not isinstance(project, dict):
                        continue
                    if str(project.get("id", "") or "") == str(
                        project_to_edit.get("id", "") or ""
                    ):
                        project["evidence_refs"] = refs_to_keep
                        break
                project_path.write_text(
                    yaml.dump(
                        {"projects": raw_projects},
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    ),
                    encoding="utf-8",
                )
                git_backup.record_change(
                    [project_path],
                    action=(
                        f"update {selected}/projects.yaml evidence refs"
                    ),
                )
                refresh_file_snapshots([project_path])
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["saved"])
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

with tab_build:
    include_drafts = st.checkbox(ui["include_drafts"])
    out_dir = st.text_input(
        ui["output_dir"],
        value=str(REPO_ROOT / "dist" / "public" / selected),
    )
    base_url = st.text_input(
        ui["base_url"],
        value="",
        help=ui["base_url_help"],
    )
    c_validate, c_build = st.columns(2)
    with c_validate:
        if st.button(ui["validate"]):
            _render_validation(
                selected,
                include_drafts=include_drafts,
                ui=ui,
            )
    with c_build:
        if st.button(ui["build_site"]):
            if _render_validation(
                selected,
                include_drafts=include_drafts,
                ui=ui,
            ):
                try:
                    result = build_public_site(
                        selected,
                        out_dir=out_dir,
                        include_drafts=include_drafts,
                        base_url=base_url,
                    )
                    st.success(str(result.output_dir))
                except PublicSiteError as exc:
                    st.error(str(exc))

    with st.expander(ui["draft_update"]):
        project_id = st.text_input(ui["project_id"])
        if st.button(ui["draft_update"]):
            try:
                path = draft_project_update(selected, project_id.strip())
                stash_git_backup_results()
                clear_web_cache()
                st.success(str(path))
            except Exception as exc:
                st.error(str(exc))
