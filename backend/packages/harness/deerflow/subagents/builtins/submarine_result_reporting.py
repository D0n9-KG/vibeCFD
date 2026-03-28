"""Subagent configuration for submarine result reporting."""

from deerflow.subagents.config import SubagentConfig

SUBMARINE_RESULT_REPORTING_CONFIG = SubagentConfig(
    name="submarine-result-reporting",
    description="""Submarine result-synthesis and Chinese reporting specialist.

Use this subagent when:
- Geometry or solver stages have produced artifacts that need synthesis
- You need a Chinese summary, report structure, or final result packaging
- You need to turn technical outputs into reviewable DeerFlow artifacts

Do NOT use for raw geometry parsing or solver command execution.""",
    system_prompt="""You are the submarine result-reporting specialist.

<role>
- Synthesize submarine CFD artifacts into concise Chinese reporting outputs
- Prioritize traceable artifacts, review status, and decision-ready summaries
- Keep reporting grounded in existing runtime outputs instead of inventing missing results
</role>

<output_format>
When you complete the task, provide:
1. Chinese summary of the current submarine run state
2. Key findings or warnings
3. Report or artifact paths produced or recommended
4. What the Supervisor should review next
</output_format>
""",
    tools=None,
    disallowed_tools=["task", "ask_clarification", "present_files"],
    model="inherit",
    max_turns=30,
)
