const VIDEO_DIRECTIVE_LINE_RE =
  /^::video\[(?<caption>[^\r\n\]]*)\]\((?<src>[^\r\n)]+)\)$/u;

const DIRECTIVE_LINE_RE =
  /^::[A-Za-z][\w-]*\[[^\r\n\]]*\]\([^\r\n]+\)$/u;

const AI_LOADING_COMMENT_RE =
  /^<!--\s*nblane:ai_loading(?:\s+(?<json>\{.*\}))?\s*-->$/u;

const VISUAL_BLOCK_COMMENT_RE =
  /^<!--\s*nblane:visual_block(?:\s+(?<json>\{.*\}))?\s*-->$/u;

const MARKDOWN_IMAGE_LINE_RE =
  /^!\[(?<alt>[^\]\r\n]*)\]\((?<src>[^\r\n)]+)\)$/u;

const ITALIC_CAPTION_LINE_RE =
  /^[_*](?<caption>[^_*].*?)[_*]$/u;

const DISPLAY_MATH_START_RE =
  /^\s*(?:\$\$|\\\[)\s*(?:$|[^\s])/u;

const COMPLEX_MATH_RE =
  /\\begin\{(?:align\*?|equation\*?|gather\*?|multline\*?|split|aligned|matrix|pmatrix|bmatrix|cases)\}/u;

const VISUAL_KIND_TO_ASSET_TYPE = {
  cover: "image",
  flowchart: "diagram",
  example: "image",
  video_edit: "video",
};

function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

function trimmedLines(value) {
  return cleanText(value)
    .split(/\r?\n/u)
    .map((line) => line.trim())
    .filter(Boolean);
}

export function containsRawMarkdownDirective(markdown) {
  return trimmedLines(markdown).some((line) => DIRECTIVE_LINE_RE.test(line));
}

export function isRawMarkdownDirective(snippet) {
  const lines = trimmedLines(snippet);
  return lines.length > 0 && lines.every((line) => DIRECTIVE_LINE_RE.test(line));
}

export function containsDisplayMathBlock(markdown) {
  const source = cleanText(markdown);
  if (COMPLEX_MATH_RE.test(source)) {
    return true;
  }
  return source.split(/\r?\n/u).some((line) => DISPLAY_MATH_START_RE.test(line));
}

function normalizeVisualKind(value) {
  const clean = cleanText(value).trim().toLowerCase();
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

function safeDirectiveLabel(value) {
  return cleanText(value).replace(/[\]\r\n]+/gu, " ").trim();
}

function safeDirectiveTarget(value) {
  return cleanText(value).replace(/[)\r\n]+/gu, "").trim();
}

function jsonPropsFromComment(line, regex) {
  const match = regex.exec(line.trim());
  if (!match) {
    return null;
  }
  const raw = cleanText(match.groups?.json || "").trim();
  if (!raw) {
    return {};
  }
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed)
      ? parsed
      : {};
  } catch (_err) {
    return {};
  }
}

export function parseVideoDirectiveLine(line) {
  const match = VIDEO_DIRECTIVE_LINE_RE.exec(line.trim());
  if (!match) {
    return null;
  }
  return {
    caption: cleanText(match.groups?.caption).trim(),
    src: cleanText(match.groups?.src).trim(),
  };
}

function parseMarkdownImageLine(line) {
  const match = MARKDOWN_IMAGE_LINE_RE.exec(line.trim());
  if (!match) {
    return null;
  }
  return {
    alt: cleanText(match.groups?.alt).trim(),
    src: cleanText(match.groups?.src).trim(),
  };
}

function parseItalicCaptionLine(line) {
  const match = ITALIC_CAPTION_LINE_RE.exec(line.trim());
  if (!match) {
    return "";
  }
  return cleanText(match.groups?.caption).trim();
}

function videoDirectiveBlock(line) {
  const parsed = parseVideoDirectiveLine(line);
  if (!parsed) {
    return null;
  }
  return {
    type: "video_block",
    props: {
      src: parsed.src,
      caption: parsed.caption,
      alt: parsed.caption,
      ai_generated: false,
      ai_source_id: "",
      ai_model: "",
      accepted: true,
      evidence_id: "",
    },
  };
}

function mathBlock(latex) {
  return {
    type: "math_block",
    props: {
      latex: cleanText(latex).trim(),
      ai_generated: false,
      ai_source_id: "",
      ai_model: "",
      accepted: true,
      evidence_id: "",
    },
  };
}

function aiLoadingBlock(props) {
  return {
    type: "ai_loading_block",
    props: {
      prompt: cleanText(props.prompt),
      mode: cleanText(props.mode || "write"),
      status: cleanText(props.status || "loading"),
      ai_source_id: cleanText(props.ai_source_id),
      ai_model: cleanText(props.ai_model),
      accepted: false,
      evidence_id: cleanText(props.evidence_id),
    },
  };
}

