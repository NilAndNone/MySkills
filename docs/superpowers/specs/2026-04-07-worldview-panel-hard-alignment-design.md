# Worldview Panel Hard Alignment Design

Date: 2026-04-07
Status: Ready for review
Scope: aggressive workspace-owned alignment to `docs/worldview_panel_product_reframe_v2.md`

## TL;DR

This spec defines a hard-alignment delivery path for the worldview panel product refactor.

The governing rule is simple:

- if a workspace-owned path, artifact, state model, verification rule, or default viewer behavior conflicts with the product reframe, it should be removed from the workspace mainline rather than preserved for compatibility

This work stays within the repository runtime-routing rules:

- `scripts/run_worldview_panel.py` remains the only supported workspace entrypoint
- `plugins/worldview-panel-codex` remains read-only
- plugin helpers may still be read as runtime dependencies
- plugin-owned product semantics are no longer treated as the supported product path

The work is delivered in four implementation stages with three fixed review checkpoints:

1. stage-one semantic alignment
2. stage-two verification and cleanup alignment
3. stage-three Studio/Audit delivery alignment
4. final acceptance-only cleanup

Fixed reviews happen:

1. after stage one
2. after stage three
3. immediately before final submission

UI work is intentionally delayed until stage three.

## Problem Statement

The current workspace is directionally aligned with the product reframe, but not fully aligned in behavior.

The main gaps are:

- the workspace mainline does not yet model all three result grades honestly
- blocked and degraded behavior is not fully separated in the product path
- verification is still too shallow relative to the claim-traceability requirement
- the default review viewer is still thinner than the documented Studio-first product surface
- old compatibility behaviors still remain visible enough to blur the new product boundary

The risk is not that the repository lacks a new direction.

The risk is that the repository ends up with:

- a correct product document
- a mostly-correct workspace path
- and enough leftover compatibility behavior to keep the old model effectively alive

This spec exists to prevent that outcome.

## Alignment Goal

The alignment target is not “mostly follows the document.”

The alignment target is:

- the supported workspace path behaves like the product reframe says it should behave
- unsupported legacy behavior no longer defines success in the workspace mainline
- default user consumption follows Studio-first product semantics
- Audit remains the evidence and review surface
- blocked, degraded, and usable are all real product states instead of partial labels

## Non-Negotiable Rules

### Workspace Mainline Is The Only Supported Product Path

The only supported workspace product path is:

- `scripts/run_worldview_panel.py`
- `worldview_runtime_adapter/*`

Nothing else counts as the workspace product mainline.

### Plugin Stays Read-Only

This repository already defines the plugin as read-only. This spec follows that rule.

Hard alignment does **not** mean editing plugin code.

It means:

- the workspace path stops depending on plugin-owned product semantics
- the workspace path stops treating plugin-owned product outputs as the supported product definition
- the plugin remains only a runtime-kernel and helper dependency

### Aggressive Removal Over Compatibility

If a workspace-owned behavior conflicts with the product reframe, it should be removed from the supported mainline rather than preserved behind compatibility logic.

This applies to:

- legacy entry assumptions
- legacy artifact expectations
- legacy result semantics
- legacy viewer defaults
- legacy verification rules
- legacy naming that keeps the old model conceptually alive

### UI Comes Last

UI work is intentionally deferred until the product semantics, verification contract, and cleanup boundaries are already correct.

The repository should not polish a screen that still sits on unstable semantics.

### Fixed Review Schedule

This work uses exactly three fixed reviews:

1. after stage one semantic alignment
2. after stage three product delivery alignment
3. immediately before final submission

No standing “review at any time” side process is part of this design.

Review is a fixed checkpoint activity, not a permanent parallel workflow.

## Stage Model

### Stage One: Semantic Alignment

Stage one corrects the meaning of the workspace-owned mainline.

It focuses only on product semantics and completion behavior.

Required outcomes:

- the workspace mainline is clearly the only supported product path
- `usable`, `degraded`, and `blocked` are all modeled as real product outcomes
- blocked runs no longer present themselves like ordinary successful outputs
- presentation surface, execution policy, and result grade remain independent
- old product artifacts no longer define completion for the workspace mainline

Stage one does **not** try to finish viewer UX.

The goal is to make the mainline semantically correct before polishing consumption.

#### Stage-One Acceptance Criteria

Stage one is complete only when all of the following are true:

- a healthy run lands in `usable`
- a partially failed but still honest run lands in `degraded`
- an insufficient run lands in `blocked`
- each of those outcomes produces product artifacts and status language consistent with the product reframe
- blocked output is visibly and structurally distinct from a normal successful result

#### Fixed Review 1

Review question:

`Is the supported workspace mainline now semantically consistent with the product reframe?`

### Stage Two: Verification And Cleanup Alignment

Stage two tightens the repository so that the workspace mainline cannot drift back into the old model unnoticed.

It focuses on verification depth and removal of conflicting workspace-owned leftovers.

Required outcomes:

- verification checks more than file presence
- claim-linked evidence references are validated
- result-grade consistency is validated
- blocked runs fail clearly when they pretend to be successful
- workspace-owned compatibility leftovers that conflict with the new model are removed

This stage is about making “passing verification” and “being aligned” much closer to the same thing.

#### Stage-Two Acceptance Criteria

