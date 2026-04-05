export type WorkspaceSidebarChrome = {
  sidebarClassName: string;
  activityBarClassName: string;
  activityBarCompactClassName: string;
  activityBarTriggerClassName: string;
  activityBarButtonClassName: string;
  activityBarButtonActiveClassName: string;
  activityBarSettingsButtonClassName: string;
  contextSidebarClassName: string;
  headerClassName: string;
  contentClassName: string;
  footerClassName: string;
  headerPanelClassName: string;
  brandEyebrowClassName: string;
  brandMetaClassName: string;
  primaryGroupClassName: string;
  secondaryGroupClassName: string;
  historyGroupClassName: string;
  groupLabelClassName: string;
  menuButtonClassName: string;
  historyButtonClassName: string;
  footerMenuButtonClassName: string;
  headerQuickActionClassName: string;
};

export type SubmarineMissionSidebarChrome = {
  rootClassName: string;
  headerWrapClassName: string;
  headerCardClassName: string;
  headerEyebrowClassName: string;
  headerTitleClassName: string;
  headerMetaClassName: string;
  runsSectionClassName: string;
  stageSectionClassName: string;
  sectionLabelClassName: string;
  sectionCardClassName: string;
  activeRunClassName: string;
  idleRunClassName: string;
  statusTextActiveClassName: string;
  statusTextIdleClassName: string;
  stageButtonClassName: string;
  stageButtonActiveClassName: string;
  footerClassName: string;
  primaryActionClassName: string;
  secondaryActionClassName: string;
};

