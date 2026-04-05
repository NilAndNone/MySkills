# Worldview Panel Governance Boundary Design

Date: 2026-04-05
Status: Ready for review
Scope: `plugins/worldview-panel-codex`

## TL;DR

This design fixes the governance half of the 2026-04-05 incident.

The problem was not only that broker v1 hit real compatibility bugs. The deeper problem was that one active panel run still allowed the same top-level session to:

- run the product path
- modify plugin code and tests
- rewrite audit narrative
- rewrite dispatch topology

Phase 1 does not require OS-level read-only isolation yet. Instead, it adds a sealed governance contract and fail-closed invalidation inside the existing artifact pipeline.

The core rule is:

**If topology, audit authority, or protected repo baseline drift during an active run, the round becomes `INVALID`, not merely failed.**

## Root Cause Framing

The 2026-04-05 incident was not a replay of the 2026-04-02 simplified-prompt problem.

There is no evidence that the sealed packet bytes and the actual worker turn input diverged in the same way as the earlier incident. The current broker path already tightened dispatch authority substantially:

- dispatch is ticket-only
- broker, not the parent planner, renders turn input
- exact turn input is attested
- fresh thread per worker attempt is already enforced
- synthesis already strict-gates on `TECHNICAL_CERTIFIED`

What failed on 2026-04-05 was the runtime governance boundary around an active panel run.

After the first real dispatch failed, the same request was allowed to continue as a hybrid of:

- plugin bring-up
- schema and protocol debugging
- code modification
- ad hoc topology changes
- top-level audit backfill
- final synthesis and verification

That means the final result was no longer a clean production-state validation sample.

## Why JSON Mismatch Checks Are Not Enough

Content mismatch checks remain necessary, but they are insufficient as the main fix.

Examples:

- `dispatch_job.techno_only.json` can be valid JSON and still be an unauthorized topology mutation.
- top-level audit events can be well-formed JSON and still be written by the wrong actor after the fact.
- a run can modify plugin code, then regenerate artifacts that all hash correctly with each other, while still invalidating the claim that the original version ran successfully.

So the design must govern not only whether JSON artifacts are internally consistent, but also:

- who is allowed to author them
- when they may appear
- whether they belong to the sealed topology
- whether the protected code baseline drifted during the run

## Design Objectives

- Preserve the current broker v1 dispatch authority model.
- Add a hard governance boundary for active runs inside the existing artifact pipeline.
- Distinguish clean product failure from governance contamination.
- Make unauthorized topology mutation detectable and fatal.
- Make top-level audit event authorship explicit and enforceable.
- Detect protected repo baseline drift during an active run.
- Refuse synthesis and verification for contaminated rounds.
- Keep Phase 1 compatible with the current workspace model.

## Non-Goals

- No OS-level read-only filesystem isolation in Phase 1.
- No new external orchestration service.
- No attempt to make contaminated runs recoverable.
- No retry/governance quality framework beyond invalidation and fail-closed gating.
- No replacement of existing broker attestation semantics.

## Governance Model

Phase 1 adds one new sealed artifact and one new runtime status artifact:

- `governance_seal.json`
- `governance_status.json`

They are created by the round builder and then treated as broker-governed runtime prerequisites.

### `governance_seal.json`

`governance_seal.json` is the single authority contract for the run. It does not replace `round_manifest.json` or `dispatch_job.json`. It seals which artifacts and actors are allowed to participate in the run.

It must include at least:

- `schema_version`
- `run_id`
- `round_root`
- `state`
- `topology`
- `allowed_runtime_outputs`
- `protected_repo_files`
- `source_authority`
- `invalidity_policy`
- `seal_fingerprint`

#### Topology Section

The topology section seals:

- the fingerprint of `round_manifest.json`
- the fingerprint of `dispatch_job.json`
- the fingerprint of each `tickets/<persona>.json`
- the selected persona set
- the dispatch mode
- the batch size

Any extra dispatch job not declared here is a governance violation.

#### Allowed Runtime Outputs

Phase 1 does not make the plugin physically read-only. Instead, it defines the only paths that may change during an active run.

Allowed runtime outputs are limited to artifact paths such as:

- `results/`
- `audit/`
- `synthesis/`
- `verify/`

Any unexpected write target discovered by runtime guard logic is a governance violation.

#### Protected Repo Files

The seal records a baseline fingerprint set for protected plugin files. At minimum this includes:

- tooling under `plugins/worldview-panel-codex/tools/`
- schemas under `plugins/worldview-panel-codex/schemas/`
- runtime skills under `plugins/worldview-panel-codex/skills/`
- plugin tests under `plugins/worldview-panel-codex/tests/`

