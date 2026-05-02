import React, { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import { AIBlockDiff } from "./AIBlockDiff.jsx";
import { MermaidRenderer } from "../blocks/MermaidRenderer.jsx";

function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

function asObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function label(labels, key, fallback = "") {
  return cleanText(labels?.[key] || fallback || key);
}

function patchId(patch, index = 0) {
  return cleanText(
    patch?.patch_id ||
      patch?.id ||
      patch?.provenance?.source_event_id ||
      `ai-patch-${index}`,
  );
}

function patchTitle(patch, labels) {
  const operation = cleanText(patch?.operation || "patch");
  return `${label(labels, "ai_patch_candidate", "Patch candidate")} / ${operation}`;
}

function targetSummary(patch) {
  const target = asObject(patch?.target);
  const blockIds = asArray(target.block_ids).map(cleanText).filter(Boolean);
  const singleBlock = cleanText(target.block_id).trim();
  if (blockIds.length) {
    return blockIds.join(", ");
  }
  if (singleBlock) {
    return singleBlock;
  }
  if (cleanText(target.selection_text).trim()) {
    return "selection";
  }
  return "cursor";
}

function blockPatchSummary(blockPatch) {
  const patch = asObject(blockPatch);
  const block = asObject(patch.block);
  const op = cleanText(patch.op || "insert");
  const blockType = cleanText(block.type || "block");
  const blockId = cleanText(patch.block_id || block.id || "");
  return [op, blockType, blockId].filter(Boolean).join(" / ");
}

function metaPatchRows(metaPatch) {
  const meta = asObject(metaPatch);
  return Object.keys(meta)
    .sort()
    .map((key) => ({ key, value: meta[key] }));
}

function patchPreviewBefore(patch) {
  const target = asObject(patch?.target);
  const selection = cleanText(target.selection_text).trim();
  if (selection) {
    return selection;
  }
  const surrounding = asArray(target.surrounding_blocks)
    .map((block) => cleanText(block?.text).trim())
    .filter(Boolean);
  return surrounding[0] || "";
}

function firstBlockOfType(patch, blockType) {
  return (
    asArray(patch?.block_patches)
      .map(asObject)
      .map((item) => asObject(item.block))
      .find((block) => cleanText(block.type) === blockType) || null
  );
}

function FormulaPreview({ latex }) {
  const source = cleanText(latex).trim();
  const rendered = useMemo(() => {
    if (!source) {
      return { html: "", error: "" };
    }
    try {
      return {
        html: katex.renderToString(source, {
          displayMode: true,
          throwOnError: false,
          strict: false,
          trust: false,
        }),
        error: "",
      };
    } catch (err) {
      return {
        html: "",
        error: err instanceof Error ? err.message : String(err),
      };
    }
  }, [source]);
  if (!source) {
    return null;
  }
  if (!rendered.html || rendered.error) {
    return <pre className="nb-math-fallback">{source}</pre>;
  }
  return (
    <div
      className="nb-ai-formula-preview"
      dangerouslySetInnerHTML={{ __html: rendered.html }}
    />
  );
}

function DiagramPreview({ block }) {
  const props = asObject(block?.props);
  const mermaid = cleanText(props.mermaid || props.prompt).trim();
  if (!mermaid) {
    return null;
  }
  return <MermaidRenderer source={mermaid} />;
}

function AssetPreview({ asset }) {
  const previewSrc = cleanText(asset.preview_src || asset.preview || asset.thumbnail).trim();
  if (!previewSrc) {
    return null;
  }
  const kind = cleanText(asset.kind || "image").toLowerCase();
  if (kind === "video" || /^data:video\//iu.test(previewSrc)) {
    return (
      <video
        className="nb-ai-asset-preview"
        src={previewSrc}
        controls
        preload="metadata"
      />
    );
  }
  return <img className="nb-ai-asset-preview" src={previewSrc} alt="AI asset preview" />;
}

export function CandidatePatchPanel({
  labels,
  patches,
  pendingAction = null,
  editable,
  onAccept,
  onReject,
  onRegenerate,
  onCancelPending,
}) {
  const rows = useMemo(() => asArray(patches).map(asObject), [patches]);
  const hasPending = Boolean(pendingAction);

  if (!rows.length && !hasPending) {
    return null;
  }

  return (
    <section className="nb-ai-patch-panel">
      <div className="nb-panel-title">
        {label(labels, "ai_patch_panel", "AI patch candidates")}
      </div>
      {hasPending ? (
        <article className="nb-ai-patch-card is-pending">
          <div className="nb-candidate-title">
            {label(labels, "ai_patch_generating", "Generating patch")}
          </div>
          <div className="nb-loading-row">
            <span className="nb-loading-dot" />
            <span>{cleanText(pendingAction.operation || "AI")}</span>
          </div>
          {cleanText(pendingAction.text).trim() ? (
            <pre className="nb-ai-stream-preview">
              {cleanText(pendingAction.text).slice(0, 1200)}
            </pre>
          ) : null}
          {cleanText(pendingAction.error).trim() ? (
            <p className="nb-editor-error">
              {cleanText(pendingAction.error)}
            </p>
          ) : null}
          {onCancelPending ? (
            <div className="nb-row-actions">
              <button
                type="button"
                className="nb-button danger"
                disabled={!editable}
                onClick={() => onCancelPending(pendingAction)}
              >
                {label(labels, "ai_stream_cancel", "Cancel")}
              </button>
            </div>
          ) : null}
        </article>
      ) : null}
      {rows.map((patch, index) => {
        const id = patchId(patch, index);
        const warnings = asArray(patch.warnings).map(cleanText).filter(Boolean);
        const assets = asArray(patch.assets).map(asObject);
        const previewAssets = assets.filter((asset) =>
          cleanText(asset.preview_src || asset.preview || asset.thumbnail).trim(),
        );
        const blockPatches = asArray(patch.block_patches).map(asObject);
        const mathBlock = firstBlockOfType(patch, "math_block");
        const visualBlock = firstBlockOfType(patch, "visual_block");
        const metaRows = metaPatchRows(patch.meta_patch);
        const markdown = cleanText(patch.markdown_fallback).trim();
        const before = patchPreviewBefore(patch);
        return (
          <article className="nb-ai-patch-card" key={`${id}-${index}`}>
            <div className="nb-candidate-title">{patchTitle(patch, labels)}</div>
            <div className="nb-ai-patch-target">
              {label(labels, "ai_patch_target", "Target")}: {targetSummary(patch)}
            </div>
            {blockPatches.length ? (
              <ul className="nb-compact-list">
                {blockPatches.map((blockPatch, patchIndex) => (
                  <li key={`${id}-block-${patchIndex}`}>
                    {blockPatchSummary(blockPatch)}
                  </li>
                ))}
              </ul>
            ) : null}
            {metaRows.length ? (
              <details>
                <summary>{label(labels, "ai_patch_meta", "Meta changes")}</summary>
                <dl className="nb-ai-patch-meta">
                  {metaRows.map((row) => (
                    <React.Fragment key={row.key}>
                      <dt>{row.key}</dt>
                      <dd>{JSON.stringify(row.value)}</dd>
                    </React.Fragment>
                  ))}
                </dl>
              </details>
            ) : null}
            {warnings.length ? (
              <ul className="nb-compact-list">
                {warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : null}
            {mathBlock ? (
              <FormulaPreview latex={asObject(mathBlock.props).latex} />
            ) : null}
            {cleanText(asObject(visualBlock?.props).asset_type) === "diagram" ? (
              <DiagramPreview block={visualBlock} />
            ) : null}
            {previewAssets.length ? (
              <div className="nb-ai-asset-grid">
                {previewAssets.map((asset, assetIndex) => (
                  <AssetPreview asset={asset} key={`${id}-asset-preview-${assetIndex}`} />
                ))}
              </div>
            ) : null}
            {assets.length ? (
              <details>
                <summary>{label(labels, "ai_patch_assets", "Assets")}</summary>
                <ul className="nb-compact-list">
                  {assets.map((asset, assetIndex) => (
                    <li key={`${id}-asset-${assetIndex}`}>
                      {cleanText(asset.kind || "asset")}
                      {asset.src ? ` / ${cleanText(asset.src)}` : ""}
                      {asset.candidate_path ? ` / ${cleanText(asset.candidate_path)}` : ""}
                      {asset.prompt ? ` / ${cleanText(asset.prompt).slice(0, 120)}` : ""}
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}
            {markdown ? (
              <>
                <AIBlockDiff before={before} after={markdown} />
                <details>
                  <summary>{label(labels, "ai_patch_markdown", "Markdown")}</summary>
                  <pre>{markdown.slice(0, 1200)}</pre>
                </details>
              </>
            ) : null}
            <div className="nb-row-actions">
              <button
                type="button"
                className="nb-button primary"
                disabled={!editable}
                onClick={() => onAccept(patch, { blockOnly: false })}
              >
                {label(labels, "ai_patch_accept", "Accept")}
              </button>
              <button
                type="button"
                className="nb-button"
                disabled={!editable || !blockPatches.length}
                onClick={() => onAccept(patch, { blockOnly: true })}
              >
                {label(labels, "ai_patch_accept_block_only", "Accept block only")}
              </button>
              <button
                type="button"
                className="nb-button"
                disabled={!editable}
                onClick={() => onRegenerate(patch)}
              >
                {label(labels, "ai_patch_regenerate", "Regenerate")}
              </button>
              <button
                type="button"
                className="nb-button danger"
                disabled={!editable}
                onClick={() => onReject(patch)}
              >
                {label(labels, "ai_patch_reject", "Reject")}
              </button>
            </div>
          </article>
        );
      })}
    </section>
  );
}
