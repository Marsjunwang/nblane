import React, { useEffect, useMemo, useState } from "react";

function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

function label(labels, key, fallback) {
  return cleanText(labels?.[key] || fallback || key);
}

const TOOLBAR_ACTIONS = [
  {
    operation: "polish",
    labelKey: "ai_action_polish",
    fallback: "Polish",
    titleKey: "ai_action_polish_help",
    title: "Improve clarity while keeping the original meaning.",
  },
  {
    operation: "shorten",
    labelKey: "ai_action_shorten",
    fallback: "Shorten",
    titleKey: "ai_action_shorten_help",
    title: "Make the selection tighter.",
  },
  {
    operation: "expand",
    labelKey: "ai_action_expand",
    fallback: "Expand",
    titleKey: "ai_action_expand_help",
    title: "Add useful detail to the selection.",
  },
  {
    operation: "continue",
    labelKey: "ai_action_continue",
    fallback: "Continue",
    titleKey: "ai_action_continue_help",
    title: "Write the next paragraph from this point.",
  },
  {
    operation: "translate",
    labelKey: "ai_action_translate",
    fallback: "Translate",
    titleKey: "ai_action_translate_help",
    title: "Translate using the configured reply language.",
  },
  {
    operation: "tone",
    labelKey: "ai_action_tone",
    fallback: "Tone",
    titleKey: "ai_action_tone_help",
    title: "Change tone while preserving substance.",
  },
  {
    operation: "formula",
    labelKey: "ai_action_formula",
    fallback: "LaTeX",
    titleKey: "ai_action_formula_help",
    title: "Convert the selection to a display formula.",
  },
  {
    operation: "visual",
    visual_kind: "example",
    context_window: "current_block",
    labelKey: "ai_action_visual",
    fallback: "Visual",
    titleKey: "ai_action_visual_help",
    title: "Create a visual prompt from this paragraph.",
  },
  {
    operation: "outline",
    labelKey: "ai_action_outline",
    fallback: "Outline",
    titleKey: "ai_action_outline_help",
    title: "Extract or generate an outline.",
  },
];

function hasUsableContext(selectedBlock) {
  const context = selectedBlock && typeof selectedBlock === "object" ? selectedBlock : {};
  const selectionText = cleanText(context.selection_text).trim();
  return Boolean(selectionText);
}

function selectionToolbarPosition() {
  if (typeof window === "undefined") {
    return null;
  }
  const selection = window.getSelection?.();
  if (!selection || selection.rangeCount < 1 || selection.isCollapsed) {
    return null;
  }
  const rect = selection.getRangeAt(0).getBoundingClientRect();
  if (!rect || (!rect.width && !rect.height)) {
    return null;
  }
  const toolbarWidth = Math.min(680, window.innerWidth - 24);
  const left = Math.max(
    12,
    Math.min(window.innerWidth - toolbarWidth - 12, rect.left + rect.width / 2 - toolbarWidth / 2),
  );
  const top = Math.max(12, rect.top - 48);
  return {
    position: "fixed",
    left: `${left}px`,
    top: `${top}px`,
    maxWidth: `${toolbarWidth}px`,
  };
}

export function SelectionAIToolbar({
  editable,
  labels,
  selectedBlock,
  onAction,
  disabled = false,
}) {
  const visible = editable && hasUsableContext(selectedBlock);
  const [style, setStyle] = useState(null);
  const actions = useMemo(() => TOOLBAR_ACTIONS, []);

  useEffect(() => {
    if (!visible) {
      setStyle(null);
      return undefined;
    }
    const update = () => setStyle(selectionToolbarPosition());
    update();
    window.addEventListener("selectionchange", update);
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    return () => {
      window.removeEventListener("selectionchange", update);
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
  }, [visible, selectedBlock]);

  if (!visible) {
    return null;
  }

  return (
    <div
      className={`nb-ai-selection-toolbar ${style ? "is-floating" : "is-docked"}`}
      style={style || undefined}
      onMouseDown={(event) => event.preventDefault()}
    >
      {actions.map((action) => (
        <button
          type="button"
          className="nb-ai-tool-button"
          disabled={disabled || !editable}
          key={action.operation}
          title={label(labels, action.titleKey, action.title)}
          onClick={() =>
            onAction({
              operation: action.operation,
              trigger: "selection_toolbar",
              visual_kind: cleanText(action.visual_kind),
              context_window: cleanText(action.context_window || "selection"),
            })
          }
        >
          {label(labels, action.labelKey, action.fallback)}
        </button>
      ))}
    </div>
  );
}
