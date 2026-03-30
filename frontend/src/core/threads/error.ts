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
  return extractErrorMessage(error) ?? fallback;
}
