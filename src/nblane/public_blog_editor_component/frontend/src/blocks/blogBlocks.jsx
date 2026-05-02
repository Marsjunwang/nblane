import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  BlockNoteSchema,
  defaultBlockSpecs,
  defaultInlineContentSpecs,
  defaultStyleSpecs,
  insertOrUpdateBlock,
} from "@blocknote/core";
import { createReactBlockSpec } from "@blocknote/react";
import katex from "katex";
import "katex/dist/katex.min.css";
import { MermaidRenderer } from "./MermaidRenderer.jsx";

const AI_PROPS = {
  ai_generated: { default: false },
  ai_source_id: { default: "" },
  ai_model: { default: "" },
  accepted: { default: false },
  evidence_id: { default: "" },
};

const VISUAL_KIND_TO_ASSET_TYPE = {
  cover: "image",
  flowchart: "diagram",
  sequence: "diagram",
  state: "diagram",
  class: "diagram",
  mindmap: "diagram",
  example: "image",
  video_edit: "video",
};

function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

function normalizeVisualKind(value) {
  const clean = cleanText(value).trim().toLowerCase();
  if (clean === "diagram" || clean === "mermaid") {
    return "flowchart";
  }
  return Object.prototype.hasOwnProperty.call(VISUAL_KIND_TO_ASSET_TYPE, clean)
    ? clean
    : "";
}

function normalizeVisualAssetType(value, visualKind = "") {
  const clean = cleanText(value).trim().toLowerCase();
  const kind = normalizeVisualKind(visualKind || clean);
  if (kind) {
    return VISUAL_KIND_TO_ASSET_TYPE[kind];
  }
  return ["image", "video", "diagram"].includes(clean) ? clean : "image";
}

function updateBlockProps(editor, block, props) {
  editor.updateBlock(block, {
    props: {
      ...block.props,
      ...props,
    },
  });
}

function emitInlineCandidateAction(action, block) {
  if (typeof window === "undefined") {
    return;
  }
  const props = block?.props || {};
  window.dispatchEvent(
    new CustomEvent("nblane:ai-candidate-action", {
      detail: {
        action,
        block_id: cleanText(block?.id),
        mode: cleanText(props.mode),
        status: cleanText(props.status),
        patch_id: cleanText(props.patch_id),
        ai_source_id: cleanText(props.ai_source_id),
        ai_model: cleanText(props.ai_model),
        prompt: cleanText(props.prompt),
        summary: cleanText(props.summary),
        preview_src: cleanText(props.preview_src),
        candidate_path: cleanText(props.candidate_path),
        evidence_id: cleanText(props.evidence_id),
      },
    }),
  );
}

function FieldText({ label, value, onChange, readOnly = false, multiline = false }) {
  const [draft, setDraft] = useState(cleanText(value));
  const draftRef = useRef(cleanText(value));

  useEffect(() => {
    const next = cleanText(value);
    draftRef.current = next;
    setDraft(next);
  }, [value]);

  const Input = multiline ? "textarea" : "input";
  return (
    <label className="nb-block-field">
      <span>{label}</span>
      <Input
        value={draft}
        readOnly={readOnly}
        rows={multiline ? 3 : undefined}
        onChange={(event) => {
          const next = event.target.value;
          draftRef.current = next;
          setDraft(next);
          onChange(next);
        }}
        onBlur={() => onChange(draftRef.current)}
        onKeyDown={(event) => event.stopPropagation()}
        onMouseDown={(event) => event.stopPropagation()}
      />
    </label>
  );
}

function BlockDetails({ label, defaultOpen = false, children }) {
  return (
    <details
      className="nb-block-details"
      defaultOpen={defaultOpen}
      onKeyDown={(event) => event.stopPropagation()}
      onMouseDown={(event) => event.stopPropagation()}
    >
      <summary>{label}</summary>
      <div className="nb-block-details-body">{children}</div>
    </details>
  );
}

