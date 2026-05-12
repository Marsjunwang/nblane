import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";

import "./style.css";
import {
  detailTitle,
  displayFocus,
  displayLabel,
  displaySummary,
  isRenderable,
  statusLabel,
} from "./payload.js";

function GoalPresence({ payload }) {
  const [open, setOpen] = useState(false);
  const texts = payload?.texts || {};
  const focus = useMemo(() => displayFocus(payload), [payload]);
  const summary = displaySummary(payload);
  const label = displayLabel(payload);
  const status = statusLabel(payload);
  const statusValue = payload?.status?.value || payload?.status || "";
  const target = payload?.target || "";
  const align = payload?.align === "right" ? "right" : "left";
  const hidden = payload?.visibility === "hidden";

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);

  if (!isRenderable(payload) || !label) {
    return null;
  }

  return (
    <div className={`goal-presence align-${align}`}>
      <button
        aria-expanded={open}
        className="goal-chip"
        onClick={() => setOpen((value) => !value)}
        type="button"
      >
        <span className="goal-prefix">{texts.current}</span>
        <span className="goal-label" title={label}>
          {label}
        </span>
        <span className="goal-meta">
          {status ? (
            <span className={`goal-status ${statusValue}`}>{status}</span>
          ) : null}
          {target ? <span className="goal-target">{target}</span> : null}
          <span
            className={`goal-caret ${open ? "open" : ""}`}
            aria-hidden="true"
          />
        </span>
      </button>
      {open ? (
        <div className="goal-panel" role="region" aria-label={texts.details}>
          <p className="goal-panel-title">{detailTitle(payload)}</p>
          {hidden ? (
            <p className="goal-panel-row">{texts.hidden_note}</p>
          ) : null}
          {summary ? <p className="goal-panel-row">{summary}</p> : null}
          {target ? (
            <p className="goal-panel-row">
              <strong>{texts.target}:</strong> {target}
            </p>
          ) : null}
          {focus.length ? (
            <div className="goal-panel-row">
              <strong>{texts.focus}:</strong>
              <ul className="goal-focus-list">
                {focus.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {payload?.agent_context_label ? (
            <p className="goal-panel-row">{payload.agent_context_label}</p>
          ) : null}
          {texts.edit_home ? (
            <p className="goal-panel-row">{texts.edit_home}</p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export default function mountGoalPresence(component) {
  const { data, parentElement } = component;
  let host = parentElement.querySelector("[data-goal-presence-root]");
  if (!host) {
    host = document.createElement("div");
    host.dataset.goalPresenceRoot = "true";
    parentElement.appendChild(host);
  }

  if (!host._goalPresenceRoot) {
    host._goalPresenceRoot = createRoot(host);
  }
  host._goalPresenceRoot.render(<GoalPresence payload={data || {}} />);

  return () => {
    if (host._goalPresenceRoot) {
      host._goalPresenceRoot.unmount();
      host._goalPresenceRoot = null;
    }
  };
}
