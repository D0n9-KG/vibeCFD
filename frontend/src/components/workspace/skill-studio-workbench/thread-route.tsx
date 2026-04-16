"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  createAgenticWorkbenchSessionModel,
  toggleAgenticWorkbenchMobileNegotiationRailVisible,
} from "@/components/workspace/agentic-workbench/session-model";
import { useArtifacts } from "@/components/workspace/artifacts";
import { ChatBox, useSpecificChatMode } from "@/components/workspace/chats";
import {
  deriveStartedThreadChatState,
  deriveThreadChatRouteState,
} from "@/components/workspace/chats/use-thread-chat.state";
import { ThreadContext } from "@/components/workspace/messages/context";
import {
  buildSkillStudioAgentOptions,
  DEFAULT_SKILL_STUDIO_AGENT,
  normalizeSkillStudioAgentLabel,
  resolveSkillStudioAgentSelection,
} from "@/components/workspace/skill-studio-agent-options";
import { useAgents } from "@/core/agents";
import { useNotification } from "@/core/notification/hooks";
import { useLocalSettings } from "@/core/settings";
import { useThreadStream } from "@/core/threads/hooks";
import { shouldPromoteStartedThreadRoute } from "@/core/threads/use-thread-stream.state";
import { resolveThreadDisplayTitle, textOfMessage } from "@/core/threads/utils";
import { uuid } from "@/core/utils/uuid";
import { env } from "@/env";

import { SkillStudioAgenticWorkbench } from "./index";

type SkillStudioThreadRouteProps = {
  routeThreadId: string;
};

type SkillStudioThreadState = {
  assistant_mode?: string | null;
  assistant_label?: string | null;
};

function buildSkillStudioThreadPath({
  threadId,
  isMock,
  agentName,
}: {
  threadId: string;
  isMock: boolean;
  agentName: string;
}) {
  const params = new URLSearchParams();
  if (env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" || isMock) {
    params.set("mock", "true");
  }
  if (agentName) {
    params.set("agent", agentName);
  }

  return `/workspace/skill-studio/${threadId}${
    params.size > 0 ? `?${params.toString()}` : ""
  }`;
}

