import React, { useEffect, useState } from "react";
import { HdDrawer } from "./drawer.jsx";
import {
  resumeIngestApplyEvent,
  resumeIngestDiscardEvent,
  resumeIngestGenerateEvent,
} from "./events.js";

function label(ui, key, fallback) {
  const value = ui && typeof ui === "object" ? ui[key] : "";
  return typeof value === "string" && value ? value : fallback;
}

export function ResumeIngestDrawer({ open, onClose, ui, resume, onEmit }) {
  const [text, setText] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [uploadInfo, setUploadInfo] = useState("");
  // Initialise from the server-side stash so that re-opening the drawer after a
  // remount (or after a generate→apply round-trip) keeps the user's choice
  // rather than silently resetting to false.
  const [allowStatus, setAllowStatus] = useState(Boolean(resume?.allowStatusChange));
  useEffect(() => {
    if (resume?.allowStatusChange !== undefined) {
      setAllowStatus(Boolean(resume.allowStatusChange));
    }
  }, [resume?.allowStatusChange]);
  const llmConfigured = Boolean(resume?.llmConfigured);
  const merge = resume?.merge || null;
  const hasPending = Boolean(resume?.hasPendingPatch);

  async function onFileChosen(event) {
    setUploadError("");
    setUploadInfo("");
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    const lower = String(file.name || "").toLowerCase();
    // PDF / DOCX must be parsed server-side; we send them as base64 through a
    // dedicated event so the Streamlit host can re-use the same extractor that
    // the file_uploader uses, then funnel the resulting text back through this
    // textarea on the next rerun.
    if (lower.endsWith(".pdf") || lower.endsWith(".docx")) {
      try {
        const buf = await file.arrayBuffer();
        let bin = "";
        const view = new Uint8Array(buf);
        for (let i = 0; i < view.byteLength; i += 1) bin += String.fromCharCode(view[i]);
        const b64 = window.btoa(bin);
        onEmit?.({
          action: "resume_ingest_upload",
          payload: { filename: file.name, base64: b64 },
        });
        setUploadInfo(
          label(
            ui,
            "resume_upload_uploading",
            "Uploading {name} for server-side extraction…",
          ).replace("{name}", file.name),
        );
      } catch (e) {
        setUploadError(String(e && e.message) || "upload failed");
      }
      return;
    }
    // Plain text — parse locally.
    try {
      const t = await file.text();
      setText(t);
      setUploadInfo(
        label(ui, "resume_upload_extracted", "Extracted {n} characters — review then Generate.")
          .replace("{n}", String(t.length)),
      );
    } catch (e) {
      setUploadError(String(e && e.message) || "could not read file");
    }
  }

  function generate() {
    if (!text.trim() || !llmConfigured) {
      return;
    }
    onEmit?.(
      resumeIngestGenerateEvent({ text, allowStatusChange: allowStatus }),
    );
  }

  function applyPatch() {
    onEmit?.(resumeIngestApplyEvent({ allowStatusChange: allowStatus }));
  }

  function discardPatch() {
    onEmit?.(resumeIngestDiscardEvent());
  }

  return (
    <HdDrawer
      open={open}
      onClose={onClose}
      title={label(ui, "dashboard_drawer_resume_ingest_title", "Resume / long text (AI ingest)")}
      footer={
        <>
          <button type="button" className="hd-ghost" onClick={onClose}>
            {label(ui, "dashboard_drawer_close", "Close")}
          </button>
          {hasPending ? (
            <>
              <button type="button" className="hd-ghost" onClick={discardPatch}>
                {label(ui, "dashboard_drawer_resume_discard", "Discard draft")}
              </button>
              <button
                type="button"
                className="hd-primary"
                onClick={applyPatch}
                disabled={!merge?.ok}
              >
                {label(ui, "resume_apply", "Apply to profile")}
              </button>
            </>
          ) : (
            <button
              type="button"
              className="hd-primary"
              onClick={generate}
              disabled={!llmConfigured || !text.trim()}
            >
              {label(ui, "resume_generate", "Generate draft")}
            </button>
          )}
        </>
      }
    >
      {!llmConfigured ? (
        <div className="hd-drawer-warning">
          {label(
            ui,
            "dashboard_drawer_resume_no_ai",
            "AI not configured. Set LLM_API_KEY in .env first.",
          )}
        </div>
      ) : null}
      <p className="hd-drawer-info">
        {label(
          ui,
          "profile_evidence_import_caption",
          "Paste resume or long bio; AI drafts evidence and skill-tree changes.",
        )}
      </p>
      {hasPending ? (
        <div className="hd-drawer-banner">
          {label(
            ui,
            "dashboard_drawer_resume_pending_caption",
            "A draft is pending. Review and Apply, or Discard to drop it.",
          )}
        </div>
      ) : (
        <div className="hd-drawer-row">
          <label>
            {label(ui, "resume_upload_label", "Or upload a resume (.pdf / .docx / .txt)")}
          </label>
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={onFileChosen}
            disabled={!llmConfigured}
          />
          {uploadInfo ? <p className="hd-drawer-info">{uploadInfo}</p> : null}
          {uploadError ? <p className="hd-drawer-warning">{uploadError}</p> : null}
        </div>
      )}
      {hasPending ? null : (
        <div className="hd-drawer-row">
          <label>{label(ui, "resume_placeholder", "Paste resume…")}</label>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={6}
            placeholder={label(ui, "resume_placeholder", "Paste resume…")}
          />
        </div>
      )}
      <div className="hd-drawer-row">
        <label>
          <input
            type="checkbox"
            checked={allowStatus}
            onChange={(event) => setAllowStatus(event.target.checked)}
          />{" "}
          {label(ui, "resume_allow_status", "Allow AI to update node status")}
        </label>
        <p className="hd-drawer-info">
          {label(ui, "resume_allow_status_help", "")}
        </p>
      </div>
      {merge ? (
        <section className="hd-drawer-section">
          <h3>
            {label(
              ui,
              "dashboard_drawer_resume_preview_delta_title",
              "Merge preview",
            )}
          </h3>
          {merge.warnings.length ? (
            <div className="hd-drawer-banner">
              {label(ui, "resume_warn", "Warnings")}
              <ul className="hd-drawer-list">
                {merge.warnings.map((line, idx) => (
                  <li key={idx}>{line}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {merge.errors.length ? (
            <div className="hd-drawer-warning">
              <ul className="hd-drawer-list">
                {merge.errors.map((line, idx) => (
                  <li key={idx}>{line}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {merge.newEvidence.length ? (
            <div className="hd-resume-diff-group">
              <strong className="hd-resume-diff-title hd-resume-diff-title-add">
                <span className="hd-resume-diff-marker">+</span>
                {label(
                  ui,
                  "dashboard_drawer_resume_preview_delta_new_evidence",
                  "New evidence",
                )}
                <em className="hd-resume-diff-count">{merge.newEvidence.length}</em>
              </strong>
              <ul className="hd-drawer-list hd-resume-diff-list add">
                {merge.newEvidence.map((line, idx) => (
                  <li key={idx}>{line}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {merge.treeDelta.length ? (
            <div className="hd-resume-diff-group">
              <strong className="hd-resume-diff-title hd-resume-diff-title-change">
                <span className="hd-resume-diff-marker">≈</span>
                {label(
                  ui,
                  "dashboard_drawer_resume_preview_delta_tree",
                  "Skill-tree changes",
                )}
                <em className="hd-resume-diff-count">{merge.treeDelta.length}</em>
              </strong>
              <ul className="hd-drawer-list hd-resume-diff-list change">
                {merge.treeDelta.map((line, idx) => (
                  <li key={idx}>{line}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {!merge.newEvidence.length && !merge.treeDelta.length ? (
            <p className="hd-drawer-info">
              {label(
                ui,
                "dashboard_drawer_resume_preview_delta_none",
                "No diff against existing data.",
              )}
            </p>
          ) : null}
          {merge.mergedPoolYaml ? (
            <details>
              <summary>{label(ui, "resume_preview_pool", "Merged evidence-pool")}</summary>
              <pre className="hd-drawer-pre">{merge.mergedPoolYaml}</pre>
            </details>
          ) : null}
          {merge.mergedTreeYaml ? (
            <details>
              <summary>{label(ui, "resume_preview_tree", "Merged skill-tree")}</summary>
              <pre className="hd-drawer-pre">{merge.mergedTreeYaml}</pre>
            </details>
          ) : null}
        </section>
      ) : null}
    </HdDrawer>
  );
}
