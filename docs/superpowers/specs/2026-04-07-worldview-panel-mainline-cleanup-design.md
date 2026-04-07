# Worldview Panel Mainline Cleanup Design

Date: 2026-04-07
Status: Ready for review
Scope: remove plugin-owned parallel product behavior while preserving and validating the adapter-owned workspace mainline

## TL;DR

This spec defines a narrow cleanup pass for the worldview panel repository.

The chosen direction is intentionally conservative:

- keep the adapter-owned product mainline
- remove the newly added plugin-owned parallel product path
- keep two plugin changes that are not product-semantic
- prove the workspace mainline still works through tests and an end-to-end run

The supported path after this cleanup remains:

- `scripts/run_worldview_panel.py`
- `scripts/verify_worldview_panel_round.py`
- `worldview_runtime_adapter/*`

The plugin remains a runtime dependency and helper source, not a second product path.

## Problem Statement

The repository already has a directionally correct workspace-owned product path:

- product intake lives in the adapter
- role planning lives in the adapter
- canonical content artifacts live in the adapter
- Studio and Audit surfaces live in the adapter
- workspace verification lives in the adapter

Recent uncommitted plugin changes reintroduced the same product responsibilities inside `plugins/worldview-panel-codex`.

That creates a split-brain repository:

- the workspace mainline says the adapter owns product semantics
- the plugin now also accepts product-shaped input, generates product-shaped artifacts, and verifies product completion

This is not a quality problem. The tests show both paths can run.

It is a boundary problem:

- two places now claim ownership of the product path
- completion means two different things depending on which code is read
- later work will drift toward whichever copy a contributor sees first

This cleanup exists to remove that ambiguity without discarding unrelated plugin fixes.

## Goal

After this cleanup, the repository should have exactly one supported product path.

That means:

- the adapter continues to own product intake, content composition, surfaces, and verification
- the plugin no longer defines or verifies a competing product path
- the supported workspace scripts still work without depending on plugin-owned product semantics
- the plugin may still contain runtime helpers and non-product bug fixes

## Non-Goals

This spec does not attempt to:

- redesign the product model
- add new benchmark fixtures or rubric enforcement in this round
- fully revert every plugin change in the worktree
- rewrite the adapter mainline
- preserve plugin tests that only exist to protect the unsupported parallel product path

## Architecture Decision

### Workspace Mainline Ownership

The only supported workspace product path remains:

- `scripts/run_worldview_panel.py`
- `scripts/verify_worldview_panel_round.py`
- `worldview_runtime_adapter/*`

Everything product-facing flows through those files.

### Plugin Responsibility

The plugin stays limited to runtime-kernel support and helper behavior.

Allowed plugin responsibility after cleanup:

- schemas and runtime-facing helpers
- packet/profile/runtime helper logic already consumed by the adapter
- non-product bug fixes that do not create a second ownership path

Disallowed plugin responsibility after cleanup:

- owning product intake semantics
- owning role-based planning semantics for the supported workspace path
- generating canonical product artifacts as the supported output contract
- defining product completion for the supported workspace path

### Exception For Two Small Plugin Fixes

Two plugin changes are explicitly retained because they do not create product ownership drift:

- `plugins/worldview-panel-codex/tools/worldview_app_server.py`
- `plugins/worldview-panel-codex/tools/build_worldview_round.py`

These are treated as isolated maintenance fixes, not product-path work.

## File Scope

### Files To Preserve

- `docs/worldview_panel_product_reframe_v2.md`
- `worldview_runtime_adapter/cli.py`
- `worldview_runtime_adapter/intake.py`
- `worldview_runtime_adapter/role_planner.py`
- `worldview_runtime_adapter/round_artifacts.py`
- `worldview_runtime_adapter/claim_model.py`
- `worldview_runtime_adapter/composer.py`
- `worldview_runtime_adapter/surfaces.py`
- `worldview_runtime_adapter/panel_runtime.py`
- `worldview_runtime_adapter/review_viewer.py`
- `worldview_runtime_adapter/verifier.py`
- `worldview_runtime_adapter/failure_summary.py`
- `scripts/run_worldview_panel.py`
- `scripts/verify_worldview_panel_round.py`
- `tests/worldview_runtime_adapter/*`
- `plugins/worldview-panel-codex/tools/worldview_app_server.py`
- `plugins/worldview-panel-codex/tools/build_worldview_round.py`

### Files To Revert Or Trim

- revert `plugins/worldview-panel-codex/tools/worldview_round_builder.py`
- revert `plugins/worldview-panel-codex/tools/worldview_synthesis.py`
- trim `plugins/worldview-panel-codex/tools/verify_worldview_round.py` so it no longer requires plugin-owned product artifacts for completion
- remove plugin test additions that protect the unsupported parallel path:
  - `plugins/worldview-panel-codex/tests/test_build_worldview_round.py`
  - `plugins/worldview-panel-codex/tests/test_synthesize_worldview_panel.py`
  - `plugins/worldview-panel-codex/tests/test_verify_worldview_round.py`

## Execution Design

### Step 1: Freeze The Keep List

Before changing anything, lock the file boundary above.

Purpose:

- prevent accidental rollback of adapter-owned product work
- prevent accidental rollback of the two approved plugin maintenance fixes
- make every later change answer one question: does this remove plugin-owned product duplication?

