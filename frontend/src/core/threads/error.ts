function normalizeErrorMessage(message: string): string {
  let normalized = message.trim();

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

export function getThreadErrorMessage(
  error: unknown,
  fallback = "Request failed.",
): string {
  const message = extractErrorMessage(error);
  return message ? normalizeErrorMessage(message) : fallback;
}
