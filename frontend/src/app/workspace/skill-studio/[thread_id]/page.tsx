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
  const { setOpen: setArtifactsOpen, deselect: deselectArtifact } =
    useArtifacts();
  const [chatOpen, setChatOpen] = useState(isNewThread);
  const [pendingThreadRouteId, setPendingThreadRouteId] = useState<
    string | null
  >(null);

  useSpecificChatMode();

  useEffect(() => {
    deselectArtifact();
    setArtifactsOpen(false);
  }, [deselectArtifact, setArtifactsOpen]);

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
        let body = "技能工作台线程已结束。";
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
    : "请在第一次提交前确认技能创建代理。";
  const assistantDescription =
    activeAgentOption?.description ??
    `${activeAssistantLabel} 负责当前线程中的技能创建、校验、测试与发布收口。`;

  return (
    <ThreadContext.Provider value={{ thread, isMock }}>
      <ChatBox threadId={threadId}>
        <div className="relative flex size-full min-h-0 flex-col">
          <header className="absolute top-0 right-0 left-0 z-30 flex h-16 shrink-0 items-center border-b border-slate-200/80 bg-white/72 px-4 backdrop-blur-xl dark:border-slate-800/80 dark:bg-slate-950/68">
            <div className="flex min-w-0 flex-1 items-center gap-3">
              <Button asChild size="sm" variant="ghost">
                <Link href={dashboardHref}>
                  <ArrowLeftIcon className="size-4" />
                  返回技能工作台
                </Link>
              </Button>
              <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl border border-cyan-200/70 bg-cyan-50/80 text-cyan-700 dark:border-cyan-900/70 dark:bg-cyan-950/35 dark:text-cyan-300">
                <WandSparklesIcon className="size-4" />
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-medium text-slate-950 dark:text-slate-50">
                  <ThreadTitle threadId={threadId} thread={thread} />
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  VibeCFD · Skill Studio · 技能创建工作台
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
                aria-label={chatOpen ? "收起对话侧栏" : "展开对话侧栏"}
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

          <main className="min-h-0 flex-1 overflow-y-auto pt-16">
            <div className="mx-auto flex min-h-full w-full max-w-[1720px] flex-col px-4 py-4 md:px-5">
              <div className={layout.shellClassName}>
                <SkillStudioWorkbenchShell
                  className={layout.workbenchPaneClassName}
                  threadId={threadId}
                  assistantLabel={activeAssistantLabel}
                  hasWorkbenchSurface={hasWorkbenchSurface}
                  isNewThread={isNewThread}
                  onOpenChat={focusChatRail}
                />

                <aside
                  id="skill-studio-chat-rail"
                  className={layout.chatRailClassName}
                >
                  <div className={layout.chatRailInnerClassName}>
                    <div className="border-b border-slate-200/80 bg-slate-50/70 px-4 py-4 dark:border-slate-800/80 dark:bg-slate-900/50">
                      <div className="flex items-center gap-2 text-sm font-medium text-slate-950 dark:text-slate-50">
                        <WandSparklesIcon className="size-4 text-cyan-600 dark:text-cyan-300" />
                        {activeAssistantLabel}
                      </div>
                      <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                        右侧对话轨道负责推进技能创建，中间工作台负责审阅技能包、校验结果、测试矩阵与图谱连接。
                      </p>
                      <div className="mt-3 space-y-3">
                        <div className="space-y-1">
                          <div className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                            技能创建代理
                          </div>
                          <Select
                            value={activeAgentName}
                            onValueChange={setSelectedAgentName}
                            disabled={!agentSelectorEnabled || agentSelectionLocked}
                          >
                            <SelectTrigger className="w-full bg-white/80 dark:bg-slate-950/60">
                              <SelectValue placeholder="选择技能创建代理" />
                            </SelectTrigger>
                            <SelectContent>
                              {agentOptions.map((option) => (
                                <SelectItem key={option.name} value={option.name}>
                                  {option.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <div className="text-xs text-slate-500 dark:text-slate-400">
                            {selectionHint}
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400">
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

                    <div className="border-t border-slate-200/80 bg-white/82 p-3 dark:border-slate-800/80 dark:bg-slate-950/82">
                      <InputBox
                        className="w-full bg-transparent"
                        isNewThread={isNewThread}
                        showNewThreadSuggestions={false}
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
