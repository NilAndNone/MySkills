# Worldview Panel Production Broker Design

Date: 2026-04-04
Status: Approved for planning
Scope: `plugins/worldview-panel-codex`

## Summary

This design replaces the current parent-orchestrated worldview panel dispatch path with a production broker architecture built on Codex app-server. The root fix is not another guard before dispatch. The root fix is removing child-prompt authority from the parent model entirely.

The new system is JSON-first across module boundaries, fail-closed by default, and audit-heavy in early versions. Worker, judge, and synthesizer turns are all broker-controlled app-server turns with explicit policy, schema, attestation, and event logging.

## Problem Statement

The current system can prepare correct `packet.txt` artifacts and still dispatch different content to child agents. That means the existing trust model is wrong. File-side validation proves only that a correct packet exists on disk. It does not prove that the same bytes were actually sent to the child.

The incident root cause is therefore:

- the parent planner still controls final child input bytes
- validation and dispatch authority live in the same model-controlled path
- the system has no runtime boundary that prevents payload substitution at dispatch time

This design treats that as an authority-boundary failure, not a missing check.

## Goals

- Remove raw child-prompt dispatch authority from the parent planner.
- Make broker dispatch deterministic and ticket-based.
- Make every module boundary JSON-only.
- Make all 24 personas first-class runtime identities.
- Require schema, policy, and quality attestation before a result becomes certified.
- Keep full incident-grade auditability for early versions.

## Non-Goals

- No compatibility layer for the old dispatch path.
- No reuse of prompt-level guardrails as the primary enforcement mechanism.
- No automatic retry in v1.
- No group-coverage constraint in v1.
- No lightweight logging mode in early versions.

## Final Design Decisions

- There are 24 independent worker identities. Persona differentiation is a core runtime feature, not a packet-only illusion.
- The parent planner becomes as deterministic as practical. It does not select prompt text, does not directly launch worker turns, and does not hold child-input authority.
- The synthesizer is still model-based, but it is also broker-controlled and may consume only certified results.
- Certification requires two layers:
  - rules/schema/policy attestation
  - independent quality judgment
- The quality judge sees persona profile, sealed packet, and worker result.
- If a worker, judge, or synthesizer turn fails, there is no automatic retry in v1.
- A run may continue only when certified success rate is at least 80 percent.
- Profile and policy are part of the seal chain and must be written into tickets and attestations.
- Early versions (`v1` through `v3`) use heavy audit logging by default.

## System Architecture

The system is split into five units with hard boundaries.

### 1. Parent Planner

Responsibilities:

- normalize user intent into `round_input.json`
- compute deterministic persona selection and batching
- submit a `dispatch_job.json` to the broker runtime
- request final synthesis from certified results only

Forbidden:

- creating raw child prompts
- directly calling `spawn_agent(message=...)`
- reading uncertified worker outputs during synthesis

### 2. Round Builder

Responsibilities:

- build persona-specific sealed packets
- materialize packet manifests
- materialize dispatch tickets
- seal packet, profile, and policy fingerprints into round artifacts

Output ends at `SEALED`. It never dispatches.

### 3. App-Server Broker

Responsibilities:

- load tickets
- verify packet/profile/policy seal data
- create app-server threads and turns
- inject effective model, policy, schema, and worker identity
- collect raw structured outputs
- write audit events and attestation artifacts
- certify or reject results

This is the only component allowed to convert sealed packet bytes into child turn input.

### 4. Quality Judge

Responsibilities:

- inspect persona profile, sealed packet, and worker result
- determine whether the result is substantively on-task and sufficiently persona-faithful
- produce structured judgment JSON

Judge failure affects only that persona. The overall run still follows the 80 percent certification threshold.

### 5. Synthesizer

Responsibilities:

- consume certified persona results only
- generate the final user-facing worldview panel
- emit structured synthesis output and synthesis attestation

The synthesizer is also broker-controlled. It is not a free parent-model step.

## Runtime Identity Model

Each persona is a distinct runtime identity.

Identity data lives in versioned broker-side JSON profiles, not in repo-local agent files. A persona identity includes:

- `profile_id`
- `profile_version`
- `profile_hash`
- policy binding
- output schema binding
- model binding
- persona-specific system instruction content

