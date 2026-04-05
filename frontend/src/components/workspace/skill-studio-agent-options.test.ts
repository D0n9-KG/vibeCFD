import assert from "node:assert/strict";
import test from "node:test";

import type { Agent } from "../../core/agents/types.ts";

const {
  buildSkillStudioAgentOptions,
  normalizeSkillStudioAgentLabel,
  resolveSkillStudioAgentSelection,
} = await import(
  new URL("./skill-studio-agent-options.ts", import.meta.url).href,
);

void test("buildSkillStudioAgentOptions keeps skill creators, prefers codex first, and uses display names", () => {
  const options = buildSkillStudioAgentOptions([
    {
      name: "claude-code-skill-creator",
      display_name: "Claude Code 技能创建器",
      description: "Dedicated Claude agent.",
      model: "claude-sonnet-4-6",
      tool_groups: null,
    },
    {
      name: "general-researcher",
      display_name: "General Researcher",
      description: "Not for Skill Studio",
      model: null,
      tool_groups: null,
    },
    {
      name: "codex-skill-creator",
      display_name: "Codex 技能创建器",
      description: "Dedicated Codex agent.",
      model: "gpt-5.4",
      tool_groups: null,
    },
  ] satisfies Agent[]);

  assert.deepEqual(
    options.map((option) => ({
      name: option.name,
      label: option.label,
    })),
    [
      {
        name: "codex-skill-creator",
        label: "Codex 技能创建器",
      },
      {
        name: "claude-code-skill-creator",
        label: "Claude Code 技能创建器",
      },
    ],
  );
});

void test("normalizeSkillStudioAgentLabel upgrades legacy skill creator labels", () => {
  assert.equal(
    normalizeSkillStudioAgentLabel("Codex · Skill Creator", "codex-skill-creator"),
    "Codex 技能创建器",
  );
  assert.equal(
    normalizeSkillStudioAgentLabel(
      "Claude Code · Skill Creator",
      "claude-code-skill-creator",
    ),
    "Claude Code 技能创建器",
  );
});

void test("resolveSkillStudioAgentSelection prefers the thread assistant when it is available", () => {
  const options = buildSkillStudioAgentOptions([
    {
      name: "codex-skill-creator",
      display_name: "Codex 技能创建器",
      description: "Dedicated Codex agent.",
      model: "gpt-5.4",
      tool_groups: null,
    },
    {
      name: "claude-code-skill-creator",
      display_name: "Claude Code 技能创建器",
      description: "Dedicated Claude agent.",
      model: "claude-sonnet-4-6",
      tool_groups: null,
    },
  ] satisfies Agent[]);

  assert.equal(
    resolveSkillStudioAgentSelection({
      selectedAgentName: null,
      persistedAssistantMode: "claude-code-skill-creator",
      options,
    }),
    "claude-code-skill-creator",
  );
});

void test("resolveSkillStudioAgentSelection falls back to codex for fresh threads", () => {
  assert.equal(
    resolveSkillStudioAgentSelection({
      selectedAgentName: null,
      persistedAssistantMode: null,
      options: [],
    }),
    "codex-skill-creator",
  );
});
