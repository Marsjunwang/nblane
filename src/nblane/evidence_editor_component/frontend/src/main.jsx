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
  linkSkillsEvent,
  suggestSkillsEvent,
  applyMigrationEvent,
  refreshCrystallizedEvent,
  prepareDoneTaskEvidenceEvent,
  applyDoneTaskEvidenceEvent,
  doneTasksToEvidenceEvent,
  bulkApplyEvent,
  requestAiReformatEvent,
  confirmAiReformatEvent,
  bulkRequestAiReformatEvent,
  bulkConfirmAiReformatEvent,
  bulkCreateFromOutputEvent,
  ignoreOutputCandidatesEvent,
  restoreOutputCandidatesEvent,
  suggestDuplicatesEvent,
  mergeOrDeprecateEvent,
  dismissDuplicateEvent,
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
function ListItem({ row, selected, labels, onClick, batch, checked, onCheck }) {
  const origin = cleanText(row.origin) || "—";
  const warns = rowWarnings(row);
  return (
    <div className={`ee-li-row${batch ? " ee-li-row-batch" : ""}`}>
      {batch && (
        <input
          type="checkbox"
          className="ee-li-check"
          checked={!!checked}
          onChange={(e) => onCheck(row.id, e.target.checked)}
          aria-label={cleanText(row.id)}
        />
      )}
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
          {row.missing_date && <span className="ee-flag ee-flag-warn" title="missing date">D</span>}
          {row.missing_formatted_content && <span className="ee-flag ee-flag-warn" title="missing formatted content">F</span>}
          {row.source_conflict && <span className="ee-flag ee-flag-warn" title="source conflict">S</span>}
          {row.dangling_task_source && <span className="ee-flag ee-flag-danger" title="dangling task source">!</span>}
        </div>
        <div className="ee-li-title">{cleanText(row.title) || cleanText(row.id)}</div>
      </button>
    </div>
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
  const skillOptions = asArray(payload.skill_options);
  const warns = rowWarnings(draft);

  const projectRefs = asArray(draft.project_refs);
  const toggleProject = (pid) => {
    const has = projectRefs.includes(pid);
    const next = has ? [] : [pid];
    set("project_refs", next);
  };

  // Skill refs live on skill-tree nodes, not on the evidence row, so they are
  // saved immediately on toggle (no LLM). Track locally for optimistic UI
  // because the payload only refreshes on the next Streamlit rerun.
  const [skillRefs, setSkillRefs] = useState(() => asArray(row.skill_refs));
  useEffect(() => {
    setSkillRefs(asArray(row.skill_refs));
  }, [row.id]);
  const toggleSkill = (sid) => {
    const has = skillRefs.includes(sid);
    const next = has
      ? skillRefs.filter((s) => s !== sid)
      : [...skillRefs, sid];
    setSkillRefs(next);
    emit(linkSkillsEvent(row.id, next));
  };

  // Skill recall: rule suggestions ship on the row; an optional LLM pass can
  // be stashed back into payload.skill_suggestion_llm for the active row.
  const [showAllSkills, setShowAllSkills] = useState(false);
  useEffect(() => {
    setShowAllSkills(false);
  }, [row.id]);
  const skillLabelById = useMemo(() => {
    const m = {};
    skillOptions.forEach((o) => {
      m[o.id] = cleanText(o.label) || o.id;
    });
    return m;
  }, [skillOptions]);
  const llmSuggest =
    payload.skill_suggestion_llm && payload.skill_suggestion_llm.id === row.id
      ? asArray(payload.skill_suggestion_llm.suggestions)
      : [];
  const skillSuggestions = useMemo(() => {
    const merged = [];
    const seen = new Set();
    [...asArray(row.skill_suggestions), ...llmSuggest].forEach((s) => {
      const id = s && s.id;
      if (!id || seen.has(id) || skillRefs.includes(id)) return;
      seen.add(id);
      merged.push({
        id,
        label: skillLabelById[id] || cleanText(s.label) || id,
        score: Number(s.score) || 0,
        source: s.source || "rule",
      });
    });
    return merged;
  }, [row.id, row.skill_suggestions, llmSuggest, skillRefs, skillLabelById]);

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
          {draft.project_resolution_status === "project_without_goal" && <Badge text="project no goal" />}
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
                className={`ee-chip${on ? " ee-chip-on" : ""}${opt.has_goal === false ? " ee-chip-warn" : ""}`}
                onClick={() => toggleProject(opt.id)}
                title={opt.has_goal === false ? "Project has no goal_refs" : ""}
              >
                {cleanText(opt.label) || opt.id}
                {opt.has_goal === false ? " · no goal" : ""}
              </button>
            );
          })}
          {projectOptions.length === 0 && <span className="ee-muted">—</span>}
        </div>
        <div className="ee-chips-label">
          {label(labels, "ee_link_skill", "Skills")}
          <button
            type="button"
            className="ee-btn-link"
            onClick={() => emit(suggestSkillsEvent(row.id))}
            title={label(labels, "ee_skill_suggest_llm_hint", "Ask AI for more skill suggestions")}
          >
            {label(labels, "ee_skill_suggest_llm", "AI suggest")}
          </button>
        </div>
        {skillSuggestions.length > 0 && (
          <div className="ee-skill-suggest">
            <span className="ee-skill-suggest-tag">
              {label(labels, "ee_skill_suggested", "Suggested")}
            </span>
            {skillSuggestions.map((s) => (
              <button
                key={s.id}
                type="button"
                className={`ee-chip ee-chip-suggest${s.source === "llm" ? " ee-chip-llm" : ""}`}
                onClick={() => toggleSkill(s.id)}
                title={`${s.source} · ${s.score}`}
              >
                + {s.label}
              </button>
            ))}
          </div>
        )}
        <div className="ee-chips">
          {skillRefs.map((sid) => (
            <button
              key={sid}
              type="button"
              className="ee-chip ee-chip-on"
              onClick={() => toggleSkill(sid)}
            >
              {skillLabelById[sid] || sid}
            </button>
          ))}
          {skillRefs.length === 0 && skillSuggestions.length === 0 && (
            <span className="ee-muted">—</span>
          )}
        </div>
        {skillOptions.length > 0 && (
          <div className="ee-skill-all">
            <button
              type="button"
              className="ee-btn-link"
              onClick={() => setShowAllSkills((s) => !s)}
            >
              {showAllSkills ? "▾" : "▸"}{" "}
              {label(labels, "ee_skill_show_all", "All skills")} ({skillOptions.length})
            </button>
            {showAllSkills && (
              <div className="ee-chips ee-chips-all">
                {skillOptions.map((opt) => {
                  const on = skillRefs.includes(opt.id);
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      className={`ee-chip${on ? " ee-chip-on" : ""}`}
                      onClick={() => toggleSkill(opt.id)}
                    >
                      {cleanText(opt.label) || opt.id}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}
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
    formatted_content: "",
    origin_detail: "",
    public_readiness: "private",
    project_refs: [],
  });
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  const projectOptions = asArray(payload.project_options);
  const ready =
    f.title.trim() &&
    f.date.trim() &&
    f.original_content.trim() &&
    f.formatted_content.trim() &&
    asArray(f.project_refs).length === 1;
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
          <span>{label(labels, "field_date", "date")}</span>
          <input value={f.date} onChange={(e) => set("date", e.target.value)} />
        </label>
        <label className="ee-field ee-field-wide">
          <span>{label(labels, "field_summary", "summary")}</span>
          <textarea className="ee-ta ee-ta-sm" value={f.summary} onChange={(e) => set("summary", e.target.value)} />
        </label>
        <label className="ee-field ee-field-wide">
          <span>{label(labels, "field_formatted_content", "formatted_content")}</span>
          <textarea className="ee-ta ee-ta-sm" value={f.formatted_content} onChange={(e) => set("formatted_content", e.target.value)} />
        </label>
        <label className="ee-field ee-field-wide">
          <span>{label(labels, "field_original_content", "original_content")}</span>
          <textarea className="ee-ta ee-mono" value={f.original_content} onChange={(e) => set("original_content", e.target.value)} />
        </label>
        <div className="ee-chips-label">{label(labels, "ee_link_project", "Internal project")}</div>
        <div className="ee-chips">
          {projectOptions.map((opt) => (
            <button
              key={opt.id}
              type="button"
              className={`ee-chip${asArray(f.project_refs).includes(opt.id) ? " ee-chip-on" : ""}${opt.has_goal === false ? " ee-chip-warn" : ""}`}
              onClick={() => set("project_refs", asArray(f.project_refs).includes(opt.id) ? [] : [opt.id])}
              title={opt.has_goal === false ? "Project has no goal_refs" : ""}
            >
              {cleanText(opt.label) || opt.id}
              {opt.has_goal === false ? " · no goal" : ""}
            </button>
          ))}
        </div>
        <div className="ee-detail-actions">
          <button
            type="button"
            className="ee-btn-primary"
            disabled={!ready}
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

/* ---- duplicate review panel (suggest-and-confirm) ---- */
const MERGE_FIELD_OPTS = [
  "summary",
  "formatted_content",
  "original_content",
  "url",
  "date",
  "project_refs",
  "source_refs",
  "kanban_refs",
];

function DuplicatePair({ cand, rowsById, labels, emit }) {
  const a = rowsById[cand.a] || { id: cand.a };
  const b = rowsById[cand.b] || { id: cand.b };
  const [keep, setKeep] = useState(cand.recommend_keep || cand.a);
  const [mergeFields, setMergeFields] = useState([]);
  const other = keep === a.id ? b : a;
  const keptRow = keep === a.id ? a : b;

  const toggleField = (f) =>
    setMergeFields((prev) =>
      prev.includes(f) ? prev.filter((x) => x !== f) : [...prev, f]
    );

  const Row = ({ row, isKeep }) => (
    <div className={`ee-dup-card${isKeep ? " ee-dup-keep" : ""}`}>
      <div className="ee-dup-card-head">
        <input
          type="radio"
          checked={keep === row.id}
          onChange={() => setKeep(row.id)}
        />
        <span className="ee-li-id">{row.id}</span>
        <Badge text={cleanText(row.origin) || "—"} color={originColor(row.origin)} />
        {isKeep && <span className="ee-dup-keep-tag">{label(labels, "ee_dup_keep", "keep")}</span>}
      </div>
      <div className="ee-dup-title">{cleanText(row.title) || row.id}</div>
      <div className="ee-dup-prov">
        {row.has_original_content ? "✓ raw" : "⚠ no raw"} ·{" "}
        {cleanText(row.review_status) || "—"}
      </div>
    </div>
  );

  return (
    <div className="ee-dup-pair">
      <div className="ee-dup-reason">
        <span className="ee-dup-score">{Math.round((cand.score || 0) * 100)}%</span>
        {cleanText(cand.reason)}
      </div>
      <div className="ee-dup-cards">
        <Row row={a} isKeep={keep === a.id} />
        <Row row={b} isKeep={keep === b.id} />
      </div>
      <details className="ee-dup-merge">
        <summary>{label(labels, "ee_dup_merge_fields", "Merge fields into kept (optional)")}</summary>
        <div className="ee-dup-fields">
          {MERGE_FIELD_OPTS.map((f) => (
            <label key={f} className="ee-check">
              <input
                type="checkbox"
                checked={mergeFields.includes(f)}
                onChange={() => toggleField(f)}
              />
              {label(labels, `field_${f}`, f)}
            </label>
          ))}
        </div>
      </details>
      <div className="ee-dup-actions">
        <button
          type="button"
          className="ee-btn-primary"
          onClick={() => emit(mergeOrDeprecateEvent(keep, other.id, mergeFields.length ? mergeFields : null))}
        >
          {mergeFields.length
            ? label(labels, "ee_dup_merge_deprecate", "Merge → deprecate other")
            : label(labels, "ee_dup_deprecate_other", "Deprecate other")}
        </button>
        <button
          type="button"
          className="ee-btn-sm"
          onClick={() => emit(dismissDuplicateEvent(a.id, b.id))}
        >
          {label(labels, "ee_dup_not_duplicate", "Not a duplicate")}
        </button>
      </div>
    </div>
  );
}

function DuplicatePanel({ candidates, rowsById, labels, emit }) {
  return (
    <div className="ee-dup-panel">
      <div className="ee-section-h">
        {label(labels, "ee_duplicate_candidates", "Duplicate candidates")} ({candidates.length})
      </div>
      {candidates.map((c) => (
        <DuplicatePair
          key={`${c.a}|${c.b}`}
          cand={c}
          rowsById={rowsById}
          labels={labels}
          emit={emit}
        />
      ))}
    </div>
  );
}

function BulkReformatPreview({ preview, labels, emit }) {
  if (!preview) return null;
  const items = asArray(preview.items);
  return (
    <div className="ee-reformat ee-bulk-reformat-preview">
      <div className="ee-section-h">
        {label(labels, "ee_bulk_reformat", "AI reformat selected")} ({preview.valid_count || 0})
      </div>
      <div className="ee-done-preview-list">
        {items.map((item) => (
          <div key={item.id} className={`ee-preview-row${item.error ? " ee-preview-invalid" : ""}`}>
            <div className="ee-preview-title">{item.id} · {cleanText(item.title)}</div>
            {item.error ? (
              <div className="ee-preview-blockers">{item.error}</div>
            ) : (
              <div className="ee-preview-summary">
                {Object.keys(item.fields || {}).join(", ")}
              </div>
            )}
          </div>
        ))}
      </div>
      <button
        type="button"
        className="ee-btn-primary"
        disabled={!preview.valid_count}
        onClick={() => emit(bulkConfirmAiReformatEvent(preview.preview_id))}
      >
        {label(labels, "ee_ai_reformat_confirm", "Confirm reformat")}
      </button>
    </div>
  );
}

/* ---- bulk action bar (batch mode) ---- */
function BulkActionBar({ ids, payload, labels, emit, onClear }) {
  const [field, setField] = useState("review_status");
  const [value, setValue] = useState("");
  const BULK_FIELDS = [
    ["review_status", "review_status_options"],
    ["public_readiness", "public_readiness_options"],
    ["strength", "strength_options"],
    ["confidence", "confidence_options"],
  ];
  const optKey = (BULK_FIELDS.find(([f]) => f === field) || [])[1];
  return (
    <div className="ee-bulkbar">
      <span className="ee-bulkbar-count">
        {ids.length} {label(labels, "ee_bulk_selected", "selected")}
      </span>
      <select value={field} onChange={(e) => { setField(e.target.value); setValue(""); }}>
        {BULK_FIELDS.map(([f]) => (
          <option key={f} value={f}>{label(labels, `field_${f}`, f)}</option>
        ))}
      </select>
      <select value={value} onChange={(e) => setValue(e.target.value)}>
        <option value="" />
        {optionList(payload, optKey).map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
      <button
        type="button"
        className="ee-btn-sm ee-btn-primary"
        disabled={!value || ids.length === 0}
        onClick={() => emit(bulkApplyEvent(ids, { field, value }))}
      >
        {label(labels, "ee_bulk_apply", "Apply to selected")}
      </button>
      <span className="ee-bulkbar-sep" />
      <button
        type="button"
        className="ee-btn-sm"
        disabled={ids.length === 0}
        onClick={() => emit(bulkRequestAiReformatEvent(ids))}
      >
        {label(labels, "ee_bulk_reformat", "AI reformat selected")}
      </button>
      <button
        type="button"
        className="ee-btn-sm ee-btn-danger"
        disabled={ids.length === 0}
        onClick={() => {
          if (window.confirm(label(labels, "ee_bulk_deprecate_confirm", "Deprecate selected rows?"))) {
            emit(bulkApplyEvent(ids, { action: "deprecate" }));
          }
        }}
      >
        {label(labels, "ee_bulk_deprecate", "Deprecate")}
      </button>
      <button type="button" className="ee-btn-sm" onClick={onClear}>
        {label(labels, "ee_bulk_clear", "Clear")}
      </button>
    </div>
  );
}

/* ---- Done tasks -> evidence picker (AI preview by default) ---- */
function DoneTasksPicker({ tasks, labels, emit, onClose }) {
  const [picked, setPicked] = useState(
    () => new Set(tasks.filter((t) => t.recommended).map((t) => t.id))
  );
  const [mark, setMark] = useState(true);
  const toggle = (id) =>
    setPicked((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  return (
    <div className="ee-modal">
      <div className="ee-modal-box">
        <div className="ee-section-h">
          {label(labels, "ee_done_tasks_title", "Done tasks → evidence")}
        </div>
        <div className="ee-muted">
          {label(labels, "ee_done_tasks_hint", "AI previews Done evidence first. Blocked tasks need date, project, and project goal before evidence can be created.")}
        </div>
        <div className="ee-done-list">
          {tasks.length === 0 && (
            <span className="ee-muted">{label(labels, "ee_done_tasks_none", "No Done tasks.")}</span>
          )}
          {tasks.map((t) => (
            <label key={t.id} className={`ee-check ee-done-row${t.blocked ? " ee-done-blocked" : ""}`}>
              <input
                type="checkbox"
                checked={picked.has(t.id)}
                disabled={!!t.blocked}
                onChange={() => toggle(t.id)}
              />
              <span className="ee-done-main">
                <span className="ee-done-title">{cleanText(t.title) || t.id}</span>
                <span className="ee-done-meta">
                  {cleanText(t.completed_on) || "no date"} · {cleanText(t.project_id) || "no project"}
                </span>
                {asArray(t.blockers).length > 0 && (
                  <span className="ee-done-blockers">
                    {asArray(t.blockers).join(" ")}
                  </span>
                )}
              </span>
              {t.crystallized && <span className="ee-flag" title="crystallized">◆</span>}
              {t.has_evidence && (
                <span className="ee-badge ee-badge-muted">
                  {label(labels, "ee_done_has_evidence", "has evidence")}
                </span>
              )}
            </label>
          ))}
        </div>
        <label className="ee-check">
          <input type="checkbox" checked={mark} onChange={() => setMark((m) => !m)} />
          {label(labels, "ee_done_mark_crystallized", "Mark selected tasks crystallized after save")}
        </label>
        <div className="ee-detail-actions">
          <button
            type="button"
            className="ee-btn-primary"
            disabled={picked.size === 0}
            onClick={() => {
              emit(prepareDoneTaskEvidenceEvent(Array.from(picked)));
              onClose();
            }}
          >
            {label(labels, "ee_done_ai_preview", "AI preview")} ({picked.size})
          </button>
          <button
            type="button"
            className="ee-btn-sm"
            disabled={picked.size === 0}
            onClick={() => {
              if (window.confirm(label(labels, "ee_done_fallback_confirm", "Use deterministic fallback without AI grading?"))) {
                emit(doneTasksToEvidenceEvent(Array.from(picked), mark));
                onClose();
              }
            }}
          >
            {label(labels, "ee_done_fallback", "Fallback")}
          </button>
          <button type="button" className="ee-btn-sm" onClick={onClose}>
            {label(labels, "ee_cancel", "Cancel")}
          </button>
        </div>
      </div>
    </div>
  );
}

function DonePreviewPanel({ preview, labels, emit }) {
  const [mark, setMark] = useState(true);
  if (!preview) return null;
  const rows = asArray(preview.rows);
  const blockers = asArray(preview.task_blockers);
  const blockingErrors = asArray(preview.blocking_errors);
  return (
    <div className={`ee-done-preview${preview.can_accept ? "" : " ee-done-preview-blocked"}`}>
      <div className="ee-section-h">
        {label(labels, "ee_done_ai_preview", "Done AI preview")}
      </div>
      {preview.ai_error && <div className="ee-warn-line">{preview.ai_error}</div>}
      {blockingErrors.map((err) => (
        <div key={err} className="ee-warn-line">{err}</div>
      ))}
      {blockers.length > 0 && (
        <div className="ee-done-preview-list">
          {blockers.map((item) => (
            <div key={item.task_id} className="ee-preview-row ee-preview-invalid">
              <div className="ee-preview-title">{cleanText(item.title) || item.task_id}</div>
              <div className="ee-preview-blockers">{asArray(item.blockers).join(" ")}</div>
            </div>
          ))}
        </div>
      )}
      {rows.length > 0 && (
        <div className="ee-done-preview-list">
          {rows.map((item, idx) => {
            const row = item.row || {};
            return (
              <div key={`${item.task_id}-${idx}`} className={`ee-preview-row${item.valid ? "" : " ee-preview-invalid"}`}>
                <div className="ee-preview-title">
                  {item.valid ? "✓" : "!"} {cleanText(row.title) || cleanText(item.task_title) || item.task_id}
                </div>
                <div className="ee-preview-meta">
                  {cleanText(row.date) || "no date"} · {asArray(row.project_refs).join(", ") || "no project"} · {cleanText(row.strength) || "no strength"} / {cleanText(row.confidence) || "no confidence"}
                </div>
                {cleanText(row.summary) && <div className="ee-preview-summary">{cleanText(row.summary)}</div>}
                {asArray(item.blockers).length > 0 && (
                  <div className="ee-preview-blockers">{asArray(item.blockers).join(" ")}</div>
                )}
              </div>
            );
          })}
        </div>
      )}
      <div className="ee-preview-meta">
        {preview.valid_count || 0} valid · {preview.invalid_count || 0} invalid · {asArray(preview.node_updates).length} skill link suggestions
      </div>
      <label className="ee-check">
        <input type="checkbox" checked={mark} onChange={() => setMark((m) => !m)} />
        {label(labels, "ee_done_mark_crystallized", "Mark accepted tasks crystallized after save")}
      </label>
      <div className="ee-row-btns">
        <button
          type="button"
          className="ee-btn-primary"
          disabled={!preview.can_accept}
          onClick={() => emit(applyDoneTaskEvidenceEvent(preview.preview_id, mark))}
        >
          {label(labels, "ee_done_accept_valid", "Accept all valid recommendations")}
        </button>
        <button
          type="button"
          className="ee-btn-sm"
          onClick={() => emit(prepareDoneTaskEvidenceEvent(asArray(preview.selected_task_ids)))}
        >
          {label(labels, "ee_retry_ai", "Retry AI")}
        </button>
      </div>
    </div>
  );
}

function outputKey(o) {
  return cleanText(o.source_key) || `${cleanText(o.source_kind) || "output"}:${cleanText(o.id)}`;
}

function outputEventItem(o, projectRefs = []) {
  return {
    output_id: cleanText(o.id),
    source_kind: cleanText(o.source_kind) || "output",
    project_refs: projectRefs,
  };
}

function formatCountLabel(text, count) {
  return cleanText(text).replace("{n}", String(count));
}

function OutputEvidencePanel({ outputs, projectOptions, labels, emit, onClose }) {
  const options = asArray(projectOptions);
  const validProjectIds = useMemo(
    () => new Set(options.filter((p) => p.has_goal !== false).map((p) => p.id)),
    [options]
  );
  const [projectByKey, setProjectByKey] = useState({});
  const [selectedKeys, setSelectedKeys] = useState(() => new Set());
  const [showBlocked, setShowBlocked] = useState(false);
  const [showIgnored, setShowIgnored] = useState(false);
  const [showExisting, setShowExisting] = useState(false);

  useEffect(() => {
    const nextProjects = {};
    const nextSelected = new Set();
    asArray(outputs).forEach((o) => {
      const key = outputKey(o);
      const refs = asArray(o.project_refs);
      const inferred = refs.length === 1 ? cleanText(refs[0]) : "";
      if (inferred) nextProjects[key] = inferred;
      if (o.source_ready && inferred && validProjectIds.has(inferred)) {
        nextSelected.add(key);
      }
    });
    setProjectByKey(nextProjects);
    setSelectedKeys(nextSelected);
  }, [outputs, validProjectIds]);

  const projectLabel = (pid) => {
    const found = options.find((p) => p.id === pid);
    return found ? cleanText(found.label) || pid : pid;
  };

  const selectedProject = (o) => {
    const key = outputKey(o);
    if (Object.prototype.hasOwnProperty.call(projectByKey, key)) {
      return cleanText(projectByKey[key]);
    }
    const refs = asArray(o.project_refs);
    return refs.length === 1 ? cleanText(refs[0]) : "";
  };

  const canCreateRow = (o) => {
    const pid = selectedProject(o);
    return !!o.source_ready && !!pid && validProjectIds.has(pid);
  };

  const setRowProject = (o, value) => {
    const key = outputKey(o);
    const pid = cleanText(value);
    setProjectByKey((prev) => ({ ...prev, [key]: pid }));
    setSelectedKeys((prev) => {
      const next = new Set(prev);
      if (o.source_ready && pid && validProjectIds.has(pid)) next.add(key);
      else next.delete(key);
      return next;
    });
  };

  const toggleRow = (o, checked) => {
    const key = outputKey(o);
    if (!canCreateRow(o)) return;
    setSelectedKeys((prev) => {
      const next = new Set(prev);
      checked ? next.add(key) : next.delete(key);
      return next;
    });
  };

  const visibleOutputs = asArray(outputs).filter((o) => {
    if (o.ignored) return showIgnored;
    if (o.already_has_evidence) return showExisting;
    if (!o.source_ready) return showBlocked;
    return true;
  });

  const selectedItems = asArray(outputs)
    .filter((o) => selectedKeys.has(outputKey(o)) && canCreateRow(o))
    .map((o) => outputEventItem(o, [selectedProject(o)]));
  const selectedCount = selectedItems.length;
  const createText = formatCountLabel(
    label(labels, "ee_output_bulk_create", "Create selected evidence ({n})"),
    selectedCount
  );
  const createSelected = () => {
    if (!selectedItems.length) return;
    emit(bulkCreateFromOutputEvent(selectedItems));
    onClose();
  };

  const actionItem = (o) => [outputEventItem(o, [])];

  return (
    <div className="ee-output-strip">
      <div className="ee-output-panel-head">
        <div className="ee-output-toggles">
          <label className="ee-check">
            <input type="checkbox" checked={showBlocked} onChange={() => setShowBlocked((v) => !v)} />
            {label(labels, "ee_output_show_blocked", "Show draft/blocked")}
          </label>
          <label className="ee-check">
            <input type="checkbox" checked={showIgnored} onChange={() => setShowIgnored((v) => !v)} />
            {label(labels, "ee_output_show_ignored", "Show skipped")}
          </label>
          <label className="ee-check">
            <input type="checkbox" checked={showExisting} onChange={() => setShowExisting((v) => !v)} />
            {label(labels, "ee_output_show_existing", "Show existing evidence")}
          </label>
        </div>
        <button
          type="button"
          className="ee-btn-primary"
          disabled={!selectedCount}
          onClick={createSelected}
        >
          {createText}
        </button>
      </div>
      {visibleOutputs.length === 0 && <span className="ee-muted">{label(labels, "ee_no_outputs", "No outputs")}</span>}
      {visibleOutputs.map((o) => {
        const key = outputKey(o);
        const blockers = asArray(o.blockers);
        const pid = selectedProject(o);
        const canCreate = canCreateRow(o);
        const checked = selectedKeys.has(key) && canCreate;
        return (
          <div key={key} className={`ee-output-row${canCreate ? "" : " ee-output-row-blocked"}`}>
            <input
              type="checkbox"
              className="ee-output-check"
              checked={checked}
              disabled={!canCreate}
              onChange={(e) => toggleRow(o, e.target.checked)}
              aria-label={cleanText(o.label) || cleanText(o.id)}
            />
            <div className="ee-output-main">
              <div className="ee-output-title">
                {cleanText(o.label)}
                {o.already_has_evidence && (
                  <span className="ee-badge ee-badge-muted">
                    {label(labels, "ee_done_has_evidence", "has evidence")}
                  </span>
                )}
                {o.ignored && (
                  <span className="ee-badge ee-badge-muted">
                    {label(labels, "ee_output_ignored_badge", "skipped")}
                  </span>
                )}
              </div>
              <div className="ee-output-meta">
                {cleanText(o.source_kind) || "output"} · {cleanText(o.status) || "—"} · {cleanText(o.date) || "no date"}
                {pid ? ` · ${projectLabel(pid)}` : ""}
              </div>
              <label className="ee-field ee-output-project">
                <span>{label(labels, "ee_link_project", "Internal project")}</span>
                <select value={pid} onChange={(e) => setRowProject(o, e.target.value)}>
                  <option value="" />
                  {options.map((p) => (
                    <option key={p.id} value={p.id} disabled={p.has_goal === false}>
                      {cleanText(p.label) || p.id}
                      {p.has_goal === false ? " · no goal" : ""}
                    </option>
                  ))}
                </select>
              </label>
              {blockers.length > 0 && (
                <div className="ee-preview-blockers">{blockers.join(" ")}</div>
              )}
            </div>
            {o.ignored ? (
              <button
                type="button"
                className="ee-btn-sm"
                onClick={() => emit(restoreOutputCandidatesEvent(actionItem(o)))}
              >
                {label(labels, "ee_output_restore", "Restore")}
              </button>
            ) : (
              <button
                type="button"
                className="ee-btn-sm"
                onClick={() => emit(ignoreOutputCandidatesEvent(actionItem(o), "not_evidence"))}
              >
                {label(labels, "ee_output_ignore", "Skip")}
              </button>
            )}
          </div>
        );
      })}
      <div className="ee-output-panel-foot">
        <button
          type="button"
          className="ee-btn-primary"
          disabled={!selectedCount}
          onClick={createSelected}
        >
          {createText}
        </button>
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
  const [showDoneTasks, setShowDoneTasks] = useState(false);
  // Batch mode: a Set of selected row ids + a toggle to reveal checkboxes.
  const [batchMode, setBatchMode] = useState(false);
  const [batchIds, setBatchIds] = useState(() => new Set());
  const doneTasks = asArray(payload.done_task_options);

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

  // Batch selection helpers. Selection is keyed by id so it survives reorder.
  const visibleIds = useMemo(() => visible.map((r) => r.id), [visible]);
  const selectedBatchIds = useMemo(
    () => visibleIds.filter((id) => batchIds.has(id)),
    [visibleIds, batchIds]
  );
  const allVisibleSelected =
    visibleIds.length > 0 && selectedBatchIds.length === visibleIds.length;
  const checkRow = (id, on) =>
    setBatchIds((prev) => {
      const next = new Set(prev);
      on ? next.add(id) : next.delete(id);
      return next;
    });
  const toggleSelectAllVisible = () =>
    setBatchIds((prev) => {
      const next = new Set(prev);
      if (allVisibleSelected) {
        visibleIds.forEach((id) => next.delete(id));
      } else {
        visibleIds.forEach((id) => next.add(id));
      }
      return next;
    });
  const clearBatch = () => {
    setBatchIds(new Set());
    setBatchMode(false);
  };

  const reformatPreview = payload.reformat_preview || null;
  const bulkReformatPreview = payload.bulk_reformat_preview || null;
  const donePreview = payload.done_preview || null;
  const duplicateCandidates = asArray(payload.duplicate_candidates);
  const rowsById = useMemo(() => {
    const m = {};
    for (const r of rows) m[r.id] = r;
    return m;
  }, [rows]);

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
          <button type="button" className="ee-btn" onClick={() => setShowDoneTasks(true)}>
            {label(labels, "ee_done_tasks_title", "Done tasks → evidence")}
          </button>
          <button type="button" className="ee-btn" onClick={() => emit(suggestDuplicatesEvent("", false))}>
            {label(labels, "ee_find_duplicates", "Find duplicates")}
          </button>
          <button type="button" className="ee-btn" onClick={() => emit(suggestDuplicatesEvent("", true))}>
            {label(labels, "ee_find_duplicates_ai", "Find duplicates (AI)")}
          </button>
          <button
            type="button"
            className={`ee-btn${batchMode ? " ee-btn-on" : ""}`}
            onClick={() => { setBatchMode((b) => !b); if (batchMode) setBatchIds(new Set()); }}
          >
            {label(labels, "ee_batch_mode", "Batch select")}
          </button>
          <button
            type="button"
            className="ee-btn"
            disabled={!visible.some((r) => r.missing_formatted_content)}
            onClick={() => emit(bulkRequestAiReformatEvent(visible.filter((r) => r.missing_formatted_content).map((r) => r.id)))}
          >
            {label(labels, "ee_bulk_reformat_missing", "AI reformat missing formatted")}
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
          <Counter icon="⚠" n={summary.missing_raw || 0} text={label(labels, "ee_original_content_missing", "Missing raw")} active={!!filters.missingRaw} onClick={() => toggleFilter("missingRaw")} />
          <Counter icon="D" n={summary.missing_date || 0} text={label(labels, "ee_missing_date", "Missing date")} active={!!filters.missingDate} onClick={() => toggleFilter("missingDate")} />
          <Counter icon="P" n={summary.missing_project || 0} text={label(labels, "ee_missing_project", "Missing project")} active={!!filters.missingProject} onClick={() => toggleFilter("missingProject")} />
          <Counter icon="G" n={summary.project_without_goal || 0} text={label(labels, "ee_project_without_goal", "Project without goal")} active={!!filters.projectWithoutGoal} onClick={() => toggleFilter("projectWithoutGoal")} />
          <Counter icon="F" n={summary.missing_formatted_content || 0} text={label(labels, "ee_missing_formatted_content", "Missing formatted")} active={!!filters.missingFormatted} onClick={() => toggleFilter("missingFormatted")} />
          <Counter icon="S" n={summary.source_conflict || 0} text={label(labels, "ee_source_conflict", "Source conflict")} active={!!filters.sourceConflict} onClick={() => toggleFilter("sourceConflict")} />
          <Counter icon="!" n={summary.dangling_task_source || 0} text={label(labels, "ee_dangling_task_source", "Dangling task source")} active={!!filters.danglingTaskSource} onClick={() => toggleFilter("danglingTaskSource")} />
          <Counter icon="⬚" n={summary.crystallized_without_evidence || 0} text={label(labels, "ee_refresh_crystallized_tasks", "Crystallized w/o evidence")} />
          <Counter
            icon="◇"
            n={summary.output_candidates || 0}
            text={label(labels, "ee_output_ready_candidates", "Evidence-ready outputs")}
            active={showOutputs}
            onClick={() => setShowOutputs((s) => !s)}
          />
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
        <OutputEvidencePanel
          outputs={outputs}
          projectOptions={asArray(payload.project_options)}
          labels={labels}
          emit={emit}
          onClose={() => setShowOutputs(false)}
        />
      )}

      <DonePreviewPanel preview={donePreview} labels={labels} emit={emit} />

      {duplicateCandidates.length > 0 && (
        <DuplicatePanel
          candidates={duplicateCandidates}
          rowsById={rowsById}
          labels={labels}
          emit={emit}
        />
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
            <label className="ee-check">
              <input type="checkbox" checked={!!filters.missingFormatted} onChange={() => toggleFilter("missingFormatted")} />
              {label(labels, "ee_missing_formatted_content", "missing formatted")}
            </label>
            <label className="ee-check">
              <input type="checkbox" checked={!!filters.danglingTaskSource} onChange={() => toggleFilter("danglingTaskSource")} />
              {label(labels, "ee_dangling_task_source", "dangling task")}
            </label>
          </div>
          {batchMode && visible.length > 0 && (
            <label className="ee-check ee-selectall">
              <input
                type="checkbox"
                checked={allVisibleSelected}
                onChange={toggleSelectAllVisible}
              />
              {label(labels, "ee_bulk_select_visible", "Select all visible")} ({visible.length})
            </label>
          )}
          <div className="ee-list-scroll">
            {visible.length === 0 && <div className="ee-empty">{label(labels, "ee_empty", "No evidence matches.")}</div>}
            {visible.map((row) => (
              <ListItem
                key={row.id}
                row={row}
                labels={labels}
                selected={row.id === selectedId}
                onClick={() => setSelectedId(row.id)}
                batch={batchMode}
                checked={batchIds.has(row.id)}
                onCheck={checkRow}
              />
            ))}
          </div>
        </div>

        {/* detail */}
        <div className="ee-detail-wrap">
          {batchMode ? (
            <div className="ee-detail ee-batch-detail">
              <BulkActionBar
                ids={selectedBatchIds}
                payload={payload}
                labels={labels}
                emit={emit}
                onClear={clearBatch}
              />
              <BulkReformatPreview
                preview={bulkReformatPreview}
                labels={labels}
                emit={emit}
              />
            </div>
          ) : selected ? (
            <DetailPane row={selected} payload={payload} labels={labels} emit={emit} reformatPreview={reformatPreview} />
          ) : (
            <div className="ee-empty ee-empty-detail">{label(labels, "ee_select_hint", "Select an evidence row to edit.")}</div>
          )}
        </div>
      </div>

      {showAdd && <AddForm payload={payload} labels={labels} emit={emit} onClose={() => setShowAdd(false)} />}
      {showDoneTasks && (
        <DoneTasksPicker
          tasks={doneTasks}
          labels={labels}
          emit={emit}
          onClose={() => setShowDoneTasks(false)}
        />
      )}
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
