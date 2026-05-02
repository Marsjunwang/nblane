import assert from "node:assert/strict";
import test from "node:test";

import { stripAliasPrefix } from "./slashItems.js";

test("stripAliasPrefix removes localized slash aliases", () => {
  const item = {
    operation: "formula",
    title: "Formula",
    visual_kind: "",
    aliases: ["formula", "latex", "math", "公式"],
  };

  assert.equal(stripAliasPrefix("公式 二次方程", item), "二次方程");
  assert.equal(stripAliasPrefix("formula quadratic equation", item), "quadratic equation");
  assert.equal(stripAliasPrefix("Formula", item), "");
  assert.equal(stripAliasPrefix("公式", item), "");
});

test("stripAliasPrefix removes repeated aliases from query start only", () => {
  const item = {
    operation: "visual",
    title: "Visual",
    visual_kind: "example",
    aliases: ["visual", "图", "配图"],
  };

  assert.equal(stripAliasPrefix("图 visual robot arm", item), "robot arm");
  assert.equal(stripAliasPrefix("robot arm visual", item), "robot arm visual");
});
