import assert from "node:assert/strict";
import test from "node:test";

const {
  getSubmarinePipelineCenterPaneConfig,
  getSubmarinePipelineChatRailClassName,
  getSubmarinePipelineDesktopShellConfig,
} = await import(
  new URL("./submarine-pipeline-shell.ts", import.meta.url).href
);

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

  assert.ok(className.includes("h-[42vh]"));
  assert.ok(className.includes("min-h-[18rem]"));
  assert.ok(className.includes("shrink-0"));
  assert.ok(className.includes("border-t"));
  assert.ok(className.includes("xl:h-full"));
  assert.ok(className.includes("xl:border-l"));
});

void test("center pane uses a desktop grid that fills large workbench space", () => {
  const config = getSubmarinePipelineCenterPaneConfig();

  assert.ok(config.scrollClassName.includes("overflow-y-auto"));
  assert.ok(config.scrollClassName.includes("pb-6"));
  assert.ok(config.overviewClassName.includes("rounded-2xl"));
  assert.ok(config.overviewClassName.includes("shadow-sm"));
  assert.ok(config.stageGridClassName.includes("grid"));
  assert.ok(config.stageGridClassName.includes("gap-4"));
  assert.ok(config.stageGridClassName.includes("xl:grid-cols-2"));
  assert.ok(
    config.stageGridClassName.includes("xl:auto-rows-[minmax(16rem,1fr)]"),
  );
  assert.ok(config.stageSectionClassName.includes("h-full"));
});
