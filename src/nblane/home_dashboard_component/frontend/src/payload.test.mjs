import assert from "node:assert/strict";
import test from "node:test";

import { goalDisplay, goalDraftFromFormData, normalizePayload } from "./payload.js";
import {
  archiveGoalEvent,
  captureInboxSubmitEvent,
  confirmGoalSkillLinksEvent,
  createGoalSubmitEvent,
  editGoalSubmitEvent,
  goalSubmitEvent,
  manualGoalSkillLinkEvent,
  navigationEvent,
  requestGoalSkillAiMatchEvent,
  requestGoalSkillRuleMatchEvent,
  setPrimaryGoalEvent,
} from "./events.js";

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
      evidence: {
        done_uncrystallized: 2,
        unlinked: 1,
        needs_review: 4,
        status_risk: 5,
      },
      public: { draft: 3, published: 1 },
      health: { error: 0, warning: 2, info: 1 },
    },
    quick_links: [{ path: "pages/3_Kanban.py", label: "Kanban" }],
    north_star: {
      visibility: "discreet",
      display_text: "Build useful robot systems.",
      is_set: true,
      locked: false,
    },
    active_goals: [
      {
        id: "g1",
        is_primary: true,
        projection: { id: "g1", visibility: "discreet", label: "Demo" },
      },
    ],
    skill_alignment: {
      primary_goal_id: "g1",
      by_goal: {
        g1: {
          confirmed: [
            { node_id: "ros2_basics", label: "ROS 2 Basics", source: "rule", score: 3 },
          ],
          candidates: [
            { node_id: "moveit2", label: "MoveIt 2", source: "ai", score: 4 },
          ],
        },
      },
      confirmed_links: [
        { node_id: "ros2_basics", label: "ROS 2 Basics", source: "rule", score: 3 },
      ],
      candidates: [
        { node_id: "moveit2", label: "MoveIt 2", source: "ai", score: 4 },
      ],
      skill_options: [{ id: "ros2_basics", label: "ROS 2 Basics" }],
    },
    sources: {
      active_total: 2,
      active_titles: ["Captured source"],
    },
    graph: {
      schema_version: "1.0",
      view: "home",
      layers: ["direction", "objective", "capability", "source"],
      nodes: [
        {
          id: "goal:g1",
          type: "goal",
          layer: "objective",
          label: "Demo",
          metric: "Primary",
          record_id: "g1",
          owner_path: "",
          is_primary: true,
        },
        {
          id: "skill:ros2_basics",
          type: "skill",
          layer: "capability",
          label: "ROS 2 Basics",
          metric: "rule",
          record_id: "ros2_basics",
          owner_path: "pages/1_Skill_Tree.py",
        },
        {
          id: "source:inbox",
          type: "source",
          layer: "source",
          label: "Inbox sources",
          metric: "planned",
          implemented: false,
          placeholder: true,
        },
      ],
      edges: [
        { from: "goal:g1", to: "skill:ros2_basics", type: "skill_link", relation: "supports" },
        { source: "skill:ros2_basics", target: "evidence", suggested: true },
        { from: "goal:g1", to: "source:inbox", type: "contains", placeholder: true },
      ],
    },
  });

  assert.equal(payload.profile, "alice");
  assert.equal(payload.charts.skills.counts.solid, 2);
  assert.equal(payload.charts.skills.litRate, 0.3);
  assert.equal(payload.charts.evidence.unlinked, 1);
  assert.equal(payload.charts.evidence.needsReview, 4);
  assert.equal(payload.charts.evidence.statusRisk, 5);
  assert.equal(payload.quickLinks[0].path, "pages/3_Kanban.py");
  assert.equal(payload.northStar.displayText, "Build useful robot systems.");
  assert.equal(payload.activeGoals[0].isPrimary, true);
  assert.equal(payload.skillAlignment.confirmedLinks[0].nodeId, "ros2_basics");
  assert.equal(payload.skillAlignment.candidates[0].source, "ai");
  assert.equal(payload.skillAlignment.byGoal.g1.confirmed[0].nodeId, "ros2_basics");
  assert.equal(payload.sources.active_total, 2);
  assert.equal(payload.graph.nodes[0].recordId, "g1");
  assert.equal(payload.graph.nodes[0].isPrimary, true);
  assert.equal(payload.graph.nodes[1].layer, "capability");
  assert.equal(payload.graph.nodes[1].implemented, true);
  assert.equal(payload.graph.nodes[2].placeholder, true);
  assert.equal(payload.graph.nodes[2].implemented, false);
  assert.deepEqual(payload.graph.layers, ["direction", "objective", "capability", "source"]);
  assert.equal(payload.graph.edges[1].from, "skill:ros2_basics");
  assert.equal(payload.graph.edges[1].suggested, true);
  assert.equal(payload.graph.edges[0].relation, "supports");
  assert.equal(payload.graph.edges[2].placeholder, true);
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
  const capture = captureInboxSubmitEvent({ title: "Paper note", tags: ["research"] });
  const goal = goalSubmitEvent({ title: "Demo" });
  const create = createGoalSubmitEvent({ title: "Second goal" });
  const edit = editGoalSubmitEvent("g2", { title: "Edited" });
  const archive = archiveGoalEvent("g2");
  const primary = setPrimaryGoalEvent("g2");
  const rule = requestGoalSkillRuleMatchEvent("g1");
  const ai = requestGoalSkillAiMatchEvent("g1");
  const manual = manualGoalSkillLinkEvent("g1", "ros2_basics");
  const confirm = confirmGoalSkillLinksEvent("g1", [{ node_id: "ros2_basics" }]);

  assert.equal(nav.action, "navigate");
  assert.equal(nav.payload.path, "pages/3_Kanban.py");
  assert.ok(nav.event_id);
  assert.equal(capture.action, "capture_inbox_submit");
  assert.equal(capture.payload.title, "Paper note");
  assert.deepEqual(capture.payload.tags, ["research"]);
  assert.equal(goal.action, "edit_goal_submit");
  assert.equal(goal.payload.title, "Demo");
  assert.equal(create.action, "create_goal_submit");
  assert.equal(create.payload.title, "Second goal");
  assert.equal(edit.action, "edit_goal_submit");
  assert.equal(edit.payload.goal_id, "g2");
  assert.equal(archive.action, "archive_goal");
  assert.equal(archive.payload.goal_id, "g2");
  assert.equal(primary.action, "set_primary_goal");
  assert.equal(primary.payload.goal_id, "g2");
  assert.equal(rule.action, "request_goal_skill_rule_match");
  assert.equal(rule.payload.goal_id, "g1");
  assert.equal(ai.action, "request_goal_skill_ai_match");
  assert.equal(ai.payload.goal_id, "g1");
  assert.equal(manual.action, "manual_goal_skill_link");
  assert.equal(manual.payload.node_id, "ros2_basics");
  assert.equal(confirm.action, "confirm_goal_skill_links");
  assert.equal(confirm.payload.links[0].node_id, "ros2_basics");
});

test("goal form draft keeps create primary intent", () => {
  const formData = new FormData();
  formData.set("title", "Create second goal");
  formData.set("status", "active");
  formData.set("include_in_agent_context", "on");
  formData.set("set_as_primary", "on");
  formData.set("target_skills", "ros2_basics\nmoveit2");

  const draft = goalDraftFromFormData(formData);

  assert.equal(draft.title, "Create second goal");
  assert.equal(draft.include_in_agent_context, true);
  assert.equal(draft.set_as_primary, true);
  assert.deepEqual(draft.target_skills, ["ros2_basics", "moveit2"]);
});
