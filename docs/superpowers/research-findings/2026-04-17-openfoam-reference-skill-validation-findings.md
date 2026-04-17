# OpenFOAM Reference Skill Validation Findings

**Artifact Scope:** task-local

**Artifact Epoch:** openfoam-reference-skill-validation

**Supersedes:** `none`

**Status:** active

**Related Plan:** `docs/superpowers/plans/2026-04-17-openfoam-reference-skill-validation.md`

**Related Session Status:** `docs/superpowers/session-status/2026-04-17-openfoam-reference-skill-validation-status.md`

## Batch 1: Raw Baseline Capture

**Question / Hypothesis**
- The external `openfoam_skill.zip` is useful, but it should fail raw installation/validation and therefore must be adapted before project use.

**Protocol**
- Inspect the extracted zip contents.
- Compare raw skill metadata against repo validation rules.
- Compare the raw skill's OpenFOAM assumptions against the current project runtime.

**Verified Facts**
- The extracted zip contains only `SKILL.md` and `extended-templates.md`; there are no scripts or runtime hooks.
- The raw frontmatter name is `openfoam_skill`, which violates the repo's kebab-case validation rule in `backend/packages/harness/deerflow/skills/validation.py`.
- The raw skill text is written as an OpenFOAM 12 + `foamRun`-centric guide and explicitly warns against legacy solver executables.
- The current project sandbox installs OpenFOAM 13 and the current submarine scaffold still resolves to `simpleFoam`-style execution.
- Official OpenFOAM 13 sources confirm that both modern (`tutorials/fluid/pitzDaily`) and legacy (`tutorials/legacy/incompressible/icoFoam/cavity`) tutorial structures still matter for this slice.

**Open Hypotheses**
- The adapted reference skill should load cleanly without requiring extra Skill Studio lifecycle metadata.
- The local Docker environment may still be able to run the chosen tutorials if execution commands are kept narrow enough.

**Negative Results / Failures**
- None recorded yet beyond the already-known raw incompatibility.

**Next Step**
- Adapt the raw material into `skills/custom/openfoam-reference`, then validate loading and official-case evidence.

## Batch 2: Adapted Skill And Official-Case Validation

**Question / Hypothesis**
- After adaptation, the custom skill should load cleanly, and the official tutorial evidence should show a split outcome: `cavity` is a fast positive baseline while `pitzDaily` is a valid modern OF13 anchor that is heavier and not directly equivalent to the current project scaffold.

**Protocol**
- Validate the raw extracted skill and the adapted custom skill with the repo validator.
- Verify discoverability through `load_skills(enabled_only=False)`.
- Verify the installed file tree for the new skill.
- Run official tutorial commands inside `deer-flow-openfoam-sandbox:latest`.
- Compare official tutorial structure against the current project-generated scaffold.

**Commands**
- Raw/adapted validation:
  - `uv run --project backend python -` with `_validate_skill_frontmatter(Path('.tmp/inspect-openfoam-skill'))` and `_validate_skill_frontmatter(Path('skills/custom/openfoam-reference'))`
- Loader verification:
  - `uv run --project backend python -` with `load_skills(enabled_only=False)`
- File-tree verification:
  - `PYTHONPATH=backend uv run --project backend python -` with `_build_skill_file_tree_nodes(...)`
- Docker/tutorial verification:
  - `docker run --rm --entrypoint sh deer-flow-openfoam-sandbox:latest -lc "echo container-ok"`
  - `docker run --rm --entrypoint bash deer-flow-openfoam-sandbox:latest -lc '. /opt/openfoam13/etc/bashrc >/dev/null 2>&1; echo FOAM_TUTORIALS=$FOAM_TUTORIALS; test -d "$FOAM_TUTORIALS/fluid/pitzDaily" && echo PITZ=yes || echo PITZ=no; test -d "$FOAM_TUTORIALS/legacy/incompressible/icoFoam/cavity" && echo CAVITY=yes || echo CAVITY=no'`
  - `docker run --rm --entrypoint bash deer-flow-openfoam-sandbox:latest -lc '. /opt/openfoam13/etc/bashrc >/dev/null 2>&1; cd "$FOAM_TUTORIALS/fluid/pitzDaily" && blockMesh -dict "$FOAM_TUTORIALS/resources/blockMesh/pitzDaily" >/tmp/pitz-direct-blockMesh.log 2>&1 && timeout 60s foamRun > /tmp/pitz-direct-foamRun.log 2>&1; status=$?; echo STATUS=$status; echo "FOAMRUN:"; tail -n 60 /tmp/pitz-direct-foamRun.log'`
  - `docker run --rm --entrypoint bash deer-flow-openfoam-sandbox:latest -lc '. /opt/openfoam13/etc/bashrc >/dev/null 2>&1; cd "$FOAM_TUTORIALS/legacy/incompressible/icoFoam/cavity/cavity" && blockMesh > /tmp/cavity-blockMesh.log 2>&1 && icoFoam > /tmp/cavity-icoFoam.log 2>&1; status=$?; echo STATUS=$status; echo "BLOCKMESH:"; tail -n 20 /tmp/cavity-blockMesh.log; echo "ICOFOAM:"; tail -n 30 /tmp/cavity-icoFoam.log'`

**Verified Facts**
- Raw skill validation fails exactly as expected:
  - `.tmp/inspect-openfoam-skill` -> `Name 'openfoam_skill' should be hyphen-case (lowercase letters, digits, and hyphens only)`
- Adapted skill validation passes:
  - `skills/custom/openfoam-reference` -> `Skill is valid!`
- Loader verification finds exactly one custom skill named `openfoam-reference`.
- Installed file-tree verification shows the expected entries:
  - top level: `SKILL.md`, `references/`
  - references: `references/extended-templates.md`, `references/official-cases.md`
