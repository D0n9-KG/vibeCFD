"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { WorkspaceStatePanel } from "@/components/workspace/workspace-state-panel";
import { getAPIClient } from "@/core/api";
import type { AgentThread, AgentThreadState } from "@/core/threads/types";
import { resolveLegacyChatThreadHref } from "@/core/threads/utils";

function buildThreadSnapshot(
  threadId: string,
  state: AgentThreadState | null | undefined,
): AgentThread {
  return {
    thread_id: threadId,
    created_at: "",
    updated_at: "",
    status: "idle",
    metadata: {},
    values: {
      title: state?.title ?? "Untitled",
      messages: state?.messages ?? [],
      artifacts: state?.artifacts ?? [],
      todos: state?.todos,
      workspace_kind: state?.workspace_kind,
      submarine_runtime: state?.submarine_runtime,
      submarine_skill_studio: state?.submarine_skill_studio,
    },
  } as AgentThread;
}

export default function LegacyChatThreadRedirectPage() {
  const params = useParams<{ thread_id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const isMock = searchParams.get("mock") === "true";
  const threadId = params.thread_id;

  useEffect(() => {
    if (!threadId) {
      return;
    }

    let cancelled = false;

    async function redirectLegacyThread() {
      try {
        const state = await getAPIClient(isMock).threads.getState<AgentThreadState>(
          threadId,
        );
        if (cancelled) {
          return;
        }

        const targetHref = resolveLegacyChatThreadHref(
          threadId,
          buildThreadSnapshot(threadId, state.values),
          isMock,
        );
        router.replace(targetHref);
      } catch (redirectError) {
        if (cancelled) {
          return;
        }
        setError(
          redirectError instanceof Error
            ? redirectError.message
            : "无法恢复这个旧线程入口。",
        );
      }
    }

    void redirectLegacyThread();

    return () => {
      cancelled = true;
    };
  }, [isMock, router, threadId]);

  if (error) {
    return (
      <WorkspaceStatePanel
        state="update-failed"
        label="线程迁移"
        title="无法恢复这个旧线程入口"
        description={error}
        actions={[
          {
            label: "返回线程与历史",
            href: "/workspace/control-center?tab=threads",
          },
          {
            label: "新建仿真任务",
            href: isMock
              ? "/workspace/submarine/new?mock=true"
              : "/workspace/submarine/new",
            variant: "ghost",
          },
        ]}
      />
    );
  }

  return (
    <WorkspaceStatePanel
      state="data-interrupted"
      label="线程迁移"
      title="正在跳转到对应工作台"
      description="这个旧的通用 chat 页面已经退役，系统正在根据线程内容把你带到仿真工作台、技能工作台，或线程管理入口。"
    />
  );
}
