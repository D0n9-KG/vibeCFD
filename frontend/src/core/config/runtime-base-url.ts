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

function isStandaloneLocalFrontendDev(location?: BrowserLocationLike): boolean {
  if (!location) {
    return false;
  }

  return (
    location.port === "3000" &&
    (location.hostname === "localhost" || location.hostname === "127.0.0.1")
  );
}

export function resolveBackendBaseURL({
  backendBaseURL,
  location,
}: BackendBaseURLOptions): string {
  if (backendBaseURL) {
    return backendBaseURL;
  }

  if (isStandaloneLocalFrontendDev(location)) {
    return "http://localhost:8001";
  }

  return "";
}

export function resolveLangGraphBaseURL({
  langGraphBaseURL,
  isMock,
  location,
}: LangGraphBaseURLOptions): string {
  if (langGraphBaseURL) {
    return langGraphBaseURL;
  }

  if (isMock) {
    if (location) {
      return `${location.origin}/mock/api`;
    }

    return "http://localhost:3000/mock/api";
  }

  if (isStandaloneLocalFrontendDev(location)) {
    return "http://localhost:2024";
  }

  if (location) {
    return `${location.origin}/api/langgraph`;
  }

  return "http://localhost:2026/api/langgraph";
}
