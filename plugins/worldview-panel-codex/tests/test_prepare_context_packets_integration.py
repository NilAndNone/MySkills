from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "tools" / "prepare_context_packets.py"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "context_packets" / "round_input.json"


class PrepareContextPacketsIntegrationTests(unittest.TestCase):
    def test_stage_all_persists_every_subagent_before_dispatch(self) -> None:
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
            round_root = Path(payload["round_root"])

            self.assertTrue((round_root / "risk_manager" / "packet.txt").is_file())
            self.assertTrue((round_root / "risk_manager" / "packet.json").is_file())
            self.assertTrue((round_root / "risk_manager" / "validation.json").is_file())
            self.assertTrue((round_root / "existentialist" / "packet.txt").is_file())
            self.assertTrue((round_root / "round.json").is_file())
            manifest = json.loads((round_root / "round.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["packet_statuses"][0]["dispatch_ready"])
            self.assertEqual(
                manifest["packet_statuses"][0]["packet_path"],
                str((round_root / "risk_manager" / "packet.txt").resolve()),
            )
            self.assertEqual(len(manifest["packet_statuses"][0]["packet_fingerprint"]), 64)
            self.assertGreater(manifest["packet_statuses"][0]["packet_length"], 0)


if __name__ == "__main__":
    unittest.main()
