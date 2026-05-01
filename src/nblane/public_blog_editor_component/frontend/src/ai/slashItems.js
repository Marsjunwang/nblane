import React from "react";

function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

function slashLabel(labels, key, fallback) {
  return cleanText(labels?.[key] || fallback);
}

function icon(text) {
  return React.createElement("span", { className: "nb-slash-icon" }, text);
}

const AI_SLASH_ITEMS = [
  {
    operation: "continue",
    titleKey: "ai_slash_write_next",
    title: "AI write next paragraph",
    subtextKey: "ai_slash_write_next_help",
    subtext: "Continue from the current cursor context.",
    aliases: ["ai", "write", "next", "continue", "写下一段", "续写"],
    icon: "ai",
  },
  {
    operation: "outline",
    titleKey: "ai_slash_outline",
    title: "Outline",
    subtextKey: "ai_slash_outline_help",
    subtext: "Generate or refine a heading outline.",
    aliases: ["outline", "scaffold", "大纲", "结构"],
    icon: "ol",
  },
  {
    operation: "formula",
    titleKey: "ai_slash_formula",
    title: "Formula",
    subtextKey: "ai_slash_formula_help",
    subtext: "Convert natural language into a LaTeX display block.",
    aliases: ["formula", "latex", "math", "公式"],
    icon: "fx",
  },
  {
    operation: "visual",
    titleKey: "ai_slash_visual",
    title: "Visual",
    subtextKey: "ai_slash_visual_help",
    subtext: "Create a visual block prompt from nearby context.",
    aliases: ["visual", "image", "picture", "图", "配图"],
    icon: "vis",
  },
  {
    operation: "visual",
    visual_kind: "diagram",
    titleKey: "ai_slash_diagram",
    title: "Diagram",
    subtextKey: "ai_slash_diagram_help",
    subtext: "Create a diagram prompt or Mermaid draft.",
    aliases: ["diagram", "mermaid", "flowchart", "图表", "流程图"],
    icon: "dia",
  },
  {
    operation: "polish",
    titleKey: "ai_slash_polish",
    title: "Polish current block",
    subtextKey: "ai_slash_polish_help",
    subtext: "Improve the selected text or current block.",
    aliases: ["polish", "rewrite", "润色", "改写"],
    icon: "rw",
  },
];

export function getAISlashMenuItems({ labels = {}, onAction }) {
  return AI_SLASH_ITEMS.map((item) => ({
    title: slashLabel(labels, item.titleKey, item.title),
    subtext: slashLabel(labels, item.subtextKey, item.subtext),
    aliases: item.aliases,
    group: slashLabel(labels, "ai_slash_group", "AI actions"),
    icon: icon(item.icon),
    onItemClick: () => {
      onAction?.({
        operation: item.operation,
        trigger: "slash",
        visual_kind: cleanText(item.visual_kind),
      });
    },
  }));
}
