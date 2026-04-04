import type { BaseStream } from "@langchain/langgraph-sdk";
import { useEffect } from "react";

import { useI18n } from "@/core/i18n/hooks";
import { localizeThreadDisplayTitle } from "@/core/i18n/workspace-display";
import type { AgentThreadState } from "@/core/threads";

import { useThreadChat } from "./chats";
import { FlipDisplay } from "./flip-display";

export function ThreadTitle({
  threadId,
  thread,
}: {
  className?: string;
  threadId: string;
  thread: BaseStream<AgentThreadState>;
}) {
  const { t } = useI18n();
  const { isNewThread } = useThreadChat();
  const rawTitle = thread.values?.title?.trim();
  const resolvedTitle =
    !rawTitle || rawTitle === "Untitled"
      ? isNewThread
        ? t.pages.newChat
        : t.pages.untitled
      : localizeThreadDisplayTitle(rawTitle);

  useEffect(() => {
    if (thread.isThreadLoading) {
      document.title = `${t.common.loading} - ${t.pages.appName}`;
      return;
    }

    document.title = `${resolvedTitle} - ${t.pages.appName}`;
  }, [
    resolvedTitle,
    t.common.loading,
    t.pages.appName,
    thread.isThreadLoading,
  ]);

  if (!rawTitle) {
    return null;
  }

  return <FlipDisplay uniqueKey={threadId}>{resolvedTitle}</FlipDisplay>;
}
