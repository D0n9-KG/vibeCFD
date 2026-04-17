# OpenFOAM Reference Skill Validation Prior Art Survey

**Artifact Scope:** task-local

**Artifact Epoch:** openfoam-reference-skill-validation

**Supersedes:** `none`

**Status:** active

**Related Plan:** `docs/superpowers/plans/2026-04-17-openfoam-reference-skill-validation.md`

**Related Session Status:** `docs/superpowers/session-status/2026-04-17-openfoam-reference-skill-validation-status.md`

**Question:** Should this project integrate the external `openfoam_skill.zip` as-is, adapt it into a project-local reference skill, or ignore it and build a new OpenFOAM reference layer from scratch?

**Constraints:** The current project runtime is OpenFOAM 13 in `docker/openfoam-sandbox`, the active submarine execution path still generates `simpleFoam`-style cases, the external zip is documentation-only rather than executable workflow logic, and any validation claims should be grounded in official OpenFOAM tutorial sources rather than secondary summaries.

## Candidate References
- External zip skill at `C:\Users\D0n9\Documents\xwechat_files\wxid_pvdxkm1ybhsh22_9f69\msg\file\2026-04\openfoam_skill.zip`
  - Strength: already contains dictionary templates, BC tables, and tutorial pointers.
  - Weakness: hard-coded to OpenFOAM 12, claims `foamRun`-only architecture, and fails current repo frontmatter validation because the skill name uses an underscore.
- Official OpenFOAM 13 tutorial source: `tutorials/fluid/pitzDaily/Allrun`
  - Source: `https://github.com/OpenFOAM/OpenFOAM-13/blob/441953dfbb4270dd54e14672e194e4a4a478afc4/tutorials/fluid/pitzDaily/Allrun`
  - Signal: modern OF13 tutorial that runs `blockMesh` plus `foamRun`.
- Official OpenFOAM 13 tutorial source: `tutorials/fluid/pitzDaily/system/controlDict`
  - Source: `https://github.com/OpenFOAM/OpenFOAM-13/blob/441953dfbb4270dd54e14672e194e4a4a478afc4/tutorials/fluid/pitzDaily/system/controlDict`
  - Signal: modern OF13 control dictionary using `solver fluid;`.
- Official OpenFOAM 13 legacy tutorial source: `tutorials/legacy/incompressible/icoFoam/cavity/Allrun`
  - Source: `https://github.com/OpenFOAM/OpenFOAM-13/blob/441953dfbb4270dd54e14672e194e4a4a478afc4/tutorials/legacy/incompressible/icoFoam/cavity/Allrun`
  - Signal: still-relevant baseline tutorial for simple incompressible case structure and dictionary sanity.
- Project-local runtime source: `docker/openfoam-sandbox/Dockerfile`
  - Signal: project sandbox explicitly installs OpenFOAM 13 and checks `simpleFoam`, `blockMesh`, and `snappyHexMesh`.
- Project-local case generator: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_case.py`
  - Signal: current VibeCFD case scaffold still writes `transportProperties`, `turbulenceProperties`, and `application simpleFoam;`.

## Reuse Options
- Reuse dependency: not suitable.
  - The external zip is not a library/package; it is documentation content.
- Adapt existing project: suitable.
  - Adapt the external zip into a repo-local custom reference skill that explicitly documents the mismatch between modern OF13 tutorials and the current VibeCFD runtime assumptions.
- Fork and modify: not suitable.
  - There is no external executable project to fork, only a compact reference skill.
- Reference only: suitable for the official tutorial material.
  - Use official OpenFOAM 13 tutorial cases as validation anchors and compatibility checks.
- Build from scratch: not justified.
  - The external zip already contains useful structure and templates; the official OpenFOAM 13 sources already define the authoritative tutorial baselines.

## Recommended Strategy
- Adapt the external zip into a project-local custom reference skill, and use official OpenFOAM 13 tutorial sources as the authoritative validation baseline.

## Why This Wins
- Preserves useful curated reference content from the zip without pretending it can directly drive runtime execution.
- Avoids shipping incorrect OF12-only claims into the project.
- Keeps the current solver-dispatch runtime stable while still exposing official-case knowledge to the lead agent and the user-facing skill inventory.
- Gives the team a concrete evidence trail for where the current `simpleFoam`-oriented runtime aligns with or diverges from modern OF13 tutorials.

## Why Not The Others
- Reuse dependency: there is no dependency to adopt.
- Fork and modify: the source material is too small and too documentation-centric to justify a fork workflow.
- Reference only without adaptation: would leave the project without an installed, previewable custom skill.
- Build from scratch: would duplicate useful material already present in the zip and official tutorials.

## Sources
- `https://github.com/OpenFOAM/OpenFOAM-13/blob/441953dfbb4270dd54e14672e194e4a4a478afc4/tutorials/fluid/pitzDaily/Allrun`
- `https://github.com/OpenFOAM/OpenFOAM-13/blob/441953dfbb4270dd54e14672e194e4a4a478afc4/tutorials/fluid/pitzDaily/system/controlDict`
- `https://github.com/OpenFOAM/OpenFOAM-13/blob/441953dfbb4270dd54e14672e194e4a4a478afc4/tutorials/legacy/incompressible/icoFoam/cavity/Allrun`
- `docker/openfoam-sandbox/Dockerfile`
- `docker/openfoam-sandbox/README.md`
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_case.py`
- `backend/packages/harness/deerflow/skills/validation.py`
