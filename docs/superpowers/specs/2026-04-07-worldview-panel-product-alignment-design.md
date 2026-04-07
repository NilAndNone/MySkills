# Worldview Panel Product Alignment Design

Date: 2026-04-07
Status: Ready for review
Scope: full workspace-owned alignment to `docs/worldview_panel_product_reframe_v2.md`

## TL;DR

This design moves the worldview panel product path fully into the workspace-owned runtime adapter.

The adapter becomes the single owner of:

1. product intake
2. role-based panel planning
3. runtime orchestration
4. content composition into `content_brief_v1`
5. Studio and Audit presentation surfaces
6. verification of product artifacts

The plugin remains read-only and is treated as a runtime kernel plus artifact helper source, not as the product layer.

The primary output of a successful run is no longer `final_panel.json` or `final_panel.md`.

The primary outputs become:

- `content_brief.json`
- `studio_surface.json`
- `audit_surface.json`

The workspace entrypoint remains `scripts/run_worldview_panel.py`.

## Problem Framing

`docs/worldview_panel_product_reframe_v2.md` changes the product center of gravity:

- the product is a multi-perspective content workbench
- the first wedge is controversy-comment briefing generation
- Studio and Audit are presentation surfaces, not runtime modes
- execution policy, result grade, and presentation surface must be independent axes
- the system must first produce a canonical content object
- role-based planning replaces fixed persona-roster-first execution

The current repository state is not fully aligned with that direction:

- product semantics still enter through plugin-owned round building
- new composition logic is currently placed in plugin code
- verification still assumes plugin-owned synthesis artifacts
- the adapter still emits the older synthesis set on its main path
- the review viewer is still centered on persona-by-persona debugging instead of Studio-first consumption

This design closes that gap by making the adapter the product path and reducing the plugin to a read-only runtime dependency.

## Product Positioning

### External Positioning

The external product positioning is fixed as:

`多视角内容工作台`

The external promise is fixed as:

`把复杂争议议题拆成可判断、可表达、可继续创作的高质量内容 briefing。`

The product is not positioned externally as a multi-persona runner, persona chat tool, or roleplay system.

### Internal Method

Internally, the system still uses worldview panel as the method.

This means:

- internally, the method can still be described as worldview panel
- externally, the product is sold as multi-perspective compression and content generation
- personas and roles remain an internal means, not the user-facing value proposition

## Alignment Requirements

These requirements are direct consequences of the product reframe and are non-negotiable in this design.

### Adapter Owns Product Semantics

The adapter, not the plugin, owns:

- parsing the product input contract
- normalizing the content task brief
- choosing the minimum sufficient role set
- deciding whether a result is usable, degraded, or blocked
- generating the canonical content object
- generating Studio and Audit surfaces

### Plugin Remains Read-Only

The adapter must not require edits under:

- `plugins/worldview-panel-codex/tools/`
- `plugins/worldview-panel-codex/schemas/`
- `plugins/worldview-panel-codex/skills/`
- `plugins/worldview-panel-codex/tests/`

The adapter may read plugin helpers and artifacts, but the product refactor cannot depend on plugin edits.

### Canonical Content Object Comes First

Before any page or viewer is considered complete, the run must produce `content_brief_v1`.

Studio consumes it.
Audit references it.
Other exports may derive from it later.

### Presentation Surface, Execution Policy, And Result Grade Stay Separate

The adapter must model three distinct axes:

- `presentation_surface`: `studio | audit`
- `execution_policy`: `strict | adaptive`
- `result_grade`: `usable | degraded | blocked`

No surface name may imply a runtime mode.
No runtime mode may imply a surface.

### Benchmark, Rubric, And Guardrails Are First-Class Inputs

The adapter must freeze and carry forward:

- benchmark topic set
- quality rubric
- product guardrails

These are not passive documentation. They are part of the adapter-owned product contract and testing baseline.

## First Wedge

The first wedge is fixed as:

`争议议题评论 briefing 生成器`

The first target users are fixed as:

- self-media authors
- knowledge-oriented writers
- research-oriented content creators
- people who need a comment frame quickly before writing or recording

The first release default output includes:

- one-line judgment
- fact / value / strategy axis consensus and disagreement
- strongest opposing point and minority reminder
- longform writing structure
- video or spoken-script entry angle
- next materials to gather

The first release explicitly does not prioritize:

- general chat product behavior
- high-risk decision advice products
- team alignment tools
- broad support for every real-time or high-compliance topic

## Approaches Considered

### Approach A: Keep Product Intake In Plugin And Only Move Composition

Pros:

- smallest code movement
- reuses current builder path

Cons:

- plugin still owns product semantics
- conflicts with the workspace-owned routing requirement
- leaves role planning outside the adapter
- does not fully align with the product reframe

