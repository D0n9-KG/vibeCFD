from __future__ import annotations

from typing import override

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import (
    ModelCallResult,
    ModelRequest,
    ModelResponse,
)
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from deerflow.agents.thread_state import ThreadState
from deerflow.tools.builtins.submarine_runtime_context import (
    detect_execution_preference_signal,
)

_OPENFOAM_SEED_WORKFLOW_REMINDER = """<openfoam_seed_workflow_reminder>
The current thread already contains a supported OpenFOAM seed upload and the latest user request asks for concrete CFD progress.
Do not end this turn with a generic acknowledgement.
Use `submarine_design_brief` now so the structured CFD contract becomes visible.
If the brief confirms execution, continue with `submarine_solver_dispatch`.
If the dispatch completes, continue with `submarine_result_report`.
Using `write_todos` alone is not sufficient for this request.
If required information is truly missing, ask only for the exact blocking item.
</openfoam_seed_workflow_reminder>"""

_OPENFOAM_SEED_WORKFLOW_REMINDER_NAME = "openfoam_seed_workflow_reminder"
_OPENFOAM_SEED_WORKFLOW_RETRY_NAME = "openfoam_seed_workflow_retry"
_OPENFOAM_SEED_WORKFLOW_RETRY_REMINDER = """<openfoam_seed_workflow_retry>
The previous draft response stopped before using the required CFD tools.
Do not send a plain-text progress acknowledgement.
Call the next required CFD tool now.
</openfoam_seed_workflow_retry>"""

_ACTION_HINTS = (
    "assemble",
    "组装",
    "design brief",
    "设计简报",
    "dispatch",
    "派发",
    "report",
    "报告",
    "run",
    "运行",
    "solve",
    "执行",
    "求解",
    "计算",
)

_SEED_HANDOFF_HINTS = (
    "use the uploaded",
    "use uploaded",
    "uploaded seed",
    "case seed",
    "seed as input",
    "case input",
    "treat the uploaded",
    "as the case input",
    "as input",
    "blockmeshdict as",
    "\u5f53\u4f5c\u8f93\u5165",
    "\u4f5c\u4e3a\u8f93\u5165",
    "\u7528\u6211\u4e0a\u4f20\u7684",
    "\u7528\u8fd9\u4e2a seed",
    "\u628a\u6211\u4e0a\u4f20\u7684",
    "\u628a\u8fd9\u4e2a",
)

_EXECUTION_PROGRESS_HINTS = (
    "assemble",
    "组装",
    "dispatch",
    "派发",
    "execute",
    "执行",
    "report",
    "报告",
    "run",
    "运行",
    "solve",
    "求解",
    "计算",
)

_GENERIC_PROGRESS_ACK_PREFIXES = (
    "i'll continue",
    "i will continue",
    "i'll keep working",
    "i will keep working",
    "i'll keep going",
    "i will keep going",
    "我先根据你刚才的输入继续推进",
    "我先继续推进",
    "我会继续推进",
    "我将继续推进",
    "我会继续处理",
)


