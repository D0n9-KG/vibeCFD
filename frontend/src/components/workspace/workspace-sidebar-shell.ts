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
      "[&_[data-slot=sidebar-inner]]:border-amber-100/80",
      "[&_[data-slot=sidebar-inner]]:bg-[linear-gradient(180deg,rgba(255,251,235,0.98),rgba(250,245,235,0.96))]",
      "[&_[data-slot=sidebar-inner]]:shadow-[inset_-1px_0_0_rgba(251,191,36,0.10)]",
    ].join(" "),
    activityBarClassName:
      "workspace-surfaces-activity-bar flex h-full w-12 shrink-0 flex-col border-r border-stone-900/80 bg-stone-950 px-2 py-3 text-stone-100 shadow-[inset_-1px_0_0_rgba(255,255,255,0.06)]",
    activityBarCompactClassName:
      "workspace-surfaces-activity-bar flex w-full items-center gap-2 rounded-2xl border border-stone-200/80 bg-white/88 px-2 py-2 shadow-[0_16px_32px_rgba(15,23,42,0.06)]",
    activityBarTriggerClassName:
      "size-8 rounded-xl border border-white/10 bg-white/10 text-white opacity-100 hover:bg-white/16 hover:text-white",
    activityBarButtonClassName:
      "flex size-9 items-center justify-center rounded-xl border border-transparent text-stone-300 transition-colors hover:border-white/10 hover:bg-white/8 hover:text-white focus-visible:border-sky-300 focus-visible:ring-2 focus-visible:ring-sky-300/60 focus-visible:ring-offset-2 focus-visible:ring-offset-stone-950",
    activityBarButtonActiveClassName:
      "border-sky-300/40 bg-sky-500/18 text-sky-100 shadow-[0_10px_24px_rgba(14,138,207,0.28)]",
    activityBarSettingsButtonClassName:
      "size-9 rounded-xl border border-white/10 bg-white/8 text-stone-200 transition-colors hover:bg-white/14 hover:text-white focus-visible:ring-2 focus-visible:ring-sky-300/60 focus-visible:ring-offset-2 focus-visible:ring-offset-stone-950",
    contextSidebarClassName:
      "workspace-context-sidebar flex min-w-0 flex-1 flex-col bg-[linear-gradient(180deg,rgba(255,251,235,0.92),rgba(250,245,235,0.82))] group-data-[collapsible=icon]:hidden",
    headerClassName:
      "gap-3 border-b border-amber-100/80 bg-transparent px-3 pb-3 pt-3",
    contentClassName: "gap-3 bg-transparent px-3 pb-3 pt-3",
    footerClassName:
      "border-t border-amber-100/70 bg-white/60 px-3 pb-3 pt-3 backdrop-blur-sm",
    headerPanelClassName:
      "rounded-2xl border border-amber-100/80 bg-white/90 px-3 py-3 shadow-[0_18px_40px_rgba(120,53,15,0.08)] backdrop-blur-sm",
    brandEyebrowClassName:
      "block whitespace-nowrap text-[10px] font-semibold uppercase tracking-[0.24em] text-amber-700/80",
    brandMetaClassName: "break-keep text-[11px] leading-5 text-stone-500",
    primaryGroupClassName:
      "rounded-2xl border border-amber-100/80 bg-white/90 p-2 shadow-[0_18px_40px_rgba(120,53,15,0.08)]",
    secondaryGroupClassName:
      "rounded-2xl border border-white/70 bg-white/72 p-2 shadow-[0_12px_30px_rgba(120,53,15,0.05)]",
    historyGroupClassName:
      "rounded-2xl border border-stone-200/80 bg-stone-50/85 p-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.85)]",
    groupLabelClassName:
      "px-2.5 text-[10px] font-semibold uppercase tracking-[0.24em] text-stone-500",
    menuButtonClassName:
      "h-10 rounded-xl text-stone-700 transition-colors hover:bg-amber-50/80 hover:text-stone-900 data-[active=true]:bg-amber-100/80 data-[active=true]:text-stone-900 data-[active=true]:shadow-sm",
    historyButtonClassName:
      "rounded-xl text-stone-600 transition-colors hover:bg-white/90 hover:text-stone-900 data-[active=true]:border data-[active=true]:border-amber-200/80 data-[active=true]:bg-white data-[active=true]:text-stone-900",
    footerMenuButtonClassName:
      "rounded-xl border border-transparent bg-white/60 text-stone-700 shadow-sm transition-colors hover:bg-white hover:text-stone-900 data-[state=open]:bg-white data-[state=open]:text-stone-900",
    headerQuickActionClassName:
      "h-10 rounded-xl bg-stone-900 text-white shadow-sm transition-colors hover:bg-stone-800 hover:text-white data-[active=true]:bg-stone-900 data-[active=true]:text-white",
  };
}

export function getSubmarineMissionSidebarChrome(): SubmarineMissionSidebarChrome {
  return {
    rootClassName:
      "flex h-full flex-col overflow-hidden border-r border-stone-200/80 bg-gradient-to-b from-sky-50/80 via-white to-stone-50/95",
    headerWrapClassName: "border-b border-stone-200/80 px-3 pb-3 pt-3",
    headerCardClassName:
      "rounded-2xl border border-sky-100/80 bg-white/95 px-3.5 py-3 shadow-[0_20px_44px_rgba(14,165,233,0.10)]",
    headerEyebrowClassName:
      "text-[10px] font-semibold uppercase tracking-[0.24em] text-sky-600",
    headerTitleClassName: "mt-1 text-[15px] font-semibold tracking-tight text-stone-900",
    headerMetaClassName: "mt-1 text-[11px] leading-5 text-stone-500",
    runsSectionClassName: "px-3 pb-2 pt-3",
    stageSectionClassName: "flex-1 overflow-y-auto px-3 pb-2 pt-2",
    sectionLabelClassName:
      "px-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-stone-500",
    sectionCardClassName:
      "mt-2 rounded-2xl border border-stone-200/80 bg-white/90 p-2 shadow-[0_16px_36px_rgba(15,23,42,0.06)]",
    activeRunClassName:
      "bg-sky-100/90 text-sky-900 ring-1 ring-sky-200/80 shadow-[0_10px_24px_rgba(14,165,233,0.12)]",
    idleRunClassName:
      "text-stone-600 transition-colors hover:bg-stone-100/80 hover:text-stone-900",
    statusTextActiveClassName: "text-sky-600",
    statusTextIdleClassName: "text-stone-400",
    stageButtonClassName:
      "flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-left text-[11px] text-stone-600 transition-colors hover:bg-stone-100/80 hover:text-stone-900",
    stageButtonActiveClassName:
      "bg-sky-100/90 font-semibold text-sky-900 ring-1 ring-sky-200/80",
    footerClassName:
      "border-t border-stone-200/80 bg-white/88 p-3 backdrop-blur-sm",
    primaryActionClassName:
      "w-full rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 py-2 text-[12px] font-semibold text-white shadow-[0_14px_30px_rgba(14,165,233,0.28)] transition-transform hover:-translate-y-[1px] hover:from-sky-600 hover:to-cyan-500",
    secondaryActionClassName:
      "h-7 rounded-lg px-2.5 text-[11px] font-medium text-stone-500 transition-colors hover:bg-white hover:text-stone-900",
  };
}
