import asyncio
from typing import NotRequired, override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langgraph.config import get_config
from langgraph.runtime import Runtime

from deerflow.agents.thread_state import ThreadDataState
from deerflow.config.paths import Paths, get_paths


class ThreadDataMiddlewareState(AgentState):
    """Compatible with the `ThreadState` schema."""

    thread_data: NotRequired[ThreadDataState | None]


class ThreadDataMiddleware(AgentMiddleware[ThreadDataMiddlewareState]):
    """Guarantee thread data directories for each thread execution.

    Creates the following directory structure:
    - {base_dir}/threads/{thread_id}/user-data/workspace
    - {base_dir}/threads/{thread_id}/user-data/uploads
    - {base_dir}/threads/{thread_id}/user-data/outputs

    The returned thread_data paths always point at directories that already
    exist before tools run. ``lazy_init`` is retained for compatibility but
    no longer skips directory creation.
    """

    state_schema = ThreadDataMiddlewareState

    def __init__(self, base_dir: str | None = None, lazy_init: bool = True):
        """Initialize the middleware.

        Args:
            base_dir: Base directory for thread data. Defaults to Paths resolution.
            lazy_init: Retained for compatibility with existing construction
                      sites. Thread directories are now guaranteed in
                      before_agent() regardless of this flag.
        """
        super().__init__()
        self._paths = Paths(base_dir) if base_dir else get_paths()
        self._lazy_init = lazy_init

    def _get_thread_paths(self, thread_id: str) -> dict[str, str]:
        """Get the paths for a thread's data directories.

        Args:
            thread_id: The thread ID.

        Returns:
            Dictionary with workspace_path, uploads_path, and outputs_path.
        """
        return {
            "workspace_path": str(self._paths.sandbox_work_dir(thread_id)),
            "uploads_path": str(self._paths.sandbox_uploads_dir(thread_id)),
            "outputs_path": str(self._paths.sandbox_outputs_dir(thread_id)),
        }

    def _create_thread_directories(self, thread_id: str) -> dict[str, str]:
        """Create the thread data directories.

        Args:
            thread_id: The thread ID.

        Returns:
            Dictionary with the created directory paths.
        """
        self._paths.ensure_thread_dirs(thread_id)
        return self._get_thread_paths(thread_id)

    def _resolve_thread_id(self, runtime: Runtime) -> str:
        context = runtime.context or {}
        thread_id = context.get("thread_id")
        if thread_id is None:
            config = get_config()
            thread_id = config.get("configurable", {}).get("thread_id")

        if thread_id is None:
            raise ValueError("Thread ID is required in runtime context or config.configurable")

        return thread_id

    def _build_thread_data(self, thread_id: str) -> dict[str, str]:
        if self._lazy_init:
            return self._get_thread_paths(thread_id)

        paths = self._get_thread_paths(thread_id)
        print(f"Created thread data directories for thread {thread_id}")
        return paths

    @override
    def before_agent(self, state: ThreadDataMiddlewareState, runtime: Runtime) -> dict | None:
        thread_id = self._resolve_thread_id(runtime)

        self._paths.ensure_thread_dirs(thread_id)
        paths = self._build_thread_data(thread_id)

        return {
            "thread_data": {
                **paths,
            }
        }

    @override
    async def abefore_agent(
        self,
        state: ThreadDataMiddlewareState,
        runtime: Runtime,
    ) -> dict | None:
        thread_id = self._resolve_thread_id(runtime)

        await asyncio.to_thread(self._paths.ensure_thread_dirs, thread_id)
        paths = self._build_thread_data(thread_id)

        return {
            "thread_data": {
                **paths,
            }
        }
