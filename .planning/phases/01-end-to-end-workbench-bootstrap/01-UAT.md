---
status: complete
phase: 01-end-to-end-workbench-bootstrap
source:
  - 01-01-SUMMARY.md
  - 01-02-SUMMARY.md
  - 01-03-SUMMARY.md
started: 2026-04-01T09:40:00Z
updated: 2026-04-01T09:54:59Z
---

## Current Test

[testing complete]

## Tests

### 1. New STL-Backed Study Bootstrap
expected: From `/workspace/submarine/new`, uploading `suboff_solid.stl` and sending the first prompt should create a real thread, route to `/workspace/submarine/{threadId}`, keep the attachment chip and first prompt visible, and avoid `Invalid URL` or unhandled bootstrap failures.
result: pass

### 2. Refresh Preserves Created Study Context
expected: Reloading a created submarine thread should keep the same title, uploaded STL, first prompt, clarification/design-brief state, and artifact downloads instead of dropping back to a blank new-study shell.
result: pass

### 3. Incomplete Inputs Stay Recoverable Inside The Submarine Cockpit
expected: When the brief is still missing operating conditions, the user should remain on the dedicated submarine route and see clarification guidance, pending questions, and design-brief artifacts inside the workbench rather than a generic chat fallback or tool error.
result: pass

## Summary

total: 3
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None.
