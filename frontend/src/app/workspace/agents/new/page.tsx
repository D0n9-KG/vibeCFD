"use client";

import { ArrowLeftIcon, BotIcon, CheckCircleIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  PromptInput,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputTextarea,
} from "@/components/ai-elements/prompt-input";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArtifactsProvider } from "@/components/workspace/artifacts";
import {
  WorkspaceSurfaceCard,
  WorkspaceSurfaceMain,
  WorkspaceSurfacePage,
} from "@/components/workspace/workspace-container";
import { MessageList } from "@/components/workspace/messages";
import { ThreadContext } from "@/components/workspace/messages/context";
import type { Agent } from "@/core/agents";
import { checkAgentName, getAgent } from "@/core/agents/api";
import { useI18n } from "@/core/i18n/hooks";
import { useThreadStream } from "@/core/threads/hooks";
import { uuid } from "@/core/utils/uuid";
import { cn } from "@/lib/utils";

type Step = "name" | "chat";

const NAME_RE = /^[A-Za-z0-9-]+$/;
const NEW_AGENT_SURFACE_LABEL = "新建智能体";

export default function NewAgentPage() {
  const { t } = useI18n();
  const router = useRouter();
  const [step, setStep] = useState<Step>("name");
  const [nameInput, setNameInput] = useState("");
  const [nameError, setNameError] = useState("");
  const [isCheckingName, setIsCheckingName] = useState(false);
  const [agentName, setAgentName] = useState("");
  const [agent, setAgent] = useState<Agent | null>(null);
  const threadId = useMemo(() => uuid(), []);

  useEffect(() => {
    document.title = `${t.agents.createPageTitle} - ${t.pages.appName}`;
  }, [t.agents.createPageTitle, t.pages.appName]);

  const [thread, sendMessage, isUploading] = useThreadStream({
    threadId: step === "chat" ? threadId : undefined,
    context: {
      mode: "flash",
      is_bootstrap: true,
    },
    onToolEnd({ name }) {
      if (name !== "setup_agent" || !agentName) return;
      getAgent(agentName)
        .then((fetched) => setAgent(fetched))
        .catch(() => {
          // Agent writes can lag the final tool event.
        });
    },
  });

  const handleConfirmName = useCallback(async () => {
    const trimmed = nameInput.trim();
    if (!trimmed) return;
    if (!NAME_RE.test(trimmed)) {
      setNameError(t.agents.nameStepInvalidError);
      return;
    }

    setNameError("");
    setIsCheckingName(true);
    try {
      const result = await checkAgentName(trimmed);
      if (!result.available) {
        setNameError(t.agents.nameStepAlreadyExistsError);
        return;
      }
    } catch {
      setNameError(t.agents.nameStepCheckError);
      return;
    } finally {
      setIsCheckingName(false);
    }

    setAgentName(trimmed);
    setStep("chat");
    await sendMessage(threadId, {
      text: t.agents.nameStepBootstrapMessage.replace("{name}", trimmed),
      files: [],
    });
  }, [
    agentName,
    nameInput,
    sendMessage,
    t.agents.nameStepAlreadyExistsError,
    t.agents.nameStepBootstrapMessage,
    t.agents.nameStepCheckError,
    t.agents.nameStepInvalidError,
    threadId,
  ]);

  const handleNameKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      void handleConfirmName();
    }
  };

  const handleChatSubmit = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || thread.isLoading) return;
      await sendMessage(
        threadId,
        { text: trimmed, files: [] },
        { agent_name: agentName },
      );
    },
    [agentName, sendMessage, thread.isLoading, threadId],
  );

  return (
    <WorkspaceSurfacePage data-surface-label={NEW_AGENT_SURFACE_LABEL}>
      <WorkspaceSurfaceMain>
        <WorkspaceSurfaceCard className="overflow-hidden">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="min-w-0 flex-1">
              <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-700">
                {NEW_AGENT_SURFACE_LABEL}
              </div>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-stone-900">
                {t.agents.createPageTitle}
              </h1>
              <p className="mt-2 max-w-3xl text-sm leading-7 text-stone-600">
                {t.agents.createPageDescription}
              </p>
            </div>

            <Button variant="outline" onClick={() => router.push("/workspace/agents")}>
              <ArrowLeftIcon className="size-4" />
              {t.agents.backToGallery}
            </Button>
          </div>
        </WorkspaceSurfaceCard>

        <div className="grid min-h-0 flex-1 gap-4 xl:grid-cols-[minmax(240px,280px)_minmax(0,1fr)]">
          <WorkspaceSurfaceCard className="h-fit">
            <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-stone-500">
              {t.agents.buildPathLabel}
            </div>
            <div className="mt-4 space-y-3">
              <StepCard
                active={step === "name"}
                complete={step === "chat"}
                index="01"
                title={t.agents.nameStepTitle}
                note={t.agents.nameStepHint}
              />
              <StepCard
                active={step === "chat"}
                complete={Boolean(agent)}
                index="02"
                title={t.agents.createPageSubtitle}
                note={
                  agent ? t.agents.agentCreated : t.agents.chatStepNote
                }
              />
            </div>

            <div className="mt-6 rounded-2xl border border-stone-200/80 bg-stone-50/80 p-4">
              <div className="text-sm font-semibold text-stone-900">
                {t.agents.plannedIdentityLabel}
              </div>
              <div className="mt-2 text-sm text-stone-600">
                {agentName || nameInput || t.agents.waitingForConfirmedName}
              </div>
            </div>
          </WorkspaceSurfaceCard>

          <ThreadContext.Provider value={{ thread }}>
            <ArtifactsProvider>
              {step === "name" ? (
                <WorkspaceSurfaceCard className="flex min-h-[34rem] items-center justify-center">
                  <div className="w-full max-w-md space-y-8">
                    <div className="space-y-3 text-center">
                      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                        <BotIcon className="size-7 text-primary" />
                      </div>
                      <div className="space-y-1">
                        <h2 className="text-xl font-semibold text-stone-900">
                          {t.agents.nameStepTitle}
                        </h2>
                        <p className="text-sm leading-6 text-stone-500">
                          {t.agents.nameStepHint}
                        </p>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <Input
                        autoFocus
                        placeholder={t.agents.nameStepPlaceholder}
                        value={nameInput}
                        onChange={(event) => {
                          setNameInput(event.target.value);
                          setNameError("");
                        }}
                        onKeyDown={handleNameKeyDown}
                        className={cn(
                          "h-12 rounded-2xl border-stone-200 bg-white shadow-sm",
                          nameError && "border-destructive",
                        )}
                      />
                      {nameError ? (
                        <p className="text-sm text-destructive">{nameError}</p>
                      ) : null}
                      <Button
                        className="w-full"
                        onClick={() => void handleConfirmName()}
                        disabled={!nameInput.trim() || isCheckingName}
                      >
                        {t.agents.nameStepContinue}
                      </Button>
                    </div>
                  </div>
                </WorkspaceSurfaceCard>
              ) : (
                <WorkspaceSurfaceCard className="flex min-h-[40rem] flex-col overflow-hidden p-0">
                  <div className="border-b border-stone-200/80 bg-stone-50/80 px-5 py-4">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-700">
                      {t.agents.bootstrapThreadLabel}
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <span className="rounded-full border border-stone-200/80 bg-white px-3 py-1 text-xs font-medium text-stone-700">
                        {agentName}
                      </span>
                      <span className="rounded-full border border-stone-200/80 bg-white px-3 py-1 text-xs font-medium text-stone-500">
                        {thread.isLoading ? t.common.running : t.common.ready}
                      </span>
                    </div>
                  </div>

                  <div className="min-h-0 flex-1 overflow-hidden px-5 pt-4">
                    <MessageList
                      className="flex-1 justify-start pt-6"
                      threadId={threadId}
                      thread={thread}
                    />
                  </div>

                  <div className="border-t border-stone-200/80 bg-white/96 p-4">
                    {agent ? (
                      <div className="flex flex-col items-center gap-4 rounded-[24px] border border-emerald-200/80 bg-emerald-50/60 py-8 text-center">
                        <CheckCircleIcon className="size-10 text-emerald-600" />
                        <p className="font-semibold text-stone-900">
                          {t.agents.agentCreated}
                        </p>
                        <div className="flex flex-wrap justify-center gap-2">
                          <Button
                            onClick={() =>
                              router.push(`/workspace/agents/${agentName}/chats/new`)
                            }
                          >
                            {t.agents.startChatting}
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => router.push("/workspace/agents")}
                          >
                            {t.agents.backToGallery}
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <PromptInput
                        onSubmit={({ text }) => void handleChatSubmit(text)}
                      >
                        <PromptInputTextarea
                          autoFocus
                          placeholder={t.agents.createPageSubtitle}
                          disabled={thread.isLoading || isUploading}
                        />
                        <PromptInputFooter className="justify-end">
                          <PromptInputSubmit
                            disabled={thread.isLoading || isUploading}
                          />
                        </PromptInputFooter>
                      </PromptInput>
                    )}
                  </div>
                </WorkspaceSurfaceCard>
              )}
            </ArtifactsProvider>
          </ThreadContext.Provider>
        </div>
      </WorkspaceSurfaceMain>
    </WorkspaceSurfacePage>
  );
}

function StepCard({
  active,
  complete,
  index,
  title,
  note,
}: {
  active: boolean;
  complete: boolean;
  index: string;
  title: string;
  note: string;
}) {
  const { t } = useI18n();

  return (
    <div
      className={cn(
        "rounded-2xl border px-4 py-4 transition-colors",
        active
          ? "border-amber-200 bg-amber-50/80"
          : "border-stone-200/80 bg-white/88",
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-stone-500">
          {index}
        </div>
        <div
          className={cn(
            "rounded-full px-2.5 py-1 text-[11px] font-medium",
            complete
              ? "bg-emerald-100 text-emerald-700"
              : active
                ? "bg-amber-100 text-amber-700"
                : "bg-stone-100 text-stone-500",
          )}
        >
          {complete ? t.common.done : active ? t.common.active : t.common.waiting}
        </div>
      </div>
      <div className="mt-3 text-sm font-semibold text-stone-900">{title}</div>
      <div className="mt-2 text-sm leading-6 text-stone-500">{note}</div>
    </div>
  );
}
