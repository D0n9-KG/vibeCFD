from pathlib import Path

from langchain.agents.middleware.types import ModelResponse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


class _FakeModelRequest:
    def __init__(self, *, state, messages, system_message=None):
        self.state = state
        self.messages = messages
        self.system_message = system_message

    def override(self, **kwargs):
        return _FakeModelRequest(
            state=kwargs.get("state", self.state),
            messages=kwargs.get("messages", self.messages),
            system_message=kwargs.get("system_message", self.system_message),
        )


def test_openfoam_seed_workflow_middleware_appends_structured_handoff_reminder(
    tmp_path: Path,
):
    import importlib

    middleware_module = importlib.import_module(
        "deerflow.agents.middlewares.openfoam_seed_workflow_middleware"
    )

    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "blockMeshDict").write_text("FoamFile{}", encoding="utf-8")

    request = _FakeModelRequest(
        state={
            "thread_data": {"uploads_path": str(uploads_dir)},
            "uploaded_files": [
                {
                    "filename": "blockMeshDict",
                    "path": "/mnt/user-data/uploads/blockMeshDict",
                }
            ],
        },
        messages=[
            HumanMessage(
                content="Please organize the design brief first, then assemble the uploaded OpenFOAM seed, run it, and produce the report."
            )
        ],
        system_message=SystemMessage(content="base prompt"),
    )

    middleware = middleware_module.OpenfoamSeedWorkflowMiddleware()
    captured = middleware.wrap_model_call(request, lambda next_request: next_request)

    assert "submarine_design_brief" in str(captured.system_message.content)
    assert "generic acknowledgement" in str(captured.system_message.content)
    assert len(captured.messages) == 2
    assert "submarine_result_report" in str(captured.messages[-1].content)
    assert "submarine_solver_dispatch" in str(captured.messages[-1].content)
    assert "write_todos" in str(captured.messages[-1].content)


def test_openfoam_seed_workflow_middleware_skips_non_seed_threads(tmp_path: Path):
    import importlib

    middleware_module = importlib.import_module(
        "deerflow.agents.middlewares.openfoam_seed_workflow_middleware"
    )

    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "notes.txt").write_text("plain text", encoding="utf-8")

    request = _FakeModelRequest(
        state={
            "thread_data": {"uploads_path": str(uploads_dir)},
            "uploaded_files": [
                {
                    "filename": "notes.txt",
                    "path": "/mnt/user-data/uploads/notes.txt",
                }
            ],
        },
        messages=[HumanMessage(content="Please continue working on this plain text note.")],
        system_message=SystemMessage(content="base prompt"),
    )

    middleware = middleware_module.OpenfoamSeedWorkflowMiddleware()
    captured = middleware.wrap_model_call(request, lambda next_request: next_request)

    assert str(captured.system_message.content) == "base prompt"


def test_openfoam_seed_workflow_middleware_uses_message_level_file_metadata_when_state_has_not_synced(
    tmp_path: Path,
):
    import importlib

    middleware_module = importlib.import_module(
        "deerflow.agents.middlewares.openfoam_seed_workflow_middleware"
    )

    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "blockMeshDict").write_text("FoamFile{}", encoding="utf-8")

    request = _FakeModelRequest(
        state={
            "thread_data": {"uploads_path": str(uploads_dir)},
            "uploaded_files": [],
        },
        messages=[
            HumanMessage(
                content="Please organize the design brief first, then assemble the uploaded OpenFOAM seed, run it, and produce the report.",
                additional_kwargs={
                    "files": [
                        {
                            "filename": "blockMeshDict",
                            "path": "/mnt/user-data/uploads/blockMeshDict",
                        }
                    ]
                },
            )
        ],
        system_message=SystemMessage(content="base prompt"),
    )

    middleware = middleware_module.OpenfoamSeedWorkflowMiddleware()
    captured = middleware.wrap_model_call(request, lambda next_request: next_request)

    assert "submarine_design_brief" in str(captured.system_message.content)


