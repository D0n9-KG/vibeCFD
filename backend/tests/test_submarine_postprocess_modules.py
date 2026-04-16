import importlib


def test_postprocess_specs_module_preserves_requested_output_contracts():
    specs_module = importlib.import_module("deerflow.domain.submarine.postprocess_specs")

    requested_outputs = [
        {
            "output_id": "surface_pressure_contour",
            "postprocess_spec": {
                "field": "p",
                "selector": {
                    "type": "patch",
                    "patches": ["pressureHull", "sail"],
                },
                "formats": ["csv", "png", "report"],
            },
        },
        {
            "output_id": "wake_velocity_slice",
            "postprocess_spec": {
                "field": "U",
                "selector": {
                    "type": "plane",
                    "origin_mode": "x_by_lref",
                    "origin_value": 2.0,
                    "normal": [0.0, 1.0, 0.0],
                },
                "formats": ["csv", "report"],
            },
        },
    ]

    function_objects = specs_module.render_requested_postprocess_function_objects(
        requested_outputs=requested_outputs,
        reference_length_m=4.0,
    )

    assert specs_module.requested_output_ids(requested_outputs) == {
        "surface_pressure_contour",
        "wake_velocity_slice",
    }
    assert "surfacePressure" in function_objects
    assert "patches     (pressureHull sail);" in function_objects
    assert "wakeVelocitySlice" in function_objects
    assert "point   (8.0 0 0);" in function_objects
    assert "normal  (0.0 1.0 0.0);" in function_objects
    assert (
        specs_module.selector_summary(
            "wake_velocity_slice",
            requested_outputs[1],
        )
        == "Plane slice at x/Lref=2 with normal (0.0, 1.0, 0.0)"
    )
    assert specs_module.requested_output_formats(
        "wake_velocity_slice",
        requested_outputs[1],
    ) == {"csv", "report"}


def test_postprocess_render_module_builds_preview_and_figure_metadata(tmp_path):
    render_module = importlib.import_module("deerflow.domain.submarine.postprocess_render")

    csv_path = tmp_path / "surface-pressure.csv"
    png_path = tmp_path / "surface-pressure.png"
    csv_path.write_text(
        "\n".join(
            [
                "x,y,z,p",
                "0.0,0.0,0.0,12.0",
                "1.0,0.2,0.1,10.5",
            ]
        ),
        encoding="utf-8",
    )

    rendered = render_module.render_requested_postprocess_png(
        output_id="surface_pressure_contour",
        csv_path=csv_path,
        png_path=png_path,
        requested_output={
            "output_id": "surface_pressure_contour",
            "postprocess_spec": {
                "field": "p",
                "selector": {
                    "type": "patch",
                    "patches": ["hull"],
                },
                "formats": ["csv", "png", "report"],
            },
        },
    )
    figure_item = render_module.build_figure_item(
        output_id="surface_pressure_contour",
        export_spec={
            "title": "Surface Pressure Result",
            "summary": "Exported surface pressure samples.",
        },
        run_dir_name="render-demo",
        csv_path=csv_path,
        csv_virtual_path="/mnt/user-data/outputs/submarine/solver-dispatch/render-demo/surface-pressure.csv",
        markdown_virtual_path="/mnt/user-data/outputs/submarine/solver-dispatch/render-demo/surface-pressure.md",
        image_virtual_path="/mnt/user-data/outputs/submarine/solver-dispatch/render-demo/surface-pressure.png",
        requested_output={
            "output_id": "surface_pressure_contour",
            "postprocess_spec": {
                "field": "p",
                "selector": {
                    "type": "patch",
                    "patches": ["hull"],
                },
                "formats": ["csv", "png", "report"],
            },
        },
        render_status="rendered",
    )
    markdown = render_module.render_postprocess_export_markdown(
        export_spec={
            "title": "Surface Pressure Result",
            "summary": "Exported surface pressure samples.",
        },
        header=["x", "y", "z", "p"],
        data_row_count=2,
        png_virtual_path="/mnt/user-data/outputs/submarine/solver-dispatch/render-demo/surface-pressure.png",
    )

    assert rendered is True
    assert png_path.exists()
    assert figure_item["figure_id"] == "render-demo:surface_pressure_contour"
    assert figure_item["field"] == "p"
    assert figure_item["selector_summary"] == "Patch selection: hull"
    assert figure_item["axes"] == ["x", "y"]
    assert figure_item["color_metric"] == "p"
    assert figure_item["sample_count"] == 2
    assert figure_item["value_range"] == {"min": 10.5, "max": 12.0}
    assert "Surface Pressure Result" in markdown
    assert "Data row count: `2`" in markdown