export function getWorkspaceSidebarChrome(): WorkspaceSidebarChrome {
  return {
    sidebarClassName: [
      "[&_[data-slot=sidebar-inner]]:border-r",
      "[&_[data-slot=sidebar-inner]]:border-slate-200/80",
      "[&_[data-slot=sidebar-inner]]:bg-[linear-gradient(180deg,rgba(248,250,252,0.98),rgba(240,244,249,0.96))]",
      "dark:[&_[data-slot=sidebar-inner]]:border-slate-800/80",
      "dark:[&_[data-slot=sidebar-inner]]:bg-[linear-gradient(180deg,rgba(10,17,31,0.98),rgba(12,21,38,0.98))]",
      "[&_[data-slot=sidebar-inner]]:shadow-[inset_-1px_0_0_rgba(15,23,42,0.04)]",
      "dark:[&_[data-slot=sidebar-inner]]:shadow-[inset_-1px_0_0_rgba(148,163,184,0.08)]",
    ].join(" "),
    activityBarClassName:
      "workspace-surfaces-activity-bar flex h-full w-12 shrink-0 flex-col border-r border-slate-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(244,247,251,0.98))] px-1.5 py-2.5 text-slate-700 shadow-[inset_-1px_0_0_rgba(15,23,42,0.04)]",
    activityBarCompactClassName:
      "workspace-surfaces-activity-bar flex w-full items-center gap-2 rounded-2xl border border-slate-200/80 bg-white/90 px-2 py-2 shadow-[0_18px_40px_rgba(15,23,42,0.08)] dark:border-slate-800/80 dark:bg-slate-950/80",
    activityBarTriggerClassName:
      "size-9 rounded-xl border border-slate-200/80 bg-white/92 text-slate-700 opacity-100 shadow-sm transition-colors hover:border-sky-200/80 hover:bg-sky-50 hover:text-sky-700",
    activityBarButtonClassName:
      "flex size-10 items-center justify-center rounded-xl border border-transparent text-slate-500 transition-colors hover:border-sky-200/80 hover:bg-sky-50 hover:text-sky-700 focus-visible:border-sky-300 focus-visible:ring-2 focus-visible:ring-sky-300/60 focus-visible:ring-offset-2 focus-visible:ring-offset-white",
    activityBarButtonActiveClassName:
      "border-sky-200/90 bg-white text-sky-700 shadow-[0_10px_24px_rgba(14,165,233,0.14)]",
    activityBarSettingsButtonClassName:
      "size-10 rounded-xl border border-slate-200/80 bg-white/92 text-slate-600 shadow-sm transition-colors hover:border-sky-200/80 hover:bg-sky-50 hover:text-sky-700 focus-visible:ring-2 focus-visible:ring-sky-300/60 focus-visible:ring-offset-2 focus-visible:ring-offset-white",
    contextSidebarClassName:
      "workspace-context-sidebar flex min-w-0 flex-1 flex-col bg-[linear-gradient(180deg,rgba(248,250,252,0.96),rgba(241,245,249,0.88))] dark:bg-[linear-gradient(180deg,rgba(10,17,31,0.88),rgba(15,23,42,0.8))] group-data-[collapsible=icon]:hidden",
    headerClassName:
      "gap-2.5 border-b border-slate-200/80 bg-transparent px-2.5 pb-2.5 pt-2.5 dark:border-slate-800/80",
    contentClassName: "gap-2.5 bg-transparent px-2.5 pb-2.5 pt-2.5",
    footerClassName:
      "border-t border-slate-200/80 bg-white/70 px-2.5 pb-2.5 pt-2.5 backdrop-blur-sm dark:border-slate-800/80 dark:bg-slate-950/50",
    headerPanelClassName:
      "rounded-[1.2rem] border border-slate-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(244,247,252,0.94))] px-3 py-3 shadow-[0_12px_28px_rgba(15,23,42,0.06)] backdrop-blur-sm dark:border-slate-800/80 dark:bg-[linear-gradient(180deg,rgba(8,15,28,0.9),rgba(12,22,39,0.82))]",
    brandEyebrowClassName:
      "block whitespace-nowrap text-[10px] font-semibold uppercase tracking-[0.24em] text-sky-700/80 dark:text-sky-300/80",
    brandMetaClassName: "break-keep text-[11px] leading-5 text-slate-500 dark:text-slate-400",
    primaryGroupClassName:
      "rounded-[1.2rem] border border-slate-200/80 bg-white/92 p-1.5 shadow-[0_12px_28px_rgba(15,23,42,0.06)] dark:border-slate-800/80 dark:bg-slate-950/64",
    secondaryGroupClassName:
      "rounded-[1.15rem] border border-white/70 bg-white/72 p-1.5 shadow-[0_10px_24px_rgba(15,23,42,0.04)] dark:border-slate-800/70 dark:bg-slate-900/48",
    historyGroupClassName:
      "rounded-[1.15rem] border border-slate-200/80 bg-slate-50/90 p-1.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.85)] dark:border-slate-800/80 dark:bg-slate-900/52",
    groupLabelClassName:
      "px-2 text-[9px] font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400",
    menuButtonClassName:
      "h-9 rounded-xl text-slate-700 transition-colors hover:bg-sky-50/80 hover:text-slate-950 data-[active=true]:border data-[active=true]:border-sky-200/80 data-[active=true]:bg-white data-[active=true]:text-slate-950 data-[active=true]:shadow-[0_10px_24px_rgba(15,23,42,0.06)] dark:text-slate-200 dark:hover:bg-slate-800/70 dark:hover:text-white dark:data-[active=true]:bg-sky-400/18 dark:data-[active=true]:text-sky-100 dark:data-[active=true]:shadow-none",
    historyButtonClassName:
      "rounded-xl text-slate-600 transition-colors hover:bg-white/90 hover:text-slate-950 data-[active=true]:border data-[active=true]:border-sky-200/80 data-[active=true]:bg-white data-[active=true]:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800/70 dark:hover:text-white dark:data-[active=true]:border-sky-400/30 dark:data-[active=true]:bg-slate-950/90 dark:data-[active=true]:text-white",
    footerMenuButtonClassName:
      "rounded-xl border border-transparent bg-white/72 text-slate-700 shadow-sm transition-colors hover:bg-white hover:text-slate-950 data-[state=open]:bg-white data-[state=open]:text-slate-950 dark:bg-slate-900/72 dark:text-slate-200 dark:hover:bg-slate-900 dark:hover:text-white dark:data-[state=open]:bg-slate-900 dark:data-[state=open]:text-white",
    headerQuickActionClassName:
      "h-10 rounded-xl bg-[linear-gradient(135deg,#f97316,#38bdf8)] text-white shadow-[0_10px_24px_rgba(56,189,248,0.18)] transition-all hover:brightness-105 hover:text-white data-[active=true]:brightness-95 data-[active=true]:text-white",
  };
}

