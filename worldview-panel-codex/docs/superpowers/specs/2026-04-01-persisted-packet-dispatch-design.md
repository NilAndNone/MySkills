# Persisted Packet Dispatch Design

## Goal

Make `worldview-panel-codex` dispatch subagents through one strict final-hop path so the text actually sent is always the same text that was persisted in `packet.txt`.

After this change:

1. packet preparation may still build and persist complete artifacts as it does today
2. dispatch may only proceed through a guarded release step
3. the guarded release step must produce a `matched=true` result before any subagent send
4. if exact-match verification is missing or fails, the whole run is aborted with the fixed user-facing message `这次请求已作废，请重新发准备好的上下文。`

## Why This Exists

The current bundle already does the hard work of generating persona materials, assembling complete packets, validating them, and persisting them before dispatch. The failure happened after that point.

The root cause is not packet preparation. The root cause is that the last hop still allows this bad shape:

1. claim the persisted packet
2. rewrite or shorten the outgoing text manually
3. send the rewritten text without proving it still matches the persisted artifact

That leaves a gap between "prepared correctly" and "sent correctly".

This design closes that gap by turning dispatch into a release gate instead of a loose retrieval step.

## Scope

### In Scope

- harden the final dispatch path inside `worldview-panel-codex`
- remove the normal-path ambiguity between "claim packet" and "verify outgoing text"
- make `matched=true` the only success signal for a dispatchable packet
- keep exact-match evidence in logs
- align skill instructions, agent prompting, tool behavior, and self-test coverage

### Out of Scope

- changing packet assembly rules
- changing synthesis behavior
- changing persona selection or batch sizing
- introducing a generic framework for other skills
- adding retries, fallback dispatch, or partial dispatch

## Design Principles

1. Preparation success is necessary but not sufficient. A ready packet is not yet a sendable packet.
2. The persisted packet is the source of truth for subagent input.
3. The dispatch gate must make the correct path easier than the incorrect path.
4. Logs must distinguish "packet was claimed" from "packet was proven identical and released".
5. Failure is strict by design. If the system cannot prove equality, it must not send.

## Current Failure Mode

Today the packet flow has two separate concepts:

- preparation tools persist a complete `packet.txt`
- dispatch guard can either claim that packet or compare a candidate payload against it

That split leaves room for the parent thread to do the wrong thing:

1. use the guard only to retrieve the persisted packet
2. handwrite or shorten a new prompt elsewhere
3. send the rewritten prompt
4. leave behind logs that show only `dispatch packet claimed`

Those logs are not enough to prove that the real outgoing text matched the persisted artifact.

## Proposed Dispatch Flow

### 1. Preparation Stays As-Is

`prepare_context_packets.py` remains responsible for:

- normalizing the round input
- building one complete packet per persona
- validating every packet
- persisting `packet.txt`, `packet.json`, and `validation.json`
- marking the round as ready or blocked

This design does not move any packet-building logic into dispatch.

### 2. Dispatch Guard Becomes the Only Release Path

`dispatch_packet_guard.py` stops being described as a loose "claim or verify" helper and becomes the standard release gate for dispatch.

The intended parent flow becomes:

1. point the guard at a persisted round root and persona
2. have the guard create an outgoing copy from the persisted `packet.txt`
3. have the guard verify that outgoing copy against the persisted packet immediately
4. only use the released outgoing copy for subagent dispatch
5. require `matched=true` before sending anything

The parent must not treat a plain packet claim as sufficient evidence anymore.

### 3. One Legal Success State

The only state that counts as a legal dispatch success is:

- `dispatch_ready=true`
- `matched=true`

Anything else is a blocked dispatch, including:

- packet exists but was only claimed
- candidate text was never verified
- candidate text differs by even one character
- packet was ready during preparation but later could not be matched during release

### 4. Outgoing Copy Instead of Freehand Rewrite

The release step produces a deterministic outgoing copy from the persisted packet. That outgoing copy is what the parent should hand to the subagent.

