export type SubmarinePipelineDesktopShellConfig = {
  containerClassName: string;
  groupClassName: string;
};

export type SubmarinePipelineCenterPaneConfig = {
  scrollClassName: string;
  overviewClassName: string;
  stageGridClassName: string;
  stageSectionClassName: string;
};

export function getSubmarinePipelineDesktopShellConfig(): SubmarinePipelineDesktopShellConfig {
  return {
    // Responsive visibility must live on an outer wrapper because
    // react-resizable-panels injects inline display:flex on the group itself.
    containerClassName: "hidden min-h-0 flex-1 xl:flex",
    groupClassName: "min-h-0 flex-1",
  };
}

export function getSubmarinePipelineChatRailClassName(): string {
  return [
    "flex",
    "h-[42vh]",
    "min-h-[18rem]",
    "shrink-0",
    "flex-col",
    "border-t",
    "border-slate-200/80",
    "bg-white/82",
    "xl:h-full",
    "xl:min-h-0",
    "xl:border-t-0",
    "xl:border-l",
    "dark:border-slate-800/80",
    "dark:bg-slate-950/76",
  ].join(" ");
}

export function getSubmarinePipelineChatViewportClassName(): string {
  return ["flex-1", "min-h-0", "justify-start", "overflow-y-auto"].join(" ");
}

export function getSubmarinePipelineCenterPaneConfig(): SubmarinePipelineCenterPaneConfig {
  return {
    scrollClassName: "min-h-0 flex-1 overflow-y-auto px-4 pb-6 pt-4",
    overviewClassName:
      "mb-4 rounded-2xl border border-slate-200/80 bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.10),_transparent_30%),linear-gradient(180deg,_rgba(255,255,255,0.98),_rgba(248,250,252,0.96))] p-5 shadow-sm backdrop-blur-sm dark:border-slate-800/80 dark:bg-[radial-gradient(circle_at_top_right,_rgba(56,189,248,0.18),_transparent_32%),linear-gradient(180deg,_rgba(15,23,42,0.92),_rgba(2,6,23,0.94))]",
    stageGridClassName:
      "grid gap-4 xl:grid-cols-2 xl:auto-rows-[minmax(16rem,auto)]",
    stageSectionClassName: "min-h-0",
  };
}
