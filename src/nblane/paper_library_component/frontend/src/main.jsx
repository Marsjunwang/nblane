import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Streamlit } from "streamlit-component-lib";

import "./style.css";
import {
  asArray,
  cleanText,
  expandableIds,
  filterItems,
  nodeId,
  nodeTitle,
  nodeType,
  normalizePayload,
} from "./payload.js";

function eventId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function label(labels, key, fallback) {
  return cleanText(labels?.[key]) || fallback;
}

function makeEvent(action, payload = {}) {
  return {
    action,
    event_id: eventId(),
    payload,
  };
}

const TRANSLATION_MODE_DEFAULT = "fast_body";

function translationModePayload(paperIds, mode) {
  const cleanMode = cleanText(mode) || TRANSLATION_MODE_DEFAULT;
  const base = {
    paper_ids: paperIds,
    mode: "missing_or_stale",
    translation_variant: cleanMode,
  };
  if (cleanMode === "full_paper") {
    return {
      ...base,
      scope_strategy: "structure",
      include_references: true,
    };
  }
  if (cleanMode === "grobid_text") {
    return {
      ...base,
      scope_strategy: "segment",
      include_references: false,
    };
  }
  return {
    ...base,
    scope_strategy: "structure",
    include_references: false,
  };
}

const WORKSPACE_JOB_POLL_TIMEOUT_MS = 45000;
const WORKSPACE_JOB_MAX_STATUS_MISSES = 4;
const WORKSPACE_JOB_RECONNECT_GRACE_MS = 180000;

function isTransientWorkspaceJobPollError(error) {
  const message = cleanText(error?.message || error);
  return (
    message.includes("Request timed out after") ||
    message.includes("Failed to fetch") ||
    message.includes("NetworkError")
  );
}

function isWorkspaceJobLostError(error) {
  const message = cleanText(error?.message || error).toLowerCase();
  return message.includes("event job not found") || message.includes("request failed: 404");
}

function workspaceJobSavedProgressText(job) {
  if (!job || typeof job !== "object") {
    return "";
  }
  const updated = Number(job.updated || 0);
  const processed = Number(job.segments_processed || 0);
  const selected = Number(job.segments_selected || 0);
  if (updated > 0 && selected > 0) {
    return `${updated} updated, ${processed}/${selected} processed`;
  }
  if (updated > 0) {
    return `${updated} updated`;
  }
  if (processed > 0 && selected > 0) {
    return `${processed}/${selected} processed`;
  }
  return "";
}

function deepLinkActionLabel(payload, action) {
  const labels = payload.labels || {};
  const actions = {
    open_reader: label(labels, "open_reader", "Open Reader"),
    run_extraction: label(labels, "run_extraction", "Run extraction"),
    force_grobid_upgrade: label(labels, "force_grobid_upgrade", "Force GROBID upgrade"),
    auto_chunk: label(labels, "auto_chunk", "Auto chunk"),
    attach_pdf: label(labels, "attach_pdf", "Attach PDF"),
    review_claims: label(labels, "review_claims", "Review claims"),
    fix_citations: label(labels, "fix_citations", "Fix citations"),
    retry_translation: label(labels, "retry_translation", "Retry translation"),
    review_visibility: label(labels, "review_visibility", "Review visibility"),
    review_metadata: label(labels, "review_metadata", "Review metadata"),
    dedupe: label(labels, "dedupe", "Review duplicates"),
  };
  return actions[action] || action.replaceAll("_", " ");
}

function eventBusyNotice(payload, event) {
  const action = cleanText(event?.action);
  if (action === "paper_library_run_extraction") {
    if (event?.payload?.force_grobid) {
      return label(payload.labels, "running_grobid_upgrade", "Upgrading with GROBID...");
    }
    return label(payload.labels, "running_extraction", "Running extraction...");
  }
  if (action === "paper_library_retry_translation") {
    return label(payload.labels, "retrying_translation", "Retrying translation...");
  }
  if (action === "paper_library_download_pdf") {
    return label(payload.labels, "downloading_pdf", "Downloading PDF...");
  }
  return "";
}

function currentUrlQuery() {
  if (typeof window === "undefined") {
    return "";
  }
  return cleanText(new URLSearchParams(window.location.search).get("query"));
}

function paperMatchesQuery(paper, query) {
  const cleanQuery = cleanText(query).toLowerCase();
  if (!cleanQuery) {
    return true;
  }
  const haystack = [
    paper?.title,
    paper?.meta,
    paper?.summary,
    paper?.notes,
    paper?.tree_path,
    paper?.status_label,
    paper?.metrics,
    ...asArray(paper?.tags),
    ...asArray(paper?.badges),
  ]
    .map(cleanText)
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return haystack.includes(cleanQuery);
}

function runtimeMode() {
  const bootstrap = window.__NBLANE_PAPER_LIBRARY_BOOTSTRAP__;
  return cleanText(bootstrap?.runtime) || "streamlit";
}

function bootstrapProfile() {
  const bootstrap = window.__NBLANE_PAPER_LIBRARY_BOOTSTRAP__;
  const fromBootstrap = cleanText(bootstrap?.profile);
  if (fromBootstrap) {
    return fromBootstrap;
  }
  return cleanText(new URLSearchParams(window.location.search).get("profile"));
}

function paperLibraryApiUrl(profile, suffix = "") {
  const encoded = encodeURIComponent(profile);
  return `/api/research/${encoded}/paper-library${suffix}`;
}

function paperApiUrl(profile, sourceId, suffix = "") {
  return `/api/research/${encodeURIComponent(profile)}/papers/${encodeURIComponent(sourceId)}${suffix}`;
}

function safeReturnHref(value, fallback = "/Research") {
  const clean = cleanText(value).trim();
  if (!clean) {
    return fallback;
  }
  if (clean.startsWith("/") && !clean.startsWith("//")) {
    return clean;
  }
  try {
    const url = new URL(clean, window.location.origin);
    if (url.protocol === "http:" || url.protocol === "https:") {
      return url.toString();
    }
  } catch {
    return fallback;
  }
  return fallback;
}

