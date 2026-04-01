# Submarine Requested Outputs Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make vibe CFD runs follow user-requested deliverables rather than a fixed result bundle, while staying inside the current DeerFlow submarine runtime.

**Architecture:** Introduce a small output-contract layer that normalizes free-form `expected_outputs` into structured `requested_outputs`, propagates it through design brief, solver dispatch, and final report, and lets the workbench display requested outputs with delivery status. Keep v1 bounded: only mark currently supported outputs as deliverable and explicitly surface unsupported requests instead of silently dropping them.

**Tech Stack:** Python, Pydantic-style runtime payloads, existing DeerFlow submarine domain modules, TypeScript workbench utilities, Node test runner, pytest.

---

### Task 1: Output Contract Backbone

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/output_contract.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- Test: `backend/tests/test_submarine_design_brief_tool.py`

- [ ] **Step 1: Write the failing test**

Add a design-brief test that passes mixed natural-language outputs such as `闃诲姏绯绘暟 Cd`, `琛ㄩ潰鍘嬪姏浜戝浘`, `娴佺嚎鍥綻, and `涓枃缁撴灉鎶ュ憡`, then asserts the payload includes normalized `requested_outputs` with stable IDs and support flags.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_design_brief_tool.py -q -k requested_outputs`
Expected: FAIL because `requested_outputs` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create a catalog-driven resolver that maps aliases to canonical output IDs and returns structured `requested_outputs` entries with:
- `output_id`
- `label`
- `requested_label`
- `status`
- `support_level`
- `notes`

Update runtime contracts to carry `requested_outputs`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_design_brief_tool.py -q -k requested_outputs`
Expected: PASS

### Task 2: Design Brief and Solver Dispatch Propagation

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/design_brief.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`
- Test: `backend/tests/test_submarine_solver_dispatch_tool.py`

- [ ] **Step 1: Write the failing test**

Add a solver-dispatch test that starts from a runtime carrying `requested_outputs` and asserts `openfoam-request.json` and runtime state preserve them and include a structured output-delivery plan.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k requested_outputs`
Expected: FAIL because dispatch payload does not preserve requested outputs yet.

- [ ] **Step 3: Write minimal implementation**

Thread `requested_outputs` through:
- design-brief payload
- runtime snapshot
- solver-dispatch payload

Add a minimal `output_delivery_plan` that marks currently supported outputs as planned and unsupported outputs as explicit follow-up items.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k requested_outputs`
Expected: PASS

### Task 3: Result Report Delivery Status

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`
- Test: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing test**

Add a result-report test that asserts `final-report.json` includes `requested_outputs` and a delivery-status list showing which requested outputs were delivered, pending, or unsupported.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k requested_outputs`
Expected: FAIL because final report does not expose requested output delivery yet.

- [ ] **Step 3: Write minimal implementation**

Build report-layer delivery status from:
- design brief / runtime `requested_outputs`
- solver metrics availability
- benchmark availability
- generated report artifacts

Persist the result into `final-report.json`, markdown, and HTML.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k requested_outputs`
Expected: PASS

### Task 4: Workbench Output-Focused Display

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- Test: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`

- [ ] **Step 1: Write the failing test**

Add a utility test that passes `requested_outputs` plus delivery-status payload and asserts the workbench summary exposes an output-focused view.

- [ ] **Step 2: Run test to verify it fails**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: FAIL because the utility layer does not expose requested output delivery yet.

- [ ] **Step 3: Write minimal implementation**

Teach the workbench to:
- show requested outputs in the brief area
- show delivery status in a dedicated output/deliverables section
- clearly mark unsupported requests as such

- [ ] **Step 4: Run test to verify it passes**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

### Task 5: Verification and Documentation

**Files:**
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-research-readiness.md`

- [ ] **Step 1: Run focused backend verification**

Run: `uv run pytest tests/test_submarine_design_brief_tool.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py -q`
Expected: PASS

- [ ] **Step 2: Run submarine-domain regression**

Run: `uv run pytest tests -q -k submarine`
Expected: PASS

- [ ] **Step 3: Run frontend verification**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 4: Run type check**

Run: `node_modules/.bin/tsc.cmd --noEmit`
Expected: PASS

- [ ] **Step 5: Update status document**

Record:
- the new output-contract capability
- current supported outputs vs unsupported requested outputs
- remaining gap to user-driven pressure/wake/streamline artifact generation
