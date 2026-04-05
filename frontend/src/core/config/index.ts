import { env } from "@/env";

import {
  resolveBackendBaseURL,
  resolveLangGraphBaseURL,
} from "./runtime-base-url";

function getBrowserLocation() {
  if (typeof window === "undefined") {
    return undefined;
  }

  return {
    origin: window.location.origin,
    hostname: window.location.hostname,
    port: window.location.port,
  };
}

export function getBackendBaseURL() {
  return resolveBackendBaseURL({
    backendBaseURL: env.NEXT_PUBLIC_BACKEND_BASE_URL,
    location: getBrowserLocation(),
  });
}

export function getLangGraphBaseURL(isMock?: boolean) {
  return resolveLangGraphBaseURL({
    langGraphBaseURL: env.NEXT_PUBLIC_LANGGRAPH_BASE_URL,
    isMock,
    location: getBrowserLocation(),
  });
}
