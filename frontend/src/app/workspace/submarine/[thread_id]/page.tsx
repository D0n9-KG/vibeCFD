"use client";

import { MessageSquareIcon, WavesIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
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
import { SubmarineWorkbenchShell } from "@/components/workspace/submarine-workbench-shell";
import { ThreadTitle } from "@/components/workspace/thread-title";
import { TokenUsageIndicator } from "@/components/workspace/token-usage-indicator";
import { useNotification } from "@/core/notification/hooks";
import { useLocalSettings } from "@/core/settings";
import { useThreadStream } from "@/core/threads/hooks";
import { textOfMessage } from "@/core/threads/utils";

import { getSubmarineWorkbenchLayout } from "../submarine-workbench-layout";

export default function SubmarineWorkbenchPage() {
  const router = useRouter();
  const [settings, setSettings] = useLocalSettings();
  const { threadId, isNewThread, markThreadStarted, isMock } = useThreadChat();
  const { showNotification } = useNotification();
  const { setOpen: setArtifactsOpen } = useArtifacts();
  const [chatOpen, setChatOpen] = useState(false);

  useSpecificChatMode();

  useEffect(() => {
    setArtifactsOpen(false);
  }, [setArtifactsOpen]);

  const [thread, sendMessage, isUploading] = useThreadStream({
    threadId: isNewThread ? undefined : threadId,
    isNewThread,
    context: settings.context,
    isMock,
    workbenchKind: "submarine",
    onStart: (createdThreadId) => {
      markThreadStarted(createdThreadId);
      const nextPath = isMock
        ? `/workspace/submarine/${createdThreadId}?mock=true`
        : `/workspace/submarine/${createdThreadId}`;
      router.replace(nextPath);
    },
    onFinish: (state) => {
      if (document.hidden || !document.hasFocus()) {
        let body = "Conversation finished";
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

  const handleStop = useCallback(async () => {
    await thread.stop();
  }, [thread]);

  const layout = useMemo(
    () => getSubmarineWorkbenchLayout({ chatOpen }),
    [chatOpen],
  );

  const chatRailErrorMessage = thread.error
    ? thread.error instanceof Error
      ? thread.error.message
      : String(thread.error)
    : null;

  return (
    <ThreadContext.Provider value={{ thread, isMock }}>
      <ChatBox threadId={threadId}>
        <div className="relative flex size-full min-h-0 flex-col">
          <header className="bg-background/85 absolute top-0 right-0 left-0 z-30 flex h-14 shrink-0 items-center border-b px-4 backdrop-blur">
            <div className="flex min-w-0 flex-1 items-center gap-2">
              <WavesIcon className="text-muted-foreground size-4 shrink-0" />
              <div className="min-w-0">
                <div className="truncate text-sm font-medium">
                  <ThreadTitle threadId={threadId} thread={thread} />
                </div>
                <div className="text-muted-foreground text-xs">
                  VibeCFD 路 浠跨湡宸ヤ綔鍙?
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                className="xl:hidden"
                onClick={() => setChatOpen((open) => !open)}
              >
                <MessageSquareIcon className="size-4" />
                {chatOpen ? "鏀惰捣鑱婂ぉ" : "灞曞紑鑱婂ぉ"}
              </Button>
              <TokenUsageIndicator messages={thread.messages} />
              <ExportTrigger threadId={threadId} />
              <ArtifactTrigger />
            </div>
          </header>

          <main className="min-h-0 flex-1 overflow-hidden pt-14">
            <div className="mx-auto flex h-full min-h-0 w-full max-w-none flex-col px-4 py-4">
              <div className={layout.shellClassName}>
                <SubmarineWorkbenchShell
                  className={layout.workbenchPaneClassName}
                  threadId={threadId}
                  isNewThread={isNewThread}
                  isUploading={isUploading}
                  isMock={isMock}
                  chatOpen={chatOpen}
                  sendMessage={sendMessage}
                  onStop={handleStop}
                />

                <aside className={layout.chatRailClassName}>
                  <div className={layout.chatRailInnerClassName}>
                    <SubmarinePipelineChatRail
                      thread={thread}
                      pipelineStatus={{
                        agentLabel: "Submarine research supervisor",
                        outputStatus: "Live",
                        runLabel: thread.isLoading ? "Running" : "Ready",
                        summaryText:
                          "Keep the thread conversation available while the runtime cockpit stays focused on the current view.",
                        tone: chatRailErrorMessage
                          ? "error"
                          : thread.isLoading
                            ? "streaming"
                            : "ready",
                        errorBanner: chatRailErrorMessage
                          ? {
                              title: "Thread error",
                              guidance:
                                "Review the latest message and retry from the runtime surface when ready.",
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
