from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "context_packets" / "round_input.json"


def load_worldview_round_builder_module(test_case: unittest.TestCase):
    module_path = TOOLS_DIR / "worldview_round_builder.py"

    spec = importlib.util.spec_from_file_location("worldview_round_builder", module_path)
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


class WorldviewRoundBuilderTests(unittest.TestCase):
    def test_build_round_from_input_writes_packets_tickets_and_identity_skills(self) -> None:
        module = load_worldview_round_builder_module(self)

        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = module.build_round_from_input(FIXTURE_PATH, output_root=Path(tmpdir))

            self.assertTrue(round_root.is_dir())
            self.assertEqual(round_root.parent, Path(tmpdir))
            self.assertTrue((round_root / "dispatch_job.json").is_file())
            self.assertTrue((round_root / "round_manifest.json").is_file())

            for persona in ("risk_manager", "existentialist"):
                packet_root = round_root / "packets" / persona
                identity_root = round_root / "identities" / persona
                ticket_path = round_root / "tickets" / f"{persona}.json"

                self.assertTrue((packet_root / "packet.txt").is_file())
                self.assertTrue((packet_root / "packet_manifest.json").is_file())
                self.assertTrue(ticket_path.is_file())
                self.assertTrue((identity_root / "worker.skill.md").is_file())

                packet_manifest = json.loads((packet_root / "packet_manifest.json").read_text(encoding="utf-8"))
                ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
                skill_text = (identity_root / "worker.skill.md").read_text(encoding="utf-8")

                self.assertEqual(packet_manifest["state"], "SEALED")
                self.assertEqual(ticket["state"], "SEALED")
                self.assertEqual(ticket["packet_fingerprint"], packet_manifest["packet_fingerprint"])
                self.assertEqual(ticket["packet_length"], packet_manifest["packet_length"])
                self.assertEqual(ticket["worker_schema_version"], "worldview_worker_result_v1")
                self.assertEqual(ticket["profile_version"], "3")
                self.assertEqual(ticket["profile_id"], f"{persona}_worker_v3")
                self.assertEqual(ticket["policy_id"], "readonly_locked_v1")
                self.assertTrue(ticket["packet_fingerprint"].startswith("sha256:"))
                self.assertEqual(len(ticket["packet_fingerprint"]), 71)
                self.assertIn(persona, skill_text)

            round_manifest = json.loads((round_root / "round_manifest.json").read_text(encoding="utf-8"))
            dispatch_job = json.loads((round_root / "dispatch_job.json").read_text(encoding="utf-8"))

            self.assertEqual(round_manifest["state"], "SEALED")
            self.assertEqual(round_manifest["selected_personas"], ["risk_manager", "existentialist"])
            self.assertEqual(dispatch_job["schema_version"], "dispatch_job_v1")
            self.assertEqual(dispatch_job["round_root"], str(round_root.resolve()))
            self.assertEqual(dispatch_job["selected_personas"], ["risk_manager", "existentialist"])

    def test_build_worldview_round_cli_json_reports_round_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            proc = subprocess.run(
                [
                    "python3",
                    str(TOOLS_DIR / "build_worldview_round.py"),
                    "--input",
                    str(FIXTURE_PATH),
                    "--output-root",
                    tmpdir,
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            payload = json.loads(proc.stdout)
            round_root = Path(payload["round_root"])

            self.assertTrue(round_root.is_dir())
            self.assertEqual(round_root.parent, Path(tmpdir))
            self.assertTrue((round_root / "dispatch_job.json").is_file())


if __name__ == "__main__":
    unittest.main()
