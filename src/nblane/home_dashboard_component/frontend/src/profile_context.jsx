import React, { useEffect, useMemo, useState } from "react";
import { HdDrawer } from "./drawer.jsx";
import {
  profileContextSaveEvent,
  profileContextSaveRawEvent,
} from "./events.js";

function label(ui, key, fallback) {
  const value = ui && typeof ui === "object" ? ui[key] : "";
  return typeof value === "string" && value ? value : fallback;
}

function identityLabel(ui, field) {
  const map = {
    Name: "identity_name",
    Domain: "identity_domain",
    Journey: "identity_journey",
    "Current Role": "identity_current_role",
    "North Star": "identity_north_star",
    "North Star Brief": "identity_north_star_brief",
    "North Star Visibility": "identity_north_star_visibility",
  };
  return label(ui, map[field] || "", field);
}

function narrativeLabel(ui, title) {
  const map = {
    "Research Fingerprint": "profile_section_research_fingerprint",
    "Thinking & Communication Style": "profile_section_thinking_style",
    "Growth Log": "profile_section_growth_log",
    "Influence & Output": "profile_section_influence_output",
  };
  return label(ui, map[title] || "", title);
}

function visibilityOptionLabel(ui, value) {
  return label(ui, `north_star_visibility_${value}`, value);
}

function competencyStatusLabel(ui, value) {
  return label(ui, `competency_status_${value}`, value);
}

const TABS = ["structured", "competencies", "narrative", "generated", "raw"];

// Minimal Markdown preview: enough to make narrative sections readable without a
// heavy dependency. Handles bold, list bullets, and preserves line breaks.
function renderMarkdownPreview(text) {
  const lines = String(text || "").split(/\r?\n/);
  return lines.map((line, idx) => {
    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    const content = bullet ? bullet[1] : line;
    const parts = content.split(/(\*\*[^*]+\*\*)/g).map((chunk, i) => {
      const bold = chunk.match(/^\*\*([^*]+)\*\*$/);
      return bold ? <strong key={i}>{bold[1]}</strong> : chunk;
    });
    if (bullet) {
      return (
        <div key={idx} style={{ paddingLeft: 14, textIndent: -10 }}>
          • {parts}
        </div>
      );
    }
    if (!line.trim()) {
      return <div key={idx} style={{ height: 8 }} />;
    }
    return <div key={idx}>{parts}</div>;
  });
}

function normalizeRows(rows) {
  return (Array.isArray(rows) ? rows : []).map((row) => ({
    area: typeof row?.area === "string" ? row.area : "",
    status: typeof row?.status === "string" ? row.status : "",
    notes: typeof row?.notes === "string" ? row.notes : "",
  }));
}

