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

const AI_PROPS = {
  ai_generated: { default: false },
  ai_source_id: { default: "" },
  ai_model: { default: "" },
  accepted: { default: false },
  evidence_id: { default: "" },
};

function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

function updateBlockProps(editor, block, props) {
  editor.updateBlock(block, {
    props: {
      ...props,
    },
  });
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
        {block.props.ai_generated ? <span>AI</span> : null}
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
  const caption = cleanText(props.caption);
  const alt = cleanText(props.alt || caption || "Visual");
  const status = cleanText(props.status || "draft");
  return (
    <div
      className="nb-custom-block nb-visual-block"
      contentEditable={false}
      data-nblane-block="visual_block"
    >
      <div className="nb-block-header">
        <strong>Visual</strong>
        <span>{status || "draft"}</span>
      </div>
      <VisualMedia src={src} assetType={props.asset_type} alt={alt} editor={editor} />
      {caption ? <div className="nb-block-caption">{caption}</div> : null}
      <BlockDetails label="Edit metadata" defaultOpen={!src}>
        <div className="nb-block-grid">
          <label className="nb-block-field">
            <span>Type</span>
            <select
              value={cleanText(props.asset_type || "image")}
              disabled={readOnly}
              onChange={(event) =>
                updateBlockProps(editor, block, { asset_type: event.target.value })
              }
              onKeyDown={(event) => event.stopPropagation()}
              onMouseDown={(event) => event.stopPropagation()}
            >
              <option value="image">image</option>
              <option value="video">video</option>
            </select>
          </label>
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
            label="Prompt"
            value={props.prompt}
            readOnly={readOnly}
            multiline
            onChange={(next) => updateBlockProps(editor, block, { prompt: next })}
          />
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
  return (
    <div
      className="nb-custom-block nb-ai-loading-block"
      contentEditable={false}
      data-nblane-block="ai_loading_block"
    >
      <div className="nb-block-header">
        <strong>AI</strong>
        <span>{status}</span>
      </div>
      <div className="nb-loading-row">
        <span className="nb-loading-dot" />
        <span>{mode}</span>
      </div>
      <FieldText
        label="Prompt"
        value={prompt}
        readOnly={readOnly}
        multiline
        onChange={(next) => updateBlockProps(editor, block, { prompt: next })}
      />
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
  return (
    <figure
      data-nblane-block="visual_block"
      data-asset-type={cleanText(props.asset_type)}
      data-src={cleanText(props.src)}
      data-prompt={cleanText(props.prompt)}
      data-caption={cleanText(props.caption)}
      data-alt={cleanText(props.alt)}
    >
      <VisualMedia
        src={props.src}
        assetType={props.asset_type}
        alt={cleanText(props.alt || props.caption)}
      />
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
    return {
      asset_type: cleanText(dataset.assetType || "image"),
      src: cleanText(dataset.src),
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
      asset_type: { default: "image", values: ["image", "video"] },
      src: { default: "" },
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
        values: ["write", "rewrite", "formula", "visual", "video"],
      },
      status: {
        default: "loading",
        values: ["loading", "failed", "done"],
      },
      ai_source_id: { default: "" },
      ai_model: { default: "" },
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
