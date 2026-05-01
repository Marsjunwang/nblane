import assert from "node:assert/strict";
import test from "node:test";

import {
  blockToSpecialMarkdown,
  blocksToNblaneMarkdown,
  containsRawMarkdownDirective,
  parseVideoDirectiveLine,
  splitMarkdownSpecialBlocks,
} from "./markdown.js";

test("parses video directives as custom blocks", () => {
  assert.deepEqual(parseVideoDirectiveLine("::video[Clip](media/blog/post/clip.mp4)"), {
    caption: "Clip",
    src: "media/blog/post/clip.mp4",
  });

  const segments = splitMarkdownSpecialBlocks(
    "Intro.\n\n::video[Clip](media/blog/post/clip.mp4)\n\nOutro.",
  );

  assert.equal(segments.length, 3);
  assert.equal(segments[0].kind, "markdown");
  assert.equal(segments[1].block.type, "video_block");
  assert.equal(segments[1].block.props.src, "media/blog/post/clip.mp4");
  assert.equal(segments[2].value, "Outro.");
});

test("does not parse directives inside fenced code", () => {
  const segments = splitMarkdownSpecialBlocks(
    "```md\n::video[Clip](secret.mp4)\n```\n\nAfter.",
  );

  assert.equal(segments.length, 1);
  assert.equal(segments[0].kind, "markdown");
  assert.match(segments[0].value, /::video\[Clip\]/u);
});

test("parses display math as math blocks", () => {
  const segments = splitMarkdownSpecialBlocks(
    "Before.\n\n$$\nJ(\\theta)=\\sum_t r_t\n$$\n\nAfter.",
  );

  assert.equal(segments.length, 3);
  assert.equal(segments[1].block.type, "math_block");
  assert.equal(segments[1].block.props.latex, "J(\\theta)=\\sum_t r_t");
});

test("parses standalone markdown images as visual blocks", () => {
  const segments = splitMarkdownSpecialBlocks(
    "Intro.\n\n![Chart](media/blog/post/chart.png)\n\n_Flow_\n\nOutro.",
  );

  assert.equal(segments.length, 3);
  assert.equal(segments[1].block.type, "visual_block");
  assert.equal(segments[1].block.props.asset_type, "image");
  assert.equal(segments[1].block.props.src, "media/blog/post/chart.png");
  assert.equal(segments[1].block.props.alt, "Chart");
  assert.equal(segments[1].block.props.caption, "Flow");
  assert.equal(segments[1].block.props.status, "accepted");
  assert.equal(segments[1].block.props.accepted, true);
});

test("does not parse markdown images inside fenced code", () => {
  const segments = splitMarkdownSpecialBlocks(
    "```md\n![Chart](media/blog/post/chart.png)\n```\n\nAfter.",
  );

  assert.equal(segments.length, 1);
  assert.equal(segments[0].kind, "markdown");
  assert.match(segments[0].value, /!\[Chart\]/u);
});

test("serializes custom blocks to public-site markdown", () => {
  assert.equal(
    blockToSpecialMarkdown({
      type: "math_block",
      props: { latex: "E=mc^2" },
    }),
    "$$\nE=mc^2\n$$",
  );

  assert.equal(
    blockToSpecialMarkdown({
      type: "video_block",
      props: { src: "media/blog/post/clip.mp4", caption: "Clip" },
    }),
    "::video[Clip](media/blog/post/clip.mp4)",
  );

  assert.equal(
    blockToSpecialMarkdown({
      type: "visual_block",
      props: {
        asset_type: "image",
        src: "media/blog/post/chart.png",
        alt: "Chart",
        caption: "Flow",
      },
    }),
    "![Chart](media/blog/post/chart.png)\n\n_Flow_",
  );
});

test("interleaves native BlockNote markdown with custom block markdown", () => {
  const editor = {
    blocksToMarkdownLossy(blocks) {
      return blocks.map((block) => block.content).join("\n\n");
    },
  };

  const markdown = blocksToNblaneMarkdown(editor, [
    { type: "paragraph", content: "Intro." },
    { type: "math_block", props: { latex: "x^2" } },
    { type: "paragraph", content: "Done." },
  ]);

  assert.equal(markdown, "Intro.\n\n$$\nx^2\n$$\n\nDone.\n");
});

test("detects raw standalone directives", () => {
  assert.equal(containsRawMarkdownDirective("Text\n\n::video[](a.mp4)"), true);
  assert.equal(containsRawMarkdownDirective("Text ::video[](a.mp4)"), false);
});