export function ProfileContextDrawer({ open, onClose, ui, profileContext, onEmit }) {
  const initialIdentity = useMemo(
    () => ({ ...(profileContext?.identity || {}) }),
    [profileContext?.identity, open],
  );
  const initialNarrative = useMemo(
    () => ({ ...(profileContext?.narrative || {}) }),
    [profileContext?.narrative, open],
  );
  const initialRaw = profileContext?.rawMarkdown || "";

  const [identity, setIdentity] = useState(initialIdentity);
  const [narrative, setNarrative] = useState(initialNarrative);
  const [competencies, setCompetencies] = useState(
    normalizeRows(profileContext?.coreCompetencies),
  );
  const [narrativePreview, setNarrativePreview] = useState({});
  const [rawMarkdown, setRawMarkdown] = useState(initialRaw);
  const [tab, setTab] = useState("structured");

  useEffect(() => {
    if (!open) return;
    setIdentity({ ...(profileContext?.identity || {}) });
    setNarrative({ ...(profileContext?.narrative || {}) });
    setCompetencies(normalizeRows(profileContext?.coreCompetencies));
    setNarrativePreview({});
    setRawMarkdown(profileContext?.rawMarkdown || "");
    setTab("structured");
  }, [open, profileContext]);

  const fields = profileContext?.identityFields || [];
  const sections = profileContext?.narrativeSections || [];
  const visibilities = profileContext?.northStarVisibilities || [];
  const statuses = profileContext?.competencyStatuses || [];
  const generatedBlocks = profileContext?.generatedBlocks || [];
  const generatedBlockText = profileContext?.generatedBlockText || {};
  const hasSkillMd = Boolean(profileContext?.hasSkillMd);

  // Validation: every competency row with notes/status must name an Area, and
  // each status must be a known value. Empty rows are dropped silently on save.
  const competencyErrors = competencies
    .map((row, idx) => {
      const hasContent = row.area || row.notes || row.status;
      if (!hasContent) return null;
      if (!row.area.trim()) {
        return { idx, kind: "area" };
      }
      if (row.status && !statuses.includes(row.status)) {
        return { idx, kind: "status" };
      }
      return null;
    })
    .filter(Boolean);
  const hasCompetencyErrors = competencyErrors.length > 0;

  const dirty = useMemo(() => {
    const baseIdentity = profileContext?.identity || {};
    const baseNarrative = profileContext?.narrative || {};
    const baseRows = normalizeRows(profileContext?.coreCompetencies);
    const identityDirty = fields.some(
      (f) => (identity[f] || "") !== (baseIdentity[f] || ""),
    );
    const narrativeDirty = sections.some(
      (t) => (narrative[t] || "") !== (baseNarrative[t] || ""),
    );
    const rowsDirty = JSON.stringify(competencies) !== JSON.stringify(baseRows);
    const rawDirty = rawMarkdown !== (profileContext?.rawMarkdown || "");
    return identityDirty || narrativeDirty || rowsDirty || rawDirty;
  }, [identity, narrative, competencies, rawMarkdown, profileContext, fields, sections]);

  function requestClose() {
    if (dirty) {
      const msg = label(
        ui,
        "profile_context_unsaved_warning",
        "You have unsaved changes. Discard them?",
      );
      if (!window.confirm(msg)) {
        return;
      }
    }
    onClose?.();
  }

  function saveStructured() {
    if (hasCompetencyErrors) return;
    onEmit?.(
      profileContextSaveEvent({
        identityFields: identity,
        narrativeSections: narrative,
        coreCompetencies: competencies,
      }),
    );
  }

  function saveRaw() {
    onEmit?.(profileContextSaveRawEvent({ rawMarkdown }));
  }

  function setField(field, value) {
    setIdentity((prev) => ({ ...prev, [field]: value }));
  }

  function setNarrativeSection(title, value) {
    setNarrative((prev) => ({ ...prev, [title]: value }));
  }

  function setRow(idx, key, value) {
    setCompetencies((prev) =>
      prev.map((row, i) => (i === idx ? { ...row, [key]: value } : row)),
    );
  }

  function addRow() {
    setCompetencies((prev) => [
      ...prev,
      { area: "", status: statuses[0] || "", notes: "" },
    ]);
  }

  function removeRow(idx) {
    setCompetencies((prev) => prev.filter((_, i) => i !== idx));
  }

  function toggleNarrativePreview(title) {
    setNarrativePreview((prev) => ({ ...prev, [title]: !prev[title] }));
  }

  return (
    <HdDrawer
      open={open}
      onClose={requestClose}
      title={label(ui, "dashboard_drawer_profile_context_title", "Profile Context / SKILL.md")}
      footer={
        <>
          <button type="button" className="hd-ghost" onClick={requestClose}>
            {label(ui, "dashboard_drawer_close", "Close")}
          </button>
          {tab === "raw" ? (
            <button type="button" className="hd-primary" onClick={saveRaw}>
              {label(ui, "dashboard_drawer_profile_save_raw", "Save raw Markdown")}
            </button>
          ) : (
            <button
              type="button"
              className="hd-primary"
              onClick={saveStructured}
              disabled={!hasSkillMd || hasCompetencyErrors}
            >
              {label(ui, "save_profile_context", "Save Profile Context")}
            </button>
          )}
        </>
      }
    >
      {!hasSkillMd ? (
        <div className="hd-drawer-warning">
          {label(ui, "warning_no_skill_md", "SKILL.md not found.")}
        </div>
      ) : null}
      <p className="hd-drawer-info">
        {label(ui, "profile_context_caption", "")}
      </p>
      <div className="hd-drawer-section">
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {TABS.map((key) => (
            <button
              key={key}
              type="button"
              className={tab === key ? "hd-primary" : "hd-ghost"}
              onClick={() => setTab(key)}
            >
              {label(
                ui,
                `dashboard_drawer_profile_section_${
                  key === "structured" ? "identity" : key
                }`,
                key,
              )}
            </button>
          ))}
        </div>
      </div>

      {tab === "structured" ? (
        <section className="hd-drawer-section">
          <h3>
            {label(
              ui,
              "dashboard_drawer_profile_section_identity",
              "Structured profile",
            )}
          </h3>
          <div className="hd-drawer-grid-2">
            {fields.map((field) => {
              if (field === "North Star") {
                return (
                  <div key={field} className="hd-drawer-row" style={{ gridColumn: "1 / -1" }}>
                    <label>{identityLabel(ui, field)}</label>
                    <textarea
                      value={identity[field] || ""}
                      onChange={(event) => setField(field, event.target.value)}
                      rows={3}
                      placeholder={label(ui, "identity_north_star_placeholder", "")}
                    />
                  </div>
                );
              }
              if (field === "North Star Visibility") {
                return (
                  <div key={field} className="hd-drawer-row">
                    <label>{identityLabel(ui, field)}</label>
                    <select
                      value={identity[field] || (visibilities[0] || "")}
                      onChange={(event) => setField(field, event.target.value)}
                    >
                      {visibilities.map((value) => (
                        <option key={value} value={value}>
                          {visibilityOptionLabel(ui, value)}
                        </option>
                      ))}
                    </select>
                  </div>
                );
              }
              return (
                <div key={field} className="hd-drawer-row">
                  <label>{identityLabel(ui, field)}</label>
                  <input
                    type="text"
                    value={identity[field] || ""}
                    onChange={(event) => setField(field, event.target.value)}
                    placeholder={label(ui, "profile_context_field_placeholder", "")}
                  />
                </div>
              );
            })}
          </div>
        </section>
      ) : null}

      {tab === "competencies" ? (
        <section className="hd-drawer-section">
          <h3>
            {label(
              ui,
              "dashboard_drawer_profile_section_competencies",
              "Core competencies",
            )}
          </h3>
          <p className="hd-drawer-info">
            {label(ui, "competencies_caption", "")}
          </p>
          {competencies.length === 0 ? (
            <p className="hd-drawer-info">
              {label(ui, "competencies_empty", "No competencies yet. Add a row to start.")}
            </p>
          ) : null}
          {competencies.map((row, idx) => {
            const rowError = competencyErrors.find((e) => e.idx === idx);
            return (
              <div
                key={idx}
                className="hd-drawer-row"
                style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: 8, padding: 8 }}
              >
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "flex-end" }}>
                  <div style={{ flex: "2 1 160px" }}>
                    <label>{label(ui, "competency_col_area", "Area")}</label>
                    <input
                      type="text"
                      value={row.area}
                      onChange={(event) => setRow(idx, "area", event.target.value)}
                      placeholder={label(ui, "competency_area_placeholder", "")}
                    />
                  </div>
                  <div style={{ flex: "1 1 110px" }}>
                    <label>{label(ui, "competency_col_status", "Status")}</label>
                    <select
                      value={row.status}
                      onChange={(event) => setRow(idx, "status", event.target.value)}
                    >
                      {row.status && !statuses.includes(row.status) ? (
                        <option value={row.status}>{row.status}</option>
                      ) : null}
                      {statuses.map((value) => (
                        <option key={value} value={value}>
                          {competencyStatusLabel(ui, value)}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    type="button"
                    className="hd-ghost"
                    onClick={() => removeRow(idx)}
                  >
                    {label(ui, "competency_remove_row", "Remove")}
                  </button>
                </div>
                <div style={{ marginTop: 6 }}>
                  <label>{label(ui, "competency_col_notes", "Notes")}</label>
                  <textarea
                    value={row.notes}
                    onChange={(event) => setRow(idx, "notes", event.target.value)}
                    rows={2}
                    placeholder={label(ui, "competency_notes_placeholder", "")}
                  />
                </div>
                {rowError ? (
                  <div className="hd-drawer-warning">
                    {rowError.kind === "area"
                      ? label(ui, "competency_error_area", "Area is required.")
                      : label(ui, "competency_error_status", "Unknown status value.")}
                  </div>
                ) : null}
              </div>
            );
          })}
          <button type="button" className="hd-ghost" onClick={addRow}>
            {label(ui, "competency_add_row", "+ Add row")}
          </button>
        </section>
      ) : null}

      {tab === "narrative" ? (
        <section className="hd-drawer-section">
          <h3>
            {label(
              ui,
              "dashboard_drawer_profile_section_narrative",
              "Long-term narrative sections",
            )}
          </h3>
          <p className="hd-drawer-info">
            {label(ui, "profile_context_narrative_caption", "")}
          </p>
          {sections.map((title) => {
            const previewing = Boolean(narrativePreview[title]);
            return (
              <div key={title} className="hd-drawer-row">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <label>{narrativeLabel(ui, title)}</label>
                  <button
                    type="button"
                    className="hd-ghost"
                    onClick={() => toggleNarrativePreview(title)}
                  >
                    {previewing
                      ? label(ui, "narrative_edit", "Edit")
                      : label(ui, "narrative_preview", "Preview")}
                  </button>
                </div>
                {previewing ? (
                  <div className="hd-drawer-pre" style={{ whiteSpace: "normal" }}>
                    {(narrative[title] || "").trim()
                      ? renderMarkdownPreview(narrative[title])
                      : label(ui, "narrative_empty_preview", "(empty)")}
                  </div>
                ) : (
                  <textarea
                    value={narrative[title] || ""}
                    onChange={(event) => setNarrativeSection(title, event.target.value)}
                    rows={6}
                    placeholder={label(ui, "narrative_placeholder", "")}
                  />
                )}
              </div>
            );
          })}
        </section>
      ) : null}

      {tab === "generated" ? (
        <section className="hd-drawer-section">
          <h3>
            {label(
              ui,
              "dashboard_drawer_profile_section_generated",
              "Generated blocks (preview)",
            )}
          </h3>
          <p className="hd-drawer-info">
            {label(ui, "generated_block_owner_hint", "")}
          </p>
          <p className="hd-drawer-info">
            {label(ui, "generated_block_sync_hint", "")}
          </p>
          {generatedBlocks.map((block) => (
            <details key={block} open>
              <summary>{block}</summary>
              <pre className="hd-drawer-pre">
                {generatedBlockText[block] ||
                  label(ui, "generated_block_missing", "Generated block not found.")}
              </pre>
            </details>
          ))}
        </section>
      ) : null}

      {tab === "raw" ? (
        <section className="hd-drawer-section">
          <h3>
            {label(ui, "dashboard_drawer_profile_section_raw", "Raw Markdown")}
          </h3>
          <div className="hd-drawer-warning">
            {label(ui, "raw_drift_warning", "")}
          </div>
          <div className="hd-drawer-row">
            <label>{label(ui, "raw_label", "Edit SKILL.md")}</label>
            <textarea
              value={rawMarkdown}
              onChange={(event) => setRawMarkdown(event.target.value)}
              rows={20}
            />
          </div>
        </section>
      ) : null}
    </HdDrawer>
  );
}