Decision: rejected.

### Approach B: Adapter Calls Plugin Product Logic

Pros:

- lowest short-term implementation cost
- reuses current synthesis work

Cons:

- product layer still lives in read-only plugin code
- keeps the wrong ownership boundary
- makes future product iteration depend on plugin patches

Decision: rejected.

### Approach C: Full Workspace-Owned Product Path

Pros:

- fully matches the product reframe
- keeps plugin read-only
- makes ownership explicit and testable
- allows the adapter to become the only supported workspace entrypoint

Cons:

- larger initial migration
- requires moving build, compose, surface, and verify semantics into the adapter

Decision: recommended.

## Design Objectives

- Make `scripts/run_worldview_panel.py` the only supported workspace run path.
- Move product intake and role planning into the adapter.
- Produce `content_brief_v1` as the canonical content object for every usable or degraded run.
- Make Studio the default consumption surface.
- Keep Audit focused on evidence, failures, and review.
- Remove old synthesis artifacts from the definition of completion.
- Fix the four review findings in the new adapter-owned composer path.
- Keep the plugin read-only.

## Non-Goals

- No attempt to rewrite plugin source files.
- No attempt to preserve the old persona-debug viewer as the primary UI.
- No attempt to keep `final_panel.*` as the primary product artifact.
- No attempt to generalize beyond the initial controversy-comment briefing wedge.
- No attempt to solve unrelated plugin historical compatibility issues in this spec.
- No attempt to make “24 personas” the main product story.
- No attempt to prioritize medical, legal, financial, or strong real-time political verification use cases in this wedge.

## Product Contract

The adapter intake contract follows the product reframe.

Required fields:

- `issue`
- `output_intent`
- `stance_mode`

Optional fields:

- `audience`
- `materials`
- `scope`
- `timeframe`
- `constraints`

The adapter normalizes these into a product-owned brief object with frozen benchmark, rubric, and guardrail metadata.

The normalized brief is the product entry object, not a runtime ticket.

Its responsibilities are:

- represent the user task in product language
- freeze benchmark, rubric, and guardrail context
- give the planner and composer a stable content task object

Legacy `question` and `answer_goal` inputs are a repository migration concern only.
If supported during migration, they must be normalized immediately into the product contract and must not remain the main semantic path.

## Proposed Workspace Layout

The adapter becomes the product owner under workspace code.

Proposed files:

- `worldview_runtime_adapter/intake.py`
- `worldview_runtime_adapter/role_planner.py`
- `worldview_runtime_adapter/round_artifacts.py`
- `worldview_runtime_adapter/panel_runtime.py`
- `worldview_runtime_adapter/composer.py`
- `worldview_runtime_adapter/surfaces.py`
- `worldview_runtime_adapter/verification.py`
- `worldview_runtime_adapter/review_viewer.py`
- `worldview_runtime_adapter/benchmark.py`
- `worldview_runtime_adapter/claim_model.py`
- `worldview_runtime_adapter/cli.py`
- `scripts/run_worldview_panel.py`

Existing adapter modules may absorb some of these responsibilities if a smaller file count stays clear, but the ownership boundaries above must remain explicit.

## Module Responsibilities

### `intake.py`

Responsibilities:

- parse the product contract
- normalize legacy compatibility input into product input
- attach frozen benchmark, rubric, and guardrail metadata
- reject unsupported issue types and malformed materials

Forbidden:

- no runtime dispatch
- no synthesis
- no surface rendering

### `role_planner.py`

Responsibilities:

- choose the minimum sufficient role set
- map roles to personas only as an internal runtime implementation detail
- follow the product rule of minimum sufficient coverage before expansion
- expand only for clear scope, material, or disagreement needs

Forbidden:

- no fixed roster as the default product behavior

### Role Planning Principles

The planner follows two fixed principles from the product reframe.

#### Minimum Sufficient Coverage

This is the repository expression of `最小充分覆盖`.

The planner must first cover the minimal set of roles needed to represent the issue well enough for the first wedge.

It should not optimize for persona count.
It should optimize for viewpoint coverage.

#### Disagreement-Driven Expansion

This is the repository expression of `分歧驱动扩展`.

The planner may expand the role set only when:

- disagreement is still unclear
- a blind spot is obvious
- user materials introduce unresolved tension
- scope or timeframe requires another structural lens

Expansion is driven by disagreement and coverage gaps, not by a default desire to fill a roster.

### `round_artifacts.py`

Responsibilities:

- write adapter-owned round input and plan artifacts
- prepare runtime packets and tickets needed by the read-only kernel path
- preserve identity and governance fingerprints where needed

This module replaces plugin-owned round-building as the workspace product path.

### `panel_runtime.py`

Responsibilities:

