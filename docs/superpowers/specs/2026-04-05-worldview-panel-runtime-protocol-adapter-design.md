# Worldview Panel Runtime Protocol Adapter Design

Date: 2026-04-05
Status: Ready for review
Scope: workspace-owned runtime adapter around `plugins/worldview-panel-codex`

## TL;DR

This design adds a runtime-only compatibility and retry layer outside the plugin.

The plugin stays read-only. We do not patch:

- `plugins/worldview-panel-codex/tools/`
- `plugins/worldview-panel-codex/schemas/`
- `plugins/worldview-panel-codex/tests/`

Instead, we add a workspace-owned adapter that:

1. builds rounds with the existing plugin builder
2. loads plugin artifacts and schema definitions
3. rewrites request-side protocol details in memory before `turn/start`
4. retries each persona up to 3 times based on concrete error reasons
5. records per-persona success or failure without killing the whole run
6. emits a degraded final panel only when successful personas reach the configured ratio threshold

The initial threshold is `67%`.

The initial retry budget is `3` per persona.

Only actual turn re-submissions consume retry budget. Local deterministic request shaping does not.

## Problem Framing

The incident on 2026-04-05 showed a real contract gap between the plugin's declared worker output schema and the currently accepted `codex app-server` structured output contract.

The strict plugin broker fails closed on the first persona because:

- it sends the plugin schema as-is
- the app-server rejects that schema before the worker completes
- the broker is strict-all-required and aborts the entire run

The user requirements for the new runtime are different from both the current plugin behavior and the earlier governance repair:

- do not modify plugin code
- do not modify plugin schemas
- do not do live code patches during a run
- repair both protocol-side and output-side errors at runtime
- retry each persona independently
- failed personas must not poison the whole run
- failed personas must still appear in the final panel as explicit failures
- synthesis must happen only if the success ratio threshold is met

This means the workspace needs a new orchestration layer, not a plugin patch.

## Fixed Constraints

These constraints are non-negotiable in this design.

### Plugin Is Read-Only

During runtime and during implementation of this feature, the adapter must not require edits under:

- `plugins/worldview-panel-codex/tools/`
- `plugins/worldview-panel-codex/schemas/`
- `plugins/worldview-panel-codex/skills/`
- `plugins/worldview-panel-codex/tests/`

The adapter may read from those paths, import those modules, and reuse their artifacts, but it must not depend on modifying them.

### Runtime Repair Is In-Memory Only

Runtime repair may:

- reshape outgoing `output_schema`
- reshape outgoing request parameters
- add structured repair instructions for a retry turn
- map known runtime identity values into the expected canonical form

Runtime repair may not:

- edit repo files
- rewrite plugin artifacts on disk
- change the installed plugin copy
- generate new ad hoc plugin source files under the plugin tree

### Retry Scope

Retry budget is per persona, not per run.

Each persona gets:

- one initial attempt
- up to three repair attempts

Only a new worker turn submission consumes one retry slot.

### Degraded Completion Semantics

If at least one persona succeeds, the run status is `completed_with_failures`.

Failed personas:

- remain visible in the final output as explicit failed slots
- do not participate in synthesis, cross-judgment, or main recommendation logic

Final synthesis is allowed only if successful personas are at least `67%` of the requested total.

Below that threshold, the runtime returns a failure summary instead of a synthesized panel.

## Approaches Considered

### Approach A: Patch The Plugin Broker

This would modify:

- `run_worldview_broker.py`
- `worldview_broker.py`
- `worldview_app_server.py`
- plugin schemas and tests

Pros:

- shortest path if plugin edits were allowed
- keeps one canonical broker path

Cons:

- directly violates the read-only constraint
- repeats the same governance risk the user rejected
- couples runtime behavior changes to plugin source changes

Decision: rejected.

### Approach B: Monkeypatch Plugin Internals At Process Start

This would import plugin modules and monkeypatch private functions in memory before dispatch.

