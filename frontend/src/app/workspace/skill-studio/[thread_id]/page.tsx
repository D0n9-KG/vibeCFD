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
  labelOfSkillStudioAgentName,
  resolveSkillStudioAgentSelection,
} from "@/components/workspace/skill-studio-agent-options";
import { SkillStudioWorkbenchPanel } from "@/components/workspace/skill-studio-workbench-panel";
import { ThreadTitle } from "@/components/workspace/thread-title";
import { TokenUsageIndicator } from "@/components/workspace/token-usage-indicator";
import { useAgents } from "@/core/agents";
import { useNotification } from "@/core/notification/hooks";
import { useLocalSettings } from "@/core/settings";
import { useThreadStream } from "@/core/threads/hooks";
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

  const [thread, sendMessage, isUploading] = useThreadStream({
    threadId: isNewThread ? undefined : threadId,
    isNewThread,
    context: settings.context,
    isMock,
    workbenchKind: "skill-studio",
    onStart: (createdThreadId) => {
      markThreadStarted(createdThreadId);
      router.replace(
        buildSkillStudioThreadPath({
          threadId: createdThreadId,
          isMock,
          agentName: selectedAgentName ?? DEFAULT_SKILL_STUDIO_AGENT,
        }),
      );
    },
    onFinish: (state) => {
      if (document.hidden || !document.hasFocus()) {
        let body = "Skill Studio thread finished";
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
  const activeAssistantLabel =
    persistedAssistantLabel ??
    activeAgentOption?.label ??
    labelOfSkillStudioAgentName(activeAgentName);
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
    ? "线程启动后会锁定 agent 身份，保持记忆、提示词和 Skill artifacts 一致。"
    : "新线程提交前可以切换 Codex 或 Claude 的 Skill Creator 身份。";
  const assistantDescription =
    activeAgentOption?.description ??
    `${activeAssistantLabel} is dedicated to Skill Studio authoring, validation, testing, and publishing workflows.`;

  return (
    <ThreadContext.Provider value={{ thread, isMock }}>
      <ChatBox threadId={threadId}>
        <div className="relative flex size-full min-h-0 flex-col">
          <header className="bg-background/85 absolute top-0 right-0 left-0 z-30 flex h-14 shrink-0 items-center border-b px-4 backdrop-blur">
            <div className="flex min-w-0 flex-1 items-center gap-3">
              <Button asChild size="sm" variant="ghost">
                <Link href={dashboardHref}>
                  <ArrowLeftIcon className="size-4" />
                  Skill Studio
                </Link>
              </Button>
              <div className="min-w-0">
                <div className="truncate text-sm font-medium">
                  <ThreadTitle threadId={threadId} thread={thread} />
                </div>
                <div className="text-muted-foreground text-xs">
                  领域专家 · Skill 创建工作台
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
                {chatOpen ? "收起聊天" : "展开聊天"}
              </Button>
              <TokenUsageIndicator messages={thread.messages} />
              <ExportTrigger threadId={threadId} />
              <ArtifactTrigger />
            </div>
          </header>

          <main className="min-h-0 flex-1 overflow-hidden pt-14">
            <div className="mx-auto flex h-full min-h-0 w-full max-w-none flex-col px-4 py-4">
              <div className={layout.shellClassName}>
                <div className={layout.workbenchPaneClassName}>
                  <SkillStudioLaunchpad
                    assistantLabel={activeAssistantLabel}
                    hasWorkbenchSurface={hasWorkbenchSurface}
                    isNewThread={isNewThread}
                    onOpenChat={focusChatRail}
                  />
                  {hasWorkbenchSurface ? (
                    <SkillStudioWorkbenchPanel threadId={threadId} />
                  ) : (
                    <SkillStudioPlaceholder
                      assistantLabel={activeAssistantLabel}
                    />
                  )}
                </div>

                <aside
                  id="skill-studio-chat-rail"
                  className={layout.chatRailClassName}
                >
                  <div className={layout.chatRailInnerClassName}>
                    <div className="bg-muted/20 border-b px-4 py-4">
                      <div className="text-foreground flex items-center gap-2 text-sm font-medium">
                        <WandSparklesIcon className="text-muted-foreground size-4" />
                        {activeAssistantLabel}
                      </div>
                      <p className="text-muted-foreground mt-2 text-sm leading-6">
                        这里的对话专门用于与领域专家共创 skill。当前会话使用{" "}
                        {activeAssistantLabel}
                        ，默认围绕 `skill-creator` 与 `writing-skills`
                        方法论来整理触发条件、workflow、规则、测试场景和发布门槛。
                      </p>
                      <div className="mt-3 space-y-3">
                        <div className="space-y-1">
                          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
                            Skill Creator Agent
                          </div>
                          <Select
                            value={
                              agentSelectorEnabled ? activeAgentName : undefined
                            }
                            onValueChange={setSelectedAgentName}
                            disabled={
                              !agentSelectorEnabled || agentSelectionLocked
                            }
                          >
                            <SelectTrigger className="w-full bg-background/70">
                              <SelectValue placeholder="Select a Skill Creator agent" />
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
                              {skill}
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

function SkillStudioLaunchpad({
  assistantLabel,
  hasWorkbenchSurface,
  isNewThread,
  onOpenChat,
}: {
  assistantLabel: string;
  hasWorkbenchSurface: boolean;
  isNewThread: boolean;
  onOpenChat: () => void;
}) {
  return (
    <section className="bg-muted/20 rounded-2xl border p-5">
      <div className="text-muted-foreground mb-3 flex items-center gap-2 text-[11px] uppercase tracking-[0.24em]">
        <WandSparklesIcon className="size-4" />
        Skill Studio Workspace
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.65fr)]">
        <div className="space-y-3">
          <h1 className="text-foreground text-2xl font-semibold">
            让领域专家直接与专属 Skill Creator 代理共创技能
          </h1>
          <p className="text-muted-foreground max-w-4xl text-sm leading-7">
            中间工作台专门展示 skill 包、校验、场景测试和发布门槛；右侧聊天只负责与
            {assistantLabel} 协作，不再混入潜艇 CFD run 的执行信息。
          </p>
          <div className="flex flex-wrap gap-2">
            <Button onClick={onOpenChat}>
              <MessageSquareIcon className="size-4" />
              {isNewThread ? "开始起草 Skill" : "继续与 Skill Creator 协作"}
            </Button>
          </div>
        </div>

        <div className="bg-background/70 rounded-xl border p-4">
          <div className="text-foreground mb-3 text-sm font-medium">
            当前工作流
          </div>
          <div className="text-muted-foreground space-y-3 text-sm leading-6">
            <div>
              1. 专家通过右侧聊天告诉 {assistantLabel} 触发条件、workflow、规则和验收要求。
            </div>
            <div>
              2. 工作台即时生成 SKILL.md、UI metadata、测试矩阵和发布就绪信息。
            </div>
            <div>
              3. 专家在同一页面审阅、修订并决定何时进入发布流程。
            </div>
            {hasWorkbenchSurface ? (
              <div>
                当前线程已经生成了 Skill Studio 产物，可以直接继续审阅与测试。
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}

function SkillStudioPlaceholder({
  assistantLabel,
}: {
  assistantLabel: string;
}) {
  return (
    <section className="bg-background/60 rounded-2xl border border-dashed p-8">
      <div className="max-w-3xl">
        <h2 className="text-foreground text-lg font-semibold">
          等待第一份 Skill 包
        </h2>
        <p className="text-muted-foreground mt-3 text-sm leading-7">
          先在右侧与 {assistantLabel} 讨论这个 skill 的目标、触发条件、workflow、
          规则、测试场景和发布门槛。工作台会在第一轮草稿生成后，自动切换到完整的技能包、
          校验和发布视图。
        </p>
      </div>
    </section>
  );
}
