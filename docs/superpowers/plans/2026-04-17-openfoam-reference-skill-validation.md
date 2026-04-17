# OpenFOAM Reference Skill Validation Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then choose the execution skill that fits the work: use superpowers:subagent-driven-development when delegation benefits outweigh the round-trip, or superpowers:executing-plans when the work is better kept local. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the plan controls below, especially reuse, continuity, artifact lifecycle, validation/review cadence, and any research-overlay constraints.

**Goal:** Adapt the external `openfoam_skill.zip` into a project-local reference skill and use official OpenFOAM tutorial cases to validate how well the current VibeCFD OpenFOAM substrate matches authoritative OF13 practice.

**Architecture:** Keep runtime behavior stable. Add a custom reference skill under `skills/custom`, wire no new execution logic into the solver-dispatch path, and run evidence-first validation that separates official tutorial execution baseline from project-specific scaffold compatibility checks.

**Tech Stack:** repo-local custom skills, DeerFlow skill loader/router, OpenFOAM 13 sandbox image, backend solver-dispatch helpers, official OpenFOAM tutorial sources

**Prior Art Survey:** `docs/superpowers/prior-art/2026-04-17-openfoam-reference-skill-validation-survey.md`

**Reuse Strategy:** adapt existing project

**Artifact Scope:** task-local

**Artifact Epoch:** openfoam-reference-skill-validation

**Supersedes:** none

**Session Status File:** `docs/superpowers/session-status/2026-04-17-openfoam-reference-skill-validation-status.md`

**Context Summary:** none

**Primary Context Files:** `docs/superpowers/prior-art/2026-04-17-openfoam-reference-skill-validation-survey.md`; `backend/packages/harness/deerflow/skills/validation.py`; `backend/packages/harness/deerflow/skills/loader.py`; `backend/app/gateway/routers/skills.py`; `docker/openfoam-sandbox/Dockerfile`; `docker/openfoam-sandbox/README.md`; `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_case.py`; `.tmp/inspect-openfoam-skill/SKILL.md`; `.tmp/inspect-openfoam-skill/extended-templates.md`

**Artifact Lifecycle:** Keep the plan/status/survey/decision-log/findings files and the new `skills/custom/openfoam-reference` skill. Replace the extracted `.tmp/inspect-openfoam-skill` scratch copy after migration is complete. Do not create parallel execution skills or shadow runtime code paths for this slice.

**Workspace Strategy:** current workspace

**Validation Strategy:** evidence-first exploratory validation

**Review Cadence:** each milestone

**Checkpoint Strategy:** user-directed checkpoints

**Research Overlay:** enabled

**Research Mainline:** Demonstrate whether the adapted OpenFOAM reference skill plus official tutorial evidence can support the current VibeCFD steady incompressible workflow without falsely overstating OpenFOAM 13 compatibility.

**Evaluation Rubric:** the skill must validate and load cleanly; the official tutorial anchors must be traceable to authoritative OF13 sources; the sandbox/tutorial checks must produce concrete execution evidence or explicit blocker evidence; the final findings must clearly separate compatible behavior from architecture gaps.

**Non-Negotiables:** do not silently change the existing submarine runtime from `simpleFoam` to `foamRun`; do not represent the reference skill as an execution skill; use official OpenFOAM sources for tutorial truth; keep all claims tied to fresh verification evidence.

**Forbidden Regressions:** reintroducing OF12-only absolutes into project skill content; claiming the project fully matches modern OF13 tutorial architecture when only partial compatibility was proven; shipping a custom skill that fails repo frontmatter validation.

**Method Fidelity Checks:** validate the raw zip baseline before adaptation; validate the adapted skill through the repo loader and skill list path; use official tutorial paths as the comparison baseline; record exact commands and outcomes for tutorial execution or execution blockers.

**Scale Gate:** prove the slice on one modern OF13 tutorial anchor (`pitzDaily`) plus one simpler legacy incompressible anchor (`cavity`) before broadening to other physics families.

**Freeze Gate:** the slice can exit research mode once the adapted skill loads cleanly and the findings file records a clear compatibility verdict for both tutorial anchors.

**Decision Log:** `docs/superpowers/research-decisions/2026-04-17-openfoam-reference-skill-validation-decision-log.md`

**Research Findings:** `docs/superpowers/research-findings/2026-04-17-openfoam-reference-skill-validation-findings.md`

**Uncertainty Hotspots:** local Docker tutorial execution may be slower or more brittle than repo-level tests on this Windows host; the project runtime currently uses `simpleFoam` conventions while official OF13 tutorials may prefer `foamRun`; hand-added custom skills may appear without Skill Studio lifecycle metadata unless explicitly added later.

**Replan Triggers:** if the adapted skill cannot be loaded by the current repo; if official tutorial execution is impossible in the local sandbox; if the compatibility gap is large enough that validation now requires runtime refactoring rather than a reference-skill slice.

---

