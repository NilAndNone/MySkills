from __future__ import annotations

import importlib.util
import sys
import tempfile
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


class WorldviewIdentityTests(unittest.TestCase):
    def test_render_worker_skill_returns_stable_fingerprint(self) -> None:
        identity = load_tools_module(self, "worldview_identity")
        persona_materials = load_tools_module(self, "persona_materials")

        seed = persona_materials.build_persona_instruction_seed("risk_manager")
        rendered_one = identity.render_worker_skill("risk_manager_worker_v1", seed["instruction_seed"])
        rendered_two = identity.render_worker_skill("risk_manager_worker_v1", seed["instruction_seed"])

        self.assertIn("name: risk_manager_worker_v1", rendered_one["skill_text"])
        self.assertIn("风险经理派", rendered_one["skill_text"])
        self.assertEqual(rendered_one["skill_fingerprint"], rendered_two["skill_fingerprint"])
        self.assertEqual(rendered_one["skill_text"], rendered_two["skill_text"])
        self.assertTrue(rendered_one["skill_fingerprint"].startswith("sha256:"))
        self.assertEqual(len(rendered_one["skill_fingerprint"]), 71)

    def test_write_worker_skill_persists_the_rendered_skill(self) -> None:
        identity = load_tools_module(self, "worldview_identity")
        persona_materials = load_tools_module(self, "persona_materials")

        seed = persona_materials.build_persona_instruction_seed("risk_manager")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "skill.md"
            result = identity.write_worker_skill(path, "risk_manager_worker_v1", seed["instruction_seed"])

            self.assertTrue(path.is_file())
            self.assertEqual(path.read_text(encoding="utf-8"), result["skill_text"])
            self.assertEqual(result["skill_fingerprint"], identity.render_worker_skill("risk_manager_worker_v1", seed["instruction_seed"])["skill_fingerprint"])
            self.assertEqual(result["skill_path"], str(path))


if __name__ == "__main__":
    unittest.main()
