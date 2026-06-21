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

// Minimal, dependency-free Markdown -> safe HTML for the read-only preview of
// formatted_content. Supports the structured bodies the AI produces: ATX
// headings, bold, inline code, unordered/ordered lists, and paragraphs.
// Everything is HTML-escaped first, so the output is safe to inject.
export function escapeHtml(text) {
  return String(text == null ? "" : text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function inlineMarkdown(text) {
  // Operates on already-escaped text.
  return text
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>");
}

export function renderMarkdown(text) {
  const src = String(text == null ? "" : text);
  if (!src.trim()) return "";
  const lines = src.split(/\r?\n/);
  const html = [];
  let listType = null; // "ul" | "ol" | null
  const closeList = () => {
    if (listType) {
      html.push(`</${listType}>`);
      listType = null;
    }
  };
  for (const raw of lines) {
    const line = raw.replace(/\s+$/, "");
    if (!line.trim()) {
      closeList();
      continue;
    }
    const esc = escapeHtml(line);
    const heading = esc.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      closeList();
      const level = heading[1].length;
      html.push(`<h${level}>${inlineMarkdown(heading[2])}</h${level}>`);
      continue;
    }
    const ul = esc.match(/^[-*]\s+(.*)$/);
    if (ul) {
      if (listType !== "ul") {
        closeList();
        html.push("<ul>");
        listType = "ul";
      }
      html.push(`<li>${inlineMarkdown(ul[1])}</li>`);
      continue;
    }
    const ol = esc.match(/^\d+\.\s+(.*)$/);
    if (ol) {
      if (listType !== "ol") {
        closeList();
        html.push("<ol>");
        listType = "ol";
      }
      html.push(`<li>${inlineMarkdown(ol[1])}</li>`);
      continue;
    }
    closeList();
    html.push(`<p>${inlineMarkdown(esc)}</p>`);
  }
  closeList();
  return html.join("\n");
}
