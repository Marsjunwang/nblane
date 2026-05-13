import React, { Suspense, lazy, useEffect, useMemo, useRef, useState } from "react";
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

import "./style.css";
import {
  asArray,
  cleanText,
  goalDisplay,
  goalDraftFromFormData,
  normalizePayload,
} from "./payload.js";
import {
  archiveGoalEvent,
  captureInboxSubmitEvent,
  confirmGoalSkillLinksEvent,
  createGoalSubmitEvent,
  editGoalSubmitEvent,
  manualGoalSkillLinkEvent,
  navigationEvent,
  openProfileContextEvent,
  requestGoalSkillAiMatchEvent,
  requestGoalSkillRuleMatchEvent,
  setPrimaryGoalEvent,
} from "./events.js";

const ForceGraph3D = lazy(() => import("react-force-graph-3d"));

const READY = "streamlit:componentReady";
const SET_VALUE = "streamlit:setComponentValue";
const SET_HEIGHT = "streamlit:setFrameHeight";
const RENDER = "streamlit:render";

const NODE_COLORS = {
  north_star: "#6b4fb3",
  goal: "#256b5d",
  project_case: "#52606d",
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
  claim: "#256b5d",
  output: "#b35a34",
  feedback: "#2f9e73",
  capacity: "#68716f",
  health: "#68716f",
};

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

function sendBack(type, payload) {
  window.parent.postMessage({ isStreamlitMessage: true, type, ...payload }, "*");
}

