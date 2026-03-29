# Scientific Auto-Followup Tool v1 Design

## 1. Goal

Turn the latest scientific remediation handoff into an executable follow-up action without baking silent reruns directly into result reporting.

This slice should let the repository continue from a report-stage handoff when that handoff is already explicit and safe enough to execute by contract.

## 2. Why This Is The Right Next Slice

The repository now has:

- scientific remediation planning
- report-stage remediation handoff artifacts
- explicit next-tool suggestions for auto-executable remediation steps

But it still lacks a dedicated runtime tool that can consume that contract and continue the workflow without reconstructing the next step manually.

That means the repository can now explain the next step, but not yet act on it in a reusable, tool-level way.

## 3. Product Principle

This slice should keep execution explicit and user-steerable rather than turning result reporting into an always-on workflow engine.

That means:

- keep result reporting as evidence synthesis, not hidden orchestration
- add a separate follow-up tool that reads the latest handoff contract
- only execute when the handoff says `ready_for_auto_followup`
- keep `manual_followup_required` and `not_needed` as non-executing outcomes

## 4. Recommended Approach

Add a new built-in DeerFlow tool:

- `submarine_scientific_followup`

Recommended behavior:

- default to the current runtime `supervisor_handoff_virtual_path`
- load and validate the referenced handoff artifact
- if the handoff is executable, dispatch the suggested tool with the suggested arguments
- if the handoff is manual or no-op, return a structured explanatory message instead of guessing

## 5. v1 Execution Scope

### 5.1 Supported Handoff Targets

The first version should support:

- `submarine_solver_dispatch`
- `submarine_result_report`

### 5.2 Solver-Dispatch Follow-Up Rule

If the handoff recommends `submarine_solver_dispatch`, the follow-up tool should:

- forward the recommended geometry/task/case/simulation arguments
- force `execute_now=true`
- preserve `execute_scientific_studies=true` when present
- reuse the current DeerFlow sandbox command path through the existing solver-dispatch tool

This is the highest-value path because it can actually close scientific verification gaps instead of merely re-rendering a report.

### 5.3 Non-Executable Outcomes

If the handoff says:

- `manual_followup_required`
- `not_needed`

the tool should not run anything. It should return a clear tool message describing why execution did not proceed.

## 6. Files

### Backend

- Modify: `backend/packages/harness/deerflow/domain/submarine/handoff.py`
  - add artifact-loading and validation helpers for report-stage handoff payloads
- Create: `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
  - execute the latest report-stage handoff when it is ready
- Modify: `backend/packages/harness/deerflow/tools/builtins/__init__.py`
  - register the new tool
- Create: `backend/tests/test_submarine_scientific_followup_tool.py`
  - tool-level execution and refusal cases

### Docs

- Modify: `docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - record the new follow-up tool and its behavior boundary

## 7. Success Criteria

This stage is successful when:

- the repository exposes a dedicated tool that can continue from `scientific-remediation-handoff.json`
- executable handoffs trigger the recommended built-in tool instead of being reinterpreted ad hoc
- manual or no-op handoffs do not execute anything
- the tool preserves the existing open-ended interaction model by remaining explicit and callable

## 8. Remaining Gap After This Stage

Even after this slice:

- there is still no autonomous policy that decides when the tool should be invoked without an agent choosing to do so
- expensive reruns are still governed by the supervising agent, not by a background scheduler
- the system still lacks a deeper remediation policy layer for cost/risk-aware auto-execution
