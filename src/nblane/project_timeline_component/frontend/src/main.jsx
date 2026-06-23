import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";

import "./style.css";
import {
  parseISO,
  toISO,
  buildDomain,
  pickUnit,
  buildTicks,
  msToX,
  xToMs,
  zoomDomain,
  _DAY_MS,
} from "./scale.js";
import {
  addTaskEvent,
  saveTaskEvent,
  deleteTaskEvent,
  addMilestoneEvent,
  saveMilestoneEvent,
  deleteMilestoneEvent,
  openEvidenceForTaskEvent,
  saveBasicsEvent,
  archiveProjectEvent,
  createProjectEvent,
  suggestRefsEvent,
  setRangeEvent,
} from "./events.js";

const READY = "streamlit:componentReady";
const SET_VALUE = "streamlit:setComponentValue";
const SET_HEIGHT = "streamlit:setFrameHeight";
const RENDER = "streamlit:render";

const PAD_L = 16;
const PAD_R = 16;
const ROW_AXIS_Y = 30; // axis baseline within a row track svg
const ROW_SVG_H = 78; // per-row track height
const TICKS_H = 22; // shared ticks header height
const LABEL_W = 210; // left project-label column width

const STATUS_OPTS = ["active", "paused", "completed", "archived"];
const KIND_OPTS = ["internal", "research", "work", "side_project", "learning"];
const VIS_OPTS = ["private", "public"];
const REF_FIELDS = [
  "goal_refs",
  "task_refs",
  "evidence_refs",
  "source_refs",
  "experience_refs",
  "output_refs",
];

// Stable per-project color palette for the multi-project review view.
const PROJECT_COLORS = [
  "#4b4ad6", "#1f7a52", "#b45309", "#0e7490",
  "#7c3aed", "#be185d", "#4d7c0f", "#9f1d1d",
];
function colorForProject(pid, projects) {
  const idx = projects.findIndex((p) => p.case?.id === pid);
  if (idx < 0) return PROJECT_COLORS[0];
  return PROJECT_COLORS[idx % PROJECT_COLORS.length];
}
const REVIEW_WINDOW_OPTS = [3, 4, 5, 6, 8];

function cleanText(value, fallback = "") {
  if (value == null) return fallback;
  const text = String(value);
  return text.length ? text : fallback;
}
function asArray(value) {
  return Array.isArray(value) ? value : [];
}
function dateParts(value) {
  const matches = cleanText(value).match(/\d{4}-\d{2}-\d{2}/g) || [];
  let start = matches[0] || "";
  let end = matches[1] || "";
  if (start && end && end < start) {
    [start, end] = [end, start];
  }
  return { start, end };
}
function formatDateRange(start, end) {
  let a = cleanText(start).trim();
  let b = cleanText(end).trim();
  if (a && b && b < a) {
    [a, b] = [b, a];
  }
  if (a && b) return a === b ? a : `${a}/${b}`;
  return a || b;
}
function projectTaskDateRange(project) {
  const dates = [];
  for (const t of asArray(project?.tasks)) {
    for (const key of ["started_on", "completed_on", "anchor"]) {
      const ms = parseISO(t?.[key]);
      if (ms != null) dates.push(ms);
    }
  }
  if (!dates.length) return "";
  return formatDateRange(toISO(Math.min(...dates)), toISO(Math.max(...dates)));
}
function projectDerivedTimeRange(project) {
  return cleanText(project?.case?.derived_time_range).trim() || projectTaskDateRange(project);
}
function projectDisplayTimeRange(project) {
  return cleanText(project?.case?.time_range).trim() || projectDerivedTimeRange(project);
}

/* ---- Streamlit bridge ---- */
function sendBack(type, payload) {
  if (window.parent === window) return;
  window.parent.postMessage({ isStreamlitMessage: true, type, ...payload }, "*");
}
function setFrameHeight(height) {
  sendBack(SET_HEIGHT, { height: Math.max(240, Math.ceil(height || document.body.scrollHeight || 420)) });
}
function setComponentValue(value) {
  sendBack(SET_VALUE, { value, dataType: "json" });
}
function initStreamlitBridge(onRender) {
  window.addEventListener("message", (event) => {
    if (event.data?.type !== RENDER) return;
    onRender(event.data?.args || {});
  });
  sendBack(READY, { apiVersion: 1 });
  window.setTimeout(() => setFrameHeight(), 0);
}

// Open Evidence Review for a task WITHOUT navigating the board away. The
// component iframe is same-origin with the parent Streamlit app, so we open a
// new browser tab pointed at the Evidence Review page (carrying the task ref in
// the query string). Falls back to the Python switch_page event if blocked
// (popup blocker, cross-origin) so the action never silently no-ops.
function openEvidenceTab(taskId, emitFallback) {
  try {
    const parentLoc = window.parent && window.parent.location;
    const origin = parentLoc ? parentLoc.origin : window.location.origin;
    const qs = `kanban_task=${encodeURIComponent(taskId)}&source_page=${encodeURIComponent("Project Board")}`;
    const url = `${origin}/Evidence_Review?${qs}`;
    // NOTE: do NOT pass "noopener" here -- with noopener, window.open() returns
    // null even on success, which would make us think it failed and fire the
    // switch_page fallback too (navigating the board away -- the exact jarring
    // behavior we're avoiding). Open normally, then sever opener for safety.
    const win = window.open(url, "_blank");
    if (win) {
      try { win.opener = null; } catch (e) { /* ignore */ }
      return;
    }
  } catch (e) {
    /* cross-origin or blocked -> fall through to Python navigation */
  }
  if (emitFallback) emitFallback();
}

function label(labels, key, fallback) {
  const v = labels?.[key];
  return v == null || v === "" ? fallback : v;
}

const SECTION_OPTS = ["Queue", "Doing", "Done", "Someday / Maybe"];
const MS_STATUS_OPTS = ["planned", "active", "completed", "archived"];

