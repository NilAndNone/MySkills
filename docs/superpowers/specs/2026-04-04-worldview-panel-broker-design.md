# Worldview Panel Broker Design

Date: 2026-04-04
Status: Revised after review
Scope: `plugins/worldview-panel-codex`

## TL;DR

This design fixes the actual root cause of the incident: the parent planner must no longer control the final bytes sent to worker turns.

The runtime is split into phases:

- `v1`: fix authority boundary and exact input attestation
- `v1.1`: add infra retry and audit governance
- `v2`: add quality governance

The first version is intentionally narrow. It does not try to solve prompt integrity, worker quality, reliability tuning, and governance all at once.

## Root Cause Framing

The incident was not caused by missing packet generation. It was caused by the fact that the parent planner still held final dispatch authority.

The old system could prove that:

- a correct `packet.txt` existed on disk
- packet validation had passed

But it could not prove that:

- the same bytes were actually delivered into the worker turn

This is an authority-boundary failure. File-side validation is not sufficient if final turn input is still mutable in the parent-controlled path.

## Design Objectives

- Remove raw child-input authority from the parent planner.
- Make dispatch ticket-only.
- Make module boundaries JSON-only.
- Prove exact turn input, not only sealed packet existence.
- Keep v1 small enough to land without creating a new availability incident.
- Preserve enough audit evidence to debug early versions.

## Non-Goals

- No compatibility path for the old dispatch model.
- No hook-based enforcement boundary.
- No quality-gated synthesis in v1.
- No percentage threshold gate in v1.
- No partial panel mode in v1.

## Versioned Rollout

### v1: Authority Boundary Fix

`v1` includes only the mechanisms required to fix the root cause:

- build round artifacts
- seal packet, identity, and policy
- dispatch by ticket only
- use fresh thread per attempt
- forbid steer, resume, rollback, compact, and review-mode continuation
- attest exact turn input
- validate worker output schema
- synthesize only if every requested persona is `TECHNICAL_CERTIFIED`

### v1.1: Reliability And Governance

`v1.1` adds:

- one idempotent infra retry
- effective requirements snapshot in attestation
- retention TTL
- redaction policy
- access control scope
- export and delete workflow
- optional future product semantics such as `PARTIAL_PANEL`

### v2: Quality Governance

`v2` adds:

- quality judge
- persona-faithfulness rubric
- `QUALITY_PASSED`
- quality-aware synthesis logic
- stratified audit modes

## System Units

### Parent Planner

Responsibilities:

- normalize the user request into round input
- choose personas deterministically
- choose batching deterministically
- create a `dispatch_job.json`
- request synthesis only from technically certified results

Forbidden:

- constructing raw worker prompt text
- calling worker dispatch directly
- reading uncertified worker outputs

### Round Builder

Responsibilities:

- materialize persona packets
- materialize packet manifests
- materialize dispatch tickets
- freeze seal data into the round

The builder never dispatches.

### Broker

Responsibilities:

- load sealed tickets
- verify sealed packet, identity, and policy state
- maintain a broker-owned app-server session
- start app-server threads and turns
- inject runtime identity through documented mechanisms
- collect app-server events
- write attestation and audit artifacts
- certify or fail worker results
- invoke synthesizer only when strict gate passes

The broker is the only component that may convert sealed packet bytes into turn input.

### Synthesizer

Responsibilities:

- consume only technically certified worker results
- generate final panel output
- write synthesis attestation

In `v1`, the synthesizer is not quality-gated. It is integrity-gated.

## Identity Model

Persona differentiation is a first-class runtime feature.

There are 24 independent worker identities. Identity data is maintained as versioned JSON profiles under broker control.

Each profile includes at least:

- `profile_id`
- `profile_version`
- `profile_hash`
- policy binding
- output schema binding
- model binding
- persona instruction content

### Runtime Injection Mechanism

`v1` does not assume an undocumented broker-side developer/system profile API.

Instead:

1. the broker reads the versioned persona JSON profile
2. the broker renders a temporary persona skill file
3. the broker injects that skill into the worker turn via the documented `skill` input item path

This gives the design a concrete mechanism that aligns with documented app-server capabilities.

### Identity Attestation Fields

Identity attestation must include:

- `identity_source = profile_json`
- `identity_runtime_carrier = skill_file`
- `profile_id`
- `profile_version`
- `profile_hash`
- `skill_path`
- `skill_fingerprint`

## Fresh-Thread Rule

Post-seal mutation paths must be closed explicitly.

For worker and synthesizer turns in `v1`, and for any future judge turns:

- every attempt uses a fresh thread
- no thread reuse across attempts
- no `turn/steer`
- no `thread/resume`
- no `thread/rollback`
- no `thread/compact/start`
- no review-mode continuation on these threads

This is not an implementation preference. It is part of the authority boundary.

## Transport Model

