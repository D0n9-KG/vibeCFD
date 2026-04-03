"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LayoutPanelLeftIcon, WavesIcon } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { type PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { Button } from "@/components/ui/button";
import { ArtifactTrigger } from "@/components/workspace/artifacts";
import {
  ChatBox,
  useSpecificChatMode,
  useThreadChat,
} from "@/components/workspace/chats";
import { ExportTrigger } from "@/components/workspace/export-trigger";
import { InputBox } from "@/components/workspace/input-box";
import { MessageList } from "@/components/workspace/messages";
import { ThreadContext } from "@/components/workspace/messages/context";
import { ThreadTitle } from "@/components/workspace/thread-title";
import { TodoList } from "@/components/workspace/todo-list";
import { TokenUsageIndicator } from "@/components/workspace/token-usage-indicator";
import { Welcome } from "@/components/workspace/welcome";
import { WorkspaceStatePanel } from "@/components/workspace/workspace-state-panel";
import { useI18n } from "@/core/i18n/hooks";
import { useNotification } from "@/core/notification/hooks";
import { useLocalSettings } from "@/core/settings";
import { useThreadStream } from "@/core/threads/hooks";
import { textOfMessage } from "@/core/threads/utils";
import { env } from "@/env";
import { cn } from "@/lib/utils";

import { getChatPageLayout } from "../chat-layout";

const CHAT_SURFACE_LABEL = "对话";