- orchestrate per-role execution
- record runtime evidence
- classify execution policy and run health
- continue per-role retries and degraded completion behavior
- call the composer automatically before returning a successful or degraded run

The runtime path must no longer require a separate manual synthesis step for the workspace-owned flow.

### `composer.py`

Responsibilities:

- build `content_brief_v1`
- generate claim-level evidence links
- compute one-line judgment and recommendations honestly
- classify axis content into consensus, conflicts, and minority alerts
- generate writing assets

This module fixes the review findings by design:

- majority buckets stay in `consensus`
- only true ties or unresolved splits become `conflicts`
- headline selection must not fall back to role order
- recommendation evidence includes only actually supporting roles

### `surfaces.py`

Responsibilities:

- build `studio_surface_v1`
- build `audit_surface_v1`
- keep surface language separate from runtime language
- map `result_grade` to product-facing Studio labels

Studio labels:

- `可用`
- `可用但降级`
- `本轮不建议使用`

Audit labels stay runtime-facing, for example:

- `strict fail closed`
- `adaptive degraded`
- `quorum passed`
- `quorum failed`
- `certification incomplete`

### Studio Default Structure

Studio is organized in this order:

1. Executive Judgment
2. Tension Map
3. Perspective Cards
4. Creation Layer
5. Expandable Trace

Each section carries the same meaning as the product reframe:

- Executive Judgment gives the quick answer, premises, largest risk, and best use
- Tension Map shows fact, value, and strategy consensus / disagreement / minority signal
- Perspective Cards are support material, not the main stage
- Creation Layer gives writing and recording assets
- Expandable Trace exposes claim-level evidence and role contribution on demand

### Audit Focus

Audit is responsible for:

- showing what happened in the run
- showing which roles succeeded and failed
- showing failure types
- showing which claims are weak
- helping decide whether the result should be reused or rerun

### `verification.py`

Responsibilities:

- verify adapter-owned runtime evidence
- verify canonical content object presence
- verify Studio and Audit surface presence
- verify claim trace references point back to available role results
- verify blocked runs expose explicit failure summaries instead of pretending to be successful

The verifier must no longer define success by the presence of `final_panel.*`.

### `review_viewer.py`

Responsibilities:

- default to Studio
- allow switching to Audit
- show persona-level details only as an Audit subview
- show blocked and degraded states in the new product language

The viewer is no longer a persona-debug-first screen.

## Artifact Model

### Primary Artifacts

The primary artifacts for a usable or degraded run are:

- `content_brief.json`
- `studio_surface.json`
- `audit_surface.json`

### Secondary Runtime Artifacts

Runtime evidence still includes:

- per-role result records
- attestations
- runtime summaries
- failure summaries
- audit events

### Deprecated Product Artifacts

`final_panel.json` and `final_panel.md` are no longer product-defining artifacts.

The adapter-owned main path does not write them.
They must not be part of the completion criteria, verification contract, or viewer default path.

## Runtime Flow

The supported workspace flow becomes:

1. `scripts/run_worldview_panel.py` receives product input.
2. `intake.py` normalizes it into the product brief.
3. `role_planner.py` chooses the minimum role set.
4. `round_artifacts.py` prepares runtime artifacts for the read-only kernel path.
5. `panel_runtime.py` executes each role with retries and runtime evidence capture.
6. `composer.py` builds `content_brief_v1` from certified role results.
7. `surfaces.py` builds Studio and Audit surfaces.
8. `verification.py` verifies the adapter-owned run.
9. `review_viewer.py` consumes Studio by default and links to Audit.

There is no separate product-facing call to plugin synthesis or plugin verify in the workspace-owned path.

## Composition Rules

### Axis Classification

For each axis:

- if there is only one surviving view, it is `consensus`
- if one group is larger than the rest, that dominant group is still `consensus`
- smaller but meaningful dissent becomes `minority_alerts`
- only unresolved ties or genuinely co-dominant splits become `conflicts`

This matches the product meaning of the Stage 7 tension map.

### One-Line Judgment

The composer may emit a single headline only when the role outputs support a dominant judgment.

When the top judgment is tied or cannot be compressed honestly:

- the headline must become an explicit unresolved or qualified statement
- `recommended_angle` must follow the same unresolved output

The composer must never choose a winner by role order.

### Recommendation Claims

Recommendation claims must include:

- only supporting roles in `supporting_roles`
- only supporting source refs in `source_refs`
- confidence derived only from those supporting roles
- opposing or dissenting roles in `counter_roles` when applicable

This keeps claim-level traceability honest in Audit.

## Result Grade Rules

The adapter computes `result_grade` independently from surface and execution policy.

### `usable`

Use when:

- enough roles succeeded
- evidence is sufficient to form a reliable content object
- Studio can recommend the result without a downgrade banner

