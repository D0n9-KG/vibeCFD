from deerflow.tools.builtins.submarine_runtime_context import (
    infer_execution_preference,
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
