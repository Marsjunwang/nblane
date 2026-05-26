import assert from "node:assert/strict";
import test from "node:test";

import {
  allItemIds,
  expandableIds,
  explanationLinksFrom,
  filterItems,
  normalizePayload,
  paperMatchesQuery,
} from "./payload.js";

test("normalizePayload keeps stable defaults", () => {
  const payload = normalizePayload({
    active_view: "reading",
    active_label: "Reading",
    profile: "alice",
    query: "robot",
    sort_mode: "title",
    detail_id: "source:paper:a",
    focus: "artifacts",
    action: "run_extraction",
    return_to: "overview",
    return_url: "http://127.0.0.1:8503/Research",
    selected_paper_ids: ["a", "", "b"],
    papers: [{ id: "source:paper:a" }],
    detail: { id: "source:paper:a", title: "A" },
    metrics: { papers: 1 },
    diagnostics: ["ok", ""],
    sections: [{ id: "library" }],
  });
  assert.equal(payload.activeView, "reading");
  assert.equal(payload.activeNodeId, "");
  assert.equal(payload.activeLabel, "Reading");
  assert.equal(payload.profile, "alice");
  assert.equal(payload.query, "robot");
  assert.equal(payload.sortMode, "title");
  assert.equal(payload.detailId, "source:paper:a");
  assert.equal(payload.focus, "artifacts");
  assert.equal(payload.action, "run_extraction");
  assert.equal(payload.returnTo, "overview");
  assert.equal(payload.returnUrl, "http://127.0.0.1:8503/Research");
  assert.deepEqual(payload.selectedPaperIds, ["a", "b"]);
  assert.equal(payload.papers.length, 1);
  assert.equal(payload.detail.title, "A");
  assert.equal(payload.metrics.papers, 1);
  assert.deepEqual(payload.diagnostics, ["ok"]);
  assert.equal(payload.sections.length, 1);
});

test("tree helpers find expandable and filtered ids", () => {
  const items = [
    {
      id: "paper-node:vla",
      title: "VLA",
      children: [{ id: "paper-node:vla-memory", title: "Memory" }],
    },
    { id: "paper-node:diffusion", title: "Diffusion" },
  ];
  assert.deepEqual([...allItemIds(items)].sort(), [
    "paper-node:diffusion",
    "paper-node:vla",
    "paper-node:vla-memory",
  ]);
  assert.deepEqual([...expandableIds(items)], ["paper-node:vla"]);
  assert.deepEqual(filterItems(items, "memory").map((item) => item.id), ["paper-node:vla"]);
});

test("explanationLinksFrom normalizes aliases and caps links", () => {
  const links = explanationLinksFrom({
    reading_links: [
      { title: "Moonlight 论文解读", url: "https://example.com/moonlight", source: "The Moonlight", summary: "Plain-language guide." },
      { name: "alphaXiv discussion", link: "https://example.com/alphaxiv", site: "alphaXiv" },
      "https://doi.org/10.1000/demo",
      { title: "Missing URL" },
      { title: "Duplicate", url: "https://example.com/moonlight" },
      { title: "Four", url: "https://example.com/four" },
      { title: "Five", url: "https://example.com/five" },
      { title: "Six", url: "https://example.com/six" },
      { title: "Seven", url: "https://example.com/seven" },
    ],
  });

  assert.equal(links.length, 6);
  assert.deepEqual(links[0], {
    title: "Moonlight 论文解读",
    url: "https://example.com/moonlight",
    source: "The Moonlight",
    summary: "Plain-language guide.",
  });
  assert.equal(links[1].title, "alphaXiv discussion");
  assert.equal(links[2].title, "https://doi.org/10.1000/demo");
  assert.equal(links.some((link) => link.title === "Missing URL"), false);
  assert.equal(links.filter((link) => link.url === "https://example.com/moonlight").length, 1);

  assert.deepEqual(explanationLinksFrom({
    explainers: [{ name: "Explainer", link: "https://example.com/explainer", platform: "Blog" }],
  }), [
    {
      title: "Explainer",
      url: "https://example.com/explainer",
      source: "Blog",
      summary: "",
    },
  ]);
});

test("paperMatchesQuery includes explanation link text", () => {
  const paper = {
    title: "Restoring Linguistic Grounding",
    explanation_links: [
      {
        title: "Moonlight 论文解读",
        url: "https://example.com/moonlight",
        source: "The Moonlight",
        summary: "IGAR reading guide",
      },
    ],
  };

  assert.equal(paperMatchesQuery(paper, "moonlight"), true);
  assert.equal(paperMatchesQuery(paper, "igar"), true);
  assert.equal(paperMatchesQuery(paper, "not-present"), false);
});
