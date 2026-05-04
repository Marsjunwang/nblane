import {
  cleanText,
  isDescendantId,
  isRootNode,
  isVirtualNode,
  libraryNodeId,
  libraryNodeTitle,
  libraryNodeType,
  parentIdFor,
} from "./treeUtils.js";

function isNodeParentableForDrop(node) {
  const type = libraryNodeType(node);
  return type === "root" || type === "folder" || type === "post";
}

function normalizeDropPosition(position = "after") {
  const clean = cleanText(position).toLowerCase();
  if (clean === "before" || clean === "upper") {
    return "before";
  }
  if (clean === "into") {
    return "into";
  }
  if (clean === "after" || clean === "lower") {
    return "after";
  }
  return "";
}

function indicatorEdgeFor(position) {
  return position === "before" ? "top" : "bottom";
}

export function canDropOn(activeNode, overNode, position = "after") {
  const activeId = libraryNodeId(activeNode);
  const overId = libraryNodeId(overNode);
  const dropPosition = normalizeDropPosition(position);
  if (
    !activeId ||
    !overId ||
    !dropPosition ||
    activeId === overId ||
    isRootNode(activeNode) ||
    isVirtualNode(overNode)
  ) {
    return false;
  }
  if (dropPosition === "into") {
    if (!isNodeParentableForDrop(overNode)) {
      return false;
    }
    return !isDescendantId(activeNode, overId);
  }
  if (dropPosition === "before" || dropPosition === "after") {
    if (isRootNode(overNode)) {
      return false;
    }
    const parentId = parentIdFor(overNode);
    if (parentId === activeId) {
      return false;
    }
    return !isDescendantId(activeNode, parentId);
  }
  return false;
}

export function resolveDropIntent(activeNode, overNode, position = "after", options = {}) {
  const dropPosition = normalizeDropPosition(position);
  if (!canDropOn(activeNode, overNode, dropPosition)) {
    return null;
  }
  const activeId = libraryNodeId(activeNode);
  const overId = libraryNodeId(overNode);
  const overDepth = Number.isFinite(Number(options.overDepth))
    ? Number(options.overDepth)
    : 0;
  const baseIntent = {
    position: dropPosition,
    indentDepth: dropPosition === "into" ? overDepth + 1 : overDepth,
    indicatorEdge: indicatorEdgeFor(dropPosition),
  };
  if (dropPosition === "before" || dropPosition === "after") {
    const parentId = parentIdFor(overNode);
    return {
      ...baseIntent,
      kind: isVirtualNode(activeNode) ? "attach-existing" : "reorder",
      activeId,
      overId,
      parentId,
      beforeNodeId: dropPosition === "before" ? overId : "",
      afterNodeId: dropPosition === "after" ? overId : "",
      targetTitle: libraryNodeTitle(overNode),
      targetType: libraryNodeType(overNode),
    };
  }
  return {
    ...baseIntent,
    kind: isVirtualNode(activeNode) ? "attach-existing" : "move-into",
    activeId,
    overId,
    parentId: overId,
    targetTitle: libraryNodeTitle(overNode),
    targetType: libraryNodeType(overNode),
  };
}

function attachRefFor(node) {
  return cleanText(node?.ref || node?.route || node?.slug || "");
}

export function actionForDropIntent(intent, activeNode) {
  if (!intent || !activeNode) {
    return null;
  }
  if (intent.kind === "attach-existing") {
    const ref = attachRefFor(activeNode);
    if (!ref) {
      return null;
    }
    return {
      action: "library_attach_existing",
      payload: {
        ref,
        title: libraryNodeTitle(activeNode),
        parent_id: intent.parentId,
        target_parent_id: intent.parentId,
        before_node_id: intent.beforeNodeId || "",
        after_node_id: intent.afterNodeId || "",
        drop_intent: intent.position,
      },
    };
  }
  if (intent.kind === "move-into") {
    return {
      action: "library_move_node",
      payload: {
        node_id: intent.activeId,
        parent_id: intent.parentId,
        target_parent_id: intent.parentId,
        drop_intent: "into",
      },
    };
  }
  if (intent.kind === "reorder") {
    return {
      action: "library_reorder_node",
      payload: {
        node_id: intent.activeId,
        parent_id: intent.parentId,
        target_parent_id: intent.parentId,
        before_node_id: intent.beforeNodeId || "",
        after_node_id: intent.afterNodeId || "",
        drop_intent: intent.position,
      },
    };
  }
  return null;
}

export function dropIntentLabel(intent, labels = {}) {
  if (!intent) {
    return "";
  }
  const title = intent.targetTitle || "";
  const get = (key, fallback) => cleanText(labels[key] || fallback || key);
  if (intent.position === "before") {
    return get("library_drop_before", `Place before "${title}"`).replace("{title}", title);
  }
  if (intent.position === "after") {
    return get("library_drop_after", `Place after "${title}"`).replace("{title}", title);
  }
  if (intent.targetType === "post") {
    return get("library_drop_as_subdoc", `Attach as a subdoc of "${title}"`).replace("{title}", title);
  }
  if (intent.targetType === "root") {
    return get("library_drop_into_root", "Place at library root").replace("{title}", title);
  }
  return get("library_drop_into_folder", `Move into "${title}"`).replace("{title}", title);
}
