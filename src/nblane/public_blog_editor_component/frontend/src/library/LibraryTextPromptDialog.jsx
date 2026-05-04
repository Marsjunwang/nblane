import React, { useEffect, useRef, useState } from "react";
import { LibraryDialog } from "./LibraryDialog.jsx";
import { cleanText } from "./treeUtils.js";

export function LibraryTextPromptDialog({
  labels = {},
  title,
  subtitle = "",
  initialValue = "",
  placeholder = "",
  confirmLabel = "",
  danger = false,
  validateValue = null,
  onCancel,
  onConfirm,
}) {
  const [value, setValue] = useState(cleanText(initialValue));
  const inputRef = useRef(null);
  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select?.();
  }, []);
  const trimmed = value.trim();
  const valid = trimmed && (typeof validateValue !== "function" || validateValue(trimmed));
  return (
    <LibraryDialog
      labels={labels}
      title={title}
      subtitle={subtitle}
      confirmLabel={confirmLabel}
      danger={danger}
      disabled={!valid}
      onCancel={onCancel}
      onConfirm={() => onConfirm?.(trimmed)}
    >
      <label className="nb-field nb-library-dialog-field">
        <span>{placeholder || title}</span>
        <input
          ref={inputRef}
          value={value}
          placeholder={placeholder}
          onChange={(event) => setValue(event.target.value)}
        />
      </label>
    </LibraryDialog>
  );
}
