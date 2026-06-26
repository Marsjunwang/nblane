import React, { useEffect } from "react";

export function HdDrawer({ open, onClose, title, children, footer = null }) {
  useEffect(() => {
    if (!open) return undefined;
    function handleKey(event) {
      if (event.key === "Escape") {
        onClose?.();
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  if (!open) {
    return null;
  }
  return (
    <div className="hd-drawer-root" role="dialog" aria-modal="true">
      <div className="hd-drawer-mask" onClick={() => onClose?.()} />
      <aside className="hd-drawer-panel">
        <header className="hd-drawer-head">
          <h2>{title}</h2>
          <button
            type="button"
            className="hd-ghost"
            data-action="close-drawer"
            onClick={() => onClose?.()}
          >
            ×
          </button>
        </header>
        <div className="hd-drawer-body">{children}</div>
        {footer ? <footer className="hd-drawer-foot">{footer}</footer> : null}
      </aside>
    </div>
  );
}
