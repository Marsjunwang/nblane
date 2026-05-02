"""Public site, blog, and resume management page."""

from __future__ import annotations

import hashlib
import base64
import json
import re
import time
import uuid
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
import yaml

from nblane.core import llm as llm_client

try:
    from nblane.public_blog_editor_component import (
        st_blocknote_markdown,
        st_public_blog_editor,
    )
except Exception:  # pragma: no cover - optional Streamlit component
    st_blocknote_markdown = None
    st_public_blog_editor = None

from nblane.core import git_backup
from nblane.core import ai_stream_tasks
from nblane.core import visual_generation
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
    blog_media_full_preview_payload,
    blog_visual_candidate_rows,
    blog_media_library_rows,
    blog_preview_fingerprint,
    blog_visual_result_rows,
    build_public_site,
    convert_blog_media_video,
    create_blog_draft,
    delete_blog_media,
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
    publish_blog_text,
    render_blog_post_preview,
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
            "blocknote_unavailable": "BlockNote 组件不可用，已降级为 Markdown 文本编辑器。",
            "math_safe_mode": "公式安全模式",
            "math_safe_help": "使用 Markdown 源码编辑器，避免公式在 BlockNote 转换中被改写。",
            "math_safe_notice": "检测到公式，已使用 Markdown 源码编辑器。",
            "tags_help": "用逗号分隔",
            "related_evidence": "关联 evidence",
            "related_kanban": "关联看板项",
            "insert_marker": "插入位置标记",
            "media": "媒体",
            "formula_block": "公式",
            "formula_block_help": "LaTeX 展示公式",
            "video_block": "视频",
            "video_block_help": "公开站视频块",
            "visual_block": "视觉块",
            "visual_block_help": "图片、视频或图表候选",
            "ai_loading_block": "AI 占位",
            "ai_loading_block_help": "生成中内容",
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
            "confirm_public_profile": "我确认将公开此资料页的姓名、简介、头像和联系方式。",
            "confirm_public_required": "从 private 切换到 public 需要先勾选公开确认。",
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
            "close_left_panel": "收起文章栏",
            "right_panel": "工具栏",
            "close_right_panel": "收起工具栏",
            "focus_mode": "专注",
            "exit_focus": "退出专注",
            "rerun_check": "重新校验",
            "public_preview": "公开预览",
            "media_library": "媒体库",
            "selected_media": "所选媒体",
            "selection_context": "选区上下文",
            "selection_context_empty": "未选中文本，使用当前块。",
            "use_selected_media": "插入所选媒体",
            "no_media": "暂无媒体",
            "no_reference_images": "媒体库里暂无图片。",
            "no_source_videos": "媒体库里暂无视频。",
            "outline_empty": "暂无标题。",
            "outline_expand_section": "展开此节",
            "outline_panel": "大纲",
            "unreferenced_media": "未引用媒体",
            "ai_candidate": "候选内容",
            "ai_action_polish": "润色",
            "ai_action_shorten": "缩短",
            "ai_action_expand": "扩写",
            "ai_action_continue": "续写",
            "ai_action_translate": "翻译",
            "ai_action_tone": "语气",
            "ai_action_formula": "公式",
            "ai_action_visual": "配图",
            "ai_action_outline": "大纲",
            "ai_patch_panel": "AI Patch 候选",
            "ai_patch_candidate": "Patch 候选",
            "ai_patch_generating": "正在生成 Patch",
            "ai_patch_target": "目标",
            "ai_patch_meta": "Meta 修改",
            "ai_patch_assets": "资产",
            "ai_patch_markdown": "Markdown",
            "ai_patch_accept": "接受",
            "ai_patch_accept_block_only": "仅接受正文",
            "ai_patch_regenerate": "重新生成",
            "ai_patch_reject": "拒绝",
            "ai_stream_cancel": "取消生成",
            "ai_stream_cancelled": "已取消",
            "ai_stream_failed": "AI 生成失败",
            "ai_slash_group": "AI 操作",
            "ai_slash_write_next": "AI 写下一段",
            "ai_slash_outline": "大纲",
            "ai_slash_formula": "公式",
            "ai_slash_visual": "图",
            "ai_slash_diagram": "Diagram",
            "ai_slash_polish": "润色当前块",
            "draft_from_title": "根据当前标题生成完整候选",
            "generate_candidate": "生成候选",
            "insert_candidate": "插入",
            "insert_placement": "插入位置",
            "insert_at_cursor": "最近光标处",
            "insert_at_marker": "插入标记处",
            "insert_at_end": "文末",
            "insert_replace": "替换选区",
            "append_candidate": "追加到文末",
            "apply_candidate_meta": "应用摘要和标签",
            "use_full_candidate": "使用完整候选",
            "discard_candidate": "丢弃候选",
            "delete_media": "删除媒体",
            "delete_media_confirm": "确认删除这个媒体文件？如果已插入正文或设为封面，请先移除引用。",
            "delete_media_referenced": "此媒体仍被正文或封面引用，请先移除引用后再删除。",
            "convert_video": "转换为兼容 MP4",
            "convert_video_confirm": "将此视频转为浏览器兼容的 H.264 MP4？原文件会保留，正文引用会改到新文件。",
            "video_codec": "编码",
            "video_incompatible": "此视频编码可能无法在浏览器播放，请转换为 H.264 MP4。",
            "video_playback_failed": "浏览器无法播放此视频，可能是编码不兼容。",
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
            "privacy_publish_blocked": "发布已暂停：正文疑似包含内部路径或私密引用，请先清理后重新检查。",
            "markdown_downgrade": "当前使用 Markdown 文本编辑器，因为 BlockNote 组件不可用。",
            "candidate_saved": "候选已写入正文。",
            "compact_layout": "窄屏模式",
            "visual": "Visual",
            "visual_prompt": "视觉 Prompt",
            "visual_style": "风格",
            "visual_size": "尺寸",
            "visual_provider": "视觉生成",
            "source_video": "源视频",
            "source_video_manual": "手动输入源视频 URL/path",
            "source_video_select": "选择源视频",
            "video_edit_source_help": (
                "DashScope 视频编辑要求 MP4/MOV，时长 2-10 秒，大小不超过 100MB。"
                "本地媒体会先上传到 DashScope 临时 OSS 再生成。"
            ),
            "reference_image": "参考图",
            "reference_image_manual": "手动输入参考图 URL/path",
            "reference_image_select": "选择参考图",
            "generate_visual": "生成视觉素材",
            "generate_cover_image": "生成封面候选",
            "recent_visuals": "最近生成",
            "save_to_media": "存到媒体",
            "visual_prompt_suggestions": "Prompt 建议",
            "visual_suggest_cover": "使用封面建议",
            "visual_suggest_cover_subject": "主体封面",
            "visual_suggest_cover_diagram": "技术插画",
            "visual_suggest_flow": "流程图",
            "visual_suggest_flow_compare": "对比流程",
            "visual_suggest_example": "事例场景",
            "visual_suggest_example_system": "系统示意",
            "visual_suggest_video": "视频优化",
            "visual_size_default": "默认尺寸",
            "visual_style_default": "默认风格",
            "visual_custom": "自定义",
            "visual_size_custom": "自定义尺寸",
            "visual_default": "默认",
            "visual_size_help": "尺寸可留空使用默认，或填写 width*height / widthxheight / 1K / 2K / 4K；最小 768*768，比例 1:8 到 8:1。",
            "visual_style_help": "选择预设风格，或用自定义补充材质、镜头、图表风格等偏好。",
            "visual_alt_help": "插入正文时写入 Markdown 图片替代文本；设为封面时不用此字段，封面 alt 使用文章标题。",
            "visual_caption_help": "插入正文时显示为图片下方说明或视频标题；设为封面时不用此字段。",
            "preview_unavailable": "此媒体没有可内联预览，可通过文件名和片段确认。",
            "update_preview": "更新预览",
            "high_quality_preview": "高清预览",
            "fast_preview": "快速预览",
            "view_full_preview": "查看大图",
            "load_full_preview": "加载高清",
            "close": "关闭",
            "flowchart": "流程图",
            "example": "事例图",
            "video_edit": "视频编辑",
            "missing_visual_key": "缺少 VISUAL_API_KEY / DASHSCOPE_API_KEY / LLM_API_KEY。",
            "using_key_from": "使用 key 来源",
            "preview_empty": "暂无预览。",
            "create_post": "新建",
            "filter_posts": "筛选",
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
        "blocknote_unavailable": "BlockNote component is unavailable; using the Markdown text editor.",
        "math_safe_mode": "Math-safe mode",
        "math_safe_help": "Use the Markdown source editor so formulas are not rewritten by BlockNote conversion.",
        "math_safe_notice": "Formulas detected; using the Markdown source editor.",
        "tags_help": "Comma-separated",
        "related_evidence": "Related evidence",
        "related_kanban": "Related kanban",
        "insert_marker": "Insert marker",
        "media": "Media",
        "formula_block": "Formula",
        "formula_block_help": "LaTeX display formula",
        "video_block": "Video",
        "video_block_help": "Public-site video block",
        "visual_block": "Visual block",
        "visual_block_help": "Image, video, or diagram candidate",
        "ai_loading_block": "AI placeholder",
        "ai_loading_block_help": "Generated content",
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
        "confirm_public_profile": "I confirm this profile page will expose the name, bio, avatar, and contact fields.",
        "confirm_public_required": "Switching from private to public requires explicit confirmation first.",
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
        "close_left_panel": "Collapse article panel",
        "right_panel": "Tool drawer",
        "close_right_panel": "Collapse tool drawer",
        "focus_mode": "Focus",
        "exit_focus": "Exit focus",
        "rerun_check": "Run check again",
        "public_preview": "Public preview",
        "media_library": "Media library",
        "selected_media": "Selected media",
        "selection_context": "Selection context",
        "selection_context_empty": "No text selection; using the current block.",
        "use_selected_media": "Insert selected media",
        "no_media": "No media yet",
        "no_reference_images": "No images in the media library.",
        "no_source_videos": "No videos in the media library.",
        "outline_empty": "No headings yet.",
        "outline_expand_section": "Expand section",
        "outline_panel": "Outline",
        "unreferenced_media": "Unreferenced media",
        "ai_candidate": "Candidate",
        "ai_action_polish": "Polish",
        "ai_action_shorten": "Shorten",
        "ai_action_expand": "Expand",
        "ai_action_continue": "Continue",
        "ai_action_translate": "Translate",
        "ai_action_tone": "Tone",
        "ai_action_formula": "Formula",
        "ai_action_visual": "Visual",
        "ai_action_outline": "Outline",
        "ai_patch_panel": "AI patch candidates",
        "ai_patch_candidate": "Patch candidate",
        "ai_patch_generating": "Generating patch",
        "ai_patch_target": "Target",
        "ai_patch_meta": "Meta changes",
        "ai_patch_assets": "Assets",
        "ai_patch_markdown": "Markdown",
        "ai_patch_accept": "Accept",
        "ai_patch_accept_block_only": "Accept block only",
        "ai_patch_regenerate": "Regenerate",
        "ai_patch_reject": "Reject",
        "ai_stream_cancel": "Cancel",
        "ai_stream_cancelled": "Cancelled",
        "ai_stream_failed": "AI generation failed",
        "ai_slash_group": "AI actions",
        "ai_slash_write_next": "AI write next paragraph",
        "ai_slash_outline": "Outline",
        "ai_slash_formula": "Formula",
        "ai_slash_visual": "Visual",
        "ai_slash_diagram": "Diagram",
        "ai_slash_polish": "Polish current block",
        "draft_from_title": "Generate full candidate from current title",
        "generate_candidate": "Generate candidate",
        "insert_candidate": "Insert",
        "insert_placement": "Insert position",
        "insert_at_cursor": "Recent cursor",
        "insert_at_marker": "Insert marker",
        "insert_at_end": "End",
        "insert_replace": "Replace selection",
        "append_candidate": "Append to end",
        "apply_candidate_meta": "Apply summary and tags",
        "use_full_candidate": "Use full candidate",
        "discard_candidate": "Discard candidate",
        "delete_media": "Delete media",
        "delete_media_confirm": "Delete this media file? If it is in the body or cover, remove the reference first.",
        "delete_media_referenced": "This media is still referenced by the body or cover. Remove the reference before deleting.",
        "convert_video": "Convert to compatible MP4",
        "convert_video_confirm": "Convert this video to browser-compatible H.264 MP4? The original file will be kept and body references will move to the new file.",
        "video_codec": "Codec",
        "video_incompatible": "This video codec may not play in browsers. Convert it to H.264 MP4.",
        "video_playback_failed": "The browser cannot play this video; the codec may be incompatible.",
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
        "privacy_publish_blocked": "Publish paused: the body appears to reference internal paths or private material. Clean it up and run the check again.",
        "markdown_downgrade": "Using the Markdown text editor because the BlockNote component is unavailable.",
        "candidate_saved": "Candidate was written into the body.",
        "compact_layout": "Compact layout",
        "visual": "Visual",
        "visual_prompt": "Visual prompt",
        "visual_style": "Style",
        "visual_size": "Size",
        "visual_provider": "Visual generation",
        "source_video": "Source video",
        "source_video_manual": "Manual source video URL/path",
        "source_video_select": "Select source video",
        "video_edit_source_help": (
            "DashScope video edit requires MP4/MOV, 2-10 seconds, up to 100MB. "
            "Local media is uploaded to temporary DashScope OSS before generation."
        ),
        "reference_image": "Reference image",
        "reference_image_manual": "Manual reference image URL/path",
        "reference_image_select": "Select reference image",
        "generate_visual": "Generate visual asset",
        "generate_cover_image": "Generate cover candidate",
        "recent_visuals": "Recent generations",
        "save_to_media": "Save to media",
        "visual_prompt_suggestions": "Prompt suggestions",
        "visual_suggest_cover": "Use cover prompt",
        "visual_suggest_cover_subject": "Subject cover",
        "visual_suggest_cover_diagram": "Technical illustration",
        "visual_suggest_flow": "Flowchart",
        "visual_suggest_flow_compare": "Compare flow",
        "visual_suggest_example": "Example scene",
        "visual_suggest_example_system": "System sketch",
        "visual_suggest_video": "Video cleanup",
        "visual_size_default": "Default size",
        "visual_style_default": "Default style",
        "visual_custom": "Custom",
        "visual_size_custom": "Custom size",
        "visual_default": "Default",
        "visual_size_help": "Leave empty for the default, or use width*height / widthxheight / 1K / 2K / 4K; minimum 768*768 and aspect ratio 1:8 to 8:1.",
        "visual_style_help": "Choose a style preset, or customize material, camera, diagram, or rendering preferences.",
        "visual_alt_help": "Used as Markdown image alt text when inserted into the body; covers use the post title instead.",
        "visual_caption_help": "Shown as an image caption or video title when inserted into the body; not used for covers.",
        "preview_unavailable": "No inline preview is available for this media; confirm it by filename and snippet.",
        "update_preview": "Update preview",
        "high_quality_preview": "High-quality preview",
        "fast_preview": "Fast preview",
        "view_full_preview": "Open large preview",
        "load_full_preview": "Load full preview",
        "close": "Close",
        "flowchart": "Flowchart",
        "example": "Example",
        "video_edit": "Video edit",
        "missing_visual_key": "Missing VISUAL_API_KEY / DASHSCOPE_API_KEY / LLM_API_KEY.",
        "using_key_from": "Using key from",
        "preview_empty": "No preview yet.",
        "create_post": "New",
        "filter_posts": "Filter",
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
    clean = rel.strip().lstrip("/")
    if not clean or clean.startswith(("http://", "https://", "oss://", "file://")):
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