### Task 1: Capture The Raw Baseline And Test Matrix

**Type:** Exploratory

**Files:**
- Notes: `docs/superpowers/prior-art/2026-04-17-openfoam-reference-skill-validation-survey.md`
- Notes: `docs/superpowers/research-findings/2026-04-17-openfoam-reference-skill-validation-findings.md`

**Goal:** Record what fails or mismatches before any adaptation so the new skill and later findings are anchored to evidence rather than memory.

**Collect Evidence:**
- raw zip skill validation result
- current project runtime assumptions (`simpleFoam`-oriented scaffold, OF13 sandbox image)
- authoritative official tutorial anchors to use in later checks

**Stop and Replan If:**
- the external zip turns out to contain executable scripts or runtime integrations that materially change the reuse decision
- the official tutorial anchors do not map onto the current project workflow at all

**Checkpoint If:**
- the survey and initial findings clearly explain why the skill must be adapted instead of installed raw

- [x] **Step 1: Validate the raw extracted skill directory with the repo frontmatter validator and record the failure mode**
- [x] **Step 2: Record the current runtime assumptions from `docker/openfoam-sandbox` and `solver_dispatch_case.py` in the findings file**
- [x] **Step 3: Record the chosen official tutorial anchors (`pitzDaily`, `cavity`) and why each one is in-scope**

### Task 2: Adapt And Install The Custom Reference Skill

**Files:**
- Add: `skills/custom/openfoam-reference/SKILL.md`
- Add: `skills/custom/openfoam-reference/references/extended-templates.md`
- Add: `skills/custom/openfoam-reference/references/official-cases.md`
- Delete: `.tmp/inspect-openfoam-skill/SKILL.md`
- Delete: `.tmp/inspect-openfoam-skill/extended-templates.md`

- [x] **Step 1: Create a valid kebab-case custom skill directory that repositions the zip content as a reference-only OpenFOAM guide**
- [x] **Step 2: Rewrite the frontmatter and overview so the skill no longer claims OF12-only or `foamRun`-only rules**
- [x] **Step 3: Preserve the useful templates in a repo-local reference file and add an explicit `official-cases.md` note for `pitzDaily` and `cavity`**
- [x] **Step 4: Remove the temporary extracted zip copy once the migrated skill content exists in `skills/custom/openfoam-reference`**

### Task 3: Verify Skill Loading And Previewability

**Files:**
- Modify: `docs/superpowers/research-findings/2026-04-17-openfoam-reference-skill-validation-findings.md`

- [x] **Step 1: Re-run the repo validator against the adapted skill and confirm it passes**
- [x] **Step 2: Run the loader/list-skills path and confirm `openfoam-reference` is discoverable as a custom skill**
- [x] **Step 3: Verify the installed file tree is previewable through the existing skill-files path or equivalent loader evidence**

### Task 4: Run Official-Case Validation Against The Current Project Substrate

**Type:** Exploratory

**Files:**
- Notes: `docs/superpowers/research-findings/2026-04-17-openfoam-reference-skill-validation-findings.md`
- Notes: `docs/superpowers/research-decisions/2026-04-17-openfoam-reference-skill-validation-decision-log.md`

**Goal:** Produce a clean evidence split between official OpenFOAM tutorial execution baseline and project-specific case-generation compatibility.

**Collect Evidence:**
- whether the local OF13 sandbox can execute or at least enter the selected official tutorial cases
- where the current VibeCFD scaffold matches or diverges from the official tutorial structure
- which differences are documentation-only versus real runtime blockers

**Stop and Replan If:**
- tutorial execution requires a broader runtime change than this slice allows
- no trustworthy local execution evidence can be collected from the sandbox

**Checkpoint If:**
- both tutorial anchors have an explicit compatibility verdict in the findings file

- [x] **Step 1: Attempt a minimal official `pitzDaily` run in the local OpenFOAM 13 sandbox and capture success or blocker evidence**
- [x] **Step 2: Attempt a minimal official `cavity` sanity run or structure check and capture success or blocker evidence**
- [x] **Step 3: Compare the official tutorial structure against the current project scaffold and record compatible assumptions, mismatches, and risk level**
- [x] **Step 4: Record any durable decision about how the new skill should describe OF13-vs-project differences**

### Task 5: Final Verification And Handoff

**Files:**
- Modify: `docs/superpowers/session-status/2026-04-17-openfoam-reference-skill-validation-status.md`
- Modify: `docs/superpowers/research-findings/2026-04-17-openfoam-reference-skill-validation-findings.md`
- Modify: `docs/superpowers/research-decisions/2026-04-17-openfoam-reference-skill-validation-decision-log.md`

- [x] **Step 1: Refresh the status file with the latest verified state, open gaps, and next recommended step**
- [x] **Step 2: Run the final verification commands for skill validation / loading evidence and record them in the findings file**
- [x] **Step 3: Confirm artifact hygiene matches this plan before reporting the slice state**
