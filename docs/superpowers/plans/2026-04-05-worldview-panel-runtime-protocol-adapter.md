# Worldview Panel Runtime Protocol Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a workspace-owned runtime adapter that keeps the plugin read-only while repairing protocol/output failures in memory, retrying per persona, and emitting degraded panel results above the configured success threshold.

**Architecture:** Add a new top-level Python package that reuses the plugin's round builder and artifact contracts but owns protocol preflight, persona retry logic, run aggregation, and degraded synthesis. The adapter never edits plugin code or schema files; it only reads plugin artifacts and transforms outgoing requests in memory before app-server submission.

**Tech Stack:** Python 3, unittest, JSON artifacts, existing worldview panel plugin tooling, filesystem round roots, app-server transport abstraction

---

## File Map

### Create

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

### Modify

- `docs/superpowers/specs/2026-04-05-worldview-panel-runtime-protocol-adapter-design.md`
- `docs/superpowers/plans/2026-04-05-worldview-panel-runtime-protocol-adapter.md`

## Task 1: Build Schema Preflight And Plugin Bridge

**Files:**
- Create: `worldview_runtime_adapter/__init__.py`
- Create: `worldview_runtime_adapter/plugin_bridge.py`
- Create: `worldview_runtime_adapter/schema_preflight.py`
- Test: `tests/worldview_runtime_adapter/test_schema_preflight.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

import unittest

from worldview_runtime_adapter import plugin_bridge, schema_preflight


class TestSchemaPreflight(unittest.TestCase):
    def test_plugin_bridge_loads_worldview_worker_schema(self) -> None:
        schema = plugin_bridge.load_worker_schema("worldview_worker_result_v1")
        self.assertEqual(schema["schema_version"] if "schema_version" in schema else schema["$id"], "worldview_worker_result_v1")

    def test_preflight_repairs_root_and_nested_object_contract(self) -> None:
        raw_schema = plugin_bridge.load_worker_schema("worldview_worker_result_v1")
        outcome = schema_preflight.prepare_output_schema(raw_schema, schema_version="worldview_worker_result_v1")
        self.assertEqual(outcome["status"], "repaired_in_memory")
        self.assertFalse(outcome["effective_schema"]["additionalProperties"])
        self.assertFalse(outcome["effective_schema"]["properties"]["judgment"]["additionalProperties"])
        self.assertEqual(
            outcome["effective_schema"]["properties"]["judgment"]["required"],
            ["factual", "value", "strategy"],
        )

    def test_preflight_rejects_unknown_schema_without_overlay(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported runtime schema"):
            schema_preflight.prepare_output_schema({"type": "object"}, schema_version="unknown_schema_v9")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_schema_preflight -q`
Expected: FAIL with import errors because the runtime adapter package does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# worldview_runtime_adapter/plugin_bridge.py
from pathlib import Path
import importlib.util
import json
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[1] / "plugins" / "worldview-panel-codex"
TOOLS_DIR = PLUGIN_ROOT / "tools"
SCHEMAS_DIR = PLUGIN_ROOT / "schemas"


def load_worker_schema(schema_version: str) -> dict:
    path = SCHEMAS_DIR / f"{schema_version}.json"
    return json.loads(path.read_text(encoding="utf-8"))


# worldview_runtime_adapter/schema_preflight.py
from copy import deepcopy


