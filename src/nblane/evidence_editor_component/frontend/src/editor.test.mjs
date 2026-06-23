import test from "node:test";
import assert from "node:assert/strict";

import { filterRows, matchesFilters, matchesSearch, rowWarnings } from "./filters.js";
import { renderMarkdown, escapeHtml } from "./schema.js";
import {
  saveEvidenceEvent,
  addEvidenceEvent,
  linkProjectEvent,
  createProjectFromEvidenceEvent,
  makeEvent,
} from "./events.js";

const ROWS = [
  {
    id: "ev1",
    title: "GAC far-range detection",
    summary: "+15 AP",
    origin: "resume_parse",
    type: "project",
    review_status: "reviewed",
    language: "en",
    has_project: false,
    has_original_content: true,
    needs_migration: false,
    public_readiness: "private",
  },
  {
    id: "ev2",
    title: "Latency tuning",
    summary: "cut to 20fps",
    origin: "kanban_task",
    type: "practice",
    review_status: "needs_review",
    language: "en",
    has_project: true,
    has_original_content: true,
    needs_migration: false,
    public_readiness: "private",
  },
  {
    id: "ev3",
    title: "Legacy note",
    summary: "",
    origin: "",
    type: "learning",
    review_status: "",
    language: "",
    has_project: false,
    has_original_content: false,
    needs_migration: true,
    public_readiness: "public_ready",
  },
];

test("matchesSearch matches title and summary", () => {
  assert.equal(matchesSearch(ROWS[0], "gac"), true);
  assert.equal(matchesSearch(ROWS[0], "20fps"), false);
  assert.equal(matchesSearch(ROWS[1], "20fps"), true);
  assert.equal(matchesSearch(ROWS[0], ""), true);
});

test("matchesFilters: origin", () => {
  assert.equal(matchesFilters(ROWS[0], { origin: "resume_parse" }), true);
  assert.equal(matchesFilters(ROWS[1], { origin: "resume_parse" }), false);
});

test("matchesFilters: review_status and type", () => {
  assert.equal(matchesFilters(ROWS[1], { review_status: "needs_review" }), true);
  assert.equal(matchesFilters(ROWS[0], { type: "project" }), true);
  assert.equal(matchesFilters(ROWS[0], { type: "paper" }), false);
});

test("matchesFilters: hasProject and needsMigration toggles", () => {
  assert.equal(matchesFilters(ROWS[1], { hasProject: true }), true);
  assert.equal(matchesFilters(ROWS[0], { hasProject: true }), false);
  assert.equal(matchesFilters(ROWS[2], { needsMigration: true }), true);
  assert.equal(matchesFilters(ROWS[0], { needsMigration: true }), false);
});

test("filterRows combines search + filters", () => {
  const out = filterRows(ROWS, "", { origin: "resume_parse" });
  assert.deepEqual(out.map((r) => r.id), ["ev1"]);
  const out2 = filterRows(ROWS, "legacy", {});
  assert.deepEqual(out2.map((r) => r.id), ["ev3"]);
});

test("rowWarnings: resume orphan + missing raw + privacy", () => {
  assert.deepEqual(rowWarnings(ROWS[0]), [
    "ee_project_provenance_reminder",
    "ee_missing_date",
  ]);
  const w3 = rowWarnings(ROWS[2]);
  assert.ok(w3.includes("ee_original_content_missing"));
  // ev3 has public_ready readiness but no raw -> privacy warning not added
  // (privacy warning requires has_original_content).
  assert.ok(!w3.includes("ee_privacy_original_content_warning"));
});

test("rowWarnings: privacy fires when public + has raw", () => {
  const row = {
    origin: "manual_daily",
    has_project: true,
    has_original_content: true,
    public_readiness: "public_ready",
  };
  assert.ok(rowWarnings(row).includes("ee_privacy_original_content_warning"));
});

