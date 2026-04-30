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
import { useCreateBlockNote } from "@blocknote/react";
import "@blocknote/core/fonts/inter.css";
import "@blocknote/mantine/style.css";
import "./style.css";

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
  ai_candidate: "Candidate",
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
  generate_candidate: "Generate candidate",
  generate_cover_image: "Generate cover candidate",
  generate_visual: "Generate visual asset",
  high_quality_preview: "High-quality preview",
  recent_visuals: "Recent generations",
  insert_candidate: "Insert",
  insert_at_cursor: "Recent cursor",
  insert_at_end: "End",
  insert_at_marker: "Marker",
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
  source_mode: "Source",
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
  video_edit: "Video edit",
  visual: "Visual",
  visual_alt_help: "Used as Markdown image alt text when inserted; covers use the post title.",
  visual_caption_help: "Shown as a body caption or video title; not used for covers.",
  visual_custom: "Custom",
  visual_default: "Default",
  visual_prompt: "Visual prompt",
  visual_prompt_suggestions: "Prompt suggestions",
  visual_provider: "Visual generation",
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

const RAW_MARKDOWN_DIRECTIVE_LINE_RE =
  /^::[A-Za-z][\w-]*\[[^\r\n\]]*\]\([^\r\n]+\)$/u;

function rawDirectiveLines(value) {
  return cleanText(value)
    .split(/\r?\n/u)
    .map((line) => line.trim())
    .filter(Boolean);
}

function containsRawMarkdownDirective(markdown) {
  return rawDirectiveLines(markdown).some((line) =>
    RAW_MARKDOWN_DIRECTIVE_LINE_RE.test(line),
  );
}

function isRawMarkdownDirective(snippet) {
  const lines = rawDirectiveLines(snippet);
  return (
    lines.length > 0 &&
    lines.every((line) => RAW_MARKDOWN_DIRECTIVE_LINE_RE.test(line))
  );
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
  useEffect(() => {
    const timer = window.setTimeout(() => {
      Streamlit.setFrameHeight(minimumHeight);
      Streamlit.setFrameHeight();
    }, 0);
    return () => window.clearTimeout(timer);
  }, deps);
}

