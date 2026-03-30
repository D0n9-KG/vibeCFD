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
    "border-stone-200",
    "bg-stone-50",
    "xl:h-full",
    "xl:min-h-0",
    "xl:border-t-0",
    "xl:border-l",
  ].join(" ");
}

export function getSubmarinePipelineCenterPaneConfig(): SubmarinePipelineCenterPaneConfig {
  return {
    scrollClassName: "min-h-0 flex-1 overflow-y-auto px-4 pb-6 pt-4",
    overviewClassName:
      "mb-4 rounded-2xl border border-stone-200 bg-white/95 p-4 shadow-sm backdrop-blur-sm",
    stageGridClassName:
      "grid gap-4 xl:grid-cols-2 xl:auto-rows-[minmax(16rem,1fr)]",
    stageSectionClassName: "h-full",
  };
}
