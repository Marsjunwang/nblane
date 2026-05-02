import React, { useMemo } from "react";

function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function label(labels, key, fallback = "") {
  return cleanText(labels?.[key] || fallback || key);
}

function inlineContentText(content) {
  if (typeof content === "string") {
    return content;
  }
  if (Array.isArray(content)) {
    return content.map((item) => inlineContentText(item)).filter(Boolean).join("");
  }
  if (!content || typeof content !== "object") {
    return "";
  }
  if (typeof content.text === "string") {
    return content.text;
  }
  if (content.content !== undefined) {
    return inlineContentText(content.content);
  }
  if (content.children !== undefined) {
    return inlineContentText(content.children);
  }
  return "";
}

function flattenBlocks(blocks, output = []) {
  for (const block of asArray(blocks)) {
    output.push(block);
    flattenBlocks(block?.children, output);
  }
  return output;
}

function blockText(block) {
  const direct = inlineContentText(block?.content).trim();
  const children = asArray(block?.children).map(blockText).filter(Boolean).join("\n");
  return [direct, children].filter(Boolean).join("\n").trim();
}

function headingLevel(block) {
  const level = Number(block?.props?.level || 2);
  return Number.isFinite(level) ? Math.max(1, Math.min(6, level)) : 2;
}

function outlineRows(blocks) {
  const flat = flattenBlocks(blocks);
  const rows = [];
  for (let index = 0; index < flat.length; index += 1) {
    const block = flat[index];
    if (cleanText(block?.type) !== "heading") {
      continue;
    }
    const level = headingLevel(block);
    const childBlocks = [];
    for (let next = index + 1; next < flat.length; next += 1) {
      const candidate = flat[next];
      if (cleanText(candidate?.type) === "heading" && headingLevel(candidate) <= level) {
        break;
      }
      childBlocks.push(candidate);
    }
    const title = blockText(block) || label({}, "outline_untitled", "Untitled");
    const sectionText = [title, ...childBlocks.map(blockText)]
      .filter(Boolean)
      .join("\n\n")
      .trim();
    rows.push({
      id: cleanText(block?.id),
      block,
      level,
      title,
      childCount: childBlocks.length,
      sectionText,
      childBlockIds: childBlocks.map((item) => cleanText(item?.id)).filter(Boolean),
    });
  }
  return rows;
}

export function OutlinePanel({
  blocks,
  editable,
  labels,
  pending = false,
  onExpandSection,
}) {
  const rows = useMemo(() => outlineRows(blocks), [blocks]);

  return (
    <section className="nb-outline-panel">
      <div className="nb-panel-title">
        {label(labels, "outline_panel", "Outline")}
      </div>
      {rows.length ? (
        <div className="nb-outline-list">
          {rows.map((row) => (
            <div
              className="nb-outline-row"
              style={{ "--nb-outline-depth": row.level - 1 }}
              key={row.id || `${row.title}-${row.level}`}
            >
              <button
                type="button"
                className="nb-outline-title"
                title={row.title}
                onClick={() => onExpandSection?.(row)}
                disabled={!editable || pending}
              >
                {row.title}
              </button>
              <button
                type="button"
                className="nb-outline-expand"
                disabled={!editable || pending}
                onClick={() => onExpandSection?.(row)}
              >
                {label(labels, "outline_expand_section", "Expand")}
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="nb-empty">{label(labels, "outline_empty", "No headings yet.")}</p>
      )}
    </section>
  );
}