test("event factory shape", () => {
  const ev = saveEvidenceEvent("ev1", { title: "X" });
  assert.equal(ev.action, "save_evidence");
  assert.equal(ev.payload.id, "ev1");
  assert.deepEqual(ev.payload.fields, { title: "X" });
  assert.ok(ev.event_id);

  const add = addEvidenceEvent({ origin: "manual_daily" });
  assert.equal(add.action, "add_evidence");
  assert.equal(add.payload.fields.origin, "manual_daily");

  const link = linkProjectEvent("ev1", ["project:gac"]);
  assert.equal(link.action, "link_project");
  assert.deepEqual(link.payload.project_refs, ["project:gac"]);

  const cp = createProjectFromEvidenceEvent({ suggested_id: "project:gac" });
  assert.equal(cp.action, "create_project_from_evidence");
  assert.equal(cp.payload.suggestion.suggested_id, "project:gac");
});

test("linkSkillsEvent shape", async () => {
  const ev = await import("./events.js");
  const link = ev.linkSkillsEvent("ev1", ["ros2_basics", "nav2"]);
  assert.equal(link.action, "link_skills");
  assert.equal(link.payload.id, "ev1");
  assert.deepEqual(link.payload.skill_ids, ["ros2_basics", "nav2"]);
  assert.ok(link.event_id);
});

test("suggestSkillsEvent shape", async () => {
  const ev = await import("./events.js");
  const e = ev.suggestSkillsEvent("ev1");
  assert.equal(e.action, "suggest_skills");
  assert.equal(e.payload.id, "ev1");
  assert.ok(e.event_id);
});

test("makeEvent generates unique ids", () => {
  const a = makeEvent("x");
  const b = makeEvent("x");
  assert.notEqual(a.event_id, b.event_id);
});

test("doneTasksToEvidenceEvent shape", async () => {
  const ev = await import("./events.js");
  const preview = ev.prepareDoneTaskEvidenceEvent(["kb_1"]);
  assert.equal(preview.action, "prepare_done_task_evidence");
  assert.deepEqual(preview.payload.task_ids, ["kb_1"]);
  const accept = ev.applyDoneTaskEvidenceEvent("p1", true);
  assert.equal(accept.action, "apply_done_task_evidence");
  assert.equal(accept.payload.preview_id, "p1");
  assert.equal(accept.payload.mark_crystallized, true);
  const e = ev.doneTasksToEvidenceEvent(["kb_1", "kb_2"], true);
  assert.equal(e.action, "done_tasks_to_evidence");
  assert.deepEqual(e.payload.task_ids, ["kb_1", "kb_2"]);
  assert.equal(e.payload.mark_crystallized, true);
  // Default mark_crystallized is false.
  assert.equal(ev.doneTasksToEvidenceEvent(["kb_1"]).payload.mark_crystallized, false);
});

test("bulkApplyEvent: field/value shape", async () => {
  const ev = await import("./events.js");
  const e = ev.bulkApplyEvent(["ev1", "ev2"], { field: "review_status", value: "reviewed" });
  assert.equal(e.action, "bulk_apply");
  assert.deepEqual(e.payload.ids, ["ev1", "ev2"]);
  assert.equal(e.payload.field, "review_status");
  assert.equal(e.payload.value, "reviewed");
  assert.equal(e.payload.bulk_action, "");
});

test("bulkApplyEvent: named action shape", async () => {
  const ev = await import("./events.js");
  const e = ev.bulkApplyEvent(["ev1"], { action: "deprecate" });
  assert.equal(e.payload.bulk_action, "deprecate");
  const link = ev.bulkApplyEvent(["ev1"], { action: "link_skills", skillIds: ["nav2"] });
  assert.equal(link.payload.bulk_action, "link_skills");
  assert.deepEqual(link.payload.skill_ids, ["nav2"]);
  const fmt = ev.bulkRequestAiReformatEvent(["ev1", "ev2"]);
  assert.equal(fmt.action, "bulk_request_ai_reformat");
  assert.deepEqual(fmt.payload.ids, ["ev1", "ev2"]);
  const confirm = ev.bulkConfirmAiReformatEvent("r1");
  assert.equal(confirm.action, "bulk_confirm_ai_reformat");
  assert.equal(confirm.payload.preview_id, "r1");
});

