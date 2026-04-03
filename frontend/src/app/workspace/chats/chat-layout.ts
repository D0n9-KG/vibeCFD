type ChatPageLayoutOptions = {
  hasRuntimeWorkbench: boolean;
  isNewThread: boolean;
  supportPanelOpen: boolean;
};

type ChatPageLayout = {
  shellClassName: string;
  contentClassName: string;
  messageListClassName: string;
  inputShellClassName: string;
  supportPanelClassName: string;
  supportPanelInnerClassName: string;
  supportToggleClassName: string;
};

export function getChatPageLayout({
  hasRuntimeWorkbench,
  isNewThread,
  supportPanelOpen,
}: ChatPageLayoutOptions): ChatPageLayout {
  return {
    shellClassName: [
      "grid",
      "w-full",
      "min-h-0",
      "grid-cols-1",
      "gap-4",
      "2xl:h-[calc(100vh-5.5rem)]",
      "2xl:grid-cols-[minmax(0,1fr)_minmax(320px,360px)]",
      "2xl:overflow-hidden",
    ].join(" "),
    contentClassName: [
      "relative",
      "flex",
      "min-h-[32rem]",
      "min-w-0",
      "flex-1",
      "overflow-hidden",
      "rounded-[28px]",
      "border",
      "border-stone-200/80",
      "bg-white/94",
      "shadow-[0_18px_44px_rgba(15,23,42,0.06)]",
      "px-4",
      "pt-4",
      hasRuntimeWorkbench ? "pb-40 md:pb-32" : "pb-32",
    ].join(" "),
    messageListClassName: ["flex-1", "justify-start", !isNewThread ? "pt-10" : "pt-6"]
      .filter(Boolean)
      .join(" "),
    inputShellClassName: [
      "relative",
      "w-full",
      isNewThread ? "-translate-y-[calc(50vh-96px)]" : "",
      isNewThread
        ? "max-w-(--container-width-sm)"
        : "max-w-(--container-width-md)",
    ]
      .filter(Boolean)
      .join(" "),
    supportPanelClassName: [
      supportPanelOpen ? "block" : "hidden",
      "min-w-0",
      "2xl:block",
      "2xl:h-full",
      "2xl:min-h-0",
    ]
      .filter(Boolean)
      .join(" "),
    supportPanelInnerClassName:
      "flex h-[min(72vh,760px)] min-h-[420px] flex-col overflow-hidden rounded-[28px] border border-stone-200/80 bg-white/94 shadow-[0_18px_44px_rgba(15,23,42,0.06)] 2xl:h-full 2xl:min-h-0",
    supportToggleClassName:
      "focus-visible:border-primary/40 focus-visible:ring-primary/40 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-background",
  };
}

export type { ChatPageLayout, ChatPageLayoutOptions };