This list can be narrowed later, but Phase 1 should start conservatively. If these protected files drift during an active run, the round is invalidated.

#### Source Authority

The seal records which emitter may write which audit stages.

Examples:

- top-level lifecycle stages such as `run_start`, `batch_end`, `synthesis`, and `run_end` are orchestrator-only
- broker persona dispatch stages are broker-only
- verification stages are verifier-only

This prevents a generic log writer from impersonating the active runtime actor.

#### Invalidity Policy

The seal also lists governance violations that force `INVALID`, such as:

- topology drift
- protected repo drift
- unauthorized emitter
- unauthorized stage write
- synthesis or verify invoked after invalidation

### `governance_status.json`

`governance_status.json` is the runtime truth for the round state. It starts at build time and is updated by guarded runtime components.

It must include at least:

- `schema_version`
- `run_id`
- `state`
- `terminal_reason`
- `violations`
- `updated_at`
- `updated_by_component`

The status file separates clean failure from contaminated execution.

## Runtime State Model

The round state machine is:

- `SEALED`
- `PRECHECK_PASSED`
- `ACTIVE_DISPATCH`
- `BROKER_COMPLETED`
- `SYNTHESIS_COMPLETED`
- `VERIFIED`

Terminal states:

- `FAILED_CLOSED`
- `INVALID`

### `FAILED_CLOSED`

`FAILED_CLOSED` means the product path executed under the sealed governance boundary, but a real technical failure stopped the run.

Examples:

- worker schema incompatibility
- app-server lifecycle failure
- invalid worker result
- missing required certification

This is a clean failure sample.

### `INVALID`

`INVALID` means the governance boundary was broken, so the run cannot be treated as a trustworthy validation sample.

Examples:

- protected repo baseline drift during the run
- unauthorized `dispatch_job*.json`
- unauthorized audit emitter
- unauthorized top-level audit stage write
- synthesis or verification attempted after authority violation

This is not merely a failed run. It is an invalid run.

## Module Responsibilities

### Round Builder

Files:

- `plugins/worldview-panel-codex/tools/worldview_round_builder.py`
- `plugins/worldview-panel-codex/tools/build_worldview_round.py`

New responsibilities:

- compute and write `governance_seal.json`
- compute and write initial `governance_status.json`
- seal topology fingerprints
- seal protected repo baseline fingerprints
- seal source authority rules
- seal invalidity policy

The builder remains the only component that initializes governance artifacts.

### Broker Entrypoint And Broker Runtime

Files:

- `plugins/worldview-panel-codex/tools/run_worldview_broker.py`
- `plugins/worldview-panel-codex/tools/worldview_broker.py`

New responsibilities:

- load and validate `governance_seal.json`
- reject runs whose `governance_status.json` is already terminal
- perform prechecks before dispatch starts
- detect topology drift before and during dispatch
- detect protected repo drift before and during dispatch
- write `INVALID` status on governance violation
- write `FAILED_CLOSED` on clean product failure

Broker prechecks must include:

- sealed fingerprint match for `dispatch_job.json`
- sealed fingerprint match for `round_manifest.json`
- no extra `dispatch_job*.json` outside the sealed topology
- protected repo baseline still matches
- governance status still allows execution

Broker may not continue dispatch after a governance violation.

### Audit And Log Writers

Files:

- `plugins/worldview-panel-codex/tools/write_run_log.py`
- `plugins/worldview-panel-codex/tools/run_log.py`
- `plugins/worldview-panel-codex/tools/worldview_audit.py`
- `plugins/worldview-panel-codex/schemas/audit_event_v1.json`

Audit events must gain explicit source identity fields:

- `emitter`
- `source_process`
- `source_session_id`
- `synthetic`

Rules:

- writing round audit now requires explicit emitter identity
- emitter-stage combinations must be checked against `source_authority`
- unauthorized top-level writes are governance violations
- `synthetic=true` events may be stored, but they are non-authoritative
- synthetic events may not unlock synthesis or verification

### Synthesizer And Verifier

Files:

- `plugins/worldview-panel-codex/tools/worldview_synthesis.py`
- `plugins/worldview-panel-codex/tools/verify_worldview_round.py`

New responsibilities:

- refuse to run if the round is already `INVALID`
- refuse to run if governance violations exist
- enforce that every requested persona remains `TECHNICAL_CERTIFIED`
- report invalidation reason separately from ordinary runtime failure

Verification must distinguish:

- clean broker failure
- governance invalidation

## Artifact Sketches

### `governance_seal.json`

