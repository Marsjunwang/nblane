import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";

import "./style.css";
import {
  asArray,
  cleanText,
  goalDisplay,
  goalDraftFromFormData,
  normalizePayload,
} from "./payload.js";
import { goalSubmitEvent, navigationEvent, openSectionEvent } from "./events.js";

const READY = "streamlit:componentReady";
const SET_VALUE = "streamlit:setComponentValue";
const SET_HEIGHT = "streamlit:setFrameHeight";
const RENDER = "streamlit:render";

const STATUS_COLORS = {
  expert: "#2f6fed",
  solid: "#2f9e73",
  learning: "#c88916",
  locked: "#a7b1ad",
};

const NODE_COLORS = {
  goal: "#256b5d",
  skill: "#2f6fed",
  task: "#8b6f20",
  evidence: "#6b4fb3",
  output: "#b35a34",
  health: "#68716f",
};

function sendBack(type, payload) {
  window.parent.postMessage({ isStreamlitMessage: true, type, ...payload }, "*");
}

function setFrameHeight(height) {
  sendBack(SET_HEIGHT, { height: Math.max(520, Math.ceil(height || document.body.scrollHeight || 860)) });
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

function MetricCard({ labelText, value, detail, tone = "" }) {
  return (
    <div className={`hd-metric ${tone ? `tone-${tone}` : ""}`}>
      <span className="hd-metric-label">{labelText}</span>
      <strong>{value}</strong>
      {detail ? <span className="hd-metric-detail">{detail}</span> : null}
    </div>
  );
}

function SkillDonut({ chart, ui }) {
  const counts = chart.counts || {};
  const total = Math.max(0, Number(chart.total) || 0);
  const lit = Math.max(0, Number(chart.lit) || 0);
  const circumference = 100;
  let offset = 25;
  const segments = ["expert", "solid", "learning", "locked"].map((key) => {
    const value = total ? (counts[key] || 0) / total * circumference : 0;
    const segment = { key, value, offset };
    offset -= value;
    return segment;
  });
  return (
    <div className="hd-donut-card">
      <svg viewBox="0 0 42 42" className="hd-donut" aria-hidden="true">
        <circle className="hd-donut-bg" cx="21" cy="21" r="15.915" />
        {segments.map((segment) =>
          segment.value > 0 ? (
            <circle
              key={segment.key}
              className="hd-donut-segment"
              cx="21"
              cy="21"
              r="15.915"
              stroke={STATUS_COLORS[segment.key]}
              strokeDasharray={`${segment.value} ${circumference - segment.value}`}
              strokeDashoffset={segment.offset}
            />
          ) : null
        )}
        <text x="21" y="20.2" textAnchor="middle" className="hd-donut-main">{lit}</text>
        <text x="21" y="25.4" textAnchor="middle" className="hd-donut-sub">/{total || 0}</text>
      </svg>
      <div className="hd-legend">
        {["expert", "solid", "learning", "locked"].map((key) => (
          <span key={key}>
            <i style={{ background: STATUS_COLORS[key] }} />
            {label(ui, `status_${key}`, key)} {counts[key] || 0}
          </span>
        ))}
      </div>
    </div>
  );
}

function StackedBar({ values }) {
  const total = values.reduce((sum, item) => sum + item.value, 0);
  return (
    <div className="hd-stackbar" aria-hidden="true">
      {values.map((item) => (
        <span
          key={item.key}
          style={{
            width: `${total ? Math.max(6, item.value / total * 100) : 0}%`,
            background: item.color,
          }}
        />
      ))}
    </div>
  );
}

function GoalHero({ payload, onEmit }) {
  const ui = payload.ui;
  const goal = payload.goal;
  const display = goalDisplay(goal, ui);
  const editor = goal.editor || {};
  const [editing, setEditing] = useState(!goal.isSet && !goal.locked);
  const statusOptions = goal.statusOptions.length ? goal.statusOptions : ["active", "paused", "completed", "archived"];
  const visibilityOptions = goal.visibilityOptions.length ? goal.visibilityOptions : ["visible", "discreet", "hidden", "private"];

  useEffect(() => {
    setEditing(!goal.isSet && !goal.locked);
  }, [goal.isSet, goal.locked]);

  function submit(event) {
    event.preventDefault();
    const draft = goalDraftFromFormData(new FormData(event.currentTarget));
    onEmit(goalSubmitEvent(draft));
  }

  return (
    <section className="hd-goal-hero">
      <div className="hd-goal-copy">
        <div className="hd-eyebrow">{display.eyebrow}</div>
        <h2>{display.title}</h2>
        {display.summary ? <p>{display.summary}</p> : null}
        <div className="hd-goal-meta">
          {display.status ? <span className={`hd-pill status-${display.status}`}>{label(ui, `goal_status_${display.status}`, display.status)}</span> : null}
          {display.target ? <span className="hd-pill">{label(ui, "goal_strip_target", "Target")}: {display.target}</span> : null}
          {payload.ai?.configured ? <span className="hd-pill">{label(ui, "dashboard_ai_ready", "AI ready")}</span> : <span className="hd-pill muted">{label(ui, "dashboard_ai_not_ready", "AI off")}</span>}
        </div>
        {display.focus.length ? (
          <ul className="hd-focus-list">
            {display.focus.map((item) => <li key={item}>{item}</li>)}
          </ul>
        ) : null}
      </div>
      <div className="hd-goal-actions">
        {goal.locked ? (
          <div className="hd-locked">{label(ui, "goal_private_locked", "This goal is private.")}</div>
        ) : (
          <button className="hd-primary" type="button" onClick={() => setEditing((value) => !value)}>
            {editing ? label(ui, "dashboard_goal_close_form", "Close") : goal.isSet ? label(ui, "dashboard_goal_edit_inline", "Edit goal") : label(ui, "dashboard_goal_create_inline", "Create goal")}
          </button>
        )}
      </div>
      {editing && !goal.locked ? (
        <form className="hd-goal-form" onSubmit={submit}>
          <input name="id" type="hidden" defaultValue={cleanText(editor.id)} />
          <label>
            {label(ui, "goal_field_title", "Title")}
            <input name="title" defaultValue={cleanText(editor.title)} required />
          </label>
          <label>
            {label(ui, "goal_field_label", "Discreet label")}
            <input name="label" defaultValue={cleanText(editor.label)} />
          </label>
          <label>
            {label(ui, "goal_field_status", "Status")}
            <select name="status" defaultValue={cleanText(editor.status, "active")}>
              {statusOptions.map((option) => <option key={option} value={option}>{label(ui, `goal_status_${option}`, option)}</option>)}
            </select>
          </label>
          <label>
            {label(ui, "goal_field_target", "Target date")}
            <input name="target" defaultValue={cleanText(editor.target)} placeholder="YYYY-MM-DD" />
          </label>
          <label className="wide">
            {label(ui, "goal_field_summary", "Summary")}
            <textarea name="summary" defaultValue={cleanText(editor.summary)} rows="2" />
          </label>
          <label>
            {label(ui, "goal_field_target_skills", "Target skills")}
            <textarea name="target_skills" defaultValue={linesText(editor.target_skills)} rows="3" />
          </label>
          <label>
            {label(ui, "goal_field_focus", "Focus")}
            <textarea name="focus" defaultValue={linesText(editor.focus)} rows="3" />
          </label>
          <label className="wide">
            {label(ui, "goal_field_success_criteria", "Success criteria")}
            <textarea name="success_criteria" defaultValue={linesText(editor.success_criteria)} rows="3" />
          </label>
          <details className="wide hd-details">
            <summary>{label(ui, "dashboard_goal_advanced_fields", "Advanced goal fields")}</summary>
            <div className="hd-advanced-grid">
              <label>
                {label(ui, "goal_field_start", "Start date")}
                <input name="start" defaultValue={cleanText(editor.start)} placeholder="YYYY-MM-DD" />
              </label>
              <label>
                {label(ui, "goal_field_ui_visibility", "UI visibility")}
                <select name="ui_visibility" defaultValue={cleanText(editor.ui_visibility, "discreet")}>
                  {visibilityOptions.map((option) => <option key={option} value={option}>{label(ui, `goal_visibility_${option}`, option)}</option>)}
                </select>
              </label>
              <label>
                {label(ui, "goal_field_evidence_refs", "Evidence refs")}
                <textarea name="evidence_refs" defaultValue={linesText(editor.evidence_refs)} rows="3" />
              </label>
              <label>
                {label(ui, "goal_field_task_refs", "Task refs")}
                <textarea name="task_refs" defaultValue={linesText(editor.task_refs)} rows="3" />
              </label>
              <label>
                {label(ui, "goal_field_output_refs", "Output refs")}
                <textarea name="output_refs" defaultValue={linesText(editor.output_refs)} rows="3" />
              </label>
              <label>
                {label(ui, "goal_field_notes", "Notes")}
                <textarea name="notes" defaultValue={cleanText(editor.notes)} rows="3" />
              </label>
            </div>
          </details>
          <label className="hd-checkbox wide">
            <input
              name="include_in_agent_context"
              type="checkbox"
              defaultChecked={editor.include_in_agent_context !== false}
            />
            {label(ui, "goal_field_agent_context", "Include in Agent context")}
          </label>
          <div className="hd-form-actions wide">
            <button className="hd-primary" type="submit">{label(ui, "goal_save", "Save current goal")}</button>
          </div>
        </form>
      ) : null}
    </section>
  );
}

function DoingPanel({ payload, onEmit }) {
  const ui = payload.ui;
  const doing = asArray(payload.kanban.doing);
  return (
    <section className="hd-panel hd-doing">
      <header>
        <div>
          <span className="hd-eyebrow">{label(ui, "dashboard_metric_doing", "Doing")}</span>
          <h3>{label(ui, "dashboard_doing_title", "This week's Doing")}</h3>
        </div>
        <button className="hd-ghost" type="button" onClick={() => onEmit(navigationEvent("pages/3_Kanban.py"))}>
          {label(ui, "quick_kanban", "Kanban")}
        </button>
      </header>
      {doing.length ? (
        <div className="hd-task-list">
          {doing.map((item, index) => (
            <article className="hd-task" key={`${item.title}-${index}`}>
              <strong>{cleanText(item.title)}</strong>
              <div className="hd-task-meta">
                {item.started_on ? <span>{label(ui, "dashboard_doing_started", "started {date}").replace("{date}", item.started_on)}</span> : null}
                {item.tags ? <span>{item.tags}</span> : null}
              </div>
              {item.blocked_by ? <span className="hd-blocked">{label(ui, "dashboard_doing_blocked", "Blocked by: {blocked}").replace("{blocked}", item.blocked_by)}</span> : null}
            </article>
          ))}
        </div>
      ) : (
        <p className="hd-empty">{label(ui, "dashboard_doing_empty", "No Doing tasks yet.")}</p>
      )}
    </section>
  );
}

function OverviewPanel({ payload }) {
  const ui = payload.ui;
  const charts = payload.charts;
  const health = charts.health;
  const evidenceTotal = charts.evidence.doneUncrystallized + charts.evidence.unlinked;
  return (
    <section className="hd-panel hd-overview">
      <header>
        <div>
          <span className="hd-eyebrow">{label(ui, "dashboard_status_overview", "Status overview")}</span>
          <h3>{label(ui, "dashboard_overview_map_title", "Map of now")}</h3>
        </div>
      </header>
      <SkillDonut chart={charts.skills} ui={ui} />
      <div className="hd-metric-grid">
        <MetricCard labelText={label(ui, "dashboard_metric_pending_evidence", "Evidence")} value={evidenceTotal} detail={`${label(ui, "dashboard_done_uncrystallized", "Done")}: ${charts.evidence.doneUncrystallized}`} />
        <MetricCard labelText={label(ui, "dashboard_public_drafts", "Drafts")} value={charts.public.draft} detail={`${label(ui, "dashboard_public_published", "Published")}: ${charts.public.published}`} />
        <MetricCard labelText={label(ui, "dashboard_health_title", "Health")} value={`${health.error}/${health.warning}/${health.info}`} detail={label(ui, "dashboard_metric_health_help", "Errors / warnings / info")} tone={health.error ? "danger" : health.warning ? "warn" : "ok"} />
      </div>
      <StackedBar
        values={[
          { key: "published", value: charts.public.published, color: "#2f9e73" },
          { key: "draft", value: charts.public.draft, color: "#c88916" },
        ]}
      />
    </section>
  );
}

function RelationGraph({ payload }) {
  const ui = payload.ui;
  const nodes = payload.graph.nodes;
  const edges = payload.graph.edges;
  const positions = useMemo(() => {
    const map = new Map();
    const byType = {
      goal: nodes.filter((node) => node.type === "goal"),
      skill: nodes.filter((node) => node.type === "skill"),
      task: nodes.filter((node) => node.type === "task"),
      evidence: nodes.filter((node) => node.type === "evidence"),
      output: nodes.filter((node) => node.type === "output"),
      health: nodes.filter((node) => node.type === "health"),
    };
    const placeColumn = (items, x, startY, step) => {
      items.forEach((node, index) => {
        map.set(node.id, { x, y: startY + index * step });
      });
    };
    placeColumn(byType.goal, 72, 180, 1);
    placeColumn(byType.skill, 250, 80, 82);
    placeColumn(byType.task, 250, 276, 74);
    placeColumn(byType.evidence, 455, 190, 1);
    placeColumn(byType.output, 640, 132, 1);
    placeColumn(byType.health, 640, 262, 1);
    return map;
  }, [nodes]);
  return (
    <section className="hd-panel hd-graph-panel">
      <header>
        <div>
          <span className="hd-eyebrow">{label(ui, "dashboard_graph_eyebrow", "Canvas")}</span>
          <h3>{label(ui, "dashboard_graph_title", "Goal to evidence map")}</h3>
        </div>
      </header>
      <svg className="hd-graph" viewBox="0 0 720 380" role="img" aria-label={label(ui, "dashboard_graph_title", "Goal to evidence map")}>
        {edges.map((edge, index) => {
          const from = positions.get(edge.from);
          const to = positions.get(edge.to);
          if (!from || !to) {
            return null;
          }
          const mid = (from.x + to.x) / 2;
          return (
            <path
              key={`${edge.from}-${edge.to}-${index}`}
              className="hd-edge"
              d={`M ${from.x + 72} ${from.y} C ${mid} ${from.y}, ${mid} ${to.y}, ${to.x - 72} ${to.y}`}
            />
          );
        })}
        {nodes.map((node) => {
          const pos = positions.get(node.id);
          if (!pos) {
            return null;
          }
          return (
            <g key={node.id} className={`hd-node node-${node.type}`} transform={`translate(${pos.x - 72} ${pos.y - 28})`}>
              <rect width="144" height="56" rx="8" />
              <circle cx="18" cy="28" r="5" fill={NODE_COLORS[node.type] || "#68716f"} />
              <text className="hd-node-label" x="30" y="24">{cleanText(node.label).slice(0, 28)}</text>
              <text className="hd-node-metric" x="30" y="40">{cleanText(node.metric).slice(0, 24)}</text>
            </g>
          );
        })}
      </svg>
    </section>
  );
}

function EvidencePanel({ payload, onEmit }) {
  const ui = payload.ui;
  const pending = payload.pendingEvidence;
  const done = asArray(pending.done_uncrystallized);
  const unlinked = asArray(pending.unlinked);
  return (
    <section className="hd-panel hd-evidence">
      <header>
        <div>
          <span className="hd-eyebrow">{label(ui, "dashboard_pending_evidence_title", "Evidence")}</span>
          <h3>{label(ui, "dashboard_evidence_inbox_title", "Evidence inbox")}</h3>
        </div>
        <button className="hd-ghost" type="button" onClick={() => onEmit(openSectionEvent("evidence"))}>
          {label(ui, "dashboard_open_section", "Open")}
        </button>
      </header>
      <div className="hd-two-counts">
        <MetricCard labelText={label(ui, "dashboard_done_uncrystallized", "Done not crystallized")} value={pending.done_uncrystallized_count || 0} />
        <MetricCard labelText={label(ui, "dashboard_unlinked_evidence", "Unlinked pool rows")} value={pending.unlinked_count || 0} />
      </div>
      {[...done.slice(0, 2), ...unlinked.slice(0, 2)].length ? (
        <ul className="hd-compact-list">
          {done.slice(0, 2).map((item, index) => <li key={`done-${index}`}>{cleanText(item.title)}</li>)}
          {unlinked.slice(0, 2).map((item) => <li key={item.id}>{cleanText(item.title, item.id)}</li>)}
        </ul>
      ) : (
        <p className="hd-empty">{label(ui, "dashboard_pending_evidence_empty", "No pending evidence.")}</p>
      )}
    </section>
  );
}

function RightRail({ payload, onEmit }) {
  const ui = payload.ui;
  const health = payload.health;
  const counts = health.counts || {};
  const publicLayer = payload.publicLayer;
  return (
    <aside className="hd-rail">
      <section className="hd-panel compact">
        <span className="hd-eyebrow">{label(ui, "dashboard_health_title", "Profile Health")}</span>
        <div className="hd-health-badges">
          <span className={counts.error ? "danger" : ""}>{label(ui, "dashboard_health_errors", "Errors")} {counts.error || 0}</span>
          <span className={counts.warning ? "warn" : ""}>{label(ui, "dashboard_health_warnings", "Warnings")} {counts.warning || 0}</span>
          <span>{label(ui, "dashboard_health_info", "Info")} {counts.info || 0}</span>
        </div>
        <button className="hd-ghost full" type="button" onClick={() => onEmit(navigationEvent("pages/5_Profile_Health.py"))}>{label(ui, "quick_profile_health", "Profile Health")}</button>
      </section>
      <section className="hd-panel compact">
        <span className="hd-eyebrow">{label(ui, "dashboard_output_title", "Output")}</span>
        <MetricCard labelText={label(ui, "dashboard_public_drafts", "Drafts")} value={publicLayer.draft_total || 0} detail={`${label(ui, "dashboard_public_published", "Published")}: ${publicLayer.published_total || 0}`} />
        <button className="hd-ghost full" type="button" onClick={() => onEmit(navigationEvent("pages/6_Public_Site.py"))}>{label(ui, "quick_public_site", "Public Site")}</button>
      </section>
      <section className="hd-panel compact">
        <span className="hd-eyebrow">{label(ui, "dashboard_quick_title", "Quick entries")}</span>
        <div className="hd-link-list">
          {payload.quickLinks.slice(0, 5).map((link) => (
            <button key={link.path} type="button" onClick={() => onEmit(navigationEvent(link.path))}>
              {cleanText(link.label, link.id)}
            </button>
          ))}
        </div>
      </section>
    </aside>
  );
}

function Dashboard({ args }) {
  const payload = useMemo(() => normalizePayload(args.payload || {}), [args]);

  useEffect(() => {
    window.setTimeout(() => setFrameHeight(), 0);
  }, [payload]);

  function emit(event) {
    setComponentValue(event);
    window.setTimeout(() => setFrameHeight(), 0);
  }

  return (
    <main className="hd-shell">
      <GoalHero payload={payload} onEmit={emit} />
      <div className="hd-workbench">
        <div className="hd-left">
          <DoingPanel payload={payload} onEmit={emit} />
          <EvidencePanel payload={payload} onEmit={emit} />
        </div>
        <div className="hd-center">
          <OverviewPanel payload={payload} />
          <RelationGraph payload={payload} />
        </div>
        <RightRail payload={payload} onEmit={emit} />
      </div>
    </main>
  );
}

function App() {
  const [args, setArgs] = useState({ payload: {}, height: 860 });
  useEffect(() => {
    initStreamlitBridge(setArgs);
  }, []);
  return <Dashboard args={args} />;
}

const root = createRoot(document.getElementById("root"));
root.render(<App />);
