type BrowserLocationLike = {
  origin: string;
  hostname: string;
  port: string;
};

type BackendBaseURLOptions = {
  backendBaseURL?: string;
  location?: BrowserLocationLike;
};

type LangGraphBaseURLOptions = {
  langGraphBaseURL?: string;
  isMock?: boolean;
  location?: BrowserLocationLike;
};

function normalizeConfiguredBaseURL(url?: string): string | undefined {
  const trimmed = url?.trim();
  if (!trimmed) {
    return undefined;
  }

  return trimmed;
}

function isStandaloneLocalFrontendHost(location?: BrowserLocationLike): boolean {
  if (!location) {
    return false;
  }

  const isLocalHost =
    location.hostname === "localhost" || location.hostname === "127.0.0.1";

  return isLocalHost && location.port !== "2026";
}

export function resolveBackendBaseURL({
  backendBaseURL,
  location,
}: BackendBaseURLOptions): string {
  const normalizedBackendBaseURL = normalizeConfiguredBaseURL(backendBaseURL);

  if (location) {
    if (normalizedBackendBaseURL) {
      return normalizedBackendBaseURL;
    }

    return "";
  }

  return normalizedBackendBaseURL ?? "http://localhost:8001";
}

export function resolveLangGraphBaseURL({
  langGraphBaseURL,
  isMock,
  location,
}: LangGraphBaseURLOptions): string {
  if (isMock) {
    if (location) {
      return `${location.origin}/mock/api`;
    }

    return "http://localhost:3000/mock/api";
  }

  const normalizedLangGraphBaseURL =
    normalizeConfiguredBaseURL(langGraphBaseURL);
  if (normalizedLangGraphBaseURL) {
    return normalizedLangGraphBaseURL;
  }

  if (location && isStandaloneLocalFrontendHost(location)) {
    return `${location.origin}/api/langgraph`;
  }

  if (location) {
    return `${location.origin}/api/langgraph`;
  }

  return "http://localhost:2026/api/langgraph";
}