def _message_text(message: HumanMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
        return "\n".join(parts)
    return str(content)


def _last_human_message(messages: list[object]) -> HumanMessage | None:
    if not messages:
        return None
    last = messages[-1]
    return last if isinstance(last, HumanMessage) else None


def _latest_human_index(messages: list[object] | None) -> int | None:
    if not isinstance(messages, list):
        return None
    for index in range(len(messages) - 1, -1, -1):
        if isinstance(messages[index], HumanMessage):
            return index
    return None


def _has_supported_openfoam_seed_upload(uploaded_files: object) -> bool:
    if not isinstance(uploaded_files, list):
        return False

    supported_names = {"blockMeshDict", "pitzDaily", "pitzDaily.blockMeshDict"}
    for entry in uploaded_files:
        if not isinstance(entry, dict):
            continue
        filename = str(entry.get("filename") or "")
        if filename in supported_names:
            return True
    return False


def _message_level_uploaded_files(message: HumanMessage | None) -> list[dict]:
    if message is None:
        return []

    additional_kwargs = getattr(message, "additional_kwargs", None)
    if not isinstance(additional_kwargs, dict):
        return []

    files = additional_kwargs.get("files")
    return files if isinstance(files, list) else []


def _has_named_human_message(messages: list[object] | None, *, name: str) -> bool:
    if not isinstance(messages, list):
        return False
    for message in messages:
        if isinstance(message, HumanMessage) and getattr(message, "name", None) == name:
            return True
    return False


def _has_tool_call_since_latest_human(
    messages: list[object] | None,
    *,
    tool_name: str,
) -> bool:
    latest_human_index = _latest_human_index(messages)
    if latest_human_index is None or not isinstance(messages, list):
        return False

    for message in messages[latest_human_index + 1 :]:
        if not isinstance(message, AIMessage):
            continue
        for tool_call in getattr(message, "tool_calls", None) or []:
            if tool_call.get("name") == tool_name:
                return True
    return False


def _is_generic_progress_ack(response: ModelCallResult) -> bool:
    if not isinstance(response, ModelResponse):
        return False

    first_ai_message = next(
        (message for message in response.result if isinstance(message, AIMessage)),
        None,
    )
    if first_ai_message is None or getattr(first_ai_message, "tool_calls", None):
        return False

    content = str(first_ai_message.content or "").strip()
    if not content or len(content) > 160:
        return False

    lowered = content.lower()
    return any(lowered.startswith(prefix) for prefix in _GENERIC_PROGRESS_ACK_PREFIXES)


def _response_has_tool_calls(response: ModelCallResult) -> bool:
    if not isinstance(response, ModelResponse):
        return False
    return any(
        isinstance(message, AIMessage) and bool(getattr(message, "tool_calls", None))
        for message in response.result
    )


def _coerce_runtime_mapping(request: ModelRequest) -> dict:
    state = request.state or {}
    runtime = state.get("submarine_runtime") or {}
    return runtime if isinstance(runtime, dict) else {}


def _has_seed_handoff_intent(message_text: str) -> bool:
    if any(hint in message_text for hint in _ACTION_HINTS):
        return True
    if detect_execution_preference_signal(message_text) is not None:
        return True
    return any(hint in message_text for hint in _SEED_HANDOFF_HINTS)


def _should_force_seed_design_brief(request: ModelRequest) -> bool:
    runtime = _coerce_runtime_mapping(request)
    if runtime.get("current_stage"):
        return False

    last_human = _last_human_message(list(request.messages or []))
    if last_human is None:
        return False

    message_text = _message_text(last_human).lower()
    if not _has_seed_handoff_intent(message_text):
        return False

    if _has_tool_call_since_latest_human(
        list(request.messages or []),
        tool_name="submarine_design_brief",
    ):
        return False

    return _has_supported_openfoam_seed_upload(
        (request.state or {}).get("uploaded_files")
    ) or _has_supported_openfoam_seed_upload(
        _message_level_uploaded_files(last_human)
    )


def _should_force_seed_solver_dispatch(request: ModelRequest) -> bool:
    runtime = _coerce_runtime_mapping(request)
    if runtime.get("input_source_type") != "openfoam_case_seed":
        return False
    if runtime.get("current_stage") != "task-intelligence":
        return False
    if runtime.get("confirmation_status") != "confirmed":
        return False
    if runtime.get("review_status") != "ready_for_supervisor":
        return False
    if runtime.get("next_recommended_stage") != "solver-dispatch":
        return False
    if _has_tool_call_since_latest_human(
        list(request.messages or []),
        tool_name="submarine_solver_dispatch",
    ):
        return False
    return True


def _should_force_seed_result_report(request: ModelRequest) -> bool:
    runtime = _coerce_runtime_mapping(request)
    if runtime.get("input_source_type") != "openfoam_case_seed":
        return False
    if runtime.get("current_stage") != "solver-dispatch":
        return False
    if runtime.get("stage_status") != "executed":
        return False
    if runtime.get("next_recommended_stage") != "result-reporting":
        return False
    if _has_tool_call_since_latest_human(
        list(request.messages or []),
        tool_name="submarine_result_report",
    ):
        return False
    return True


def _resolve_seed_recovery_action(request: ModelRequest) -> str | None:
    if _should_force_seed_result_report(request):
        return "result_report"
    if _should_force_seed_solver_dispatch(request):
        return "solver_dispatch"
    if _should_force_seed_design_brief(request):
        return "design_brief"
    return None


def _seed_execution_preference(message_text: str) -> str | None:
    explicit_preference = detect_execution_preference_signal(message_text)
    if explicit_preference is not None:
        return explicit_preference

    normalized = message_text.lower()
    if any(hint in normalized for hint in _EXECUTION_PROGRESS_HINTS):
        return "execute_now"
    return None


def _latest_request_text(request: ModelRequest) -> str:
    last_human = _last_human_message(list(request.messages or []))
    return _message_text(last_human).strip() if last_human is not None else ""


def _build_design_brief_recovery_tool_call(request: ModelRequest) -> dict:
    task_description = _latest_request_text(request)
    tool_args: dict[str, object] = {
        "task_description": task_description,
    }
    execution_preference = _seed_execution_preference(task_description)
    if execution_preference is not None:
        tool_args["confirmation_status"] = "confirmed"
        tool_args["execution_preference"] = execution_preference
    return {
        "name": "submarine_design_brief",
        "args": tool_args,
        "id": "fallback_openfoam_seed_design_brief_0",
        "type": "tool_call",
    }


def _build_solver_dispatch_recovery_tool_call(request: ModelRequest) -> dict:
    runtime = _coerce_runtime_mapping(request)
    task_description = str(runtime.get("task_summary") or "").strip()
    if not task_description:
        task_description = _latest_request_text(request)
    tool_args: dict[str, object] = {
        "task_description": task_description,
        "task_type": str(runtime.get("task_type") or "official_openfoam_case"),
    }
    if runtime.get("execution_preference") == "execute_now":
        tool_args["execute_now"] = True
    return {
        "name": "submarine_solver_dispatch",
        "args": tool_args,
        "id": "fallback_openfoam_seed_solver_dispatch_0",
        "type": "tool_call",
    }


def _build_result_report_recovery_tool_call() -> dict:
    return {
        "name": "submarine_result_report",
        "args": {},
        "id": "fallback_openfoam_seed_result_report_0",
        "type": "tool_call",
    }


def _build_seed_recovery_response(
    request: ModelRequest,
    *,
    action: str,
) -> ModelResponse:
    if action == "design_brief":
        tool_call = _build_design_brief_recovery_tool_call(request)
    elif action == "solver_dispatch":
        tool_call = _build_solver_dispatch_recovery_tool_call(request)
    elif action == "result_report":
        tool_call = _build_result_report_recovery_tool_call()
    else:
        raise ValueError(f"Unsupported seed recovery action: {action}")

    return ModelResponse(result=[AIMessage(content="", tool_calls=[tool_call])])


class OpenfoamSeedWorkflowMiddleware(AgentMiddleware[ThreadState]):
    state_schema = ThreadState

    def _should_enforce_structured_openfoam_seed_handoff(
        self,
        request: ModelRequest,
    ) -> bool:
        return _resolve_seed_recovery_action(request) is not None

    @staticmethod
    def _append_reminder(request: ModelRequest) -> ModelRequest:
        updated_messages = list(request.messages or [])
        if not _has_named_human_message(
            updated_messages,
            name=_OPENFOAM_SEED_WORKFLOW_REMINDER_NAME,
        ):
            updated_messages.append(
                HumanMessage(
                    content=_OPENFOAM_SEED_WORKFLOW_REMINDER,
                    name=_OPENFOAM_SEED_WORKFLOW_REMINDER_NAME,
                )
            )

        system_message = request.system_message
        if isinstance(system_message, SystemMessage):
            content = str(system_message.content)
            if _OPENFOAM_SEED_WORKFLOW_REMINDER in content:
                return request.override(messages=updated_messages)
            return request.override(
                messages=updated_messages,
                system_message=SystemMessage(
                    content=f"{content}\n\n{_OPENFOAM_SEED_WORKFLOW_REMINDER}"
                ),
            )

        if system_message:
            content = str(system_message)
            if _OPENFOAM_SEED_WORKFLOW_REMINDER in content:
                return request.override(messages=updated_messages)
            return request.override(
                messages=updated_messages,
                system_message=SystemMessage(
                    content=f"{content}\n\n{_OPENFOAM_SEED_WORKFLOW_REMINDER}"
                ),
            )

        return request.override(
            messages=updated_messages,
            system_message=SystemMessage(content=_OPENFOAM_SEED_WORKFLOW_REMINDER),
        )

    @staticmethod
    def _append_retry_reminder(request: ModelRequest) -> ModelRequest:
        updated_messages = list(request.messages or [])
        if not _has_named_human_message(
            updated_messages,
            name=_OPENFOAM_SEED_WORKFLOW_RETRY_NAME,
        ):
            updated_messages.append(
                HumanMessage(
                    content=_OPENFOAM_SEED_WORKFLOW_RETRY_REMINDER,
                    name=_OPENFOAM_SEED_WORKFLOW_RETRY_NAME,
                )
            )
        return request.override(messages=updated_messages)

    @override
    def wrap_model_call(self, request: ModelRequest, handler) -> ModelCallResult:
        recovery_action = _resolve_seed_recovery_action(request)
        if recovery_action is None:
            return handler(request)

        seeded_request = (
            self._append_reminder(request)
            if recovery_action == "design_brief"
            else request
        )
        response = handler(seeded_request)
        if not isinstance(response, ModelResponse):
            return response
        if _response_has_tool_calls(response):
            return response
        if _is_generic_progress_ack(response):
            response = handler(self._append_retry_reminder(seeded_request))
            if not isinstance(response, ModelResponse):
                return response
            if _response_has_tool_calls(response):
                return response
        return _build_seed_recovery_response(request, action=recovery_action)

    @override
    async def awrap_model_call(self, request: ModelRequest, handler) -> ModelCallResult:
        recovery_action = _resolve_seed_recovery_action(request)
        if recovery_action is None:
            return await handler(request)

        seeded_request = (
            self._append_reminder(request)
            if recovery_action == "design_brief"
            else request
        )
        response = await handler(seeded_request)
        if not isinstance(response, ModelResponse):
            return response
        if _response_has_tool_calls(response):
            return response
        if _is_generic_progress_ack(response):
            response = await handler(self._append_retry_reminder(seeded_request))
            if not isinstance(response, ModelResponse):
                return response
            if _response_has_tool_calls(response):
                return response
        return _build_seed_recovery_response(request, action=recovery_action)
