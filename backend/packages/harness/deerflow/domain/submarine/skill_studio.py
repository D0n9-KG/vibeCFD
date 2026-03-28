"""Skill-studio helpers for expert-authored submarine CFD skills."""

from __future__ import annotations

import json
import re
import zipfile
from html import escape
from pathlib import Path

ASSISTANT_MODE = "claude-code-skill-creator"
ASSISTANT_LABEL = "Claude Code · Skill Creator"
BUILTIN_SKILLS = ["skill-creator", "writing-skills"]


def _slugify_skill_name(value: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "submarine-domain-skill"


def _artifact_virtual_path(skill_slug: str, filename: str) -> str:
    return f"/mnt/user-data/outputs/submarine/skill-studio/{skill_slug}/{filename}"


def _build_skill_archive(*, draft_dir: Path, archive_path: Path, skill_slug: str) -> None:
    package_files = [
        draft_dir / "SKILL.md",
        draft_dir / "agents" / "openai.yaml",
    ]
    package_dirs = [
        draft_dir / "references",
        draft_dir / "scripts",
        draft_dir / "assets",
    ]

    with zipfile.ZipFile(
        archive_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for file_path in package_files:
            if not file_path.is_file():
                continue
            relative_path = file_path.relative_to(draft_dir).as_posix()
            archive.write(file_path, arcname=f"{skill_slug}/{relative_path}")

        for directory in package_dirs:
            if not directory.is_dir():
                continue
            for file_path in sorted(directory.rglob("*")):
                if not file_path.is_file():
                    continue
                relative_path = file_path.relative_to(draft_dir).as_posix()
                archive.write(file_path, arcname=f"{skill_slug}/{relative_path}")


def _build_description(
    *,
    skill_purpose: str,
    trigger_conditions: list[str],
) -> str:
    trigger_text = "; ".join(trigger_conditions[:3]) or skill_purpose
    return f"Use when {trigger_text}."


def _build_skill_markdown(
    *,
    skill_name: str,
    description: str,
    skill_purpose: str,
    trigger_conditions: list[str],
    workflow_steps: list[str],
    acceptance_criteria: list[str],
    test_scenarios: list[str],
) -> str:
    triggers_md = "\n".join(f"- {item}" for item in trigger_conditions)
    workflow_md = "\n".join(
        f"{index}. {item}" for index, item in enumerate(workflow_steps, start=1)
    )
    acceptance_md = "\n".join(f"- {item}" for item in acceptance_criteria)
    scenarios_md = "\n".join(f"- {item}" for item in test_scenarios)
    return "\n".join(
        [
            "---",
            f"name: {skill_name}",
            f"description: {description}",
            "---",
            "",
            f"# {skill_name}",
            "",
            "## Overview",
            skill_purpose,
            "",
            "## Trigger Conditions",
            triggers_md or "- Pending expert input",
            "",
            "## Workflow",
            workflow_md or "1. Pending expert workflow definition",
            "",
            "## Acceptance Criteria",
            acceptance_md or "- Pending expert acceptance criteria",
            "",
            "## Validation Scenarios",
            scenarios_md or "- Pending expert validation scenarios",
            "",
        ],
    )


def _build_rules_markdown(
    *,
    expert_rules: list[str],
    acceptance_criteria: list[str],
    test_scenarios: list[str],
) -> str:
    expert_rules_md = "\n".join(f"- {item}" for item in expert_rules) or "- None yet"
    acceptance_md = "\n".join(f"- {item}" for item in acceptance_criteria) or "- None yet"
    scenarios_md = "\n".join(f"- {item}" for item in test_scenarios) or "- None yet"
    return "\n".join(
        [
            "# Domain Rules",
            "",
            "## Expert Rules",
            expert_rules_md,
            "",
            "## Acceptance Criteria",
            acceptance_md,
            "",
            "## Validation Scenarios",
            scenarios_md,
            "",
        ],
    )


def _build_openai_yaml(
    *,
    skill_title: str,
    description: str,
    skill_slug: str,
) -> str:
    short_description = description
    default_prompt = (
        f"Help me draft, validate, and prepare the {skill_slug} skill for publishing."
    )
    return "\n".join(
        [
            f"display_name: {skill_title.strip()}",
            f"short_description: {short_description}",
            f"default_prompt: {default_prompt}",
            "",
        ]
    )


def _validate_skill(
    *,
    skill_name: str,
    description: str,
    skill_markdown: str,
    trigger_conditions: list[str],
    workflow_steps: list[str],
    acceptance_criteria: list[str],
    test_scenarios: list[str],
) -> dict:
    checks = {
        "skill_name_slug_format": (
            "passed" if re.fullmatch(r"[a-z0-9-]{1,64}", skill_name) else "failed"
        ),
        "description_starts_with_use_when": (
            "passed" if description.startswith("Use when") else "failed"
        ),
        "has_overview_section": (
            "passed" if "## Overview" in skill_markdown else "failed"
        ),
        "has_workflow_section": (
            "passed" if "## Workflow" in skill_markdown else "failed"
        ),
        "has_acceptance_section": (
            "passed" if "## Acceptance Criteria" in skill_markdown else "failed"
        ),
        "has_validation_section": (
            "passed" if "## Validation Scenarios" in skill_markdown else "failed"
        ),
        "trigger_conditions_present": "passed" if trigger_conditions else "failed",
        "workflow_steps_present": "passed" if workflow_steps else "failed",
        "acceptance_criteria_present": "passed" if acceptance_criteria else "failed",
        "test_scenarios_present": "passed" if test_scenarios else "failed",
    }
    errors = [key for key, result in checks.items() if result == "failed"]
    warnings: list[str] = []
    if len(description) > 500:
        warnings.append("description_too_long")

    status = "ready_for_review" if not errors else "needs_revision"
    return {
        "status": status,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }


def _build_test_matrix(
    *,
    skill_slug: str,
    test_scenarios: list[str],
    validation: dict,
) -> dict:
    blocked_reasons = list(validation["errors"])
    scenario_tests = []
    can_dry_run = validation["error_count"] == 0 and len(test_scenarios) > 0

    for index, scenario in enumerate(test_scenarios, start=1):
        scenario_tests.append(
            {
                "id": f"scenario-{index}",
                "scenario": scenario,
                "status": "ready_for_dry_run" if can_dry_run else "blocked",
                "expected_outcome": (
                    "Claude Code should trigger the drafted skill and produce a reviewable output."
                ),
                "blocking_reasons": [] if can_dry_run else blocked_reasons,
            }
        )

    return {
        "skill_name": skill_slug,
        "status": "ready_for_dry_run" if can_dry_run else "blocked",
        "scenario_test_count": len(scenario_tests),
        "blocking_count": 0 if can_dry_run else len(blocked_reasons),
        "scenario_tests": scenario_tests,
    }


def _build_publish_readiness(
    *,
    skill_slug: str,
    validation: dict,
    test_matrix: dict,
    ui_metadata_virtual_path: str,
) -> dict:
    gates = [
        {
            "id": "structure",
            "label": "Skill structure is valid",
            "status": "passed" if validation["error_count"] == 0 else "failed",
        },
        {
            "id": "trigger",
            "label": "Trigger description is discoverable",
            "status": (
                "passed"
                if validation["checks"]["description_starts_with_use_when"] == "passed"
                else "failed"
            ),
        },
        {
            "id": "scenarios",
            "label": "Scenario tests are prepared",
            "status": "passed" if test_matrix["scenario_test_count"] > 0 else "failed",
        },
        {
            "id": "dry-run",
            "label": "Dry-run handoff is ready",
            "status": "passed" if test_matrix["status"] == "ready_for_dry_run" else "failed",
        },
        {
            "id": "ui-metadata",
            "label": "UI metadata has been generated",
            "status": "passed" if ui_metadata_virtual_path else "failed",
        },
    ]

    blocking_count = sum(1 for gate in gates if gate["status"] != "passed")
    status = "ready_for_review" if blocking_count == 0 else "blocked"
    next_actions = (
        [
            "Run a dry-run conversation using one of the prepared scenarios.",
            "Review the generated SKILL.md, domain rules, and UI metadata together.",
            "Publish only after the expert signs off on the dry-run result.",
        ]
        if status == "ready_for_review"
        else [
            "Fix failing structure or scenario gates before asking the expert to review the package.",
        ]
    )
    return {
        "skill_name": skill_slug,
        "status": status,
        "publish_gate_count": len(gates),
        "blocking_count": blocking_count,
        "gates": gates,
        "next_actions": next_actions,
    }


def _render_validation_markdown(payload: dict) -> str:
    passed = [key for key, result in payload["checks"].items() if result == "passed"]
    failed = payload["errors"]
    warnings = payload["warnings"]
    passed_lines = [f"- {item}" for item in passed] or ["- None"]
    error_lines = [f"- {item}" for item in failed] or ["- None"]
    warning_lines = [f"- {item}" for item in warnings] or ["- None"]
    return "\n".join(
        [
            f"# {payload['report_title']}",
            "",
            f"- status: `{payload['status']}`",
            f"- error_count: `{payload['error_count']}`",
            f"- warning_count: `{payload['warning_count']}`",
            "",
            "## Passed Checks",
            *passed_lines,
            "",
            "## Errors",
            *error_lines,
            "",
            "## Warnings",
            *warning_lines,
            "",
        ],
    )


def _render_validation_html(payload: dict) -> str:
    passed = "".join(f"<li>{escape(item)}</li>" for item in payload["passed_checks"]) or "<li>None</li>"
    errors = "".join(f"<li>{escape(item)}</li>" for item in payload["errors"]) or "<li>None</li>"
    warnings = "".join(f"<li>{escape(item)}</li>" for item in payload["warnings"]) or "<li>None</li>"
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{escape(payload["report_title"])}</title>
    <style>
      body {{
        margin: 0;
        padding: 32px;
        font-family: "Segoe UI", sans-serif;
        background: #f8f8f7;
        color: #18181b;
      }}
      main {{
        max-width: 960px;
        margin: 0 auto;
      }}
      .panel {{
        background: #ffffff;
        border: 1px solid #e4e4e7;
        border-radius: 18px;
        padding: 20px 24px;
        margin-bottom: 18px;
      }}
      h1, h2 {{
        margin-top: 0;
      }}
      ul {{
        margin: 0;
        padding-left: 18px;
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="panel">
        <h1>{escape(payload["report_title"])}</h1>
        <p>status: <strong>{escape(payload["status"])}</strong></p>
        <p>error_count: <strong>{payload["error_count"]}</strong></p>
        <p>warning_count: <strong>{payload["warning_count"]}</strong></p>
      </section>
      <section class="panel">
        <h2>Passed Checks</h2>
        <ul>{passed}</ul>
      </section>
      <section class="panel">
        <h2>Errors</h2>
        <ul>{errors}</ul>
      </section>
      <section class="panel">
        <h2>Warnings</h2>
        <ul>{warnings}</ul>
      </section>
    </main>
  </body>
</html>
"""


def _render_test_matrix_markdown(payload: dict) -> str:
    lines = [
        f"# {payload['skill_name']} test matrix",
        "",
        f"- status: `{payload['status']}`",
        f"- scenario_test_count: `{payload['scenario_test_count']}`",
        "",
        "## Scenario Tests",
    ]
    if not payload["scenario_tests"]:
        lines.append("- None")
    for item in payload["scenario_tests"]:
        lines.extend(
            [
                f"- `{item['id']}` {item['scenario']}",
                f"  - status: `{item['status']}`",
                f"  - expected_outcome: {item['expected_outcome']}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _render_publish_readiness_markdown(payload: dict) -> str:
    lines = [
        f"# {payload['skill_name']} publish readiness",
        "",
        f"- status: `{payload['status']}`",
        f"- publish_gate_count: `{payload['publish_gate_count']}`",
        f"- blocking_count: `{payload['blocking_count']}`",
        "",
        "## Gates",
    ]
    for gate in payload["gates"]:
        lines.append(f"- `{gate['status']}` {gate['label']}")
    lines.extend(["", "## Next Actions"])
    for item in payload["next_actions"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def run_skill_studio(
    *,
    outputs_dir: Path,
    skill_name: str,
    skill_purpose: str,
    trigger_conditions: list[str] | None,
    workflow_steps: list[str] | None,
    expert_rules: list[str] | None,
    acceptance_criteria: list[str] | None,
    test_scenarios: list[str] | None,
) -> tuple[dict, list[str]]:
    cleaned_triggers = [item.strip() for item in trigger_conditions or [] if item and item.strip()]
    cleaned_workflow = [item.strip() for item in workflow_steps or [] if item and item.strip()]
    cleaned_rules = [item.strip() for item in expert_rules or [] if item and item.strip()]
    cleaned_acceptance = [item.strip() for item in acceptance_criteria or [] if item and item.strip()]
    cleaned_scenarios = [item.strip() for item in test_scenarios or [] if item and item.strip()]

    if not skill_name.strip():
        raise ValueError("skill_name is required")
    if not skill_purpose.strip():
        raise ValueError("skill_purpose is required")

    skill_title = skill_name.strip()
    skill_slug = _slugify_skill_name(skill_title)
    description = _build_description(
        skill_purpose=skill_purpose.strip(),
        trigger_conditions=cleaned_triggers,
    )
    skill_markdown = _build_skill_markdown(
        skill_name=skill_slug,
        description=description,
        skill_purpose=skill_purpose.strip(),
        trigger_conditions=cleaned_triggers,
        workflow_steps=cleaned_workflow,
        acceptance_criteria=cleaned_acceptance,
        test_scenarios=cleaned_scenarios,
    )
    validation = _validate_skill(
        skill_name=skill_slug,
        description=description,
        skill_markdown=skill_markdown,
        trigger_conditions=cleaned_triggers,
        workflow_steps=cleaned_workflow,
        acceptance_criteria=cleaned_acceptance,
        test_scenarios=cleaned_scenarios,
    )

    draft_dir = outputs_dir / "submarine" / "skill-studio" / skill_slug
    references_dir = draft_dir / "references"
    agents_dir = draft_dir / "agents"
    references_dir.mkdir(parents=True, exist_ok=True)
    agents_dir.mkdir(parents=True, exist_ok=True)
    archive_filename = f"{skill_slug}.skill"
    archive_virtual_path = _artifact_virtual_path(skill_slug, archive_filename)

    artifact_virtual_paths = [
        _artifact_virtual_path(skill_slug, "skill-draft.json"),
        _artifact_virtual_path(skill_slug, "skill-package.json"),
        _artifact_virtual_path(skill_slug, "SKILL.md"),
        _artifact_virtual_path(skill_slug, "agents/openai.yaml"),
        _artifact_virtual_path(skill_slug, "references/domain-rules.md"),
        _artifact_virtual_path(skill_slug, "test-matrix.json"),
        _artifact_virtual_path(skill_slug, "test-matrix.md"),
        _artifact_virtual_path(skill_slug, "validation-report.json"),
        _artifact_virtual_path(skill_slug, "validation-report.md"),
        _artifact_virtual_path(skill_slug, "validation-report.html"),
        _artifact_virtual_path(skill_slug, "publish-readiness.json"),
        _artifact_virtual_path(skill_slug, "publish-readiness.md"),
        archive_virtual_path,
    ]

    payload = {
        "skill_name": skill_slug,
        "skill_title": skill_title,
        "skill_purpose": skill_purpose.strip(),
        "description": description,
        "assistant_mode": ASSISTANT_MODE,
        "assistant_label": ASSISTANT_LABEL,
        "workspace_mode": "expert_skill_studio",
        "builtin_skills": BUILTIN_SKILLS,
        "trigger_conditions": cleaned_triggers,
        "workflow_steps": cleaned_workflow,
        "expert_rules": cleaned_rules,
        "acceptance_criteria": cleaned_acceptance,
        "test_scenarios": cleaned_scenarios,
        "artifact_virtual_paths": artifact_virtual_paths,
        "report_virtual_path": _artifact_virtual_path(skill_slug, "validation-report.md"),
        "ui_metadata_virtual_path": _artifact_virtual_path(skill_slug, "agents/openai.yaml"),
        "package_virtual_path": _artifact_virtual_path(skill_slug, "skill-package.json"),
        "package_archive_virtual_path": archive_virtual_path,
        "test_virtual_path": _artifact_virtual_path(skill_slug, "test-matrix.json"),
        "publish_virtual_path": _artifact_virtual_path(skill_slug, "publish-readiness.json"),
    }

    validation_payload = {
        "report_title": f"{skill_slug} validation report",
        **validation,
        "passed_checks": [key for key, result in validation["checks"].items() if result == "passed"],
        "skill_name": skill_slug,
        "report_virtual_path": payload["report_virtual_path"],
        "artifact_virtual_paths": artifact_virtual_paths,
    }
    test_matrix = _build_test_matrix(
        skill_slug=skill_slug,
        test_scenarios=cleaned_scenarios,
        validation=validation,
    )
    publish_readiness = _build_publish_readiness(
        skill_slug=skill_slug,
        validation=validation,
        test_matrix=test_matrix,
        ui_metadata_virtual_path=payload["ui_metadata_virtual_path"],
    )

    package_payload = {
        "skill_name": skill_slug,
        "skill_title": skill_title,
        "assistant_mode": ASSISTANT_MODE,
        "assistant_label": ASSISTANT_LABEL,
        "workspace_mode": payload["workspace_mode"],
        "builtin_skills": BUILTIN_SKILLS,
        "validation_status": validation_payload["status"],
        "test_status": test_matrix["status"],
        "publish_status": publish_readiness["status"],
        "package_virtual_path": payload["package_virtual_path"],
        "package_archive_virtual_path": archive_virtual_path,
        "archive_virtual_path": archive_virtual_path,
        "ui_metadata_virtual_path": payload["ui_metadata_virtual_path"],
        "artifact_virtual_paths": artifact_virtual_paths,
    }

    payload["validation_status"] = validation_payload["status"]
    payload["test_status"] = test_matrix["status"]
    payload["publish_status"] = publish_readiness["status"]
    payload["error_count"] = validation_payload["error_count"]
    payload["warning_count"] = validation_payload["warning_count"]

    (draft_dir / "skill-draft.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (draft_dir / "skill-package.json").write_text(
        json.dumps(package_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (draft_dir / "SKILL.md").write_text(skill_markdown, encoding="utf-8")
    (agents_dir / "openai.yaml").write_text(
        _build_openai_yaml(
            skill_title=skill_title,
            description=description,
            skill_slug=skill_slug,
        ),
        encoding="utf-8",
    )
    (references_dir / "domain-rules.md").write_text(
        _build_rules_markdown(
            expert_rules=cleaned_rules,
            acceptance_criteria=cleaned_acceptance,
            test_scenarios=cleaned_scenarios,
        ),
        encoding="utf-8",
    )
    (draft_dir / "test-matrix.json").write_text(
        json.dumps(test_matrix, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (draft_dir / "test-matrix.md").write_text(
        _render_test_matrix_markdown(test_matrix),
        encoding="utf-8",
    )
    (draft_dir / "validation-report.json").write_text(
        json.dumps(validation_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (draft_dir / "validation-report.md").write_text(
        _render_validation_markdown(validation_payload),
        encoding="utf-8",
    )
    (draft_dir / "validation-report.html").write_text(
        _render_validation_html(validation_payload),
        encoding="utf-8",
    )
    (draft_dir / "publish-readiness.json").write_text(
        json.dumps(publish_readiness, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (draft_dir / "publish-readiness.md").write_text(
        _render_publish_readiness_markdown(publish_readiness),
        encoding="utf-8",
    )
    _build_skill_archive(
        draft_dir=draft_dir,
        archive_path=draft_dir / archive_filename,
        skill_slug=skill_slug,
    )

    return payload, artifact_virtual_paths
