import type { SubmarineRuntimeSnapshotPayload } from "../submarine-runtime-panel.contract";

export function getSubmarineNegotiationAttentionKey(
  runtime: SubmarineRuntimeSnapshotPayload | null | undefined,
): string | null {
  if (!runtime) {
    return null;
  }

  const needsUserConfirmation =
    runtime.review_status === "needs_user_confirmation" ||
    runtime.next_recommended_stage === "user-confirmation" ||
    runtime.requires_immediate_confirmation === true;

  if (!needsUserConfirmation) {
    return null;
  }

  return [
    runtime.current_stage ?? "unknown",
    runtime.review_status ?? "unknown",
    runtime.next_recommended_stage ?? "unknown",
  ].join("::");
}
