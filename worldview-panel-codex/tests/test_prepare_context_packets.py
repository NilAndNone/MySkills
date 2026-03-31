from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "skills" / "worldview-panel-codex" / "tools" / "prepare_context_packets.py"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "context_packets" / "round_input.json"


class PrepareContextPacketsCliTests(unittest.TestCase):
    def test_all_stage_creates_round_directory_and_packet_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            proc = subprocess.run(
                [
                    "python3",
                    str(CLI_PATH),
                    "--input",
                    str(FIXTURE_PATH),
                    "--stage",
                    "all",
                    "--output-root",
                    tmpdir,
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertTrue(Path(payload["round_root"]).is_dir())
            self.assertTrue((Path(payload["round_root"]) / "risk_manager" / "packet.txt").is_file())
            self.assertTrue((Path(payload["round_root"]) / "round.json").is_file())

    def test_normalize_stage_returns_normalized_payload_only(self) -> None:
        proc = subprocess.run(
            [
                "python3",
                str(CLI_PATH),
                "--input",
                str(FIXTURE_PATH),
                "--stage",
                "normalize",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertIn("normalized", payload)
        self.assertNotIn("round_root", payload)


if __name__ == "__main__":
    unittest.main()
