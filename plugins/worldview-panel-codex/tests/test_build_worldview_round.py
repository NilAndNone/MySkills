from __future__ import annotations

import importlib.util
import hashlib
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
    def _build_round(self, payload: dict[str, object]) -> Path:
        module = load_worldview_round_builder_module(self)

        tmpdir = Path(tempfile.mkdtemp())
        input_path = tmpdir / "round_input.json"
        input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return module.build_round_from_input(input_path, output_root=tmpdir)

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
                packet_bytes = (packet_root / "packet.txt").read_bytes()

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
                self.assertEqual(packet_manifest["packet_length"], len(packet_bytes))
                self.assertEqual(
                    packet_manifest["packet_fingerprint"],
                    f"sha256:{hashlib.sha256(packet_bytes).hexdigest()}",
                )

            round_manifest = json.loads((round_root / "round_manifest.json").read_text(encoding="utf-8"))
            dispatch_job = json.loads((round_root / "dispatch_job.json").read_text(encoding="utf-8"))

            self.assertEqual(round_manifest["state"], "SEALED")
            self.assertEqual(round_manifest["selected_personas"], ["risk_manager", "existentialist"])
            self.assertEqual(dispatch_job["schema_version"], "dispatch_job_v1")
            self.assertEqual(dispatch_job["round_root"], str(round_root.resolve()))
            self.assertEqual(dispatch_job["selected_personas"], ["risk_manager", "existentialist"])

    def test_same_persona_keeps_identity_hashes_across_domains(self) -> None:
        module = load_worldview_round_builder_module(self)

        with FIXTURE_PATH.open(encoding="utf-8") as handle:
            payload = json.load(handle)

        payload["selected_personas"] = ["risk_manager"]
        payload["domain"] = "career"
        career_root = self._build_round(payload)
        career_manifest = json.loads((career_root / "packets" / "risk_manager" / "packet_manifest.json").read_text(encoding="utf-8"))
        career_ticket = json.loads((career_root / "tickets" / "risk_manager.json").read_text(encoding="utf-8"))
        career_profile_bytes = (career_root / "identities" / "risk_manager" / "profile.json").read_bytes()
        career_profile = json.loads((career_root / "identities" / "risk_manager" / "profile.json").read_text(encoding="utf-8"))

        payload["domain"] = "startup"
        startup_root = self._build_round(payload)
        startup_manifest = json.loads((startup_root / "packets" / "risk_manager" / "packet_manifest.json").read_text(encoding="utf-8"))
        startup_ticket = json.loads((startup_root / "tickets" / "risk_manager.json").read_text(encoding="utf-8"))
        startup_profile_bytes = (startup_root / "identities" / "risk_manager" / "profile.json").read_bytes()
        startup_profile = json.loads((startup_root / "identities" / "risk_manager" / "profile.json").read_text(encoding="utf-8"))

        self.assertEqual(career_ticket["profile_hash"], startup_ticket["profile_hash"])
        self.assertEqual(career_manifest["skill_fingerprint"], startup_manifest["skill_fingerprint"])
        self.assertTrue((career_root / "identities" / "risk_manager" / "profile.json").is_file())
        self.assertTrue((startup_root / "identities" / "risk_manager" / "profile.json").is_file())
        self.assertEqual(career_profile["identity_source"], "profile_json")
        self.assertEqual(career_profile["identity_runtime_carrier"], "skill_file")
        self.assertEqual(career_profile["profile_id"], "risk_manager_worker_v3")
        self.assertEqual(career_profile["profile_version"], "3")
        self.assertEqual(career_profile["instruction_text"], startup_profile["instruction_text"])
        self.assertEqual(career_profile["policy_id"], "readonly_locked_v1")
        self.assertEqual(career_profile["output_schema_version"], "worldview_worker_result_v1")
        self.assertEqual(career_profile["model_binding"], "gpt-5-codex")
        self.assertIn("profile_hash", career_profile)
        career_profile_without_hash = dict(career_profile)
        startup_profile_without_hash = dict(startup_profile)
        career_profile_without_hash.pop("profile_hash")
        startup_profile_without_hash.pop("profile_hash")
        self.assertEqual(
            career_profile["profile_hash"],
            startup_profile["profile_hash"],
        )
        self.assertEqual(
            career_profile["profile_hash"],
            career_ticket["profile_hash"],
        )
        self.assertEqual(
            career_profile["profile_hash"],
            f"sha256:{hashlib.sha256(module.canonical_json_bytes(career_profile_without_hash)).hexdigest()}",
        )
        self.assertEqual(
            startup_profile["profile_hash"],
            f"sha256:{hashlib.sha256(module.canonical_json_bytes(startup_profile_without_hash)).hexdigest()}",
        )
        self.assertEqual(career_profile_bytes, startup_profile_bytes)

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

    def test_dispatch_job_batch_size_caps_at_six(self) -> None:
        with FIXTURE_PATH.open(encoding="utf-8") as handle:
            payload = json.load(handle)

        payload["domain"] = "other"
        payload["selected_personas"] = [
            "risk_manager",
            "existentialist",
            "techno_optimist",
            "collapse_prophet",
            "baseline_conformist",
            "modern_mystic",
            "terminal_jester",
        ]

        round_root = self._build_round(payload)
        dispatch_job = json.loads((round_root / "dispatch_job.json").read_text(encoding="utf-8"))

        self.assertEqual(dispatch_job["batch_size"], 6)


if __name__ == "__main__":
    unittest.main()
