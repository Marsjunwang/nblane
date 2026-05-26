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

export function explanationLinksFrom(value) {
  const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  const raw = Array.isArray(value)
    ? value
    : (source.explanation_links || source.reading_links || source.explainers);
  const seen = new Set();
  return asArray(raw)
    .map((item) => {
      if (typeof item === "string") {
        const url = cleanText(item);
        return { url, title: url, source: "", summary: "" };
      }
      if (!item || typeof item !== "object") {
        return null;
      }
      const url = cleanText(item.url || item.link);
      const title = cleanText(item.title || item.name || url);
      const site = cleanText(item.source || item.site || item.platform);
      const summary = cleanText(item.summary || item.note || item.why);
      return { url, title, source: site, summary };
    })
    .filter((item) => {
      if (!item?.url || seen.has(item.url)) {
        return false;
      }
      seen.add(item.url);
      return true;
    })
    .slice(0, 6);
}

export function paperMatchesQuery(paper, query) {
  const cleanQuery = cleanText(query).toLowerCase();
  if (!cleanQuery) {
    return true;
  }
  const linkText = explanationLinksFrom(paper)
    .flatMap((link) => [link.title, link.source, link.summary, link.url])
    .join(" ");
  const haystack = [
    paper?.title,
    paper?.meta,
    paper?.summary,
    paper?.notes,
    paper?.tree_path,
    paper?.status_label,
    paper?.metrics,
    linkText,
    ...asArray(paper?.tags),
    ...asArray(paper?.badges),
  ]
    .map(cleanText)
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return haystack.includes(cleanQuery);
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
