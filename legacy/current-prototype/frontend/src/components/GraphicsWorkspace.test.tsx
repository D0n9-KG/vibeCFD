import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { createRunSummary } from "../test/fixtures";
import { GraphicsWorkspace } from "./GraphicsWorkspace";

describe("GraphicsWorkspace", () => {
  it("renders a real 3D geometry viewport when a model artifact is available", () => {
    const run = createRunSummary({
      artifacts: [
        {
          label: "三维几何预览",
          category: "model",
          relative_path: "postprocess/models/geometry_preview.obj",
          mime_type: "model/obj",
          url: "/api/runs/run_20260321_0001/artifacts/postprocess/models/geometry_preview.obj"
        },
        {
          label: "压力分布图",
          category: "image",
          relative_path: "postprocess/images/pressure_distribution.svg",
          mime_type: "image/svg+xml",
          url: "/api/runs/run_20260321_0001/artifacts/postprocess/images/pressure_distribution.svg"
        }
      ]
    });

    render(<GraphicsWorkspace run={run} />);

    expect(screen.getByLabelText("三维几何视图")).toBeInTheDocument();
    expect(screen.getByText("三维几何预览")).toBeInTheDocument();
  });
});
