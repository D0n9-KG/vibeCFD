export type SubmarinePipelineDesktopShellConfig = {
  containerClassName: string;
  groupClassName: string;
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