def test_openfoam_seed_workflow_middleware_retries_when_first_model_reply_is_generic_ack(
    tmp_path: Path,
):
    import importlib

    middleware_module = importlib.import_module(
        "deerflow.agents.middlewares.openfoam_seed_workflow_middleware"
    )

    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "blockMeshDict").write_text("FoamFile{}", encoding="utf-8")

    request = _FakeModelRequest(
        state={
            "thread_data": {"uploads_path": str(uploads_dir)},
            "uploaded_files": [
                {
                    "filename": "blockMeshDict",
                    "path": "/mnt/user-data/uploads/blockMeshDict",
                }
            ],
        },
        messages=[
            HumanMessage(
                content="Please organize the design brief first, then assemble the uploaded OpenFOAM seed, run it, and produce the report."
            )
        ],
        system_message=SystemMessage(content="base prompt"),
    )

    seen_requests: list[_FakeModelRequest] = []

    def _handler(next_request):
        seen_requests.append(next_request)
        if len(seen_requests) == 1:
            return ModelResponse(
                result=[
                    AIMessage(
                        content="I'll continue from the latest request and ask only if a blocking detail is missing."
                    )
                ]
            )
        return ModelResponse(
            result=[
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "submarine_design_brief",
                            "args": {"task_description": "seed flow"},
                            "id": "call_retry_design_brief",
                            "type": "tool_call",
                        }
                    ],
                )
            ]
        )

    middleware = middleware_module.OpenfoamSeedWorkflowMiddleware()
    captured = middleware.wrap_model_call(request, _handler)

    assert len(seen_requests) == 2
    assert "Call the next required CFD tool now" in str(seen_requests[-1].messages[-1].content)
    assert captured.result[0].tool_calls[0]["name"] == "submarine_design_brief"


def test_openfoam_seed_workflow_middleware_forces_design_brief_when_seed_thread_reply_has_no_tool_call(
    tmp_path: Path,
):
    import importlib

    middleware_module = importlib.import_module(
        "deerflow.agents.middlewares.openfoam_seed_workflow_middleware"
    )

    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "blockMeshDict").write_text("FoamFile{}", encoding="utf-8")

    request = _FakeModelRequest(
        state={
            "thread_data": {"uploads_path": str(uploads_dir)},
            "uploaded_files": [
                {
                    "filename": "blockMeshDict",
                    "path": "/mnt/user-data/uploads/blockMeshDict",
                }
            ],
        },
        messages=[
            HumanMessage(
                content="Please use the uploaded OpenFOAM seed, assemble the official case, run it, and produce the report."
            )
        ],
        system_message=SystemMessage(content="base prompt"),
    )

    middleware = middleware_module.OpenfoamSeedWorkflowMiddleware()
    captured = middleware.wrap_model_call(
        request,
        lambda next_request: ModelResponse(
            result=[AIMessage(content="I will summarize the plan before acting.")]
        ),
    )

    assert captured.result[0].tool_calls[0]["name"] == "submarine_design_brief"
    assert (
        captured.result[0].tool_calls[0]["args"]["task_description"]
        == "Please use the uploaded OpenFOAM seed, assemble the official case, run it, and produce the report."
    )
    assert captured.result[0].tool_calls[0]["args"]["confirmation_status"] == "confirmed"
    assert captured.result[0].tool_calls[0]["args"]["execution_preference"] == "execute_now"


def test_openfoam_seed_workflow_middleware_forces_design_brief_for_seed_input_handoff_without_run_verbs(
    tmp_path: Path,
):
    import importlib

    middleware_module = importlib.import_module(
        "deerflow.agents.middlewares.openfoam_seed_workflow_middleware"
    )

    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "pitzDaily.blockMeshDict").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    request = _FakeModelRequest(
        state={
            "thread_data": {"uploads_path": str(uploads_dir)},
            "uploaded_files": [
                {
                    "filename": "pitzDaily.blockMeshDict",
                    "path": "/mnt/user-data/uploads/pitzDaily.blockMeshDict",
                }
            ],
        },
        messages=[
            HumanMessage(
                content="Please use the uploaded pitzDaily seed as the case input."
            )
        ],
        system_message=SystemMessage(content="base prompt"),
    )

    middleware = middleware_module.OpenfoamSeedWorkflowMiddleware()
    captured = middleware.wrap_model_call(
        request,
        lambda next_request: ModelResponse(
            result=[AIMessage(content="I will inspect the file before deciding.")]
        ),
    )

    assert captured.result[0].tool_calls[0]["name"] == "submarine_design_brief"
    assert (
        captured.result[0].tool_calls[0]["args"]["task_description"]
        == "Please use the uploaded pitzDaily seed as the case input."
    )
    assert "confirmation_status" not in captured.result[0].tool_calls[0]["args"]
    assert "execution_preference" not in captured.result[0].tool_calls[0]["args"]