Acceptance check:

- no revert action touches adapter-owned product files
- the two approved plugin maintenance fixes remain present

### Step 2: Remove Plugin Parallel Product Semantics

This is the cleanup core.

Actions:

- remove plugin-side product-brief parsing and role-plan derivation that was added as a supported path
- remove plugin-side canonical content object generation for the supported path
- remove plugin-side Studio and Audit surface generation for the supported path
- remove plugin-side verification rules that require those plugin-owned product artifacts

Implementation rule:

- prefer whole-file reverts where a file is mostly parallel-path logic
- use targeted edits only when a file also contains behavior that should remain

Expected result:

- plugin code no longer looks like a second implementation of the product reframe
- the adapter remains the only place a reader finds the supported mainline contract

Acceptance check:

- plugin tools do not define the supported product artifact contract
- plugin verification does not require `content_brief`, `studio_surface`, or `audit_surface` as plugin completion artifacts
- retained plugin maintenance fixes are still intact

### Step 3: Reconfirm Adapter-Owned Mainline

Once the plugin parallel route is removed, validate the supported mainline directly.

The repository must prove:

- adapter tests still pass
- the supported run script still executes a round
- the supported verify script still validates the round
- Studio-first consumption remains intact

Acceptance check:

- adapter-owned tests pass
- a real run through `scripts/run_worldview_panel.py` succeeds
- a real verification through `scripts/verify_worldview_panel_round.py` succeeds
- output remains adapter-owned rather than plugin-owned

### Step 4: Residual Boundary Scan

After the direct validations pass, scan for leftover repository cues that could reactivate the wrong path.

Look for:

- plugin requirements that still imply ownership of product artifacts
- comments, tests, or checks that still treat the plugin path as co-equal with the adapter path
- stale wording that reintroduces a second completion contract

Acceptance check:

- only one supported product path remains visible in repository behavior
- plugin is clearly subordinate to the adapter-owned mainline for product semantics

## Component And Data-Flow View

### Supported Flow After Cleanup

1. user input enters through `scripts/run_worldview_panel.py`
2. `worldview_runtime_adapter.cli` normalizes product input
3. adapter-owned round artifacts are built
4. plugin helpers support runtime execution where needed
5. adapter-owned runtime builds `content_brief`, `studio_surface`, and `audit_surface`
6. adapter-owned verifier validates round completion

### Explicitly Unsupported Flow After Cleanup

1. plugin accepts product-shaped input as a supported entry
2. plugin builds product artifacts as the supported contract
3. plugin verification requires those plugin-owned product artifacts for completion

That unsupported flow is what this cleanup removes.

## Error Handling And Decision Rules

### If Plugin Tests Fail After Cleanup

Decision rule:

- if a plugin test only protects the removed parallel product path, delete or revert that expectation
- if a plugin test reveals a real runtime-helper regression unrelated to product ownership, fix only that helper behavior

### If Adapter Tests Fail After Cleanup

Decision rule:

- treat adapter test failures as potential regressions in the supported path
- patch the adapter only if the cleanup exposed a real dependency on plugin-owned product semantics
- do not restore plugin product behavior just to make the adapter pass indirectly

### If End-To-End Validation Fails

Decision rule:

- debug the supported scripts and adapter path first
- only inspect plugin code to restore helper behavior, never to restore product ownership

## Verification Plan

### Automated Verification

Run the adapter-owned test suite that protects:

- product intake
- role planning
- round artifact creation
- composition
- Studio and Audit surfaces
- mainline runtime behavior
- review viewer behavior
- round verification

At minimum, the validation should include the current adapter-owned tests under `tests/worldview_runtime_adapter/`.

### End-To-End Verification

Run one supported round through:

- `scripts/run_worldview_panel.py`

Then validate the result through:

- `scripts/verify_worldview_panel_round.py`

The run should confirm:

- adapter-owned artifacts are emitted
- verification passes on the adapter-owned contract
- default consumption still points to the adapter-owned Studio-first path

### Boundary Verification

Run a final repository scan for signs of the removed parallel path.

The scan should confirm:

- plugin verification no longer requires plugin-owned product artifacts
- plugin synthesis no longer acts like the supported product delivery path
- repository language does not suggest two equal product owners

## Risks

### Risk 1: Over-Reverting Plugin Maintenance Behavior

Mitigation:

- freeze the keep list first
- preserve the two approved plugin maintenance fixes by name

### Risk 2: Hidden Adapter Dependency On Plugin Product Logic

Mitigation:

- validate through the supported scripts after cleanup
- if the adapter relies on a plugin helper, preserve the helper but not the plugin-owned product contract

### Risk 3: Leaving Residual Drift Behind

Mitigation:

- run a final boundary scan after tests and end-to-end validation
- treat leftover parallel-path wording as an incomplete cleanup

## Success Criteria

This cleanup is complete only when all of the following are true:

- the adapter remains the only supported product mainline
- plugin-owned parallel product behavior has been removed
- the two approved plugin maintenance fixes remain
- adapter-owned tests pass
- a supported round can still be run and verified end to end
- repository behavior no longer suggests two co-equal product paths

## Recommendation

Use the minimal cleanup path.

Keep the adapter-owned mainline intact.

Remove only the plugin changes that recreate product ownership.

Do not widen scope into benchmark work, feature work, or a full plugin revert.
