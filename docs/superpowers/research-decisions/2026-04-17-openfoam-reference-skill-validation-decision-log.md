# OpenFOAM Reference Skill Validation Decision Log

**Artifact Scope:** task-local

**Artifact Epoch:** openfoam-reference-skill-validation

**Supersedes:** `none`

**Status:** active

**Related Plan:** `docs/superpowers/plans/2026-04-17-openfoam-reference-skill-validation.md`

**Related Session Status:** `docs/superpowers/session-status/2026-04-17-openfoam-reference-skill-validation-status.md`

## Decision 1: Treat The External Zip As A Reference Skill, Not An Execution Skill
- Context: the extracted zip contains only documentation files and no runtime integration code.
- Options considered:
  - install as-is and imply it can steer execution
  - adapt it into a reference-only custom skill
  - ignore it and write a new skill from scratch
- Chosen decision: adapt it into a reference-only custom skill.
- Why this won: it preserves useful content while avoiding false claims about runtime behavior.
- Re-evaluation trigger: if a later version of the external package includes executable workflow assets or richer lifecycle metadata.

## Decision 2: Use `pitzDaily` Plus `cavity` As The Initial Official Validation Anchors
- Context: the project currently focuses on steady incompressible external-flow execution, but the official OF13 tutorial tree spans both modern and legacy organizations.
- Options considered:
  - modern OF13 `pitzDaily` only
  - legacy `cavity` only
  - `pitzDaily` plus `cavity`
- Chosen decision: use both.
- Why this won: `pitzDaily` stress-tests modern OF13 conventions, while `cavity` provides a lighter-weight incompressible sanity anchor.
- Re-evaluation trigger: if either case is impossible to execute or turns out irrelevant to the current VibeCFD substrate.

## Decision 3: Encode Official-vs-Project Distinctions Directly In The Skill
- Context: the main failure mode in adapting the external zip was not missing templates, but misleading future agents into treating official OF13 tutorial conventions and the current VibeCFD runtime as the same thing.
- Options considered:
  - keep a generic OpenFOAM guide with no explicit distinction
  - encode `Official OF13 baseline` versus `Current VibeCFD runtime-compatible` as explicit labels
  - optimize only for the current runtime and drop official tutorial framing
- Chosen decision: encode the distinction directly in the skill.
- Why this won: it preserves both official tutorial literacy and project-specific honesty, which reduces false compatibility claims.
- Re-evaluation trigger: if the project later modernizes runtime generation from `simpleFoam`-style scaffolds to official OF13 `foamRun`-style case generation.

## Decision 4: Modernize The Main Steady Incompressible Scaffold Instead Of Leaving The Gap As Documentation Only
- Context: official evidence plus `simpleFoam -help` showed a direct migration path toward `foamRun -solver incompressibleFluid`, and the remaining mismatch was no longer just a documentation concern.
- Options considered:
  - leave the gap documented but unfixed
  - fully delete all legacy files immediately
  - switch the main steady incompressible scaffold to `foamRun / incompressibleFluid` while temporarily keeping compatibility files
- Chosen decision: switch the main scaffold to `foamRun / incompressibleFluid` and keep compatibility files for now.
- Why this won: it closes the main runtime gap without forcing a risky all-at-once cleanup of every legacy assumption in the same pass.
- Re-evaluation trigger: if a later cleanup pass proves the compatibility files are no longer needed, or if another physics family needs its own modernization strategy.
