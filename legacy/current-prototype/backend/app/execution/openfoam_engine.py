from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path

from ..config import get_settings
from ..models import RunStatus
from ..store import RunStore


class OpenFoamExecutionEngine:
    engine_name = "openfoam"

    def __init__(self, store: RunStore) -> None:
        self.store = store
        self.settings = get_settings()

    def launch(self, run_id: str) -> None:
        thread = threading.Thread(target=self.run_pipeline, args=(run_id,), daemon=True)
        thread.start()

    def run_pipeline(self, run_id: str):
        run = self.store.get_run(run_id)
        if run.status not in {RunStatus.RUNNING, RunStatus.AWAITING_CONFIRMATION}:
            raise RuntimeError(f"Run {run_id} is not ready for execution.")

        run_path = Path(run.run_directory)
        request_path = run_path / "execution" / "solver_case" / "openfoam_request.json"
        request_path.write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "task_type": run.request.task_type,
                    "geometry_family": run.request.geometry_family_hint,
                    "selected_case_id": run.selected_case.case_id if run.selected_case else None,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        self.store.append_timeline(
            run_id,
            "execution",
            "OpenFOAM adapter selected. Preparing external solver command.",
            "running",
        )
        self.store.set_stage(run_id, "execution", "Running OpenFOAM")

        log_path = run_path / "execution" / "logs" / "run.log"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write("[openfoam] Adapter initialized.\n")
            handle.write(f"[openfoam] Request manifest: {request_path.name}\n")

            if not self.settings.openfoam_command:
                handle.write("[openfoam] No solver command configured.\n")
                raise RuntimeError(
                    "OpenFOAM command is not configured. Set SUBMARINE_OPENFOAM_COMMAND."
                )

            completed = subprocess.run(
                self.settings.openfoam_command,
                shell=True,
                cwd=run_path,
                capture_output=True,
                text=True,
                check=False,
            )
            handle.write(completed.stdout)
            handle.write(completed.stderr)

            if completed.returncode != 0:
                raise RuntimeError(
                    f"OpenFOAM command failed with exit code {completed.returncode}."
                )

        self.store.append_timeline(
            run_id,
            "execution",
            "OpenFOAM command finished. Additional postprocess integration is still required.",
            "ok",
        )
        self.store.set_stage(run_id, "execution", "OpenFOAM Finished")
        return self.store.get_run(run_id)
