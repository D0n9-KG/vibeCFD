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
      "min-h-full",
      "grid-cols-1",
      "gap-4",
      chatOpen && "xl:grid-cols-[minmax(0,1fr)_minmax(360px,460px)]",
    ]
      .filter(Boolean)
      .join(" "),
    workbenchPaneClassName: [
      "min-w-0",
      "grid",
      "gap-4",
      "xl:min-h-full",
      "xl:grid-cols-[minmax(240px,280px)_minmax(0,1fr)]",
      "xl:pr-2",
    ].join(" "),
    chatRailClassName: [
      chatOpen ? "block" : "hidden",
      "min-w-0",
      "xl:h-full",
      "xl:min-h-0",
    ]
      .filter(Boolean)
      .join(" "),
    chatRailInnerClassName:
      "flex h-[min(72vh,760px)] min-h-[560px] flex-col overflow-hidden rounded-[30px] border border-slate-200/80 bg-white/88 shadow-[0_24px_64px_rgba(15,23,42,0.08)] xl:sticky xl:top-0 xl:max-h-[calc(100vh-7.5rem)] xl:min-h-[640px] dark:border-slate-800/80 dark:bg-slate-950/76",
  };
}

export type {
  SkillStudioWorkbenchLayout,
  SkillStudioWorkbenchLayoutOptions,
};
