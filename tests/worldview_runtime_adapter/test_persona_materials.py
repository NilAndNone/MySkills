from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PERSONA_INDEX_PATH = REPO_ROOT / "worldview_runtime_adapter" / "runtime_assets" / "persona-index.json"


from worldview_runtime_adapter import persona_materials


class TestPersonaMaterials(unittest.TestCase):
    def test_persona_index_shape_and_count(self) -> None:
        personas = json.loads(PERSONA_INDEX_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(personas), 24)

        for persona in personas:
            self.assertIn("name", persona)
            self.assertIn("chinese_name", persona)
            self.assertIn("description", persona)
            self.assertIn("group", persona)
            self.assertIn("persona_brief", persona)

    def test_build_persona_material_packet_includes_psychology_and_domain_full_text(self) -> None:
        bundle = persona_materials.build_persona_material_packet("techno_optimist", "career")

        self.assertEqual(bundle["persona"], "techno_optimist")
        self.assertEqual(bundle["domain"], "career")
        self.assertIn("人格底盘材料", bundle["packet_material"])
        self.assertIn("### psychology.md（全文）", bundle["packet_material"])
        self.assertIn("### career.md（全文）", bundle["packet_material"])
        self.assertIn("### profile_2_0.md（提炼）", bundle["packet_material"])

        self.assertIn("## 机制解释", bundle["psychology_full_text"])
        self.assertIn("## 典型论据", bundle["domain_full_text"])

        self.assertIn("职业", bundle["packet_material"])
        self.assertIn(bundle["psychology_full_text"], bundle["packet_material"])
        self.assertIn(bundle["domain_full_text"], bundle["packet_material"])

        self.assertGreater(len(bundle["profile"]), 0)
        self.assertIn("archetypes", bundle["profile"])


if __name__ == "__main__":
    unittest.main()
