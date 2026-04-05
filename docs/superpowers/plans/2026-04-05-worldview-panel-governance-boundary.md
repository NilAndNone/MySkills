# Worldview Panel Governance Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a sealed governance boundary that invalidates active worldview panel runs when topology, audit authority, or protected repo baseline drift.

**Architecture:** Reuse the current broker-v1 artifact pipeline and add two new artifacts, `governance_seal.json` and `governance_status.json`. Builder seals topology, protected files, and emitter authority; broker, audit writers, synthesis, and verify all enforce that contract and fail closed on violations.

**Tech Stack:** Python 3 CLIs, JSON artifacts, unittest/pytest, filesystem round artifacts, existing worldview broker runtime

---

## File Map

### Create

- `plugins/worldview-panel-codex/tools/worldview_governance.py`
- `plugins/worldview-panel-codex/tests/test_worldview_governance.py`

### Modify

- `plugins/worldview-panel-codex/tools/worldview_round_builder.py`
- `plugins/worldview-panel-codex/tools/worldview_contracts.py`
- `plugins/worldview-panel-codex/tools/worldview_audit.py`
- `plugins/worldview-panel-codex/tools/write_run_log.py`
- `plugins/worldview-panel-codex/tools/run_log.py`
- `plugins/worldview-panel-codex/tools/worldview_broker.py`
- `plugins/worldview-panel-codex/tools/worldview_synthesis.py`
- `plugins/worldview-panel-codex/tools/verify_worldview_round.py`
- `plugins/worldview-panel-codex/schemas/audit_event_v1.json`
- `plugins/worldview-panel-codex/tests/test_build_worldview_round.py`
- `plugins/worldview-panel-codex/tests/test_worldview_audit.py`
- `plugins/worldview-panel-codex/tests/test_run_worldview_broker.py`
- `plugins/worldview-panel-codex/tests/test_synthesize_worldview_panel.py`
- `plugins/worldview-panel-codex/tests/test_verify_worldview_round.py`
- `plugins/worldview-panel-codex/tests/test_worldview_contracts.py`

## Task 1: Seal Governance Metadata At Build Time

**Files:**
- Create: `plugins/worldview-panel-codex/tools/worldview_governance.py`
- Modify: `plugins/worldview-panel-codex/tools/worldview_round_builder.py`
- Modify: `plugins/worldview-panel-codex/tools/worldview_contracts.py`
- Modify: `plugins/worldview-panel-codex/tests/test_build_worldview_round.py`
- Test: `plugins/worldview-panel-codex/tests/test_worldview_governance.py`

- [ ] **Step 1: Write failing tests for governance artifacts**

```python
def test_build_round_writes_governance_artifacts(self) -> None:
    round_root = module.build_round_from_input(FIXTURE_PATH, output_root=Path(tmpdir))
    self.assertTrue((round_root / "governance_seal.json").is_file())
    self.assertTrue((round_root / "governance_status.json").is_file())

def test_governance_seal_tracks_dispatch_and_manifest_fingerprints(self) -> None:
    seal = json.loads((round_root / "governance_seal.json").read_text(encoding="utf-8"))
    self.assertIn("topology", seal)
    self.assertIn("dispatch_job_fingerprint", seal["topology"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_build_worldview_round.py plugins/worldview-panel-codex/tests/test_worldview_governance.py -q`
Expected: FAIL because governance artifacts and helpers do not exist yet.

- [ ] **Step 3: Implement minimal governance sealing**

```python
def build_governance_seal(*, round_root: Path, dispatch_job: dict[str, Any], round_manifest: dict[str, Any], protected_repo_files: dict[str, str]) -> dict[str, Any]:
    return {
        "schema_version": "governance_seal_v1",
        "run_id": round_manifest["run_id"],
        "round_root": str(round_root.resolve()),
        "state": "SEALED",
        "topology": {
            "dispatch_job_fingerprint": sha256_prefixed(canonical_json_bytes(dispatch_job)),
            "round_manifest_fingerprint": sha256_prefixed(canonical_json_bytes(round_manifest)),
        },
        "protected_repo_files": protected_repo_files,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_build_worldview_round.py plugins/worldview-panel-codex/tests/test_worldview_governance.py -q`
Expected: PASS

## Task 2: Fail Closed On Topology Drift And Protected Repo Drift

**Files:**
- Modify: `plugins/worldview-panel-codex/tools/worldview_broker.py`
- Modify: `plugins/worldview-panel-codex/tools/worldview_governance.py`
- Modify: `plugins/worldview-panel-codex/tests/test_run_worldview_broker.py`

- [ ] **Step 1: Write failing broker governance tests**

```python
def test_run_worldview_broker_invalidates_round_when_extra_dispatch_job_exists(self) -> None:
    (round_root / "dispatch_job.techno_only.json").write_text("{}", encoding="utf-8")
    with self.assertRaisesRegex(ValueError, "governance violation"):
        broker.run_broker(dispatch_job_path, app_server_client=fixture_client)

def test_run_worldview_broker_invalidates_round_when_protected_repo_file_drifts(self) -> None:
    broker_path.write_text(broker_path.read_text(encoding="utf-8") + "# drift\n", encoding="utf-8")
    with self.assertRaisesRegex(ValueError, "protected repo drift"):
        broker.run_broker(dispatch_job_path, app_server_client=fixture_client)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_run_worldview_broker.py -q`
Expected: FAIL because broker does not precheck governance or write invalid status yet.

- [ ] **Step 3: Implement governance precheck and invalidation**