/* ---- chip multi-select (refs) ---- */
function ChipSelect({ labelText, options, selected, onChange }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const opts = asArray(options);
  const sel = asArray(selected);
  const labelOf = (id) => {
    const hit = opts.find((o) => o.id === id);
    return hit ? hit.label : id;
  };
  const remaining = opts.filter(
    (o) => !sel.includes(o.id) && (!q || `${o.label}`.toLowerCase().includes(q.toLowerCase()))
  );
  return (
    <div className="tl-field">
      <label>{labelText}</label>
      <div className="tl-chips">
        {sel.map((id) => (
          <span className="tl-chip-item" key={id}>
            {labelOf(id)}
            <button
              type="button"
              className="tl-chip-x"
              onClick={() => onChange(sel.filter((x) => x !== id))}
            >
              ✕
            </button>
          </span>
        ))}
        <button type="button" className="tl-chip-add" onClick={() => setOpen((o) => !o)}>
          +
        </button>
      </div>
      {open && (
        <div className="tl-chip-dropdown">
          <input
            className="tl-chip-search"
            value={q}
            placeholder="…"
            onChange={(e) => setQ(e.target.value)}
            autoFocus
          />
          <div className="tl-chip-options">
            {remaining.length === 0 && <div className="tl-chip-empty">—</div>}
            {remaining.slice(0, 50).map((o) => (
              <button
                type="button"
                key={o.id}
                className="tl-chip-option"
                onClick={() => {
                  onChange([...sel, o.id]);
                  setQ("");
                }}
              >
                {o.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function DateRangeFields({ labels, value, fallback, onChange }) {
  const manual = dateParts(value);
  const derived = dateParts(fallback);
  const useDerived = !cleanText(value).trim();
  const start = manual.start || (useDerived ? derived.start : "");
  const end = manual.end || (useDerived ? derived.end : "");
  const update = (part, nextValue) => {
    onChange(formatDateRange(part === "start" ? nextValue : start, part === "end" ? nextValue : end));
  };
  return (
    <div className="tl-field">
      <label>{label(labels, "field_time_range", "Time range")}</label>
      <div className="tl-date-range">
        <label className="tl-date-part">
          <span>{label(labels, "tl_range_start", "From")}</span>
          <input type="date" value={start} onChange={(e) => update("start", e.target.value)} />
        </label>
        <label className="tl-date-part">
          <span>{label(labels, "tl_range_end", "To")}</span>
          <input type="date" value={end} onChange={(e) => update("end", e.target.value)} />
        </label>
      </div>
    </div>
  );
}

/* ---- project full-info / basics editor ---- */
function BasicsForm({ project, labels, emit, onClose }) {
  const c = project.case || {};
  const optionMaps = project.option_maps || {};
  const fallbackTimeRange = projectDerivedTimeRange(project);
  const [form, setForm] = useState(() => ({
    title: c.title || "",
    status: c.status || "active",
    kind: c.kind || "internal",
    visibility: c.visibility || "private",
    time_range: c.time_range || "",
    summary: c.summary || "",
    notes: c.notes || "",
    goal_refs: asArray(c.goal_refs),
    task_refs: asArray(c.task_refs),
    evidence_refs: asArray(c.evidence_refs),
    source_refs: asArray(c.source_refs),
    experience_refs: asArray(c.experience_refs),
    output_refs: asArray(c.output_refs),
  }));
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  return (
    <div className="tl-detail">
      <div className="tl-detail-head">
        <span className="tl-detail-title">{label(labels, "tl_full_info", "Project info")}</span>
        <button className="tl-btn tl-btn-ghost" onClick={onClose}>✕</button>
      </div>
      <div className="tl-field">
        <label>{label(labels, "field_title", "Title")}</label>
        <input value={form.title} onChange={(e) => set("title", e.target.value)} />
      </div>
      <div className="tl-row3">
        <div className="tl-field">
          <label>{label(labels, "field_status", "Status")}</label>
          <select value={form.status} onChange={(e) => set("status", e.target.value)}>
            {STATUS_OPTS.map((s) => (
              <option key={s} value={s}>{label(labels, `status_${s}`, s)}</option>
            ))}
          </select>
        </div>
        <div className="tl-field">
          <label>{label(labels, "field_kind", "Kind")}</label>
          <select value={form.kind} onChange={(e) => set("kind", e.target.value)}>
            {KIND_OPTS.map((s) => (
              <option key={s} value={s}>{label(labels, `kind_${s}`, s)}</option>
            ))}
          </select>
        </div>
        <div className="tl-field">
          <label>{label(labels, "field_visibility", "Visibility")}</label>
          <select value={form.visibility} onChange={(e) => set("visibility", e.target.value)}>
            {VIS_OPTS.map((s) => (
              <option key={s} value={s}>{label(labels, `visibility_${s}`, s)}</option>
            ))}
          </select>
        </div>
      </div>
      <DateRangeFields
        labels={labels}
        value={form.time_range}
        fallback={fallbackTimeRange}
        onChange={(next) => set("time_range", next)}
      />
      <div className="tl-field">
        <label>{label(labels, "field_summary", "Summary")}</label>
        <textarea value={form.summary} onChange={(e) => set("summary", e.target.value)} />
      </div>
      <div className="tl-field">
        <label>{label(labels, "field_notes", "Notes")}</label>
        <textarea value={form.notes} onChange={(e) => set("notes", e.target.value)} />
      </div>
      <div className="tl-refs-head">
        <span>{label(labels, "links_section", "Links")}</span>
        <button
          className="tl-btn tl-btn-ghost"
          onClick={() => emit(suggestRefsEvent(c.id))}
          title={label(labels, "project_ai_suggest_help", "")}
        >
          ✦ {label(labels, "project_ai_suggest_refs", "AI suggest")}
        </button>
      </div>
      {REF_FIELDS.map((field) => (
        <ChipSelect
          key={field}
          labelText={label(labels, `field_${field}`, field)}
          options={optionMaps[field]}
          selected={form[field]}
          onChange={(next) => set(field, next)}
        />
      ))}
      <div className="tl-detail-actions">
        {form.status !== "archived" && (
          <button
            className="tl-btn tl-btn-danger"
            onClick={() => {
              if (window.confirm(label(labels, "tl_delete_confirm", "Archive this project?"))) {
                emit(archiveProjectEvent(c.id));
              }
            }}
          >
            {label(labels, "archive_project", "Archive")}
          </button>
        )}
        <button className="tl-btn" onClick={onClose}>{label(labels, "cancel", "Cancel")}</button>
        <button
          className="tl-btn tl-btn-primary"
          onClick={() => {
            if (!cleanText(form.title).trim()) return;
            emit(saveBasicsEvent(c.id, form));
          }}
        >{label(labels, "save_project", "Save")}</button>
      </div>
    </div>
  );
}

/* ---- subtask checklist editor (task add/edit) ---- */
function SubtaskEditor({ labels, value, onChange }) {
  const items = asArray(value);
  const update = (i, patch) =>
    onChange(items.map((it, idx) => (idx === i ? { ...it, ...patch } : it)));
  const remove = (i) => onChange(items.filter((_, idx) => idx !== i));
  const add = () => onChange([...items, { title: "", done: false }]);
  return (
    <div className="tl-field">
      <label>{label(labels, "task_subtasks", "Subtasks")}</label>
      <div className="tl-subtask-edit">
        {items.map((it, i) => (
          <div className="tl-subtask-edit-row" key={i}>
            <button
              type="button"
              className={`tl-subtask-check${it.done ? " is-done" : ""}`}
              onClick={() => update(i, { done: !it.done })}
              title={it.done ? "✓" : "○"}
            >
              {it.done ? "☑" : "☐"}
            </button>
            <input
              value={it.title || ""}
              placeholder={label(labels, "tl_subtask_placeholder", "Subtask…")}
              onChange={(e) => update(i, { title: e.target.value })}
            />
            <button type="button" className="tl-subtask-del" onClick={() => remove(i)}>
              ✕
            </button>
          </div>
        ))}
        <button type="button" className="tl-btn tl-btn-sm tl-subtask-add" onClick={add}>
          + {label(labels, "tl_subtask_add", "Add subtask")}
        </button>
      </div>
    </div>
  );
}

/* ---- inline add/edit form (task / milestone) ---- */
function EditForm({ kind, initial, labels, settings, onSubmit, onCancel, onDelete }) {
  const today = cleanText(settings.today);
  // Seed the date so the form SENDS what it shows. The date input displays
  // `form.date || today`, but without seeding form.date stays "" and an empty
  // date gets submitted -> task lands with no timeline anchor and disappears.
  const [form, setForm] = useState(() => {
    const f = { ...initial };
    if (kind === "task" && !cleanText(f.date)) f.date = today;
    if (kind === "task") f.subtasks = asArray(f.subtasks).map((s) => ({ ...s }));
    return f;
  });
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const isTask = kind === "task";
  return (
    <div className="tl-detail">
      <div className="tl-detail-head">
        <span className="tl-detail-title">
          {isTask
            ? label(labels, "task_title", "Task")
            : label(labels, "milestones", "Milestone")}
        </span>
        <button className="tl-btn tl-btn-ghost" onClick={onCancel}>✕</button>
      </div>
      <div className="tl-field">
        <label>{label(labels, "field_title", "Title")}</label>
        <input value={form.title || ""} onChange={(e) => set("title", e.target.value)} autoFocus />
      </div>
      {isTask ? (
        <div className="tl-row2">
          <div className="tl-field">
            <label>{label(labels, "task_section", "Section")}</label>
            <select value={form.section || "Queue"} onChange={(e) => set("section", e.target.value)}>
              {SECTION_OPTS.map((s) => (
                <option key={s} value={s}>{label(labels, `section_${s}`, s)}</option>
              ))}
            </select>
          </div>
          <div className="tl-field">
            <label>{label(labels, "tl_date", "Date")}</label>
            <input type="date" value={form.date || today} onChange={(e) => set("date", e.target.value)} />
          </div>
        </div>
      ) : (
        <div className="tl-row2">
          <div className="tl-field">
            <label>{label(labels, "field_status", "Status")}</label>
            <select value={form.status || "planned"} onChange={(e) => set("status", e.target.value)}>
              {MS_STATUS_OPTS.map((s) => (
                <option key={s} value={s}>{label(labels, `status_${s}`, s)}</option>
              ))}
            </select>
          </div>
          <div className="tl-field">
            <label>{label(labels, "field_date", "Date")}</label>
            <input type="date" value={form.date || ""} onChange={(e) => set("date", e.target.value)} />
          </div>
        </div>
      )}
      {isTask ? (
        <>
          <div className="tl-field">
            <label>{label(labels, "task_field_context", "Context")}</label>
            <textarea value={form.context || ""} onChange={(e) => set("context", e.target.value)} />
          </div>
          <SubtaskEditor
            labels={labels}
            value={form.subtasks}
            onChange={(next) => set("subtasks", next)}
          />
        </>
      ) : (
        <>
          <div className="tl-field">
            <label>{label(labels, "field_target", "Target")}</label>
            <input value={form.target || ""} onChange={(e) => set("target", e.target.value)} />
          </div>
          <div className="tl-field">
            <label>{label(labels, "field_summary", "Summary")}</label>
            <textarea value={form.summary || ""} onChange={(e) => set("summary", e.target.value)} />
          </div>
        </>
      )}
      <div className="tl-detail-actions">
        {onDelete && (
          <button className="tl-btn tl-btn-danger" onClick={onDelete}>
            {label(labels, "delete_task", "Delete")}
          </button>
        )}
        <button className="tl-btn" onClick={onCancel}>{label(labels, "cancel", "Cancel")}</button>
        <button
          className="tl-btn tl-btn-primary"
          onClick={() => {
            if (!cleanText(form.title).trim()) return;
            onSubmit(form);
          }}
        >{label(labels, "save", "Save")}</button>
      </div>
    </div>
  );
}

/* ---- shared task detail body (DetailPanel + review window reuse this) ---- */
function TaskDetailBody({ t, project, labels, emit, compact = false }) {
  const cid = project?.case?.id;
  const sectionLabel = label(labels, `section_${t.section}`, t.section);
  const body = (
    <div className={`tl-task-detail${compact ? " tl-task-detail-compact" : ""}`}>
      <div className="tl-detail-meta">
        <span className={`tl-chip tl-chip-${t.done ? "done" : t.archived ? "archived" : "doing"}`}>
          {sectionLabel}
        </span>
        {asArray(t.tags).map((tag) => (
          <span className="tl-chip" key={tag}>#{tag}</span>
        ))}
      </div>
      {t.started_on && (
        <div className="tl-read-line"><strong>{label(labels, "tl_started", "Started")}</strong>{t.started_on}</div>
      )}
      {t.completed_on && (
        <div className="tl-read-line"><strong>{label(labels, "tl_completed", "Completed")}</strong>{t.completed_on}</div>
      )}
      {!t.started_on && !t.completed_on && (
        <div className="tl-read-line"><strong>{label(labels, "tl_date", "Date")}</strong>{t.anchor}</div>
      )}
      {t.why && (
        <div className="tl-read-block tl-read-block-why">
          <span className="tl-read-label">{label(labels, "task_field_why", "Why")}</span>
          <p>{t.why}</p>
        </div>
      )}
      {t.context && (
        <div className="tl-read-block tl-read-block-context">
          <span className="tl-read-label">{label(labels, "task_field_context", "Context")}</span>
          <p>{t.context}</p>
        </div>
      )}
      {t.outcome && (
        <div className="tl-read-block tl-read-block-outcome">
          <span className="tl-read-label">{label(labels, "task_field_outcome", "Outcome")}</span>
          <p>{t.outcome}</p>
        </div>
      )}
      {asArray(t.subtasks).length > 0 && (
        <div className="tl-read-block tl-read-block-subtasks">
          <span className="tl-read-label">
            {label(labels, "task_subtasks", "Subtasks")}
            {" "}({asArray(t.subtasks).filter((s) => s.done).length}/{asArray(t.subtasks).length})
          </span>
          <ul className="tl-subtasks">
            {asArray(t.subtasks).map((s, i) => (
              <li key={i} className={s.done ? "is-done" : ""}>
                <span className="tl-subtask-box">{s.done ? "☑" : "☐"}</span>
                {s.title}
              </li>
            ))}
          </ul>
        </div>
      )}
      {t.done && (
        <div className="tl-detail-actions">
          <button className="tl-btn tl-btn-primary"
                  onClick={() => openEvidenceTab(t.id, () => emit(openEvidenceForTaskEvent(t.id, cid)))}>
            → {label(labels, "tl_to_evidence", "Distill to evidence")}
          </button>
        </div>
      )}
    </div>
  );
  return body;
}

/* ---- review window: full detail for every task in the current window ---- */
function ReviewDetail({ tasks, cursor, windowSize, labels, projects, emit, onClose }) {
  if (!tasks.length) return null;
  const winStart = Math.floor(cursor / windowSize) * windowSize;
  const win = tasks.slice(winStart, winStart + windowSize);
  return (
    <div className="tl-review-detail">
      <div className="tl-detail-head tl-review-detail-head">
        <span className="tl-detail-title">
          {label(labels, "tl_review_window", "Window")}
          {" "}{winStart + 1}–{Math.min(winStart + windowSize, tasks.length)} / {tasks.length}
        </span>
        <button className="tl-btn tl-btn-ghost" onClick={onClose}>✕</button>
      </div>
      {win.map((t, i) => {
        const idx = winStart + i;
        const color = colorForProject(t._pid, projects);
        const proj = projects.find((p) => p.case?.id === t._pid);
        return (
          <div
            key={`${t._pid}:${t.id || idx}`}
            className={`tl-detail tl-review-card${idx === cursor ? " is-cursor" : ""}`}
            style={{ "--pc": color }}
          >
            <div className="tl-detail-head">
              <span className="tl-detail-title">{t.title || t.id}</span>
              <span className="tl-review-card-project" style={{ color }}>{t._ptitle}</span>
            </div>
            <TaskDetailBody t={t} project={proj} labels={labels} emit={emit} compact />
          </div>
        );
      })}
    </div>
  );
}

/* ---- detail / read card for a selected task or milestone ---- */
function DetailPanel({ project, labels, selected, settings, emit, onClose, onEdit }) {
  if (!selected) return null;
  if (selected.kind === "task") {
    const t = asArray(project.tasks).find((x) => x.id === selected.id);
    if (!t) return null;
    return (
      <div className="tl-detail">
        <div className="tl-detail-head">
          <span className="tl-detail-title">{t.title || t.id}</span>
          <div style={{ display: "flex", gap: 6 }}>
            <button className="tl-btn" onClick={() => onEdit("task", { ...t })}>
              {label(labels, "edit", "Edit")}
            </button>
            <button className="tl-btn tl-btn-ghost" onClick={onClose}>✕</button>
          </div>
        </div>
        <TaskDetailBody t={t} project={project} labels={labels} emit={emit} />
      </div>
    );
  }
  const m = asArray(project.milestones).find((x) => x.id === selected.id);
  if (!m) return null;
  return (
    <div className="tl-detail">
      <div className="tl-detail-head">
        <span className="tl-detail-title">{m.title || m.id}</span>
        <div style={{ display: "flex", gap: 6 }}>
          <button className="tl-btn" onClick={() => onEdit("milestone", { ...m })}>
            {label(labels, "edit", "Edit")}
          </button>
          <button className="tl-btn tl-btn-ghost" onClick={onClose}>✕</button>
        </div>
      </div>
      {m.date && <div className="tl-read-line"><strong>{label(labels, "field_date", "Date")}</strong>{m.date}</div>}
      {m.target && <div className="tl-read-line"><strong>{label(labels, "field_target", "Target")}</strong>{m.target}</div>}
      {m.summary && <div className="tl-read-line">{m.summary}</div>}
    </div>
  );
}

/* ---- shared ticks header (aligns all rows to the same columns) ---- */
function TicksHeader({ dom, width, ticks, todayMs }) {
  const xOf = (ms) => msToX(ms, dom.start, dom.end, width, PAD_L, PAD_R);
  return (
    <svg className="tl-ticks-svg" viewBox={`0 0 ${width} ${TICKS_H}`}>
      {ticks.map((t) => {
        const x = xOf(t.ms);
        return (
          <text key={t.ms} className="tl-tick-text" x={x} y={15} textAnchor="middle">
            {t.label}
          </text>
        );
      })}
      {todayMs >= dom.start && todayMs <= dom.end && (
        <line className="tl-today-line" x1={xOf(todayMs)} y1={2} x2={xOf(todayMs)} y2={TICKS_H} />
      )}
    </svg>
  );
}

function TimelineLegend({ labels }) {
  const items = [
    { key: "doing", labelKey: "tl_legend_doing", fallback: "In progress task" },
    { key: "done", labelKey: "tl_legend_done", fallback: "Done task" },
    { key: "archived", labelKey: "tl_legend_archived", fallback: "Archived task" },
    { key: "milestone", labelKey: "tl_legend_milestone", fallback: "Milestone" },
    { key: "today", labelKey: "tl_legend_today", fallback: "Today" },
  ];
  return (
    <div className="tl-legend" aria-label={label(labels, "tl_legend_title", "Legend")}>
      <span className="tl-legend-title">{label(labels, "tl_legend_title", "Legend")}</span>
      {items.map((item) => (
        <span className="tl-legend-item" key={item.key}>
          <span className={`tl-legend-swatch tl-legend-${item.key}`} aria-hidden="true" />
          {label(labels, item.labelKey, item.fallback)}
        </span>
      ))}
    </div>
  );
}

/* ---- one project row: left label + right svg track ---- */
function ProjectRow({
  project,
  labels,
  dom,
  width,
  ticks,
  todayMs,
  isSelected,
  selectedItem,
  onSelectProject,
  onSelectItem,
  onContext,
  onAddTask,
  onAddMilestone,
  onFullInfo,
  showTip,
  hideTip,
}) {
  const c = project.case || {};
  const tasks = asArray(project.tasks);
  const milestones = asArray(project.milestones);
  const noDateCount = Number(project.no_date_count || 0);
  const displayTimeRange = projectDisplayTimeRange(project);
  const xOf = (ms) => msToX(ms, dom.start, dom.end, width, PAD_L, PAD_R);

  const pointClass = (t) => {
    if (t.archived) return "tl-pt tl-pt-archived";
    if (t.done) return "tl-pt tl-pt-done";
    return "tl-pt tl-pt-doing";
  };

  // stack overlapping points vertically; row height grows with lane count so
  // dense projects (many points near the same date) don't clamp/pile up.
  const { placed, maxLane } = useMemo(() => {
    const sorted = [...tasks].sort((a, b) => (parseISO(a.anchor) || 0) - (parseISO(b.anchor) || 0));
    const lastXByLane = [];
    let hi = 0;
    const out = sorted.map((t) => {
      const ms = parseISO(t.anchor);
      const x = ms == null ? PAD_L : xOf(ms);
      let lane = 0;
      while (lane < lastXByLane.length && x - lastXByLane[lane] < 14) lane += 1;
      lastXByLane[lane] = x;
      if (lane > hi) hi = lane;
      return { ...t, _x: x, _lane: lane };
    });
    return { placed: out, maxLane: hi };
  }, [tasks, dom, width]);

  const LANE_H = 12;
  const svgH = Math.max(ROW_SVG_H, ROW_AXIS_Y + 14 + (maxLane + 1) * LANE_H + 4);

  return (
    <div className={`tl-row${isSelected ? " is-selected" : ""}`}>
      <div className="tl-row-label" onClick={() => onSelectProject(c.id)}>
        <div className="tl-row-title">{c.title || c.id}</div>
        <div className="tl-row-sub">
          <span className="tl-chip">{label(labels, `status_${c.status}`, c.status)}</span>
          {displayTimeRange ? <span className="tl-row-range">{displayTimeRange}</span> : null}
        </div>
        {c.summary ? <div className="tl-row-summary">{c.summary}</div> : null}
      </div>
      <div className="tl-row-track">
        <svg className="tl-svg" viewBox={`0 0 ${width} ${svgH}`}>
          {/* tick guide lines */}
          {ticks.map((t) => {
            const x = xOf(t.ms);
            return <line key={t.ms} className="tl-tick-line" x1={x} y1={4} x2={x} y2={ROW_AXIS_Y} />;
          })}
          {/* axis */}
          <line className="tl-axis-line" x1={PAD_L} y1={ROW_AXIS_Y} x2={width - PAD_R} y2={ROW_AXIS_Y} />
          {/* today */}
          {todayMs >= dom.start && todayMs <= dom.end && (
            <line className="tl-today-line" x1={xOf(todayMs)} y1={4} x2={xOf(todayMs)} y2={ROW_AXIS_Y + 6} />
          )}
          {/* milestones (above axis) */}
          {milestones.filter((m) => parseISO(m.date)).map((m) => {
            const x = xOf(parseISO(m.date));
            const isSel = selectedItem?.kind === "milestone" && selectedItem.id === m.id;
            return (
              <g key={m.id}
                 onClick={(e) => { e.stopPropagation(); onSelectItem(c.id, { kind: "milestone", id: m.id }); }}
                 onContextMenu={(e) => onContext(e, c.id, "milestone", m.id)}
                 onMouseMove={(e) => showTip(e, `${m.title || m.id} · ${m.date}`)}
                 onMouseLeave={hideTip}>
                <rect className="tl-ms-marker" x={x - 5} y={ROW_AXIS_Y - 5} width="10" height="10"
                      transform={`rotate(45 ${x} ${ROW_AXIS_Y})`}
                      style={isSel ? { strokeWidth: 2, stroke: "var(--ink)" } : null} />
                <text className="tl-ms-text" x={x} y={ROW_AXIS_Y - 12} textAnchor="middle">
                  {(m.title || m.id).slice(0, 12)}
                </text>
              </g>
            );
          })}
          {/* task points (below axis) */}
          {placed.map((t) => {
            const y = ROW_AXIS_Y + 14 + t._lane * LANE_H;
            const isSel = selectedItem?.kind === "task" && selectedItem.id === t.id;
            return (
              <circle
                key={t.id || `${t.title}-${t._x}`}
                className={`${pointClass(t)}${isSel ? " tl-pt-sel" : ""}`}
                cx={t._x}
                cy={Math.min(y, svgH - 6)}
                r="5"
                onClick={(e) => { e.stopPropagation(); onSelectItem(c.id, { kind: "task", id: t.id }); }}
                onContextMenu={(e) => onContext(e, c.id, "task", t.id)}
                onMouseMove={(e) => showTip(e, `${t.title} · ${t.anchor}${t.archived ? " (archived)" : ""}`)}
                onMouseLeave={hideTip}
              />
            );
          })}
        </svg>
        <div className="tl-row-actions">
          {noDateCount > 0 && (
            <span className="tl-warn">
              {label(labels, "tl_no_date_tasks", "{n} task(s) have no date and are not shown.").replace("{n}", noDateCount)}
            </span>
          )}
          <button className="tl-btn tl-btn-sm" onClick={() => onAddTask(c.id)}>
            + {label(labels, "task_title", "Task")}
          </button>
          <button className="tl-btn tl-btn-sm" onClick={() => onAddMilestone(c.id)}>
            + {label(labels, "milestones", "Milestone")}
          </button>
          <button className="tl-btn tl-btn-sm" onClick={() => onFullInfo(c.id)}>
            {label(labels, "tl_full_info", "Project info")}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---- review mode: time-ordered interleaved task list, colored by project ---- */
function ReviewList({ tasks, cursor, windowSize, labels, projects, onPick }) {
  const scrollRef = useRef(null);
  const activeRef = useRef(null);
  useEffect(() => {
    if (activeRef.current && activeRef.current.scrollIntoView) {
      activeRef.current.scrollIntoView({ block: "nearest" });
    }
  }, [cursor]);
  if (!tasks.length) {
    return <div className="tl-review-empty">{label(labels, "tl_review_empty", "No tasks in range.")}</div>;
  }
  const winStart = Math.floor(cursor / windowSize) * windowSize;
  const winEnd = winStart + windowSize;
  return (
    <div className="tl-review-list" ref={scrollRef}>
      {tasks.map((t, i) => {
        const isCursor = i === cursor;
        const inWindow = i >= winStart && i < winEnd;
        const color = colorForProject(t._pid, projects);
        const sectionLabel = label(labels, `section_${t.section}`, t.section);
        return (
          <div
            key={`${t._pid}:${t.id || i}`}
            ref={isCursor ? activeRef : null}
            className={`tl-review-item${isCursor ? " is-cursor" : ""}${inWindow ? " is-inwindow" : ""}`}
            style={{ "--pc": color }}
            onClick={() => onPick(i)}
          >
            <span className="tl-review-date">{t.anchor}</span>
            <span className="tl-review-dot" />
            <span className="tl-review-main">
              <span className="tl-review-title">{t.title || t.id}</span>
              <span className="tl-review-sub">
                <span className="tl-review-project">{t._ptitle}</span>
                <span className="tl-review-section">{sectionLabel}</span>
                {t.done ? <span className="tl-review-done">✓</span> : null}
              </span>
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ---- compact summary chips folded into the legend row ---- */
function SummaryChips({ summary, labels }) {
  if (!summary || typeof summary !== "object") return null;
  const statusItems = STATUS_OPTS.map((s) => ({
    key: s,
    text: label(labels, `status_${s}`, s),
    value: Number(summary[s] || 0),
    tone: "",
  }));
  const gapItems = [
    {
      key: "unassigned_tasks",
      text: label(labels, "metric_unassigned_tasks", "Unassigned tasks"),
      value: Number(summary.unassigned_tasks || 0),
      tone: summary.unassigned_tasks ? "risk" : "quiet",
    },
    {
      key: "unassigned_evidence",
      text: label(labels, "metric_unassigned_evidence", "Unassigned evidence"),
      value: Number(summary.unassigned_evidence || 0),
      tone: summary.unassigned_evidence ? "risk" : "quiet",
    },
    {
      key: "current_goal_projects",
      text: label(labels, "metric_current_goal_projects", "Current-goal projects"),
      value: Number(summary.current_goal_projects || 0),
      tone: "goal",
    },
  ];
  const chip = (item) => (
    <span className={`tl-sum-chip${item.tone ? ` tl-sum-chip-${item.tone}` : ""}`} key={item.key}>
      <span className="tl-sum-label">{item.text}</span>
      <strong>{item.value}</strong>
    </span>
  );
  return (
    <span className="tl-sum">
      <span className="tl-sum-group">{statusItems.map(chip)}</span>
      <span className="tl-sum-group">{gapItems.map(chip)}</span>
    </span>
  );
}

/* ---- inline create-project form (opened from the toolbar) ---- */
function CreateProjectForm({ createForm, labels, emit, onClose }) {
  const opts = createForm || {};
  const prefill = opts.prefill || {};
  const statuses = asArray(opts.statuses).length ? asArray(opts.statuses) : STATUS_OPTS;
  const kinds = asArray(opts.kinds).length ? asArray(opts.kinds) : KIND_OPTS;
  const visibilities = asArray(opts.visibilities).length ? asArray(opts.visibilities) : VIS_OPTS;
  const [form, setForm] = useState(() => ({
    title: cleanText(prefill.title),
    id: cleanText(prefill.id),
    status: statuses[0],
    kind: kinds.includes(prefill.kind) ? prefill.kind : kinds[0],
    visibility: visibilities.includes(prefill.visibility) ? prefill.visibility : visibilities[0],
    summary: cleanText(prefill.summary),
    goal_refs: [],
  }));
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const evidenceCount = Number(prefill.evidence_count || 0);
  return (
    <div className="tl-detail tl-create-form">
      <div className="tl-detail-head">
        <span className="tl-detail-title">{label(labels, "create_project", "Create project")}</span>
        <button className="tl-btn tl-btn-ghost" onClick={onClose}>✕</button>
      </div>
      {evidenceCount > 0 && (
        <div className="tl-create-hint">
          {label(
            labels,
            "create_from_evidence_hint",
            "Prefilled from {n} evidence row(s). Confirm to create and link."
          ).replace("{n}", evidenceCount)}
        </div>
      )}
      <div className="tl-row2">
        <div className="tl-field">
          <label>{label(labels, "field_title", "Title")}</label>
          <input value={form.title} onChange={(e) => set("title", e.target.value)} autoFocus />
        </div>
        <div className="tl-field">
          <label>{label(labels, "field_id", "ID")}</label>
          <input
            value={form.id}
            placeholder={label(labels, "id_help", "")}
            onChange={(e) => set("id", e.target.value)}
          />
        </div>
      </div>
      <div className="tl-row3">
        <div className="tl-field">
          <label>{label(labels, "field_status", "Status")}</label>
          <select value={form.status} onChange={(e) => set("status", e.target.value)}>
            {statuses.map((s) => (
              <option key={s} value={s}>{label(labels, `status_${s}`, s)}</option>
            ))}
          </select>
        </div>
        <div className="tl-field">
          <label>{label(labels, "field_kind", "Kind")}</label>
          <select value={form.kind} onChange={(e) => set("kind", e.target.value)}>
            {kinds.map((s) => (
              <option key={s} value={s}>{label(labels, `kind_${s}`, s)}</option>
            ))}
          </select>
        </div>
        <div className="tl-field">
          <label>{label(labels, "field_visibility", "Visibility")}</label>
          <select value={form.visibility} onChange={(e) => set("visibility", e.target.value)}>
            {visibilities.map((s) => (
              <option key={s} value={s}>{label(labels, `visibility_${s}`, s)}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="tl-field">
        <label>{label(labels, "field_summary", "Summary")}</label>
        <textarea value={form.summary} onChange={(e) => set("summary", e.target.value)} />
      </div>
      <ChipSelect
        labelText={label(labels, "field_goal_refs", "Goals")}
        options={opts.goal_options}
        selected={form.goal_refs}
        onChange={(next) => set("goal_refs", next)}
      />
      <div className="tl-detail-actions">
        <button className="tl-btn" onClick={onClose}>{label(labels, "cancel", "Cancel")}</button>
        <button
          className="tl-btn tl-btn-primary"
          onClick={() => {
            if (!cleanText(form.title).trim()) return;
            emit(createProjectEvent(form));
          }}
        >{label(labels, "create_project", "Create project")}</button>
      </div>
    </div>
  );
}

function App() {
  const [args, setArgs] = useState({ payload: {} });
  useEffect(() => {
    initStreamlitBridge(setArgs);
  }, []);
  const payload = args.payload || {};
  const emit = (event) => setComponentValue(event);

  // Normalize: accept either {projects:[...]} or a single-case legacy payload.
  const projects = useMemo(() => {
    if (Array.isArray(payload.projects)) return payload.projects;
    if (payload.case) {
      return [{
        case: payload.case,
        tasks: payload.tasks,
        milestones: payload.milestones,
        no_date_count: payload.no_date_count,
        option_maps: payload.option_maps || {},
      }];
    }
    return [];
  }, [payload]);

  const labels = payload.labels || {};
  const settings = payload.settings || {};
  const lang = cleanText(settings.lang, "en");
  const todayMs = parseISO(settings.today) ?? Date.now();
  const range = payload.range || {};
  const summary = payload.summary || null;
  const createForm = payload.create_form || null;

  const wrapRef = useRef(null);
  const mainRef = useRef(null); // timeline area; native wheel listener attaches here
  const rowRefs = useRef({}); // projectId -> row DOM node
  const [trackWidth, setTrackWidth] = useState(720);
  const [view, setView] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [panel, setPanel] = useState(null); // {projectId, mode, kind?, initial?, top}
  const [menu, setMenu] = useState(null); // {x,y,projectId,kind,id}
  const [tip, setTip] = useState(null);
  const [showCreate, setShowCreate] = useState(false);

  // Auto-open the create form when Python prefilled it (create-from-evidence
  // flow) or when there are no projects yet -- creating one is the first step.
  const createEvidenceCount = Number(createForm?.prefill?.evidence_count || 0);
  useEffect(() => {
    if (createEvidenceCount > 0) setShowCreate(true);
  }, [createEvidenceCount]);

  // Review mode: interleave selected projects' tasks in time order, color by
  // project, step with up/down, page with left/right over an N-task window.
  const [reviewMode, setReviewMode] = useState(false);
  const [reviewProjects, setReviewProjects] = useState(() => new Set());
  const [reviewWindow, setReviewWindow] = useState(4);
  const [reviewCursor, setReviewCursor] = useState(0);

  // Measure track width responsively (excludes the left label column + panel).
  useLayoutEffect(() => {
    const el = wrapRef.current;
    if (!el) return undefined;
    const update = () => {
      const track = el.querySelector(".tl-row-track");
      if (track) setTrackWidth(Math.max(320, track.clientWidth || 720));
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  });

  // Keep the Streamlit iframe tall enough for whatever is rendered. App does
  // not re-render when a child form (BasicsForm chips, etc.) grows, so a
  // render-time setFrameHeight() misses it -> the Save button gets clipped.
  // Observe document.body directly so height tracks any content change.
  useEffect(() => {
    const sync = () => setFrameHeight();
    sync();
    const ro = new ResizeObserver(sync);
    ro.observe(document.body);
    return () => ro.disconnect();
  }, []);

  // Base domain: explicit range overrides; missing ends fall back to data extent.
  const baseDomain = useMemo(() => {
    const dates = [];
    for (const p of projects) {
      for (const t of asArray(p.tasks)) if (t.anchor) dates.push(t.anchor);
      for (const m of asArray(p.milestones)) if (m.date) dates.push(m.date);
      const rangeParts = dateParts(p.case?.time_range);
      if (rangeParts.start) dates.push(rangeParts.start);
      if (rangeParts.end) dates.push(rangeParts.end);
    }
    const data = buildDomain(dates, todayMs);
    const rs = parseISO(range.start);
    const re = parseISO(range.end);
    let start = rs != null ? rs : data.start;
    let end = re != null ? re : data.end;
    if (end <= start) end = start + 30 * _DAY_MS;
    return { start, end };
  }, [payload]);

  useEffect(() => {
    setView(baseDomain);
  }, [baseDomain]);

  const dom = view || baseDomain;
  const unit = pickUnit(dom.end - dom.start);
  const ticks = buildTicks(dom.start, dom.end, unit, lang);

  useEffect(() => { setFrameHeight(); });

  // Zoom is engaged only once a project row is selected, and uses a NATIVE
  // non-passive wheel listener so preventDefault() actually stops the page
  // from scrolling. React's synthetic onWheel is passive -> preventDefault is
  // ignored, which caused wheel-zoom to fight page scroll.
  const domRef = useRef(dom);
  domRef.current = dom;
  const zoomEngaged = selectedProject != null;
  const zoomEngagedRef = useRef(zoomEngaged);
  zoomEngagedRef.current = zoomEngaged;

  useEffect(() => {
    const el = mainRef.current;
    if (!el) return undefined;
    const onWheelNative = (e) => {
      if (!zoomEngagedRef.current) return; // no project selected -> page scrolls
      e.preventDefault();
      const track = el.querySelector(".tl-row-track");
      const rect = (track || el).getBoundingClientRect();
      const x = e.clientX - rect.left;
      const d = domRef.current;
      const anchor = xToMs(x, d.start, d.end, trackWidth, PAD_L, PAD_R);
      const factor = e.deltaY > 0 ? 1.15 : 0.87;
      setView(zoomDomain(d.start, d.end, anchor, factor));
    };
    el.addEventListener("wheel", onWheelNative, { passive: false });
    return () => el.removeEventListener("wheel", onWheelNative);
  }, [trackWidth]);

  const onDoubleClick = () => setView(baseDomain);

  // ---- review mode: flat time-ordered task list across selected projects ----
  const reviewTasks = useMemo(() => {
    if (!reviewMode) return [];
    const rangeStart = parseISO(range.start);
    const rangeEnd = parseISO(range.end);
    const out = [];
    for (const p of projects) {
      const pid = p.case?.id;
      if (reviewProjects.size && !reviewProjects.has(pid)) continue;
      for (const t of asArray(p.tasks)) {
        // Apply the same From/To range filter used by the timeline.
        const ms = parseISO(t.anchor);
        if (rangeStart != null && (ms == null || ms < rangeStart)) continue;
        if (rangeEnd != null && (ms == null || ms > rangeEnd)) continue;
        out.push({ ...t, _pid: pid, _ptitle: p.case?.title || pid });
      }
    }
    out.sort((a, b) => (parseISO(a.anchor) || 0) - (parseISO(b.anchor) || 0));
    return out;
  }, [reviewMode, reviewProjects, projects, range.start, range.end]);

  // Keep the cursor in range as the task list changes.
  useEffect(() => {
    if (reviewCursor > reviewTasks.length - 1) {
      setReviewCursor(Math.max(0, reviewTasks.length - 1));
    }
  }, [reviewTasks.length]);

  // Keyboard navigation: up/down step one task; left/right page by the window.
  useEffect(() => {
    if (!reviewMode) return undefined;
    const onKey = (e) => {
      const n = reviewTasks.length;
      if (!n) return;
      if (e.key === "ArrowDown") { e.preventDefault(); setReviewCursor((c) => Math.min(n - 1, c + 1)); }
      else if (e.key === "ArrowUp") { e.preventDefault(); setReviewCursor((c) => Math.max(0, c - 1)); }
      else if (e.key === "ArrowRight") { e.preventDefault(); setReviewCursor((c) => Math.min(n - 1, c + reviewWindow)); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); setReviewCursor((c) => Math.max(0, c - reviewWindow)); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [reviewMode, reviewTasks.length, reviewWindow]);

  const toggleReviewProject = (pid) => {
    setReviewProjects((prev) => {
      const next = new Set(prev);
      if (next.has(pid)) next.delete(pid);
      else next.add(pid);
      return next;
    });
    setReviewCursor(0);
  };

  const showTip = (e, text) => setTip({ x: e.clientX + 12, y: e.clientY + 12, text });
  const hideTip = () => setTip(null);
  const onContext = (e, projectId, kind, id) => {
    e.preventDefault();
    setMenu({ x: e.clientX, y: e.clientY, projectId, kind, id });
  };

  // panel top aligned to the clicked row
  const panelTopFor = (projectId) => {
    const node = rowRefs.current[projectId];
    const wrap = wrapRef.current;
    if (!node || !wrap) return 0;
    return Math.max(0, node.offsetTop - wrap.offsetTop);
  };
  const openPanel = (projectId, spec) => {
    setSelectedProject(projectId);
    setMenu(null);
    setPanel({ projectId, top: panelTopFor(projectId), ...spec });
  };
  const closePanel = () => setPanel(null);

  const projectById = (id) => projects.find((p) => p.case?.id === id);

  return (
    <div className="tl-root" ref={wrapRef} onClick={() => setMenu(null)}>
      {/* range toolbar */}
      <div className="tl-toolbar">
        <span className="tl-hint">{label(labels, "tl_zoom_hint", "Scroll to zoom · double-click to reset")}</span>
        <div className="tl-range">
          <button
            className={`tl-btn tl-btn-sm tl-btn-primary${showCreate ? " is-open" : ""}`}
            onClick={() => setShowCreate((s) => !s)}
          >
            + {label(labels, "create_project", "Create project")}
          </button>
          <button
            className={`tl-btn tl-btn-sm${reviewMode ? " tl-btn-primary" : ""}`}
            onClick={() => { setReviewMode((m) => !m); setReviewCursor(0); }}
          >
            {label(labels, "tl_review_mode", "Review mode")}
          </button>
          <label>{label(labels, "tl_range_start", "From")}</label>
          <input
            type="date"
            value={cleanText(range.start)}
            onChange={(e) => emit(setRangeEvent(e.target.value, cleanText(range.end)))}
          />
          <label>{label(labels, "tl_range_end", "To")}</label>
          <input
            type="date"
            value={cleanText(range.end)}
            onChange={(e) => emit(setRangeEvent(cleanText(range.start), e.target.value))}
          />
          {(range.start || range.end) && (
            <button className="tl-btn tl-btn-sm" onClick={() => emit(setRangeEvent("", ""))}>
              {label(labels, "tl_range_reset", "Reset")}
            </button>
          )}
        </div>
      </div>

      {/* legend + folded summary chips share one compact row */}
      <div className="tl-legend-row">
        <TimelineLegend labels={labels} />
        <SummaryChips summary={summary} labels={labels} />
      </div>

      {showCreate && (
        <CreateProjectForm
          createForm={createForm}
          labels={labels}
          emit={emit}
          onClose={() => setShowCreate(false)}
        />
      )}

      {!projects.length && (
        <div className="tl-empty-hint">{label(labels, "empty_board", "No internal projects yet.")}</div>
      )}

      {reviewMode && (
        <div className="tl-review-bar">
          <span className="tl-review-hint">{label(labels, "tl_review_pick", "Pick projects:")}</span>
          {projects.map((p) => {
            const pid = p.case?.id;
            const on = reviewProjects.size === 0 || reviewProjects.has(pid);
            return (
              <button
                key={pid}
                className={`tl-review-chip${on ? " is-on" : ""}`}
                style={{ "--pc": colorForProject(pid, projects) }}
                onClick={() => toggleReviewProject(pid)}
              >
                <span className="tl-review-dot" />
                {p.case?.title || pid}
              </button>
            );
          })}
          <span className="tl-review-window">
            <label>{label(labels, "tl_review_window", "Window")}</label>
            <select value={reviewWindow} onChange={(e) => setReviewWindow(Number(e.target.value))}>
              {REVIEW_WINDOW_OPTS.map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </span>
          <span className="tl-review-keyshint">{label(labels, "tl_review_keys", "↑↓ step · ←→ page")}</span>
        </div>
      )}

      {projects.length > 0 && (
      <div className={`tl-layout${reviewMode ? " is-review" : ""}`}>
        <div className="tl-main" ref={mainRef} onDoubleClick={onDoubleClick}>
          {!reviewMode && (
            <div className="tl-ticks-header">
              <div className="tl-ticks-spacer" style={{ width: LABEL_W }} />
              <div className="tl-ticks-track">
                <TicksHeader dom={dom} width={trackWidth} ticks={ticks} todayMs={todayMs} />
              </div>
            </div>
          )}
          {reviewMode ? (
            <ReviewList
              tasks={reviewTasks}
              cursor={reviewCursor}
              windowSize={reviewWindow}
              labels={labels}
              projects={projects}
              onPick={(i) => setReviewCursor(i)}
            />
          ) : (
            <div className="tl-rows">
              {projects.map((p) => {
                const pid = p.case?.id;
                return (
                  <div className="tl-row-wrap" key={pid} ref={(n) => { if (n) rowRefs.current[pid] = n; }}>
                    <ProjectRow
                      project={p}
                      labels={labels}
                      dom={dom}
                      width={trackWidth}
                      ticks={ticks}
                      todayMs={todayMs}
                      isSelected={selectedProject === pid}
                      selectedItem={panel && panel.projectId === pid && panel.mode === "detail" ? panel.selected : null}
                      onSelectProject={(id) => setSelectedProject(id)}
                      onSelectItem={(id, sel) => openPanel(id, { mode: "detail", selected: sel })}
                      onContext={onContext}
                      onAddTask={(id) => openPanel(id, { mode: "edit", kind: "task", editMode: "add", initial: { section: "Queue" } })}
                      onAddMilestone={(id) => openPanel(id, { mode: "edit", kind: "milestone", editMode: "add", initial: {} })}
                      onFullInfo={(id) => openPanel(id, { mode: "basics" })}
                      showTip={showTip}
                      hideTip={hideTip}
                    />
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {!reviewMode && panel && (
          <aside className="tl-aside" style={{ marginTop: panel.top }}>
            <PanelContent
              key={`${panel.projectId}:${panel.mode}:${panel.kind || ""}:${panel.initial?.id || panel.selected?.id || ""}`}
              panel={panel}
              project={projectById(panel.projectId)}
              labels={labels}
              settings={settings}
              emit={emit}
              onClose={closePanel}
              setPanel={setPanel}
            />
          </aside>
        )}

        {reviewMode && reviewTasks.length > 0 && (
          <aside className="tl-aside tl-aside-review">
            <ReviewDetail
              tasks={reviewTasks}
              cursor={reviewCursor}
              windowSize={reviewWindow}
              labels={labels}
              projects={projects}
              emit={emit}
              onClose={() => setReviewMode(false)}
            />
          </aside>
        )}
      </div>
      )}

      {tip && <div className="tl-tooltip" style={{ left: tip.x, top: tip.y }}>{tip.text}</div>}

      {menu && (
        <div className="tl-menu" style={{ left: menu.x, top: menu.y }} onClick={(e) => e.stopPropagation()}>
          <button className="tl-btn-danger" onClick={() => {
            if (window.confirm(label(labels, "tl_delete_confirm", "Delete this item?"))) {
              if (menu.kind === "task") emit(deleteTaskEvent(menu.projectId, menu.id));
              else emit(deleteMilestoneEvent(menu.projectId, menu.id));
            }
            setMenu(null);
          }}>{label(labels, "delete_task", "Delete")}</button>
        </div>
      )}
    </div>
  );
}

/* ---- right aside content dispatcher ---- */
function PanelContent({ panel, project, labels, settings, emit, onClose, setPanel }) {
  if (!project) return null;
  const cid = project.case?.id;
  if (panel.mode === "basics") {
    return <BasicsForm project={project} labels={labels} emit={emit} onClose={onClose} />;
  }
  if (panel.mode === "detail") {
    return (
      <DetailPanel
        project={project}
        labels={labels}
        selected={panel.selected}
        settings={settings}
        emit={emit}
        onClose={onClose}
        onEdit={(kind, initial) =>
          setPanel({ ...panel, mode: "edit", kind, editMode: "edit", initial })
        }
      />
    );
  }
  // edit mode (add or edit task/milestone)
  return (
    <EditForm
      kind={panel.kind}
      initial={panel.initial}
      labels={labels}
      settings={settings}
      onCancel={onClose}
      onDelete={panel.editMode === "edit" ? () => {
        if (window.confirm(label(labels, "tl_delete_confirm", "Delete this item?"))) {
          if (panel.kind === "task") emit(deleteTaskEvent(cid, panel.initial.id));
          else emit(deleteMilestoneEvent(cid, panel.initial.id));
        }
        onClose();
      } : null}
      onSubmit={(form) => {
        if (panel.kind === "task") {
          if (panel.editMode === "add") emit(addTaskEvent(cid, form));
          else emit(saveTaskEvent(cid, panel.initial.id, form));
        } else {
          if (panel.editMode === "add") emit(addMilestoneEvent(cid, form));
          else emit(saveMilestoneEvent(cid, panel.initial.id, form));
        }
        onClose();
      }}
    />
  );
}

const root = createRoot(document.getElementById("root"));
root.render(<App />);