function LegacyMarkdownEditor(props) {
  const args = props.args || {};
  const documentId = String(args.document_id || "blog");
  const initialMarkdown = markdownFromValue(args.initial_markdown);
  const height = Number(args.height || 560);
  const editable = args.editable !== false;
  const sourceMode = args.source_mode === true || args.math_safe === true;
  const editorSourceMode =
    sourceMode || containsRawMarkdownDirective(initialMarkdown);
  const editor = useCreateBlockNote({});
  const [sourceMarkdown, setSourceMarkdown] = useState(initialMarkdown);
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);
  const latestMarkdownRef = useRef(initialMarkdown);
  const loadedDocumentRef = useRef("");
  const loadedInitialMarkdownRef = useRef(null);
  const loadedSourceModeRef = useRef(null);
  const sendTimerRef = useRef(null);

  useEffect(() => {
    Streamlit.setFrameHeight(height + 34);
  }, [height]);

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
      if (editorSourceMode) {
        setSourceMarkdown(initialMarkdown || "");
        latestMarkdownRef.current = initialMarkdown || "";
        loadedDocumentRef.current = documentId;
        loadedInitialMarkdownRef.current = initialMarkdown;
        loadedSourceModeRef.current = editorSourceMode;
        Streamlit.setComponentValue({
          markdown: latestMarkdownRef.current,
          dirty: false,
          selected_block: null,
          insert_event: null,
        });
        setReady(true);
        Streamlit.setFrameHeight(height + 34);
        return;
      }
      try {
        const blocks = await editor.tryParseMarkdownToBlocks(initialMarkdown || "");
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
          selected_block: null,
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

  function sendLegacyValue(markdown, immediate = false) {
    latestMarkdownRef.current = markdown;
    const send = () => {
      Streamlit.setComponentValue({
        markdown,
        dirty: markdown !== (initialMarkdown || ""),
        selected_block: null,
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
      const markdown = await editor.blocksToMarkdownLossy(editor.document);
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
          className="nb-source-editor"
          value={sourceMarkdown}
          readOnly={!editable}
          onChange={(event) => {
            const next = event.target.value;
            setSourceMarkdown(next);
            sendLegacyValue(next, false);
          }}
          onBlur={() => sendLegacyValue(latestMarkdownRef.current, true)}
          style={{ minHeight: `${height}px` }}
        />
      ) : (
        <BlockNoteView
          editor={editor}
          editable={editable}
          theme="light"
          onChange={() => syncMarkdown(false)}
          onBlur={() => syncMarkdown(true)}
        />
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
  const previewHtml = cleanText(args.preview_html);
  const initialStatusFilter = cleanText(args.status_filter || "all") || "all";
  const activeSlug = cleanText(args.active_slug || args.slug || args.document_id || "");
  const documentId = String(args.document_id || activeSlug || "blog");
  const initialMarkdown = markdownFromValue(args.initial_markdown);
  const height = Number(args.height || 720);
  const editable = args.editable !== false;
  const sourceMode = args.source_mode === true || args.math_safe === true;
  const initialHasRawDirectives = containsRawMarkdownDirective(initialMarkdown);
  const layoutStorageKey = cleanText(
    args.layout_storage_key ||
      args.storage_key ||
      (documentId ? `public_blog_editor:${documentId}` : ""),
  );
  const editor = useCreateBlockNote({});
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [sourceMarkdown, setSourceMarkdown] = useState(initialMarkdown);
  const [rawDirectiveSourceDocumentId, setRawDirectiveSourceDocumentIdState] =
    useState(() => (initialHasRawDirectives ? documentId : ""));
  const [dirty, setDirty] = useState(false);
  const [mobileView, setMobileView] = useState("Editor");
  const [newPostTitle, setNewPostTitle] = useState("");
  const [evidenceId, setEvidenceId] = useState("");
  const [statusFilter, setStatusFilter] = useState(initialStatusFilter);
  const [layout, setLayoutState] = useState(() =>
    readStoredLayout(layoutStorageKey, normalizeLayout(args.layout_state)),
  );
  const [draftMeta, setDraftMetaState] = useState(() =>
    normalizeMeta(args.active_post_meta),
  );

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
  const rawDirectiveSourceDocumentIdRef = useRef(
    initialHasRawDirectives ? documentId : "",
  );
  const sourceTextareaRef = useRef(null);
  const sourceSelectionRef = useRef({ start: 0, end: 0 });
  const editorSourceMode =
    sourceMode ||
    initialHasRawDirectives ||
    rawDirectiveSourceDocumentId === documentId;

  const layoutSeed = deepStableStringify(args.layout_state || {});
  const metaSeed = deepStableStringify(args.active_post_meta || {});
  const visualSeed = deepStableStringify(args.visual_config || {});
  const visualResultsSeed = deepStableStringify(args.visual_results || []);
  const visualGuidanceSeed = deepStableStringify(args.visual_guidance || {});

  const setRawDirectiveSourceDocumentId = useCallback((nextDocumentId) => {
    rawDirectiveSourceDocumentIdRef.current = nextDocumentId;
    setRawDirectiveSourceDocumentIdState(nextDocumentId);
  }, []);

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
    setRawDirectiveSourceDocumentId(initialHasRawDirectives ? documentId : "");
  }, [documentId, initialHasRawDirectives, setRawDirectiveSourceDocumentId]);

  useEffect(() => {
    setStatusFilter(initialStatusFilter);
  }, [initialStatusFilter]);

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
        const blocks = await editor.tryParseMarkdownToBlocks(initialMarkdown || "");
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
    const preserveRawDirectives =
      rawDirectiveSourceDocumentIdRef.current === documentId ||
      initialHasRawDirectives;
    if (sourceMode || preserveRawDirectives) {
      return latestMarkdownRef.current;
    }
    try {
      const markdown = await editor.blocksToMarkdownLossy(editor.document);
      latestMarkdownRef.current = markdown;
      return markdown;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      return latestMarkdownRef.current;
    }
  }, [documentId, editor, initialHasRawDirectives, sourceMode]);

  const rememberCursorBlock = useCallback(() => {
    if (editorSourceMode) {
      return;
    }
    try {
      const block = editor.getTextCursorPosition()?.block || null;
      if (block?.id) {
        lastCursorBlockIdRef.current = block.id;
      }
    } catch (_err) {
      // BlockNote can throw after focus leaves the editor; keep the previous block id.
    }
  }, [editor, editorSourceMode]);

  const rememberSourceSelection = useCallback(() => {
    const textarea = sourceTextareaRef.current;
    if (!textarea) {
      return;
    }
    sourceSelectionRef.current = {
      start: textarea.selectionStart,
      end: textarea.selectionEnd,
    };
  }, []);

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

  const emitAction = useCallback(
    async (action, extraPayload = {}) => {
      if (!editable && WRITE_ACTIONS.has(action)) {
        return;
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
        selected_block: null,
        insert_event:
          action === "insert_candidate" || action === "insert_media"
            ? extraPayload
            : null,
      });
    },
    [activeSlug, computeDirty, documentId, editable, getCurrentMarkdown, nextEventId],
  );

  const syncMarkdown = useCallback(
    async () => {
      if (!ready || !editable) {
        return;
      }
      rememberCursorBlock();
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
      rememberCursorBlock,
      ready,
    ],
  );

  const replaceEditorMarkdown = useCallback(
    async (markdown, options = {}) => {
      latestMarkdownRef.current = markdown;
      setDirty(computeDirty(markdown, draftMetaRef.current));
      const preserveRawDirectives =
        options.preserveRawDirectives === true ||
        containsRawMarkdownDirective(markdown);
      if (preserveRawDirectives) {
        setRawDirectiveSourceDocumentId(documentId);
      }
      if (editorSourceMode || preserveRawDirectives) {
        setSourceMarkdown(markdown);
        return markdown;
      }
      const blocks = await editor.tryParseMarkdownToBlocks(markdown || "");
      editor.replaceBlocks(editor.document, blocks);
      return markdown;
    },
    [computeDirty, documentId, editor, editorSourceMode, setRawDirectiveSourceDocumentId],
  );

  const insertMarkdown = useCallback(
    async (snippet, placement = "cursor") => {
      const insertPlacement = normalizeInsertPlacement(placement);
      const cleanSnippet = cleanText(snippet).trim();
      if (!cleanSnippet) {
        return latestMarkdownRef.current;
      }
      const current = await getCurrentMarkdown();
      const rawDirective = isRawMarkdownDirective(cleanSnippet);
      if (editorSourceMode) {
        const next =
          insertPlacement === "cursor" || insertPlacement === "replace"
            ? insertMarkdownAtTextSelection(
                current,
                cleanSnippet,
                sourceSelectionRef.current,
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
        await replaceEditorMarkdown(next, { preserveRawDirectives: rawDirective });
        return next;
      }
      try {
        if (insertPlacement === "replace" && editor.getSelection()) {
          editor.removeBlocks(editor.getSelectionCutBlocks());
        }
        const blocks = await editor.tryParseMarkdownToBlocks(cleanSnippet);
        let referenceBlock = findBlockById(
          editor.document,
          lastCursorBlockIdRef.current,
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
        editor.insertBlocks(blocks, referenceBlock, "after");
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

  return (
    <main className={shellClasses} style={{ minHeight: `${height}px` }}>
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
            disabled={!editable}
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
            disabled={!editable}
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
                onSelect={rememberSourceSelection}
                onKeyUp={rememberSourceSelection}
                onMouseUp={rememberSourceSelection}
                onBlur={() => {
                  rememberSourceSelection();
                  syncMarkdown();
                }}
                style={{ minHeight: `${Math.max(360, height - 190)}px` }}
              />
            ) : (
              <div
                className="nb-blocknote-frame"
                style={{ minHeight: `${Math.max(360, height - 190)}px` }}
                onKeyUp={rememberCursorBlock}
                onMouseUp={rememberCursorBlock}
                onFocus={rememberCursorBlock}
              >
                <BlockNoteView
                  editor={editor}
                  editable={editable}
                  theme="light"
                  onChange={() => {
                    rememberCursorBlock();
                    syncMarkdown();
                  }}
                  onBlur={() => {
                    rememberCursorBlock();
                    syncMarkdown();
                  }}
                />
              </div>
            )}
          </div>
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
              onLoadFullPreview={(item) => handleLoadMediaPreviewDetail(item, "media")}
              onDelete={handleDeleteMedia}
              onConvertVideo={handleConvertMediaVideo}
            />
          ) : null}
          {activeRightTab === "AI" ? (
            <AiDrawer
              editable={editable}
              labels={labels}
              candidates={aiCandidates}
              onInsert={handleInsertCandidate}
              onApplyMeta={handleApplyCandidateMeta}
              onRun={(payload) => emitAction("generate_ai_candidate", payload)}
              currentTitle={currentTitle}
            />
          ) : null}
          {activeRightTab === "Visual" ? (
            <VisualDrawer
              editable={editable}
              labels={labels}
              visualConfig={visualConfig}
              visualResults={visualResults}
              visualGuidance={visualGuidance}
              onGenerate={handleGenerateVisual}
              onInsert={handleInsertMedia}
              onSetCover={handleSetCover}
              onSaveCandidate={handleSaveVisualCandidate}
              onDiscardCandidate={handleDiscardVisualCandidate}
              onLoadFullPreview={(item) => handleLoadMediaPreviewDetail(item, "visual")}
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
  onLoadFullPreview,
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
  const [selectedKey, setSelectedKey] = useState("");
  const keyedRows = mediaItems.map((item, index) => ({
    item,
    key: visualItemKey(item, index),
  }));
  const selected = keyedRows.find((row) => row.key === selectedKey)?.item || null;

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
                  onClick={() => setSelectedKey(key)}
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
                    onClick={() => setSelectedKey(key)}
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
      {selected ? (
        <VisualPreviewDialog
          item={selected}
          labels={labels}
          editable={editable}
          onClose={() => setSelectedKey("")}
          onInsert={onInsert}
          onSetCover={onSetCover}
          onSaveCandidate={() => {}}
          onDiscardCandidate={() => {}}
          onLoadFullPreview={onLoadFullPreview}
          onConvertVideo={onConvertVideo}
        />
      ) : null}
    </div>
  );
}

function AiDrawer({
  editable,
  labels,
  candidates,
  onInsert,
  onApplyMeta,
  onRun,
  currentTitle,
}) {
  const [evidenceId, setEvidenceId] = useState("");
  return (
    <div className="nb-drawer-body">
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
                  <button
                    type="button"
                    className="nb-button"
                    disabled={!editable}
                    onClick={() => onInsert(candidate, index, "marker")}
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
  onLoadFullPreview,
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
  return (
    <div className="nb-preview-dialog" role="dialog" aria-modal="true">
      <div className="nb-preview-dialog-panel">
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
  onLoadFullPreview,
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
  onLoadFullPreview,
}) {
  const rows = asArray(items).map(asObject);
  const [selectedKey, setSelectedKey] = useState("");
  const keyedRows = rows.map((item, index) => ({
    item,
    key: visualItemKey(item, index),
  }));
  const selected = keyedRows.find((row) => row.key === selectedKey)?.item || null;
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
          onOpenPreview={() => setSelectedKey(key)}
          onInsert={onInsert}
          onSetCover={onSetCover}
          onSaveCandidate={onSaveCandidate}
          onDiscardCandidate={onDiscardCandidate}
        />
      ))}
      {selected ? (
        <VisualPreviewDialog
          item={selected}
          labels={labels}
          editable={editable}
          onClose={() => setSelectedKey("")}
          onInsert={onInsert}
          onSetCover={onSetCover}
          onSaveCandidate={onSaveCandidate}
          onDiscardCandidate={onDiscardCandidate}
          onLoadFullPreview={onLoadFullPreview}
        />
      ) : null}
    </section>
  );
}

function VisualDrawer({
  editable,
  labels,
  visualConfig,
  visualResults,
  visualGuidance,
  onGenerate,
  onInsert,
  onSetCover,
  onSaveCandidate,
  onDiscardCandidate,
  onLoadFullPreview,
}) {
  const [assetType, setAssetType] = useState("cover");
  const [prompt, setPrompt] = useState("");
  const [styleChoice, setStyleChoice] = useState("");
  const [customStyle, setCustomStyle] = useState("");
  const [sizeChoice, setSizeChoice] = useState("");
  const [customSize, setCustomSize] = useState("");
  const [alt, setAlt] = useState("");
  const [caption, setCaption] = useState("");
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
        disabled={!editable || !configured || !prompt.trim()}
        onClick={() =>
          onGenerate({
            asset_type: assetType,
            prompt: prompt.trim(),
            style: selectedStyle,
            size: selectedSize,
            alt,
            caption,
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
        onLoadFullPreview={onLoadFullPreview}
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