def prepare_output_schema(raw_schema: dict, *, schema_version: str) -> dict:
    if schema_version != "worldview_worker_result_v1":
        raise ValueError(f"unsupported runtime schema: {schema_version}")
    schema = deepcopy(raw_schema)
    schema["additionalProperties"] = False
    schema["properties"]["judgment"] = {
        "type": "object",
        "properties": {
            "factual": {"type": "string"},
            "value": {"type": "string"},
            "strategy": {"type": "string"},
        },
        "required": ["factual", "value", "strategy"],
        "additionalProperties": False,
    }
    return {"status": "repaired_in_memory", "effective_schema": schema, "repair_notes": ["tightened object schemas"]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_schema_preflight -q`
Expected: PASS

## Task 2: Add Persona Runtime With Targeted Retry

**Files:**
- Create: `worldview_runtime_adapter/persona_runtime.py`
- Test: `tests/worldview_runtime_adapter/test_persona_runtime.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

import unittest

from worldview_runtime_adapter.persona_runtime import run_persona


class FakeClient:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def start_thread(self) -> str:
        return f"thr_{len(self.calls) + 1}"

    def start_turn(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class TestPersonaRuntime(unittest.TestCase):
    def test_protocol_schema_error_triggers_retry_without_counting_local_repair(self) -> None:
        client = FakeClient(
            [
                RuntimeError("invalid_json_schema: additionalProperties must be false"),
                {"result": {"schema_version": "worldview_worker_result_v1", "persona": "risk_manager", "judgment": {"factual": "f", "value": "v", "strategy": "s"}, "diagnosis": ["d"], "recommended_actions": ["a"], "voice_style": "plain", "blind_spot": "b", "overuse_risk": "r", "signature_line": "sig", "confidence": 0.6}},
            ]
        )
        outcome = run_persona(
            persona="risk_manager",
            packet_text="packet text",
            skill_path="/tmp/risk_manager.skill.md",
            schema_version="worldview_worker_result_v1",
            app_server_client=client,
            max_retries=3,
        )
        self.assertEqual(outcome["status"], "certified_success")
        self.assertEqual(outcome["attempt_count"], 2)
        self.assertEqual(outcome["retry_count"], 1)

    def test_result_schema_error_exhausts_three_retries_then_fails(self) -> None:
        invalid_result = {"result": {"persona": "risk_manager"}}
        client = FakeClient([invalid_result, invalid_result, invalid_result, invalid_result])
        outcome = run_persona(
            persona="risk_manager",
            packet_text="packet text",
            skill_path="/tmp/risk_manager.skill.md",
            schema_version="worldview_worker_result_v1",
            app_server_client=client,
            max_retries=3,
        )
        self.assertEqual(outcome["status"], "failed_after_retries")
        self.assertEqual(outcome["retry_count"], 3)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_persona_runtime -q`
Expected: FAIL because `run_persona` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def run_persona(*, persona: str, packet_text: str, skill_path: str, schema_version: str, app_server_client, max_retries: int) -> dict:
    retry_count = 0
    attempt_count = 0
    last_error = ""
    while True:
        attempt_count += 1
        try:
            turn = app_server_client.start_turn(
                thread_id=app_server_client.start_thread(),
                input_items=[{"type": "skill", "name": persona, "path": skill_path}, {"type": "text", "text": packet_text}],
                output_schema={},
                sandbox_policy="read-only",
                approval_policy="never",
            )
            result = turn["result"]
            _validate_result(result, persona=persona)
            return {"status": "certified_success", "retry_count": retry_count, "attempt_count": attempt_count, "result": result}
        except RuntimeError as exc:
            last_error = str(exc)
        except ValueError as exc:
            last_error = str(exc)

        if retry_count >= max_retries:
            return {"status": "failed_after_retries", "retry_count": retry_count, "attempt_count": attempt_count, "failure_reason": last_error}
        retry_count += 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_persona_runtime -q`
Expected: PASS

## Task 3: Add Panel Runtime Threshold And Failed Persona Placeholders

**Files:**
- Create: `worldview_runtime_adapter/panel_runtime.py`
- Create: `worldview_runtime_adapter/failure_summary.py`
- Test: `tests/worldview_runtime_adapter/test_panel_runtime.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

import unittest

from worldview_runtime_adapter.panel_runtime import build_panel_outcome


class TestPanelRuntime(unittest.TestCase):
    def test_failed_personas_remain_visible_but_do_not_join_synthesis(self) -> None:
        results = [
            {"persona": "risk_manager", "status": "certified_success", "result": {"signature_line": "sig-a"}},
            {"persona": "modern_mystic", "status": "failed_after_retries", "failure_reason": "invalid_json_schema"},
        ]
        outcome = build_panel_outcome(results, minimum_success_ratio=0.5)
        self.assertEqual(outcome["run_status"], "completed_with_failures")
        self.assertEqual(len(outcome["successful_personas"]), 1)
        self.assertEqual(len(outcome["failed_personas"]), 1)
        self.assertIn("modern_mystic", outcome["panel"]["failed_personas"])

    def test_panel_is_not_emitted_below_threshold(self) -> None:
        results = [
            {"persona": "risk_manager", "status": "certified_success", "result": {"signature_line": "sig-a"}},
            {"persona": "modern_mystic", "status": "failed_after_retries", "failure_reason": "invalid_json_schema"},
            {"persona": "systems_operator", "status": "failed_after_retries", "failure_reason": "missing field"},
        ]
        outcome = build_panel_outcome(results, minimum_success_ratio=0.67)
        self.assertEqual(outcome["run_status"], "completed_with_failures")
        self.assertFalse(outcome["panel_emitted"])
        self.assertIn("failure_summary", outcome)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_panel_runtime -q`
Expected: FAIL because `panel_runtime` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def build_panel_outcome(results: list[dict], minimum_success_ratio: float) -> dict:
    successful = [item for item in results if item["status"] == "certified_success"]
    failed = [item for item in results if item["status"] != "certified_success"]
    ratio = len(successful) / len(results) if results else 0.0
    run_status = "completed" if not failed and successful else "completed_with_failures" if successful else "failed"
    if ratio < minimum_success_ratio:
        return {
            "run_status": run_status,
            "panel_emitted": False,
            "successful_personas": successful,
            "failed_personas": failed,
            "failure_summary": {"success_ratio": ratio, "failed_personas": [item["persona"] for item in failed]},
        }
    return {
        "run_status": run_status,
        "panel_emitted": True,
        "successful_personas": successful,
        "failed_personas": failed,
        "panel": {
            "successful_personas": [item["persona"] for item in successful],
            "failed_personas": [item["persona"] for item in failed],
        },
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_panel_runtime -q`
Expected: PASS

## Task 4: Add CLI Wrapper And Full Verification

**Files:**
- Create: `scripts/run_worldview_panel_runtime.py`
- Modify: `worldview_runtime_adapter/plugin_bridge.py`
- Modify: `worldview_runtime_adapter/panel_runtime.py`
- Test: `tests/worldview_runtime_adapter/test_schema_preflight.py`
- Test: `tests/worldview_runtime_adapter/test_persona_runtime.py`
- Test: `tests/worldview_runtime_adapter/test_panel_runtime.py`

- [ ] **Step 1: Write a failing CLI smoke test**

```python
import subprocess
import sys
import unittest
from pathlib import Path


class TestRuntimeCli(unittest.TestCase):
    def test_runtime_cli_help_executes(self) -> None:
        script = Path("scripts/run_worldview_panel_runtime.py")
        proc = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("minimum-success-ratio", proc.stdout)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_schema_preflight tests.worldview_runtime_adapter.test_persona_runtime tests.worldview_runtime_adapter.test_panel_runtime -q`
Expected: PASS for existing adapter tests, and the CLI smoke test is still absent.

- [ ] **Step 3: Write minimal implementation**

```python
parser = argparse.ArgumentParser(description="Run worldview panel through the workspace runtime adapter.")
parser.add_argument("--round-input", required=True)
parser.add_argument("--app-server-url", default="ws://127.0.0.1:8787")
parser.add_argument("--minimum-success-ratio", type=float, default=0.67)
parser.add_argument("--max-retries", type=int, default=3)
```

- [ ] **Step 4: Run focused verification**

Run: `python3 -m unittest tests.worldview_runtime_adapter.test_schema_preflight tests.worldview_runtime_adapter.test_persona_runtime tests.worldview_runtime_adapter.test_panel_runtime -q`
Expected: PASS

- [ ] **Step 5: Run plugin regression guard**

Run: `python3 -m unittest plugins.worldview-panel-codex.tests.test_worldview_app_server plugins.worldview-panel-codex.tests.test_run_worldview_broker -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/plans/2026-04-05-worldview-panel-runtime-protocol-adapter.md \
  worldview_runtime_adapter/__init__.py \
  worldview_runtime_adapter/plugin_bridge.py \
  worldview_runtime_adapter/schema_preflight.py \
  worldview_runtime_adapter/persona_runtime.py \
  worldview_runtime_adapter/panel_runtime.py \
  worldview_runtime_adapter/failure_summary.py \
  scripts/run_worldview_panel_runtime.py \
  tests/worldview_runtime_adapter/test_schema_preflight.py \
  tests/worldview_runtime_adapter/test_persona_runtime.py \
  tests/worldview_runtime_adapter/test_panel_runtime.py
git commit -m "feat: add worldview runtime protocol adapter"
```
