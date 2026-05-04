import React, { useEffect, useRef, useState } from "react";
import { LibraryDialog } from "./LibraryDialog.jsx";

export function AttachExistingDialog({
  labels = {},
  parentTitle = "",
  onCancel,
  onConfirm,
}) {
  const [ref, setRef] = useState("");
  const [title, setTitle] = useState("");
  const inputRef = useRef(null);
  useEffect(() => {
    inputRef.current?.focus();
  }, []);
  const cleanRef = ref.trim();
  return (
    <LibraryDialog
      labels={labels}
      title={labels.library_attach_existing || "Attach reference"}
      subtitle={parentTitle}
      confirmLabel={labels.library_attach_existing || "Attach"}
      disabled={!cleanRef}
      onCancel={onCancel}
      onConfirm={() => onConfirm?.({ ref: cleanRef, title: title.trim() })}
    >
      <label className="nb-field nb-library-dialog-field">
        <span>{labels.library_attach_ref_prompt || "Existing ref or route"}</span>
        <input
          ref={inputRef}
          value={ref}
          placeholder="blog/post.md or media/example.png"
          onChange={(event) => setRef(event.target.value)}
        />
      </label>
      <label className="nb-field nb-library-dialog-field">
        <span>{labels.library_attach_title || "Display title"}</span>
        <input
          value={title}
          placeholder={labels.library_attach_title_optional || "Optional"}
          onChange={(event) => setTitle(event.target.value)}
        />
      </label>
    </LibraryDialog>
  );
}
