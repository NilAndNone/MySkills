# Worldview Panel Broker v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the legacy parent-controlled worldview panel dispatch path with a strict `v1` app-server broker that proves exact worker turn input and blocks all legacy prompt-side dispatch.

**Architecture:** `v1` lands only the authority-boundary fix. Build round artifacts and temporary persona skill carriers up front, dispatch workers by sealed ticket through a broker-owned app-server client, certify only technical integrity, and synthesize only when every requested persona is technically certified. `v1.1` retry/governance work and `v2` quality judging are explicitly out of scope for this plan.

**Tech Stack:** Python 3 CLIs, JSON schema artifacts, unittest/pytest, filesystem round artifacts, Codex app-server JSON-RPC over WebSocket, local transport adapter tests

---

## Scope Guard

This plan implements `v1` only:

- in scope: build, seal, identity carrier rendering, fresh-thread broker dispatch, exact input attestation, strict technical certification, strict synthesis gate, audit-heavy evidence
- out of scope: infra retry, TTL/redaction/access control enforcement, partial panels, quality judge, quality scoring

Future work requires separate plans:

- `v1.1`: retry and audit governance
- `v2`: quality governance

Transport assumption for this plan:

- real broker transport is WebSocket JSON-RPC to `codex app-server --listen ws://127.0.0.1:8787`
- `turn/start` is asynchronous and must be followed by `turn/completed` plus `thread/read includeTurns=true`
- no task in this plan may reintroduce a fake REST `POST /thread/start` or `POST /turn/start` model

## File Map

### Create

- `plugins/worldview-panel-codex/schemas/dispatch_job_v1.json`
- `plugins/worldview-panel-codex/schemas/dispatch_ticket_v1.json`
- `plugins/worldview-panel-codex/schemas/worldview_worker_result_v1.json`
- `plugins/worldview-panel-codex/schemas/attestation_v1.json`
- `plugins/worldview-panel-codex/schemas/technical_certified_result_v1.json`
- `plugins/worldview-panel-codex/schemas/audit_event_v1.json`
- `plugins/worldview-panel-codex/tools/worldview_contracts.py`
- `plugins/worldview-panel-codex/tools/worldview_identity.py`
- `plugins/worldview-panel-codex/tools/worldview_round_builder.py`
- `plugins/worldview-panel-codex/tools/worldview_audit.py`
- `plugins/worldview-panel-codex/tools/worldview_attestation.py`
- `plugins/worldview-panel-codex/tools/worldview_app_server.py`
- `plugins/worldview-panel-codex/tools/worldview_broker.py`
- `plugins/worldview-panel-codex/tools/worldview_synthesis.py`
- `plugins/worldview-panel-codex/tools/build_worldview_round.py`
- `plugins/worldview-panel-codex/tools/run_worldview_broker.py`
- `plugins/worldview-panel-codex/tools/synthesize_worldview_panel.py`
- `plugins/worldview-panel-codex/tools/verify_worldview_round.py`
- `plugins/worldview-panel-codex/tests/test_worldview_contracts.py`
- `plugins/worldview-panel-codex/tests/test_worldview_identity.py`
- `plugins/worldview-panel-codex/tests/test_build_worldview_round.py`
- `plugins/worldview-panel-codex/tests/test_worldview_audit.py`
- `plugins/worldview-panel-codex/tests/test_worldview_app_server.py`
- `plugins/worldview-panel-codex/tests/test_run_worldview_broker.py`
- `plugins/worldview-panel-codex/tests/test_synthesize_worldview_panel.py`
- `plugins/worldview-panel-codex/tests/test_verify_worldview_round.py`
- `plugins/worldview-panel-codex/tests/fixtures/broker/worker_turn_items.json`
- `plugins/worldview-panel-codex/tests/fixtures/broker/disallowed_item_turn_items.json`

### Modify

- `plugins/worldview-panel-codex/.codex-plugin/plugin.json`
- `plugins/worldview-panel-codex/AGENTS.md`
- `plugins/worldview-panel-codex/scripts/install_local_plugin.py`
- `plugins/worldview-panel-codex/scripts/uninstall_local_plugin.py`
- `plugins/worldview-panel-codex/skills/worldview-panel-entry/SKILL.md`
- `plugins/worldview-panel-codex/skills/worldview-panel-entry/agents/openai.yaml`
- `plugins/worldview-panel-codex/skills/worldview-context-prep/SKILL.md`
- `plugins/worldview-panel-codex/skills/worldview-panel-logging/SKILL.md`
- `plugins/worldview-panel-codex/tools/persona_materials.py`
- `plugins/worldview-panel-codex/tools/run_log.py`
- `plugins/worldview-panel-codex/tools/write_run_log.py`
- `plugins/worldview-panel-codex/tests/test_plugin_layout.py`
- `plugins/worldview-panel-codex/tests/test_local_plugin_install.py`
- `plugins/worldview-panel-codex/docs/developer/DEVELOPER_MAINTENANCE.md`
- `plugins/worldview-panel-codex/docs/developer/DEVELOPER_SELFTEST.md`
- `plugins/worldview-panel-codex/docs/user/USER_GUIDE.md`
- `plugins/worldview-panel-codex/docs/user/USER_PROMPTS.md`

### Delete