Pros:

- avoids on-disk plugin edits
- can reuse more of the existing plugin broker path

Cons:

- fragile against private function changes
- hard to audit
- hard to test cleanly
- still inherits the plugin broker's strict all-or-nothing flow

Decision: rejected as too brittle.

### Approach C: External Runtime Adapter And Orchestrator

This adds a workspace-owned adapter that treats the plugin as a read-only artifact source.

Pros:

- satisfies the read-only constraint
- makes repair policy explicit and testable
- supports per-persona retry and degraded completion without mutating the plugin
- keeps protocol adaptation separate from plugin source of truth

Cons:

- duplicates part of broker orchestration outside the plugin
- requires a new synthesis path for degraded runs

Decision: recommended.

## Design Objectives

- Keep the plugin read-only.
- Guarantee app-server protocol compatibility before `turn/start`.
- Handle protocol-side and result-side validation failures with targeted retries.
- Keep retry accounting per persona.
- Preserve strict evidence for which personas succeeded and which failed.
- Produce a degraded but honest final panel only when the success ratio threshold is met.
- Keep initial implementation narrow and testable.

## Non-Goals

- No attempt to rewrite plugin schemas on disk.
- No attempt to make the plugin's own `run_worldview_broker.py` support degraded mode.
- No attempt to teach the adapter arbitrary schema inference from unknown object shapes.
- No partial weighting of failed personas in synthesis.
- No silent fallback to unstructured freeform output.

## Proposed Runtime Layout

The new code lives outside the plugin in a workspace-owned package and a small CLI wrapper.

Proposed file layout:

- `worldview_runtime_adapter/__init__.py`
- `worldview_runtime_adapter/plugin_bridge.py`
- `worldview_runtime_adapter/schema_preflight.py`
- `worldview_runtime_adapter/persona_runtime.py`
- `worldview_runtime_adapter/panel_runtime.py`
- `worldview_runtime_adapter/failure_summary.py`
- `scripts/run_worldview_panel_runtime.py`
- `tests/worldview_runtime_adapter/test_schema_preflight.py`
- `tests/worldview_runtime_adapter/test_persona_runtime.py`
- `tests/worldview_runtime_adapter/test_panel_runtime.py`

This keeps all new behavior outside the plugin while still allowing direct reuse of plugin helpers.

## Module Responsibilities

### `plugin_bridge.py`

Responsibilities:

- locate the installed plugin root
- import plugin helpers from read-only code
- call the existing round builder
- load plugin round artifacts such as tickets, profiles, packets, and manifests
- call existing plugin audit and attestation helpers where safe to reuse

Forbidden:

- mutating plugin source files
- writing new files into the plugin tree

### `schema_preflight.py`

Responsibilities:

- load the plugin-declared output schema version
- build a runtime-safe app-server schema in memory
- apply schema overlays for known schema versions
- validate the outgoing schema before turn submission
- emit structured repair reasons when the schema still cannot be adapted safely

This is the main protection against the specific `invalid_json_schema` class of failure.

### `persona_runtime.py`

Responsibilities:

- execute one persona end-to-end
- keep per-persona retry count
- classify failures into protocol-side vs result-side
- build retry prompts from concrete error reasons
- return one of:
  - `certified_success`
  - `failed_after_retries`
  - `fatal_runtime_error`

### `panel_runtime.py`

Responsibilities:

- iterate all personas from the plugin-generated round
- run each persona independently
- aggregate success and failure records
- compute success ratio
- decide whether synthesis is allowed
- generate final panel payload or failure summary
- write workspace-owned runtime summary artifacts under the round root

### `failure_summary.py`

Responsibilities:

- render a human-readable summary when the success ratio threshold is not met
- include persona-level failure reasons
- avoid pretending that a degraded run is a full certified panel

## Runtime Data Flow

The new execution path is:

