import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const {
  getSubmarinePipelineCenterPaneConfig,
  getSubmarinePipelineChatRailClassName,
  getSubmarinePipelineChatViewportClassName,
  getSubmarinePipelineDesktopShellConfig,
} = await import(
  new URL("./submarine-pipeline-shell.ts", import.meta.url).href
);
const moduleDir = path.dirname(fileURLToPath(import.meta.url));

void test(
  "desktop shell keeps responsive visibility classes outside the inline panel group",
  () => {
    const shell = getSubmarinePipelineDesktopShellConfig();

    assert.equal(shell.containerClassName, "hidden min-h-0 flex-1 xl:flex");
    assert.equal(shell.groupClassName, "min-h-0 flex-1");
    assert.ok(shell.containerClassName.includes("hidden"));
    assert.ok(!shell.groupClassName.includes("hidden"));
    assert.ok(!shell.groupClassName.includes("xl:flex"));
  },
);

void test("chat rail uses an explicit mobile height instead of collapsing to zero", () => {
  const className = getSubmarinePipelineChatRailClassName();
  const viewportClassName = getSubmarinePipelineChatViewportClassName();

  assert.ok(className.includes("h-[42vh]"));
  assert.ok(className.includes("min-h-[18rem]"));
  assert.ok(className.includes("shrink-0"));
  assert.ok(className.includes("border-t"));
  assert.ok(className.includes("xl:h-full"));
  assert.ok(className.includes("xl:border-l"));
  assert.ok(viewportClassName.includes("min-h-0"));
  assert.ok(viewportClassName.includes("flex-1"));
  assert.ok(viewportClassName.includes("overflow-y-auto"));
});

void test("chat rail gives the conversation the rail instead of spending height on a duplicate header", async () => {
  const source = await readFile(
    path.join(moduleDir, "submarine-pipeline.tsx"),
    "utf-8",
  );

  assert.doesNotMatch(source, /pipelineStatus\.agentLabel/);
  assert.doesNotMatch(source, /Chat header/);
});

void test("center pane uses a scroll-friendly desktop grid instead of clipping stage content", () => {
  const config = getSubmarinePipelineCenterPaneConfig();

  assert.ok(config.scrollClassName.includes("overflow-y-auto"));
  assert.ok(config.scrollClassName.includes("pb-6"));
  assert.ok(config.overviewClassName.includes("rounded-2xl"));
  assert.ok(config.overviewClassName.includes("shadow-sm"));
  assert.ok(config.stageGridClassName.includes("grid"));
  assert.ok(config.stageGridClassName.includes("gap-4"));
  assert.ok(config.stageGridClassName.includes("xl:grid-cols-2"));
  assert.ok(config.stageGridClassName.includes("xl:auto-rows-[minmax(16rem,auto)]"));
  assert.ok(!config.stageSectionClassName.includes("h-full"));
});
