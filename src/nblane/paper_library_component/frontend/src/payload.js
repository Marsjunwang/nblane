export function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

export function asArray(value) {
  return Array.isArray(value) ? value : [];
}

export function nodeId(node, fallback = "") {
  const source = node && typeof node === "object" ? node : {};
  return cleanText(source.id || source.node_id || fallback);
}

export function nodeTitle(node) {
  const source = node && typeof node === "object" ? node : {};
  return cleanText(source.title || source.name || source.path || source.id || "Untitled");
}

export function nodeType(node) {
  const source = node && typeof node === "object" ? node : {};
  const type = cleanText(source.type || "").toLowerCase();
  return type || "view";
}

export function flattenItems(items, depth = 0, rows = []) {
  for (const item of asArray(items)) {
    rows.push({ item, depth });
    flattenItems(item.children, depth + 1, rows);
  }
  return rows;
}

export function allItemIds(items) {
  return new Set(flattenItems(items).map((row) => nodeId(row.item)).filter(Boolean));
}

export function expandableIds(items) {
  return new Set(
    flattenItems(items)
      .filter((row) => asArray(row.item.children).length > 0)
      .map((row) => nodeId(row.item))
      .filter(Boolean),
  );
}

export function filterItems(items, query) {
  const cleanQuery = cleanText(query).trim().toLowerCase();
  if (!cleanQuery) {
    return asArray(items);
  }
  const visit = (rows) => {
    const out = [];
    for (const item of asArray(rows)) {
      const children = visit(item.children);
      const haystack = [
        nodeTitle(item),
        nodeType(item),
        item.path,
        item.status,
        item.description,
        item.id,
      ]
        .map(cleanText)
        .join(" ")
        .toLowerCase();
      if (children.length || haystack.includes(cleanQuery)) {
        out.push({ ...item, children });
      }
    }
    return out;
  };
  return visit(items);
}

export function normalizePayload(raw) {
  const payload = raw && typeof raw === "object" ? raw : {};
  return {
    activeView: cleanText(payload.active_view || "all"),
    activeNodeId: cleanText(payload.active_node_id || ""),
    activeLabel: cleanText(payload.active_label || ""),
    profile: cleanText(payload.profile || ""),
    query: cleanText(payload.query || ""),
    sortMode: cleanText(payload.sort_mode || "recent"),
    detailId: cleanText(payload.detail_id || ""),
    focus: cleanText(payload.focus || payload.deep_link?.focus || ""),
    action: cleanText(payload.action || payload.deep_link?.action || ""),
    returnTo: cleanText(payload.return_to || payload.deep_link?.return_to || ""),
    returnUrl: cleanText(payload.return_url || payload.deep_link?.return_url || ""),
    selectedPaperIds: asArray(payload.selected_paper_ids).map(cleanText).filter(Boolean),
    papers: asArray(payload.papers),
    detail: payload.detail && typeof payload.detail === "object" ? payload.detail : {},
    metrics: payload.metrics && typeof payload.metrics === "object" ? payload.metrics : {},
    diagnostics: asArray(payload.diagnostics).map(cleanText).filter(Boolean),
    sections: asArray(payload.sections),
    capabilities: payload.capabilities && typeof payload.capabilities === "object" ? payload.capabilities : {},
    labels: payload.labels && typeof payload.labels === "object" ? payload.labels : {},
  };
}
