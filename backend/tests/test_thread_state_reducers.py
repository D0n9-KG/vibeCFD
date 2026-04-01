from langgraph.graph import END, START, StateGraph

from deerflow.agents.thread_state import ThreadState


def _design_brief_runtime_update() -> dict:
    return {
        "current_stage": "task-intelligence",
        "task_summary": "Bind uploaded SUBOFF geometry into a CFD study brief",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
        "stage_status": "draft",
        "next_recommended_stage": "geometry-preflight",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/demo/cfd-design-brief.md",
        "request_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/openfoam-request.json",
        "artifact_virtual_paths": [
            "/mnt/user-data/outputs/submarine/reports/demo/cfd-design-brief.json",
            "/mnt/user-data/outputs/submarine/reports/demo/cfd-design-brief.md",
        ],
        "requested_outputs": [
            {
                "output_id": "drag_coefficient",
                "label": "Drag coefficient",
                "requested_label": "Cd",
                "status": "requested",
                "support_level": "supported",
            }
        ],
        "output_delivery_plan": [
            {
                "output_id": "drag_coefficient",
                "label": "Drag coefficient",
                "delivery_status": "planned",
                "detail": "Queued for solver dispatch.",
            }
        ],
        "execution_plan": [
            {
                "role_id": "task-intelligence",
                "owner": "DeerFlow task-intelligence",
                "goal": "Draft the initial study brief",
                "status": "in_progress",
                "target_skills": [],
            },
            {
                "role_id": "geometry-preflight",
                "owner": "DeerFlow geometry-preflight",
                "goal": "Inspect the uploaded STL",
                "status": "pending",
                "target_skills": [],
            },
        ],
        "activity_timeline": [
            {
                "stage": "task-intelligence",
                "actor": "claude-code-supervisor",
                "title": "Updated CFD design brief",
                "summary": "Captured the uploaded geometry and draft study scope.",
                "status": "draft",
                "skill_names": [],
                "timestamp": "2026-03-30T12:00:00+00:00",
            }
        ],
    }


def _delegation_runtime_update() -> dict:
    return {
        "requested_outputs": [
            {
                "output_id": "drag_coefficient",
                "notes": "Promoted into the execution-ready baseline package.",
            }
        ],
        "output_delivery_plan": [
            {
                "output_id": "drag_coefficient",
                "delivery_status": "delivered",
                "detail": "Delivered through solver-results.json.",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json"
                ],
            }
        ],
        "execution_plan": [
            {
                "role_id": "geometry-preflight",
                "owner": "DeerFlow geometry-preflight",
                "goal": "Inspect the uploaded STL",
                "status": "ready",
                "target_skills": ["submarine-geometry-preflight"],
            }
        ],
        "activity_timeline": [
            {
                "stage": "task-intelligence",
                "actor": "claude-code-supervisor",
                "role_id": "geometry-preflight",
                "title": "Delegated geometry preflight",
                "summary": "Queued the uploaded STL for geometry inspection.",
                "status": "completed",
                "skill_names": ["submarine-geometry-preflight"],
                "timestamp": "2026-03-30T12:00:01+00:00",
            }
        ],
    }


def test_thread_state_merges_parallel_submarine_runtime_updates():
    def design_node(_: ThreadState) -> dict:
        return {"submarine_runtime": _design_brief_runtime_update()}

    def delegation_node(_: ThreadState) -> dict:
        return {"submarine_runtime": _delegation_runtime_update()}

    graph = StateGraph(ThreadState)
    graph.add_node("design", design_node)
    graph.add_node("delegation", delegation_node)
    graph.add_edge(START, "design")
    graph.add_edge(START, "delegation")
    graph.add_edge("design", END)
    graph.add_edge("delegation", END)

    result = graph.compile().invoke({"messages": []})

    runtime_state = result["submarine_runtime"]
    assert runtime_state["current_stage"] == "task-intelligence"
    assert runtime_state["geometry_virtual_path"] == "/mnt/user-data/uploads/suboff_solid.stl"
    assert runtime_state["artifact_virtual_paths"] == [
        "/mnt/user-data/outputs/submarine/reports/demo/cfd-design-brief.json",
        "/mnt/user-data/outputs/submarine/reports/demo/cfd-design-brief.md",
    ]
    assert runtime_state["request_virtual_path"].endswith("/openfoam-request.json")
    assert runtime_state["requested_outputs"][0]["notes"] == (
        "Promoted into the execution-ready baseline package."
    )
    assert runtime_state["output_delivery_plan"][0]["delivery_status"] == "delivered"
    assert runtime_state["output_delivery_plan"][0]["artifact_virtual_paths"] == [
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json"
    ]

    geometry_preflight = next(
        item for item in runtime_state["execution_plan"] if item["role_id"] == "geometry-preflight"
    )
    assert geometry_preflight["status"] == "ready"
    assert geometry_preflight["target_skills"] == ["submarine-geometry-preflight"]

    assert len(runtime_state["activity_timeline"]) == 2
    assert runtime_state["activity_timeline"][0]["title"] == "Updated CFD design brief"
    assert runtime_state["activity_timeline"][1]["title"] == "Delegated geometry preflight"