Repo-local persona source material remains in:

- `runtime/personas/`
- `runtime/persona-index.json`

Repo-local runtime agent files are removed from the execution path.

## Data Contracts

All cross-module interfaces are JSON. Text exists only where the model must ultimately receive text input.

### Core Artifacts

```text
<round_root>/
  round_input.json
  round_manifest.json
  dispatch_job.json
  packets/
    <persona>/
      packet.txt
      packet_manifest.json
  tickets/
    <persona>.json
  results/
    <persona>/
      raw_result.json
      quality_judgment.json
      attestation.json
      certified_result.json
  synthesis/
    synthesis_input.json
    synthesis_raw_result.json
    synthesis_attestation.json
    final_panel.json
    final_panel.md
  audit/
    events.jsonl
    run_summary.json
    diagnostic_bundle.json
```

### Dispatch Job

`dispatch_job.json` is the parent-to-broker entrypoint.

Example shape:

```json
{
  "schema_version": "dispatch_job_v1",
  "run_id": "wv-e70f63811dfd",
  "round_root": "/abs/path/to/round_root",
  "selected_personas": ["risk_manager", "stoic_pragmatist"],
  "batch_size": 6,
  "dispatch_mode": "strict_thresholded_fail_closed",
  "min_certified_success_rate": 0.8
}
```

### Dispatch Ticket

Each persona has one ticket. The broker API accepts tickets, never raw prompt text.

```json
{
  "schema_version": "dispatch_ticket_v1",
  "run_id": "wv-e70f63811dfd",
  "persona": "risk_manager",
  "ticket_id": "tkt-risk_manager-v1",
  "packet_id": "pkt-risk_manager-v1",
  "packet_path": "packets/risk_manager/packet.txt",
  "packet_fingerprint": "sha256:...",
  "packet_length": 4287,
  "profile_id": "risk_manager_worker_v3",
  "profile_hash": "sha256:...",
  "policy_id": "readonly_locked_v1",
  "policy_hash": "sha256:...",
  "worker_schema_version": "worldview_worker_result_v1",
  "attempt": 1,
  "state": "SEALED"
}
```

### Worker Result

Worker output is schema-first JSON, not a natural-language interface contract.

```json
{
  "schema_version": "worldview_worker_result_v1",
  "persona": "risk_manager",
  "judgment": {
    "factual": "...",
    "value": "...",
    "strategy": "..."
  },
  "diagnosis": ["..."],
  "recommended_actions": ["..."],
  "voice_style": "...",
  "blind_spot": "...",
  "overuse_risk": "...",
  "signature_line": "...",
  "confidence": 0.78
}
```

### Quality Judgment

```json
{
  "schema_version": "quality_judgment_v1",
  "run_id": "wv-e70f63811dfd",
  "persona": "risk_manager",
  "judge_status": "passed",
  "persona_faithful": true,
  "task_faithful": true,
  "substantive_enough": true,
  "issues": [],
  "judge_summary": "..."
}
```

### Attestation

```json
{
  "schema_version": "attestation_v1",
  "run_id": "wv-e70f63811dfd",
  "persona": "risk_manager",
  "packet_id": "pkt-risk_manager-v1",
  "packet_fingerprint": "sha256:...",
  "packet_length": 4287,
  "ticket_id": "tkt-risk_manager-v1",
  "ticket_fingerprint": "sha256:...",
  "profile_id": "risk_manager_worker_v3",
  "profile_hash": "sha256:...",
  "policy_id": "readonly_locked_v1",
  "policy_hash": "sha256:...",
  "thread_id": "thr_...",
  "turn_id": "turn_...",
  "effective_model": "gpt-5-codex",
  "effective_output_schema_version": "worldview_worker_result_v1",
  "schema_valid": true,
  "policy_valid": true,
  "forbidden_tool_use": false,
  "quality_valid": true,
  "status": "CERTIFIED",
  "dispatch_started_at": "2026-04-04T12:00:00Z",
  "dispatch_completed_at": "2026-04-04T12:00:18Z"
}
```

### Certified Result

This is the only persona result the synthesizer may consume.

