type SkillStudioWorkbenchLayoutOptions = {
  chatOpen: boolean;
};

type SkillStudioWorkbenchLayout = {
  shellClassName: string;
  workbenchPaneClassName: string;
  chatRailClassName: string;
  chatRailInnerClassName: string;
};

export function getSkillStudioWorkbenchLayout({
  chatOpen,
}: SkillStudioWorkbenchLayoutOptions): SkillStudioWorkbenchLayout {
  return {
    shellClassName: [
      "grid",
      "w-full",
      "min-h-0",
      "grid-cols-1",
      "gap-4",
      "xl:h-[calc(100vh-5.5rem)]",
      "xl:overflow-hidden",
      chatOpen && "xl:grid-cols-[minmax(0,1.15fr)_minmax(400px,480px)]",
    ]
      .filter(Boolean)
      .join(" "),
    workbenchPaneClassName:
      "min-w-0 space-y-4 xl:min-h-0 xl:overflow-y-auto xl:pr-2",
    chatRailClassName: [
      chatOpen ? "block" : "hidden",
      "min-w-0",
      "xl:block",
      "xl:h-full",
      "xl:min-h-0",
    ]
      .filter(Boolean)
      .join(" "),
    chatRailInnerClassName:
      "flex h-[min(72vh,760px)] min-h-[560px] flex-col overflow-hidden rounded-2xl border bg-background shadow-sm xl:sticky xl:top-0 xl:h-full xl:min-h-0",
  };
}

export type {
  SkillStudioWorkbenchLayout,
  SkillStudioWorkbenchLayoutOptions,
};
