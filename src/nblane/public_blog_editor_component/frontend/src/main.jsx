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

const RIGHT_TABS = ["Meta", "Media", "AI", "Check"];
const STATUS_OPTIONS = ["draft", "published", "archived"];
const INSERT_MARKER = "<!-- nblane:insert -->";

const DEFAULT_LABELS = {
  add_media: "Add media",
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
  date: "Date",
  draft: "draft",
  editor: "Editor",
  exit_focus: "Exit focus",
  focus_mode: "Focus",
  generate_candidate: "Generate candidate",
  insert_candidate: "Insert",
  insert_into_post: "Insert",
  layout: "Layout",
  left_panel: "Articles",
  media: "Media",
  media_library: "Media library",
  meta: "Meta",
  no_issues: "No issues.",
  no_media: "No media.",
  post: "Post",
  publish: "Publish",
  published: "published",
  raw_yaml: "Markdown source",
  related_evidence: "Related evidence",
  related_kanban: "Related kanban",
  right_panel: "Tools",
  run_check: "Run check",
  save: "Save",
  selected_media: "Selected media",
  source_mode: "Source",
  status: "Status",
  summary: "Summary",
  tags: "Tags",
  title_label: "Title",
  tools: "Tools",
  validate: "Check",
  validation_errors: "Errors",
  validation_warnings: "Warnings",
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
  if (next.focus_mode) {
    next.left_open = false;
    next.right_open = false;
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
  for (const key of [
    "title",
    "date",
    "status",
    "summary",
    "cover",
    "related_evidence",
    "related_kanban",
  ]) {
    if (meta[key] === null || meta[key] === undefined) {
      meta[key] = "";
    }
  }
  if (!Array.isArray(meta.tags)) {
    meta.tags = cleanText(meta.tags)
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
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
  return meta;
}

function insertMarkdownText(markdown, snippet, placement = "cursor") {
  const cleanSnippet = cleanText(snippet).trim();
  if (!cleanSnippet) {
    return markdown;
  }
  const source = cleanText(markdown);
  if (source.includes(INSERT_MARKER) && placement !== "append") {
    return source.replace(INSERT_MARKER, `${cleanSnippet}\n\n${INSERT_MARKER}`);
  }
  const base = source.trimEnd();
  if (!base) {
    return `${cleanSnippet}\n`;
  }
  return `${base}\n\n${cleanSnippet}\n`;
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
        loadedSourceModeRef.current === sourceMode
      ) {
        return;
      }
      setReady(false);
      setError("");
      if (sourceMode) {
        setSourceMarkdown(initialMarkdown || "");
        latestMarkdownRef.current = initialMarkdown || "";
        loadedDocumentRef.current = documentId;
        loadedInitialMarkdownRef.current = initialMarkdown;
        loadedSourceModeRef.current = sourceMode;
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
        loadedSourceModeRef.current = sourceMode;
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
  }, [documentId, editor, height, initialMarkdown, sourceMode]);

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
    if (sourceMode) {
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
      {sourceMode ? (
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
  const activeSlug = cleanText(args.active_slug || args.slug || args.document_id || "");
  const documentId = String(args.document_id || activeSlug || "blog");
  const initialMarkdown = markdownFromValue(args.initial_markdown);
  const height = Number(args.height || 720);
  const editable = args.editable !== false;
  const sourceMode = args.source_mode === true || args.math_safe === true;
  const layoutStorageKey = cleanText(
    args.layout_storage_key ||
      args.storage_key ||
      (documentId ? `public_blog_editor:${documentId}` : ""),
  );
  const editor = useCreateBlockNote({});
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [sourceMarkdown, setSourceMarkdown] = useState(initialMarkdown);
  const [dirty, setDirty] = useState(false);
  const [mobileView, setMobileView] = useState("Editor");
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
  const sendTimerRef = useRef(null);

  const layoutSeed = deepStableStringify(args.layout_state || {});
  const metaSeed = deepStableStringify(args.active_post_meta || {});

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
      sourceMode,
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
    let cancelled = false;
    async function loadMarkdown() {
      if (
        loadedDocumentRef.current === documentId &&
        loadedInitialMarkdownRef.current === initialMarkdown &&
        loadedSourceModeRef.current === sourceMode
      ) {
        return;
      }
      setReady(false);
      setError("");
      if (sourceMode) {
        setSourceMarkdown(initialMarkdown || "");
        latestMarkdownRef.current = initialMarkdown || "";
        loadedDocumentRef.current = documentId;
        loadedInitialMarkdownRef.current = initialMarkdown;
        loadedSourceModeRef.current = sourceMode;
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
        loadedSourceModeRef.current = sourceMode;
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
  }, [documentId, editor, initialMarkdown, sourceMode]);

  useEffect(() => {
    return () => {
      if (sendTimerRef.current !== null) {
        window.clearTimeout(sendTimerRef.current);
      }
    };
  }, []);

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
      const markdown = await editor.blocksToMarkdownLossy(editor.document);
      latestMarkdownRef.current = markdown;
      return markdown;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      return latestMarkdownRef.current;
    }
  }, [editor, sourceMode]);

  const emitAction = useCallback(
    async (action, extraPayload = {}) => {
      const markdown = await getCurrentMarkdown();
      const payload = {
        slug: activeSlug,
        document_id: documentId,
        markdown,
        meta: draftMetaRef.current,
        layout_state: layoutRef.current,
        dirty: computeDirty(markdown, draftMetaRef.current),
        ...extraPayload,
      };
      Streamlit.setComponentValue({
        action,
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
    [activeSlug, computeDirty, documentId, getCurrentMarkdown],
  );

  const updateLayout = useCallback(
    (updater, action = "layout_state_changed") => {
      const next = normalizeLayout(
        typeof updater === "function" ? updater(layoutRef.current) : updater,
      );
      layoutRef.current = next;
      setLayoutState(next);
      persistLayout(layoutStorageKey, next);
      emitAction(action, { layout_state: next });
      return next;
    },
    [emitAction, layoutStorageKey],
  );

  const syncMarkdown = useCallback(
    async (immediate = false) => {
      if (!ready) {
        return;
      }
      const markdown = sourceMode
        ? latestMarkdownRef.current
        : await getCurrentMarkdown();
      const nextDirty = computeDirty(markdown, draftMetaRef.current);
      setDirty(nextDirty);
      if (sendTimerRef.current !== null) {
        window.clearTimeout(sendTimerRef.current);
      }
      if (!immediate) {
        sendTimerRef.current = window.setTimeout(() => {
          Streamlit.setComponentValue({
            action: "markdown_changed",
            payload: {
              slug: activeSlug,
              document_id: documentId,
              markdown,
              meta: draftMetaRef.current,
              layout_state: layoutRef.current,
              dirty: nextDirty,
            },
            markdown,
            dirty: nextDirty,
            layout_state: layoutRef.current,
            selected_block: null,
            insert_event: null,
          });
        }, 900);
        return;
      }
      Streamlit.setComponentValue({
        action: "markdown_changed",
        payload: {
          slug: activeSlug,
          document_id: documentId,
          markdown,
          meta: draftMetaRef.current,
          layout_state: layoutRef.current,
          dirty: nextDirty,
        },
        markdown,
        dirty: nextDirty,
        layout_state: layoutRef.current,
        selected_block: null,
        insert_event: null,
      });
    },
    [activeSlug, computeDirty, documentId, getCurrentMarkdown, ready, sourceMode],
  );

  const replaceEditorMarkdown = useCallback(
    async (markdown) => {
      latestMarkdownRef.current = markdown;
      setDirty(computeDirty(markdown, draftMetaRef.current));
      if (sourceMode) {
        setSourceMarkdown(markdown);
        return markdown;
      }
      const blocks = await editor.tryParseMarkdownToBlocks(markdown || "");
      editor.replaceBlocks(editor.document, blocks);
      return markdown;
    },
    [computeDirty, editor, sourceMode],
  );

  const insertMarkdown = useCallback(
    async (snippet, placement = "cursor") => {
      const cleanSnippet = cleanText(snippet).trim();
      if (!cleanSnippet) {
        return latestMarkdownRef.current;
      }
      const current = await getCurrentMarkdown();
      if (current.includes(INSERT_MARKER) || sourceMode || placement === "append") {
        const next = insertMarkdownText(current, cleanSnippet, placement);
        await replaceEditorMarkdown(next);
        return next;
      }
      try {
        if (placement === "replace" && editor.getSelection()) {
          editor.removeBlocks(editor.getSelectionCutBlocks());
        }
        if (typeof editor.pasteMarkdown === "function") {
          await editor.pasteMarkdown(cleanSnippet);
        } else {
          const blocks = await editor.tryParseMarkdownToBlocks(cleanSnippet);
          const lastBlock = editor.document[editor.document.length - 1];
          editor.insertBlocks(blocks, lastBlock, "after");
        }
        return await getCurrentMarkdown();
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setError(message);
        const next = insertMarkdownText(current, cleanSnippet, placement);
        await replaceEditorMarkdown(next);
        return next;
      }
    },
    [editor, getCurrentMarkdown, replaceEditorMarkdown, sourceMode],
  );

  function toggleFocusMode() {
    updateLayout((current) => {
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
        left_open: false,
        right_open: false,
      };
    });
  }

  function toggleRightTab(tab) {
    updateLayout((current) => {
      if (current.right_open && current.active_right_tab === tab) {
        return { ...current, right_open: false, focus_mode: false };
      }
      return {
        ...current,
        right_open: true,
        active_right_tab: tab,
        focus_mode: false,
      };
    });
    setMobileView("Tools");
  }

  function updateMetaText(key, value) {
    setDraftMeta({ [key]: value });
  }

  function updateMetaList(key, value) {
    setDraftMeta({ [key]: listFromCsv(value) });
  }

  async function handleInsertCandidate(candidate, placement = "cursor") {
    const body = candidateBody(candidate);
    const id = candidateId(candidate, 0);
    const markdown = await insertMarkdown(body, placement);
    await emitAction("insert_candidate", {
      candidate_id: id,
      candidate,
      placement,
      markdown,
    });
  }

  async function handleInsertMedia(item) {
    const snippet = mediaSnippet(item);
    const markdown = await insertMarkdown(snippet, "cursor");
    await emitAction("insert_media", {
      media: item,
      snippet,
      markdown,
    });
  }

  async function handleApplyCandidateMeta(candidate) {
    const metaPatch = candidateMeta(candidate);
    const nextMeta = setDraftMeta((current) => ({ ...current, ...metaPatch }));
    await emitAction("apply_candidate_meta", {
      candidate_id: candidateId(candidate, 0),
      candidate,
      meta_patch: metaPatch,
      meta: nextMeta,
    });
  }

  async function handleSetCover(item) {
    const cover = mediaPath(item);
    const nextMeta = setDraftMeta({ cover });
    await emitAction("apply_candidate_meta", {
      source: "media",
      media: item,
      meta_patch: { cover },
      meta: nextMeta,
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
            onClick={() => emitAction("run_check")}
          >
            {label(labels, "validate", "Check")}
          </button>
          <button
            type="button"
            className="nb-button"
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
              updateLayout((current) => ({
                ...current,
                left_open: !current.left_open,
                focus_mode: false,
              }));
              setMobileView("Articles");
            }}
          >
            A
          </button>
          <button
            type="button"
            className="nb-icon-button"
            title={label(labels, "right_panel")}
            onClick={() => {
              updateLayout((current) => ({
                ...current,
                right_open: !current.right_open,
                focus_mode: false,
              }));
              setMobileView("Tools");
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
        {["Editor", "Articles", "Tools"].map((tab) => (
          <button
            type="button"
            key={tab}
            className={mobileView === tab ? "is-active" : ""}
            onClick={() => setMobileView(tab)}
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
              title={label(labels, "left_panel")}
              onClick={() =>
                updateLayout((current) => ({
                  ...current,
                  left_open: false,
                  focus_mode: false,
                }))
              }
            >
              L
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
          <div className="nb-title-editor">
            <label htmlFor="nb-title-input">{label(labels, "title_label")}</label>
            <input
              id="nb-title-input"
              value={cleanText(draftMeta.title)}
              readOnly={!editable}
              onChange={(event) => updateMetaText("title", event.target.value)}
            />
          </div>
          {sourceMode ? (
            <textarea
              className="nb-source-editor"
              value={sourceMarkdown}
              readOnly={!editable}
              onChange={(event) => {
                const next = event.target.value;
                setSourceMarkdown(next);
                latestMarkdownRef.current = next;
                setDirty(computeDirty(next, draftMetaRef.current));
                syncMarkdown(false);
              }}
              onBlur={() => syncMarkdown(true)}
              style={{ minHeight: `${Math.max(360, height - 190)}px` }}
            />
          ) : (
            <div
              className="nb-blocknote-frame"
              style={{ minHeight: `${Math.max(360, height - 190)}px` }}
            >
              <BlockNoteView
                editor={editor}
                editable={editable}
                theme="light"
                onChange={() => syncMarkdown(false)}
                onBlur={() => syncMarkdown(true)}
              />
            </div>
          )}
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
                onClick={() => toggleRightTab(tab)}
              >
                {label(labels, tab.toLowerCase())}
              </button>
            ))}
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
              labels={labels}
              mediaItems={mediaItems}
              onInsert={handleInsertMedia}
              onSetCover={handleSetCover}
            />
          ) : null}
          {activeRightTab === "AI" ? (
            <AiDrawer
              labels={labels}
              candidates={aiCandidates}
              onInsert={handleInsertCandidate}
              onApplyMeta={handleApplyCandidateMeta}
              onRun={() => emitAction("generate_ai_candidate", { source: "ai" })}
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

function MediaDrawer({ labels, mediaItems, onInsert, onSetCover }) {
  return (
    <div className="nb-drawer-body">
      <div className="nb-panel-title">{label(labels, "media_library")}</div>
      {mediaItems.length ? (
        <div className="nb-media-list">
          {mediaItems.map((item, index) => {
            const path = mediaPath(item);
            const kind = cleanText(item.kind || item.type || "media");
            return (
              <article className="nb-media-row" key={`${path}-${index}`}>
                <div>
                  <strong>{cleanText(item.name || path || label(labels, "media"))}</strong>
                  <span>
                    {kind}
                    {item.referenced === false ? " / unused" : ""}
                  </span>
                </div>
                <div className="nb-row-actions">
                  <button type="button" className="nb-button" onClick={() => onInsert(item)}>
                    {label(labels, "insert_into_post")}
                  </button>
                  <button
                    type="button"
                    className="nb-button"
                    disabled={kind !== "image" && !/\.(png|jpe?g|gif|webp|avif)$/i.test(path)}
                    onClick={() => onSetCover(item)}
                  >
                    {label(labels, "cover")}
                  </button>
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

function AiDrawer({ labels, candidates, onInsert, onApplyMeta, onRun }) {
  return (
    <div className="nb-drawer-body">
      <button type="button" className="nb-button wide" onClick={onRun}>
        {label(labels, "generate_candidate")}
      </button>
      {candidates.length ? (
        <div className="nb-candidate-list">
          {candidates.map((candidate, index) => {
            const meta = candidateMeta(candidate);
            const body = candidateBody(candidate);
            return (
              <article className="nb-candidate" key={candidateId(candidate, index)}>
                <div className="nb-candidate-title">
                  {cleanText(candidate.title || meta.title || label(labels, "ai_candidate"))}
                </div>
                {meta.summary ? <p>{cleanText(meta.summary)}</p> : null}
                {body ? <pre>{body.slice(0, 420)}</pre> : null}
                <div className="nb-row-actions">
                  <button
                    type="button"
                    className="nb-button"
                    onClick={() => onInsert(candidate, "cursor")}
                  >
                    {label(labels, "insert_candidate")}
                  </button>
                  <button
                    type="button"
                    className="nb-button"
                    onClick={() => onInsert(candidate, "append")}
                  >
                    {label(labels, "append_candidate")}
                  </button>
                  <button
                    type="button"
                    className="nb-button"
                    onClick={() => onApplyMeta(candidate)}
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

function CheckDrawer({ labels, state, onRun }) {
  const errors = asArray(state.errors).map(cleanText).filter(Boolean);
  const warnings = asArray(state.warnings).map(cleanText).filter(Boolean);
  const quality = asArray(state.quality).map(cleanText).filter(Boolean);
  return (
    <div className="nb-drawer-body">
      <button type="button" className="nb-button wide" onClick={onRun}>
        {label(labels, "validate", "Check")}
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
