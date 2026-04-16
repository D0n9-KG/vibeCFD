from deerflow.agents.thread_state import merge_submarine_runtime


def test_merge_submarine_runtime_preserves_more_specific_iterative_context():
    existing = {
        "contract_revision": 4,
        "iteration_mode": "derive_variant",
        "revision_summary": "Add a wake-focused geometry-preflight pass.",
        "variant_policy": {
            "default_compare_target_run_id": "baseline",
        },
    }
    new = {
        "contract_revision": 1,
        "iteration_mode": "baseline",
        "revision_summary": None,
        "variant_policy": {},
    }

    merged = merge_submarine_runtime(existing, new)

    assert merged["contract_revision"] == 4
    assert merged["iteration_mode"] == "derive_variant"
    assert merged["revision_summary"] == (
        "Add a wake-focused geometry-preflight pass."
    )
    assert merged["variant_policy"]["default_compare_target_run_id"] == "baseline"


def test_merge_submarine_runtime_replaces_contract_lists_for_new_revision():
    existing = {
        "contract_revision": 2,
        "capability_gaps": [
            {
                "output_id": "streamlines",
                "support_level": "not_yet_supported",
            }
        ],
        "unresolved_decisions": [
            {
                "decision_id": "confirm-wake-origin",
                "label": "Confirm wake origin",
            }
        ],
        "evidence_expectations": [
            {
                "expectation_id": "tail-stability",
                "kind": "stability",
            }
        ],
    }
    new = {
        "contract_revision": 3,
        "capability_gaps": [],
        "unresolved_decisions": [
            {
                "decision_id": "confirm-tail-window",
                "label": "Confirm tail averaging window",
            }
        ],
        "evidence_expectations": [
            {
                "expectation_id": "mesh-independence",
                "kind": "verification",
            }
        ],
    }

    merged = merge_submarine_runtime(existing, new)

    assert merged["contract_revision"] == 3
    assert merged["capability_gaps"] == []
    assert merged["unresolved_decisions"] == [
        {
            "decision_id": "confirm-tail-window",
            "label": "Confirm tail averaging window",
        }
    ]
    assert merged["evidence_expectations"] == [
        {
            "expectation_id": "mesh-independence",
            "kind": "verification",
        }
    ]
