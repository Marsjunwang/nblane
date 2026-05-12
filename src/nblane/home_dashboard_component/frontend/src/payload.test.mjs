import assert from "node:assert/strict";
import test from "node:test";

import { goalDisplay, normalizePayload } from "./payload.js";
import { goalSubmitEvent, navigationEvent } from "./events.js";

test("normalizes chart totals and quick links", () => {
  const payload = normalizePayload({
    profile: "alice",
    charts: {
      skills: {
        counts: { expert: 1, solid: 2, learning: 3, locked: 4 },
        total: 10,
        lit: 3,
        lit_rate: 0.3,
      },
      evidence: { done_uncrystallized: 2, unlinked: 1 },
      public: { draft: 3, published: 1 },
      health: { error: 0, warning: 2, info: 1 },
    },
    quick_links: [{ path: "pages/3_Kanban.py", label: "Kanban" }],
  });

  assert.equal(payload.profile, "alice");
  assert.equal(payload.charts.skills.counts.solid, 2);
  assert.equal(payload.charts.skills.litRate, 0.3);
  assert.equal(payload.charts.evidence.unlinked, 1);
  assert.equal(payload.quickLinks[0].path, "pages/3_Kanban.py");
});

test("private goal remains display-only and does not expose editor fields", () => {
  const payload = normalizePayload({
    goal: { is_set: true, locked: true, projection: null, editor: {} },
    ui: {
      goal_private_locked: "Private",
      dashboard_metric_goal: "Goal",
    },
  });
  const display = goalDisplay(payload.goal, payload.ui);

  assert.equal(payload.goal.locked, true);
  assert.deepEqual(payload.goal.editor, {});
  assert.equal(display.title, "Private");
  assert.equal(display.visibility, "private");
});

test("empty payload still renders stable defaults", () => {
  const payload = normalizePayload({});
  const display = goalDisplay(payload.goal, payload.ui);

  assert.equal(payload.profile, "");
  assert.equal(payload.charts.skills.total, 0);
  assert.equal(payload.graph.nodes.length, 0);
  assert.equal(display.visibility, "");
});

test("events return stable action shapes", () => {
  const nav = navigationEvent("pages/3_Kanban.py");
  const goal = goalSubmitEvent({ title: "Demo" });

  assert.equal(nav.action, "navigate");
  assert.equal(nav.payload.path, "pages/3_Kanban.py");
  assert.ok(nav.event_id);
  assert.equal(goal.action, "edit_goal_submit");
  assert.equal(goal.payload.title, "Demo");
});
