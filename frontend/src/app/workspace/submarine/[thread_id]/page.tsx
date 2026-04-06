"use client";

import { MessageSquareIcon, WavesIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  createAgenticWorkbenchSessionModel,
  setAgenticWorkbenchMobileNegotiationRailVisible,
  toggleAgenticWorkbenchMobileNegotiationRailVisible,
} from "@/components/workspace/agentic-workbench/session-model";
import {
  ArtifactTrigger,
  useArtifacts,
} from "@/components/workspace/artifacts";
import {
  ChatBox,
  useSpecificChatMode,
  useThreadChat,
} from "@/components/workspace/chats";
import { ExportTrigger } from "@/components/workspace/export-trigger";
import { ThreadContext } from "@/components/workspace/messages/context";
import { SubmarinePipelineChatRail } from "@/components/workspace/submarine-pipeline";
import { SubmarineAgenticWorkbench } from "@/components/workspace/submarine-workbench";
import { ThreadTitle } from "@/components/workspace/thread-title";
import { TokenUsageIndicator } from "@/components/workspace/token-usage-indicator";
import { useNotification } from "@/core/notification/hooks";
import { useLocalSettings } from "@/core/settings";
import { useThreadStream } from "@/core/threads/hooks";
import { shouldPromoteStartedThreadRoute } from "@/core/threads/use-thread-stream.state";
import { textOfMessage } from "@/core/threads/utils";

import { getSubmarineWorkbenchLayout } from "../submarine-workbench-layout";

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
        let body = "对话已结束。";
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

  const layout = useMemo(
    () =>
      getSubmarineWorkbenchLayout({
        mobileNegotiationRailVisible,
      }),
    [mobileNegotiationRailVisible],
  );

  const chatRailErrorMessage = thread.error
    ? thread.error instanceof Error
      ? thread.error.message
      : typeof thread.error === "string"
        ? thread.error
        : "线程发生未知错误。"
    : null;

  return (
    <ThreadContext.Provider value={{ thread, isMock }}>
      <ChatBox threadId={threadId}>
        <div className="relative flex size-full min-h-0 flex-col">
          <header className="absolute top-0 right-0 left-0 z-30 flex h-16 shrink-0 items-center border-b border-slate-200/80 bg-white/72 px-4 backdrop-blur-xl dark:border-slate-800/80 dark:bg-slate-950/68">
            <div className="flex min-w-0 flex-1 items-center gap-3">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl border border-sky-200/70 bg-sky-50/80 text-sky-700 dark:border-sky-900/70 dark:bg-sky-950/35 dark:text-sky-300">
                <WavesIcon className="size-4 shrink-0" />
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-medium text-slate-950 dark:text-slate-50">
                  <ThreadTitle threadId={threadId} thread={thread} />
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  VibeCFD · Submarine Cockpit · 仿真工作台
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                aria-label={
                  mobileNegotiationRailVisible
                    ? "收起对话侧栏"
                    : "展开对话侧栏"
                }
                onClick={() =>
                  setSessionModel((model) =>
                    toggleAgenticWorkbenchMobileNegotiationRailVisible(model),
                  )
                }
              >
                <MessageSquareIcon className="size-4" />
                {mobileNegotiationRailVisible ? "收起对话" : "展开对话"}
              </Button>
              <TokenUsageIndicator messages={thread.messages} />
              <ExportTrigger threadId={threadId} />
              <ArtifactTrigger />
            </div>
          </header>

          <main className="min-h-0 flex-1 overflow-y-auto pt-16">
            <div className="mx-auto flex min-h-full w-full max-w-[1720px] flex-col px-4 py-4 md:px-5">
              <div className={layout.shellClassName}>
                <div className={layout.workbenchPaneClassName}>
                  <SubmarineAgenticWorkbench
                    threadId={threadId}
                    isNewThread={isNewThread}
                    onOpenChat={focusChatRail}
                  />
                </div>

                <aside id="submarine-chat-rail" className={layout.chatRailClassName}>
                  <div className={layout.chatRailInnerClassName}>
                    <SubmarinePipelineChatRail
                      thread={thread}
                      pipelineStatus={{
                        agentLabel: "潜艇研究监督代理",
                        outputStatus: "实时同步",
                        runLabel: thread.isLoading ? "运行中" : "就绪",
                        summaryText:
                          "右侧保留协作对话与消息流，中间工作台继续专注当前阶段、证据与交付判断。",
                        tone: chatRailErrorMessage
                          ? "error"
                          : thread.isLoading
                            ? "streaming"
                            : "ready",
                        errorBanner: chatRailErrorMessage
                          ? {
                              title: "线程出错",
                              guidance:
                                "先检查最新消息，再决定是否回到运行台继续重试或调整任务。",
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
                  </div>
                </aside>
              </div>
            </div>
          </main>
        </div>
      </ChatBox>
    </ThreadContext.Provider>
  );
}