- `plugins/worldview-panel-codex/tools/dispatch_packet_guard.py`
- `plugins/worldview-panel-codex/tools/context_packet_common.py`
- `plugins/worldview-panel-codex/tools/prepare_context_packets.py`
- `plugins/worldview-panel-codex/scripts/rebuild_agents.py`
- `plugins/worldview-panel-codex/runtime/agents/*.toml`
- `plugins/worldview-panel-codex/tests/test_context_packet_common.py`
- `plugins/worldview-panel-codex/tests/test_prepare_context_packets.py`
- `plugins/worldview-panel-codex/tests/test_prepare_context_packets_integration.py`
- `plugins/worldview-panel-codex/tests/test_panel_logging.py`

## Task 1: Lock The Repo Surface To v1 Broker Files

**Files:**
- Create: `plugins/worldview-panel-codex/schemas/dispatch_job_v1.json`
- Create: `plugins/worldview-panel-codex/schemas/dispatch_ticket_v1.json`
- Create: `plugins/worldview-panel-codex/schemas/worldview_worker_result_v1.json`
- Create: `plugins/worldview-panel-codex/schemas/attestation_v1.json`
- Create: `plugins/worldview-panel-codex/schemas/technical_certified_result_v1.json`
- Create: `plugins/worldview-panel-codex/schemas/audit_event_v1.json`
- Create: `plugins/worldview-panel-codex/tools/build_worldview_round.py`
- Create: `plugins/worldview-panel-codex/tools/run_worldview_broker.py`
- Create: `plugins/worldview-panel-codex/tools/synthesize_worldview_panel.py`
- Create: `plugins/worldview-panel-codex/tools/verify_worldview_round.py`
- Modify: `plugins/worldview-panel-codex/tests/test_plugin_layout.py`
- Modify: `plugins/worldview-panel-codex/tests/test_local_plugin_install.py`
- Modify: `plugins/worldview-panel-codex/scripts/install_local_plugin.py`
- Modify: `plugins/worldview-panel-codex/scripts/uninstall_local_plugin.py`
- Modify: `plugins/worldview-panel-codex/.codex-plugin/plugin.json`

- [ ] **Step 1: Write the failing layout and install tests**

```python
def test_plugin_root_contains_v1_broker_files(self) -> None:
    expected_schema_files = {
        "dispatch_job_v1.json",
        "dispatch_ticket_v1.json",
        "worldview_worker_result_v1.json",
        "attestation_v1.json",
        "technical_certified_result_v1.json",
        "audit_event_v1.json",
    }
    schema_dir = PLUGIN_ROOT / "schemas"
    self.assertEqual({path.name for path in schema_dir.glob("*.json")}, expected_schema_files)
    self.assertTrue((PLUGIN_ROOT / "tools" / "build_worldview_round.py").is_file())
    self.assertTrue((PLUGIN_ROOT / "tools" / "run_worldview_broker.py").is_file())
    self.assertTrue((PLUGIN_ROOT / "tools" / "synthesize_worldview_panel.py").is_file())
    self.assertTrue((PLUGIN_ROOT / "tools" / "verify_worldview_round.py").is_file())
    self.assertFalse((PLUGIN_ROOT / "runtime" / "agents").exists())
    self.assertFalse((PLUGIN_ROOT / "scripts" / "rebuild_agents.py").exists())

def test_install_local_plugin_does_not_copy_runtime_agents(self) -> None:
    self.assertFalse((dest_home / ".codex" / "agents" / "risk_manager.toml").exists())
```

- [ ] **Step 2: Run the targeted tests and confirm they fail**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_plugin_layout.py plugins/worldview-panel-codex/tests/test_local_plugin_install.py -q`
Expected: FAIL because the `schemas/` directory, new CLIs, and no-agent install behavior do not exist yet.

- [ ] **Step 3: Add the v1 surface and installer changes**

```json
// plugins/worldview-panel-codex/schemas/dispatch_job_v1.json
{
  "schema_version": "dispatch_job_v1",
  "type": "object",
  "required": ["schema_version", "run_id", "round_root", "selected_personas", "batch_size", "dispatch_mode"]
}
```

```python
# plugins/worldview-panel-codex/scripts/install_local_plugin.py
actions = [
    f"copy {PLUGIN_ROOT} -> {plugin_dest}",
    f"symlink {skills_link} -> {plugin_dest / 'skills'}",
]

shutil.copytree(PLUGIN_ROOT, plugin_dest, ignore=IGNORE_NAMES)
skills_link.symlink_to((plugin_dest / "skills").resolve(), target_is_directory=True)

# runtime identities are rendered per round; no static companion-agent install step remains
print(f"Installed local plugin to {plugin_dest}")
```

```python
# plugins/worldview-panel-codex/scripts/uninstall_local_plugin.py
targets = [
    dest_home / "plugins" / PLUGIN_NAME,
    dest_home / ".agents" / "skills" / PLUGIN_NAME,
]
for target in targets:
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)
```

```json
// plugins/worldview-panel-codex/.codex-plugin/plugin.json
{
  "interface": {
    "displayName": "Worldview Panel Codex",
    "shortDescription": "Run worldview panels through a sealed broker v1 pipeline.",
    "longDescription": "Local plugin that builds sealed worldview round artifacts and dispatches worker turns only through the broker v1 runtime."
  }
}
```

```python
# plugins/worldview-panel-codex/tools/build_worldview_round.py
#!/usr/bin/env python3
from __future__ import annotations

