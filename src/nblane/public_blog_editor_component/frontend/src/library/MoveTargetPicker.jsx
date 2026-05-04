import React, { useMemo, useState } from "react";
import { LibraryDialog } from "./LibraryDialog.jsx";
import {
  asArray,
  cleanText,
  descendantIds,
  isParentableNode,
  isVirtualNode,
  libraryNodeId,
  libraryNodeTitle,
  libraryNodeType,
} from "./treeUtils.js";

function TargetNode({ node, depth, disabledIds, selectedId, labels, onSelect }) {
  const id = libraryNodeId(node);
  const type = libraryNodeType(node);
  const disabled = disabledIds.has(id) || !isParentableNode(node) || isVirtualNode(node);
  return (
    <>
      <button
        type="button"
        className={`nb-library-picker-row ${selectedId === id ? "is-selected" : ""}`}
        style={{ "--nb-tree-depth": depth }}
        disabled={disabled}
        title={disabled ? labels.library_move_target_unavailable || "" : ""}
        onClick={() => onSelect(node)}
      >
        <span className={`nb-library-type is-${type}`}>
          {type === "root" ? "R" : type === "folder" ? "D" : type === "media" ? "M" : "P"}
        </span>
        <span>{libraryNodeTitle(node)}</span>
      </button>
      {asArray(node.children).map((child) => (
        <TargetNode
          key={libraryNodeId(child)}
          node={child}
          depth={depth + 1}
          disabledIds={disabledIds}
          selectedId={selectedId}
          labels={labels}
          onSelect={onSelect}
        />
      ))}
    </>
  );
}

export function MoveTargetPicker({
  labels = {},
  nodes = [],
  activeNode,
  initialParentId = "",
  onCancel,
  onConfirm,
}) {
  const activeId = libraryNodeId(activeNode);
  const disabledIds = useMemo(() => {
    const ids = descendantIds(activeNode);
    if (activeId) {
      ids.add(activeId);
    }
    return ids;
  }, [activeId, activeNode]);
  const [selectedId, setSelectedId] = useState(cleanText(initialParentId) || "root");
  const selectedNode = useMemo(() => {
    const stack = [...asArray(nodes)];
    while (stack.length) {
      const node = stack.shift();
      if (libraryNodeId(node) === selectedId) {
        return node;
      }
      stack.push(...asArray(node.children));
    }
    return null;
  }, [nodes, selectedId]);
  return (
    <LibraryDialog
      labels={labels}
      title={labels.library_move_to || "Move to"}
      subtitle={libraryNodeTitle(activeNode)}
      confirmLabel={labels.library_move || "Move"}
      disabled={!selectedNode || disabledIds.has(selectedId) || !isParentableNode(selectedNode) || isVirtualNode(selectedNode)}
      onCancel={onCancel}
      onConfirm={() => onConfirm?.(selectedId)}
    >
      <div className="nb-library-picker-tree" role="tree">
        {asArray(nodes).map((node) => (
          <TargetNode
            key={libraryNodeId(node)}
            node={node}
            depth={0}
            disabledIds={disabledIds}
            selectedId={selectedId}
            labels={labels}
            onSelect={(target) => setSelectedId(libraryNodeId(target))}
          />
        ))}
      </div>
    </LibraryDialog>
  );
}
