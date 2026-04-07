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

            self.assertEqual(
                contracts.load_json(path),
                {"schema_version": "dispatch_job_v1", "run_id": "wv-test"},
            )

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

    def test_validate_dispatch_job_rejects_nested_prompt_field(self) -> None:
        payload = {
            "schema_version": "dispatch_job_v1",
            "run_id": "wv-test",
            "round_root": "/tmp/round",
            "selected_personas": ["risk_manager"],
            "batch_size": 1,
            "dispatch_mode": "strict_all_required",
            "materials": [{"prompt": "do not include"}],
        }

        with self.assertRaisesRegex(ValueError, "raw prompt fields are forbidden"):
            contracts.validate_dispatch_job(payload)

    def test_validate_dispatch_job_rejects_batch_size_boolean(self) -> None:
        payload = {
            "schema_version": "dispatch_job_v1",
            "run_id": "wv-test",
            "round_root": "/tmp/round",
            "selected_personas": ["risk_manager"],
            "batch_size": True,
            "dispatch_mode": "strict_all_required",
        }

        with self.assertRaisesRegex(ValueError, "batch_size must be an integer"):
            contracts.validate_dispatch_job(payload)

    def test_validate_dispatch_job_rejects_non_strict_dispatch_mode(self) -> None:
        payload = {
            "schema_version": "dispatch_job_v1",
            "run_id": "wv-test",
            "round_root": "/tmp/round",
            "selected_personas": ["risk_manager"],
            "batch_size": 1,
            "dispatch_mode": "permissive",
        }

        with self.assertRaisesRegex(ValueError, "dispatch_mode must be strict_all_required"):
            contracts.validate_dispatch_job(payload)

    def test_write_json_creates_directory_and_writes_pretty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = {"b": 2, "a": 1}
            path = Path(tmpdir) / "nested" / "payload.json"

            returned = contracts.write_json(path, payload)

            self.assertEqual(returned, path)
            self.assertTrue(path.is_file())
            self.assertTrue((Path(tmpdir) / "nested").is_dir())
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                '{\n  "b": 2,\n  "a": 1\n}\n',
            )


if __name__ == "__main__":
    unittest.main()
