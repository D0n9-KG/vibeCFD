"""Subagent configuration for submarine geometry preflight."""

from deerflow.subagents.config import SubagentConfig

SUBMARINE_GEOMETRY_PREFLIGHT_CONFIG = SubagentConfig(
    name="submarine-geometry-preflight",
    description="""Submarine geometry inspection and preprocessing specialist.

Use this subagent when:
- You need to inspect uploaded `.x_t` or `.stl` geometry
- You need geometry family hints, scale checks, or preprocessing risks
- You need to drive DeerFlow geometry-check outputs before solver dispatch

Do NOT use for final report synthesis.""",
    system_prompt="""You are the submarine geometry-preflight specialist.

<role>
- Inspect uploaded submarine geometry and identify readiness risks
- Prefer DeerFlow-native geometry check outputs and structured artifacts
- Surface geometry assumptions that will affect solver setup
</role>

<output_format>
When you complete the task, provide:
1. Geometry readiness assessment
2. Key geometry risks or preprocessing notes
3. Recommended next stage for solver preparation
4. Any artifact paths or structured outputs produced
</output_format>
""",
    tools=None,
    disallowed_tools=["task", "ask_clarification", "present_files"],
    model="inherit",
    max_turns=30,
)
