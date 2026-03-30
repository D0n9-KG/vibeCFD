import type { Message } from "@langchain/langgraph-sdk";

import type { AgentThread } from "./types";

export function pathOfThread(threadId: string) {
  return `/workspace/chats/${threadId}`;
}

export function pathOfThreadByState(thread: AgentThread): string {
  const id = thread.thread_id;
  if (
    thread.values?.submarine_runtime != null &&
    typeof thread.values.submarine_runtime === "object"
  ) {
    return `/workspace/submarine/${id}`;
  }
  if (
    thread.values?.submarine_skill_studio != null &&
    typeof thread.values.submarine_skill_studio === "object"
  ) {
    return `/workspace/skill-studio/${id}`;
  }
  const artifacts = thread.values?.artifacts;
  if (Array.isArray(artifacts)) {
    const hasCfd = artifacts.some(
      (a) =>
        typeof a === "string" &&
        a.includes("/submarine/") &&
        !a.includes("/submarine/skill-studio/"),
    );
    if (hasCfd) return `/workspace/submarine/${id}`;
    const hasSkillStudio = artifacts.some(
      (a) => typeof a === "string" && a.includes("/submarine/skill-studio/"),
    );
    if (hasSkillStudio) return `/workspace/skill-studio/${id}`;
  }
  return `/workspace/chats/${id}`;
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

  const deletedPath = pathOfThreadByState(threads[threadIndex]!);
  if (deletedPath.startsWith("/workspace/submarine/")) {
    return "/workspace/submarine/new";
  }
  if (deletedPath.startsWith("/workspace/skill-studio/")) {
    return "/workspace/skill-studio";
  }
  return "/workspace/chats/new";
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
