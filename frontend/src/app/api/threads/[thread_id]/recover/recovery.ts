import type { Dirent } from "node:fs";
import fs from "node:fs/promises";
import path from "node:path";

type RunningThreadRecoveryDecisionInput = {
  latestRunStatus: string | null | undefined;
  latestRunCreatedAt: string | null | undefined;
  latestCommandExitAt: Date | null;
};

export type RunningThreadRecoveryDecision = {
  recoverable: boolean;
  reason:
    | "latest_run_not_running"
    | "run_created_at_unknown"
    | "no_command_exit_evidence"
    | "command_exit_predates_run"
    | "command_exit_after_run_start";
};

const COMMAND_EXIT_FILENAME = ".deerflow-command-exit-status";

export function decideRunningThreadRecovery({
  latestRunStatus,
  latestRunCreatedAt,
  latestCommandExitAt,
}: RunningThreadRecoveryDecisionInput): RunningThreadRecoveryDecision {
  if (latestRunStatus !== "running") {
    return {
      recoverable: false,
      reason: "latest_run_not_running",
    };
  }

  const createdAt =
    latestRunCreatedAt != null ? new Date(latestRunCreatedAt) : null;
  if (createdAt == null || Number.isNaN(createdAt.valueOf())) {
    return {
      recoverable: false,
      reason: "run_created_at_unknown",
    };
  }

  if (latestCommandExitAt == null) {
    return {
      recoverable: false,
      reason: "no_command_exit_evidence",
    };
  }

  if (latestCommandExitAt < createdAt) {
    return {
      recoverable: false,
      reason: "command_exit_predates_run",
    };
  }

  return {
    recoverable: true,
    reason: "command_exit_after_run_start",
  };
}

export async function findLatestCommandExitAtInDirectory(
  rootDir: string,
): Promise<Date | null> {
  const stack = [rootDir];
  let latest: Date | null = null;

  while (stack.length > 0) {
    const current = stack.pop();
    if (!current) {
      continue;
    }

    let entries: Dirent[];
    try {
      entries = await fs.readdir(current, { withFileTypes: true });
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") {
        continue;
      }
      throw error;
    }

    for (const entry of entries) {
      const entryPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        stack.push(entryPath);
        continue;
      }

      if (!entry.isFile() || entry.name !== COMMAND_EXIT_FILENAME) {
        continue;
      }

      const stats = await fs.stat(entryPath);
      if (latest == null || stats.mtime > latest) {
        latest = stats.mtime;
      }
    }
  }

  return latest;
}

export async function findLatestCommandExitAtForThread(
  threadId: string,
): Promise<Date | null> {
  const workspaceRoot = path.resolve(
    process.cwd(),
    "..",
    "backend",
    ".deer-flow",
    "threads",
    threadId,
    "user-data",
    "workspace",
  );
  return findLatestCommandExitAtInDirectory(workspaceRoot);
}
