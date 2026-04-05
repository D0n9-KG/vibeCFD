# Submarine Sub-Agent Roles

Reserved role boundaries for the DeerFlow-native submarine workflow:

- `submarine-task-intelligence`
  - case search
  - task understanding
  - workflow recommendation
- `submarine-geometry-preflight`
  - `STL` inspection within the v1 STL-only runtime boundary
  - scale sanity checks
  - family mapping
- `submarine-solver-dispatch`
  - case packaging
  - solver handoff
  - execution log tracking
- `submarine-result-reporting`
  - artifact curation
  - report generation
  - archive-ready output

Runtime handoff expectations:

- `submarine-task-intelligence` should hand off candidate cases and workflow assumptions.
- `submarine-geometry-preflight` should hand off `review_status`, `next_recommended_stage`, and geometry artifacts.
- `submarine-solver-dispatch` should hand off request manifests, execution logs when present, and dispatch review fields.
- `submarine-result-reporting` should convert accumulated runtime artifacts into Chinese summary and final review outputs.
