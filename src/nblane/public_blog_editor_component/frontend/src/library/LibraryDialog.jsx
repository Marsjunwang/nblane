import React, { useEffect, useId, useRef } from "react";

function focusableElements(root) {
  if (!root) {
    return [];
  }
  return Array.from(
    root.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((element) => element.offsetParent !== null || element === document.activeElement);
}

export function LibraryDialog({
  title,
  subtitle = "",
  labels = {},
  children,
  confirmLabel = "",
  cancelLabel = "",
  danger = false,
  disabled = false,
  onCancel,
  onConfirm,
}) {
  const panelRef = useRef(null);
  const titleId = useId();
  useEffect(() => {
    const previous = document.activeElement;
    const focusables = focusableElements(panelRef.current);
    (focusables[0] || panelRef.current)?.focus?.();
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onCancel?.();
        return;
      }
      if (event.key !== "Tab") {
        return;
      }
      const items = focusableElements(panelRef.current);
      if (!items.length) {
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      previous?.focus?.();
    };
  }, [onCancel]);

  const effectiveConfirm = confirmLabel || labels.confirm || labels.create || "Confirm";
  const effectiveCancel = cancelLabel || labels.cancel || "Cancel";
  return (
    <div
      className="nb-preview-dialog nb-library-dialog-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onCancel?.();
        }
      }}
    >
      <form
        ref={panelRef}
        className={`nb-preview-dialog-panel nb-library-dialog ${danger ? "is-danger" : ""}`}
        tabIndex={-1}
        onMouseDown={(event) => event.stopPropagation()}
        onSubmit={(event) => {
          event.preventDefault();
          if (!disabled) {
            onConfirm?.();
          }
        }}
      >
        <div className="nb-preview-dialog-header">
          <div>
            <strong id={titleId}>{title}</strong>
            {subtitle ? <span className="nb-muted-line">{subtitle}</span> : null}
          </div>
          <button
            type="button"
            className="nb-icon-button"
            title={labels.close || "Close"}
            onClick={onCancel}
          >
            x
          </button>
        </div>
        <div className="nb-library-dialog-body">{children}</div>
        <div className="nb-row-actions">
          <button type="button" className="nb-button" onClick={onCancel}>
            {effectiveCancel}
          </button>
          <button
            type="submit"
            className={`nb-button ${danger ? "danger" : "primary"}`}
            disabled={disabled}
          >
            {effectiveConfirm}
          </button>
        </div>
      </form>
    </div>
  );
}
