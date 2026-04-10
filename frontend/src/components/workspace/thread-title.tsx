import type { BaseStream } from "@langchain/langgraph-sdk";
import { useEffect } from "react";

import { useI18n } from "@/core/i18n/hooks";
import type { AgentThreadState } from "@/core/threads";
import { resolveThreadDisplayTitle } from "@/core/threads/utils";

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
  const resolvedTitle = resolveThreadDisplayTitle(
    rawTitle,
    isNewThread ? t.pages.newChat : t.pages.untitled,
    thread.values?.messages,
  );
  const fallbackTitle = isNewThread ? t.pages.newChat : t.pages.untitled;

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

  if (!rawTitle && resolvedTitle === fallbackTitle) {
    return null;
  }

  return <FlipDisplay uniqueKey={threadId}>{resolvedTitle}</FlipDisplay>;
}
