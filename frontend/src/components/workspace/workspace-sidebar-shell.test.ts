import assert from "node:assert/strict";
import test from "node:test";

const {
  getSubmarineMissionSidebarChrome,
  getWorkspaceSidebarChrome,
} = await import(new URL("./workspace-sidebar-shell.ts", import.meta.url).href);

void test("workspace rail keeps a studio-navigation identity", () => {
  const chrome = getWorkspaceSidebarChrome();

  assert.ok(chrome.sidebarClassName.includes("border-amber-100/80"));
  assert.ok(chrome.sidebarClassName.includes("bg-[linear-gradient("));
  assert.ok(chrome.activityBarClassName.includes("workspace-surfaces-activity-bar"));
  assert.ok(chrome.activityBarClassName.includes("bg-stone-950"));
  assert.ok(chrome.contextSidebarClassName.includes("workspace-context-sidebar"));
  assert.ok(chrome.contextSidebarClassName.includes("group-data-[collapsible=icon]:hidden"));
  assert.ok(chrome.headerPanelClassName.includes("rounded-2xl"));
  assert.ok(chrome.headerPanelClassName.includes("bg-white/90"));
  assert.ok(chrome.primaryGroupClassName.includes("border-amber-100/80"));
  assert.ok(chrome.primaryGroupClassName.includes("shadow-[0_18px_40px_rgba(120,53,15,0.08)]"));
  assert.ok(chrome.menuButtonClassName.includes("data-[active=true]:bg-amber-100/80"));
  assert.ok(chrome.menuButtonClassName.includes("hover:bg-amber-50/80"));
  assert.ok(chrome.historyGroupClassName.includes("bg-stone-50/85"));
});

void test("submarine mission board reads differently from the global workspace rail", () => {
  const chrome = getSubmarineMissionSidebarChrome();

  assert.ok(chrome.rootClassName.includes("border-r"));
  assert.ok(chrome.rootClassName.includes("from-sky-50/80"));
  assert.ok(chrome.headerCardClassName.includes("border-sky-100/80"));
  assert.ok(chrome.headerCardClassName.includes("bg-white/95"));
  assert.ok(chrome.sectionCardClassName.includes("rounded-2xl"));
  assert.ok(chrome.sectionCardClassName.includes("border-stone-200/80"));
  assert.ok(chrome.activeRunClassName.includes("bg-sky-100/90"));
  assert.ok(chrome.activeRunClassName.includes("ring-1"));
  assert.ok(chrome.idleRunClassName.includes("hover:bg-stone-100/80"));
  assert.ok(chrome.stageButtonActiveClassName.includes("bg-sky-100/90"));
  assert.ok(chrome.footerClassName.includes("bg-white/88"));
  assert.ok(chrome.primaryActionClassName.includes("from-sky-500"));
});

void test("workspace rail and mission board do not collapse into the same surface language", () => {
  const workspace = getWorkspaceSidebarChrome();
  const mission = getSubmarineMissionSidebarChrome();

  assert.notEqual(workspace.sidebarClassName, mission.rootClassName);
  assert.notEqual(workspace.primaryGroupClassName, mission.sectionCardClassName);
  assert.ok(workspace.menuButtonClassName.includes("amber"));
  assert.ok(!mission.primaryActionClassName.includes("amber"));
});