function setFrameHeight(height) {
  sendBack(SET_HEIGHT, { height: Math.max(620, Math.ceil(height || document.body.scrollHeight || 900)) });
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

function label(ui, key, fallback) {
  return cleanText(ui?.[key], fallback || key);
}

function linesText(value) {
  return asArray(value).map((item) => cleanText(item)).filter(Boolean).join("\n");
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

function nodeColor(node) {
  if (node.placeholder || node.implemented === false) {
    return "#8b9691";
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

function captureDraftFromFormData(formData) {
  const tags = cleanText(formData.get("tags"))
    .split(/[,\n]/)
    .map((tag) => tag.trim())
    .filter(Boolean);
  return {
    title: cleanText(formData.get("title")),
    type: cleanText(formData.get("type"), "note"),
    source: cleanText(formData.get("source")),
    source_url: cleanText(formData.get("source_url")),
    raw_text: cleanText(formData.get("raw_text")),
    goal_id: cleanText(formData.get("goal_id")),
    tags,
  };
}

function goalIdFromNode(node) {
  return cleanText(node?.recordId || (cleanText(node?.id).startsWith("goal:") ? cleanText(node.id).slice(5) : ""));
}

function goalById(payload, goalId) {
  if (!goalId) {
    return null;
  }
  return asArray(payload.activeGoals).find((goal) => goal.id === goalId) || null;
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

function ContextHeader({ payload, onEmit, onCreateGoal, onSelectGoal }) {
  const ui = payload.ui;
  const northStar = payload.northStar;
  const primary = goalDisplay(payload.primaryGoal, ui);
  const activeGoals = asArray(payload.activeGoals);
  const northStarText =
    northStar.locked || northStar.visibility === "private"
      ? label(ui, "north_star_private_display", "Private North Star")
      : cleanText(northStar.displayText, label(ui, "north_star_empty", "No North Star set"));

  return (
    <section className="hd-context-header">
      <div className="hd-context-main">
        <div className="hd-context-north">
          <span className="hd-eyebrow">{label(ui, "north_star_strip_title", "North Star")}</span>
          <strong>{northStarText}</strong>
          <span className="hd-tag">
            {label(ui, `north_star_visibility_${northStar.visibility}`, northStar.visibility)}
          </span>
        </div>
        <div className="hd-context-primary">
          <span className="hd-eyebrow">{label(ui, "dashboard_primary_goal", "Primary goal")}</span>
          <strong>{primary.title}</strong>
          <span>{primary.status ? label(ui, `goal_status_${primary.status}`, primary.status) : label(ui, "goal_no_current", "No current goal set.")}</span>
        </div>
      </div>
      <div className="hd-context-goals">
        <span className="hd-eyebrow">{label(ui, "dashboard_active_goals_title", "Active goals")}</span>
        <div className="hd-goal-orb-row">
          {activeGoals.length ? activeGoals.map((goal) => {
            const display = goalDisplay(goal, ui);
            return (
              <button
                key={goal.id || display.title}
                className={`hd-goal-orb ${goal.isPrimary ? "primary" : ""}`}
                type="button"
                title={`${display.title} · ${goal.isPrimary ? label(ui, "dashboard_primary_goal", "Primary") : label(ui, `goal_status_${display.status}`, display.status || "active")}`}
                onClick={() => onSelectGoal(goal.id)}
              >
                <span className="hd-goal-orb-dot" />
                <strong>{display.title}</strong>
              </button>
            );
          }) : <span className="hd-empty-inline">{label(ui, "goal_no_current", "No current goal set.")}</span>}
        </div>
      </div>
      <div className="hd-context-actions">
        <button className="hd-primary" type="button" onClick={onCreateGoal}>
          {label(ui, "dashboard_add_active_goal", "+ Active Goal")}
        </button>
        <button className="hd-ghost" type="button" onClick={() => onEmit(openProfileContextEvent())}>
          {label(ui, "north_star_edit_action", "Edit Profile Context")}
        </button>
      </div>
    </section>
  );
}

function CanvasNode({ data, selected }) {
  const node = data.node;
  return (
    <div className={`hd-flow-node type-${node.type} ${node.suggested ? "suggested" : ""} ${node.placeholder ? "placeholder" : ""} ${node.implemented === false ? "not-implemented" : ""} ${node.locked ? "locked" : ""} ${selected ? "selected" : ""}`}>
      <Handle type="target" position={Position.Left} className="hd-flow-handle" />
      <span className="hd-node-dot" style={{ background: nodeColor(node) }} />
      <div>
        <strong>{node.label}</strong>
        <span>{node.metric || node.status || node.layer || node.type}</span>
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
    const step = items.length > 3 ? 84 : 102;
    items.forEach((node, index) => {
      positions.set(node.id, { x, y: startY + index * step });
    });
  };
  layers.forEach((layer, index) => {
    place(byLayer.get(layer) || [], index * 236, 68);
  });
  return positions;
}

function flowData(payload) {
  const layers = graphLayers(payload);
  const positions = canvasLayout(payload.graph.nodes, layers);
  const layerCounts = new Map();
  payload.graph.nodes.forEach((node) => {
    layerCounts.set(node.layer, (layerCounts.get(node.layer) || 0) + 1);
  });
  const layerNodes = layers.map((layer, index) => ({
    id: `layer:${layer}`,
    type: "layerHeader",
    position: { x: index * 236, y: 0 },
    data: { label: layerLabel(payload.ui, layer), count: layerCounts.get(layer) || 0 },
    draggable: false,
    selectable: false,
  }));
  const graphNodes = payload.graph.nodes.map((node) => ({
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
      animated: edge.type === "readiness" || edge.relation === "watches",
      className: `hd-flow-edge ${edge.suggested ? "suggested" : ""} ${edge.placeholder ? "placeholder" : ""}`,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: 14,
        height: 14,
      },
      label: edge.relation && edge.relation !== edge.type ? edge.relation : undefined,
      labelStyle: { fill: "#60716b", fontSize: 10, fontWeight: 700 },
      labelBgStyle: { fill: "rgba(255,255,255,.86)" },
      style: edge.suggested || edge.placeholder
        ? { strokeDasharray: "5 5", strokeWidth: 2.1 }
        : { strokeWidth: 2.3 },
    }));
  return { nodes: [...layerNodes, ...graphNodes], edges };
}

function nodeWeight(node) {
  if (node.type === "north_star") {
    return 13;
  }
  if (node.type === "goal") {
    return node.isPrimary ? 11 : 9;
  }
  if (node.type === "skill") {
    return 7.2;
  }
  return 5.6;
}

function ContextCanvas({ payload, selectedNodeId, onSelectNode, viewMode, setViewMode }) {
  const ui = payload.ui;
  const data = useMemo(() => flowData(payload), [payload]);
  const graphRef = useRef(null);
  const [hiddenLayers, setHiddenLayers] = useState(() => new Set());
  const filterLayers = useMemo(
    () => graphLayers(payload),
    [payload],
  );
  const graph3d = useMemo(
    () => {
      const nodes = payload.graph.nodes.filter((node) => !hiddenLayers.has(node.layer));
      const nodeIds = new Set(nodes.map((node) => node.id));
      return {
        nodes: nodes.map((node) => ({ ...node, name: node.label })),
        links: payload.graph.edges
          .filter((edge) => nodeIds.has(edge.from) && nodeIds.has(edge.to))
          .map((edge) => ({
            source: edge.from,
            target: edge.to,
            suggested: edge.suggested,
            placeholder: edge.placeholder,
            relation: edge.relation,
          })),
      };
    },
    [payload, hiddenLayers],
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

  return (
    <section className="hd-canvas-panel">
      <header>
        <div>
          <span className="hd-eyebrow">{label(ui, "dashboard_graph_eyebrow", "Canvas")}</span>
          <h3>{label(ui, "dashboard_graph_title", "Context Canvas")}</h3>
        </div>
        <div className="hd-segmented">
          <button className={viewMode === "canvas" ? "active" : ""} type="button" onClick={() => setViewMode("canvas")}>
            {label(ui, "dashboard_view_canvas", "Canvas")}
          </button>
          <button className={viewMode === "3d" ? "active" : ""} type="button" onClick={() => setViewMode("3d")}>
            {label(ui, "dashboard_view_3d_graph", "3D Graph")}
          </button>
        </div>
      </header>
      {viewMode === "3d" ? (
        <div className="hd-graph3d">
          <p className="hd-graph-note">
            {label(ui, "dashboard_graph_3d_hint", "North Star flows into goals, goals connect to skills and tasks, then evidence and output. Rotate to explore; click any node to inspect.")}
          </p>
          <div className="hd-filter-row">
            {filterLayers.map((layer) => (
              <button
                key={layer}
                className={hiddenLayers.has(layer) ? "" : "active"}
                type="button"
                onClick={() => toggleLayer(layer)}
              >
                {layerLabel(ui, layer)}
              </button>
            ))}
          </div>
          <Suspense fallback={<p className="hd-empty">{label(ui, "dashboard_graph_loading", "Loading graph...")}</p>}>
            <ForceGraph3D
              ref={graphRef}
              graphData={graph3d}
              nodeLabel="label"
              nodeColor={(node) => nodeColor(node)}
              nodeVal={(node) => nodeWeight(node)}
              nodeRelSize={8.4}
              nodeResolution={40}
              linkLabel="relation"
              linkColor={(link) => (link.suggested || link.placeholder ? "rgba(104,113,111,.28)" : "rgba(37,107,93,.55)")}
              linkWidth={(link) => (link.suggested || link.placeholder ? 1.4 : 2.2)}
              linkOpacity={0.72}
              linkDirectionalArrowLength={(link) => (link.suggested || link.placeholder ? 0 : 5)}
              linkDirectionalArrowRelPos={0.98}
              linkDirectionalArrowResolution={24}
              linkDirectionalParticles={(link) => (link.suggested || link.placeholder ? 0 : 2)}
              linkDirectionalParticleWidth={1.8}
              linkDirectionalParticleResolution={16}
              linkDirectionalParticleSpeed={0.006}
              backgroundColor="rgba(255,255,255,0)"
              height={318}
              dagMode="lr"
              dagLevelDistance={128}
              cooldownTicks={80}
              enableNodeDrag={false}
              showNavInfo={false}
              onEngineStop={() => graphRef.current?.zoomToFit?.(450, 16)}
              onNodeClick={(node) => onSelectNode(node.id)}
            />
          </Suspense>
        </div>
      ) : (
        <div className="hd-flow-wrap">
          <ReactFlow
            nodes={data.nodes.map((node) => ({ ...node, selected: node.id === selectedNodeId }))}
            edges={data.edges}
            nodeTypes={NODE_TYPES}
            defaultEdgeOptions={{
              interactionWidth: 18,
            }}
            fitView
            fitViewOptions={{ padding: 0.16 }}
            minZoom={0.35}
            maxZoom={1.6}
            panOnDrag
            zoomOnScroll
            nodesDraggable={false}
            onNodeClick={(_, node) => onSelectNode(node.id)}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#d9e1dd" gap={24} size={1} />
            <Controls showInteractive={false} />
          </ReactFlow>
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
      <label>
        {label(ui, "goal_field_summary", "Summary")}
        <textarea name="summary" defaultValue={cleanText(source.summary)} rows="2" />
      </label>
      <label>
        {label(ui, "goal_field_alignment", "North Star alignment")}
        <textarea name="alignment" defaultValue={cleanText(source.alignment)} rows="2" />
      </label>
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
        <button className="hd-ghost" type="button" onClick={onCancel}>{label(ui, "dashboard_goal_close_form", "Close")}</button>
        <button className="hd-primary" type="submit">{label(ui, "goal_save", "Save goal")}</button>
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
        <button className="hd-ghost" type="button" onClick={() => onEmit(requestGoalSkillRuleMatchEvent(goalId))}>
          {label(ui, "skill_alignment_rule", "Rule match")}
        </button>
        <button className="hd-ghost" type="button" disabled={!payload.ai?.configured} onClick={() => onEmit(requestGoalSkillAiMatchEvent(goalId))}>
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
      <button className="hd-primary full" type="button" disabled={!selectedLinks.length} onClick={() => onEmit(confirmGoalSkillLinksEvent(goalId, selectedLinks.map(linkPayload)))}>
        {label(ui, "skill_alignment_confirm", "Confirm links")}
      </button>
      <div className="hd-manual-row">
        <select value={manualNodeId} onChange={(event) => setManualNodeId(event.currentTarget.value)}>
          <option value="">{label(ui, "skill_alignment_manual_label", "Manual add")}</option>
          {payload.skillAlignment.skillOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
        </select>
        <button className="hd-ghost" type="button" disabled={!manualNodeId} onClick={() => onEmit(manualGoalSkillLinkEvent(goalId, manualNodeId))}>
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
  if (!node.placeholder && node.implemented !== false) {
    return null;
  }
  return (
      <div className="hd-placeholder-box">
      <span className="hd-section-label">{label(ui, "dashboard_inspector_owner_reserved", "Interface reserved")}</span>
      <p>
        {node.implemented === false
          ? label(ui, "dashboard_inspector_placeholder_hint", "This graph node is planned but does not have a backing record yet.")
          : label(ui, "dashboard_source_to_evidence_hint", "This graph node is suggested by the dashboard graph.")}
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

function InspectorPanel({ payload, selectedNodeId, goalEditor, setGoalEditor, onEmit, onSelectNode }) {
  const ui = payload.ui;
  const nodesById = useMemo(() => new Map(payload.graph.nodes.map((node) => [node.id, node])), [payload]);
  const selectedNode = nodesById.get(selectedNodeId) || payload.graph.nodes.find((node) => node.type === "goal") || null;
  const relations = selectedNode ? nodeRelations(payload, selectedNode.id) : [];

  if (goalEditor?.mode === "create") {
    return (
      <aside className="hd-inspector">
        <header><span className="hd-eyebrow">{label(ui, "dashboard_add_active_goal", "Add Active Goal")}</span><h3>{label(ui, "goal_create_title", "Create goal")}</h3></header>
        <GoalForm payload={payload} goal={{ editor: emptyGoalEditor() }} mode="create" onCancel={() => setGoalEditor(null)} onEmit={onEmit} />
      </aside>
    );
  }

  const selectedGoalId = goalIdFromNode(selectedNode);
  const selectedGoal = goalById(payload, selectedGoalId);
  if (goalEditor?.mode === "edit" && selectedGoal) {
    return (
      <aside className="hd-inspector">
        <header><span className="hd-eyebrow">{label(ui, "dashboard_goal_edit_inline", "Edit goal")}</span><h3>{goalDisplay(selectedGoal, ui).title}</h3></header>
        <GoalForm payload={payload} goal={selectedGoal} mode="edit" onCancel={() => setGoalEditor(null)} onEmit={onEmit} />
      </aside>
    );
  }

  if (!selectedNode) {
    return (
      <aside className="hd-inspector">
        <p className="hd-empty">{label(ui, "dashboard_inspector_empty", "Select a node to inspect it.")}</p>
      </aside>
    );
  }

  if (selectedNode.type === "goal" && selectedGoal) {
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
        <div className="hd-action-row">
          {!selectedGoal.locked ? <button className="hd-primary" type="button" onClick={() => setGoalEditor({ mode: "edit", goalId: selectedGoal.id })}>{label(ui, "dashboard_goal_edit_inline", "Edit goal")}</button> : null}
          {!selectedGoal.isPrimary ? <button className="hd-ghost" type="button" onClick={() => onEmit(setPrimaryGoalEvent(selectedGoal.id))}>{label(ui, "dashboard_set_primary", "Set primary")}</button> : null}
          <button className="hd-ghost danger" type="button" onClick={() => onEmit(archiveGoalEvent(selectedGoal.id))}>{label(ui, "dashboard_archive_goal", "Archive")}</button>
        </div>
        {!selectedGoal.locked ? <GoalSkillAlignment payload={payload} goalId={selectedGoal.id} onEmit={onEmit} /> : null}
      </aside>
    );
  }

  return (
    <aside className="hd-inspector">
      <header>
        <span className="hd-eyebrow">{selectedNode.type}</span>
        <h3>{selectedNode.label}</h3>
      </header>
      <div className="hd-inspector-meta">
        {selectedNode.layer ? <span>{layerLabel(ui, selectedNode.layer)}</span> : null}
        {selectedNode.implemented === false ? <span>{label(ui, "dashboard_placeholder_metric", "planned")}</span> : null}
        {selectedNode.metric ? <span>{selectedNode.metric}</span> : null}
        {selectedNode.status ? <span>{selectedNode.status}</span> : null}
      </div>
      <PlaceholderInspector payload={payload} node={selectedNode} relations={relations} />
      <p className="hd-inspector-summary">
        {selectedNode.suggested || selectedNode.placeholder ? label(ui, "skill_alignment_suggested", "suggested") : label(ui, "dashboard_inspector_node_hint", "Open the owner page for details.")}
      </p>
      <div className="hd-action-row">
        {selectedNode.ownerPath && selectedNode.ownerPath !== "profile_context" && selectedNode.implemented !== false ? (
          <button className="hd-primary" type="button" onClick={() => onEmit(navigationEvent(selectedNode.ownerPath))}>{label(ui, "dashboard_open_section", "Open")}</button>
        ) : null}
        {selectedNode.ownerPath === "profile_context" && selectedNode.implemented !== false ? (
          <button className="hd-primary" type="button" onClick={() => onEmit(openProfileContextEvent())}>{label(ui, "north_star_edit_action", "Edit Profile Context")}</button>
        ) : null}
      </div>
      {selectedNode.type === "skill" && selectedNode.implemented !== false ? (
        <button className="hd-ghost full" type="button" onClick={() => onEmit(navigationEvent("pages/2_Gap_Analysis.py"))}>{label(ui, "quick_gap", "Gap Analysis")}</button>
      ) : null}
    </aside>
  );
}

function HomeCaptureForm({ payload, onEmit }) {
  const ui = payload.ui;
  const currentGoalId = primaryGoalId(payload);

  function submit(event) {
    event.preventDefault();
    const draft = captureDraftFromFormData(new FormData(event.currentTarget));
    if (!draft.title) {
      return;
    }
    onEmit(captureInboxSubmitEvent(draft));
    event.currentTarget.reset();
  }

  return (
    <form className="hd-capture-form" onSubmit={submit}>
      <header>
        <span className="hd-eyebrow">{label(ui, "dashboard_today_capture_sources", "Capture / Sources")}</span>
        <strong>{label(ui, "dashboard_capture_title", "Capture source")}</strong>
      </header>
      <label>
        {label(ui, "goal_field_title", "Title")}
        <input name="title" required placeholder={label(ui, "dashboard_capture_title_placeholder", "What did you notice?")} />
      </label>
      <input type="hidden" name="goal_id" value={currentGoalId} />
      <div className="hd-form-row">
        <label>
          {label(ui, "dashboard_capture_type", "Type")}
          <select name="type" defaultValue="note">
            <option value="note">{label(ui, "dashboard_capture_type_note", "Note")}</option>
            <option value="link">{label(ui, "dashboard_capture_type_link", "Link")}</option>
            <option value="resource">{label(ui, "dashboard_capture_type_resource", "Resource")}</option>
            <option value="idea">{label(ui, "dashboard_capture_type_idea", "Idea")}</option>
          </select>
        </label>
        <label>
          {label(ui, "dashboard_capture_source", "Source URL or origin")}
          <input name="source" />
        </label>
      </div>
      <label>
        {label(ui, "dashboard_capture_source", "Source URL or origin")}
        <input name="source_url" type="url" />
      </label>
      <label>
        {label(ui, "dashboard_capture_raw_text", "Note")}
        <textarea name="raw_text" rows="3" />
      </label>
      <label>
        {label(ui, "dashboard_capture_tags", "Tags")}
        <input name="tags" placeholder="project/nblane, flow/learning" />
      </label>
      <button className="hd-primary full" type="submit">{label(ui, "dashboard_capture_submit", "Capture")}</button>
    </form>
  );
}

function TodayLane({ payload, onEmit }) {
  const ui = payload.ui;
  const doing = asArray(payload.kanban.doing);
  const evidenceCandidates = Number(payload.pendingEvidence.done_uncrystallized_count || 0);
  const unlinkedAtomic = Number(payload.pendingEvidence.unlinked_count || 0);
  const health = payload.charts.health;
  const sourceActive = Number(payload.sources.active_total || 0);
  const sourceTitles = asArray(payload.sources.active_titles).map((item) => cleanText(item)).filter(Boolean);
  const gapRisk = Number(payload.skills.evidence_risk_count || 0) + asArray(payload.skills.target_learning_locked).length;
  return (
    <section className="hd-today-lane">
      <div className="hd-today-metrics">
        <article>
          <span className="hd-eyebrow">{label(ui, "dashboard_today_current_focus", "Current focus")}</span>
          <strong>{payload.kanban.doing_total || doing.length || 0}</strong>
          <p>{doing.slice(0, 2).map((item) => cleanText(item.title)).join(" / ") || label(ui, "dashboard_doing_empty", "No Doing tasks yet.")}</p>
        </article>
        <article className="hd-today-capture-card">
          <span className="hd-eyebrow">{label(ui, "dashboard_today_capture_sources", "Capture / Sources")}</span>
          <strong>{sourceActive}</strong>
          <p>{sourceTitles.slice(0, 2).join(" / ") || label(ui, "dashboard_source_inbox_empty", "No source items captured yet.")}</p>
          <HomeCaptureForm payload={payload} onEmit={onEmit} />
        </article>
        <article>
          <span className="hd-eyebrow">{label(ui, "dashboard_today_evidence_review", "Evidence review")}</span>
          <strong>{evidenceCandidates}</strong>
          <p>{label(ui, "dashboard_atomic_evidence_unlinked", "Unlinked atomic rows")}: {unlinkedAtomic}</p>
        </article>
        <article>
          <span className="hd-eyebrow">{label(ui, "dashboard_today_gap_next_action", "Gap / Next action")}</span>
          <strong>{gapRisk}</strong>
          <p>{label(ui, "dashboard_gap_risk_title", "Gap risk")}</p>
        </article>
        <article>
          <span className="hd-eyebrow">{label(ui, "dashboard_today_output_feedback", "Output / Feedback")}</span>
          <strong>{payload.charts.public.draft}</strong>
          <p>{label(ui, "dashboard_public_published", "Published")}: {payload.charts.public.published} · {label(ui, "dashboard_feedback_planned", "Feedback interface reserved.")}</p>
        </article>
      </div>
      <div className="hd-today-actions">
        {payload.quickLinks.map((link) => (
          <button key={link.path} className="hd-ghost" type="button" onClick={() => onEmit(navigationEvent(link.path))}>{cleanText(link.label, link.id)}</button>
        ))}
        <span className="hd-health-inline">{label(ui, "dashboard_health_title", "Health")}: {health.error}/{health.warning}/{health.info}</span>
      </div>
    </section>
  );
}

function Dashboard({ args }) {
  const payload = useMemo(() => normalizePayload(args.payload || {}), [args]);
  const [selectedNodeId, setSelectedNodeId] = useState("");
  const [goalEditor, setGoalEditor] = useState(null);
  const [viewMode, setViewMode] = useState("canvas");

  useEffect(() => {
    const primaryId = primaryGoalId(payload);
    const firstGoalNode = payload.graph.nodes.find((node) => node.type === "goal" && (!primaryId || node.recordId === primaryId));
    if (!selectedNodeId && firstGoalNode) {
      setSelectedNodeId(firstGoalNode.id);
    }
    window.setTimeout(() => setFrameHeight(), 0);
  }, [payload, selectedNodeId]);

  function emit(event) {
    setComponentValue(event);
    window.setTimeout(() => setFrameHeight(), 0);
  }

  function selectGoal(goalId) {
    const node = payload.graph.nodes.find((item) => item.type === "goal" && item.recordId === goalId);
    if (node) {
      setSelectedNodeId(node.id);
      setGoalEditor(null);
    }
  }

  return (
    <main className="hd-shell">
      <ContextHeader
        payload={payload}
        onEmit={emit}
        onCreateGoal={() => setGoalEditor({ mode: "create" })}
        onSelectGoal={selectGoal}
      />
      <div className="hd-canvas-workbench">
        <ContextCanvas
          payload={payload}
          selectedNodeId={selectedNodeId}
          onSelectNode={(nodeId) => {
            setSelectedNodeId(nodeId);
            setGoalEditor(null);
          }}
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
        <InspectorPanel
          payload={payload}
          selectedNodeId={selectedNodeId}
          goalEditor={goalEditor}
          setGoalEditor={setGoalEditor}
          onEmit={emit}
        />
      </div>
      <TodayLane payload={payload} onEmit={emit} />
    </main>
  );
}

function App() {
  const [args, setArgs] = useState({ payload: {}, height: 900 });
  useEffect(() => {
    initStreamlitBridge(setArgs);
  }, []);
  return <Dashboard args={args} />;
}

const root = createRoot(document.getElementById("root"));
root.render(<App />);
