import assert from "node:assert/strict";
import test from "node:test";

const {
  WORKSPACE_SURFACES,
  getWorkspaceSurfaceHref,
  isWorkspaceSurfaceActive,
  matchWorkspaceSurface,
} = await import(new URL("./workspace-surface-config.ts", import.meta.url).href);

void test("workspace surfaces expose the four locked top-level entries", () => {
  assert.deepEqual(
    WORKSPACE_SURFACES.map((surface) => ({
      id: surface.id,
      label: surface.label,
      href: surface.defaultHref,
    })),
    [
      {
        id: "submarine",
        label: "仿真",
        href: "/workspace/submarine/new",
      },
      {
        id: "skill-studio",
        label: "Skill Studio",
        href: "/workspace/skill-studio",
      },
      {
        id: "chats",
        label: "对话",
        href: "/workspace/chats",
      },
      {
        id: "agents",
        label: "智能体",
        href: "/workspace/agents",
      },
    ],
  );
});

void test("workspace surfaces resolve active state from route prefixes", () => {
  assert.equal(
    isWorkspaceSurfaceActive("submarine", "/workspace/submarine/123"),
    true,
  );
  assert.equal(
    isWorkspaceSurfaceActive("skill-studio", "/workspace/skill-studio/abc"),
    true,
  );
  assert.equal(isWorkspaceSurfaceActive("agents", "/workspace/agents/new"), true);
  assert.equal(isWorkspaceSurfaceActive("chats", "/workspace/agents/new"), false);
  assert.equal(matchWorkspaceSurface("/workspace/chats/123").id, "chats");
});

void test("workspace surfaces preserve mock-aware skill studio hrefs", () => {
  assert.equal(getWorkspaceSurfaceHref("skill-studio"), "/workspace/skill-studio");
  assert.equal(
    getWorkspaceSurfaceHref("skill-studio", { isMock: true }),
    "/workspace/skill-studio?mock=true",
  );
  assert.equal(getWorkspaceSurfaceHref("agents"), "/workspace/agents");
});
