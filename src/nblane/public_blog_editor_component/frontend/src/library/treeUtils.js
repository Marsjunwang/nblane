export function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

export function asArray(value) {
  return Array.isArray(value) ? value : [];
}

export function libraryNodeTitle(node) {
  const source = node && typeof node === "object" ? node : {};
  return cleanText(
    source.title ||
      source.name ||
      source.slug ||
      source.route ||
      source.ref ||
      source.id ||
      "Untitled",
  );
}

export function libraryNodeId(node, fallback = "") {
  const source = node && typeof node === "object" ? node : {};
  return cleanText(
    source.id ||
      source.node_id ||
      source.route ||
      source.slug ||
      source.ref ||
      fallback,
  );
}

export function libraryNodeType(node) {
  const source = node && typeof node === "object" ? node : {};
  const type = cleanText(source.type || "").toLowerCase();
  if (type === "folder" || type === "directory") {
    return "folder";
  }
  if (type === "root") {
    return "root";
  }
  if (type === "media" || type === "asset" || type === "image" || type === "video") {
    return "media";
  }
  return type || "post";
}

export function parentIdFor(node) {
  return cleanText(node?.parent_id || "") || "root";
}

export function isParentableNode(node) {
  const type = libraryNodeType(node);
  return type === "root" || type === "folder" || type === "post";
}

export function isRootNode(node) {
  return libraryNodeId(node) === "root" || libraryNodeType(node) === "root";
}

export function isVirtualNode(node) {
  return node?.virtual === true || cleanText(node?.id || "").startsWith("post:");
}

export function flattenLibraryTree(nodes, depth = 0, parent = null, rows = []) {
  for (const node of asArray(nodes)) {
    rows.push({
      node,
      depth,
      parent,
      parentType: parent ? libraryNodeType(parent) : "",
      parentTitle: parent ? libraryNodeTitle(parent) : "",
    });
    flattenLibraryTree(node.children, depth + 1, node, rows);
  }
  return rows;
}

export function buildNodeIndex(nodes) {
  const rows = flattenLibraryTree(nodes);
  return new Map(rows.map((row) => [libraryNodeId(row.node), row]));
}

export function descendantIds(node, ids = new Set()) {
  for (const child of asArray(node?.children)) {
    const id = libraryNodeId(child);
    if (id) {
      ids.add(id);
    }
    descendantIds(child, ids);
  }
  return ids;
}

export function isDescendantId(node, id) {
  return descendantIds(node).has(cleanText(id));
}

export function ancestorIdsForNodeId(nodeById, nodeId) {
  const ids = [];
  let row = nodeById.get(cleanText(nodeId));
  const seen = new Set();
  while (row?.parent) {
    const parentId = libraryNodeId(row.parent);
    if (!parentId || seen.has(parentId)) {
      break;
    }
    seen.add(parentId);
    ids.push(parentId);
    row = nodeById.get(parentId);
  }
  return ids;
}

export function directExpandableRootChildren(nodes) {
  const ids = new Set();
  for (const root of asArray(nodes)) {
    if (libraryNodeId(root) === "root" || libraryNodeType(root) === "root") {
      if (asArray(root.children).length) {
        ids.add(libraryNodeId(root));
      }
      for (const child of asArray(root.children)) {
        if (asArray(child.children).length) {
          ids.add(libraryNodeId(child));
        }
      }
    }
  }
  return ids;
}

export function validTreeIds(nodes) {
  return new Set(flattenLibraryTree(nodes).map((row) => libraryNodeId(row.node)).filter(Boolean));
}

export function filterTreeWithAncestors(nodes, query) {
  const cleanQuery = cleanText(query).trim().toLowerCase();
  if (!cleanQuery) {
    return nodes;
  }
  const visit = (items) => {
    const next = [];
    for (const node of asArray(items)) {
      const children = visit(node.children);
      const haystack = [
        libraryNodeTitle(node),
        libraryNodeType(node),
        node.status,
        node.visibility,
        node.ref,
        node.route,
        node.slug,
        node.id,
      ]
        .map(cleanText)
        .join(" ")
        .toLowerCase();
      if (children.length || haystack.includes(cleanQuery)) {
        next.push({ ...node, children });
      }
    }
    return next;
  };
  return visit(nodes);
}

export function childCounts(node) {
  const children = asArray(node?.children);
  const subdocs = children.filter((child) => libraryNodeType(child) !== "folder").length;
  return { children: children.length, subdocs };
}