test("output candidate event factories shape", async () => {
  const ev = await import("./events.js");
  const single = ev.createFromOutputEvent("out1", "output", ["project:x"]);
  assert.equal(single.action, "create_from_output");
  assert.equal(single.payload.output_id, "out1");
  assert.deepEqual(single.payload.project_refs, ["project:x"]);

  const items = [
    { output_id: "out1", source_kind: "output", project_refs: ["project:x"] },
    { output_id: "route-1", source_kind: "blog", project_refs: ["project:y"] },
  ];
  const bulk = ev.bulkCreateFromOutputEvent(items);
  assert.equal(bulk.action, "bulk_create_from_output");
  assert.deepEqual(bulk.payload.items, items);

  const ignore = ev.ignoreOutputCandidatesEvent(
    [{ output_id: "out1", source_kind: "output" }],
    "not_evidence"
  );
  assert.equal(ignore.action, "ignore_output_candidates");
  assert.equal(ignore.payload.reason, "not_evidence");
  assert.deepEqual(ignore.payload.items, [{ output_id: "out1", source_kind: "output" }]);

  const restore = ev.restoreOutputCandidatesEvent([{ output_id: "route-1", source_kind: "blog" }]);
  assert.equal(restore.action, "restore_output_candidates");
  assert.deepEqual(restore.payload.items, [{ output_id: "route-1", source_kind: "blog" }]);
});

test("renderMarkdown: headings, bold, lists, code", () => {
  const md = "# Title\n\nSome **bold** and `code`.\n\n- one\n- two\n\n1. first\n2. second";
  const html = renderMarkdown(md);
  assert.ok(html.includes("<h1>Title</h1>"));
  assert.ok(html.includes("<strong>bold</strong>"));
  assert.ok(html.includes("<code>code</code>"));
  assert.ok(html.includes("<ul>"));
  assert.ok(html.includes("<li>one</li>"));
  assert.ok(html.includes("<ol>"));
  assert.ok(html.includes("<li>first</li>"));
});

test("renderMarkdown: empty -> empty string", () => {
  assert.equal(renderMarkdown(""), "");
  assert.equal(renderMarkdown("   "), "");
  assert.equal(renderMarkdown(null), "");
});

test("renderMarkdown: escapes HTML (no injection)", () => {
  const html = renderMarkdown("<script>alert(1)</script>");
  assert.ok(!html.includes("<script>"));
  assert.ok(html.includes("&lt;script&gt;"));
});

test("escapeHtml basics", () => {
  assert.equal(escapeHtml('a & b < c > "d"'), "a &amp; b &lt; c &gt; &quot;d&quot;");
});

test("dedup event factories", async () => {
  const ev = await import("./events.js");
  const sug = ev.suggestDuplicatesEvent("ev1", true);
  assert.equal(sug.action, "suggest_duplicates");
  assert.equal(sug.payload.id, "ev1");
  assert.equal(sug.payload.ai, true);

  const merge = ev.mergeOrDeprecateEvent("keep1", "other1", ["summary"]);
  assert.equal(merge.action, "merge_or_deprecate");
  assert.equal(merge.payload.keep, "keep1");
  assert.equal(merge.payload.other, "other1");
  assert.deepEqual(merge.payload.merge_fields, ["summary"]);

  const dismiss = ev.dismissDuplicateEvent("a", "b");
  assert.equal(dismiss.action, "dismiss_duplicate");
  assert.equal(dismiss.payload.id, "a");
  assert.equal(dismiss.payload.other, "b");
});
