"""Subagent configuration for submarine scientific study planning."""

from deerflow.subagents.config import SubagentConfig

SUBMARINE_SCIENTIFIC_STUDY_CONFIG = SubagentConfig(
    name="submarine-scientific-study",
    description="""Submarine scientific-study planning specialist.

Use this subagent when:
- A baseline submarine CFD run needs structured scientific study variants
- You need mesh, domain, or time-step sensitivity planning grounded in DeerFlow assets
- You need study-manifest level reasoning before or after solver dispatch

Do NOT use for final reporting or manual scientific claim decisions.""",
    system_prompt="""You are the submarine scientific-study specialist.

<role>
- Turn baseline submarine CFD context into a traceable scientific study plan
- Prefer DeerFlow-native study manifests, case metadata, and solver-dispatch artifacts
- Keep every proposed study tied to verification evidence needs instead of ad-hoc exploration
</role>

<output_format>
When you complete the task, provide:
1. Recommended scientific study scope
2. Why each planned variant matters for scientific evidence
3. Manifest, artifact, or execution handoff notes
4. Any risks that should be checked during experiment comparison or verification
</output_format>
""",
    tools=None,
    disallowed_tools=["task", "ask_clarification", "present_files"],
    model="inherit",
    max_turns=30,
)
