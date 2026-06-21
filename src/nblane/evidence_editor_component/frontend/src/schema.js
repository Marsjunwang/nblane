// Shared constants for the evidence editor frontend.

// Origin badge colors. Color never carries meaning alone — badges always
// render the text label too (color-blind safe).
export const ORIGIN_COLORS = {
  kanban_task: "#1f7a52",
  resume_parse: "#b91c1c",
  output: "#b45309",
  manual_daily: "#0e7490",
  paper: "#7c3aed",
  research_source: "#334155",
};

export function originColor(origin) {
  return ORIGIN_COLORS[origin] || "#64748b";
}

// Editable scalar fields in the detail "Basics" section.
export const BASIC_FIELDS = [
  "type",
  "date",
  "strength",
  "confidence",
  "review_status",
  "public_readiness",
  "url",
];

// Fields the AI reformat may propose (never touches original_content).
export const REFORMAT_FIELDS = ["title", "summary", "formatted_content"];

export function cleanText(value, fallback = "") {
  if (value == null) return fallback;
  const text = String(value);
  return text.length ? text : fallback;
}

export function asArray(value) {
  return Array.isArray(value) ? value : [];
}

export function label(labels, key, fallback) {
  const map = labels && typeof labels === "object" ? labels : {};
  const val = map[key];
  return val == null || val === "" ? fallback : String(val);
}
