import assert from "node:assert/strict";
import test from "node:test";
import {
  actionForDropIntent,
  canDropOn,
  dropIntentLabel,
  resolveDropIntent,
} from "./dndHelpers.js";

const root = {
  id: "root",
  type: "root",
  title: "Public Library",
  children: [],
};
const folder = {
  id: "folder",
  type: "folder",
  title: "Folder",
  parent_id: "root",
  children: [],
};
const post = {
  id: "post",
  type: "post",
  title: "Post",
  ref: "blog/post.md",
  parent_id: "root",
  children: [],
};
const child = {
  id: "child",
  type: "post",
  title: "Child",
  ref: "blog/child.md",
  parent_id: "folder",
  children: [],
};
const media = {
  id: "media",
  type: "media",
  title: "Media",
  ref: "media/example.png",
  parent_id: "root",
  children: [],
};
folder.children = [child];
root.children = [folder, post, media];

test("explicit drop positions map parentable and leaf rows consistently", () => {
  assert.equal(canDropOn(media, folder, "before"), true);
  assert.equal(canDropOn(media, folder, "into"), true);
  assert.equal(canDropOn(media, folder, "after"), true);
  assert.equal(canDropOn(media, post, "into"), true);
  assert.equal(canDropOn(post, root, "into"), true);
  assert.equal(canDropOn(post, root, "before"), false);
  assert.equal(canDropOn(post, root, "after"), false);
  assert.equal(canDropOn(post, media, "before"), true);
  assert.equal(canDropOn(post, media, "after"), true);
  assert.equal(canDropOn(post, media, "into"), false);
});

test("drop intent rejects self and descendant cycles", () => {
  assert.equal(canDropOn(folder, folder, "into"), false);
  assert.equal(canDropOn(folder, child, "into"), false);
  assert.equal(canDropOn(folder, child, "before"), false);
});

test("before position produces reorder payloads and same-depth indicators", () => {
  const before = resolveDropIntent(post, folder, "before", { overDepth: 1 });
  assert.equal(before.kind, "reorder");
  assert.equal(before.position, "before");
  assert.equal(before.indentDepth, 1);
  assert.equal(before.indicatorEdge, "top");
  assert.equal(before.beforeNodeId, "folder");
  assert.equal(before.parentId, "root");
  assert.deepEqual(actionForDropIntent(before, post), {
    action: "library_reorder_node",
    payload: {
      node_id: "post",
      parent_id: "root",
      target_parent_id: "root",
      before_node_id: "folder",
      after_node_id: "",
      drop_intent: "before",
    },
  });
});

test("into position on folder, post, and root produces move-into payloads", () => {
  const intoFolder = resolveDropIntent(media, folder, "into", { overDepth: 1 });
  assert.equal(intoFolder.kind, "move-into");
  assert.equal(intoFolder.position, "into");
  assert.equal(intoFolder.parentId, "folder");
  assert.equal(intoFolder.indentDepth, 2);
  assert.equal(intoFolder.indicatorEdge, "bottom");
  assert.deepEqual(actionForDropIntent(intoFolder, media), {
    action: "library_move_node",
    payload: {
      node_id: "media",
      parent_id: "folder",
      target_parent_id: "folder",
      drop_intent: "into",
    },
  });

  const intoPost = resolveDropIntent(media, post, "into", { overDepth: 1 });
  assert.equal(intoPost.kind, "move-into");
  assert.equal(intoPost.parentId, "post");

  const intoRoot = resolveDropIntent(child, root, "into", { overDepth: 0 });
  assert.equal(intoRoot.kind, "move-into");
  assert.equal(intoRoot.position, "into");
  assert.equal(intoRoot.parentId, "root");
  assert.equal(intoRoot.indentDepth, 1);
});

test("after position produces reorder payloads on media and parentable rows", () => {
  const after = resolveDropIntent(post, media, "after", { overDepth: 1 });
  assert.equal(after.kind, "reorder");
  assert.equal(after.position, "after");
  assert.equal(after.afterNodeId, "media");
  assert.equal(after.parentId, "root");
  assert.equal(after.indentDepth, 1);
  assert.deepEqual(actionForDropIntent(after, post), {
    action: "library_reorder_node",
    payload: {
      node_id: "post",
      parent_id: "root",
      target_parent_id: "root",
      before_node_id: "",
      after_node_id: "media",
      drop_intent: "after",
    },
  });

  const afterFolder = resolveDropIntent(post, folder, "after", { overDepth: 1 });
  assert.equal(afterFolder.kind, "reorder");
  assert.equal(afterFolder.afterNodeId, "folder");
  assert.equal(afterFolder.parentId, "root");
});

test("virtual posts attach existing refs instead of moving node ids", () => {
  const virtual = {
    id: "post:virtual",
    type: "post",
    title: "Virtual",
    route: "virtual",
    virtual: true,
    parent_id: "root",
  };
  const intoIntent = resolveDropIntent(virtual, folder, "into");
  assert.equal(intoIntent.kind, "attach-existing");
  assert.deepEqual(actionForDropIntent(intoIntent, virtual), {
    action: "library_attach_existing",
    payload: {
      ref: "virtual",
      title: "Virtual",
      parent_id: "folder",
      target_parent_id: "folder",
      before_node_id: "",
      after_node_id: "",
      drop_intent: "into",
    },
  });

  const beforeIntent = resolveDropIntent(virtual, post, "before");
  assert.equal(beforeIntent.kind, "attach-existing");
  assert.deepEqual(actionForDropIntent(beforeIntent, virtual), {
    action: "library_attach_existing",
    payload: {
      ref: "virtual",
      title: "Virtual",
      parent_id: "root",
      target_parent_id: "root",
      before_node_id: "post",
      after_node_id: "",
      drop_intent: "before",
    },
  });

  const afterIntent = resolveDropIntent(virtual, media, "after");
  assert.equal(afterIntent.kind, "attach-existing");
  assert.deepEqual(actionForDropIntent(afterIntent, virtual), {
    action: "library_attach_existing",
    payload: {
      ref: "virtual",
      title: "Virtual",
      parent_id: "root",
      target_parent_id: "root",
      before_node_id: "",
      after_node_id: "media",
      drop_intent: "after",
    },
  });
});

test("virtual targets are rejected", () => {
  const virtualTarget = {
    id: "target:virtual",
    type: "post",
    title: "Virtual target",
    virtual: true,
    parent_id: "root",
  };
  assert.equal(resolveDropIntent(post, virtualTarget, "before"), null);
  assert.equal(resolveDropIntent(post, virtualTarget, "into"), null);
  assert.equal(resolveDropIntent(post, virtualTarget, "after"), null);
});

test("drop labels distinguish folder, post subdoc, and sibling positions", () => {
  assert.equal(
    dropIntentLabel(resolveDropIntent(post, folder, "into"), {
      library_drop_into_folder: "放入「{title}」",
    }),
    "放入「Folder」",
  );
  assert.equal(
    dropIntentLabel(resolveDropIntent(folder, post, "into"), {
      library_drop_as_subdoc: "作为「{title}」的子文档",
    }),
    "作为「Post」的子文档",
  );
  assert.equal(
    dropIntentLabel(resolveDropIntent(post, folder, "after"), {
      library_drop_after: "放在「{title}」之后",
    }),
    "放在「Folder」之后",
  );
});
