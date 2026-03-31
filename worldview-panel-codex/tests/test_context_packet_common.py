from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "src" / "skills" / "worldview-panel-codex" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from context_packet_common import (  # noqa: E402
    build_packet_bundle,
    build_round_bundle,
    normalize_round_input,
    persist_round_bundle,
    require_round_ready,
)


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

    def test_build_packet_bundle_includes_persona_domain_and_external_sections(self) -> None:
        normalized = normalize_round_input(
            {
                "question": "请判断“先完整备包，再统一分发”这套流程是否稳妥",
                "answer_goal": "decide",
                "domain": "career",
                "hard_constraints": ["只用中文"],
                "selected_personas": ["risk_manager"],
                "external_materials": [
                    {
                        "title": "用户粘贴内容",
                        "source": "用户粘贴内容",
                        "content": "完整原文材料",
                    }
                ],
            }
        )

        bundle = build_packet_bundle(normalized, persona_slug="risk_manager")

        self.assertIn("[任务]", bundle["rendered_packet"])
        self.assertIn("[人格底盘材料]", bundle["rendered_packet"])
        self.assertIn("[当前领域材料]", bundle["rendered_packet"])
        self.assertIn("[外部材料]", bundle["rendered_packet"])
        self.assertEqual(bundle["validation"]["status"], "passed")

    def test_build_round_bundle_marks_batch_not_ready_when_other_answer_leaks_in(self) -> None:
        round_bundle = build_round_bundle(
            {
                "question": "请判断“先完整备包，再统一分发”这套流程是否稳妥",
                "answer_goal": "decide",
                "domain": "career",
                "hard_constraints": ["只用中文"],
                "selected_personas": ["risk_manager", "existentialist"],
                "external_materials": [
                    {
                        "title": "用户粘贴内容",
                        "source": "用户粘贴内容",
                        "content": "[人格]\n这是别人已经写好的回答",
                    }
                ],
            }
        )

        self.assertFalse(round_bundle["manifest"]["ready"])
        self.assertEqual(round_bundle["packets"][0]["validation"]["status"], "failed")
        self.assertIn(
            "forbidden_other_answer_sections",
            [item["code"] for item in round_bundle["packets"][0]["validation"]["errors"]],
        )
        with self.assertRaisesRegex(ValueError, "batch blocked"):
            require_round_ready(round_bundle)

    def test_persist_round_bundle_writes_three_packet_artifacts_and_manifest(self) -> None:
        round_bundle = build_round_bundle(
            {
                "question": "请判断“先完整备包，再统一分发”这套流程是否稳妥",
                "answer_goal": "decide",
                "domain": "career",
                "hard_constraints": ["只用中文"],
                "selected_personas": ["risk_manager"],
                "external_materials": [
                    {
                        "title": "用户粘贴内容",
                        "source": "用户粘贴内容",
                        "content": "完整原文材料",
                    }
                ],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = persist_round_bundle(round_bundle, output_root=Path(tmpdir) / "round-1")

            self.assertTrue((round_root / "risk_manager" / "packet.txt").is_file())
            self.assertTrue((round_root / "risk_manager" / "packet.json").is_file())
            self.assertTrue((round_root / "risk_manager" / "validation.json").is_file())
            manifest = json.loads((round_root / "round.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["ready"])


if __name__ == "__main__":
    unittest.main()