`v1` talks to Codex app-server over JSON-RPC on a WebSocket transport.

This design does not assume:

- a synchronous REST `POST /thread/start`
- a synchronous REST `POST /turn/start`
- a `codex app-server run` subcommand

The runtime shape is:

1. broker opens a WebSocket connection to `codex app-server --listen ws://127.0.0.1:8787`
2. broker sends `initialize`
3. broker sends `thread/start`
4. broker sends `turn/start`
5. broker waits for the matching `turn/completed` notification
6. broker calls `thread/read` with `includeTurns=true`
7. broker extracts the completed turn's observed items from `thread.turns[*].items`

`turn/start` carries app-server `UserInput` items such as `skill` and `text`. It is an acknowledgement step, not a complete-result step. `Turn.items` is empty on `turn/start` and on `turn/completed`, so observed item extraction must come from `thread/read`.

The broker may wrap this in a local adapter abstraction, but the transport truth remains WebSocket JSON-RPC. Any local shim must preserve the same attestation semantics and may not invent alternate payload authority.

## Data Contracts

All module boundaries are JSON-only.

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
      attestation.json
      technical_certified_result.json
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

## Core Artifacts

### Dispatch Job

```json
{
  "schema_version": "dispatch_job_v1",
  "run_id": "wv-e70f63811dfd",
  "round_root": "/abs/path/to/round_root",
  "selected_personas": ["risk_manager", "stoic_pragmatist"],
  "batch_size": 6,
  "dispatch_mode": "strict_all_required"
}
```

### Dispatch Ticket

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
  "profile_version": "3",
  "profile_hash": "sha256:...",
  "policy_id": "readonly_locked_v1",
  "policy_hash": "sha256:...",
  "worker_schema_version": "worldview_worker_result_v1",
  "state": "SEALED"
}
```

### Worker Result

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

### Attestation

`v1` attestation must prove exact turn input, not just packet existence.

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
  "profile_version": "3",
  "profile_hash": "sha256:...",
  "skill_fingerprint": "sha256:...",
  "policy_id": "readonly_locked_v1",
  "policy_hash": "sha256:...",
  "thread_id": "thr_...",
  "turn_id": "turn_...",
  "turn_input_fingerprint": "sha256:...",
  "turn_user_text_fingerprint": "sha256:...",
  "renderer_version": "turn_renderer_v1",
  "newline_policy": "lf",
  "encoding": "utf-8",
  "input_item_count": 2,
  "effective_model": "gpt-5-codex",
  "effective_output_schema_version": "worldview_worker_result_v1",
  "schema_valid": true,
  "item_allowlist_valid": true,
  "technical_status": "TECHNICAL_CERTIFIED",
  "dispatch_started_at": "2026-04-04T12:00:00Z",
  "dispatch_completed_at": "2026-04-04T12:00:18Z"
}
```

### Technical Certified Result

```json
{
  "schema_version": "technical_certified_result_v1",
  "run_id": "wv-e70f63811dfd",
  "persona": "risk_manager",
  "packet_fingerprint": "sha256:...",
  "result_fingerprint": "sha256:...",
  "attestation_fingerprint": "sha256:...",
  "technical_status": "TECHNICAL_CERTIFIED",
  "certified_at": "2026-04-04T12:00:19Z",
  "result": {}
}
```

## Exact Input Attestation

The attestation source of truth is:

- the broker-constructed JSON-RPC `turn/start` payload
- the matching `turn/completed` notification
- the `thread/read(includeTurns=true)` response that yields the completed turn items

It is not:

- model self-report
- parent planner log text
- ad hoc human-readable summaries

The broker must compute and persist:

- `packet_fingerprint`
- `turn_input_fingerprint = sha256(canonical_json(turn/start.params.input))`
- `turn_user_text_fingerprint = sha256(extracted_text_user_input_bytes)`

This allows the system to distinguish:

- sealed packet correctness
- broker render correctness
- app-server observed input correctness

## Item Allowlist

`forbidden_tool_use` becomes an explicit item-type rule computed from observed thread items.

### Allowed In v1

- `userMessage`
- `agentMessage`

### Optional But Disabled By Default

- `reasoning`
- `plan`

### Forbidden In v1

- `commandExecution`
- `mcpToolCall`
- `dynamicToolCall`
- `collabToolCall`
- `webSearch`
- `imageView`
- any future item type not on the allowlist

`item_allowlist_valid` is computed from observed app-server item types, not inferred from output text.

## Certification Model

### v1 Technical Certification

`TECHNICAL_CERTIFIED` means all of the following are true:

- packet fingerprint matches
- profile hash matches
- policy hash matches
- exact turn input fingerprints were recorded
- app-server item events align with allowed types
- output schema is valid
- attestation is complete

### v2 Quality Status

`QUALITY_PASSED` is introduced later and is not part of the `v1` gate.

## Run Gate

