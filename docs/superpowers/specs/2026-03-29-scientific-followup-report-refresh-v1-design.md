# Scientific Followup Report Refresh v1 Design

## 1. Goal

Close the most valuable single follow-up loop by teaching `submarine_scientific_followup` to refresh result reporting after an executed scientific study rerun.

This slice should make one explicit follow-up invocation produce an updated report-stage evidence state instead of leaving the runtime stranded at `solver-dispatch`.

## 2. Why This Is The Right Next Slice

The repository now has:

- report-stage remediation handoffs
- a dedicated `submarine_scientific_followup` tool
- executable delegation into `submarine_solver_dispatch` and `submarine_result_report`

But when the follow-up tool executes a scientific-study solver rerun, the runtime currently stops at solver dispatch and still needs a second manual tool call to regenerate the final report.

That means the repository can continue one step, but it still cannot complete a single scientific rerun-and-reassess cycle in one bounded action.

## 3. Product Principle

This slice should close one explicit follow-up cycle, not create an unbounded autonomous loop.

That means:

- only chain into result reporting after a solver dispatch that actually executed
- do not recursively keep following new handoffs
- do not hide the chain inside result-reporting
- keep the orchestration bounded to one dispatch-plus-report refresh

## 4. Recommended Approach

Extend `submarine_scientific_followup` so that:

- if it delegates to `submarine_solver_dispatch`
- and the returned runtime indicates the dispatch was executed successfully
- then it immediately delegates to `submarine_result_report`
- and returns the refreshed report-stage `Command`

Recommended behavior boundary:

- solver dispatch planned but not executed -> stop at dispatch output
- solver dispatch failed -> stop and return the failed dispatch output
- solver dispatch executed -> refresh the report once, then stop

## 5. Files

### Backend

- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
  - chain result reporting after successful solver reruns
- Modify: `backend/tests/test_submarine_scientific_followup_tool.py`
  - refresh-chain coverage

### Docs

- Modify: `docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - record the new one-step dispatch-plus-report behavior

## 6. Success Criteria

This stage is successful when:

- one `submarine_scientific_followup` call can execute a scientific-study rerun and return a refreshed report-stage runtime
- failed or non-executed dispatches do not trigger report refresh
- the chain stays bounded to one dispatch plus one report refresh

## 7. Remaining Gap After This Stage

Even after this slice:

- there is still no repeated loop until research readiness is achieved
- the supervising agent still decides whether to invoke follow-up again
- there is still no cost/risk policy for repeated expensive reruns