def _visual_media_input_for_generation(root: Path, value: str) -> str:
    """Turn profile-relative media refs into local file paths for provider upload."""
    clean = str(value or "").strip()
    if not clean:
        return ""
    local_path = _local_media_path(root, clean)
    return str(local_path) if local_path is not None else clean


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
    public_visibility_confirmed = True
    if visibility != "public" and new_visibility == "public":
        public_visibility_confirmed = st.checkbox(
            ui["confirm_public_profile"],
            value=False,
            key=_profile_widget_key(selected, "confirm_public"),
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
        if not public_visibility_confirmed:
            st.warning(ui["confirm_public_required"])
            return profile_override, media_overrides
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


_BLOG_RIGHT_TABS = ("Meta", "Media", "AI", "Visual", "Check")
_BLOG_RIGHT_TAB_ICONS = {
    "Meta": "M",
    "Media": "▧",
    "AI": "AI",
    "Visual": "V",
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
    *,
    collapse_current: bool = False,
) -> None:
    next_state = dict(state)
    if (
        collapse_current
        and next_state.get("right_open")
        and next_state.get("active_right_tab") == tab
    ):
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


def _blog_preview_html_key(selected: str, slug: str) -> str:
    return _blog_editor_key(selected, slug, "preview_html")


def _blog_preview_fingerprint_key(selected: str, slug: str) -> str:
    return _blog_editor_key(selected, slug, "preview_fingerprint")


def _blog_preview_quality_key(selected: str, slug: str) -> str:
    return _blog_editor_key(selected, slug, "preview_quality")


def _clear_blog_preview(selected: str, slug: str) -> None:
    for key in (
        _blog_preview_html_key(selected, slug),
        _blog_preview_fingerprint_key(selected, slug),
        _blog_preview_quality_key(selected, slug),
    ):
        st.session_state.pop(key, None)


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


_BLOG_EVENT_DEDUPE_ACTIONS = {
    "markdown_changed",
    "layout_state_changed",
    "insert_media",
    "delete_media",
    "convert_media_video",
    "insert_candidate",
    "apply_candidate_meta",
    "select_post",
    "filter_posts",
    "create_post",
    "draft_from_evidence",
    "draft_from_done",
    "generate_ai_candidate",
    "ai_inline_action",
    "ai_stream_poll",
    "cancel_ai_stream",
    "apply_ai_patch",
    "reject_ai_patch",
    "upload_media",
    "generate_visual_asset",
    "generate_cover_image",
    "save_visual_candidate",
    "discard_visual_candidate",
    "load_media_preview_detail",
    "preview_post",
    "run_check",
    "save_post",
    "publish_request",
}


def _blog_shell_event_dedupe_key(selected: str, slug: str) -> str:
    return _blog_editor_key(selected, slug, "processed_events")


def _blog_shell_notice_key(selected: str, slug: str) -> str:
    return _blog_editor_key(selected, slug, "operation_notice")


def _blog_ai_patch_key(selected: str, slug: str) -> str:
    return _blog_editor_key(selected, slug, "ai_patch")


def _blog_ai_stream_key(selected: str, slug: str) -> str:
    return _blog_editor_key(selected, slug, "ai_stream")


def _ai_stream_snapshot(task_id: str) -> dict:
    """Return a JSON-safe snapshot for a background AI stream task."""
    return ai_stream_tasks.snapshot(task_id)


def _cleanup_ai_stream_tasks(now: float | None = None) -> None:
    """Drop old completed stream tasks from the in-memory store."""
    ai_stream_tasks.cleanup(now)


def _start_ai_stream_task(
    *,
    task_id: str,
    profile: str,
    slug: str,
    meta: dict,
    markdown: str,
    selected_block: dict,
    operation: str,
    prompt: str,
    visual_kind: str,
) -> dict:
    """Start background generation and return the initial stream snapshot."""
    return ai_stream_tasks.start_ai_patch_stream(
        task_id=task_id,
        profile=profile,
        slug=slug,
        meta=meta,
        markdown=markdown,
        selected_block=selected_block,
        operation=operation,
        prompt=prompt,
        visual_kind=visual_kind,
    )


def _cancel_ai_stream_task(task_id: str) -> dict:
    """Request cancellation for a running AI stream task."""
    return ai_stream_tasks.cancel(task_id)


def _set_blog_shell_notice(
    selected: str,
    slug: str,
    *,
    tone: str,
    message: str,
    source: str = "",
) -> None:
    st.session_state[_blog_shell_notice_key(selected, slug)] = {
        "tone": tone,
        "message": message,
        "source": source,
        "created_at": time.time(),
    }


def _clear_blog_shell_notice(selected: str, slug: str) -> None:
    st.session_state.pop(_blog_shell_notice_key(selected, slug), None)


def _blog_shell_event_id(event: dict, action: str) -> str:
    """Return a stable id for one React shell event."""
    if not action:
        return ""
    payload = event.get("payload")
    payload = payload if isinstance(payload, dict) else {}
    for source in (event, payload):
        for field_name in ("event_id", "client_event_id"):
            value = source.get(field_name)
            if isinstance(value, str) and value.strip():
                return value.strip()
    if action not in _BLOG_EVENT_DEDUPE_ACTIONS:
        return ""
    try:
        signature = json.dumps(
            {
                "action": action,
                "payload": payload,
                "markdown": event.get("markdown", ""),
                "dirty": event.get("dirty", False),
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
    except Exception:
        signature = repr((action, payload))
    digest = hashlib.sha1(signature.encode("utf-8")).hexdigest()[:16]
    return f"legacy:{digest}"


def _blog_shell_event_already_processed(
    selected: str,
    slug: str,
    event: dict,
    action: str,
) -> bool:
    """Return True when Streamlit is replaying a component event after rerun."""
    event_id = _blog_shell_event_id(event, action)
    if not event_id:
        return False
    key = _blog_shell_event_dedupe_key(selected, slug)
    seen = st.session_state.get(key)
    if not isinstance(seen, list):
        seen = []
    if event_id in seen:
        return True
    seen.append(event_id)
    st.session_state[key] = seen[-120:]
    return False


def _blog_media_preview_details_key(selected: str, slug: str) -> str:
    return _blog_editor_key(selected, slug, "media_preview_details")


def _blog_media_preview_details(selected: str, slug: str) -> dict[str, dict]:
    details = st.session_state.get(_blog_media_preview_details_key(selected, slug), {})
    return details if isinstance(details, dict) else {}


def _merge_blog_media_preview_details(
    selected: str,
    slug: str,
    rows: list[dict],
) -> list[dict]:
    if not selected:
        return rows
    details = _blog_media_preview_details(selected, slug)
    if not details:
        return rows
    merged: list[dict] = []
    for row in rows:
        next_row = dict(row)
        rel = str(next_row.get("relative_path", "") or "").strip()
        detail = details.get(rel)
        if isinstance(detail, dict):
            next_row.update(detail)
        merged.append(next_row)
    return merged


def _blog_media_library(
    root: Path,
    slug: str,
    meta: dict,
    body: str,
    *,
    selected: str = "",
) -> list[dict]:
    """Return local media rows for one blog post."""
    rows = blog_media_library_rows(root, slug, meta, body)
    return _merge_blog_media_preview_details(selected, slug, rows)


def _blog_visual_results_key(selected: str, slug: str) -> str:
    return _blog_editor_key(selected, slug, "visual_results")


def _blog_visual_candidate_store_key(selected: str, slug: str) -> str:
    return _blog_editor_key(selected, slug, "visual_candidate_store")


def _blog_visual_candidate_payload(
    slug: str,
    assets: list[visual_generation.GeneratedVisualAsset],
    *,
    asset_type: str,
    alt: str = "",
    caption: str = "",
) -> tuple[list[dict], dict[str, dict]]:
    rows = blog_visual_candidate_rows(
        slug,
        assets,
        asset_type=asset_type,
        alt=alt,
        caption=caption,
    )
    store: dict[str, dict] = {}
    for row, asset in zip(rows, assets):
        candidate_id = str(row.get("id", "") or "")
        if not candidate_id:
            continue
        store[candidate_id] = {
            "data": asset.data,
            "filename": str(row.get("name", "") or "generated-visual.bin"),
            "kind": str(row.get("kind", "") or "image"),
            "mime_type": asset.mime_type,
            "asset_type": str(row.get("asset_type", "") or asset_type),
            "visual_kind": str(row.get("visual_kind", "") or ""),
            "alt": str(row.get("alt", "") or ""),
            "caption": str(row.get("caption", "") or ""),
        }
    return rows, store


def _blog_visual_session_rows(selected: str, slug: str) -> list[dict]:
    rows = st.session_state.get(_blog_visual_results_key(selected, slug), [])
    return rows if isinstance(rows, list) else []


def _blog_visual_session_store(selected: str, slug: str) -> dict[str, dict]:
    store = st.session_state.get(_blog_visual_candidate_store_key(selected, slug), {})
    return store if isinstance(store, dict) else {}


def _discard_blog_visual_candidate(selected: str, slug: str, candidate_id: str) -> None:
    rows = [
        row
        for row in _blog_visual_session_rows(selected, slug)
        if str(row.get("id", "") if isinstance(row, dict) else "") != candidate_id
    ]
    store = dict(_blog_visual_session_store(selected, slug))
    store.pop(candidate_id, None)
    st.session_state[_blog_visual_results_key(selected, slug)] = rows
    st.session_state[_blog_visual_candidate_store_key(selected, slug)] = store


def _save_blog_visual_candidate(
    *,
    selected: str,
    root: Path,
    slug: str,
    candidate_id: str,
    meta: dict,
    body: str,
) -> list[dict]:
    store = dict(_blog_visual_session_store(selected, slug))
    entry = store.get(candidate_id)
    if not isinstance(entry, dict):
        raise PublicSiteError("Visual candidate is no longer available.")
    data = entry.get("data")
    if not isinstance(data, bytes):
        raise PublicSiteError("Visual candidate data is no longer available.")
    result = add_blog_media_bytes(
        selected,
        slug,
        data=data,
        filename=str(entry.get("filename", "") or "generated-visual.bin"),
        kind=str(entry.get("kind", "") or "image"),
        alt=str(entry.get("alt", "") or ""),
        caption=str(entry.get("caption", "") or ""),
    )
    saved_rows = blog_visual_result_rows(
        root,
        slug,
        [result],
        asset_type=str(entry.get("asset_type", "") or "cover"),
        alt=str(entry.get("alt", "") or ""),
        caption=str(entry.get("caption", "") or ""),
        meta=meta,
        body=body,
    )
    for row in saved_rows:
        row["visual_kind"] = str(entry.get("visual_kind", "") or row.get("visual_kind", ""))
        row["saved"] = True
        row["unsaved"] = False
    rows: list[dict] = []
    replaced = False
    for row in _blog_visual_session_rows(selected, slug):
        if isinstance(row, dict) and str(row.get("id", "") or "") == candidate_id:
            rows.extend(saved_rows)
            replaced = True
        else:
            rows.append(row)
    if not replaced:
        rows.extend(saved_rows)
    store.pop(candidate_id, None)
    st.session_state[_blog_visual_results_key(selected, slug)] = rows
    st.session_state[_blog_visual_candidate_store_key(selected, slug)] = store
    refresh_file_snapshots([result.path])
    stash_git_backup_results()
    clear_web_cache()
    return saved_rows


def _load_blog_visual_preview_detail(
    *,
    selected: str,
    root: Path,
    slug: str,
    candidate_id: str = "",
    relative_path: str = "",
) -> None:
    rows = _blog_visual_session_rows(selected, slug)
    target_index = -1
    target_row: dict | None = None
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        row_id = str(row.get("id", "") or "")
        row_path = str(row.get("relative_path", "") or "")
        if (candidate_id and row_id == candidate_id) or (
            relative_path and row_path == relative_path
        ):
            target_index = index
            target_row = dict(row)
            break
    if target_index < 0 or target_row is None:
        raise PublicSiteError("Visual preview is no longer available.")
    if target_row.get("unsaved"):
        entry = _blog_visual_session_store(selected, slug).get(
            str(target_row.get("id", "") or "")
        )
        if not isinstance(entry, dict) or not isinstance(entry.get("data"), bytes):
            raise PublicSiteError("Visual candidate data is no longer available.")
        detail = blog_media_full_preview_payload(
            root,
            str(target_row.get("relative_path", "") or ""),
            data=entry["data"],
            filename=str(entry.get("filename", "") or target_row.get("name", "")),
            kind=str(entry.get("kind", "") or target_row.get("kind", "") or "image"),
            mime=str(entry.get("mime_type", "") or target_row.get("preview_mime", "")),
        )
    else:
        detail = blog_media_full_preview_payload(
            root,
            str(target_row.get("relative_path", "") or relative_path),
            kind=str(target_row.get("kind", "") or "image"),
        )
    if not detail.get("full_preview_src"):
        raise PublicSiteError("Full preview is not available for this media.")
    target_row.update(detail)
    rows[target_index] = target_row
    st.session_state[_blog_visual_results_key(selected, slug)] = rows


def _load_blog_media_preview_detail(
    *,
    selected: str,
    root: Path,
    slug: str,
    relative_path: str,
) -> None:
    rel = str(relative_path or "").strip()
    if not rel:
        raise PublicSiteError("Media path is missing.")
    target = _local_media_path(root, rel)
    if target is None:
        raise PublicSiteError(f"Media file does not exist: {rel}")
    ext = target.suffix.lower().lstrip(".")
    kind = "video" if ext in BLOG_VIDEO_EXTENSIONS else "image"
    if ext not in BLOG_IMAGE_EXTENSIONS and ext not in BLOG_VIDEO_EXTENSIONS:
        raise PublicSiteError(f"Unsupported media file: {rel}")
    detail = blog_media_full_preview_payload(root, rel, kind=kind)
    if not detail.get("full_preview_src"):
        raise PublicSiteError("Full preview is not available for this media.")
    details = dict(_blog_media_preview_details(selected, slug))
    details[rel] = {
        "relative_path": rel,
        **detail,
    }
    st.session_state[_blog_media_preview_details_key(selected, slug)] = details


def _trim_for_prompt(value: str, limit: int = 180) -> str:
    clean = re.sub(r"\s+", " ", str(value or "")).strip()
    return clean[:limit]


def _candidate_cover_prompt(candidates: list[dict]) -> str:
    for candidate in candidates:
        meta = candidate.get("meta") if isinstance(candidate.get("meta"), dict) else candidate
        prompt = str(meta.get("cover_prompt", "") or "").strip()
        if prompt:
            return prompt
    return ""


def _blog_visual_guidance(
    *,
    post,
    meta: dict,
    body: str,
    candidates: list[dict],
    ui: dict[str, str],
) -> dict:
    """Return visual prompt, size, style, and field guidance for the editor."""
    cfg = visual_generation.current_config()
    title = str(meta.get("title", "") or getattr(post, "title", "") or "").strip()
    summary = str(meta.get("summary", "") or getattr(post, "summary", "") or "").strip()
    tags = meta.get("tags") if isinstance(meta.get("tags"), list) else []
    tags_text = ", ".join(str(tag).strip() for tag in tags if str(tag).strip())
    gist = _trim_for_prompt(summary or body, 180)
    cover_prompt = (
        str(meta.get("cover_prompt", "") or "").strip()
        or _candidate_cover_prompt(candidates)
    )
    cover_base = cover_prompt or (
        "Editorial technical blog cover for "
        f"{title or 'this article'}, no embedded text, inspectable main subject, "
        "clear negative space for an HTML title overlay"
    )
    context_suffix = []
    if gist:
        context_suffix.append(f"context: {gist}")
    if tags_text:
        context_suffix.append(f"tags: {tags_text}")
    context = "; ".join(context_suffix)
    cover_suggestions = [
        {
            "label": ui["visual_suggest_cover"],
            "prompt": cover_base + (f"; {context}" if context else ""),
        },
        {
            "label": ui["visual_suggest_cover_subject"],
            "prompt": (
                f"One strong visual metaphor for {title or 'the article'}, "
                "realistic lighting, public technical blog cover, no text, no logo"
            ),
        },
        {
            "label": ui["visual_suggest_cover_diagram"],
            "prompt": (
                f"Layered technical editorial illustration for {title or 'the article'}, "
                "subtle system components, generous whitespace, no embedded words"
            ),
        },
    ]
    common = {
        "alt_help": ui["visual_alt_help"],
        "caption_help": ui["visual_caption_help"],
        "size_help": ui["visual_size_help"],
        "style_help": ui["visual_style_help"],
    }
    return {
        "cover": {
            **common,
            "default_size": str(cfg.get("default_cover_size") or "1536*864"),
            "size_options": [
                {"label": ui["visual_size_default"], "value": ""},
                {"label": "1536*864"},
                {"label": "1024*1024"},
                {"label": "2K"},
                {"label": "4K"},
            ],
            "style_options": [
                {"label": ui["visual_style_default"], "value": ""},
                {"label": "Editorial technical cover"},
                {"label": "Realistic product-style rendering"},
                {"label": "Clean isometric illustration"},
            ],
            "prompt_suggestions": cover_suggestions,
        },
        "flowchart": {
            **common,
            "default_size": str(cfg.get("default_diagram_size") or "1440*1440"),
            "size_options": [
                {"label": ui["visual_size_default"], "value": ""},
                {"label": "1440*1440"},
                {"label": "1024*1024"},
                {"label": "1536*864"},
                {"label": "2K"},
            ],
            "style_options": [
                {"label": ui["visual_style_default"], "value": ""},
                {"label": "Clean vector diagram"},
                {"label": "Whiteboard systems sketch"},
                {"label": "Minimal publication figure"},
            ],
            "prompt_suggestions": [
                {
                    "label": ui["visual_suggest_flow"],
                    "prompt": (
                        f"Flowchart for {title or 'this article'}: show major steps as "
                        "rectangular boxes with clear arrows, readable hierarchy, no tiny text"
                    ),
                },
                {
                    "label": ui["visual_suggest_flow_compare"],
                    "prompt": (
                        "Process comparison diagram with two lanes, labeled stages, clear "
                        "handoffs, high contrast, sparse labels"
                    ),
                },
            ],
        },
        "example": {
            **common,
            "default_size": str(cfg.get("default_example_size") or "1440*1440"),
            "size_options": [
                {"label": ui["visual_size_default"], "value": ""},
                {"label": "1440*1440"},
                {"label": "1024*1024"},
                {"label": "1536*864"},
                {"label": "2K"},
            ],
            "style_options": [
                {"label": ui["visual_style_default"], "value": ""},
                {"label": "Inspectable technical illustration"},
                {"label": "Realistic lab/demo scene"},
                {"label": "Annotated system mockup without tiny text"},
            ],
            "prompt_suggestions": [
                {
                    "label": ui["visual_suggest_example"],
                    "prompt": (
                        f"Concrete example scene for {title or 'this article'}, show the "
                        "system or workflow clearly, public-safe, no private paths"
                    ),
                },
                {
                    "label": ui["visual_suggest_example_system"],
                    "prompt": (
                        "Inspectable system illustration with clear components, realistic "
                        "workspace context, no watermark, no unreadable labels"
                    ),
                },
            ],
        },
        "video_edit": {
            **common,
            "default_size": "source-video",
            "size_help": ui["video_edit_source_help"],
            "size_options": [
                {"label": ui["visual_size_default"], "value": ""},
            ],
            "style_options": [
                {"label": ui["visual_style_default"], "value": ""},
                {"label": "Clean presentation edit"},
                {"label": "Subtle crop and color correction"},
            ],
            "prompt_suggestions": [
                {
                    "label": ui["visual_suggest_video"],
                    "prompt": (
                        "Clean presentation-ready edit: improve clarity, keep content factual, "
                        "avoid watermarks and private identifiers"
                    ),
                },
            ],
        },
    }


def _visual_option_pairs(options: list[dict | str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for option in options:
        if isinstance(option, dict):
            label = str(option.get("label", "") or option.get("value", "") or "").strip()
            value = str(option.get("value", "") if "value" in option else label).strip()
        else:
            label = str(option or "").strip()
            value = label
        if label:
            pairs.append((label, value))
    return pairs


def _media_snippet(kind: str, rel: str, alt: str = "", caption: str = "") -> str:
    if kind == "image":
        return f"![{alt or caption}]({rel})"
    return f"::video[{caption or alt}]({rel})"


def _decode_blog_upload_payload(payload: dict) -> bytes:
    raw = (
        payload.get("data_url")
        or payload.get("data")
        or payload.get("base64")
        or payload.get("content")
        or ""
    )
    if not isinstance(raw, str) or not raw.strip():
        raise PublicSiteError("Upload payload is missing base64 data.")
    encoded = raw.strip()
    if encoded.startswith("data:") and "," in encoded:
        encoded = encoded.split(",", 1)[1]
    try:
        return base64.b64decode(re.sub(r"\s+", "", encoded), validate=True)
    except Exception as exc:
        raise PublicSiteError("Upload payload is not valid base64 data.") from exc


def _store_blog_preview_html(
    selected: str,
    slug: str,
    meta: dict,
    body: str,
    *,
    preview_quality: str = "fast",
) -> str:
    quality = "full" if str(preview_quality or "").strip().lower() == "full" else "fast"
    html_text = render_blog_post_preview(
        selected,
        slug,
        meta,
        body,
        preview_quality=quality,
    )
    st.session_state[_blog_preview_html_key(selected, slug)] = html_text
    st.session_state[_blog_preview_quality_key(selected, slug)] = quality
    st.session_state[_blog_preview_fingerprint_key(selected, slug)] = (
        blog_preview_fingerprint(
            profile_dir(selected),
            meta,
            body,
            preview_quality=quality,
        )
    )
    return html_text


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
    if st_blocknote_markdown is None:
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


def _blog_publish_blocked(check_state: dict, ui: dict[str, str]) -> bool:
    """Return True when publish must pause for errors or privacy warnings."""
    if check_state.get("errors"):
        return True
    quality = check_state.get("quality")
    return isinstance(quality, list) and ui["privacy_hint"] in quality


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
    if st_blocknote_markdown is not None:
        edited = st_blocknote_markdown(
            initial_markdown=body,
            document_id=f"{selected}:{slug}",
            height=560,
            math_safe=True,
            key=f"{key}:blocknote",
        )
        if isinstance(edited, str):
            return edited
    else:
        st.info(ui["blocknote_unavailable"])
    return st.text_area(
        ui["body"],
        value=body,
        height=520,
        key=f"{key}:fallback:{body_token}",
    )


def _blog_page_preview(
    selected: str,
    slug: str,
    ui: dict[str, str],
    *,
    meta: dict | None = None,
    body: str | None = None,
    preview_quality: str = "fast",
) -> None:
    """Render the generated public blog detail page preview."""
    st.subheader(ui["site_post_preview"])
    if meta is not None and body is not None:
        try:
            html_text = render_blog_post_preview(
                selected,
                slug,
                meta,
                body,
                preview_quality=preview_quality,
            )
        except Exception as exc:
            st.error(str(exc))
            return
        components.html(html_text, height=960, scrolling=True)
        return
    try:
        preview = render_public_site_preview(
            selected,
            include_drafts=True,
            preview_quality=preview_quality,
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
        height=960,
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
        selected=selected,
    )
    ai_candidates = _blog_shell_ai_candidates(selected, latest_post.slug)
    visual_results = st.session_state.get(
        _blog_visual_results_key(selected, latest_post.slug),
        [],
    )
    if not isinstance(visual_results, list):
        visual_results = []
    check_state = st.session_state.get(
        _blog_check_state_key(selected, latest_post.slug),
        {"errors": [], "warnings": [], "quality": []},
    )
    preview_html = st.session_state.get(
        _blog_preview_html_key(selected, latest_post.slug),
        "",
    )
    if preview_html:
        preview_quality = str(
            st.session_state.get(
                _blog_preview_quality_key(selected, latest_post.slug),
                "fast",
            )
            or "fast"
        )
        expected_fingerprint = blog_preview_fingerprint(
            root,
            draft_meta,
            draft_body,
            preview_quality=preview_quality,
        )
        if (
            st.session_state.get(
                _blog_preview_fingerprint_key(selected, latest_post.slug)
            )
            != expected_fingerprint
        ):
            preview_html = ""
            _clear_blog_preview(selected, latest_post.slug)
    editor_kwargs = {
        "posts": _blog_shell_posts_payload(posts),
        "active_slug": latest_post.slug,
        "initial_markdown": draft_body,
        "active_post_meta": draft_meta,
        "media_items": media_rows,
        "ai_candidates": ai_candidates,
        "validation_state": check_state,
        "visual_config": visual_generation.current_config(),
        "visual_results": visual_results,
        "visual_guidance": _blog_visual_guidance(
            post=latest_post,
            meta=draft_meta,
            body=draft_body,
            candidates=ai_candidates,
            ui=ui,
        ),
        "ai_patch": st.session_state.get(
            _blog_ai_patch_key(selected, latest_post.slug),
            {},
        ),
        "ai_stream": _ai_stream_snapshot(
            str(
                st.session_state.get(
                    _blog_ai_stream_key(selected, latest_post.slug),
                    "",
                )
                or ""
            )
        ),
        "operation_notice": st.session_state.get(
            _blog_shell_notice_key(selected, latest_post.slug),
            {},
        ),
        "preview_html": str(preview_html or ""),
        "status_filter": (
            "all"
            if st.session_state.get(f"blog_status_filter:{selected}", ui["all_statuses"])
            == ui["all_statuses"]
            else str(st.session_state.get(f"blog_status_filter:{selected}", "all"))
        ),
        "layout_state": layout_state,
        "ui_labels": ui,
        "document_id": f"{selected}:{latest_post.slug}",
        "layout_storage_key": _blog_layout_storage_key(selected, latest_post.slug),
        "key": _blog_editor_key(selected, latest_post.slug, "react_shell"),
        "height": 960,
        "editable": True,
        "math_safe": True,
    }
    try:
        event = st_public_blog_editor(**editor_kwargs)
    except TypeError as exc:
        if "unexpected keyword argument 'ai_patch'" in str(exc):
            editor_kwargs.pop("ai_patch", None)
        elif "unexpected keyword argument 'ai_stream'" in str(exc):
            editor_kwargs.pop("ai_stream", None)
        else:
            raise
        event = st_public_blog_editor(**editor_kwargs)

    if not isinstance(event, dict):
        return True

    action, event_meta, event_body, dirty = _blog_shell_event_payload(
        event,
        draft_meta,
        draft_body,
    )
    if _blog_shell_event_already_processed(
        selected,
        latest_post.slug,
        event,
        action,
    ):
        return True
    event_layout = event.get("layout_state")
    if isinstance(event_layout, dict):
        _persist_blog_layout_state(selected, latest_post.slug, event_layout)
    payload = event.get("payload")
    payload = payload if isinstance(payload, dict) else {}

    if action in {
        "markdown_changed",
        "layout_state_changed",
        "insert_media",
        "insert_candidate",
        "apply_candidate_meta",
        "apply_ai_patch",
    }:
        if action == "insert_media":
            media = payload.get("media")
            media = media if isinstance(media, dict) else {}
            rel = str(media.get("relative_path", "") or "").strip()
            if media.get("unsaved"):
                st.error("Visual candidate must be saved to media before insertion.")
                return True
            if rel and _local_media_path(root, rel) is None:
                st.error(f"Media file does not exist: {rel}")
                return True
        _blog_shell_store_draft(
            selected,
            latest_post.slug,
            event_meta,
            event_body,
            dirty=dirty,
        )
        if action in {
            "markdown_changed",
            "insert_media",
            "insert_candidate",
            "apply_candidate_meta",
            "apply_ai_patch",
        }:
            _clear_blog_preview(selected, latest_post.slug)
        if action == "apply_ai_patch":
            st.session_state.pop(_blog_ai_patch_key(selected, latest_post.slug), None)
            st.session_state.pop(_blog_ai_stream_key(selected, latest_post.slug), None)
        return True

    if action == "delete_media":
        try:
            media = payload.get("media")
            media = media if isinstance(media, dict) else {}
            rel = str(
                payload.get("relative_path", "")
                or media.get("relative_path", "")
                or ""
            ).strip()
            if media.get("unsaved"):
                st.error("Visual candidate must be saved to media before deletion.")
                return True
            cover = str(event_meta.get("cover", "") or "").strip()
            if rel and (rel in event_body or rel == cover):
                st.error(ui["delete_media_referenced"])
                return True
            deleted_path = delete_blog_media(
                selected,
                latest_post.slug,
                rel,
                meta=event_meta,
                body=event_body,
            )
            details = dict(_blog_media_preview_details(selected, latest_post.slug))
            details.pop(rel, None)
            st.session_state[
                _blog_media_preview_details_key(selected, latest_post.slug)
            ] = details
            st.session_state[
                _blog_visual_results_key(selected, latest_post.slug)
            ] = [
                row
                for row in _blog_visual_session_rows(selected, latest_post.slug)
                if not isinstance(row, dict)
                or str(row.get("relative_path", "") or "") != rel
            ]
            _blog_shell_store_draft(
                selected,
                latest_post.slug,
                event_meta,
                event_body,
                dirty=dirty,
            )
            _clear_blog_preview(selected, latest_post.slug)
            refresh_file_snapshots([deleted_path])
            stash_git_backup_results()
            clear_web_cache()
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
        return True

    if action == "convert_media_video":
        try:
            media = payload.get("media")
            media = media if isinstance(media, dict) else {}
            rel = str(
                payload.get("relative_path", "")
                or media.get("relative_path", "")
                or ""
            ).strip()
            if media.get("unsaved"):
                st.error("Visual candidate must be saved to media before conversion.")
                return True
            result = convert_blog_media_video(selected, latest_post.slug, rel)
            next_body = str(event_body or "")
            if rel and rel in next_body:
                next_body = next_body.replace(rel, result.relative_path)
            _blog_shell_store_draft(
                selected,
                latest_post.slug,
                event_meta,
                next_body,
                dirty=True,
            )
            details = dict(_blog_media_preview_details(selected, latest_post.slug))
            details.pop(rel, None)
            st.session_state[
                _blog_media_preview_details_key(selected, latest_post.slug)
            ] = details
            _clear_blog_preview(selected, latest_post.slug)
            refresh_file_snapshots([result.path])
            stash_git_backup_results()
            clear_web_cache()
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
        return True

    if action == "select_post":
        _blog_shell_store_draft(
            selected,
            latest_post.slug,
            event_meta,
            event_body,
            dirty=dirty,
        )
        slug = str(payload.get("slug", "") or "")
        if slug and slug != latest_post.slug:
            st.session_state[f"blog_post_slug_select:{selected}"] = slug
            st.rerun()
        return True

    if action == "filter_posts":
        status = str(payload.get("status", "all") or "all")
        st.session_state[f"blog_status_filter:{selected}"] = (
            ui["all_statuses"]
            if status == "all"
            else status if status in {"draft", "published", "archived"} else ui["all_statuses"]
        )
        st.rerun()
        return True

    if action == "create_post":
        _blog_shell_store_draft(
            selected,
            latest_post.slug,
            event_meta,
            event_body,
            dirty=dirty,
        )
        title = str(payload.get("title", "") or "").strip()
        if not title:
            st.warning(ui["title_label"])
            return True
        try:
            path = create_blog_draft(
                selected,
                title=title,
                body=f"{BLOG_INSERT_MARKER}\n\n",
                summary="",
            )
            st.session_state[f"blog_post_slug_select:{selected}"] = path.stem
            stash_git_backup_results()
            clear_web_cache()
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
        return True

    if action == "draft_from_evidence":
        _blog_shell_store_draft(
            selected,
            latest_post.slug,
            event_meta,
            event_body,
            dirty=dirty,
        )
        evidence_id = str(payload.get("evidence_id", "") or "").strip()
        try:
            path = draft_blog_from_evidence(selected, evidence_id)
            st.session_state[f"blog_post_slug_select:{selected}"] = path.stem
            stash_git_backup_results()
            clear_web_cache()
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
        return True

    if action == "draft_from_done":
        _blog_shell_store_draft(
            selected,
            latest_post.slug,
            event_meta,
            event_body,
            dirty=dirty,
        )
        try:
            path = draft_blog_from_kanban_done(selected)
            st.session_state[f"blog_post_slug_select:{selected}"] = path.stem
            stash_git_backup_results()
            clear_web_cache()
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
        return True

    if action == "ai_inline_action":
        _blog_shell_store_draft(
            selected,
            latest_post.slug,
            event_meta,
            event_body,
            dirty=dirty,
        )
        try:
            _clear_blog_shell_notice(selected, latest_post.slug)
            selected_block = payload.get("selected_block")
            if not isinstance(selected_block, dict):
                selected_block = event.get("selected_block")
            if not isinstance(selected_block, dict):
                selected_block = {}
            stream_id = str(
                payload.get("stream_id", "")
                or payload.get("event_id", "")
                or event.get("event_id", "")
                or f"ai-stream-{uuid.uuid4().hex[:12]}"
            )
            _start_ai_stream_task(
                task_id=stream_id,
                profile=selected,
                slug=latest_post.slug,
                meta=event_meta,
                markdown=event_body,
                selected_block=selected_block,
                operation=str(payload.get("operation", "") or "polish"),
                prompt=str(payload.get("prompt", "") or ""),
                visual_kind=str(payload.get("visual_kind", "") or ""),
            )
            st.session_state[_blog_ai_stream_key(selected, latest_post.slug)] = stream_id
            st.session_state.pop(_blog_ai_patch_key(selected, latest_post.slug), None)
            _set_blog_shell_notice(
                selected,
                latest_post.slug,
                tone="info",
                message="AI generation started.",
                source="ai",
            )
            next_state = dict(layout_state)
            next_state["right_open"] = True
            next_state["active_right_tab"] = "AI"
            next_state["focus_mode"] = False
            _rerun_with_blog_layout(selected, latest_post.slug, next_state)
        except Exception as exc:
            message = str(exc)
            st.session_state.pop(_blog_ai_patch_key(selected, latest_post.slug), None)
            st.session_state.pop(_blog_ai_stream_key(selected, latest_post.slug), None)
            _set_blog_shell_notice(
                selected,
                latest_post.slug,
                tone="error",
                message=message,
                source="ai",
            )
            st.error(message)
            st.rerun()
        return True

    if action == "ai_stream_poll":
        stream_id = str(
            payload.get("stream_id", "")
            or st.session_state.get(_blog_ai_stream_key(selected, latest_post.slug), "")
            or ""
        )
        snapshot = _ai_stream_snapshot(stream_id)
        if snapshot.get("status") == "done":
            patch = snapshot.get("patch")
            if isinstance(patch, dict) and patch.get("operation"):
                st.session_state[_blog_ai_patch_key(selected, latest_post.slug)] = patch
                _set_blog_shell_notice(
                    selected,
                    latest_post.slug,
                    tone="success",
                    message="AI patch candidate is ready.",
                    source="ai",
                )
                st.rerun()
        elif snapshot.get("status") == "failed":
            st.session_state.pop(_blog_ai_patch_key(selected, latest_post.slug), None)
            _set_blog_shell_notice(
                selected,
                latest_post.slug,
                tone="error",
                message=str(snapshot.get("error", "") or "AI generation failed."),
                source="ai",
            )
            st.rerun()
        elif snapshot.get("status") == "cancelled":
            st.session_state.pop(_blog_ai_patch_key(selected, latest_post.slug), None)
            _set_blog_shell_notice(
                selected,
                latest_post.slug,
                tone="info",
                message="AI generation cancelled.",
                source="ai",
            )
            st.rerun()
        return True

    if action == "cancel_ai_stream":
        stream_id = str(
            payload.get("stream_id", "")
            or st.session_state.get(_blog_ai_stream_key(selected, latest_post.slug), "")
            or ""
        )
        _cancel_ai_stream_task(stream_id)
        st.session_state[_blog_ai_stream_key(selected, latest_post.slug)] = stream_id
        st.session_state.pop(_blog_ai_patch_key(selected, latest_post.slug), None)
        _set_blog_shell_notice(
            selected,
            latest_post.slug,
            tone="info",
            message="AI generation cancelled.",
            source="ai",
        )
        st.rerun()
        return True

    if action == "reject_ai_patch":
        st.session_state.pop(_blog_ai_patch_key(selected, latest_post.slug), None)
        st.session_state.pop(_blog_ai_stream_key(selected, latest_post.slug), None)
        _clear_blog_shell_notice(selected, latest_post.slug)
        st.rerun()
        return True

    if action == "generate_ai_candidate":
        try:
            source = str(payload.get("source", "title") or "title")
            if source == "evidence":
                candidate = blog_candidate_from_evidence(
                    selected,
                    str(payload.get("evidence_id", "") or "").strip(),
                )
            elif source == "kanban_done":
                candidate = blog_candidate_from_kanban_done(selected)
            else:
                candidate = blog_candidate_from_title(
                    selected,
                    str(payload.get("title", "") or event_meta.get("title", "") or latest_post.title),
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

    if action == "upload_media":
        try:
            data = _decode_blog_upload_payload(payload)
            filename = str(payload.get("filename", "") or "upload.bin")
            kind = str(payload.get("kind", "") or "image").strip().lower()
            alt = str(payload.get("alt", "") or "").strip()
            caption = str(payload.get("caption", "") or "").strip()
            insert = bool(payload.get("insert", False))
            placement = str(payload.get("placement", "") or "marker").strip().lower()
            cover = bool(payload.get("cover", False))
            if cover and kind != "image":
                raise PublicSiteError(ui["set_cover"])
            result = add_blog_media_bytes(
                selected,
                latest_post.slug,
                data=data,
                filename=filename,
                kind=kind,
                alt=alt,
                caption=caption,
            )
            next_meta = dict(event_meta)
            next_body = event_body
            if insert:
                next_body = (
                    _append_candidate_to_body(next_body, result.snippet)
                    if placement == "append"
                    else insert_blog_snippet(next_body, result.snippet)
                )
            if cover:
                next_meta["cover"] = result.relative_path
            _blog_shell_store_draft(
                selected,
                latest_post.slug,
                next_meta,
                next_body,
                dirty=dirty or insert or cover,
            )
            _clear_blog_preview(selected, latest_post.slug)
            refresh_file_snapshots([result.path])
            stash_git_backup_results()
            clear_web_cache()
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
        return True

    if action in {"generate_visual_asset", "generate_cover_image"}:
        try:
            _clear_blog_shell_notice(selected, latest_post.slug)
            asset_type = str(payload.get("asset_type", "") or "cover")
            clean_type = "cover" if action == "generate_cover_image" else asset_type
            prompt = str(payload.get("prompt", "") or "").strip()
            style = str(payload.get("style", "") or "").strip()
            size = str(payload.get("size", "") or "").strip()
            alt = str(payload.get("alt", "") or "").strip()
            caption = str(payload.get("caption", "") or "").strip()
            generated = visual_generation.generate_visual_asset(
                clean_type,
                prompt,
                style=style,
                size=size,
                title=str(event_meta.get("title", "") or latest_post.title),
                summary=str(event_meta.get("summary", "") or latest_post.summary),
                tags=[
                    str(tag).strip()
                    for tag in event_meta.get("tags", [])
                    if str(tag).strip()
                ]
                if isinstance(event_meta.get("tags"), list)
                else [],
                body=event_body,
                source_video=_visual_media_input_for_generation(
                    root,
                    str(payload.get("source_video", "") or ""),
                ),
                reference_image=_visual_media_input_for_generation(
                    root,
                    str(payload.get("reference_image", "") or ""),
                ),
            )
            rows, store = _blog_visual_candidate_payload(
                latest_post.slug,
                generated,
                asset_type=clean_type,
                alt=alt,
                caption=caption,
            )
            st.session_state[
                _blog_visual_results_key(selected, latest_post.slug)
            ] = rows
            st.session_state[
                _blog_visual_candidate_store_key(selected, latest_post.slug)
            ] = store
            _set_blog_shell_notice(
                selected,
                latest_post.slug,
                tone="success",
                message=f"Generated {len(rows)} visual candidate(s).",
                source="visual",
            )
            st.rerun()
        except Exception as exc:
            message = str(exc)
            _set_blog_shell_notice(
                selected,
                latest_post.slug,
                tone="error",
                message=message,
                source="visual",
            )
            st.error(message)
            st.rerun()
        return True

    if action == "save_visual_candidate":
        candidate_id = str(payload.get("candidate_id", "") or "").strip()
        try:
            if not candidate_id:
                raise PublicSiteError("Visual candidate id is missing.")
            _save_blog_visual_candidate(
                selected=selected,
                root=root,
                slug=latest_post.slug,
                candidate_id=candidate_id,
                meta=event_meta,
                body=event_body,
            )
            _clear_blog_preview(selected, latest_post.slug)
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
        return True

    if action == "discard_visual_candidate":
        candidate_id = str(payload.get("candidate_id", "") or "").strip()
        if candidate_id:
            _discard_blog_visual_candidate(selected, latest_post.slug, candidate_id)
            _clear_blog_preview(selected, latest_post.slug)
            st.rerun()
        return True

    if action == "load_media_preview_detail":
        try:
            media = payload.get("media")
            media = media if isinstance(media, dict) else {}
            candidate_id = str(
                payload.get("candidate_id", "") or media.get("id", "") or ""
            ).strip()
            relative_path = str(
                payload.get("relative_path", "")
                or media.get("relative_path", "")
                or ""
            ).strip()
            source = str(payload.get("source", "") or "").strip().lower()
            if source == "visual" or candidate_id or media.get("unsaved"):
                _load_blog_visual_preview_detail(
                    selected=selected,
                    root=root,
                    slug=latest_post.slug,
                    candidate_id=candidate_id,
                    relative_path=relative_path,
                )
            else:
                _load_blog_media_preview_detail(
                    selected=selected,
                    root=root,
                    slug=latest_post.slug,
                    relative_path=relative_path,
                )
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
        return True

    if action == "preview_post":
        _blog_shell_store_draft(
            selected,
            latest_post.slug,
            event_meta,
            event_body,
            dirty=dirty,
        )
        try:
            preview_quality = str(payload.get("preview_quality", "") or "fast")
            _store_blog_preview_html(
                selected,
                latest_post.slug,
                event_meta,
                event_body,
                preview_quality=preview_quality,
            )
            next_state = dict(layout_state)
            next_state["preview_open"] = True
            next_state["focus_mode"] = False
            _rerun_with_blog_layout(selected, latest_post.slug, next_state)
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
            selected=selected,
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
        if _blog_publish_blocked(check, ui):
            if ui["privacy_hint"] in check.get("quality", []):
                st.warning(ui["privacy_publish_blocked"])
            next_state = dict(layout_state)
            next_state["right_open"] = True
            next_state["active_right_tab"] = "Check"
            next_state["focus_mode"] = False
            _rerun_with_blog_layout(selected, latest_post.slug, next_state)
        try:
            assert_files_current([latest_post.path])
            published = publish_blog_text(
                selected,
                latest_post.slug,
                publish_meta,
                event_body,
            )
            refresh_file_snapshots([published])
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["saved"])
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
        selected_path = _local_media_path(root, selected_rel)
        if selected_path is not None:
            if selected_row["kind"] == "image":
                st.image(str(selected_path), use_container_width=True)
            elif selected_row["kind"] == "video":
                st.video(str(selected_path))
                if selected_row.get("video_browser_compatible") is False:
                    st.warning(ui["video_incompatible"])
        alt = st.text_input(
            ui["alt_text"],
            key=_blog_editor_key(selected, latest_post.slug, "library_alt"),
        )
        caption = st.text_input(
            ui["caption"],
            key=_blog_editor_key(selected, latest_post.slug, "library_caption"),
        )
        placement = st.selectbox(
            ui["insert_placement"],
            [ui["insert_at_marker"], ui["insert_at_end"]],
            key=_blog_editor_key(selected, latest_post.slug, "library_insert_placement"),
        )
        insert_col, cover_col, convert_col, delete_col = st.columns(4)
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
                        body=(
                            _append_candidate_to_body(edited_body, snippet)
                            if placement == ui["insert_at_end"]
                            else insert_blog_snippet(edited_body, snippet)
                        ),
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
        with convert_col:
            if st.button(
                ui["convert_video"],
                key=_blog_editor_key(selected, latest_post.slug, "convert_library"),
                use_container_width=True,
                disabled=selected_row["kind"] != "video",
            ):
                try:
                    result = convert_blog_media_video(
                        selected,
                        latest_post.slug,
                        selected_rel,
                    )
                    next_body = edited_body.replace(selected_rel, result.relative_path)
                    _save_blog_editor(
                        selected=selected,
                        post_path=latest_post.path,
                        meta=edited_meta,
                        body=next_body,
                        ui=ui,
                    )
                    refresh_file_snapshots([result.path])
                    stash_git_backup_results()
                    clear_web_cache()
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with delete_col:
            if st.button(
                ui["delete_media"],
                key=_blog_editor_key(selected, latest_post.slug, "delete_library"),
                use_container_width=True,
                disabled=bool(selected_row.get("referenced")),
                help=ui["delete_media_referenced"]
                if selected_row.get("referenced")
                else ui["delete_media_confirm"],
            ):
                try:
                    deleted_path = delete_blog_media(
                        selected,
                        latest_post.slug,
                        selected_rel,
                        meta=edited_meta,
                        body=edited_body,
                    )
                    _clear_blog_preview(selected, latest_post.slug)
                    refresh_file_snapshots([deleted_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    st.rerun()
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


def _render_blog_visual_results_panel(
    *,
    selected: str,
    latest_post,
    edited_meta: dict,
    edited_body: str,
    ui: dict[str, str],
) -> None:
    """Render recent visual candidates in the Streamlit fallback UI."""
    rows = st.session_state.get(_blog_visual_results_key(selected, latest_post.slug), [])
    if not isinstance(rows, list) or not rows:
        return
    st.markdown(f"**{ui['recent_visuals']}**")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name", "") or row.get("relative_path", "") or ui["media"])
        kind = str(row.get("kind", "") or "image")
        preview_src = str(row.get("preview_src", "") or "")
        snippet = str(row.get("snippet", "") or _media_snippet(
            kind,
            str(row.get("relative_path", "") or ""),
            alt=str(row.get("alt", "") or ""),
            caption=str(row.get("caption", "") or ""),
        ))
        st.caption(f"{name} · {kind} · {row.get('size_kb', '-')} KB")
        if preview_src and kind == "image":
            st.image(preview_src, use_container_width=True)
        elif not preview_src:
            st.caption(ui["preview_unavailable"])
        if snippet:
            st.code(snippet, language="markdown")
        if bool(row.get("unsaved", False)):
            save_col, discard_col = st.columns(2)
            with save_col:
                if st.button(
                    ui["save_to_media"],
                    key=_blog_editor_key(
                        selected,
                        latest_post.slug,
                        f"visual_result_save_{index}",
                    ),
                    use_container_width=True,
                ):
                    try:
                        _save_blog_visual_candidate(
                            selected=selected,
                            root=latest_post.path.parents[1],
                            slug=latest_post.slug,
                            candidate_id=str(row.get("id", "") or ""),
                            meta=edited_meta,
                            body=edited_body,
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with discard_col:
                if st.button(
                    ui["discard_candidate"],
                    key=_blog_editor_key(
                        selected,
                        latest_post.slug,
                        f"visual_result_discard_{index}",
                    ),
                    use_container_width=True,
                ):
                    _discard_blog_visual_candidate(
                        selected,
                        latest_post.slug,
                        str(row.get("id", "") or ""),
                    )
                    st.rerun()
            continue
        insert_col, cover_col = st.columns(2)
        with insert_col:
            if st.button(
                ui["insert_into_post"],
                key=_blog_editor_key(
                    selected,
                    latest_post.slug,
                    f"visual_result_insert_{index}",
                ),
                use_container_width=True,
            ):
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
                key=_blog_editor_key(
                    selected,
                    latest_post.slug,
                    f"visual_result_cover_{index}",
                ),
                use_container_width=True,
                disabled=kind != "image",
            ):
                next_meta = dict(edited_meta)
                next_meta["cover"] = str(row.get("relative_path", "") or "")
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


def _render_blog_visual_panel(
    *,
    selected: str,
    root: Path,
    latest_post,
    edited_meta: dict,
    edited_body: str,
    ui: dict[str, str],
) -> None:
    """Render visual-generation status for the Streamlit fallback drawer."""
    cfg = visual_generation.current_config()
    st.caption(
        f"{ui['visual_provider']}: {cfg.get('provider')} · "
        f"{cfg.get('image_model')} · {ui['using_key_from']} "
        f"{cfg.get('api_key_source') or '-'}"
    )
    for warning in cfg.get("warnings", []):
        st.warning(str(warning))
    candidates = _blog_shell_ai_candidates(selected, latest_post.slug)
    guidance = _blog_visual_guidance(
        post=latest_post,
        meta=edited_meta,
        body=edited_body,
        candidates=candidates,
        ui=ui,
    )
    asset_type = st.selectbox(
        ui["visual"],
        ["cover", "flowchart", "example", "video_edit"],
        format_func=lambda value: ui.get(value, value),
        key=_blog_editor_key(selected, latest_post.slug, "visual_asset_type"),
    )
    guide = guidance.get(str(asset_type), {})
    prompt_key = _blog_editor_key(selected, latest_post.slug, "visual_prompt")
    suggestions = guide.get("prompt_suggestions") if isinstance(guide, dict) else []
    if suggestions:
        st.caption(ui["visual_prompt_suggestions"])
        suggestion_cols = st.columns(min(3, len(suggestions)))
        for index, suggestion in enumerate(suggestions):
            if not isinstance(suggestion, dict):
                continue
            with suggestion_cols[index % len(suggestion_cols)]:
                if st.button(
                    str(suggestion.get("label", "") or ui["visual_prompt"]),
                    key=_blog_editor_key(
                        selected,
                        latest_post.slug,
                        f"visual_suggestion_{asset_type}_{index}",
                    ),
                    use_container_width=True,
                ):
                    st.session_state[prompt_key] = str(suggestion.get("prompt", "") or "")
                    st.rerun()
    prompt = st.text_area(
        ui["visual_prompt"],
        key=prompt_key,
        height=120,
    )
    source_video = ""
    reference_image = ""
    if str(asset_type) == "video_edit":
        source_video = st.text_input(
            ui["source_video_manual"],
            key=_blog_editor_key(selected, latest_post.slug, "visual_source_video"),
        )
        st.caption(ui["video_edit_source_help"])
        reference_image = st.text_input(
            ui["reference_image_manual"],
            key=_blog_editor_key(selected, latest_post.slug, "visual_reference_image"),
        )
    style_pairs = _visual_option_pairs(list(guide.get("style_options") or []))
    style_pairs.append((ui["visual_custom"], "__custom__"))
    style_labels = [label for label, _value in style_pairs]
    style_label = st.selectbox(
        ui["visual_style"],
        style_labels,
        key=_blog_editor_key(selected, latest_post.slug, "visual_style_choice"),
    )
    style_value = dict(style_pairs).get(style_label, "")
    if style_value == "__custom__":
        style_value = st.text_input(
            ui["visual_custom"],
            key=_blog_editor_key(selected, latest_post.slug, "visual_style_custom"),
        )
    st.caption(str(guide.get("style_help", "") or ""))
    size_pairs = _visual_option_pairs(list(guide.get("size_options") or []))
    size_pairs.append((ui["visual_custom"], "__custom__"))
    size_labels = [label for label, _value in size_pairs]
    size_label = st.selectbox(
        ui["visual_size"],
        size_labels,
        key=_blog_editor_key(selected, latest_post.slug, "visual_size_choice"),
    )
    size_value = dict(size_pairs).get(size_label, "")
    if size_value == "__custom__":
        size_value = st.text_input(
            ui["visual_size_custom"],
            key=_blog_editor_key(selected, latest_post.slug, "visual_size_custom"),
        )
    default_size = str(guide.get("default_size", "") or "")
    st.caption(f"{guide.get('size_help', '')} {ui['visual_default']}: {default_size}")
    alt = st.text_input(
        ui["alt_text"],
        key=_blog_editor_key(selected, latest_post.slug, "visual_alt"),
    )
    st.caption(str(guide.get("alt_help", "") or ""))
    caption = st.text_input(
        ui["caption"],
        key=_blog_editor_key(selected, latest_post.slug, "visual_caption"),
    )
    st.caption(str(guide.get("caption_help", "") or ""))
    if st.button(
        ui["generate_visual"],
        key=_blog_editor_key(selected, latest_post.slug, "visual_generate"),
        use_container_width=True,
        disabled=(
            not bool(cfg.get("configured"))
            or not str(prompt or "").strip()
            or (str(asset_type) == "video_edit" and not source_video.strip())
        ),
    ):
        try:
            generated = visual_generation.generate_visual_asset(
                str(asset_type),
                prompt,
                style=style_value,
                size=size_value,
                title=str(edited_meta.get("title", "") or latest_post.title),
                summary=str(edited_meta.get("summary", "") or latest_post.summary),
                tags=[
                    str(tag).strip()
                    for tag in edited_meta.get("tags", [])
                    if str(tag).strip()
                ]
                if isinstance(edited_meta.get("tags"), list)
                else [],
                body=edited_body,
                source_video=_visual_media_input_for_generation(root, source_video),
                reference_image=_visual_media_input_for_generation(root, reference_image),
            )
            rows, store = _blog_visual_candidate_payload(
                latest_post.slug,
                generated,
                asset_type=str(asset_type),
                alt=alt.strip(),
                caption=caption.strip(),
            )
            st.session_state[
                _blog_visual_results_key(selected, latest_post.slug)
            ] = rows
            st.session_state[
                _blog_visual_candidate_store_key(selected, latest_post.slug)
            ] = store
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    _render_blog_visual_results_panel(
        selected=selected,
        latest_post=latest_post,
        edited_meta=edited_meta,
        edited_body=edited_body,
        ui=ui,
    )


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
    _blog_page_preview(
        selected,
        latest_post.slug,
        ui,
        meta=edited_meta,
        body=edited_body,
    )


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
    elif active_tab == "Visual":
        _render_blog_visual_panel(
            selected=selected,
            root=root,
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
            _blog_page_preview(
                selected,
                latest_post.slug,
                ui,
                meta=edited_meta,
                body=edited_body,
            )

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
        selected=selected,
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
                            collapse_current=True,
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
        selected=selected,
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
        if _blog_publish_blocked(check_state, ui):
            if ui["privacy_hint"] in check_state.get("quality", []):
                st.warning(ui["privacy_publish_blocked"])
            next_state = dict(layout_state)
            next_state["right_open"] = True
            next_state["active_right_tab"] = "Check"
            next_state["focus_mode"] = False
            _rerun_with_blog_layout(selected, latest_post.slug, next_state)
        try:
            assert_files_current([latest_post.path])
            published = publish_blog_text(
                selected,
                latest_post.slug,
                publish_meta,
                edited_body,
            )
            refresh_file_snapshots([published])
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["saved"])
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
