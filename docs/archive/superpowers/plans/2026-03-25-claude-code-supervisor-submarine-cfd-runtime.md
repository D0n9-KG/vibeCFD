# Claude Code Supervisor Submarine CFD Runtime Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first full DeerFlow-native submarine CFD runtime shape: Claude Code acts as Supervisor, DeerFlow owns the runtime, specialized submarine subagents are registered, OpenFOAM dispatch enters the DeerFlow execution model, and every run produces traceable artifacts and Chinese reporting outputs.

**Architecture:** Keep Claude Code outside DeerFlow through the existing `claude-to-deerflow` integration surface, and deepen DeerFlow itself into a submarine runtime by adding professional subagents, a structured runtime contract, OpenFOAM dispatch services, and result/report artifacts. Reuse only domain experience from `legacy/current-prototype/`, while keeping all new execution, state, and outputs inside DeerFlow's `thread / upload / artifact / sandbox / memory / MCP` model.

**Tech Stack:** DeerFlow LangGraph runtime, FastAPI Gateway, DeerFlow built-in tools and subagents, Python 3.12, Pydantic models, existing sandbox layer, OpenFOAM shell integration, Markdown/HTML/JSON artifacts, backend pytest + ruff.

---

## File Map

- Create: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
  Structured request/response objects for Supervisor-facing submarine runs.
- Create: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
  OpenFOAM dispatch planning, command manifest writing, and artifact generation.
- Create: `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`
  DeerFlow tool for launching controlled solver dispatch from a thread context.
- Create: `backend/packages/harness/deerflow/subagents/builtins/submarine_task_intelligence.py`
  Specialized subagent config for case matching and task understanding.
- Create: `backend/packages/harness/deerflow/subagents/builtins/submarine_geometry_preflight.py`
  Specialized subagent config for geometry check and preprocessing.
- Create: `backend/packages/harness/deerflow/subagents/builtins/submarine_solver_dispatch.py`
  Specialized subagent config for solver planning and execution.
- Create: `backend/packages/harness/deerflow/subagents/builtins/submarine_result_reporting.py`
  Specialized subagent config for result synthesis and Chinese reporting.
- Create: `backend/tests/test_submarine_subagents.py`
  Registry, prompt, and task-tool coverage for new specialized subagents.
- Create: `backend/tests/test_submarine_solver_dispatch_tool.py`
  OpenFOAM dispatch contract and artifact loop coverage.
- Modify: `backend/packages/harness/deerflow/subagents/builtins/__init__.py`
  Register the specialized submarine subagents.
- Modify: `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
  Make DeerFlow's orchestrator prompt aware of the submarine subagent roster and role boundaries.
- Modify: `backend/packages/harness/deerflow/tools/builtins/__init__.py`
  Export the new solver dispatch tool.
- Modify: `backend/packages/harness/deerflow/tools/tools.py`
  Add the solver dispatch tool to DeerFlow built-ins.
- Modify: `backend/packages/harness/deerflow/tools/builtins/task_tool.py`
  Expand accepted `subagent_type` values and descriptions.
- Modify: `skills/public/submarine-orchestrator/SKILL.md`
  Make the runtime workflow explicitly call the specialized subagents.
- Modify: `skills/public/submarine-report/SKILL.md`
  Align reporting behavior with Supervisor review and final artifact contracts.
- Modify: `README.md`
  Document the Supervisor/runtime split and current implementation scope.
- Modify: `backend/CLAUDE.md`
  Document the specialized subagent layer and OpenFOAM DeerFlow integration path.
- Modify: `domain/submarine/README.md`
  Document how domain assets feed the runtime contract, subagents, and solver dispatch.

## Chunk 1: Supervisor And Runtime Contract

### Task 1: Define the structured submarine runtime contract

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/__init__.py`
- Test: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

```python
def test_submarine_runtime_contract_has_supervisor_fields():
    contract = SubmarineRuntimeRequest(
        task_summary="评估阻力",
        confirmation_status="confirmed",
        uploaded_geometry_path="/mnt/user-data/uploads/submarine.stl",
    )
    assert contract.confirmation_status == "confirmed"
    assert contract.uploaded_geometry_path.endswith(".stl")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_domain_assets.py::test_submarine_runtime_contract_has_supervisor_fields' -v`
Expected: FAIL because the runtime contract models do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
class SubmarineRuntimeRequest(BaseModel):
    task_summary: str
    confirmation_status: Literal["draft", "confirmed"]
    uploaded_geometry_path: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_domain_assets.py::test_submarine_runtime_contract_has_supervisor_fields' -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/contracts.py backend/packages/harness/deerflow/domain/submarine/__init__.py backend/tests/test_submarine_domain_assets.py
