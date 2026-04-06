import type { AgenticWorkbenchSurface } from "./session-model.ts";

export type AgenticWorkbenchLayoutOptions = {
  surface: AgenticWorkbenchSurface;
  mobileNegotiationRailVisible: boolean;
};

export type AgenticWorkbenchLayout = {
  shellClassName: string;
  workbenchPaneClassName: string;
  chatRailClassName: string;
  chatRailInnerClassName: string;
};

export function getAgenticWorkbenchLayout({
  surface,
  mobileNegotiationRailVisible,
}: AgenticWorkbenchLayoutOptions): AgenticWorkbenchLayout {
  const desktopNegotiationRailWidthClassName =
    surface === "submarine" ? "minmax(320px,420px)" : "minmax(340px,460px)";
  const desktopWorkbenchPaddingClassName =
    surface === "submarine" ? "xl:pr-1" : "xl:pr-2";

  return {
    shellClassName: [
      "grid",
      "w-full",
      "min-h-full",
      "grid-cols-1",
      "gap-4",
      "xl:h-[calc(100vh-5.5rem)]",
      "xl:overflow-hidden",
      `xl:grid-cols-[minmax(0,1fr)_${desktopNegotiationRailWidthClassName}]`,
    ].join(" "),
    workbenchPaneClassName: [
      "min-w-0",
      "grid",
      "gap-4",
      "xl:min-h-0",
      "xl:overflow-hidden",
      "xl:grid-cols-[minmax(240px,280px)_minmax(400px,1fr)]",
      desktopWorkbenchPaddingClassName,
    ].join(" "),
    chatRailClassName: [
      mobileNegotiationRailVisible ? "block" : "hidden",
      "min-w-0",
      "xl:block",
      "xl:h-full",
      "xl:min-h-0",
    ].join(" "),
    chatRailInnerClassName:
      "flex h-[min(72vh,760px)] min-h-[560px] flex-col overflow-hidden rounded-[30px] border border-slate-200/80 bg-white/88 shadow-[0_24px_64px_rgba(15,23,42,0.08)] xl:h-full xl:min-h-[640px] dark:border-slate-800/80 dark:bg-slate-950/76",
  };
}