export default function ChatPage() {
  const { t } = useI18n();
  const [settings, setSettings] = useLocalSettings();
  const router = useRouter();
  const { threadId, isNewThread, markThreadStarted, isMock } = useThreadChat();
  const { showNotification } = useNotification();
  const [supportPanelOpen, setSupportPanelOpen] = useState(false);

  useSpecificChatMode();

  const [thread, sendMessage, isUploading] = useThreadStream({
    threadId: isNewThread ? undefined : threadId,
    isNewThread,
    context: settings.context,
    isMock,
    onStart: (createdThreadId) => {
      markThreadStarted(createdThreadId);
      router.replace(`/workspace/chats/${createdThreadId}`);
    },
    onFinish: (state) => {
      if (document.hidden || !document.hasFocus()) {
        let body = "对话已结束";
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

  const handleSubmit = useCallback(
    (message: PromptInputMessage) => {
      void sendMessage(threadId, message);
    },
    [sendMessage, threadId],
  );

  const handleStop = useCallback(async () => {
    await thread.stop();
  }, [thread]);

  const hasSubmarineRuntime =
    thread.values.submarine_runtime != null &&
    typeof thread.values.submarine_runtime === "object";
  const hasSubmarineArtifacts =
    Array.isArray(thread.values.artifacts) &&
    thread.values.artifacts.some(
      (artifact) =>
        typeof artifact === "string" && artifact.includes("/submarine/"),
    );
  const hasRuntimeWorkbench =
    !isNewThread && (hasSubmarineRuntime || hasSubmarineArtifacts);

  useEffect(() => {
    if (hasRuntimeWorkbench) {
      setSupportPanelOpen(true);
    }
  }, [hasRuntimeWorkbench]);

  const layout = getChatPageLayout({
    hasRuntimeWorkbench,
    isNewThread,
    supportPanelOpen,
  });

  const runtimeHref = isMock
    ? `/workspace/submarine/${threadId}?mock=true`
    : `/workspace/submarine/${threadId}`;
  const artifactCount = Array.isArray(thread.values.artifacts)
    ? thread.values.artifacts.length
    : 0;
  const todoCount = Array.isArray(thread.values.todos)
    ? thread.values.todos.length
    : 0;
  const threadErrorMessage =
    thread.error instanceof Error
      ? thread.error.message
      : thread.error
        ? String(thread.error)
        : null;
  const threadLabel = thread.values.title ?? (isNewThread ? t.pages.newChat : t.pages.untitled);

  return (
    <ThreadContext.Provider value={{ thread, isMock }}>
      <ChatBox threadId={threadId}>
        <div
          className="relative flex size-full min-h-0 flex-col bg-[radial-gradient(circle_at_top,_rgba(251,191,36,0.08),_transparent_28%),linear-gradient(180deg,_rgba(247,244,238,0.96),_rgba(255,255,255,0.98))]"
          data-surface-label={CHAT_SURFACE_LABEL}
        >
          <header className="bg-background/85 absolute inset-x-0 top-0 z-30 flex h-14 shrink-0 items-center border-b px-4 backdrop-blur">
            <div className="flex min-w-0 flex-1 items-center gap-3">
              <div className="flex min-w-0 flex-1 flex-col">
                <div className="sr-only">
                  <ThreadTitle threadId={threadId} thread={thread} />
                </div>
                <div className="truncate text-sm font-medium text-stone-900">
                  {threadLabel}
                </div>
                <div className="text-xs text-stone-500">
                  {t.chats.threadMetaLabel}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                className={cn("2xl:hidden", layout.supportToggleClassName)}
                aria-label={t.workspace.toggleWorkspacePanel}
                onClick={() => setSupportPanelOpen((open) => !open)}
              >
                <LayoutPanelLeftIcon className="size-4" />
                {t.common.panel}
              </Button>
              {hasRuntimeWorkbench ? (
                <Button asChild size="sm" variant="outline">
                  <Link href={runtimeHref}>
                    <WavesIcon className="size-4" />
                    {t.workspace.openRuntimeWorkbench}
                  </Link>
                </Button>
              ) : null}
              <TokenUsageIndicator messages={thread.messages} />
              <ExportTrigger threadId={threadId} />
              <ArtifactTrigger />
            </div>
          </header>

          <main className="min-h-0 flex-1 overflow-hidden pt-14">
            <div className="mx-auto flex h-full min-h-0 w-full max-w-[1600px] flex-col px-4 py-4">
              <div className={layout.shellClassName}>
                <section className={layout.contentClassName}>
                  <div className="rounded-[24px] border border-stone-200/80 bg-stone-50/80 px-4 py-4">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-700">
                      {CHAT_SURFACE_LABEL}
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-stone-500">
                      <span className="rounded-full border border-stone-200/80 bg-white px-2.5 py-1 font-medium text-stone-700">
                        {t.common.messageCount(thread.messages.length)}
                      </span>
                      <span className="rounded-full border border-stone-200/80 bg-white px-2.5 py-1 font-medium text-stone-700">
                        {t.common.artifactCount(artifactCount)}
                      </span>
                      <span className="rounded-full border border-stone-200/80 bg-white px-2.5 py-1 font-medium text-stone-700">
                        {t.common.todoCount(todoCount)}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-stone-600">
                      {t.chats.threadSummaryDescription}
                    </p>
                  </div>

                  <div className="min-h-0 flex-1 overflow-hidden">
                    <MessageList
                      className={layout.messageListClassName}
                      threadId={threadId}
                      thread={thread}
                    />
                  </div>

                  <div
                    className={cn(
                      "absolute inset-x-0 z-20 flex justify-center px-4",
                      isNewThread ? "top-0" : "bottom-0 pb-4",
                    )}
                  >
                    <div className={layout.inputShellClassName}>
                      <div className="absolute -top-4 inset-x-0 z-0">
                        <div className="absolute inset-x-0 bottom-0">
                          <TodoList
                            className="bg-background/5"
                            todos={thread.values.todos ?? []}
                            hidden={!todoCount}
                          />
                        </div>
                      </div>
                      <InputBox
                        className="bg-background/80 w-full -translate-y-4 backdrop-blur"
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
                        extraHeader={
                          isNewThread ? <Welcome mode={settings.context.mode} /> : null
                        }
                        disabled={
                          env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" ||
                          isUploading
                        }
                        onContextChange={(context) => setSettings("context", context)}
                        onSubmit={handleSubmit}
                        onStop={handleStop}
                      />
                      {env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" ? (
                        <div className="w-full translate-y-12 text-center text-xs text-stone-500">
                          {t.common.notAvailableInDemoMode}
                        </div>
                      ) : null}
                    </div>
                  </div>
                </section>

                <aside className={layout.supportPanelClassName}>
                  <div className={layout.supportPanelInnerClassName}>
                    <div className="flex-1 space-y-4 overflow-y-auto p-4">
                      {threadErrorMessage ? (
                        <WorkspaceStatePanel
                          state="data-interrupted"
                          description={threadErrorMessage}
                          actions={[
                            {
                              label: t.workspace.retryUpdate,
                              onClick: () => window.location.reload(),
                            },
                            {
                              label: t.workspace.backToOverview,
                              href: "/workspace/chats",
                              variant: "ghost",
                            },
                          ]}
                        />
                      ) : null}

                      <div className="rounded-[24px] border border-stone-200/80 bg-stone-50/80 p-4">
                        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-700">
                          {t.chats.workspaceContextLabel}
                        </div>
                        <h2 className="mt-2 text-lg font-semibold tracking-tight text-stone-900">
                          {threadLabel}
                        </h2>
                        <p className="mt-2 text-sm leading-6 text-stone-600">
                          {t.chats.workspaceContextDescription}
                        </p>
                      </div>

                      {hasRuntimeWorkbench ? (
                        <div className="rounded-[24px] border border-sky-200/80 bg-[linear-gradient(135deg,rgba(239,246,255,0.96),rgba(255,255,255,0.98))] p-4">
                          <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-sky-700">
                            {t.chats.runtimeHandoffLabel}
                          </div>
                          <p className="mt-2 text-sm leading-6 text-sky-950">
                            {t.chats.runtimeHandoffDescription}
                          </p>
                          <Button asChild className="mt-4">
                            <Link href={runtimeHref}>
                              <WavesIcon className="size-4" />
                              {t.workspace.openRuntimeWorkbench}
                            </Link>
                          </Button>
                        </div>
                      ) : (
                        <div className="rounded-[24px] border border-dashed border-stone-300 bg-white/80 p-4">
                          <div className="text-sm font-semibold text-stone-900">
                            {t.chats.conversationFirstTitle}
                          </div>
                          <p className="mt-2 text-sm leading-6 text-stone-600">
                            {t.chats.conversationFirstDescription}
                          </p>
                        </div>
                      )}

                      <div className="rounded-[24px] border border-stone-200/80 bg-white/92 p-4">
                        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-stone-500">
                          {t.chats.sessionSnapshotLabel}
                        </div>
                        <div className="mt-3 grid gap-3 sm:grid-cols-2">
                          <SnapshotMetric
                            label={t.common.messages}
                            value={String(thread.messages.length)}
                          />
                          <SnapshotMetric
                            label={t.common.artifacts}
                            value={String(artifactCount)}
                          />
                          <SnapshotMetric label={t.common.todos} value={String(todoCount)} />
                          <SnapshotMetric
                            label={t.common.status}
                            value={
                              thread.error
                                ? t.common.interrupted
                                : thread.isLoading
                                  ? t.common.running
                                  : t.common.ready
                            }
                          />
                        </div>
                      </div>
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

function SnapshotMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-stone-200/80 bg-stone-50/80 px-3 py-3">
      <div className="text-[11px] uppercase tracking-[0.18em] text-stone-500">
        {label}
      </div>
      <div className="mt-2 text-sm font-semibold text-stone-900">{value}</div>
    </div>
  );
}
