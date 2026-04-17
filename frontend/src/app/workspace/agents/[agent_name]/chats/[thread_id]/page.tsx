"use client";

import { LayoutPanelLeftIcon, PlusSquareIcon } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { Button } from "@/components/ui/button";
import { AgentWelcome } from "@/components/workspace/agent-welcome";
import { ArtifactTrigger } from "@/components/workspace/artifacts";
import { ChatBox, useThreadChat } from "@/components/workspace/chats";
import { ExportTrigger } from "@/components/workspace/export-trigger";
import { InputBox } from "@/components/workspace/input-box";
import { MessageList } from "@/components/workspace/messages";
import { ThreadContext } from "@/components/workspace/messages/context";
import { ThreadTitle } from "@/components/workspace/thread-title";
import { TodoList } from "@/components/workspace/todo-list";
import { TokenUsageIndicator } from "@/components/workspace/token-usage-indicator";
import { WorkspaceStatePanel } from "@/components/workspace/workspace-state-panel";
import { useAgent } from "@/core/agents";
import {
  getAgentDisplayName,
  getAgentModelLabel,
  getAgentToolGroupLabel,
} from "@/core/agents/display";
import { useI18n } from "@/core/i18n/hooks";
import { useNotification } from "@/core/notification/hooks";
import { useLocalSettings } from "@/core/settings";
import { useThreadStream } from "@/core/threads/hooks";
import { shouldPromoteStartedThreadRoute } from "@/core/threads/use-thread-stream.state";
import { resolveThreadDisplayTitle, textOfMessage } from "@/core/threads/utils";
import { env } from "@/env";
import { cn } from "@/lib/utils";

import { getChatPageLayout } from "../../../../chats/chat-layout";

const AGENTS_SURFACE_LABEL = "智能体";
const AGENTS_MANAGEMENT_HREF = "/workspace/control-center?tab=agents";

