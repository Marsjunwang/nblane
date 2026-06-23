import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import ForceGraph3D from "react-force-graph-3d";
import * as THREE from "three";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";

import "./style.css";
import {
  asArray,
  asObject,
  cleanText,
  goalDisplay,
  goalDraftFromFormData,
  normalizePayload,
} from "./payload.js";
import {
  archiveGoalEvent,
  confirmGoalSkillLinksEvent,
  createGoalSubmitEvent,
  editGoalSubmitEvent,
  makeEvent,
  manualGoalSkillLinkEvent,
  navigationEvent,
  openProfileContextEvent,
  requestGoalSkillAiMatchEvent,
  requestGoalSkillRuleMatchEvent,
  setPrimaryGoalEvent,
} from "./events.js";

const READY = "streamlit:componentReady";
const SET_VALUE = "streamlit:setComponentValue";
const SET_HEIGHT = "streamlit:setFrameHeight";
const RENDER = "streamlit:render";
const SKILL_RING_SIZE = 132;
const SKILL_RING_STROKE = 12;
const SKILL_RING_RADIUS = 52;

const NODE_COLORS = {
  north_star: "#6b4fb3",
  goal: "#21685b",
  project_case: "#6f7b82",
  skill: "#2f6fed",
  gap: "#9f1d1d",
  next_action: "#2f9e73",
  task: "#8b6f20",
  daily_work: "#8b6f20",
  research: "#b35a34",
  agent_run: "#52606d",
  source: "#b35a34",
  evidence: "#6b4fb3",
  evidence_candidate: "#6b4fb3",
  atomic_evidence: "#6b4fb3",
  composite_evidence: "#6b4fb3",
  claim: "#21685b",
  output: "#b35a34",
  feedback: "#2f9e73",
  capacity: "#68716f",
  health: "#68716f",
};

const EDGE_COLORS = {
  alignment: "#7a5ac4",
  contains: "#71827d",
  generated_by: "#b7822b",
  source_to_candidate: "#b35a34",
  review: "#6b4fb3",
  derives: "#8b6f20",
  supports: "#21685b",
  drives: "#2f6fed",
  produces: "#b35a34",
  feedback: "#2f9e73",
  watches: "#9f1d1d",
  link: "#60716b",
};

const EDGE_WIDTHS = {
  alignment: 1.35,
  contains: 1.1,
  generated_by: 1.25,
  source_to_candidate: 1.55,
  review: 1.45,
  derives: 1.35,
  supports: 1.7,
  drives: 1.75,
  produces: 1.55,
  feedback: 1.45,
  watches: 1.1,
};

const GRAPH_3D_MIN_HEIGHT = 520;

// ── Star-tree (role-based) visual model ──────────────────────────────────────
// Block B replaces the flat force-directed 3D graph with a deterministic
// "star tree": roles map to visual prototypes pinned at fixed coordinates, and
// "Live" comes from a breathing animation loop rather than force drift.
const TREE_ROLES = new Set([
  "trunk",
  "direction",
  "branch",
  "leaf",
  "fruit",
  "star",
  "constellation",
]);
const SAND_ROLE = "sand";

const ROLE_COLORS = {
  trunk: "#7d5fd0",
  direction: "#21685b",
  branch: "#7d8a91",
  leaf: "#3f9e63",
  fruit: "#c2683a",
  star: "#bcd4ff",
  constellation: "#e8d27a",
  sand: "#c4b186",
};

// Star brightness by skill status — the dome dims for locked, blazes for expert.
const STAR_STATUS_EMISSIVE = {
  locked: 0.05,
  learning: 0.18,
  solid: 0.4,
  expert: 0.7,
};

// Tree skeleton dimensions (world units, y is up).
const TREE_HEIGHT = 92;
const STAR_DOME_CENTER_Y = TREE_HEIGHT + 8;
const STAR_DOME_RADIUS = 96;
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

const FALLBACK_LAYERS = [
  "direction",
  "objective",
  "work_context",
  "activity",
  "source",
  "evidence",
  "claim",
  "capability",
  "output",
  "feedback",
  "governance",
];

const LAYER_LABELS = {
  direction: "Direction",
  objective: "Objective",
  work_context: "Work Context",
  activity: "Activity",
  source: "Source",
  evidence: "Evidence",
  claim: "Claim",
  capability: "Capability",
  output: "Output",
  feedback: "Feedback",
  governance: "Governance",
};

const SKILL_STATUS_META = [
  { key: "expert", color: "#2f9e73", fallback: "Expert" },
  { key: "solid", color: "#2f6fed", fallback: "Solid" },
  { key: "learning", color: "#b7822b", fallback: "Learning" },
  { key: "locked", color: "#a2afb9", fallback: "Locked" },
];

const EXPLORE_LANES = [
  {
    key: "direction",
    labelKey: "dashboard_explore_lane_direction",
    fallback: "Direction",
    layers: ["direction", "objective"],
    types: ["north_star", "goal"],
  },
  {
    key: "work_source",
    labelKey: "dashboard_explore_lane_work_source",
    fallback: "Work / Source",
    layers: ["work_context", "activity", "source"],
    types: ["project_case", "task", "daily_work", "research", "agent_run", "source"],
  },
  {
    key: "evidence_claim",
    labelKey: "dashboard_explore_lane_evidence_claim",
    fallback: "Evidence / Claim",
    layers: ["evidence", "claim"],
    types: ["evidence", "evidence_candidate", "atomic_evidence", "composite_evidence", "claim"],
  },
  {
    key: "skill_gap",
    labelKey: "dashboard_explore_lane_skill_gap",
    fallback: "Skill / Gap",
    layers: ["capability", "governance"],
    types: ["skill", "gap", "next_action", "capacity", "health"],
  },
  {
    key: "output_feedback",
    labelKey: "dashboard_explore_lane_output_feedback",
    fallback: "Output / Feedback",
    layers: ["output", "feedback"],
    types: ["output", "feedback"],
  },
];

function sendBack(type, payload) {
  if (window.parent === window) {
    return;
  }
  window.parent.postMessage({ isStreamlitMessage: true, type, ...payload }, "*");
}

function setFrameHeight(height) {
  sendBack(SET_HEIGHT, { height: Math.max(720, Math.ceil(height || document.body.scrollHeight || 980)) });
}

function setComponentValue(value) {
  sendBack(SET_VALUE, { value, dataType: "json" });
}

function initStreamlitBridge(onRender) {
  window.addEventListener("message", (event) => {
    if (event.data?.type !== RENDER) {
      return;
    }
    onRender(event.data?.args || {});
  });
  sendBack(READY, { apiVersion: 1 });
  window.setTimeout(() => setFrameHeight(), 0);
}

function standaloneConfig() {
  const config = window.__NBLANE_DASHBOARD_STANDALONE__;
  return config && typeof config === "object" ? config : null;
}

function standaloneTargetUrl(path, streamlitBase = "") {
  const clean = cleanText(path);
  if (!clean) {
    return "";
  }
  if (/^https?:\/\//i.test(clean)) {
    return clean;
  }
  const base = cleanText(streamlitBase, "http://127.0.0.1:8503").replace(/\/+$/, "");
  return `${base}/${clean.replace(/^\/+/, "")}`;
}

const DASHBOARD_VIEW_MODES = new Set(["focus", "canvas", "attention", "3d"]);
const READ_ONLY_ACTIONS = new Set(["navigate", "set_north_star_display_open_profile_context"]);

function initialDashboardViewMode(args) {
  if (typeof window !== "undefined") {
    const requested = cleanText(new URLSearchParams(window.location.search).get("view"));
    if (DASHBOARD_VIEW_MODES.has(requested)) {
      return requested;
    }
  }
  return args?.standalone && !args?.embed ? "3d" : "focus";
}

function urlSearchParam(name) {
  if (typeof window === "undefined") {
    return "";
  }
  return cleanText(new URLSearchParams(window.location.search).get(name));
}

function initialDashboardNodeId() {
  return urlSearchParam("node");
}

function dashboardNodeUrl(url, nodeId, view = "3d") {
  const cleanUrl = cleanText(url);
  const cleanNode = cleanText(nodeId);
  if (!cleanUrl || !cleanNode) {
    return cleanUrl;
  }
  try {
    const parsed = new URL(cleanUrl, typeof window !== "undefined" ? window.location.href : "http://127.0.0.1");
    parsed.searchParams.set("view", cleanText(view, "3d"));
    parsed.searchParams.set("node", cleanNode);
    return parsed.toString();
  } catch {
    const separator = cleanUrl.includes("?") ? "&" : "?";
    return `${cleanUrl}${separator}view=${encodeURIComponent(cleanText(view, "3d"))}&node=${encodeURIComponent(cleanNode)}`;
  }
}

function canEmitInReadOnly(actionName) {
  return READ_ONLY_ACTIONS.has(cleanText(actionName));
}

function canRenderGraphAction(action, readOnly = false) {
  const actionName = cleanText(action?.event?.action);
  if (!actionName || actionName === "noop") {
    return false;
  }
  return !readOnly || canEmitInReadOnly(actionName);
}

function graphActionKey(action) {
  const event = action?.event || {};
  const payload = event.payload || {};
  return [
    cleanText(action?.id),
    cleanText(event.action),
    cleanText(payload.path),
    cleanText(payload.section),
  ].join("|");
}

function nodeActionBundle(payload, node, readOnly = false) {
  const nodeActions = [
    node?.primaryAction,
    ...asArray(node?.secondaryActions),
  ].filter((action) => canRenderGraphAction(action, readOnly));
  const graphActions = asArray(payload?.graph?.actions)
    .filter((action) => cleanText(action.nodeId) === cleanText(node?.id))
    .filter((action) => canRenderGraphAction(action, readOnly));
  const deduped = [];
  const seen = new Set();
  [...graphActions, ...nodeActions].forEach((action) => {
    const key = graphActionKey(action);
    if (seen.has(key)) {
      return;
    }
    seen.add(key);
    deduped.push(action);
  });
  const fallbackPrimary = nodeActions[0] || null;
  const specificPrimary = graphActions[0] || fallbackPrimary;
  const primary = specificPrimary || null;
  const primaryKey = primary ? graphActionKey(primary) : "";
  const secondary = deduped.filter((action) => graphActionKey(action) !== primaryKey);
  return { primary, secondary };
}

function dashboardCanvasEmbed(payload) {
  const embed = payload?.canvasEmbed || payload?.canvas_embed || {};
  const url = cleanText(embed.url);
  if (!url) {
    return null;
  }
  return {
    url,
    standaloneUrl: cleanText(embed.standaloneUrl || embed.standalone_url, url.replace(/([?&])embed=1(&?)/, "$1").replace(/[?&]$/, "")),
  };
}

function label(ui, key, fallback) {
  return cleanText(ui?.[key], fallback || key);
}

function linesText(value) {
  return asArray(value).map((item) => cleanText(item)).filter(Boolean).join("\n");
}

function formatPercent(value) {
  return `${Math.round(Math.max(0, Math.min(1, Number(value) || 0)) * 100)}%`;
}

function linkPayload(link) {
  return {
    node_id: cleanText(link.nodeId),
    label: cleanText(link.label),
    source: cleanText(link.source, "manual"),
    score: Math.max(0, Number(link.score) || 0),
    rationale: cleanText(link.rationale),
  };
}

function graphActionEvent(action) {
  const event = action?.event || {};
  const actionName = cleanText(event.action);
  if (!actionName || actionName === "noop") {
    return null;
  }
  return makeEvent(actionName, event.payload || {});
}

function translatedNodeType(ui, type) {
  const clean = cleanText(type);
  return label(ui, `dashboard_node_${clean}`, clean.replace(/_/g, " "));
}

function nodeColor(node) {
  if (node.placeholder || node.implemented === false) {
    return "#a6b2ad";
  }
  return NODE_COLORS[node.type] || "#68716f";
}

function layerLabel(ui, layer) {
  const clean = cleanText(layer);
  return label(ui, `dashboard_layer_${clean}`, LAYER_LABELS[clean] || clean.replace(/_/g, " "));
}

function graphLayers(payload) {
  const fromPayload = asArray(payload.graph.layers).map((layer) => cleanText(layer)).filter(Boolean);
  const seen = new Set();
  const out = [];
  const add = (layer) => {
    if (!layer || seen.has(layer)) {
      return;
    }
    seen.add(layer);
    out.push(layer);
  };
  fromPayload.forEach(add);
  if (!out.length) {
    FALLBACK_LAYERS.forEach((layer) => {
      if (payload.graph.nodes.some((node) => node.layer === layer)) {
        add(layer);
      }
    });
  }
  payload.graph.nodes.forEach((node) => add(node.layer));
  return out;
}

function goalIdFromNode(node) {
  return cleanText(node?.recordId || (cleanText(node?.id).startsWith("goal:") ? cleanText(node.id).slice(5) : ""));
}

function goalById(payload, goalId) {
  if (!goalId) {
    return null;
  }
  const activeGoal = asArray(payload.activeGoals).find((goal) => goal.id === goalId);
  if (activeGoal) {
    return activeGoal;
  }
  const primaryId = primaryGoalId(payload);
  if (primaryId && primaryId === goalId && payload.primaryGoal?.isSet) {
    return {
      ...payload.primaryGoal,
      id: primaryId,
      isPrimary: true,
    };
  }
  return null;
}

function primaryGoalId(payload) {
  return (
    cleanText(payload.skillAlignment.primaryGoalId) ||
    cleanText(payload.primaryGoal.editor?.id) ||
    cleanText(payload.primaryGoal.projection?.id)
  );
}

function emptyGoalEditor() {
  return {
    id: "",
    title: "",
    label: "",
    status: "active",
    start: "",
    target: "",
    ui_visibility: "discreet",
    include_in_agent_context: true,
    summary: "",
    alignment: "",
    target_skills: [],
    success_criteria: [],
    focus: [],
    evidence_refs: [],
    task_refs: [],
    output_refs: [],
    notes: "",
  };
}

function isConcreteNode(node) {
  return Boolean(node) && node.implemented !== false && !node.placeholder;
}

function isPlaceholderNode(node) {
  return Boolean(node?.placeholder || node?.implemented === false);
}

function graphInsight(payload) {
  const total = payload.graph.nodes.length;
  const realCount = payload.graph.nodes.filter(isConcreteNode).length;
  const placeholderCount = payload.graph.nodes.filter((node) => node.placeholder || node.implemented === false).length;
  return {
    total,
    realCount,
    placeholderCount,
    mostlyPlaceholder: total > 0 && (realCount === 0 || placeholderCount >= realCount),
  };
}

function preferredNode(payload) {
  const nodesById = new Map(payload.graph.nodes.map((node) => [node.id, node]));
  const attentionNode = asArray(payload.graph.attention.nodes)
    .map((item) => nodesById.get(item.id))
    .find((node) => node && (isConcreteNode(node) || node.primaryAction?.event?.action));
  if (attentionNode) {
    return attentionNode;
  }
  const goalIds = new Set(asArray(payload.activeGoals).map((goal) => goal.id).filter(Boolean));
  const realNodes = payload.graph.nodes.filter(isConcreteNode);
  return (
    realNodes.find((node) =>
      (node.role === "direction" && goalIds.has(node.recordId)) ||
      Boolean(node.ownerPath) ||
      node.role === "star" ||
      (node.role === "leaf" && node.type === "task") ||
      node.role === "trunk"
    ) ||
    realNodes[0] ||
    null
  );
}

function quickLink(payload, id, fallbackPath, fallbackLabel) {
  return (
    asArray(payload.quickLinks).find((link) => cleanText(link.id) === id) ||
    {
      id,
      path: fallbackPath,
      label: fallbackLabel || id,
    }
  );
}

function dashboardMetrics(payload) {
  const doing = asArray(payload.kanban.doing);
  const evidenceCandidates = Number(payload.pendingEvidence.done_uncrystallized_count || 0);
  const unlinkedAtomic = Number(payload.pendingEvidence.unlinked_count || 0);
  const needsReview = Number(payload.pendingEvidence.needs_review_count || 0);
  const statusRisk = Number(payload.pendingEvidence.status_risk_count || 0);
  const evidenceAttention = evidenceCandidates + unlinkedAtomic + needsReview + statusRisk;
  const gapRisk = Number(payload.skills.evidence_risk_count || 0) + asArray(payload.skills.target_learning_locked).length;
  const outputDrafts = Number(payload.charts.public.draft) || 0;
  const healthAlerts = Number(payload.charts.health.error || 0) + Number(payload.charts.health.warning || 0);
  return {
    doing,
    doingTotal: Number(payload.kanban.doing_total || 0) || doing.length,
    evidenceCandidates,
    unlinkedAtomic,
    needsReview,
    statusRisk,
    evidenceAttention,
    gapRisk,
    outputDrafts,
    published: Number(payload.charts.public.published) || 0,
    healthAlerts,
    sourceActive: Number(payload.sources.active_total || 0),
  };
}