function useResolvedMediaSrc(src, editor) {
  const cleanSrc = cleanText(src).trim();
  const [resolvedSrc, setResolvedSrc] = useState(cleanSrc);

  useEffect(() => {
    let cancelled = false;
    setResolvedSrc(cleanSrc);
    if (!cleanSrc || typeof editor?.resolveFileUrl !== "function") {
      return () => {
        cancelled = true;
      };
    }
    Promise.resolve(editor.resolveFileUrl(cleanSrc))
      .then((next) => {
        if (!cancelled && next) {
          setResolvedSrc(cleanText(next));
        }
      })
      .catch(() => {
        if (!cancelled) {
          setResolvedSrc(cleanSrc);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [cleanSrc, editor]);

  return resolvedSrc;
}

function KatexPreview({ latex }) {
  const rendered = useMemo(() => {
    const source = cleanText(latex).trim();
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
  }, [latex]);

  if (rendered.error) {
    return <pre className="nb-math-fallback">{cleanText(latex)}</pre>;
  }
  if (!rendered.html) {
    return <div className="nb-block-empty">LaTeX</div>;
  }
  return (
    <div
      className="nb-math-preview"
      dangerouslySetInnerHTML={{ __html: rendered.html }}
    />
  );
}

function MathBlock({ block, editor }) {
  const readOnly = editor.isEditable === false;
  const latex = cleanText(block.props.latex);
  return (
    <div
      className="nb-custom-block nb-math-block"
      contentEditable={false}
      data-nblane-block="math_block"
    >
      <div className="nb-block-header">
        <strong>Formula</strong>
        {block.props.ai_generated ? <span>ai_generated</span> : null}
      </div>
      <KatexPreview latex={latex} />
      <BlockDetails label="Edit LaTeX" defaultOpen={!latex}>
        <FieldText
          label="LaTeX"
          value={latex}
          readOnly={readOnly}
          multiline
          onChange={(next) => updateBlockProps(editor, block, { latex: next })}
        />
      </BlockDetails>
    </div>
  );
}

function VideoBlock({ block, editor }) {
  const readOnly = editor.isEditable === false;
  const src = cleanText(block.props.src).trim();
  const caption = cleanText(block.props.caption);
  const alt = cleanText(block.props.alt || caption || "Video");
  return (
    <div
      className="nb-custom-block nb-video-block"
      contentEditable={false}
      data-nblane-block="video_block"
    >
      <div className="nb-block-header">
        <strong>Video</strong>
        {block.props.accepted ? <span>accepted</span> : null}
      </div>
      <VisualMedia
        src={src}
        assetType="video"
        alt={alt}
        editor={editor}
        emptyLabel="Video URL"
      />
      {caption ? <div className="nb-block-caption">{caption}</div> : null}
      <BlockDetails label="Edit metadata" defaultOpen={!src}>
        <div className="nb-block-grid">
          <FieldText
            label="Source"
            value={src}
            readOnly={readOnly}
            onChange={(next) => updateBlockProps(editor, block, { src: next })}
          />
          <FieldText
            label="Caption"
            value={caption}
            readOnly={readOnly}
            onChange={(next) => updateBlockProps(editor, block, { caption: next })}
          />
          <FieldText
            label="Alt"
            value={alt}
            readOnly={readOnly}
            onChange={(next) => updateBlockProps(editor, block, { alt: next })}
          />
        </div>
      </BlockDetails>
    </div>
  );
}

function VisualMedia({ src, assetType, alt, editor = null, emptyLabel = "Visual" }) {
  const cleanSrc = cleanText(src).trim();
  const resolvedSrc = useResolvedMediaSrc(cleanSrc, editor);
  const cleanType = cleanText(assetType).toLowerCase();
  const isVideo =
    cleanType.includes("video") || /\.(mp4|webm|ogg|mov|m4v)$/iu.test(cleanSrc);
  if (!cleanSrc) {
    return <div className="nb-block-empty">{emptyLabel}</div>;
  }
  if (isVideo) {
    return (
      <video className="nb-block-video" src={resolvedSrc} controls preload="metadata" />
    );
  }
  return <img className="nb-block-image" src={resolvedSrc} alt={alt || "Visual"} />;
}

function VisualBlock({ block, editor }) {
  const readOnly = editor.isEditable === false;
  const props = block.props;
  const src = cleanText(props.src);
  const previewSrc = cleanText(props.preview_src);
  const caption = cleanText(props.caption);
  const alt = cleanText(props.alt || caption || "Visual");
  const status = cleanText(props.status || "draft");
  const assetType = normalizeVisualAssetType(props.asset_type, props.visual_kind);
  const visualKind = normalizeVisualKind(props.visual_kind);
  const mermaid = cleanText(props.mermaid);
  const candidatePath = cleanText(props.candidate_path);
  const shouldRenderMermaid = Boolean(mermaid.trim()) || (assetType === "diagram" && !src);
  const mermaidSource =
    mermaid.trim() || (assetType === "diagram" ? cleanText(props.prompt).trim() : "");
  return (
    <div
      className="nb-custom-block nb-visual-block"
      contentEditable={false}
      data-nblane-block="visual_block"
    >
      <div className="nb-block-header">
        <strong>Visual</strong>
        {visualKind ? <span>{visualKind}</span> : null}
        <span>{status || "draft"}</span>
      </div>
      {shouldRenderMermaid ? (
        <MermaidRenderer source={mermaidSource} />
      ) : (
        <VisualMedia src={src || previewSrc} assetType={assetType} alt={alt} editor={editor} />
      )}
      {caption ? <div className="nb-block-caption">{caption}</div> : null}
      <BlockDetails label="Edit metadata" defaultOpen={!src && !mermaidSource}>
        <div className="nb-block-grid">
          <label className="nb-block-field">
            <span>Type</span>
            <select
              value={assetType}
              disabled={readOnly}
              onChange={(event) =>
                updateBlockProps(editor, block, { asset_type: event.target.value })
              }
              onKeyDown={(event) => event.stopPropagation()}
              onMouseDown={(event) => event.stopPropagation()}
            >
              <option value="image">image</option>
              <option value="video">video</option>
              <option value="diagram">diagram</option>
            </select>
          </label>
          <label className="nb-block-field">
            <span>Visual kind</span>
            <select
              value={visualKind}
              disabled={readOnly}
              onChange={(event) => {
                const nextKind = normalizeVisualKind(event.target.value);
                updateBlockProps(editor, block, {
                  visual_kind: nextKind,
                  asset_type: normalizeVisualAssetType(props.asset_type, nextKind),
                });
              }}
              onKeyDown={(event) => event.stopPropagation()}
              onMouseDown={(event) => event.stopPropagation()}
            >
              <option value="">none</option>
              <option value="cover">cover</option>
              <option value="flowchart">flowchart</option>
              <option value="sequence">sequence</option>
              <option value="state">state</option>
              <option value="class">class</option>
              <option value="mindmap">mindmap</option>
              <option value="example">example</option>
              <option value="video_edit">video_edit</option>
            </select>
          </label>
          <FieldText
            label="Source"
            value={src}
            readOnly={readOnly}
            onChange={(next) => updateBlockProps(editor, block, { src: next })}
          />
          {candidatePath ? (
            <FieldText
              label="Candidate"
              value={candidatePath}
              readOnly
              onChange={() => {}}
            />
          ) : null}
          <FieldText
            label="Caption"
            value={caption}
            readOnly={readOnly}
            onChange={(next) => updateBlockProps(editor, block, { caption: next })}
          />
          <FieldText
            label="Prompt"
            value={props.prompt}
            readOnly={readOnly}
            multiline
            onChange={(next) => updateBlockProps(editor, block, { prompt: next })}
          />
          {shouldRenderMermaid ? (
            <FieldText
              label="Mermaid"
              value={mermaid}
              readOnly={readOnly}
              multiline
              onChange={(next) => updateBlockProps(editor, block, { mermaid: next })}
            />
          ) : null}
        </div>
      </BlockDetails>
    </div>
  );
}

function AiLoadingBlock({ block, editor }) {
  const readOnly = editor.isEditable === false;
  const prompt = cleanText(block.props.prompt);
  const status = cleanText(block.props.status || "loading");
  const mode = cleanText(block.props.mode || "write");
  const previewSrc = cleanText(block.props.preview_src);
  const summary = cleanText(block.props.summary || prompt);
  const isFormula = mode === "formula";
  const isVisual = mode === "visual" || mode === "diagram" || mode === "video";
  const isDiagram = mode === "diagram";
  const visualLabel =
    mode === "diagram" ? "Generating diagram..." : mode === "video" ? "Generating video..." : "Generating visual...";
  const isCandidate = status === "candidate";
  return (
    <div
      className={`nb-custom-block nb-ai-loading-block nb-ai-loading-${mode} ${
        isCandidate ? "is-candidate" : ""
      }`}
      contentEditable={false}
      data-nblane-block="ai_loading_block"
    >
      <div className="nb-block-header">
        <strong>AI</strong>
        <span>{status}</span>
      </div>
      {isCandidate ? (
        <div
          className={`nb-ai-candidate-placeholder ${
            previewSrc ? "" : "is-no-preview"
          }`}
        >
          {previewSrc ? (
            <img className="nb-ai-candidate-image" src={previewSrc} alt="AI candidate" />
          ) : null}
          <div>
            <strong>Candidate ready</strong>
            {summary && !isDiagram ? <p>{summary.slice(0, 240)}</p> : null}
          </div>
          {isDiagram && summary ? (
            <div className="nb-ai-candidate-diagram">
              <MermaidRenderer source={summary} />
            </div>
          ) : null}
          <div className="nb-ai-candidate-actions">
            <button
              type="button"
              className="nb-button primary"
              disabled={readOnly}
              onClick={(event) => {
                event.stopPropagation();
                emitInlineCandidateAction("accept", block);
              }}
            >
              Accept
            </button>
            <button
              type="button"
              className="nb-button"
              disabled={readOnly}
              onClick={(event) => {
                event.stopPropagation();
                emitInlineCandidateAction("review", block);
              }}
            >
              Review
            </button>
            <button
              type="button"
              className="nb-button danger"
              disabled={readOnly}
              onClick={(event) => {
                event.stopPropagation();
                emitInlineCandidateAction("reject", block);
              }}
            >
              Reject
            </button>
          </div>
        </div>
      ) : (
        <div className="nb-loading-row">
          <span className="nb-loading-dot" />
          <span>{mode}</span>
        </div>
      )}
      {!isCandidate && isFormula ? (
        <div className="nb-ai-loading-formula">
          <KatexPreview latex={prompt} />
        </div>
      ) : !isCandidate && isVisual ? (
        <div className="nb-ai-loading-visual" aria-label={visualLabel}>
          <div className="nb-ai-loading-progress">
            <span />
          </div>
          <p>{visualLabel}</p>
        </div>
      ) : !isCandidate && prompt ? (
        <pre className="nb-ai-loading-preview">{prompt}</pre>
      ) : null}
      {!isCandidate && !isFormula && !isVisual ? (
        <FieldText
          label="Prompt"
          value={prompt}
          readOnly={readOnly}
          multiline
          onChange={(next) => updateBlockProps(editor, block, { prompt: next })}
        />
      ) : null}
    </div>
  );
}

function ExternalMath({ block }) {
  return (
    <div data-nblane-block="math_block" data-latex={cleanText(block.props.latex)}>
      {cleanText(block.props.latex)}
    </div>
  );
}

function ExternalVideo({ block }) {
  const src = cleanText(block.props.src);
  const caption = cleanText(block.props.caption);
  return (
    <figure data-nblane-block="video_block" data-src={src} data-caption={caption}>
      <video src={src} controls />
      {caption ? <figcaption>{caption}</figcaption> : null}
    </figure>
  );
}

function ExternalVisual({ block }) {
  const props = block.props || {};
  const assetType = normalizeVisualAssetType(props.asset_type, props.visual_kind);
  const src = cleanText(props.src);
  const mermaid = cleanText(props.mermaid);
  const shouldRenderMermaid = Boolean(mermaid.trim()) || (assetType === "diagram" && !src);
  return (
    <figure
      data-nblane-block="visual_block"
      data-asset-type={cleanText(assetType)}
      data-visual-kind={cleanText(props.visual_kind)}
      data-src={src}
      data-candidate-path={cleanText(props.candidate_path)}
      data-preview-src={cleanText(props.preview_src)}
      data-mermaid={mermaid}
      data-prompt={cleanText(props.prompt)}
      data-caption={cleanText(props.caption)}
      data-alt={cleanText(props.alt)}
    >
      {shouldRenderMermaid ? (
        <pre>{mermaid || cleanText(props.prompt)}</pre>
      ) : (
        <VisualMedia
          src={props.src}
          assetType={props.asset_type}
          alt={cleanText(props.alt || props.caption)}
        />
      )}
      {props.caption ? <figcaption>{cleanText(props.caption)}</figcaption> : null}
    </figure>
  );
}

function ExternalAiLoading({ block }) {
  return (
    <div
      data-nblane-block="ai_loading_block"
      data-prompt={cleanText(block.props.prompt)}
      data-mode={cleanText(block.props.mode)}
      data-status={cleanText(block.props.status)}
      data-ai-source-id={cleanText(block.props.ai_source_id)}
      data-ai-model={cleanText(block.props.ai_model)}
      data-patch-id={cleanText(block.props.patch_id)}
      data-preview-src={cleanText(block.props.preview_src)}
      data-summary={cleanText(block.props.summary)}
      data-candidate-path={cleanText(block.props.candidate_path)}
      data-evidence-id={cleanText(block.props.evidence_id)}
    />
  );
}

function parseDataBlock(element, type) {
  if (element.getAttribute("data-nblane-block") !== type) {
    return undefined;
  }
  const dataset = element.dataset || {};
  if (type === "math_block") {
    return { latex: cleanText(dataset.latex || element.textContent) };
  }
  if (type === "video_block") {
    return {
      src: cleanText(dataset.src),
      caption: cleanText(dataset.caption),
      alt: cleanText(dataset.caption),
    };
  }
  if (type === "visual_block") {
    const visualKind = normalizeVisualKind(dataset.visualKind || dataset.assetType);
    return {
      asset_type: normalizeVisualAssetType(dataset.assetType || "image", visualKind),
      visual_kind: visualKind,
      src: cleanText(dataset.src),
      candidate_path: cleanText(dataset.candidatePath),
      preview_src: cleanText(dataset.previewSrc),
      mermaid: cleanText(dataset.mermaid),
      prompt: cleanText(dataset.prompt),
      caption: cleanText(dataset.caption),
      alt: cleanText(dataset.alt),
    };
  }
  if (type === "ai_loading_block") {
    return {
      prompt: cleanText(dataset.prompt),
      mode: cleanText(dataset.mode || "write"),
      status: cleanText(dataset.status || "loading"),
      ai_source_id: cleanText(dataset.aiSourceId),
      ai_model: cleanText(dataset.aiModel),
      patch_id: cleanText(dataset.patchId),
      preview_src: cleanText(dataset.previewSrc),
      summary: cleanText(dataset.summary),
      candidate_path: cleanText(dataset.candidatePath),
      evidence_id: cleanText(dataset.evidenceId),
    };
  }
  return undefined;
}

const MathBlockSpec = createReactBlockSpec(
  {
    type: "math_block",
    propSchema: {
      latex: { default: "" },
      ...AI_PROPS,
    },
    content: "none",
  },
  {
    render: MathBlock,
    toExternalHTML: ExternalMath,
    parse: (element) => parseDataBlock(element, "math_block"),
  },
);

const VideoBlockSpec = createReactBlockSpec(
  {
    type: "video_block",
    propSchema: {
      src: { default: "" },
      caption: { default: "" },
      alt: { default: "" },
      ...AI_PROPS,
    },
    content: "none",
  },
  {
    render: VideoBlock,
    toExternalHTML: ExternalVideo,
    parse: (element) => parseDataBlock(element, "video_block"),
  },
);

const VisualBlockSpec = createReactBlockSpec(
  {
    type: "visual_block",
    propSchema: {
      asset_type: { default: "image", values: ["image", "video", "diagram"] },
      visual_kind: {
        default: "",
        values: [
          "",
          "cover",
          "flowchart",
          "sequence",
          "state",
          "class",
          "mindmap",
          "example",
          "video_edit",
        ],
      },
      src: { default: "" },
      candidate_path: { default: "" },
      preview_src: { default: "" },
      mermaid: { default: "" },
      prompt: { default: "" },
      caption: { default: "" },
      alt: { default: "" },
      status: {
        default: "draft",
        values: ["draft", "loading", "candidate", "accepted", "failed"],
      },
      candidates: { default: "" },
      ...AI_PROPS,
    },
    content: "none",
  },
  {
    render: VisualBlock,
    toExternalHTML: ExternalVisual,
    parse: (element) => parseDataBlock(element, "visual_block"),
  },
);

const AiLoadingBlockSpec = createReactBlockSpec(
  {
    type: "ai_loading_block",
    propSchema: {
      prompt: { default: "" },
      mode: {
        default: "write",
        values: ["write", "rewrite", "formula", "visual", "diagram", "video"],
      },
      status: {
        default: "loading",
        values: ["loading", "failed", "done", "candidate"],
      },
      ai_source_id: { default: "" },
      ai_model: { default: "" },
      patch_id: { default: "" },
      preview_src: { default: "" },
      summary: { default: "" },
      candidate_path: { default: "" },
      accepted: { default: false },
      evidence_id: { default: "" },
    },
    content: "none",
  },
  {
    render: AiLoadingBlock,
    toExternalHTML: ExternalAiLoading,
    parse: (element) => parseDataBlock(element, "ai_loading_block"),
  },
);

export const blogBlockSpecs = {
  ...defaultBlockSpecs,
  math_block: MathBlockSpec(),
  video_block: VideoBlockSpec(),
  visual_block: VisualBlockSpec(),
  ai_loading_block: AiLoadingBlockSpec(),
};

export const blogSchema = BlockNoteSchema.create({
  blockSpecs: blogBlockSpecs,
  inlineContentSpecs: defaultInlineContentSpecs,
  styleSpecs: defaultStyleSpecs,
});

function slashLabel(labels, key, fallback) {
  return cleanText(labels?.[key] || fallback);
}

function icon(text) {
  return <span className="nb-slash-icon">{text}</span>;
}

export function getBlogSlashMenuItems(editor, labels = {}) {
  return [
    {
      title: slashLabel(labels, "formula_block", "Formula"),
      subtext: slashLabel(labels, "formula_block_help", "LaTeX display block"),
      aliases: ["math", "latex", "equation", "formula"],
      group: "AI blocks",
      icon: icon("fx"),
      onItemClick: () =>
        insertOrUpdateBlock(editor, {
          type: "math_block",
          props: { latex: "" },
        }),
    },
    {
      title: slashLabel(labels, "video_block", "Video"),
      subtext: slashLabel(labels, "video_block_help", "Public-site video"),
      aliases: ["video", "movie", "media"],
      group: "AI blocks",
      icon: icon("vid"),
      onItemClick: () =>
        insertOrUpdateBlock(editor, {
          type: "video_block",
          props: { src: "", caption: "", accepted: true },
        }),
    },
    {
      title: slashLabel(labels, "visual_block", "Visual"),
      subtext: slashLabel(labels, "visual_block_help", "Image or video candidate"),
      aliases: ["visual", "image", "ai image"],
      group: "AI blocks",
      icon: icon("vis"),
      onItemClick: () =>
        insertOrUpdateBlock(editor, {
          type: "visual_block",
          props: { asset_type: "image", status: "draft" },
        }),
    },
    {
      title: slashLabel(labels, "ai_loading_block", "AI placeholder"),
      subtext: slashLabel(labels, "ai_loading_block_help", "Generated content"),
      aliases: ["ai", "loading", "write"],
      group: "AI blocks",
      icon: icon("ai"),
      onItemClick: () =>
        insertOrUpdateBlock(editor, {
          type: "ai_loading_block",
          props: { mode: "write", status: "loading" },
        }),
    },
  ];
}
