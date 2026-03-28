type ChatPageLayoutOptions = {
  hasRuntimeWorkbench: boolean;
  isNewThread: boolean;
};

type ChatPageLayout = {
  contentClassName: string;
  messageListClassName: string;
  inputShellClassName: string;
};

export function getChatPageLayout({
  hasRuntimeWorkbench,
  isNewThread,
}: ChatPageLayoutOptions): ChatPageLayout {
  return {
    contentClassName: [
      "flex",
      "size-full",
      "w-full",
      "max-w-[calc(var(--container-width-md)+64px)]",
      "flex-col",
      "px-4",
      hasRuntimeWorkbench ? "pb-40 md:pb-32" : "",
    ]
      .filter(Boolean)
      .join(" "),
    messageListClassName: ["size-full", !isNewThread ? "pt-10" : ""]
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
  };
}
