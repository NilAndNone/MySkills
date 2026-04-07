# Worldview Panel Plugin Removal Design

Date: 2026-04-07
Status: Draft for review
Scope: remove `plugins/worldview-panel-codex/` by migrating all remaining workspace dependencies into workspace-owned modules and assets

## TL;DR

The workspace product path must become fully self-owned.

The final state is:

- the only supported run entrypoint is `scripts/run_worldview_panel.py`
- the only supported verification entrypoint is `scripts/verify_worldview_panel_round.py`
- the workspace no longer imports, loads, or reads anything from `plugins/worldview-panel-codex/`
- all still-needed runtime foundations are migrated into workspace-owned modules and assets
- the entire `plugins/worldview-panel-codex/` directory can be deleted

This is not a plugin cleanup.

This is a full de-pluginization of the worldview panel workspace path.

The migration must follow one hard rule:

**replace first, switch references second, delete last**

## Problem Statement

The current repository already has a workspace-owned product path, but it is not actually independent.

Today, the supported workspace path still relies on plugin-owned modules and assets for critical runtime behavior:

- app-server transport loading
- JSON contract helpers and fingerprints
- worker identity rendering
- attestation payload generation
- persona material assembly
- worker output schemas
- raw persona runtime assets

As long as those dependencies remain, the plugin is still part of the supported workspace mainline, even if users are told not to run the plugin entrypoints directly.

That creates three problems:

1. the product boundary remains conceptually split
2. the workspace cannot honestly claim a single self-owned execution path
3. deleting the plugin directory would break the supported path immediately

The user requirement for this design is stricter than “de-prioritize the plugin” or “keep the plugin but mark it unsupported.”

The required end state is:

**migrate everything the supported workspace path still needs into workspace-owned code and assets, then delete the plugin directory entirely.**

## Goals

- Make the workspace fully independent from `plugins/worldview-panel-codex/`.
- Preserve the current workspace product semantics while removing plugin dependencies.
- Keep a single supported user-facing path:
  - `scripts/run_worldview_panel.py`
  - `scripts/verify_worldview_panel_round.py`
- Move all runtime foundations still required by the workspace into workspace-owned modules and assets.
- Remove plugin installation, plugin documentation, plugin entrypoints, and plugin tests from the repository.
- Ensure repository readers no longer infer that there are two supported ways to run worldview panel.

## Non-Goals

- This design does not preserve plugin installability.
- This design does not preserve plugin-specific entrypoints or compatibility behavior.
- This design does not attempt to keep plugin packaging files, plugin user guides, or plugin lifecycle scripts.
- This design does not widen product scope beyond the current workspace worldview panel path.
- This design does not redesign persona content, role planning strategy, or content brief semantics during the migration.

## Final Boundary

After the migration completes, the repository boundary is:

### Supported Runtime Surface

- `scripts/run_worldview_panel.py`
- `scripts/verify_worldview_panel_round.py`
- `worldview_runtime_adapter/*`

### Workspace-Owned Foundations

The workspace owns:

- transport connection code
- contract helpers and hash utilities
- worker identity rendering
- attestation generation
- persona material loading and packet assembly
- worker output schemas
- persona runtime assets
- verification logic
- all user-facing workspace documentation

### Removed Surface

The repository no longer contains:

- `plugins/worldview-panel-codex/`
- plugin install/uninstall scripts
- plugin-specific user documentation
- plugin-specific AGENTS instructions
- plugin-specific tests
- plugin entrypoints such as broker, synthesis, or plugin verifier flows

### Architectural Consequence

`plugin_bridge.py` cannot remain as a bridge to plugin-owned paths.

By the end of the migration, either:

- it is deleted completely, or
- it is replaced by an internal workspace loader with no plugin path semantics

The preferred outcome is deletion, because any remaining “bridge” naming keeps the old mental model alive.

## Current Workspace Dependencies On Plugin Code

The supported workspace path currently depends on plugin-owned code in these ways:

### Direct Module Loading

- `worldview_runtime_adapter/cli.py` loads `worldview_app_server`
- `worldview_runtime_adapter/schema_preflight.py` loads contract helpers through `plugin_bridge`
- `worldview_runtime_adapter/persona_runtime.py` loads worker schema through `plugin_bridge`
- `worldview_runtime_adapter/panel_runtime.py` loads contract and attestation helpers through `plugin_bridge`
- `worldview_runtime_adapter/round_artifacts.py` loads:
  - contracts
  - persona materials
  - identity helpers

### Direct Schema Dependency

The workspace still reads plugin-owned schema files for worker output validation.

### Direct Runtime Asset Dependency

The workspace still depends on plugin-owned persona runtime assets:

- `runtime/persona-index.json`
- `runtime/personas/**`

This means plugin removal cannot happen until all three dependency classes are migrated.

## Migration Inventory

The migration inventory is split into three buckets.

### Bucket A: Must Migrate Into Workspace

These are still needed by the supported workspace path and must be rehomed before plugin deletion.

#### Runtime Helper Modules

