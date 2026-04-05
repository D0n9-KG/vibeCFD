from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import uuid4

from .config import get_settings
from .models import (
    ArtifactItem,
    AttemptFailureCategory,
    AttemptFailureSource,
    CaseCandidate,
    ExecutionAttempt,
    ExecutionAttemptStatus,
    RunEvent,
    RunStatus,
    RunSummary,
    TimelineEvent,
    WorkflowDraft,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def duration_seconds(started_at: datetime, finished_at: datetime) -> float:
    elapsed = max((finished_at - started_at).total_seconds(), 0.0)
    return round(elapsed, 3)


class RunStore:
    def __init__(self) -> None:
        self._runs: dict[str, RunSummary] = {}
        self._events: dict[str, list[RunEvent]] = {}
        self._attempts: dict[str, list[ExecutionAttempt]] = {}
        self._lock = RLock()
        self.settings = get_settings()
        self.settings.runs_dir.mkdir(parents=True, exist_ok=True)
        self._load_existing_runs()

    def _state_path(self, run: RunSummary | str) -> Path:
        if isinstance(run, str):
            run = self._runs[run]
        return Path(run.run_directory) / "run_state.json"

    def _events_path_for_directory(self, run_directory: str | Path) -> Path:
        return Path(run_directory) / "events" / "events.jsonl"

    def _attempts_path_for_directory(self, run_directory: str | Path) -> Path:
        return Path(run_directory) / "attempts" / "attempts.json"

    def _events_path(self, run: RunSummary | str) -> Path:
        if isinstance(run, str):
            run = self._runs[run]
        return self._events_path_for_directory(run.run_directory)

    def _attempts_path(self, run: RunSummary | str) -> Path:
        if isinstance(run, str):
            run = self._runs[run]
        return self._attempts_path_for_directory(run.run_directory)

    def _persist_run(self, run: RunSummary) -> None:
        state_path = self._state_path(run)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps(run.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _persist_attempts_locked(self, run_id: str) -> None:
        attempts_path = self._attempts_path(run_id)
        attempts_path.parent.mkdir(parents=True, exist_ok=True)
        attempts_path.write_text(
            json.dumps(
                [attempt.model_dump(mode="json") for attempt in self._attempts.get(run_id, [])],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def _append_event_locked(
        self,
        run_id: str,
        *,
        event_type: str,
        stage: str,
        status: str,
        message: str,
        details: dict[str, str | int | float | bool | None] | None = None,
        timestamp: datetime | None = None,
    ) -> RunEvent:
        event = RunEvent(
            event_id=f"evt_{uuid4().hex[:12]}",
            timestamp=timestamp or utcnow(),
            event_type=event_type,
            stage=stage,
            status=status,
            message=message,
            details=details or {},
        )
        self._events.setdefault(run_id, []).append(event)
        events_path = self._events_path(run_id)
        events_path.parent.mkdir(parents=True, exist_ok=True)
        with events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False) + "\n")
        return event

    def _load_events(self, run_directory: str | Path) -> list[RunEvent]:
        events_path = self._events_path_for_directory(run_directory)
        if not events_path.exists():
            return []

        events: list[RunEvent] = []
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                events.append(RunEvent.model_validate_json(line))
            except Exception:
                continue
        return events

    def _load_attempts(self, run_directory: str | Path) -> list[ExecutionAttempt]:
        attempts_path = self._attempts_path_for_directory(run_directory)
        if not attempts_path.exists():
            return []

        try:
            payload = json.loads(attempts_path.read_text(encoding="utf-8"))
        except Exception:
            return []

        if not isinstance(payload, list):
            return []

        attempts: list[ExecutionAttempt] = []
        for item in payload:
            try:
                attempts.append(ExecutionAttempt.model_validate(item))
            except Exception:
                continue
        return attempts

    def _normalize_loaded_run(self, run: RunSummary) -> RunSummary:
        if run.status != RunStatus.RUNNING:
            return run

        recovered_at = utcnow()
        return run.model_copy(
            update={
                "status": RunStatus.FAILED,
                "current_stage": "failed",
                "stage_label": "Recovered: Retry Required",
                "updated_at": recovered_at,
                "timeline": [
                    *run.timeline,
                    TimelineEvent(
                        timestamp=recovered_at,
                        stage="recovery",
                        message="Recovered interrupted run after restart; manual retry is required.",
                        status="error",
                    ),
                ],
            },
            deep=True,
        )

    def _finalize_latest_attempt_locked(
        self,
        run_id: str,
        *,
        status: ExecutionAttemptStatus,
        summary: str | None = None,
        error_message: str | None = None,
        failure_category: AttemptFailureCategory | None = None,
        failure_source: AttemptFailureSource | None = None,
        finished_at: datetime | None = None,
    ) -> ExecutionAttempt | None:
        attempts = self._attempts.get(run_id, [])
        if not attempts:
            return None

        latest = attempts[-1]
        if latest.status != "running":
            return None

        resolved_finished_at = finished_at or utcnow()
        finalized = latest.model_copy(
            update={
                "status": status,
                "finished_at": resolved_finished_at,
                "duration_seconds": duration_seconds(latest.started_at, resolved_finished_at),
                "summary": summary,
                "error_message": error_message,
                "failure_category": failure_category,
                "failure_source": failure_source,
            },
            deep=True,
        )
        attempts[-1] = finalized
        self._persist_attempts_locked(run_id)
        return finalized

    def _load_existing_runs(self) -> None:
        for state_path in self.settings.runs_dir.glob("*/run_state.json"):
            try:
                loaded = RunSummary.model_validate_json(state_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            normalized = self._normalize_loaded_run(loaded)
            self._runs[normalized.run_id] = normalized
            self._events[normalized.run_id] = self._load_events(normalized.run_directory)
            self._attempts[normalized.run_id] = self._load_attempts(normalized.run_directory)
            self._persist_run(normalized)
            if loaded.status == RunStatus.RUNNING and normalized.status == RunStatus.FAILED:
                self._finalize_latest_attempt_locked(
                    normalized.run_id,
                    status="failed",
                    summary="Execution attempt interrupted by service restart.",
                    error_message="Recovered interrupted run after restart; manual retry is required.",
                    failure_category="service_restart_interruption",
                    failure_source="store_recovery",
                )
                self._append_event_locked(
                    normalized.run_id,
                    event_type="run_recovered_after_restart",
                    stage="recovery",
                    status=normalized.status.value,
                    message="Recovered interrupted run after restart; manual retry is required.",
                )

    def _replace_run(self, run: RunSummary) -> RunSummary:
        self._runs[run.run_id] = run
        self._persist_run(run)
        return run.model_copy(deep=True)

    def add_run(self, run: RunSummary) -> RunSummary:
        with self._lock:
            self._events.setdefault(run.run_id, [])
            self._attempts.setdefault(run.run_id, [])
            self._replace_run(run.model_copy(deep=True))
            self._append_event_locked(
                run.run_id,
                event_type="run_created",
                stage="request",
                status=run.status.value,
                message="Run created and written to the run directory.",
                details={"task_type": run.request.task_type},
            )
            self._persist_attempts_locked(run.run_id)
            return self.get_run(run.run_id)

    def get_run(self, run_id: str) -> RunSummary:
        with self._lock:
            if run_id not in self._runs:
                raise KeyError(run_id)
            return self._runs[run_id].model_copy(deep=True)

    def list_runs(self) -> list[RunSummary]:
        with self._lock:
            runs = [run.model_copy(deep=True) for run in self._runs.values()]
        return sorted(runs, key=lambda item: item.created_at, reverse=True)

    def list_events(self, run_id: str) -> list[RunEvent]:
        with self._lock:
            if run_id not in self._runs:
                raise KeyError(run_id)
            events = self._events.get(run_id, [])
            return [event.model_copy(deep=True) for event in events]

    def list_attempts(self, run_id: str) -> list[ExecutionAttempt]:
        with self._lock:
            if run_id not in self._runs:
                raise KeyError(run_id)
            attempts = self._attempts.get(run_id, [])
            return [attempt.model_copy(deep=True) for attempt in attempts]

    def append_event(
        self,
        run_id: str,
        *,
        event_type: str,
        stage: str,
        message: str,
        status: str,
        details: dict[str, str | int | float | bool | None] | None = None,
    ) -> RunEvent:
        with self._lock:
            if run_id not in self._runs:
                raise KeyError(run_id)
            return self._append_event_locked(
                run_id,
                event_type=event_type,
                stage=stage,
                status=status,
                message=message,
                details=details,
            )

    def start_execution_attempt(self, run_id: str, *, engine_name: str) -> ExecutionAttempt:
        with self._lock:
            if run_id not in self._runs:
                raise KeyError(run_id)
            attempts = self._attempts.setdefault(run_id, [])
            started_at = utcnow()
            attempt = ExecutionAttempt(
                attempt_id=f"att_{uuid4().hex[:12]}",
                attempt_number=len(attempts) + 1,
                engine_name=engine_name,
                status="running",
                started_at=started_at,
            )
            attempts.append(attempt)
            self._persist_attempts_locked(run_id)
            self._append_event_locked(
                run_id,
                event_type="execution_attempt_started",
                stage="execution",
                status="running",
                message=f"Execution attempt {attempt.attempt_number} started via {engine_name}.",
                details={
                    "attempt_id": attempt.attempt_id,
                    "attempt_number": attempt.attempt_number,
                    "engine_name": engine_name,
                },
                timestamp=started_at,
            )
            return attempt.model_copy(deep=True)

    def finish_execution_attempt(
        self,
        run_id: str,
        *,
        status: ExecutionAttemptStatus,
        summary: str | None = None,
        error_message: str | None = None,
        failure_category: AttemptFailureCategory | None = None,
        failure_source: AttemptFailureSource | None = None,
    ) -> ExecutionAttempt | None:
        with self._lock:
            if run_id not in self._runs:
                raise KeyError(run_id)
            finalized = self._finalize_latest_attempt_locked(
                run_id,
                status=status,
                summary=summary,
                error_message=error_message,
                failure_category=failure_category,
                failure_source=failure_source,
            )
            if finalized is None:
                return None
            event_details: dict[str, str | int | float | bool | None] = {
                "attempt_id": finalized.attempt_id,
                "attempt_number": finalized.attempt_number,
                "engine_name": finalized.engine_name,
                "duration_seconds": finalized.duration_seconds,
            }
            if finalized.failure_category is not None:
                event_details["failure_category"] = finalized.failure_category
            if finalized.failure_source is not None:
                event_details["failure_source"] = finalized.failure_source
            self._append_event_locked(
                run_id,
                event_type="execution_attempt_finished",
                stage="execution",
                status=status,
                message=summary or error_message or f"Execution attempt {finalized.attempt_number} finished.",
                details=event_details,
                timestamp=finalized.finished_at,
            )
            return finalized.model_copy(deep=True)

    def update_run(self, run_id: str, **updates: object) -> RunSummary:
        with self._lock:
            run = self._runs[run_id]
            updated = run.model_copy(update={**updates, "updated_at": utcnow()}, deep=True)
            return self._replace_run(updated)

    def prepare_run(
        self,
        run_id: str,
        *,
        geometry_check: str,
        candidate_cases: list[CaseCandidate],
        selected_case: CaseCandidate,
        workflow_draft: WorkflowDraft,
    ) -> RunSummary:
        self.update_run(
            run_id,
            geometry_check=geometry_check,
            candidate_cases=[item.model_copy(deep=True) for item in candidate_cases],
            selected_case=selected_case.model_copy(deep=True),
            workflow_draft=workflow_draft.model_copy(deep=True),
            status=RunStatus.AWAITING_CONFIRMATION,
            current_stage="awaiting_confirmation",
            stage_label="Awaiting Confirmation",
        )
        self.append_event(
            run_id,
            event_type="workflow_prepared",
            stage="prepare",
            message="Workflow draft prepared from candidate cases.",
            status=RunStatus.AWAITING_CONFIRMATION.value,
            details={
                "candidate_count": len(candidate_cases),
                "selected_case_id": selected_case.case_id,
            },
        )
        return self.get_run(run_id)

    def append_timeline(self, run_id: str, stage: str, message: str, status: str) -> RunSummary:
        with self._lock:
            run = self._runs[run_id]
            events = [
                *run.timeline,
                TimelineEvent(timestamp=utcnow(), stage=stage, message=message, status=status),
            ]
            updated = run.model_copy(update={"timeline": events, "updated_at": utcnow()}, deep=True)
            return self._replace_run(updated)

    def confirm_run(self, run_id: str, reviewer_notes: str) -> RunSummary:
        with self._lock:
            run = self._runs[run_id]
            confirmed_at = utcnow()
            queued = run.model_copy(
                update={
                    "status": RunStatus.QUEUED,
                    "current_stage": "queued",
                    "stage_label": "Queued For Dispatch",
                    "confirmed_at": confirmed_at,
                    "reviewer_notes": reviewer_notes,
                    "updated_at": confirmed_at,
                    "timeline": [
                        *run.timeline,
                        TimelineEvent(
                            timestamp=confirmed_at,
                            stage="queued",
                            message="Run queued for background dispatch.",
                            status="pending",
                        ),
                    ],
                },
                deep=True,
            )
            self._replace_run(queued)
            self._append_event_locked(
                run_id,
                event_type="run_queued",
                stage="queued",
                status=RunStatus.QUEUED.value,
                message="Run queued for background dispatch.",
                details={"reviewer_notes": reviewer_notes or None},
                timestamp=confirmed_at,
            )
            return self.get_run(run_id)

    def cancel_queued_run(self, run_id: str, reason: str) -> RunSummary:
        with self._lock:
            run = self._runs[run_id]
            if run.status != RunStatus.QUEUED:
                raise ValueError("Only queued runs can be cancelled.")

            cancelled_at = utcnow()
            message = reason.strip() or "Queued run cancelled before dispatch."
            cancelled = run.model_copy(
                update={
                    "status": RunStatus.CANCELLED,
                    "current_stage": "cancelled",
                    "stage_label": "Cancelled",
                    "updated_at": cancelled_at,
                    "timeline": [
                        *run.timeline,
                        TimelineEvent(
                            timestamp=cancelled_at,
                            stage="cancelled",
                            message=message,
                            status="warning",
                        ),
                    ],
                },
                deep=True,
            )
            self._replace_run(cancelled)
            self._append_event_locked(
                run_id,
                event_type="run_cancelled",
                stage="cancelled",
                status=RunStatus.CANCELLED.value,
                message=message,
                timestamp=cancelled_at,
            )
            return self.get_run(run_id)

    def claim_next_queued_run(self) -> RunSummary | None:
        with self._lock:
            queued_runs = [
                run for run in self._runs.values() if run.status == RunStatus.QUEUED
            ]
            if not queued_runs:
                return None

            next_run = min(
                queued_runs,
                key=lambda item: (
                    item.confirmed_at or item.updated_at,
                    item.created_at,
                    item.run_id,
                ),
            )
            claimed_at = utcnow()
            claimed = next_run.model_copy(
                update={
                    "status": RunStatus.RUNNING,
                    "current_stage": "execution",
                    "stage_label": "Running",
                    "updated_at": claimed_at,
                    "timeline": [
                        *next_run.timeline,
                        TimelineEvent(
                            timestamp=claimed_at,
                            stage="dispatch",
                            message="Dispatcher claimed queued run for execution.",
                            status="running",
                        ),
                    ],
                },
                deep=True,
            )
            self._replace_run(claimed)
            self._append_event_locked(
                claimed.run_id,
                event_type="dispatch_claimed",
                stage="dispatch",
                status=RunStatus.RUNNING.value,
                message="Dispatcher claimed queued run for execution.",
                timestamp=claimed_at,
            )
            return self.get_run(claimed.run_id)

    def set_stage(self, run_id: str, stage: str, stage_label: str) -> RunSummary:
        return self.update_run(run_id, current_stage=stage, stage_label=stage_label)

    def set_artifacts(self, run_id: str, artifacts: list[ArtifactItem]) -> RunSummary:
        return self.update_run(
            run_id,
            artifacts=[item.model_copy(deep=True) for item in artifacts],
        )

    def complete_run(
        self,
        run_id: str,
        *,
        artifacts: list[ArtifactItem],
        report_markdown: str,
        metrics: dict[str, float | str],
    ) -> RunSummary:
        self.update_run(
            run_id,
            status=RunStatus.COMPLETED,
            current_stage="completed",
            stage_label="Completed",
            artifacts=[item.model_copy(deep=True) for item in artifacts],
            report_markdown=report_markdown,
            metrics=metrics,
        )
        self.finish_execution_attempt(
            run_id,
            status="completed",
            summary="Execution attempt completed successfully.",
        )
        self.append_event(
            run_id,
            event_type="run_completed",
            stage="completed",
            message="Run completed and artifacts are available.",
            status=RunStatus.COMPLETED.value,
            details={"artifact_count": len(artifacts)},
        )
        return self.get_run(run_id)

    def fail_run(self, run_id: str, message: str) -> RunSummary:
        return self.fail_run_with_metadata(
            run_id,
            message,
            summary="Execution attempt failed.",
            failure_category="execution_failure",
            failure_source="execution_engine",
        )

    def fail_run_with_metadata(
        self,
        run_id: str,
        message: str,
        *,
        summary: str,
        failure_category: AttemptFailureCategory,
        failure_source: AttemptFailureSource,
    ) -> RunSummary:
        self.update_run(
            run_id,
            status=RunStatus.FAILED,
            current_stage="failed",
            stage_label="Failed",
        )
        self.append_timeline(run_id, "failed", message, "error")
        self.finish_execution_attempt(
            run_id,
            status="failed",
            summary=summary,
            error_message=message,
            failure_category=failure_category,
            failure_source=failure_source,
        )
        self.append_event(
            run_id,
            event_type="run_failed",
            stage="failed",
            message=message,
            status=RunStatus.FAILED.value,
            details={
                "failure_category": failure_category,
                "failure_source": failure_source,
            },
        )
        return self.get_run(run_id)