function actionQueueItems(payload) {
  const ui = payload.ui;
  const metrics = dashboardMetrics(payload);
  const kanban = quickLink(payload, "kanban", "pages/3_Kanban.py", label(ui, "quick_kanban", "Kanban"));
  const evidence = quickLink(payload, "evidence_review", "pages/2_Evidence_Review.py", label(ui, "quick_evidence_review", "Evidence Review"));
  const gap = quickLink(payload, "gap", "pages/2_Gap_Analysis.py", label(ui, "quick_gap", "Gap Analysis"));
  const output = quickLink(payload, "public_site", "pages/6_Output_Studio.py", label(ui, "quick_public_site", "Output Studio"));
  const items = [
    {
      id: "evidence",
      count: metrics.evidenceAttention,
      eyebrow: label(ui, "dashboard_today_evidence_review", "Evidence review"),
      title: metrics.evidenceAttention
        ? label(ui, "dashboard_action_review_evidence", "Review evidence")
        : label(ui, "dashboard_pending_evidence_empty", "No evidence waiting"),
      detail: `${label(ui, "dashboard_done_uncrystallized", "Done not crystallized")}: ${metrics.evidenceCandidates} · ${label(ui, "dashboard_atomic_evidence_unlinked", "Unlinked atomic rows")}: ${metrics.unlinkedAtomic}`,
      why: metrics.evidenceAttention
        ? label(ui, "dashboard_action_why_evidence", "Evidence queues are the highest-confidence next review work.")
        : label(ui, "dashboard_action_why_clear", "No urgent queue is blocking the daily path."),
      filter: `pending=${metrics.evidenceAttention}`,
      path: evidence.path,
      tone: metrics.evidenceAttention ? "warning" : "",
    },
    {
      id: "focus",
      count: metrics.doingTotal,
      eyebrow: label(ui, "dashboard_today_current_focus", "Current focus"),
      title: metrics.doingTotal
        ? label(ui, "dashboard_action_open_focus", "Open current work")
        : label(ui, "dashboard_doing_empty", "No Doing tasks yet."),
      detail: metrics.doing.slice(0, 2).map((item) => cleanText(item.title)).filter(Boolean).join(" / ") || label(ui, "dashboard_action_open_kanban_hint", "Choose current work from Kanban."),
      why: metrics.doingTotal
        ? label(ui, "dashboard_action_why_focus", "Current Doing work keeps today's actions tied to the active goal.")
        : label(ui, "dashboard_action_why_focus_empty", "Pick one active task before expanding the rest of the system."),
      filter: `doing=${metrics.doingTotal}`,
      path: kanban.path,
      tone: metrics.doingTotal ? "" : "muted",
    },
    {
      id: "gap",
      count: metrics.gapRisk,
      eyebrow: label(ui, "dashboard_today_gap_next_action", "Gap / Next action"),
      title: metrics.gapRisk
        ? label(ui, "dashboard_action_resolve_gap", "Resolve gap risk")
        : label(ui, "dashboard_gap_risk_title", "Gap risk"),
      detail: metrics.gapRisk
        ? label(ui, "dashboard_gap_risk_title", "Gap risk")
        : label(ui, "dashboard_action_gap_clear", "No urgent gap signal."),
      why: metrics.gapRisk
        ? label(ui, "dashboard_action_why_gap", "Gap risks can block the current goal if they stay unresolved.")
        : label(ui, "dashboard_action_why_clear", "No urgent queue is blocking the daily path."),
      filter: `gap=${metrics.gapRisk}`,
      path: gap.path,
      tone: metrics.gapRisk ? "warning" : "",
    },
    {
      id: "output",
      count: metrics.outputDrafts,
      eyebrow: label(ui, "dashboard_today_output_feedback", "Output / Feedback"),
      title: metrics.outputDrafts
        ? label(ui, "dashboard_action_open_output", "Open output drafts")
        : label(ui, "dashboard_action_draft_output", "Draft output"),
      detail: `${label(ui, "dashboard_public_published", "Published")}: ${metrics.published}`,
      why: metrics.outputDrafts
        ? label(ui, "dashboard_action_why_output", "Drafts are ready to turn reviewed work into reusable output.")
        : label(ui, "dashboard_action_why_output_empty", "Create an output only after the review queues have enough support."),
      filter: `drafts=${metrics.outputDrafts}`,
      path: output.path,
      tone: metrics.outputDrafts ? "" : "muted",
    },
  ];
  // Priority sort: urgent (warning) first, then neutral, then muted/empty.
  // Within the same tone, higher counts lead so "what to do first" is obvious.
  const toneRank = { warning: 0, "": 1, muted: 2 };
  return items
    .map((item, index) => ({ item, index }))
    .sort((a, b) => {
      const ta = toneRank[a.item.tone] ?? 1;
      const tb = toneRank[b.item.tone] ?? 1;
      if (ta !== tb) return ta - tb;
      const ca = Number(a.item.count) || 0;
      const cb = Number(b.item.count) || 0;
      if (ca !== cb) return cb - ca;
      return a.index - b.index;
    })
    .map((entry) => entry.item);
}

function TodayFocusStrip({ payload, onEmit }) {
  const ui = payload.ui;
  return (
    <div className="hd-today-strip" aria-label={label(ui, "dashboard_today_focus_title", "Today focus")}>
      {actionQueueItems(payload).map((item) => (
        <button
          key={item.id}
          className={`hd-today-item ${item.tone || ""}`}
          type="button"
          data-action="navigate"
          data-dashboard-action={`today:${item.id}`}
          data-target={item.path}
          onClick={() => onEmit(navigationEvent(item.path))}
        >
          <span>{item.eyebrow}</span>
          <strong>{item.count}</strong>
          <small>{item.title}</small>
        </button>
      ))}
    </div>
  );
}

function skillSegments(counts, total) {
  const raw = SKILL_STATUS_META.map((item) => ({
    ...item,
    count: Math.max(0, Number(counts[item.key]) || 0),
  }));
  if (!total) {
    return raw.map((item) => ({ ...item, dasharray: "", dashoffset: 0 }));
  }

  const visible = raw.filter((item) => item.count > 0);
  const circumference = 2 * Math.PI * SKILL_RING_RADIUS;
  const gap = visible.length > 1 ? 8 : 0;
  const available = circumference - gap * visible.length;
  let offset = 0;

  return raw.map((item) => {
    if (!item.count) {
      return { ...item, dasharray: "", dashoffset: 0 };
    }
    const length = (item.count / total) * available;
    const segment = {
      ...item,
      dasharray: `${length} ${circumference}`,
      dashoffset: -offset,
    };
    offset += length + gap;
    return segment;
  });
}

function ContextHeader({ payload, onEmit, onCreateGoal, onSelectGoal, onEditGoal, canEditGoals = true, canSelectGoals = true, showToday = true, selectedGoalId = "" }) {
  const ui = payload.ui;
  const northStar = payload.northStar;
  const primary = goalDisplay(payload.primaryGoal, ui);
  const primaryId = primaryGoalId(payload);
  const activeGoals = asArray(payload.activeGoals);
  const secondaryGoals = activeGoals.filter((goal) => !goal.isPrimary);
  const northStarText =
    northStar.locked || northStar.visibility === "private"
      ? label(ui, "north_star_private_display", "Private North Star")
      : cleanText(northStar.displayText, label(ui, "north_star_empty", "No North Star set"));
  const primaryMeta = [
    primary.status ? label(ui, `goal_status_${primary.status}`, primary.status) : "",
    primary.target ? `${label(ui, "goal_strip_target", "Target")}: ${primary.target}` : "",
  ].filter(Boolean);

  return (
    <section className={showToday ? "hd-context-header" : "hd-context-header no-today"}>
      <div className="hd-context-main">
        <div className="hd-context-card hd-context-north">
          <span className="hd-eyebrow">{label(ui, "north_star_strip_title", "North Star")}</span>
          <strong>{northStarText}</strong>
          <div className="hd-context-meta">
            <span className="hd-context-badge">
              {label(ui, `north_star_visibility_${northStar.visibility}`, northStar.visibility)}
            </span>
          </div>
        </div>
        <div className="hd-context-card hd-context-primary">
          <div className="hd-context-card-head">
            <span className="hd-eyebrow">{label(ui, "dashboard_primary_goal", "Primary goal")}</span>
            {canEditGoals && primaryId && !payload.primaryGoal.locked ? (
              <button
                className="hd-context-edit"
                type="button"
                data-action="open-goal-form"
                data-goal-id={primaryId}
                onClick={() => onEditGoal?.(primaryId)}
              >
                {label(ui, "dashboard_goal_edit_inline", "Edit goal")}
              </button>
            ) : null}
          </div>
          <strong>{primary.title}</strong>
          {primary.summary ? (
            <p className="hd-context-copy">{primary.summary}</p>
          ) : (
            <div className="hd-context-meta">
              {primaryMeta.length ? primaryMeta.map((item) => (
                <span key={item} className="hd-context-badge">{item}</span>
              )) : (
                <>
                  <span className="hd-context-badge">{label(ui, "goal_no_current", "No current goal set.")}</span>
                  {canEditGoals ? (
                    <button
                      className="hd-ghost hd-context-empty-cta"
                      type="button"
                      data-action="open-goal-form"
                      onClick={onCreateGoal}
                    >
                      {label(ui, "dashboard_add_active_goal", "Add goal")}
                    </button>
                  ) : null}
                </>
              )}
            </div>
          )}
        </div>

        <div className="hd-context-goals">
          <div className="hd-context-goals-head">
            <span className="hd-eyebrow">{label(ui, "dashboard_active_goals_title", "Active goals")}</span>
            <span className="hd-context-count">{secondaryGoals.length}</span>
          </div>
          <div className="hd-goal-rail">
            {secondaryGoals.length ? secondaryGoals.map((goal) => {
              const display = goalDisplay(goal, ui);
              const isSelected = Boolean(goal.id) && goal.id === selectedGoalId;
              const className = `hd-goal-pill${isSelected ? " selected" : ""}`;
              const title = `${display.title} · ${label(ui, `goal_status_${display.status}`, display.status || "active")}`;
              return canSelectGoals ? (
                <button
                  key={goal.id || display.title}
                  className={className}
                  type="button"
                  data-action="select-goal"
                  data-goal-id={goal.id}
                  aria-pressed={isSelected}
                  title={title}
                  onClick={() => onSelectGoal(goal.id)}
                >
                  <span className="hd-goal-pill-dot" />
                  <strong>{display.title}</strong>
                </button>
              ) : (
                <span
                  key={goal.id || display.title}
                  className={`${className} static`}
                  data-action="goal-context"
                  data-goal-id={goal.id}
                  title={title}
                >
                  <span className="hd-goal-pill-dot" />
                  <strong>{display.title}</strong>
                </span>
              );
            }) : <span className="hd-empty-inline">{label(ui, "dashboard_no_secondary_goals", "Only the primary goal is active.")}</span>}
          </div>
        </div>
      </div>

      {showToday ? <TodayFocusStrip payload={payload} onEmit={onEmit} /> : null}

      <div className="hd-context-actions">
        {canEditGoals ? (
          <button className="hd-primary full" type="button" data-action="open-goal-form" onClick={onCreateGoal}>
            {label(ui, "dashboard_add_active_goal", "Add goal")}
          </button>
        ) : null}
        <button className="hd-ghost full" type="button" data-action="open-profile-context" onClick={() => onEmit(openProfileContextEvent())}>
          {label(ui, "north_star_edit_action", "Edit Profile Context")}
        </button>
      </div>
    </section>
  );
}

function CanvasNode({ data, selected }) {
  const node = data.node;
  return (
    <div
      className={[
        "hd-flow-node",
        `type-${node.type}`,
        node.suggested ? "suggested" : "",
        node.placeholder ? "placeholder" : "",
        node.implemented === false ? "not-implemented" : "",
        node.locked ? "locked" : "",
        selected ? "selected" : "",
      ].filter(Boolean).join(" ")}
    >
      <Handle type="target" position={Position.Left} className="hd-flow-handle" />
      <span className="hd-node-dot" style={{ background: nodeColor(node) }} />
      <div>
        <strong>{node.label}</strong>
        <span>{node.metric || node.status || node.layer || translatedNodeType({}, node.type)}</span>
      </div>
      <Handle type="source" position={Position.Right} className="hd-flow-handle" />
    </div>
  );
}

function LayerHeaderNode({ data }) {
  return (
    <div className="hd-flow-layer">
      <strong>{data.label}</strong>
      <span>{data.count}</span>
    </div>
  );
}

const NODE_TYPES = { contextNode: CanvasNode, layerHeader: LayerHeaderNode };

function canvasLayout(nodes, layers) {
  const byLayer = new Map();
  nodes.forEach((node) => {
    const layer = cleanText(node.layer, "activity");
    byLayer.set(layer, [...(byLayer.get(layer) || []), node]);
  });
  const positions = new Map();
  const place = (items, x, startY) => {
    const step = items.length > 4 ? 88 : 98;
    items.forEach((node, index) => {
      positions.set(node.id, { x, y: startY + index * step });
    });
  };
  layers.forEach((layer, index) => {
    place(byLayer.get(layer) || [], index * 226, 72);
  });
  return positions;
}

function graphNodesForView(payload, hiddenLayers, viewMode) {
  const baseNodes = payload.graph.nodes.filter((node) => !hiddenLayers.has(node.layer));
  if (viewMode === "focus" && payload.graph.focusPath.length) {
    const focusIds = new Set(payload.graph.focusPath);
    return baseNodes.filter((node) => focusIds.has(node.id));
  }
  if (viewMode === "attention") {
    const attentionIds = new Set(payload.graph.attention.nodes.map((node) => node.id));
    payload.graph.focusPath.slice(0, 3).forEach((id) => attentionIds.add(id));
    if (attentionIds.size) {
      return baseNodes.filter((node) => attentionIds.has(node.id));
    }
  }
  return baseNodes;
}

function graphAttentionIds(payload) {
  return new Set(asArray(payload.graph.attention.nodes).map((item) => cleanText(item.id)).filter(Boolean));
}

function walkRelatedNodeIds(payload, selectedNodeId, direction) {
  const selected = cleanText(selectedNodeId);
  if (!selected) {
    return new Set();
  }
  const ids = new Set([selected]);
  const queue = [{ id: selected, depth: 0 }];
  while (queue.length) {
    const current = queue.shift();
    if (!current || current.depth >= 3) {
      continue;
    }
    payload.graph.edges.forEach((edge) => {
      const next = direction === "upstream" && edge.to === current.id
        ? edge.from
        : direction === "downstream" && edge.from === current.id
          ? edge.to
          : "";
      if (!next || ids.has(next)) {
        return;
      }
      ids.add(next);
      queue.push({ id: next, depth: current.depth + 1 });
    });
  }
  return ids;
}

function relatedNodeIds(payload, selectedNodeId, scope) {
  const selected = cleanText(selectedNodeId);
  if (scope === "upstream" || scope === "downstream") {
    return walkRelatedNodeIds(payload, selected, scope);
  }

  const ids = new Set([
    ...asArray(payload.graph.focusPath).map((id) => cleanText(id)).filter(Boolean),
    ...graphAttentionIds(payload),
  ]);
  if (!selected) {
    return ids.size ? ids : null;
  }
  ids.add(selected);
  payload.graph.edges.forEach((edge) => {
    if (edge.to === selected) {
      ids.add(edge.from);
    }
    if (edge.from === selected) {
      ids.add(edge.to);
    }
  });
  return ids;
}

function exploreNodeScore(payload, node, selectedNodeId) {
  const focusIndex = asArray(payload.graph.focusPath).indexOf(node.id);
  const attentionIndex = asArray(payload.graph.attention.nodes).findIndex((item) => item.id === node.id);
  let score = 0;
  if (node.id === selectedNodeId) {
    score += 1000;
  }
  if (focusIndex >= 0) {
    score += 760 - focusIndex * 18;
  }
  if (attentionIndex >= 0) {
    score += 720 - attentionIndex * 18;
  }
  if (isConcreteNode(node)) {
    score += 120;
  }
  if (cleanText(node.primaryAction?.event?.action)) {
    score += 80;
  }
  if (node.isPrimary) {
    score += 60;
  }
  if (node.placeholder || node.implemented === false) {
    score -= 45;
  }
  return score;
}

function sortedExploreNodes(payload, nodes, selectedNodeId) {
  const layerOrder = graphLayers(payload);
  return [...nodes].sort((a, b) => {
    const scoreDiff = exploreNodeScore(payload, b, selectedNodeId) - exploreNodeScore(payload, a, selectedNodeId);
    if (scoreDiff) {
      return scoreDiff;
    }
    const layerDiff = layerOrder.indexOf(a.layer) - layerOrder.indexOf(b.layer);
    if (layerDiff) {
      return layerDiff;
    }
    return cleanText(a.label).localeCompare(cleanText(b.label));
  });
}

function nodeMatchesExploreQuery(payload, node, query) {
  const needle = cleanText(query).toLowerCase();
  if (!needle) {
    return true;
  }
  const haystack = [
    node.id,
    node.label,
    node.metric,
    node.status,
    node.summary,
    node.description,
    node.recordId,
    node.ownerPath,
    node.type,
    node.layer,
    translatedNodeType(payload.ui, node.type),
    layerLabel(payload.ui, node.layer),
  ].map((item) => cleanText(item).toLowerCase()).join(" ");
  return haystack.includes(needle);
}