- `plugins/worldview-panel-codex/tools/worldview_app_server.py`
  - new home: `worldview_runtime_adapter/app_server.py`

- `plugins/worldview-panel-codex/tools/worldview_contracts.py`
  - new home: `worldview_runtime_adapter/contracts.py`

- `plugins/worldview-panel-codex/tools/worldview_identity.py`
  - new home: `worldview_runtime_adapter/identity.py`

- `plugins/worldview-panel-codex/tools/worldview_attestation.py`
  - new home: `worldview_runtime_adapter/attestation.py`

- `plugins/worldview-panel-codex/tools/persona_materials.py`
  - new home: `worldview_runtime_adapter/persona_materials.py`

#### Schemas

- `plugins/worldview-panel-codex/schemas/worldview_worker_result_v1.json`
  - new home: `worldview_runtime_adapter/schemas/worldview_worker_result_v1.json`

- any additional schema file still referenced by the workspace test and runtime path
  - new home: `worldview_runtime_adapter/schemas/`

#### Persona Runtime Assets

- `plugins/worldview-panel-codex/runtime/persona-index.json`
- `plugins/worldview-panel-codex/runtime/personas/**`

New home:

- `worldview_runtime_adapter/runtime_assets/persona-index.json`
- `worldview_runtime_adapter/runtime_assets/personas/**`

### Bucket B: Do Not Migrate, Remove Instead

These are plugin-path entrypoints or plugin-owned workflow shells that conflict with the single-entrypoint requirement and should not be carried into the workspace.

- `plugins/worldview-panel-codex/tools/build_worldview_round.py`
- `plugins/worldview-panel-codex/tools/run_worldview_broker.py`
- `plugins/worldview-panel-codex/tools/synthesize_worldview_panel.py`
- `plugins/worldview-panel-codex/tools/verify_worldview_round.py`
- `plugins/worldview-panel-codex/tools/worldview_broker.py`
- `plugins/worldview-panel-codex/tools/worldview_round_builder.py`
- `plugins/worldview-panel-codex/tools/worldview_synthesis.py`
- `plugins/worldview-panel-codex/tools/worldview_governance.py`
- `plugins/worldview-panel-codex/tools/worldview_audit.py`
- plugin logging helpers that only exist to support the removed plugin flow

The workspace mainline already has its own run and verify path.

Carrying these forward would recreate the two-path problem under a new directory layout.

### Bucket C: Packaging And Narrative Layer To Remove

These files exist because the plugin exists as a plugin, not because the workspace product path needs them.

- `plugins/worldview-panel-codex/.codex-plugin/plugin.json`
- `plugins/worldview-panel-codex/scripts/install_local_plugin.py`
- `plugins/worldview-panel-codex/scripts/uninstall_local_plugin.py`
- `plugins/worldview-panel-codex/docs/user/USER_GUIDE.md`
- `plugins/worldview-panel-codex/docs/user/USER_PROMPTS.md`
- `plugins/worldview-panel-codex/docs/user/USER_PERSONAS.md`
- `plugins/worldview-panel-codex/AGENTS.md`
- plugin layout and install tests

## Target Workspace Layout

After migration, the workspace should own a coherent internal layout such as:

```text
worldview_runtime_adapter/
  app_server.py
  attestation.py
  contracts.py
  identity.py
  persona_materials.py
  schemas/
    worldview_worker_result_v1.json
  runtime_assets/
    persona-index.json
    personas/
      ...
  cli.py
  composer.py
  intake.py
  panel_runtime.py
  persona_runtime.py
  review_viewer.py
  role_planner.py
  round_artifacts.py
  schema_preflight.py
  surfaces.py
  verifier.py
scripts/
  run_worldview_panel.py
  verify_worldview_panel_round.py
docs/
  worldview_panel_workspace_usage.md
```

This keeps every workspace-owned dependency visible under one runtime namespace.

## Migration Phases

The migration uses five phases.

### Phase 1: Freeze Deletion Scope And Dependency Inventory

Purpose:

- lock the intended end state
- enumerate every current plugin dependency before any code movement

Required outcomes:

- a complete inventory of workspace calls into plugin code
- a complete inventory of plugin-owned assets still required by the workspace
- a file list of plugin-owned surfaces that will be removed without migration

Acceptance criteria:

- no hidden workspace dependency on plugin code remains unidentified

### Phase 2: Migrate Workspace Foundations Without Switching Call Sites Yet

Purpose:

- copy or rehome the required foundations into workspace-owned modules and assets
- keep behavior functionally equivalent during migration

Required outcomes:

- workspace-owned `app_server.py`
- workspace-owned `contracts.py`
- workspace-owned `identity.py`
- workspace-owned `attestation.py`
- workspace-owned `persona_materials.py`
- workspace-owned schemas
- workspace-owned persona runtime assets

Implementation rule:

- preserve behavior before improving structure
- do not mix “behavioral redesign” into the migration of low-level helpers

Acceptance criteria:

- every required helper and asset exists in the workspace-owned location
- migration has not yet deleted plugin references prematurely

