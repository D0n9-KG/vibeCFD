import type { Translations } from "@/core/i18n/locales/types";

export type WorkspaceStatePanelId =
  | "first-run"
  | "permissions-error"
  | "data-interrupted"
  | "update-failed";

export const WORKSPACE_STATE_IDS: WorkspaceStatePanelId[] = [
  "first-run",
  "permissions-error",
  "data-interrupted",
  "update-failed",
];

export function getWorkspaceStateCopy(
  states: Translations["workspaceStates"],
  state: WorkspaceStatePanelId,
) {
  return states[state];
}
