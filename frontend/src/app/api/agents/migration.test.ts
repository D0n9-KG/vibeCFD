import assert from "node:assert/strict";
import test from "node:test";

const migration = await import(new URL("./migration.ts", import.meta.url).href);

void test("mergeCanonicalAgentsWithLegacyAgents preserves backend agents and appends unmigrated legacy agents", () => {
  const merged = migration.mergeCanonicalAgentsWithLegacyAgents(
    [
      {
        name: "codex-skill-creator",
        description: "Built-in",
        display_name: "Codex Skill Creator",
        model: "gpt-5.4",
        tool_groups: ["workspace", "skills"],
        kind: "builtin",
        is_builtin: true,
        is_editable: false,
        is_deletable: false,
      },
      {
        name: "backend-agent",
        description: "Canonical backend agent",
        display_name: "Backend Agent",
        model: "gpt-5.4",
        tool_groups: ["workspace"],
        kind: "custom",
        is_builtin: false,
        is_editable: true,
        is_deletable: true,
      },
    ],
    [
      {
        name: "legacy-local",
        description: "Legacy local agent",
        display_name: "Legacy Local",
        model: "gpt-5.4",
        tool_groups: ["workspace"],
      },
      {
        name: "backend-agent",
        description: "Should be deduplicated",
        display_name: "Backend Agent",
        model: "gpt-5.4",
        tool_groups: ["workspace"],
      },
    ],
  );

  assert.deepEqual(
    merged.map((agent: { name: string }) => agent.name),
    ["backend-agent", "codex-skill-creator", "legacy-local"],
  );
  assert.equal(
    merged.find((agent: { name: string }) => agent.name === "legacy-local")
      ?.inventory_source,
    "legacy-local",
  );
  assert.equal(
    merged.find((agent: { name: string }) => agent.name === "backend-agent")
      ?.inventory_source,
    "backend",
  );
});