if __name__ == "__main__":
    raise SystemExit("build_worldview_round.py is implemented in Task 3")
```

```text
Delete:
- plugins/worldview-panel-codex/runtime/agents/
- plugins/worldview-panel-codex/scripts/rebuild_agents.py
```

- [ ] **Step 4: Run the tests again and confirm the surface contract passes**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_plugin_layout.py plugins/worldview-panel-codex/tests/test_local_plugin_install.py -q`
Expected: PASS

- [ ] **Step 5: Commit the surface lock-in**

```bash
git add plugins/worldview-panel-codex/.codex-plugin/plugin.json \
  plugins/worldview-panel-codex/schemas \
  plugins/worldview-panel-codex/scripts/install_local_plugin.py \
  plugins/worldview-panel-codex/scripts/uninstall_local_plugin.py \
  plugins/worldview-panel-codex/tests/test_plugin_layout.py \
  plugins/worldview-panel-codex/tests/test_local_plugin_install.py \
  plugins/worldview-panel-codex/tools/build_worldview_round.py \
  plugins/worldview-panel-codex/tools/run_worldview_broker.py \
  plugins/worldview-panel-codex/tools/synthesize_worldview_panel.py \
  plugins/worldview-panel-codex/tools/verify_worldview_round.py
git rm -r plugins/worldview-panel-codex/runtime/agents plugins/worldview-panel-codex/scripts/rebuild_agents.py
git commit -m "refactor: lock worldview plugin to broker v1 surface"
```

## Task 2: Add Contract Validators And Identity Rendering

**Files:**
- Create: `plugins/worldview-panel-codex/tools/worldview_contracts.py`
- Create: `plugins/worldview-panel-codex/tools/worldview_identity.py`
- Create: `plugins/worldview-panel-codex/tests/test_worldview_contracts.py`
- Create: `plugins/worldview-panel-codex/tests/test_worldview_identity.py`
- Modify: `plugins/worldview-panel-codex/tools/persona_materials.py`

- [ ] **Step 1: Write failing validator and identity tests**

```python
def test_validate_dispatch_job_rejects_raw_prompt_fields(self) -> None:
    payload = {
        "schema_version": "dispatch_job_v1",
        "run_id": "wv-test",
        "round_root": "/tmp/round",
        "selected_personas": ["risk_manager"],
        "batch_size": 1,
        "dispatch_mode": "strict_all_required",
        "message": "illegal raw prompt"
    }
    with self.assertRaisesRegex(ValueError, "raw prompt fields are forbidden"):
        validate_dispatch_job(payload)

def test_render_worker_skill_returns_stable_fingerprint(self) -> None:
    rendered = render_worker_skill("risk_manager_worker_v1", "你是 risk_manager。")
    self.assertIn("name: risk_manager_worker_v1", rendered["skill_text"])
    self.assertEqual(len(rendered["skill_fingerprint"]), 71)  # sha256:<64 hex>
```

- [ ] **Step 2: Run the new tests and verify failure**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_worldview_contracts.py plugins/worldview-panel-codex/tests/test_worldview_identity.py -q`
Expected: FAIL with import errors for `validate_dispatch_job` and `render_worker_skill`.

- [ ] **Step 3: Implement manual validators and identity rendering**

```python
# plugins/worldview-panel-codex/tools/worldview_contracts.py
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

FORBIDDEN_RAW_PROMPT_KEYS = {"message", "prompt", "input_text", "raw_prompt"}

def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256_prefixed(raw: bytes) -> str:
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"

def validate_dispatch_job(payload: dict[str, Any]) -> dict[str, Any]:
    required = {"schema_version", "run_id", "round_root", "selected_personas", "batch_size", "dispatch_mode"}
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"dispatch_job_v1 missing fields: {', '.join(missing)}")
    forbidden = sorted(FORBIDDEN_RAW_PROMPT_KEYS & payload.keys())
    if forbidden:
        raise ValueError("raw prompt fields are forbidden in dispatch_job_v1")
    if payload["schema_version"] != "dispatch_job_v1":
        raise ValueError("dispatch_job_v1 schema_version mismatch")
    if not isinstance(payload["selected_personas"], list) or not payload["selected_personas"]:
        raise ValueError("selected_personas must be a non-empty list")
    return payload

def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
```

```python
# plugins/worldview-panel-codex/tools/worldview_identity.py
from __future__ import annotations

from pathlib import Path

from worldview_contracts import sha256_prefixed

def render_worker_skill(profile_id: str, instruction_text: str) -> dict[str, str]:
    skill_text = "\n".join(
        [
            "---",
            f"name: {profile_id}",
            'description: "Temporary worldview worker identity carrier"',
            "---",
            "",
            instruction_text.strip(),
            "",
        ]
    )
    return {
        "skill_text": skill_text,
        "skill_fingerprint": sha256_prefixed(skill_text.encode("utf-8")),
    }

def write_worker_skill(path: Path, profile_id: str, instruction_text: str) -> dict[str, str]:
    rendered = render_worker_skill(profile_id, instruction_text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered["skill_text"], encoding="utf-8")
    return {**rendered, "skill_path": str(path.resolve())}
```

```python
# plugins/worldview-panel-codex/tools/persona_materials.py
def load_persona_instruction_seed(persona_slug: str) -> str:
    packet = build_persona_material_packet(persona_slug, "other")
    return packet["packet_material"]
