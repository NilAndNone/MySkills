from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from worldview_runtime_adapter import intake, round_artifacts
from worldview_runtime_adapter.round_artifacts import PROFILE_SUFFIX


class TestRoundArtifacts(unittest.TestCase):
    def test_round_artifacts_build_mainline_round_without_plugin_round_builder(self) -> None:
        tmpdir = Path(tempfile.mkdtemp())
        brief = intake.normalize_product_input(
            {
                "issue": "平台是否应该更严格标注 AI 生成的政治广告？",
                "output_intent": "briefing",
                "stance_mode": "neutral_compare",
            }
        )

        round_root = round_artifacts.build_round(brief, output_root=tmpdir)

        round_input = json.loads((round_root / "round_input.json").read_text(encoding="utf-8"))
        persona = str(round_input["selected_personas"][0])
        profile = json.loads((round_root / "identities" / persona / "profile.json").read_text(encoding="utf-8"))
        ticket = json.loads((round_root / "tickets" / f"{persona}.json").read_text(encoding="utf-8"))

        self.assertTrue((round_root / "identities" / persona / "profile.json").is_file())
        self.assertEqual(profile["persona"], persona)
        self.assertEqual(profile["profile_id"], f"{persona}_{PROFILE_SUFFIX}")
        skill_path = (round_root / profile["skill_path"]).resolve()
        self.assertEqual(skill_path.parent.name, persona)
        self.assertEqual(skill_path.name, "worker.skill.md")
        self.assertTrue(skill_path.is_file())
        self.assertEqual(ticket["profile_id"], profile["profile_id"])
        self.assertEqual(ticket["profile_version"], profile["profile_version"])
        self.assertEqual(ticket["profile_hash"], profile["profile_hash"])

        self.assertTrue((round_root / "round_input.json").is_file())
        self.assertTrue((round_root / "dispatch_job.json").is_file())
        self.assertTrue((round_root / "packets" / "external_reference" / "packet.txt").is_file())


if __name__ == "__main__":
    unittest.main()