```json
{
  "schema_version": "certified_result_v1",
  "run_id": "wv-e70f63811dfd",
  "persona": "risk_manager",
  "packet_fingerprint": "sha256:...",
  "result_fingerprint": "sha256:...",
  "attestation_fingerprint": "sha256:...",
  "certification_status": "certified",
  "certified_at": "2026-04-04T12:00:19Z",
  "result": {}
}
```

## Runtime State Machine

Each persona follows a hard lifecycle:

`DRAFT -> PREPARED -> VALIDATED -> SEALED -> DISPATCH_RESERVED -> DISPATCHED -> RESULT_RECEIVED -> RESULT_SCHEMA_VALID -> QUALITY_VALIDATED -> ATTESTED -> CERTIFIED`

Failure may occur at any step and moves the persona into `FAILED`.

Run-level behavior:

- synthesis may begin only if certified success rate is at least `0.8`
- below `0.8`, the run fails closed
- no automatic retry in v1

## Broker Execution Flow

The broker flow is:

1. validate `dispatch_job.json`
2. load all referenced tickets
3. verify sealed packet, profile, and policy hashes
4. reserve a batch
5. for each persona in the batch:
   - start thread
   - start turn with broker-injected packet bytes, profile, policy, and output schema
   - collect worker result
   - validate schema
   - run quality judge
   - write attestation
   - write certified result or failure record
6. compute certification rate
7. if rate is at least `0.8`, start synthesizer turn
8. certify synthesis output
9. write run summary

The parent never injects child bytes directly.

## App-Server Mapping

The broker uses Codex app-server as the runtime substrate.

- `thread/start` creates isolated sessions for worker, judge, and synthesizer turns
- `turn/start` is where the broker injects packet text and effective runtime controls
- per-turn `approvalPolicy` and `sandboxPolicy` are set by the broker, not trusted from static repo config
- per-turn `outputSchema` is mandatory for worker, judge, and synthesizer turns
- app-server event streams are captured into audit artifacts

This matches the design requirement that the runtime, not the parent model, enforces the protocol.

## Logging and Audit Design

Early versions are intentionally heavy on audit data.

### Heavy Audit Rule

`v1` through `v3` run with heavy audit by default. This is not a debug option. It is the standard operating mode.

### Audit Layers

1. `audit/events.jsonl`
   - append-only machine-readable event stream
   - every critical state transition is recorded
2. attestation artifacts
   - per-persona and synthesis proofs
3. run summary artifacts
   - operator-facing diagnosis and counts
4. global navigation index
   - lightweight cross-run locator only

### Audit Event Requirements

Each event contains at least:

- `schema_version`
- `event_id`
- timestamp
- `run_id`
- `component`
- `entity_type`
- `entity_id`
- `stage`
- `status`
- relevant hash references
- thread and turn ids when applicable

Suggested stages:

- `run_started`
- `round_input_validated`
- `packet_prepared`
- `packet_sealed`
- `ticket_issued`
- `batch_reserved`
- `worker_dispatch_started`
- `worker_dispatched`
- `worker_result_received`
- `worker_schema_validated`
- `worker_quality_validated`
- `worker_certified`
- `worker_failed`
- `synth_dispatch_started`
- `synth_result_received`
- `synth_certified`
- `run_completed`
- `run_failed`

### Heavy Audit Payload Retention

Early versions retain:

- sealed packets
- packet manifests
- dispatch tickets
- worker raw structured outputs
- quality judge inputs and outputs
- synthesis inputs and raw outputs
- app-server critical event snapshots

The audit design avoids putting full text bodies inside `events.jsonl`. Event logs store identifiers, hashes, lengths, schema versions, and error codes. Full content stays in dedicated artifacts.

### Global Run Index

The global log becomes a lightweight navigation index only:

```text
~/.codex/log/worldview-panel-codex/run_index.jsonl
```

Each record includes:

- `run_id`
- `round_root`
- start and end timestamps
- run status
- certified persona count
- certification success rate

Full diagnosis always happens from `round_root/audit/`, not from global logs.

## Certification Rules

A worker result becomes certified only if all of the following are true:

- packet seal verifies
- profile seal verifies
- policy seal verifies
- worker output matches schema
- no forbidden tool or collaboration behavior is detected
- quality judge passes
- attestation is complete