export default function AgentChatPage() {
  const { t } = useI18n();
  const [settings, setSettings] = useLocalSettings();
  const router = useRouter();
  const [supportPanelOpen, setSupportPanelOpen] = useState(false);
  const [pendingThreadRouteId, setPendingThreadRouteId] = useState<
    string | null
  >(null);

  const { agent_name } = useParams<{
    agent_name: string;
  }>();
  const { agent, error: agentError } = useAgent(agent_name);
  const { threadId, isNewThread, markThreadStarted } = useThreadChat();
  const { showNotification } = useNotification();

  const [thread, sendMessage, isUploading, streamMeta] = useThreadStream({
    threadId: isNewThread ? undefined : threadId,
    isNewThread,
    context: { ...settings.context, agent_name },
    onStart: (createdThreadId) => {
      markThreadStarted(createdThreadId);
      if (isNewThread) {
        setPendingThreadRouteId(createdThreadId);
      }
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
        showNotification(
          resolveThreadDisplayTitle(state.title, t.pages.untitled, state.messages),
          { body },
        );
      }
    },
  });

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

    router.replace(
      `/workspace/agents/${agent_name}/chats/${pendingThreadRouteId}`,
    );
    setPendingThreadRouteId(null);
  }, [
    agent_name,
    pendingThreadRouteId,
    router,
    threadId,
    thread.messages.length,
    streamMeta.persistedMessageCount,
    thread.isLoading,
  ]);

  const handleSubmit = useCallback(
    (message: PromptInputMessage) => {
      void sendMessage(threadId, message, { agent_name });
    },
    [agent_name, sendMessage, threadId],
  );

  const handleStop = useCallback(async () => {
    await thread.stop();
  }, [thread]);

  const layout = getChatPageLayout({
    hasRuntimeWorkbench: false,
    isNewThread,
    supportPanelOpen,
  });
  const todoCount = Array.isArray(thread.values.todos)
    ? thread.values.todos.length
    : 0;
  const artifactCount = Array.isArray(thread.values.artifacts)
    ? thread.values.artifacts.length
    : 0;
  const threadErrorMessage =
    thread.error instanceof Error
      ? thread.error.message
      : typeof thread.error === "string"
        ? thread.error
        : null;
  const threadLabel =
    isNewThread && (!thread.values.title || thread.values.title === "Untitled")
      ? t.pages.newChat
      : resolveThreadDisplayTitle(
          thread.values.title,
          t.pages.untitled,
          thread.values.messages,
        );
  const agentDisplayName = getAgentDisplayName(agent, agent_name);

  return (
    <ThreadContext.Provider value={{ thread }}>
      <ChatBox threadId={threadId}>
        <div
          className="relative flex size-full min-h-0 flex-col bg-[radial-gradient(circle_at_top,_rgba(251,191,36,0.08),_transparent_28%),linear-gradient(180deg,_rgba(247,244,238,0.96),_rgba(255,255,255,0.98))]"
          data-surface-label={AGENTS_SURFACE_LABEL}
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
                  {agentDisplayName}
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
              <Button
                size="sm"
                variant="outline"
                onClick={() => router.push(`/workspace/agents/${agent_name}/chats/new`)}
              >
                <PlusSquareIcon className="size-4" />
                {t.agents.newChat}
              </Button>
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
                      {AGENTS_SURFACE_LABEL}
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-stone-500">
                      <span className="rounded-full border border-stone-200/80 bg-white px-2.5 py-1 font-medium text-stone-700">
                        {agentDisplayName}
                      </span>
                      <span className="rounded-full border border-stone-200/80 bg-white px-2.5 py-1 font-medium text-stone-700">
                        {t.common.messageCount(thread.messages.length)}
                      </span>
                      <span className="rounded-full border border-stone-200/80 bg-white px-2.5 py-1 font-medium text-stone-700">
                        {t.common.artifactCount(artifactCount)}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-stone-600">
                      {t.agents.collaborationDescription}
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
                          isNewThread ? (
                            <AgentWelcome agent={agent} agentName={agent_name} />
                          ) : null
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
                      {agentError ? (
                        <WorkspaceStatePanel
                          state="update-failed"
                          description={
                            agentError instanceof Error
                              ? agentError.message
                              : t.agents.agentProfileRefreshError
                          }
                          actions={[
                            {
                              label: t.workspace.retryUpdate,
                              onClick: () => window.location.reload(),
                            },
                          ]}
                        />
                      ) : null}

                      {threadErrorMessage ? (
                        <WorkspaceStatePanel
                          state="data-interrupted"
                          description={threadErrorMessage}
                          actions={[
                            {
                              label: t.workspace.retryUpdate,
                              onClick: () => window.location.reload(),
                            },
                          ]}
                        />
                      ) : null}

                      <div className="rounded-[24px] border border-stone-200/80 bg-stone-50/80 p-4">
                        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-700">
                          {t.agents.profileLabel}
                        </div>
                        <h2 className="mt-2 text-lg font-semibold tracking-tight text-stone-900">
                          {agentDisplayName}
                        </h2>
                        <p className="mt-2 text-sm leading-6 text-stone-600">
                          {agent?.description ??
                            t.agents.profileFallbackDescription}
                        </p>
                        {agent?.model ? (
                          <div className="mt-3 rounded-full border border-stone-200/80 bg-white px-3 py-1 text-xs font-medium text-stone-600">
                            {getAgentModelLabel(agent.model)}
                          </div>
                        ) : null}
                      </div>

                      <div className="rounded-[24px] border border-stone-200/80 bg-white/92 p-4">
                        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-stone-500">
                          {t.agents.actionsLabel}
                        </div>
                        <div className="mt-4 flex flex-wrap gap-2">
                          <Button
                            onClick={() =>
                              router.push(`/workspace/agents/${agent_name}/chats/new`)
                            }
                          >
                            {t.agents.newChat}
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => router.push(AGENTS_MANAGEMENT_HREF)}
                          >
                            {t.workspace.backToOverview}
                          </Button>
                        </div>
                      </div>

                      <div className="rounded-[24px] border border-stone-200/80 bg-white/92 p-4">
                        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-stone-500">
                          {t.agents.sessionSnapshotLabel}
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
                            label={t.agents.toolGroupsLabel}
                            value={String(agent?.tool_groups?.length ?? 0)}
                          />
                        </div>
                      </div>

                      {agent?.tool_groups?.length ? (
                        <div className="rounded-[24px] border border-stone-200/80 bg-stone-50/80 p-4">
                          <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-stone-500">
                            {t.agents.capabilitiesLabel}
                          </div>
                          <div className="mt-3 flex flex-wrap gap-2">
                            {agent.tool_groups.map((group) => (
                              <span
                                key={group}
                                className="rounded-full border border-stone-200/80 bg-white px-3 py-1 text-xs font-medium text-stone-600"
                              >
                                {getAgentToolGroupLabel(group)}
                              </span>
                            ))}
                          </div>
                        </div>
                      ) : null}
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