```

- [ ] **Step 4: Run the tests and confirm the validators/identity helpers pass**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_worldview_contracts.py plugins/worldview-panel-codex/tests/test_worldview_identity.py -q`
Expected: PASS

- [ ] **Step 5: Commit the contracts and identity helpers**

```bash
git add plugins/worldview-panel-codex/tools/worldview_contracts.py \
  plugins/worldview-panel-codex/tools/worldview_identity.py \
  plugins/worldview-panel-codex/tools/persona_materials.py \
  plugins/worldview-panel-codex/tests/test_worldview_contracts.py \
  plugins/worldview-panel-codex/tests/test_worldview_identity.py
git commit -m "feat: add worldview contract validators and identity rendering"
```

## Task 3: Build Sealed Round Artifacts And Temporary Skill Carriers

**Files:**
- Create: `plugins/worldview-panel-codex/tools/worldview_round_builder.py`
- Modify: `plugins/worldview-panel-codex/tools/build_worldview_round.py`
- Create: `plugins/worldview-panel-codex/tests/test_build_worldview_round.py`
- Modify: `plugins/worldview-panel-codex/tests/fixtures/context_packets/round_input.json`

- [ ] **Step 1: Write the failing round-builder tests**

```python
def test_build_worldview_round_writes_packets_tickets_and_identity_skills(self) -> None:
    round_root = build_round_from_input(FIXTURE_PATH, output_root=Path(tmpdir))
    self.assertTrue((round_root / "packets" / "risk_manager" / "packet.txt").is_file())
    self.assertTrue((round_root / "packets" / "risk_manager" / "packet_manifest.json").is_file())
    self.assertTrue((round_root / "tickets" / "risk_manager.json").is_file())
    self.assertTrue((round_root / "identities" / "risk_manager" / "worker.skill.md").is_file())
    self.assertTrue((round_root / "dispatch_job.json").is_file())
    manifest = json.loads((round_root / "round_manifest.json").read_text(encoding="utf-8"))
    self.assertEqual(manifest["state"], "SEALED")
```

- [ ] **Step 2: Run the round-builder test and verify it fails**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_build_worldview_round.py -q`
Expected: FAIL because `build_round_from_input` and the `identities/` artifact tree do not exist yet.

- [ ] **Step 3: Implement the round builder**

```python
# plugins/worldview-panel-codex/tools/worldview_round_builder.py
from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from persona_materials import build_persona_material_packet, load_persona_instruction_seed
from worldview_contracts import load_json, sha256_prefixed
from worldview_identity import write_worker_skill

