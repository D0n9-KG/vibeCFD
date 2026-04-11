function normalizeErrorMessage(message: string): string {
  let normalized = message.trim();

  if (/Failed to construct 'URL': Invalid URL/i.test(normalized)) {
    return "LangGraph URL 配置无效，无法创建潜艇仿真线程。";
  }

  if (/LangGraph base URL is empty or invalid\.?/i.test(normalized)) {
    return "LangGraph base URL is empty or invalid. Please verify the LangGraph URL configuration.";
  }

  if (/Thread bootstrap stream did not rebind\.?/i.test(normalized)) {
    return "新建线程后未能完成流绑定，请在当前潜艇工作台直接重试。";
  }

  const wrappedMatch = /^([A-Za-z]+Error)\((['"])([\s\S]*)\2\)$/.exec(
    normalized,
  );
  if (wrappedMatch?.[3]) {
    normalized = wrappedMatch[3].trim();
  }

  const providerMessageFromPayload = /['"]message['"]:\s*['"]([^'"]+)['"]/.exec(
    normalized,
  );
  if (providerMessageFromPayload?.[1]?.trim()) {
    return providerMessageFromPayload[1].trim();
  }

  const providerMessageFromAssignment = /message=("|')([^"']+)\1/.exec(
    normalized,
  );
  if (providerMessageFromAssignment?.[2]?.trim()) {
    return providerMessageFromAssignment[2].trim();
  }

  const errorCodePrefix = /^Error code:\s*\d+\s*-\s*(.+)$/.exec(normalized);
  if (errorCodePrefix?.[1]) {
    normalized = errorCodePrefix[1].trim();
  }

  return normalized;
}

function extractErrorMessage(error: unknown, depth = 0): string | null {
  if (depth > 4 || error == null) {
    return null;
  }

  if (typeof error === "string") {
    const trimmed = error.trim();
    return trimmed ? trimmed : null;
  }

  if (error instanceof Error) {
    const trimmed = error.message.trim();
    if (trimmed) {
      return trimmed;
    }
  }

  if (typeof error === "object") {
    const directMessage = Reflect.get(error, "message");
    const message = extractErrorMessage(directMessage, depth + 1);
    if (message) {
      return message;
    }

    const nestedError = Reflect.get(error, "error");
    const nested = extractErrorMessage(nestedError, depth + 1);
    if (nested) {
      return nested;
    }

    const detail = Reflect.get(error, "detail");
    const detailMessage = extractErrorMessage(detail, depth + 1);
    if (detailMessage) {
      return detailMessage;
    }

    const cause = Reflect.get(error, "cause");
    return extractErrorMessage(cause, depth + 1);
  }

  return null;
}

function hasMatchingErrorMessage(
  error: unknown,
  predicate: (message: string) => boolean,
  depth = 0,
): boolean {
  if (depth > 4 || error == null) {
    return false;
  }

  if (typeof error === "string") {
    const trimmed = error.trim();
    return trimmed ? predicate(trimmed) : false;
  }

  if (error instanceof Error) {
    const trimmed = error.message.trim();
    if (trimmed && predicate(trimmed)) {
      return true;
    }
  }

  if (typeof error === "object") {
    return ["message", "error", "detail", "cause"].some((key) =>
      hasMatchingErrorMessage(Reflect.get(error, key), predicate, depth + 1),
    );
  }

  return false;
}

const MISSING_THREAD_PATTERNS = [
  /Thread with ID [^"'`\s]+ not found/i,
  /thread not found/i,
] as const;

export function isMissingThreadError(error: unknown): boolean {
  return MISSING_THREAD_PATTERNS.some((pattern) =>
    hasMatchingErrorMessage(error, (message) => pattern.test(message)),
  );
}

export function getThreadErrorMessage(
  error: unknown,
  fallback = "Request failed.",
): string {
  const message = extractErrorMessage(error);
  return message ? normalizeErrorMessage(message) : fallback;
}