1. Use the read-only plugin builder to create a sealed round.
2. Load `dispatch_job.json` and the per-persona artifacts.
3. For each persona:
   - verify packet, ticket, and identity using plugin data
   - construct runtime input items
   - build a runtime-safe `output_schema`
   - submit the turn
   - validate the resulting JSON payload
   - if validation fails, derive a targeted repair and retry
   - after success, write workspace-owned result status for that persona
4. After all personas:
   - compute success ratio
   - if ratio >= `67%`, generate degraded final panel from successful personas plus failed placeholders
   - otherwise generate failure summary only
5. Write a workspace-owned run summary artifact.

The adapter does not depend on plugin-side degraded synthesis support.

## Schema Preflight Design

### Why Preflight Exists

The plugin schema is a source artifact, not guaranteed runtime truth.

The adapter must produce runtime truth that is acceptable to the current app-server contract.

### Runtime Schema Overlay

The adapter maintains a small overlay registry keyed by `worker_schema_version`.

For `worldview_worker_result_v1`, the initial overlay explicitly tightens the schema in memory:

- root object gets `additionalProperties: false`
- `judgment` becomes an explicit object
- `judgment.properties` includes:
  - `factual`
  - `value`
  - `strategy`
- `judgment.required` includes those keys
- `judgment.additionalProperties` becomes `false`

This overlay is not a plugin patch. It is a runtime adapter contract.

### Preflight Output

`schema_preflight.py` returns:

- `effective_schema`
- `repair_notes`
- `schema_fingerprint`
- `status`

Status values:

- `ready`
- `repaired_in_memory`
- `unrepairable`

Local preflight repair does not consume retry budget by itself. Retry budget is consumed only by a new turn submission.

### Preflight Guardrail

The adapter must not invent unknown nested fields. It may only apply overlays for schema versions with explicitly defined runtime mappings.

If a future schema version appears without an overlay and cannot pass raw preflight, the persona fails with a clear unsupported-schema reason.

## Persona Retry Design

### Failure Classes

Each failed attempt is classified as one of:

- `protocol_schema_error`
- `protocol_request_error`
- `result_schema_error`
- `result_persona_mismatch`
- `transport_error`
- `unsupported_runtime_contract`

### Repair Rules

For `protocol_schema_error`:

- inspect the error details
- adjust outgoing request shape in memory
- retry with a fresh turn

For `result_schema_error`:

- convert validator output into a compact repair instruction
- retry with a fresh turn

For `result_persona_mismatch`:

- inject explicit canonical persona slug reminder
- retry with a fresh turn

For `transport_error`:

- allow retry only when the error is transient
- permanent transport configuration failures short-circuit the persona

### Retry Budget

Per persona:

- `attempt_index = 0` is the initial turn
- `attempt_index = 1..3` are repair turns

The adapter stops after attempt `3` fails.

### Retry Evidence

For every attempt, the runtime summary stores:

- persona
- attempt index
- error class or success
- repair reason
- effective schema fingerprint

## Success, Failure, And Certification Semantics

### Persona Success

A persona is successful only when:

- the turn completes
- the final payload parses as JSON
- the payload passes the runtime validator
- the persona identity matches the requested persona

The initial implementation may mark this as adapter-certified rather than plugin `TECHNICAL_CERTIFIED`, because the plugin's own certification path stays untouched.

### Persona Failure

A persona is failed when:

- three repair turns are exhausted
- the schema is unsupported by the runtime adapter
- a permanent protocol failure remains after targeted repair

The persona still appears in final output as:

- `status = failed`
- `failure_class`
- `failure_reason`

### Run Status

Run-level status values:

- `failed`
- `completed_with_failures`
- `completed`

Rules:

- `failed`: zero successful personas
- `completed_with_failures`: at least one success and at least one failure
- `completed`: all personas succeed

## Synthesis Design

Because the plugin synthesizer is strict-all-required, the adapter cannot reuse it unchanged for degraded runs.