async function jsonRequest(url, options = {}) {
  const { timeoutMs = 60000, headers = {}, signal, ...fetchOptions } = options;
  const controller = signal ? null : new AbortController();
  const timer = controller
    ? window.setTimeout(() => controller.abort(), Math.max(1000, Number(timeoutMs) || 60000))
    : null;
  const response = await fetch(url, {
    credentials: "same-origin",
    ...fetchOptions,
    signal: signal || controller.signal,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  }).catch((error) => {
    if (error?.name === "AbortError") {
      throw new Error(`Request timed out after ${Math.round((Number(timeoutMs) || 60000) / 1000)}s.`);
    }
    throw error;
  }).finally(() => {
    if (timer) {
      window.clearTimeout(timer);
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload?.ok === false) {
    throw new Error(payload?.detail || payload?.message || payload?.error || `Request failed: ${response.status}`);
  }
  return payload;
}

async function formRequest(url, formData, options = {}) {
  const { timeoutMs = 180000, signal, ...fetchOptions } = options;
  const controller = signal ? null : new AbortController();
  const timer = controller
    ? window.setTimeout(() => controller.abort(), Math.max(1000, Number(timeoutMs) || 180000))
    : null;
  const response = await fetch(url, {
    credentials: "same-origin",
    method: "POST",
    ...fetchOptions,
    signal: signal || controller.signal,
    body: formData,
  }).catch((error) => {
    if (error?.name === "AbortError") {
      throw new Error(`Request timed out after ${Math.round((Number(timeoutMs) || 180000) / 1000)}s.`);
    }
    throw error;
  }).finally(() => {
    if (timer) {
      window.clearTimeout(timer);
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload?.ok === false) {
    throw new Error(payload?.detail || payload?.message || payload?.error || `Request failed: ${response.status}`);
  }
  return payload;
}

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function optionalPositiveSeconds(value) {
  const clean = cleanText(value);
  if (!clean) {
    return null;
  }
  const number = Number(clean);
  if (!Number.isFinite(number) || number <= 0) {
    return null;
  }
  return number;
}

function updateUrlParams(next) {
  const url = new URL(window.location.href);
  for (const [key, value] of Object.entries(next)) {
    const clean = cleanText(value);
    if (clean) {
      url.searchParams.set(key, clean);
    } else {
      url.searchParams.delete(key);
    }
  }
  window.history.replaceState({}, "", url);
}

function collectionOptionsFromPayload(payload) {
  const rows = [{ id: "", title: label(payload.labels, "unsorted_inbox", "Unsorted Inbox") }];
  const visit = (items, depth = 0) => {
    for (const item of asArray(items)) {
      const type = nodeType(item);
      if (type === "collection") {
        rows.push({
          id: nodeId(item),
          title: `${"\u00a0\u00a0".repeat(depth)}${nodeTitle(item)}`,
        });
      }
      visit(item.children, depth + 1);
    }
  };
  for (const section of asArray(payload.sections)) {
    if (cleanText(section.id) === "collections") {
      visit(section.items, 0);
    }
  }
  return rows;
}

function searchStepText(step) {
  const stage = cleanText(step?.stage || "search");
  const name = cleanText(step?.provider || step?.backend || step?.query);
  const accepted = cleanText(step?.accepted_count);
  const raw = cleanText(step?.raw_count);
  const elapsed = cleanText(step?.elapsed_ms);
  const status = step?.ok === false ? "failed" : "ok";
  const counts = accepted || raw ? `${accepted || 0}/${raw || accepted || 0} kept` : "";
  return [stage, name, status, counts, elapsed ? `${elapsed} ms` : ""].filter(Boolean).join(" · ");
}

function searchEventText(event) {
  const phase = cleanText(event?.phase || event?.event || "search");
  const message = cleanText(event?.message);
  const stream = cleanText(event?.stream);
  const outputKind = cleanText(event?.output_kind);
  const detail = cleanText(event?.detail);
  const elapsedMs = Number(event?.elapsed_ms || 0);
  const elapsed = elapsedMs > 0 ? `${Math.round(elapsedMs / 1000)}s` : "";
  if (event?.step && typeof event.step === "object") {
    return searchStepText(event.step);
  }
  if (outputKind === "web_search") {
    return ["web search", message || detail, elapsed].filter(Boolean).join(" · ");
  }
  if (outputKind === "structured_result") {
    return ["organizing", message, elapsed].filter(Boolean).join(" · ");
  }
  if (outputKind === "plugin_warning") {
    return ["codex setup", message, elapsed].filter(Boolean).join(" · ");
  }
  if (outputKind === "usage") {
    return ["codex usage", message, elapsed].filter(Boolean).join(" · ");
  }
  if (event?.event === "output") {
    return [phase, message, elapsed].filter(Boolean).join(" · ");
  }
  return [phase, stream, message, elapsed].filter(Boolean).join(" · ");
}

function searchProgressText(progress) {
  const status = cleanText(progress?.status || "running");
  const phase = cleanText(progress?.phase || "search");
  const elapsedMs = Number(progress?.elapsed_ms || 0);
  const timeoutSeconds = Number(progress?.timeout_seconds || 0);
  const budgetMode = cleanText(progress?.budget_mode || progress?.codex_budget_mode);
  const transport = cleanText(progress?.transport);
  const elapsed = elapsedMs > 0 ? `${Math.round(elapsedMs / 1000)}s` : "";
  const timeout = budgetMode === "manual" && timeoutSeconds > 0 ? `max ${Math.round(timeoutSeconds)}s` : "";
  const budget = budgetMode === "auto" ? "adaptive" : "";
  const live = transport === "stream" ? "live" : "";
  return [status, phase, elapsed, live, budget, timeout].filter(Boolean).join(" · ");
}

function workspaceProgressText(progress) {
  const status = cleanText(progress?.status || "running");
  const phase = cleanText(progress?.phase || "action");
  const elapsedMs = Number(progress?.elapsed_ms || 0);
  const elapsed = elapsedMs > 0 ? `${Math.round(elapsedMs / 1000)}s` : "";
  const batches = Number(progress?.batches || 0);
  const batchesCompleted = Number(progress?.batches_completed || 0);
  const batchText = batches > 0 ? `${Math.min(batchesCompleted, batches)}/${batches} batches` : "";
  const stepTotal = Number(progress?.step_total || 0);
  const stepCurrent = Number(progress?.step_current || 0);
  const stepText = stepTotal > 0 ? `${Math.min(stepCurrent, stepTotal)}/${stepTotal} steps` : "";
  const selected = Number(progress?.segments_selected || 0);
  const processed = Number(progress?.segments_processed || 0);
  const segmentText = selected > 0 ? `${Math.min(processed, selected)}/${selected} units` : "";
  return [status, phase, elapsed, batchText || stepText, segmentText].filter(Boolean).join(" · ");
}

function workspaceProgressPercent(progress) {
  const batches = Number(progress?.batches || 0);
  const batchesCompleted = Number(progress?.batches_completed || 0);
  if (batches > 0) {
    return Math.max(6, Math.min(100, (batchesCompleted / batches) * 100));
  }
  const stepTotal = Number(progress?.step_total || 0);
  const stepCurrent = Number(progress?.step_current || 0);
  if (stepTotal > 0) {
    return Math.max(6, Math.min(100, (stepCurrent / stepTotal) * 100));
  }
  const status = cleanText(progress?.status);
  if (status === "done") {
    return 100;
  }
  if (status === "failed") {
    return 100;
  }
  return 14;
}

function isJobRunning(job) {
  const status = cleanText(job?.status);
  return status === "queued" || status === "running" || status === "starting" || status === "cancelling";
}

function shouldRunEventAsJob(event) {
  const action = cleanText(event?.action);
  return (
    action === "paper_library_retry_translation" ||
    action === "paper_library_run_extraction" ||
    action === "paper_library_download_pdf"
  );
}

function codexReasoningEffort(depth) {
  return depth === "deep" ? "xhigh" : "high";
}

function codexBudgetLabel(depth, maxSeconds = "") {
  const manualMax = optionalPositiveSeconds(maxSeconds);
  const budget = manualMax ? `manual max ${Math.round(manualMax)}s` : "adaptive";
  return `Codex ${codexReasoningEffort(depth)} · ${budget}`;
}

function candidateMeta(candidate) {
  return [
    cleanText(candidate.year),
    cleanText(candidate.venue),
    asArray(candidate.authors).slice(0, 3).map(cleanText).filter(Boolean).join(", "),
    asArray(candidate.provider_refs).slice(0, 3).map(cleanText).filter(Boolean).join(", "),
  ].filter(Boolean).join(" · ");
}

function candidateHasPdf(candidate) {
  return Boolean(cleanText(candidate.pdf_url || candidate.open_access_pdf_url));
}

function candidateExplanationLinks(candidate) {
  const seen = new Set();
  return asArray(candidate?.explanation_links)
    .filter((item) => item && typeof item === "object")
    .map((item) => {
      const url = cleanText(item.url || item.link);
      const title = cleanText(item.title || item.name || url);
      const source = cleanText(item.source || item.site || item.platform);
      const summary = cleanText(item.summary || item.note || item.why);
      return { url, title, source, summary };
    })
    .filter((item) => {
      if (!item.url || seen.has(item.url)) {
        return false;
      }
      seen.add(item.url);
      return true;
    })
    .slice(0, 6);
}

const optionalArtifactKeys = new Set([
  "grobid_last_error",
  "grobid_last_failed_at",
  "structured_extracted_at",
  "open_access_pdf_url",
  "pdf_download_status",
  "pdf_download_error",
  "pdf_download_attempted_at",
]);

function artifactLabel(labels, key) {
  return label(labels, `artifact_${key}`, key.replaceAll("_", " "));
}

function artifactEntries(artifacts) {
  return Object.entries(artifacts || {}).filter(([key, value]) => {
    if (!optionalArtifactKeys.has(key)) {
      return true;
    }
    return Boolean(cleanText(value));
  });
}

function ContextMenu({ menu, payload, onClose, onAction }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!menu) {
      return undefined;
    }
    const onPointer = (event) => {
      if (!ref.current?.contains(event.target)) {
        onClose();
      }
    };
    const onKey = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("pointerdown", onPointer);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("pointerdown", onPointer);
      window.removeEventListener("keydown", onKey);
    };
  }, [menu, onClose]);

  if (!menu) {
    return null;
  }
  const item = menu.item || {};
  const type = nodeType(item);
  const id = nodeId(item);
  const paperIds = asArray(menu.paperIds || (type === "paper" ? [id] : []))
    .map(cleanText)
    .filter(Boolean);
  const selectedCount = payload.selectedPaperIds.length;
  const canCollections = payload.capabilities.create_collection !== false;
  const canDropPapers = payload.capabilities.drop_papers !== false;
  const rows = [];
  const addRow = (key, text, action, disabled = false, danger = false) => {
    rows.push({ key, text, action, disabled, danger });
  };

  if (type === "collection_root") {
    addRow(
      "create",
      label(payload.labels, "new_collection", "New collection"),
      () => onAction("dialog:create", { parent_id: "" }),
      !canCollections,
    );
    addRow(
      "move-selected-root",
      label(payload.labels, "move_selected_here", "Move selected papers here"),
      () => onAction("emit", makeEvent("paper_library_move_selected_papers_to_collection", { node_id: "", paper_ids: payload.selectedPaperIds })),
      !canDropPapers || selectedCount < 1,
    );
  } else if (type === "collection") {
    addRow(
      "create-child",
      label(payload.labels, "new_subcollection", "New subcollection"),
      () => onAction("dialog:create", { parent_id: id }),
      !canCollections,
    );
    addRow(
      "add-selected",
      label(payload.labels, "add_selected_here", "Add selected papers here"),
      () => onAction("emit", makeEvent("paper_library_add_selected_papers_to_collection", { node_id: id, paper_ids: payload.selectedPaperIds })),
      !canDropPapers || selectedCount < 1,
    );
    addRow(
      "move-selected",
      label(payload.labels, "move_selected_here", "Move selected papers here"),
      () => onAction("emit", makeEvent("paper_library_move_selected_papers_to_collection", { node_id: id, paper_ids: payload.selectedPaperIds })),
      !canDropPapers || selectedCount < 1,
    );
    rows.push({ key: "sep-1", separator: true });
    addRow(
      "rename",
      label(payload.labels, "rename", "Rename"),
      () => onAction("dialog:rename", { node_id: id, title: nodeTitle(item) }),
      payload.capabilities.rename_collection === false,
    );
    addRow(
      "move",
      label(payload.labels, "move_collection", "Move collection"),
      () => onAction("dialog:move", { node_id: id, parent_id: cleanText(item.parent_id) }),
      payload.capabilities.move_collection === false,
    );
    addRow(
      "up",
      label(payload.labels, "move_up", "Move up"),
      () => onAction("emit", makeEvent("paper_library_reorder_collection", { node_id: id, direction: "up" })),
      payload.capabilities.move_collection === false,
    );
    addRow(
      "down",
      label(payload.labels, "move_down", "Move down"),
      () => onAction("emit", makeEvent("paper_library_reorder_collection", { node_id: id, direction: "down" })),
      payload.capabilities.move_collection === false,
    );
    rows.push({ key: "sep-2", separator: true });
    addRow(
      "delete",
      label(payload.labels, "delete_collection", "Delete collection"),
      () => onAction("dialog:delete", { node_id: id, title: nodeTitle(item), parent_id: cleanText(item.parent_id) }),
      payload.capabilities.delete_collection === false,
      true,
    );
  } else if (type === "collection_trash") {
    addRow(
      "restore",
      label(payload.labels, "restore_collection", "Restore collection"),
      () => onAction("emit", makeEvent("paper_library_restore_collection", { node_id: id })),
      payload.capabilities.restore_collection === false,
    );
    addRow(
      "purge",
      label(payload.labels, "purge_collection", "Purge forever"),
      () => onAction("dialog:purge", { node_id: id, title: nodeTitle(item), parent_id: cleanText(item.parent_id) }),
      payload.capabilities.purge_collection === false,
      true,
    );
  } else if (type === "paper") {
    const activeNodeId = cleanText(payload.activeNodeId);
    if (item.reader_url) {
      addRow(
        "open-reader",
        label(payload.labels, "open_reader", "Open Reader"),
        () => window.open(cleanText(item.reader_url), "_blank", "noopener,noreferrer"),
      );
    }
    addRow(
      "show-details",
      label(payload.labels, "show_details", "Show details"),
      () => onAction("emit", makeEvent("paper_library_select_paper", { source_id: id })),
    );
    addRow(
      "rename-paper",
      label(payload.labels, "rename_paper", "Rename paper..."),
      () => onAction("dialog:paper-rename", { source_id: id, title: nodeTitle(item) }),
      payload.capabilities.rename_papers === false || paperIds.length !== 1,
    );
    if (!item.has_pdf && cleanText(item.open_access_pdf_url)) {
      addRow(
        "download-pdf",
        label(payload.labels, "download_pdf", "Download PDF"),
        () => onAction("emit", makeEvent("paper_library_download_pdf", { paper_ids: paperIds })),
        paperIds.length < 1,
      );
    }
    rows.push({ key: "sep-paper-1", separator: true });
    addRow(
      "move-paper",
      label(payload.labels, "move_to_collection", "Move to collection"),
      () => onAction("dialog:paper-location", { mode: "move", paper_ids: paperIds }),
      !canDropPapers || paperIds.length < 1,
    );
    addRow(
      "add-paper",
      label(payload.labels, "add_to_collection", "Add to collection"),
      () => onAction("dialog:paper-location", { mode: "add", paper_ids: paperIds }),
      !canDropPapers || paperIds.length < 1,
    );
    addRow(
      "remove-paper",
      label(payload.labels, "remove_from_current_collection", "Remove from current collection"),
      () => onAction("emit", makeEvent("paper_library_remove_papers_from_collection", { node_id: activeNodeId, paper_ids: paperIds })),
      !activeNodeId || paperIds.length < 1,
    );
    rows.push({ key: "sep-paper-2", separator: true });
    addRow(
      "mark-reading",
      label(payload.labels, "mark_as_reading", "Mark as reading"),
      () => onAction("emit", makeEvent("paper_library_update_papers_status", { paper_ids: paperIds, status: "reading" })),
      paperIds.length < 1,
    );
    addRow(
      "archive",
      label(payload.labels, "archive", "Archive"),
      () => onAction("emit", makeEvent("paper_library_update_papers_status", { paper_ids: paperIds, status: "archived" })),
      paperIds.length < 1,
    );
    addRow(
      "discard",
      label(payload.labels, "discard", "Mark as discarded"),
      () => onAction("emit", makeEvent("paper_library_update_papers_status", { paper_ids: paperIds, status: "discarded" })),
      paperIds.length < 1,
      true,
    );
    addRow(
      "run-extraction",
      label(payload.labels, "run_extraction", "Run extraction"),
      () => onAction("emit", makeEvent("paper_library_run_extraction", { paper_ids: paperIds })),
      paperIds.length < 1,
    );
    addRow(
      "retry-translation",
      label(payload.labels, "retry_translation", "Retry translation"),
      () => onAction("emit", makeEvent("paper_library_retry_translation", translationModePayload(paperIds, "fast_body"))),
      paperIds.length < 1,
    );
    addRow(
      "translate-full-paper",
      label(payload.labels, "translate_full_paper", "Translate full paper"),
      () => onAction("emit", makeEvent("paper_library_retry_translation", translationModePayload(paperIds, "full_paper"))),
      paperIds.length < 1,
    );
    addRow(
      "translate-grobid-text",
      label(payload.labels, "translate_grobid_text", "GROBID paragraphs"),
      () => onAction("emit", makeEvent("paper_library_retry_translation", translationModePayload(paperIds, "grobid_text"))),
      paperIds.length < 1,
    );
  }

  if (!rows.length) {
    return null;
  }
  const estimatedHeight = 42 + rows.reduce((total, row) => total + (row.separator ? 11 : 32), 0);
  const viewportWidth = typeof window === "undefined" ? 1024 : window.innerWidth;
  const viewportHeight = typeof window === "undefined" ? 768 : window.innerHeight;
  const style = {
    left: Math.min(
      Math.max(8, Number(menu.x || 0)),
      Math.max(8, viewportWidth - 248),
    ),
    top: Math.min(
      Math.max(8, Number(menu.y || 0)),
      Math.max(8, viewportHeight - estimatedHeight - 8),
    ),
  };
  return (
    <div ref={ref} className="paper-tree-menu" style={style} role="menu">
      <div className="paper-tree-menu-title">{nodeTitle(item)}</div>
      {rows.map((row) => row.separator ? (
        <div className="paper-tree-menu-separator" key={row.key} />
      ) : (
        <button
          type="button"
          key={row.key}
          className={row.danger ? "is-danger" : ""}
          disabled={row.disabled}
          onClick={() => {
            if (row.disabled) {
              return;
            }
            row.action();
            onClose();
          }}
        >
          {row.text}
        </button>
      ))}
    </div>
  );
}

