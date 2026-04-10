import asyncio
import threading

import pytest
from langgraph.runtime import Runtime

from deerflow.agents.middlewares.thread_data_middleware import ThreadDataMiddleware


def _normalize_path(value: str) -> str:
    return value.replace("\\", "/")


class TestThreadDataMiddleware:
    def test_before_agent_returns_paths_when_thread_id_present_in_context(self, tmp_path):
        middleware = ThreadDataMiddleware(base_dir=str(tmp_path), lazy_init=True)

        result = middleware.before_agent(state={}, runtime=Runtime(context={"thread_id": "thread-123"}))

        assert result is not None
        assert _normalize_path(result["thread_data"]["workspace_path"]).endswith("threads/thread-123/user-data/workspace")
        assert _normalize_path(result["thread_data"]["uploads_path"]).endswith("threads/thread-123/user-data/uploads")
        assert _normalize_path(result["thread_data"]["outputs_path"]).endswith("threads/thread-123/user-data/outputs")
        assert tmp_path.joinpath("threads", "thread-123", "user-data", "workspace").is_dir()
        assert tmp_path.joinpath("threads", "thread-123", "user-data", "uploads").is_dir()
        assert tmp_path.joinpath("threads", "thread-123", "user-data", "outputs").is_dir()

    def test_before_agent_uses_thread_id_from_configurable_when_context_is_none(self, tmp_path, monkeypatch):
        middleware = ThreadDataMiddleware(base_dir=str(tmp_path), lazy_init=True)
        runtime = Runtime(context=None)
        monkeypatch.setattr(
            "deerflow.agents.middlewares.thread_data_middleware.get_config",
            lambda: {"configurable": {"thread_id": "thread-from-config"}},
        )

        result = middleware.before_agent(state={}, runtime=runtime)

        assert result is not None
        assert _normalize_path(result["thread_data"]["workspace_path"]).endswith("threads/thread-from-config/user-data/workspace")
        assert runtime.context is None

    def test_before_agent_uses_thread_id_from_configurable_when_context_missing_thread_id(self, tmp_path, monkeypatch):
        middleware = ThreadDataMiddleware(base_dir=str(tmp_path), lazy_init=True)
        runtime = Runtime(context={})
        monkeypatch.setattr(
            "deerflow.agents.middlewares.thread_data_middleware.get_config",
            lambda: {"configurable": {"thread_id": "thread-from-config"}},
        )

        result = middleware.before_agent(state={}, runtime=runtime)

        assert result is not None
        assert _normalize_path(result["thread_data"]["uploads_path"]).endswith("threads/thread-from-config/user-data/uploads")
        assert runtime.context == {}

    def test_before_agent_raises_clear_error_when_thread_id_missing_everywhere(self, tmp_path, monkeypatch):
        middleware = ThreadDataMiddleware(base_dir=str(tmp_path), lazy_init=True)
        monkeypatch.setattr(
            "deerflow.agents.middlewares.thread_data_middleware.get_config",
            lambda: {"configurable": {}},
        )

        with pytest.raises(ValueError, match="Thread ID is required in runtime context or config.configurable"):
            middleware.before_agent(state={}, runtime=Runtime(context=None))

    def test_before_agent_creates_standard_thread_directories_with_lazy_init(self, tmp_path):
        middleware = ThreadDataMiddleware(base_dir=str(tmp_path), lazy_init=True)

        middleware.before_agent(state={}, runtime=Runtime(context={"thread_id": "thread-lazy"}))

        assert tmp_path.joinpath("threads", "thread-lazy", "user-data", "workspace").is_dir()
        assert tmp_path.joinpath("threads", "thread-lazy", "user-data", "uploads").is_dir()
        assert tmp_path.joinpath("threads", "thread-lazy", "user-data", "outputs").is_dir()

    def test_abefore_agent_initializes_thread_directories_off_main_thread(self, tmp_path):
        middleware = ThreadDataMiddleware(base_dir=str(tmp_path), lazy_init=True)
        ensure_thread_names: list[str] = []

        class RecordingPaths:
            def ensure_thread_dirs(self, thread_id: str) -> None:
                ensure_thread_names.append(threading.current_thread().name)

            def sandbox_work_dir(self, thread_id: str):
                return tmp_path / "threads" / thread_id / "user-data" / "workspace"

            def sandbox_uploads_dir(self, thread_id: str):
                return tmp_path / "threads" / thread_id / "user-data" / "uploads"

            def sandbox_outputs_dir(self, thread_id: str):
                return tmp_path / "threads" / thread_id / "user-data" / "outputs"

        middleware._paths = RecordingPaths()

        result = asyncio.run(
            middleware.abefore_agent(
                state={},
                runtime=Runtime(context={"thread_id": "thread-async"}),
            )
        )

        assert result is not None
        assert ensure_thread_names
        assert ensure_thread_names[0] != threading.current_thread().name