function filterExploreNodes(payload, nodes, query, showPlaceholders) {
  return nodes.filter((node) => {
    if (!showPlaceholders && isPlaceholderNode(node)) {
      return false;
    }
    return nodeMatchesExploreQuery(payload, node, query);
  });
}

function groupedExploreNodes(payload, nodes) {
  const layerOrder = graphLayers(payload);
  const grouped = new Map();
  nodes.forEach((node) => {
    const layer = cleanText(node.layer, "activity");
    if (!grouped.has(layer)) {
      grouped.set(layer, []);
    }
    grouped.get(layer).push(node);
  });
  return [...grouped.entries()]
    .sort(([a], [b]) => {
      const aIndex = layerOrder.indexOf(a);
      const bIndex = layerOrder.indexOf(b);
      if (aIndex === -1 && bIndex === -1) {
        return a.localeCompare(b);
      }
      if (aIndex === -1) {
        return 1;
      }
      if (bIndex === -1) {
        return -1;
      }
      return aIndex - bIndex;
    })
    .map(([layer, layerNodes]) => ({ layer, nodes: layerNodes }));
}

function graphExploreNodes(payload, hiddenLayers, selectedNodeId, scope) {
  const baseNodes = payload.graph.nodes.filter((node) => !hiddenLayers.has(node.layer));
  if (scope === "all") {
    return sortedExploreNodes(payload, baseNodes, selectedNodeId);
  }
  const focusIds = new Set(payload.graph.focusPath);
  const attentionIds = graphAttentionIds(payload);
  const scopedIds = relatedNodeIds(payload, selectedNodeId, scope);
  const firstPass = baseNodes.filter((node) => (
    focusIds.has(node.id) ||
    attentionIds.has(node.id) ||
    isConcreteNode(node) ||
    cleanText(node.primaryAction?.event?.action)
  ));
  const scoped = scopedIds
    ? baseNodes.filter((node) => scopedIds.has(node.id) || node.id === selectedNodeId)
    : firstPass;
  return sortedExploreNodes(payload, scoped.length ? scoped : firstPass.length ? firstPass : baseNodes, selectedNodeId);
}

function flowData(payload, hiddenLayers, viewMode) {
  const visibleNodes = graphNodesForView(payload, hiddenLayers, viewMode);
  const visibleLayers = graphLayers(payload).filter((layer) =>
    !hiddenLayers.has(layer) && visibleNodes.some((node) => node.layer === layer)
  );
  const positions = canvasLayout(visibleNodes, visibleLayers);
  const layerCounts = new Map();
  visibleNodes.forEach((node) => {
    layerCounts.set(node.layer, (layerCounts.get(node.layer) || 0) + 1);
  });
  const layerNodes = visibleLayers.map((layer, index) => ({
    id: `layer:${layer}`,
    type: "layerHeader",
    position: { x: index * 226, y: 0 },
    data: { label: layerLabel(payload.ui, layer), count: layerCounts.get(layer) || 0 },
    draggable: false,
    selectable: false,
  }));
  const graphNodes = visibleNodes.map((node) => ({
    id: node.id,
    type: "contextNode",
    position: positions.get(node.id) || { x: 0, y: 0 },
    data: { node },
    draggable: false,
  }));
  const nodeIds = new Set(graphNodes.map((node) => node.id));
  const edges = payload.graph.edges
    .filter((edge) => nodeIds.has(edge.from) && nodeIds.has(edge.to))
    .map((edge, index) => ({
      id: `${edge.from}-${edge.to}-${index}`,
      source: edge.from,
      target: edge.to,
      type: "smoothstep",
      animated: edge.relation === "watches",
      className: `hd-flow-edge ${edge.suggested ? "suggested" : ""} ${edge.placeholder ? "placeholder" : ""}`,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: 12,
        height: 12,
      },
      label: edge.relation && edge.relation !== edge.type ? edge.relation : undefined,
      labelStyle: { fill: "#60716b", fontSize: 10, fontWeight: 700 },
      labelBgStyle: { fill: "rgba(255,255,255,.9)" },
      style: edge.suggested || edge.placeholder
        ? { strokeDasharray: "5 5", strokeWidth: 1.8 }
        : { strokeWidth: 2.1 },
    }));
  return { nodes: [...layerNodes, ...graphNodes], edges };
}

function CanvasSetupBanner({ payload, insight, hiddenLayers, onEmit, onCreateGoal, readOnly = false }) {
  const ui = payload.ui;
  const missing = [];
  if (!payload.northStar.isSet) {
    missing.push(label(ui, "dashboard_canvas_missing_north_star", "North Star missing"));
  }
  if (!payload.primaryGoal.isSet) {
    missing.push(label(ui, "dashboard_canvas_missing_goal", "Current goal missing"));
  }
  if (!Number(payload.sources.active_total || 0)) {
    missing.push(label(ui, "dashboard_canvas_missing_sources", "No captured sources yet"));
  }
  const allHidden = hiddenLayers.size >= graphLayers(payload).length && graphLayers(payload).length > 0;
  if (!missing.length && !insight.mostlyPlaceholder && !allHidden) {
    return null;
  }

  return (
    <div className="hd-canvas-banner">
      <div className="hd-canvas-banner-copy">
        <span className="hd-eyebrow">{label(ui, "dashboard_graph_eyebrow", "Canvas")}</span>
        <strong>
          {allHidden
            ? label(ui, "dashboard_canvas_no_layers", "All layers are hidden.")
            : label(ui, "dashboard_canvas_setup_title", "The canvas is still in setup")}
        </strong>
        <p>
          {allHidden
            ? label(ui, "dashboard_canvas_reset_filters", "Show all layers to continue.")
            : label(
              ui,
              "dashboard_canvas_setup_hint",
              "Add North Star and a current goal first, then capture sources to replace the skeleton.",
            )}
        </p>
      </div>

      {missing.length ? (
        <div className="hd-canvas-banner-tags">
          {missing.map((item) => <span key={item}>{item}</span>)}
        </div>
      ) : null}

      <div className="hd-canvas-banner-actions">
        {!payload.northStar.isSet ? (
          <button className="hd-ghost" type="button" data-action="open-profile-context" onClick={() => onEmit(openProfileContextEvent())}>
            {label(ui, "north_star_edit_action", "Edit Profile Context")}
          </button>
        ) : null}
        {!readOnly && payload.northStar.isSet && !payload.primaryGoal.isSet ? (
          <button className="hd-primary" type="button" data-action="open-goal-form" onClick={onCreateGoal}>
            {label(ui, "dashboard_add_active_goal", "Add goal")}
          </button>
        ) : null}
      </div>
    </div>
  );
}

