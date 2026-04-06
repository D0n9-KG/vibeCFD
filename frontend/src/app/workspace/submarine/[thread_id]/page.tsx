"use client";

import { MessageSquareIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

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
import { ThreadContext } from "@/components/workspace/messages/context";
import { SubmarinePipelineChatRail } from "@/components/workspace/submarine-pipeline";
import { SubmarineAgenticWorkbench } from "@/components/workspace/submarine-workbench";
import { TokenUsageIndicator } from "@/components/workspace/token-usage-indicator";
import { useNotification } from "@/core/notification/hooks";
import { useLocalSettings } from "@/core/settings";
import { useThreadStream } from "@/core/threads/hooks";
import { shouldPromoteStartedThreadRoute } from "@/core/threads/use-thread-stream.state";
import { textOfMessage } from "@/core/threads/utils";

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
        showNotification(state.title, { body });
      }
    },
  });

  useEffect(() => {
    if (
      !shouldPromoteStartedThreadRoute({
        pendingThreadId: pendingThreadRouteId,
        isLoading: thread.isLoading,
        persistedMessageCount: streamMeta.persistedMessageCount,
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
    pendingThreadRouteId,
    router,
    streamMeta.persistedMessageCount,
    thread.isLoading,
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
        <div className="flex size-full min-h-0 flex-col">
          <main className="min-h-0 flex-1 overflow-y-auto">
            <div className="mx-auto flex min-h-full w-full max-w-[1720px] flex-col px-4 py-4 md:px-5">
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
                      aria-label={
                        mobileNegotiationRailVisible
                          ? "Hide negotiation rail"
                          : "Show negotiation rail"
                      }
                      onClick={() =>
                        setSessionModel((model) =>
                          toggleAgenticWorkbenchMobileNegotiationRailVisible(model),
                        )
                      }
                    >
                      <MessageSquareIcon className="size-4" />
                      {mobileNegotiationRailVisible ? "Hide rail" : "Show rail"}
                    </Button>
                    <TokenUsageIndicator messages={thread.messages} />
                    <ExportTrigger threadId={threadId} />
                    <ArtifactTrigger />
                  </div>
                }
                negotiationContent={
                  <SubmarinePipelineChatRail
                    thread={thread}
                    pipelineStatus={{
                      agentLabel: "Submarine research supervisor",
                      outputStatus: "Live sync",
                      runLabel: thread.isLoading ? "Running" : "Ready",
                      summaryText:
                        "The right rail keeps collaboration, approvals, and interruption context visible while the center remains workbench-focused.",
                      tone: chatRailErrorMessage
                        ? "error"
                        : thread.isLoading
                          ? "streaming"
                          : "ready",
                      errorBanner: chatRailErrorMessage
                        ? {
                            title: "Thread error",
                            guidance:
                              "Review the latest message, then decide whether to revise and rerun.",
                            message: chatRailErrorMessage,
                          }
                        : null,
                    }}
                    threadId={threadId}
                    isNewThread={isNewThread}
                    isUploading={isUploading}
                    context={settings.context}
                    onContextChange={(context) => setSettings("context", context)}
                    handleSubmit={(message) => sendMessage(threadId, message)}
                    onStop={handleStop}
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
