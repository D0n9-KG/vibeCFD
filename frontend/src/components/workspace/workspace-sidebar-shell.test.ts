import assert from "node:assert/strict";
import test from "node:test";

const {
  getSubmarineMissionSidebarChrome,
  getWorkspaceSidebarChrome,
} = await import(new URL("./workspace-sidebar-shell.ts", import.meta.url).href);

void test("workspace rail uses the slate-and-sky tokenized surface language", () => {
  const chrome = getWorkspaceSidebarChrome();

  assert.ok(chrome.sidebarClassName.includes("border-slate-200/80"));
  assert.ok(chrome.sidebarClassName.includes("bg-[linear-gradient("));
  assert.ok(
    chrome.sidebarClassName.includes(
      "dark:[&_[data-slot=sidebar-inner]]:border-slate-800/80",
    ),
  );
  assert.ok(chrome.activityBarClassName.includes("workspace-surfaces-activity-bar"));
  assert.ok(chrome.activityBarClassName.includes("border-slate-200/80"));
  assert.ok(chrome.activityBarClassName.includes("text-slate-700"));
  assert.ok(chrome.contextSidebarClassName.includes("workspace-context-sidebar"));
  assert.ok(chrome.contextSidebarClassName.includes("group-data-[collapsible=icon]:hidden"));
  assert.ok(chrome.headerPanelClassName.includes("rounded-[1.2rem]"));
  assert.ok(chrome.headerPanelClassName.includes("bg-[linear-gradient("));
  assert.ok(chrome.primaryGroupClassName.includes("border-slate-200/80"));
  assert.ok(chrome.primaryGroupClassName.includes("bg-white/92"));
  assert.ok(chrome.menuButtonClassName.includes("data-[active=true]:bg-white"));
  assert.ok(chrome.menuButtonClassName.includes("hover:bg-sky-50/80"));
  assert.ok(chrome.menuButtonClassName.includes("dark:data-[active=true]:bg-sky-400/18"));
  assert.ok(chrome.historyGroupClassName.includes("bg-slate-50/90"));
});

void test("submarine mission board keeps its own sky-forward chrome", () => {
  const chrome = getSubmarineMissionSidebarChrome();

  assert.ok(chrome.rootClassName.includes("border-r"));
  assert.ok(chrome.rootClassName.includes("bg-[linear-gradient("));
  assert.ok(chrome.headerCardClassName.includes("border-sky-100/80"));
  assert.ok(chrome.headerCardClassName.includes("bg-white/95"));
  assert.ok(chrome.sectionCardClassName.includes("rounded-[1.25rem]"));
  assert.ok(chrome.sectionCardClassName.includes("border-slate-200/80"));
  assert.ok(chrome.activeRunClassName.includes("bg-sky-100/90"));
  assert.ok(chrome.activeRunClassName.includes("ring-1"));
  assert.ok(chrome.idleRunClassName.includes("hover:bg-slate-100/80"));
  assert.ok(chrome.stageButtonActiveClassName.includes("bg-sky-100/90"));
  assert.ok(chrome.footerClassName.includes("bg-white/88"));
  assert.ok(chrome.primaryActionClassName.includes("from-sky-500"));
});

void test("workspace rail and mission board remain distinct surface families", () => {
  const workspace = getWorkspaceSidebarChrome();
  const mission = getSubmarineMissionSidebarChrome();

  assert.notEqual(workspace.sidebarClassName, mission.rootClassName);
  assert.notEqual(workspace.primaryGroupClassName, mission.sectionCardClassName);
  assert.ok(workspace.menuButtonClassName.includes("slate-700"));
  assert.ok(mission.primaryActionClassName.includes("sky-500"));
});