### Phase 3: Switch The Supported Workspace Path To Workspace-Owned Foundations

Purpose:

- cut the supported path away from plugin-owned files

Required call-site updates:

- `worldview_runtime_adapter/cli.py`
- `worldview_runtime_adapter/schema_preflight.py`
- `worldview_runtime_adapter/persona_runtime.py`
- `worldview_runtime_adapter/panel_runtime.py`
- `worldview_runtime_adapter/round_artifacts.py`
- any tests still loading plugin-owned schemas or helpers

Required outcomes:

- no supported runtime path imports plugin-owned modules
- no supported runtime path reads plugin-owned schemas
- no supported runtime path reads plugin-owned runtime assets

Acceptance criteria:

- searching the workspace runtime path shows no references to `plugins/worldview-panel-codex`
- the supported path still runs successfully

### Phase 4: Remove Plugin Packaging, Plugin Workflow, And Plugin Directory

Purpose:

- remove the old shape completely once the workspace no longer depends on it

Required outcomes:

- delete plugin user guides
- delete plugin install scripts
- delete plugin packaging metadata
- delete plugin workflow entrypoints
- delete plugin tests
- delete the `plugins/worldview-panel-codex/` directory

Acceptance criteria:

- the directory no longer exists
- no repository docs or scripts still refer users to plugin entrypoints as valid usage

### Phase 5: Final Cleanup And Acceptance Validation

Purpose:

- make sure the repository now communicates and behaves as a single-path workspace product

Required outcomes:

- remove or rename `plugin_bridge.py`
- update remaining docs to remove plugin-era mental models
- confirm the repository presents only one supported worldview panel path

Acceptance criteria:

- only workspace-owned run and verify entrypoints remain
- no plugin path survives in supported docs, tests, or runtime code

## Why The Order Matters

The order is not optional.

If the plugin directory is removed before migration and call-site cutover are complete, the supported workspace path will fail immediately.

The order must remain:

1. replace foundations
2. switch references
3. delete plugin

This sequencing is the main risk-control mechanism for the entire change.

## Risks

### Risk 1: Persona Content Drift

Migrating persona assets may accidentally change the effective runtime material and alter output quality or tone.

Mitigation:

- migrate assets verbatim first
- treat content changes as out of scope for this removal

### Risk 2: Helper Behavior Drift

Low-level helpers such as contracts, attestation, or identity rendering may change behavior while being moved.

Mitigation:

- preserve functional equivalence first
- keep tests focused on behavior parity during migration

### Risk 3: Hidden Plugin Dependency

A call site or test may still load plugin-owned content after most of the migration is done.

Mitigation:

- perform explicit repository-wide searches for plugin path references
- treat any remaining hit in supported runtime paths as a release blocker

### Risk 4: Narrative Residue

Even after code migration, old docs or tests may still teach users that the plugin path is valid.

Mitigation:

- include docs and repository wording in acceptance criteria
- treat lingering user-facing plugin guidance as an unfinished migration

## Verification Strategy

Each migration phase must be validated separately.

### Layer 1: Supported Path Validation

Confirm that:

- `scripts/run_worldview_panel.py` still runs a round
- `scripts/verify_worldview_panel_round.py` still validates the round

### Layer 2: Result Integrity Validation

Confirm that the supported path still produces expected outcome classes and product artifacts:

- `usable`
- `degraded`
- `blocked`
- `content_brief.json`
- `studio_surface.json`
- `audit_surface.json`

### Layer 3: Residual Path Validation

Confirm that the repository no longer presents a second path by checking:

- runtime imports
- test references
- documentation references
- scripts

### Final Validation Question

The migration is complete only if the answer is yes to this question:

**After deleting `plugins/worldview-panel-codex/`, can the repository still run and verify worldview panel through the supported workspace path, with no remaining ambiguity about a second supported entrypoint?**

## Acceptance Criteria

This design is complete only when all of the following are true:

- the workspace no longer imports from `plugins/worldview-panel-codex/`
- the workspace no longer reads schemas from `plugins/worldview-panel-codex/`
- the workspace no longer reads persona assets from `plugins/worldview-panel-codex/`
- `scripts/run_worldview_panel.py` remains the single supported runtime entrypoint
- `scripts/verify_worldview_panel_round.py` remains the single supported verification entrypoint
- `plugin_bridge.py` is removed or no longer carries plugin path semantics
- plugin user docs, install scripts, and plugin tests are removed
- `plugins/worldview-panel-codex/` is deleted
- the supported tests still pass after plugin deletion
- repository readers can no longer reasonably infer that there are two supported worldview panel paths

## Recommendation

Proceed with a staged de-pluginization plan, not a big-bang delete.

The required end state is total plugin removal, but the safe path is still phased:

1. freeze dependency inventory
2. migrate foundations into workspace-owned modules and assets
3. switch workspace call sites
4. delete plugin directory and plugin narrative
5. run final cleanup and acceptance validation

This matches the user requirement exactly while minimizing the chance of breaking the supported path mid-migration.