def test_openfoam_seed_workflow_middleware_forces_design_brief_for_real_chinese_seed_request(
    tmp_path: Path,
):
    import importlib

    middleware_module = importlib.import_module(
        "deerflow.agents.middlewares.openfoam_seed_workflow_middleware"
    )

    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "blockMeshDict").write_text("FoamFile{}", encoding="utf-8")

    request = _FakeModelRequest(
        state={
            "thread_data": {"uploads_path": str(uploads_dir)},
            "uploaded_files": [
                {
                    "filename": "blockMeshDict",
                    "path": "/mnt/user-data/uploads/blockMeshDict",
                }
            ],
        },
        messages=[
            HumanMessage(
                content=(
                    "继续推进，不需要再等我补充。请直接把这个 blockMeshDict 当作 "
                    "OpenFOAM 官方 cavity seed 输入，先生成结构化设计简报，再按默认设置"
                    "组装并执行案例，最后输出最终结果报告。"
                ),
                additional_kwargs={
                    "files": [
                        {
                            "filename": "blockMeshDict",
                            "path": "/mnt/user-data/uploads/blockMeshDict",
                        }
                    ]
                },
            )
        ],
        system_message=SystemMessage(content="base prompt"),
    )

    middleware = middleware_module.OpenfoamSeedWorkflowMiddleware()
    captured = middleware.wrap_model_call(
        request,
        lambda next_request: ModelResponse(
            result=[AIMessage(content="我先根据你刚才的输入继续推进；如需补充我会明确说明。")]
        ),
    )

    assert captured.result[0].tool_calls[0]["name"] == "submarine_design_brief"
    assert "blockMeshDict 当作 OpenFOAM 官方 cavity seed 输入" in captured.result[0].tool_calls[0]["args"]["task_description"]
    assert captured.result[0].tool_calls[0]["args"]["confirmation_status"] == "confirmed"
    assert captured.result[0].tool_calls[0]["args"]["execution_preference"] == "execute_now"


def test_openfoam_seed_workflow_middleware_forces_solver_dispatch_after_confirmed_seed_brief(
    tmp_path: Path,
):
    import importlib

    middleware_module = importlib.import_module(
        "deerflow.agents.middlewares.openfoam_seed_workflow_middleware"
    )

    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "blockMeshDict").write_text("FoamFile{}", encoding="utf-8")

    request = _FakeModelRequest(
        state={
            "thread_data": {"uploads_path": str(uploads_dir)},
            "uploaded_files": [
                {
                    "filename": "blockMeshDict",
                    "path": "/mnt/user-data/uploads/blockMeshDict",
                }
            ],
            "submarine_runtime": {
                "current_stage": "task-intelligence",
                "task_summary": "Use the official cavity defaults and run the case.",
                "task_type": "official_openfoam_case",
                "input_source_type": "openfoam_case_seed",
                "official_case_id": "cavity",
                "confirmation_status": "confirmed",
                "execution_preference": "execute_now",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "solver-dispatch",
            },
        },
        messages=[HumanMessage(content="Continue and actually run the uploaded official case.")],
        system_message=SystemMessage(content="base prompt"),
    )

    middleware = middleware_module.OpenfoamSeedWorkflowMiddleware()
    captured = middleware.wrap_model_call(
        request,
        lambda next_request: ModelResponse(
            result=[AIMessage(content="I will keep working on it.")]
        ),
    )

    assert captured.result[0].tool_calls[0]["name"] == "submarine_solver_dispatch"
    assert (
        captured.result[0].tool_calls[0]["args"]["task_description"]
        == "Use the official cavity defaults and run the case."
    )
    assert captured.result[0].tool_calls[0]["args"]["task_type"] == "official_openfoam_case"
    assert captured.result[0].tool_calls[0]["args"]["execute_now"] is True


def test_openfoam_seed_workflow_middleware_forces_result_report_after_executed_seed_dispatch(
    tmp_path: Path,
):
    import importlib

    middleware_module = importlib.import_module(
        "deerflow.agents.middlewares.openfoam_seed_workflow_middleware"
    )

    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "blockMeshDict").write_text("FoamFile{}", encoding="utf-8")

    request = _FakeModelRequest(
        state={
            "thread_data": {"uploads_path": str(uploads_dir)},
            "uploaded_files": [
                {
                    "filename": "blockMeshDict",
                    "path": "/mnt/user-data/uploads/blockMeshDict",
                }
            ],
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Use the official cavity defaults and run the case.",
                "input_source_type": "openfoam_case_seed",
                "official_case_id": "cavity",
                "confirmation_status": "confirmed",
                "review_status": "ready_for_supervisor",
                "stage_status": "executed",
                "next_recommended_stage": "result-reporting",
            },
        },
        messages=[HumanMessage(content="Continue and finish the report for this official case.")],
        system_message=SystemMessage(content="base prompt"),
    )

    middleware = middleware_module.OpenfoamSeedWorkflowMiddleware()
    captured = middleware.wrap_model_call(
        request,
        lambda next_request: ModelResponse(
            result=[AIMessage(content="I will continue and wrap it up.")]
        ),
    )

    assert captured.result[0].tool_calls[0]["name"] == "submarine_result_report"
    assert captured.result[0].tool_calls[0]["args"] == {}