git commit -m "feat: add submarine runtime contract models"
```

### Task 2: Add runtime contract output fields for Supervisor review

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
- Test: `backend/tests/test_submarine_geometry_check_tool.py`

- [ ] **Step 1: Write the failing test**

```python
def test_geometry_check_result_contains_supervisor_review_fields():
    result = run_geometry_check(...)
    assert result.summary_zh
    assert result.next_recommended_stage == "geometry-preflight"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_geometry_check_tool.py::test_geometry_check_result_contains_supervisor_review_fields' -v`
Expected: FAIL because the structured review fields are not emitted yet.

- [ ] **Step 3: Write minimal implementation**

```python
payload["next_recommended_stage"] = "geometry-preflight"
payload["review_status"] = "ready_for_supervisor"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_geometry_check_tool.py::test_geometry_check_result_contains_supervisor_review_fields' -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/contracts.py backend/packages/harness/deerflow/domain/submarine/geometry_check.py backend/tests/test_submarine_geometry_check_tool.py
git commit -m "feat: expose supervisor review fields in geometry results"
```

## Chunk 2: Specialized Subagents

### Task 3: Register submarine-specific DeerFlow subagents

**Files:**
- Create: `backend/packages/harness/deerflow/subagents/builtins/submarine_task_intelligence.py`
- Create: `backend/packages/harness/deerflow/subagents/builtins/submarine_geometry_preflight.py`
- Create: `backend/packages/harness/deerflow/subagents/builtins/submarine_solver_dispatch.py`
- Create: `backend/packages/harness/deerflow/subagents/builtins/submarine_result_reporting.py`
- Modify: `backend/packages/harness/deerflow/subagents/builtins/__init__.py`
- Test: `backend/tests/test_submarine_subagents.py`

- [ ] **Step 1: Write the failing test**

```python
def test_submarine_subagents_are_registered():
    names = set(get_subagent_names())
    assert {
        "submarine-task-intelligence",
        "submarine-geometry-preflight",
        "submarine-solver-dispatch",
        "submarine-result-reporting",
    } <= names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_subagents.py::test_submarine_subagents_are_registered' -v`
Expected: FAIL because only `general-purpose` and `bash` are registered today.

- [ ] **Step 3: Write minimal implementation**

```python
SUBMARINE_TASK_INTELLIGENCE_CONFIG = SubagentConfig(...)
BUILTIN_SUBAGENTS["submarine-task-intelligence"] = SUBMARINE_TASK_INTELLIGENCE_CONFIG
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_subagents.py::test_submarine_subagents_are_registered' -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/subagents/builtins backend/tests/test_submarine_subagents.py
git commit -m "feat: register submarine specialized subagents"
```

### Task 4: Expand task tool and lead prompt to advertise the new subagents

**Files:**
- Modify: `backend/packages/harness/deerflow/tools/builtins/task_tool.py`
- Modify: `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- Test: `backend/tests/test_submarine_subagents.py`
- Test: `backend/tests/test_task_tool_core_logic.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_task_tool_accepts_submarine_subagent_type():
    result = task_tool.func(..., subagent_type="submarine-task-intelligence", ...)
    assert "Task Succeeded" in result

def test_subagent_prompt_mentions_submarine_roles():
    prompt = apply_prompt_template(subagent_enabled=True)
    assert "submarine-task-intelligence" in prompt
```

- [ ] **Step 2: Run test to verify they fail**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_subagents.py' 'backend/tests/test_task_tool_core_logic.py' -v`
Expected: FAIL because `task_tool` only supports `general-purpose` and `bash`, and the prompt still documents only those two.

- [ ] **Step 3: Write minimal implementation**

```python
subagent_type: Literal[
    "general-purpose",
    "bash",
    "submarine-task-intelligence",
    "submarine-geometry-preflight",
    "submarine-solver-dispatch",
    "submarine-result-reporting",
]
```

- [ ] **Step 4: Run test to verify they pass**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_subagents.py' 'backend/tests/test_task_tool_core_logic.py' -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/tools/builtins/task_tool.py backend/packages/harness/deerflow/agents/lead_agent/prompt.py backend/tests/test_submarine_subagents.py backend/tests/test_task_tool_core_logic.py
git commit -m "feat: expose submarine subagents to DeerFlow orchestration"
```

## Chunk 3: OpenFOAM Dispatch Inside DeerFlow

### Task 5: Add a DeerFlow-native solver dispatch service

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- Test: `backend/tests/test_submarine_solver_dispatch_tool.py`
- Reference: `legacy/current-prototype/backend/app/execution/openfoam_engine.py`

- [ ] **Step 1: Write the failing test**

```python
def test_solver_dispatch_writes_openfoam_manifest(tmp_path):
    result = dispatch_openfoam_case(...)
    assert result.manifest_virtual_path.endswith("openfoam-request.json")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_solver_dispatch_tool.py::test_solver_dispatch_writes_openfoam_manifest' -v`
