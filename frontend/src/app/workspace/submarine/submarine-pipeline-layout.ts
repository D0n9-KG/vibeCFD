export const PIPELINE_DEFAULT_VIEWPORT_WIDTH_PX = 1440;
export const PIPELINE_MIN_WORKBENCH_WIDTH_PX = 1024;
export const PIPELINE_WORKSPACE_SIDEBAR_WIDTH_PX = 256;

export const PIPELINE_SIDEBAR_MIN_PX = 220;
export const PIPELINE_SIDEBAR_DEFAULT_PX = 280;
export const PIPELINE_SIDEBAR_MAX_PX = 360;

export const PIPELINE_CHAT_MIN_PX = 320;
export const PIPELINE_CHAT_DEFAULT_PX = 380;
export const PIPELINE_CHAT_MAX_PX = 480;

export const PIPELINE_STORAGE_KEY_SIDEBAR = "submarine-pipeline-sidebar-size-v2";
export const PIPELINE_STORAGE_KEY_CHAT = "submarine-pipeline-chat-size-v2";

export type PanelPercentSize = `${number}%`;
export type PanelPixelSize = `${number}px`;
export type PanelSize = PanelPercentSize | PanelPixelSize;

export type PipelineLayoutConfig = {
  sidebarDefaultPct: number;
  sidebarMinPct: number;
  sidebarMaxPct: number;
  sidebarDefaultSize: PanelSize;
  sidebarMinSize: PanelSize;
  sidebarMaxSize: PanelSize;
  chatDefaultPct: number;
  chatMinPct: number;
  chatMaxPct: number;
  chatDefaultSize: PanelSize;
  chatMinSize: PanelSize;
  chatMaxSize: PanelSize;
  sidebarStorageKey: string;
  chatStorageKey: string;
};

export function toPanelPercentSize(value: number): PanelPercentSize {
  return `${value}%`;
}

export function toPanelPixelSize(value: number): PanelPixelSize {
  return `${value}px`;
}

function roundToTwoDecimals(value: number): number {
  return Number(value.toFixed(2));
}

function estimateWorkbenchWidth(viewportWidth: number): number {
  return Math.max(
    PIPELINE_MIN_WORKBENCH_WIDTH_PX,
    viewportWidth - PIPELINE_WORKSPACE_SIDEBAR_WIDTH_PX,
  );
}

function pxToPercent(px: number, totalWidth: number): number {
  return roundToTwoDecimals((px / totalWidth) * 100);
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

export function getPipelineLayoutConfig(
  viewportWidth = PIPELINE_DEFAULT_VIEWPORT_WIDTH_PX,
): PipelineLayoutConfig {
  const workbenchWidth = estimateWorkbenchWidth(viewportWidth);

  return {
    sidebarDefaultPct: pxToPercent(PIPELINE_SIDEBAR_DEFAULT_PX, workbenchWidth),
    sidebarMinPct: pxToPercent(PIPELINE_SIDEBAR_MIN_PX, workbenchWidth),
    sidebarMaxPct: pxToPercent(PIPELINE_SIDEBAR_MAX_PX, workbenchWidth),
    sidebarDefaultSize: toPanelPixelSize(PIPELINE_SIDEBAR_DEFAULT_PX),
    sidebarMinSize: toPanelPixelSize(PIPELINE_SIDEBAR_MIN_PX),
    sidebarMaxSize: toPanelPixelSize(PIPELINE_SIDEBAR_MAX_PX),
    chatDefaultPct: pxToPercent(PIPELINE_CHAT_DEFAULT_PX, workbenchWidth),
    chatMinPct: pxToPercent(PIPELINE_CHAT_MIN_PX, workbenchWidth),
    chatMaxPct: pxToPercent(PIPELINE_CHAT_MAX_PX, workbenchWidth),
    chatDefaultSize: toPanelPixelSize(PIPELINE_CHAT_DEFAULT_PX),
    chatMinSize: toPanelPixelSize(PIPELINE_CHAT_MIN_PX),
    chatMaxSize: toPanelPixelSize(PIPELINE_CHAT_MAX_PX),
    sidebarStorageKey: PIPELINE_STORAGE_KEY_SIDEBAR,
    chatStorageKey: PIPELINE_STORAGE_KEY_CHAT,
  };
}