function AttentionSummary({ payload, onSelectNode }) {
  const ui = payload.ui;
  const attention = payload.graph.attention;
  if (!attention.nodes.length) {
    return null;
  }
  return (
    <div className="hd-attention-strip">
      <span className="hd-eyebrow">{label(ui, "dashboard_attention_title", "Attention")}</span>
      <div className="hd-attention-list">
        {attention.nodes.map((item) => (
          <button
            key={item.id}
            className={`hd-attention-chip ${item.severity || ""}`}
            type="button"
            data-action="select-node"
            data-source="attention-chip"
            data-node-id={item.id}
            onClick={() => onSelectNode(item.id)}
          >
            <strong>{item.id}</strong>
            <span>{item.reason}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function FocusPathView({ payload, selectedNodeId, onSelectNode }) {
  const ui = payload.ui;
  const nodesById = new Map(payload.graph.nodes.map((node) => [node.id, node]));
  const focusNodes = payload.graph.focusPath.map((id) => nodesById.get(id)).filter(Boolean);
  if (!focusNodes.length) {
    return (
      <div className="hd-focus-path-wrap hd-canvas-surface-empty">
        <p className="hd-empty">{label(ui, "dashboard_canvas_no_layers", "All layers are hidden.")}</p>
      </div>
    );
  }
  return (
    <div className="hd-focus-path-wrap">
      <div className="hd-focus-path">
        {focusNodes.map((node, index) => (
          <button
            key={node.id}
            className={[
              "hd-focus-node",
              `type-${node.type}`,
              node.placeholder ? "placeholder" : "",
              node.implemented === false ? "not-implemented" : "",
              selectedNodeId === node.id ? "selected" : "",
            ].filter(Boolean).join(" ")}
            type="button"
            data-action="select-node"
            data-source="focus-path"
            data-node-id={node.id}
            onClick={() => onSelectNode(node.id)}
          >
            <span className="hd-focus-step">{String(index + 1).padStart(2, "0")}</span>
            <span className="hd-focus-layer">{translatedNodeType(ui, node.type)}</span>
            <strong>{node.label}</strong>
            <small>{node.metric || node.status || layerLabel(ui, node.layer)}</small>
            {node.primaryAction?.label ? (
              <span className="hd-focus-cta">{node.primaryAction.label}</span>
            ) : null}
          </button>
        ))}
      </div>
    </div>
  );
}

function AttentionCanvasView({ payload, onSelectNode }) {
  const ui = payload.ui;
  const nodesById = new Map(payload.graph.nodes.map((node) => [node.id, node]));
  const attention = payload.graph.attention.nodes
    .map((item) => ({ ...item, node: nodesById.get(item.id) }))
    .filter((item) => item.node);
  if (!attention.length) {
    return (
      <div className="hd-attention-canvas hd-canvas-surface-empty">
        <p className="hd-empty">{label(ui, "dashboard_pending_evidence_empty", "No attention items right now.")}</p>
      </div>
    );
  }
  return (
    <div className="hd-attention-canvas">
      {attention.map((item) => (
        <button
          key={`${item.id}-${item.reason}`}
          className={`hd-attention-card ${item.severity || ""}`}
          type="button"
          data-action="select-node"
          data-source="attention-card"
          data-node-id={item.id}
          onClick={() => onSelectNode(item.id)}
        >
          <span>{translatedNodeType(ui, item.node.type)}</span>
          <strong>{item.node.label}</strong>
          <small>{item.reason}</small>
          {item.node.primaryAction?.label ? <em>{item.node.primaryAction.label}</em> : null}
        </button>
      ))}
    </div>
  );
}

function exploreLaneForNode(node) {
  const layer = cleanText(node.layer);
  const type = cleanText(node.type);
  return (
    EXPLORE_LANES.find((lane) => lane.types.includes(type)) ||
    EXPLORE_LANES.find((lane) => lane.layers.includes(layer)) ||
    EXPLORE_LANES[1]
  );
}

function exploreEdgePath(edge) {
  const from = edge.fromPosition;
  const to = edge.toPosition;
  if (Math.abs(from.x - to.x) < 1) {
    const bend = Math.min(98, from.x + 10);
    return `M ${from.x} ${from.y} C ${bend} ${from.y}, ${bend} ${to.y}, ${to.x} ${to.y}`;
  }
  const mid = (from.x + to.x) / 2;
  return `M ${from.x} ${from.y} C ${mid} ${from.y}, ${mid} ${to.y}, ${to.x} ${to.y}`;
}

function exploreMapData(payload, nodes, selectedNodeId) {
  const laneRecords = EXPLORE_LANES.map((lane) => ({
    ...lane,
    nodes: [],
    visibleNodes: [],
    moreCount: 0,
    total: 0,
  }));
  const lanesByKey = new Map(laneRecords.map((lane) => [lane.key, lane]));
  nodes.forEach((node) => {
    const lane = lanesByKey.get(exploreLaneForNode(node).key) || laneRecords[1];
    lane.nodes.push(node);
  });

  laneRecords.forEach((lane) => {
    lane.nodes = sortedExploreNodes(payload, lane.nodes, selectedNodeId);
    lane.total = lane.nodes.length;
    const selectedNode = lane.nodes.find((node) => node.id === selectedNodeId);
    let kept = lane.nodes.slice(0, 4);
    if (selectedNode && !kept.some((node) => node.id === selectedNode.id)) {
      kept = [selectedNode, ...lane.nodes.filter((node) => node.id !== selectedNode.id).slice(0, 3)];
    }
    lane.visibleNodes = kept;
    lane.moreCount = Math.max(0, lane.nodes.length - kept.length);
  });

  const positionedNodes = [];
  const positions = new Map();
  const laneCount = laneRecords.length;
  laneRecords.forEach((lane, laneIndex) => {
    const count = Math.max(1, lane.visibleNodes.length);
    const x = ((laneIndex + 0.5) / laneCount) * 100;
    lane.visibleNodes.forEach((node, index) => {
      const y = 18 + ((index + 1) / (count + 1)) * 70;
      const position = { x, y };
      positions.set(node.id, position);
      positionedNodes.push({ node, lane, x, y });
    });
  });

  const visibleIds = new Set(positionedNodes.map((item) => item.node.id));
  const edges = payload.graph.edges
    .filter((edge) => visibleIds.has(edge.from) && visibleIds.has(edge.to))
    .map((edge, index) => ({
      ...edge,
      id: `${edge.from}-${edge.to}-${index}`,
      fromPosition: positions.get(edge.from),
      toPosition: positions.get(edge.to),
      active: edge.from === selectedNodeId || edge.to === selectedNodeId,
    }));

  return { lanes: laneRecords, nodes: positionedNodes, edges };
}

function linkEndpointId(endpoint) {
  if (endpoint && typeof endpoint === "object") {
    return cleanText(endpoint.id);
  }
  return cleanText(endpoint);
}

function relationColor(relation) {
  return EDGE_COLORS[cleanText(relation)] || EDGE_COLORS.link;
}

// Stable hash → [0,1). Keeps the star tree deterministic across refreshes
// (no Math.random), so the silhouette stays put while it breathes.
function hashUnit(text) {
  const str = cleanText(text);
  let h = 2166136261;
  for (let i = 0; i < str.length; i += 1) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 100000) / 100000;
}

// Resolve the parent of a node along a set of preferred relations. Edges point
// parent → child, so we look for an incoming edge whose source is allowed.
function parentByRelation(node, edgesByTarget, allowed, nodesById) {
  const incoming = edgesByTarget.get(node.id) || [];
  for (const relation of allowed) {
    const match = incoming.find((edge) => (edge.relation || edge.type) === relation && nodesById.has(edge.from));
    if (match) {
      return nodesById.get(match.from);
    }
  }
  // Fall back to any structural incoming edge from a placed node.
  const any = incoming.find((edge) => nodesById.has(edge.from));
  return any ? nodesById.get(any.from) : null;
}

// Deterministic star-tree skeleton. Returns id -> {x, y, z} for every tree,
// star and constellation node. Sand nodes are excluded (rendered as a particle
// field). Coordinates are pinned onto node.fx/fy/fz by the caller so the
// force engine never drifts them.
function growthTreeLayout(payload, nodes) {
  const positions = new Map();
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const edges = asArray(payload.graph.edges).filter(
    (edge) => nodesById.has(edge.from) && nodesById.has(edge.to),
  );
  const edgesByTarget = new Map();
  edges.forEach((edge) => {
    if (!edgesByTarget.has(edge.to)) {
      edgesByTarget.set(edge.to, []);
    }
    edgesByTarget.get(edge.to).push(edge);
  });

  const byRole = (role) => nodes.filter((node) => node.role === role);

  // 1. Trunk — vertical spine at the origin.
  const trunks = byRole("trunk");
  trunks.forEach((node) => {
    positions.set(node.id, { x: 0, y: TREE_HEIGHT, z: 0 });
  });
  const trunkAnchor = () => ({ x: 0, y: TREE_HEIGHT * 0.62, z: 0 });

  // 2. Direction (goals) — fan out around the upper trunk, angled up-and-out.
  const directions = byRole("direction");
  const dirCount = Math.max(1, directions.length);
  const directionPos = new Map();
  directions.forEach((node, index) => {
    const theta = (index / dirCount) * Math.PI * 2 + 0.4;
    const r = 42;
    const pos = {
      x: Math.cos(theta) * r,
      y: TREE_HEIGHT * 0.6 + (index % 3) * 9,
      z: Math.sin(theta) * r,
    };
    positions.set(node.id, pos);
    directionPos.set(node.id, { pos, theta });
  });

  const fallbackDirection = () => {
    const first = directions[0];
    return first ? directionPos.get(first.id) : { pos: trunkAnchor(), theta: 0.4 };
  };

  // 3. Branch (projects) — second-order spread off their owning goal.
  const branches = byRole("branch");
  const branchPos = new Map();
  branches.forEach((node, index) => {
    const parent = parentByRelation(node, edgesByTarget, ["contains", "alignment"], nodesById);
    const base = (parent && directionPos.get(parent.id)) || fallbackDirection();
    const spread = hashUnit(node.id) * Math.PI * 2;
    const theta = base.theta + (hashUnit(`${node.id}:t`) - 0.5) * 1.1;
    const r = 26 + hashUnit(`${node.id}:r`) * 10;
    const pos = {
      x: base.pos.x + Math.cos(theta) * r,
      y: base.pos.y + 8 + (hashUnit(`${node.id}:y`) - 0.5) * 8,
      z: base.pos.z + Math.sin(theta) * r,
    };
    positions.set(node.id, pos);
    branchPos.set(node.id, { pos, theta, spread });
  });

  // 4. Leaf (tasks/outputs) — scatter at the branch tips, lifted slightly.
  const leaves = byRole("leaf");
  const leafPos = new Map();
  leaves.forEach((node) => {
    const parent = parentByRelation(
      node,
      edgesByTarget,
      ["contains", "produces", "drives", "supports"],
      nodesById,
    );
    const parentPos =
      (parent && (branchPos.get(parent.id)?.pos || directionPos.get(parent.id)?.pos || positions.get(parent.id))) ||
      null;
    const anchor = parentPos || fallbackDirection().pos;
    const theta = hashUnit(`${node.id}:lt`) * Math.PI * 2;
    const r = 12 + hashUnit(`${node.id}:lr`) * 10;
    const pos = {
      x: anchor.x + Math.cos(theta) * r,
      y: anchor.y + 10 + hashUnit(`${node.id}:ly`) * 8,
      z: anchor.z + Math.sin(theta) * r,
    };
    positions.set(node.id, pos);
    leafPos.set(node.id, { pos });
  });

  // 5. Fruit (evidence) — hang below the leaf that generated them.
  const fruits = byRole("fruit");
  fruits.forEach((node) => {
    const parent = parentByRelation(
      node,
      edgesByTarget,
      ["generated_by", "produces", "contains", "supports", "review", "derives"],
      nodesById,
    );
    const base =
      (parent && (leafPos.get(parent.id)?.pos || positions.get(parent.id))) || null;
    const anchor = base || { x: 0, y: TREE_HEIGHT * 0.5, z: 0 };
    const theta = hashUnit(`${node.id}:ft`) * Math.PI * 2;
    const r = 6 + hashUnit(`${node.id}:fr`) * 8;
    positions.set(node.id, {
      x: anchor.x + Math.cos(theta) * r,
      y: anchor.y - 8 - hashUnit(`${node.id}:fy`) * 8,
      z: anchor.z + Math.sin(theta) * r,
    });
  });

  // 6. Star (skills) — a glowing dome above the canopy. Sectorized by category
  // then distributed with a fibonacci-style spiral for an even sky.
  const stars = byRole("star");
  const categories = [...new Set(stars.map((node) => cleanText(node.metric) || "general"))];
  const categoryIndex = new Map(categories.map((cat, idx) => [cat, idx]));
  const catCount = Math.max(1, categories.length);
  const starTotal = Math.max(1, stars.length);
  stars.forEach((node, index) => {
    const cat = cleanText(node.metric) || "general";
    const sector = (categoryIndex.get(cat) || 0) / catCount;
    // Map index onto a hemisphere; bias phi toward the top so it reads as a dome.
    const t = (index + 0.5) / starTotal;
    const phi = Math.acos(1 - t * 0.92); // 0 (top) .. ~0.9π/2
    const theta = sector * Math.PI * 2 + index * GOLDEN_ANGLE;
    const r = STAR_DOME_RADIUS * (0.82 + hashUnit(`${node.id}:sr`) * 0.18);
    positions.set(node.id, {
      x: Math.sin(phi) * Math.cos(theta) * r,
      y: STAR_DOME_CENTER_Y + Math.cos(phi) * r * 0.5,
      z: Math.sin(phi) * Math.sin(theta) * r,
    });
  });

  // 7. Constellation (claims) — float above the centroid of their sources.
  const constellations = byRole("constellation");
  constellations.forEach((node) => {
    const incoming = (edgesByTarget.get(node.id) || []).filter((edge) =>
      ["supports", "derives"].includes(edge.relation || edge.type),
    );
    const anchors = incoming
      .map((edge) => positions.get(edge.from))
      .filter(Boolean);
    let centroid;
    if (anchors.length) {
      centroid = anchors.reduce(
        (acc, p) => ({ x: acc.x + p.x, y: acc.y + p.y, z: acc.z + p.z }),
        { x: 0, y: 0, z: 0 },
      );
      centroid = {
        x: centroid.x / anchors.length,
        y: centroid.y / anchors.length,
        z: centroid.z / anchors.length,
      };
    } else {
      const theta = hashUnit(`${node.id}:ct`) * Math.PI * 2;
      centroid = { x: Math.cos(theta) * 40, y: TREE_HEIGHT * 0.8, z: Math.sin(theta) * 40 };
    }
    positions.set(node.id, {
      x: centroid.x,
      y: centroid.y + 18 + hashUnit(`${node.id}:cy`) * 8,
      z: centroid.z,
    });
  });

  // Any tree-role node still unplaced (missing edges) gets pinned to the trunk
  // at a stable height so nothing snaps to the origin.
  nodes.forEach((node) => {
    if (positions.has(node.id) || node.role === SAND_ROLE || !TREE_ROLES.has(node.role)) {
      return;
    }
    positions.set(node.id, {
      x: (hashUnit(`${node.id}:ux`) - 0.5) * 20,
      y: TREE_HEIGHT * (0.3 + hashUnit(`${node.id}:uy`) * 0.4),
      z: (hashUnit(`${node.id}:uz`) - 0.5) * 20,
    });
  });

  return positions;
}

function graph3DData(payload, nodes) {
  // Sand nodes (sources / daily work / research) leave the force graph and are
  // rendered as a particle field; keep only tree/star/constellation nodes here.
  const treeNodes = nodes.filter((node) => node.role !== SAND_ROLE);
  const visibleIds = new Set(treeNodes.map((node) => node.id));
  const positions = growthTreeLayout(payload, treeNodes);
  const links = payload.graph.edges
    .filter((edge) => visibleIds.has(edge.from) && visibleIds.has(edge.to))
    .map((edge, index) => ({
      id: `${edge.from}-${edge.to}-${edge.type}-${index}`,
      source: edge.from,
      target: edge.to,
      relation: edge.relation || edge.type,
      type: edge.type,
      suggested: edge.suggested,
      placeholder: edge.placeholder,
    }));
  const degree = new Map();
  links.forEach((link) => {
    degree.set(link.source, (degree.get(link.source) || 0) + 1);
    degree.set(link.target, (degree.get(link.target) || 0) + 1);
  });
  return {
    nodes: treeNodes.map((node) => {
      const pos = positions.get(node.id) || { x: 0, y: TREE_HEIGHT * 0.5, z: 0 };
      const nodeDegree = degree.get(node.id) || 0;
      const isStar = node.role === "star";
      return {
        ...node,
        x: pos.x,
        y: pos.y,
        z: pos.z,
        // Pin coordinates so the force engine never drifts the skeleton.
        fx: pos.x,
        fy: pos.y,
        fz: pos.z,
        group: node.role || node.layer,
        color: starTreeColor(node),
        starEmissive: isStar
          ? STAR_STATUS_EMISSIVE[cleanText(node.status)] ?? STAR_STATUS_EMISSIVE.locked
          : 0,
        val: Math.max(
          3,
          (isStar ? 3 : 5) + Math.min(9, nodeDegree) + (node.isPrimary ? 4 : 0) + (node.placeholder ? -1 : 0),
        ),
        degree: nodeDegree,
      };
    }),
    links,
  };
}

// Color for a star-tree node: stars tint by brightness, others by role.
function starTreeColor(node) {
  if (node.placeholder || node.implemented === false) {
    return "#a6b2ad";
  }
  return ROLE_COLORS[node.role] || NODE_COLORS[node.type] || "#68716f";
}


function graph3DSelectedLink(link, selectedNodeId) {
  const source = linkEndpointId(link.source);
  const target = linkEndpointId(link.target);
  return Boolean(selectedNodeId && (source === selectedNodeId || target === selectedNodeId));
}

function drawRoundedRect(ctx, x, y, width, height, radius) {
  const r = Math.min(radius, width / 2, height / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + width - r, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + r);
  ctx.lineTo(x + width, y + height - r);
  ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
  ctx.lineTo(x + r, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function createLabelSprite(text, color, selected) {
  const labelText = cleanText(text, "Node").slice(0, 36);
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  const fontSize = selected ? 46 : 38;
  const paddingX = selected ? 24 : 20;
  const paddingY = selected ? 13 : 10;
  ctx.font = `800 ${fontSize}px Inter, system-ui, sans-serif`;
  const measured = Math.ceil(ctx.measureText(labelText).width);
  canvas.width = Math.max(120, Math.min(620, measured + paddingX * 2));
  canvas.height = fontSize + paddingY * 2;
  ctx.font = `800 ${fontSize}px Inter, system-ui, sans-serif`;
  ctx.textBaseline = "middle";
  drawRoundedRect(ctx, 0, 0, canvas.width, canvas.height, selected ? 24 : 20);
  // Dark translucent pill + light text so labels stay below the bloom
  // threshold on the night sky (white fills would blow out into glare).
  ctx.fillStyle = selected ? "rgba(15, 22, 40, .92)" : "rgba(12, 17, 32, .74)";
  ctx.fill();
  ctx.strokeStyle = selected ? color : "rgba(150, 170, 210, .42)";
  ctx.lineWidth = selected ? 5 : 3;
  ctx.stroke();
  ctx.fillStyle = selected ? "#eaf1ff" : "#cdd8ee";
  ctx.fillText(labelText, paddingX, canvas.height / 2);
  const texture = new THREE.CanvasTexture(canvas);
  if ("colorSpace" in texture && THREE.SRGBColorSpace) {
    texture.colorSpace = THREE.SRGBColorSpace;
  }
  texture.needsUpdate = true;
  const material = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthWrite: false,
    opacity: selected ? 1 : 0.86,
  });
  const sprite = new THREE.Sprite(material);
  const scale = selected ? 8.8 : 9.6;
  sprite.scale.set(canvas.width / scale, canvas.height / scale, 1);
  sprite.position.set(0, selected ? -14 : -12, 0);
  return sprite;
}

function nodeThreeObject(node, selectedNodeId) {
  const selected = selectedNodeId === node.id;
  const color = node.color || starTreeColor(node);
  const group = new THREE.Group();

  // Stars: small, bright spheres whose emissive tracks skill status. No label
  // (82 of them) unless selected — the dome reads as a sky, not a tag cloud.
  if (node.role === "star") {
    const baseEmissive = Number.isFinite(node.starEmissive) ? node.starEmissive : STAR_STATUS_EMISSIVE.locked;
    const radius = Math.max(1.6, 1.8 + baseEmissive * 3.4) * (selected ? 1.8 : 1);
    const material = new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: selected ? Math.max(0.85, baseEmissive + 0.4) : baseEmissive,
      metalness: 0.0,
      roughness: 0.5,
      transparent: true,
      opacity: 0.55 + baseEmissive * 0.6,
    });
    const star = new THREE.Mesh(new THREE.SphereGeometry(radius, 14, 12), material);
    star.userData.baseEmissive = baseEmissive;
    star.userData.role = "star";
    group.add(star);
    if (selected) {
      group.add(createLabelSprite(node.label || node.id, "#bcd4ff", true));
    }
    group.userData.starMesh = star;
    return group;
  }

  const radius = Math.min(
    selected ? 8.5 : 6.2,
    Math.max(3.2, Math.sqrt(Math.max(1, node.val || 5)) * (selected ? 1.7 : 1.32)),
  );
  const geometry = node.placeholder || node.implemented === false
    ? new THREE.OctahedronGeometry(radius, 1)
    : new THREE.SphereGeometry(radius, 22, 18);
  const material = new THREE.MeshStandardMaterial({
    color,
    emissive: color,
    // Keep tree nodes below the bloom threshold so they read as distinct
    // colored beads against the night sky rather than a glare.
    emissiveIntensity: selected ? 0.34 : 0.14,
    metalness: 0.12,
    roughness: 0.62,
    transparent: true,
    opacity: node.placeholder || node.implemented === false ? 0.5 : 0.92,
  });
  group.add(new THREE.Mesh(geometry, material));
  if (selected) {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(radius * 1.42, Math.max(0.22, radius * 0.05), 10, 48),
      new THREE.MeshBasicMaterial({ color: "#ffffff", transparent: true, opacity: 0.94 }),
    );
    ring.rotation.x = Math.PI / 2;
    group.add(ring);
  }
  group.add(createLabelSprite(node.label || node.id, color, selected));
  return group;
}

function focusGraphCamera(graph, node, duration = 700) {
  if (!graph || !node) {
    return;
  }
  const distance = 48;
  const x = Number.isFinite(node.x) ? node.x : 0;
  const y = Number.isFinite(node.y) ? node.y : 0;
  const z = Number.isFinite(node.z) ? node.z : 0;
  graph.cameraPosition(
    { x: x + distance * 0.68, y: y + distance * 0.38, z: z + distance * 1.08 },
    { x, y, z },
    duration,
  );
}

function connectedGraphNode(node) {
  return (node?.degree || 0) > 0;
}

function fitGraphCamera(graph, duration = 700) {
  // Include every node in the bounds: the star dome's 82 skills are mostly
  // edge-less, but the deterministic layout keeps them on-screen, so the fit
  // must frame the whole tree + sky, not just connected nodes.
  graph?.zoomToFit?.(duration, 28);
}

function graph3DLinkWidth(link, selectedNodeId) {
  const base = EDGE_WIDTHS[link.relation] || 1.1;
  if (graph3DSelectedLink(link, selectedNodeId)) {
    return Math.max(1.35, base * 1.4);
  }
  return Math.max(0.45, base * 0.58);
}

function Graph3DLegend({ payload, graphData }) {
  const ui = payload.ui;
  const layers = graphLayers(payload).filter((layer) => graphData.nodes.some((node) => node.layer === layer));
  const relations = [...new Set(graphData.links.map((link) => cleanText(link.relation, link.type)).filter(Boolean))].slice(0, 9);
  return (
    <div className="hd-graph3d-legend" aria-hidden="true">
      <div className="hd-graph3d-legend-group">
        {layers.map((layer) => (
          <span key={layer}>
            <i style={{ background: NODE_COLORS[graphData.nodes.find((node) => node.layer === layer)?.type] || "#68716f" }} />
            {layerLabel(ui, layer)}
          </span>
        ))}
      </div>
      <div className="hd-graph3d-legend-group relations">
        {relations.map((relation) => (
          <span key={relation}>
            <i style={{ background: relationColor(relation) }} />
            {relation.replace(/_/g, " ")}
          </span>
        ))}
      </div>
    </div>
  );
}

// Build the sand particle field (sources / daily work / research). Sand nodes
// are clustered by theme (tags → goal_refs → kind) and rendered as one
// THREE.Points cloud — atmosphere, not clickable nodes. Returns {points,
// clusters} where clusters carry the member items for hover aggregation.
function buildSandField(payload, sandNodes) {
  if (!sandNodes.length) {
    return null;
  }
  const themeOf = (node) => {
    const meta = asObject(node.meta);
    const tag = asArray(meta.tags).map((t) => cleanText(t)).find(Boolean);
    if (tag) return `tag:${tag}`;
    const goalRef = asArray(meta.goal_refs).map((g) => cleanText(g)).find(Boolean);
    if (goalRef) return `goal:${goalRef}`;
    const kind = cleanText(node.metric) || cleanText(node.type) || "sand";
    return `kind:${kind}`;
  };
  const clustersByKey = new Map();
  sandNodes.forEach((node) => {
    const key = themeOf(node);
    if (!clustersByKey.has(key)) {
      clustersByKey.set(key, { key, label: key.split(":").slice(1).join(":") || key, nodes: [] });
    }
    clustersByKey.get(key).nodes.push(node);
  });
  const clusters = [...clustersByKey.values()];
  const clusterCount = Math.max(1, clusters.length);

  const positions = [];
  const colors = [];
  const basePositions = [];
  const color = new THREE.Color();
  clusters.forEach((cluster, ci) => {
    const angle = (ci / clusterCount) * Math.PI * 2 + 0.7;
    const ringR = 30 + (ci % 3) * 16;
    const center = {
      x: Math.cos(angle) * ringR,
      y: 26 + hashUnit(`${cluster.key}:cy`) * 8,
      z: Math.sin(angle) * ringR,
    };
    cluster.center = center;
    color.set(SAND_PALETTE[ci % SAND_PALETTE.length]);
    cluster.nodes.forEach((node) => {
      // Gaussian-ish scatter around the cluster center — a thin ground haze.
      const dx = (hashUnit(`${node.id}:sx`) + hashUnit(`${node.id}:sx2`) - 1) * 18;
      const dy = (hashUnit(`${node.id}:sy`) + hashUnit(`${node.id}:sy2`) - 1) * 5;
      const dz = (hashUnit(`${node.id}:sz`) + hashUnit(`${node.id}:sz2`) - 1) * 18;
      const px = center.x + dx;
      const py = center.y + dy;
      const pz = center.z + dz;
      positions.push(px, py, pz);
      basePositions.push(px, py, pz);
      colors.push(color.r, color.g, color.b);
    });
  });

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  const material = new THREE.PointsMaterial({
    size: 3.4,
    sizeAttenuation: true,
    vertexColors: true,
    transparent: true,
    opacity: 0.72,
    depthWrite: false,
  });
  const points = new THREE.Points(geometry, material);
  points.userData.basePositions = Float32Array.from(basePositions);
  points.userData.isSandField = true;
  return { points, clusters };
}

const SAND_PALETTE = ["#c4b186", "#a8b48f", "#bfa27a", "#9fb0a6", "#c9b27c", "#b0a394"];

function Graph3DView({ payload, nodes, selectedNodeId, onSelectNode, emptyMessage = "", minHeight = GRAPH_3D_MIN_HEIGHT, compact = false }) {
  const ui = payload.ui;
  const graphRef = useRef(null);
  const wrapRef = useRef(null);
  const sceneObjsRef = useRef({ points: null, clusters: [], bloom: null, raf: 0 });
  const [size, setSize] = useState({ width: 900, height: minHeight });
  const [sandHover, setSandHover] = useState(null);
  const graphData = useMemo(() => graph3DData(payload, nodes), [payload, nodes]);
  const sandNodes = useMemo(() => nodes.filter((node) => node.role === SAND_ROLE), [nodes]);

  useLayoutEffect(() => {
    const element = wrapRef.current;
    if (!element) {
      return undefined;
    }
    const update = () => {
      const rect = element.getBoundingClientRect();
      const next = {
        width: Math.max(320, Math.round(element.clientWidth || rect.width || 900)),
        height: Math.max(minHeight, Math.round(element.clientHeight || rect.height || minHeight)),
      };
      graphRef.current?.width?.(next.width);
      graphRef.current?.height?.(next.height);
      element.querySelectorAll(".scene-container, .scene-container canvas").forEach((child) => {
        child.style.setProperty("width", `${next.width}px`, "important");
        child.style.setProperty("height", `${next.height}px`, "important");
      });
      setSize((current) => {
        if (Math.abs(current.width - next.width) < 2 && Math.abs(current.height - next.height) < 2) {
          return current;
        }
        return next;
      });
    };
    update();
    const rafs = [
      window.requestAnimationFrame(update),
      window.requestAnimationFrame(() => window.requestAnimationFrame(update)),
    ];
    const timers = [
      window.setTimeout(update, 180),
      window.setTimeout(update, 650),
      window.setTimeout(update, 1400),
    ];
    const interval = window.setInterval(update, 250);
    const stopInterval = window.setTimeout(() => window.clearInterval(interval), 2600);
    const observer = new ResizeObserver(update);
    observer.observe(element);
    window.addEventListener("resize", update);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", update);
      rafs.forEach((id) => window.cancelAnimationFrame(id));
      timers.forEach((id) => window.clearTimeout(id));
      window.clearInterval(interval);
      window.clearTimeout(stopInterval);
    };
  }, [minHeight]);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) {
      return;
    }
    graph.width?.(size.width);
    graph.height?.(size.height);
    window.setTimeout(() => fitGraphCamera(graph, 350), 80);
  }, [size.width, size.height]);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) {
      return undefined;
    }
    // Skeleton is pinned via fx/fy/fz, so neutralize the force engine — the
    // "Live" feel comes from the breathing rAF loop below, not force drift.
    const charge = graph.d3Force?.("charge");
    if (charge?.strength) {
      charge.strength(0);
    }

    const scene = graph.scene?.();
    const store = sceneObjsRef.current;

    // 1. Bloom — make bright stars glow, leave the dim (locked) ones matte.
    let bloom = null;
    try {
      const composer = graph.postProcessingComposer?.();
      if (composer && !store.bloom) {
        bloom = new UnrealBloomPass(
          new THREE.Vector2(size.width || 900, size.height || minHeight),
          0.62, // strength — subtle halo, not a floodlight
          0.55, // radius
          0.62, // threshold — only genuinely bright stars bloom
        );
        composer.addPass(bloom);
        store.bloom = bloom;
      }
    } catch (err) {
      // Bloom is a progressive enhancement; ignore if composer isn't ready.
    }

    // 2. Sand particle field.
    if (scene) {
      if (store.points) {
        scene.remove(store.points);
        store.points.geometry?.dispose?.();
        store.points.material?.dispose?.();
        store.points = null;
        store.clusters = [];
      }
      const sand = buildSandField(payload, sandNodes);
      if (sand) {
        scene.add(sand.points);
        store.points = sand.points;
        store.clusters = sand.clusters;
      }
    }

    window.setTimeout(() => fitGraphCamera(graph, 700), 240);
    window.setTimeout(() => fitGraphCamera(graph, 500), 920);

    // 3. Breathing animation loop — single rAF, updates only materials and the
    // sand position attribute (no geometry rebuilds).
    let frame = 0;
    const animate = () => {
      frame += 1;
      const t = frame / 60;
      // Stars: gentle per-star emissive flicker, phase offset by index.
      scene?.traverse?.((obj) => {
        if (obj.userData?.role === "star") {
          const base = obj.userData.baseEmissive || 0;
          const phase = (obj.id % 17) * 0.37;
          obj.material.emissiveIntensity = Math.max(0, base + Math.sin(t * 1.6 + phase) * base * 0.35);
        }
      });
      // Sand: slow drift around the base positions.
      if (store.points) {
        const attr = store.points.geometry.getAttribute("position");
        const base = store.points.userData.basePositions;
        if (attr && base) {
          for (let i = 0; i < attr.count; i += 1) {
            const o = i * 3;
            attr.array[o] = base[o] + Math.sin(t * 0.4 + i * 0.5) * 1.2;
            attr.array[o + 1] = base[o + 1] + Math.sin(t * 0.32 + i * 0.7) * 0.8;
            attr.array[o + 2] = base[o + 2] + Math.cos(t * 0.36 + i * 0.6) * 1.2;
          }
          attr.needsUpdate = true;
        }
      }
      store.raf = window.requestAnimationFrame(animate);
    };
    store.raf = window.requestAnimationFrame(animate);

    return () => {
      window.cancelAnimationFrame(store.raf);
      store.raf = 0;
      if (scene && store.points) {
        scene.remove(store.points);
        store.points.geometry?.dispose?.();
        store.points.material?.dispose?.();
        store.points = null;
        store.clusters = [];
      }
      if (store.bloom) {
        try {
          const composer = graph.postProcessingComposer?.();
          composer?.removePass?.(store.bloom);
        } catch (err) {
          // composer already gone
        }
        store.bloom.dispose?.();
        store.bloom = null;
      }
    };
  }, [graphData, sandNodes, payload, size.width, size.height, minHeight]);

  useEffect(() => {
    const target = graphData.nodes.find((node) => node.id === selectedNodeId);
    if (target) {
      window.setTimeout(() => {
        if (connectedGraphNode(target)) {
          focusGraphCamera(graphRef.current, target);
        } else {
          fitGraphCamera(graphRef.current);
        }
      }, 80);
    }
  }, [graphData, selectedNodeId]);

  // Hover aggregation over the sand field — raycast pointer against the
  // particle cloud and, on a hit, surface the nearest cluster's items.
  useEffect(() => {
    const element = wrapRef.current;
    const graph = graphRef.current;
    if (!element || !graph) {
      return undefined;
    }
    const raycaster = new THREE.Raycaster();
    raycaster.params.Points = { threshold: 9 };
    const pointer = new THREE.Vector2();
    let scheduled = false;
    const onMove = (event) => {
      if (scheduled) {
        return;
      }
      scheduled = true;
      window.requestAnimationFrame(() => {
        scheduled = false;
        const store = sceneObjsRef.current;
        const camera = graph.camera?.();
        if (!store.points || !camera) {
          if (sandHover) setSandHover(null);
          return;
        }
        const rect = element.getBoundingClientRect();
        pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(pointer, camera);
        const hits = raycaster.intersectObject(store.points, false);
        if (!hits.length) {
          if (sandHover) setSandHover(null);
          return;
        }
        // Find the cluster whose center is nearest the hit point.
        const point = hits[0].point;
        let best = null;
        let bestDist = Infinity;
        store.clusters.forEach((cluster) => {
          const c = cluster.center;
          const d = (c.x - point.x) ** 2 + (c.y - point.y) ** 2 + (c.z - point.z) ** 2;
          if (d < bestDist) {
            bestDist = d;
            best = cluster;
          }
        });
        if (best) {
          setSandHover({
            label: best.label,
            count: best.nodes.length,
            items: best.nodes.slice(0, 8).map((node) => ({
              id: node.id,
              title: node.label || node.id,
              kind: cleanText(node.metric) || cleanText(node.type),
            })),
            x: event.clientX - rect.left,
            y: event.clientY - rect.top,
          });
        }
      });
    };
    const onLeave = () => setSandHover(null);
    element.addEventListener("pointermove", onMove);
    element.addEventListener("pointerleave", onLeave);
    return () => {
      element.removeEventListener("pointermove", onMove);
      element.removeEventListener("pointerleave", onLeave);
    };
  }, [graphData, sandNodes, sandHover]);

  if (!graphData.nodes.length) {
    return (
      <div className="hd-graph3d-stage hd-canvas-surface-empty">
        <p className="hd-empty">{emptyMessage || label(ui, "dashboard_canvas_no_layers", "All layers are hidden.")}</p>
      </div>
    );
  }

  return (
    <div className={compact ? "hd-graph3d-stage compact" : "hd-graph3d-stage"} ref={wrapRef} data-testid="dashboard-3d-graph">
      <div className="hd-graph3d-force">
        <ForceGraph3D
          ref={graphRef}
          width={size.width}
          height={size.height}
          graphData={graphData}
          backgroundColor="#070b18"
          nodeId="id"
          nodeVal="val"
          nodeLabel={(node) => `${node.label || node.id}\n${layerLabel(ui, node.layer)} · ${translatedNodeType(ui, node.type)}`}
          nodeColor={(node) => node.color || starTreeColor(node)}
          nodeThreeObject={(node) => nodeThreeObject(node, selectedNodeId)}
          nodeThreeObjectExtend={false}
          nodeOpacity={0.92}
          nodeResolution={18}
          linkLabel={(link) => cleanText(link.relation, link.type).replace(/_/g, " ")}
          linkColor={(link) => relationColor(link.relation || link.type)}
          linkWidth={(link) => graph3DLinkWidth(link, selectedNodeId)}
          linkOpacity={0.34}
          linkCurvature={(link) => (link.relation === "watches" ? 0.2 : link.relation === "feedback" ? 0.16 : 0.04)}
          linkDirectionalArrowLength={(link) => (link.placeholder ? 0 : 2.6)}
          linkDirectionalArrowColor={(link) => relationColor(link.relation || link.type)}
          linkDirectionalArrowRelPos={0.74}
          linkDirectionalParticles={(link) => (graph3DSelectedLink(link, selectedNodeId) ? 2 : link.relation === "supports" ? 1 : 0)}
          linkDirectionalParticleSpeed={0.005}
          linkDirectionalParticleWidth={(link) => (graph3DSelectedLink(link, selectedNodeId) ? 1.85 : 0.95)}
          linkDirectionalParticleColor={(link) => relationColor(link.relation || link.type)}
          showNavInfo={false}
          controlType="orbit"
          rendererConfig={{ antialias: true, alpha: true, preserveDrawingBuffer: true }}
          enableNodeDrag={false}
          cooldownTicks={0}
          warmupTicks={0}
          d3VelocityDecay={0.9}
          onNodeClick={(node) => {
            onSelectNode(node.id);
            focusGraphCamera(graphRef.current, node);
          }}
          onBackgroundClick={() => fitGraphCamera(graphRef.current)}
        />
      </div>
      {sandHover ? (
        <div
          className="hd-sand-tooltip"
          style={{ left: `${sandHover.x + 14}px`, top: `${sandHover.y + 14}px` }}
        >
          <strong>{sandHover.label} · {sandHover.count}</strong>
          <ul>
            {sandHover.items.map((item) => (
              <li key={item.id}>
                <span>{item.title}</span>
                {item.kind ? <em>{item.kind}</em> : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="hd-graph3d-toolbar">
        <button type="button" data-action="graph-fit" onClick={() => fitGraphCamera(graphRef.current)}>
          {label(ui, "dashboard_graph_fit", "Fit")}
        </button>
        <button
          type="button"
          data-action="graph-focus-selected"
          disabled={!selectedNodeId}
          onClick={() => {
            const target = graphData.nodes.find((node) => node.id === selectedNodeId);
            if (connectedGraphNode(target)) {
              focusGraphCamera(graphRef.current, target);
            } else {
              fitGraphCamera(graphRef.current);
            }
          }}
        >
          {label(ui, "dashboard_graph_focus_selected", "Focus")}
        </button>
      </div>
      <Graph3DLegend payload={payload} graphData={graphData} />
    </div>
  );
}

function ExploreMapView({ payload, nodes, selectedNodeId, onSelectNode }) {
  const ui = payload.ui;
  const map = useMemo(() => exploreMapData(payload, nodes, selectedNodeId), [payload, nodes, selectedNodeId]);
  if (!map.nodes.length) {
    return (
      <div className="hd-explore-map-stage hd-canvas-surface-empty">
        <p className="hd-empty">{label(ui, "dashboard_canvas_no_layers", "All layers are hidden.")}</p>
      </div>
    );
  }
  return (
    <div className="hd-explore-map-stage" style={{ "--lane-count": map.lanes.length }}>
      <div className="hd-explore-map-lanes" aria-hidden="true">
        {map.lanes.map((lane) => (
          <div key={lane.key} className={lane.total ? "hd-explore-map-lane" : "hd-explore-map-lane empty"}>
            <span>{label(ui, lane.labelKey, lane.fallback)}</span>
            <small>{lane.total}{lane.moreCount ? ` +${lane.moreCount}` : ""}</small>
          </div>
        ))}
      </div>
      <svg className="hd-explore-map-links" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <marker id="hd-explore-arrow" markerHeight="4" markerWidth="5" orient="auto" refX="4" refY="2">
            <path d="M0,0 L4,2 L0,4 Z" />
          </marker>
        </defs>
        {map.edges.map((edge) => (
          <path
            key={edge.id}
            className={[
              "hd-explore-map-link",
              edge.active ? "active" : "",
              edge.suggested || edge.placeholder ? "suggested" : "",
            ].filter(Boolean).join(" ")}
            d={exploreEdgePath(edge)}
            markerEnd="url(#hd-explore-arrow)"
          />
        ))}
      </svg>
      <div className="hd-explore-map-nodes">
        {map.nodes.map(({ node, x, y }) => (
          <button
            key={node.id}
            className={[
              "hd-explore-map-node",
              `type-${node.type}`,
              selectedNodeId === node.id ? "selected" : "",
              node.placeholder ? "placeholder" : "",
              node.implemented === false ? "not-implemented" : "",
            ].filter(Boolean).join(" ")}
            style={{ left: `${x}%`, top: `${y}%`, "--node-color": nodeColor(node) }}
            type="button"
            data-action="select-node"
            data-source="explore-map"
            data-node-id={node.id}
            onClick={() => onSelectNode(node.id)}
          >
            <span className="hd-node-dot" style={{ background: nodeColor(node) }} />
            <strong>{node.label}</strong>
            <small>{translatedNodeType(ui, node.type)}</small>
            {node.primaryAction?.label || node.metric || node.status ? (
              <em>{node.primaryAction?.label || node.metric || node.status}</em>
            ) : null}
          </button>
        ))}
      </div>
    </div>
  );
}

function ExploreNodeList({
  payload,
  nodes,
  selectedNodeId,
  scope,
  setScope,
  query,
  setQuery,
  showPlaceholders,
  setShowPlaceholders,
  onSelectNode,
}) {
  const ui = payload.ui;
  const orderedNodes = sortedExploreNodes(payload, nodes, selectedNodeId);
  const groups = groupedExploreNodes(payload, orderedNodes);
  return (
    <aside className="hd-explore-panel">
      <div>
        <span className="hd-eyebrow">{label(ui, "dashboard_explore_title", "Explore")}</span>
        <strong>{label(ui, "dashboard_explore_nodes", "Graph nodes")}</strong>
        <small>{orderedNodes.length} {label(ui, "dashboard_explore_result_count", "shown")}</small>
      </div>
      <div className="hd-explore-scope">
        {["all", "context", "upstream", "downstream"].map((item) => (
          <button
            key={item}
            className={scope === item ? "active" : ""}
            type="button"
            data-action="explore-scope"
            data-scope={item}
            onClick={() => setScope(item)}
          >
            {label(ui, `dashboard_explore_${item}`, item)}
          </button>
        ))}
      </div>
      <label className="hd-explore-search">
        <span>{label(ui, "dashboard_explore_search", "Search")}</span>
        <input
          value={query}
          type="search"
          data-action="explore-search"
          placeholder={label(ui, "dashboard_explore_search_placeholder", "Node, layer, status")}
          onChange={(event) => setQuery(event.currentTarget.value)}
        />
      </label>
      <label className="hd-explore-check">
        <input
          type="checkbox"
          data-action="hide-placeholders"
          checked={!showPlaceholders}
          onChange={(event) => setShowPlaceholders(!event.currentTarget.checked)}
        />
        <span>{label(ui, "dashboard_explore_hide_placeholders", "Hide placeholders")}</span>
      </label>
      <div className="hd-explore-list">
        {groups.length ? groups.map((group) => (
          <div className="hd-explore-group" key={group.layer} data-layer={group.layer}>
            <div className="hd-explore-group-title">
              <span>{layerLabel(ui, group.layer)}</span>
              <small>{group.nodes.length}</small>
            </div>
            {group.nodes.map((node) => (
              <button
                key={node.id}
                className={[
                  selectedNodeId === node.id ? "selected" : "",
                  isPlaceholderNode(node) ? "placeholder" : "",
                ].filter(Boolean).join(" ")}
                type="button"
                data-action="select-node"
                data-source="explore-list"
                data-node-id={node.id}
                onClick={() => onSelectNode(node.id)}
              >
                <span className="hd-node-dot" style={{ background: nodeColor(node) }} />
                <span>
                  <strong>{node.label}</strong>
                  <small>{translatedNodeType(ui, node.type)} · {node.metric || node.status || layerLabel(ui, node.layer)}</small>
                </span>
              </button>
            ))}
          </div>
        )) : (
          <p className="hd-empty">{label(ui, "dashboard_explore_no_matches", "No graph nodes match this filter.")}</p>
        )}
      </div>
    </aside>
  );
}

function EmbeddedCanvasFrame({ payload, embed, showHeader = true }) {
  const ui = payload.ui;
  const [loaded, setLoaded] = useState(false);
  return (
    <section className={showHeader ? "hd-canvas-embed" : "hd-canvas-embed hd-canvas-embed-inline"} aria-label={label(ui, "dashboard_embedded_canvas_title", "Embedded canvas")}>
      {showHeader ? (
        <header>
          <div>
            <span className="hd-eyebrow">{label(ui, "dashboard_graph_eyebrow", "Canvas")}</span>
            <h3>{label(ui, "dashboard_embedded_canvas_title", "Embedded canvas")}</h3>
          </div>
          {embed.standaloneUrl ? (
            <a href={embed.standaloneUrl} target="_blank" rel="noreferrer" data-action="open-8502-canvas">
              {label(ui, "dashboard_open_8502_canvas", "Open 8502 Canvas")}
            </a>
          ) : null}
        </header>
      ) : null}
      <div className={loaded ? "hd-canvas-embed-frame loaded" : "hd-canvas-embed-frame"}>
        {!loaded ? <span>{label(ui, "dashboard_graph_loading", "Loading graph...")}</span> : null}
        <iframe
          title={label(ui, "dashboard_embedded_canvas_title", "Embedded canvas")}
          src={embed.url}
          loading="eager"
          onLoad={() => setLoaded(true)}
        />
      </div>
    </section>
  );
}

function CanvasSummaryPanel({ payload, embed }) {
  const ui = payload.ui;
  const [showEmbed, setShowEmbed] = useState(false);
  const nodesById = useMemo(() => new Map(payload.graph.nodes.map((node) => [node.id, node])), [payload]);
  const focusNodes = payload.graph.focusPath.map((id) => nodesById.get(id)).filter(Boolean);
  const attentionCount = asArray(payload.graph.attention.nodes).length;
  const graphNodeCount = asArray(payload.graph.nodes).length;
  const previewNodes = focusNodes.slice(0, 8);
  return (
    <section className="hd-canvas-summary" data-section="canvas-summary">
      <header>
        <div>
          <span className="hd-eyebrow">{label(ui, "dashboard_graph_eyebrow", "Canvas")}</span>
          <h3>{label(ui, "dashboard_canvas_summary_title", "Canvas summary")}</h3>
          <p>{label(ui, "dashboard_canvas_summary_caption", "The daily dashboard keeps the big canvas folded until you need deeper graph exploration.")}</p>
        </div>
        {embed.standaloneUrl ? (
          <a href={embed.standaloneUrl} target="_blank" rel="noreferrer" data-action="open-8502-canvas">
            {label(ui, "dashboard_open_8502_canvas", "Open 8502 Canvas")}
          </a>
        ) : null}
      </header>

      <div className="hd-canvas-summary-body">
        <div className="hd-canvas-summary-path" aria-label={label(ui, "dashboard_view_focus_path", "Focus Path")}>
          {previewNodes.length ? previewNodes.map((node, index) => (
            embed.standaloneUrl ? (
              <a
                key={node.id}
                className={`type-${node.type} ${node.placeholder ? "placeholder" : ""}`}
                href={dashboardNodeUrl(embed.standaloneUrl, node.id)}
                target="_blank"
                rel="noreferrer"
                data-action="open-8502-node"
                data-node-id={node.id}
              >
                <small>{String(index + 1).padStart(2, "0")} · {translatedNodeType(ui, node.type)}</small>
                <strong>{node.label}</strong>
              </a>
            ) : (
              <span key={node.id} className={`type-${node.type} ${node.placeholder ? "placeholder" : ""}`}>
              <small>{String(index + 1).padStart(2, "0")} · {translatedNodeType(ui, node.type)}</small>
              <strong>{node.label}</strong>
              </span>
            )
          )) : (
            <p className="hd-empty">{label(ui, "dashboard_canvas_no_layers", "All layers are hidden.")}</p>
          )}
        </div>
        <div className="hd-canvas-summary-stats">
          <span><strong>{focusNodes.length}</strong>{label(ui, "dashboard_view_focus_path", "Focus Path")}</span>
          <span><strong>{attentionCount}</strong>{label(ui, "dashboard_attention_title", "Attention")}</span>
          <span><strong>{graphNodeCount}</strong>{label(ui, "dashboard_explore_nodes", "Graph nodes")}</span>
        </div>
      </div>

      <details
        className="hd-canvas-embed-details"
        onToggle={(event) => setShowEmbed(event.currentTarget.open)}
      >
        <summary data-action="load-embedded-canvas">
          {label(ui, "dashboard_canvas_load_embed", "Load embedded canvas")}
        </summary>
        {showEmbed ? <EmbeddedCanvasFrame payload={payload} embed={embed} showHeader={false} /> : null}
      </details>
    </section>
  );
}

function GraphHeroPanel({ payload, embed, selectedNodeId, onSelectNode, onEmit }) {
  const ui = payload.ui;
  const [showEmbed, setShowEmbed] = useState(false);
  const itemsById = useMemo(() => {
    const map = new Map();
    actionQueueItems(payload).forEach((item) => map.set(item.id, item));
    return map;
  }, [payload]);
  const evidenceItem = itemsById.get("evidence");
  const signalTiles = ["output", "focus", "gap"]
    .map((id) => itemsById.get(id))
    .filter(Boolean);
  const nodesById = useMemo(() => new Map(payload.graph.nodes.map((node) => [node.id, node])), [payload]);
  const selectedNode = nodesById.get(selectedNodeId) || preferredNode(payload);
  const heroNodes = useMemo(() => {
    const scoped = graphExploreNodes(payload, new Set(), selectedNodeId, "context");
    const selected = nodesById.get(selectedNodeId);
    const combined = selected && !scoped.some((node) => node.id === selected.id)
      ? [selected, ...scoped]
      : scoped;
    return sortedExploreNodes(payload, combined, selectedNodeId).slice(0, 42);
  }, [payload, nodesById, selectedNodeId]);

  return (
    <section className="hd-graph-hero" data-section="graph-hero">
      <div className="hd-graph-hero-visual">
        <header className="hd-graph-hero-header">
          <div>
            <span className="hd-eyebrow">{label(ui, "dashboard_graph_eyebrow", "Canvas")}</span>
            <h3>{label(ui, "dashboard_graph_hero_title", "Live growth graph")}</h3>
            <p>{label(ui, "dashboard_graph_hero_caption", "A compact 3D map of today’s goals, sources, evidence, skills, and outputs.")}</p>
          </div>
          {embed?.standaloneUrl ? (
            <a href={dashboardNodeUrl(embed.standaloneUrl, selectedNode?.id || "")} target="_blank" rel="noreferrer" data-action="open-8502-canvas">
              {label(ui, "dashboard_open_8502_canvas", "Open 8502 Canvas")}
            </a>
          ) : null}
        </header>
        <Graph3DView
          payload={payload}
          nodes={heroNodes}
          selectedNodeId={selectedNode?.id || selectedNodeId}
          onSelectNode={onSelectNode}
          minHeight={340}
          compact
          emptyMessage={label(ui, "dashboard_explore_no_matches", "No graph nodes match this filter.")}
        />
      </div>

      <aside className="hd-graph-hero-panel">
        <div className="hd-hero-top">
          <SkillProgressCard payload={payload} onEmit={onEmit} className="hd-hero-skill" />
          {evidenceItem ? (
            <button
              className={`hd-hero-evidence ${evidenceItem.tone || ""}`}
              type="button"
              data-action="navigate"
              data-dashboard-action={`hero:${evidenceItem.id}`}
              data-target={evidenceItem.path}
              onClick={() => onEmit(navigationEvent(evidenceItem.path))}
            >
              <span>{evidenceItem.eyebrow}</span>
              <strong>{evidenceItem.title}</strong>
              <small>{evidenceItem.detail}</small>
              <em>{evidenceItem.count}</em>
            </button>
          ) : null}
        </div>

        <div className="hd-hero-signal-grid" aria-label={label(ui, "dashboard_today_focus_title", "Today focus")}>
          {signalTiles.map((item) => (
            <button
              key={item.id}
              className={`hd-hero-signal ${item.tone || ""}`}
              type="button"
              data-action="navigate"
              data-dashboard-action={`hero-signal:${item.id}`}
              data-target={item.path}
              onClick={() => onEmit(navigationEvent(item.path))}
            >
              <span>{item.eyebrow}</span>
              <strong>{item.count}</strong>
            </button>
          ))}
        </div>

        <HealthSummaryPanel payload={payload} className="hd-hero-health" />
      </aside>

      {embed?.url ? (
        <details
          className="hd-graph-hero-embed"
          onToggle={(event) => setShowEmbed(event.currentTarget.open)}
        >
          <summary data-action="load-embedded-canvas">
            {label(ui, "dashboard_canvas_load_embed", "Load embedded canvas")}
          </summary>
          {showEmbed ? <EmbeddedCanvasFrame payload={payload} embed={embed} showHeader={false} /> : null}
        </details>
      ) : null}
    </section>
  );
}

function ContextCanvas({ payload, selectedNodeId, onSelectNode, onEmit, onCreateGoal, viewMode, setViewMode, readOnly = false }) {
  const ui = payload.ui;
  const [hiddenLayers, setHiddenLayers] = useState(() => new Set());
  const [exploreScope, setExploreScope] = useState("all");
  const [exploreQuery, setExploreQuery] = useState("");
  const [showPlaceholders, setShowPlaceholders] = useState(true);
  const filterLayers = useMemo(() => graphLayers(payload), [payload]);
  const insight = useMemo(() => graphInsight(payload), [payload]);
  const data = useMemo(() => flowData(payload, hiddenLayers, viewMode), [payload, hiddenLayers, viewMode]);
  const rawExploreNodes = useMemo(
    () => graphExploreNodes(payload, hiddenLayers, selectedNodeId, exploreScope),
    [payload, hiddenLayers, selectedNodeId, exploreScope],
  );
  const exploreNodes = useMemo(
    () => filterExploreNodes(payload, rawExploreNodes, exploreQuery, showPlaceholders),
    [payload, rawExploreNodes, exploreQuery, showPlaceholders],
  );

  function toggleLayer(layer) {
    setHiddenLayers((current) => {
      const next = new Set(current);
      if (next.has(layer)) {
        next.delete(layer);
      } else {
        next.add(layer);
      }
      return next;
    });
  }

  function showAllLayers() {
    setHiddenLayers(new Set());
  }

  const allLayersHidden = filterLayers.length > 0 && hiddenLayers.size >= filterLayers.length;

  return (
    <section className="hd-canvas-panel">
      <header>
        <div>
          <span className="hd-eyebrow">{label(ui, "dashboard_graph_eyebrow", "Canvas")}</span>
          <h3>{label(ui, "dashboard_graph_title", "Context Canvas")}</h3>
        </div>
        <div className="hd-segmented">
          <button className={viewMode === "focus" ? "active" : ""} type="button" data-action="view-toggle" data-view="focus" onClick={() => setViewMode("focus")}>
            {label(ui, "dashboard_view_focus_path", "Focus Path")}
          </button>
          <button className={viewMode === "canvas" ? "active" : ""} type="button" data-action="view-toggle" data-view="canvas" onClick={() => setViewMode("canvas")}>
            {label(ui, "dashboard_view_canvas", "2D Canvas")}
          </button>
          <button className={viewMode === "attention" ? "active" : ""} type="button" data-action="view-toggle" data-view="attention" onClick={() => setViewMode("attention")}>
            {label(ui, "dashboard_view_attention", "Attention")}
          </button>
          <button className={viewMode === "3d" ? "active" : ""} type="button" data-action="view-toggle" data-view="3d" onClick={() => setViewMode("3d")}>
            {label(ui, "dashboard_view_3d_graph", "3D Graph")}
          </button>
        </div>
      </header>

      <details className="hd-canvas-toolbar">
        <summary>{label(ui, "dashboard_canvas_more_filters", "More filters")}</summary>
        <div className="hd-filter-row">
          {filterLayers.map((layer) => (
            <button
              key={layer}
              className={hiddenLayers.has(layer) ? "" : "active"}
              type="button"
              data-action="filter-toggle"
              data-layer={layer}
              onClick={() => toggleLayer(layer)}
            >
              {layerLabel(ui, layer)}
            </button>
          ))}
        </div>
        {hiddenLayers.size ? (
          <button className="hd-ghost hd-toolbar-reset" type="button" data-action="filter-reset" onClick={showAllLayers}>
            {label(ui, "dashboard_canvas_reset_filters", "Show all layers")}
          </button>
        ) : null}
      </details>

      <CanvasSetupBanner
        payload={payload}
        insight={insight}
        hiddenLayers={hiddenLayers}
        onEmit={onEmit}
        onCreateGoal={onCreateGoal}
        readOnly={readOnly}
      />

      <AttentionSummary payload={payload} onSelectNode={onSelectNode} />

      {viewMode === "focus" ? (
        <FocusPathView payload={payload} selectedNodeId={selectedNodeId} onSelectNode={onSelectNode} />
      ) : viewMode === "attention" ? (
        <AttentionCanvasView payload={payload} onSelectNode={onSelectNode} />
      ) : viewMode === "3d" ? (
        <div className="hd-explore-canvas">
          {allLayersHidden ? (
            <div className="hd-canvas-surface hd-canvas-surface-empty">
              <p className="hd-empty">{label(ui, "dashboard_canvas_no_layers", "All layers are hidden.")}</p>
            </div>
          ) : (
            <>
              <Graph3DView
                payload={payload}
                nodes={exploreNodes}
                selectedNodeId={selectedNodeId}
                onSelectNode={onSelectNode}
                emptyMessage={label(ui, "dashboard_explore_no_matches", "No graph nodes match this filter.")}
              />
              <ExploreNodeList
                payload={payload}
                nodes={exploreNodes}
                selectedNodeId={selectedNodeId}
                scope={exploreScope}
                setScope={setExploreScope}
                query={exploreQuery}
                setQuery={setExploreQuery}
                showPlaceholders={showPlaceholders}
                setShowPlaceholders={setShowPlaceholders}
                onSelectNode={onSelectNode}
              />
            </>
          )}
        </div>
      ) : (
        <div className="hd-flow-wrap">
          {allLayersHidden ? (
            <div className="hd-canvas-surface hd-canvas-surface-empty">
              <p className="hd-empty">{label(ui, "dashboard_canvas_no_layers", "All layers are hidden.")}</p>
            </div>
          ) : (
            <ReactFlow
              nodes={data.nodes.map((node) => ({ ...node, selected: node.id === selectedNodeId }))}
              edges={data.edges}
              nodeTypes={NODE_TYPES}
              defaultEdgeOptions={{
                interactionWidth: 18,
              }}
              fitView
              fitViewOptions={{ padding: 0.2 }}
              minZoom={0.36}
              maxZoom={1.5}
              panOnDrag
              zoomOnScroll
              nodesDraggable={false}
              onNodeClick={(_, node) => onSelectNode(node.id)}
              proOptions={{ hideAttribution: true }}
            >
              <Background color="#dde6e1" gap={24} size={1} />
              <Controls showInteractive={false} />
            </ReactFlow>
          )}
        </div>
      )}
    </section>
  );
}

function GoalForm({ payload, goal, mode, onCancel, onEmit }) {
  const ui = payload.ui;
  const source = goal?.editor || emptyGoalEditor();
  const statusOptions = payload.primaryGoal.statusOptions.length ? payload.primaryGoal.statusOptions : ["active", "paused", "completed", "archived"];
  const visibilityOptions = payload.primaryGoal.visibilityOptions.length ? payload.primaryGoal.visibilityOptions : ["visible", "discreet", "hidden", "private"];

  function submit(event) {
    event.preventDefault();
    const draft = goalDraftFromFormData(new FormData(event.currentTarget));
    if (mode === "create") {
      onEmit(createGoalSubmitEvent(draft));
    } else {
      onEmit(editGoalSubmitEvent(goal.id, draft));
    }
  }

  return (
    <form className="hd-inspector-form" onSubmit={submit}>
      <input name="id" type="hidden" defaultValue={cleanText(source.id)} />

      <div className="hd-form-block">
        <label>
          {label(ui, "goal_field_title", "Title")}
          <input name="title" defaultValue={cleanText(source.title)} required />
        </label>
        <label>
          {label(ui, "goal_field_label", "Discreet label")}
          <input name="label" defaultValue={cleanText(source.label)} />
        </label>
        <div className="hd-form-row">
          <label>
            {label(ui, "goal_field_status", "Status")}
            <select name="status" defaultValue={cleanText(source.status, "active")}>
              {statusOptions.map((option) => <option key={option} value={option}>{label(ui, `goal_status_${option}`, option)}</option>)}
            </select>
          </label>
          <label>
            {label(ui, "goal_field_target", "Target date")}
            <input name="target" defaultValue={cleanText(source.target)} placeholder="YYYY-MM-DD" />
          </label>
        </div>
      </div>

      <div className="hd-form-block">
        <label>
          {label(ui, "goal_field_summary", "Summary")}
          <textarea name="summary" defaultValue={cleanText(source.summary)} rows="3" />
        </label>
        <label>
          {label(ui, "goal_field_alignment", "North Star alignment")}
          <textarea name="alignment" defaultValue={cleanText(source.alignment)} rows="3" />
        </label>
      </div>

      <div className="hd-form-block">
        <div className="hd-form-row">
          <label>
            {label(ui, "goal_field_ui_visibility", "UI visibility")}
            <select name="ui_visibility" defaultValue={cleanText(source.ui_visibility, "discreet")}>
              {visibilityOptions.map((option) => <option key={option} value={option}>{label(ui, `goal_visibility_${option}`, option)}</option>)}
            </select>
          </label>
          <label className="hd-check">
            <input name="include_in_agent_context" type="checkbox" defaultChecked={source.include_in_agent_context !== false} />
            {label(ui, "goal_field_agent_context", "Agent context")}
          </label>
        </div>
      </div>

      <details>
        <summary>{label(ui, "dashboard_goal_advanced_fields", "Advanced goal fields")}</summary>
        <label>{label(ui, "goal_field_start", "Start date")}<input name="start" defaultValue={cleanText(source.start)} placeholder="YYYY-MM-DD" /></label>
        <label>{label(ui, "goal_field_target_skills", "Target skills")}<textarea name="target_skills" defaultValue={linesText(source.target_skills)} rows="3" /></label>
        <label>{label(ui, "goal_field_success_criteria", "Success criteria")}<textarea name="success_criteria" defaultValue={linesText(source.success_criteria)} rows="3" /></label>
        <label>{label(ui, "goal_field_focus", "Focus")}<textarea name="focus" defaultValue={linesText(source.focus)} rows="3" /></label>
        <label>{label(ui, "goal_field_evidence_refs", "Evidence refs")}<textarea name="evidence_refs" defaultValue={linesText(source.evidence_refs)} rows="2" /></label>
        <label>{label(ui, "goal_field_task_refs", "Task refs")}<textarea name="task_refs" defaultValue={linesText(source.task_refs)} rows="2" /></label>
        <label>{label(ui, "goal_field_output_refs", "Output refs")}<textarea name="output_refs" defaultValue={linesText(source.output_refs)} rows="2" /></label>
        <label>{label(ui, "goal_field_notes", "Notes")}<textarea name="notes" defaultValue={cleanText(source.notes)} rows="3" /></label>
      </details>

      {mode === "create" ? (
        <label className="hd-check">
          <input name="set_as_primary" type="checkbox" defaultChecked={!payload.primaryGoal.isSet} />
          {label(ui, "dashboard_set_as_primary", "Set as primary")}
        </label>
      ) : null}

      <div className="hd-form-actions">
        <button className="hd-ghost" type="button" data-action="close-goal-form" onClick={onCancel}>{label(ui, "dashboard_goal_close_form", "Close")}</button>
        <button className="hd-primary" type="submit" data-action={mode === "create" ? "create-goal" : "save-goal"}>{label(ui, "goal_save", "Save goal")}</button>
      </div>
    </form>
  );
}

function GoalSkillAlignment({ payload, goalId, onEmit }) {
  const ui = payload.ui;
  const alignment = payload.skillAlignment.byGoal[goalId] || { confirmed: [], candidates: [] };
  const candidates = asArray(alignment.candidates);
  const confirmed = asArray(alignment.confirmed);
  const [selected, setSelected] = useState(() => new Set(candidates.map((link) => link.nodeId)));
  const [manualNodeId, setManualNodeId] = useState("");

  useEffect(() => {
    setSelected(new Set(candidates.map((link) => link.nodeId)));
  }, [candidates.map((link) => link.nodeId).join("|")]);

  const selectedLinks = candidates.filter((link) => selected.has(link.nodeId));
  return (
    <div className="hd-align-box">
      <div className="hd-align-actions">
        <button className="hd-ghost" type="button" data-action="goal-skill-rule-match" data-goal-id={goalId} onClick={() => onEmit(requestGoalSkillRuleMatchEvent(goalId))}>
          {label(ui, "skill_alignment_rule", "Rule match")}
        </button>
        <button className="hd-ghost" type="button" data-action="goal-skill-ai-match" data-goal-id={goalId} disabled={!payload.ai?.configured} onClick={() => onEmit(requestGoalSkillAiMatchEvent(goalId))}>
          {label(ui, "skill_alignment_ai", "AI match")}
        </button>
      </div>
      <span className="hd-section-label">{label(ui, "skill_alignment_confirmed", "Confirmed links")}</span>
      {confirmed.length ? (
        <ul className="hd-link-list">
          {confirmed.map((link) => <li key={link.nodeId}>{cleanText(link.label, link.nodeId)} <span>{link.source}</span></li>)}
        </ul>
      ) : (
        <p className="hd-empty">{label(ui, "skill_alignment_no_links", "No confirmed skill links yet.")}</p>
      )}
      <span className="hd-section-label">{label(ui, "skill_alignment_candidates", "Candidates")}</span>
      {candidates.length ? (
        <div className="hd-candidate-list">
          {candidates.map((link) => (
            <label key={link.nodeId} className="hd-candidate">
              <input
                type="checkbox"
                checked={selected.has(link.nodeId)}
                onChange={(event) => {
                  const next = new Set(selected);
                  if (event.currentTarget.checked) {
                    next.add(link.nodeId);
                  } else {
                    next.delete(link.nodeId);
                  }
                  setSelected(next);
                }}
              />
              <span><strong>{cleanText(link.label, link.nodeId)}</strong><small>{link.source}{link.score ? ` · ${link.score}` : ""}</small></span>
            </label>
          ))}
        </div>
      ) : (
        <p className="hd-empty">{label(ui, "skill_alignment_no_candidates", "Run rule match or AI match to get candidates.")}</p>
      )}
      <button className="hd-primary full" type="button" data-action="confirm-goal-skill-links" data-goal-id={goalId} disabled={!selectedLinks.length} onClick={() => onEmit(confirmGoalSkillLinksEvent(goalId, selectedLinks.map(linkPayload)))}>
        {label(ui, "skill_alignment_confirm", "Confirm links")}
      </button>
      <div className="hd-manual-row">
        <select value={manualNodeId} onChange={(event) => setManualNodeId(event.currentTarget.value)}>
          <option value="">{label(ui, "skill_alignment_manual_label", "Manual add")}</option>
          {payload.skillAlignment.skillOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
        </select>
        <button className="hd-ghost" type="button" data-action="manual-goal-skill-link" data-goal-id={goalId} disabled={!manualNodeId} onClick={() => onEmit(manualGoalSkillLinkEvent(goalId, manualNodeId))}>
          {label(ui, "skill_alignment_manual_add", "Add")}
        </button>
      </div>
    </div>
  );
}

function nodeRelations(payload, nodeId) {
  return payload.graph.edges
    .filter((edge) => edge.from === nodeId || edge.to === nodeId)
    .map((edge) => ({
      direction: edge.from === nodeId ? "to" : "from",
      relation: cleanText(edge.relation, edge.type),
      peer: edge.from === nodeId ? edge.to : edge.from,
      placeholder: edge.placeholder,
      suggested: edge.suggested,
    }));
}

function PlaceholderInspector({ payload, node, relations }) {
  const ui = payload.ui;
  if (!node.placeholder && node.implemented !== false && !node.suggested) {
    return null;
  }
  return (
    <div className="hd-placeholder-box">
      <span className="hd-section-label">{label(ui, "dashboard_inspector_owner_reserved", "Setup state")}</span>
      <p>
        {node.implemented === false
          ? label(ui, "dashboard_inspector_placeholder_hint", "This area is still a scaffold and does not have a backing record yet.")
          : label(ui, "dashboard_source_to_evidence_hint", "This node is still a suggested part of the dashboard graph.")}
      </p>
      {relations.length ? (
        <ul>
          {relations.slice(0, 4).map((relation) => (
            <li key={`${relation.direction}-${relation.relation}-${relation.peer}`}>
              <strong>{relation.relation}</strong>
              <span>{relation.direction} {relation.peer}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function InspectorActionButton({ action, onEmit, primary = false, readOnly = false }) {
  if (!canRenderGraphAction(action, readOnly)) {
    return null;
  }
  const event = graphActionEvent(action);
  if (!event) {
    return null;
  }
  return (
    <button
      className={primary ? "hd-primary" : "hd-ghost"}
      type="button"
      data-action={cleanText(action.event.action)}
      data-action-id={cleanText(action.id)}
      data-node-id={cleanText(action.nodeId)}
      onClick={() => onEmit(event)}
    >
      {cleanText(action.label, "Open")}
    </button>
  );
}

function NodeActionRow({ payload, node, onEmit, readOnly = false }) {
  const { primary, secondary } = nodeActionBundle(payload, node, readOnly);
  if (!primary && !secondary.length) {
    return null;
  }
  return (
    <div className="hd-action-row">
      <InspectorActionButton action={primary} onEmit={onEmit} primary readOnly={readOnly} />
      {secondary.slice(0, 3).map((action) => (
        <InspectorActionButton key={action.id || action.label} action={action} onEmit={onEmit} readOnly={readOnly} />
      ))}
    </div>
  );
}

function EmptyInspector({ payload, onEmit, onCreateGoal, readOnly = false }) {
  const ui = payload.ui;
  const missingNorthStar = !payload.northStar.isSet;
  const missingGoal = !payload.primaryGoal.isSet;

  return (
    <aside className="hd-inspector hd-inspector-empty">
      <header>
        <span className="hd-eyebrow">{label(ui, "dashboard_graph_eyebrow", "Canvas")}</span>
        <h3>{label(ui, "dashboard_inspector_setup_title", "Choose a real node or finish setup")}</h3>
      </header>
      <div className="hd-inspector-empty-body">
        <p className="hd-inspector-summary">
          {label(
            ui,
            "dashboard_inspector_setup_hint",
            "This graph is still mostly scaffolded. Start with North Star, then set a current goal.",
          )}
        </p>
        <div className="hd-action-row">
          {missingNorthStar ? (
            <button className="hd-primary" type="button" data-action="open-profile-context" onClick={() => onEmit(openProfileContextEvent())}>
              {label(ui, "north_star_edit_action", "Edit Profile Context")}
            </button>
          ) : null}
          {!readOnly && !missingNorthStar && missingGoal ? (
            <button className="hd-primary" type="button" data-action="open-goal-form" onClick={onCreateGoal}>
              {label(ui, "dashboard_add_active_goal", "Add goal")}
            </button>
          ) : null}
        </div>
      </div>
    </aside>
  );
}

function InspectorPanel({ payload, selectedNodeId, goalEditor, setGoalEditor, onEmit, readOnly = false }) {
  const ui = payload.ui;
  const nodesById = useMemo(() => new Map(payload.graph.nodes.map((node) => [node.id, node])), [payload]);
  const selectedNode = selectedNodeId ? nodesById.get(selectedNodeId) || null : null;
  const relations = selectedNode ? nodeRelations(payload, selectedNode.id) : [];

  if (!readOnly && goalEditor?.mode === "create") {
    return (
      <aside className="hd-inspector" data-section="goal-editor">
        <header><span className="hd-eyebrow">{label(ui, "dashboard_add_active_goal", "Add Active Goal")}</span><h3>{label(ui, "goal_create_title", "Create goal")}</h3></header>
        <GoalForm key="create-goal" payload={payload} goal={{ editor: emptyGoalEditor() }} mode="create" onCancel={() => setGoalEditor(null)} onEmit={onEmit} />
      </aside>
    );
  }

  const selectedGoalId = goalIdFromNode(selectedNode);
  const selectedGoal = goalById(payload, selectedGoalId);
  if (!readOnly && goalEditor?.mode === "edit" && selectedGoal) {
    return (
      <aside className="hd-inspector" data-section="goal-editor">
        <header><span className="hd-eyebrow">{label(ui, "dashboard_goal_edit_inline", "Edit goal")}</span><h3>{goalDisplay(selectedGoal, ui).title}</h3></header>
        <GoalForm key={`edit-goal:${selectedGoal.id}`} payload={payload} goal={selectedGoal} mode="edit" onCancel={() => setGoalEditor(null)} onEmit={onEmit} />
      </aside>
    );
  }

  if (!selectedNode) {
    return <EmptyInspector payload={payload} onEmit={onEmit} onCreateGoal={() => setGoalEditor({ mode: "create" })} readOnly={readOnly} />;
  }

  if (selectedNode.role === "direction" && selectedGoal) {
    const display = goalDisplay(selectedGoal, ui);
    return (
      <aside className="hd-inspector">
        <header>
          <span className="hd-eyebrow">{selectedGoal.isPrimary ? label(ui, "dashboard_primary_goal", "Primary goal") : label(ui, "dashboard_active_goal", "Active goal")}</span>
          <h3>{display.title}</h3>
        </header>
        <div className="hd-inspector-meta">
          {selectedNode.layer ? <span>{layerLabel(ui, selectedNode.layer)}</span> : null}
          {display.status ? <span>{label(ui, `goal_status_${display.status}`, display.status)}</span> : null}
          {display.target ? <span>{label(ui, "goal_strip_target", "Target")}: {display.target}</span> : null}
          {selectedGoal.locked ? <span>{label(ui, "goal_visibility_private", "Private")}</span> : null}
        </div>
        <PlaceholderInspector payload={payload} node={selectedNode} relations={relations} />
        <p className="hd-inspector-summary">{cleanText(selectedGoal.editor?.summary || display.summary, label(ui, "goal_module_caption", "A stage goal for this profile."))}</p>
        {!readOnly ? (
          <div className="hd-action-row">
            {!selectedGoal.locked ? <button className="hd-primary" type="button" data-action="open-goal-form" data-goal-id={selectedGoal.id} onClick={() => setGoalEditor({ mode: "edit", goalId: selectedGoal.id })}>{label(ui, "dashboard_goal_edit_inline", "Edit goal")}</button> : null}
            {!selectedGoal.isPrimary ? <button className="hd-ghost" type="button" data-action="set-primary-goal" data-goal-id={selectedGoal.id} onClick={() => onEmit(setPrimaryGoalEvent(selectedGoal.id))}>{label(ui, "dashboard_set_primary", "Set primary")}</button> : null}
            <button className="hd-ghost danger" type="button" data-action="archive-goal" data-goal-id={selectedGoal.id} onClick={() => onEmit(archiveGoalEvent(selectedGoal.id))}>{label(ui, "dashboard_archive_goal", "Archive")}</button>
          </div>
        ) : null}
        {!readOnly && !selectedGoal.locked ? <GoalSkillAlignment payload={payload} goalId={selectedGoal.id} onEmit={onEmit} /> : null}
      </aside>
    );
  }

  const hasNodeAction = Boolean(nodeActionBundle(payload, selectedNode, readOnly).primary);

  return (
    <aside className="hd-inspector">
      <header>
        <span className="hd-eyebrow">{translatedNodeType(ui, selectedNode.type)}</span>
        <h3>{selectedNode.label}</h3>
      </header>
      <div className="hd-inspector-meta">
        {selectedNode.layer ? <span>{layerLabel(ui, selectedNode.layer)}</span> : null}
        {selectedNode.implemented === false ? <span>{label(ui, "dashboard_placeholder_metric", "Planned")}</span> : null}
        {selectedNode.metric ? <span>{selectedNode.metric}</span> : null}
        {selectedNode.status ? <span>{selectedNode.status}</span> : null}
      </div>
      <PlaceholderInspector payload={payload} node={selectedNode} relations={relations} />
      <p className="hd-inspector-summary">
        {selectedNode.summary
          ? selectedNode.summary
          : selectedNode.suggested || selectedNode.placeholder
          ? label(ui, "skill_alignment_suggested", "suggested")
          : label(ui, "dashboard_inspector_node_hint", "Open the owner page for details.")}
      </p>
      <NodeActionRow payload={payload} node={selectedNode} onEmit={onEmit} readOnly={readOnly} />
      {!hasNodeAction ? (
        <div className="hd-action-row">
          {selectedNode.ownerPath && selectedNode.ownerPath !== "profile_context" && selectedNode.implemented !== false ? (
            <button className="hd-primary" type="button" data-action="navigate" data-target={selectedNode.ownerPath} onClick={() => onEmit(navigationEvent(selectedNode.ownerPath))}>{label(ui, "dashboard_open_section", "Open")}</button>
          ) : null}
          {selectedNode.ownerPath === "profile_context" && selectedNode.implemented !== false ? (
            <button className="hd-primary" type="button" data-action="open-profile-context" onClick={() => onEmit(openProfileContextEvent())}>{label(ui, "north_star_edit_action", "Edit Profile Context")}</button>
          ) : null}
        </div>
      ) : null}
      {selectedNode.role === "star" && selectedNode.implemented !== false ? (
        <button className="hd-ghost full" type="button" data-action="navigate" data-target="pages/2_Gap_Analysis.py" onClick={() => onEmit(navigationEvent("pages/2_Gap_Analysis.py"))}>{label(ui, "quick_gap", "Gap Analysis")}</button>
      ) : null}
    </aside>
  );
}

function SkillProgressCard({ payload, onEmit, className = "" }) {
  const ui = payload.ui;
  const counts = payload.charts.skills.counts || {};
  const totalCount = Math.max(0, Number(payload.charts.skills.total) || 0);
  const countSum = SKILL_STATUS_META.reduce((sum, item) => sum + (Number(counts[item.key]) || 0), 0);
  const total = totalCount || countSum;
  const lit = Math.max(0, Number(payload.charts.skills.lit) || 0);
  const litRate = total ? (Number(payload.charts.skills.litRate) || (lit / total)) : 0;
  const segments = skillSegments(counts, total);
  const summaryMessage = total
    ? `${label(ui, "dashboard_skill_progress_caption", "solid + expert lit rate")} · ${formatPercent(litRate)}`
    : label(ui, "dashboard_skill_progress_empty", "No skill tree data yet.");
  const cardClassName = ["hd-summary-card", "hd-skill-card", className].filter(Boolean).join(" ");
  const skillMapLink = quickLink(payload, "skill_map", "pages/1_Skill_Tree.py", label(ui, "quick_skill_map", "Skill Map"));

  return (
    <article className={cardClassName}>
      <div className="hd-summary-head">
        <div>
          <span className="hd-eyebrow">{label(ui, "dashboard_skill_progress_title", "Skill Progress")}</span>
          <h4>{label(ui, "dashboard_metric_skill_lit", "Skill lit")}</h4>
          <p className="hd-skill-head-copy">{summaryMessage}</p>
          {!total && onEmit ? (
            <button
              className="hd-ghost hd-skill-empty-cta"
              type="button"
              data-action="navigate"
              data-target={skillMapLink.path}
              onClick={() => onEmit(navigationEvent(skillMapLink.path))}
            >
              {label(ui, "dashboard_skill_empty_cta", "Open Skill Map")}
            </button>
          ) : null}
        </div>
        <span className="hd-summary-chip">{label(ui, "dashboard_skill_lit_rate", "Lit rate")}: {formatPercent(litRate)}</span>
      </div>

      <div className="hd-skill-meter">
        <div className="hd-skill-ring">
          <svg viewBox={`0 0 ${SKILL_RING_SIZE} ${SKILL_RING_SIZE}`} aria-hidden="true">
            <circle
              cx={SKILL_RING_SIZE / 2}
              cy={SKILL_RING_SIZE / 2}
              r={SKILL_RING_RADIUS}
              fill="none"
              stroke="rgba(216, 225, 220, .9)"
              strokeWidth={SKILL_RING_STROKE}
            />
            {segments.map((segment) => (
              segment.count ? (
                <circle
                  key={segment.key}
                  cx={SKILL_RING_SIZE / 2}
                  cy={SKILL_RING_SIZE / 2}
                  r={SKILL_RING_RADIUS}
                  fill="none"
                  stroke={segment.color}
                  strokeWidth={SKILL_RING_STROKE}
                  strokeLinecap="round"
                  strokeDasharray={segment.dasharray}
                  strokeDashoffset={segment.dashoffset}
                  transform={`rotate(-90 ${SKILL_RING_SIZE / 2} ${SKILL_RING_SIZE / 2})`}
                />
              ) : null
            ))}
          </svg>
          <div className="hd-skill-ring-center">
            <strong>{lit}/{total}</strong>
            <span>{label(ui, "dashboard_metric_skill_lit", "Skill lit")}</span>
          </div>
        </div>
      </div>
    </article>
  );
}

function HealthSummaryPanel({ payload, className = "" }) {
  const ui = payload.ui;
  const health = payload.charts.health || {};
  const contextReady = Boolean(payload.health?.context_ready);
  const panelClassName = ["hd-side-panel", "hd-health-panel", className].filter(Boolean).join(" ");

  return (
    <section className={panelClassName}>
      <header>
        <span className="hd-eyebrow">{label(ui, "dashboard_health_title", "Health")}</span>
        <strong>{label(ui, "dashboard_health_title", "Health")}</strong>
      </header>
      <div className="hd-health-grid">
        <div className="hd-health-chip">
          <span>{label(ui, "dashboard_health_errors", "Errors")}</span>
          <strong>{Number(health.error) || 0}</strong>
        </div>
        <div className="hd-health-chip">
          <span>{label(ui, "dashboard_health_warnings", "Warnings")}</span>
          <strong>{Number(health.warning) || 0}</strong>
        </div>
        <div className="hd-health-chip">
          <span>{label(ui, "dashboard_health_info", "Info")}</span>
          <strong>{Number(health.info) || 0}</strong>
        </div>
        <div className="hd-health-chip">
          <span>{label(ui, "dashboard_health_context_ready", "Context ready")}</span>
          <strong>{contextReady ? label(ui, "dashboard_yes", "Yes") : label(ui, "dashboard_no", "No")}</strong>
        </div>
      </div>
    </section>
  );
}

function ActionQueue({ payload, onEmit, className = "" }) {
  const ui = payload.ui;
  const queueClassName = ["hd-side-panel", "hd-action-queue", className].filter(Boolean).join(" ");
  return (
    <section className={queueClassName}>
      <header>
        <span className="hd-eyebrow">{label(ui, "dashboard_action_queue_title", "Action queue")}</span>
        <strong>{label(ui, "dashboard_action_queue_title", "Action queue")}</strong>
      </header>
      <div className="hd-action-list">
        {actionQueueItems(payload).map((item) => (
          <button
            key={item.id}
            className={`hd-action-card ${item.tone || ""}`}
            type="button"
            data-action="navigate"
            data-dashboard-action={`queue:${item.id}`}
            data-target={item.path}
            onClick={() => onEmit(navigationEvent(item.path))}
          >
            <span>{item.eyebrow}</span>
            <strong>{item.title}</strong>
            <small>{item.detail}</small>
            <small className="hd-action-why">{item.why}</small>
            <small className="hd-action-filter">{item.filter}</small>
            <em>{item.count}</em>
          </button>
        ))}
      </div>
    </section>
  );
}

function Workbench({ payload, onEmit, readOnly = false, showActionQueue = true }) {
  const ui = payload.ui;
  const metrics = dashboardMetrics(payload);
  const urgentHealth = metrics.healthAlerts > 0;
  const layoutClassName = showActionQueue ? "hd-workbench-layout" : "hd-workbench-layout no-queue";

  return (
    <section className="hd-workbench">
      <header className="hd-workbench-header">
        <div>
          <span className="hd-eyebrow">{label(ui, "dashboard_workbench_title", "Workbench")}</span>
          <h3>{label(ui, "dashboard_workbench_caption", "Today's signals, capture inbox, and quick actions.")}</h3>
        </div>
      </header>

      <div className={layoutClassName}>
        {showActionQueue ? <ActionQueue payload={payload} onEmit={onEmit} className="hd-workbench-queue" /> : null}

        <SkillProgressCard payload={payload} onEmit={onEmit} className="hd-workbench-skill" />

        <HealthSummaryPanel payload={payload} className={`hd-workbench-health ${urgentHealth ? "urgent" : "secondary"}`} />
      </div>
    </section>
  );
}

function Dashboard({ args }) {
  const payload = useMemo(() => normalizePayload(args.payload || {}), [args]);
  const requestedNodeId = useMemo(() => initialDashboardNodeId(), []);
  const [selectedNodeId, setSelectedNodeId] = useState(() => requestedNodeId);
  const [goalEditor, setGoalEditor] = useState(null);
  const [viewMode, setViewMode] = useState(() => initialDashboardViewMode(args));
  const canvasEmbed = useMemo(() => (!args.standalone ? dashboardCanvasEmbed(payload) : null), [args.standalone, payload]);
  const readOnlyCanvas = Boolean(args.standalone);
  const useDailyGraphHero = !args.standalone && !args.embed;

  useLayoutEffect(() => {
    window.setTimeout(() => setFrameHeight(), 0);
    if (!goalEditor?.mode || readOnlyCanvas) {
      return undefined;
    }
    const frame = window.requestAnimationFrame(() => {
      const editor = document.querySelector('[data-section="goal-editor"]');
      if (!editor) {
        return;
      }
      editor.scrollIntoView({ block: "start", behavior: "smooth" });
      const titleInput = editor.querySelector('input[name="title"]');
      if (titleInput instanceof HTMLElement) {
        titleInput.focus({ preventScroll: true });
      }
    });
    return () => window.cancelAnimationFrame(frame);
  }, [goalEditor?.mode, goalEditor?.goalId, readOnlyCanvas]);

  useEffect(() => {
    const availableIds = new Set(payload.graph.nodes.map((node) => node.id));
    if (requestedNodeId && !availableIds.size && selectedNodeId === requestedNodeId) {
      window.setTimeout(() => setFrameHeight(), 0);
      return;
    }
    const nextPreferred = preferredNode(payload);
    const requestedAvailable = requestedNodeId && availableIds.has(requestedNodeId);
    const nextId = availableIds.has(selectedNodeId)
      ? selectedNodeId
      : requestedAvailable
      ? requestedNodeId
      : cleanText(nextPreferred?.id);
    if (nextId !== selectedNodeId) {
      setSelectedNodeId(nextId);
    }
    window.setTimeout(() => setFrameHeight(), 0);
  }, [payload, requestedNodeId, selectedNodeId]);

  function emit(event) {
    if (args.standalone) {
      const action = cleanText(event?.action);
      const path = cleanText(event?.payload?.path);
      if (action === "navigate" && path) {
        const target = standaloneTargetUrl(path, args.streamlitBase);
        if (args.embed && window.top && window.top !== window) {
          window.top.location.href = target;
        } else {
          window.location.href = target;
        }
        return;
      }
      if (action === "set_north_star_display_open_profile_context") {
        const target = standaloneTargetUrl("", args.streamlitBase) || cleanText(args.streamlitBase, "http://127.0.0.1:8503");
        if (args.embed && window.top && window.top !== window) {
          window.top.location.href = target;
        } else {
          window.location.href = target;
        }
        return;
      }
      if (!canEmitInReadOnly(action)) {
        return;
      }
      return;
    }
    setComponentValue(event);
    window.setTimeout(() => setFrameHeight(), 0);
  }

  function selectGoal(goalId) {
    const node = payload.graph.nodes.find((item) => item.role === "direction" && item.recordId === goalId);
    if (node) {
      setSelectedNodeId(node.id);
    }
    if (!readOnlyCanvas && useDailyGraphHero && goalById(payload, goalId)) {
      setGoalEditor({ mode: "edit", goalId });
    } else {
      setGoalEditor(null);
    }
  }

  const handleSelectNode = (nodeId) => {
    setSelectedNodeId(nodeId);
    setGoalEditor(null);
  };

  const selectedGoalId = useMemo(() => {
    const node = payload.graph.nodes.find((item) => item.id === selectedNodeId && item.role === "direction");
    return node ? node.recordId : "";
  }, [payload, selectedNodeId]);

  const inlineGoal = goalEditor?.mode === "edit" ? goalById(payload, goalEditor.goalId) : null;
  const inlineGoalEditor = !readOnlyCanvas && useDailyGraphHero && goalEditor?.mode && (
    goalEditor.mode === "create" || inlineGoal
  ) ? (
    <section className="hd-inline-goal-editor" data-section="goal-editor">
      <header>
        <div>
          <span className="hd-eyebrow">
            {goalEditor.mode === "create"
              ? label(payload.ui, "dashboard_add_active_goal", "Add Active Goal")
              : label(payload.ui, "dashboard_goal_edit_inline", "Edit goal")}
          </span>
          <h3>
            {goalEditor.mode === "create"
              ? label(payload.ui, "goal_create_title", "Create goal")
              : goalDisplay(inlineGoal, payload.ui).title}
          </h3>
        </div>
        <button className="hd-ghost" type="button" data-action="close-goal-form" onClick={() => setGoalEditor(null)}>
          {label(payload.ui, "cancel", "Cancel")}
        </button>
      </header>
      <GoalForm
        key={goalEditor.mode === "create" ? "create-goal" : `edit-goal:${inlineGoal?.id || ""}`}
        payload={payload}
        goal={goalEditor.mode === "create" ? { editor: emptyGoalEditor() } : inlineGoal}
        mode={goalEditor.mode}
        onCancel={() => setGoalEditor(null)}
        onEmit={emit}
      />
    </section>
  ) : null;
  const canvasSurface = useDailyGraphHero ? (
    <GraphHeroPanel
      payload={payload}
      embed={canvasEmbed}
      selectedNodeId={selectedNodeId}
      onSelectNode={handleSelectNode}
      onEmit={emit}
    />
  ) : (
    <div className="hd-canvas-workbench">
      <ContextCanvas
        payload={payload}
        selectedNodeId={selectedNodeId}
        onSelectNode={handleSelectNode}
        onEmit={emit}
        onCreateGoal={() => setGoalEditor({ mode: "create" })}
        viewMode={viewMode}
        setViewMode={setViewMode}
        readOnly={readOnlyCanvas}
      />
      <InspectorPanel
        payload={payload}
        selectedNodeId={selectedNodeId}
        goalEditor={goalEditor}
        setGoalEditor={setGoalEditor}
        onEmit={emit}
        readOnly={readOnlyCanvas}
      />
    </div>
  );

  return (
    <main className={args.embed ? "hd-shell hd-shell-embed" : "hd-shell"}>
      {args.standalone && !args.embed ? (
        <section className="hd-standalone-top">
          <div>
            <span className="hd-eyebrow">{label(payload.ui, "dashboard_graph_eyebrow", "Context")}</span>
            <h1>Dashboard Canvas</h1>
            <p>
              {args.loading
                ? label(payload.ui, "dashboard_graph_loading", "Loading graph...")
                : args.error
                ? args.error
                : `${label(payload.ui, "profile", "Profile")}: ${payload.profile}`}
            </p>
          </div>
          <a href={cleanText(args.streamlitBase, "http://127.0.0.1:8503")} data-action="open-8503">
            {label(payload.ui, "dashboard_open_8503", "Open 8503")}
          </a>
        </section>
      ) : null}
      {args.embed ? (
        <div className="hd-canvas-workbench hd-canvas-workbench-embed">
          <ContextCanvas
            payload={payload}
            selectedNodeId={selectedNodeId}
            onSelectNode={handleSelectNode}
            onEmit={emit}
            onCreateGoal={() => setGoalEditor({ mode: "create" })}
            viewMode={viewMode}
            setViewMode={setViewMode}
            readOnly={readOnlyCanvas}
          />
          <InspectorPanel
            payload={payload}
            selectedNodeId={selectedNodeId}
            goalEditor={goalEditor}
            setGoalEditor={setGoalEditor}
            onEmit={emit}
            readOnly={readOnlyCanvas}
          />
        </div>
      ) : (
        <>
      <ContextHeader
        payload={payload}
        onEmit={emit}
        onCreateGoal={() => setGoalEditor({ mode: "create" })}
        onSelectGoal={selectGoal}
        onEditGoal={(goalId) => setGoalEditor({ mode: "edit", goalId })}
        canEditGoals={!readOnlyCanvas}
        canSelectGoals={!readOnlyCanvas}
        showToday={!useDailyGraphHero}
        selectedGoalId={selectedGoalId}
      />
      {inlineGoalEditor}

      {canvasSurface}
      {useDailyGraphHero ? null : <Workbench payload={payload} onEmit={emit} readOnly={readOnlyCanvas} showActionQueue={!useDailyGraphHero} />}
        </>
      )}
    </main>
  );
}

function App() {
  const standalone = standaloneConfig();
  const [args, setArgs] = useState({
    payload: standalone?.payload || {},
    height: 900,
    standalone: Boolean(standalone),
    embed: Boolean(standalone?.embed),
    loading: Boolean(standalone && !standalone.payload),
    error: "",
    streamlitBase: cleanText(standalone?.streamlitBase, "http://127.0.0.1:8503"),
  });
  useEffect(() => {
    if (!standalone) {
      initStreamlitBridge(setArgs);
      return undefined;
    }
    if (standalone.payload) {
      return undefined;
    }
    let cancelled = false;
    const profile = cleanText(standalone.profile);
    const endpoint = cleanText(standalone.payloadUrl, "/api/dashboard/payload");
    const url = `${endpoint}${endpoint.includes("?") ? "&" : "?"}profile=${encodeURIComponent(profile)}`;
    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (cancelled) {
          return;
        }
        if (!data?.ok) {
          throw new Error(cleanText(data?.detail, "Failed to load dashboard payload"));
        }
        setArgs((current) => ({ ...current, payload: data.payload || {}, loading: false, error: "" }));
      })
      .catch((error) => {
        if (!cancelled) {
          setArgs((current) => ({ ...current, loading: false, error: error?.message || "Failed to load dashboard payload" }));
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);
  return <Dashboard args={args} />;
}

const root = createRoot(document.getElementById("root"));
root.render(<App />);
