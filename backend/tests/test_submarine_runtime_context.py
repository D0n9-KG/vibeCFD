from pathlib import Path

from deerflow.tools.builtins.submarine_runtime_context import (
    infer_execution_preference,
    requires_user_confirmation,
    resolve_bound_geometry_virtual_path,
    resolve_execution_preference,
    resolve_task_summary,
)


def test_infer_execution_preference_treats_confirm_then_execute_as_preflight():
    assert (
        infer_execution_preference("确认方案，开始执行。")
        == "preflight_then_execute"
    )
    assert (
        infer_execution_preference("确认后按当前方案继续执行")
        == "preflight_then_execute"
    )
    assert (
        infer_execution_preference("确认方案后先预检再执行")
        == "preflight_then_execute"
    )


def test_resolve_execution_preference_falls_back_to_confirm_then_execute_intent():
    assert (
        resolve_execution_preference(
            explicit_preference=None,
            existing_runtime=None,
            existing_brief=None,
            task_description="请确认当前方案，然后继续执行这次 CFD 计算。",
        )
        == "preflight_then_execute"
    )


def test_infer_execution_preference_treats_do_not_start_solver_as_plan_only():
    assert (
        infer_execution_preference(
            "请先对这个 STL 做几何可用性预检，并给出后续 CFD 准备建议；当前不要启动求解。"
        )
        == "plan_only"
    )


def test_requires_user_confirmation_allows_plan_only_geometry_preflight_before_brief_confirmation():
    assert (
        requires_user_confirmation(
            existing_runtime={
                "confirmation_status": "draft",
                "execution_preference": "plan_only",
                "review_status": "needs_user_confirmation",
                "next_recommended_stage": "user-confirmation",
            },
            existing_brief=None,
            target_stage="geometry-preflight",
        )
        is False
    )


def test_requires_user_confirmation_still_blocks_plan_only_solver_dispatch_before_brief_confirmation():
    assert (
        requires_user_confirmation(
            existing_runtime={
                "confirmation_status": "draft",
                "execution_preference": "plan_only",
                "review_status": "needs_user_confirmation",
                "next_recommended_stage": "user-confirmation",
            },
            existing_brief=None,
            target_stage="solver-dispatch",
        )
        is True
    )


def test_resolve_task_summary_prefers_design_brief_contract():
    assert (
        resolve_task_summary(
            explicit_task_description="Run geometry preflight for the confirmed brief",
            existing_runtime={
                "task_summary": "Geometry preflight completed for the uploaded STL."
            },
            existing_brief={
                "task_description": "Execute the confirmed 5 m/s baseline CFD study."
            },
            fallback_task_description="Prepare a submarine CFD run",
        )
        == "Execute the confirmed 5 m/s baseline CFD study."
    )


def test_resolve_task_summary_falls_back_when_no_design_brief_exists():
    assert (
        resolve_task_summary(
            explicit_task_description="Inspect the uploaded geometry for resistance CFD.",
            existing_runtime=None,
            existing_brief=None,
            fallback_task_description="Prepare a submarine CFD run",
        )
        == "Inspect the uploaded geometry for resistance CFD."
    )


def test_resolve_bound_geometry_virtual_path_recovers_uploaded_files_candidate(tmp_path, monkeypatch):
    uploads_dir = tmp_path / "threads" / "thread-1" / "user-data" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    geometry_path = uploads_dir / "uploaded-from-state.stl"
    geometry_path.write_text("solid demo\nendsolid demo\n", encoding="utf-8")

    monkeypatch.setattr(
        "deerflow.tools.builtins.submarine_runtime_context.get_paths",
        lambda: type(
            "FakePaths",
            (),
            {"resolve_virtual_path": staticmethod(lambda thread_id, path: uploads_dir / Path(path).name)},
        )(),
    )

    resolved = resolve_bound_geometry_virtual_path(
        thread_id="thread-1",
        uploads_dir=uploads_dir,
        explicit_geometry_path=None,
        existing_runtime=None,
        existing_brief=None,
        uploaded_files=[
            {
                "filename": "uploaded-from-state.stl",
                "path": "/mnt/user-data/uploads/uploaded-from-state.stl",
            }
        ],
    )

    assert resolved == "/mnt/user-data/uploads/uploaded-from-state.stl"


def test_resolve_bound_geometry_virtual_path_falls_back_to_latest_upload_when_bound_candidates_missing(
    tmp_path,
):
    uploads_dir = tmp_path / "threads" / "thread-1" / "user-data" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    older = uploads_dir / "older.stl"
    newer = uploads_dir / "newer.stl"
    older.write_text("solid older\nendsolid older\n", encoding="utf-8")
    newer.write_text("solid newer\nendsolid newer\n", encoding="utf-8")
    older.touch()
    newer.touch()

    resolved = resolve_bound_geometry_virtual_path(
        thread_id="thread-1",
        uploads_dir=uploads_dir,
        explicit_geometry_path="/mnt/user-data/uploads/missing.stl",
        existing_runtime={"geometry_virtual_path": "/mnt/user-data/uploads/also-missing.stl"},
        existing_brief=None,
        uploaded_files=None,
    )

    assert resolved == "/mnt/user-data/uploads/newer.stl"
