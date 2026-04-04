"use client";

import {
  ArrowLeftIcon,
  MessageSquareIcon,
  WandSparklesIcon,
} from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { type PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import { InputBox } from "@/components/workspace/input-box";
import { MessageList } from "@/components/workspace/messages";
import { ThreadContext } from "@/components/workspace/messages/context";
import {
  buildSkillStudioAgentOptions,
  DEFAULT_SKILL_STUDIO_AGENT,
  normalizeSkillStudioAgentLabel,
  resolveSkillStudioAgentSelection,
} from "@/components/workspace/skill-studio-agent-options";
import { SkillStudioWorkbenchShell } from "@/components/workspace/skill-studio-workbench-shell";
import { ThreadTitle } from "@/components/workspace/thread-title";
import { TokenUsageIndicator } from "@/components/workspace/token-usage-indicator";
import { useAgents } from "@/core/agents";
import { localizeWorkspaceDisplayText } from "@/core/i18n/workspace-display";
import { useNotification } from "@/core/notification/hooks";
import { useLocalSettings } from "@/core/settings";
import { useThreadStream } from "@/core/threads/hooks";
import { shouldPromoteStartedThreadRoute } from "@/core/threads/use-thread-stream.state";
import { textOfMessage } from "@/core/threads/utils";
import { env } from "@/env";

import { getSkillStudioWorkbenchLayout } from "../skill-studio-workbench-layout";

const SKILL_STUDIO_BUILTIN_SKILLS = ["skill-creator", "writing-skills"];

type SkillStudioThreadState = {
  assistant_mode?: string | null;
  assistant_label?: string | null;
};

function withMock(path: string, isMock: boolean) {
  return env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" || isMock
    ? `${path}?mock=true`
    : path;
}

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

export default function SkillStudioWorkbenchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [settings, setSettings] = useLocalSettings();
  const { threadId, isNewThread, markThreadStarted, isMock } = useThreadChat();
  const { agents } = useAgents();
  const { showNotification } = useNotification();
  const { setOpen: setArtifactsOpen } = useArtifacts();
  const [chatOpen, setChatOpen] = useState(true);
  const [pendingThreadRouteId, setPendingThreadRouteId] = useState<
    string | null
  >(null);

  useSpecificChatMode();

  useEffect(() => {
    setArtifactsOpen(false);
  }, [setArtifactsOpen]);

  const agentOptions = useMemo(
    () => buildSkillStudioAgentOptions(agents),
    [agents],
  );
  const requestedAgentName = searchParams.get("agent");
  const [selectedAgentName, setSelectedAgentName] = useState<string | null>(
    requestedAgentName,
  );

  const [thread, sendMessage, isUploading, streamMeta] = useThreadStream({
    threadId: isNewThread ? undefined : threadId,
    isNewThread,
    context: settings.context,
    isMock,
    workbenchKind: "skill-studio",
    onStart: (createdThreadId) => {
      markThreadStarted(createdThreadId);
      if (isNewThread) {
        setPendingThreadRouteId(createdThreadId);
      }
    },
    onFinish: (state) => {
      if (document.hidden || !document.hasFocus()) {
        let body = "技能工作台线程已结束";
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

    const nextThreadId = pendingThreadRouteId;
    if (nextThreadId == null) {
      return;
    }
    router.replace(
      buildSkillStudioThreadPath({
        threadId: nextThreadId,
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
    streamMeta.persistedMessageCount,
    thread.isLoading,
  ]);

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

  const activeAgentName = selectedAgentName ?? DEFAULT_SKILL_STUDIO_AGENT;
  const activeAgentOption =
    agentOptions.find((option) => option.name === activeAgentName) ?? null;
  const activeAssistantLabel = normalizeSkillStudioAgentLabel(
    persistedAssistantLabel ?? activeAgentOption?.label,
    activeAgentName,
  );
  const agentSelectionLocked = !isNewThread || persistedAssistantMode != null;
  const agentSelectorEnabled = agentOptions.length > 0;

  const layout = useMemo(
    () => getSkillStudioWorkbenchLayout({ chatOpen }),
    [chatOpen],
  );

  const hasSkillStudioState = studioState != null;
  const hasSkillStudioArtifacts =
    Array.isArray(thread.values.artifacts) &&
    thread.values.artifacts.some(
      (artifact) =>
        typeof artifact === "string" &&
        artifact.includes("/submarine/skill-studio/"),
    );
  const hasWorkbenchSurface =
    !isNewThread && (hasSkillStudioState || hasSkillStudioArtifacts);

  const handleSubmit = useCallback(
    (message: PromptInputMessage) => {
      void sendMessage(threadId, message, {
        agent_name: activeAgentName,
      });
    },
    [activeAgentName, sendMessage, threadId],
  );

  const handleStop = useCallback(async () => {
    await thread.stop();
  }, [thread]);

  const focusChatRail = useCallback(() => {
    if (!chatOpen) {
      setChatOpen(true);
      window.setTimeout(() => {
        const rail = document.getElementById("skill-studio-chat-rail");
        rail?.scrollIntoView({ behavior: "smooth", block: "start" });
        const input = rail?.querySelector("textarea");
        if (input instanceof HTMLTextAreaElement) {
          input.focus();
        }
      }, 50);
      return;
    }

    const rail = document.getElementById("skill-studio-chat-rail");
    rail?.scrollIntoView({ behavior: "smooth", block: "start" });
    const input = rail?.querySelector("textarea");
    if (input instanceof HTMLTextAreaElement) {
      input.focus();
    }
  }, [chatOpen]);

  const dashboardHref = withMock("/workspace/skill-studio", isMock);
  const selectionHint = agentSelectionLocked
    ? "线程开始后会锁定代理身份，避免技能包上下文在中途漂移。"
    : "请在第一次提交前确认技能创建器身份。";
  const assistantDescription =
    activeAgentOption?.description ??
    `${activeAssistantLabel} 负责当前技能工作台线程中的起草、校验、测试与发布收口。`;

  return (
    <ThreadContext.Provider value={{ thread, isMock }}>
      <ChatBox threadId={threadId}>
        <div className="relative flex size-full min-h-0 flex-col">
          <header className="bg-background/85 absolute top-0 right-0 left-0 z-30 flex h-14 shrink-0 items-center border-b px-4 backdrop-blur">
            <div className="flex min-w-0 flex-1 items-center gap-3">
              <Button asChild size="sm" variant="ghost">
                <Link href={dashboardHref}>
                  <ArrowLeftIcon className="size-4" />
                  返回技能工作台
                </Link>
              </Button>
              <div className="min-w-0">
                <div className="truncate text-sm font-medium">
                  <ThreadTitle threadId={threadId} thread={thread} />
                </div>
                <div className="text-muted-foreground text-xs">
                  领域专家 · 技能创建工作台
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="hidden lg:inline-flex">
                {activeAssistantLabel}
              </Badge>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setChatOpen((open) => !open)}
              >
                <MessageSquareIcon className="size-4" />
                {chatOpen ? "收起对话" : "展开对话"}
              </Button>
              <TokenUsageIndicator messages={thread.messages} />
              <ExportTrigger threadId={threadId} />
              <ArtifactTrigger />
            </div>
          </header>

          <main className="min-h-0 flex-1 overflow-hidden pt-14">
            <div className="mx-auto flex h-full min-h-0 w-full max-w-none flex-col px-4 py-4">
              <div className={layout.shellClassName}>
                <SkillStudioWorkbenchShell
                  className={layout.workbenchPaneClassName}
                  threadId={threadId}
                  assistantLabel={activeAssistantLabel}
                  hasWorkbenchSurface={hasWorkbenchSurface}
                  isNewThread={isNewThread}
                  onOpenChat={focusChatRail}
                />

                <aside id="skill-studio-chat-rail" className={layout.chatRailClassName}>
                  <div className={layout.chatRailInnerClassName}>
                    <div className="bg-muted/20 border-b px-4 py-4">
                      <div className="text-foreground flex items-center gap-2 text-sm font-medium">
                        <WandSparklesIcon className="text-muted-foreground size-4" />
                        {activeAssistantLabel}
                      </div>
                      <p className="text-muted-foreground mt-2 text-sm leading-6">
                        右侧对话轨道只服务当前技能创建线程，让中间工作台专注技能包审阅、测试、发布门槛和图谱分析。
                      </p>
                      <div className="mt-3 space-y-3">
                        <div className="space-y-1">
                          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
                            技能创建器代理
                          </div>
                          <Select
                            value={activeAgentName}
                            onValueChange={setSelectedAgentName}
                            disabled={!agentSelectorEnabled || agentSelectionLocked}
                          >
                            <SelectTrigger className="w-full bg-background/70">
                              <SelectValue placeholder="选择技能创建器代理" />
                            </SelectTrigger>
                            <SelectContent>
                              {agentOptions.map((option) => (
                                <SelectItem key={option.name} value={option.name}>
                                  {option.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <div className="text-xs text-muted-foreground">
                            {selectionHint}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {assistantDescription}
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {SKILL_STUDIO_BUILTIN_SKILLS.map((skill) => (
                            <Badge key={skill} variant="outline">
                              {localizeWorkspaceDisplayText(skill)}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="min-h-0 flex-1 overflow-hidden">
                      <MessageList
                        className="flex-1 justify-start"
                        paddingBottom={32}
                        threadId={threadId}
                        thread={thread}
                      />
                    </div>

                    <div className="bg-background border-t p-3">
                      <InputBox
                        className="bg-background w-full"
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
                        onContextChange={(context) => setSettings("context", context)}
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
