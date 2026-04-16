import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

const {
  decideRunningThreadRecovery,
  findLatestCommandExitAtInDirectory,
} = await import(new URL("./recovery.ts", import.meta.url).href);

void test("decideRunningThreadRecovery marks a running run as recoverable once command-exit evidence lands after the run started", () => {
  const decision = decideRunningThreadRecovery({
    latestRunStatus: "running",
    latestRunCreatedAt: "2026-04-15T01:06:38.999Z",
    latestCommandExitAt: new Date("2026-04-15T01:17:54.000Z"),
  });

  assert.equal(decision.recoverable, true);
  assert.equal(decision.reason, "command_exit_after_run_start");
});

void test("decideRunningThreadRecovery keeps a running run non-recoverable when there is no command-exit evidence yet", () => {
  const decision = decideRunningThreadRecovery({
    latestRunStatus: "running",
    latestRunCreatedAt: "2026-04-15T01:06:38.999Z",
    latestCommandExitAt: null,
  });

  assert.equal(decision.recoverable, false);
  assert.equal(decision.reason, "no_command_exit_evidence");
});

void test("decideRunningThreadRecovery ignores exit markers that predate the current run", () => {
  const decision = decideRunningThreadRecovery({
    latestRunStatus: "running",
    latestRunCreatedAt: "2026-04-15T01:06:38.999Z",
    latestCommandExitAt: new Date("2026-04-15T00:01:01.000Z"),
  });

  assert.equal(decision.recoverable, false);
  assert.equal(decision.reason, "command_exit_predates_run");
});

void test("findLatestCommandExitAtInDirectory returns the newest command-exit marker under a thread workspace", async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "vibecfd-recovery-"));
  const early = path.join(
    root,
    "suboff",
    "openfoam-case",
    ".deerflow-command-exit-status",
  );
  const late = path.join(
    root,
    "suboff",
    "studies",
    "mesh-independence",
    "coarse",
    "openfoam-case",
    ".deerflow-command-exit-status",
  );

  await fs.mkdir(path.dirname(early), { recursive: true });
  await fs.mkdir(path.dirname(late), { recursive: true });
  await fs.writeFile(early, "0", "utf8");
  await fs.writeFile(late, "0", "utf8");
  await fs.utimes(early, new Date("2026-04-15T01:17:54.000Z"), new Date("2026-04-15T01:17:54.000Z"));
  await fs.utimes(late, new Date("2026-04-15T01:22:01.000Z"), new Date("2026-04-15T01:22:01.000Z"));

  const latest = await findLatestCommandExitAtInDirectory(root);

  assert.ok(latest instanceof Date);
  assert.equal(latest?.toISOString(), "2026-04-15T01:22:01.000Z");

  await fs.rm(root, { recursive: true, force: true });
});
