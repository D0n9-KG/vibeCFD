"use client";

import {
  ArrowLeftIcon,
  FileOutputIcon,
  FileUpIcon,
  MessageSquareIcon,
  ShipWheelIcon,
  WorkflowIcon,
} from "lucide-react";
import Link from "next/link";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ComponentType,
} from "react";

import { type PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { Button } from "@/components/ui/button";
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
import { SubmarineRuntimePanel } from "@/components/workspace/submarine-runtime-panel";
import { ThreadTitle } from "@/components/workspace/thread-title";
import { TokenUsageIndicator } from "@/components/workspace/token-usage-indicator";
import { useNotification } from "@/core/notification/hooks";
import { useLocalSettings } from "@/core/settings";
import { useThreadStream } from "@/core/threads/hooks";
import { textOfMessage } from "@/core/threads/utils";
import { env } from "@/env";

import { getSubmarineWorkbenchLayout } from "../submarine-workbench-layout";

export default function SubmarineWorkbenchPage() {
  const [settings, setSettings] = useLocalSettings();
  const { threadId, isNewThread, setIsNewThread, isMock } = useThreadChat();
  const { showNotification } = useNotification();
  const { setOpen: setArtifactsOpen } = useArtifacts();
  const [chatOpen, setChatOpen] = useState(true);

  useSpecificChatMode();

  useEffect(() => {
    setArtifactsOpen(false);
  }, [setArtifactsOpen]);

  const [thread, sendMessage, isUploading] = useThreadStream({
    threadId: isNewThread ? undefined : threadId,
    context: settings.context,
    isMock,
    onStart: () => {
      setIsNewThread(false);
      const nextPath = isMock
        ? `/workspace/submarine/${threadId}?mock=true`
        : `/workspace/submarine/${threadId}`;
      history.replaceState(null, "", nextPath);
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

  const layout = useMemo(
    () => getSubmarineWorkbenchLayout({ chatOpen }),
    [chatOpen],
  );

  const hasSubmarineRuntime =
    thread.values.submarine_runtime != null &&
    typeof thread.values.submarine_runtime === "object";
  const hasSubmarineArtifacts =
    Array.isArray(thread.values.artifacts) &&
    thread.values.artifacts.some(
      (artifact) =>
        typeof artifact === "string" && artifact.includes("/submarine/"),
    );
  const hasCfdArtifacts =
    Array.isArray(thread.values.artifacts) &&
    thread.values.artifacts.some(
      (artifact) =>
        typeof artifact === "string" &&
        artifact.includes("/submarine/") &&
        !artifact.includes("/submarine/skill-studio/"),
    );
  const hasRuntimeWorkbench = !isNewThread && (hasSubmarineRuntime || hasCfdArtifacts);
  const hasWorkbenchSurface =
    !isNewThread && (hasSubmarineRuntime || hasSubmarineArtifacts);

  const handleSubmit = useCallback(
    (message: PromptInputMessage) => {
      void sendMessage(threadId, message);
    },
    [sendMessage, threadId],
  );

  const handleStop = useCallback(async () => {
    await thread.stop();
  }, [thread]);

  const focusChatRail = useCallback(() => {
    if (!chatOpen) {
      setChatOpen(true);
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
  }, [chatOpen]);

  const chatHref = isMock
    ? `/workspace/chats/${threadId}?mock=true`
    : `/workspace/chats/${threadId}`;

  return (
    <ThreadContext.Provider value={{ thread, isMock }}>
      <ChatBox threadId={threadId}>
        <div className="relative flex size-full min-h-0 flex-col">
          <header className="absolute top-0 right-0 left-0 z-30 flex h-14 shrink-0 items-center border-b bg-background/85 px-4 backdrop-blur">
            <div className="flex min-w-0 flex-1 items-center gap-3">
              <Button asChild size="sm" variant="ghost">
                <Link href={chatHref}>
                  <ArrowLeftIcon className="size-4" />
                  聊天视图
                </Link>
              </Button>
              <div className="min-w-0">
                <div className="truncate text-sm font-medium">
                  <ThreadTitle threadId={threadId} thread={thread} />
                </div>
                <div className="text-xs text-muted-foreground">
                  潜艇 CFD 工作台
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setChatOpen((open) => !open)}
              >
                <MessageSquareIcon className="size-4" />
                {chatOpen ? "收起聊天" : "展开聊天"}
              </Button>
              <TokenUsageIndicator messages={thread.messages} />
              <ExportTrigger threadId={threadId} />
              <ArtifactTrigger />
            </div>
          </header>

          <main className="min-h-0 flex-1 overflow-hidden pt-14">
            <div className="mx-auto flex h-full w-full max-w-none min-h-0 flex-col px-4 py-4">
              <div className={layout.shellClassName} data-submarine-shell>
                <div
                  className={layout.workbenchPaneClassName}
                  data-submarine-workbench
                >
                  <SubmarineLaunchpad
                    hasRuntimeWorkbench={hasWorkbenchSurface}
                    isNewThread={isNewThread}
                    onOpenChat={focusChatRail}
                  />
                  {hasRuntimeWorkbench ? (
                    <div className="space-y-4">
                      <SubmarineRuntimePanel threadId={threadId} />
                    </div>
                  ) : (
                    <RuntimePlaceholder />
                  )}
                </div>

                <aside
                  id="submarine-chat-rail"
                  data-submarine-chat-rail
                  className={layout.chatRailClassName}
                >
                  <div className={layout.chatRailInnerClassName}>
                    <div className="border-b bg-muted/20 px-4 py-4">
                      <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                        <MessageSquareIcon className="size-4 text-muted-foreground" />
                        与 Claude Code 共创 CFD 方案
                      </div>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">
                        在这里持续上传几何、说明计算目标、修正工况和交付要求。
                        中间工作台会实时同步设计简报、执行状态、结果和产物。
                      </p>
                    </div>

                    <div className="min-h-0 flex-1 overflow-hidden">
                      <MessageList
                        className="flex-1 justify-start"
                        paddingBottom={32}
                        threadId={threadId}
                        thread={thread}
                      />
                    </div>

                    <div className="border-t bg-background p-3">
                      <InputBox
                        className="w-full bg-background"
                        isNewThread={isNewThread}
                        threadId={threadId}
                        autoFocus={isNewThread}
                        status={
                          thread.error
                            ? "error"
                            : thread.isLoading
                              ? "streaming"
                              : "ready"
                        }
                        context={settings.context}
                        disabled={
                          env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" ||
                          isUploading
                        }
                        onContextChange={(context) =>
                          setSettings("context", context)
                        }
                        onSubmit={handleSubmit}
                        onStop={handleStop}
                      />
                    </div>
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

function SubmarineLaunchpad({
  hasRuntimeWorkbench,
  isNewThread,
  onOpenChat,
}: {
  hasRuntimeWorkbench: boolean;
  isNewThread: boolean;
  onOpenChat: () => void;
}) {
  return (
    <section className="rounded-2xl border bg-muted/20 p-5">
      <div className="mb-3 flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
        <ShipWheelIcon className="size-4" />
        Submarine CFD Workspace
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.7fr)]">
        <div className="space-y-3">
          <h1 className="text-2xl font-semibold text-foreground">
            用对话方式推进一次完整的潜艇 CFD run
          </h1>
          <p className="max-w-4xl text-sm leading-7 text-muted-foreground">
            右侧是与你和 Claude Code 共创计算方案的实时协作栏，中心工作台负责把设计简报、
            几何检查、求解执行、结果整理和 artifact 交付同步展示在同一个线程里。
          </p>
          <div className="flex flex-wrap gap-2">
            <Button onClick={onOpenChat}>
              <MessageSquareIcon className="size-4" />
              {isNewThread ? "开始和 Claude Code 讨论方案" : "继续调整计算方案"}
            </Button>
          </div>
        </div>

        <div className="rounded-xl border bg-background/70 p-4">
          <div className="mb-3 text-sm font-medium text-foreground">
            当前协作方式
          </div>
          <div className="space-y-3">
            <CollaborationStep
              icon={FileUpIcon}
              title="上传几何与目标"
              description="通过右侧聊天栏上传 .stl，并直接告诉 Claude Code 计算目的。"
            />
            <CollaborationStep
              icon={WorkflowIcon}
              title="共创并确认方案"
              description="Claude Code 负责梳理计算条件、结果要求和执行分工，工作台实时镜像最新方案。"
            />
            <CollaborationStep
              icon={FileOutputIcon}
              title="执行与交付"
              description={
                hasRuntimeWorkbench
                  ? "当前线程已经开始沉淀运行数据，下方可继续查看执行状态、结果与交付物。"
                  : "确认方案后，执行过程、日志、结果和报告都会回到这个工作台。"
              }
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function RuntimePlaceholder() {
  return (
    <section className="rounded-2xl border border-dashed bg-background/60 p-8">
      <div className="max-w-3xl">
        <h2 className="text-lg font-semibold text-foreground">
          等待第一次潜艇 CFD run
        </h2>
        <p className="mt-3 text-sm leading-7 text-muted-foreground">
          先在右侧和 Claude Code 讨论几何、任务目标、工况和交付要求。随着设计简报逐步成形，
          这个工作台会开始显示案例匹配、执行状态、结果指标和最终报告。
        </p>
      </div>
    </section>
  );
}

function CollaborationStep({
  icon: Icon,
  title,
  description,
}: {
  icon: ComponentType<{ className?: string }>;
  title: string;
  description: string;
}) {
  return (
    <div className="flex gap-3">
      <div className="mt-0.5 rounded-lg border bg-muted/40 p-2">
        <Icon className="size-4 text-muted-foreground" />
      </div>
      <div className="min-w-0">
        <div className="text-sm font-medium text-foreground">{title}</div>
        <div className="mt-1 text-sm leading-6 text-muted-foreground">
          {description}
        </div>
      </div>
    </div>
  );
}
