import assert from "node:assert/strict";
import test from "node:test";

import {
  getAgentDisplayName,
  getAgentModelLabel,
  getAgentToolGroupLabel,
} from "./display.ts";

void test("getAgentDisplayName prefers localized display names for built-in agents", () => {
  assert.equal(
    getAgentDisplayName({ name: "codex-skill-creator", display_name: null }),
    "Codex 技能创建器",
  );
  assert.equal(
    getAgentDisplayName({ name: "claude-code-skill-creator", display_name: "" }),
    "Claude Code 技能创建器",
  );
});

void test("getAgentDisplayName keeps explicit display names and custom names", () => {
  assert.equal(
    getAgentDisplayName({
      name: "project-reviewer",
      display_name: "项目评审助手",
    }),
    "项目评审助手",
  );
  assert.equal(getAgentDisplayName(null, "project-reviewer"), "project-reviewer");
});

void test("getAgentToolGroupLabel localizes common tool groups", () => {
  assert.equal(getAgentToolGroupLabel("workspace"), "工作区");
  assert.equal(getAgentToolGroupLabel("skills"), "技能");
  assert.equal(getAgentToolGroupLabel("unknown-group"), "unknown-group");
});

void test("getAgentModelLabel humanizes common model ids", () => {
  assert.equal(getAgentModelLabel("gpt-5.4"), "GPT-5.4");
  assert.equal(getAgentModelLabel("claude-sonnet-4-6"), "Claude Sonnet 4.6");
  assert.equal(getAgentModelLabel("custom-model"), "custom-model");
});
