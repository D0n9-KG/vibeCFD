import type { AgentThread } from "../../core/threads/types.ts";
import {
  type ThreadWorkbenchKind,
  workbenchKindOfThread,
} from "../../core/threads/utils.ts";

export type SidebarThreadGroup = {
  kind: ThreadWorkbenchKind;
  threads: AgentThread[];
};

export function classifyThreadsForSidebar(
  threads: AgentThread[],
): SidebarThreadGroup[] {
  const groups: Record<ThreadWorkbenchKind, AgentThread[]> = {
    submarine: [],
    "skill-studio": [],
    chat: [],
  };

  for (const thread of threads) {
    groups[workbenchKindOfThread(thread)].push(thread);
  }

  return (["submarine", "skill-studio", "chat"] as const)
    .map((kind) => ({
      kind,
      threads: groups[kind],
    }))
    .filter((group) => group.threads.length > 0);
}

export function labelOfSidebarThreadGroup(kind: ThreadWorkbenchKind) {
  switch (kind) {
    case "submarine":
      return "仿真任务";
    case "skill-studio":
      return "Skill 创建";
    default:
      return "通用对话";
  }
}
