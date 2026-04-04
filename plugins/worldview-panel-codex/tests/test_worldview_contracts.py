from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"


def load_worldview_contracts_module(test_case: unittest.TestCase):
    module_path = TOOLS_DIR / "worldview_contracts.py"
    test_case.assertTrue(module_path.is_file(), "worldview_contracts.py should exist in the worldview tools directory.")

    spec = importlib.util.spec_from_file_location("worldview_contracts", module_path)
    test_case.assertIsNotNone(spec)
    test_case.assertIsNotNone(spec.loader)

    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        spec.loader.exec_module(module)
    finally:
        if sys.path and sys.path[0] == str(TOOLS_DIR):
            sys.path.pop(0)
    return module


class WorldviewContractsTests(unittest.TestCase):
    def test_canonical_json_bytes_is_stable_and_sorted(self) -> None:
        module = load_worldview_contracts_module(self)

        payload = {"b": 2, "a": {"z": "终", "y": [3, 1]}}
        rendered = module.canonical_json_bytes(payload)

        self.assertEqual(rendered, '{"a":{"y":[3,1],"z":"终"},"b":2}'.encode("utf-8"))

    def test_sha256_prefixed_returns_prefixed_digest(self) -> None:
        module = load_worldview_contracts_module(self)

        self.assertEqual(module.sha256_prefixed(b"abc"), "sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_load_json_reads_a_file(self) -> None:
        module = load_worldview_contracts_module(self)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "payload.json"
            path.write_text('{"schema_version":"dispatch_job_v1","run_id":"wv-test"}', encoding="utf-8")

            self.assertEqual(module.load_json(path), {"schema_version": "dispatch_job_v1", "run_id": "wv-test"})

    def test_validate_dispatch_job_rejects_raw_prompt_fields(self) -> None:
        module = load_worldview_contracts_module(self)

        payload = {
            "schema_version": "dispatch_job_v1",
            "run_id": "wv-test",
            "round_root": "/tmp/round",
            "selected_personas": ["risk_manager"],
            "batch_size": 1,
            "dispatch_mode": "strict_all_required",
            "message": "illegal raw prompt",
        }

        with self.assertRaisesRegex(ValueError, "raw prompt fields are forbidden"):
            module.validate_dispatch_job(payload)

    def test_validate_dispatch_job_rejects_missing_required_fields(self) -> None:
        module = load_worldview_contracts_module(self)

        payload = {
            "schema_version": "dispatch_job_v1",
            "run_id": "wv-test",
            "round_root": "/tmp/round",
            "selected_personas": ["risk_manager"],
            "dispatch_mode": "strict_all_required",
        }

        with self.assertRaisesRegex(ValueError, "missing required dispatch_job_v1 fields"):
            module.validate_dispatch_job(payload)

    def test_validate_dispatch_job_accepts_task1_shape(self) -> None:
        module = load_worldview_contracts_module(self)

        payload = {
            "schema_version": "dispatch_job_v1",
            "run_id": "wv-test",
            "round_root": "/tmp/round",
            "selected_personas": ["risk_manager"],
            "batch_size": 1,
            "dispatch_mode": "strict_all_required",
        }

        self.assertEqual(module.validate_dispatch_job(payload), payload)


if __name__ == "__main__":
    unittest.main()
