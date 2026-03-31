# Subagent Context Packet Design

## Goal

Make the parent thread prepare subagent context through one fixed pipeline instead of ad hoc prompt assembly.

Before any batch dispatch, the parent must:

1. normalize the round input
2. build one complete packet per subagent
3. validate every packet
4. persist every packet and validation result to a temporary round directory
5. release the batch only if every packet is ready

The design is intentionally limited to pre-dispatch preparation. It does not change synthesis, retry behavior, or advanced dispatch policy.

## Why This Exists

The current bundle already has strong packet rules and a material generator, but most parent-side preparation is still enforced by instructions and tests rather than one explicit assembly pipeline. This design closes that gap.

The main outcomes are:

- every subagent receives a predictable packet
- missing materials or ambiguous references are blocked before dispatch
- each round leaves behind enough artifacts to explain what each subagent actually saw

## Scope

### In Scope

- define one canonical parent-side packet contract
- generate one complete packet per selected subagent
- treat external user-provided material as a first-class packet section
- validate packet completeness and contamination rules
- write per-subagent artifacts to a temporary round directory before dispatch
- expose a batch-ready / batch-blocked result to the upstream dispatcher
- add deterministic tests for packet assembly, validation, and round persistence

### Out of Scope

- automatic summarization or truncation of long external material
- retry logic
- partial batch dispatch when one packet fails
- synthesis changes
- long-term archive or replay system beyond temporary round artifacts

## Design Principles

1. Parent does the preparation work. Subagents stay packet-only.
2. The final packet sent to subagents remains text-first and human-readable.
3. Parent internals use a structured packet shape so assembly and validation can be deterministic.
4. External material defaults to full text, not summary.
5. Deterministic, low-risk cleanup is allowed; semantic rewriting is not.
6. A batch is only dispatchable when every selected subagent packet is prepared, validated, and persisted.

## Packet Shape

The parent prepares a structured packet for each subagent and then renders it into the final text packet.

Each packet contains these sections in this order:

1. Task instructions
2. Persona foundation material
3. Current domain material
4. External material

### Task Instructions

This section contains:

- task
- normalized user question
- answer goal
- hard constraints
- allowed assumptions
- forbidden actions
- output format contract

Reference expansion applies to all of the above, not only the user question. Shorthand like "this", "that", "the above", "that plan", or unlabeled aliases must be expanded before validation passes.

### Persona Foundation Material

This section comes from the existing persona material source and includes the persona profile block plus the full psychology material.

### Current Domain Material

This section comes from the existing domain material source. For `other`, the packet explicitly marks that there is no fixed domain file.

### External Material

External material is a first-class packet section.

- default policy is full text, not summary
- if there are multiple materials, each appears as its own labeled segment
- each segment must carry a clear title and source label
- if title or source is unavailable, use the placeholder `用户粘贴内容`
- external material appears after task instructions and persona/domain material so the packet keeps a clear primary line

## Parent Pipeline

### 1. Input Normalization

The parent collects:

- the round question
- explicit constraints
- selected subagents
- domain and answer goal
- external materials

Then it expands references and fills deterministic placeholders where allowed, such as `用户粘贴内容`.

This stage may do low-risk cleanup only:

- whitespace cleanup
- section title normalization
- default placeholder injection for missing title/source

It must not do semantic work such as:

- summarizing material
- trimming long material automatically
- deciding what evidence matters
- rewriting complex meaning on the user's behalf

### 2. Per-Subagent Assembly

For each selected subagent, the parent builds one complete packet by combining:

- normalized task instructions
- persona foundation material
- current domain material
- shared external material blocks

Each subagent gets its own complete packet. The parent may reuse shared intermediate data internally, but the observable output is always one standalone final packet per subagent.

### 3. Validation

Validation is performed per packet.

Hard failures include:

- missing required sections
- missing persona foundation material
- missing current domain material when one is required
- unresolved references in task instructions, constraints, or external material references
- parent synthesis leaking into the packet
- another persona's answer leaking into the packet

Advisory or normalization-level issues remain separate from hard failures so failure reasons stay clear.

### 4. Temporary Persistence

Before dispatch, every packet is written to a temporary round directory.

The design uses one round directory per run, and one subagent subdirectory per packet.

Each subagent subdirectory stores exactly three artifacts:

- the final rendered packet text
- the structured source packet
- the validation result

The round directory also stores one round manifest describing:

- round question
- selected subagents
- readiness state per subagent
- overall batch readiness

Successful runs are still retained by default for inspection and debugging.

### 5. Batch Gate

The batch gate checks whether every selected subagent packet is:

- assembled
- validated successfully
- persisted successfully

If any one packet fails, the batch is blocked. There is no partial dispatch in this design.

## Failure Model

Failure handling is intentionally strict:

- one failed packet blocks the whole batch
- failed packets are still persisted
- failure output must be explicit enough for the parent to repair and rerun
- no automatic retry or fallback summarization

This design assumes packet failure should be rare once assembly is template-driven, but it still treats failure as a first-class state instead of an impossible case.

## Interfaces

The design introduces three parent-side outputs:

1. structured packet payload per subagent
2. rendered final text packet per subagent
3. machine-readable validation result per subagent

The upstream dispatcher should consume only packets marked ready by the batch gate. It should not rebuild packet logic on the side.

The subagent-facing output contract does not change in this phase.

## Testing Strategy

### Unit-Level

- input normalization expands required references
- missing title/source becomes `用户粘贴内容`
- external material segments preserve per-material boundaries and labels
- `other` domain is represented correctly

### Packet-Level

- deterministic packet rendering for the same input
- required section ordering is stable
- persona material and domain material appear in the correct place
- external material full text is preserved
- contamination by parent synthesis or other persona content is rejected

### Round-Level

- one round directory is created per run
- one subagent directory is created per selected subagent
- each subagent directory contains the three required artifacts
- the round manifest reflects per-subagent readiness and overall batch readiness
- a single failed packet keeps the whole batch blocked

## Acceptance Criteria

- repeated runs with identical input produce identical packet text
- all selected subagents have fully prepared artifacts before dispatch begins
- batch dispatch is blocked when any packet fails validation or persistence
- successful runs are still inspectable through the temporary round directory
- documentation, validation rules, and tests all describe the same packet requirements

## Assumptions

- this is limited to `worldview-panel-codex`
- the current persona/domain material source remains authoritative
- external material is important enough to preserve in full by default
- token overflow is treated as a separate later problem, not solved in this phase
