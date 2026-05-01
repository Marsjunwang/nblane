import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { createRoot } from "react-dom/client";
import { Streamlit } from "streamlit-component-lib";
import { BlockNoteView } from "@blocknote/mantine";
import { filterSuggestionItems } from "@blocknote/core";
import {
  getDefaultReactSlashMenuItems,
  SuggestionMenuController,
  useCreateBlockNote,
} from "@blocknote/react";
import "@blocknote/core/fonts/inter.css";
import "@blocknote/mantine/style.css";
import "./style.css";
import { CandidatePatchPanel } from "./ai/CandidatePatchPanel.jsx";
import { SelectionAIToolbar } from "./ai/SelectionAIToolbar.jsx";
import { getAISlashMenuItems } from "./ai/slashItems.js";
import { normalizeAIStream, useAIStream } from "./ai/useAIStream.js";
import { blogSchema, getBlogSlashMenuItems } from "./blocks/blogBlocks.jsx";
import {
  blocksToNblaneMarkdown,
  containsDisplayMathBlock,
  isRawMarkdownDirective,
  parseMarkdownToEditorBlocks,
} from "./blocks/markdown.js";

const RIGHT_TABS = ["Meta", "Media", "AI", "Visual", "Check"];
const MOBILE_VIEWS = ["Editor", "Articles", "Tools", "Preview"];
const STATUS_OPTIONS = ["draft", "published", "archived"];
const INSERT_MARKER = "<!-- nblane:insert -->";
const WRITE_ACTIONS = new Set([
  "markdown_changed",
  "save_post",
  "publish_request",
  "insert_candidate",
  "insert_media",
  "delete_media",
  "convert_media_video",
  "apply_candidate_meta",
  "generate_ai_candidate",
  "ai_inline_action",
  "cancel_ai_stream",
  "apply_ai_patch",
  "reject_ai_patch",
  "upload_media",
  "generate_visual_asset",
  "generate_cover_image",
  "save_visual_candidate",
  "discard_visual_candidate",
  "create_post",
  "draft_from_evidence",
  "draft_from_done",
]);

const DEFAULT_LABELS = {
  add_media: "Add media",
  alt_text: "Alt text",
  ai: "AI",
  ai_action_continue: "Continue",
  ai_action_expand: "Expand",
  ai_action_formula: "LaTeX",
  ai_action_outline: "Outline",
  ai_action_polish: "Polish",
  ai_action_shorten: "Shorten",
  ai_action_tone: "Tone",
  ai_action_translate: "Translate",
  ai_action_visual: "Visual",
  ai_candidate: "Candidate",
  ai_patch_accept: "Accept",
  ai_patch_accept_block_only: "Accept block only",
  ai_patch_assets: "Assets",
  ai_patch_candidate: "Patch candidate",
  ai_patch_generating: "Generating patch",
  ai_patch_markdown: "Markdown",
  ai_patch_meta: "Meta changes",
  ai_patch_panel: "AI patch candidates",
  ai_patch_regenerate: "Regenerate",
  ai_patch_reject: "Reject",
  ai_patch_target: "Target",
  ai_stream_cancel: "Cancel",
  ai_stream_cancelled: "Cancelled",
  ai_stream_failed: "AI generation failed",
  ai_slash_diagram: "Diagram",
  ai_slash_formula: "Formula",
  ai_slash_group: "AI actions",
  ai_slash_outline: "Outline",
  ai_slash_polish: "Polish current block",
  ai_slash_visual: "Visual",
  ai_slash_write_next: "AI write next paragraph",
  all_statuses: "All statuses",
  append_candidate: "Append",
  apply_candidate_meta: "Apply meta",
  archived: "archived",
  articles: "Articles",
  body: "Body",
  caption: "Caption",
  check: "Check",
  cover: "Cover",
  cover_prompt: "Cover prompt",
  create: "Create",
  create_post: "New",
  candidate_warnings: "Candidate warnings",
  close_left_panel: "Collapse articles",
  close_right_panel: "Collapse tools",
  date: "Date",
  discard_candidate: "Discard candidate",
  delete_media: "Delete media",
  delete_media_confirm: "Delete this media file? Remove body or cover references first.",
  delete_media_referenced: "This media is still referenced by the body or cover. Remove the reference before deleting.",
  convert_video: "Convert to compatible MP4",
  convert_video_confirm: "Convert this video to browser-compatible H.264 MP4? The original file will be kept and body references will move to the new file.",
  video_codec: "Codec",
  video_incompatible: "This video codec may not play in browsers. Convert it to H.264 MP4.",
  video_playback_failed: "The browser cannot play this video; the codec may be incompatible.",
  draft: "draft",
  draft_from_done: "Draft from Done",
  draft_from_evidence: "Draft from evidence",
  draft_from_title: "Draft from title",
  editor: "Editor",
  evidence_id: "Evidence ID",
  example: "Example",
  exit_focus: "Exit focus",
  filter_posts: "Filter",
  flowchart: "Flowchart",
  focus_mode: "Focus",
  fast_preview: "Fast preview",
  formula_block: "Formula",
  formula_block_help: "LaTeX display block",
  generate_candidate: "Generate candidate",
  generate_cover_image: "Generate cover candidate",
  generate_visual: "Generate visual asset",
  high_quality_preview: "High-quality preview",
  recent_visuals: "Recent generations",
  insert_candidate: "Insert",
  insert_at_cursor: "Recent cursor",
  insert_at_end: "End",
  insert_at_marker: "Marker",
  insert_replace: "Replace selection",
  insert_into_post: "Insert",
  insert_placement: "Insert position",
  layout: "Layout",
  left_panel: "Articles",
  media: "Media",
  media_library: "Media library",
  media_kind: "Media kind",
  meta: "Meta",
  missing_visual_key: "Missing VISUAL_API_KEY / DASHSCOPE_API_KEY / LLM_API_KEY.",
  close: "Close",
  load_full_preview: "Load full preview",
  new_blog: "New blog draft",
  no_issues: "No issues.",
  no_media: "No media.",
  no_reference_images: "No images in the media library.",
  no_source_videos: "No videos in the media library.",
  preview: "Preview",
  preview_empty: "No preview yet.",
  preview_unavailable: "No inline preview available.",
  post: "Post",
  public_preview: "Public preview",
  publish: "Publish",
  published: "published",
  raw_yaml: "Markdown source",
  related_evidence: "Related evidence",
  related_kanban: "Related kanban",
  right_panel: "Tools",
  run_check: "Run check",
  rerun_check: "Run check again",
  save: "Save",
  save_to_media: "Save to media",
  selected_media: "Selected media",
  selection_context: "Selection context",
  selection_context_empty: "No text selection; using the current block.",
  source_mode: "Source",
  source_video: "Source video",
  source_video_manual: "Manual source video URL/path",
  source_video_select: "Select source video",
  video_edit_source_help:
    "DashScope video edit requires MP4/MOV, 2-10 seconds, up to 100MB. Local media is uploaded to temporary DashScope OSS before generation.",
  status: "Status",
  summary: "Summary",
  tags: "Tags",
  title_label: "Title",
  tools: "Tools",
  upload_media: "Upload media",
  update_preview: "Update preview",
  using_key_from: "Using key from",
  validate: "Check",
  validation_errors: "Errors",
  validation_warnings: "Warnings",
  ai_loading_block: "AI placeholder",
  ai_loading_block_help: "Generated content",
  video_block: "Video",
  video_block_help: "Public-site video",
  video_edit: "Video edit",
  visual: "Visual",
  visual_block: "Visual",
  visual_block_help: "Image, video, or diagram candidate",
  visual_alt_help: "Used as Markdown image alt text when inserted; covers use the post title.",
  visual_caption_help: "Shown as a body caption or video title; not used for covers.",
  visual_custom: "Custom",
  visual_default: "Default",
  visual_prompt: "Visual prompt",
  visual_prompt_suggestions: "Prompt suggestions",
  visual_provider: "Visual generation",
  reference_image: "Reference image",
  reference_image_manual: "Manual reference image URL/path",
  reference_image_select: "Select reference image",
  view_full_preview: "Open large preview",
  visual_size: "Size",
  visual_size_custom: "Custom size",
  visual_size_default: "Default size",
  visual_size_help: "Use width*height, widthxheight, 1K, 2K, or 4K.",
  visual_style: "Style",
  visual_style_default: "Default style",
  visual_style_help: "Choose a preset or customize visual treatment.",
  quality_warnings: "Quality",
};

function markdownFromValue(value) {
  return typeof value === "string" ? value : "";
}

function asObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

