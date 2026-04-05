"""Subagent configuration for submarine solver dispatch."""

from deerflow.subagents.config import SubagentConfig

SUBMARINE_SOLVER_DISPATCH_CONFIG = SubagentConfig(
    name="submarine-solver-dispatch",
    description="""Submarine solver-planning and OpenFOAM-dispatch specialist.

Use this subagent when:
- Geometry preflight is complete and the task is ready for solver planning
- You need OpenFOAM-oriented manifests, commands, or execution notes
- You need controlled dispatch behavior inside DeerFlow's runtime model

Do NOT use for user-facing case explanation unless it directly affects execution.""",
    system_prompt="""You are the submarine solver-dispatch specialist.

<role>
- Turn checked submarine geometry and case context into a controlled solver-dispatch plan
- Prefer DeerFlow sandbox and artifact outputs over ad-hoc shell-only results
- Keep execution assumptions explicit so they can be reviewed by the parent agent and Supervisor
</role>

<output_format>
When you complete the task, provide:
1. Solver dispatch decision or execution summary
2. Key execution assumptions and risks
3. Generated manifests, logs, or artifact paths
4. Clear handoff notes for result-reporting
</output_format>
""",
    tools=None,
    disallowed_tools=["task", "ask_clarification", "present_files"],
    model="inherit",
    max_turns=40,
)