def build_round_from_input(input_path: Path, output_root: Path | None = None) -> Path:
    payload = load_json(input_path)
    round_root = (output_root or Path("/tmp")) / f"wv-round-{uuid4().hex}"
    round_root.mkdir(parents=True, exist_ok=True)
    packets_root = round_root / "packets"
    tickets_root = round_root / "tickets"
    identities_root = round_root / "identities"

    packet_statuses: list[dict[str, object]] = []
    for persona in payload["selected_personas"]:
        persona_material = build_persona_material_packet(persona, payload["domain"])
        packet_text = "\n\n".join([
            "[任务]",
            payload["question"],
            persona_material["packet_material"],
        ]).strip()
        packet_root = packets_root / persona
        packet_root.mkdir(parents=True, exist_ok=True)
        packet_path = packet_root / "packet.txt"
        packet_path.write_text(packet_text, encoding="utf-8")

        packet_fingerprint = sha256_prefixed(packet_text.encode("utf-8"))
        (packet_root / "packet_manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": "packet_manifest_v1",
                    "persona": persona,
                    "packet_path": str(packet_path.resolve()),
                    "packet_length": len(packet_text),
                    "packet_fingerprint": packet_fingerprint,
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )

        skill_info = write_worker_skill(
            identities_root / persona / "worker.skill.md",
            f"{persona}_worker_v1",
            load_persona_instruction_seed(persona),
        )

        ticket = {
            "schema_version": "dispatch_ticket_v1",
            "run_id": round_root.name,
            "persona": persona,
            "ticket_id": f"tkt-{persona}-v1",
            "packet_id": f"pkt-{persona}-v1",
            "packet_path": str(packet_path.resolve()),
            "packet_fingerprint": packet_fingerprint,
            "packet_length": len(packet_text),
            "profile_id": f"{persona}_worker_v1",
            "profile_version": "1",
            "profile_hash": skill_info["skill_fingerprint"],
            "policy_id": "readonly_locked_v1",
            "policy_hash": sha256_prefixed(b"readonly_locked_v1"),
            "worker_schema_version": "worldview_worker_result_v1",
            "state": "SEALED",
        }
        ticket_path = tickets_root / f"{persona}.json"
        ticket_path.parent.mkdir(parents=True, exist_ok=True)
        ticket_path.write_text(json.dumps(ticket, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        packet_statuses.append(ticket)

    (round_root / "round_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "round_manifest_v1",
                "run_id": round_root.name,
                "selected_personas": payload["selected_personas"],
                "state": "SEALED",
                "packet_statuses": packet_statuses,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    (round_root / "dispatch_job.json").write_text(
        json.dumps(
            {
                "schema_version": "dispatch_job_v1",
                "run_id": round_root.name,
                "round_root": str(round_root.resolve()),
                "selected_personas": payload["selected_personas"],
                "batch_size": min(6, len(payload["selected_personas"])),
                "dispatch_mode": "strict_all_required",
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    return round_root
```

```python
# plugins/worldview-panel-codex/tools/build_worldview_round.py
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from worldview_round_builder import build_round_from_input

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output-root")
parser.add_argument("--json", action="store_true")
args = parser.parse_args()

round_root = build_round_from_input(
    Path(args.input),
    output_root=Path(args.output_root).resolve() if args.output_root else None,
)
payload = {"round_root": str(round_root.resolve())}
print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload["round_root"])
```

- [ ] **Step 4: Run the round-builder test and CLI smoke test**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_build_worldview_round.py -q`
Expected: PASS

Run: `python3 plugins/worldview-panel-codex/tools/build_worldview_round.py --input plugins/worldview-panel-codex/tests/fixtures/context_packets/round_input.json --output-root /tmp/worldview-round --json`
Expected: JSON output with a real `round_root` path.

- [ ] **Step 5: Commit the round builder**

```bash
git add plugins/worldview-panel-codex/tools/worldview_round_builder.py \
  plugins/worldview-panel-codex/tools/build_worldview_round.py \
  plugins/worldview-panel-codex/tests/test_build_worldview_round.py \
  plugins/worldview-panel-codex/tests/fixtures/context_packets/round_input.json
git commit -m "feat: add worldview round builder"
```

## Task 4: Add JSONL Audit And Exact Input Attestation Primitives

**Files:**
- Create: `plugins/worldview-panel-codex/tools/worldview_audit.py`
- Create: `plugins/worldview-panel-codex/tools/worldview_attestation.py`
- Create: `plugins/worldview-panel-codex/tests/test_worldview_audit.py`
- Modify: `plugins/worldview-panel-codex/tools/run_log.py`
- Modify: `plugins/worldview-panel-codex/tools/write_run_log.py`

- [ ] **Step 1: Write the failing audit and attestation tests**

- `test_write_audit_event_requires_run_id_and_preserves_context`
- `test_build_attestation_records_full_v1_shape`
- `test_write_run_log_cli_can_emit_audit_event_without_breaking_text_logs`

Required assertions:

- audit events require `run_id`
- JSONL payload preserves `thread_id`, `turn_id`, `fingerprints`, and `details`
- audit payload uses `timestamp` and `schema_version=audit_event_v1`
- attestation fingerprints the exact app-server `input` item list; in `v1` the sealed packet is carried by `{"type": "text", "text": ...}`
- attestation records `turn_input_fingerprint`, `turn_user_text_fingerprint`, renderer/newline/encoding, and policy/profile/ticket linkage fields

- [ ] **Step 2: Run the tests and verify failure**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_worldview_audit.py -q`
Expected: FAIL with import errors for `write_audit_event` and `build_attestation`.

- [ ] **Step 3: Implement audit and attestation helpers**

- `worldview_audit.py`
  - append sorted JSONL events under `<round_root>/audit/events.jsonl`
  - require `run_id`, `component`, `entity_type`, `entity_id`, `stage`, and `status`
  - preserve optional `thread_id`, `turn_id`, `fingerprints`, and `details`
- `worldview_attestation.py`
  - accept either the raw input item list or a wrapper shaped like `{"input": [...]}`
  - compute `turn_input_fingerprint` from the exact input items array, not from an abstract prompt object
  - compute `turn_user_text_fingerprint` from the extracted sealed packet text
  - emit the full `attestation_v1` shape used by broker `v1`
  - do not reintroduce legacy helper fields such as `turn_input_user_messages`
- `run_log.py`
  - keep text log helpers intact
  - expose a thin `write_audit_event` passthrough so callers can write JSONL audit events without duplicating logic
- `write_run_log.py`
  - preserve the text-log CLI
  - when `--round-root` is provided, also emit a matching JSONL audit event

- [ ] **Step 4: Run the audit tests and existing log callers**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_worldview_audit.py -q`
Expected: PASS

Run: `python3 plugins/worldview-panel-codex/tools/write_run_log.py --help`
Expected: command usage prints successfully.

- [ ] **Step 5: Commit the audit layer**

```bash
git add plugins/worldview-panel-codex/tools/worldview_audit.py \
  plugins/worldview-panel-codex/tools/worldview_attestation.py \
  plugins/worldview-panel-codex/tools/run_log.py \
  plugins/worldview-panel-codex/tools/write_run_log.py \
  plugins/worldview-panel-codex/tests/test_worldview_audit.py
git commit -m "feat: add worldview audit and attestation helpers"
```

## Task 5: Implement Broker Dispatch With JSON-RPC App-Server Tests

**Files:**
- Create: `plugins/worldview-panel-codex/tools/worldview_app_server.py`
- Create: `plugins/worldview-panel-codex/tools/worldview_broker.py`
- Modify: `plugins/worldview-panel-codex/tools/run_worldview_broker.py`
- Create: `plugins/worldview-panel-codex/tests/test_worldview_app_server.py`
- Create: `plugins/worldview-panel-codex/tests/test_run_worldview_broker.py`
- Create: `plugins/worldview-panel-codex/tests/fixtures/broker/worker_turn_items.json`
- Create: `plugins/worldview-panel-codex/tests/fixtures/broker/disallowed_item_turn_items.json`

- [ ] **Step 1: Write the failing app-server transport tests**

- `test_json_rpc_client_initializes_then_starts_thread`
- `test_json_rpc_client_waits_for_turn_completed_then_reads_thread_items`

Required assertions:

- the client sends `initialize` before the first `thread/start`
- `turn/start` is treated as asynchronous
- the client waits for the matching `turn/completed` notification
- observed items are loaded from `thread/read(includeTurns=true)`
- the worker result is parsed from the final `agentMessage.text` JSON payload

- [ ] **Step 2: Run the transport tests and verify failure**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_worldview_app_server.py -q`
Expected: FAIL because the JSON-RPC client and scripted transport do not exist yet.

- [ ] **Step 3: Implement the JSON-RPC app-server client**

- `worldview_app_server.py`
  - provide `ScriptedTransport` for deterministic tests
  - provide `WebSocketJsonRpcTransport` using `websocket.create_connection`
  - suppress the default WebSocket `Origin` header because the local app-server returns `403` to the default handshake
  - provide `JsonRpcAppServerClient` that:
    - initializes lazily
    - issues JSON-RPC requests with stable request ids
    - buffers unmatched notifications/responses until the expected message arrives
    - maps broker runtime policy to app-server payloads
    - waits for `turn/completed`
    - calls `thread/read(includeTurns=true)` and extracts the observed items/result from the completed turn
  - keep `FixtureAppServerClient` for deterministic broker tests
- the implementation must not reintroduce a fake REST `/thread/start` or `/turn/start` client

- [ ] **Step 4: Write the failing broker tests against app-server user-input shapes**

```python
def test_run_worldview_broker_uses_skill_and_text_user_inputs(self) -> None:
    ...
```

- broker assertions:

- input item `0` is `{"type": "skill", "name": <profile_id>, "path": ...}`
- input item `1` is `{"type": "text", "text": <packet_text>}`
- attestation fingerprints those exact two input items
- allowlist enforcement still applies to observed `userMessage`/`agentMessage` thread items

- [ ] **Step 5: Run the app-server transport and broker tests**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_worldview_app_server.py plugins/worldview-panel-codex/tests/test_run_worldview_broker.py -q`
Expected: PASS

- [ ] **Step 6: Update the broker CLI to use WebSocket terminology**

- rename the CLI flag to `--app-server-url`
- default to `WORLDVIEW_APP_SERVER_URL` or `ws://127.0.0.1:8787`
- treat fixture mode as test-only
- close the app-server client on exit

- [ ] **Step 7: Commit the broker core**

```bash
git add plugins/worldview-panel-codex/tools/worldview_app_server.py \
  plugins/worldview-panel-codex/tools/worldview_broker.py \
  plugins/worldview-panel-codex/tools/run_worldview_broker.py \
  plugins/worldview-panel-codex/tests/test_worldview_app_server.py \
  plugins/worldview-panel-codex/tests/test_run_worldview_broker.py \
  plugins/worldview-panel-codex/tests/fixtures/broker
git commit -m "feat: add strict worldview broker dispatch"
```

## Task 6: Implement Strict Synthesis Gate And Round Verification

**Files:**
- Create: `plugins/worldview-panel-codex/tools/worldview_synthesis.py`
- Modify: `plugins/worldview-panel-codex/tools/synthesize_worldview_panel.py`
- Modify: `plugins/worldview-panel-codex/tools/verify_worldview_round.py`
- Create: `plugins/worldview-panel-codex/tests/test_synthesize_worldview_panel.py`
- Create: `plugins/worldview-panel-codex/tests/test_verify_worldview_round.py`

- [ ] **Step 1: Write the failing synthesis and verification tests**

```python
def test_synthesis_requires_every_requested_persona_to_be_technically_certified(self) -> None:
    with self.assertRaisesRegex(ValueError, "strict gate failed"):
        synthesize_round(round_root_with_missing_persona)

def test_verify_worldview_round_reports_missing_attestation(self) -> None:
    report = verify_round(round_root_missing_attestation)
    self.assertEqual(report["status"], "failed")
    self.assertIn("missing attestation", report["errors"][0])
```

- [ ] **Step 2: Run the tests and verify failure**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_synthesize_worldview_panel.py plugins/worldview-panel-codex/tests/test_verify_worldview_round.py -q`
Expected: FAIL because `synthesize_round` and `verify_round` do not exist yet.

- [ ] **Step 3: Implement strict-gated synthesis and verification**

```python
# plugins/worldview-panel-codex/tools/worldview_synthesis.py
from __future__ import annotations

import json
from pathlib import Path

def collect_technical_results(round_root: Path) -> dict[str, dict]:
    results: dict[str, dict] = {}
    for path in sorted((round_root / "results").glob("*/technical_certified_result.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        results[payload["persona"]] = payload
    return results

def synthesize_round(round_root: Path) -> Path:
    manifest = json.loads((round_root / "round_manifest.json").read_text(encoding="utf-8"))
    certified = collect_technical_results(round_root)
    missing = [persona for persona in manifest["selected_personas"] if persona not in certified]
    if missing:
        raise ValueError(f"strict gate failed: missing TECHNICAL_CERTIFIED personas: {', '.join(missing)}")
    synthesis_root = round_root / "synthesis"
    synthesis_root.mkdir(parents=True, exist_ok=True)
    final_panel = {
        "schema_version": "final_panel_v1",
        "run_id": manifest["run_id"],
        "personas": manifest["selected_personas"],
        "technical_results": certified,
    }
    (synthesis_root / "final_panel.json").write_text(json.dumps(final_panel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (synthesis_root / "final_panel.md").write_text("# Worldview Panel\n\nTechnical certification passed for all requested personas.\n", encoding="utf-8")
    return synthesis_root
```

```python
# plugins/worldview-panel-codex/tools/verify_worldview_round.py
#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

def verify_round(round_root: Path) -> dict[str, object]:
    manifest = json.loads((round_root / "round_manifest.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    for persona in manifest["selected_personas"]:
        result_root = round_root / "results" / persona
        if not (result_root / "attestation.json").is_file():
            errors.append(f"{persona}: missing attestation")
        if not (result_root / "technical_certified_result.json").is_file():
            errors.append(f"{persona}: missing technical_certified_result")
    return {"status": "failed" if errors else "completed", "errors": errors}
```

- [ ] **Step 4: Run the tests and confirm strict gate behavior**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_synthesize_worldview_panel.py plugins/worldview-panel-codex/tests/test_verify_worldview_round.py -q`
Expected: PASS

- [ ] **Step 5: Commit synthesis and verification**

```bash
git add plugins/worldview-panel-codex/tools/worldview_synthesis.py \
  plugins/worldview-panel-codex/tools/synthesize_worldview_panel.py \
  plugins/worldview-panel-codex/tools/verify_worldview_round.py \
  plugins/worldview-panel-codex/tests/test_synthesize_worldview_panel.py \
  plugins/worldview-panel-codex/tests/test_verify_worldview_round.py
git commit -m "feat: add strict worldview synthesis gate"
```

## Task 7: Rewrite Skills, Docs, And Legacy Test Surfaces

**Files:**
- Modify: `plugins/worldview-panel-codex/AGENTS.md`
- Modify: `plugins/worldview-panel-codex/skills/worldview-panel-entry/SKILL.md`
- Modify: `plugins/worldview-panel-codex/skills/worldview-panel-entry/agents/openai.yaml`
- Modify: `plugins/worldview-panel-codex/skills/worldview-context-prep/SKILL.md`
- Modify: `plugins/worldview-panel-codex/skills/worldview-panel-logging/SKILL.md`
- Modify: `plugins/worldview-panel-codex/docs/developer/DEVELOPER_MAINTENANCE.md`
- Modify: `plugins/worldview-panel-codex/docs/developer/DEVELOPER_SELFTEST.md`
- Modify: `plugins/worldview-panel-codex/docs/user/USER_GUIDE.md`
- Modify: `plugins/worldview-panel-codex/docs/user/USER_PROMPTS.md`
- Delete: `plugins/worldview-panel-codex/tools/dispatch_packet_guard.py`
- Delete: `plugins/worldview-panel-codex/tools/context_packet_common.py`
- Delete: `plugins/worldview-panel-codex/tools/prepare_context_packets.py`
- Delete: `plugins/worldview-panel-codex/tests/test_context_packet_common.py`
- Delete: `plugins/worldview-panel-codex/tests/test_prepare_context_packets.py`
- Delete: `plugins/worldview-panel-codex/tests/test_prepare_context_packets_integration.py`
- Delete: `plugins/worldview-panel-codex/tests/test_panel_logging.py`

- [ ] **Step 1: Write the failing doc and skill boundary tests**

```python
def test_split_skills_point_to_broker_v1_tools(self) -> None:
    entry_text = (PLUGIN_ROOT / "skills" / "worldview-panel-entry" / "SKILL.md").read_text(encoding="utf-8")
    self.assertIn("run_worldview_broker.py", entry_text)
    self.assertIn("build_worldview_round.py", entry_text)
    self.assertNotIn("dispatch_packet_guard.py", entry_text)
    self.assertNotIn("spawn_agent(message", entry_text)
```

- [ ] **Step 2: Run the plugin layout test and verify failure**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_plugin_layout.py -q`
Expected: FAIL because the skill docs still mention the legacy prepare/guard pipeline.

- [ ] **Step 3: Rewrite docs and remove the old execution path**

```yaml
# plugins/worldview-panel-codex/skills/worldview-panel-entry/agents/openai.yaml
interface:
  display_name: "Worldview Panel (Broker v1)"
  short_description: "Build a sealed worldview round and run broker-controlled worker turns."
  default_prompt: "Create a sealed worldview round with ../../tools/build_worldview_round.py, dispatch only through ../../tools/run_worldview_broker.py, and synthesize only from technically certified results. Do not use spawn_agent(message=...), do not reuse threads, and do not invoke legacy packet guard tools."
policy:
  allow_implicit_invocation: true
```

```markdown
<!-- plugins/worldview-panel-codex/skills/worldview-context-prep/SKILL.md -->
- Use `../../tools/build_worldview_round.py` to create `packets/`, `tickets/`, and `identities/`.
- Do not use `prepare_context_packets.py`.
- Do not use `dispatch_packet_guard.py`.
```

```text
Delete:
- plugins/worldview-panel-codex/tools/dispatch_packet_guard.py
- plugins/worldview-panel-codex/tools/context_packet_common.py
- plugins/worldview-panel-codex/tools/prepare_context_packets.py
- plugins/worldview-panel-codex/tests/test_context_packet_common.py
- plugins/worldview-panel-codex/tests/test_prepare_context_packets.py
- plugins/worldview-panel-codex/tests/test_prepare_context_packets_integration.py
- plugins/worldview-panel-codex/tests/test_panel_logging.py
```

- [ ] **Step 4: Run the documentation and layout tests**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests/test_plugin_layout.py plugins/worldview-panel-codex/tests/test_local_plugin_install.py -q`
Expected: PASS

- [ ] **Step 5: Commit the doc and legacy-path rewrite**

```bash
git add plugins/worldview-panel-codex/AGENTS.md \
  plugins/worldview-panel-codex/skills/worldview-panel-entry/SKILL.md \
  plugins/worldview-panel-codex/skills/worldview-panel-entry/agents/openai.yaml \
  plugins/worldview-panel-codex/skills/worldview-context-prep/SKILL.md \
  plugins/worldview-panel-codex/skills/worldview-panel-logging/SKILL.md \
  plugins/worldview-panel-codex/docs/developer/DEVELOPER_MAINTENANCE.md \
  plugins/worldview-panel-codex/docs/developer/DEVELOPER_SELFTEST.md \
  plugins/worldview-panel-codex/docs/user/USER_GUIDE.md \
  plugins/worldview-panel-codex/docs/user/USER_PROMPTS.md
git rm plugins/worldview-panel-codex/tools/dispatch_packet_guard.py \
  plugins/worldview-panel-codex/tools/context_packet_common.py \
  plugins/worldview-panel-codex/tools/prepare_context_packets.py \
  plugins/worldview-panel-codex/tests/test_context_packet_common.py \
  plugins/worldview-panel-codex/tests/test_prepare_context_packets.py \
  plugins/worldview-panel-codex/tests/test_prepare_context_packets_integration.py \
  plugins/worldview-panel-codex/tests/test_panel_logging.py
git commit -m "refactor: remove legacy worldview dispatch path"
```

## Task 8: Run The Full v1 Regression Suite

**Files:**
- Modify: `plugins/worldview-panel-codex/tests/test_plugin_layout.py`
- Modify: `plugins/worldview-panel-codex/tests/test_local_plugin_install.py`
- Modify: `plugins/worldview-panel-codex/docs/developer/DEVELOPER_SELFTEST.md`

- [ ] **Step 1: Add one end-to-end regression test for strict mode**

```python
def test_broker_round_trip_requires_every_requested_persona(self) -> None:
    round_root = build_round_from_input(FIXTURE_PATH, output_root=Path(tmpdir))
    dispatch_job = Path(round_root) / "dispatch_job.json"
    dispatch_job.write_text(
        json.dumps(
            {
                "schema_version": "dispatch_job_v1",
                "run_id": Path(round_root).name,
                "round_root": str(Path(round_root).resolve()),
                "selected_personas": ["risk_manager", "existentialist"],
                "batch_size": 2,
                "dispatch_mode": "strict_all_required",
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    with self.assertRaisesRegex(ValueError, "strict gate failed"):
        synthesize_round(Path(round_root))
```

- [ ] **Step 2: Run the targeted regression suite**

Run:

```bash
python3 -m pytest plugins/worldview-panel-codex/tests/test_worldview_contracts.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_worldview_identity.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_build_worldview_round.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_worldview_audit.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_run_worldview_broker.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_synthesize_worldview_panel.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_verify_worldview_round.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_plugin_layout.py -q
python3 -m pytest plugins/worldview-panel-codex/tests/test_local_plugin_install.py -q
```

Expected: all commands PASS.

- [ ] **Step 3: Run the full plugin suite**

Run: `python3 -m pytest plugins/worldview-panel-codex/tests -q`
Expected: PASS

- [ ] **Step 4: Update the self-test doc with the final command set**

```text
## v1 Broker Regression

RUN_ROOT=$(python3 plugins/worldview-panel-codex/tools/build_worldview_round.py --input plugins/worldview-panel-codex/tests/fixtures/context_packets/round_input.json --output-root /tmp/worldview-round --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["round_root"])')
python3 -m pytest plugins/worldview-panel-codex/tests -q
python3 plugins/worldview-panel-codex/tools/run_worldview_broker.py --dispatch-job "$RUN_ROOT/dispatch_job.json" --fixture-turn-items plugins/worldview-panel-codex/tests/fixtures/broker/worker_turn_items.json
python3 plugins/worldview-panel-codex/tools/verify_worldview_round.py --round-root "$RUN_ROOT"
```

- [ ] **Step 5: Commit the final regression pass**

```bash
git add plugins/worldview-panel-codex/tests \
  plugins/worldview-panel-codex/docs/developer/DEVELOPER_SELFTEST.md
git commit -m "test: cover worldview broker v1 end-to-end flow"
```

## Self-Review Checklist

- Spec coverage:
  - strict `v1` gate is implemented in Task 6
  - temporary skill identity carrier is implemented in Task 3
  - exact input attestation is implemented in Task 4 and exercised in Task 5
  - fresh-thread broker dispatch is implemented in Task 5
  - legacy path deletion is implemented in Task 7
- Placeholder scan:
  - no `TBD`
  - no `TODO`
  - no “similar to previous task”
  - every code-changing step includes concrete code
- Type consistency:
  - `TECHNICAL_CERTIFIED` is used consistently
  - `dispatch_job_v1` and `dispatch_ticket_v1` naming stays stable
  - `turn_input_fingerprint` / `turn_user_text_fingerprint` names stay stable
