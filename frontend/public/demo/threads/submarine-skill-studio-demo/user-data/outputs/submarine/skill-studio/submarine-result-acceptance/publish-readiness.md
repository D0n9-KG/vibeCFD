# submarine-result-acceptance publish readiness

- status: `ready_for_review`
- publish_gate_count: `5`
- blocking_count: `0`

## Gates
- `passed` Skill structure is valid
- `passed` Trigger description is discoverable
- `passed` Scenario tests are prepared
- `passed` Dry-run handoff is ready
- `passed` UI metadata has been generated

## Next Actions
- Run a dry-run conversation using one of the prepared scenarios.
- Review the generated SKILL.md, domain rules, and UI metadata together.
- Publish only after the expert signs off on the dry-run result.