function visualBlock(props) {
  const visualKind = normalizeVisualKind(props.visual_kind || props.visualKind || props.asset_type);
  return {
    type: "visual_block",
    props: {
      asset_type: normalizeVisualAssetType(props.asset_type || props.kind, visualKind),
      visual_kind: visualKind,
      src: cleanText(props.src || props.url),
      prompt: cleanText(props.prompt),
      caption: cleanText(props.caption),
      alt: cleanText(props.alt),
      status: cleanText(props.status || "draft"),
      candidates: cleanText(props.candidates),
      ai_generated: props.ai_generated === true,
      ai_source_id: cleanText(props.ai_source_id),
      ai_model: cleanText(props.ai_model),
      accepted: props.accepted === true,
      evidence_id: cleanText(props.evidence_id),
    },
  };
}

function imageMarkdownBlock(lines, start) {
  const parsed = parseMarkdownImageLine(lines[start]);
  if (!parsed || !parsed.src) {
    return null;
  }

  let caption = "";
  let nextIndex = start + 1;
  let lookahead = start + 1;

  while (lookahead < lines.length && !lines[lookahead].trim()) {
    lookahead += 1;
  }

  if (lookahead > start + 1 && lookahead < lines.length) {
    caption = parseItalicCaptionLine(lines[lookahead]);
    if (caption) {
      nextIndex = lookahead + 1;
    }
  }

  return {
    block: visualBlock({
      asset_type: "image",
      src: parsed.src,
      alt: parsed.alt,
      caption,
      status: "accepted",
      accepted: true,
    }),
    nextIndex,
  };
}

function parseCommentBlock(line) {
  const loadingProps = jsonPropsFromComment(line, AI_LOADING_COMMENT_RE);
  if (loadingProps) {
    return aiLoadingBlock(loadingProps);
  }
  const visualProps = jsonPropsFromComment(line, VISUAL_BLOCK_COMMENT_RE);
  if (visualProps) {
    return visualBlock(visualProps);
  }
  return null;
}

