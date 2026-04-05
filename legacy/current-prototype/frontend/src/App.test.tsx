import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import * as api from "./lib/api";
import { createRunSummary } from "./test/fixtures";

vi.mock("./lib/api", () => ({
  listRuns: vi.fn(),
  getRun: vi.fn(),
  listRunEvents: vi.fn(),
  listRunAttempts: vi.fn(),
  submitTask: vi.fn(),
  confirmRun: vi.fn(),
  cancelRun: vi.fn(),
  retryRun: vi.fn()
}));

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.listRuns).mockResolvedValue([]);
    vi.mocked(api.listRunEvents).mockResolvedValue([]);
    vi.mocked(api.listRunAttempts).mockResolvedValue([]);
  });

  it("renders the Chinese workbench shell and primary command actions", async () => {
    render(<App />);

    expect(await screen.findByText("潜艇仿真工作台")).toBeInTheDocument();
    expect(screen.getByText("新建任务")).toBeInTheDocument();
    expect(screen.getByText("任务输入")).toBeInTheDocument();
    expect(screen.getByText("图形视图")).toBeInTheDocument();
    expect(screen.getByText("时间线")).toBeInTheDocument();
  });

  it("shows compact run history entries in the left sidebar", async () => {
    vi.mocked(api.listRuns).mockResolvedValue([
      createRunSummary({
        run_id: "run_demo_0007",
        status: "completed",
        request: {
          task_description: "查看某次尾流切片结果",
          task_type: "wake_field",
          geometry_family_hint: "Joubert BB2",
          geometry_file_name: "bb2.stl",
          operating_notes: "深潜稳态工况"
        }
      })
    ]);

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("tab", { name: /历史/ }));

    expect(await screen.findByText("run_demo_0007")).toBeInTheDocument();
    expect(screen.getByText("查看某次尾流切片结果")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "载入" })).toBeInTheDocument();
  });

  it("keeps the right inspector structurally complete even before a run is loaded", async () => {
    render(<App />);

    expect(await screen.findByRole("heading", { name: "关键指标" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "工具与产物" })).toBeInTheDocument();
  });

  it("opens the workflow dock first when an awaiting-confirmation run is loaded", async () => {
    const run = createRunSummary({
      workflow_draft: {
        summary: "建议先复用 SUBOFF 压力分布案例，再进入受控执行。",
        assumptions: ["默认深潜稳态工况"],
        recommended_case_ids: ["case_suboff_pressure"],
        linked_skills: ["case-search"],
        allowed_tools: ["case-search", "report-writer"],
        required_artifacts: ["pressure_distribution.svg", "final_report.md"],
        stages: [
          {
            stage_id: "prepare",
            title: "准备执行",
            description: "整理输入并检查几何。"
          }
        ]
      }
    });

    vi.mocked(api.listRuns).mockResolvedValue([run]);
    vi.mocked(api.getRun).mockResolvedValue(run);
    vi.mocked(api.listRunEvents).mockResolvedValue([]);
    vi.mocked(api.listRunAttempts).mockResolvedValue([]);

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("tab", { name: /历史/ }));
    await user.click(await screen.findByRole("button", { name: "载入" }));

    expect(await screen.findByRole("tab", { name: "流程详情" })).toHaveAttribute("aria-selected", "true");
  });

  it("keeps task-type labels localized instead of exposing internal identifiers", async () => {
    const run = createRunSummary({
      workflow_draft: {
        summary: "建议先复用 SUBOFF 压力分布案例，再进入受控执行。",
        assumptions: ["默认深潜稳态工况"],
        recommended_case_ids: ["case_suboff_pressure"],
        linked_skills: ["case-search"],
        allowed_tools: ["case-search", "report-writer"],
        required_artifacts: ["pressure_distribution.svg", "final_report.md"],
        stages: [
          {
            stage_id: "prepare",
            title: "准备执行",
            description: "整理输入并检查几何。"
          }
        ]
      },
      candidate_cases: [
        {
          case_id: "case_suboff_pressure",
          title: "SUBOFF 压力分布基线案例",
          geometry_family: "DARPA SUBOFF",
          geometry_description: "压力分布验证案例",
          task_type: "pressure_distribution",
          condition_tags: ["深潜"],
          input_requirements: ["stl"],
          expected_outputs: ["pressure_distribution.svg"],
          recommended_solver: "simpleFoam",
          mesh_strategy: "局部加密",
          bc_strategy: "速度入口",
          postprocess_steps: ["压力云图"],
          validation_targets: ["压力峰值"],
          reference_sources: [],
          reuse_role: "主案例",
          linked_skills: ["case-search"],
          score: 0.93,
          rationale: "任务类型与几何家族高度一致。"
        },
        {
          case_id: "case_suboff_drag",
          title: "SUBOFF 阻力复核案例",
          geometry_family: "DARPA SUBOFF",
          geometry_description: "阻力复核基线案例",
          task_type: "resistance",
          condition_tags: ["深潜"],
          input_requirements: ["stl"],
          expected_outputs: ["drag.csv"],
          recommended_solver: "simpleFoam",
          mesh_strategy: "局部加密",
          bc_strategy: "速度入口",
          postprocess_steps: ["阻力积分"],
          validation_targets: ["总阻力"],
          reference_sources: [],
          reuse_role: "辅助案例",
          linked_skills: ["case-search"],
          score: 0.82,
          rationale: "可作为阻力复核参考。"
        }
      ]
    });

    vi.mocked(api.listRuns).mockResolvedValue([run]);
    vi.mocked(api.getRun).mockResolvedValue(run);
    vi.mocked(api.listRunEvents).mockResolvedValue([]);
    vi.mocked(api.listRunAttempts).mockResolvedValue([]);

    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("tab", { name: /历史/ }));
    await user.click(await screen.findByRole("button", { name: "载入" }));

    expect(screen.queryByText("pressure_distribution")).not.toBeInTheDocument();
    expect(screen.queryByText("resistance")).not.toBeInTheDocument();
  });

  it("shows one focused left workspace panel at a time and lets users switch to history", async () => {
    vi.mocked(api.listRuns).mockResolvedValue([
      createRunSummary({
        run_id: "run_demo_0012",
        status: "completed",
        request: {
          task_description: "查看历史阻力结果",
          task_type: "resistance",
          geometry_family_hint: "DARPA SUBOFF",
          geometry_file_name: "suboff.stl",
          operating_notes: "深潜稳态工况"
        }
      })
    ]);

    const user = userEvent.setup();
    render(<App />);

    expect(await screen.findByRole("heading", { name: "任务输入" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "历史运行" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: /历史/ }));

    expect(await screen.findByRole("heading", { name: "历史运行" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "任务输入" })).not.toBeInTheDocument();
  });

  it("switches the left workspace to candidate cases when a matched run is loaded", async () => {
    const run = createRunSummary({
      candidate_cases: [
        {
          case_id: "case_suboff_pressure",
          title: "SUBOFF 压力分布基线案例",
          geometry_family: "DARPA SUBOFF",
          geometry_description: "压力分布验证案例",
          task_type: "pressure_distribution",
          condition_tags: ["深潜"],
          input_requirements: ["stl"],
          expected_outputs: ["pressure_distribution.svg"],
          recommended_solver: "simpleFoam",
          mesh_strategy: "局部加密",
          bc_strategy: "速度入口",
          postprocess_steps: ["压力云图"],
          validation_targets: ["压力峰值"],
          reference_sources: [],
          reuse_role: "主案例",
          linked_skills: ["case-search"],
          score: 0.93,
          rationale: "任务类型与几何家族高度一致。"
        }
      ]
    });

    vi.mocked(api.listRuns).mockResolvedValue([run]);
    vi.mocked(api.getRun).mockResolvedValue(run);
    vi.mocked(api.listRunEvents).mockResolvedValue([]);
    vi.mocked(api.listRunAttempts).mockResolvedValue([]);

    const user = userEvent.setup();
    render(<App />);

    expect(await screen.findByRole("heading", { name: "任务输入" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "候选案例" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: /历史/ }));
    await user.click(screen.getByRole("button", { name: "载入" }));

    expect(await screen.findByRole("heading", { name: "候选案例" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "任务输入" })).not.toBeInTheDocument();
  });
});
