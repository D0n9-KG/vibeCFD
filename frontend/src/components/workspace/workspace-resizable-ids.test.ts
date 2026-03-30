import assert from "node:assert/strict";
import test from "node:test";

const { WORKSPACE_RESIZABLE_IDS } = await import(
  new URL("./workspace-resizable-ids.ts", import.meta.url).href
);

void test(
  "workspace workbench resizable groups and handles use explicit stable ids",
  () => {
    assert.deepEqual(WORKSPACE_RESIZABLE_IDS, {
      chatBoxGroup: "workspace-chat-box-group",
      chatBoxArtifactsHandle: "workspace-chat-box-artifacts-handle",
      submarinePipelineGroup: "submarine-pipeline-group",
      submarinePipelineSidebarHandle: "submarine-pipeline-sidebar-handle",
      submarinePipelineChatHandle: "submarine-pipeline-chat-handle",
    });
  },
);

void test("workspace resizable ids stay unique", () => {
  const ids = Object.values(WORKSPACE_RESIZABLE_IDS);
  assert.equal(new Set(ids).size, ids.length);
  ids.forEach((id) => {
    assert.equal(typeof id, "string");
    if (typeof id === "string") {
      assert.match(id, /^[a-z0-9-]+$/);
    }
  });
});