```python
precheck_governance(round_root=round_root, dispatch_job_path=Path(dispatch_job_path))
mark_governance_state(round_root, state="ACTIVE_DISPATCH", updated_by_component="broker")
...
except GovernanceViolation as exc:
    invalidate_round(round_root, violation_type=exc.violation_type, message=str(exc), updated_by_component="broker")
    raise ValueError(f"governance violation: {exc}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_run_worldview_broker.py -q`
Expected: PASS

## Task 3: Enforce Audit Emitter Authority

**Files:**
- Modify: `plugins/worldview-panel-codex/tools/worldview_audit.py`
- Modify: `plugins/worldview-panel-codex/tools/write_run_log.py`
- Modify: `plugins/worldview-panel-codex/tools/run_log.py`
- Modify: `plugins/worldview-panel-codex/schemas/audit_event_v1.json`
- Modify: `plugins/worldview-panel-codex/tests/test_worldview_audit.py`

- [ ] **Step 1: Write failing audit authority tests**

```python
def test_write_run_log_cli_rejects_unauthorized_top_level_emitter(self) -> None:
    proc = subprocess.run([... "--emitter", "manual_backfill"], ...)
    self.assertNotEqual(proc.returncode, 0)

def test_write_audit_event_persists_source_identity(self) -> None:
    event = audit.write_audit_event(..., emitter="broker", source_process="pytest", source_session_id="sess-1", synthetic=False)
    self.assertEqual(event["emitter"], "broker")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_worldview_audit.py -q`
Expected: FAIL because source identity fields and emitter checks do not exist yet.

- [ ] **Step 3: Implement source identity and authority checks**

```python
if governance_round_root is not None:
    validate_audit_authority(
        round_root=governance_round_root,
        emitter=emitter,
        stage=stage,
        synthetic=synthetic,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_worldview_audit.py -q`
Expected: PASS

## Task 4: Gate Synthesis And Verification On Governance Status

**Files:**
- Modify: `plugins/worldview-panel-codex/tools/worldview_synthesis.py`
- Modify: `plugins/worldview-panel-codex/tools/verify_worldview_round.py`
- Modify: `plugins/worldview-panel-codex/tests/test_synthesize_worldview_panel.py`
- Modify: `plugins/worldview-panel-codex/tests/test_verify_worldview_round.py`

- [ ] **Step 1: Write failing synthesis and verify tests**

```python
def test_synthesis_refuses_invalid_round(self) -> None:
    invalidate_round(round_root, violation_type="unauthorized_emitter", message="bad top-level write", updated_by_component="test")
    with self.assertRaisesRegex(ValueError, "round is INVALID"):
        synthesis.synthesize_round(round_root)

def test_verify_round_reports_invalid_status_and_violations(self) -> None:
    invalidate_round(round_root, violation_type="topology_drift", message="extra dispatch job", updated_by_component="test")
    report = verifier.verify_round(round_root)
    self.assertEqual(report["status"], "invalid")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_synthesize_worldview_panel.py plugins/worldview-panel-codex/tests/test_verify_worldview_round.py -q`
Expected: FAIL because synthesis and verify ignore governance status today.

- [ ] **Step 3: Implement terminal governance gating**

```python
status = load_governance_status(root)
if status["state"] == "INVALID":
    raise ValueError("round is INVALID")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_synthesize_worldview_panel.py plugins/worldview-panel-codex/tests/test_verify_worldview_round.py -q`
Expected: PASS

## Task 5: Run Focused And Full Verification

**Files:**
- Modify: `plugins/worldview-panel-codex/tests/...` as needed from previous tasks

- [ ] **Step 1: Run the focused worldview test suite**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_build_worldview_round.py plugins/worldview-panel-codex/tests/test_worldview_governance.py plugins/worldview-panel-codex/tests/test_worldview_audit.py plugins/worldview-panel-codex/tests/test_run_worldview_broker.py plugins/worldview-panel-codex/tests/test_synthesize_worldview_panel.py plugins/worldview-panel-codex/tests/test_verify_worldview_round.py -q`
Expected: PASS

- [ ] **Step 2: Run the full plugin test suite**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests -q`
Expected: PASS

- [ ] **Step 3: Commit the governance boundary implementation**

```bash
git add docs/superpowers/plans/2026-04-05-worldview-panel-governance-boundary.md \
  plugins/worldview-panel-codex/tools/worldview_governance.py \
  plugins/worldview-panel-codex/tools/worldview_round_builder.py \
  plugins/worldview-panel-codex/tools/worldview_contracts.py \
  plugins/worldview-panel-codex/tools/worldview_audit.py \
  plugins/worldview-panel-codex/tools/write_run_log.py \
  plugins/worldview-panel-codex/tools/run_log.py \
  plugins/worldview-panel-codex/tools/worldview_broker.py \
  plugins/worldview-panel-codex/tools/worldview_synthesis.py \
  plugins/worldview-panel-codex/tools/verify_worldview_round.py \
  plugins/worldview-panel-codex/schemas/audit_event_v1.json \
  plugins/worldview-panel-codex/tests/test_build_worldview_round.py \
  plugins/worldview-panel-codex/tests/test_worldview_governance.py \
  plugins/worldview-panel-codex/tests/test_worldview_audit.py \
  plugins/worldview-panel-codex/tests/test_run_worldview_broker.py \
  plugins/worldview-panel-codex/tests/test_synthesize_worldview_panel.py \
  plugins/worldview-panel-codex/tests/test_verify_worldview_round.py
git commit -m "feat: enforce worldview governance boundaries"
```
