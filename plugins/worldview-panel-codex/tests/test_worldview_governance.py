from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"


def load_tools_module(test_case: unittest.TestCase, module_name: str):
    module_path = TOOLS_DIR / f"{module_name}.py"
    test_case.assertTrue(module_path.is_file(), f"{module_name}.py should exist in the worldview tools directory.")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
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


class WorldviewGovernanceTests(unittest.TestCase):
    def test_build_governance_seal_records_topology_authority_and_repo_baseline(self) -> None:
        governance = load_tools_module(self, "worldview_governance")

        seal = governance.build_governance_seal(
            round_root=Path("/tmp/wv-round"),
            run_id="wv-round-test",
            topology={
                "dispatch_job_fingerprint": "sha256:dispatch",
                "round_manifest_fingerprint": "sha256:manifest",
                "tickets": {"risk_manager": "sha256:ticket"},
                "selected_personas": ["risk_manager"],
                "dispatch_mode": "strict_all_required",
                "batch_size": 1,
            },
            protected_repo_files={"plugins/worldview-panel-codex/tools/worldview_broker.py": "sha256:file"},
        )

        self.assertEqual(seal["schema_version"], "governance_seal_v1")
        self.assertEqual(seal["run_id"], "wv-round-test")
        self.assertEqual(seal["state"], "SEALED")
        self.assertEqual(seal["topology"]["dispatch_job_fingerprint"], "sha256:dispatch")
        self.assertEqual(seal["topology"]["tickets"]["risk_manager"], "sha256:ticket")
        self.assertEqual(
            seal["protected_repo_files"]["plugins/worldview-panel-codex/tools/worldview_broker.py"],
            "sha256:file",
        )
        self.assertIn("orchestrator", seal["source_authority"])
        self.assertIn("topology_drift", seal["invalidity_policy"])

    def test_build_governance_status_starts_sealed_without_violations(self) -> None:
        governance = load_tools_module(self, "worldview_governance")

        status = governance.build_governance_status(run_id="wv-round-test", updated_by_component="round_builder")

        self.assertEqual(status["schema_version"], "governance_status_v1")
        self.assertEqual(status["run_id"], "wv-round-test")
        self.assertEqual(status["state"], "SEALED")
        self.assertIsNone(status["terminal_reason"])
        self.assertEqual(status["violations"], [])
        self.assertEqual(status["updated_by_component"], "round_builder")


if __name__ == "__main__":
    unittest.main()
