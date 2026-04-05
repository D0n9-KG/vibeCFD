from types import SimpleNamespace

from langchain_core.messages import ToolMessage
from langgraph.types import Command

from deerflow.agents.middlewares.clarification_middleware import ClarificationMiddleware


class _StrictEncodedStdout:
    def __init__(self, encoding: str):
        self.encoding = encoding
        self.writes: list[str] = []

    def write(self, text: str) -> int:
        text.encode(self.encoding, errors="strict")
        self.writes.append(text)
        return len(text)

    def flush(self) -> None:
        return None


def _request(question: str, tool_call_id: str = "tc-clarify"):
    return SimpleNamespace(
        tool_call={
            "name": "ask_clarification",
            "id": tool_call_id,
            "args": {
                "question": question,
                "clarification_type": "missing_info",
                "context": "需要确认体积流量单位。",
                "options": ["m^3/s", "kg/s"],
            },
        }
    )


def test_wrap_tool_call_handles_gbk_stdout_with_superscript_character(monkeypatch):
    middleware = ClarificationMiddleware()
    stdout = _StrictEncodedStdout("gbk")
    monkeypatch.setattr("sys.stdout", stdout)

    result = middleware.wrap_tool_call(_request("请确认体积流量是否以 m³/s 提供。"), lambda _req: None)

    assert isinstance(result, Command)
    messages = result.update["messages"]
    assert len(messages) == 1
    assert isinstance(messages[0], ToolMessage)
    assert "m³/s" in messages[0].text
    assert any("\\xb3" in entry for entry in stdout.writes)
