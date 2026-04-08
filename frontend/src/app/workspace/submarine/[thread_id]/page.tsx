"use client";

import { MessageSquareIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { Button } from "@/components/ui/button";
import {
  createAgenticWorkbenchSessionModel,
  setAgenticWorkbenchMobileNegotiationRailVisible,
  toggleAgenticWorkbenchMobileNegotiationRailVisible,
} from "@/components/workspace/agentic-workbench/session-model";
import { ArtifactTrigger, useArtifacts } from "@/components/workspace/artifacts";
import {
  ChatBox,
  useSpecificChatMode,
  useThreadChat,
} from "@/components/workspace/chats";
import { ExportTrigger } from "@/components/workspace/export-trigger";
import { InputBox } from "@/components/workspace/input-box";
import { MessageList } from "@/components/workspace/messages";
import { ThreadContext } from "@/components/workspace/messages/context";
import type { SubmarineRuntimeSnapshotPayload } from "@/components/workspace/submarine-runtime-panel.contract";
import { SubmarineAgenticWorkbench } from "@/components/workspace/submarine-workbench";
import { getSubmarineNegotiationAttentionKey } from "@/components/workspace/submarine-workbench/submarine-negotiation-rail.model";
import { TokenUsageIndicator } from "@/components/workspace/token-usage-indicator";
import { useNotification } from "@/core/notification/hooks";
import { useLocalSettings } from "@/core/settings";
import { useThreadStream } from "@/core/threads/hooks";
import { shouldPromoteStartedThreadRoute } from "@/core/threads/use-thread-stream.state";
import { resolveThreadDisplayTitle, textOfMessage } from "@/core/threads/utils";
import { env } from "@/env";

type SubmarineInputContext = ReturnType<typeof useLocalSettings>[0]["context"];
type SubmarineThreadStream = ReturnType<typeof useThreadStream>[0];

type SubmarineNegotiationRailBodyProps = {
  thread: SubmarineThreadStream;
  threadId: string;
  isNewThread: boolean;
  isUploading: boolean;
  context: SubmarineInputContext;
  onContextChange: (context: SubmarineInputContext) => void;
  onSubmit: (message: PromptInputMessage) => Promise<void> | void;
  onStop: () => Promise<void>;
  errorMessage: string | null;
};

function SubmarineNegotiationRailBody({
  thread,
  threadId,
  isNewThread,
  isUploading,
  context,
  onContextChange,
  onSubmit,
  onStop,
  errorMessage,
}: SubmarineNegotiationRailBodyProps) {
  const inputStatus = errorMessage
    ? "error"
    : thread.isLoading
      ? "streaming"
      : "ready";

  return (
    <div
      id="submarine-chat-rail"
      className="flex h-full min-h-0 flex-col overflow-hidden rounded-[24px] border border-slate-200/80 bg-white/96"
    >
      <div className="border-b border-slate-200/70 px-4 py-3">
        <div className="text-sm font-semibold text-slate-900">
          主智能体协商线程
        </div>
        <div className="mt-1 text-xs leading-5 text-slate-500">
          右侧协商区负责所有修改、追问和重新协商，中央主画布只负责讲清楚研究推进过程。
        </div>
        {errorMessage ? (
          <div className="mt-3 rounded-2xl border border-red-200 bg-red-50 px-3 py-2 text-xs leading-5 text-red-800">
            {errorMessage}
          </div>
        ) : null}
      </div>
      <div className="flex min-h-0 flex-1 overflow-hidden">
        <MessageList
          className="flex-1 min-h-0 justify-start overflow-y-auto"
          paddingBottom={160}
          threadId={threadId}
          thread={thread}
        />
      </div>
      <div className="shrink-0 border-t border-slate-200/80 bg-white p-2.5">
        <InputBox
          className="w-full bg-white"
          textareaClassName="min-h-36"
          isNewThread={isNewThread}
          showNewThreadSuggestions={false}
          threadId={threadId}
          autoFocus={isNewThread}
          status={inputStatus}
          context={context}
          disabled={env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" || isUploading}
          onContextChange={onContextChange}
          onSubmit={onSubmit}
          onStop={onStop}
        />
      </div>
    </div>
  );
}

export default function SubmarineWorkbenchPage() {
  const router = useRouter();
  const [settings, setSettings] = useLocalSettings();
  const { threadId, isNewThread, markThreadStarted, isMock } = useThreadChat();
  const { showNotification } = useNotification();
  const { setOpen: setArtifactsOpen, deselect: deselectArtifact } =
    useArtifacts();
  const [sessionModel, setSessionModel] = useState(() =>
    createAgenticWorkbenchSessionModel({
      surface: "submarine",
      isNewThread,
    }),
  );
  const [pendingThreadRouteId, setPendingThreadRouteId] = useState<
    string | null
  >(null);
  const [autoNegotiationAttentionKey, setAutoNegotiationAttentionKey] =
    useState<string | null>(null);
  const mobileNegotiationRailVisible =
    sessionModel.mobileNegotiationRailVisible;

  useSpecificChatMode();

  useEffect(() => {
    deselectArtifact();
    setArtifactsOpen(false);
  }, [deselectArtifact, setArtifactsOpen]);

  const [thread, sendMessage, isUploading, streamMeta] = useThreadStream({
    threadId: isNewThread ? undefined : threadId,
    isNewThread,
    context: settings.context,
    isMock,
    workbenchKind: "submarine",
    onStart: (createdThreadId) => {
      markThreadStarted(createdThreadId);
      if (isNewThread) {
        setPendingThreadRouteId(createdThreadId);
      }
    },
    onFinish: (state) => {
      if (document.hidden || !document.hasFocus()) {
        let body = "Conversation finished.";
        const lastMessage = state.messages.at(-1);
        if (lastMessage) {
          const textContent = textOfMessage(lastMessage);
          if (textContent) {
            body =
              textContent.length > 200
                ? `${textContent.substring(0, 200)}...`
                : textContent;
          }
        }
        showNotification(
          resolveThreadDisplayTitle(state.title, "潜艇 CFD 会话", state.messages),
          { body },
        );
      }
    },
  });
  const runtime =
    thread.values.submarine_runtime != null &&
    typeof thread.values.submarine_runtime === "object"
      ? (thread.values.submarine_runtime as SubmarineRuntimeSnapshotPayload)
      : null;
  const negotiationAttentionKey =
    getSubmarineNegotiationAttentionKey(runtime);

  useEffect(() => {
    if (
      !shouldPromoteStartedThreadRoute({
        pendingThreadId: pendingThreadRouteId,
        activeThreadId: threadId,
        isLoading: thread.isLoading,
        persistedMessageCount: streamMeta.persistedMessageCount,
        visibleMessageCount: thread.messages.length,
      })
    ) {
      return;
    }

    const nextPath = isMock
      ? `/workspace/submarine/${pendingThreadRouteId}?mock=true`
      : `/workspace/submarine/${pendingThreadRouteId}`;
    router.replace(nextPath);
    setPendingThreadRouteId(null);
  }, [
    isMock,
    threadId,
    pendingThreadRouteId,
    router,
    thread.messages.length,
    streamMeta.persistedMessageCount,
    thread.isLoading,
  ]);

  useEffect(() => {
    if (!negotiationAttentionKey) {
      if (autoNegotiationAttentionKey !== null) {
        setAutoNegotiationAttentionKey(null);
      }
      return;
    }

    if (autoNegotiationAttentionKey === negotiationAttentionKey) {
      return;
    }

    setAutoNegotiationAttentionKey(negotiationAttentionKey);

    if (!mobileNegotiationRailVisible) {
      setSessionModel((model) =>
        setAgenticWorkbenchMobileNegotiationRailVisible(model, true),
      );
    }
  }, [
    autoNegotiationAttentionKey,
    mobileNegotiationRailVisible,
    negotiationAttentionKey,
  ]);

  const handleStop = useCallback(async () => {
    await thread.stop();
  }, [thread]);

  const focusChatRail = useCallback(() => {
    if (!mobileNegotiationRailVisible) {
      setSessionModel((model) =>
        setAgenticWorkbenchMobileNegotiationRailVisible(model, true),
      );
      window.setTimeout(() => {
        const rail = document.getElementById("submarine-chat-rail");
        rail?.scrollIntoView({ behavior: "smooth", block: "start" });
        const input = rail?.querySelector("textarea");
        if (input instanceof HTMLTextAreaElement) {
          input.focus();
        }
      }, 50);
      return;
    }

    const rail = document.getElementById("submarine-chat-rail");
    rail?.scrollIntoView({ behavior: "smooth", block: "start" });
    const input = rail?.querySelector("textarea");
    if (input instanceof HTMLTextAreaElement) {
      input.focus();
    }
  }, [mobileNegotiationRailVisible]);

  const chatRailErrorMessage = thread.error
    ? thread.error instanceof Error
      ? thread.error.message
      : typeof thread.error === "string"
        ? thread.error
        : "Thread failed with an unknown error."
    : null;

  return (
    <ThreadContext.Provider value={{ thread, isMock }}>
      <ChatBox threadId={threadId}>
        <div className="flex size-full min-h-0 flex-col overflow-hidden">
          <main className="min-h-0 flex-1 overflow-hidden">
            <div className="mx-auto flex h-full w-full max-w-[1720px] flex-col px-4 py-4 md:px-5">
              <SubmarineAgenticWorkbench
                threadId={threadId}
                isNewThread={isNewThread}
                showChatRail={mobileNegotiationRailVisible}
                onToggleChatRail={() =>
                  setSessionModel((model) =>
                    toggleAgenticWorkbenchMobileNegotiationRailVisible(model),
                  )
                }
                onOpenChat={focusChatRail}
                headerActions={
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className="xl:hidden"
                      aria-label={
                        mobileNegotiationRailVisible
                          ? "收起协商区"
                          : "展开协商区"
                      }
                      onClick={() =>
                        setSessionModel((model) =>
                          toggleAgenticWorkbenchMobileNegotiationRailVisible(model),
                        )
                      }
                    >
                      <MessageSquareIcon className="size-4" />
                      {mobileNegotiationRailVisible ? "收起协商区" : "展开协商区"}
                    </Button>
                    <TokenUsageIndicator messages={thread.messages} />
                    <ExportTrigger threadId={threadId} />
                    <ArtifactTrigger />
                  </div>
                }
                negotiationContent={
                  <SubmarineNegotiationRailBody
                    thread={thread}
                    threadId={threadId}
                    isNewThread={isNewThread}
                    isUploading={isUploading}
                    context={settings.context}
                    onContextChange={(context) => setSettings("context", context)}
                    onSubmit={(message) => sendMessage(threadId, message)}
                    onStop={handleStop}
                    errorMessage={chatRailErrorMessage}
                  />
                }
              />
            </div>
          </main>
        </div>
      </ChatBox>
    </ThreadContext.Provider>
  );
}