- Minimal container startup succeeds:
  - `container-ok`
- Official tutorial roots are present in the local OF13 sandbox:
  - `FOAM_TUTORIALS=/opt/openfoam13/tutorials`
  - `PITZ=yes`
  - `CAVITY=yes`
- `pitzDaily` evidence is a real run, not a structure-only check:
  - `blockMesh` completes successfully
  - direct `foamRun` enters repeated `PIMPLE` iterations with `Ux`, `Uy`, `e`, `p`, `rho`, and `k` updates
  - the 60-second timebox exits with `STATUS=124`, so this is a bounded partial execution rather than a completed run
- `cavity` evidence is a completed run:
  - `blockMesh` succeeds with a 400-cell mesh
  - `icoFoam` reaches `Time = 0.5s` and ends cleanly with `STATUS=0`
- Fresh repo verification stays green after the skill is added:
  - `uv run --project backend pytest backend/tests/test_skills_router.py -q` -> `10 passed`
- Fresh loader/file-tree verification after cleanup still succeeds:
  - validator passes
  - loader still finds `openfoam-reference`
  - file-tree still exposes `SKILL.md`, `references/extended-templates.md`, and `references/official-cases.md`
- Fresh tutorial verification after cleanup still succeeds:
  - `cavity` again exits `STATUS=0`
  - `pitzDaily` again enters real `foamRun` iterations inside a 20-second timebox and exits `STATUS=124`
- Current project scaffold evidence remains explicitly `simpleFoam`-style:
  - generated `solver_application` is `simpleFoam`
  - generated files include `constant/transportProperties` and `constant/turbulenceProperties`
  - generated `system/controlDict` contains `application     simpleFoam;`
- Official modern `pitzDaily` structure differs materially from the current scaffold:
  - official `controlDict` uses `solver          fluid;`
  - official constant dictionaries include `physicalProperties` and `momentumTransport`

**Compatibility Verdict**
- `cavity`: compatible as a low-complexity tutorial literacy and environment sanity anchor.
- `pitzDaily`: compatible as an official OF13 substrate anchor, but only partially aligned with the current VibeCFD case-generation model.
- Current VibeCFD runtime vs official modern OF13 tutorials: partial compatibility, not parity.

**Open Hypotheses**
- A longer or more targeted `pitzDaily` execution window could finish cleanly, but that was not required to prove the environment and architecture distinction.
- If the control-center UI later needs lifecycle metadata for hand-added skills, `openfoam-reference` may need a follow-up lifecycle record rather than more skill-content changes.

**Negative Results / Failures**
- `pitzDaily` does not finish inside a 60-second timebox on this Windows-hosted local Docker environment.
- An earlier PowerShell attempt mis-expanded `$FOAM_TUTORIALS`; this was corrected with stricter shell quoting and should not be treated as a real runtime failure.

**Next Step**
- Refresh the task-local status/plan files, retire the raw extraction copy, and report the slice as validated-with-gaps rather than overclaiming full OF13 parity.

## Batch 3: Runtime Modernization Follow-Through

**Question / Hypothesis**
- The remaining steady-incompressible OF13 gap can be reduced safely by modernizing the generated submarine scaffold to `foamRun / incompressibleFluid` while keeping temporary compatibility files for older expectations.

**Protocol**
- Write a failing scaffold test that expects modern OF13 incompressible files and command entry.
- Update the case scaffold, report copy, and case-catalog recommendations.
- Re-run targeted backend suites.
- Run a real generated-case smoke test inside the OF13 sandbox.

**Verified Facts**
- The failing scaffold test was created and then passed after implementation.
- The generated case scaffold now returns:
  - `solver_application: foamRun`
  - `solver_module: incompressibleFluid`
- The generated case now writes modern dictionaries:
  - `constant/physicalProperties`
  - `constant/momentumTransport`
- The generated `Allrun` now uses `foamRun` rather than `simpleFoam`.
- The submarine case catalog now recommends `OpenFOAM foamRun / incompressibleFluid` for the steady incompressible cases that previously advertised `simpleFoam`.
- The result-reporting copy was updated so it no longer claims the entry script uses `simpleFoam`.
- Fresh targeted backend verification passed:
  - `uv run --project backend pytest backend/tests/test_submarine_solver_dispatch_tool.py -q` -> `50 passed`
  - `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py backend/tests/test_submarine_experiment_linkage_contracts.py backend/tests/test_skills_router.py -q` -> `54 passed`
- Fresh real smoke test on a project-generated modern case passed in the OF13 sandbox:
  - generated case exits `STATUS=0`
  - log reaches `End`
  - runtime is clearly `foamRun / incompressibleFluid`
- Final fresh regression verification passed after the last doc/skill sync:
  - `uv run --project backend pytest backend/tests/test_submarine_solver_dispatch_tool.py backend/tests/test_submarine_result_report_tool.py backend/tests/test_submarine_experiment_linkage_contracts.py backend/tests/test_skills_router.py -q` -> `104 passed`
  - validator still reports `Skill is valid!`
  - loader still finds `openfoam-reference`

**Compatibility Verdict**
- Current VibeCFD steady incompressible submarine scaffold is now aligned with the modern OF13 execution entry.
- Legacy compatibility files may still exist temporarily, but they are no longer the primary execution path.

**Open Hypotheses**
- A future cleanup slice can decide whether the temporary legacy compatibility files should be retired entirely.
- Other physics families still need their own modernization pass before we can claim repo-wide OF13 parity.

**Negative Results / Failures**
- None remained after the modernization pass and fresh verification.

**Next Step**
- Treat the steady incompressible runtime gap as closed for this slice; if we continue later, focus on either retiring the temporary compatibility files or modernizing other physics families.