This removes the normal-path need for the parent to:

- reassemble text manually
- shorten the packet for convenience
- restate instructions from memory
- mix retrieved packet text with extra handwritten glue

If a caller wants to send something else, that is not a legal dispatch path.

## Tool Contract Changes

### `context_packet_common.py`

Add one shared release-path helper that:

- loads the persisted packet for a persona
- writes a deterministic outgoing copy
- verifies the outgoing copy against the persisted packet
- returns packet path, outgoing path, lengths, fingerprints, and `matched`

This keeps the release logic in one place rather than splitting it across CLI wrappers.

### `dispatch_packet_guard.py`

Reframe this CLI around a release gate.

It should support two clear modes:

1. release mode
   - produce the outgoing copy from the persisted packet
   - verify it immediately
   - return the outgoing path plus exact-match evidence
2. verification mode
   - compare a caller-provided candidate file against the persisted packet
   - fail if they differ

Release mode becomes the documented and recommended normal path. Verification mode remains available for explicit checks and tests.

The old "claim only" success path must no longer be documented as enough for dispatch.

## Logging Contract

Dispatch logs must now prove release, not just retrieval.

For each persona release attempt, the log should include:

- persona
- packet path
- outgoing path when available
- expected length
- actual length
- expected fingerprint
- actual fingerprint
- `matched=true` or `matched=false`

Operational interpretation changes as follows:

- `dispatch packet claimed` is not a compliant dispatch event
- `matched=true` is the required evidence that the outgoing text was the persisted text
- if logs do not show `matched=true`, the run must be treated as non-compliant

## Failure Handling

Failure handling is intentionally strict.

If the release step cannot produce `matched=true` for any persona in the batch:

1. do not send that persona
2. do not continue the round
3. surface the fixed user-facing message `这次请求已作废，请重新发准备好的上下文。`
4. leave enough log detail to show which persona failed and how the lengths or fingerprints differed

There is no fallback mode such as:

- "send the persisted packet anyway without verification"
- "warn in logs but keep going"
- "retry with a shorter rewritten packet"

## Documentation Changes

The following sources must describe the same final-hop rule:

- `src/skills/worldview-panel-codex/SKILL.md`
- `src/skills/worldview-panel-codex/agents/openai.yaml`
- `src/skills/worldview-context-prep/SKILL.md`
- `docs/DEVELOPER_SELFTEST.md`
- `docs/DEVELOPER_MAINTENANCE.md`
- `docs/USER_GUIDE.md`

The documentation should be explicit about this distinction:

- `ready=true` means the packet bundle was prepared and persisted correctly
- `matched=true` means the exact outgoing text has been proven identical and is therefore sendable

## Testing Strategy

### Unit-Level

- release helper writes an outgoing copy identical to the persisted packet
- exact-match verification succeeds for the untouched outgoing copy
- exact-match verification fails when the outgoing copy is shortened or edited
- failure returns the fixed abort message

### CLI-Level

- `dispatch_packet_guard.py` release mode returns an outgoing path and `matched=true`
- explicit verification mode returns `matched=false` for a modified candidate file
- logs record expected and actual lengths on mismatch

### Documentation and Prompting Consistency

- tests should continue checking that skill text and agent prompt both require exact-match verification
- self-test commands should demonstrate both the happy path and a forced mismatch
- maintenance docs should no longer describe a claim-only flow as dispatch-complete

## Acceptance Criteria

- a normal dispatch path can produce a released outgoing copy and a `matched=true` record for each persona
- a modified outgoing text is rejected before any send occurs
- the fixed abort message is used whenever release verification fails
- packet preparation behavior remains unchanged and still persists complete artifacts
- logs clearly distinguish release success from simple packet retrieval
- skill rules, prompting, and self-test docs all describe the same strict flow

## Assumptions

- the parent thread still controls the actual subagent send step outside these local tools
- exact string equality is the correct rule for this skill; semantic equivalence is not enough
- keeping a separate outgoing copy is acceptable because it makes the release path auditable
