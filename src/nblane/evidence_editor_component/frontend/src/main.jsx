import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";

import "./style.css";
import { filterRows, rowWarnings } from "./filters.js";
import { originColor, cleanText, asArray, label, renderMarkdown } from "./schema.js";
import {
  saveEvidenceEvent,
  addEvidenceEvent,
  deprecateEvidenceEvent,
  linkProjectEvent,
  backfillProjectRefsEvent,
  createProjectFromEvidenceEvent,
  applyMigrationEvent,
  refreshCrystallizedEvent,
  requestAiReformatEvent,
  confirmAiReformatEvent,
  createFromOutputEvent,
  suggestDuplicatesEvent,
} from "./events.js";

const READY = "streamlit:componentReady";
const SET_VALUE = "streamlit:setComponentValue";
const SET_HEIGHT = "streamlit:setFrameHeight";
const RENDER = "streamlit:render";

/* ---- Streamlit bridge ---- */
function sendBack(type, payload) {
  if (window.parent === window) return;
  window.parent.postMessage({ isStreamlitMessage: true, type, ...payload }, "*");
}
function setFrameHeight(height) {
  sendBack(SET_HEIGHT, {
    height: Math.max(420, Math.ceil(height || document.body.scrollHeight || 700)),
  });
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

/* ---- small presentational helpers ---- */
function Badge({ text, color }) {
  return (
    <span className="ee-badge" style={color ? { borderColor: color, color } : undefined}>
      {text}
    </span>
  );
}

function Counter({ icon, n, text, active, onClick }) {
  return (
    <button
      className={`ee-counter${active ? " ee-counter-active" : ""}`}
      onClick={onClick}
      type="button"
      title={text}
    >
      <span className="ee-counter-icon">{icon}</span>
      <span className="ee-counter-n">{n}</span>
      <span className="ee-counter-label">{text}</span>
    </button>
  );
}

/* ---- list item ---- */
function ListItem({ row, selected, labels, onClick }) {
  const origin = cleanText(row.origin) || "—";
  const warns = rowWarnings(row);
  return (
    <button
      type="button"
      className={`ee-li${selected ? " ee-li-sel" : ""}`}
      onClick={onClick}
    >
      <div className="ee-li-top">
        <span className="ee-li-id">{cleanText(row.id)}</span>
        <Badge text={origin} color={originColor(row.origin)} />
        {row.has_project ? (
          <span className="ee-dot ee-dot-ok" title="has project">●</span>
        ) : (
          <span className="ee-dot ee-dot-warn" title="no project">○</span>
        )}
        {row.needs_migration && <span className="ee-flag" title="needs migration">◐</span>}
        {!row.has_original_content && <span className="ee-flag ee-flag-warn" title="missing raw">⚠</span>}
      </div>
      <div className="ee-li-title">{cleanText(row.title) || cleanText(row.id)}</div>
    </button>
  );
}

/* ---- detail editing ---- */
const SCALAR_SELECTS = [
  ["type", "type_options"],
  ["strength", "strength_options"],
  ["confidence", "confidence_options"],
  ["review_status", "review_status_options"],
  ["public_readiness", "public_readiness_options"],
  ["language", "language_options"],
];

function optionList(payload, key) {
  return asArray(payload[key]).map((o) => o.id);
}

function DetailPane({ row, payload, labels, emit, reformatPreview }) {
  const [draft, setDraft] = useState(() => ({ ...row }));
  const [dirty, setDirty] = useState(false);
  const [showRaw, setShowRaw] = useState(false);
  // Default to a rendered preview when formatted_content has text, edit mode
  // when it is empty (so adding content is one click away).
  const [fmtPreview, setFmtPreview] = useState(
    () => !!cleanText(row.formatted_content)
  );

  useEffect(() => {
    setDraft({ ...row });
    setDirty(false);
    setShowRaw(false);
    setFmtPreview(!!cleanText(row.formatted_content));
  }, [row.id]);

  const set = (key, value) => {
    setDraft((d) => ({ ...d, [key]: value }));
    setDirty(true);
  };

  const projectOptions = asArray(payload.project_options);
  const publicProjects = asArray(payload.public_project_options);
  const warns = rowWarnings(draft);

  const projectRefs = asArray(draft.project_refs);
  const toggleProject = (pid) => {
    const has = projectRefs.includes(pid);
    const next = has
      ? projectRefs.filter((p) => p !== pid)
      : [...projectRefs, pid];
    set("project_refs", next);
  };

  const save = () => {
    const fields = {};
    [
      "title",
      "summary",
      "formatted_content",
      "source_excerpt",
      "type",
      "date",
      "url",
      "strength",
      "confidence",
      "review_status",
      "public_readiness",
      "language",
      "origin",
      "origin_ref",
      "origin_detail",
      "project_refs",
    ].forEach((k) => {
      fields[k] = draft[k] ?? (Array.isArray(row[k]) ? [] : "");
    });
    emit(saveEvidenceEvent(row.id, fields));
    setDirty(false);
  };

  return (
    <div className="ee-detail">
      <div className="ee-detail-head">
        <div className="ee-detail-title">{cleanText(draft.title) || cleanText(row.id)}</div>
        <div className="ee-detail-badges">
          <Badge text={cleanText(draft.origin) || "—"} color={originColor(draft.origin)} />
          <Badge text={draft.has_project ? "project" : "no project"} />
          <Badge text={cleanText(draft.review_status) || "—"} />
          {!draft.has_original_content && <Badge text="no raw" />}
        </div>
        <div className="ee-meta">
          id: {cleanText(row.id)} · hash: {cleanText(row.original_content_hash) || "—"} · lang: {cleanText(draft.language) || "—"}
        </div>
      </div>

      {warns.length > 0 && (
        <div className="ee-warn">
          {warns.map((w) => (
            <div key={w} className="ee-warn-line">
              ⚠ {label(labels, w, w)}
            </div>
          ))}
          {warns.includes("ee_project_provenance_reminder") && (
            <button
              type="button"
              className="ee-btn-sm"
              onClick={() => {
                const sug = {
                  suggested_id: `project:${cleanText(row.id)}`,
                  suggested_title: cleanText(draft.title),
                  kind: "work",
                  visibility: "private",
                  summary: cleanText(draft.summary),
                  evidence_ids: [row.id],
                  origin: "resume_parse",
                };
                emit(createProjectFromEvidenceEvent(sug));
              }}
            >
              {label(labels, "ee_create_project_from_evidence", "Create project from this")}
            </button>
          )}
        </div>
      )}

      <Section title={label(labels, "section_basics", "Basics")}>
        <div className="ee-grid">
          {SCALAR_SELECTS.map(([field, optKey]) => (
            <label key={field} className="ee-field">
              <span>{label(labels, `field_${field}`, field)}</span>
              <select value={cleanText(draft[field])} onChange={(e) => set(field, e.target.value)}>
                <option value="" />
                {optionList(payload, optKey).map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </label>
          ))}
          <label className="ee-field">
            <span>{label(labels, "field_date", "date")}</span>
            <input value={cleanText(draft.date)} onChange={(e) => set("date", e.target.value)} />
          </label>
          <label className="ee-field ee-field-wide">
            <span>{label(labels, "field_url", "url")}</span>
            <input value={cleanText(draft.url)} onChange={(e) => set("url", e.target.value)} />
          </label>
        </div>
      </Section>

      <Section title={label(labels, "field_summary", "Summary")}>
        <textarea
          className="ee-ta ee-ta-sm"
          value={cleanText(draft.summary)}
          onChange={(e) => set("summary", e.target.value)}
        />
      </Section>

      <Section title={label(labels, "field_formatted_content", "Formatted content")}>
        <div className="ee-fmt-toolbar">
          <button
            type="button"
            className={`ee-toggle${fmtPreview ? " ee-toggle-on" : ""}`}
            onClick={() => setFmtPreview(true)}
          >
            {label(labels, "ee_preview", "Preview")}
          </button>
          <button
            type="button"
            className={`ee-toggle${!fmtPreview ? " ee-toggle-on" : ""}`}
            onClick={() => setFmtPreview(false)}
          >
            {label(labels, "ee_edit", "Edit")}
          </button>
        </div>
        {fmtPreview ? (
          cleanText(draft.formatted_content) ? (
            <div
              className="ee-md"
              dangerouslySetInnerHTML={{
                __html: renderMarkdown(draft.formatted_content),
              }}
            />
          ) : (
            <div className="ee-muted">
              {label(labels, "ee_formatted_content_missing", "No formatted content yet.")}
            </div>
          )
        ) : (
          <textarea
            className="ee-ta ee-ta-wrap"
            value={cleanText(draft.formatted_content)}
            onChange={(e) => set("formatted_content", e.target.value)}
          />
        )}
      </Section>

      <Section title={label(labels, "field_original_content", "Original content")}>
        <button type="button" className="ee-btn-sm" onClick={() => setShowRaw((s) => !s)}>
          {showRaw ? "▾" : "▸"} {cleanText(draft.original_content).length} chars
          {draft.original_language ? ` · ${draft.original_language}` : ""}
        </button>
        {showRaw && (
          <textarea
            className="ee-ta ee-mono ee-ta-ro"
            value={cleanText(draft.original_content)}
            readOnly
          />
        )}
      </Section>

      <Section title={label(labels, "section_links", "Links")}>
        <label className="ee-field ee-field-wide">
          <span>{label(labels, "field_source_excerpt", "source_excerpt")}</span>
          <input
            value={cleanText(draft.source_excerpt)}
            onChange={(e) => set("source_excerpt", e.target.value)}
          />
        </label>
        <div className="ee-chips-label">{label(labels, "ee_link_project", "Internal project")}</div>
        <div className="ee-chips">
          {projectOptions.map((opt) => {
            const on = projectRefs.includes(opt.id);
            return (
              <button
                key={opt.id}
                type="button"
                className={`ee-chip${on ? " ee-chip-on" : ""}`}
                onClick={() => toggleProject(opt.id)}
              >
                {cleanText(opt.label) || opt.id}
              </button>
            );
          })}
          {projectOptions.length === 0 && <span className="ee-muted">—</span>}
        </div>
        {publicProjects.length > 0 && (
          <div className="ee-public-usage">
            {label(labels, "ee_public_project_distinction", "Public usage (read-only):")}{" "}
            {publicProjects
              .filter((p) => asArray(p.evidence_refs).includes(row.id))
              .map((p) => cleanText(p.label) || p.id)
              .join(", ") || "—"}
          </div>
        )}
      </Section>

      <Section title={label(labels, "section_ai", "AI / tools")}>
        <div className="ee-row-btns">
          <button
            type="button"
            className="ee-btn-sm"
            onClick={() => emit(requestAiReformatEvent(row.id))}
          >
            {label(labels, "ee_ai_reformat", "AI reformat")}
          </button>
          <button
            type="button"
            className="ee-btn-sm"
            onClick={() => emit(suggestDuplicatesEvent(row.id))}
          >
            {label(labels, "ee_duplicate_candidates", "Find duplicates")}
          </button>
        </div>
        {reformatPreview && reformatPreview.id === row.id && (
          <div className="ee-reformat">
            <div className="ee-reformat-head">{label(labels, "ee_ai_reformat", "AI reformat")} →</div>
            {asArray(payload.__reformat_fields).length === 0 && (
              <ReformatPreview
                preview={reformatPreview}
                labels={labels}
                onConfirm={(fields) => emit(confirmAiReformatEvent(row.id, fields))}
              />
            )}
          </div>
        )}
      </Section>

      <div className="ee-detail-actions">
        <button type="button" className="ee-btn-primary" disabled={!dirty} onClick={save}>
          {label(labels, "ee_save", "Save")}
        </button>
        <button
          type="button"
          className="ee-btn-danger"
          onClick={() => {
            if (window.confirm(label(labels, "ee_deprecate_confirm", "Deprecate this evidence?"))) {
              emit(deprecateEvidenceEvent(row.id));
            }
          }}
        >
          {label(labels, "ee_deprecate", "Deprecate")}
        </button>
        {dirty && <span className="ee-unsaved">● {label(labels, "ee_unsaved", "unsaved changes")}</span>}
      </div>
    </div>
  );
}

function ReformatPreview({ preview, labels, onConfirm }) {
  const [fields, setFields] = useState(() => ({ ...(preview.fields || {}) }));
  useEffect(() => setFields({ ...(preview.fields || {}) }), [preview]);
  const keys = Object.keys(fields);
  if (keys.length === 0) return <div className="ee-muted">—</div>;
  return (
    <div>
      {keys.map((k) => (
        <label key={k} className="ee-field ee-field-wide">
          <span>{label(labels, `field_${k}`, k)}</span>
          <textarea
            className="ee-ta ee-ta-sm"
            value={cleanText(fields[k])}
            onChange={(e) => setFields((f) => ({ ...f, [k]: e.target.value }))}
          />
        </label>
      ))}
      <button type="button" className="ee-btn-primary" onClick={() => onConfirm(fields)}>
        {label(labels, "ee_ai_reformat_confirm", "Confirm reformat")}
      </button>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="ee-section">
      <div className="ee-section-h">{title}</div>
      {children}
    </div>
  );
}

/* ---- add evidence (manual_daily first-class entry) ---- */
function AddForm({ payload, labels, emit, onClose }) {
  const [f, setF] = useState({
    origin: "manual_daily",
    title: "",
    date: "",
    summary: "",
    original_content: "",
    origin_detail: "",
    public_readiness: "private",
  });
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  return (
    <div className="ee-modal">
      <div className="ee-modal-box">
        <div className="ee-section-h">{label(labels, "ee_add_evidence", "Add evidence")}</div>
        <label className="ee-field ee-field-wide">
          <span>{label(labels, "field_origin", "origin")}</span>
          <select value={f.origin} onChange={(e) => set("origin", e.target.value)}>
            {optionList(payload, "origin_options").map((o) => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>
        </label>
        <label className="ee-field ee-field-wide">
          <span>{label(labels, "field_title", "title")}</span>
          <input value={f.title} onChange={(e) => set("title", e.target.value)} />
        </label>
        <label className="ee-field ee-field-wide">
          <span>{label(labels, "field_summary", "summary")}</span>
          <textarea className="ee-ta ee-ta-sm" value={f.summary} onChange={(e) => set("summary", e.target.value)} />
        </label>
        <label className="ee-field ee-field-wide">
          <span>{label(labels, "field_original_content", "original_content")}</span>
          <textarea className="ee-ta ee-mono" value={f.original_content} onChange={(e) => set("original_content", e.target.value)} />
        </label>
        <div className="ee-muted">{label(labels, "ee_project_provenance_reminder", "Link or confirm a project source.")}</div>
        <div className="ee-detail-actions">
          <button
            type="button"
            className="ee-btn-primary"
            disabled={!f.title.trim()}
            onClick={() => {
              emit(addEvidenceEvent(f));
              onClose();
            }}
          >
            {label(labels, "ee_add_evidence", "Add evidence")}
          </button>
          <button type="button" className="ee-btn-sm" onClick={onClose}>
            {label(labels, "ee_cancel", "Cancel")}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---- main app ---- */
function App() {
  const [args, setArgs] = useState({ payload: {} });
  useEffect(() => {
    initStreamlitBridge(setArgs);
  }, []);
  const payload = args.payload || {};
  const emit = (event) => setComponentValue(event);

  const labels = payload.labels || {};
  const settings = payload.settings || {};
  const rows = useMemo(() => asArray(payload.evidence_rows), [payload]);
  const summary = payload.migration_summary || {};
  const suggestions = asArray(payload.project_suggestions);
  const outputs = asArray(payload.output_options);

  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({});
  const [selectedId, setSelectedId] = useState(null);
  const [showAdd, setShowAdd] = useState(false);
  const [showOutputs, setShowOutputs] = useState(false);

  // After a fragment rerun re-mounts the iframe, restore the row the user was
  // acting on (Python echoes it via settings.last_selected_id) so the detail
  // pane does not collapse and the page does not feel like it "jumped".
  const lastSelectedId = cleanText(settings.last_selected_id);
  useEffect(() => {
    if (selectedId) return;
    if (!lastSelectedId) return;
    if (rows.some((r) => r.id === lastSelectedId)) {
      setSelectedId(lastSelectedId);
    }
  }, [lastSelectedId, rows, selectedId]);

  const rootRef = useRef(null);
  useEffect(() => {
    const h = rootRef.current ? rootRef.current.scrollHeight : 0;
    setFrameHeight(h + 24);
  });

  const visible = useMemo(() => filterRows(rows, query, filters), [rows, query, filters]);
  const selected = useMemo(
    () => visible.find((r) => r.id === selectedId) || rows.find((r) => r.id === selectedId) || null,
    [visible, rows, selectedId]
  );

  const setFilter = (k, v) => setFilters((f) => ({ ...f, [k]: v }));
  const toggleFilter = (k) => setFilters((f) => ({ ...f, [k]: !f[k] }));

  const reformatPreview = payload.reformat_preview || null;

  return (
    <div className="ee-root" ref={rootRef}>
      {/* toolbar */}
      <div className="ee-toolbar">
        <div className="ee-toolbar-btns">
          <button type="button" className="ee-btn" onClick={() => setShowAdd(true)}>
            + {label(labels, "ee_add_evidence", "Add evidence")}
          </button>
          <button type="button" className="ee-btn" onClick={() => emit(applyMigrationEvent(null))}>
            {label(labels, "ee_run_migration", "Run migration")}
          </button>
          <button type="button" className="ee-btn" onClick={() => emit(refreshCrystallizedEvent(null))}>
            {label(labels, "ee_refresh_crystallized_tasks", "Refresh crystallized")}
          </button>
          <button type="button" className="ee-btn" onClick={() => setShowOutputs((s) => !s)}>
            {label(labels, "ee_create_from_output", "Create from output")}
          </button>
          {visible.some((r) => r.needs_migration) && (
            <button
              type="button"
              className="ee-btn"
              onClick={() => emit(backfillProjectRefsEvent(null))}
            >
              {label(labels, "ee_backfill_project", "Backfill project refs")}
            </button>
          )}
        </div>
        <div className="ee-counters">
          <Counter icon="◐" n={summary.needs_migration || 0} text={label(labels, "ee_filter_needs_migration", "Needs migration")} active={!!filters.needsMigration} onClick={() => toggleFilter("needsMigration")} />
          <Counter icon="⚠" n={summary.missing_raw || 0} text={label(labels, "ee_original_content_missing", "Missing raw")} />
          <Counter icon="⚑" n={summary.resume_manual_unassigned || 0} text={label(labels, "ee_project_provenance_reminder", "Unassigned project")} />
          <Counter icon="⬚" n={summary.crystallized_without_evidence || 0} text={label(labels, "ee_refresh_crystallized_tasks", "Crystallized w/o evidence")} />
          <Counter icon="◇" n={summary.output_candidates || 0} text={label(labels, "ee_create_from_output", "Output candidates")} />
        </div>
      </div>

      {suggestions.length > 0 && (
        <div className="ee-suggest-banner">
          💡 {suggestions.length} {label(labels, "ee_create_project_from_evidence", "project suggestion(s)")}
          {suggestions.slice(0, 1).map((s) => (
            <button
              key={s.suggested_id}
              type="button"
              className="ee-btn-sm"
              onClick={() => emit(createProjectFromEvidenceEvent(s))}
            >
              {cleanText(s.suggested_title)} →
            </button>
          ))}
        </div>
      )}

      {showOutputs && (
        <div className="ee-output-strip">
          {outputs.length === 0 && <span className="ee-muted">{label(labels, "ee_no_outputs", "No outputs")}</span>}
          {outputs.map((o) => (
            <button
              key={o.id}
              type="button"
              className="ee-chip"
              onClick={() => {
                emit(createFromOutputEvent(o.id));
                setShowOutputs(false);
              }}
            >
              {cleanText(o.label)}
            </button>
          ))}
        </div>
      )}

      <div className="ee-body">
        {/* list */}
        <div className="ee-list">
          <input
            className="ee-search"
            placeholder={label(labels, "ee_search", "Search title / summary…")}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="ee-filters">
            <FilterSelect payload={payload} optKey="origin_options" value={filters.origin} onChange={(v) => setFilter("origin", v)} placeholder={label(labels, "ee_filter_origin", "origin")} />
            <FilterSelect payload={payload} optKey="type_options" value={filters.type} onChange={(v) => setFilter("type", v)} placeholder={label(labels, "ee_filter_type", "type")} />
            <FilterSelect payload={payload} optKey="review_status_options" value={filters.review_status} onChange={(v) => setFilter("review_status", v)} placeholder={label(labels, "ee_filter_review_status", "status")} />
            <FilterSelect payload={payload} optKey="language_options" value={filters.language} onChange={(v) => setFilter("language", v)} placeholder={label(labels, "ee_filter_language", "lang")} />
            <label className="ee-check">
              <input type="checkbox" checked={!!filters.hasProject} onChange={() => toggleFilter("hasProject")} />
              {label(labels, "ee_filter_has_project", "has project")}
            </label>
            <label className="ee-check">
              <input type="checkbox" checked={!!filters.needsMigration} onChange={() => toggleFilter("needsMigration")} />
              {label(labels, "ee_filter_needs_migration", "needs migration")}
            </label>
          </div>
          <div className="ee-list-scroll">
            {visible.length === 0 && <div className="ee-empty">{label(labels, "ee_empty", "No evidence matches.")}</div>}
            {visible.map((row) => (
              <ListItem
                key={row.id}
                row={row}
                labels={labels}
                selected={row.id === selectedId}
                onClick={() => setSelectedId(row.id)}
              />
            ))}
          </div>
        </div>

        {/* detail */}
        <div className="ee-detail-wrap">
          {selected ? (
            <DetailPane row={selected} payload={payload} labels={labels} emit={emit} reformatPreview={reformatPreview} />
          ) : (
            <div className="ee-empty ee-empty-detail">{label(labels, "ee_select_hint", "Select an evidence row to edit.")}</div>
          )}
        </div>
      </div>

      {showAdd && <AddForm payload={payload} labels={labels} emit={emit} onClose={() => setShowAdd(false)} />}
    </div>
  );
}

function FilterSelect({ payload, optKey, value, onChange, placeholder }) {
  return (
    <select className="ee-fsel" value={value || ""} onChange={(e) => onChange(e.target.value)}>
      <option value="">{placeholder}</option>
      {optionList(payload, optKey).map((o) => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  );
}

const root = createRoot(document.getElementById("root"));
root.render(<App />);
