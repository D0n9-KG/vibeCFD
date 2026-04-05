from __future__ import annotations

from threading import Event, Thread

from .execution.base import ExecutionEngine
from .store import RunStore


class ExecutionDispatcher:
    def __init__(
        self,
        *,
        store: RunStore,
        execution_engine: ExecutionEngine,
        poll_interval_seconds: float,
    ) -> None:
        self.store = store
        self.execution_engine = execution_engine
        self.poll_interval_seconds = poll_interval_seconds
        self._stop_event = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = Thread(target=self._run_loop, name="execution-dispatcher", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=max(self.poll_interval_seconds * 4, 0.2))
        self._thread = None

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            dispatched = self._dispatch_once()
            if dispatched:
                continue
            self._stop_event.wait(self.poll_interval_seconds)

    def _dispatch_once(self) -> bool:
        claimed = self.store.claim_next_queued_run()
        if claimed is None:
            return False

        try:
            self.store.start_execution_attempt(
                claimed.run_id,
                engine_name=self.execution_engine.engine_name,
            )
            self.execution_engine.launch(claimed.run_id)
        except Exception as exc:  # pragma: no cover - rare path, exercised in integration scenarios
            self.store.fail_run_with_metadata(
                claimed.run_id,
                f"Execution dispatch failed: {exc}",
                summary="Execution attempt failed before engine launch completed.",
                failure_category="dispatch_launch_error",
                failure_source="dispatcher",
            )
        return True