function deepStableStringify(value) {
  if (Array.isArray(value)) {
    return `[${value.map((item) => deepStableStringify(item)).join(",")}]`;
  }
  if (value && typeof value === "object") {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${deepStableStringify(value[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

function label(labels, key, fallback = "") {
  const value = labels[key];
  return cleanText(value || fallback || DEFAULT_LABELS[key] || key);
}

function normalizeLayout(raw) {
  const source = asObject(raw);
  const activeTab = RIGHT_TABS.includes(cleanText(source.active_right_tab))
    ? cleanText(source.active_right_tab)
    : "Meta";
  const next = {
    left_open: source.left_open !== false,
    right_open: source.right_open !== false,
    active_right_tab: activeTab,
    focus_mode: Boolean(source.focus_mode),
    preview_open: Boolean(source.preview_open),
  };
  if ("left_before_focus" in source) {
    next.left_before_focus = Boolean(source.left_before_focus);
  }
  if ("right_before_focus" in source) {
    next.right_before_focus = Boolean(source.right_before_focus);
  }
  return next;
}

function readStoredLayout(storageKey, fallback) {
  if (!storageKey || typeof window === "undefined") {
    return fallback;
  }
  try {
    const stored = window.localStorage.getItem(storageKey);
    if (!stored) {
      return fallback;
    }
    return normalizeLayout({ ...fallback, ...JSON.parse(stored) });
  } catch (_err) {
    return fallback;
  }
}

function persistLayout(storageKey, state) {
  if (!storageKey || typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(storageKey, JSON.stringify(state));
  } catch (_err) {
    // localStorage can be unavailable in private browsing or embedded contexts.
  }
}

function normalizeMeta(raw) {
  const meta = { ...asObject(raw) };
  for (const key of ["title", "date", "status", "summary", "cover"]) {
    if (meta[key] === null || meta[key] === undefined) {
      meta[key] = "";
    }
  }
  for (const key of ["tags", "related_evidence", "related_kanban"]) {
    if (!Array.isArray(meta[key])) {
      meta[key] = listFromCsv(meta[key]);
    } else {
      meta[key] = meta[key].map((item) => cleanText(item).trim()).filter(Boolean);
    }
  }
  return meta;
}

function csvFromValue(value) {
  return Array.isArray(value) ? value.join(", ") : cleanText(value);
}

function listFromCsv(value) {
  return cleanText(value)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function postTitle(post) {
  return cleanText(post.title || post.slug || "Untitled");
}

function postSlug(post) {
  return cleanText(post.slug || post.id || "");
}

function mediaPath(item) {
  return cleanText(
    item.relative_path || item.path || item.url || item.src || item.name || "",
  );
}

function mediaSnippet(item) {
  const visualSnippet = generatedVisualSnippet(item);
  if (visualSnippet) {
    return visualSnippet;
  }
  const provided = cleanText(item.snippet || "");
  if (provided.trim()) {
    return provided;
  }
  const path = mediaPath(item);
  const kind = cleanText(item.kind || item.type || "");
  const alt = cleanText(item.alt || item.alt_text || item.title || "");
  const caption = cleanText(item.caption || "");
  if (!path) {
    return "";
  }
  if (kind === "video" || /\.(mp4|mov|webm|m4v)$/i.test(path)) {
    return `::video[${caption || alt}](${path})`;
  }
  const image = `![${alt}](${path})`;
  return caption ? `${image}\n\n_${caption}_` : image;
}

function mediaKind(item) {
  const path = mediaPath(item);
  const kind = cleanText(item.kind || item.type || "");
  if (kind) {
    return kind;
  }
  return /\.(mp4|mov|webm|m4v)$/i.test(path) ? "video" : "image";
}

function basename(value) {
  const clean = cleanText(value).replace(/\\/gu, "/").replace(/\/+$/u, "");
  return clean.split("/").filter(Boolean).pop() || clean;
}

function mediaOptionLabel(item, labels) {
  const path = mediaPath(item);
  const name = cleanText(item.name || item.title || basename(path) || label(labels, "media"));
  const details = [
    mediaKind(item),
    item.size_kb !== undefined ? `${item.size_kb} KB` : "",
  ].filter(Boolean);
  return details.length ? `${name} (${details.join(" / ")})` : name;
}

function selectableMediaOptions(items, kind, labels) {
  const byPath = new Map();
  for (const item of asArray(items).map(asObject)) {
    if (item.unsaved === true) {
      continue;
    }
    const path = mediaPath(item);
    if (!path || mediaKind(item) !== kind) {
      continue;
    }
    const key = mediaLookupKey(path);
    if (!key || byPath.has(key)) {
      continue;
    }
    byPath.set(key, {
      path,
      label: mediaOptionLabel(item, labels),
    });
  }
  return Array.from(byPath.values());
}

const VISUAL_KIND_TO_ASSET_TYPE = {
  cover: "image",
  flowchart: "diagram",
  example: "image",
  video_edit: "video",
};

function normalizeVisualKind(value) {
  const clean = cleanText(value).trim().toLowerCase();
  return Object.prototype.hasOwnProperty.call(VISUAL_KIND_TO_ASSET_TYPE, clean)
    ? clean
    : "";
}

function normalizeVisualAssetType(value, visualKind = "") {
  const clean = cleanText(value).trim().toLowerCase();
  const kind = normalizeVisualKind(visualKind || clean);
  if (kind) {
    return VISUAL_KIND_TO_ASSET_TYPE[kind];
  }
  return ["image", "video", "diagram"].includes(clean) ? clean : "image";
}

function visualBlockMarkdownComment(props) {
  const json = JSON.stringify(props).replace(/--/gu, "- -");
  return `<!-- nblane:visual_block ${json} -->`;
}

function generatedVisualSnippet(item) {
  const path = mediaPath(item);
  if (!path) {
    return "";
  }
  const rawVisualKind = item.visual_kind || item.visualKind || item.asset_type;
  const visualKind = normalizeVisualKind(rawVisualKind);
  const itemKind = mediaKind(item);
  const assetType = normalizeVisualAssetType(
    item.asset_type || itemKind,
    visualKind,
  );
  if (!visualKind && assetType !== "diagram" && item.ai_generated !== true) {
    return "";
  }
  return visualBlockMarkdownComment({
    asset_type: assetType,
    visual_kind: visualKind,
    src: path,
    prompt: cleanText(item.prompt),
    caption: cleanText(item.caption),
    alt: cleanText(item.alt || item.alt_text || item.title || ""),
    status: cleanText(item.status || "accepted"),
    ai_generated: item.ai_generated === true || item.generated === true,
    ai_source_id: cleanText(item.ai_source_id),
    ai_model: cleanText(item.ai_model || item.model),
    accepted: item.accepted !== false,
    evidence_id: cleanText(item.evidence_id),
  });
}

function mediaVideoCodecLabel(item, labels) {
  const codec = cleanText(item.video_codec || "");
  const tag = cleanText(item.video_codec_tag || "");
  if (!codec && !tag) {
    return "";
  }
  const suffix = codec && tag && codec !== tag ? `${codec} / ${tag}` : codec || tag;
  return `${label(labels, "video_codec")}: ${suffix}`;
}

function mediaVideoWarning(item, labels) {
  if (item.video_browser_compatible !== false) {
    return "";
  }
  const codec = cleanText(item.video_codec || item.video_codec_tag || "");
  return codec
    ? `${label(labels, "video_incompatible")} (${codec})`
    : label(labels, "video_incompatible");
}

function mediaPreviewSrc(item) {
  return cleanText(item.preview_src || item.preview || item.thumbnail || "");
}

function mediaFullPreviewSrc(item) {
  return cleanText(item.full_preview_src || item.full_preview || "");
}

function mediaDisplaySrc(item) {
  return mediaFullPreviewSrc(item) || mediaPreviewSrc(item);
}

function mediaLookupKey(value) {
  return cleanText(value).trim().replace(/^\/+/u, "");
}

function isAbsoluteAssetUrl(value) {
  return /^([a-z][a-z0-9+.-]*:|\/\/)/iu.test(cleanText(value).trim());
}

function buildMediaPreviewMap(items) {
  const map = new Map();
  for (const item of asArray(items).map(asObject)) {
    const path = mediaPath(item);
    const displaySrc = mediaDisplaySrc(item);
    if (!path || !displaySrc) {
      continue;
    }
    map.set(path, displaySrc);
    map.set(mediaLookupKey(path), displaySrc);
  }
  return map;
}

function resolveMediaPreviewUrl(value, mediaPreviewMap) {
  const src = cleanText(value).trim();
  if (!src || isAbsoluteAssetUrl(src)) {
    return src;
  }
  return mediaPreviewMap.get(src) || mediaPreviewMap.get(mediaLookupKey(src)) || src;
}

function visualItemKey(item, index = 0) {
  return [
    cleanText(item.id || ""),
    mediaPath(item),
    cleanText(item.name || ""),
    String(index),
  ]
    .filter(Boolean)
    .join("::");
}

function optionPairs(options) {
  return asArray(options)
    .map((option) => {
      if (option && typeof option === "object" && !Array.isArray(option)) {
        const labelText = cleanText(option.label || option.value || "").trim();
        const valueText =
          option.value === undefined ? labelText : cleanText(option.value).trim();
        return labelText ? { label: labelText, value: valueText } : null;
      }
      const text = cleanText(option).trim();
      return text ? { label: text, value: text } : null;
    })
    .filter(Boolean);
}

function candidateId(candidate, index) {
  return cleanText(candidate.id || candidate.key || candidate.slug || `candidate-${index}`);
}

function candidateBody(candidate) {
  return cleanText(
    candidate.body ||
      candidate.markdown ||
      candidate.content ||
      candidate.text ||
      candidate.snippet ||
      "",
  );
}

function candidateMeta(candidate) {
  const direct = asObject(candidate.meta);
  const meta = { ...direct };
  for (const key of [
    "title",
    "summary",
    "cover",
    "cover_prompt",
    "tags",
    "related_evidence",
    "related_kanban",
  ]) {
    if (candidate[key] !== undefined && meta[key] === undefined) {
      meta[key] = candidate[key];
    }
  }
  for (const key of ["tags", "related_evidence", "related_kanban"]) {
    if (meta[key] !== undefined) {
      meta[key] = Array.isArray(meta[key])
        ? meta[key].map((item) => cleanText(item).trim()).filter(Boolean)
        : listFromCsv(meta[key]);
    }
  }
  return meta;
}

function aiPatchId(patch, index = 0) {
  const data = asObject(patch);
  return cleanText(
    data.patch_id ||
      data.id ||
      asObject(data.provenance).source_event_id ||
      `ai-patch-${index}`,
  );
}

function normalizeAIPatch(value) {
  const patch = asObject(value);
  const operation = cleanText(patch.operation).trim();
  if (!operation) {
    return null;
  }
  return {
    patch_id: cleanText(patch.patch_id || patch.id || `ai-${Date.now()}`),
    operation,
    target: asObject(patch.target),
    meta_patch: asObject(patch.meta_patch),
    block_patches: asArray(patch.block_patches).map(asObject),
    markdown_fallback: cleanText(patch.markdown_fallback),
    assets: asArray(patch.assets).map(asObject),
    warnings: asArray(patch.warnings).map(cleanText).filter(Boolean),
    citations: asArray(patch.citations).map(asObject),
    provenance: asObject(patch.provenance),
  };
}

function makeAIStreamId(documentId, operation) {
  const random =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `${cleanText(documentId || "doc")}:ai:${cleanText(operation || "write")}:${random}`;
}

function aiLoadingMode(operation) {
  const clean = cleanText(operation).toLowerCase();
  if (clean === "formula") {
    return "formula";
  }
  if (clean === "visual") {
    return "visual";
  }
  return clean === "continue" ? "write" : "rewrite";
}

function patchDefaultPlacement(patch) {
  const operation = cleanText(patch?.operation).toLowerCase();
  const blockPatches = asArray(patch?.block_patches).map(asObject);
  const firstOp = cleanText(blockPatches[0]?.op).toLowerCase();
  if (
    firstOp === "replace" ||
    ["polish", "rewrite", "shorten", "expand", "translate", "tone", "formula"].includes(
      operation,
    )
  ) {
    return "replace";
  }
  return "cursor";
}

function normalizeInsertPlacement(value) {
  const placement = cleanText(value || "cursor");
  return ["cursor", "marker", "append", "replace"].includes(placement)
    ? placement
    : "cursor";
}

function insertMarkdownText(markdown, snippet, placement = "cursor") {
  const cleanSnippet = cleanText(snippet).trim();
  if (!cleanSnippet) {
    return markdown;
  }
  const source = cleanText(markdown);
  if (normalizeInsertPlacement(placement) === "marker" && source.includes(INSERT_MARKER)) {
    return source.replace(INSERT_MARKER, `${cleanSnippet}\n\n${INSERT_MARKER}`);
  }
  const base = source.trimEnd();
  if (!base) {
    return `${cleanSnippet}\n`;
  }
  return `${base}\n\n${cleanSnippet}\n`;
}

function insertMarkdownAtTextSelection(markdown, snippet, selection) {
  const cleanSnippet = cleanText(snippet).trim();
  if (!cleanSnippet) {
    return markdown;
  }
  const source = cleanText(markdown);
  const length = source.length;
  const rawStart = Number(selection?.start);
  const rawEnd = Number(selection?.end);
  const start = Number.isFinite(rawStart)
    ? Math.max(0, Math.min(length, rawStart))
    : length;
  const end = Number.isFinite(rawEnd)
    ? Math.max(start, Math.min(length, rawEnd))
    : start;
  const before = source.slice(0, start).replace(/[ \t]*$/u, "");
  const after = source.slice(end).replace(/^[ \t]*/u, "");
  const prefix = before ? `${before}\n\n` : "";
  const suffix = after ? `\n\n${after}` : "\n";
  return `${prefix}${cleanSnippet}${suffix}`;
}

function findBlockById(blocks, blockId) {
  const targetId = cleanText(blockId);
  if (!targetId) {
    return null;
  }
  for (const block of asArray(blocks)) {
    if (cleanText(block?.id) === targetId) {
      return block;
    }
    const child = findBlockById(block?.children, targetId);
    if (child) {
      return child;
    }
  }
  return null;
}

function truncateContextText(value, limit = 900) {
  const clean = cleanText(value).replace(/\s+/gu, " ").trim();
  return clean.length > limit ? `${clean.slice(0, limit)}...` : clean;
}

function inlineContentText(content) {
  if (typeof content === "string") {
    return content;
  }
  if (Array.isArray(content)) {
    return content.map((item) => inlineContentText(item)).filter(Boolean).join("");
  }
  if (!content || typeof content !== "object") {
    return "";
  }
  if (typeof content.text === "string") {
    return content.text;
  }
  if (content.content !== undefined) {
    return inlineContentText(content.content);
  }
  if (content.children !== undefined) {
    return inlineContentText(content.children);
  }
  return "";
}

function blockContextText(block) {
  if (!block) {
    return "";
  }
  const parts = [
    inlineContentText(block.content),
    ...asArray(block.children).map((child) => blockContextText(child)),
  ].filter(Boolean);
  return parts.join("\n").trim();
}

function flattenBlocks(blocks, output = []) {
  for (const block of asArray(blocks)) {
    output.push(block);
    flattenBlocks(block?.children, output);
  }
  return output;
}

function blockContextSummary(block) {
  return {
    block_id: cleanText(block?.id),
    type: cleanText(block?.type),
    text: truncateContextText(blockContextText(block), 420),
  };
}

function browserSelectionText() {
  try {
    const selection = window.getSelection?.();
    return selection && !selection.isCollapsed ? cleanText(selection.toString()).trim() : "";
  } catch (_err) {
    return "";
  }
}

function buildSourceSelectionContext(markdown, selection) {
  const source = cleanText(markdown);
  const length = source.length;
  const rawStart = Number(selection?.start);
  const rawEnd = Number(selection?.end);
  const start = Number.isFinite(rawStart)
    ? Math.max(0, Math.min(length, rawStart))
    : length;
  const end = Number.isFinite(rawEnd)
    ? Math.max(start, Math.min(length, rawEnd))
    : start;
  const contextStart = Math.max(0, start - 420);
  const contextEnd = Math.min(length, end + 420);
  return {
    block_id: "source",
    selection_text: source.slice(start, end),
    range: { start, end },
    cursor_block_id: "source",
    surrounding_blocks: [
      {
        block_id: "source",
        type: "markdown",
        text: truncateContextText(source.slice(contextStart, contextEnd), 900),
      },
    ],
  };
}

function buildEditorSelectionContext(editor, rememberedBlockId = "") {
  let cursorBlock = null;
  try {
    cursorBlock = editor.getTextCursorPosition()?.block || null;
  } catch (_err) {
    cursorBlock = null;
  }

  let selection = null;
  try {
    selection = editor.getSelection?.() || null;
  } catch (_err) {
    selection = null;
  }

  let cutSelection = null;
  if (selection) {
    try {
      cutSelection = editor.getSelectionCutBlocks?.() || null;
    } catch (_err) {
      cutSelection = null;
    }
  }

  const selectedBlocks = asArray(selection?.blocks);
  const cutBlocks = asArray(cutSelection?.blocks);
  const flatBlocks = flattenBlocks(editor.document);
  const rememberedBlock = findBlockById(editor.document, rememberedBlockId);
  const activeBlock = selectedBlocks[0] || cursorBlock || rememberedBlock || null;
  const activeBlockId = cleanText(activeBlock?.id || cursorBlock?.id || rememberedBlockId);
  const activeIndex = flatBlocks.findIndex((block) => cleanText(block?.id) === activeBlockId);
  const contextBlocks =
    activeIndex >= 0
      ? flatBlocks.slice(Math.max(0, activeIndex - 2), activeIndex + 3)
      : activeBlock
        ? [activeBlock]
        : [];
  const selectionText =
    browserSelectionText() ||
    (cutBlocks.length ? cutBlocks : selectedBlocks).map(blockContextText).join("\n\n").trim();
  const blockIds = (selectedBlocks.length ? selectedBlocks : activeBlock ? [activeBlock] : [])
    .map((block) => cleanText(block?.id))
    .filter(Boolean);

  if (!activeBlockId && !blockIds.length && !selectionText) {
    return null;
  }

  return {
    block_id: blockIds[0] || activeBlockId,
    selection_text: selectionText,
    range: selection
      ? {
          block_ids: blockIds,
          start_pos: cutSelection?._meta?.startPos ?? null,
          end_pos: cutSelection?._meta?.endPos ?? null,
          block_cut_at_start: cutSelection?.blockCutAtStart || null,
          block_cut_at_end: cutSelection?.blockCutAtEnd || null,
        }
      : null,
    cursor_block_id: cleanText(cursorBlock?.id || rememberedBlockId),
    surrounding_blocks: contextBlocks.map(blockContextSummary),
  };
}

function statusClass(status) {
  const value = cleanText(status || "draft").toLowerCase();
  if (value === "published") {
    return "is-published";
  }
  if (value === "archived") {
    return "is-archived";
  }
  return "is-draft";
}

function useFrameHeight(deps, minimumHeight) {
  const lastHeightRef = useRef(0);
  useEffect(() => {
    let frame = null;
    const observed = new WeakSet();
    const measuredSelectors = [
      ".nb-editor-shell",
      ".nb-shell",
      ".nb-workspace",
      ".nb-center-panel",
      ".nb-editor-area",
      ".nb-preview-panel",
      ".nb-left-panel",
      ".nb-right-panel",
    ];
    const measuredElements = () =>
      [...document.querySelectorAll(measuredSelectors.join(","))].filter(Boolean);
    const elementExtent = (element) => {
      const rect = element.getBoundingClientRect();
      const top = rect.top + (window.scrollY || window.pageYOffset || 0);
      return (
        top +
        Math.max(
          element.scrollHeight || 0,
          element.offsetHeight || 0,
          rect.height || 0,
        )
      );
    };
    const measure = () => {
      const nextHeight = Math.ceil(
        Math.max(
          minimumHeight,
          ...measuredElements().map((element) => elementExtent(element)),
        ) + 18,
      );
      if (nextHeight === lastHeightRef.current) {
        return;
      }
      lastHeightRef.current = nextHeight;
      Streamlit.setFrameHeight(nextHeight);
    };
    const schedule = () => {
      if (frame !== null) {
        window.cancelAnimationFrame(frame);
      }
      frame = window.requestAnimationFrame(() => {
        frame = null;
        measure();
      });
    };
    const timers = [
      window.setTimeout(schedule, 0),
      window.setTimeout(schedule, 120),
      window.setTimeout(schedule, 480),
    ];
    const observer =
      typeof ResizeObserver === "undefined"
        ? null
        : new ResizeObserver(schedule);
    const observeMeasuredElements = () => {
      if (!observer) {
        return;
      }
      for (const element of measuredElements()) {
        if (!observed.has(element)) {
          observer.observe(element);
          observed.add(element);
        }
      }
    };
    observeMeasuredElements();
    const mutationObserver =
      typeof MutationObserver !== "undefined"
        ? new MutationObserver(() => {
            observeMeasuredElements();
            schedule();
          })
        : null;
    const root = document.getElementById("root");
    if (root) {
      mutationObserver?.observe(root, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["class", "style"],
      });
    }
    window.addEventListener("resize", schedule);
    document.addEventListener("load", schedule, true);
    document.addEventListener("loadedmetadata", schedule, true);
    return () => {
      if (frame !== null) {
        window.cancelAnimationFrame(frame);
      }
      for (const timer of timers) {
        window.clearTimeout(timer);
      }
      observer?.disconnect();
      mutationObserver?.disconnect();
      window.removeEventListener("resize", schedule);
      document.removeEventListener("load", schedule, true);
      document.removeEventListener("loadedmetadata", schedule, true);
    };
  }, deps);
}

function waitForInputFlush() {
  return new Promise((resolve) => {
    window.setTimeout(resolve, 0);
  });
}

function floatingPreviewMetrics() {
  const fallbackWidth =
    typeof window === "undefined" ? 960 : Math.max(320, window.innerWidth - 32);
  const fallbackHeight =
    typeof window === "undefined" ? 640 : Math.max(320, window.innerHeight - 32);
  const fallback = {
    left: "50%",
    top: "50%",
    maxWidth: `${Math.min(1180, fallbackWidth)}px`,
    maxHeight: `${fallbackHeight}px`,
  };
  if (typeof window === "undefined") {
    return fallback;
  }
  try {
    const frame = window.frameElement;
    const parentWindow =
      window.parent && window.parent !== window ? window.parent : null;
    if (!frame || !parentWindow) {
      return fallback;
    }
    const rect = frame.getBoundingClientRect();
    const parentWidth = parentWindow.innerWidth || window.innerWidth;
    const parentHeight = parentWindow.innerHeight || window.innerHeight;
    const visibleLeft = Math.max(0, rect.left);
    const visibleRight = Math.min(parentWidth, rect.right);
    const visibleTop = Math.max(0, rect.top);
    const visibleBottom = Math.min(parentHeight, rect.bottom);
    const visibleWidth = visibleRight - visibleLeft;
    const visibleHeight = visibleBottom - visibleTop;
    if (visibleWidth <= 0 || visibleHeight <= 0) {
      return fallback;
    }
    return {
      left: `${visibleLeft + visibleWidth / 2 - rect.left}px`,
      top: `${visibleTop + visibleHeight / 2 - rect.top}px`,
      maxWidth: `${Math.max(320, Math.min(1180, visibleWidth - 32))}px`,
      maxHeight: `${Math.max(320, visibleHeight - 32)}px`,
    };
  } catch (_err) {
    return fallback;
  }
}

function parentWindowForFloatingOverlay() {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    return window.parent && window.parent !== window ? window.parent : null;
  } catch (_err) {
    return null;
  }
}

function useFloatingPreviewStyle(active) {
  const [metrics, setMetrics] = useState(() => floatingPreviewMetrics());
  useEffect(() => {
    if (!active) {
      return undefined;
    }
    let frame = null;
    const update = () => setMetrics(floatingPreviewMetrics());
    const schedule = () => {
      if (frame !== null) {
        window.cancelAnimationFrame(frame);
      }
      frame = window.requestAnimationFrame(() => {
        frame = null;
        update();
      });
    };
    const parentWindow = parentWindowForFloatingOverlay();
    const timers = [
      window.setTimeout(schedule, 0),
      window.setTimeout(schedule, 120),
      window.setInterval(schedule, 300),
    ];
    window.addEventListener("resize", schedule);
    let parentListening = false;
    try {
      parentWindow?.addEventListener("resize", schedule);
      parentWindow?.addEventListener("scroll", schedule, true);
      parentListening = Boolean(parentWindow);
    } catch (_err) {
      parentListening = false;
    }
    return () => {
      if (frame !== null) {
        window.cancelAnimationFrame(frame);
      }
      window.clearTimeout(timers[0]);
      window.clearTimeout(timers[1]);
      window.clearInterval(timers[2]);
      window.removeEventListener("resize", schedule);
      if (parentListening) {
        try {
          parentWindow?.removeEventListener("resize", schedule);
          parentWindow?.removeEventListener("scroll", schedule, true);
        } catch (_err) {
          // The parent window may become unavailable while Streamlit reruns.
        }
      }
    };
  }, [active]);
  return {
    "--nb-floating-preview-left": metrics.left,
    "--nb-floating-preview-top": metrics.top,
    "--nb-floating-preview-max-width": metrics.maxWidth,
    "--nb-floating-preview-max-height": metrics.maxHeight,
  };
}

function BlogSlashMenu({ editor, labels, onAIAction = null }) {
  const getItems = useCallback(
    async (query) =>
      filterSuggestionItems(
        [
          ...(onAIAction ? getAISlashMenuItems({ labels, onAction: onAIAction }) : []),
          ...getDefaultReactSlashMenuItems(editor),
          ...getBlogSlashMenuItems(editor, labels),
        ],
        query,
      ),
    [editor, labels, onAIAction],
  );
  return <SuggestionMenuController triggerCharacter="/" getItems={getItems} />;
}

function LegacyMarkdownEditor(props) {
  const args = props.args || {};
  const labels = { ...DEFAULT_LABELS, ...asObject(args.ui_labels) };
  const documentId = String(args.document_id || "blog");
  const initialMarkdown = markdownFromValue(args.initial_markdown);
  const height = Number(args.height || 560);
  const editable = args.editable !== false;
  const mathSafe = args.math_safe === true;
  const sourceMode = args.source_mode === true || (mathSafe && containsDisplayMathBlock(initialMarkdown));
  const editorSourceMode = sourceMode;
  const editor = useCreateBlockNote({ schema: blogSchema });
  const [sourceMarkdown, setSourceMarkdown] = useState(initialMarkdown);
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);
  const latestMarkdownRef = useRef(initialMarkdown);
  const loadedDocumentRef = useRef("");
  const loadedInitialMarkdownRef = useRef(null);
  const loadedSourceModeRef = useRef(null);
  const sendTimerRef = useRef(null);
  const sourceTextareaRef = useRef(null);
  const sourceSelectionRef = useRef({
    start: (initialMarkdown || "").length,
    end: (initialMarkdown || "").length,
  });
  const lastCursorBlockIdRef = useRef("");

  useFrameHeight([height, error, ready, editorSourceMode], height + 34);

  useEffect(() => {
    let cancelled = false;
    async function loadMarkdown() {
      if (
        loadedDocumentRef.current === documentId &&
        loadedInitialMarkdownRef.current === initialMarkdown &&
        loadedSourceModeRef.current === editorSourceMode
      ) {
        return;
      }
      setReady(false);
      setError("");
      lastCursorBlockIdRef.current = "";
      sourceSelectionRef.current = {
        start: (initialMarkdown || "").length,
        end: (initialMarkdown || "").length,
      };
      if (editorSourceMode) {
        setSourceMarkdown(initialMarkdown || "");
        latestMarkdownRef.current = initialMarkdown || "";
        loadedDocumentRef.current = documentId;
        loadedInitialMarkdownRef.current = initialMarkdown;
        loadedSourceModeRef.current = editorSourceMode;
        Streamlit.setComponentValue({
          markdown: latestMarkdownRef.current,
          dirty: false,
          selected_block: buildSourceSelectionContext(
            latestMarkdownRef.current,
            sourceSelectionRef.current,
          ),
          insert_event: null,
        });
        setReady(true);
        Streamlit.setFrameHeight(height + 34);
        return;
      }
      try {
        const blocks = parseMarkdownToEditorBlocks(editor, initialMarkdown || "");
        if (cancelled) {
          return;
        }
        editor.replaceBlocks(editor.document, blocks);
        latestMarkdownRef.current = initialMarkdown || "";
        loadedDocumentRef.current = documentId;
        loadedInitialMarkdownRef.current = initialMarkdown;
        loadedSourceModeRef.current = editorSourceMode;
        Streamlit.setComponentValue({
          markdown: latestMarkdownRef.current,
          dirty: false,
          selected_block: buildEditorSelectionContext(
            editor,
            lastCursorBlockIdRef.current,
          ),
          insert_event: null,
        });
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) {
          setReady(true);
          Streamlit.setFrameHeight(height + 34);
        }
      }
    }
    loadMarkdown();
    return () => {
      cancelled = true;
    };
  }, [documentId, editor, height, initialMarkdown, editorSourceMode]);

  useEffect(() => {
    return () => {
      if (sendTimerRef.current !== null) {
        window.clearTimeout(sendTimerRef.current);
      }
    };
  }, []);

  function rememberLegacySourceSelection() {
    const textarea = sourceTextareaRef.current;
    if (!textarea) {
      return sourceSelectionRef.current;
    }
    const next = {
      start: textarea.selectionStart,
      end: textarea.selectionEnd,
    };
    sourceSelectionRef.current = next;
    return next;
  }

  function rememberLegacyCursorBlock() {
    if (editorSourceMode) {
      return null;
    }
    try {
      const block = editor.getTextCursorPosition()?.block || null;
      if (block?.id) {
        lastCursorBlockIdRef.current = block.id;
      }
      return block;
    } catch (_err) {
      return null;
    }
  }

  function legacySelectionContext() {
    return editorSourceMode
      ? buildSourceSelectionContext(latestMarkdownRef.current, sourceSelectionRef.current)
      : buildEditorSelectionContext(editor, lastCursorBlockIdRef.current);
  }

  function sendLegacyValue(markdown, immediate = false) {
    latestMarkdownRef.current = markdown;
    const send = () => {
      Streamlit.setComponentValue({
        markdown,
        dirty: markdown !== (initialMarkdown || ""),
        selected_block: legacySelectionContext(),
        insert_event: null,
      });
    };
    if (sendTimerRef.current !== null) {
      window.clearTimeout(sendTimerRef.current);
    }
    if (immediate) {
      send();
      return;
    }
    sendTimerRef.current = window.setTimeout(send, 700);
  }

  async function syncMarkdown(immediate = false) {
    if (!ready) {
      return;
    }
    if (editorSourceMode) {
      sendLegacyValue(latestMarkdownRef.current, immediate);
      return;
    }
    try {
      const markdown = blocksToNblaneMarkdown(editor, editor.document);
      sendLegacyValue(markdown, immediate);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <main className="nb-editor-shell nb-legacy-shell" style={{ minHeight: `${height}px` }}>
      {error ? <div className="nb-editor-error">{error}</div> : null}
      {editorSourceMode ? (
        <textarea
          ref={sourceTextareaRef}
          className="nb-source-editor"
          value={sourceMarkdown}
          readOnly={!editable}
          onChange={(event) => {
            const next = event.target.value;
            setSourceMarkdown(next);
            sendLegacyValue(next, false);
          }}
          onSelect={rememberLegacySourceSelection}
          onKeyUp={rememberLegacySourceSelection}
          onMouseUp={rememberLegacySourceSelection}
          onBlur={() => {
            rememberLegacySourceSelection();
            sendLegacyValue(latestMarkdownRef.current, true);
          }}
          style={{ minHeight: `${height}px` }}
        />
      ) : (
        <BlockNoteView
          editor={editor}
          editable={editable}
          theme="light"
          slashMenu={false}
          onSelectionChange={rememberLegacyCursorBlock}
          onKeyUp={rememberLegacyCursorBlock}
          onMouseUp={rememberLegacyCursorBlock}
          onFocus={rememberLegacyCursorBlock}
          onChange={() => {
            rememberLegacyCursorBlock();
            syncMarkdown(false);
          }}
          onBlur={() => {
            rememberLegacyCursorBlock();
            syncMarkdown(true);
          }}
        >
          <BlogSlashMenu editor={editor} labels={labels} />
        </BlockNoteView>
      )}
    </main>
  );
}

function ShellEditor(props) {
  const args = props.args || {};
  const labels = { ...DEFAULT_LABELS, ...asObject(args.ui_labels) };
  const posts = asArray(args.posts).map(asObject);
  const mediaItems = asArray(args.media_items).map(asObject);
  const aiCandidates = asArray(args.ai_candidates).map(asObject);
  const validationState = asObject(args.validation_state);
  const visualConfig = asObject(args.visual_config);
  const visualResults = asArray(args.visual_results).map(asObject);
  const visualGuidance = asObject(args.visual_guidance);
  const operationNotice = asObject(args.operation_notice);
  const incomingAIPatch = useMemo(() => normalizeAIPatch(args.ai_patch), [args.ai_patch]);
  const incomingAIStream = useMemo(
    () => normalizeAIStream(args.ai_stream),
    [args.ai_stream],
  );
  const previewHtml = cleanText(args.preview_html);
  const initialStatusFilter = cleanText(args.status_filter || "all") || "all";
  const activeSlug = cleanText(args.active_slug || args.slug || args.document_id || "");
  const documentId = String(args.document_id || activeSlug || "blog");
  const initialMarkdown = markdownFromValue(args.initial_markdown);
  const height = Number(args.height || 720);
  const editable = args.editable !== false;
  const mathSafe = args.math_safe === true;
  const sourceMode = args.source_mode === true || (mathSafe && containsDisplayMathBlock(initialMarkdown));
  const layoutStorageKey = cleanText(
    args.layout_storage_key ||
      args.storage_key ||
      (documentId ? `public_blog_editor:${documentId}` : ""),
  );
  const mediaPreviewMapRef = useRef(new Map());
  mediaPreviewMapRef.current = buildMediaPreviewMap([
    ...mediaItems,
    ...visualResults,
  ]);
  const editor = useCreateBlockNote({
    schema: blogSchema,
    resolveFileUrl: (url) =>
      resolveMediaPreviewUrl(url, mediaPreviewMapRef.current),
  });
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [sourceMarkdown, setSourceMarkdown] = useState(initialMarkdown);
  const [dirty, setDirty] = useState(false);
  const [mobileView, setMobileView] = useState("Editor");
  const [newPostTitle, setNewPostTitle] = useState("");
  const [evidenceId, setEvidenceId] = useState("");
  const [statusFilter, setStatusFilter] = useState(initialStatusFilter);
  const [largePreview, setLargePreview] = useState({ source: "", key: "" });
  const [layout, setLayoutState] = useState(() =>
    readStoredLayout(layoutStorageKey, normalizeLayout(args.layout_state)),
  );
  const [draftMeta, setDraftMetaState] = useState(() =>
    normalizeMeta(args.active_post_meta),
  );
  const [selectedBlock, setSelectedBlockState] = useState(null);
  const [patchCandidates, setPatchCandidates] = useState([]);
  const [pendingAIAction, setPendingAIAction] = useState(null);

  const latestMarkdownRef = useRef(initialMarkdown);
  const loadedDocumentRef = useRef("");
  const loadedInitialMarkdownRef = useRef(null);
  const loadedSourceModeRef = useRef(null);
  const layoutRef = useRef(layout);
  const draftMetaRef = useRef(draftMeta);
  const initialMetaSignatureRef = useRef(deepStableStringify(draftMeta));
  const initialMarkdownRef = useRef(initialMarkdown);
  const eventCounterRef = useRef(0);
  const lastCursorBlockIdRef = useRef("");
  const selectedBlockRef = useRef(null);
  const sourceTextareaRef = useRef(null);
  const sourceSelectionRef = useRef({ start: 0, end: 0 });
  const editorSourceMode = sourceMode;

  const layoutSeed = deepStableStringify(args.layout_state || {});
  const metaSeed = deepStableStringify(args.active_post_meta || {});
  const visualSeed = deepStableStringify(args.visual_config || {});
  const visualResultsSeed = deepStableStringify(args.visual_results || []);
  const visualGuidanceSeed = deepStableStringify(args.visual_guidance || {});
  const operationNoticeSeed = deepStableStringify(args.operation_notice || {});
  const aiPatchSeed = deepStableStringify(args.ai_patch || {});
  const aiStreamSeed = deepStableStringify(args.ai_stream || {});
  const mediaPreviewRows = useMemo(
    () =>
      mediaItems.map((item, index) => ({
        item,
        key: visualItemKey(item, index),
      })),
    [mediaItems],
  );
  const visualPreviewRows = useMemo(
    () =>
      visualResults.map((item, index) => ({
        item,
        key: visualItemKey(item, index),
      })),
    [visualResults],
  );
  const largePreviewRow = useMemo(() => {
    const rows = largePreview.source === "visual" ? visualPreviewRows : mediaPreviewRows;
    return rows.find((row) => row.key === largePreview.key) || null;
  }, [largePreview.key, largePreview.source, mediaPreviewRows, visualPreviewRows]);

  useFrameHeight(
    [
      height,
      layout.left_open,
      layout.right_open,
      layout.active_right_tab,
      layout.focus_mode,
      layout.preview_open,
      mobileView,
      posts.length,
      mediaItems.length,
      aiCandidates.length,
      error,
      editorSourceMode,
      previewHtml.length,
      visualSeed,
      visualResultsSeed,
      visualGuidanceSeed,
      operationNoticeSeed,
      aiPatchSeed,
      aiStreamSeed,
      patchCandidates.length,
      pendingAIAction?.operation,
      pendingAIAction?.text,
    ],
    height + 72,
  );

  useEffect(() => {
    const nextLayout = readStoredLayout(
      layoutStorageKey,
      normalizeLayout(args.layout_state),
    );
    layoutRef.current = nextLayout;
    setLayoutState(nextLayout);
  }, [layoutSeed, layoutStorageKey]);

  useEffect(() => {
    const nextMeta = normalizeMeta(args.active_post_meta);
    draftMetaRef.current = nextMeta;
    initialMetaSignatureRef.current = deepStableStringify(nextMeta);
    initialMarkdownRef.current = initialMarkdown;
    setDraftMetaState(nextMeta);
    setDirty(false);
  }, [activeSlug, documentId, initialMarkdown, metaSeed]);

  useEffect(() => {
    setStatusFilter(initialStatusFilter);
  }, [initialStatusFilter]);

  useEffect(() => {
    if (largePreview.key && !largePreviewRow) {
      setLargePreview({ source: "", key: "" });
    }
  }, [largePreview.key, largePreviewRow]);

  useEffect(() => {
    if (layout.focus_mode) {
      setMobileView("Editor");
    }
  }, [layout.focus_mode]);

  useEffect(() => {
    let cancelled = false;
    async function loadMarkdown() {
      if (
        loadedDocumentRef.current === documentId &&
        loadedInitialMarkdownRef.current === initialMarkdown &&
        loadedSourceModeRef.current === editorSourceMode
      ) {
        return;
      }
      setReady(false);
      setError("");
      lastCursorBlockIdRef.current = "";
      selectedBlockRef.current = null;
      setSelectedBlockState(null);
      sourceSelectionRef.current = {
        start: (initialMarkdown || "").length,
        end: (initialMarkdown || "").length,
      };
      if (editorSourceMode) {
        setSourceMarkdown(initialMarkdown || "");
        latestMarkdownRef.current = initialMarkdown || "";
        loadedDocumentRef.current = documentId;
        loadedInitialMarkdownRef.current = initialMarkdown;
        loadedSourceModeRef.current = editorSourceMode;
        setReady(true);
        return;
      }
      try {
        const blocks = parseMarkdownToEditorBlocks(editor, initialMarkdown || "");
        if (cancelled) {
          return;
        }
        editor.replaceBlocks(editor.document, blocks);
        latestMarkdownRef.current = initialMarkdown || "";
        loadedDocumentRef.current = documentId;
        loadedInitialMarkdownRef.current = initialMarkdown;
        loadedSourceModeRef.current = editorSourceMode;
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) {
          setReady(true);
        }
      }
    }
    loadMarkdown();
    return () => {
      cancelled = true;
    };
  }, [documentId, editor, initialMarkdown, editorSourceMode]);

  const computeDirty = useCallback((markdown, meta = draftMetaRef.current) => {
    return (
      markdown !== (initialMarkdownRef.current || "") ||
      deepStableStringify(meta) !== initialMetaSignatureRef.current
    );
  }, []);

  const setDraftMeta = useCallback(
    (patchOrUpdater) => {
      const current = draftMetaRef.current;
      const next =
        typeof patchOrUpdater === "function"
          ? normalizeMeta(patchOrUpdater(current))
          : normalizeMeta({ ...current, ...patchOrUpdater });
      draftMetaRef.current = next;
      setDraftMetaState(next);
      setDirty(computeDirty(latestMarkdownRef.current, next));
      return next;
    },
    [computeDirty],
  );

  const getCurrentMarkdown = useCallback(async () => {
    if (sourceMode) {
      return latestMarkdownRef.current;
    }
    try {
      const markdown = blocksToNblaneMarkdown(editor, editor.document);
      latestMarkdownRef.current = markdown;
      return markdown;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      return latestMarkdownRef.current;
    }
  }, [editor, sourceMode]);

  const rememberCursorBlock = useCallback(() => {
    if (editorSourceMode) {
      return null;
    }
    try {
      const block = editor.getTextCursorPosition()?.block || null;
      if (block?.id) {
        lastCursorBlockIdRef.current = block.id;
      }
      return block;
    } catch (_err) {
      // BlockNote can throw after focus leaves the editor; keep the previous block id.
      return null;
    }
  }, [editor, editorSourceMode]);

  const rememberSourceSelection = useCallback(() => {
    const textarea = sourceTextareaRef.current;
    if (!textarea) {
      return sourceSelectionRef.current;
    }
    const next = {
      start: textarea.selectionStart,
      end: textarea.selectionEnd,
    };
    sourceSelectionRef.current = next;
    return next;
  }, []);

  const refreshSelectedBlock = useCallback(() => {
    const next = editorSourceMode
      ? buildSourceSelectionContext(latestMarkdownRef.current, sourceSelectionRef.current)
      : buildEditorSelectionContext(editor, lastCursorBlockIdRef.current);
    if (deepStableStringify(next) !== deepStableStringify(selectedBlockRef.current)) {
      selectedBlockRef.current = next;
      setSelectedBlockState(next);
    } else {
      selectedBlockRef.current = next;
    }
    return next;
  }, [editor, editorSourceMode]);

  const handleEditorSelectionUpdate = useCallback(() => {
    rememberCursorBlock();
    refreshSelectedBlock();
  }, [refreshSelectedBlock, rememberCursorBlock]);

  const nextEventId = useCallback(
    (action) => {
      eventCounterRef.current += 1;
      return `${documentId}:${action}:${Date.now()}:${eventCounterRef.current}`;
    },
    [documentId],
  );

  const applyLayoutLocal = useCallback(
    (updater) => {
      const next = normalizeLayout(
        typeof updater === "function" ? updater(layoutRef.current) : updater,
      );
      layoutRef.current = next;
      setLayoutState(next);
      persistLayout(layoutStorageKey, next);
      return next;
    },
    [layoutStorageKey],
  );

  useEffect(() => {
    if (!incomingAIPatch) {
      return;
    }
    const incomingId = aiPatchId(incomingAIPatch);
    setPatchCandidates((current) => {
      const withoutDuplicate = current.filter(
        (patch, index) => aiPatchId(patch, index) !== incomingId,
      );
      return [incomingAIPatch, ...withoutDuplicate].slice(0, 8);
    });
    setPendingAIAction(null);
    applyLayoutLocal((current) => ({
      ...current,
      right_open: true,
      active_right_tab: "AI",
      focus_mode: false,
    }));
    setMobileView("Tools");
  }, [applyLayoutLocal, incomingAIPatch]);

  const emitAction = useCallback(
    async (action, extraPayload = {}) => {
      if (!editable && WRITE_ACTIONS.has(action)) {
        return;
      }
      const selectionContext = selectedBlockRef.current || refreshSelectedBlock();
      if (document.activeElement instanceof HTMLElement) {
        document.activeElement.blur();
        await waitForInputFlush();
      }
      const markdown = await getCurrentMarkdown();
      const eventId = nextEventId(action);
      const payload = {
        slug: activeSlug,
        document_id: documentId,
        markdown,
        meta: draftMetaRef.current,
        layout_state: layoutRef.current,
        dirty: computeDirty(markdown, draftMetaRef.current),
        selected_block: selectionContext,
        ...extraPayload,
        event_id: eventId,
      };
      Streamlit.setComponentValue({
        action,
        event_id: eventId,
        payload,
        markdown,
        dirty: payload.dirty,
        layout_state: layoutRef.current,
        selected_block: selectionContext,
        insert_event:
          action === "insert_candidate" || action === "insert_media"
            ? extraPayload
            : null,
      });
    },
    [
      activeSlug,
      computeDirty,
      documentId,
      editable,
      getCurrentMarkdown,
      nextEventId,
      refreshSelectedBlock,
    ],
  );

  const syncMarkdown = useCallback(
    async () => {
      if (!ready || !editable) {
        return;
      }
      rememberCursorBlock();
      refreshSelectedBlock();
      const markdown = editorSourceMode
        ? latestMarkdownRef.current
        : await getCurrentMarkdown();
      const nextDirty = computeDirty(markdown, draftMetaRef.current);
      setDirty(nextDirty);
    },
    [
      computeDirty,
      editable,
      editorSourceMode,
      getCurrentMarkdown,
      refreshSelectedBlock,
      rememberCursorBlock,
      ready,
    ],
  );

  const replaceEditorMarkdown = useCallback(
    async (markdown) => {
      latestMarkdownRef.current = markdown;
      setDirty(computeDirty(markdown, draftMetaRef.current));
      if (editorSourceMode) {
        setSourceMarkdown(markdown);
        return markdown;
      }
      const blocks = parseMarkdownToEditorBlocks(editor, markdown || "");
      editor.replaceBlocks(editor.document, blocks);
      return markdown;
    },
    [computeDirty, editor, editorSourceMode],
  );

  const insertMarkdown = useCallback(
    async (snippet, placement = "cursor", options = {}) => {
      const insertPlacement = normalizeInsertPlacement(placement);
      const cleanSnippet = cleanText(snippet).trim();
      const targetContext = asObject(options.target || options.targetContext);
      if (!cleanSnippet) {
        return latestMarkdownRef.current;
      }
      const current = await getCurrentMarkdown();
      const rawDirective = isRawMarkdownDirective(cleanSnippet);
      if (editorSourceMode) {
        const targetRange = asObject(targetContext.range);
        const sourceSelection =
          Number.isFinite(Number(targetRange.start)) ||
          Number.isFinite(Number(targetRange.end))
            ? targetRange
            : sourceSelectionRef.current;
        const next =
          insertPlacement === "cursor" || insertPlacement === "replace"
            ? insertMarkdownAtTextSelection(
                current,
                cleanSnippet,
                sourceSelection,
              )
            : insertMarkdownText(current, cleanSnippet, insertPlacement);
        await replaceEditorMarkdown(next);
        return next;
      }
      if (rawDirective || insertPlacement === "marker" || insertPlacement === "append") {
        const next = insertMarkdownText(
          current,
          cleanSnippet,
          rawDirective && insertPlacement !== "marker" ? "append" : insertPlacement,
        );
        await replaceEditorMarkdown(next);
        return next;
      }
      if (insertPlacement === "replace") {
        const targetText = cleanText(targetContext.selection_text).trim();
        if (targetText && current.includes(targetText)) {
          const next = current.replace(targetText, cleanSnippet);
          await replaceEditorMarkdown(next);
          return next;
        }
      }
      try {
        const blocks = parseMarkdownToEditorBlocks(editor, cleanSnippet);
        let insertionReference = null;
        let insertionPlacement = "after";
        if (insertPlacement === "replace") {
          let replacementBlocks = [];
          const targetIds = asArray(targetContext.block_ids)
            .map((id) => cleanText(id).trim())
            .filter(Boolean);
          const targetBlockId = cleanText(
            targetContext.block_id || targetContext.cursor_block_id,
          ).trim();
          if (targetIds.length || targetBlockId) {
            replacementBlocks = (targetIds.length ? targetIds : [targetBlockId])
              .map((blockId) => findBlockById(editor.document, blockId))
              .filter(Boolean);
          } else {
            try {
              replacementBlocks = asArray(editor.getSelection()?.blocks);
            } catch (_err) {
              replacementBlocks = [];
            }
          }
          if (!replacementBlocks.length) {
            const rememberedTarget = cleanText(
              selectedBlockRef.current?.block_id || lastCursorBlockIdRef.current,
            );
            const targetBlock = findBlockById(editor.document, rememberedTarget);
            if (targetBlock) {
              replacementBlocks = [targetBlock];
            }
          }
          if (replacementBlocks.length) {
            const flatBlocks = flattenBlocks(editor.document);
            const replacementIds = new Set(
              replacementBlocks.map((block) => cleanText(block?.id)).filter(Boolean),
            );
            const firstIndex = flatBlocks.findIndex((block) =>
              replacementIds.has(cleanText(block?.id)),
            );
            let lastIndex = -1;
            if (firstIndex >= 0) {
              for (let index = flatBlocks.length - 1; index >= firstIndex; index -= 1) {
                if (replacementIds.has(cleanText(flatBlocks[index]?.id))) {
                  lastIndex = index;
                  break;
                }
              }
            }
            const previousBlock = firstIndex > 0 ? flatBlocks[firstIndex - 1] : null;
            const nextBlock =
              lastIndex >= 0 && lastIndex + 1 < flatBlocks.length
                ? flatBlocks[lastIndex + 1]
                : null;
            insertionReference = previousBlock || nextBlock;
            insertionPlacement = previousBlock ? "after" : "before";
            editor.removeBlocks(replacementBlocks);
            if (!insertionReference) {
              editor.replaceBlocks(editor.document, blocks);
              return await getCurrentMarkdown();
            }
          }
        }
        const referenceBlockId = cleanText(
          selectedBlockRef.current?.cursor_block_id ||
            selectedBlockRef.current?.block_id ||
            lastCursorBlockIdRef.current,
        );
        let referenceBlock = findBlockById(
          editor.document,
          referenceBlockId,
        );
        try {
          const cursorBlock = editor.getTextCursorPosition()?.block || null;
          if (cursorBlock?.id) {
            lastCursorBlockIdRef.current = cursorBlock.id;
          }
          referenceBlock = referenceBlock || cursorBlock;
        } catch (_err) {
          // Use the remembered block id or fall back below.
        }
        if (!referenceBlock) {
          referenceBlock = editor.document[editor.document.length - 1];
        }
        editor.insertBlocks(
          blocks,
          insertionReference || referenceBlock,
          insertionReference ? insertionPlacement : "after",
        );
        const next = await getCurrentMarkdown();
        if (next === current) {
          const fallback = insertMarkdownText(current, cleanSnippet, "append");
          await replaceEditorMarkdown(fallback);
          return fallback;
        }
        return next;
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setError(message);
        const next = insertMarkdownText(current, cleanSnippet, "append");
        await replaceEditorMarkdown(next);
        return next;
      }
    },
    [editor, editorSourceMode, getCurrentMarkdown, replaceEditorMarkdown],
  );

  const findAILoadingBlock = useCallback(
    (streamId) => {
      if (editorSourceMode) {
        return null;
      }
      const targetId = cleanText(streamId).trim();
      if (!targetId) {
        return null;
      }
      return (
        flattenBlocks(editor.document).find(
          (block) =>
            cleanText(block?.type) === "ai_loading_block" &&
            cleanText(block?.props?.ai_source_id).trim() === targetId,
        ) || null
      );
    },
    [editor, editorSourceMode],
  );

  const insertAILoadingBlock = useCallback(
    (streamId, operation, selectionContext = {}) => {
      if (editorSourceMode || !editable || findAILoadingBlock(streamId)) {
        return;
      }
      const targetContext = asObject(selectionContext);
      const referenceId = cleanText(
        targetContext.cursor_block_id ||
          targetContext.block_id ||
          lastCursorBlockIdRef.current,
      ).trim();
      let referenceBlock = findBlockById(editor.document, referenceId);
      try {
        const cursorBlock = editor.getTextCursorPosition()?.block || null;
        if (cursorBlock?.id) {
          lastCursorBlockIdRef.current = cursorBlock.id;
        }
        referenceBlock = referenceBlock || cursorBlock;
      } catch (_err) {
        // Use the remembered reference or fall back to the last document block.
      }
      referenceBlock = referenceBlock || editor.document[editor.document.length - 1];
      if (!referenceBlock) {
        return;
      }
      editor.insertBlocks(
        [
          {
            type: "ai_loading_block",
            props: {
              prompt: "",
              mode: aiLoadingMode(operation),
              status: "loading",
              ai_source_id: streamId,
            },
          },
        ],
        referenceBlock,
        "after",
      );
    },
    [editable, editor, editorSourceMode, findAILoadingBlock],
  );

  const updateAILoadingBlock = useCallback(
    (stream) => {
      const block = findAILoadingBlock(stream?.task_id);
      if (!block) {
        return;
      }
      const status =
        stream.status === "running" ? "loading" : stream.status === "done" ? "done" : "failed";
      const prompt = stream.status === "failed" ? stream.error : stream.text;
      editor.updateBlock(block, {
        props: {
          ...block.props,
          prompt: cleanText(prompt),
          status,
        },
      });
    },
    [editor, findAILoadingBlock],
  );

  const removeAILoadingBlock = useCallback(
    (streamId) => {
      const block = findAILoadingBlock(streamId);
      if (block) {
        editor.removeBlocks([block]);
      }
    },
    [editor, findAILoadingBlock],
  );

  const emitAIStreamControl = useCallback(
    (action, streamId) => {
      const cleanStreamId = cleanText(streamId).trim();
      if (!cleanStreamId) {
        return;
      }
      const selectionContext = selectedBlockRef.current || refreshSelectedBlock();
      const eventId = nextEventId(action);
      Streamlit.setComponentValue({
        action,
        event_id: eventId,
        payload: {
          slug: activeSlug,
          document_id: documentId,
          stream_id: cleanStreamId,
          layout_state: layoutRef.current,
          selected_block: selectionContext,
          event_id: eventId,
        },
        markdown: latestMarkdownRef.current,
        dirty,
        layout_state: layoutRef.current,
        selected_block: selectionContext,
        insert_event: null,
      });
    },
    [activeSlug, dirty, documentId, nextEventId, refreshSelectedBlock],
  );

  useAIStream({
    stream: incomingAIStream,
    poll: (streamId) => emitAIStreamControl("ai_stream_poll", streamId),
    onFlush: (stream) => {
      setPendingAIAction((current) => {
        const streamId = cleanText(stream.task_id).trim();
        if (!streamId) {
          return current;
        }
        if (stream.status !== "running" && cleanText(current?.stream_id) !== streamId) {
          return current;
        }
        return {
          ...(current || {}),
          operation: cleanText(stream.operation || current?.operation || "AI"),
          trigger: cleanText(current?.trigger || "stream"),
          started_at: current?.started_at || Date.now(),
          stream_id: streamId,
          status: stream.status,
          text: stream.text,
          error: stream.error,
        };
      });
      updateAILoadingBlock(stream);
    },
    onComplete: (stream) => {
      if (stream.status !== "running") {
        removeAILoadingBlock(stream.task_id);
        setPendingAIAction((current) =>
          cleanText(current?.stream_id).trim() === stream.task_id ? null : current,
        );
      }
    },
  });

  function toggleFocusMode() {
    setMobileView("Editor");
    applyLayoutLocal((current) => {
      if (current.focus_mode) {
        return {
          ...current,
          focus_mode: false,
          left_open:
            current.left_before_focus === undefined
              ? true
              : current.left_before_focus,
          right_open:
            current.right_before_focus === undefined
              ? true
              : current.right_before_focus,
        };
      }
      return {
        ...current,
        focus_mode: true,
        left_before_focus: Boolean(current.left_open),
        right_before_focus: Boolean(current.right_open),
      };
    });
  }

  function toggleRightTab(tab) {
    openRightTab(tab, true);
  }

  function openRightTab(tab, collapseCurrent = false) {
    let nextRightOpen = true;
    applyLayoutLocal((current) => {
      if (collapseCurrent && current.right_open && current.active_right_tab === tab) {
        nextRightOpen = false;
        return { ...current, right_open: false, focus_mode: false };
      }
      nextRightOpen = true;
      return {
        ...current,
        right_open: true,
        active_right_tab: tab,
        focus_mode: false,
      };
    });
    setMobileView(nextRightOpen ? "Tools" : "Editor");
  }

  function closeRightPanel() {
    applyLayoutLocal((current) => ({ ...current, right_open: false, focus_mode: false }));
    setMobileView("Editor");
  }

  function exitFocusLayout(current) {
    if (!current.focus_mode) {
      return current;
    }
    return {
      ...current,
      focus_mode: false,
      left_open:
        current.left_before_focus === undefined
          ? current.left_open
          : current.left_before_focus,
      right_open:
        current.right_before_focus === undefined
          ? current.right_open
          : current.right_before_focus,
    };
  }

  function switchMobileView(tab) {
    if (tab === "Preview") {
      requestPreview();
      return;
    }
    if (tab === "Articles") {
      applyLayoutLocal((current) => ({
        ...exitFocusLayout(current),
        left_open: true,
      }));
      setMobileView("Articles");
      return;
    }
    if (tab === "Tools") {
      applyLayoutLocal((current) => ({
        ...exitFocusLayout(current),
        right_open: true,
      }));
      setMobileView("Tools");
      return;
    }
    applyLayoutLocal((current) => exitFocusLayout(current));
    setMobileView("Editor");
  }

  function setPreviewOpen(open) {
    const next = normalizeLayout({
      ...layoutRef.current,
      preview_open: open,
      focus_mode: false,
    });
    layoutRef.current = next;
    setLayoutState(next);
    persistLayout(layoutStorageKey, next);
    return next;
  }

  function updateMetaText(key, value) {
    if (!editable) {
      return;
    }
    setDraftMeta({ [key]: value });
  }

  function updateMetaList(key, value) {
    if (!editable) {
      return;
    }
    setDraftMeta({ [key]: listFromCsv(value) });
  }

  async function handleInsertCandidate(candidate, index, placement = "cursor") {
    if (!editable) {
      return;
    }
    const body = candidateBody(candidate);
    const id = candidateId(candidate, index);
    const markdown = await insertMarkdown(body, placement);
    await emitAction("insert_candidate", {
      candidate_id: id,
      candidate,
      placement,
      markdown,
    });
  }

  async function handleInsertMedia(item, placement = "cursor") {
    if (!editable) {
      return;
    }
    const insertPlacement = normalizeInsertPlacement(placement);
    const snippet = mediaSnippet(item);
    const markdown = await insertMarkdown(snippet, insertPlacement);
    await emitAction("insert_media", {
      media: item,
      snippet,
      placement: insertPlacement,
      markdown,
    });
  }

  async function handleApplyCandidateMeta(candidate, index) {
    if (!editable) {
      return;
    }
    const metaPatch = candidateMeta(candidate);
    const nextMeta = setDraftMeta((current) => ({ ...current, ...metaPatch }));
    await emitAction("apply_candidate_meta", {
      candidate_id: candidateId(candidate, index),
      candidate,
      meta_patch: metaPatch,
      meta: nextMeta,
    });
  }

  async function handleAIInlineAction(request = {}) {
    if (!editable) {
      return;
    }
    const operation = cleanText(request.operation || "polish").trim() || "polish";
    const requestedSelection = asObject(request.selected_block);
    const selectionContext =
      cleanText(requestedSelection.block_id).trim() ||
      cleanText(requestedSelection.selection_text).trim() ||
      asArray(requestedSelection.block_ids).length
        ? requestedSelection
        : refreshSelectedBlock();
    const markdownBeforeAI = await getCurrentMarkdown();
    const streamId = cleanText(request.stream_id).trim() || makeAIStreamId(documentId, operation);
    insertAILoadingBlock(streamId, operation, selectionContext);
    setPendingAIAction({
      operation,
      trigger: cleanText(request.trigger || "inline"),
      started_at: Date.now(),
      stream_id: streamId,
      status: "running",
      text: "",
      error: "",
    });
    applyLayoutLocal((current) => ({
      ...current,
      right_open: true,
      active_right_tab: "AI",
      focus_mode: false,
    }));
    setMobileView("Tools");
    await emitAction("ai_inline_action", {
      operation,
      trigger: cleanText(request.trigger || "inline"),
      prompt: cleanText(request.prompt),
      context_window: cleanText(request.context_window || "selection"),
      visual_kind: cleanText(request.visual_kind),
      selected_block: selectionContext,
      stream_id: streamId,
      markdown: markdownBeforeAI,
      dirty: computeDirty(markdownBeforeAI, draftMetaRef.current),
    });
  }

  async function handleCancelAIStream() {
    const streamId = cleanText(
      pendingAIAction?.stream_id || incomingAIStream?.task_id || "",
    ).trim();
    if (!streamId) {
      setPendingAIAction(null);
      return;
    }
    removeAILoadingBlock(streamId);
    setPendingAIAction(null);
    emitAIStreamControl("cancel_ai_stream", streamId);
  }

  async function handleAcceptAIPatch(patch, options = {}) {
    if (!editable) {
      return;
    }
    const normalized = normalizeAIPatch(patch);
    if (!normalized) {
      return;
    }
    const id = aiPatchId(normalized);
    const blockOnly = options.blockOnly === true;
    const metaPatch = asObject(normalized.meta_patch);
    let nextMeta = draftMetaRef.current;
    if (!blockOnly && Object.keys(metaPatch).length) {
      nextMeta = setDraftMeta((current) => ({ ...current, ...metaPatch }));
    }
    let markdown = latestMarkdownRef.current;
    const fallback = cleanText(normalized.markdown_fallback).trim();
    if (fallback) {
      markdown = await insertMarkdown(
        fallback,
        patchDefaultPlacement(normalized),
        { target: normalized.target },
      );
    }
    setPatchCandidates((current) =>
      current.filter((candidate, index) => aiPatchId(candidate, index) !== id),
    );
    await emitAction("apply_ai_patch", {
      patch_id: id,
      patch: normalized,
      accepted: true,
      block_only: blockOnly,
      markdown,
      meta: nextMeta,
    });
  }

  async function handleRejectAIPatch(patch) {
    const normalized = normalizeAIPatch(patch);
    if (!normalized) {
      return;
    }
    const id = aiPatchId(normalized);
    setPatchCandidates((current) =>
      current.filter((candidate, index) => aiPatchId(candidate, index) !== id),
    );
    await emitAction("reject_ai_patch", {
      patch_id: id,
      patch: normalized,
      rejected: true,
    });
  }

  async function handleRegenerateAIPatch(patch) {
    const normalized = normalizeAIPatch(patch);
    if (!normalized) {
      return;
    }
    await handleAIInlineAction({
      operation: normalized.operation,
      trigger: "regenerate",
      selected_block: normalized.target,
    });
  }

  async function handleSetCover(item) {
    if (!editable) {
      return;
    }
    const cover = mediaPath(item);
    const nextMeta = setDraftMeta({ cover });
    await emitAction("apply_candidate_meta", {
      source: "media",
      media: item,
      meta_patch: { cover },
      meta: nextMeta,
    });
  }

  async function handleUploadMedia(payload) {
    if (!editable) {
      return;
    }
    await emitAction("upload_media", payload);
  }

  async function handleGenerateVisual(payload) {
    if (!editable) {
      return;
    }
    const action =
      cleanText(payload.asset_type || "cover") === "cover"
        ? "generate_cover_image"
        : "generate_visual_asset";
    await emitAction(action, payload);
  }

  async function handleSaveVisualCandidate(item) {
    if (!editable) {
      return;
    }
    await emitAction("save_visual_candidate", {
      candidate_id: cleanText(item.id),
      candidate: item,
    });
  }

  async function handleDiscardVisualCandidate(item) {
    if (!editable) {
      return;
    }
    await emitAction("discard_visual_candidate", {
      candidate_id: cleanText(item.id),
      candidate: item,
    });
  }

  async function handleLoadMediaPreviewDetail(item, source = "media") {
    await emitAction("load_media_preview_detail", {
      media: item,
      source,
      candidate_id: cleanText(item.id),
      relative_path: mediaPath(item),
    });
  }

  function handleOpenLargePreview(item, source = "media", key = "") {
    const cleanSource = source === "visual" ? "visual" : "media";
    setLargePreview({
      source: cleanSource,
      key: key || visualItemKey(item, 0),
    });
    setMobileView("Preview");
  }

  async function handleDeleteMedia(item) {
    if (!editable) {
      return;
    }
    const path = mediaPath(item);
    if (!path) {
      return;
    }
    if (
      typeof window !== "undefined" &&
      !window.confirm(label(labels, "delete_media_confirm"))
    ) {
      return;
    }
    await emitAction("delete_media", {
      media: item,
      relative_path: path,
    });
  }

  async function handleConvertMediaVideo(item) {
    if (!editable) {
      return;
    }
    const path = mediaPath(item);
    if (!path || mediaKind(item) !== "video") {
      return;
    }
    if (
      typeof window !== "undefined" &&
      !window.confirm(label(labels, "convert_video_confirm"))
    ) {
      return;
    }
    await emitAction("convert_media_video", {
      media: item,
      relative_path: path,
    });
  }

  async function requestPreview(previewQuality = "fast") {
    const nextLayout = setPreviewOpen(true);
    setMobileView("Preview");
    await emitAction("preview_post", {
      layout_state: nextLayout,
      preview_quality: previewQuality,
    });
  }

  const activePost = useMemo(
    () => posts.find((post) => postSlug(post) === activeSlug) || null,
    [activeSlug, posts],
  );

  const shellClasses = [
    "nb-shell",
    layout.focus_mode ? "is-focus" : "",
    layout.left_open ? "has-left" : "left-collapsed",
    layout.right_open ? "has-right" : "right-collapsed",
    `mobile-${mobileView.toLowerCase()}`,
  ]
    .filter(Boolean)
    .join(" ");

  const activeRightTab = RIGHT_TABS.includes(layout.active_right_tab)
    ? layout.active_right_tab
    : "Meta";
  const currentTitle =
    cleanText(draftMeta.title) || cleanText(activePost?.title) || label(labels, "title_label");
  const currentStatus = cleanText(draftMeta.status || activePost?.status || "draft");
  const currentDate = cleanText(draftMeta.date || activePost?.date || "");
  const basePaneHeight = Math.max(700, height - 190);
  const editorPaneHeight = layout.focus_mode
    ? Math.max(basePaneHeight, height - 120)
    : basePaneHeight;
  const shellStyle = {
    minHeight: `${height}px`,
    "--nb-editor-pane-height": `${editorPaneHeight}px`,
    "--nb-preview-pane-height": `${basePaneHeight}px`,
    "--nb-side-pane-height": `${Math.max(760, height - 80)}px`,
  };

  return (
    <main className={shellClasses} style={shellStyle}>
      <header className="nb-topbar">
        <div className="nb-title-strip">
          <strong>{currentTitle}</strong>
          <span className={`nb-status-pill ${statusClass(currentStatus)}`}>
            {currentStatus}
          </span>
          <span className="nb-toolbar-subtle">
            {currentDate || "-"} / {activeSlug || documentId}
          </span>
          {dirty ? <span className="nb-dirty-dot">Unsaved</span> : null}
        </div>
        <div className="nb-toolbar-actions">
          <button
            type="button"
            className="nb-button primary"
            disabled={!editable || Boolean(pendingAIAction)}
            onClick={() => emitAction("save_post")}
          >
            {label(labels, "save")}
          </button>
          <button
            type="button"
            className="nb-button"
            onClick={() => requestPreview("fast")}
          >
            {label(labels, "public_preview")}
          </button>
          <button
            type="button"
            className="nb-button"
            onClick={() => emitAction("run_check")}
          >
            {label(labels, "validate", "Check")}
          </button>
          <button
            type="button"
            className="nb-button"
            disabled={!editable || Boolean(pendingAIAction)}
            onClick={() => emitAction("publish_request")}
          >
            {label(labels, "publish")}
          </button>
        </div>
        <div className="nb-toolbar-actions compact">
          <button
            type="button"
            className="nb-icon-button"
            title={label(labels, "left_panel")}
            onClick={() => {
              const nextOpen = !layoutRef.current.left_open;
              applyLayoutLocal({
                ...layoutRef.current,
                left_open: nextOpen,
                focus_mode: false,
              });
              setMobileView("Editor");
            }}
          >
            A
          </button>
          <button
            type="button"
            className="nb-icon-button"
            title={label(labels, "right_panel")}
            onClick={() => {
              const nextOpen = !layoutRef.current.right_open;
              applyLayoutLocal({
                ...layoutRef.current,
                right_open: nextOpen,
                focus_mode: false,
              });
              setMobileView("Editor");
            }}
          >
            T
          </button>
          <button
            type="button"
            className="nb-button"
            onClick={toggleFocusMode}
          >
            {layout.focus_mode
              ? label(labels, "exit_focus")
              : label(labels, "focus_mode")}
          </button>
        </div>
      </header>

      <nav className="nb-mobile-tabs" aria-label={label(labels, "layout")}>
        {MOBILE_VIEWS.map((tab) => (
          <button
            type="button"
            key={tab}
            className={mobileView === tab ? "is-active" : ""}
            onClick={() => switchMobileView(tab)}
          >
            {label(labels, tab.toLowerCase())}
          </button>
        ))}
      </nav>

      <section className="nb-workspace">
        <aside className="nb-left-panel" aria-label={label(labels, "articles")}>
          <div className="nb-panel-header">
            <strong>{label(labels, "articles")}</strong>
            <button
              type="button"
              className="nb-icon-button"
              title={label(labels, "close_left_panel")}
              onClick={() => {
                applyLayoutLocal((current) => ({
                  ...current,
                  left_open: false,
                  focus_mode: false,
                }));
                setMobileView("Editor");
              }}
            >
              x
            </button>
          </div>
          <div className="nb-left-tools">
            <label className="nb-field compact">
              <span>{label(labels, "filter_posts")}</span>
              <select
                value={statusFilter}
                onChange={(event) => {
                  const next = event.target.value;
                  setStatusFilter(next);
                  emitAction("filter_posts", { status: next });
                }}
              >
                <option value="all">{label(labels, "all_statuses")}</option>
                {STATUS_OPTIONS.map((status) => (
                  <option key={status} value={status}>
                    {label(labels, status, status)}
                  </option>
                ))}
              </select>
            </label>
            <div className="nb-inline-form">
              <input
                value={newPostTitle}
                disabled={!editable}
                placeholder={label(labels, "title_label")}
                onChange={(event) => setNewPostTitle(event.target.value)}
              />
              <button
                type="button"
                className="nb-button"
                disabled={!editable || !newPostTitle.trim()}
                onClick={() => emitAction("create_post", { title: newPostTitle.trim() })}
              >
                {label(labels, "create_post")}
              </button>
            </div>
            <div className="nb-inline-form">
              <input
                value={evidenceId}
                disabled={!editable}
                placeholder={label(labels, "evidence_id")}
                onChange={(event) => setEvidenceId(event.target.value)}
              />
              <button
                type="button"
                className="nb-button"
                disabled={!editable || !evidenceId.trim()}
                onClick={() =>
                  emitAction("draft_from_evidence", { evidence_id: evidenceId.trim() })
                }
              >
                {label(labels, "draft_from_evidence")}
              </button>
            </div>
            <button
              type="button"
              className="nb-button wide"
              disabled={!editable}
              onClick={() => emitAction("draft_from_done", { source: "kanban_done" })}
            >
              {label(labels, "draft_from_done")}
            </button>
          </div>
          <div className="nb-post-list">
            {posts.length ? (
              posts.map((post) => {
                const slug = postSlug(post);
                return (
                  <button
                    type="button"
                    key={slug || postTitle(post)}
                    className={`nb-post-row ${slug === activeSlug ? "is-active" : ""}`}
                    onClick={() => emitAction("select_post", { slug, post })}
                  >
                    <span className="nb-post-title">{postTitle(post)}</span>
                    <span className="nb-post-meta">
                      {cleanText(post.date || "-")} / {cleanText(post.status || "draft")}
                    </span>
                  </button>
                );
              })
            ) : (
              <p className="nb-empty">{label(labels, "post")}</p>
            )}
          </div>
        </aside>

        <section className="nb-center-panel" aria-label={label(labels, "editor")}>
          {error ? <div className="nb-editor-error">{error}</div> : null}
          <div className="nb-editor-area">
            <div className="nb-title-editor">
              <label htmlFor="nb-title-input">{label(labels, "title_label")}</label>
              <input
                id="nb-title-input"
                value={cleanText(draftMeta.title)}
                readOnly={!editable}
                onChange={(event) => updateMetaText("title", event.target.value)}
              />
            </div>
            {editorSourceMode ? (
              <textarea
                ref={sourceTextareaRef}
                className="nb-source-editor"
                value={sourceMarkdown}
                readOnly={!editable}
                onChange={(event) => {
                  if (!editable) {
                    return;
                  }
                  const next = event.target.value;
                  setSourceMarkdown(next);
                  latestMarkdownRef.current = next;
                  setDirty(computeDirty(next, draftMetaRef.current));
                  syncMarkdown();
                }}
                onSelect={() => {
                  rememberSourceSelection();
                  refreshSelectedBlock();
                }}
                onKeyUp={() => {
                  rememberSourceSelection();
                  refreshSelectedBlock();
                }}
                onMouseUp={() => {
                  rememberSourceSelection();
                  refreshSelectedBlock();
                }}
                onBlur={() => {
                  rememberSourceSelection();
                  refreshSelectedBlock();
                  syncMarkdown();
                }}
              />
            ) : (
              <div
                className="nb-blocknote-frame"
                onKeyUp={handleEditorSelectionUpdate}
                onMouseUp={handleEditorSelectionUpdate}
                onFocus={handleEditorSelectionUpdate}
              >
                <BlockNoteView
                  editor={editor}
                  editable={editable}
                  theme="light"
                  slashMenu={false}
                  formattingToolbar={false}
                  onSelectionChange={handleEditorSelectionUpdate}
                  onChange={() => {
                    handleEditorSelectionUpdate();
                    syncMarkdown();
                  }}
                  onBlur={() => {
                    handleEditorSelectionUpdate();
                    syncMarkdown();
                  }}
                >
                  <BlogSlashMenu
                    editor={editor}
                    labels={labels}
                    onAIAction={handleAIInlineAction}
                  />
                </BlockNoteView>
              </div>
            )}
            <SelectionAIToolbar
              editable={editable}
              labels={labels}
              selectedBlock={selectedBlock}
              disabled={Boolean(pendingAIAction)}
              onAction={handleAIInlineAction}
            />
          </div>
          {largePreviewRow ? (
            <VisualPreviewDialog
              item={largePreviewRow.item}
              labels={labels}
              editable={editable}
              onClose={() => setLargePreview({ source: "", key: "" })}
              onInsert={handleInsertMedia}
              onSetCover={handleSetCover}
              onSaveCandidate={handleSaveVisualCandidate}
              onDiscardCandidate={handleDiscardVisualCandidate}
              onLoadFullPreview={(item) =>
                handleLoadMediaPreviewDetail(item, largePreview.source || "media")
              }
              onConvertVideo={
                largePreview.source === "media" ? handleConvertMediaVideo : null
              }
            />
          ) : null}
          {layout.preview_open ? (
            <div className="nb-preview-panel">
              <div className="nb-preview-toolbar">
                <strong>{label(labels, "preview")}</strong>
                <div className="nb-preview-actions">
                  <button
                    type="button"
                    className="nb-button"
                    onClick={() => requestPreview("fast")}
                  >
                    {label(labels, "update_preview")}
                  </button>
                  <button
                    type="button"
                    className="nb-button"
                    onClick={() => requestPreview("full")}
                  >
                    {label(labels, "high_quality_preview")}
                  </button>
                  <button
                    type="button"
                    className="nb-icon-button"
                    title={label(labels, "preview")}
                    onClick={() => {
                      applyLayoutLocal((current) => ({
                        ...current,
                        preview_open: false,
                        focus_mode: false,
                      }));
                      setMobileView("Editor");
                    }}
                  >
                    x
                  </button>
                </div>
              </div>
              {previewHtml ? (
                <iframe
                  className="nb-preview-frame"
                  title={label(labels, "public_preview")}
                  srcDoc={previewHtml}
                />
              ) : (
                <p className="nb-empty">{label(labels, "preview_empty")}</p>
              )}
            </div>
          ) : null}
        </section>

        <aside className="nb-right-rail" aria-label={label(labels, "right_panel")}>
          {RIGHT_TABS.map((tab) => (
            <button
              type="button"
              key={tab}
              className={activeRightTab === tab && layout.right_open ? "is-active" : ""}
              title={label(labels, tab.toLowerCase())}
              onClick={() => toggleRightTab(tab)}
            >
              {tab.slice(0, 1)}
            </button>
          ))}
        </aside>

        <aside className="nb-right-panel" aria-label={label(labels, "tools")}>
          <div className="nb-tabs">
            {RIGHT_TABS.map((tab) => (
              <button
                type="button"
                key={tab}
                className={activeRightTab === tab ? "is-active" : ""}
                onClick={() => openRightTab(tab, false)}
              >
                {label(labels, tab.toLowerCase())}
              </button>
            ))}
            <button
              type="button"
              className="nb-icon-button"
              title={label(labels, "close_right_panel")}
              onClick={closeRightPanel}
            >
              x
            </button>
          </div>
          {activeRightTab === "Meta" ? (
            <MetaDrawer
              editable={editable}
              labels={labels}
              meta={draftMeta}
              onText={updateMetaText}
              onList={updateMetaList}
            />
          ) : null}
          {activeRightTab === "Media" ? (
            <MediaDrawer
              editable={editable}
              labels={labels}
              mediaItems={mediaItems}
              onInsert={handleInsertMedia}
              onSetCover={handleSetCover}
              onUpload={handleUploadMedia}
              onOpenLargePreview={(item, key) =>
                handleOpenLargePreview(item, "media", key)
              }
              onDelete={handleDeleteMedia}
              onConvertVideo={handleConvertMediaVideo}
            />
          ) : null}
          {activeRightTab === "AI" ? (
            <AiDrawer
              editable={editable}
              labels={labels}
              candidates={aiCandidates}
              patchCandidates={patchCandidates}
              pendingAIAction={pendingAIAction}
              selectedBlock={selectedBlock}
              onInsert={handleInsertCandidate}
              onApplyMeta={handleApplyCandidateMeta}
              onRun={(payload) => emitAction("generate_ai_candidate", payload)}
              onInlineAction={handleAIInlineAction}
              onAcceptPatch={handleAcceptAIPatch}
              onRejectPatch={handleRejectAIPatch}
              onRegeneratePatch={handleRegenerateAIPatch}
              onCancelPending={handleCancelAIStream}
              currentTitle={currentTitle}
            />
          ) : null}
          {activeRightTab === "Visual" ? (
            <VisualDrawer
              editable={editable}
              labels={labels}
              visualConfig={visualConfig}
              mediaItems={mediaItems}
              visualResults={visualResults}
              visualGuidance={visualGuidance}
              operationNotice={operationNotice}
              onGenerate={handleGenerateVisual}
              onInsert={handleInsertMedia}
              onSetCover={handleSetCover}
              onSaveCandidate={handleSaveVisualCandidate}
              onDiscardCandidate={handleDiscardVisualCandidate}
              onOpenLargePreview={(item, key) =>
                handleOpenLargePreview(item, "visual", key)
              }
            />
          ) : null}
          {activeRightTab === "Check" ? (
            <CheckDrawer
              labels={labels}
              state={validationState}
              onRun={() => emitAction("run_check")}
            />
          ) : null}
        </aside>
      </section>
    </main>
  );
}

function MetaDrawer({ editable, labels, meta, onText, onList }) {
  return (
    <div className="nb-drawer-body">
      <label className="nb-field">
        <span>{label(labels, "status")}</span>
        <select
          value={cleanText(meta.status || "draft")}
          disabled={!editable}
          onChange={(event) => onText("status", event.target.value)}
        >
          {STATUS_OPTIONS.map((status) => (
            <option key={status} value={status}>
              {label(labels, status, status)}
            </option>
          ))}
        </select>
      </label>
      <label className="nb-field">
        <span>{label(labels, "date")}</span>
        <input
          value={cleanText(meta.date)}
          readOnly={!editable}
          onChange={(event) => onText("date", event.target.value)}
        />
      </label>
      <label className="nb-field">
        <span>{label(labels, "summary")}</span>
        <textarea
          value={cleanText(meta.summary)}
          readOnly={!editable}
          onChange={(event) => onText("summary", event.target.value)}
          rows={4}
        />
      </label>
      <label className="nb-field">
        <span>{label(labels, "tags")}</span>
        <input
          value={csvFromValue(meta.tags)}
          readOnly={!editable}
          onChange={(event) => onList("tags", event.target.value)}
        />
      </label>
      <label className="nb-field">
        <span>{label(labels, "cover")}</span>
        <input
          value={cleanText(meta.cover)}
          readOnly={!editable}
          onChange={(event) => onText("cover", event.target.value)}
        />
      </label>
      <label className="nb-field">
        <span>{label(labels, "related_evidence")}</span>
        <input
          value={csvFromValue(meta.related_evidence)}
          readOnly={!editable}
          onChange={(event) => onList("related_evidence", event.target.value)}
        />
      </label>
      <label className="nb-field">
        <span>{label(labels, "related_kanban")}</span>
        <input
          value={csvFromValue(meta.related_kanban)}
          readOnly={!editable}
          onChange={(event) => onList("related_kanban", event.target.value)}
        />
      </label>
    </div>
  );
}

function MediaPreview({ item, labels, className = "", srcOverride = "" }) {
  const src = cleanText(srcOverride) || mediaPreviewSrc(item);
  const kind = mediaKind(item);
  const alt = cleanText(item.alt || item.alt_text || item.name || label(labels, "media"));
  const classes = ["nb-media-preview", className].filter(Boolean).join(" ");
  const [playbackFailed, setPlaybackFailed] = useState(false);
  useEffect(() => {
    setPlaybackFailed(false);
  }, [src]);
  if (!src) {
    return (
      <div className={`${classes} is-empty`} aria-label={label(labels, "preview_unavailable")}>
        {kind === "video" ? "VID" : "IMG"}
      </div>
    );
  }
  if (kind === "video") {
    return (
      <div className={`${classes} nb-video-preview`}>
        <video
          src={src}
          controls
          preload="metadata"
          aria-label={alt}
          onError={() => setPlaybackFailed(true)}
        />
        {playbackFailed ? (
          <span className="nb-video-error">{label(labels, "video_playback_failed")}</span>
        ) : null}
      </div>
    );
  }
  return <img className={classes} src={src} alt={alt} loading="lazy" />;
}

function InsertPlacementSelect({
  labels,
  value,
  onChange,
  disabled = false,
  includeCursor = true,
  includeReplace = true,
}) {
  return (
    <label className="nb-field compact nb-placement-field">
      <span>{label(labels, "insert_placement")}</span>
      <select
        value={normalizeInsertPlacement(value)}
        disabled={disabled}
        onChange={(event) => onChange(normalizeInsertPlacement(event.target.value))}
      >
        {includeCursor ? (
          <option value="cursor">{label(labels, "insert_at_cursor")}</option>
        ) : null}
        <option value="marker">{label(labels, "insert_at_marker")}</option>
        <option value="append">{label(labels, "insert_at_end")}</option>
        {includeReplace ? (
          <option value="replace">{label(labels, "insert_replace")}</option>
        ) : null}
      </select>
    </label>
  );
}

function MediaDrawer({
  editable,
  labels,
  mediaItems,
  onInsert,
  onSetCover,
  onUpload,
  onOpenLargePreview,
  onDelete,
  onConvertVideo,
}) {
  const [file, setFile] = useState(null);
  const [kind, setKind] = useState("image");
  const [alt, setAlt] = useState("");
  const [caption, setCaption] = useState("");
  const [insert, setInsert] = useState(false);
  const [cover, setCover] = useState(false);
  const [insertPlacement, setInsertPlacement] = useState("cursor");
  const [uploadPlacement, setUploadPlacement] = useState("marker");
  const keyedRows = mediaItems.map((item, index) => ({
    item,
    key: visualItemKey(item, index),
  }));

  function fileToDataUrl(targetFile) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(cleanText(reader.result));
      reader.onerror = () => reject(reader.error || new Error("file read failed"));
      reader.readAsDataURL(targetFile);
    });
  }

  async function uploadSelected() {
    if (!editable || !file) {
      return;
    }
    const dataUrl = await fileToDataUrl(file);
    onUpload({
      filename: file.name,
      kind,
      data_url: dataUrl,
      alt,
      caption,
      insert,
      placement: uploadPlacement,
      cover,
    });
  }

  return (
    <div className="nb-drawer-body">
      <div className="nb-panel-title">{label(labels, "media_library")}</div>
      <div className="nb-upload-box">
        <input
          type="file"
          disabled={!editable}
          accept="image/*,video/mp4,video/webm"
          onChange={(event) => {
            const nextFile = event.target.files?.[0] || null;
            setFile(nextFile);
            if (nextFile?.type?.startsWith("video/")) {
              setKind("video");
            } else if (nextFile) {
              setKind("image");
            }
          }}
        />
        <label className="nb-field compact">
          <span>{label(labels, "media_kind")}</span>
          <select
            value={kind}
            disabled={!editable}
            onChange={(event) => setKind(event.target.value)}
          >
            <option value="image">image</option>
            <option value="video">video</option>
          </select>
        </label>
        <label className="nb-field compact">
          <span>{label(labels, "alt_text")}</span>
          <input
            value={alt}
            disabled={!editable}
            onChange={(event) => setAlt(event.target.value)}
          />
          <small>{label(labels, "visual_alt_help")}</small>
        </label>
        <label className="nb-field compact">
          <span>{label(labels, "caption")}</span>
          <input
            value={caption}
            disabled={!editable}
            onChange={(event) => setCaption(event.target.value)}
          />
          <small>{label(labels, "visual_caption_help")}</small>
        </label>
        <div className="nb-check-row">
          <label>
            <input
              type="checkbox"
              checked={insert}
              disabled={!editable}
              onChange={(event) => setInsert(event.target.checked)}
            />
            {label(labels, "insert_into_post")}
          </label>
          <label>
            <input
              type="checkbox"
              checked={cover}
              disabled={!editable || kind !== "image"}
              onChange={(event) => setCover(event.target.checked)}
            />
            {label(labels, "cover")}
          </label>
        </div>
        {insert ? (
          <InsertPlacementSelect
            labels={labels}
            value={uploadPlacement}
            onChange={setUploadPlacement}
            disabled={!editable}
            includeCursor={false}
            includeReplace={false}
          />
        ) : null}
        <button
          type="button"
          className="nb-button wide"
          disabled={!editable || !file}
          onClick={uploadSelected}
        >
          {label(labels, "upload_media")}
        </button>
      </div>
      {mediaItems.length ? (
        <div className="nb-media-list">
          {keyedRows.map(({ item, key }) => {
            const path = mediaPath(item);
            const kind = mediaKind(item);
            const previewSrc = mediaPreviewSrc(item);
            const codecLabel = mediaVideoCodecLabel(item, labels);
            const videoWarning = mediaVideoWarning(item, labels);
            const canDelete = editable && Boolean(path);
            return (
              <article className="nb-media-row" key={key || path}>
                <button
                  type="button"
                  className="nb-preview-button nb-media-thumb-button"
                  onClick={() => onOpenLargePreview(item, key)}
                  title={label(labels, "view_full_preview")}
                >
                  <MediaPreview
                    item={item}
                    labels={labels}
                    className="nb-media-thumb"
                  />
                </button>
                <div className="nb-media-meta">
                  <strong>{cleanText(item.name || path || label(labels, "media"))}</strong>
                  <span>
                    {kind}
                    {item.size_kb !== undefined ? ` / ${item.size_kb} KB` : ""}
                    {item.referenced === false ? " / unused" : ""}
                  </span>
                  {codecLabel ? <span>{codecLabel}</span> : null}
                  {videoWarning ? (
                    <span className="nb-warning-line">{videoWarning}</span>
                  ) : null}
                  {!previewSrc ? (
                    <span className="nb-muted-line">{label(labels, "preview_unavailable")}</span>
                  ) : null}
                </div>
                <div className="nb-row-actions">
                  <InsertPlacementSelect
                    labels={labels}
                    value={insertPlacement}
                    onChange={setInsertPlacement}
                    disabled={!editable}
                  />
                  <button
                    type="button"
                    className="nb-button"
                    onClick={() => onOpenLargePreview(item, key)}
                  >
                    {label(labels, "view_full_preview")}
                  </button>
                  <button
                    type="button"
                    className="nb-button"
                    disabled={!editable}
                    onClick={() => onInsert(item, insertPlacement)}
                  >
                    {label(labels, "insert_into_post")}
                  </button>
                  <button
                    type="button"
                    className="nb-button"
                    disabled={
                      !editable ||
                      (kind !== "image" && !/\.(png|jpe?g|gif|webp|avif)$/i.test(path))
                    }
                    onClick={() => onSetCover(item)}
                  >
                    {label(labels, "cover")}
                  </button>
                  <button
                    type="button"
                    className="nb-button danger"
                    disabled={!canDelete}
                    title={
                      item.referenced
                        ? label(labels, "delete_media_referenced")
                        : label(labels, "delete_media")
                    }
                    onClick={() => onDelete(item)}
                  >
                    {label(labels, "delete_media")}
                  </button>
                  {kind === "video" ? (
                    <button
                      type="button"
                      className="nb-button"
                      disabled={!editable || !path}
                      onClick={() => onConvertVideo(item)}
                    >
                      {label(labels, "convert_video")}
                    </button>
                  ) : null}
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <p className="nb-empty">{label(labels, "no_media")}</p>
      )}
    </div>
  );
}

function SelectionContextPanel({ labels, selectedBlock }) {
  const context = asObject(selectedBlock);
  const blockId = cleanText(context.block_id || context.cursor_block_id);
  const selectionText = cleanText(context.selection_text).trim();
  const surrounding = asArray(context.surrounding_blocks)
    .map((block) => asObject(block))
    .map((block) => cleanText(block.text).trim())
    .filter(Boolean);
  if (!blockId && !selectionText && !surrounding.length) {
    return null;
  }
  return (
    <section className="nb-selection-context">
      <strong>{label(labels, "selection_context")}</strong>
      {blockId ? <span className="nb-muted-line">{blockId}</span> : null}
      {selectionText ? (
        <pre>{selectionText.slice(0, 520)}</pre>
      ) : (
        <p>{label(labels, "selection_context_empty")}</p>
      )}
      {!selectionText && surrounding.length ? <pre>{surrounding[0].slice(0, 520)}</pre> : null}
    </section>
  );
}

function AiDrawer({
  editable,
  labels,
  candidates,
  patchCandidates = [],
  pendingAIAction = null,
  selectedBlock,
  onInsert,
  onApplyMeta,
  onRun,
  onInlineAction,
  onAcceptPatch,
  onRejectPatch,
  onRegeneratePatch,
  onCancelPending,
  currentTitle,
}) {
  const [evidenceId, setEvidenceId] = useState("");
  const [candidatePlacement, setCandidatePlacement] = useState("cursor");
  return (
    <div className="nb-drawer-body">
      <SelectionContextPanel labels={labels} selectedBlock={selectedBlock} />
      <div className="nb-ai-inline-actions">
        {[
          ["polish", "ai_action_polish", "Polish"],
          ["shorten", "ai_action_shorten", "Shorten"],
          ["expand", "ai_action_expand", "Expand"],
          ["continue", "ai_action_continue", "Continue"],
          ["translate", "ai_action_translate", "Translate"],
          ["tone", "ai_action_tone", "Tone"],
          ["formula", "ai_action_formula", "LaTeX"],
          ["visual", "ai_action_visual", "Visual"],
          ["outline", "ai_action_outline", "Outline"],
        ].map(([operation, key, fallback]) => (
          <button
            type="button"
            className="nb-button"
            disabled={!editable || Boolean(pendingAIAction)}
            key={operation}
            onClick={() => onInlineAction({ operation, trigger: "ai_drawer" })}
          >
            {label(labels, key, fallback)}
          </button>
        ))}
      </div>
      <CandidatePatchPanel
        labels={labels}
        patches={patchCandidates}
        pendingAction={pendingAIAction}
        editable={editable}
        onAccept={onAcceptPatch}
        onReject={onRejectPatch}
        onRegenerate={onRegeneratePatch}
        onCancelPending={onCancelPending}
      />
      <button
        type="button"
        className="nb-button wide"
        disabled={!editable}
        onClick={() => onRun({ source: "title", title: currentTitle })}
      >
        {label(labels, "draft_from_title")}
      </button>
      <div className="nb-inline-form">
        <input
          value={evidenceId}
          disabled={!editable}
          placeholder={label(labels, "evidence_id")}
          onChange={(event) => setEvidenceId(event.target.value)}
        />
        <button
          type="button"
          className="nb-button"
          disabled={!editable || !evidenceId.trim()}
          onClick={() => onRun({ source: "evidence", evidence_id: evidenceId.trim() })}
        >
          {label(labels, "generate_candidate")}
        </button>
      </div>
      <button
        type="button"
        className="nb-button wide"
        disabled={!editable}
        onClick={() => onRun({ source: "kanban_done" })}
      >
        {label(labels, "draft_from_done")}
      </button>
      {candidates.length ? (
        <div className="nb-candidate-list">
          {candidates.map((candidate, index) => {
            const meta = candidateMeta(candidate);
            const body = candidateBody(candidate);
            const tags = asArray(meta.tags).map(cleanText).filter(Boolean);
            const warnings = asArray(candidate.warnings || meta.warnings)
              .map(cleanText)
              .filter(Boolean);
            return (
              <article
                className="nb-candidate"
                key={`${candidateId(candidate, index)}-${index}`}
              >
                <div className="nb-candidate-title">
                  {cleanText(candidate.title || meta.title || label(labels, "ai_candidate"))}
                </div>
                {meta.summary ? <p>{cleanText(meta.summary)}</p> : null}
                {tags.length ? <p>{tags.join(", ")}</p> : null}
                {meta.cover_prompt ? (
                  <details>
                    <summary>{label(labels, "cover_prompt")}</summary>
                    <p>{cleanText(meta.cover_prompt)}</p>
                  </details>
                ) : null}
                {warnings.length ? (
                  <details open>
                    <summary>{label(labels, "candidate_warnings")}</summary>
                    <ul className="nb-compact-list">
                      {warnings.map((warning) => (
                        <li key={warning}>{warning}</li>
                      ))}
                    </ul>
                  </details>
                ) : null}
                {body ? <pre>{body.slice(0, 420)}</pre> : null}
                <div className="nb-row-actions">
                  <InsertPlacementSelect
                    labels={labels}
                    value={candidatePlacement}
                    onChange={setCandidatePlacement}
                    disabled={!editable}
                  />
                  <button
                    type="button"
                    className="nb-button"
                    disabled={!editable}
                    onClick={() => onInsert(candidate, index, candidatePlacement)}
                  >
                    {label(labels, "insert_candidate")}
                  </button>
                  <button
                    type="button"
                    className="nb-button"
                    disabled={!editable}
                    onClick={() => onInsert(candidate, index, "append")}
                  >
                    {label(labels, "append_candidate")}
                  </button>
                  <button
                    type="button"
                    className="nb-button"
                    disabled={!editable}
                    onClick={() => onApplyMeta(candidate, index)}
                  >
                    {label(labels, "apply_candidate_meta")}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <p className="nb-empty">{label(labels, "ai_candidate")}</p>
      )}
    </div>
  );
}

function VisualPreviewActions({
  item,
  labels,
  editable,
  onInsert,
  onSetCover,
  onSaveCandidate,
  onDiscardCandidate,
}) {
  const [insertPlacement, setInsertPlacement] = useState("cursor");
  const kind = mediaKind(item);
  const snippet = mediaSnippet(item);
  const path = mediaPath(item);
  const canCover = kind === "image" || /\.(png|jpe?g|gif|webp|avif)$/i.test(path);
  const unsaved = item.unsaved === true;
  if (unsaved) {
    return (
      <>
        <button
          type="button"
          className="nb-button primary"
          disabled={!editable || !cleanText(item.id)}
          onClick={() => onSaveCandidate(item)}
        >
          {label(labels, "save_to_media")}
        </button>
        <button
          type="button"
          className="nb-button"
          disabled={!editable || !cleanText(item.id)}
          onClick={() => onDiscardCandidate(item)}
        >
          {label(labels, "discard_candidate")}
        </button>
      </>
    );
  }
  return (
    <>
      <InsertPlacementSelect
        labels={labels}
        value={insertPlacement}
        onChange={setInsertPlacement}
        disabled={!editable}
      />
      <button
        type="button"
        className="nb-button"
        disabled={!editable || !snippet}
        onClick={() => onInsert(item, insertPlacement)}
      >
        {label(labels, "insert_into_post")}
      </button>
      <button
        type="button"
        className="nb-button"
        disabled={!editable || !canCover}
        onClick={() => onSetCover(item)}
      >
        {label(labels, "cover")}
      </button>
    </>
  );
}

function VisualPreviewDialog({
  item,
  labels,
  editable,
  onClose,
  onInsert,
  onSetCover,
  onSaveCandidate,
  onDiscardCandidate,
  onLoadFullPreview,
  onConvertVideo = null,
}) {
  const kind = mediaKind(item);
  const path = mediaPath(item);
  const name = cleanText(item.name || path || label(labels, "media"));
  const fullSrc = mediaFullPreviewSrc(item);
  const previewSrc = mediaPreviewSrc(item);
  const displaySrc = fullSrc || previewSrc;
  const canLoadFull = item.full_preview_available !== false && !fullSrc;
  const codecLabel = mediaVideoCodecLabel(item, labels);
  const videoWarning = mediaVideoWarning(item, labels);
  const overlayStyle = useFloatingPreviewStyle(true);
  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);
  return (
    <div
      className="nb-preview-dialog"
      role="dialog"
      aria-modal="true"
      aria-label={label(labels, "view_full_preview")}
      style={overlayStyle}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        className="nb-preview-dialog-panel"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="nb-preview-dialog-header">
          <div>
            <strong>{name}</strong>
            <span className="nb-muted-line">
              {kind}
              {item.original_size_kb !== undefined
                ? ` / ${item.original_size_kb} KB`
                : item.size_kb !== undefined
                  ? ` / ${item.size_kb} KB`
                  : ""}
              {fullSrc ? ` / ${label(labels, "high_quality_preview")}` : ""}
            </span>
          </div>
          <button
            type="button"
            className="nb-icon-button"
            title={label(labels, "close")}
            onClick={onClose}
          >
            x
          </button>
        </div>
        <MediaPreview
          item={item}
          labels={labels}
          className="nb-visual-dialog-preview"
          srcOverride={displaySrc}
        />
        {codecLabel ? <div className="nb-muted-line">{codecLabel}</div> : null}
        {videoWarning ? <div className="nb-warning-line">{videoWarning}</div> : null}
        {path ? <div className="nb-muted-line">{path}</div> : null}
        <div className="nb-row-actions">
          <button
            type="button"
            className="nb-button"
            disabled={!canLoadFull}
            onClick={() => onLoadFullPreview(item)}
          >
            {fullSrc
              ? label(labels, "high_quality_preview")
              : label(labels, "load_full_preview")}
          </button>
          <VisualPreviewActions
            item={item}
            labels={labels}
            editable={editable}
            onInsert={onInsert}
            onSetCover={onSetCover}
            onSaveCandidate={onSaveCandidate}
            onDiscardCandidate={onDiscardCandidate}
          />
          {kind === "video" && onConvertVideo ? (
            <button
              type="button"
              className="nb-button"
              disabled={!editable || !path}
              onClick={() => onConvertVideo(item)}
            >
              {label(labels, "convert_video")}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function VisualResultCard({
  item,
  labels,
  editable,
  onOpenPreview,
  onInsert,
  onSetCover,
  onSaveCandidate,
  onDiscardCandidate,
}) {
  const path = mediaPath(item);
  const kind = mediaKind(item);
  const snippet = mediaSnippet(item);
  const name = cleanText(item.name || path || label(labels, "media"));
  return (
    <article className="nb-visual-card">
      <button
        type="button"
        className="nb-preview-button"
        onClick={() => onOpenPreview(item)}
        title={label(labels, "view_full_preview")}
      >
        <MediaPreview item={item} labels={labels} className="nb-visual-preview" />
      </button>
      <div className="nb-visual-card-main">
        <strong>{name}</strong>
        <span className="nb-muted-line">
          {kind}
          {item.asset_type ? ` / ${cleanText(item.asset_type)}` : ""}
          {item.original_size_kb !== undefined
            ? ` / ${item.original_size_kb} KB`
            : item.size_kb !== undefined
              ? ` / ${item.size_kb} KB`
              : ""}
          {item.referenced === false ? " / unused" : ""}
        </span>
        {snippet ? <pre className="nb-snippet-preview">{snippet}</pre> : null}
        <div className="nb-row-actions">
          <button
            type="button"
            className="nb-button"
            onClick={() => onOpenPreview(item)}
          >
            {label(labels, "view_full_preview")}
          </button>
          <VisualPreviewActions
            item={item}
            labels={labels}
            editable={editable}
            onInsert={onInsert}
            onSetCover={onSetCover}
            onSaveCandidate={onSaveCandidate}
            onDiscardCandidate={onDiscardCandidate}
          />
        </div>
      </div>
    </article>
  );
}

function VisualResultsList({
  items,
  labels,
  editable,
  onInsert,
  onSetCover,
  onSaveCandidate,
  onDiscardCandidate,
  onOpenLargePreview,
}) {
  const rows = asArray(items).map(asObject);
  const keyedRows = rows.map((item, index) => ({
    item,
    key: visualItemKey(item, index),
  }));
  if (!rows.length) {
    return null;
  }
  return (
    <section className="nb-visual-results">
      <div className="nb-panel-title">{label(labels, "recent_visuals")}</div>
      {keyedRows.map(({ item, key }) => (
        <VisualResultCard
          key={key}
          item={item}
          labels={labels}
          editable={editable}
          onOpenPreview={() => onOpenLargePreview(item, key)}
          onInsert={onInsert}
          onSetCover={onSetCover}
          onSaveCandidate={onSaveCandidate}
          onDiscardCandidate={onDiscardCandidate}
        />
      ))}
    </section>
  );
}

function OperationNotice({ notice, source = "" }) {
  const data = asObject(notice);
  const message = cleanText(data.message).trim();
  if (!message) {
    return null;
  }
  const noticeSource = cleanText(data.source).trim();
  if (source && noticeSource && noticeSource !== source) {
    return null;
  }
  const tone = cleanText(data.tone || "info").toLowerCase();
  const className = tone === "error" ? "nb-editor-error" : "nb-editor-notice";
  return <div className={className}>{message}</div>;
}

function VisualDrawer({
  editable,
  labels,
  visualConfig,
  mediaItems = [],
  visualResults,
  visualGuidance,
  operationNotice = {},
  onGenerate,
  onInsert,
  onSetCover,
  onSaveCandidate,
  onDiscardCandidate,
  onOpenLargePreview,
}) {
  const [assetType, setAssetType] = useState("cover");
  const [prompt, setPrompt] = useState("");
  const [styleChoice, setStyleChoice] = useState("");
  const [customStyle, setCustomStyle] = useState("");
  const [sizeChoice, setSizeChoice] = useState("");
  const [customSize, setCustomSize] = useState("");
  const [alt, setAlt] = useState("");
  const [caption, setCaption] = useState("");
  const [sourceVideo, setSourceVideo] = useState("");
  const [referenceImage, setReferenceImage] = useState("");
  const configured = visualConfig.configured === true;
  const model =
    assetType === "video_edit"
      ? cleanText(visualConfig.video_model)
      : cleanText(visualConfig.image_model);
  const keySource = cleanText(visualConfig.api_key_source || "");
  const warnings = asArray(visualConfig.warnings).map(cleanText).filter(Boolean);
  const guidance = asObject(asObject(visualGuidance)[assetType]);
  const suggestions = asArray(guidance.prompt_suggestions).map(asObject);
  const styleOptions = optionPairs(guidance.style_options);
  const sizeOptions = optionPairs(guidance.size_options);
  const selectedStyle = styleChoice === "__custom__" ? customStyle : styleChoice;
  const selectedSize = sizeChoice === "__custom__" ? customSize : sizeChoice;
  const selectableMedia = useMemo(
    () => [...asArray(mediaItems), ...asArray(visualResults)],
    [mediaItems, visualResults],
  );
  const sourceVideoOptions = useMemo(
    () => selectableMediaOptions(selectableMedia, "video", labels),
    [labels, selectableMedia],
  );
  const referenceImageOptions = useMemo(
    () => selectableMediaOptions(selectableMedia, "image", labels),
    [labels, selectableMedia],
  );

  useEffect(() => {
    setStyleChoice("");
    setCustomStyle("");
    setSizeChoice("");
    setCustomSize("");
  }, [assetType]);

  function renderOptionSelect({ title, value, onChange, options, customLabel }) {
    const rows = options.length
      ? options
      : [{ label: label(labels, "visual_default"), value: "" }];
    return (
      <select value={value} disabled={!editable} onChange={(event) => onChange(event.target.value)}>
        {rows.map((option) => (
          <option value={option.value} key={`${title}-${option.label}-${option.value}`}>
            {option.label}
            {!option.value && guidance.default_size && title === "size"
              ? ` (${label(labels, "visual_default")} ${cleanText(guidance.default_size)})`
              : ""}
          </option>
        ))}
        <option value="__custom__">{customLabel}</option>
      </select>
    );
  }

  return (
    <div className="nb-drawer-body">
      <div className="nb-provider-box">
        <strong>{label(labels, "visual_provider")}</strong>
        <span>
          {cleanText(visualConfig.provider || "dashscope_wan")} / {model || "-"}
        </span>
        <span>
          {keySource
            ? `${label(labels, "using_key_from")} ${keySource}`
            : label(labels, "missing_visual_key")}
        </span>
      </div>
      {!configured ? (
        <p className="nb-editor-error">{label(labels, "missing_visual_key")}</p>
      ) : null}
      <OperationNotice notice={operationNotice} source="visual" />
      {warnings.length ? (
        <ul className="nb-compact-list">
          {warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}
      <label className="nb-field">
        <span>{label(labels, "visual")}</span>
        <select
          value={assetType}
          disabled={!editable}
          onChange={(event) => setAssetType(event.target.value)}
        >
          <option value="cover">{label(labels, "cover")}</option>
          <option value="flowchart">{label(labels, "flowchart")}</option>
          <option value="example">{label(labels, "example")}</option>
          <option value="video_edit">{label(labels, "video_edit")}</option>
        </select>
      </label>
      {suggestions.length ? (
        <div className="nb-suggestion-group">
          <span>{label(labels, "visual_prompt_suggestions")}</span>
          <div className="nb-suggestion-list">
            {suggestions.map((suggestion, index) => (
              <button
                type="button"
                className="nb-button"
                disabled={!editable}
                key={`${cleanText(suggestion.label)}-${index}`}
                onClick={() => setPrompt(cleanText(suggestion.prompt))}
              >
                {cleanText(suggestion.label || label(labels, "visual_prompt"))}
              </button>
            ))}
          </div>
        </div>
      ) : null}
      <label className="nb-field">
        <span>{label(labels, "visual_prompt")}</span>
        <textarea
          value={prompt}
          disabled={!editable}
          onChange={(event) => setPrompt(event.target.value)}
          rows={5}
        />
      </label>
      {assetType === "video_edit" ? (
        <>
          <label className="nb-field">
            <span>{label(labels, "source_video_select")}</span>
            <select
              value={
                sourceVideoOptions.some((option) => option.path === sourceVideo)
                  ? sourceVideo
                  : ""
              }
              disabled={!editable || !sourceVideoOptions.length}
              onChange={(event) => setSourceVideo(event.target.value)}
            >
              <option value="">
                {sourceVideoOptions.length
                  ? label(labels, "visual_custom")
                  : label(labels, "no_source_videos")}
              </option>
              {sourceVideoOptions.map((option) => (
                <option value={option.path} key={`source-video-${option.path}`}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="nb-field">
            <span>{label(labels, "source_video_manual")}</span>
            <input
              value={sourceVideo}
              disabled={!editable}
              placeholder="media/blog/post/source.mp4 or https://example.com/source.mp4"
              onChange={(event) => setSourceVideo(event.target.value)}
            />
            <small>{label(labels, "video_edit_source_help")}</small>
          </label>
          <label className="nb-field">
            <span>{label(labels, "reference_image_select")}</span>
            <select
              value={
                referenceImageOptions.some((option) => option.path === referenceImage)
                  ? referenceImage
                  : ""
              }
              disabled={!editable || !referenceImageOptions.length}
              onChange={(event) => setReferenceImage(event.target.value)}
            >
              <option value="">
                {referenceImageOptions.length
                  ? label(labels, "visual_custom")
                  : label(labels, "no_reference_images")}
              </option>
              {referenceImageOptions.map((option) => (
                <option value={option.path} key={`reference-image-${option.path}`}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="nb-field">
            <span>{label(labels, "reference_image_manual")}</span>
            <input
              value={referenceImage}
              disabled={!editable}
              placeholder="media/blog/post/reference.png"
              onChange={(event) => setReferenceImage(event.target.value)}
            />
          </label>
        </>
      ) : null}
      <label className="nb-field">
        <span>{label(labels, "visual_style")}</span>
        {renderOptionSelect({
          title: "style",
          value: styleChoice,
          onChange: setStyleChoice,
          options: styleOptions,
          customLabel: label(labels, "visual_custom"),
        })}
        {styleChoice === "__custom__" ? (
          <input
            value={customStyle}
            disabled={!editable}
            placeholder={label(labels, "visual_style")}
            onChange={(event) => setCustomStyle(event.target.value)}
          />
        ) : null}
        <small>{cleanText(guidance.style_help || label(labels, "visual_style_help"))}</small>
      </label>
      <label className="nb-field">
        <span>{label(labels, "visual_size")}</span>
        {renderOptionSelect({
          title: "size",
          value: sizeChoice,
          onChange: setSizeChoice,
          options: sizeOptions,
          customLabel: label(labels, "visual_size_custom"),
        })}
        {sizeChoice === "__custom__" ? (
          <input
            value={customSize}
            disabled={!editable}
            placeholder="1536*864"
            onChange={(event) => setCustomSize(event.target.value)}
          />
        ) : null}
        <small>{cleanText(guidance.size_help || label(labels, "visual_size_help"))}</small>
      </label>
      <label className="nb-field">
        <span>{label(labels, "alt_text")}</span>
        <input
          value={alt}
          disabled={!editable}
          onChange={(event) => setAlt(event.target.value)}
        />
        <small>{cleanText(guidance.alt_help || label(labels, "visual_alt_help"))}</small>
      </label>
      <label className="nb-field">
        <span>{label(labels, "caption")}</span>
        <input
          value={caption}
          disabled={!editable}
          onChange={(event) => setCaption(event.target.value)}
        />
        <small>{cleanText(guidance.caption_help || label(labels, "visual_caption_help"))}</small>
      </label>
      <button
        type="button"
        className="nb-button wide"
        disabled={
          !editable ||
          !configured ||
          !prompt.trim() ||
          (assetType === "video_edit" && !sourceVideo.trim())
        }
        onClick={() =>
          onGenerate({
            asset_type: assetType,
            prompt: prompt.trim(),
            style: selectedStyle,
            size: selectedSize,
            alt,
            caption,
            source_video: sourceVideo.trim(),
            reference_image: referenceImage.trim(),
          })
        }
      >
        {assetType === "cover"
          ? label(labels, "generate_cover_image")
          : label(labels, "generate_visual")}
      </button>
      <VisualResultsList
        items={visualResults}
        labels={labels}
        editable={editable}
        onInsert={onInsert}
        onSetCover={onSetCover}
        onSaveCandidate={onSaveCandidate}
        onDiscardCandidate={onDiscardCandidate}
        onOpenLargePreview={onOpenLargePreview}
      />
    </div>
  );
}

function CheckDrawer({ labels, state, onRun }) {
  const errors = asArray(state.errors).map(cleanText).filter(Boolean);
  const warnings = asArray(state.warnings).map(cleanText).filter(Boolean);
  const quality = asArray(state.quality).map(cleanText).filter(Boolean);
  return (
    <div className="nb-drawer-body">
      <button type="button" className="nb-button wide" onClick={onRun}>
        {label(labels, "rerun_check", "Run check again")}
      </button>
      <CheckList title={label(labels, "validation_errors")} items={errors} tone="danger" />
      <CheckList title={label(labels, "validation_warnings")} items={warnings} tone="warn" />
      <CheckList title={label(labels, "quality_warnings")} items={quality} tone="info" />
      {!errors.length && !warnings.length && !quality.length ? (
        <p className="nb-empty">{label(labels, "no_issues")}</p>
      ) : null}
    </div>
  );
}

function CheckList({ title, items, tone }) {
  if (!items.length) {
    return null;
  }
  return (
    <section className={`nb-check-list ${tone}`}>
      <strong>{title}</strong>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function ConnectedEditor() {
  const [args, setArgs] = useState({});

  useEffect(() => {
    Streamlit.setComponentReady();
    const onRender = (event) => {
      setArgs(event.detail.args || {});
    };
    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
    Streamlit.setFrameHeight();
    return () => {
      Streamlit.events.removeEventListener(Streamlit.RENDER_EVENT, onRender);
    };
  }, []);

  if (args.mode === "shell") {
    return <ShellEditor args={args} />;
  }
  return <LegacyMarkdownEditor args={args} />;
}

const root = createRoot(document.getElementById("root"));
root.render(<ConnectedEditor />);
