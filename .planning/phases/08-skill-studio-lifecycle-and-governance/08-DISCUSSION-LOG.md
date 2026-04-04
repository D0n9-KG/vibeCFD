# Phase 8: Skill Studio Lifecycle and Governance - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 08-skill-studio-lifecycle-and-governance
**Areas discussed:** current UI baseline, graph and publish retention, skill application model, version and rollback model

---

## Current UI baseline

| Option | Description | Selected |
|--------|-------------|----------|
| Reopen Phase 7 shell decisions | Rework the shared workspace shell and Skill Studio top-level IA again inside Phase 8 | |
| Treat the current post-Phase-7 redesign as the baseline | Build lifecycle governance on top of the current `Create / Evaluate / Connect` direction and focused workbench pattern | x |

**User's choice:** Treat the current post-Phase-7 redesign as the baseline.
**Notes:** The user explicitly said that more frontend page design changes landed after Phase 7. The accepted direction is to carry those changes forward instead of reopening shell architecture work.

---

## Graph and publish retention

| Option | Description | Selected |
|--------|-------------|----------|
| De-emphasize graph into generic relationship hints only | Keep lightweight relationship signals but remove the graph as a first-class work surface | |
| Keep graph and publish as first-class lifecycle capabilities | Preserve the dedicated graph view for relationship reasoning and keep publish as the real application path | x |
| Stop at readiness summaries without a real publish action | Treat Skill Studio as review-only and leave actual application outside the product | |

**User's choice:** Keep graph and publish as first-class lifecycle capabilities.
**Notes:** The user explicitly said the graph is valuable because it clearly shows relationships between skills, and also pushed back on removing publish because the product needs a real answer for how the skill is applied after review.

---

## Skill application model

| Option | Description | Selected |
|--------|-------------|----------|
| Global auto-discovery only | Publish and enable the skill, then let agents choose from the enabled skill pool automatically | |
| Explicit prebinding only | Skills run only when manually attached to a step or subagent | |
| Dual-layer model | Keep global enabled-skill discovery, but also support explicit per-step or per-subagent binding when needed | x |

**User's choice:** Dual-layer model.
**Notes:** The user asked whether skills should be found automatically by the agent or set up ahead of time, and specifically wants a feature for configuring a skill to a specific step. Existing `target_skills` runtime contracts make the dual-layer approach the strongest fit.

---

## Version and rollback model

| Option | Description | Selected |
|--------|-------------|----------|
| Thread-centered version history | Treat each Skill Studio thread as the main version record | |
| Skill-asset-centered version history | Keep threads as creation workspaces, while revisions, version notes, and rollback targets belong to the skill record | x |
| No explicit version model | Keep today's overwrite publish behavior without first-class history or rollback targets | |

**User's choice:** Skill-asset-centered version history.
**Notes:** The user approved the recommendation after asking for a clearer explanation. Phase 8 should therefore promote the skill itself to the primary governance object, with thread history staying secondary.

---

## the agent's Discretion

- Exact naming of `图谱` versus `连接`, as long as the graph remains explicit and easy to find.
- Exact screen placement for revision history, rollback targets, enable or disable state, and publish indicators.
- Exact interaction design for configuring step-bound skill usage, as long as users can see and edit the assignment clearly.

## Deferred Ideas

- Marketplace-style or organization-wide skill governance is still out of scope for this phase.
- Deployment isolation and sandbox policy remain Phase 9 work.
- Large-scale architecture cleanup remains Phase 10 work unless a small supporting refactor is unavoidable.
