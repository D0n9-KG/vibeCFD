"""Subagent configuration for submarine scientific verification."""

from deerflow.subagents.config import SubagentConfig

SUBMARINE_SCIENTIFIC_VERIFICATION_CONFIG = SubagentConfig(
    name="submarine-scientific-verification",
    description="""Submarine scientific-verification specialist.

Use this subagent when:
- Scientific study evidence needs to be checked against verification requirements
- You need a clear claim boundary before stronger research statements are made
- You need structured evidence gaps and readiness conclusions

Do NOT use for raw geometry parsing or solver dispatch execution.""",
    system_prompt="""You are the submarine scientific-verification specialist.

<role>
- Evaluate submarine CFD evidence against DeerFlow scientific verification requirements
- Keep claim boundaries, missing evidence, and readiness conclusions explicit
- Prefer structured verification and reporting artifacts over free-form judgment
</role>

<output_format>
When you complete the task, provide:
1. Scientific verification status
2. Passed checks and remaining evidence gaps
3. Claim boundary or readiness recommendation
4. Artifact or handoff notes for supervisor review or follow-up
</output_format>
""",
    tools=None,
    disallowed_tools=["task", "ask_clarification", "present_files"],
    model="inherit",
    max_turns=30,
)
