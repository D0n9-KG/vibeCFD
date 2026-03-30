import type { Message } from "@langchain/langgraph-sdk";

import type { AgentThread } from "./types";

export function pathOfThread(threadId: string) {
  return `/workspace/chats/${threadId}`;
}

export type ThreadWorkbenchKind = "submarine" | "skill-studio" | "chat";
const rememberedWorkbenchKinds = new Map<
  string,
  Exclude<ThreadWorkbenchKind, "chat">
>();

export function rememberWorkbenchKindForThread(
  threadId: string,
  workbenchKind: Exclude<ThreadWorkbenchKind, "chat">,
) {
  rememberedWorkbenchKinds.set(threadId, workbenchKind);
}

export function forgetWorkbenchKindForThread(threadId: string) {
  rememberedWorkbenchKinds.delete(threadId);
}

export function workbenchKindOfThread(
  thread: AgentThread,
): ThreadWorkbenchKind {
  if (
    thread.values?.workspace_kind === "submarine" ||
    thread.values?.workspace_kind === "skill-studio"
  ) {
    return thread.values.workspace_kind;
  }
  const rememberedWorkbenchKind = rememberedWorkbenchKinds.get(
    thread.thread_id,
  );
  if (rememberedWorkbenchKind) {
    return rememberedWorkbenchKind;
  }
  if (
    thread.values?.submarine_runtime != null &&
    typeof thread.values.submarine_runtime === "object"
  ) {
    return "submarine";
  }
  if (
    thread.values?.submarine_skill_studio != null &&
    typeof thread.values.submarine_skill_studio === "object"
  ) {
    return "skill-studio";
  }
  const artifacts = thread.values?.artifacts;
  if (Array.isArray(artifacts)) {
    const hasCfd = artifacts.some(
      (a) =>
        typeof a === "string" &&
        a.includes("/submarine/") &&
        !a.includes("/submarine/skill-studio/"),
    );
    if (hasCfd) return "submarine";
    const hasSkillStudio = artifacts.some(
      (a) => typeof a === "string" && a.includes("/submarine/skill-studio/"),
    );
    if (hasSkillStudio) return "skill-studio";
  }
  return "chat";
}

export function pathOfThreadByState(thread: AgentThread): string {
  const id = thread.thread_id;
  switch (workbenchKindOfThread(thread)) {
    case "submarine":
      return `/workspace/submarine/${id}`;
    case "skill-studio":
      return `/workspace/skill-studio/${id}`;
    default:
      return `/workspace/chats/${id}`;
  }
}

export function pathAfterThreadDeletion(
  threads: AgentThread[],
  deletedThreadId: string,
) {
  const threadIndex = threads.findIndex((t) => t.thread_id === deletedThreadId);
  if (threadIndex < 0) {
    return "/workspace/chats/new";
  }

  const nextThread = threads[threadIndex + 1] ?? threads[threadIndex - 1];
  if (nextThread) {
    return pathOfThreadByState(nextThread);
  }

  switch (workbenchKindOfThread(threads[threadIndex]!)) {
    case "submarine":
      return "/workspace/submarine/new";
    case "skill-studio":
      return "/workspace/skill-studio";
    default:
      return "/workspace/chats/new";
  }
}

export function textOfMessage(message: Message) {
  if (typeof message.content === "string") {
    return message.content;
  } else if (Array.isArray(message.content)) {
    for (const part of message.content) {
      if (part.type === "text") {
        return part.text;
      }
    }
  }
  return null;
}

export function titleOfThread(thread: AgentThread) {
  return thread.values?.title ?? "Untitled";
}
