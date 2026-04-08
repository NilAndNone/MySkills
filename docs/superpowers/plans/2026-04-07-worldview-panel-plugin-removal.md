# Worldview Panel Plugin Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove `plugins/worldview-panel-codex/` completely by migrating every remaining workspace dependency into `worldview_runtime_adapter`, switching the supported path to those workspace-owned foundations, and then deleting the plugin tree without breaking the supported run and verify flow.

**Architecture:** Keep the supported entrypoints unchanged at `scripts/run_worldview_panel.py` and `scripts/verify_worldview_panel_round.py`, but replace every plugin dependency behind them with workspace-owned modules, schemas, fixtures, and persona runtime assets. Follow one migration rule only: replace foundations first, switch references second, delete the plugin tree last. Repository instructions forbid worktree use for this effort, so all changes happen in-place.

**Tech Stack:** Python 3.14, `unittest`, JSON schema files, markdown persona assets, existing `worldview_runtime_adapter`

---

## File Structure Map

- Create: `worldview_runtime_adapter/contracts.py`
  Owns canonical JSON rendering, SHA-256 helpers, JSON file loading, and `dispatch_job_v1` validation.
- Create: `worldview_runtime_adapter/schema_store.py`
  Loads workspace-owned schemas from `worldview_runtime_adapter/schemas/`.
- Create: `worldview_runtime_adapter/schemas/worldview_worker_result_v1.json`
  Workspace-owned worker output schema used by preflight and runtime validation.
- Create: `worldview_runtime_adapter/app_server.py`
  Workspace-owned transport layer and fixture/live app-server clients.
- Create: `worldview_runtime_adapter/identity.py`
  Renders and writes temporary worker skill files.
- Create: `worldview_runtime_adapter/attestation.py`
  Builds attestation payloads for technically certified persona results.
- Create: `worldview_runtime_adapter/persona_materials.py`
  Loads persona runtime assets from workspace-owned `runtime_assets/` and builds packet material.
- Create: `worldview_runtime_adapter/runtime_assets/persona-index.json`
  Workspace-owned persona registry.
- Create: `worldview_runtime_adapter/runtime_assets/personas/**`
  Workspace-owned persona source materials.
- Create: `tests/fixtures/worldview_runtime_adapter/worker_turn_items.json`
  Workspace-owned deterministic fixture for local runs.
- Create: `tests/worldview_runtime_adapter/test_contracts.py`
  Protects workspace-owned contracts behavior and dispatch-job validation.
- Create: `tests/worldview_runtime_adapter/test_app_server.py`
  Protects workspace-owned app-server transport and client behavior.
- Create: `tests/worldview_runtime_adapter/test_identity.py`
  Protects worker skill rendering and persistence.
- Create: `tests/worldview_runtime_adapter/test_attestation.py`
  Protects attestation payload construction.
- Create: `tests/worldview_runtime_adapter/test_persona_materials.py`
  Protects runtime asset loading and packet material assembly.
- Create: `tests/worldview_runtime_adapter/test_no_plugin_dependency.py`
  Guards against plugin path references in supported runtime code and docs.
- Modify: `worldview_runtime_adapter/cli.py`
  Stops loading the app-server client from plugin code.
- Modify: `worldview_runtime_adapter/schema_preflight.py`
  Stops loading schemas and fingerprint helpers through `plugin_bridge`.
- Modify: `worldview_runtime_adapter/persona_runtime.py`
  Uses workspace-owned schema loading only.
- Modify: `worldview_runtime_adapter/panel_runtime.py`
  Uses workspace-owned contracts and attestation helpers.
- Modify: `worldview_runtime_adapter/round_artifacts.py`
  Uses workspace-owned contracts, identity helpers, and persona materials.
- Modify: `tests/worldview_runtime_adapter/test_schema_preflight.py`
  Stops asserting plugin-owned schema loading.
- Modify: `tests/worldview_runtime_adapter/test_runtime_cli.py`
  Stops asserting plugin entrypoint wording and instead asserts plugin removal.
- Modify: `AGENTS.md`
  Removes plugin-era routing language and points only to workspace-owned assets and entrypoints.
