export const PIPELINE_SIDEBAR_MIN_PCT = 10;
export const PIPELINE_SIDEBAR_DEFAULT_PCT = 14;
export const PIPELINE_SIDEBAR_MAX_PCT = 22;

export const PIPELINE_CHAT_MIN_PCT = 16;
export const PIPELINE_CHAT_DEFAULT_PCT = 22;
export const PIPELINE_CHAT_MAX_PCT = 32;

export const PIPELINE_STORAGE_KEY_SIDEBAR = "submarine-pipeline-sidebar-size";
export const PIPELINE_STORAGE_KEY_CHAT = "submarine-pipeline-chat-size";

export type PanelPercentSize = `${number}%`;

export type PipelineLayoutConfig = {
  sidebarDefaultPct: number;
  sidebarMinPct: number;
  sidebarMaxPct: number;
  sidebarDefaultSize: PanelPercentSize;
  sidebarMinSize: PanelPercentSize;
  sidebarMaxSize: PanelPercentSize;
  chatDefaultPct: number;
  chatMinPct: number;
  chatMaxPct: number;
  chatDefaultSize: PanelPercentSize;
  chatMinSize: PanelPercentSize;
  chatMaxSize: PanelPercentSize;
  sidebarStorageKey: string;
  chatStorageKey: string;
};

export function toPanelPercentSize(value: number): PanelPercentSize {
  return `${value}%`;
}

export function resolveStoredPanelPct(
  raw: string | null | undefined,
  {
    fallbackPct,
    minPct,
    maxPct,
  }: {
    fallbackPct: number;
    minPct: number;
    maxPct: number;
  },
): number {
  if (!raw) return fallbackPct;

  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) return fallbackPct;

  return Math.min(maxPct, Math.max(minPct, parsed));
}

export function getPipelineLayoutConfig(): PipelineLayoutConfig {
  return {
    sidebarDefaultPct: PIPELINE_SIDEBAR_DEFAULT_PCT,
    sidebarMinPct: PIPELINE_SIDEBAR_MIN_PCT,
    sidebarMaxPct: PIPELINE_SIDEBAR_MAX_PCT,
    sidebarDefaultSize: toPanelPercentSize(PIPELINE_SIDEBAR_DEFAULT_PCT),
    sidebarMinSize: toPanelPercentSize(PIPELINE_SIDEBAR_MIN_PCT),
    sidebarMaxSize: toPanelPercentSize(PIPELINE_SIDEBAR_MAX_PCT),
    chatDefaultPct: PIPELINE_CHAT_DEFAULT_PCT,
    chatMinPct: PIPELINE_CHAT_MIN_PCT,
    chatMaxPct: PIPELINE_CHAT_MAX_PCT,
    chatDefaultSize: toPanelPercentSize(PIPELINE_CHAT_DEFAULT_PCT),
    chatMinSize: toPanelPercentSize(PIPELINE_CHAT_MIN_PCT),
    chatMaxSize: toPanelPercentSize(PIPELINE_CHAT_MAX_PCT),
    sidebarStorageKey: PIPELINE_STORAGE_KEY_SIDEBAR,
    chatStorageKey: PIPELINE_STORAGE_KEY_CHAT,
  };
}
