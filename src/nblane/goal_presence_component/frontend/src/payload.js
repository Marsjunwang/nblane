export function isRenderable(payload) {
  return Boolean(payload && payload.visibility && payload.visibility !== "private");
}

export function statusLabel(payload) {
  return payload?.status?.label || payload?.status_label || payload?.status || "";
}

export function displayLabel(payload) {
  const texts = payload?.texts || {};
  if (!isRenderable(payload)) {
    return "";
  }
  if (payload.visibility === "hidden") {
    return texts.goal_set || texts.current || "";
  }
  if (payload.visibility === "discreet") {
    return payload.label || texts.default_label || texts.current || "";
  }
  return payload.title || payload.label || texts.default_label || texts.current || "";
}

export function displaySummary(payload) {
  if (payload?.visibility !== "visible") {
    return "";
  }
  return payload.summary || "";
}

export function displayFocus(payload) {
  if (payload?.visibility !== "visible" || !Array.isArray(payload.focus)) {
    return [];
  }
  return payload.focus.filter(Boolean).slice(0, 3);
}

export function detailTitle(payload) {
  const texts = payload?.texts || {};
  if (payload?.visibility === "hidden") {
    return texts.details || texts.current || "";
  }
  return displayLabel(payload);
}
