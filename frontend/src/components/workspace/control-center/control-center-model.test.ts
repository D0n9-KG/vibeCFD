import assert from "node:assert/strict";
import test from "node:test";

const {
  buildOrphanAuditSummary,
  buildStageRoleSkillSummaries,
  filterAgents,
  filterStageRoleSkillSummaries,
  filterAndSortOrphans,
} = await import(new URL("./control-center-model.ts", import.meta.url).href);

void test("buildStageRoleSkillSummaries maps lifecycle bindings onto runtime stage roles", () => {
  const summaries = buildStageRoleSkillSummaries(
    [
      {
        role_id: "solver-dispatch",
        subagent_name: "submarine-solver-dispatch",
        display_title: "求解调度",
        model_mode: "explicit",
        effective_model: "gpt-5.4",
        config_source: "runtime-config",
        timeout_seconds: 900,
      },
      {
        role_id: "scientific-verification",
        subagent_name: "submarine-scientific-verification",
        display_title: "科学核验",
        model_mode: "inherit",
        effective_model: "claude-sonnet-4-6",
        config_source: "builtin:subagent",
        timeout_seconds: 1200,
      },
    ],
    [
      {
        skill_name: "submarine-solver-dispatch",
        enabled: true,
        binding_targets: [
          {
            role_id: "solver-dispatch",
            mode: "explicit",
            target_skills: ["submarine-solver-dispatch"],
          },
        ],
      },
      {
        skill_name: "submarine-shared-guard",
        enabled: true,
        binding_targets: [
          {
            role_id: "solver-dispatch",
            mode: "explicit",
            target_skills: [],
          },
          {
            role_id: "scientific-verification",
            mode: "explicit",
            target_skills: ["submarine-shared-guard"],
          },
        ],
      },
      {
        skill_name: "disabled-skill",
        enabled: false,
        binding_targets: [
          {
            role_id: "scientific-verification",
            mode: "explicit",
            target_skills: ["disabled-skill"],
          },
        ],
      },
    ],
  );

  assert.deepEqual(
    summaries.map((item) => ({
      roleId: item.role_id,
      skillCount: item.assigned_skills.length,
      assignedSkills: item.assigned_skills,
    })),
    [
      {
        roleId: "solver-dispatch",
        skillCount: 2,
        assignedSkills: ["submarine-shared-guard", "submarine-solver-dispatch"],
      },
      {
        roleId: "scientific-verification",
        skillCount: 1,
        assignedSkills: ["submarine-shared-guard"],
      },
    ],
  );
});

void test("buildOrphanAuditSummary totals orphan counts, files, and byte distribution", () => {
  const summary = buildOrphanAuditSummary([
    {
      thread_id: "alpha",
      thread_dir: "/tmp/alpha",
      total_files: 5,
      total_bytes: 4096,
      langgraph_state: { status: "missing", can_delete: false },
    },
    {
      thread_id: "beta",
      thread_dir: "/tmp/beta",
      total_files: 0,
      total_bytes: 0,
      langgraph_state: { status: "missing", can_delete: false },
    },
  ]);

  assert.deepEqual(summary, {
    orphan_count: 2,
    occupied_orphan_count: 1,
    zero_byte_orphan_count: 1,
    total_files: 5,
    total_bytes: 4096,
    largest_orphan_bytes: 4096,
  });
});

void test("filterAndSortOrphans filters by search term, hides zero-byte leftovers when requested, and sorts by size", () => {
  const filtered = filterAndSortOrphans(
    [
      {
        thread_id: "small-match",
        thread_dir: "/tmp/demo/small-match",
        total_files: 2,
        total_bytes: 1024,
        langgraph_state: { status: "missing", can_delete: false },
      },
      {
        thread_id: "large-match",
        thread_dir: "/tmp/demo/large-match",
        total_files: 9,
        total_bytes: 8192,
        langgraph_state: { status: "missing", can_delete: false },
      },
      {
        thread_id: "empty-match",
        thread_dir: "/tmp/demo/empty-match",
        total_files: 0,
        total_bytes: 0,
        langgraph_state: { status: "missing", can_delete: false },
      },
      {
        thread_id: "other-thread",
        thread_dir: "/tmp/demo/other-thread",
        total_files: 4,
        total_bytes: 4096,
        langgraph_state: { status: "missing", can_delete: false },
      },
    ],
    {
      search: "match",
      includeZeroByte: false,
    },
  );

  assert.deepEqual(
    filtered.map((item) => item.thread_id),
    ["large-match", "small-match"],
  );
});

void test("filterAgents matches agent search across name, description, model, tool groups, and migration source", () => {
  const filtered = filterAgents(
    [
      {
        name: "codex-skill-builder",
        display_name: "Codex 技能创建器",
        description: "负责技能工作台中的技能编写与校验。",
        model: "gpt-5.4",
        tool_groups: ["workspace", "skills"],
        inventory_source: "backend",
      },
      {
        name: "legacy-claude-agent",
        display_name: "Claude 历史智能体",
        description: "从本地旧清单迁移而来。",
        model: "claude-sonnet-4-6",
        tool_groups: ["workspace"],
        inventory_source: "legacy-local",
      },
      {
        name: "solver-helper",
        display_name: "求解助手",
        description: "处理后续求解任务。",
        model: null,
        tool_groups: null,
        inventory_source: "backend",
      },
    ],
    "legacy",
  );

  assert.deepEqual(filtered.map((agent) => agent.name), ["legacy-claude-agent"]);
  assert.deepEqual(filterAgents(filtered, "claude").map((agent) => agent.name), [
    "legacy-claude-agent",
  ]);
  assert.deepEqual(
    filterAgents(
      [
        {
          name: "codex-skill-builder",
          display_name: "Codex 技能创建器",
          description: "负责技能工作台中的技能编写与校验。",
          model: "gpt-5.4",
          tool_groups: ["workspace", "skills"],
          inventory_source: "backend",
        },
      ],
      "skills",
    ).map((agent) => agent.name),
    ["codex-skill-builder"],
  );
});

void test("filterStageRoleSkillSummaries matches execution subagents by title, name, model, and assigned skills", () => {
  const filtered = filterStageRoleSkillSummaries(
    [
      {
        role_id: "solver-dispatch",
        subagent_name: "submarine-solver-dispatch",
        display_title: "求解调度",
        model_mode: "explicit",
        effective_model: "gpt-5.4",
        config_source: "runtime-config",
        timeout_seconds: 900,
        assigned_skills: ["solver-planner", "mesh-guard"],
      },
      {
        role_id: "scientific-verification",
        subagent_name: "submarine-scientific-verification",
        display_title: "科学核验",
        model_mode: "inherit",
        effective_model: "claude-sonnet-4-6",
        config_source: "builtin:subagent",
        timeout_seconds: 900,
        assigned_skills: ["report-checker"],
      },
    ],
    "mesh",
  );

  assert.deepEqual(filtered.map((stageRole) => stageRole.role_id), [
    "solver-dispatch",
  ]);
  assert.deepEqual(
    filterStageRoleSkillSummaries(filtered, "gpt-5.4").map(
      (stageRole) => stageRole.role_id,
    ),
    ["solver-dispatch"],
  );
});
