# VibeCFD Timeline Workbench Prior Art Survey

**Question:** VibeCFD should evolve from a fixed stage/workflow UI into a flexible, AI-native CFD research surface that can automatically cut new "pages" as work advances, let users inspect earlier slices in detail, and optionally branch from prior slices without destructive rollback.

**Constraints:**
- Must feel like `vibecoding`, not a hard-coded wizard or workflow runner.
- Must preserve scientific traceability: earlier states, evidence, artifacts, and agent reasoning should stay inspectable.
- Must work with the current DeerFlow / LangGraph thread architecture instead of inventing a separate history stack.
- First release should emphasize historical inspection and branching, not destructive state rollback of CFD results.

## Candidate References

- [Figma version history](https://help.figma.com/hc/en-us/articles/360038006754-View-a-file-s-version-history): named checkpoints, shareable links to specific versions, and the ability to browse a prior state without overwriting the current one.
- [Figma branching guide](https://help.figma.com/hc/de/articles/360063144053-Leitfaden-zum-Branching): isolated branches for experiments, explicit review/merge, and archived branch history.
- [Replit Agent checkpoints and rollbacks](https://docs.replit.com/core-concepts/agent/checkpoints-and-rollbacks): automatic milestone snapshots that capture full project context, not just files.
- [v0 Versions](https://v0.app/docs/versions): each meaningful agent generation creates a version; restoring an old state creates a new latest version instead of mutating history.
- [v0 Fork Chat](https://v0.app/docs/api/platform/reference/chats/fork): fork from a specific version to explore an alternate path without affecting the original conversation.
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence): threads, checkpoints, time travel, and forking from arbitrary checkpoints.
- [W&B Run Comparer](https://docs.wandb.ai/models/app/features/panels/run-comparer): compare visible runs side-by-side and focus the UI on differences, not just chronology.
- [W&B lineage graphs](https://docs.wandb.ai/guides/registry/lineage/): show inputs, outputs, and audit history for artifacts and runs.
- [MLflow Tracking UI](https://mlflow.org/docs/latest/ml/tracking/): experiment listing, comparison, search/filter, and remote artifact-backed team workflows.

## Reuse Options

- **Reuse dependency:** Not suitable as a direct UI dependency. None of the products above can be dropped into VibeCFD unchanged.
- **Adapt existing project:** Not suitable as a base product. Figma / Replit / v0 / W&B / MLflow solve adjacent problems, not a CFD-native agentic research cockpit.
- **Fork and modify:** Not suitable. These are products/platforms, not a practical frontend base for this repo.
- **Reference only:** Strong candidate. Their interaction models map well onto VibeCFD:
  - Figma: version links, branch/archive mental model
  - Replit: milestone checkpoints with complete context
  - v0: version-per-meaningful-generation and fork-from-version
  - W&B / MLflow: experiment compare, lineage, and provenance surfaces
  - LangGraph: underlying checkpoint/time-travel mechanism
- **Build from scratch:** Justified for the actual VibeCFD UI, but only while reusing the checkpoint and lineage ideas above.

## Recommended Strategy

- **Reference only + local adaptation on top of LangGraph checkpoints**

## Why This Wins

- It keeps VibeCFD flexible: page/slice creation is driven by meaningful AI or artifact events, not a fixed stage table.
- It preserves scientific traceability: every slice can retain prompt context, files, artifacts, decisions, and later comparisons.
- It matches the current stack: LangGraph already models threads and checkpoints, including time travel and forking.
- It avoids the wrong product smell: a fixed "proposal -> execution -> report" rail can be replaced by dynamic research slices with timeline navigation.
- It gives a safe first release path: historical inspection and branch-from-here can ship before any destructive state restoration.

## Why Not The Others

- **Direct reuse dependency:** Too mismatched to VibeCFD's CFD + agent + sandbox context.
- **Adapt/fork an external product:** Unrealistic integration cost and poor domain fit.
- **Pure greenfield without references:** Would likely reinvent weaker versions of checkpoint history, branching, and experiment comparison patterns that already exist elsewhere.

## Local Leverage In This Repo

- Demo thread payloads already contain `checkpoint_id` and `parent_checkpoint_id`, which suggests the thread model is already compatible with checkpoint-aware UI.
- The current frontend still hard-codes an eight-module research flow in:
  - `frontend/src/components/workspace/submarine-workbench/submarine-session-model.ts`
  - `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.tsx`
- This means the likely migration path is:
  1. replace fixed modules with dynamic "research slices"
  2. derive slices from checkpoints + semantic events + artifact arrivals
  3. add inspect-history / compare / branch-from-here affordances

## Sources

- https://help.figma.com/hc/en-us/articles/360038006754-View-a-file-s-version-history
- https://help.figma.com/hc/de/articles/360063144053-Leitfaden-zum-Branching
- https://docs.replit.com/core-concepts/agent/checkpoints-and-rollbacks
- https://v0.app/docs/versions
- https://v0.app/docs/api/platform/reference/chats/fork
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.wandb.ai/models/app/features/panels/run-comparer
- https://docs.wandb.ai/guides/registry/lineage/
- https://mlflow.org/docs/latest/ml/tracking/