Stage two is complete only when all of the following are true:

- missing or broken claim trace references are caught
- mismatched run status and result grade are caught
- blocked runs without the required failure explanation are caught
- workspace-owned tests protect the new artifact contract instead of preserving old assumptions
- unsupported legacy compatibility no longer shapes the mainline

### Stage Three: Product Delivery Alignment

Stage three is the first UI-facing stage.

Only after the semantics and verification contract are stable does the repository finish the default delivery surface.

Required outcomes:

- Studio is the default consumption surface
- Audit is the secondary review and evidence surface
- the default experience is product-first, not persona-debug-first
- the visible structure follows the product reframe
- degraded and blocked states are understandable in product language

Stage three is where the repository finally makes the delivered result look like the documented product.

#### Stage-Three Acceptance Criteria

Stage three is complete only when all of the following are true:

- the default viewer opens Studio first
- Studio prioritizes judgment, tension, and creation value over runtime noise
- Audit remains available for review, failures, and evidence
- persona-level details are subordinate drill-down material rather than the homepage structure
- the visible experience distinguishes `usable`, `degraded`, and `blocked`

#### Fixed Review 2

Review question:

`Does the default delivered result now look and behave like the product described by the document?`

### Final Acceptance-Only Stage

The final stage does not add new direction.

It only performs:

- final verification
- edge cleanup
- residual inconsistency removal
- acceptance review before submission

No new scope should be introduced here.

#### Final Acceptance Criteria

The final stage is complete only when all of the following are true:

- all intended tests and validations pass
- the workspace mainline does not expose conflicting legacy behavior as supported behavior
- the three result grades remain consistent end to end
- Studio and Audit remain clearly separated
- no remaining workspace-owned path undermines the documented product model

#### Fixed Review 3

Review question:

`Is there any remaining workspace-owned inconsistency that could pull the repository back toward the old model after this lands?`

## Removal And Retention Boundaries

### Must Be Removed From The Supported Workspace Mainline

The following categories must be removed from the workspace-owned supported path if they conflict with the product reframe:

- legacy compatibility entry behavior
- legacy completion rules based on old product artifacts
- viewer defaults that preserve persona-debug-first consumption
- product-path logic that collapses `usable` and `degraded`
- naming or behavior that ties presentation surfaces to runtime modes
- workspace-owned bridges that keep old product semantics alive as if they were still supported

The standard is not “delete every old file in the repository.”

The standard is:

- do not let conflicting legacy behavior remain part of the supported workspace product story

### Must Be Retained

The following should remain:

- `scripts/run_worldview_panel.py` as the supported workspace entrypoint
- adapter-owned intake, planning, composition, verification, and delivery
- plugin-owned runtime helpers, schemas, and artifact-reading dependencies
- runtime evidence, per-role results, and failure records
- deterministic fixtures and tests that help verify the workspace path

### Plugin Treatment

The plugin is not modified as part of this spec.

Instead:

- the plugin remains read-only
- the workspace stops treating plugin-owned product logic as the supported product path
- the workspace no longer uses plugin-owned product semantics to define completion

This is a boundary clarification, not a plugin rewrite.

## Data-Flow Target

When hard alignment is complete, the supported workspace flow should read conceptually as:

1. product input is normalized into a content task
2. the minimum sufficient role set is chosen
3. runtime execution is performed
4. a canonical content object is produced
5. Studio and Audit surfaces are derived from that content object
6. verification judges the run against the adapter-owned product contract

This means:

- the canonical content object is the source of truth
- Studio and Audit are consumers, not competing truth sources
- result grade is determined before the final consumption surfaces are trusted

## Review Policy

This design uses fixed review checkpoints rather than open-ended continuous review.

That is the correct fit for this repository because:

- the work is explicitly staged
- the user asked for three fixed reviews
- the repository guidance does not call for concurrent development
- Audit and verification are already the product’s intended review surfaces

Subagent review may still be used later as an execution tactic if needed, but it is **not** part of the product design and is **not** the default control structure for this effort.

## Testing Expectations

The implementation plan derived from this spec must cover tests for:

- all three result grades
- blocked-vs-degraded-vs-usable artifact behavior
- result-grade and run-status consistency
- claim trace reference validation
- Studio-first viewer behavior
- Audit availability as a secondary surface
- removal of conflicting workspace-owned legacy completion assumptions

## Completion Definition

This hard-alignment effort is complete only when all of the following are true:

- the supported workspace path matches the product reframe in semantics
- the workspace mainline no longer relies on conflicting legacy product assumptions
- verification reflects the new artifact contract and traceability expectations
- Studio is the default delivery surface
- Audit remains the evidence and review surface
- UI changes happen only after semantic and verification alignment
- the repository has passed all three fixed review checkpoints

## Out Of Scope

This spec does not do the following:

- rewrite plugin code
- preserve old compatibility for its own sake
- optimize visual polish before semantic correctness
- introduce additional floating review checkpoints beyond the agreed three
- expand the product beyond the documented wedge

## Recommended Next Step

The next step after user approval of this spec is to write a stage-by-stage implementation plan that follows this order:

1. stage one semantic alignment
2. fixed review 1
3. stage two verification and cleanup alignment
4. stage three product delivery alignment
5. fixed review 2
6. final acceptance-only cleanup
7. fixed review 3
