import assert from "node:assert/strict";
import test from "node:test";

import {
  allItemIds,
  expandableIds,
  filterItems,
  normalizePayload,
} from "./payload.js";

test("normalizePayload keeps stable defaults", () => {
  const payload = normalizePayload({
    active_view: "reading",
    active_label: "Reading",
    profile: "alice",
    query: "robot",
    sort_mode: "title",
    detail_id: "source:paper:a",
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
