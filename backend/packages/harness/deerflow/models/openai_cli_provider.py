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
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.messages.tool import tool_call_chunk
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

from deerflow.models.credential_loader import load_openai_api_credential

logger = logging.getLogger(__name__)


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
        return self._build_chat_result_from_response_dict(response)

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
        return self._build_chat_result_from_response_dict(response)

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