### `degraded`

Use when:

- some roles failed or evidence is weaker
- the remaining successful roles still support an honest content object
- Studio must present the result as usable with downgrade language

### `blocked`

Use when:

- the run does not meet the minimum completion threshold
- or the successful evidence is too weak to support a valid `content_brief_v1`

Blocked runs must produce a failure summary and Audit-facing explanation.
They must not pretend to be successful Studio outputs.

## Benchmark, Rubric, And Guardrails

The adapter freezes the initial benchmark and quality rubric from the product reframe.

### Benchmark Set

The initial benchmark set is constrained to representative controversy topics in these categories:

- technology and platform issues
- business model and industry judgment
- social and cultural controversy
- media and public-opinion controversy

It is intentionally narrow rather than broad.

### Quality Rubric

The fixed rubric dimensions are:

- Coverage
- Compression
- Conflict Clarity
- Minority Signal
- Traceability
- Creatability
- Usefulness

### Guardrails

The adapter carries these concrete product guardrails:

- `支持的问题类型` / supported issue types
- `不支持的问题类型` / unsupported issue types
- `支持的材料形式` / supported material forms
- `默认时效要求` / default freshness requirement
- `证据不足时如何降级表达` / insufficient-evidence downgrade rule

The initial values are fixed as:

- supported issue types:
  - technology and platform issues
  - business model and industry judgment
  - social and cultural controversy
  - media and public-opinion controversy
- unsupported issue types:
  - medical advice
  - legal advice
  - financial investment advice
  - strongly real-time sensitive political verification
- supported material forms:
  - article excerpts
  - screenshot text
  - user notes
  - quote bundles
- default freshness requirement:
  - non-realtime
- insufficient-evidence downgrade rule:
  - explicitly downgrade the framing and preserve research gaps

These values must be available in the adapter-owned content task brief and must be test-visible.

## Verification Contract

A run is complete only when the adapter can verify:

- runtime evidence exists for attempted roles
- successful roles have certified results
- blocked runs have explicit failure summaries
- usable or degraded runs have `content_brief.json`
- usable or degraded runs have `studio_surface.json`
- usable or degraded runs have `audit_surface.json`
- claim trace references resolve to available role evidence

Legacy `final_panel.*` presence is not part of the completion contract.

## Viewer Contract

The review viewer changes from a persona-debug shell into a product result viewer.

Default behavior:

- open Studio first
- show Executive Judgment, Tension Map, Perspective Cards, Creation Layer, and Expandable Trace

Audit behavior:

- show execution policy
- show result grade
- show role success and failure
- show claims needing review
- allow drill-down into role evidence and raw runtime records

Persona-by-persona packet inspection becomes an Audit drill-down, not the top-level page structure.

## Recommended Delivery Order

The repository implementation order follows the product reframe:

1. freeze benchmark, rubric, and guardrails
2. freeze product positioning and user promise
3. freeze the product input contract
4. implement `content_brief_v1` and claim model
5. implement role planning and composer
6. implement Studio and Audit surfaces
7. only then clean up remaining internal naming and compatibility leftovers

This sequence matters because the product model must constrain the implementation, not the other way around.

## Testing Strategy

The implementation must add or update tests for:

1. adapter end-to-end runs emitting the three primary product artifacts
2. verification passing on the adapter-owned flow without a separate plugin synthesis step
3. majority-vs-minority axis classification
4. tie handling for one-line judgment and recommendation angle
5. recommendation claim evidence only including supporting roles
6. degraded runs producing Studio and Audit surfaces with downgrade semantics when still valid
7. blocked runs producing failure summaries without fake successful Studio output
8. review viewer defaulting to Studio and exposing Audit as a secondary surface
9. benchmark, rubric, and guardrail metadata being present in adapter-owned artifacts

## Completion Criteria

This work is complete only when all of the following are true:

- the workspace entrypoint runs through the adapter-owned product path
- the adapter owns product intake and role planning
- the adapter produces `content_brief.json`, `studio_surface.json`, and `audit_surface.json`
- Studio is the default viewer surface
- Audit is the review and evidence surface
- verification keys off the new artifact contract
- the four review findings are fixed and covered by tests
- old `final_panel.*` artifacts are no longer part of the product completion definition

## Open Decision Resolved By This Spec

This spec makes one explicit repository-level decision:

The worldview panel product path is owned by the workspace adapter end to end.

The plugin remains a read-only runtime dependency.
It is not the home of future product semantics.

## Repository Migration Decisions

The following are repository migration choices, not product-level promises from the reframe document:

- whether legacy `question` / `answer_goal` intake is temporarily accepted at the adapter boundary
- whether any legacy compatibility artifacts are emitted outside the adapter-owned main path

These decisions exist only to help repository migration and must not redefine the product contract.
