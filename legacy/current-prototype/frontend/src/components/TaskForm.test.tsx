import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TaskForm } from "./TaskForm";

describe("TaskForm", () => {
  it("renders the full vertical task form without nested section tabs", () => {
    render(<TaskForm onSubmit={vi.fn().mockResolvedValue(undefined)} />);

    expect(screen.getByLabelText("任务说明")).toBeInTheDocument();
    expect(screen.getByLabelText("任务类型")).toBeInTheDocument();
    expect(screen.getByLabelText("几何家族")).toBeInTheDocument();
    expect(screen.getByLabelText("工况说明")).toBeInTheDocument();
    expect(screen.getByLabelText("几何文件")).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "基础任务" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "工况设置" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "文件导入" })).not.toBeInTheDocument();
  });
});
