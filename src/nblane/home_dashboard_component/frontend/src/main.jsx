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
import * as THREE from "three";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { GalaxyScene } from "./galaxy_scene.js";

import "./style.css";
import {
  asArray,
  asObject,
  cleanText,
  goalDisplay,
  goalDraftFromFormData,
  hiddenArchivedSubtreeIds,
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
import { ResumeIngestDrawer } from "./resume_ingest.jsx";
import { ProfileContextDrawer } from "./profile_context.jsx";
import { HdDrawer } from "./drawer.jsx";

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

const GRAPH_3D_MIN_HEIGHT = 560;

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

// Synthetic catch-all goal: projects with no goal_refs are adopted into this
// "Other" hub so they orbit a labelled sun like any real goal, instead of being
// flung onto a huge near-empty ring around the North Star.
const OTHER_GOAL_ID = "__other_goal__";

const ROLE_COLORS = {
  trunk: "#a98b6b",
  direction: "#3f8f7c",
  branch: "#9b7e5e",
  leaf: "#79b889",
  fruit: "#e09a6e",
  star: "#9bbf86",
  constellation: "#d8b4d0",
  sand: "#a9cdd8",
};

const SKILL_CATEGORY_COLORS = [
  "#7fa8e0",
  "#6cc3b4",
  "#e3bd6a",
  "#dd8fb0",
  "#92cf7e",
  "#b59ae0",
  "#73b8d8",
  "#e09a78",
  "#bcce72",
  "#84cbd8",
];

// Star brightness by skill status — the dome dims for locked, blazes for expert.
// Locked sits at the visibility floor so the dome's shape always reads as faint
// points, while solid/expert push past the bloom threshold and glow.
const STAR_STATUS_EMISSIVE = {
  locked: 0.2,
  learning: 0.28,
  solid: 0.48,
  expert: 0.78,
};

// Tree skeleton dimensions (world units, y is up).
const TREE_HEIGHT = 92;
const STAR_DOME_CENTER_Y = 96;
const STAR_DOME_RADIUS = 58;
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

// Vertical tiers — the metaphor stacks bottom-to-top so the silhouette reads as
// a tree growing upward: ground haze (sand) → trunk (north_star) low → goals
// branch up-and-out → projects fork higher → leaves at the crown → fruit hangs
// below its leaf → star dome floats above the canopy.
const GROUND_Y = 0; // sand sits on the ground plane
const TRUNK_BASE_Y = 0; // trunk rises from the ground
const TRUNK_TOP_Y = 52; // north_star crowns a tall, present trunk
const DIRECTION_Y = 64; // goals branch up-and-out from the trunk top
const BRANCH_RISE = 16; // projects lift above their goal
const LEAF_RISE = 13; // tasks / outputs at the branch tips (crown)
const FRUIT_DROP = 12; // evidence hangs below its leaf
const DOME_BASE_Y = 128; // star dome floats clearly above the canopy
const STAR_EMISSIVE_FLOOR = 0.2; // locked stars stay faintly visible (below bloom)

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
  let rendered = false;
  window.addEventListener("message", (event) => {
    if (event.data?.type !== RENDER) {
      return;
    }
    rendered = true;
    onRender(event.data?.args || {});
  });
  // Re-announce READY a few times with backoff. Streamlit only sends the first
  // RENDER (which carries the payload) in response to our READY ping; if that
  // ping is dropped during a parent rerun — e.g. the st.rerun() right after
  // login — the component never receives a payload and paints blank until the
  // user navigates away and back. Repeating READY until the first RENDER
  // arrives makes that handshake self-heal instead of requiring a manual round
  // trip. Pings stop as soon as any RENDER lands.
  const announce = (attempt) => {
    if (rendered) {
      return;
    }
    sendBack(READY, { apiVersion: 1 });
    window.setTimeout(() => setFrameHeight(), 0);
    if (attempt < 6) {
      window.setTimeout(() => announce(attempt + 1), 150 * (attempt + 1));
    }
  };
  announce(0);
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
  // No configured base means same-origin: production sits behind a reverse
  // proxy where "/" already resolves to the Streamlit app, and 8503 is a
  // local-dev-only port that never exists in production.
  const base = cleanText(streamlitBase).replace(/\/+$/, "");
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
  return asObject(payload?.canvasEmbed).standaloneUrl ? asObject(payload.canvasEmbed) : null;
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
  const allGoal = asArray(payload.allGoals).find((goal) => goal.id === goalId);
  if (allGoal) {
    return allGoal;
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

function DeltaChip({ value, kindLabel = "" }) {
  if (!Number.isFinite(value) || value === 0) return null;
  const sign = value > 0 ? "+" : "-";
  const tone = value > 0 ? "up" : "down";
  return (
    <span
      className={`hd-delta-chip ${tone}`}
      aria-label={kindLabel ? `${kindLabel} ${sign}${Math.abs(value)}` : undefined}
    >
      {sign}{Math.abs(value)}
    </span>
  );
}

function Sparkline({ series = [], width = 60, height = 18, tone = "" }) {
  const points = (series || []).filter((n) => Number.isFinite(n));
  if (points.length < 2) return null;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const step = width / (points.length - 1);
  const coords = points
    .map((value, idx) => {
      const x = idx * step;
      const y = height - ((value - min) / range) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const stroke =
    tone === "down"
      ? "rgba(255, 107, 107, .82)"
      : tone === "up"
        ? "rgba(94, 224, 160, .92)"
        : "rgba(122, 162, 255, .85)";
  return (
    <svg
      className="hd-sparkline"
      viewBox={`0 0 ${width} ${height}`}
      aria-hidden="true"
    >
      <polyline
        points={coords}
        fill="none"
        stroke={stroke}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function sortGoalChips(goals) {
  // Most-urgent first: overdue > due-soon > active-with-progress > stalled > rest.
  const score = (g) => {
    const days = Number.isFinite(g.daysToTarget) ? g.daysToTarget : null;
    if (days !== null && days < 0) return -1000 + days; // overdue, most-negative first
    if (days !== null && days <= 30) return -500 + days;
    if (g.stalled) return 500;
    if (Number.isFinite(g.progress) && g.progress !== null) return 100 - Math.round(g.progress * 100);
    return 1000;
  };
  return [...goals].sort((a, b) => score(a) - score(b));
}

function goalDueLabel(goal, ui) {
  const days = Number.isFinite(goal.daysToTarget) ? goal.daysToTarget : null;
  if (days === null) return null;
  if (days < 0) {
    const abs = Math.abs(days);
    return {
      tone: "overdue",
      short: `${abs}${label(ui, "dashboard_goal_overdue_short", "d overdue")}`,
      full: `${label(ui, "dashboard_goal_overdue", "Overdue")} ${abs}${label(ui, "dashboard_goal_days", "d")}`,
    };
  }
  if (days === 0) {
    return {
      tone: "due-soon",
      short: label(ui, "dashboard_goal_due_today", "today"),
      full: label(ui, "dashboard_goal_due_today", "Due today"),
    };
  }
  if (days <= 30) {
    return {
      tone: "due-soon",
      short: `${days}${label(ui, "dashboard_goal_days", "d")}`,
      full: `${label(ui, "dashboard_goal_due_in", "Due in")} ${days}${label(ui, "dashboard_goal_days", "d")}`,
    };
  }
  return {
    tone: "far",
    short: `${days}${label(ui, "dashboard_goal_days", "d")}`,
    full: `${label(ui, "dashboard_goal_due_in", "Due in")} ${days}${label(ui, "dashboard_goal_days", "d")}`,
  };
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

function ContextHeader({ payload, onEmit, onCreateGoal, onSelectGoal, onEditGoal, onOpenResumeIngest, onOpenProfileContext, canEditGoals = true, canSelectGoals = true, showToday = true, selectedGoalId = "" }) {
  const ui = payload.ui;
  const northStar = payload.northStar;
  const primary = goalDisplay(payload.primaryGoal, ui);
  const primaryId = primaryGoalId(payload);
  const activeGoals = asArray(payload.activeGoals);
  const allGoals = asArray(payload.allGoals);
  const RAIL_ARCHIVED_KEY = "nblane.context.goalRail.showArchived";
  const [showArchivedRail, setShowArchivedRail] = useState(() => {
    try {
      return window.localStorage.getItem(RAIL_ARCHIVED_KEY) === "1";
    } catch (e) {
      return false;
    }
  });
  const toggleArchivedRail = () => {
    setShowArchivedRail((current) => {
      const next = !current;
      try {
        window.localStorage.setItem(RAIL_ARCHIVED_KEY, next ? "1" : "0");
      } catch (e) {
        // ignore — privacy mode blocks storage
      }
      return next;
    });
  };
  const isExtinguishedGoal = (goal) => {
    const status = String(goal?.status || "").toLowerCase();
    return status === "archived" || status === "paused" || status === "completed";
  };
  const railSource = allGoals.length ? allGoals : activeGoals;
  const secondaryActive = railSource.filter(
    (goal) => !goal.isPrimary && String(goal.status || "active").toLowerCase() === "active",
  );
  const secondaryExtinguished = railSource.filter(
    (goal) => !goal.isPrimary && isExtinguishedGoal(goal),
  );
  const extinguishedCount = secondaryExtinguished.length;
  const secondaryGoals = showArchivedRail
    ? [...secondaryActive, ...secondaryExtinguished]
    : secondaryActive;
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
            {extinguishedCount > 0 ? (
              <button
                type="button"
                className={`hd-context-archived-toggle${showArchivedRail ? " on" : ""}`}
                onClick={toggleArchivedRail}
                aria-pressed={showArchivedRail}
                title={label(ui, "dashboard_show_archived_goals", "Show archived / paused goals (extinguished stars)")}
              >
                {showArchivedRail ? "◐" : "◯"} {extinguishedCount}
              </button>
            ) : null}
          </div>
          <div className="hd-goal-rail">
            {secondaryGoals.length ? sortGoalChips(secondaryGoals).map((goal) => {
              const display = goalDisplay(goal, ui);
              const isSelected = Boolean(goal.id) && goal.id === selectedGoalId;
              const extinguished = isExtinguishedGoal(goal);
              const className = `hd-goal-pill${isSelected ? " selected" : ""}${goal.stalled ? " stalled" : ""}${extinguished ? " extinguished" : ""}`;
              const progressPct = Number.isFinite(goal.progress) && goal.progress !== null
                ? Math.round(Math.max(0, Math.min(1, goal.progress)) * 100)
                : null;
              const due = goalDueLabel(goal, ui);
              const titleAttr = [
                display.title,
                label(ui, `goal_status_${display.status}`, display.status || "active"),
                progressPct !== null ? `${progressPct}%` : null,
                due ? due.full : null,
              ].filter(Boolean).join(" · ");
              const inner = (
                <>
                  <span className="hd-goal-pill-dot" />
                  <strong>{display.title}</strong>
                  {progressPct !== null ? (
                    <span className="hd-goal-pill-progress" aria-label={`${progressPct}%`}>
                      <i style={{ width: `${progressPct}%` }} />
                    </span>
                  ) : null}
                  {due ? <span className={`hd-goal-pill-due ${due.tone}`}>{due.short}</span> : null}
                </>
              );
              return canSelectGoals ? (
                <button
                  key={goal.id || display.title}
                  className={className}
                  type="button"
                  data-action="select-goal"
                  data-goal-id={goal.id}
                  aria-pressed={isSelected}
                  title={titleAttr}
                  onClick={() => onSelectGoal(goal.id)}
                >
                  {inner}
                </button>
              ) : (
                <span
                  key={goal.id || display.title}
                  className={`${className} static`}
                  data-action="goal-context"
                  data-goal-id={goal.id}
                  title={titleAttr}
                >
                  {inner}
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
        {onOpenResumeIngest ? (
          <button className="hd-ghost full" type="button" data-action="open-resume-ingest" onClick={onOpenResumeIngest}>
            {label(ui, "dashboard_open_resume_ingest", "Import resume")}
          </button>
        ) : null}
        <button
          className="hd-ghost full"
          type="button"
          data-action="open-profile-context"
          onClick={() => {
            if (onOpenProfileContext) {
              onOpenProfileContext();
              return;
            }
            onEmit(openProfileContextEvent());
          }}
        >
          {label(ui, "dashboard_open_profile_context", label(ui, "north_star_edit_action", "Edit Profile Context"))}
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

// Ids to hide when the "show archived / paused goals" toggle is OFF: an
// extinguished goal PLUS its whole subtree (see hiddenArchivedSubtreeIds in
// payload.js — kept there so it is unit-testable without importing this entry).
function graphNodesForView(payload, hiddenLayers, viewMode, options = {}) {
  const { showArchived = false } = options;
  const hidden = hiddenArchivedSubtreeIds(payload, showArchived);
  const baseNodes = payload.graph.nodes
    .filter((node) => !hiddenLayers.has(node.layer))
    .filter((node) => !hidden.has(node.id));
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

function flowData(payload, hiddenLayers, viewMode, options = {}) {
  const visibleNodes = graphNodesForView(payload, hiddenLayers, viewMode, options);
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

function AttentionSummary({ payload, selectedNodeId = "", onSelectNode }) {
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
            className={[
              "hd-attention-chip",
              item.severity || "",
              selectedNodeId === item.id ? "selected" : "",
            ].filter(Boolean).join(" ")}
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

function skillCategoryColor(node) {
  const category = cleanText(node.metric || node.meta?.category || node.recordId || node.id, "general");
  const index = Math.floor(hashUnit(category) * SKILL_CATEGORY_COLORS.length) % SKILL_CATEGORY_COLORS.length;
  return SKILL_CATEGORY_COLORS[index] || ROLE_COLORS.star;
}

function nodeVisualWeight(node) {
  const status = cleanText(node.status).toLowerCase();
  const placeholder = Boolean(node.placeholder || node.implemented === false);
  if (placeholder) {
    return {
      radius: 0.72,
      opacity: node.role === "fruit" ? 0.38 : 0.48,
      emissive: 0.55,
    };
  }
  if (status === "archived") {
    return { radius: 0.78, opacity: 0.48, emissive: 0.5 };
  }
  if (status === "done" || status === "completed") {
    return { radius: 0.88, opacity: 0.66, emissive: 0.66 };
  }
  if (status === "draft" || status === "planned") {
    return { radius: 0.82, opacity: 0.56, emissive: 0.58 };
  }
  return { radius: 1, opacity: 0.92, emissive: 1 };
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

function outgoingAnchorPosition(node, edgesBySource, allowed, positions, nodesById) {
  const outgoing = edgesBySource.get(node.id) || [];
  for (const relation of allowed) {
    const match = outgoing.find((edge) => (edge.relation || edge.type) === relation && nodesById.has(edge.to) && positions.has(edge.to));
    if (match) {
      return positions.get(match.to);
    }
  }
  const any = outgoing.find((edge) => nodesById.has(edge.to) && positions.has(edge.to));
  return any ? positions.get(any.to) : null;
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
  const edgesBySource = new Map();
  edges.forEach((edge) => {
    if (!edgesByTarget.has(edge.to)) {
      edgesByTarget.set(edge.to, []);
    }
    edgesByTarget.get(edge.to).push(edge);
    if (!edgesBySource.has(edge.from)) {
      edgesBySource.set(edge.from, []);
    }
    edgesBySource.get(edge.from).push(edge);
  });

  const byRole = (role) => nodes.filter((node) => node.role === role);

  // 1. Trunk — vertical spine rising from the ground to the canopy.
  const trunks = byRole("trunk");
  trunks.forEach((node) => {
    positions.set(node.id, { x: 0, y: TRUNK_TOP_Y, z: 0 });
  });
  const trunkAnchor = () => ({ x: 0, y: DIRECTION_Y, z: 0 });

  // 2. Direction (goals) — fan out around the trunk with golden-angle spacing so
  // even 1-3 goals separate visibly. Each goal carries an angular budget for its
  // child branches to spread within.
  const directions = byRole("direction");
  const dirCount = Math.max(1, directions.length);
  const directionPos = new Map();
  // Even angular spacing around the trunk keeps the canopy balanced (golden-angle
  // bunches goals to one side for small counts). A half-step phase offset avoids a
  // goal sitting dead-center-front.
  const dirRadius = 34 + (dirCount <= 3 ? (4 - dirCount) * 4 : 0);
  const angSpan = Math.min(1.0, ((Math.PI * 2) / dirCount) * 0.4 + 0.4);
  directions.forEach((node, index) => {
    const theta = (index / dirCount) * Math.PI * 2 + Math.PI / dirCount;
    const pos = {
      x: Math.cos(theta) * dirRadius,
      y: DIRECTION_Y + (index % 2) * 6,
      z: Math.sin(theta) * dirRadius,
    };
    positions.set(node.id, pos);
    directionPos.set(node.id, { pos, theta, angSpan });
  });

  const fallbackDirection = () => {
    const first = directions[0];
    return first
      ? directionPos.get(first.id)
      : { pos: trunkAnchor(), theta: 0.4, angSpan: Math.PI * 0.9 };
  };

  // 3. Branch (projects) — siblings of one goal fan evenly across its angular
  // budget (ranked deterministically by id) instead of scattering randomly.
  const branches = byRole("branch");
  const branchPos = new Map();
  // Group branches by their owning goal so we can fan siblings evenly.
  const branchGoal = new Map();
  const siblingsByGoal = new Map();
  branches.forEach((node) => {
    const parent = parentByRelation(node, edgesByTarget, ["contains", "alignment"], nodesById);
    const goalId = parent && directionPos.has(parent.id) ? parent.id : "__fallback__";
    branchGoal.set(node.id, goalId);
    if (!siblingsByGoal.has(goalId)) {
      siblingsByGoal.set(goalId, []);
    }
    siblingsByGoal.get(goalId).push(node.id);
  });
  siblingsByGoal.forEach((ids) => ids.sort());
  branches.forEach((node) => {
    const goalId = branchGoal.get(node.id);
    const base = (goalId !== "__fallback__" && directionPos.get(goalId)) || fallbackDirection();
    const siblings = siblingsByGoal.get(goalId) || [node.id];
    const n = siblings.length;
    const rank = Math.max(0, siblings.indexOf(node.id));
    const span = base.angSpan ?? angSpan;
    // Even fan within ±span; single child sits on the goal's own bearing.
    const frac = n > 1 ? rank / (n - 1) - 0.5 : 0;
    const jitter = (hashUnit(`${node.id}:t`) - 0.5) * 0.18;
    const theta = base.theta + frac * 2 * span + jitter;
    const r = 22 + Math.min(n, 8) * 1.6 + hashUnit(`${node.id}:r`) * 8;
    const pos = {
      x: base.pos.x + Math.cos(theta) * r,
      y: base.pos.y + BRANCH_RISE + (hashUnit(`${node.id}:y`) - 0.5) * 6,
      z: base.pos.z + Math.sin(theta) * r,
    };
    positions.set(node.id, pos);
    branchPos.set(node.id, { pos, theta, spread: theta });
  });

  // 4. Leaf (tasks/outputs) — scatter at the branch tips, lifted to the crown.
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
    const r = 11 + hashUnit(`${node.id}:lr`) * 9;
    const pos = {
      x: anchor.x + Math.cos(theta) * r,
      y: anchor.y + LEAF_RISE + hashUnit(`${node.id}:ly`) * 6,
      z: anchor.z + Math.sin(theta) * r,
    };
    positions.set(node.id, pos);
    leafPos.set(node.id, { pos });
  });

  // 5. Star (skills) — a glowing dome above the canopy. Each category claims a
  // contiguous sky sector (a "constellation region"); within a sector skills
  // spiral out by a fibonacci angle for an even, stable spread.
  const stars = byRole("star");
  // Stable category order so sectors don't reshuffle between renders.
  const categories = [...new Set(stars.map((node) => cleanText(node.metric) || "general"))].sort();
  const categoryIndex = new Map(categories.map((cat, idx) => [cat, idx]));
  const catCount = Math.max(1, categories.length);
  // Rank each star within its own category for the intra-sector spiral.
  const starsByCat = new Map();
  stars.forEach((node) => {
    const cat = cleanText(node.metric) || "general";
    if (!starsByCat.has(cat)) {
      starsByCat.set(cat, []);
    }
    starsByCat.get(cat).push(node.id);
  });
  starsByCat.forEach((ids) => ids.sort());
  const sectorWidth = (Math.PI * 2) / catCount;
  stars.forEach((node) => {
    const cat = cleanText(node.metric) || "general";
    const catIdx = categoryIndex.get(cat) || 0;
    const peers = starsByCat.get(cat) || [node.id];
    const localRank = Math.max(0, peers.indexOf(node.id));
    const localCount = Math.max(1, peers.length);
    // Latitude band: spread the category's skills from dome edge toward the top.
    const t = (localRank + 0.5) / localCount;
    const phi = Math.acos(1 - t * 0.92); // 0 (top) .. ~0.9*pi/2
    // Longitude: sit inside this category's sector, fanned within it.
    const within = localCount > 1 ? localRank / (localCount - 1) - 0.5 : 0;
    const theta = catIdx * sectorWidth + sectorWidth * (0.5 + within * 0.7);
    const r = STAR_DOME_RADIUS * (0.84 + hashUnit(`${node.id}:sr`) * 0.16);
    positions.set(node.id, {
      x: Math.sin(phi) * Math.cos(theta) * r,
      y: STAR_DOME_CENTER_Y - 10 + Math.cos(phi) * r * 0.42,
      z: Math.sin(phi) * Math.sin(theta) * r,
    });
  });

  // 6. Fruit (evidence) — hang below a task/project/output anchor, or drift
  // toward an outgoing skill/output support when no incoming parent exists.
  const fruits = byRole("fruit");
  fruits.forEach((node) => {
    const parent = parentByRelation(
      node,
      edgesByTarget,
      ["layout_anchor", "generated_by", "produces", "supports", "contains", "review", "derives"],
      nodesById,
    );
    const outgoing = outgoingAnchorPosition(
      node,
      edgesBySource,
      ["produces", "supports", "claim_evidence_skill"],
      positions,
      nodesById,
    );
    const base =
      (parent && (leafPos.get(parent.id)?.pos || branchPos.get(parent.id)?.pos || positions.get(parent.id))) ||
      outgoing ||
      null;
    const anchor = base || { x: 0, y: DIRECTION_Y + LEAF_RISE, z: 0 };
    const theta = hashUnit(`${node.id}:ft`) * Math.PI * 2;
    const r = 6 + hashUnit(`${node.id}:fr`) * 8;
    positions.set(node.id, {
      x: anchor.x + Math.cos(theta) * r,
      y: anchor.y - FRUIT_DROP - hashUnit(`${node.id}:fy`) * 7,
      z: anchor.z + Math.sin(theta) * r,
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
      centroid = { x: Math.cos(theta) * 34, y: TRUNK_TOP_Y * 0.78, z: Math.sin(theta) * 34 };
    }
    positions.set(node.id, {
      x: centroid.x,
      y: centroid.y + 14 + hashUnit(`${node.id}:cy`) * 8,
      z: centroid.z,
    });
  });

  // Any tree-role node still unplaced (missing edges) gets pinned near the trunk
  // at a stable mid-height so nothing snaps to the origin.
  nodes.forEach((node) => {
    if (positions.has(node.id) || node.role === SAND_ROLE || !TREE_ROLES.has(node.role)) {
      return;
    }
    positions.set(node.id, {
      x: (hashUnit(`${node.id}:ux`) - 0.5) * 20,
      y: DIRECTION_Y + hashUnit(`${node.id}:uy`) * 30,
      z: (hashUnit(`${node.id}:uz`) - 0.5) * 20,
    });
  });

  return positions;
}

// Deterministic "growth galaxy" layout. Returns id -> {x,y,z}. The North Star
// is the bright core; goals/projects/tasks/outputs/evidence spiral outward on a
// flattened galactic plane (parent angle inherited so containment reads as
// clustering); skills form a surrounding spherical halo sectorized by category;
// claims sit at the centroid of what they support; sand is excluded (ambient
// dust). No Math.random — hashUnit keeps it refresh-stable.
function growthGalaxyLayout(payload, nodes, focusGoalId = null) {
  const positions = new Map();
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const edges = asArray(payload.graph.edges).filter(
    (edge) => nodesById.has(edge.from) && nodesById.has(edge.to),
  );
  const edgesByTarget = new Map();
  edges.forEach((edge) => {
    if (!edgesByTarget.has(edge.to)) edgesByTarget.set(edge.to, []);
    edgesByTarget.get(edge.to).push(edge);
  });
  const byRole = (role) => nodes.filter((node) => node.role === role);

  // Goal orbit geometry. Hoisted to the top of the layout scope because
  // `placeSkillConstellations` (defined below) reads these to push the skill
  // shell outside the outermost goal ring — and that helper is CALLED from the
  // focus branch (clicking a goal) which runs BEFORE the goal-placement section.
  // Declaring them only at the goal section left them in the temporal dead zone
  // during a focused render → "Cannot access GOAL_BASE_R before initialization"
  // → white screen whenever a goal was clicked. Single declaration, used by both
  // the focus path and the overview goal rings.
  const GOAL_BASE_R = 80;
  const GOAL_RING_GAP = 60;

  // The galaxy has real 3D volume (a central bulge + arm waviness) so it never
  // collapses to an edge-on sheet. Rings grow outward by metaphor depth.
  // Nested orbital system (银河系/太阳系/地月系): the North Star is the center;
  // goals orbit it on distinct inclined shells; projects orbit their goal; tasks
  // /outputs/evidence orbit their project; orphans (no parent) share a common
  // orbit. `orbits` records each ring (center + radius + tilt) so the scene can
  // draw the "who circles whom" rings.
  const orbits = [];
  const childrenByParent = (relations) => {
    const map = new Map();
    edges.forEach((e) => {
      if (!relations.includes(e.relation || e.type)) return;
      if (!map.has(e.from)) map.set(e.from, []);
      map.get(e.from).push(e.to);
    });
    return map;
  };

  // 0. Core.
  const core = byRole("trunk")[0];
  const corePos = { x: 0, y: 0, z: 0 };
  if (core) positions.set(core.id, corePos);

  // Per-node orbit params so the scene can animate true rotation around the
  // (possibly moving) parent center: { parentId, a, b, tilt, swivel, baseAngle, speed }.
  // Orbits are gently elliptical (a=semi-major, b=semi-minor) and each is swivelled
  // in-plane so the rings don't all align — borrowing the layered, orderly beauty
  // of NASA Eyes without chasing literal Keplerian accuracy.
  const nodeOrbits = new Map();

  // Place children evenly along an elliptical orbit around a parent. `tilt`
  // inclines the orbital plane; `swivel` rotates the ellipse within that plane;
  // `ecc` sets how oval it is. Deterministic (hashUnit, no random).
  const placeOnOrbit = (children, parentId, center, radius, tilt, phaseSeed, speed, ecc = 0.18, centerOffsetY = 0, tier = null, skipRing = false) => {
    const n = Math.max(1, children.length);
    const a = radius; // semi-major
    const b = radius * (1 - ecc); // semi-minor
    const cosT = Math.cos(tilt);
    const sinT = Math.sin(tilt);
    const swivel = hashUnit(`${phaseSeed}:sw`) * Math.PI * 2;
    const cosS = Math.cos(swivel);
    const sinS = Math.sin(swivel);
    const phase = hashUnit(`${phaseSeed}:ph`) * Math.PI * 2;
    // The orbital plane can be lifted/lowered off the parent's center so tiers
    // sharing a parent (tasks above, evidence below) read as distinct shells.
    const cy = center.y + centerOffsetY;
    const at = (ang) => {
      // Ellipse in local plane, swivelled, then inclined about the X axis.
      const ex = Math.cos(ang) * a;
      const ey = Math.sin(ang) * b;
      const px = ex * cosS - ey * sinS;
      const pz = ex * sinS + ey * cosS;
      return { x: center.x + px, y: cy + pz * sinT, z: center.z + pz * cosT };
    };
    children.forEach((id, i) => {
      const ang = phase + (i / n) * Math.PI * 2;
      positions.set(id, at(ang));
      nodeOrbits.set(id, { parentId, a, b, tilt, swivel, baseAngle: ang, speed, centerOffsetY, tier });
    });
    // Only record a ring when something actually orbits on it — an empty `children`
    // array (e.g. a focused goal with zero projects) must never paint a hollow ellipse.
    // Tier 3 (evidence comets) draws no ring: the comet's own fading trail traces
    // the orbit, so a static ellipse there would just be redundant clutter.
    if (children.length && tier !== 3 && !skipRing) {
      orbits.push({ center: { x: center.x, y: cy, z: center.z }, a, b, tilt, swivel, phase, parentId, tier });
    }
  };
  // Orbit angular speed: slower for bigger orbits (Keplerian feel), capped.
  const orbitSpeed = (radius) => 0.12 * Math.sqrt(60 / Math.max(20, radius));

  // Spread a set of bodies across up to 3 nested concentric rings around a parent
  // so a project with many tasks reads as a multi-orbit planetary system rather
  // than a single crammed circle. The rings stay NEAR-COPLANAR (small per-ring
  // tilt step + small jitter) so a project's tasks read as a flat "disk" / Saturn
  // ring, not a tangled ball of differently-angled hoops. Bodies are dealt
  // round-robin (i % ringCount) so siblings of different kinds interleave.
  // Geometric collision constants — keep in sync with galaxy_scene.js sphere
  // size bands (r_p ≤ 9 for projects, r_t ≤ 4.5 for tasks). The constraint
  // system below uses these directly so a child disk never welds onto the
  // project body or laps an inner ring. Single source of truth.
  const LAYOUT_R_PROJECT_MAX = 9;
  const LAYOUT_R_TASK_MAX = 4.5;
  const LAYOUT_SAFE_MARGIN = 2;
  const placeConcentric = (ids, parentId, center, { baseR, gap, tilt, offsetY = 0, tier = 2, speedMul = 1.5, ecc = 0.16, parentRadius = LAYOUT_R_PROJECT_MAX, childRadius = LAYOUT_R_TASK_MAX } = {}) => {
    if (!ids.length) return;
    // Constraint B: inner ring must clear the parent sphere.
    const R0 = Math.max(baseR || 0, parentRadius + childRadius + LAYOUT_SAFE_MARGIN);
    // Constraint C: adjacent rings must not collide.
    const dR = Math.max(gap || 0, 2 * childRadius + LAYOUT_SAFE_MARGIN);
    const f = Math.max(0.6, 1 - ecc); // eccentricity foreshortening
    // Constraint A: same-ring spacing — max bodies a ring of radius R can hold.
    const ringCapacity = (R) => {
      const arg = (childRadius + LAYOUT_SAFE_MARGIN / 2) / (f * R);
      if (arg >= 1) return 1;
      return Math.max(1, Math.floor(Math.PI / Math.asin(arg)));
    };
    // Capacity-driven K: grow rings outward until we can hold every child.
    const ringRadii = [];
    const caps = [];
    let assigned = 0;
    let kIdx = 0;
    while (assigned < ids.length && kIdx < 12) {
      const R = R0 + kIdx * dR;
      const cap = ringCapacity(R);
      ringRadii.push(R);
      caps.push(cap);
      assigned += cap;
      kIdx += 1;
    }
    const K = ringRadii.length;
    // Distribute ids proportional to ring capacity (inner rings fill first to
    // their cap; the outer ring absorbs the remainder so we never violate A).
    const buckets = Array.from({ length: K }, () => []);
    let cursor = 0;
    for (let k = 0; k < K; k += 1) {
      const take = k === K - 1 ? ids.length - cursor : Math.min(caps[k], ids.length - cursor);
      for (let i = 0; i < take; i += 1) {
        buckets[k].push(ids[cursor + i]);
      }
      cursor += take;
      if (cursor >= ids.length) break;
    }
    for (let k = 0; k < K; k += 1) {
      const chunk = buckets[k];
      if (!chunk.length) continue;
      const R = ringRadii[k];
      // Keep rings nearly coplanar: a small progressive k term gives just enough
      // depth to tell nested rings apart, with a small hash jitter to break
      // dead symmetry. Eccentricity grows gently outward.
      const t = tilt + k * 0.06 + (hashUnit(`${parentId}:rt${k}`) - 0.5) * 0.15;
      const e = Math.min(0.4, Math.max(0.05, ecc + k * 0.05 + (hashUnit(`${parentId}:re${k}`) - 0.5) * 0.08));
      placeOnOrbit(chunk, parentId, center, R, t, `${parentId}:ring${k}`, orbitSpeed(R) * speedMul, e, offsetY, tier);
    }
  };

  // Skills are grouped into per-category constellations: each category owns a
  // small cluster placed around the galaxy (not one enveloping sphere), and the
  // scene draws faint figure-lines between a cluster's stars. Deterministic
  // (hashUnit, no Math.random). Returns [{cat, center, memberIds, color}] so the
  // scene can draw lines + a category label without re-grouping. Shared by the
  // overview and focused layouts (skills stay as the outer reference when zoomed).
  const placeSkillConstellations = () => {
    const stars = byRole("star");
    if (!stars.length) return [];
    // Push the skill shell outside the outermost goal orbit so constellations
    // never collide with goal rings in fit mode. The outermost goal sits at
    // GOAL_BASE_R + (N-1)·GOAL_RING_GAP; we add a healthy gap on top so cluster
    // jitter (≤40) + per-skill scatter (≤32) still clears the goal band.
    const directionCount = byRole("direction").length;
    const goalsMaxRadius = directionCount
      ? GOAL_BASE_R + Math.max(0, directionCount - 1) * GOAL_RING_GAP
      : 0;
    const skillShellBase = Math.max(230, goalsMaxRadius + 120);
    const NON_CATEGORY = new Set(["manual", "rule", "ai", "rule+ai", ""]);
    const catOf = (n) => {
      const m = cleanText(n.metric);
      return m && !NON_CATEGORY.has(m) ? m : `misc${Math.floor(hashUnit(`${n.id}:cat`) * 6)}`;
    };
    const categories = [...new Set(stars.map(catOf))].sort();
    const catCount = Math.max(1, categories.length);
    const starsByCat = new Map();
    stars.forEach((n) => {
      const c = catOf(n);
      if (!starsByCat.has(c)) starsByCat.set(c, []);
      starsByCat.get(c).push(n.id);
    });
    starsByCat.forEach((ids) => ids.sort());
    const constellations = [];
    categories.forEach((cat, ci) => {
      // Cluster center: spread around a ring of longitudes, jittered in latitude
      // + radius so the constellations don't sit on one perfect circle.
      const ringAng = ((ci + 0.5) / catCount) * Math.PI * 2;
      const lat = (hashUnit(`${cat}:lat`) - 0.5) * 0.9;
      const CR = skillShellBase + hashUnit(`${cat}:cr`) * 40;
      const center = {
        x: Math.cos(ringAng) * Math.cos(lat) * CR,
        y: 40 + Math.sin(lat) * CR * 0.5,
        z: Math.sin(ringAng) * Math.cos(lat) * CR,
      };
      const memberIds = starsByCat.get(cat) || [];
      memberIds.forEach((id) => {
        // Small blob around the cluster center, deterministic per skill id.
        const rad = 14 + hashUnit(`${id}:cr`) * 18; // 14..32
        const a = hashUnit(`${id}:ca`) * Math.PI * 2;
        const b = Math.acos(1 - 2 * hashUnit(`${id}:cb`));
        positions.set(id, {
          x: center.x + Math.sin(b) * Math.cos(a) * rad,
          y: center.y + Math.cos(b) * rad,
          z: center.z + Math.sin(b) * Math.sin(a) * rad,
        });
      });
      constellations.push({ cat, center, memberIds, color: skillCategoryColor({ metric: cat }) });
    });
    return constellations;
  };

  // ── Focused sub-galaxy ─────────────────────────────────────────────────────
  // Clicking into a goal pins it at the center as a STATIC sun (no nodeOrbits
  // entry → the animation loop never moves it) and shows only its three orbital
  // tiers: projects circle the goal (Tier 1, near-circular reference plane),
  // tasks circle each project on a high-inclination tight oval lifted above
  // (Tier 2), evidence circles on a wide elongated belt dropped below (Tier 3).
  // The North Star, sibling goals, orphans and claims are excluded so the goal
  // reads as its own clean solar system. Returns focusVisibleIds so graph3DData
  // can trim the rendered node set.
  if (focusGoalId && nodesById.has(focusGoalId)) {
    const goalPos = { x: 0, y: 0, z: 0 };
    positions.set(focusGoalId, goalPos);
    const branches = byRole("branch");
    const leaves = byRole("leaf");
    const fruits = byRole("fruit");
    const hasFrom = (id, relations, from) =>
      (edgesByTarget.get(id) || []).some(
        (e) => relations.includes(e.relation || e.type) && e.from === from,
      );

    // Tier 1 — projects orbit the goal. Wider base + gap so the sub-galaxy reads
    // roomy (the goal sits big at center; projects need clearance from it).
    const projects = branches
      .filter((b) => hasFrom(b.id, ["contains", "alignment"], focusGoalId))
      .map((b) => b.id)
      .sort();
    const R1 = 58 + Math.min(projects.length, 8) * 7;
    placeOnOrbit(projects, focusGoalId, goalPos, R1, 0.16, `${focusGoalId}:f1`, orbitSpeed(R1) * 1.0, 0.08, 0, 1);
    // Constraint D — budget: the task disk's outermost ring must fit inside
    // the chord distance between adjacent projects, else neighbouring task
    // disks will overlap. Log when we bust the budget rather than silently
    // overlap; the visual will still draw but the dev console makes it
    // diagnosable.
    if (projects.length >= 2) {
      const chord = R1 * Math.sin(Math.PI / projects.length);
      const maxOutR = chord - LAYOUT_R_TASK_MAX - LAYOUT_SAFE_MARGIN / 2;
      window.__nblaneLayoutBudget = { R1, chord, maxOutR, P: projects.length };
    }

    const visible = new Set([focusGoalId, ...projects]);
    const candFrom = (id) =>
      (edgesByTarget.get(id) || [])
        .filter((e) =>
          ["generated_by", "produces", "supports", "contains", "review", "derives"].includes(e.relation || e.type),
        )
        .map((e) => e.from);
    projects.forEach((pid) => {
      const center = positions.get(pid) || goalPos;
      // Tasks/outputs that belong to this project.
      const tasks = leaves
        .filter((l) => hasFrom(l.id, ["contains", "produces", "drives", "supports"], pid))
        .map((l) => l.id)
        .sort();
      const taskSet = new Set(tasks);

      // Evidence on this project splits two ways: generated by one of its tasks
      // (→ a small fast "moon" of that task — the task↔evidence link is the orbit
      // itself) vs tied only to the project (→ a same-tier peer of the tasks,
      // told apart by colour, not a separate wide "twin" ring).
      const evNodes = fruits.filter((f) => {
        const cand = candFrom(f.id);
        return cand.includes(pid) || cand.some((id) => taskSet.has(id));
      });
      const evByTask = new Map();
      const evProjectOnly = [];
      evNodes.forEach((f) => {
        const cand = candFrom(f.id);
        const ownerTask = cand.find((id) => taskSet.has(id));
        if (ownerTask) {
          if (!evByTask.has(ownerTask)) evByTask.set(ownerTask, []);
          evByTask.get(ownerTask).push(f.id);
        } else {
          evProjectOnly.push(f.id);
        }
      });

      // Tier 2a — tasks alone share one concentric-ring disk around the
      // project, so the disk reads as "task plate". Project-only evidence is
      // pushed to its own outer comet orbit (tier 2b) instead of being mixed
      // into the task disk, which used to leave a clump of dots welded onto
      // the project body. With the tighter baseR/gap the disk stays inside
      // the project↔project gap (≤21).
      placeConcentric(tasks, pid, center, {
        baseR: 10, gap: 6, tilt: 0.36, offsetY: 5, tier: 2, speedMul: 1.5, ecc: 0.1,
      });
      tasks.forEach((x) => visible.add(x));

      if (evProjectOnly.length) {
        // Project-only evidence orbit: a single faster comet ring further out
        // than the task disk so it reads as evidence drifting around the
        // project as a whole, not stitched onto any one task. Same comet
        // visual the task-owned evidence uses (see Tier 3 below), so the eye
        // sees one consistent "evidence = comet" cue everywhere.
        evProjectOnly.sort();
        const Rp = 18 + Math.min(evProjectOnly.length, 6) * 1.2;
        const tiltp = 0.55 + hashUnit(`${pid}:ev`) * 0.5;
        placeOnOrbit(evProjectOnly, pid, center, Rp, tiltp, `${pid}:ev`, orbitSpeed(Rp) * 4, 0.18, 0, 3);
        evProjectOnly.forEach((x) => visible.add(x));
      }

      // Tier 3 — task-generated evidence orbits its task as a tiny, fast comet
      // (small bright head + fading trail, drawn by the scene). The whipping comet
      // *is* the cue, so no orbit ring is drawn for this tier. A task with a comet
      // circling it has produced evidence; a bare task has not yet.
      evByTask.forEach((ids, tid) => {
        const tcenter = positions.get(tid) || center;
        ids.sort();
        const Rm = 5 + Math.min(ids.length, 4) * 1.2; // tight comet orbit around the task
        const tilt = 0.9 + hashUnit(`${tid}:em`) * 0.5;
        // Whip the evidence comet around at "paper-meteor" pace — a full revolution
        // in ~2s reads as a tiny streak flicking around its task, not a lazy moon.
        // The high tilt keeps the loop near edge-on so it flashes across like a comet.
        placeOnOrbit(ids, tid, tcenter, Rm, tilt, `${tid}:em`, orbitSpeed(Rm) * 14, 0.34, 0, 3);
        ids.forEach((x) => visible.add(x));
      });
    });

    const constellations = placeSkillConstellations();
    byRole("star").forEach((s) => visible.add(s.id));
    return { positions, orbits, nodeOrbits, constellations, focusVisibleIds: visible };
  }

  // 1. Goals orbit the North Star, each on its own shell + inclination so the
  // orbits nest like a solar system rather than lying flat.
  // (GOAL_BASE_R / GOAL_RING_GAP are hoisted to the top of this function.)
  const directions = byRole("direction");
  directions.forEach((node, i) => {
    const radius = GOAL_BASE_R + i * GOAL_RING_GAP;
    const tilt = 0.5 + (i - (directions.length - 1) / 2) * 0.34; // distinct inclinations
    // The synthetic "Other" goal hangs orphan work off a labelled hub but isn't
    // a real direction the user set — drawing a top-level ring for it would
    // mint a huge empty outer ellipse that reads as scaffolding noise. Place
    // the orb on the orbit so its subsystem still nests cleanly, just skip
    // the parent ring.
    const skipRing = node.id === OTHER_GOAL_ID;
    placeOnOrbit([node.id], core?.id || "__core__", corePos, radius, tilt, `goal${i}`, orbitSpeed(radius), 0.18, 0, null, skipRing);
  });

  // 2. Projects orbit their owning goal; orphan projects share one outer orbit
  // around the core (a "loose work" cluster).
  const projContains = childrenByParent(["contains", "alignment"]);
  const goalIds = new Set(directions.map((d) => d.id));
  const branches = byRole("branch");
  const projByGoal = new Map();
  const orphanProjects = [];
  branches.forEach((node) => {
    const parents = (edgesByTarget.get(node.id) || [])
      .filter((e) => ["contains", "alignment"].includes(e.relation || e.type))
      .map((e) => e.from)
      .filter((id) => goalIds.has(id));
    if (parents.length) {
      const g = parents[0];
      if (!projByGoal.has(g)) projByGoal.set(g, []);
      projByGoal.get(g).push(node.id);
    } else {
      orphanProjects.push(node.id);
    }
  });
  projByGoal.forEach((ids, goalId) => {
    const center = positions.get(goalId) || corePos;
    ids.sort();
    // Keep the project cloud tight to its goal: child orbit radius must stay well
    // under the goal-to-goal gap (≈60) so adjacent goals read as separate solar
    // systems with vacuum between them, not interpenetrating rings. Iron rule:
    // child ≤ 0.4 × parent gap → cap is ~21 with GOAL_RING_GAP=60.
    const radius = 12 + Math.min(ids.length, 6) * 1.5;
    placeOnOrbit(ids, goalId, center, radius, 0.5 + hashUnit(`${goalId}:t`) * 0.6, goalId, orbitSpeed(radius) * 1.4);
  });
  if (orphanProjects.length) {
    orphanProjects.sort();
    const radius = GOAL_BASE_R + directions.length * GOAL_RING_GAP + 24;
    placeOnOrbit(orphanProjects, core?.id || "__core__", corePos, radius, -0.5, "orphan", orbitSpeed(radius), 0.18, 0, null, true);
  }

  // 3 + 4. Project sub-systems: tasks/outputs (leaves) and project-tied evidence
  // (fruit) share ONE concentric-ring system around their project (2–3 nested
  // rings; colour separates task=brown from evidence=purple — same tier, no wide
  // "twin" ring). Evidence generated by a specific task, plus leaves/fruit on a
  // non-project parent, get a single tidy ring; true orphans cluster on an outer
  // ring. (Per-task moons are a focused-view detail — too fine to draw zoomed out.)
  const leaves = byRole("leaf");
  const leavesByParent = new Map();
  const orphanLeaves = [];
  leaves.forEach((node) => {
    const parents = (edgesByTarget.get(node.id) || [])
      .filter((e) => ["contains", "produces", "drives", "supports"].includes(e.relation || e.type))
      .map((e) => e.from)
      .filter((id) => positions.has(id));
    if (parents.length) {
      const p = parents[0];
      if (!leavesByParent.has(p)) leavesByParent.set(p, []);
      leavesByParent.get(p).push(node.id);
    } else {
      orphanLeaves.push(node.id);
    }
  });

  const branchIds = new Set(branches.map((b) => b.id));
  const fruits = byRole("fruit");
  const fruitByParent = new Map();
  const orphanFruit = [];
  fruits.forEach((node) => {
    const cand = (edgesByTarget.get(node.id) || [])
      .filter((e) =>
        ["generated_by", "produces", "supports", "contains", "review", "derives"].includes(e.relation || e.type),
      )
      .map((e) => e.from)
      .filter((id) => positions.has(id));
    // Prefer a project parent (direct, or the project that owns a linked task).
    let parent = cand.find((id) => branchIds.has(id));
    if (!parent) {
      for (const id of cand) {
        const po = nodeOrbits.get(id);
        if (po && branchIds.has(po.parentId)) {
          parent = po.parentId;
          break;
        }
      }
    }
    if (!parent) parent = cand[0];
    if (parent) {
      if (!fruitByParent.has(parent)) fruitByParent.set(parent, []);
      fruitByParent.get(parent).push(node.id);
    } else {
      orphanFruit.push(node.id);
    }
  });

  const childParents = new Set([...leavesByParent.keys(), ...fruitByParent.keys()]);
  childParents.forEach((parentId) => {
    const center = positions.get(parentId) || corePos;
    const leafIds = (leavesByParent.get(parentId) || []).slice().sort();
    const fruitIds = (fruitByParent.get(parentId) || []).slice().sort();
    if (branchIds.has(parentId)) {
      // Project: tasks + project-tied evidence are peers on a concentric system.
      placeConcentric([...leafIds, ...fruitIds], parentId, center, {
        baseR: 14, gap: 9, tilt: 0.7, offsetY: 6, tier: 2, speedMul: 1.7, ecc: 0.16,
      });
    } else {
      // Non-project parent (task/output/…): one tidy ring per child kind.
      if (leafIds.length) {
        const radius = 13 + Math.min(leafIds.length, 6) * 1.6;
        placeOnOrbit(leafIds, parentId, center, radius, 0.7 + hashUnit(`${parentId}:lt`) * 0.7, parentId, orbitSpeed(radius) * 1.8, 0.18, 0, 2);
      }
      if (fruitIds.length) {
        const radius = 9 + Math.min(fruitIds.length, 5) * 1.5;
        const tilt = 0.9 + hashUnit(`${parentId}:ft`) * 0.5;
        placeOnOrbit(fruitIds, parentId, center, radius, tilt, `${parentId}:ev`, orbitSpeed(radius) * 2.0, 0.18, 0, 2);
      }
    }
  });
  if (orphanLeaves.length) {
    orphanLeaves.sort();
    const radius = GOAL_BASE_R + directions.length * GOAL_RING_GAP + 48;
    // Orphan-leaf catch-all orbit: the work itself still flies around, but the
    // ring is an outer scaffold most users don't recognise as theirs. Skip the
    // visible ellipse so the canvas stops looking like there's a giant empty
    // orbit at the rim.
    placeOnOrbit(orphanLeaves, core?.id || "__core__", corePos, radius, 0.3, "orphanleaf", orbitSpeed(radius), 0.18, 0, null, true);
  }
  if (orphanFruit.length) {
    orphanFruit.sort();
    const radius = GOAL_BASE_R + directions.length * GOAL_RING_GAP + 66;
    placeOnOrbit(orphanFruit, core?.id || "__core__", corePos, radius, -0.3, "orphanfruit", orbitSpeed(radius), 0.18, 0, null, true);
  }

  // 5. Skills — grouped into per-category constellations placed around the galaxy
  // (see placeSkillConstellations). The scene draws figure-lines + a label per
  // cluster; brightness still maps to mastery via starEmissive.
  const constellations = placeSkillConstellations();

  // 6. Claims — at the centroid of the evidence/skills they tie together, lifted
  // above the plane so the "constellation" floats over its sources.
  byRole("constellation").forEach((node) => {
    const anchors = (edgesByTarget.get(node.id) || [])
      .filter((e) => ["supports", "derives"].includes(e.relation || e.type))
      .map((e) => positions.get(e.from))
      .filter(Boolean);
    let c;
    if (anchors.length) {
      c = anchors.reduce((a, p) => ({ x: a.x + p.x, y: a.y + p.y, z: a.z + p.z }), { x: 0, y: 0, z: 0 });
      c = { x: c.x / anchors.length, y: c.y / anchors.length, z: c.z / anchors.length };
    } else {
      const a = hashUnit(`${node.id}:ct`) * Math.PI * 2;
      c = { x: Math.cos(a) * 120, y: 30, z: Math.sin(a) * 120 };
    }
    positions.set(node.id, { x: c.x, y: c.y + 26 + hashUnit(`${node.id}:cy`) * 10, z: c.z });
  });

  // Any remaining placeable node (missing edges) drifts on an outer ring so it
  // never collapses to the core.
  nodes.forEach((node) => {
    if (positions.has(node.id) || node.role === SAND_ROLE || !TREE_ROLES.has(node.role)) return;
    const a = hashUnit(`${node.id}:ux`) * Math.PI * 2;
    const r = 100 + hashUnit(`${node.id}:ur`) * 60;
    positions.set(node.id, { x: Math.cos(a) * r, y: (hashUnit(`${node.id}:uy`) - 0.5) * 20, z: Math.sin(a) * r });
  });

  return { positions, orbits, nodeOrbits, constellations, focusVisibleIds: null };
}

// Resolve which goal (role "direction") a selected node belongs to, by walking
// the containment edges upward. A selected goal returns itself; a project/task
// /evidence returns the goal it rolls up into; anything else (or no selection)
// returns null → overview. Mirrors the scene's `_ancestorGoal` walk so React and
// THREE agree on the focused subsystem.
function ancestorGoalId(payload, nodes, selectedId) {
  const sel = cleanText(selectedId);
  if (!sel) return null;
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const selNode = nodesById.get(sel);
  if (!selNode || !TREE_ROLES.has(selNode.role)) return null;
  if (selNode.role === "direction") return sel;
  const edgesByTarget = new Map();
  asArray(payload.graph.edges).forEach((edge) => {
    if (!edgesByTarget.has(edge.to)) edgesByTarget.set(edge.to, []);
    edgesByTarget.get(edge.to).push(edge);
  });
  const allowed = ["contains", "alignment", "produces", "drives", "supports", "generated_by", "derives"];
  let cur = sel;
  const guard = new Set();
  while (cur && !guard.has(cur)) {
    guard.add(cur);
    const node = nodesById.get(cur);
    if (node && node.role === "direction") return cur;
    const parent = (edgesByTarget.get(cur) || [])
      .filter((e) => allowed.includes(e.relation || e.type))
      .map((e) => e.from)
      .find((id) => nodesById.has(id) && !guard.has(id));
    cur = parent || null;
  }
  return null;
}

// Aggregate hubs (the "Evidence candidates" pending pool + the atomic-evidence
// catch-all pool) are inbox concepts with their own dashboard panels — like
// source:inbox they don't belong in the galaxy, where they'd otherwise fall to
// an orphan ring around the North Star.
function isGalaxyAggregate(node) {
  return node.type === "evidence_candidate" || node.id === "atomic_evidence:pool";
}

// The real (non-aggregate) tree-role nodes that make up the galaxy.
function galaxyTreeNodes(nodes) {
  return nodes.filter((node) => TREE_ROLES.has(node.role) && !isGalaxyAggregate(node));
}

// Adopt orphans under a synthetic "Other" goal. A project with no owning goal —
// or a task/evidence with no placeable parent at all — used to be flung onto a
// huge, near-empty ring around the North Star. Instead we mint one catch-all
// "Other" goal (a real direction sun) and hang every orphan off it with a
// `contains` edge, so loose work orbits a labelled hub exactly like a real goal's
// work does. Returns the node list + payload the galaxy layout should actually
// use (augmented when any orphan exists, the originals untouched otherwise).
function buildGalaxyInputs(payload, treeNodes) {
  const nodesById = new Map(treeNodes.map((n) => [n.id, n]));
  const goalIds = new Set(treeNodes.filter((n) => n.role === "direction").map((n) => n.id));
  const edgesByTarget = new Map();
  asArray(payload.graph.edges).forEach((e) => {
    if (!nodesById.has(e.to) || !nodesById.has(e.from)) return;
    if (!edgesByTarget.has(e.to)) edgesByTarget.set(e.to, []);
    edgesByTarget.get(e.to).push(e);
  });
  const parentsOf = (id, relations) =>
    (edgesByTarget.get(id) || [])
      .filter((e) => relations.includes(e.relation || e.type))
      .map((e) => e.from);
  const orphans = [];
  treeNodes.forEach((node) => {
    if (node.role === "branch") {
      // A project with no owning goal among the real directions.
      if (!parentsOf(node.id, ["contains", "alignment"]).some((id) => goalIds.has(id))) {
        orphans.push(node.id);
      }
    } else if (node.role === "leaf" || node.role === "fruit") {
      // A task/output/evidence with no placeable structural parent at all.
      const rel = ["contains", "produces", "drives", "supports", "generated_by", "review", "derives"];
      if (!parentsOf(node.id, rel).some((id) => nodesById.has(id))) {
        orphans.push(node.id);
      }
    }
  });
  if (!orphans.length) {
    return { nodes: treeNodes, payload, otherGoalId: null };
  }
  const otherGoal = {
    id: OTHER_GOAL_ID,
    role: "direction",
    type: "goal",
    layer: "objective",
    label: label(payload.ui, "dashboard_other_goal", "其他"),
    implemented: true,
    synthetic: true,
  };
  const synthEdges = orphans.map((to) => ({
    from: OTHER_GOAL_ID,
    to,
    relation: "contains",
    type: "contains",
    synthetic: true,
  }));
  return {
    nodes: [...treeNodes, otherGoal],
    payload: {
      ...payload,
      graph: { ...payload.graph, edges: [...asArray(payload.graph.edges), ...synthEdges] },
    },
    otherGoalId: OTHER_GOAL_ID,
  };
}

// Count how many nodes sit beneath each node along structural (parent→child)
// edges — a goal's "subtree mass". Goals are then sized by this so a direction
// that spawned a big body of work reads as a dominant sun, never smaller than the
// project swarm orbiting it.
function subtreeMassByNode(links, nodes) {
  const children = new Map();
  const STRUCT = new Set(["contains", "alignment", "produces", "drives", "supports", "generated_by", "derives"]);
  links.forEach((link) => {
    const rel = cleanText(link.relation || link.type);
    if (!STRUCT.has(rel)) return;
    const from = linkEndpointId(link.source);
    const to = linkEndpointId(link.target);
    if (!from || !to) return;
    if (!children.has(from)) children.set(from, []);
    children.get(from).push(to);
  });
  const mass = new Map();
  const countFrom = (rootId) => {
    const seen = new Set([rootId]);
    const stack = [rootId];
    let n = 0;
    while (stack.length) {
      const id = stack.pop();
      (children.get(id) || []).forEach((c) => {
        if (seen.has(c)) return;
        seen.add(c);
        n += 1;
        stack.push(c);
      });
    }
    return n;
  };
  nodes.forEach((node) => mass.set(node.id, countFrom(node.id)));
  return mass;
}

function graph3DData(payload, nodes, focusGoalId = null) {
  // Keep only nodes that belong in the galaxy (the 7 tree-roles). Sand renders as
  // the source spiral; empty-role types (health/gap/next_action/feedback/capacity
  // /agent_run) have their own dashboard UI and must NOT appear as stray orbs.
  const realTreeNodes = galaxyTreeNodes(nodes);
  // Adopt orphan projects/leaves/fruit under a synthetic "Other" goal so loose
  // work orbits a labelled hub instead of a giant ring around the North Star.
  const { nodes: allTreeNodes, payload: galaxyPayload } = buildGalaxyInputs(payload, realTreeNodes);
  const { positions, orbits, nodeOrbits, constellations, focusVisibleIds } = growthGalaxyLayout(
    galaxyPayload,
    allTreeNodes,
    focusGoalId,
  );
  // In focused mode only the goal's own sub-galaxy (+ the skill constellations as
  // the outer reference) is rendered; everything else is excluded.
  const treeNodes = focusVisibleIds
    ? allTreeNodes.filter((node) => focusVisibleIds.has(node.id))
    : allTreeNodes;
  const visibleIds = new Set(treeNodes.map((node) => node.id));
  const links = asArray(galaxyPayload.graph.edges)
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
  // Subtree mass drives goal size so a direction sun always dominates its swarm.
  const mass = subtreeMassByNode(links, treeNodes);
  // Tasks that have at least one evidence (fruit) attached become "produced"
  // overview indicators: in overview mode the per-task comet is too noisy so
  // these tasks get a faint static halo instead — preserves the
  // "produced evidence" semantic without the visual noise.
  const tasksWithEvidence = new Set();
  if (!focusGoalId) {
    const leafIdSet = new Set(treeNodes.filter((n) => n.role === "leaf").map((n) => n.id));
    asArray(galaxyPayload.graph.edges).forEach((edge) => {
      const rel = edge.relation || edge.type;
      if (rel === "generated_by" && leafIdSet.has(edge.from)) {
        tasksWithEvidence.add(edge.from);
      }
    });
  }
  return {
    nodes: treeNodes.map((node) => {
      const pos = positions.get(node.id) || { x: 0, y: DIRECTION_Y, z: 0 };
      const nodeDegree = degree.get(node.id) || 0;
      const isStar = node.role === "star";
      const isGoal = node.role === "direction";
      const weight = nodeVisualWeight(node);
      // Goals: size by how much work hangs under them (subtree mass), so the sun
      // grows with its system and never shrinks below an orbiting project. Size
      // encodes IMPORTANCE/mass only — derived PROJECT-completion progress is
      // shown by a separate progress ARC around the goal (see _addGoalProgressArc
      // in galaxy_scene.js), not by size, so the two channels stay independent.
      // Other roles keep the modest degree-based size, clamped well under the goal
      // band so the hierarchy goal ≫ project > task reads at a glance.
      const val = isGoal
        ? Math.min(18, 11 + Math.sqrt(mass.get(node.id) || 0) * 2.2) * (weight.radius || 1)
        : Math.min(
            9,
            (isStar ? 3 : 5) + Math.min(7, nodeDegree) + (node.isPrimary ? 3 : 0) + (node.placeholder ? -1 : 0),
          ) * (weight.radius || 1);
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
          ? (STAR_STATUS_EMISSIVE[cleanText(node.status)] ?? STAR_STATUS_EMISSIVE.locked) * weight.emissive
          : 0,
        val: Math.max(3, val),
        degree: nodeDegree,
        visualWeight: weight,
        // Tier-3 evidence orbits its task as a moon → rendered small + bright.
        moon: (nodeOrbits.get(node.id) || {}).tier === 3,
        // Overview-only flag: this task has at least one evidence attached.
        // Used by galaxy_scene to add a small static halo without the per-task
        // comet (which only appears in focused mode).
        hasEvidence: tasksWithEvidence.has(node.id),
      };
    }),
    links,
    orbits,
    nodeOrbits: Object.fromEntries(nodeOrbits),
    constellations: constellations || [],
  };
}

// Color for a star-tree node: stars tint by brightness, others by role.
function starTreeColor(node) {
  if (node.placeholder || node.implemented === false) {
    return "#a6b2ad";
  }
  if (node.role === "star") {
    return skillCategoryColor(node);
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
  const weight = node.visualWeight || nodeVisualWeight(node);
  const opacity = selected ? Math.min(1, weight.opacity + 0.16) : weight.opacity;
  const group = new THREE.Group();

  // Stars: small, bright spheres whose emissive tracks skill status. No label
  // (82 of them) unless selected — the dome reads as a sky, not a tag cloud.
  if (node.role === "star") {
    const rawEmissive = Number.isFinite(node.starEmissive) ? node.starEmissive : STAR_STATUS_EMISSIVE.locked;
    // Floor keeps locked stars visible as faint points so the dome's shape always
    // reads; it stays below the bloom threshold so they don't glow.
    const baseEmissive = Math.max(STAR_EMISSIVE_FLOOR, rawEmissive);
    const radius = Math.max(2.2, 1.9 + baseEmissive * 3.4) * (selected ? 1.8 : 1) * weight.radius;
    const material = new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: selected ? Math.max(0.85, baseEmissive + 0.4) : baseEmissive,
      metalness: 0.0,
      roughness: 0.5,
      transparent: true,
      opacity: Math.min(1, (0.66 + baseEmissive * 0.55) * (selected ? 1 : weight.opacity)),
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

  // Claims read as a soft willow-catkin glow: a warm core ringed by low-opacity
  // drifting puffs. Deliberately restrained — the core stays below the bloom
  // threshold so it shimmers without stealing focus from the tree or stars.
  if (node.role === "constellation") {
    const warm = new THREE.Color(node.placeholder ? "#cdd6c9" : "#ecdca6");
    const coreRadius = Math.max(2.2, Math.sqrt(Math.max(1, node.val || 5)) * (selected ? 1.4 : 1.05)) * weight.radius;
    const coreMaterial = new THREE.MeshStandardMaterial({
      color: warm,
      emissive: warm,
      // Below bloom threshold (0.62) at rest; only a selected claim blooms.
      emissiveIntensity: selected ? 0.85 : 0.46,
      roughness: 0.5,
      metalness: 0.0,
      transparent: true,
      opacity: node.placeholder ? Math.min(opacity, 0.5) : Math.min(1, opacity + 0.04),
    });
    group.add(new THREE.Mesh(new THREE.SphereGeometry(coreRadius * 0.5, 14, 12), coreMaterial));

    // Catkin halo: a handful of faint puffs scattered deterministically around
    // the core; the breathing loop drifts them for a floating-down feel.
    const puffCount = node.placeholder ? 5 : 7;
    const puffMaterial = new THREE.MeshStandardMaterial({
      color: warm,
      emissive: warm,
      emissiveIntensity: 0.22,
      roughness: 0.85,
      transparent: true,
      opacity: node.placeholder ? 0.18 : 0.3,
      depthWrite: false,
    });
    for (let i = 0; i < puffCount; i += 1) {
      const puff = new THREE.Mesh(new THREE.SphereGeometry(coreRadius * 0.34, 8, 8), puffMaterial);
      const u = hashUnit(`${node.id}:pf${i}`);
      const v = hashUnit(`${node.id}:pg${i}`);
      const ang = u * Math.PI * 2;
      const rad = coreRadius * (0.9 + v * 1.3);
      puff.position.set(
        Math.cos(ang) * rad,
        (hashUnit(`${node.id}:ph${i}`) - 0.5) * coreRadius * 1.6,
        Math.sin(ang) * rad,
      );
      puff.userData.role = "constellation";
      puff.userData.basePos = puff.position.clone();
      puff.userData.phase = u * Math.PI * 2;
      group.add(puff);
    }
    if (selected || !node.placeholder) {
      group.add(createLabelSprite(node.label || node.id, "#ecdca6", selected));
    }
    return group;
  }

  if (node.role === "fruit") {
    const baseRadius = Math.max(2.6, Math.sqrt(Math.max(1, node.val || 5)) * (selected ? 1.32 : 1.02)) * weight.radius;
    const petalColor = new THREE.Color(color).lerp(new THREE.Color("#f7d7c8"), node.placeholder ? 0.46 : 0.22);
    const petalMaterial = new THREE.MeshStandardMaterial({
      color: petalColor,
      emissive: petalColor,
      emissiveIntensity: (selected ? 0.28 : 0.1) * weight.emissive,
      roughness: 0.72,
      metalness: 0.02,
      transparent: true,
      opacity: node.placeholder ? Math.min(opacity, 0.34) : opacity,
      depthWrite: false,
    });
    const centerMaterial = new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: (selected ? 0.32 : 0.13) * weight.emissive,
      roughness: 0.55,
      transparent: true,
      opacity: node.placeholder ? Math.min(opacity + 0.08, 0.5) : Math.min(1, opacity + 0.04),
    });
    const petals = node.placeholder ? 5 : 6;
    for (let i = 0; i < petals; i += 1) {
      const angle = (i / petals) * Math.PI * 2;
      const petal = new THREE.Mesh(new THREE.SphereGeometry(baseRadius * 0.72, 12, 10), petalMaterial);
      petal.scale.set(1.35, 0.62, 0.32);
      petal.position.set(Math.cos(angle) * baseRadius * 0.72, Math.sin(angle) * baseRadius * 0.72, 0);
      petal.rotation.z = angle;
      group.add(petal);
    }
    group.add(new THREE.Mesh(new THREE.SphereGeometry(baseRadius * 0.48, 14, 12), centerMaterial));
    if (selected) {
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(baseRadius * 1.42, Math.max(0.18, baseRadius * 0.045), 10, 48),
        new THREE.MeshBasicMaterial({ color: "#ffffff", transparent: true, opacity: 0.9 }),
      );
      ring.rotation.x = Math.PI / 2;
      group.add(ring);
    }
    if (selected || !node.placeholder) {
      group.add(createLabelSprite(node.label || node.id, color, selected));
    }
    return group;
  }

  const radius = Math.min(
    selected ? 8.5 : 6.2,
    Math.max(3.2, Math.sqrt(Math.max(1, node.val || 5)) * (selected ? 1.7 : 1.32) * weight.radius),
  );
  const geometry = node.placeholder || node.implemented === false
    ? new THREE.OctahedronGeometry(radius, 1)
    : new THREE.SphereGeometry(radius, 22, 18);
  const material = new THREE.MeshStandardMaterial({
    color,
    emissive: color,
    // Keep tree nodes below the bloom threshold so they read as distinct
    // colored beads against the night sky rather than a glare.
    emissiveIntensity: (selected ? 0.34 : 0.14) * weight.emissive,
    metalness: 0.12,
    roughness: 0.62,
    transparent: true,
    opacity,
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
  // Frame the tree body (trunk/goals/projects/leaves/fruit/claims) and let the
  // 82-skill dome arc out past the top of the viewport, so the tree fills the
  // frame instead of being shrunk by the wide star sphere.
  graph?.zoomToFit?.(duration, 36, (n) => Boolean(n?.role) && n.role !== "star");
}

function graph3DLinkWidth(link, selectedNodeId) {
  const base = EDGE_WIDTHS[link.relation] || 1.1;
  if (graph3DSelectedLink(link, selectedNodeId)) {
    return Math.max(1.35, base * 1.4);
  }
  return Math.max(0.45, base * 0.58);
}

// Legend keyed to the star-tree's eight visual roles (trunk/direction/branch/
// leaf/fruit/star/constellation/sand) — the vocabulary the tree actually speaks,
// not the legacy layer/relation taxonomy it replaced.
function Graph3DLegend({ payload, graphData, selectedNodeId = "", onSelectNode }) {
  const ui = payload.ui;
  // Replace the static role swatches with the real North Star + goals as
  // clickable chips: clicking one selects + focuses that node in 3D (the scene
  // then dives into the goal's subsystem). This makes the bottom-left corner an
  // actual navigator instead of a colour key.
  const nodes = graphData.nodes;
  const northStar = nodes.find((node) => node.role === "trunk");
  const goals = nodes
    .filter((node) => node.role === "direction")
    .sort((a, b) => cleanText(a.label || a.id).localeCompare(cleanText(b.label || b.id)));
  const LEGEND_STORAGE_KEY = "nblane.graph3d.legend.opened";
  const [encodingOpen, setEncodingOpen] = useState(() => {
    try {
      return window.localStorage.getItem(LEGEND_STORAGE_KEY) === "0";
    } catch (e) {
      return false;
    }
  });
  const toggleEncoding = () => {
    setEncodingOpen((current) => {
      const next = !current;
      try {
        window.localStorage.setItem(LEGEND_STORAGE_KEY, next ? "0" : "1");
      } catch (e) {
        // ignore — privacy modes block storage
      }
      return next;
    });
  };
  if (!northStar && !goals.length) {
    return null;
  }
  const Chip = ({ node, kind }) => {
    const selected = node.id === selectedNodeId;
    return (
      <button
        type="button"
        className={`hd-graph3d-nav-chip ${kind}${selected ? " selected" : ""}`}
        data-action="select-node"
        data-source="graph-legend"
        data-node-id={node.id}
        aria-pressed={selected}
        title={cleanText(node.label || node.id)}
        onClick={() => onSelectNode?.(node.id)}
      >
        <i style={{ background: node.color || ROLE_COLORS[node.role] || "#9fb29c" }} />
        <span>{cleanText(node.label || node.id)}</span>
      </button>
    );
  };
  return (
    <div className="hd-graph3d-legend hd-graph3d-nav">
      {northStar ? (
        <div className="hd-graph3d-nav-group">
          <span className="hd-graph3d-nav-label">{label(ui, "dashboard_node_north_star", "North Star")}</span>
          <Chip node={northStar} kind="trunk" />
        </div>
      ) : null}
      {goals.length ? (
        <div className="hd-graph3d-nav-group">
          <span className="hd-graph3d-nav-label">{label(ui, "dashboard_active_goals_title", "Goals")}</span>
          <div className="hd-graph3d-nav-chips">
            {goals.map((node) => (
              <Chip key={node.id} node={node} kind="direction" />
            ))}
          </div>
        </div>
      ) : null}
      <div className={`hd-graph3d-nav-group hd-graph3d-encoding ${encodingOpen ? "open" : ""}`}>
        <button
          type="button"
          className="hd-graph3d-encoding-toggle"
          onClick={toggleEncoding}
          aria-expanded={encodingOpen}
        >
          <span>{label(ui, "dashboard_graph_legend_encoding", "What the visuals mean")}</span>
          <em>{encodingOpen ? "▾" : "▸"}</em>
        </button>
        {encodingOpen ? (
          <ul
            className="hd-graph3d-encoding-list"
            onWheel={(e) => e.stopPropagation()}
          >
            <li><b>{label(ui, "dashboard_graph_legend_size", "Size")}</b> · {label(ui, "dashboard_graph_legend_size_desc", "subtree mass / scope")}</li>
            <li><b>{label(ui, "dashboard_graph_legend_brightness", "Brightness")}</b> · {label(ui, "dashboard_graph_legend_brightness_desc", "mastery (skills) / lit by North Star (goals)")}</li>
            <li><b>{label(ui, "dashboard_graph_legend_arc", "Progress arc")}</b> · {label(ui, "dashboard_graph_legend_arc_desc", "derived goal completion (mean of project completion)")}</li>
            <li><b>{label(ui, "dashboard_graph_legend_grey", "Grey / frozen")}</b> · {label(ui, "dashboard_graph_legend_grey_desc", "stalled or archived/paused goal")}</li>
            <li><b>{label(ui, "dashboard_graph_legend_comet", "Comet trail")}</b> · {label(ui, "dashboard_graph_legend_comet_desc", "evidence under a task (presence = produced)")}</li>
            <li><b>{label(ui, "dashboard_graph_legend_octahedron", "Octahedron")}</b> · {label(ui, "dashboard_graph_legend_octahedron_desc", "scaffolding / placeholder node")}</li>
            <li className="hint">{label(ui, "dashboard_graph_legend_hint", "Click any goal chip to dive in; click empty space to zoom out.")}</li>
          </ul>
        ) : null}
      </div>
    </div>
  );
}

// Build the sand particle field (sources / daily work / research). Sand nodes
// are clustered by theme (tags → goal_refs → kind) and rendered as one
// THREE.Points cloud — atmosphere, not clickable nodes. Returns {points,
// clusters} where clusters carry the member items for hover aggregation.
// The sources form their own spiral galaxy floating below the main growth
// galaxy: each research theme (tag) is a spiral arm, lit sources burn bright,
// placeholder/inbox ones are faint dust. Returns { points, clusters } where
// clusters carry members + a center for hover aggregation.
const SOURCE_GALAXY_Y = -175; // sits clearly below the main galaxy

// Palette for research-source kinds (paper/course/blog/...). Deterministic by
// kind so a kind always gets the same comet colour.
const RESEARCH_KIND_COLORS = ["#8fb8ff", "#76d0c0", "#f0c86a", "#e68ab3", "#9bd97a", "#c6a6ff", "#f09a72", "#84cbd8"];

// Build the research meteor-shower model from sand (source) nodes: count real
// papers, group by kind, assign each a colour, and emit one comet per source.
function researchShowerData(sandNodes) {
  const sources = (sandNodes || []).filter(
    (n) =>
      cleanText(n.type) === "source" &&
      !n.placeholder &&
      n.implemented !== false &&
      n.id !== "source:inbox" && // the inbox is an aggregate, not a paper
      !cleanText(n.id).includes(":inbox"),
  );
  const kindOf = (n) => cleanText(n.metric) || cleanText(asObject(n.meta).kind) || "paper";
  const tagOf = (n) => asArray(asObject(n.meta).tags).map((t) => cleanText(t)).find(Boolean) || "";
  // Group by tag (research theme) when present, else by kind — that's the
  // "种类" the user wants the shower bucketed by.
  const bucketOf = (n) => tagOf(n) || kindOf(n);
  const buckets = [...new Set(sources.map(bucketOf))].sort();
  const colorOf = new Map(buckets.map((b, i) => [b, RESEARCH_KIND_COLORS[i % RESEARCH_KIND_COLORS.length]]));
  // Title riding the comet: per the owner-facing privacy policy the real source
  // title now ships even when `locked` (it's the user's own workspace), so show
  // the paper name directly. Fall back to the research theme/kind only when the
  // payload genuinely carries no usable title (the label is just the id, or a
  // "私密来源 · id" placeholder from an older payload).
  const titleOf = (n) => {
    const t = cleanText(n.label);
    const id = cleanText(n.id);
    const isPlaceholder = !t || id.includes(t) || /^私密来源|·\s/.test(t);
    return isPlaceholder ? tagOf(n) || kindOf(n) : t.slice(0, 40);
  };
  const meteors = sources.map((n) => ({
    id: n.id,
    title: titleOf(n),
    color: colorOf.get(bucketOf(n)),
  }));
  return {
    count: sources.length,
    kinds: buckets.map((b) => ({ key: b, color: colorOf.get(b), count: sources.filter((n) => bucketOf(n) === b).length })),
    meteors,
  };
}

// Build one comet instance with its own diagonal trajectory. Each meteor tilts by
// a per-instance angle (`--ang`) so the streak + tail ride a varied diagonal, and
// carries its own flight duration (speed) and tail length. Deterministic per
// (source, tag) via hashUnit so a given comet always flies the same path.
const METEOR_MAX_ACTIVE = 44; // bound concurrent DOM nodes (burst can be dense)
function makeMeteor(src, tag, seq) {
  const h = (k) => hashUnit(`${src.id}:${tag}:${k}`);
  const dir = h("d") < 0.5 ? "ltr" : "rtl";
  const top = 4 + h("t") * 72; // 4..76% down the stage
  const ang = (h("a") - 0.5) * 54; // -27..27° diagonal tilt
  const dur = 2.0 + h("v") * 1.8; // 2.0..3.8s flight (speed variety)
  const tail = 78 + h("l") * 92; // 78..170px tail length
  return {
    ...src,
    key: `${tag}:${seq}`,
    dir,
    flightMs: dur * 1000,
    style: {
      color: src.color,
      top: `${top}%`,
      "--ang": `${ang}deg`,
      "--tail": `${tail}px`,
      animationDuration: `${dur}s`,
    },
  };
}

// The comet field: papers streak across the stage on varied diagonal paths. A
// calm ambient stream trickles a few at a time; the "流星雨" toolbar button fires
// a dense burst (burstSignal bumps each click). Each comet carries its source's
// title and self-removes after its flight so the DOM stays light. The paper/theme
// counts live in the right data panel (ResearchStatsPanel), not here.
function ResearchShower({ research, burstSignal = 0 }) {
  const [active, setActive] = useState([]);
  const timersRef = useRef(new Set());
  const seqRef = useRef(0);

  // Clear every pending timer on unmount (no setState after unmount).
  useEffect(
    () => () => {
      timersRef.current.forEach((id) => window.clearTimeout(id));
      timersRef.current.clear();
    },
    [],
  );

  const meteors = research && research.meteors ? research.meteors : [];

  const launch = (m) => {
    seqRef.current += 1;
    setActive((cur) => [...cur, m].slice(-METEOR_MAX_ACTIVE));
    const rm = window.setTimeout(() => {
      setActive((cur) => cur.filter((x) => x.key !== m.key));
      timersRef.current.delete(rm);
    }, m.flightMs + 200);
    timersRef.current.add(rm);
  };

  // Ambient sparse stream.
  useEffect(() => {
    if (!meteors.length) {
      setActive([]);
      return undefined;
    }
    let alive = true;
    let idx = 0;
    let timer = 0;
    const spawn = () => {
      if (!alive) return;
      const src = meteors[idx % meteors.length];
      idx += 1;
      launch(makeMeteor(src, `amb${idx}`, seqRef.current));
      const gap = 3200 + hashUnit(`amb${idx}:g`) * 9000; // 3.2–12.2s, varying
      timer = window.setTimeout(spawn, gap);
      timersRef.current.add(timer);
    };
    timer = window.setTimeout(spawn, 300); // first comet appears promptly
    timersRef.current.add(timer);
    return () => {
      alive = false;
      window.clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [research]);

  // Burst: a dense shower fired by the toolbar button (burstSignal increments).
  useEffect(() => {
    if (!burstSignal || !meteors.length) return undefined;
    const n = Math.min(meteors.length, 18);
    for (let i = 0; i < n; i += 1) {
      const src = meteors[(i * 5 + burstSignal) % meteors.length];
      const delay = hashUnit(`burst${burstSignal}:${i}:s`) * 1700; // staggered 0–1.7s
      const t = window.setTimeout(() => {
        launch(makeMeteor(src, `b${burstSignal}-${i}`, seqRef.current));
        timersRef.current.delete(t);
      }, delay);
      timersRef.current.add(t);
    }
    return undefined;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [burstSignal]);

  if (!research || !research.count) {
    return null;
  }
  return (
    <div className="hd-research-shower" aria-hidden="true">
      {active.map((m) => (
        <span key={m.key} className={`hd-meteor ${m.dir}`} style={m.style}>
          <em className="hd-meteor-label">{m.title}</em>
        </span>
      ))}
    </div>
  );
}

// Research counts moved out of the canvas overlay into the right data column
// (below "Context ready"): N papers · M themes + a colour-coded theme legend.
function ResearchStatsPanel({ research, ui, className = "" }) {
  if (!research || !research.count) {
    return null;
  }
  const panelClassName = ["hd-side-panel", "hd-research-panel", className].filter(Boolean).join(" ");
  return (
    <section className={panelClassName}>
      <header>
        <span className="hd-eyebrow">{label(ui, "dashboard_research_title", "Research")}</span>
        <strong>
          {research.count} {label(ui, "dashboard_research_papers", "papers")} ·{" "}
          {research.kinds.length} {label(ui, "dashboard_research_kinds", "themes")}
        </strong>
      </header>
      <div className="hd-research-panel-kinds">
        {research.kinds.slice(0, 8).map((k) => (
          <span key={k.key}>
            <i style={{ background: k.color }} />
            {k.key} <em>{k.count}</em>
          </span>
        ))}
      </div>
    </section>
  );
}

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
  // Stable arm order so the spiral doesn't reshuffle between renders.
  const clusters = [...clustersByKey.values()].sort((a, b) => a.key.localeCompare(b.key));
  const armCount = Math.max(1, clusters.length);

  const positions = [];
  const colors = [];
  const sizes = [];
  const basePositions = [];
  const litColor = new THREE.Color("#b8e0ff");
  const dimColor = new THREE.Color("#41597a");
  clusters.forEach((cluster, ci) => {
    // Each theme is a logarithmic spiral arm radiating from the source-galaxy
    // center; members sorted so lit ones sit inner, placeholders trail outward.
    const armBase = (ci / armCount) * Math.PI * 2;
    const members = cluster.nodes.slice().sort((a, b) => {
      const la = a.status === "reading" || a.status === "read" ? 0 : 1;
      const lb = b.status === "reading" || b.status === "read" ? 0 : 1;
      return la - lb || cleanText(a.id).localeCompare(cleanText(b.id));
    });
    const n = Math.max(1, members.length);
    // Approximate arm center for hover (mid of the arm).
    cluster.center = {
      x: Math.cos(armBase + 0.6) * 46,
      y: SOURCE_GALAXY_Y,
      z: Math.sin(armBase + 0.6) * 46,
    };
    members.forEach((node, j) => {
      const t = (j + 1) / n; // 0..1 outward along the arm
      const r = 22 + t * 130;
      const swirl = armBase + t * 3.0; // arm winds as it extends — a clear spiral
      const jx = (hashUnit(`${node.id}:jx`) - 0.5) * 12;
      const jz = (hashUnit(`${node.id}:jz`) - 0.5) * 12;
      const jy = (hashUnit(`${node.id}:jy`) - 0.5) * 10;
      const px = Math.cos(swirl) * r + jx;
      const pz = Math.sin(swirl) * r + jz;
      const py = SOURCE_GALAXY_Y + jy;
      positions.push(px, py, pz);
      basePositions.push(px, py, pz);
      const lit = node.status === "reading" || node.status === "read";
      const placeholder = node.placeholder || node.implemented === false || node.meta?.synthetic;
      const c = (lit && !placeholder ? litColor : dimColor).clone();
      // Tint slightly per-arm so themes are distinguishable.
      c.offsetHSL((ci / armCount) * 0.5 - 0.1, 0, 0);
      colors.push(c.r, c.g, c.b);
      sizes.push(lit && !placeholder ? 30 : 13);
    });
  });

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  geometry.setAttribute("aSize", new THREE.Float32BufferAttribute(sizes, 1));
  const material = new THREE.ShaderMaterial({
    uniforms: { uTex: { value: makeSoftDot() }, uPulse: { value: 1.0 } },
    vertexShader: `
      attribute float aSize;
      varying vec3 vColor;
      uniform float uPulse;
      void main() {
        vColor = color;
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = aSize * uPulse * (300.0 / -mv.z);
        gl_Position = projectionMatrix * mv;
      }
    `,
    fragmentShader: `
      uniform sampler2D uTex;
      varying vec3 vColor;
      void main() {
        vec4 t = texture2D(uTex, gl_PointCoord);
        gl_FragColor = vec4(vColor, 1.0) * t;
      }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    vertexColors: true,
  });
  const points = new THREE.Points(geometry, material);
  points.userData.basePositions = Float32Array.from(basePositions);
  points.userData.isSandField = true;
  return { points, clusters };
}

// Soft round dot texture for the source-galaxy points (mirrors the skill glow).
let _softDot = null;
function makeSoftDot() {
  if (_softDot) return _softDot;
  const s = 64;
  const c = document.createElement("canvas");
  c.width = s;
  c.height = s;
  const ctx = c.getContext("2d");
  const g = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  g.addColorStop(0, "rgba(255,255,255,1)");
  g.addColorStop(0.3, "rgba(255,255,255,0.85)");
  g.addColorStop(0.7, "rgba(255,255,255,0.18)");
  g.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, s, s);
  _softDot = new THREE.CanvasTexture(c);
  _softDot.needsUpdate = true;
  return _softDot;
}

const SAND_PALETTE = ["#9ed3e6", "#7fb8d6", "#b5d9e8", "#82c6c0", "#a7c7e8", "#87aeca"];

function Graph3DView({ payload, nodes, selectedNodeId, onSelectNode, emptyMessage = "", minHeight = GRAPH_3D_MIN_HEIGHT, compact = false, research: researchProp = null }) {
  const ui = payload.ui;
  const wrapRef = useRef(null);
  const canvasHostRef = useRef(null);
  const sceneRef = useRef(null);
  const [sandHover, setSandHover] = useState(null);
  // Bumped each time the "流星雨" button is pressed → fires a dense burst shower.
  const [burstSignal, setBurstSignal] = useState(0);
  // The focused goal drives the sub-galaxy relayout: clicking any node resolves
  // to its owning goal (a project/task/evidence dives into the goal it belongs
  // to); clicking the North Star / Fit / empty space clears it back to overview.
  // Resolve against the augmented inputs so an orphan adopted by the synthetic
  // "Other" goal — and the Other goal itself — focus like any real goal.
  const focusedGoalId = useMemo(() => {
    const { nodes: galaxyNodes, payload: galaxyPayload } = buildGalaxyInputs(payload, galaxyTreeNodes(nodes));
    return ancestorGoalId(galaxyPayload, galaxyNodes, selectedNodeId);
  }, [payload, nodes, selectedNodeId]);
  const graphData = useMemo(() => graph3DData(payload, nodes, focusedGoalId), [payload, nodes, focusedGoalId]);
  // The legend stays an overview (North Star + every goal) even when focused, so
  // its nav chips keep working as the way back out.
  const legendData = useMemo(() => graph3DData(payload, nodes, null), [payload, nodes]);
  const sandNodes = useMemo(() => nodes.filter((node) => node.role === SAND_ROLE), [nodes]);
  // Research sources become a full-stage comet shower (one comet per real paper,
  // coloured by theme). The paper/theme counts render in the right data panel
  // (ResearchStatsPanel), so prefer the parent-provided research object and only
  // compute locally as a fallback.
  const localResearch = useMemo(() => researchShowerData(sandNodes), [sandNodes]);
  const research = researchProp || localResearch;
  const hasNodes = graphData.nodes.length > 0;

  // Latest callbacks/selection without forcing a scene rebuild.
  const onSelectRef = useRef(onSelectNode);
  onSelectRef.current = onSelectNode;

  // Mount the native THREE scene once.
  useEffect(() => {
    const host = canvasHostRef.current;
    if (!host || !hasNodes) {
      return undefined;
    }
    const scene = new GalaxyScene();
    // Debug hook for live motion sampling (Playwright probes etc). No
    // functional impact — just a window reference that the cleanup below
    // unwinds. Safe to keep in production: read-only access by the dev
    // console / test harness, and removed when this view unmounts.
    if (typeof window !== "undefined") {
      window.__nblaneScene = scene;
    }
    const rect = host.getBoundingClientRect();
    scene.mount(host, {
      width: rect.width || 900,
      height: rect.height || minHeight,
      makeLabel: (node, selected) => createLabelSprite(node.label || node.id, node.color || starTreeColor(node), selected),
      makeCatLabel: (text, color) => createLabelSprite(text, color, false),
      onSelect: (id) => onSelectRef.current?.(id),
      onHover: (hover) => {
        if (!hover) {
          setSandHover(null);
          return;
        }
        const best = hover.cluster;
        setSandHover({
          label: best.label,
          count: best.nodes.length,
          items: best.nodes.slice(0, 8).map((node) => ({
            id: node.id,
            title: node.label || node.id,
            kind: cleanText(node.metric) || cleanText(node.type),
          })),
          x: hover.x,
          y: hover.y,
        });
      },
    });
    sceneRef.current = scene;
    return () => {
      scene.dispose();
      sceneRef.current = null;
      if (typeof window !== "undefined" && window.__nblaneScene === scene) {
        delete window.__nblaneScene;
      }
    };
    // Mount only once per stage lifetime; data flows in via the effect below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasNodes, minHeight]);

  // Feed data (rebuilds the tree geometry) whenever the graph changes.
  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene || !hasNodes) {
      return;
    }
    // Sources are no longer a 3D spiral — they fly as the right-edge meteor
    // shower (see ResearchShower). The galaxy stays focused on goals→evidence.
    scene.setData(graphData, null);
    scene.setSelected(selectedNodeId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphData, sandNodes, payload]);

  // Selection highlight + focus.
  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) {
      return;
    }
    scene.setSelected(selectedNodeId);
    const target = graphData.nodes.find((node) => node.id === selectedNodeId);
    if (target) {
      scene.focus(target);
    }
  }, [selectedNodeId, graphData]);

  // Returning to the overview (focused goal cleared): the explicit Fit / empty
  // click fires before the overview data rebuilds, so re-fit once the full galaxy
  // is back in the scene. Runs after the setData effect (declared above).
  const prevFocusRef = useRef(focusedGoalId);
  useEffect(() => {
    const scene = sceneRef.current;
    if (scene && prevFocusRef.current && !focusedGoalId) {
      scene.fit();
    }
    prevFocusRef.current = focusedGoalId;
  }, [focusedGoalId]);

  // Keep the renderer sized to the stage.
  useLayoutEffect(() => {
    const element = wrapRef.current;
    if (!element) {
      return undefined;
    }
    const update = () => {
      const rect = element.getBoundingClientRect();
      const width = Math.max(320, Math.round(element.clientWidth || rect.width || 900));
      const height = Math.max(minHeight, Math.round(element.clientHeight || rect.height || minHeight));
      sceneRef.current?.resize(width, height);
    };
    update();
    const timers = [window.setTimeout(update, 180), window.setTimeout(update, 650)];
    const observer = new ResizeObserver(update);
    observer.observe(element);
    window.addEventListener("resize", update);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", update);
      timers.forEach((id) => window.clearTimeout(id));
    };
  }, [minHeight, hasNodes]);

  const northStarSet = Boolean(payload.northStar?.isSet);
  const goalCount = Math.max(
    payload.activeGoals?.length || 0,
    payload.goalCounts?.total || 0,
  );
  const skeletalState =
    !hasNodes ||
    (!northStarSet && goalCount === 0);

  // Search hooks live up here (before any early return) so React's hook order
  // stays stable across renders — react-hook-order #310 fires the moment a
  // useState appears after a conditional return.
  const [searchQuery, setSearchQuery] = useState("");
  const searchMatches = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return [];
    return graphData.nodes
      .filter((n) => cleanText(n.label || n.id).toLowerCase().includes(q))
      .slice(0, 8);
  }, [searchQuery, graphData]);

  if (skeletalState) {
    // Canvas-internal onboarding: when the user has not yet set a North Star
    // (and therefore the graph is a single empty shell), render a deliberate
    // three-step guide INSIDE the dark canvas instead of an "all layers
    // hidden" placeholder. The three steps map to the activation loop the
    // critique calls out (North Star → goals → resume import).
    return (
      <div className={compact ? "hd-graph3d-stage compact" : "hd-graph3d-stage"} ref={wrapRef}>
        <div className="hd-graph3d-onboarding">
          <span className="hd-graph3d-onboarding-eyebrow">
            {label(ui, "dashboard_canvas_onboarding_eyebrow", "Start here")}
          </span>
          <h3>{label(ui, "dashboard_canvas_onboarding_title", "Build your growth galaxy")}</h3>
          <ol>
            <li className={northStarSet ? "done" : "active"}>
              <strong>1 · {label(ui, "dashboard_canvas_onboarding_step_north_star", "Set your North Star")}</strong>
              <p>{label(ui, "dashboard_canvas_onboarding_step_north_star_hint", "Name the single bright pursuit you want everything to orbit.")}</p>
            </li>
            <li className={!northStarSet ? "" : goalCount === 0 ? "active" : "done"}>
              <strong>2 · {label(ui, "dashboard_canvas_onboarding_step_goal", "Add an active goal")}</strong>
              <p>{label(ui, "dashboard_canvas_onboarding_step_goal_hint", "Each goal becomes a sun. Projects and tasks orbit underneath.")}</p>
            </li>
            <li className={goalCount === 0 ? "" : "active"}>
              <strong>3 · {label(ui, "dashboard_canvas_onboarding_step_resume", "Paste a resume to seed history")}</strong>
              <p>{label(ui, "dashboard_canvas_onboarding_step_resume_hint", "AI extracts evidence + skills; the galaxy fills itself in.")}</p>
            </li>
          </ol>
          {emptyMessage && hasNodes ? (
            <p className="hd-graph3d-onboarding-note">{emptyMessage}</p>
          ) : null}
        </div>
      </div>
    );
  }

  // Keyboard navigation: when the canvas (or any non-input descendant) has
  // focus, arrows / Tab cycle between goal suns + the North Star, Enter dives
  // into the highlighted node (the same as a click), Esc fits back to overview.
  const handleStageKeyDown = (event) => {
    if (event.defaultPrevented) return;
    const target = event.target;
    if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable)) {
      return;
    }
    const navOrder = [];
    const trunk = graphData.nodes.find((n) => n.role === "trunk");
    if (trunk) navOrder.push(trunk.id);
    graphData.nodes
      .filter((n) => n.role === "direction")
      .sort((a, b) => cleanText(a.label || a.id).localeCompare(cleanText(b.label || b.id)))
      .forEach((n) => navOrder.push(n.id));
    if (!navOrder.length) return;
    if (event.key === "Escape") {
      onSelectNode?.("");
      sceneRef.current?.fit();
      event.preventDefault();
      return;
    }
    const currentIdx = navOrder.indexOf(selectedNodeId);
    const step = event.key === "ArrowRight" || event.key === "ArrowDown" || event.key === "Tab" && !event.shiftKey
      ? 1
      : event.key === "ArrowLeft" || event.key === "ArrowUp" || event.key === "Tab" && event.shiftKey
      ? -1
      : 0;
    if (step !== 0) {
      const nextIdx = currentIdx < 0 ? 0 : (currentIdx + step + navOrder.length) % navOrder.length;
      onSelectNode?.(navOrder[nextIdx]);
      event.preventDefault();
      return;
    }
    if (event.key === "Enter" && selectedNodeId) {
      const target = graphData.nodes.find((n) => n.id === selectedNodeId);
      if (target) {
        sceneRef.current?.focus(target);
        event.preventDefault();
      }
    }
  };

  return (
    <div
      className={compact ? "hd-graph3d-stage compact" : "hd-graph3d-stage"}
      ref={wrapRef}
      data-testid="dashboard-3d-graph"
      tabIndex={0}
      onKeyDown={handleStageKeyDown}
    >
      <div className="hd-graph3d-force" ref={canvasHostRef} />
      <ResearchShower research={research} burstSignal={burstSignal} />
      <div className="hd-graph3d-search">
        <input
          type="search"
          placeholder={label(ui, "dashboard_graph_search_placeholder", "Search node…")}
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          aria-label={label(ui, "dashboard_graph_search_aria", "Search graph nodes")}
        />
        {searchMatches.length ? (
          <ul className="hd-graph3d-search-results">
            {searchMatches.map((node) => (
              <li key={node.id}>
                <button
                  type="button"
                  onClick={() => {
                    onSelectNode?.(node.id);
                    sceneRef.current?.focus(node);
                    setSearchQuery("");
                  }}
                >
                  <i style={{ background: node.color || ROLE_COLORS[node.role] || "#9fb29c" }} />
                  <span>{cleanText(node.label || node.id)}</span>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
      <div className="hd-graph3d-toolbar">
        <button
          type="button"
          data-action="graph-fit"
          onClick={() => {
            // Fit returns to the overview, so clear the selection too — otherwise
            // focusedGoalId would re-derive the sub-galaxy on the next render.
            onSelectNode?.("");
            sceneRef.current?.fit();
          }}
        >
          {label(ui, "dashboard_graph_fit", "Fit")}
        </button>
        <button
          type="button"
          data-action="graph-focus-selected"
          disabled={!selectedNodeId}
          onClick={() => {
            const target = graphData.nodes.find((node) => node.id === selectedNodeId);
            if (target) {
              sceneRef.current?.focus(target);
            } else {
              sceneRef.current?.fit();
            }
          }}
        >
          {label(ui, "dashboard_graph_focus_selected", "Focus")}
        </button>
        {research && research.count ? (
          <button
            type="button"
            data-action="graph-meteor-shower"
            title={label(ui, "dashboard_graph_meteor_shower_hint", "Fire a research meteor shower")}
            onClick={() => setBurstSignal((s) => s + 1)}
          >
            {label(ui, "dashboard_graph_meteor_shower", "流星雨")}
          </button>
        ) : null}
      </div>
      <Graph3DLegend payload={payload} graphData={legendData} selectedNodeId={selectedNodeId} onSelectNode={onSelectNode} />
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

function GraphHeroPanel({ payload, embed, selectedNodeId, onSelectNode, onEmit }) {
  const ui = payload.ui;
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
  // Feed the full node set (matching the standalone 8502 ContextCanvas) so the
  // hero shows the complete star tree, not a 42-node curated subset.
  const heroNodes = useMemo(
    () => graphExploreNodes(payload, new Set(), selectedNodeId, "all"),
    [payload, selectedNodeId],
  );
  // Research stats live in the right data panel (below Context ready), not as a
  // canvas overlay. Compute here from the same sand nodes the comet shower uses.
  const research = useMemo(
    () => researchShowerData(heroNodes.filter((node) => node.role === SAND_ROLE)),
    [heroNodes],
  );

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
            <a
              className="hd-graph-hero-fullscreen"
              href={dashboardNodeUrl(embed.standaloneUrl, "")}
              target="_blank"
              rel="noreferrer"
              data-action="open-fullscreen-galaxy"
              title={label(ui, "dashboard_open_fullscreen_galaxy", "Open Fullscreen Galaxy")}
            >
              <span aria-hidden="true">⤢</span>
              {label(ui, "dashboard_open_fullscreen_galaxy", "Open Fullscreen Galaxy")}
            </a>
          ) : null}
        </header>
        <Graph3DView
          payload={payload}
          nodes={heroNodes}
          selectedNodeId={selectedNode?.id || selectedNodeId}
          onSelectNode={onSelectNode}
          research={research}
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
        <ResearchStatsPanel research={research} ui={ui} className="hd-hero-research" />
      </aside>
    </section>
  );
}

function ContextCanvas({ payload, selectedNodeId, onSelectNode, onEmit, onCreateGoal, viewMode, setViewMode, readOnly = false, defaultShowArchived = false, fullBleed = false }) {
  const ui = payload.ui;
  const [hiddenLayers, setHiddenLayers] = useState(() => new Set());
  const [exploreScope, setExploreScope] = useState("all");
  const [exploreQuery, setExploreQuery] = useState("");
  const [showPlaceholders, setShowPlaceholders] = useState(true);
  const [showArchived, setShowArchived] = useState(() => {
    try {
      const stored = window.localStorage.getItem("nblane.context.goalRail.showArchived");
      // The fullscreen standalone page wants history dimmed-but-visible by
      // default (a "hide history to declutter" toggle), while the embed and
      // the goal rail keep the existing hidden-by-default behavior. Only fall
      // back to that default when the user has never touched the toggle.
      return stored === null ? defaultShowArchived : stored === "1";
    } catch (e) {
      return defaultShowArchived;
    }
  });
  const hasExtinguishedGoal = useMemo(
    () => payload.graph.nodes.some(
      (n) => n.type === "goal" && (n.status === "archived" || n.status === "paused"),
    ),
    [payload],
  );
  const filterLayers = useMemo(() => graphLayers(payload), [payload]);
  const insight = useMemo(() => graphInsight(payload), [payload]);
  const data = useMemo(
    () => flowData(payload, hiddenLayers, viewMode, { showArchived }),
    [payload, hiddenLayers, viewMode, showArchived],
  );
  const rawExploreNodes = useMemo(
    () => graphExploreNodes(payload, hiddenLayers, selectedNodeId, exploreScope),
    [payload, hiddenLayers, selectedNodeId, exploreScope],
  );
  const exploreNodes = useMemo(
    () => {
      const filtered = filterExploreNodes(payload, rawExploreNodes, exploreQuery, showPlaceholders);
      if (showArchived) return filtered;
      // Drop extinguished goals AND their subtrees — otherwise the orphaned
      // children get adopted into the synthetic "Other" sun (see graph3DData /
      // buildGalaxyInputs) and the hidden goal's work reappears under "Other".
      const hidden = hiddenArchivedSubtreeIds(payload, showArchived);
      return filtered.filter((n) => !hidden.has(n.id));
    },
    [payload, rawExploreNodes, exploreQuery, showPlaceholders, showArchived],
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

  const viewSwitcher = (
    <div className={fullBleed ? "hd-segmented hd-segmented-overlay" : "hd-segmented"}>
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
  );

  const archivedToggle = hasExtinguishedGoal ? (
    <label className="hd-canvas-archived-toggle">
      <input
        type="checkbox"
        checked={showArchived}
        onChange={(event) => {
          const checked = event.target.checked;
          setShowArchived(checked);
          try {
            window.localStorage.setItem(
              "nblane.context.goalRail.showArchived",
              checked ? "1" : "0",
            );
          } catch (e) {
            // ignore — privacy mode blocks storage
          }
        }}
        data-action="toggle-archived-goals"
      />
      <span>{label(ui, "dashboard_show_archived_goals", "Show archived / paused goals (extinguished stars)")}</span>
    </label>
  ) : null;

  const stage = viewMode === "focus" ? (
    <FocusPathView payload={payload} selectedNodeId={selectedNodeId} onSelectNode={onSelectNode} />
  ) : viewMode === "attention" ? (
    <AttentionCanvasView payload={payload} onSelectNode={onSelectNode} />
  ) : viewMode === "3d" ? (
    <div className={fullBleed ? "hd-explore-canvas fullbleed" : "hd-explore-canvas"}>
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
          {fullBleed ? null : (
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
          )}
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
  );

  if (fullBleed) {
    // The fullscreen /dashboard page wants the galaxy to be the whole page:
    // no header, no filter drawer, no attention summary competing with the
    // stage. The view switcher survives as a small edge overlay (still
    // reachable, still honors ?view= deep-links) instead of a segmented bar.
    return (
      <section className="hd-canvas-panel hd-canvas-panel-fullbleed">
        {viewSwitcher}
        {archivedToggle ? <div className="hd-canvas-archived-toggle-overlay">{archivedToggle}</div> : null}
        {stage}
      </section>
    );
  }

  return (
    <section className="hd-canvas-panel">
      <header>
        <div>
          <span className="hd-eyebrow">{label(ui, "dashboard_graph_eyebrow", "Canvas")}</span>
          <h3>{label(ui, "dashboard_graph_title", "Context Canvas")}</h3>
        </div>
        {viewSwitcher}
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
        {archivedToggle}
      </details>

      <CanvasSetupBanner
        payload={payload}
        insight={insight}
        hiddenLayers={hiddenLayers}
        onEmit={onEmit}
        onCreateGoal={onCreateGoal}
        readOnly={readOnly}
      />

      <AttentionSummary payload={payload} selectedNodeId={selectedNodeId} onSelectNode={onSelectNode} />

      {stage}
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
  // Goal-relevant framing: count the distinct skills the active goals actually
  // care about (via confirmed skill_links). 13/82 stays as the long-tail
  // overview underneath; the centre figure becomes "lit goal-relevant / total
  // goal-relevant" so the denominator is decision-relevant.
  const alignment = payload.skillAlignment || {};
  const targetSkillIds = new Set();
  const byGoal = alignment.byGoal || {};
  Object.values(byGoal).forEach((entry) => {
    asArray(entry?.confirmed).forEach((link) => {
      if (link?.nodeId) targetSkillIds.add(link.nodeId);
    });
  });
  asArray(alignment.confirmedLinks).forEach((link) => {
    if (link?.nodeId) targetSkillIds.add(link.nodeId);
  });
  const lockedSet = new Set(
    asArray(payload.skills.target_learning_locked).map(
      (n) => cleanText(n?.id || n?.node_id || n),
    ).filter(Boolean),
  );
  const targetLocked = [...targetSkillIds].filter((id) => lockedSet.has(id)).length;
  const targetTotal = targetSkillIds.size;
  // Precise lit count: intersect skill_links node ids with the expert/solid
  // bucket from payload.skills.items (already status-bucketed per node). Falls
  // back to targetTotal − targetLocked when items aren't available.
  const litStatusSet = new Set();
  asArray(payload.skills?.items).forEach((item) => {
    const status = cleanText(item?.status);
    if (status === "expert" || status === "solid") {
      const id = cleanText(item?.id);
      if (id) litStatusSet.add(id);
    }
  });
  const targetLit = litStatusSet.size
    ? [...targetSkillIds].filter((id) => litStatusSet.has(id)).length
    : Math.max(0, targetTotal - targetLocked);
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
          {targetTotal > 0 ? (
            <p className="hd-skill-head-subline">
              <strong>{targetLit}/{targetTotal}</strong>{" "}
              {label(ui, "dashboard_skill_target_caption", "goal-relevant skills lit")}
              {targetLocked ? (
                <em>
                  {" · "}
                  {targetLocked}{" "}
                  {label(ui, "dashboard_skill_target_blocked", "blocking the primary goal")}
                </em>
              ) : null}
            </p>
          ) : null}
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
            {targetTotal > 0 ? (
              <em className="hd-skill-ring-secondary">
                {targetLit}/{targetTotal} {label(ui, "dashboard_skill_ring_target_label", "goal-relevant")}
              </em>
            ) : null}
            {Number.isFinite(payload.trends?.deltas?.skills_lit) && payload.trends.deltas.skills_lit !== 0 ? (
              <span className="hd-skill-ring-trend">
                <DeltaChip value={payload.trends.deltas.skills_lit} kindLabel={label(ui, "dashboard_skill_delta_label", "skills lit this week")} />
                <Sparkline
                  series={payload.trends.sparkline?.skills_lit || []}
                  tone={payload.trends.deltas.skills_lit > 0 ? "up" : "down"}
                />
              </span>
            ) : null}
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
  const items = actionQueueItems(payload);
  const [hero, ...rest] = items;
  return (
    <section className={queueClassName}>
      <header>
        <span className="hd-eyebrow">{label(ui, "dashboard_action_queue_title", "Action queue")}</span>
        <strong>{label(ui, "dashboard_action_next_title", "Next: what to do")}</strong>
      </header>
      {hero ? (
        <button
          key={hero.id}
          className={`hd-action-hero ${hero.tone || ""}`}
          type="button"
          data-action="navigate"
          data-dashboard-action={`queue-hero:${hero.id}`}
          data-target={hero.path}
          onClick={() => onEmit(navigationEvent(hero.path))}
        >
          <span className="hd-action-hero-eyebrow">{hero.eyebrow}</span>
          <span className="hd-action-hero-row">
            <strong className="hd-action-hero-title">{hero.title}</strong>
            {Number(hero.count) > 0 ? <em className="hd-action-hero-count">{hero.count}</em> : null}
            {(() => {
              const deltas = payload.trends?.deltas || {};
              const key = hero.id === "focus" ? "kanban_done" : hero.id === "evidence" ? "evidence_total" : null;
              if (!key) return null;
              return <DeltaChip value={deltas[key]} kindLabel={label(ui, "dashboard_action_hero_delta_label", "this week")} />;
            })()}
          </span>
          {hero.why ? <span className="hd-action-hero-why">{hero.why}</span> : null}
          {hero.detail ? <small className="hd-action-hero-detail">{hero.detail}</small> : null}
        </button>
      ) : null}
      <div className="hd-action-rest">
        {rest.map((item) => (
          <button
            key={item.id}
            className={`hd-action-chip ${item.tone || ""}`}
            type="button"
            data-action="navigate"
            data-dashboard-action={`queue:${item.id}`}
            data-target={item.path}
            onClick={() => onEmit(navigationEvent(item.path))}
            title={item.why}
          >
            <span className="hd-action-chip-eyebrow">{item.eyebrow}</span>
            <span className="hd-action-chip-title">{item.title}</span>
            {Number(item.count) > 0 ? <em className="hd-action-chip-count">{item.count}</em> : null}
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
  const payloadInput = args.payload || {};
  const payloadRevision = payloadInput.revision || payloadInput.profile || "";
  const payload = useMemo(
    () => normalizePayload(payloadInput),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [payloadRevision],
  );
  const requestedNodeId = useMemo(() => initialDashboardNodeId(), []);
  const [selectedNodeId, setSelectedNodeId] = useState(() => requestedNodeId);
  // The deep-linked ?node= is a one-shot: it seeds the initial selection, but
  // once the user closes the drawer (or picks another node) it must not be
  // re-applied, otherwise the auto-select effect keeps snapping the selection
  // back to it and the drawer cannot be closed.
  const deepLinkConsumedRef = useRef(false);
  const [goalEditor, setGoalEditor] = useState(null);
  const [viewMode, setViewMode] = useState(() => initialDashboardViewMode(args));
  const [resumeIngestOpen, setResumeIngestOpen] = useState(false);
  const [profileContextOpen, setProfileContextOpen] = useState(false);
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

  const fullBleedStandalone = args.standalone && !args.embed;
  useEffect(() => {
    const availableIds = new Set(payload.graph.nodes.map((node) => node.id));
    if (requestedNodeId && !availableIds.size && selectedNodeId === requestedNodeId) {
      window.setTimeout(() => setFrameHeight(), 0);
      return;
    }
    const requestedAvailable =
      !deepLinkConsumedRef.current && requestedNodeId && availableIds.has(requestedNodeId);
    // The fullscreen standalone page keeps the inspector drawer closed by
    // default (the galaxy fills the viewport) rather than auto-selecting a
    // "preferred" node on load — a deep-linked ?node= is the one case that
    // should still populate the selection so the drawer opens on it, but only
    // on first load: once the graph nodes exist we mark the deep link consumed
    // so closing the drawer (selectedNodeId="") is not undone on the next run.
    const nextPreferred = fullBleedStandalone ? null : preferredNode(payload);
    const nextId = availableIds.has(selectedNodeId)
      ? selectedNodeId
      : requestedAvailable
      ? requestedNodeId
      : cleanText(nextPreferred?.id);
    if (availableIds.size) {
      deepLinkConsumedRef.current = true;
    }
    if (nextId !== selectedNodeId) {
      setSelectedNodeId(nextId);
    }
    window.setTimeout(() => setFrameHeight(), 0);
  }, [payload, requestedNodeId, selectedNodeId, fullBleedStandalone]);

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
        const target = standaloneTargetUrl("", args.streamlitBase) || cleanText(args.streamlitBase, "/");
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
    if (args.standalone && !args.embed && typeof window !== "undefined") {
      // Keep the address bar shareable as the user explores: replaceState (not
      // pushState) so the browser Back button exits cleanly to the main app
      // instead of walking through every node the user clicked.
      const url = new URL(window.location.href);
      if (nodeId) {
        url.searchParams.set("node", nodeId);
      } else {
        url.searchParams.delete("node");
      }
      window.history.replaceState(null, "", url);
    }
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

  if (args.standalone && !args.embed) {
    // The fullscreen /dashboard page is a different animal from the embed and
    // in-app hero: the galaxy should fill the viewport instead of sharing
    // space with a permanent inspector column, so the InspectorPanel becomes
    // an on-demand right-side drawer that opens on node select/focus.
    return (
      <main className="hd-shell hd-shell-standalone">
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
          <a href={cleanText(args.streamlitBase, "/")} data-action="open-main-app">
            {label(payload.ui, "dashboard_open_main_app", "Back to app")}
          </a>
        </section>
        <ContextCanvas
          payload={payload}
          selectedNodeId={selectedNodeId}
          onSelectNode={handleSelectNode}
          onEmit={emit}
          onCreateGoal={() => setGoalEditor({ mode: "create" })}
          viewMode={viewMode}
          setViewMode={setViewMode}
          readOnly={readOnlyCanvas}
          defaultShowArchived
          fullBleed
        />
        <HdDrawer
          open={Boolean(selectedNodeId)}
          onClose={() => handleSelectNode("")}
          title={label(payload.ui, "dashboard_graph_title", "Context Canvas")}
        >
          <InspectorPanel
            payload={payload}
            selectedNodeId={selectedNodeId}
            goalEditor={goalEditor}
            setGoalEditor={setGoalEditor}
            onEmit={emit}
            readOnly={readOnlyCanvas}
            embedded
          />
        </HdDrawer>
      </main>
    );
  }

  return (
    <main className={args.embed ? "hd-shell hd-shell-embed" : "hd-shell"}>
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
        onOpenResumeIngest={readOnlyCanvas ? null : () => setResumeIngestOpen(true)}
        onOpenProfileContext={readOnlyCanvas ? null : () => setProfileContextOpen(true)}
        canEditGoals={!readOnlyCanvas}
        canSelectGoals={!readOnlyCanvas}
        showToday={!useDailyGraphHero}
        selectedGoalId={selectedGoalId}
      />
      {inlineGoalEditor}

      {canvasSurface}
      {useDailyGraphHero ? null : <Workbench payload={payload} onEmit={emit} readOnly={readOnlyCanvas} showActionQueue={!useDailyGraphHero} />}
      <ResumeIngestDrawer
        open={resumeIngestOpen}
        onClose={() => setResumeIngestOpen(false)}
        ui={payload.ui}
        resume={payload.resumeIngest}
        onEmit={emit}
      />
      <ProfileContextDrawer
        open={profileContextOpen}
        onClose={() => setProfileContextOpen(false)}
        ui={payload.ui}
        profileContext={payload.profileContext}
        onEmit={emit}
      />
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
    streamlitBase: cleanText(standalone?.streamlitBase),
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

// Without a boundary, any throw during render unmounts the whole tree and the
// iframe paints pure white with no hint of what happened (this is exactly how
// the GOAL_BASE_R temporal-dead-zone crash surfaced). Catch render errors here
// so the user sees a recoverable message + the actual error instead of a blank
// frame, and so we can still report a sane frame height.
class DashboardErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error) {
    // Surface the height so Streamlit does not collapse the iframe to 0px.
    window.setTimeout(() => setFrameHeight(420), 0);
    // eslint-disable-next-line no-console
    console.error("Dashboard render error:", error);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="hd-error-boundary" role="alert">
          <h2>Dashboard failed to render</h2>
          <p>The growth graph hit an error while drawing. Reloading usually clears it.</p>
          <button type="button" onClick={() => window.location.reload()}>
            Reload
          </button>
          <pre className="hd-error-detail">{String(this.state.error?.message || this.state.error)}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

const root = createRoot(document.getElementById("root"));
root.render(
  <DashboardErrorBoundary>
    <App />
  </DashboardErrorBoundary>,
);