- Modify: `docs/worldview_panel_workspace_usage.md`
  Rewrites fixture paths and usage notes to be fully workspace-owned.
- Delete: `worldview_runtime_adapter/plugin_bridge.py`
  Removes the last plugin path bridge from the supported workspace path.
- Delete: `plugins/worldview-panel-codex/`
  Removes the plugin tree once the workspace no longer depends on it.

### Task 1: Migrate Contracts And Schema Loading Into Workspace-Owned Modules

**Files:**
- Create: `worldview_runtime_adapter/contracts.py`
- Create: `worldview_runtime_adapter/schema_store.py`
- Create: `worldview_runtime_adapter/schemas/worldview_worker_result_v1.json`
- Create: `tests/worldview_runtime_adapter/test_contracts.py`
- Modify: `tests/worldview_runtime_adapter/test_schema_preflight.py`
- Modify: `worldview_runtime_adapter/schema_preflight.py`
- Modify: `worldview_runtime_adapter/persona_runtime.py`

- [ ] **Step 1: Write the failing contracts and schema-loading tests**

```python
# tests/worldview_runtime_adapter/test_contracts.py
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from worldview_runtime_adapter import contracts


class TestContracts(unittest.TestCase):
    def test_canonical_json_bytes_is_stable_and_sorted(self) -> None:
        payload = {"b": 2, "a": {"z": "终", "y": [3, 1]}}
        rendered = contracts.canonical_json_bytes(payload)
        self.assertEqual(rendered, '{"a":{"y":[3,1],"z":"终"},"b":2}'.encode("utf-8"))

    def test_sha256_prefixed_returns_prefixed_digest(self) -> None:
        self.assertEqual(
            contracts.sha256_prefixed(b"abc"),
            "sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )

    def test_load_json_reads_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "payload.json"
            path.write_text('{"schema_version":"dispatch_job_v1","run_id":"wv-test"}', encoding="utf-8")
            self.assertEqual(contracts.load_json(path), {"schema_version": "dispatch_job_v1", "run_id": "wv-test"})

    def test_validate_dispatch_job_accepts_task1_shape(self) -> None:
        payload = {
            "schema_version": "dispatch_job_v1",
            "run_id": "wv-test",
            "round_root": "/tmp/round",
            "selected_personas": ["risk_manager"],
            "batch_size": 1,
            "dispatch_mode": "strict_all_required",
        }
        self.assertEqual(contracts.validate_dispatch_job(payload), payload)
```

```python
# tests/worldview_runtime_adapter/test_schema_preflight.py
from __future__ import annotations

import unittest

from worldview_runtime_adapter import schema_preflight, schema_store


class TestSchemaPreflight(unittest.TestCase):
    def test_schema_store_loads_worldview_worker_schema(self) -> None:
        schema = schema_store.load_worker_schema("worldview_worker_result_v1")
        self.assertEqual(schema["$id"], "worldview_worker_result_v1")
```

- [ ] **Step 2: Run the new tests to verify they fail for the right reason**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_contracts tests.worldview_runtime_adapter.test_schema_preflight`

Expected: FAIL with import errors such as `cannot import name 'contracts'` or `cannot import name 'schema_store'`.

- [ ] **Step 3: Add workspace-owned contracts and schema storage**

```bash
mkdir -p worldview_runtime_adapter/schemas
cp plugins/worldview-panel-codex/schemas/worldview_worker_result_v1.json worldview_runtime_adapter/schemas/worldview_worker_result_v1.json
cat > worldview_runtime_adapter/contracts.py <<'EOF'
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


