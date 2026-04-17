import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const {
  PRIMARY_WORKSPACE_SURFACES,
  WORKSPACE_SURFACES,
  getWorkspaceSurfaceHref,
  isWorkspaceSurfaceActive,
  matchWorkspaceSurface,
} = await import(new URL("./workspace-surface-config.ts", import.meta.url).href);

void test("workspace surface registry keeps only product workbenches and the management center as first-class surfaces", () => {
  assert.deepEqual(
    WORKSPACE_SURFACES.map((surface) => ({
      id: surface.id,
      href: surface.defaultHref,
      primary: surface.primaryNavigation,
    })),
    [
      { id: "submarine", href: "/workspace/submarine/new", primary: true },
      { id: "skill-studio", href: "/workspace/skill-studio/new", primary: true },
      { id: "agents", href: "/workspace/agents", primary: false },
      { id: "control-center", href: "/workspace/control-center", primary: true },
    ],
  );

  assert.deepEqual(
    PRIMARY_WORKSPACE_SURFACES.map((surface) => surface.id),
    ["submarine", "skill-studio", "control-center"],
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
  assert.equal(
    isWorkspaceSurfaceActive("control-center", "/workspace/control-center"),
    true,
  );
  assert.equal(matchWorkspaceSurface("/workspace/chats/123").id, "submarine");
});

void test("workspace surfaces preserve mock-aware skill studio hrefs", () => {
  assert.equal(
    getWorkspaceSurfaceHref("skill-studio"),
    "/workspace/skill-studio/new",
  );
  assert.equal(
    getWorkspaceSurfaceHref("skill-studio", { isMock: true }),
    "/workspace/skill-studio/new?mock=true",
  );
  assert.equal(getWorkspaceSurfaceHref("agents"), "/workspace/agents");
  assert.equal(
    getWorkspaceSurfaceHref("control-center"),
    "/workspace/control-center",
  );
});

void test("workspace header no longer shows English product eyebrow copy", async () => {
  const source = await readFile(
    new URL("./workspace-header.tsx", import.meta.url),
    "utf8",
  );

  assert.doesNotMatch(source, /Engineering Research Workspace/);
  assert.match(source, /当前界面/);
});