The adapter therefore provides a workspace-owned degraded synthesizer with these rules:

- only successful personas contribute to cross-judgment
- failed personas are rendered as explicit failure slots
- final main recommendation uses only successful personas
- the output must state the success ratio and failed persona count

Required sections:

- `TL;DR`
- `Run status`
- `Successful persona count`
- `Failed persona count`
- `Persona panel`
- `Cross-judgment`
- `Main recommendation`
- `Failed persona appendix`

If success ratio is below `67%`, the adapter does not synthesize those sections and returns a failure summary instead.

## Artifacts

The adapter writes new workspace-owned artifacts under the round root without mutating plugin artifacts.

Proposed paths:

- `<round_root>/runtime_adapter/run_summary.json`
- `<round_root>/runtime_adapter/personas/<persona>.json`
- `<round_root>/runtime_adapter/final_panel.json`
- `<round_root>/runtime_adapter/failure_summary.json`

These artifacts are additive and do not replace plugin files.

## Error Handling

### Unsupported Schema Version

If the plugin declares an unknown `worker_schema_version` and no overlay exists:

- mark the persona as failed
- include `unsupported_runtime_contract`
- continue the rest of the run

### App-Server Rejects Repaired Schema

If the app-server still rejects the repaired schema:

- capture the raw error message
- derive the next repair only if the error is concretely actionable
- otherwise fail that persona early instead of blind retries

### Low Success Ratio

If successful personas are below `67%`:

- skip final synthesis
- emit failure summary
- mark run as `failed` if no successful persona exists
- otherwise mark run as `completed_with_failures` with `panel_emitted = false`

## Testing Strategy

### Unit Tests

`test_schema_preflight.py`

- raw plugin schema is read
- runtime overlay produces `additionalProperties: false`
- `judgment` is expanded into explicit properties
- unknown schema version fails cleanly

`test_persona_runtime.py`

- protocol schema error triggers targeted retry
- result schema error triggers targeted retry
- local deterministic reshaping does not consume retry budget
- three failed retries end in persona failure
- persona mismatch is retried and then either succeeds or fails cleanly

`test_panel_runtime.py`

- one persona failure does not abort the rest
- failed personas stay in the final panel as placeholders
- failed personas do not contribute to synthesis
- success ratio threshold gates final panel emission
- all-success run is marked `completed`
- mixed run above threshold is marked `completed_with_failures`

### Fixture Strategy

Tests should use workspace-owned scripted transports and fixture outputs rather than editing plugin fixtures in place.

### Manual Verification

Initial manual check should prove:

1. the adapter can build a round using the plugin builder
2. the adapter repairs the outgoing schema in memory
3. the app-server accepts the repaired request shape
4. failed personas do not abort the entire run
5. threshold logic works at `67%`

## Implementation Phases

### Phase 1: Runtime Skeleton

- create the external package and CLI wrapper
- bridge into the read-only plugin builder and artifact loaders

### Phase 2: Schema Preflight

- implement overlay-backed runtime schema shaping
- add schema unit tests

### Phase 3: Persona Runtime

- implement retry controller
- classify protocol-side and result-side failures
- add per-persona tests

### Phase 4: Degraded Panel Runtime

- implement run aggregation
- implement threshold gate
- implement degraded synthesis and failure summary

## Open Questions Closed By This Design

These design decisions are already fixed and should not be re-litigated during implementation:

- plugin code stays read-only
- plugin schema files stay read-only
- both protocol-side and result-side failures are repairable at runtime
- retry budget is per persona
- retry budget is `3`
- failed personas remain visible in the final output
- failed personas do not participate in synthesis
- final panel requires `67%` successful personas
- only real turn re-submissions consume retry budget

## Recommendation

Implement Approach C as a workspace-owned runtime adapter.

It is the only option that satisfies the user's hard constraint that the plugin must not be modified while still making the protocol contract acceptable to the current app-server and enabling degraded multi-persona completion.
