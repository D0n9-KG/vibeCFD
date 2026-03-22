from app.models import ArtifactItem, RunStatus, TaskSubmission, WorkflowDraft, WorkflowStage


def test_task_submission_defaults() -> None:
    task = TaskSubmission(
        task_description="Compute pressure distribution for uploaded hull.",
        task_type="pressure_distribution",
        geometry_family_hint="DARPA SUBOFF",
    )

    assert task.task_type == "pressure_distribution"
    assert task.geometry_file_name is None
    assert task.operating_notes == ""


def test_workflow_draft_contains_stage_sequence() -> None:
    draft = WorkflowDraft(
        summary="Pressure workflow",
        assumptions=["deeply submerged"],
        recommended_case_ids=["darpa_suboff_bare_hull_resistance"],
        linked_skills=["search_similar_submarine_case"],
        allowed_tools=["case-search.get_case"],
        required_artifacts=["result.json"],
        stages=[
            WorkflowStage(
                stage_id="retrieval",
                title="案例检索",
                description="Retrieve similar cases",
            ),
            WorkflowStage(
                stage_id="execution",
                title="执行求解",
                description="Run the solver",
            ),
        ],
    )

    assert draft.stages[0].stage_id == "retrieval"
    assert draft.stages[1].title == "执行求解"


def test_artifact_item_preserves_relative_path() -> None:
    artifact = ArtifactItem(
        label="Pressure Map",
        category="image",
        relative_path="postprocess/images/pressure.svg",
        mime_type="image/svg+xml",
        url="/api/runs/run_001/artifacts/postprocess/images/pressure.svg",
    )

    assert artifact.relative_path.endswith("pressure.svg")
    assert artifact.category == "image"


def test_run_status_values_are_string_enums() -> None:
    assert RunStatus.AWAITING_CONFIRMATION.value == "awaiting_confirmation"
