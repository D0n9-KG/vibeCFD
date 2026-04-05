---
name: submarine-result-acceptance
description: Use when a submarine CFD workflow needs an explicit acceptance decision before delivery.
---

# submarine-result-acceptance

## Overview
Define how Claude Code and reporting subagents should decide whether a submarine CFD run is trustworthy, needs review, or should be rerun.

## Trigger Conditions
- the user asks whether the current CFD result is trustworthy
- Claude Code needs a final acceptance decision before delivery
- result-reporting needs a clear delivery conclusion

## Workflow
1. review mesh, residual, and force summaries from the current run
2. decide whether the run is deliverable, risky, or should be rerun
3. produce a Chinese acceptance conclusion with evidence and next-step advice

## Acceptance Criteria
- state an explicit delivery decision
- cite which CFD indicators support that decision

## Validation Scenarios
- baseline steady-state bare-hull case with stable Cd and residual decay
- report generated despite residuals staying high and force history oscillating