```json
{
  "schema_version": "governance_seal_v1",
  "run_id": "wv-round-...",
  "round_root": "/abs/path/to/round",
  "state": "SEALED",
  "topology": {
    "round_manifest_fingerprint": "sha256:...",
    "dispatch_job_fingerprint": "sha256:...",
    "selected_personas": ["risk_manager", "existentialist"],
    "dispatch_mode": "strict_all_required",
    "batch_size": 2,
    "tickets": {
      "risk_manager": "sha256:...",
      "existentialist": "sha256:..."
    }
  },
  "allowed_runtime_outputs": [
    "results/",
    "audit/",
    "synthesis/",
    "verify/"
  ],
  "protected_repo_files": {
    "plugins/worldview-panel-codex/tools/worldview_broker.py": "sha256:...",
    "plugins/worldview-panel-codex/schemas/worldview_worker_result_v1.json": "sha256:..."
  },
  "source_authority": {
    "orchestrator": ["run_start", "question_classify", "panel_select", "context_prepare", "batch_end", "synthesis", "run_end"],
    "broker": ["dispatch_started", "result_received", "technical_certified", "dispatch_failed"],
    "verifier": ["verify_started", "verify_completed"]
  },
  "invalidity_policy": [
    "topology_drift",
    "protected_repo_drift",
    "unauthorized_emitter",
    "unauthorized_stage_write",
    "post_invalidation_execution"
  ],
  "seal_fingerprint": "sha256:..."
}
```

### `governance_status.json`

```json
{
  "schema_version": "governance_status_v1",
  "run_id": "wv-round-...",
  "state": "SEALED",
  "terminal_reason": null,
  "violations": [],
  "updated_at": "2026-04-05T12:00:00Z",
  "updated_by_component": "round_builder"
}
```

## Violation Types

Phase 1 should use explicit violation identifiers rather than free-form strings.

Recommended initial set:

- `topology_drift`
- `extra_dispatch_job`
- `dispatch_job_fingerprint_mismatch`
- `round_manifest_fingerprint_mismatch`
- `protected_repo_drift`
- `unauthorized_emitter`
- `unauthorized_stage_write`
- `synthetic_top_level_event`
- `post_invalidation_execution`

These identifiers should appear in both status and verification output.

## Rollout Plan

### Phase 1: Seal And State Machine

Deliverables:

- add `governance_seal.json`
- add `governance_status.json`
- seal topology fingerprints
- seal protected repo baseline fingerprints
- add broker precheck
- invalidate on topology or baseline drift

Core tests:

- builder writes both governance artifacts
- modifying `dispatch_job.json` makes broker fail before dispatch
- adding `dispatch_job.techno_only.json` makes broker invalidate the round
- changing protected repo files during the run invalidates the round

### Phase 2: Audit Authority Enforcement

Deliverables:

- extend `audit_event_v1`
- require emitter identity for round audit writes
- enforce source-authority policy
- mark synthetic events explicitly

Core tests:

- authorized emitter can write allowed stages
- unauthorized emitter cannot write top-level stages
- synthetic event does not count as authoritative execution evidence
- missing source identity fails verification

### Phase 3: Synthesis And Verify Terminal Gating

Deliverables:

- synthesis refuses `INVALID`
- verification distinguishes `FAILED_CLOSED` from `INVALID`
- verify reports authority violations directly

Core tests:

- synthesis refuses to proceed after governance invalidation
- verify reports invalidation even if certified persona results exist
- clean runtime failure remains `FAILED_CLOSED`, not `INVALID`

### Phase 4: Diagnostics And Operator Clarity

Deliverables:

- stable violation reporting
- improved verify diagnostics
- updated developer workflow docs

Core tests:

- each violation maps to a clear report entry
- workflow docs match the actual enforced runtime path

## Acceptance Criteria

Phase 1 is complete only if all of the following are true:

- an active run cannot add ad hoc dispatch jobs without being invalidated
- an active run cannot drift protected plugin files without being invalidated
- top-level audit authority is no longer anonymous
- synthesis and verification refuse contaminated rounds
- verification output clearly distinguishes clean runtime failure from invalid execution

## Deferred Work

These remain explicitly out of scope for this design and belong to later work:

- OS-level read-only or isolated install execution
- capability-token infrastructure beyond sealed source authority
- retry orchestration improvements
- quality-gated synthesis
- policy for partial panels

## Final Position

The current broker v1 implementation already fixed much of the dispatch-authority side of the earlier incident class.

What remains is the runtime governance side:

- execution must not silently coexist with code modification
- audit authority must not be anonymous
- topology must not remain mutable after seal

This design intentionally makes those constraints enforceable through sealed artifacts and terminal invalidation before moving on to stronger physical isolation.
