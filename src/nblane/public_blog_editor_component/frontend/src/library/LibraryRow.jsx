import React from "react";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import {
  libraryNodeId,
  libraryNodeTitle,
  libraryNodeType,
} from "./treeUtils.js";

function DropZone({ node, depth, half }) {
  const id = `${libraryNodeId(node)}:${half}`;
  const { setNodeRef, isOver } = useDroppable({
    id,
    data: { node, half, depth },
  });
  return (
    <span
      ref={setNodeRef}
      className={`nb-library-drop-zone is-${half} ${isOver ? "is-over" : ""}`}
      aria-hidden="true"
    />
  );
}

export function LibraryRow({
  node,
  depth,
  parentType = "",
  parentTitle = "",
  active = false,
  selected = false,
  expanded = false,
  hasChildren = false,
  activeIntent = null,
  labels = {},
  onToggle,
  onSelect,
  onMenu,
}) {
  const type = libraryNodeType(node);
  const id = libraryNodeId(node);
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({
    id: `drag:${id}`,
    data: { node },
    disabled: id === "root" || node.status === "trashed",
  });
  const isDropTarget =
    activeIntent?.overId === id && activeIntent?.position === "into";
  const style = {
    "--nb-tree-depth": depth,
    transform: CSS.Transform.toString(transform),
  };
  const subdoc = parentType === "post";
  const tooltip = subdoc
    ? (labels.library_subdoc_tooltip || "As a subdoc of {title}").replace("{title}", parentTitle)
    : "";
  return (
    <div
      ref={setNodeRef}
      className={`nb-library-row ${active ? "is-active" : ""} ${selected ? "is-selected" : ""} ${isDragging ? "is-dragging" : ""} ${isDropTarget ? "is-drop-target" : ""} ${subdoc ? "is-subdoc" : ""}`}
      role="treeitem"
      aria-expanded={hasChildren ? expanded : undefined}
      aria-selected={selected}
      style={style}
      title={tooltip}
      onContextMenu={(event) => {
        event.preventDefault();
        onMenu?.(event, node);
      }}
      onKeyDown={(event) => {
        if (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10")) {
          event.preventDefault();
          const rect = event.currentTarget.getBoundingClientRect();
          onMenu?.({ clientX: rect.left + 24, clientY: rect.top + 24, preventDefault() {} }, node);
        }
      }}
    >
      <DropZone node={node} depth={depth} half="upper" />
      <DropZone node={node} depth={depth} half="lower" />
      <button
        type="button"
        className="nb-library-toggle"
        disabled={!hasChildren}
        aria-label={expanded ? labels.library_collapse || "Collapse" : labels.library_expand || "Expand"}
        onClick={onToggle}
      >
        {hasChildren ? (expanded ? "v" : ">") : ""}
      </button>
      <button type="button" className="nb-library-node" onClick={onSelect}>
        <span
          className="nb-library-drag-handle"
          {...listeners}
          {...attributes}
          title={labels.library_drag_handle || "Drag"}
        >
          ::
        </span>
        <span className={`nb-library-type is-${type}`}>
          {type === "root" ? "R" : type === "folder" ? "D" : type === "media" ? "M" : "P"}
        </span>
        <span className="nb-library-title">
          {subdoc ? (
            <span className="nb-library-subdoc-chip">
              {labels.library_subdoc_chip || "Subdoc"}
            </span>
          ) : null}
          {libraryNodeTitle(node)}
        </span>
        <span className="nb-library-meta">
          {[type, node.virtual ? labels.library_virtual || "virtual" : "", node.status || node.visibility || "", node.route || node.slug || node.ref || ""]
            .filter(Boolean)
            .join(" / ")}
        </span>
      </button>
      <button
        type="button"
        className="nb-icon-button nb-library-row-menu"
        title={labels.library_node_actions || "File tree actions"}
        onClick={(event) => {
          event.preventDefault();
          const rect = event.currentTarget.getBoundingClientRect();
          onMenu?.({ clientX: rect.left, clientY: rect.bottom + 4, preventDefault() {} }, node);
        }}
      >
        ...
      </button>
    </div>
  );
}
