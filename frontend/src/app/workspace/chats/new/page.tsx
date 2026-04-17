"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";

import { WorkspaceStatePanel } from "@/components/workspace/workspace-state-panel";

export default function LegacyNewChatRedirectPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isMock = searchParams.get("mock") === "true";

  useEffect(() => {
    router.replace(
      isMock ? "/workspace/submarine/new?mock=true" : "/workspace/submarine/new",
    );
  }, [isMock, router]);

  return (
    <WorkspaceStatePanel
      state="data-interrupted"
      label="入口迁移"
      title="正在跳转到仿真工作台"
      description="旧的通用 chat 入口已经退役，系统正在为你打开默认的仿真工作台。"
    />
  );
}
