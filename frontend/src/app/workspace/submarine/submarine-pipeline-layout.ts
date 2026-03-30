export const PIPELINE_SIDEBAR_MIN_PCT = 10;
export const PIPELINE_SIDEBAR_DEFAULT_PCT = 14;
export const PIPELINE_SIDEBAR_MAX_PCT = 22;

export const PIPELINE_CHAT_MIN_PCT = 16;
export const PIPELINE_CHAT_DEFAULT_PCT = 22;
export const PIPELINE_CHAT_MAX_PCT = 32;

export const PIPELINE_STORAGE_KEY_SIDEBAR = "submarine-pipeline-sidebar-size";
export const PIPELINE_STORAGE_KEY_CHAT = "submarine-pipeline-chat-size";

export type PipelineLayoutConfig = {
  sidebarDefaultPct: number;
  sidebarMinPct: number;
  sidebarMaxPct: number;
  chatDefaultPct: number;
  chatMinPct: number;
  chatMaxPct: number;
  sidebarStorageKey: string;
  chatStorageKey: string;
};

export function getPipelineLayoutConfig(): PipelineLayoutConfig {
  return {
    sidebarDefaultPct: PIPELINE_SIDEBAR_DEFAULT_PCT,
    sidebarMinPct: PIPELINE_SIDEBAR_MIN_PCT,
    sidebarMaxPct: PIPELINE_SIDEBAR_MAX_PCT,
    chatDefaultPct: PIPELINE_CHAT_DEFAULT_PCT,
    chatMinPct: PIPELINE_CHAT_MIN_PCT,
    chatMaxPct: PIPELINE_CHAT_MAX_PCT,
    sidebarStorageKey: PIPELINE_STORAGE_KEY_SIDEBAR,
    chatStorageKey: PIPELINE_STORAGE_KEY_CHAT,
  };
}