DISALLOWED_PROMPT_FIELDS = {"message", "prompt", "input_text", "raw_prompt"}
DISPATCH_JOB_REQUIRED_FIELDS = (
    "schema_version",
    "run_id",
    "round_root",
    "selected_personas",
    "batch_size",
    "dispatch_mode",
)
DISPATCH_MODE_STRICT_ALL_REQUIRED = "strict_all_required"


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_prefixed(raw: bytes | bytearray | memoryview | str) -> str:
    raw_bytes = raw.encode("utf-8") if isinstance(raw, str) else bytes(raw)
    return f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}"


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _find_disallowed_prompt_fields(value: Any, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if key in DISALLOWED_PROMPT_FIELDS:
                hits.append(child_path)
            hits.extend(_find_disallowed_prompt_fields(child, child_path))
        return hits
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            hits.extend(_find_disallowed_prompt_fields(child, child_path))
    return hits


def validate_dispatch_job(payload: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(payload)
    if data.get("schema_version") != "dispatch_job_v1":
        raise ValueError("schema_version must be dispatch_job_v1")
    missing = [field for field in DISPATCH_JOB_REQUIRED_FIELDS if field not in data]
    if missing:
        raise ValueError(f"missing required dispatch_job_v1 fields: {', '.join(missing)}")
    forbidden = _find_disallowed_prompt_fields(data)
    if forbidden:
        raise ValueError(f"raw prompt fields are forbidden: {', '.join(forbidden)}")
    if not isinstance(data["run_id"], str) or not data["run_id"]:
        raise ValueError("run_id must be a non-empty string")
    if not isinstance(data["round_root"], str) or not data["round_root"]:
        raise ValueError("round_root must be a non-empty string")
    if not isinstance(data["selected_personas"], list) or not data["selected_personas"]:
        raise ValueError("selected_personas must be a non-empty list of strings")
    if not all(isinstance(item, str) and item for item in data["selected_personas"]):
        raise ValueError("selected_personas must be a list of non-empty strings")
    if not isinstance(data["batch_size"], int) or isinstance(data["batch_size"], bool):
        raise ValueError("batch_size must be an integer")
    if data["batch_size"] <= 0 or data["batch_size"] > 6:
        raise ValueError("batch_size must be between 1 and 6")
    if data["dispatch_mode"] != DISPATCH_MODE_STRICT_ALL_REQUIRED:
        raise ValueError("dispatch_mode must be strict_all_required")
    return data
EOF
cat > worldview_runtime_adapter/schema_store.py <<'EOF'
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"


def load_worker_schema(schema_version: str) -> dict[str, Any]:
    schema_path = SCHEMAS_DIR / f"{schema_version}.json"
    if not schema_path.is_file():
        raise FileNotFoundError(f"worker schema not found: {schema_version}")
    return json.loads(schema_path.read_text(encoding="utf-8"))
EOF
```

- [ ] **Step 4: Switch preflight and persona runtime to workspace-owned loading**

```python
# worldview_runtime_adapter/schema_preflight.py
from worldview_runtime_adapter import contracts

def prepare_output_schema(raw_schema: dict[str, Any], *, schema_version: str) -> dict[str, Any]:
    if schema_version == "worldview_worker_result_v1":
        effective_schema = _tighten_worldview_worker_result_v1(raw_schema)
        return {
            "status": "repaired_in_memory",
            "effective_schema": effective_schema,
            "repair_notes": [
                "set root additionalProperties to false",
                "expanded judgment object to explicit strict properties",
                "added explicit types for const-only schema nodes",
            ],
            "schema_fingerprint": contracts.sha256_prefixed(contracts.canonical_json_bytes(effective_schema)),
        }
    raise ValueError(f"unsupported runtime schema: {schema_version}")
```

```python
# worldview_runtime_adapter/persona_runtime.py
from worldview_runtime_adapter import schema_preflight, schema_store

def run_persona(...):
    raw_schema = schema_store.load_worker_schema(schema_version)
    ...
```

- [ ] **Step 5: Run the contracts, schema preflight, and persona runtime tests**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_contracts tests.worldview_runtime_adapter.test_schema_preflight tests.worldview_runtime_adapter.test_persona_runtime`

Expected: PASS

- [ ] **Step 6: Commit the contracts and schema migration**

```bash
git add worldview_runtime_adapter/contracts.py worldview_runtime_adapter/schema_store.py worldview_runtime_adapter/schemas/worldview_worker_result_v1.json worldview_runtime_adapter/schema_preflight.py worldview_runtime_adapter/persona_runtime.py tests/worldview_runtime_adapter/test_contracts.py tests/worldview_runtime_adapter/test_schema_preflight.py
git commit -m "feat: migrate worldview runtime contracts and schemas"
```

### Task 2: Migrate App-Server, Identity, And Attestation Helpers Into Workspace-Owned Modules

**Files:**
- Create: `worldview_runtime_adapter/app_server.py`
- Create: `worldview_runtime_adapter/identity.py`
- Create: `worldview_runtime_adapter/attestation.py`
- Create: `tests/worldview_runtime_adapter/test_app_server.py`
- Create: `tests/worldview_runtime_adapter/test_identity.py`
- Create: `tests/worldview_runtime_adapter/test_attestation.py`
- Modify: `worldview_runtime_adapter/cli.py`
- Modify: `worldview_runtime_adapter/panel_runtime.py`
- Modify: `worldview_runtime_adapter/round_artifacts.py`

- [ ] **Step 1: Write failing workspace-owned helper tests**

```python
# tests/worldview_runtime_adapter/test_identity.py
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from worldview_runtime_adapter import identity


class TestIdentity(unittest.TestCase):
    def test_render_worker_skill_returns_stable_fingerprint(self) -> None:
        rendered_one = identity.render_worker_skill("risk_manager_worker_v1", "风险经理派\\n测试材料")
        rendered_two = identity.render_worker_skill("risk_manager_worker_v1", "风险经理派\\n测试材料")
        self.assertEqual(rendered_one["skill_fingerprint"], rendered_two["skill_fingerprint"])
        self.assertIn("name: risk_manager_worker_v1", rendered_one["skill_text"])

    def test_write_worker_skill_persists_the_rendered_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = identity.write_worker_skill(Path(tmpdir) / "skill.md", "risk_manager_worker_v1", "风险经理派\\n测试材料")
            self.assertTrue((Path(tmpdir) / "skill.md").is_file())
            self.assertEqual((Path(tmpdir) / "skill.md").read_text(encoding="utf-8"), result["skill_text"])
```

```python
# tests/worldview_runtime_adapter/test_attestation.py
from __future__ import annotations

import unittest

from worldview_runtime_adapter import attestation


class TestAttestation(unittest.TestCase):
    def test_build_attestation_hashes_turn_input_and_user_text(self) -> None:
        payload = attestation.build_attestation(
            packet_fingerprint="sha256:packet",
            turn_input=[{"type": "text", "text": "packet"}],
            observed_user_text="packet",
            run_id="wv-round-test",
            persona="risk_manager",
        )
        self.assertEqual(payload["schema_version"], "attestation_v1")
        self.assertEqual(payload["run_id"], "wv-round-test")
        self.assertTrue(payload["turn_input_fingerprint"].startswith("sha256:"))
        self.assertTrue(payload["turn_user_text_fingerprint"].startswith("sha256:"))
```

```python
# tests/worldview_runtime_adapter/test_app_server.py
from __future__ import annotations

import unittest
from unittest import mock

from worldview_runtime_adapter import app_server


class TestAppServer(unittest.TestCase):
    def test_websocket_transport_suppresses_origin_header(self) -> None:
        fake_socket = mock.Mock()
        with mock.patch.object(app_server, "create_connection", return_value=fake_socket) as mocked_connect:
            transport = app_server.WebSocketJsonRpcTransport("ws://127.0.0.1:8787", 5.0)
        mocked_connect.assert_called_once_with("ws://127.0.0.1:8787", timeout=5.0, suppress_origin=True)
        transport.close()
```

- [ ] **Step 2: Run the helper tests to verify they fail**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_identity tests.worldview_runtime_adapter.test_attestation tests.worldview_runtime_adapter.test_app_server`

Expected: FAIL with import errors for `identity`, `attestation`, or `app_server`.

- [ ] **Step 3: Copy the helper implementations into workspace-owned files**

```bash
cp plugins/worldview-panel-codex/tools/worldview_app_server.py worldview_runtime_adapter/app_server.py
cp plugins/worldview-panel-codex/tools/worldview_identity.py worldview_runtime_adapter/identity.py
cp plugins/worldview-panel-codex/tools/worldview_attestation.py worldview_runtime_adapter/attestation.py
```

- [ ] **Step 4: Rewrite the imported dependencies to use workspace-owned contracts**

```python
# worldview_runtime_adapter/identity.py
from worldview_runtime_adapter.contracts import sha256_prefixed
```

```python
# worldview_runtime_adapter/attestation.py
from worldview_runtime_adapter.contracts import canonical_json_bytes, sha256_prefixed
```

```python
# worldview_runtime_adapter/cli.py
from worldview_runtime_adapter import app_server, intake, round_artifacts

def main(argv: list[str] | None = None) -> int:
    ...
    if args.fixture_turn_items:
        client = app_server.FixtureAppServerClient(args.fixture_turn_items)
    else:
        client = app_server.JsonRpcAppServerClient.connect(args.app_server_url)
```

```python
# worldview_runtime_adapter/panel_runtime.py
from worldview_runtime_adapter import attestation, composer, contracts, intake, role_planner, surfaces

def _hash_payload(payload: Any) -> str:
    return contracts.sha256_prefixed(contracts.canonical_json_bytes(payload))
```

```python
# worldview_runtime_adapter/round_artifacts.py
from worldview_runtime_adapter import contracts, identity, persona_materials, role_planner

def _contracts() -> Any:
    return contracts
```

- [ ] **Step 5: Run the helper and runtime tests**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_identity tests.worldview_runtime_adapter.test_attestation tests.worldview_runtime_adapter.test_app_server tests.worldview_runtime_adapter.test_panel_runtime`

Expected: PASS

- [ ] **Step 6: Commit the helper migration**

```bash
git add worldview_runtime_adapter/app_server.py worldview_runtime_adapter/identity.py worldview_runtime_adapter/attestation.py worldview_runtime_adapter/cli.py worldview_runtime_adapter/panel_runtime.py worldview_runtime_adapter/round_artifacts.py tests/worldview_runtime_adapter/test_identity.py tests/worldview_runtime_adapter/test_attestation.py tests/worldview_runtime_adapter/test_app_server.py
git commit -m "feat: migrate worldview runtime helper modules"
```

### Task 3: Migrate Persona Runtime Assets, Persona Materials, And Deterministic Fixture Data

**Files:**
- Create: `worldview_runtime_adapter/persona_materials.py`
- Create: `worldview_runtime_adapter/runtime_assets/persona-index.json`
- Create: `worldview_runtime_adapter/runtime_assets/personas/**`
- Create: `tests/fixtures/worldview_runtime_adapter/worker_turn_items.json`
- Create: `tests/worldview_runtime_adapter/test_persona_materials.py`
- Modify: `worldview_runtime_adapter/round_artifacts.py`
- Modify: `docs/worldview_panel_workspace_usage.md`

- [ ] **Step 1: Write the failing persona material tests**

```python
# tests/worldview_runtime_adapter/test_persona_materials.py
from __future__ import annotations

import json
import unittest
from pathlib import Path

from worldview_runtime_adapter import persona_materials


class TestPersonaMaterials(unittest.TestCase):
    def test_persona_index_stays_lightweight(self) -> None:
        personas = json.loads((Path(__file__).resolve().parents[2] / "worldview_runtime_adapter" / "runtime_assets" / "persona-index.json").read_text(encoding="utf-8"))
        self.assertEqual(len(personas), 24)
        for persona in personas:
            self.assertEqual(sorted(persona.keys()), ["chinese_name", "description", "group", "name", "persona_brief"])

    def test_build_persona_material_packet_includes_full_psychology_and_domain_material_by_default(self) -> None:
        bundle = persona_materials.build_persona_material_packet("techno_optimist", "career")
        self.assertEqual(bundle["persona"], "techno_optimist")
        self.assertEqual(bundle["domain"], "career")
        self.assertIn("人格底盘材料", bundle["packet_material"])
        self.assertIn("当前领域材料", bundle["packet_material"])
        self.assertIn("### psychology.md（全文）", bundle["packet_material"])
        self.assertIn("### career.md（全文）", bundle["packet_material"])
```

- [ ] **Step 2: Run the persona material tests to verify they fail**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_persona_materials`

Expected: FAIL because `persona_materials.py` and `runtime_assets/` do not exist yet.

- [ ] **Step 3: Copy the runtime assets and deterministic fixture into workspace-owned locations**

```bash
mkdir -p worldview_runtime_adapter/runtime_assets tests/fixtures/worldview_runtime_adapter
cp plugins/worldview-panel-codex/runtime/persona-index.json worldview_runtime_adapter/runtime_assets/persona-index.json
cp -R plugins/worldview-panel-codex/runtime/personas worldview_runtime_adapter/runtime_assets/personas
cp plugins/worldview-panel-codex/tests/fixtures/broker/worker_turn_items.json tests/fixtures/worldview_runtime_adapter/worker_turn_items.json
cp plugins/worldview-panel-codex/tools/persona_materials.py worldview_runtime_adapter/persona_materials.py
```

- [ ] **Step 4: Rebase persona materials onto workspace-owned runtime assets**

```python
# worldview_runtime_adapter/persona_materials.py
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parent / "runtime_assets"
PERSONA_INDEX_PATH = RUNTIME_ROOT / "persona-index.json"
PERSONAS_ROOT = RUNTIME_ROOT / "personas"


def runtime_root() -> Path:
    return RUNTIME_ROOT


def persona_index_path() -> Path:
    if not PERSONA_INDEX_PATH.is_file():
        raise FileNotFoundError(f"could not locate {PERSONA_INDEX_PATH}")
    return PERSONA_INDEX_PATH


def personas_root() -> Path:
    if not PERSONAS_ROOT.is_dir():
        raise FileNotFoundError(f"could not locate {PERSONAS_ROOT}")
    return PERSONAS_ROOT
```

```python
# worldview_runtime_adapter/round_artifacts.py
from worldview_runtime_adapter import contracts, identity, persona_materials, role_planner

def _packet_identity(round_root: Path, persona: str, persona_material: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    profile_id = f"{persona}_{PROFILE_SUFFIX}"
    skill_path = round_root / "identities" / persona / "worker.skill.md"
    identity_seed = persona_materials.build_persona_instruction_seed(persona)
    skill = identity.write_worker_skill(skill_path, profile_id, identity_seed["instruction_seed"])
    ...
```

```markdown
<!-- docs/worldview_panel_workspace_usage.md -->
`--fixture-turn-items tests/fixtures/worldview_runtime_adapter/worker_turn_items.json`
```

- [ ] **Step 5: Run the persona material and round artifact tests**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_persona_materials tests.worldview_runtime_adapter.test_round_artifacts tests.worldview_runtime_adapter.test_panel_runtime`

Expected: PASS

- [ ] **Step 6: Commit the runtime asset migration**

```bash
git add worldview_runtime_adapter/persona_materials.py worldview_runtime_adapter/runtime_assets tests/fixtures/worldview_runtime_adapter/worker_turn_items.json worldview_runtime_adapter/round_artifacts.py docs/worldview_panel_workspace_usage.md tests/worldview_runtime_adapter/test_persona_materials.py
git commit -m "feat: migrate worldview runtime assets into workspace"
```

### Task 4: Remove The Plugin Bridge And Cut The Supported Path Over To Workspace-Owned Modules Only

**Files:**
- Modify: `worldview_runtime_adapter/cli.py`
- Modify: `worldview_runtime_adapter/schema_preflight.py`
- Modify: `worldview_runtime_adapter/persona_runtime.py`
- Modify: `worldview_runtime_adapter/panel_runtime.py`
- Modify: `worldview_runtime_adapter/round_artifacts.py`
- Modify: `tests/worldview_runtime_adapter/test_runtime_cli.py`
- Create: `tests/worldview_runtime_adapter/test_no_plugin_dependency.py`
- Delete: `worldview_runtime_adapter/plugin_bridge.py`

- [ ] **Step 1: Write the failing residual-dependency test**

```python
# tests/worldview_runtime_adapter/test_no_plugin_dependency.py
from __future__ import annotations

import unittest
from pathlib import Path


class TestNoPluginDependency(unittest.TestCase):
    def test_supported_runtime_code_contains_no_plugin_path_reference(self) -> None:
        runtime_root = Path(__file__).resolve().parents[2] / "worldview_runtime_adapter"
        checked = []
        for path in sorted(runtime_root.glob("*.py")):
            if path.name == "__init__.py":
                continue
            checked.append(path.name)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("plugins/worldview-panel-codex", text, path.name)
        self.assertTrue(checked)

    def test_plugin_bridge_file_is_removed(self) -> None:
        bridge_path = Path(__file__).resolve().parents[2] / "worldview_runtime_adapter" / "plugin_bridge.py"
        self.assertFalse(bridge_path.exists())
```

- [ ] **Step 2: Run the residual-dependency test to verify it fails**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_no_plugin_dependency`

Expected: FAIL because supported runtime files still reference plugin paths and `plugin_bridge.py` still exists.

- [ ] **Step 3: Remove `plugin_bridge.py` and update all remaining imports**

```python
# worldview_runtime_adapter/cli.py
from worldview_runtime_adapter import app_server, contracts, intake, round_artifacts

payload = contracts.load_json(args.round_input)
```

```python
# worldview_runtime_adapter/schema_preflight.py
from worldview_runtime_adapter import contracts
```

```python
# worldview_runtime_adapter/persona_runtime.py
from worldview_runtime_adapter import schema_preflight, schema_store
```

```python
# worldview_runtime_adapter/panel_runtime.py
from worldview_runtime_adapter import attestation, composer, contracts, intake, role_planner, surfaces
```

```bash
rm worldview_runtime_adapter/plugin_bridge.py
```

- [ ] **Step 4: Update CLI and AGENTS assertions to match the fully workspace-owned path**

```python
# tests/worldview_runtime_adapter/test_runtime_cli.py
    def test_repo_agents_routes_worldview_panel_to_workspace_only_path(self) -> None:
        agents_path = Path(__file__).resolve().parents[2] / "AGENTS.md"
        text = agents_path.read_text(encoding="utf-8")
        self.assertIn("scripts/run_worldview_panel.py", text)
        self.assertIn("scripts/verify_worldview_panel_round.py", text)
        self.assertNotIn("plugins/worldview-panel-codex/tools/run_worldview_broker.py", text)
```

```markdown
<!-- AGENTS.md -->
- 优先走 `scripts/run_worldview_panel.py`
- 跑完后用 `scripts/verify_worldview_panel_round.py` 检查
- 不要再依赖任何 plugin 目录路径
```

- [ ] **Step 5: Run the supported runtime test suite**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_schema_preflight tests.worldview_runtime_adapter.test_persona_runtime tests.worldview_runtime_adapter.test_panel_runtime tests.worldview_runtime_adapter.test_runtime_cli tests.worldview_runtime_adapter.test_no_plugin_dependency`

Expected: PASS

- [ ] **Step 6: Commit the cutover away from plugin references**

```bash
git add worldview_runtime_adapter/cli.py worldview_runtime_adapter/schema_preflight.py worldview_runtime_adapter/persona_runtime.py worldview_runtime_adapter/panel_runtime.py worldview_runtime_adapter/round_artifacts.py AGENTS.md tests/worldview_runtime_adapter/test_runtime_cli.py tests/worldview_runtime_adapter/test_no_plugin_dependency.py
git rm worldview_runtime_adapter/plugin_bridge.py
git commit -m "refactor: remove worldview plugin bridge"
```

### Task 5: Delete The Plugin Tree And Clean Up Plugin-Era Docs, Tests, And Narratives

**Files:**
- Delete: `plugins/worldview-panel-codex/`
- Modify: `docs/worldview_panel_workspace_usage.md`
- Modify: `tests/worldview_runtime_adapter/test_no_plugin_dependency.py`

- [ ] **Step 1: Extend the residual-dependency test to assert plugin tree removal**

```python
# tests/worldview_runtime_adapter/test_no_plugin_dependency.py
    def test_plugin_tree_is_removed(self) -> None:
        plugin_root = Path(__file__).resolve().parents[2] / "plugins" / "worldview-panel-codex"
        self.assertFalse(plugin_root.exists())
```

- [ ] **Step 2: Run the residual-dependency test to verify it fails**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_no_plugin_dependency`

Expected: FAIL because `plugins/worldview-panel-codex/` still exists.

- [ ] **Step 3: Delete the plugin tree and remove the last plugin-era usage notes**

```bash
rm -rf plugins/worldview-panel-codex
```

```markdown
<!-- docs/worldview_panel_workspace_usage.md -->
- 删除“不要直接调用 plugin 里的旧工具链”这类表述
- 改成“工作区主线只保留 run / verify 两个入口”
- 所有示例都只使用工作区自有 fixture 和工作区自有资产
```

- [ ] **Step 4: Run the full supported test suite and repository hygiene checks**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_contracts tests.worldview_runtime_adapter.test_app_server tests.worldview_runtime_adapter.test_identity tests.worldview_runtime_adapter.test_attestation tests.worldview_runtime_adapter.test_persona_materials tests.worldview_runtime_adapter.test_intake tests.worldview_runtime_adapter.test_role_planner tests.worldview_runtime_adapter.test_round_artifacts tests.worldview_runtime_adapter.test_composer tests.worldview_runtime_adapter.test_surfaces tests.worldview_runtime_adapter.test_panel_runtime tests.worldview_runtime_adapter.test_persona_runtime tests.worldview_runtime_adapter.test_review_viewer tests.worldview_runtime_adapter.test_runtime_cli tests.worldview_runtime_adapter.test_schema_preflight tests.worldview_runtime_adapter.test_verifier tests.worldview_runtime_adapter.test_no_plugin_dependency`

Expected: PASS

Run: `rg -n "plugins/worldview-panel-codex" worldview_runtime_adapter scripts tests/worldview_runtime_adapter AGENTS.md docs/worldview_panel_workspace_usage.md`

Expected: no matches

- [ ] **Step 5: Run one deterministic end-to-end round and verify it**

```bash
tmpdir=$(mktemp -d)
cat > "$tmpdir/input.json" <<'EOF'
{
  "issue": "平台是否应该更严格标注 AI 生成的政治广告？",
  "output_intent": "briefing",
  "stance_mode": "neutral_compare"
}
EOF
python3 scripts/run_worldview_panel.py \
  --round-input "$tmpdir/input.json" \
  --output-root "$tmpdir/out" \
  --fixture-turn-items tests/fixtures/worldview_runtime_adapter/worker_turn_items.json \
  --json > "$tmpdir/run.json"
round_root=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["round_root"])' "$tmpdir/run.json")
python3 scripts/verify_worldview_panel_round.py --round-root "$round_root" --json
```

Expected: JSON output with `"ok": true` and an empty `errors` list

- [ ] **Step 6: Commit the plugin deletion**

```bash
git add AGENTS.md docs/worldview_panel_workspace_usage.md tests/worldview_runtime_adapter/test_no_plugin_dependency.py tests/fixtures/worldview_runtime_adapter/worker_turn_items.json
git rm -r plugins/worldview-panel-codex
git commit -m "refactor: remove worldview panel plugin tree"
```

## Self-Review

### Spec Coverage

- Final boundary and single-entrypoint requirement are implemented by Tasks 4 and 5.
- Foundation migration is implemented by Tasks 1, 2, and 3.
- Plugin tree deletion is implemented by Task 5.
- Result integrity and supported path validation are covered by Tasks 1 through 5 test commands.
- Residual narrative cleanup is covered by Tasks 4 and 5 through `AGENTS.md`, workspace usage docs, and repository hygiene searches.

No spec requirement is left without a task.

### Placeholder Scan

- No placeholder markers remain.
- Every task has exact files, code or shell content, run commands, expected outcomes, and commit messages.

### Type Consistency

- The plan uses `contracts.py`, `schema_store.py`, `app_server.py`, `identity.py`, `attestation.py`, and `persona_materials.py` consistently across all tasks.
- The deterministic fixture path is consistently `tests/fixtures/worldview_runtime_adapter/worker_turn_items.json`.
- The supported entrypoints remain consistently `scripts/run_worldview_panel.py` and `scripts/verify_worldview_panel_round.py`.