Anything less than this is not certifiable.

## Failure Policy

### Persona-Level Failure

A persona is marked `FAILED` when any of the following occurs:

- packet hash mismatch
- profile hash mismatch
- policy hash mismatch
- missing or invalid packet artifact
- app-server runtime mismatch
- schema invalid output
- forbidden tool or collaboration usage
- quality judge timeout, error, or failure
- missing attestation

### Run-Level Failure

- If certified success rate is below 80 percent, the run fails closed.
- If certified success rate is at least 80 percent, synthesis may proceed.
- There is no automatic retry in v1.

## File-Level Refactor Plan

### Keep

- `plugins/worldview-panel-codex/runtime/personas/`
- `plugins/worldview-panel-codex/runtime/persona-index.json`
- `plugins/worldview-panel-codex/tools/persona_materials.py`
- logging helpers only if rewritten to support the new JSON audit model

### Remove From Execution Path

- `plugins/worldview-panel-codex/tools/dispatch_packet_guard.py`
- `plugins/worldview-panel-codex/runtime/agents/*.toml`
- old natural-language worker interface assumptions
- old prompt-level worldview dispatch orchestration

### Replace Or Rewrite

- `plugins/worldview-panel-codex/skills/worldview-panel-entry/SKILL.md`
- `plugins/worldview-panel-codex/skills/worldview-panel-entry/agents/openai.yaml`
- `plugins/worldview-panel-codex/tools/context_packet_common.py`
- `plugins/worldview-panel-codex/tools/prepare_context_packets.py`
- current logging contract and log format

### New Core Entrypoints

- `plugins/worldview-panel-codex/tools/build_worldview_round.py`
- `plugins/worldview-panel-codex/tools/run_worldview_broker.py`
- `plugins/worldview-panel-codex/tools/synthesize_worldview_panel.py`
- `plugins/worldview-panel-codex/tools/verify_worldview_round.py`

### New Schema Directory

- `plugins/worldview-panel-codex/schemas/round_input_v1.json`
- `plugins/worldview-panel-codex/schemas/round_manifest_v1.json`
- `plugins/worldview-panel-codex/schemas/dispatch_job_v1.json`
- `plugins/worldview-panel-codex/schemas/dispatch_ticket_v1.json`
- `plugins/worldview-panel-codex/schemas/worldview_worker_result_v1.json`
- `plugins/worldview-panel-codex/schemas/quality_judgment_v1.json`
- `plugins/worldview-panel-codex/schemas/attestation_v1.json`
- `plugins/worldview-panel-codex/schemas/certified_result_v1.json`
- `plugins/worldview-panel-codex/schemas/synthesis_result_v1.json`
- `plugins/worldview-panel-codex/schemas/audit_event_v1.json`

## Test and Acceptance Plan

### Interface Acceptance

- every cross-module interface is validated against versioned JSON schema
- broker APIs reject raw prompt input
- synthesizer rejects uncertified persona results

### Boundary Acceptance

- parent cannot directly dispatch worker turns
- broker rejects any packet/profile/policy mismatch
- every worker, judge, and synthesizer turn leaves attestation

### End-to-End Acceptance

- 24 persona / 4 batch runs succeed only when certified success rate is at least 80 percent
- schema-invalid worker output is rejected
- quality-invalid worker output is rejected
- synthesis starts only after certification threshold passes

### Incident Regression Acceptance

- recreating the prior simplified-prompt behavior is impossible through the supported interface
- tampering with packet, profile, or policy artifacts causes broker rejection
- removing attestation causes synthesis rejection

## Implementation Boundaries For Planning

This spec is for architecture and planning only.

Implementation planning should assume:

- a hard cut from the old dispatch model
- no compatibility bridge
- no fallback to prompt-level controls
- heavy audit remains enabled through the first three runtime versions unless explicitly redesigned later

## Open Assumptions Locked By Approval

The following are now fixed inputs for implementation planning:

- production end-state app-server broker, not MCP-first
- JSON-only module interfaces
- 24 independent worker identities
- deterministic parent planner direction
- model-based synthesizer under broker control
- 80 percent certification threshold
- no automatic retries in v1
- no group-coverage constraint in v1
- heavy audit logging by default in early versions
