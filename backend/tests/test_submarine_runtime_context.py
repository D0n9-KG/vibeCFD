from deerflow.tools.builtins.submarine_runtime_context import (
    infer_execution_preference,
    resolve_execution_preference,
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