Expected: FAIL because no DeerFlow-native solver dispatch service exists yet.

- [ ] **Step 3: Write minimal implementation**

```python
def dispatch_openfoam_case(...):
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return SolverDispatchResult(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_solver_dispatch_tool.py::test_solver_dispatch_writes_openfoam_manifest' -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py backend/tests/test_submarine_solver_dispatch_tool.py
git commit -m "feat: add DeerFlow-native submarine solver dispatch service"
```

### Task 6: Expose solver dispatch as a built-in DeerFlow tool with artifacts

**Files:**
- Create: `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/__init__.py`
- Modify: `backend/packages/harness/deerflow/tools/tools.py`
- Modify: `skills/public/submarine-orchestrator/SKILL.md`
- Test: `backend/tests/test_submarine_solver_dispatch_tool.py`

- [ ] **Step 1: Write the failing test**

```python
def test_submarine_solver_dispatch_tool_registers_artifacts():
    outcome = submarine_solver_dispatch_tool.func(...)
    assert any(path.endswith("dispatch-summary.md") for path in outcome.update["artifacts"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_solver_dispatch_tool.py::test_submarine_solver_dispatch_tool_registers_artifacts' -v`
Expected: FAIL because the tool is not registered.

- [ ] **Step 3: Write minimal implementation**

```python
@tool("submarine_solver_dispatch", parse_docstring=True)
def submarine_solver_dispatch_tool(...):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_solver_dispatch_tool.py::test_submarine_solver_dispatch_tool_registers_artifacts' -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/tools/builtins backend/packages/harness/deerflow/tools/tools.py skills/public/submarine-orchestrator/SKILL.md backend/tests/test_submarine_solver_dispatch_tool.py
git commit -m "feat: add submarine solver dispatch DeerFlow tool"
```

## Chunk 4: Reporting And Runtime Verification

### Task 7: Extend reporting artifacts for Supervisor-ready review

**Files:**
- Modify: `skills/public/submarine-report/SKILL.md`
- Modify: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
- Test: `backend/tests/test_submarine_solver_dispatch_tool.py`

- [ ] **Step 1: Write the failing test**

```python
def test_solver_dispatch_outputs_chinese_summary_and_report_paths():
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["summary_zh"]
    assert payload["report_virtual_path"].endswith(".md")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_solver_dispatch_tool.py::test_solver_dispatch_outputs_chinese_summary_and_report_paths' -v`
Expected: FAIL because the report-oriented outputs do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
payload["summary_zh"] = "..."
payload["report_virtual_path"] = report_virtual_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_solver_dispatch_tool.py::test_solver_dispatch_outputs_chinese_summary_and_report_paths' -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/public/submarine-report/SKILL.md backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py backend/packages/harness/deerflow/domain/submarine/geometry_check.py backend/tests/test_submarine_solver_dispatch_tool.py
git commit -m "feat: add supervisor-ready submarine reporting artifacts"
```

### Task 8: Run the regression slice and update docs

**Files:**
- Modify: `README.md`
- Modify: `backend/CLAUDE.md`
- Modify: `domain/submarine/README.md`

- [ ] **Step 1: Document the new runtime surface**

```markdown
- Claude Code is Supervisor
- DeerFlow owns runtime state and artifacts
- Specialized submarine subagents and OpenFOAM dispatch are available
```

- [ ] **Step 2: Run targeted regression tests**

Run: `$env:PYTHONPATH='C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend\\packages\\harness;C:\\Users\\D0n9\\Desktop\\颠覆性大赛\\backend'; & 'backend/.venv/Scripts/python.exe' -m pytest 'backend/tests/test_submarine_domain_assets.py' 'backend/tests/test_submarine_skills_presence.py' 'backend/tests/test_submarine_geometry_check_tool.py' 'backend/tests/test_submarine_subagents.py' 'backend/tests/test_submarine_solver_dispatch_tool.py' 'backend/tests/test_task_tool_core_logic.py' 'backend/tests/test_present_file_tool_core_logic.py' 'backend/tests/test_artifacts_router.py' 'backend/tests/test_uploads_middleware_core_logic.py' -v`
Expected: PASS

- [ ] **Step 3: Run lint**

Run: `& 'backend/.venv/Scripts/python.exe' -m ruff check 'backend/packages/harness/deerflow/domain/submarine' 'backend/packages/harness/deerflow/subagents/builtins' 'backend/packages/harness/deerflow/tools/builtins' 'backend/tests/test_submarine_subagents.py' 'backend/tests/test_submarine_solver_dispatch_tool.py'`
Expected: All checks passed.

- [ ] **Step 4: Commit**

```bash
git add README.md backend/CLAUDE.md domain/submarine/README.md
git commit -m "docs: document submarine supervisor runtime architecture"
```
