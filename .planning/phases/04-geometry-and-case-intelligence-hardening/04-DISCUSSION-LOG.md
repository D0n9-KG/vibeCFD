# Phase 4: Geometry and Case Intelligence Hardening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 04-geometry-and-case-intelligence-hardening
**Mode:** discuss
**Areas discussed:** uncertainty ownership, referenced case presentation, weak-reference handling, draft review flow, approval model, taxonomy simplification

---

## Uncertainty Ownership

| Option | Description | Selected |
|--------|-------------|----------|
| AI autonomous decision-making | Let the AI resolve ambiguous geometry and case assumptions on its own | |
| Researcher-approved decisions | AI identifies uncertainty and suggests values, but the researcher makes final decisions | ✓ |
| Fixed mandatory confirmation checklist | Always require the same set of confirmations before solving | |

**User's choice:** AI should detect uncertainty and provide references or ranges, but the researcher makes the final decision.
**Notes:** If the researcher already supplied the needed information in the initial prompt, no extra confirmation is necessary. The agent should decide dynamically when clarification is needed.

---

## Referenced Case Presentation

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-fill only | Use the case and value directly in the plan without extra context | |
| Show source, confidence, and applicability | Display the suggested value or range together with evidence and conditions | ✓ |
| Force per-item confirmation even with good references | Always interrupt the researcher for each referenced value | |

**User's choice:** When a case has real reference support, the draft should show the source, confidence, and applicability conditions alongside the suggested value or range.
**Notes:** These items can usually remain in the consolidated draft for final review.

---

## Weak-Reference Suggestions

| Option | Description | Selected |
|--------|-------------|----------|
| Hide weak-reference cases | Exclude them from recommendations entirely | |
| Show as disclosed suggestions | Keep them visible when useful, but explain the missing evidence clearly | ✓ |
| Treat them like normal recommendations | Rank and present them without special disclosure | |

**User's choice:** Weak-reference or placeholder-backed cases may still appear, but only with clear disclosure of their limits.
**Notes:** The user explicitly rejected adding a large new trust-status ladder for these cases.

---

## Draft Review Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Interrupt on every key uncertainty | Ask as soon as each uncertainty appears | |
| Draft first, interrupt only for severe issues | Build a draft and only stop early when the risk is serious | ✓ |
| Final review only | Never interrupt before final approval | |

**User's choice:** The normal path should be a consolidated calculation-plan draft, with early interruptions reserved for severe uncertainties.
**Notes:** This keeps the workflow efficient while still protecting high-risk assumptions.

---

## Approval Model

| Option | Description | Selected |
|--------|-------------|----------|
| Overall approval only | Review the whole plan and approve or reject it as one bundle | |
| Per-item review plus final approval | Review and edit key items, then give overall approval | ✓ |
| Final approval without item states | Show details, but only track one global approval action | |

**User's choice:** The researcher should be able to review or edit key items and then give a final approval.
**Notes:** The researcher must be able to approve directly, modify then approve, or send the draft back for revision.

---

## Taxonomy Simplification

| Option | Description | Selected |
|--------|-------------|----------|
| Add multiple new trust tiers | Introduce a formal ladder such as research-backed vs engineering-only vs more sub-levels | |
| Keep the approval state simple | Track pending researcher confirmation vs researcher confirmed, with clear disclosure text | ✓ |
| Collapse everything into one final button | Avoid item-level tracking and rely only on final submission | |

**User's choice:** Keep the system simple and avoid introducing many new status levels.
**Notes:** The final record should show what was uncertain, what the AI suggested, and what the researcher accepted or modified, without creating a confusing parallel taxonomy. The existing scientific claim levels should stay, but only for post-compute evidence/report gating rather than pre-compute plan approval.

---

## Plan Approval vs Claim Level

| Option | Description | Selected |
|--------|-------------|----------|
| Couple them tightly | Treat researcher confirmation as direct evidence for a higher claim level | |
| Keep them separate | Researcher confirmation approves execution, while claim level is still decided by post-compute evidence | ✓ |

**User's choice:** Keep researcher plan approval separate from scientific claim-level evaluation.
**Notes:** A confirmed plan means the run may proceed, but the resulting claim level must still depend on stability, benchmark, verification, and reporting evidence after the computation finishes.