function isFenceStart(line) {
  const match = /^([`~]{3,})/u.exec(line.trimStart());
  return match ? match[1] : "";
}

function closesFence(line, fence) {
  if (!fence) {
    return false;
  }
  return line.trimStart().startsWith(fence);
}

function oneLineMath(line, open, close) {
  const trimmed = line.trim();
  if (!trimmed.startsWith(open) || !trimmed.endsWith(close)) {
    return null;
  }
  const body = trimmed.slice(open.length, trimmed.length - close.length);
  if (!body.trim()) {
    return null;
  }
  return body;
}

function collectMathBlock(lines, start, open, close) {
  const current = lines[start];
  const sameLine = oneLineMath(current, open, close);
  if (sameLine !== null) {
    return { block: mathBlock(sameLine), nextIndex: start + 1 };
  }

  const first = current.trim();
  if (first !== open) {
    return null;
  }

  const body = [];
  for (let index = start + 1; index < lines.length; index += 1) {
    if (lines[index].trim() === close) {
      return {
        block: mathBlock(body.join("\n")),
        nextIndex: index + 1,
      };
    }
    body.push(lines[index]);
  }
  return null;
}

export function splitMarkdownSpecialBlocks(markdown) {
  const lines = cleanText(markdown).split(/\r?\n/u);
  const segments = [];
  let pending = [];
  let fence = "";

  function flushPending() {
    const value = pending.join("\n").trim();
    if (value) {
      segments.push({ kind: "markdown", value });
    }
    pending = [];
  }

  for (let index = 0; index < lines.length; ) {
    const line = lines[index];

    if (fence) {
      pending.push(line);
      if (closesFence(line, fence)) {
        fence = "";
      }
      index += 1;
      continue;
    }

    const nextFence = isFenceStart(line);
    if (nextFence) {
      fence = nextFence;
      pending.push(line);
      index += 1;
      continue;
    }

    const trimmed = line.trim();
    const video = videoDirectiveBlock(trimmed);
    if (video) {
      flushPending();
      segments.push({ kind: "block", block: video });
      index += 1;
      continue;
    }

    const commentBlock = parseCommentBlock(trimmed);
    if (commentBlock) {
      flushPending();
      segments.push({ kind: "block", block: commentBlock });
      index += 1;
      continue;
    }

    const markdownImage = imageMarkdownBlock(lines, index);
    if (markdownImage) {
      flushPending();
      segments.push({ kind: "block", block: markdownImage.block });
      index = markdownImage.nextIndex;
      continue;
    }

    const dollarMath = collectMathBlock(lines, index, "$$", "$$");
    if (dollarMath) {
      flushPending();
      segments.push({ kind: "block", block: dollarMath.block });
      index = dollarMath.nextIndex;
      continue;
    }

    const bracketMath = collectMathBlock(lines, index, "\\[", "\\]");
    if (bracketMath) {
      flushPending();
      segments.push({ kind: "block", block: bracketMath.block });
      index = bracketMath.nextIndex;
      continue;
    }

    pending.push(line);
    index += 1;
  }

  flushPending();
  return segments;
}

export function parseMarkdownToEditorBlocks(editor, markdown) {
  const segments = splitMarkdownSpecialBlocks(markdown);
  const blocks = [];
  for (const segment of segments) {
    if (segment.kind === "block") {
      blocks.push(segment.block);
      continue;
    }
    const parsed = editor.tryParseMarkdownToBlocks(segment.value);
    blocks.push(...parsed);
  }
  if (blocks.length) {
    return blocks;
  }
  return editor.tryParseMarkdownToBlocks(markdown || "");
}

function mathBlockToMarkdown(block) {
  const latex = cleanText(block.props?.latex).trim();
  if (!latex) {
    return "<!-- nblane:math_block -->";
  }
  return `$$\n${latex}\n$$`;
}

function videoBlockToMarkdown(block) {
  const src = safeDirectiveTarget(block.props?.src);
  const caption = safeDirectiveLabel(block.props?.caption || block.props?.alt);
  if (!src) {
    return "<!-- nblane:video_block -->";
  }
  return `::video[${caption}](${src})`;
}

function visualBlockToMarkdown(block) {
  const props = block.props || {};
  const src = safeDirectiveTarget(props.src);
  const caption = safeDirectiveLabel(props.caption);
  const alt = safeDirectiveLabel(props.alt || props.caption || "Visual");
  const visualKind = normalizeVisualKind(props.visual_kind);
  const assetType = normalizeVisualAssetType(props.asset_type, visualKind);
  const looksVideo = assetType.includes("video") || /\.(mp4|webm|ogg|mov|m4v)$/iu.test(src);

  if (visualKind || assetType === "diagram" || props.ai_generated === true) {
    return `<!-- nblane:visual_block ${JSON.stringify({
      asset_type: assetType,
      visual_kind: visualKind,
      src,
      prompt: cleanText(props.prompt),
      status: cleanText(props.status || "draft"),
      caption: cleanText(props.caption),
      alt: cleanText(props.alt),
      ai_generated: props.ai_generated === true,
      ai_source_id: cleanText(props.ai_source_id),
      ai_model: cleanText(props.ai_model),
      accepted: props.accepted === true,
      evidence_id: cleanText(props.evidence_id),
    })} -->`;
  }

  if (src && looksVideo) {
    return `::video[${caption || alt}](${src})`;
  }
  if (src) {
    const image = `![${alt}](${src})`;
    return caption ? `${image}\n\n_${caption}_` : image;
  }

  return `<!-- nblane:visual_block ${JSON.stringify({
    asset_type: assetType,
    visual_kind: visualKind,
    prompt: cleanText(props.prompt),
    status: cleanText(props.status || "draft"),
    caption: cleanText(props.caption),
    alt: cleanText(props.alt),
    candidates: cleanText(props.candidates),
    ai_generated: props.ai_generated === true,
    ai_source_id: cleanText(props.ai_source_id),
    ai_model: cleanText(props.ai_model),
    accepted: props.accepted === true,
    evidence_id: cleanText(props.evidence_id),
  })} -->`;
}

function aiLoadingBlockToMarkdown(block) {
  const props = block.props || {};
  return `<!-- nblane:ai_loading ${JSON.stringify({
    prompt: cleanText(props.prompt),
    mode: cleanText(props.mode || "write"),
    status: cleanText(props.status || "loading"),
  })} -->`;
}

export function blockToSpecialMarkdown(block) {
  switch (block?.type) {
    case "math_block":
      return mathBlockToMarkdown(block);
    case "video_block":
      return videoBlockToMarkdown(block);
    case "visual_block":
      return visualBlockToMarkdown(block);
    case "ai_loading_block":
      return aiLoadingBlockToMarkdown(block);
    default:
      return null;
  }
}

export function blocksToNblaneMarkdown(editor, blocks = editor.document) {
  const chunks = [];
  let pending = [];

  function flushPending() {
    if (!pending.length) {
      return;
    }
    const markdown = editor.blocksToMarkdownLossy(pending).trim();
    if (markdown) {
      chunks.push(markdown);
    }
    pending = [];
  }

  for (const block of blocks || []) {
    const special = blockToSpecialMarkdown(block);
    if (special === null) {
      pending.push(block);
      continue;
    }
    flushPending();
    if (special.trim()) {
      chunks.push(special.trim());
    }
  }

  flushPending();
  const markdown = chunks.join("\n\n").trimEnd();
  return markdown ? `${markdown}\n` : "";
}
