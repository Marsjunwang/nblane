import assert from "node:assert/strict";
import test from "node:test";

import {
  detailTitle,
  displayFocus,
  displayLabel,
  displaySummary,
  isRenderable,
} from "./payload.js";

const texts = {
  current: "Current goal",
  default_label: "Stage goal",
  details: "Details",
  goal_set: "Goal set",
};

test("visible payload can reveal title summary and focus", () => {
  const payload = {
    visibility: "visible",
    title: "Sensitive title",
    label: "Safe label",
    summary: "Summary",
    focus: ["one", "two", "three", "four"],
    texts,
  };

  assert.equal(displayLabel(payload), "Sensitive title");
  assert.equal(detailTitle(payload), "Sensitive title");
  assert.equal(displaySummary(payload), "Summary");
  assert.deepEqual(displayFocus(payload), ["one", "two", "three"]);
});

test("discreet payload ignores detailed fields even if present", () => {
  const payload = {
    visibility: "discreet",
    title: "Do not show",
    label: "Stage label",
    summary: "Do not show",
    focus: ["Do not show"],
    texts,
  };

  assert.equal(displayLabel(payload), "Stage label");
  assert.equal(displaySummary(payload), "");
  assert.deepEqual(displayFocus(payload), []);
});

test("hidden payload does not reveal label or details", () => {
  const payload = {
    visibility: "hidden",
    label: "Do not show",
    title: "Do not show",
    summary: "Do not show",
    texts,
  };

  assert.equal(displayLabel(payload), "Goal set");
  assert.equal(detailTitle(payload), "Details");
  assert.equal(displaySummary(payload), "");
});

test("private payload is not renderable", () => {
  assert.equal(isRenderable({ visibility: "private", texts }), false);
});
