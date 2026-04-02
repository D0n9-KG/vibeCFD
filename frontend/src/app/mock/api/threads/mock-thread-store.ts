import fs from "fs";
import path from "path";

type MockThreadState = Record<string, unknown>;

const MOCK_THREAD_OVERRIDES_KEY = "__DEERFLOW_MOCK_THREAD_OVERRIDES__";

type GlobalWithMockThreadOverrides = typeof globalThis & {
  [MOCK_THREAD_OVERRIDES_KEY]?: Map<string, MockThreadState>;
};

function getMockThreadOverrides() {
  const globalWithOverrides = globalThis as GlobalWithMockThreadOverrides;
  if (globalWithOverrides[MOCK_THREAD_OVERRIDES_KEY] == null) {
    globalWithOverrides[MOCK_THREAD_OVERRIDES_KEY] = new Map();
  }
  return globalWithOverrides[MOCK_THREAD_OVERRIDES_KEY];
}

function readMockThreadFromDisk(threadId: string): MockThreadState {
  const jsonString = fs.readFileSync(
    path.resolve(process.cwd(), `public/demo/threads/${threadId}/thread.json`),
    "utf8",
  );
  return JSON.parse(jsonString) as MockThreadState;
}

export function readMockThread(threadId: string): MockThreadState {
  return getMockThreadOverrides().get(threadId) ?? readMockThreadFromDisk(threadId);
}

export function writeMockThread(threadId: string, threadState: MockThreadState) {
  getMockThreadOverrides().set(threadId, threadState);
}

function extractTextContent(content: unknown): string {
  if (typeof content === "string") {
    return content;
  }

  if (!Array.isArray(content)) {
    return "";
  }

  return content
    .map((item) => {
      if (
        item &&
        typeof item === "object" &&
        "type" in item &&
        item.type === "text" &&
        "text" in item &&
        typeof item.text === "string"
      ) {
        return item.text;
      }
      return "";
    })
    .join("")
    .trim();
}

function buildActionAcknowledgement(actionText: string) {
  if (actionText.includes("确认通过")) {
    return {
      taskSummary:
        "已记录 mock 审批通过动作；前端验证确认 approval CTA 会在工作台内完成，不会触发 404。",
      runtimeSummary:
        "Mock researcher approval was captured in-browser. This validation thread still stays in review mode and never launches a real solver run.",
      aiText:
        "已记录 mock 审批通过动作。本演示线程会继续停留在前端验证模式，不会启动真实求解，但确认按钮已能在工作台内闭环执行。",
    };
  }

  if (actionText.includes("重算") || actionText.includes("重新计算")) {
    return {
      taskSummary:
        "已记录 mock 重算请求；前端验证确认 revise CTA 会在工作台内完成，不会触发 404。",
      runtimeSummary:
        "Mock rerun feedback was captured in-browser. The thread remains a deterministic review fixture and does not dispatch a real solver run.",
      aiText:
        "已记录 mock 重算请求。本演示线程继续保持 deterministic mock 状态，但“需要重算”动作已能在工作台内完成。",
    };
  }

  return {
    taskSummary:
      "已记录 mock 补充说明动作；前端验证确认 clarification CTA 会在工作台内完成，不会触发 404。",
    runtimeSummary:
      "Mock clarification feedback was captured in-browser. The thread remains a deterministic review fixture and does not dispatch a real solver run.",
    aiText:
      "已记录 mock 补充说明动作。本演示线程继续保持 deterministic mock 状态，但“补充待确认条件”动作已能在工作台内完成。",
  };
}

export function applyMockThreadAction(
  threadState: MockThreadState,
  actionText: string,
  nowIso: string,
): MockThreadState {
  const nextState = JSON.parse(JSON.stringify(threadState)) as MockThreadState;
  const values =
    nextState.values && typeof nextState.values === "object"
      ? (nextState.values as Record<string, unknown>)
      : {};
  const messages = Array.isArray(values.messages)
    ? ([...values.messages] as Array<Record<string, unknown>>)
    : [];
  const trimmedActionText = actionText.trim() || "继续当前 mock 审批流程。";
  const acknowledgement = buildActionAcknowledgement(trimmedActionText);

  messages.push({
    content: [{ type: "text", text: trimmedActionText }],
    additional_kwargs: {},
    response_metadata: {},
    type: "human",
    name: null,
    id: `mock-human-${Date.now()}`,
  });

  messages.push({
    content: acknowledgement.aiText,
    additional_kwargs: {},
    response_metadata: {
      finish_reason: "stop",
      model_name: "mock-review-assistant",
    },
    type: "ai",
    name: null,
    id: `mock-ai-${Date.now()}`,
    tool_calls: [],
    invalid_tool_calls: [],
    usage_metadata: null,
  });

  values.messages = messages;

  const runtime =
    values.submarine_runtime && typeof values.submarine_runtime === "object"
      ? (values.submarine_runtime as Record<string, unknown>)
      : undefined;

  if (runtime) {
    runtime.task_summary = acknowledgement.taskSummary;
    runtime.runtime_summary = acknowledgement.runtimeSummary;
    runtime.recovery_guidance =
      "Mock browser validation only: stay in the current workbench and inspect the updated approval messaging without launching a real solver run.";
    runtime.blocker_detail =
      "Mock approval action captured for browser validation. Real solver dispatch remains intentionally disabled in this fixture.";
  }

  nextState.values = values;
  nextState.updated_at = nowIso;

  return nextState;
}
