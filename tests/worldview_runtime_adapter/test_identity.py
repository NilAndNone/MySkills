from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from worldview_runtime_adapter import identity


class TestWorldviewRuntimeIdentity(unittest.TestCase):
    def test_render_worker_skill_fingerprint_is_stable(self) -> None:
        rendered_one = identity.render_worker_skill("risk_manager_worker_v3", "Instruction A")
        rendered_two = identity.render_worker_skill("risk_manager_worker_v3", "Instruction A")

        self.assertIn("name: risk_manager_worker_v3", rendered_one["skill_text"])
        self.assertEqual(rendered_one["skill_fingerprint"], rendered_two["skill_fingerprint"])
        self.assertEqual(rendered_one["skill_text"], rendered_two["skill_text"])
        self.assertEqual(rendered_one["instruction_text"], "Instruction A")
        self.assertTrue(rendered_one["skill_fingerprint"].startswith("sha256:"))
        self.assertEqual(len(rendered_one["skill_fingerprint"]), 71)

    def test_write_worker_skill_persists_skill_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "worker.skill.md"
            result = identity.write_worker_skill(skill_path, "risk_manager_worker_v3", "Instruction B")

            self.assertTrue(skill_path.is_file())
            self.assertEqual(result["skill_path"], str(skill_path.resolve()))
            self.assertEqual(skill_path.read_text(encoding="utf-8"), result["skill_text"])
            self.assertEqual(
                result["skill_fingerprint"],
                identity.render_worker_skill("risk_manager_worker_v3", "Instruction B")["skill_fingerprint"],
            )


if __name__ == "__main__":
    unittest.main()