`v1` uses strict mode.

If the user requested a persona, that persona must be `TECHNICAL_CERTIFIED`.

Run-level rule:

- all requested personas technically certified -> synthesis may start
- any requested persona not technically certified -> run fails closed

There is no:

- 80 percent threshold in `v1`
- `PARTIAL_PANEL` in `v1`
- quality gate in `v1`

## Reliability Policy

### v1

- no retry

### v1.1

- one infra retry is allowed
- retry is idempotent only
- retry must reuse the same sealed ticket, packet hash, profile hash, and policy hash
- retry must use a fresh thread

Infra retry applies only to transient infrastructure failures such as transport or upstream disconnects.

It does not apply to:

- schema failure
- item allowlist violation
- packet mismatch
- profile mismatch
- policy mismatch

## Logging And Audit

Early versions remain audit-heavy, but audit must be governed.

### Heavy Audit In Early Versions

`v1` through `v3` retain detailed operational evidence, including:

- sealed packets
- packet manifests
- dispatch tickets
- raw worker outputs
- app-server critical event snapshots
- synthesis inputs and raw outputs

### Audit Structure

```text
audit/
  events.jsonl
  run_summary.json
  diagnostic_bundle.json
```

### Event Rules

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
- relevant fingerprints
- thread and turn ids when applicable

Suggested stages:

- `run_started`
- `round_input_validated`
- `packet_prepared`
- `packet_sealed`
- `ticket_issued`
- `worker_dispatch_started`
- `worker_dispatched`
- `worker_result_received`
- `worker_schema_validated`
- `worker_technical_certified`
- `worker_failed`
- `synth_dispatch_started`
- `synth_result_received`
- `synth_certified`
- `run_completed`
- `run_failed`

### Governance Additions In v1.1

Heavy audit must be paired with:

- retention TTL
- redaction policy
- access scope and authorization rules
- export workflow
- delete workflow
- audit mode options such as `full`, `redacted`, or `metadata-only`

## File-Level Refactor

### Keep

- `plugins/worldview-panel-codex/runtime/personas/`
- `plugins/worldview-panel-codex/runtime/persona-index.json`
- `plugins/worldview-panel-codex/tools/persona_materials.py`

### Remove From Execution Path

- `plugins/worldview-panel-codex/tools/dispatch_packet_guard.py`
- `plugins/worldview-panel-codex/runtime/agents/*.toml`
- old prompt-level dispatch orchestration
- old natural-language subagent interface contracts

### Rewrite

- `plugins/worldview-panel-codex/skills/worldview-panel-entry/SKILL.md`
- `plugins/worldview-panel-codex/skills/worldview-panel-entry/agents/openai.yaml`
- `plugins/worldview-panel-codex/tools/context_packet_common.py`
- `plugins/worldview-panel-codex/tools/prepare_context_packets.py`
- logging helpers and log format

### New Entrypoints

- `plugins/worldview-panel-codex/tools/build_worldview_round.py`
- `plugins/worldview-panel-codex/tools/run_worldview_broker.py`
- `plugins/worldview-panel-codex/tools/synthesize_worldview_panel.py`
- `plugins/worldview-panel-codex/tools/verify_worldview_round.py`

### New Schemas

- `plugins/worldview-panel-codex/schemas/dispatch_job_v1.json`
- `plugins/worldview-panel-codex/schemas/dispatch_ticket_v1.json`
- `plugins/worldview-panel-codex/schemas/worldview_worker_result_v1.json`
- `plugins/worldview-panel-codex/schemas/attestation_v1.json`
- `plugins/worldview-panel-codex/schemas/technical_certified_result_v1.json`
- `plugins/worldview-panel-codex/schemas/audit_event_v1.json`

## Acceptance Criteria

### v1

- parent planner cannot submit raw worker input
- broker accepts tickets, not prompts
- worker identity is injected through rendered skill files
- every worker attempt uses a fresh thread
- steer, resume, rollback, compact, and review-mode continuation are blocked by policy
- attestation includes packet, turn-input, and observed user-text fingerprints
- worker item types outside allowlist fail certification
- synthesis starts only if every requested persona is technically certified

### v1.1

- one infra retry works without changing sealed artifacts
- effective requirements snapshot is recorded with attestation or run metadata
- audit TTL exists
- redaction policy exists
- access control policy exists

### v2

- quality status is computed separately from technical certification
- synthesis can consume quality metadata without replacing technical integrity as the root gate

## Locked Decisions

The following decisions are fixed for planning:

- production end-state uses app-server broker
- module boundaries are JSON-only
- worker identities are first-class
- runtime identity injection uses temporary skill files in `v1`
- exact turn-input attestation is mandatory
- every attempt uses a fresh thread
- `v1` uses strict all-required technical gate
- retry, data governance, and partial-panel semantics are deferred out of `v1`
- quality governance is deferred to `v2`