export function getSubmarineMissionSidebarChrome(): SubmarineMissionSidebarChrome {
  return {
    rootClassName:
      "flex h-full flex-col overflow-hidden border-r border-slate-200/80 bg-[linear-gradient(180deg,rgba(248,250,252,0.98),rgba(241,245,249,0.96))] dark:border-slate-800/80 dark:bg-[linear-gradient(180deg,rgba(9,15,27,0.98),rgba(12,20,35,0.98))]",
    headerWrapClassName: "border-b border-slate-200/80 px-3 pb-3 pt-3 dark:border-slate-800/80",
    headerCardClassName:
      "rounded-[1.35rem] border border-sky-100/80 bg-white/95 px-3.5 py-3 shadow-[0_20px_44px_rgba(14,165,233,0.10)] dark:border-sky-400/20 dark:bg-slate-950/72",
    headerEyebrowClassName:
      "text-[10px] font-semibold uppercase tracking-[0.24em] text-sky-600 dark:text-sky-300",
    headerTitleClassName: "mt-1 text-[15px] font-semibold tracking-tight text-slate-950 dark:text-white",
    headerMetaClassName: "mt-1 text-[11px] leading-5 text-slate-500 dark:text-slate-400",
    runsSectionClassName: "px-3 pb-2 pt-3",
    stageSectionClassName: "flex-1 overflow-y-auto px-3 pb-2 pt-2",
    sectionLabelClassName:
      "px-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400",
    sectionCardClassName:
      "mt-2 rounded-[1.25rem] border border-slate-200/80 bg-white/92 p-2 shadow-[0_16px_36px_rgba(15,23,42,0.06)] dark:border-slate-800/80 dark:bg-slate-950/64",
    activeRunClassName:
      "bg-sky-100/90 text-sky-900 ring-1 ring-sky-200/80 shadow-[0_10px_24px_rgba(14,165,233,0.12)]",
    idleRunClassName:
      "text-slate-600 transition-colors hover:bg-slate-100/80 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800/80 dark:hover:text-white",
    statusTextActiveClassName: "text-sky-600",
    statusTextIdleClassName: "text-slate-400 dark:text-slate-500",
    stageButtonClassName:
      "flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-left text-[11px] text-slate-600 transition-colors hover:bg-slate-100/80 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800/80 dark:hover:text-white",
    stageButtonActiveClassName:
      "bg-sky-100/90 font-semibold text-sky-900 ring-1 ring-sky-200/80 dark:bg-sky-400/18 dark:text-sky-100 dark:ring-sky-400/28",
    footerClassName:
      "border-t border-slate-200/80 bg-white/88 p-3 backdrop-blur-sm dark:border-slate-800/80 dark:bg-slate-950/72",
    primaryActionClassName:
      "w-full rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 py-2 text-[12px] font-semibold text-white shadow-[0_14px_30px_rgba(14,165,233,0.28)] transition-transform hover:-translate-y-[1px] hover:from-sky-600 hover:to-cyan-500",
    secondaryActionClassName:
      "h-7 rounded-lg px-2.5 text-[11px] font-medium text-slate-500 transition-colors hover:bg-white hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white",
  };
}
