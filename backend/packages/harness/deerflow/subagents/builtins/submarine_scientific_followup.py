"""Subagent configuration for submarine scientific follow-up."""

from deerflow.subagents.config import SubagentConfig

SUBMARINE_SCIENTIFIC_FOLLOWUP_CONFIG = SubagentConfig(
    name="submarine-scientific-followup",
    description="""Submarine scientific-followup specialist.

Use this subagent when:
- Scientific remediation handoff needs to be executed or tracked
- You need to decide whether DeerFlow can auto-follow up with another dispatch or report refresh
- You need follow-up history summarized into a traceable next step

Do NOT use for first-pass task understanding or baseline solver setup.""",
    system_prompt="""You are the submarine scientific-followup specialist.

<role>
- Turn scientific remediation handoffs into a traceable next-step decision
- Prefer DeerFlow-native follow-up history, refreshed reports, and runtime artifacts
- Keep automated follow-up separate from final scientific claim approval
</role>

<output_format>
When you complete the task, provide:
1. Follow-up decision or status
2. Whether the next step is auto-executable or manual
3. Updated history, artifact, or refreshed-report paths
4. What the supervisor should review after follow-up
</output_format>
""",
    tools=None,
    disallowed_tools=["task", "ask_clarification", "present_files"],
    model="inherit",
    max_turns=30,
)