function Dialog({ dialog, payload, onClose, onEmit }) {
  const [title, setTitle] = useState(dialog?.title || "");
  const [parentId, setParentId] = useState(dialog?.parent_id || "");
  const [policy, setPolicy] = useState("move_to_parent");
  const [targetId, setTargetId] = useState("");

  useEffect(() => {
    setTitle(dialog?.title || "");
    setParentId(dialog?.parent_id || "");
    setPolicy("move_to_parent");
    setTargetId("");
  }, [dialog]);

  if (!dialog) {
    return null;
  }
  const collections = asArray(payload.sections.find((section) => section.id === "collections")?.items)
    .flatMap((item) => item.type === "collection_root" ? asArray(item.children) : [item]);
  const flatCollections = [];
  const collect = (items, depth = 0) => {
    for (const item of asArray(items)) {
      if (nodeType(item) === "collection") {
        flatCollections.push({ item, depth });
      }
      collect(item.children, depth + 1);
    }
  };
  collect(collections);
  const parentOptions = [{ id: "", title: label(payload.labels, "top_level", "Top level"), depth: 0 }];
  for (const row of flatCollections) {
    if (nodeId(row.item) !== dialog.node_id) {
      parentOptions.push({ id: nodeId(row.item), title: nodeTitle(row.item), depth: row.depth });
    }
  }
  const targetOptions = parentOptions.filter((option) => option.id && option.id !== dialog.node_id);
  const submit = () => {
    if (dialog.kind === "create") {
      onEmit(makeEvent("paper_library_create_collection", { parent_id: parentId, title }));
    } else if (dialog.kind === "rename") {
      onEmit(makeEvent("paper_library_rename_collection", { node_id: dialog.node_id, title }));
    } else if (dialog.kind === "paper-rename") {
      onEmit(makeEvent("paper_library_rename_paper", { source_id: dialog.source_id, title }));
    } else if (dialog.kind === "move") {
      onEmit(makeEvent("paper_library_move_collection", { node_id: dialog.node_id, parent_id: parentId }));
    } else if (dialog.kind === "delete") {
      const paperPolicy = policy === "move_to_collection" ? `move_to:${targetId}` : policy;
      onEmit(makeEvent("paper_library_trash_collection", {
        node_id: dialog.node_id,
        paper_policy: paperPolicy,
      }));
    } else if (dialog.kind === "purge") {
      const paperPolicy = policy === "move_to_collection" ? `move_to:${targetId}` : policy;
      onEmit(makeEvent("paper_library_purge_collection", {
        node_id: dialog.node_id,
        paper_policy: paperPolicy,
      }));
    } else if (dialog.kind === "paper-location") {
      onEmit(makeEvent(
        dialog.mode === "add"
          ? "paper_library_add_selected_papers_to_collection"
          : "paper_library_move_selected_papers_to_collection",
        {
          node_id: targetId,
          paper_ids: asArray(dialog.paper_ids).map(cleanText).filter(Boolean),
        },
      ));
    }
    onClose();
  };
  const titleText = {
    create: label(payload.labels, "new_collection", "New collection"),
    rename: label(payload.labels, "rename", "Rename"),
    "paper-rename": label(payload.labels, "rename_paper", "Rename paper..."),
    move: label(payload.labels, "move_collection", "Move collection"),
    delete: label(payload.labels, "delete_collection", "Delete collection"),
    purge: label(payload.labels, "purge_collection", "Purge forever"),
    "paper-location": dialog.mode === "add"
      ? label(payload.labels, "add_to_collection", "Add to collection")
      : label(payload.labels, "move_to_collection", "Move to collection"),
  }[dialog.kind] || "";
  const disabled =
    (dialog.kind === "create" && !title.trim()) ||
    (dialog.kind === "rename" && !title.trim()) ||
    (dialog.kind === "paper-rename" && !title.trim()) ||
    (dialog.kind === "delete" && policy === "move_to_collection" && !targetId) ||
    (dialog.kind === "purge" && policy === "move_to_collection" && !targetId) ||
    (dialog.kind === "paper-location" && !targetId);
  return (
    <div className="paper-tree-dialog-backdrop" role="presentation">
      <div className="paper-tree-dialog" role="dialog" aria-modal="true">
        <div className="paper-tree-dialog-title">{titleText}</div>
        {dialog.kind === "create" || dialog.kind === "rename" || dialog.kind === "paper-rename" ? (
          <label className="paper-tree-field">
            <span>{label(payload.labels, dialog.kind === "paper-rename" ? "paper_title" : "collection_title", dialog.kind === "paper-rename" ? "Paper title" : "Collection title")}</span>
            <input value={title} onChange={(event) => setTitle(event.target.value)} autoFocus />
          </label>
        ) : null}
        {dialog.kind === "create" || dialog.kind === "move" ? (
          <label className="paper-tree-field">
            <span>{label(payload.labels, "parent_collection", "Parent collection")}</span>
            <select value={parentId} onChange={(event) => setParentId(event.target.value)}>
              {parentOptions.map((option) => (
                <option key={option.id || "__root"} value={option.id}>
                  {"  ".repeat(option.depth)}{option.title}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        {dialog.kind === "delete" || dialog.kind === "purge" ? (
          <>
            <div className="paper-tree-dialog-note">{dialog.title}</div>
            <label className="paper-tree-field">
              <span>{label(payload.labels, "paper_policy", "Paper policy")}</span>
              <select value={policy} onChange={(event) => setPolicy(event.target.value)}>
                <option value="move_to_parent">{label(payload.labels, "move_papers_to_parent", "Move papers to parent collection")}</option>
                <option value="move_to_unsorted">{label(payload.labels, "move_papers_to_unsorted", "Move papers to Unsorted Inbox")}</option>
                <option value="move_to_collection">{label(payload.labels, "move_papers_to_collection", "Move papers to collection")}</option>
              </select>
            </label>
            {policy === "move_to_collection" ? (
              <label className="paper-tree-field">
                <span>{label(payload.labels, "target_collection", "Target collection")}</span>
                <select value={targetId} onChange={(event) => setTargetId(event.target.value)}>
                  <option value=""></option>
                  {targetOptions.map((option) => (
                    <option key={option.id} value={option.id}>
                      {"  ".repeat(option.depth)}{option.title}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
          </>
        ) : null}
        {dialog.kind === "paper-location" ? (
          <label className="paper-tree-field">
            <span>{label(payload.labels, "target_collection", "Target collection")}</span>
            <select value={targetId} onChange={(event) => setTargetId(event.target.value)} autoFocus>
              <option value=""></option>
              {parentOptions.map((option) => (
                <option key={option.id || "__unsorted"} value={option.id}>
                  {"  ".repeat(option.depth)}{option.title}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        <div className="paper-tree-dialog-actions">
          <button type="button" onClick={onClose}>{label(payload.labels, "cancel", "Cancel")}</button>
          <button type="button" className="is-primary" disabled={disabled} onClick={submit}>
            {dialog.kind === "delete"
              ? label(payload.labels, "delete_collection", "Delete collection")
              : dialog.kind === "purge"
                ? label(payload.labels, "purge_collection", "Purge forever")
                : label(payload.labels, "save", "Save")}
          </button>
        </div>
      </div>
    </div>
  );
}

function TreeRow({
  item,
  depth,
  payload,
  expandedIds,
  dragTarget,
  onToggle,
  onSelect,
  onMenu,
  onDropCollection,
  onDragStart,
  onDragTarget,
}) {
  const id = nodeId(item);
  const type = nodeType(item);
  const children = asArray(item.children);
  const hasChildren = children.length > 0;
  const isExpanded = expandedIds.has(id);
  const isActive =
    (type === "view" && !payload.activeNodeId && payload.activeView === id) ||
    ((type === "collection" || type === "collection_root") && payload.activeNodeId === cleanText(item.node_id ?? id));
  const count = item.count === undefined || item.count === null ? "" : cleanText(item.count);
  const draggable = type === "collection";
  const droppable = type === "collection" || type === "collection_root";
  const activeDropPosition = dragTarget?.id === id ? dragTarget.position : "";
  const dropPositionForEvent = (event) => {
    if (type === "collection_root") {
      return "into";
    }
    const rect = event.currentTarget.getBoundingClientRect();
    const y = event.clientY - rect.top;
    if (y < rect.height * 0.28) {
      return "before";
    }
    if (y > rect.height * 0.72) {
      return "after";
    }
    return "into";
  };
  return (
    <>
      <div
        className={`paper-tree-row is-${type} ${isActive ? "is-active" : ""} ${activeDropPosition ? `is-drop-${activeDropPosition}` : ""}`}
        style={{ "--depth": depth }}
        draggable={draggable}
        onDragStart={(event) => {
          if (!draggable) {
            return;
          }
          event.dataTransfer.effectAllowed = "move";
          event.dataTransfer.setData("text/plain", id);
          onDragStart(id);
        }}
        onDragOver={(event) => {
          if (droppable) {
            event.preventDefault();
            event.dataTransfer.dropEffect = "move";
            onDragTarget({ id, position: dropPositionForEvent(event) });
          }
        }}
        onDragLeave={() => {
          if (droppable) {
            onDragTarget(null);
          }
        }}
        onDrop={(event) => {
          if (!droppable) {
            return;
          }
          event.preventDefault();
          const position = dropPositionForEvent(event);
          onDragTarget(null);
          onDropCollection(type === "collection_root" ? "" : id, position, event);
        }}
        onContextMenu={(event) => {
          event.preventDefault();
          onMenu(event, item);
        }}
      >
        <button
          type="button"
          className="paper-tree-toggle"
          disabled={!hasChildren}
          onClick={() => onToggle(id)}
          aria-label={isExpanded ? label(payload.labels, "collapse", "Collapse") : label(payload.labels, "expand", "Expand")}
        >
          {hasChildren ? (isExpanded ? "v" : ">") : ""}
        </button>
        <button type="button" className="paper-tree-main" onClick={() => onSelect(item)}>
          <span className="paper-tree-icon">{type === "view" ? "V" : type === "collection_root" ? "L" : type === "collection_trash_root" ? "T" : type === "collection_trash" ? "X" : type === "taxonomy" ? "T" : "C"}</span>
          <span className="paper-tree-title">{nodeTitle(item)}</span>
          {count ? <span className="paper-tree-count">{count}</span> : null}
        </button>
        {(type === "collection" || type === "collection_root" || type === "collection_trash") ? (
          <button
            type="button"
            className="paper-tree-more"
            onClick={(event) => {
              const rect = event.currentTarget.getBoundingClientRect();
              onMenu({ clientX: rect.left, clientY: rect.bottom + 4, preventDefault() {} }, item);
            }}
            aria-label={label(payload.labels, "collection_actions", "Collection actions")}
          >
            ...
          </button>
        ) : null}
      </div>
      {hasChildren && isExpanded ? children.map((child) => (
        <TreeRow
          key={nodeId(child)}
          item={child}
          depth={depth + 1}
          payload={payload}
          expandedIds={expandedIds}
          dragTarget={dragTarget}
          onToggle={onToggle}
          onSelect={onSelect}
          onMenu={onMenu}
          onDropCollection={onDropCollection}
          onDragStart={onDragStart}
          onDragTarget={onDragTarget}
        />
      )) : null}
    </>
  );
}

function Section({
  section,
  payload,
  expanded,
  dragTarget,
  onToggle,
  onSelect,
  onMenu,
  onDialog,
  onDropCollection,
  onDragStart,
  onDragTarget,
}) {
  const [open, setOpen] = useState(true);
  const items = asArray(section.items);
  return (
    <section className={`paper-tree-section is-${section.id || ""}`}>
      <div className="paper-tree-section-head">
        <button type="button" className="paper-tree-section-toggle" onClick={() => setOpen(!open)}>
          {open ? "v" : ">"}
        </button>
        <span>{cleanText(section.title || section.id)}</span>
        {section.id === "collections" ? (
          <button
            type="button"
            className="paper-tree-head-action"
            onClick={() => onDialog({ kind: "create", parent_id: "" })}
            aria-label={label(payload.labels, "new_collection", "New collection")}
          >
            +
          </button>
        ) : null}
      </div>
      {open ? (
        <div className="paper-tree-section-items">
          {items.map((item) => (
            <TreeRow
              key={nodeId(item)}
              item={item}
              depth={0}
              payload={payload}
              expandedIds={expanded}
              dragTarget={dragTarget}
              onToggle={onToggle}
              onSelect={onSelect}
              onMenu={onMenu}
              onDropCollection={onDropCollection}
              onDragStart={onDragStart}
              onDragTarget={onDragTarget}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}

function PaperList({
  payload,
  selectedPaperIds,
  setSelectedPaperIds,
  setDragPayload,
  emit,
  onPaperMenu,
}) {
  const activeQuery = cleanText(payload.query || currentUrlQuery());
  const papers = asArray(payload.papers).filter((paper) => paperMatchesQuery(paper, activeQuery));
  const selected = selectedPaperIds;
  const selectedCount = selected.size;
  useEffect(() => {
    if (!payload.detailId || !(payload.focus || payload.action)) {
      return;
    }
    const match = [...document.querySelectorAll(".paper-list-card")]
      .find((element) => element.dataset.paperId === payload.detailId);
    match?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [payload.detailId, payload.focus, payload.action, payload.activeView, payload.query]);
  const togglePaper = (paperId, checked) => {
    const next = new Set(selected);
    if (checked) {
      next.add(paperId);
    } else {
      next.delete(paperId);
    }
    setSelectedPaperIds(next);
  };
  const toggleAll = () => {
    if (selectedCount > 0) {
      setSelectedPaperIds(new Set());
    } else {
      setSelectedPaperIds(new Set(papers.map((paper) => cleanText(paper.id)).filter(Boolean)));
    }
  };
  return (
    <main className="paper-list-pane">
      <div className="paper-list-head">
        <div>
          <div className="paper-list-title">{payload.activeLabel || label(payload.labels, "papers", "Papers")}</div>
          <div className="paper-list-caption">
            {label(payload.labels, "library_result_count", "{count} papers").replace("{count}", papers.length)}
          </div>
        </div>
        <button type="button" className="paper-list-select-all" onClick={toggleAll} disabled={!papers.length}>
          {selectedCount > 0 ? label(payload.labels, "clear_selection", "Clear") : label(payload.labels, "bulk_select", "Bulk select")}
        </button>
      </div>
      {!papers.length ? (
        <div className="paper-list-empty">{label(payload.labels, "library_empty", "No papers match this view.")}</div>
      ) : (
        <div className="paper-card-list">
          {papers.map((paper) => {
            const paperId = cleanText(paper.id);
            const isSelected = selected.has(paperId);
            const isActive = payload.detailId === paperId;
            const isDeepLinked = isActive && Boolean(payload.focus || payload.action);
            const dragIds = isSelected ? [...selected] : [paperId];
            return (
              <article
                key={paperId}
                data-paper-id={paperId}
                className={`paper-list-card ${isActive ? "is-active" : ""} ${isSelected ? "is-selected" : ""} ${isDeepLinked ? "is-deep-linked" : ""}`}
                draggable
                onContextMenu={(event) => {
                  event.preventDefault();
                  onPaperMenu(event, paper, dragIds);
                }}
                onDragStart={(event) => {
                  event.dataTransfer.effectAllowed = "move";
                  event.dataTransfer.setData("text/plain", dragIds.join("\n"));
                  setDragPayload({ kind: "papers", paperIds: dragIds, append: event.altKey || event.shiftKey });
                }}
                onDragEnd={() => setDragPayload(null)}
              >
                <label className="paper-card-check">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={(event) => togglePaper(paperId, event.target.checked)}
                    aria-label={label(payload.labels, "select_paper", "Select paper")}
                  />
                </label>
                <button
                  type="button"
                  className="paper-card-body"
                  onClick={() => emit(makeEvent("paper_library_select_paper", { source_id: paperId }))}
                >
                  <span className="paper-card-title-row">
                    <span className="paper-card-title">{cleanText(paper.title || paperId)}</span>
                    {paper.status_label ? (
                      <span className={`paper-card-status is-${cleanText(paper.status || "inbox").replaceAll("_", "-")}`}>
                        {cleanText(paper.status_label)}
                      </span>
                    ) : null}
                  </span>
                  {paper.meta ? <span className="paper-card-meta">{cleanText(paper.meta)}</span> : null}
                  {paper.summary ? <span className="paper-card-summary">{cleanText(paper.summary)}</span> : null}
                  <span className="paper-card-badges">
                    {asArray(paper.badges).slice(0, 5).map((badge) => (
                      <span key={cleanText(badge)}>{cleanText(badge)}</span>
                    ))}
                  </span>
                  {paper.metrics ? <span className="paper-card-metrics">{cleanText(paper.metrics)}</span> : null}
                </button>
              </article>
            );
          })}
        </div>
      )}
    </main>
  );
}

function DiscoveryPanel({ payload, profile, onImported, workspaceBusy = false }) {
  const [open, setOpen] = useState(true);
  const [mode, setMode] = useState("codex");
  const [codexDepth, setCodexDepth] = useState("quick");
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(10);
  const [providerText, setProviderText] = useState("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");
  const [downloadPdf, setDownloadPdf] = useState(true);
  const [manualUrl, setManualUrl] = useState("");
  const [manualTitle, setManualTitle] = useState("");
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadFile, setUploadFile] = useState(null);
  const [nodeIdValue, setNodeIdValue] = useState(cleanText(payload.activeNodeId));
  const [statusValue, setStatusValue] = useState("inbox");
  const [uploadStatusValue, setUploadStatusValue] = useState("reading");
  const [visibilityValue, setVisibilityValue] = useState("private");
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [codexMaxSeconds, setCodexMaxSeconds] = useState("");
  const [codexIdleSeconds, setCodexIdleSeconds] = useState("");
  const [providerBudgetSeconds, setProviderBudgetSeconds] = useState("");
  const [providerRequestSeconds, setProviderRequestSeconds] = useState("");
  const [results, setResults] = useState([]);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [diagnostics, setDiagnostics] = useState({});
  const [progress, setProgress] = useState(null);
  const [currentJobId, setCurrentJobId] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const uploadInputRef = useRef(null);
  const collections = useMemo(() => collectionOptionsFromPayload(payload), [payload.sections, payload.labels]);
  const searchMode = ["codex", "model", "provider"].includes(mode);
  const selectedCount = selectedIds.size;

  useEffect(() => {
    if (!nodeIdValue) {
      setNodeIdValue(cleanText(payload.activeNodeId));
    }
  }, [payload.activeNodeId]);

  const switchMode = (nextMode) => {
    setMode(nextMode);
    setMessage("");
    if (!["codex", "model", "provider"].includes(nextMode)) {
      setProgress(null);
      setDiagnostics({});
    }
  };

  const waitForSearchJobPolling = async (jobId) => {
    for (;;) {
      await sleep(800);
      const data = await jsonRequest(paperLibraryApiUrl(profile, `/search/jobs/${jobId}`), { method: "GET", timeoutMs: 15000 });
      const job = data.job && typeof data.job === "object" ? data.job : {};
      setProgress(job);
      if (job.status === "done") {
        return data.result || {};
      }
      if (job.status === "cancelled") {
        throw new Error("Search cancelled.");
      }
      if (job.status === "failed") {
        throw new Error(cleanText(job.error || job.message) || "Search failed.");
      }
    }
  };

  const waitForSearchJob = async (jobId) => {
    if (typeof window === "undefined" || typeof window.EventSource !== "function") {
      return waitForSearchJobPolling(jobId);
    }
    return new Promise((resolve, reject) => {
      let settled = false;
      let source;
      const close = () => {
        if (source) {
          source.close();
        }
      };
      const settle = (handler, value) => {
        if (settled) {
          return;
        }
        settled = true;
        close();
        handler(value);
      };
      const fallbackToPolling = () => {
        if (settled) {
          return;
        }
        settled = true;
        close();
        waitForSearchJobPolling(jobId).then(resolve).catch(reject);
      };
      const handlePayload = (event) => {
        let data = {};
        try {
          data = JSON.parse(event.data || "{}");
        } catch (error) {
          settle(reject, error);
          return;
        }
        const job = data.job && typeof data.job === "object" ? { ...data.job, transport: "stream" } : {};
        if (Object.keys(job).length) {
          setProgress(job);
        }
        if (job.status === "done" && (event.type === "result" || data.result)) {
          settle(resolve, data.result || {});
        } else if (job.status === "cancelled") {
          settle(reject, new Error("Search cancelled."));
        } else if (job.status === "failed") {
          settle(reject, new Error(cleanText(job.error || job.message) || "Search failed."));
        }
      };
      try {
        source = new window.EventSource(paperLibraryApiUrl(profile, `/search/jobs/${jobId}/stream`));
        source.addEventListener("job", handlePayload);
        source.addEventListener("progress", handlePayload);
        source.addEventListener("result", handlePayload);
        source.addEventListener("error", fallbackToPolling);
      } catch {
        fallbackToPolling();
      }
    });
  };

  const applySearchResult = (data) => {
    const nextResults = asArray(data.candidates).filter((item) => item && typeof item === "object");
    const warnings = asArray(data.warnings).map(cleanText).filter(Boolean);
    const trace = asArray(data.search_trace).filter((item) => item && typeof item === "object");
    const variants = asArray(data.query_variants).map(cleanText).filter(Boolean);
    setDiagnostics({ warnings, trace, variants });
    setResults(nextResults);
    setSelectedIds(new Set(
      nextResults
        .filter((candidate) => candidateHasPdf(candidate))
        .map((candidate) => cleanText(candidate.candidate_id))
        .filter(Boolean),
    ));
    setMessage(
      nextResults.length
        ? `${nextResults.length} PDF-ready candidates found.`
        : warnings[0] || "No PDF-ready candidates found.",
    );
    setOpen(true);
  };

  const runSearch = async () => {
    const cleanQuery = query.trim();
    if (workspaceBusy) {
      setMessage("Another Paper Library action is still running. Wait for it to finish, then search.");
      return;
    }
    if (!cleanQuery || !profile) {
      setMessage(cleanQuery ? "Missing profile." : "Enter a query first.");
      return;
    }
    setBusy(true);
    setMessage("");
    setDiagnostics({});
    setCurrentJobId("");
    const reasoningEffort = codexReasoningEffort(codexDepth);
    const codexTimeout = optionalPositiveSeconds(codexMaxSeconds);
    const codexIdleTimeout = optionalPositiveSeconds(codexIdleSeconds);
    const providerBudget = optionalPositiveSeconds(providerBudgetSeconds);
    const providerTimeout = optionalPositiveSeconds(providerRequestSeconds);
    setProgress({
      status: "starting",
      phase: mode,
      message: mode === "codex" ? `Starting Codex ${codexDepth} search.` : "Starting paper search.",
      elapsed_ms: 0,
      budget_mode: mode === "codex" ? (codexTimeout ? "manual" : "auto") : "",
      timeout_seconds: mode === "codex" ? codexTimeout || 0 : providerBudget || 0,
      idle_timeout_seconds: mode === "codex" ? codexIdleTimeout || 0 : 0,
      codex_reasoning_effort: mode === "codex" ? reasoningEffort : "",
      codex_search_depth: mode === "codex" ? codexDepth : "",
      events: [],
    });
    try {
      const requestBody = {
        mode,
        query: cleanQuery,
        limit,
        providers: providerText,
        year_from: yearFrom,
        year_to: yearTo,
        require_pdf: true,
      };
      if (mode === "codex") {
        requestBody.codex_search_depth = codexDepth;
        requestBody.codex_reasoning_effort = reasoningEffort;
        requestBody.codex_budget_mode = codexTimeout ? "manual" : "auto";
        if (codexTimeout) {
          requestBody.codex_timeout_seconds = codexTimeout;
        }
        if (codexIdleTimeout) {
          requestBody.codex_idle_timeout_seconds = codexIdleTimeout;
        }
      }
      if (providerBudget) {
        requestBody.provider_budget_seconds = providerBudget;
      }
      if (providerTimeout) {
        requestBody.provider_timeout_seconds = providerTimeout;
      }
      const started = await jsonRequest(paperLibraryApiUrl(profile, "/search/jobs"), {
        method: "POST",
        timeoutMs: 20000,
        body: JSON.stringify(requestBody),
      });
      if (started.job) {
        setProgress(started.job);
      }
      const jobId = cleanText(started.job_id || started.job?.job_id);
      if (!jobId) {
        throw new Error("Search job did not start.");
      }
      setCurrentJobId(jobId);
      const data = await waitForSearchJob(jobId);
      applySearchResult(data);
    } catch (error) {
      setDiagnostics({});
      const errorMessage = error.message || String(error);
      const cancelled = errorMessage.toLowerCase().includes("cancelled");
      setProgress((current) => ({
        ...(current || {}),
        status: cancelled ? "cancelled" : "failed",
        phase: cancelled ? "cancelled" : "failed",
        message: errorMessage,
      }));
      setMessage(error.message || String(error));
    } finally {
      setBusy(false);
      setCurrentJobId("");
    }
  };

  const cancelSearch = async () => {
    const jobId = cleanText(currentJobId || progress?.job_id);
    if (!jobId || !profile) {
      return;
    }
    setMessage("Cancelling search...");
    setProgress((current) => ({ ...(current || {}), status: "cancelling", phase: "cancelling", message: "Cancelling paper search." }));
    try {
      const data = await jsonRequest(paperLibraryApiUrl(profile, `/search/jobs/${jobId}/cancel`), {
        method: "POST",
        timeoutMs: 10000,
        body: JSON.stringify({}),
      });
      if (data.job) {
        setProgress(data.job);
      }
    } catch (error) {
      setMessage(error.message || String(error));
    }
  };

  const importSelected = async () => {
    if (!selectedCount) {
      setMessage("Select at least one candidate.");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      const data = await jsonRequest(paperLibraryApiUrl(profile, "/import"), {
        method: "POST",
        body: JSON.stringify({
          candidates: results,
          selected_ids: [...selectedIds],
          node_id: nodeIdValue,
          status: statusValue,
          visibility: visibilityValue,
          download_pdf: downloadPdf,
          replace_existing: true,
        }),
      });
      const imported = asArray(data.imported).map(cleanText).filter(Boolean);
      let importedIndex = 0;
      setResults((rows) => rows.map((row) => {
        if (!selectedIds.has(cleanText(row.candidate_id))) {
          return row;
        }
        const existingId = cleanText(row.imported_source_id);
        const importedId = existingId || imported[importedIndex] || "imported";
        importedIndex += 1;
        return { ...row, imported_source_id: importedId };
      }));
      setSelectedIds(new Set());
      const importWarnings = asArray(data.warnings).map(cleanText).filter(Boolean);
      setMessage([
        data.message || `Imported ${imported.length} papers.`,
        ...importWarnings.slice(0, 2),
      ].filter(Boolean).join(" "));
      onImported(data);
    } catch (error) {
      setMessage(error.message || String(error));
    } finally {
      setBusy(false);
    }
  };

  const importManualUrl = async () => {
    const cleanUrl = manualUrl.trim();
    if (workspaceBusy) {
      setMessage("Another Paper Library action is still running. Wait for it to finish, then import.");
      return;
    }
    if (!cleanUrl || !profile) {
      setMessage(cleanUrl ? "Missing profile." : "Paste a paper URL first.");
      return;
    }
    setBusy(true);
    setMessage("");
    setProgress(null);
    setDiagnostics({});
    try {
      const data = await jsonRequest(paperLibraryApiUrl(profile, "/import-url"), {
        method: "POST",
        body: JSON.stringify({
          url: cleanUrl,
          title: manualTitle,
          node_id: nodeIdValue,
          status: statusValue,
          visibility: visibilityValue,
          download_pdf: downloadPdf,
        }),
      });
      setManualUrl("");
      setManualTitle("");
      setResults([]);
      setSelectedIds(new Set());
      setMessage(data.message || "Imported paper from URL.");
      onImported(data);
    } catch (error) {
      setMessage(error.message || String(error));
    } finally {
      setBusy(false);
    }
  };

  const uploadLocalPdf = async () => {
    if (workspaceBusy) {
      setMessage("Another Paper Library action is still running. Wait for it to finish, then upload.");
      return;
    }
    if (!profile || !uploadFile) {
      setMessage(profile ? "Choose a PDF file first." : "Missing profile.");
      return;
    }
    setBusy(true);
    setMessage("");
    setProgress(null);
    setDiagnostics({});
    try {
      const formData = new FormData();
      formData.append("file", uploadFile, uploadFile.name || "paper.pdf");
      formData.append("title", uploadTitle);
      formData.append("node_id", nodeIdValue);
      formData.append("status", uploadStatusValue);
      formData.append("visibility", visibilityValue);
      const data = await formRequest(paperLibraryApiUrl(profile, "/upload"), formData, { timeoutMs: 180000 });
      setUploadTitle("");
      setUploadFile(null);
      if (uploadInputRef.current) {
        uploadInputRef.current.value = "";
      }
      setResults([]);
      setSelectedIds(new Set());
      setMessage(data.message || "Uploaded and imported PDF.");
      onImported(data);
    } catch (error) {
      setMessage(error.message || String(error));
    } finally {
      setBusy(false);
    }
  };

  const toggleCandidate = (candidateId, checked) => {
    const next = new Set(selectedIds);
    if (checked) {
      next.add(candidateId);
    } else {
      next.delete(candidateId);
    }
    setSelectedIds(next);
  };

  return (
    <section className={`paper-discovery ${open ? "is-open" : "is-collapsed"}`}>
      <div className="paper-discovery-head">
        <button type="button" className="paper-discovery-title" onClick={() => setOpen(!open)} aria-expanded={open}>
          <span>{open ? "v" : ">"}</span>
          <strong>{label(payload.labels, "find_import_papers", "Find and import papers")}</strong>
        </button>
        <div className="paper-discovery-mode" role="group" aria-label="Search mode">
          <button type="button" className={mode === "codex" ? "is-active" : ""} onClick={() => switchMode("codex")}>
            Codex
          </button>
          <button type="button" className={mode === "model" ? "is-active" : ""} onClick={() => switchMode("model")}>
            Model
          </button>
          <button type="button" className={mode === "provider" ? "is-active" : ""} onClick={() => switchMode("provider")}>
            Provider
          </button>
          <button type="button" className={mode === "url" ? "is-active" : ""} onClick={() => switchMode("url")}>
            URL
          </button>
          <button type="button" className={mode === "upload" ? "is-active" : ""} onClick={() => switchMode("upload")}>
            Upload
          </button>
        </div>
      </div>
      {open ? (
        <>
          {searchMode ? (
            <>
          <div className="paper-discovery-form">
            <label className="paper-discovery-query">
              <span>Query</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    runSearch();
                  }
                }}
                placeholder="VLA memory"
              />
            </label>
            {mode === "provider" ? (
              <label>
                <span>Providers</span>
                <input
                  value={providerText}
                  onChange={(event) => setProviderText(event.target.value)}
                  placeholder="arxiv, semantic_scholar"
                />
              </label>
            ) : null}
            {mode === "codex" ? (
              <label className="paper-discovery-depth">
                <span>Codex depth</span>
                <span className="paper-discovery-depth-options" role="group" aria-label="Codex search depth">
                  <button
                    type="button"
                    className={codexDepth === "quick" ? "is-active" : ""}
                    onClick={() => setCodexDepth("quick")}
                  >
                    Fast
                  </button>
                  <button
                    type="button"
                    className={codexDepth === "deep" ? "is-active" : ""}
                    onClick={() => setCodexDepth("deep")}
                  >
                    Deep
                  </button>
                </span>
              </label>
            ) : null}
            <label>
              <span>Limit</span>
              <input
                type="number"
                min="1"
                max="50"
                value={limit}
                onChange={(event) => setLimit(event.target.value)}
              />
            </label>
            <label>
              <span>Year from</span>
              <input value={yearFrom} onChange={(event) => setYearFrom(event.target.value)} inputMode="numeric" />
            </label>
            <label>
              <span>Year to</span>
              <input value={yearTo} onChange={(event) => setYearTo(event.target.value)} inputMode="numeric" />
            </label>
            <div className="paper-discovery-actions">
              <button type="button" className="paper-discovery-search" disabled={busy || workspaceBusy || !query.trim()} onClick={runSearch}>
                {busy ? "Searching..." : workspaceBusy ? "Action running" : "Search PDFs"}
              </button>
              {busy && currentJobId ? (
                <button type="button" className="paper-discovery-cancel" onClick={cancelSearch}>
                  Cancel
                </button>
              ) : null}
            </div>
          </div>
          <div className="paper-discovery-policy">
            <span>PDF required</span>
            <span>
              {mode === "provider"
                ? "Provider + arXiv web fallback"
                : mode === "codex"
                  ? codexBudgetLabel(codexDepth, codexMaxSeconds)
                  : "Model-first + arXiv web fallback"}
            </span>
          </div>
          <div className={`paper-discovery-advanced ${advancedOpen ? "is-open" : ""}`}>
            <button
              type="button"
              className="paper-discovery-advanced-toggle"
              aria-expanded={advancedOpen}
              onClick={() => setAdvancedOpen(!advancedOpen)}
            >
              <span>{advancedOpen ? "v" : ">"}</span>
              <strong>Advanced</strong>
            </button>
            {advancedOpen ? (
              <div className="paper-discovery-advanced-grid">
                {mode === "codex" ? (
                  <>
                    <label>
                      <span>Codex max s</span>
                      <input
                        type="number"
                        min="1"
                        step="1"
                        inputMode="numeric"
                        value={codexMaxSeconds}
                        onChange={(event) => setCodexMaxSeconds(event.target.value)}
                        placeholder="auto"
                      />
                    </label>
                    <label>
                      <span>Idle s</span>
                      <input
                        type="number"
                        min="1"
                        step="1"
                        inputMode="numeric"
                        value={codexIdleSeconds}
                        onChange={(event) => setCodexIdleSeconds(event.target.value)}
                        placeholder="auto"
                      />
                    </label>
                  </>
                ) : null}
                <label>
                  <span>Provider budget s</span>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    inputMode="numeric"
                    value={providerBudgetSeconds}
                    onChange={(event) => setProviderBudgetSeconds(event.target.value)}
                    placeholder="default"
                  />
                </label>
                <label>
                  <span>Provider request s</span>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    inputMode="numeric"
                    value={providerRequestSeconds}
                    onChange={(event) => setProviderRequestSeconds(event.target.value)}
                    placeholder="default"
                  />
                </label>
              </div>
            ) : null}
          </div>
            </>
          ) : mode === "url" ? (
            <div className="paper-discovery-form is-direct">
              <label className="paper-discovery-query">
                <span>Paper URL</span>
                <input
                  value={manualUrl}
                  onChange={(event) => setManualUrl(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      importManualUrl();
                    }
                  }}
                  placeholder="https://arxiv.org/abs/..."
                />
              </label>
              <label>
                <span>Title hint</span>
                <input value={manualTitle} onChange={(event) => setManualTitle(event.target.value)} placeholder="optional" />
              </label>
              <label>
                <span>Collection</span>
                <select value={nodeIdValue} onChange={(event) => setNodeIdValue(event.target.value)}>
                  {collections.map((item) => (
                    <option key={item.id || "inbox"} value={item.id}>{item.title}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>Status</span>
                <select value={statusValue} onChange={(event) => setStatusValue(event.target.value)}>
                  <option value="inbox">Inbox</option>
                  <option value="reading">Reading</option>
                  <option value="candidate_ready">Candidate ready</option>
                </select>
              </label>
              <label>
                <span>Visibility</span>
                <select value={visibilityValue} onChange={(event) => setVisibilityValue(event.target.value)}>
                  <option value="private">Private</option>
                  <option value="public">Public</option>
                </select>
              </label>
              <div className="paper-discovery-actions">
                <label className="paper-discovery-check">
                  <input type="checkbox" checked={downloadPdf} onChange={(event) => setDownloadPdf(event.target.checked)} />
                  <span>Download PDF</span>
                </label>
                <button type="button" className="paper-discovery-search" disabled={busy || workspaceBusy || !manualUrl.trim()} onClick={importManualUrl}>
                  {busy ? "Importing..." : workspaceBusy ? "Action running" : "Import URL"}
                </button>
              </div>
            </div>
          ) : (
            <div className="paper-discovery-form is-direct">
              <label>
                <span>Title</span>
                <input value={uploadTitle} onChange={(event) => setUploadTitle(event.target.value)} placeholder="defaults to filename" />
              </label>
              <label className="paper-discovery-query">
                <span>PDF file</span>
                <input
                  ref={uploadInputRef}
                  type="file"
                  accept="application/pdf,.pdf"
                  onChange={(event) => setUploadFile(event.target.files?.[0] || null)}
                />
              </label>
              <label>
                <span>Collection</span>
                <select value={nodeIdValue} onChange={(event) => setNodeIdValue(event.target.value)}>
                  {collections.map((item) => (
                    <option key={item.id || "inbox"} value={item.id}>{item.title}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>Status</span>
                <select value={uploadStatusValue} onChange={(event) => setUploadStatusValue(event.target.value)}>
                  <option value="inbox">Inbox</option>
                  <option value="reading">Reading</option>
                  <option value="candidate_ready">Candidate ready</option>
                </select>
              </label>
              <label>
                <span>Visibility</span>
                <select value={visibilityValue} onChange={(event) => setVisibilityValue(event.target.value)}>
                  <option value="private">Private</option>
                  <option value="public">Public</option>
                </select>
              </label>
              <div className="paper-discovery-actions">
                <button type="button" className="paper-discovery-search" disabled={busy || workspaceBusy || !uploadFile} onClick={uploadLocalPdf}>
                  {busy ? "Uploading..." : workspaceBusy ? "Action running" : "Upload PDF"}
                </button>
              </div>
            </div>
          )}
          {message ? <div className="paper-discovery-message">{message}</div> : null}
          {searchMode && progress ? (
            <div className="paper-discovery-progress">
              <div className="paper-discovery-progress-top">
                <strong>{cleanText(progress.message) || "Searching papers..."}</strong>
                <span>{searchProgressText(progress)}</span>
              </div>
              {isJobRunning(progress) ? (
                <div className="paper-discovery-progress-track is-active">
                  <span />
                </div>
              ) : null}
              {asArray(progress.events).some((event) => event?.visible !== false) ? (
                <ol>
                  {asArray(progress.events).filter((event) => event?.visible !== false).slice(-8).map((event, index) => (
                    <li key={`${cleanText(event.seq) || index}`}>{searchEventText(event)}</li>
                  ))}
                </ol>
              ) : null}
              {!asArray(progress.events).length && asArray(progress.trace).length ? (
                <ol>
                  {asArray(progress.trace).slice(-4).map((step, index) => (
                    <li key={`${cleanText(step.stage)}-${index}`}>{searchStepText(step)}</li>
                  ))}
                </ol>
              ) : null}
            </div>
          ) : null}
          {searchMode && (asArray(diagnostics.trace).length || asArray(diagnostics.warnings).length) ? (
            <div className="paper-discovery-diagnostics">
              {asArray(diagnostics.variants).length ? (
                <p>{asArray(diagnostics.variants).slice(0, 4).map(cleanText).filter(Boolean).join(" | ")}</p>
              ) : null}
              {asArray(diagnostics.trace).length ? (
                <ol>
                  {asArray(diagnostics.trace).slice(0, 8).map((step, index) => (
                    <li key={`${cleanText(step.stage)}-${index}`}>{searchStepText(step)}</li>
                  ))}
                </ol>
              ) : null}
              {asArray(diagnostics.warnings).length ? (
                <ul>
                  {asArray(diagnostics.warnings).slice(0, 4).map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
          {searchMode && results.length ? (
            <div className="paper-discovery-results">
              <div className="paper-discovery-importbar">
                <select value={nodeIdValue} onChange={(event) => setNodeIdValue(event.target.value)}>
                  {collections.map((item) => (
                    <option key={item.id || "inbox"} value={item.id}>{item.title}</option>
                  ))}
                </select>
                <select value={statusValue} onChange={(event) => setStatusValue(event.target.value)}>
                  <option value="inbox">Inbox</option>
                  <option value="reading">Reading</option>
                  <option value="candidate_ready">Candidate ready</option>
                </select>
                <select value={visibilityValue} onChange={(event) => setVisibilityValue(event.target.value)}>
                  <option value="private">Private</option>
                  <option value="public">Public</option>
                </select>
                <label className="paper-discovery-check">
                  <input type="checkbox" checked={downloadPdf} onChange={(event) => setDownloadPdf(event.target.checked)} />
                  <span>Download PDF</span>
                </label>
                <button type="button" className="paper-discovery-import" disabled={busy || !selectedCount} onClick={importSelected}>
                  Import / update selected ({selectedCount})
                </button>
              </div>
              <div className="paper-discovery-card-list">
                {results.map((candidate) => {
                  const candidateId = cleanText(candidate.candidate_id);
                  const importedId = cleanText(candidate.imported_source_id);
                  const disabled = !candidateHasPdf(candidate);
                  const overview = cleanText(candidate.ai_summary);
                  const selectionReason = cleanText(candidate.why_relevant);
                  const explanationLinks = candidateExplanationLinks(candidate);
                  return (
                    <article className={`paper-discovery-card ${disabled ? "is-disabled" : ""}`} key={candidateId || cleanText(candidate.title)}>
                      <label className="paper-discovery-card-check">
                        <input
                          type="checkbox"
                          checked={selectedIds.has(candidateId)}
                          disabled={disabled}
                          onChange={(event) => toggleCandidate(candidateId, event.target.checked)}
                        />
                      </label>
                      <div className="paper-discovery-card-body">
                        <div className="paper-discovery-card-top">
                          <strong>{cleanText(candidate.title || candidateId)}</strong>
                          <span>{importedId ? "Update local" : "PDF ready"}</span>
                        </div>
                        {candidateMeta(candidate) ? <p className="paper-discovery-meta">{candidateMeta(candidate)}</p> : null}
                        {overview ? (
                          <div className="paper-discovery-card-section">
                            <span>Overview</span>
                            <p>{overview}</p>
                          </div>
                        ) : null}
                        {selectionReason ? (
                          <div className="paper-discovery-card-section is-reason">
                            <span>Why selected</span>
                            <p>{selectionReason}</p>
                          </div>
                        ) : null}
                        {cleanText(candidate.abstract) ? <p>{cleanText(candidate.abstract).slice(0, 520)}</p> : null}
                        {explanationLinks.length ? (
                          <div className="paper-discovery-explainers">
                            <span>Explainers / reading links</span>
                            <div className="paper-discovery-explainer-list">
                              {explanationLinks.map((link) => (
                                <a
                                  className="paper-discovery-explainer"
                                  href={link.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  title={link.summary || link.title}
                                  key={link.url}
                                >
                                  <strong>{link.title}</strong>
                                  {link.source ? <span>{link.source}</span> : null}
                                </a>
                              ))}
                            </div>
                          </div>
                        ) : null}
                        <div className="paper-discovery-links">
                          {cleanText(candidate.pdf_url) ? (
                            <a href={cleanText(candidate.pdf_url)} target="_blank" rel="noreferrer">PDF</a>
                          ) : null}
                          {cleanText(candidate.canonical_url) ? (
                            <a href={cleanText(candidate.canonical_url)} target="_blank" rel="noreferrer">Paper page</a>
                          ) : null}
                          {cleanText(candidate.doi) ? (
                            <a href={`https://doi.org/${cleanText(candidate.doi)}`} target="_blank" rel="noreferrer">DOI</a>
                          ) : null}
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  );
}

function WorkspaceHeader({ payload, paperQuery, setPaperQuery, sortMode, setSortMode, onApply }) {
  const metrics = payload.metrics || {};
  const metricRows = [
    ["papers", "Papers"],
    ["reading", "Reading"],
    ["no_pdf", "PDF missing"],
    ["needs_extraction", "Needs extraction"],
    ["claims_need_review", "Claims review"],
  ];
  return (
    <header className="paper-workspace-head">
      <div className="paper-workspace-metrics">
        {metricRows.map(([key, fallback]) => (
          <div className="paper-workspace-metric" key={key}>
            <span>{fallback}</span>
            <strong>{cleanText(metrics[key] ?? 0)}</strong>
          </div>
        ))}
      </div>
      <div className="paper-workspace-controls">
        <input
          value={paperQuery}
          onChange={(event) => setPaperQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              onApply({ query: event.currentTarget.value });
            }
          }}
          onKeyUp={(event) => {
            if (event.key === "Enter") {
              onApply({ query: event.currentTarget.value });
            }
          }}
          placeholder={label(payload.labels, "search_library", "Search title, author, tag, note...")}
        />
        <select value={sortMode} onChange={(event) => {
          setSortMode(event.target.value);
          window.setTimeout(() => onApply({ sortMode: event.target.value }), 0);
        }}>
          <option value="recent">Recently read</option>
          <option value="added">Recently added</option>
          <option value="title">Title</option>
          <option value="status">Status</option>
          <option value="claims">Research claims</option>
        </select>
        <button type="button" onClick={() => onApply({ query: paperQuery })}>
          Apply
        </button>
      </div>
      {payload.diagnostics.length ? (
        <div className="paper-workspace-diagnostics">
          {payload.diagnostics.slice(0, 3).map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      ) : null}
    </header>
  );
}

function DeletePaperDialog({ dialog, payload, onClose, onConfirm }) {
  const [confirmText, setConfirmText] = useState("");
  const [deletePdfAsset, setDeletePdfAsset] = useState(false);
  const [deleteReaderArtifacts, setDeleteReaderArtifacts] = useState(false);

  useEffect(() => {
    setConfirmText("");
    setDeletePdfAsset(false);
    setDeleteReaderArtifacts(false);
  }, [dialog?.source_id]);

  if (!dialog) {
    return null;
  }
  const sourceId = cleanText(dialog.source_id);
  const preview = dialog.preview && typeof dialog.preview === "object" ? dialog.preview : null;
  const totals = preview?.totals && typeof preview.totals === "object" ? preview.totals : {};
  const blockers = asArray(preview?.blocking_refs).filter((item) => item && typeof item === "object");
  const papers = asArray(preview?.papers).filter((item) => item && typeof item === "object");
  const firstPaper = papers[0] || {};
  const pdf = firstPaper.pdf && typeof firstPaper.pdf === "object" ? firstPaper.pdf : {};
  const artifacts = asArray(firstPaper.artifacts).filter((item) => item && typeof item === "object");
  const previewReady = Boolean(preview);
  const disabled = !previewReady || confirmText !== sourceId || blockers.length > 0 || dialog.pending;
  return (
    <div className="paper-tree-dialog-backdrop" role="presentation">
      <div className="paper-tree-dialog paper-delete-dialog" role="dialog" aria-modal="true">
        <div className="paper-tree-dialog-title">{label(payload.labels, "delete_paper", "Delete paper...")}</div>
        <div className="paper-tree-dialog-note">
          <strong>{cleanText(dialog.title || sourceId)}</strong>
          <code>{sourceId}</code>
        </div>
        {dialog.error ? <div className="paper-delete-warning">{cleanText(dialog.error)}</div> : null}
        {cleanText(pdf.warning) ? <div className="paper-delete-warning">{cleanText(pdf.warning)}</div> : null}
        {dialog.pending ? (
          <div className="paper-delete-preview">Loading deletion preview...</div>
        ) : !previewReady ? (
          <div className="paper-delete-preview">Deletion preview is required before this action can run.</div>
        ) : (
          <div className="paper-delete-preview">
            <div className="paper-delete-grid">
              <span>PDF asset</span>
              <strong>{cleanText(pdf.asset_ref) || "-"}</strong>
              <span>Artifact files</span>
              <strong>{cleanText(totals.artifact_files ?? 0)}</strong>
              <span>Active annotations</span>
              <strong>{cleanText(totals.active_annotations ?? 0)}</strong>
              <span>Chunks</span>
              <strong>{cleanText(totals.chunks ?? 0)}</strong>
              <span>Claims</span>
              <strong>{cleanText(totals.claims ?? 0)}</strong>
              <span>Citations</span>
              <strong>{cleanText(totals.citations ?? 0)}</strong>
            </div>
            {blockers.length ? (
              <div className="paper-delete-blockers">
                <strong>{label(payload.labels, "delete_paper_blocked", "Deletion blocked by references.")}</strong>
                {blockers.slice(0, 6).map((item, index) => (
                  <span key={`${cleanText(item.type)}-${cleanText(item.id)}-${index}`}>
                    {cleanText(item.type)}: {cleanText(item.id)}
                  </span>
                ))}
              </div>
            ) : null}
            {artifacts.some((item) => item.exists) ? (
              <details className="paper-delete-artifacts">
                <summary>Artifact files</summary>
                {artifacts.filter((item) => item.exists).map((item) => (
                  <span key={`${cleanText(item.kind)}-${cleanText(item.path)}`}>
                    {cleanText(item.kind)}: {cleanText(item.path)}
                  </span>
                ))}
              </details>
            ) : null}
          </div>
        )}
        <label className="paper-tree-field">
          <span>{label(payload.labels, "delete_paper_confirm", "Type the source id to confirm deletion.")}</span>
          <input value={confirmText} onChange={(event) => setConfirmText(event.target.value)} autoFocus />
        </label>
        <label className="paper-delete-check">
          <input type="checkbox" checked={deletePdfAsset} onChange={(event) => setDeletePdfAsset(event.target.checked)} />
          <span>{label(payload.labels, "delete_pdf_asset", "Delete PDF asset")}</span>
        </label>
        <label className="paper-delete-check">
          <input type="checkbox" checked={deleteReaderArtifacts} onChange={(event) => setDeleteReaderArtifacts(event.target.checked)} />
          <span>{label(payload.labels, "delete_reader_artifacts", "Delete extracted reader artifacts")}</span>
        </label>
        <div className="paper-tree-dialog-actions">
          <button type="button" onClick={onClose}>{label(payload.labels, "cancel", "Cancel")}</button>
          <button
            type="button"
            className="is-danger"
            disabled={disabled}
            onClick={() => onConfirm({
              sourceId,
              deletePdfAsset,
              deleteReaderArtifacts,
              confirm: confirmText,
            })}
          >
            {label(payload.labels, "delete_paper", "Delete paper...")}
          </button>
        </div>
      </div>
    </div>
  );
}

function PaperDetailPane({ payload, emit, onDeletePaper, onUploadPdf, workspaceBusy = false }) {
  const [translationMode, setTranslationMode] = useState(TRANSLATION_MODE_DEFAULT);
  const uploadInputRef = useRef(null);
  const detail = payload.detail || {};
  const sourceId = cleanText(detail.source_id || detail.id);
  if (!sourceId) {
    return (
      <aside className="paper-detail-pane">
        <div className="paper-detail-empty">
          {label(payload.labels, "select_paper_detail_hint", "Select a paper to see details and actions.")}
        </div>
      </aside>
    );
  }
  const badges = asArray(detail.badges).map(cleanText).filter(Boolean);
  const metrics = asArray(detail.metrics).filter((item) => item && typeof item === "object");
  const artifacts = detail.artifacts && typeof detail.artifacts === "object" ? detail.artifacts : {};
  const artifactRows = artifactEntries(artifacts);
  const readingCard = detail.reading_card && typeof detail.reading_card === "object" ? detail.reading_card : {};
  const readingBody = cleanText(readingCard.body);
  const notesSummary = cleanText(detail.summary);
  const notesBody = cleanText(detail.notes);
  const showSummaryNote = notesSummary && notesSummary !== readingBody;
  const showNotesBody = notesBody && notesBody !== readingBody;
  const canOpenReader = Boolean(detail.reader_url);
  const pdfDownload = detail.pdf_download && typeof detail.pdf_download === "object" ? detail.pdf_download : {};
  const remotePdfUrl = cleanText(detail.open_access_pdf_url || pdfDownload.url || artifacts.open_access_pdf_url);
  const pdfDownloadStatus = cleanText(pdfDownload.status || artifacts.pdf_download_status);
  const pdfDownloadError = cleanText(pdfDownload.error || artifacts.pdf_download_error);
  const canDownloadPdf = Boolean(remotePdfUrl && !canOpenReader);
  const canUploadPdf = typeof onUploadPdf === "function";
  const paperIds = [sourceId];
  const selectedTranslationMode = ["fast_body", "full_paper", "grobid_text"].includes(translationMode)
    ? translationMode
    : TRANSLATION_MODE_DEFAULT;
  const focus = cleanText(payload.focus);
  const action = cleanText(payload.action);
  const sectionClass = (name, extra = "") => [
    "paper-detail-section",
    extra,
    focus === name ? "is-focused" : "",
  ].filter(Boolean).join(" ");
  const actionClass = (name, extra = "") => [
    extra,
    action === name ? "is-suggested" : "",
  ].filter(Boolean).join(" ");
  const focusDetails = {
    claims: {
      title: label(payload.labels, "claims_focus", "Claims"),
      body: label(payload.labels, "claims_focus_hint", "Review AI candidates and promoted evidence for this paper."),
    },
    translations: {
      title: label(payload.labels, "translations_focus", "Translations"),
      body: label(payload.labels, "translations_focus_hint", "Refresh stale translation rows after extraction or segment changes."),
    },
    safety: {
      title: label(payload.labels, "safety_focus", "Publish safety"),
      body: label(payload.labels, "safety_focus_hint", "Check visibility and private-source blockers before export."),
    },
    metadata: {
      title: label(payload.labels, "metadata_focus", "Metadata"),
      body: label(payload.labels, "metadata_focus_hint", "Check title, collection placement, duplicate risk, and source metadata."),
    },
  };
  const focusDetail = focusDetails[focus];
  const returnHref = safeReturnHref(payload.returnUrl);
  return (
    <aside className="paper-detail-pane">
      {payload.returnTo === "overview" ? (
        <a className="paper-return-link" href={returnHref}>
          {label(payload.labels, "back_to_overview", "Back to Overview")}
        </a>
      ) : null}
      <div className="paper-detail-title">{cleanText(detail.title || sourceId)}</div>
      {detail.meta ? <div className="paper-detail-meta">{cleanText(detail.meta)}</div> : null}
      {detail.status_label ? (
        <div className={`paper-detail-status is-${cleanText(detail.status || "inbox").replaceAll("_", "-")}`}>
          {cleanText(detail.status_label)}
        </div>
      ) : null}
      <div className="paper-detail-badges">
        {badges.slice(0, 8).map((badge) => (
          <span key={badge}>{badge}</span>
        ))}
      </div>
      <code className="paper-detail-source">{sourceId}</code>
      {action ? (
        <div className="paper-deep-link-hint" data-deep-link-action={action}>
          <span>{label(payload.labels, "overview_suggested_action", "Suggested from Overview")}</span>
          <strong>{deepLinkActionLabel(payload, action)}</strong>
        </div>
      ) : null}

      <section className={sectionClass("reading", "paper-reading-card")} data-focus-section="reading">
        <div className="paper-detail-section-title">
          {label(payload.labels, "abstract_preview", "Abstract Preview")}
        </div>
        {cleanText(readingCard.source_label) ? (
          <div className="paper-reading-source">
            {label(payload.labels, "preview_source", "From {source}").replace("{source}", cleanText(readingCard.source_label))}
          </div>
        ) : null}
        {readingBody ? (
          <p className="paper-reading-body">{readingBody}</p>
        ) : (
          <p className="paper-reading-empty">
            {cleanText(readingCard.empty_message) || label(payload.labels, "no_abstract_preview", "No abstract or summary yet.")}
          </p>
        )}
        {cleanText(readingCard.why_relevant) ? (
          <div className="paper-reading-related">
            <span>{label(payload.labels, "why_relevant", "Why it matters")}</span>
            <p>{cleanText(readingCard.why_relevant)}</p>
          </div>
        ) : null}
      </section>

      <div className="paper-detail-metrics">
        {metrics.map((item) => (
          <div className="paper-detail-metric" key={cleanText(item.label)}>
            <span>{cleanText(item.label)}</span>
            <strong>{cleanText(item.value)}</strong>
          </div>
        ))}
      </div>

      <div className="paper-detail-actions">
        <button
          type="button"
          className={actionClass("open_reader", "is-primary")}
          disabled={!canOpenReader}
          onClick={() => {
            if (canOpenReader) {
              window.open(cleanText(detail.reader_url), "_blank", "noopener,noreferrer");
            }
          }}
        >
          {label(payload.labels, "open_reader", "Open Reader")}
        </button>
        <button
          type="button"
          className={actionClass("attach_pdf")}
          disabled={!canDownloadPdf || workspaceBusy}
          title={pdfDownloadError || remotePdfUrl}
          onClick={() => emit(makeEvent("paper_library_download_pdf", { paper_ids: paperIds }))}
        >
          {label(
            payload.labels,
            pdfDownloadStatus === "failed" ? "retry_pdf_download" : "download_pdf",
            pdfDownloadStatus === "failed" ? "Retry PDF" : "Download PDF",
          )}
        </button>
        <div className="paper-upload-control">
          <input
            ref={uploadInputRef}
            type="file"
            accept="application/pdf,.pdf"
            onChange={(event) => {
              const file = event.target.files?.[0];
              event.target.value = "";
              if (file && canUploadPdf) {
                onUploadPdf(sourceId, file);
              }
            }}
          />
          <button
            type="button"
            className={actionClass("attach_pdf")}
            disabled={!canUploadPdf || workspaceBusy}
            onClick={() => uploadInputRef.current?.click()}
          >
            {label(payload.labels, "upload_pdf", "Upload PDF")}
          </button>
        </div>
        <button
          type="button"
          className={actionClass("run_extraction")}
          disabled={!canOpenReader || workspaceBusy}
          title={label(payload.labels, "run_extraction_hint", "Prepare reader artifacts and reuse fallback text after recent GROBID timeouts.")}
          onClick={() => emit(makeEvent("paper_library_run_extraction", { paper_ids: paperIds }))}
        >
          {label(payload.labels, "run_extraction", "Run extraction")}
        </button>
        <button
          type="button"
          className={actionClass("force_grobid_upgrade", "is-force-grobid")}
          disabled={!canOpenReader || workspaceBusy}
          title={label(payload.labels, "force_grobid_upgrade_hint", "Retry GROBID even when a recent timeout is cooling down.")}
          onClick={() => emit(makeEvent("paper_library_run_extraction", {
            paper_ids: paperIds,
            force_grobid: true,
          }))}
        >
          {label(payload.labels, "force_grobid_upgrade", "Force GROBID upgrade")}
        </button>
        <button
          type="button"
          className={actionClass("auto_chunk")}
          disabled={workspaceBusy}
          onClick={() => emit(makeEvent("paper_library_auto_chunk", { paper_ids: paperIds }))}
        >
          {label(payload.labels, "auto_chunk", "Auto chunk")}
        </button>
        <div className="paper-translation-control">
          <select
            aria-label={label(payload.labels, "translation_mode", "Translation mode")}
            value={selectedTranslationMode}
            disabled={!canOpenReader || workspaceBusy}
            onChange={(event) => setTranslationMode(event.target.value)}
          >
            <option value="fast_body">{label(payload.labels, "translation_mode_fast_body", "Fast body")}</option>
            <option value="full_paper">{label(payload.labels, "translation_mode_full_paper", "Full paper")}</option>
            <option value="grobid_text">{label(payload.labels, "translation_mode_grobid_text", "GROBID paragraphs")}</option>
          </select>
          <button
            type="button"
            className={actionClass("retry_translation")}
            disabled={!canOpenReader || workspaceBusy}
            onClick={() => emit(makeEvent("paper_library_retry_translation", translationModePayload(paperIds, selectedTranslationMode)))}
          >
            {label(payload.labels, "retry_translation", "Retry translation")}
          </button>
        </div>
      </div>

      {showSummaryNote || showNotesBody || detail.url || remotePdfUrl || pdfDownloadError ? (
        <section className={sectionClass("metadata")} data-focus-section="metadata">
          <div className="paper-detail-section-title">Notes</div>
          {showSummaryNote ? <p>{notesSummary}</p> : null}
          {showNotesBody ? <p>{notesBody}</p> : null}
          {pdfDownloadError ? <p>{pdfDownloadError}</p> : null}
          {detail.url ? (
            <a href={cleanText(detail.url)} target="_blank" rel="noreferrer">
              Open source
            </a>
          ) : null}
          {remotePdfUrl ? (
            <a href={remotePdfUrl} target="_blank" rel="noreferrer">
              {label(payload.labels, "open_remote_pdf", "Open remote PDF")}
            </a>
          ) : null}
        </section>
      ) : null}

      {focusDetail ? (
        <section className={sectionClass(focus, "paper-detail-followup")} data-focus-section={focus}>
          <div className="paper-detail-section-title">{focusDetail.title}</div>
          <p>{focusDetail.body}</p>
        </section>
      ) : null}

      <section className={sectionClass("artifacts")} data-focus-section="artifacts">
        <div className="paper-detail-section-title">Artifacts</div>
        <dl className="paper-detail-artifacts">
          {artifactRows.map(([key, value]) => (
            <React.Fragment key={key}>
              <dt>{artifactLabel(payload.labels, key)}</dt>
              <dd>{cleanText(value) || "-"}</dd>
            </React.Fragment>
          ))}
        </dl>
      </section>

      <section className="paper-detail-section paper-detail-danger">
        <div className="paper-detail-section-title">{label(payload.labels, "danger_zone", "Danger zone")}</div>
        <button type="button" onClick={() => onDeletePaper({ sourceId, title: cleanText(detail.title || sourceId) })}>
          {label(payload.labels, "delete_paper", "Delete paper...")}
        </button>
      </section>
    </aside>
  );
}

function WorkspaceTaskProgress({ job }) {
  if (!job) {
    return null;
  }
  const warnings = Number(job.warning_count || 0);
  const warningItems = asArray(job.warnings).map(cleanText).filter(Boolean).slice(0, 2);
  const updated = Number(job.updated || 0);
  const saved = Number(job.saved || 0);
  return (
    <div className={`paper-workspace-task-progress is-${cleanText(job.status || "running")}`}>
      <div className="paper-workspace-task-progress-top">
        <strong>{cleanText(job.message) || "Working..."}</strong>
        <span>{workspaceProgressText(job)}</span>
      </div>
      <div className="paper-workspace-task-progress-track">
        <span style={{ width: `${workspaceProgressPercent(job)}%` }} />
      </div>
      <div className="paper-workspace-task-progress-meta">
        {cleanText(job.source_id) ? <span>{cleanText(job.source_id)}</span> : null}
        {cleanText(job.scope) ? <span>{cleanText(job.scope)}</span> : null}
        {updated ? <span>{updated} updated</span> : null}
        {!updated && saved ? <span>{saved} saved</span> : null}
        {warnings ? <span>{warnings} warnings</span> : null}
        {warningItems.map((item) => (
          <span className="paper-workspace-task-warning" key={item}>{item}</span>
        ))}
      </div>
    </div>
  );
}

function App() {
  const runtime = useMemo(() => runtimeMode(), []);
  const standalone = runtime !== "streamlit";
  const profile = useMemo(() => bootstrapProfile(), []);
  const [args, setArgs] = useState({});
  const [query, setQuery] = useState("");
  const [paperQuery, setPaperQuery] = useState("");
  const [sortMode, setSortMode] = useState("recent");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const [workspaceJob, setWorkspaceJob] = useState(null);
  const [expanded, setExpanded] = useState(new Set());
  const [selectedPaperIds, setSelectedPaperIds] = useState(new Set());
  const [menu, setMenu] = useState(null);
  const [dialog, setDialog] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState(null);
  const [dragPayload, setDragPayload] = useState(null);
  const [dragTarget, setDragTarget] = useState(null);
  const payload = useMemo(() => normalizePayload(args.payload), [args.payload]);
  const activePayload = useMemo(
    () => ({ ...payload, selectedPaperIds: [...selectedPaperIds] }),
    [payload, selectedPaperIds],
  );
  const workspaceBusy = loading || isJobRunning(workspaceJob);
  const filteredSections = useMemo(() => {
    return payload.sections.map((section) => ({
      ...section,
      items: filterItems(section.items, query),
    }));
  }, [payload.sections, query]);

  const applyStandalonePayload = (nextPayload, nextNotice = "") => {
    if (!nextPayload || typeof nextPayload !== "object") {
      return;
    }
    setArgs({ payload: nextPayload });
    setNotice(nextNotice);
    setPaperQuery(cleanText(nextPayload.query || ""));
    setSortMode(cleanText(nextPayload.sort_mode || "recent") || "recent");
    updateUrlParams({
      profile,
      view: nextPayload.active_view || "",
      node_id: nextPayload.active_node_id || "",
      query: nextPayload.query || "",
      sort: nextPayload.sort_mode || "recent",
      detail_id: nextPayload.detail_id || "",
      focus: nextPayload.focus || "",
      action: nextPayload.action || "",
      return_to: nextPayload.return_to || "",
      return_url: nextPayload.return_url || "",
    });
  };

  const loadStandalonePayload = async (overrides = {}, options = {}) => {
    const setBusy = options.setBusy !== false;
    const clearNotice = options.clearNotice !== false;
    const preserveNoticeOnError = options.preserveNoticeOnError === true;
    if (!profile) {
      if (!preserveNoticeOnError) {
        setNotice("Missing profile in URL.");
      }
      return;
    }
    if (setBusy) {
      setLoading(true);
    }
    try {
      const url = new URL(paperLibraryApiUrl(profile), window.location.origin);
      const params = new URLSearchParams(window.location.search);
      const nextQuery = overrides.query ?? paperQuery ?? params.get("query") ?? "";
      const nextSort = overrides.sortMode ?? sortMode ?? params.get("sort") ?? "recent";
      const nextView = overrides.view ?? params.get("view") ?? payload.activeView ?? "all";
      const nextNode = overrides.node_id ?? params.get("node_id") ?? payload.activeNodeId ?? "";
      const nextDetail = overrides.detail_id ?? params.get("detail_id") ?? payload.detailId ?? "";
      const nextFocus = overrides.focus ?? params.get("focus") ?? payload.focus ?? "";
      const nextAction = overrides.action ?? params.get("action") ?? payload.action ?? "";
      const nextReturnTo = overrides.return_to ?? params.get("return_to") ?? payload.returnTo ?? "";
      const nextReturnUrl = overrides.return_url ?? params.get("return_url") ?? payload.returnUrl ?? "";
      if (nextView) url.searchParams.set("view", nextView);
      if (nextNode) url.searchParams.set("node_id", nextNode);
      if (nextQuery) url.searchParams.set("query", nextQuery);
      if (nextSort) url.searchParams.set("sort", nextSort);
      if (nextDetail) url.searchParams.set("detail_id", nextDetail);
      if (nextFocus) url.searchParams.set("focus", nextFocus);
      if (nextAction) url.searchParams.set("action", nextAction);
      if (nextReturnTo) url.searchParams.set("return_to", nextReturnTo);
      if (nextReturnUrl) url.searchParams.set("return_url", nextReturnUrl);
      const data = await jsonRequest(url.toString(), { method: "GET" });
      setArgs({ payload: data.payload || data });
      setPaperQuery(cleanText((data.payload || data).query || nextQuery));
      setSortMode(cleanText((data.payload || data).sort_mode || nextSort) || "recent");
      updateUrlParams({
        profile,
        view: (data.payload || data).active_view || nextView,
        node_id: (data.payload || data).active_node_id || "",
        query: (data.payload || data).query || nextQuery,
        sort: (data.payload || data).sort_mode || nextSort,
        detail_id: (data.payload || data).detail_id || "",
        focus: (data.payload || data).focus || nextFocus,
        action: (data.payload || data).action || nextAction,
        return_to: (data.payload || data).return_to || nextReturnTo,
        return_url: (data.payload || data).return_url || nextReturnUrl,
      });
      if (clearNotice) {
        setNotice("");
      }
    } catch (error) {
      if (!preserveNoticeOnError) {
        setNotice(error.message || String(error));
      }
    } finally {
      if (setBusy) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    if (standalone) {
      const bootstrapPayload = window.__NBLANE_PAPER_LIBRARY_BOOTSTRAP__?.payload;
      if (bootstrapPayload) {
        setArgs({ payload: bootstrapPayload });
        setPaperQuery(cleanText(bootstrapPayload.query || ""));
        setSortMode(cleanText(bootstrapPayload.sort_mode || "recent") || "recent");
      } else {
        loadStandalonePayload();
      }
      return undefined;
    }
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

  useEffect(() => {
    if (!standalone) {
      setPaperQuery(cleanText(payload.query || ""));
      setSortMode(cleanText(payload.sortMode || "recent") || "recent");
    }
  }, [payload.query, payload.sortMode, standalone]);

  useEffect(() => {
    setSelectedPaperIds(new Set(payload.selectedPaperIds));
  }, [payload.selectedPaperIds.join("\u0000")]);

  useEffect(() => {
    const ids = new Set();
    for (const section of payload.sections) {
      for (const id of expandableIds(section.items)) {
        ids.add(id);
      }
    }
    setExpanded(ids);
  }, [payload.sections]);

  useEffect(() => {
    if (!standalone) {
      window.setTimeout(() => Streamlit.setFrameHeight(), 0);
    }
  }, [filteredSections, menu, dialog, deleteDialog, expanded, workspaceJob, standalone]);

  const eventState = () => ({
    query: paperQuery,
    sort_mode: sortMode,
    view: payload.activeView,
    node_id: payload.activeNodeId,
    detail_id: payload.detailId,
    focus: payload.focus,
    action: payload.action,
    return_to: payload.returnTo,
    return_url: payload.returnUrl,
  });

  const waitForWorkspaceJob = async (jobId) => {
    let statusMisses = 0;
    let statusOfflineSince = 0;
    let lastJob = null;
    for (;;) {
      await sleep(1000);
      let data;
      try {
        data = await jsonRequest(paperLibraryApiUrl(profile, `/events/jobs/${jobId}`), {
          method: "GET",
          timeoutMs: WORKSPACE_JOB_POLL_TIMEOUT_MS,
        });
        statusMisses = 0;
        statusOfflineSince = 0;
      } catch (error) {
        if (isWorkspaceJobLostError(error)) {
          const progress = workspaceJobSavedProgressText(lastJob);
          const message = progress
            ? `Paper Library action was interrupted after saved progress (${progress}). The saved translations are kept; retry to continue the remaining units.`
            : "Paper Library action was interrupted. Reloaded the latest saved paper state; retry to continue.";
          const interrupted = new Error(message);
          interrupted.recoverPayload = true;
          throw interrupted;
        }
        const now = Date.now();
        if (!isTransientWorkspaceJobPollError(error)) {
          throw error;
        }
        if (!statusOfflineSince) {
          statusOfflineSince = now;
        }
        statusMisses += 1;
        const offlineMs = now - statusOfflineSince;
        if (statusMisses >= WORKSPACE_JOB_MAX_STATUS_MISSES && offlineMs >= WORKSPACE_JOB_RECONNECT_GRACE_MS) {
          const progress = workspaceJobSavedProgressText(lastJob);
          const message = progress
            ? `Lost connection to the Paper Library action after saved progress (${progress}). The saved translations are kept; retry once 8502 is back.`
            : `Lost connection to the Paper Library action for ${Math.round(WORKSPACE_JOB_RECONNECT_GRACE_MS / 1000)}s.`;
          const disconnected = new Error(message);
          disconnected.recoverPayload = true;
          throw disconnected;
        }
        const remainingSeconds = Math.max(0, Math.ceil((WORKSPACE_JOB_RECONNECT_GRACE_MS - offlineMs) / 1000));
        setWorkspaceJob((current) => (
          current
            ? {
                ...current,
                status: "running",
                phase: cleanText(current.phase || "waiting"),
                message: `Reconnecting to job status... ${remainingSeconds}s grace remaining`,
              }
            : current
        ));
        continue;
      }
      const job = data.job && typeof data.job === "object" ? data.job : {};
      lastJob = job;
      setWorkspaceJob(job);
      if (job.status === "done") {
        return data.result || {};
      }
      if (job.status === "failed") {
        throw new Error(cleanText(job.error || job.message) || "Paper Library action failed.");
      }
    }
  };

  const applyEventResponse = (data, fallbackNotice = "") => {
    const nextPayload = data.payload || data;
    setArgs({ payload: nextPayload });
    setNotice(data.result?.message || data.message || fallbackNotice || "");
    setPaperQuery(cleanText(nextPayload.query || paperQuery));
    setSortMode(cleanText(nextPayload.sort_mode || sortMode) || "recent");
    updateUrlParams({
      profile,
      view: nextPayload.active_view || "",
      node_id: nextPayload.active_node_id || "",
      query: nextPayload.query || "",
      sort: nextPayload.sort_mode || "recent",
      detail_id: nextPayload.detail_id || "",
      focus: nextPayload.focus || "",
      action: nextPayload.action || "",
      return_to: nextPayload.return_to || "",
      return_url: nextPayload.return_url || "",
    });
  };

  const emit = async (event) => {
    if (!standalone) {
      Streamlit.setComponentValue(event);
      window.setTimeout(() => Streamlit.setFrameHeight(), 0);
      return { ok: true };
    }
    if (!profile) {
      setNotice("Missing profile in URL.");
      return { ok: false };
    }
    if (workspaceBusy) {
      setNotice("Another Paper Library action is still running.");
      return { ok: false };
    }
    setLoading(true);
    const busyNotice = eventBusyNotice(payload, event);
    if (busyNotice) {
      setNotice(busyNotice);
    }
    try {
      if (shouldRunEventAsJob(event)) {
        setWorkspaceJob({
          status: "queued",
          phase: "queued",
          event_action: cleanText(event.action),
          message: busyNotice || "Queued Paper Library action.",
          elapsed_ms: 0,
        });
        const started = await jsonRequest(paperLibraryApiUrl(profile, "/events/jobs"), {
          method: "POST",
          timeoutMs: 20000,
          body: JSON.stringify({
            ...event,
            state: eventState(),
          }),
        });
        if (started.job) {
          setWorkspaceJob(started.job);
        }
        const jobId = cleanText(started.job_id || started.job?.job_id);
        if (!jobId) {
          throw new Error("Paper Library action job did not start.");
        }
        const data = await waitForWorkspaceJob(jobId);
        applyEventResponse(data, "Paper Library action finished.");
        return { ok: data.ok !== false, data };
      }
      setWorkspaceJob(null);
      const data = await jsonRequest(paperLibraryApiUrl(profile, "/events"), {
        method: "POST",
        timeoutMs: 180000,
        body: JSON.stringify({
          ...event,
          state: eventState(),
        }),
      });
      applyEventResponse(data);
      return { ok: data.ok !== false, data };
    } catch (error) {
      setWorkspaceJob((current) => (
        current
          ? { ...current, status: "failed", phase: "failed", message: error.message || String(error), error: error.message || String(error) }
          : current
      ));
      setNotice(error.message || String(error));
      if (standalone && error?.recoverPayload) {
        await loadStandalonePayload({}, { setBusy: false, clearNotice: false, preserveNoticeOnError: true });
      }
      return { ok: false, error };
    } finally {
      setLoading(false);
    }
  };
  const uploadPdf = async (sourceId, file) => {
    const cleanSourceId = cleanText(sourceId);
    if (!standalone) {
      setNotice("Open the 8502 Paper Library Workspace to upload PDFs.");
      return { ok: false };
    }
    if (!profile || !cleanSourceId) {
      setNotice("Missing profile or paper id.");
      return { ok: false };
    }
    if (!file) {
      setNotice("Choose a PDF file first.");
      return { ok: false };
    }
    if (workspaceBusy) {
      setNotice("Another Paper Library action is still running.");
      return { ok: false };
    }
    setLoading(true);
    setNotice(`Uploading ${cleanText(file.name) || "PDF"}...`);
    try {
      const formData = new FormData();
      formData.append("file", file, file.name || "paper.pdf");
      const data = await formRequest(
        paperApiUrl(profile, cleanSourceId, "/pdf-upload"),
        formData,
        { timeoutMs: 180000 },
      );
      applyEventResponse(data, "Uploaded PDF.");
      return { ok: data.ok !== false, data };
    } catch (error) {
      setNotice(error.message || String(error));
      return { ok: false, error };
    } finally {
      setLoading(false);
    }
  };
  const requestDeletePreview = async ({ sourceId, title }) => {
    const base = { source_id: sourceId, title, pending: standalone };
    setDeleteDialog(base);
    if (!standalone) {
      setDeleteDialog({
        ...base,
        pending: false,
        error: "Open the 8502 Paper Library Workspace to preview and delete papers.",
      });
      return;
    }
    setLoading(true);
    try {
      const data = await jsonRequest(paperLibraryApiUrl(profile, "/events"), {
        method: "POST",
        body: JSON.stringify({
          action: "paper_library_delete_paper_preview",
          event_id: eventId(),
          payload: { paper_ids: [sourceId] },
          state: {
            query: paperQuery,
            sort_mode: sortMode,
            view: payload.activeView,
            node_id: payload.activeNodeId,
            detail_id: payload.detailId,
            focus: payload.focus,
            action: payload.action,
            return_to: payload.returnTo,
            return_url: payload.returnUrl,
          },
        }),
      });
      setDeleteDialog({ ...base, pending: false, preview: data.result?.data?.delete_preview || data.result?.delete_preview || null });
    } catch (error) {
      setDeleteDialog({ ...base, pending: false, error: error.message || String(error) });
    } finally {
      setLoading(false);
    }
  };
  const confirmDeletePaper = async ({ sourceId, deletePdfAsset, deleteReaderArtifacts, confirm }) => {
    const result = await emit(makeEvent("paper_library_delete_paper_record", {
      paper_ids: [sourceId],
      confirm,
      delete_pdf_asset: deletePdfAsset,
      delete_reader_artifacts: deleteReaderArtifacts,
    }));
    if (result?.ok !== false) {
      setDeleteDialog(null);
    }
  };
  const handleSelect = (item) => {
    const type = nodeType(item);
    if (type === "view") {
      emit(makeEvent("paper_library_select_view", { view_id: nodeId(item) }));
    } else if (type === "collection" || type === "collection_root") {
      emit(makeEvent("paper_library_select_collection", {
        node_id: type === "collection_root" ? "" : nodeId(item),
      }));
    }
  };
  const handleAction = (kind, data) => {
    if (kind === "emit") {
      emit(data);
      return;
    }
    if (kind.startsWith("dialog:")) {
      setDialog({ kind: kind.split(":", 2)[1], ...data });
    }
  };
  const dropCollection = (targetId, position = "into", event = null) => {
    if (!dragPayload) {
      return;
    }
    if (dragPayload.kind === "collection") {
      if (!dragPayload.nodeId || dragPayload.nodeId === targetId) {
        return;
      }
      const eventPayload = {
        node_id: dragPayload.nodeId,
      };
      if (position === "before") {
        eventPayload.before_node_id = targetId;
      } else if (position === "after") {
        eventPayload.after_node_id = targetId;
      } else {
        eventPayload.parent_id = targetId;
      }
      emit(makeEvent("paper_library_move_collection", eventPayload));
    } else if (dragPayload.kind === "papers") {
      const paperIds = asArray(dragPayload.paperIds).map(cleanText).filter(Boolean);
      if (!paperIds.length) {
        return;
      }
      emit(makeEvent("paper_library_drop_papers_to_collection", {
        node_id: targetId,
        paper_ids: paperIds,
        append: Boolean(dragPayload.append || event?.altKey || event?.shiftKey),
      }));
    }
    setDragPayload(null);
    setDragTarget(null);
  };

  const liveSelectedCount = selectedPaperIds.size;
  const hasPapers = payload.papers.length > 0 || args.payload?.papers;
  const treePane = (
    <>
      <div className="paper-tree-toolbar">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={label(payload.labels, "search_collections", "Search collections")}
        />
        <button type="button" onClick={() => {
          const ids = new Set();
          for (const section of payload.sections) {
            for (const id of expandableIds(section.items)) {
              ids.add(id);
            }
          }
          setExpanded(ids);
        }}>
          {label(payload.labels, "expand_all", "Expand all")}
        </button>
        <button type="button" onClick={() => setExpanded(new Set())}>
          {label(payload.labels, "collapse_all", "Collapse all")}
        </button>
      </div>
      {liveSelectedCount ? (
        <div className="paper-tree-selection">
          {label(payload.labels, "selected_papers", "{count} papers selected").replace("{count}", liveSelectedCount)}
        </div>
      ) : null}
      <div className="paper-tree-sections">
        {filteredSections.map((section) => (
          <Section
            key={section.id || section.title}
            section={section}
            payload={activePayload}
            expanded={expanded}
            dragTarget={dragTarget}
            onToggle={(id) => {
              const next = new Set(expanded);
              if (next.has(id)) {
                next.delete(id);
              } else {
                next.add(id);
              }
              setExpanded(next);
            }}
            onSelect={handleSelect}
            onMenu={(event, item) => setMenu({ item, x: event.clientX, y: event.clientY })}
            onDialog={setDialog}
            onDropCollection={dropCollection}
            onDragStart={(nodeIdValue) => setDragPayload({ kind: "collection", nodeId: nodeIdValue })}
            onDragTarget={setDragTarget}
          />
        ))}
      </div>
    </>
  );
  return (
    <div className={`paper-tree-shell ${hasPapers ? "has-papers" : ""} ${standalone ? "is-standalone" : ""}`}>
      {standalone ? (
        <>
          <DiscoveryPanel
            payload={payload}
            profile={profile}
            workspaceBusy={workspaceBusy}
            onImported={(data) => applyStandalonePayload(data.payload, data.message || "")}
          />
          <WorkspaceHeader
            payload={payload}
            paperQuery={paperQuery}
            setPaperQuery={setPaperQuery}
            sortMode={sortMode}
            setSortMode={setSortMode}
            onApply={(overrides = {}) => loadStandalonePayload({ query: paperQuery, ...overrides })}
          />
        </>
      ) : null}
      {notice ? <div className="paper-workspace-notice">{notice}</div> : null}
      <WorkspaceTaskProgress job={workspaceJob} />
      {loading && !workspaceJob ? <div className="paper-workspace-loading">Loading...</div> : null}
      {hasPapers ? (
        <div className="paper-workbench">
          <aside className="paper-tree-pane">{treePane}</aside>
          <PaperList
            payload={payload}
            selectedPaperIds={selectedPaperIds}
            setSelectedPaperIds={setSelectedPaperIds}
            setDragPayload={setDragPayload}
            emit={emit}
            onPaperMenu={(event, paper, paperIds) => setMenu({
              item: { ...paper, type: "paper" },
              paperIds,
              x: event.clientX,
              y: event.clientY,
            })}
          />
          <PaperDetailPane
            payload={payload}
            emit={emit}
            onDeletePaper={requestDeletePreview}
            onUploadPdf={uploadPdf}
            workspaceBusy={workspaceBusy}
          />
        </div>
      ) : treePane}
      <ContextMenu
        menu={menu}
        payload={activePayload}
        onClose={() => setMenu(null)}
        onAction={handleAction}
      />
      <Dialog
        dialog={dialog}
        payload={payload}
        onClose={() => setDialog(null)}
        onEmit={emit}
      />
      <DeletePaperDialog
        dialog={deleteDialog}
        payload={payload}
        onClose={() => setDeleteDialog(null)}
        onConfirm={confirmDeletePaper}
      />
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
