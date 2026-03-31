from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "src" / "skills" / "worldview-panel-codex" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from context_packet_common import normalize_round_input  # noqa: E402


class ContextPacketCommonTests(unittest.TestCase):
    def test_normalize_round_input_rewrites_missing_material_labels(self) -> None:
        normalized = normalize_round_input(
            {
                "question": "请评价明确写成“先做结构化任务包，再统一生成最终输入”的方案",
                "answer_goal": "decide",
                "domain": "career",
                "hard_constraints": ["只用中文"],
                "selected_personas": ["risk_manager"],
                "external_materials": [{"content": "用户直接贴来的原文"}],
            }
        )

        self.assertEqual(normalized["external_materials"][0]["title"], "用户粘贴内容")
        self.assertEqual(normalized["external_materials"][0]["source"], "用户粘贴内容")

    def test_normalize_round_input_rejects_unresolved_references(self) -> None:
        with self.assertRaisesRegex(ValueError, "unresolved reference"):
            normalize_round_input(
                {
                    "question": "请评价明确写成“先做结构化任务包，再统一生成最终输入”的方案",
                    "answer_goal": "decide",
                    "domain": "career",
                    "hard_constraints": ["不要只针对上面那份材料复述"],
                    "selected_personas": ["risk_manager"],
                    "external_materials": [],
                }
            )


if __name__ == "__main__":
    unittest.main()