export function SkillStudioThreadRoute({
  routeThreadId,
}: SkillStudioThreadRouteProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [settings, setSettings] = useLocalSettings();
  const { agents } = useAgents();
  const { showNotification } = useNotification();
  const { setOpen: setArtifactsOpen, deselect: deselectArtifact } =
    useArtifacts();
  const [threadState, setThreadState] = useState(() =>
    deriveThreadChatRouteState(routeThreadId, uuid),
  );
  const [sessionModel, setSessionModel] = useState(() =>
    createAgenticWorkbenchSessionModel({
      surface: "skill-studio",
      isNewThread: routeThreadId === "new",
    }),
  );
  const [pendingThreadRouteId, setPendingThreadRouteId] = useState<string | null>(
    null,
  );
  const requestedAgentName = searchParams.get("agent");
  const isMock = searchParams.get("mock") === "true";

  useSpecificChatMode();

  useEffect(() => {
    setThreadState(deriveThreadChatRouteState(routeThreadId, uuid));
    setSessionModel(
      createAgenticWorkbenchSessionModel({
        surface: "skill-studio",
        isNewThread: routeThreadId === "new",
      }),
    );
  }, [routeThreadId]);

  useEffect(() => {
    deselectArtifact();
    setArtifactsOpen(false);
  }, [routeThreadId, deselectArtifact, setArtifactsOpen]);

  const { threadId, isNewThread } = threadState;
  const [thread, sendMessage, isUploading, streamMeta] = useThreadStream({
    threadId: isNewThread ? undefined : threadId,
    isNewThread,
    context: settings.context,
    isMock,
    workbenchKind: "skill-studio",
    onStart: (createdThreadId) => {
      setThreadState(deriveStartedThreadChatState(createdThreadId));
      if (isNewThread) {
        setPendingThreadRouteId(createdThreadId);
      }
    },
    onFinish: (state) => {
      if (document.hidden || !document.hasFocus()) {
        const lastMessage = state.messages.at(-1);
        const textContent = lastMessage ? textOfMessage(lastMessage) : "";
        showNotification(
          resolveThreadDisplayTitle(
            state.title,
            "技能工作台会话",
            state.messages,
          ),
          {
            body:
              textContent && textContent.length > 0
                ? textContent.slice(0, 200)
                : "技能工作台线程已完成最新一轮处理。",
          },
        );
      }
    },
  });

  const agentOptions = buildSkillStudioAgentOptions(agents);
  const [selectedAgentName, setSelectedAgentName] = useState<string | null>(
    requestedAgentName,
  );
  const studioState =
    thread.values.submarine_skill_studio != null &&
    typeof thread.values.submarine_skill_studio === "object"
      ? (thread.values.submarine_skill_studio as SkillStudioThreadState)
      : null;
  const persistedAssistantMode =
    typeof studioState?.assistant_mode === "string"
      ? studioState.assistant_mode
      : null;
  const persistedAssistantLabel =
    typeof studioState?.assistant_label === "string"
      ? studioState.assistant_label
      : null;

  useEffect(() => {
    setSelectedAgentName((current) =>
      resolveSkillStudioAgentSelection({
        selectedAgentName: current ?? requestedAgentName,
        persistedAssistantMode,
        options: agentOptions,
      }),
    );
  }, [agentOptions, persistedAssistantMode, requestedAgentName]);

  useEffect(() => {
    if (
      !shouldPromoteStartedThreadRoute({
        pendingThreadId: pendingThreadRouteId,
        activeThreadId: threadId,
        isLoading: thread.isLoading,
        persistedMessageCount: streamMeta.persistedMessageCount,
        visibleMessageCount: thread.messages.length,
      }) ||
      pendingThreadRouteId == null
    ) {
      return;
    }

    router.replace(
      buildSkillStudioThreadPath({
        threadId: pendingThreadRouteId,
        isMock,
        agentName: selectedAgentName ?? DEFAULT_SKILL_STUDIO_AGENT,
      }),
    );
    setPendingThreadRouteId(null);
  }, [
    isMock,
    pendingThreadRouteId,
    router,
    selectedAgentName,
    threadId,
    thread.messages.length,
    streamMeta.persistedMessageCount,
    thread.isLoading,
  ]);

  const activeAgentName = selectedAgentName ?? DEFAULT_SKILL_STUDIO_AGENT;
  const activeAgentOption =
    agentOptions.find((option) => option.name === activeAgentName) ?? null;
  const activeAssistantLabel = normalizeSkillStudioAgentLabel(
    persistedAssistantLabel ?? activeAgentOption?.label,
    activeAgentName,
  );

  const handleSubmit = useCallback(
    (message: Parameters<typeof sendMessage>[1]) => {
      void sendMessage(threadId, message, {
        agent_name: activeAgentName,
      });
    },
    [activeAgentName, sendMessage, threadId],
  );

  const handleStop = useCallback(async () => {
    await thread.stop();
  }, [thread]);

  return (
    <ThreadContext.Provider value={{ thread, isMock }}>
      <ChatBox threadId={threadId}>
        <div className="flex size-full min-h-0 flex-col overflow-hidden">
          <main className="min-h-0 flex-1 overflow-hidden">
            <div className="mx-auto flex h-full w-full max-w-[1720px] flex-col px-4 py-4 md:px-5">
              <SkillStudioAgenticWorkbench
          threadId={threadId}
          isNewThread={isNewThread}
          activeAgentName={activeAgentName}
          activeAssistantLabel={activeAssistantLabel}
          assistantDescription={
            activeAgentOption?.description ??
            `${activeAssistantLabel} 负责这条技能生命周期线程中的定义整理、验证试跑与发布协商。`
          }
          agentOptions={agentOptions}
          agentSelectionLocked={!isNewThread || persistedAssistantMode != null}
          agentSelectorEnabled={agentOptions.length > 0}
          onAgentChange={setSelectedAgentName}
          mobileNegotiationRailVisible={sessionModel.mobileNegotiationRailVisible}
          onToggleChatRail={() =>
            setSessionModel((model) =>
              toggleAgenticWorkbenchMobileNegotiationRailVisible(model),
            )
          }
          isUploading={
            env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" || isUploading
          }
          context={settings.context}
          onContextChange={(context) => setSettings("context", context)}
          onSubmit={handleSubmit}
          onStop={handleStop}
              />
            </div>
          </main>
        </div>
      </ChatBox>
    </ThreadContext.Provider>
  );
}
