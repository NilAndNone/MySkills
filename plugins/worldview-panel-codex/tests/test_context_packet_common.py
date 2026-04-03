from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from context_packet_common import (  # noqa: E402
    DISPATCH_MISMATCH_MESSAGE,
    build_packet_bundle,
    build_round_bundle,
    load_dispatch_packet,
    normalize_round_input,
    persist_round_bundle,
    release_dispatch_payload,
    require_matching_dispatch_payload,
    require_released_dispatch_payload,
    require_round_ready,
    verify_dispatch_payload,
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
        self.assertIsNone(bundle["dispatch_artifact"]["packet_path"])
        self.assertEqual(bundle["dispatch_artifact"]["packet_length"], len(bundle["rendered_packet"]))
        self.assertEqual(len(bundle["dispatch_artifact"]["packet_fingerprint"]), 64)
        self.assertFalse(bundle["dispatch_artifact"]["dispatch_ready"])

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
            self.assertEqual(
                round_bundle["packets"][0]["dispatch_artifact"]["packet_path"],
                str((round_root / "risk_manager" / "packet.txt").resolve()),
            )
            self.assertTrue(round_bundle["packets"][0]["dispatch_artifact"]["dispatch_ready"])
            manifest = json.loads((round_root / "round.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["ready"])
            self.assertEqual(
                manifest["packet_statuses"][0]["packet_path"],
                str((round_root / "risk_manager" / "packet.txt").resolve()),
            )
            self.assertEqual(
                manifest["packet_statuses"][0]["packet_length"],
                len((round_root / "risk_manager" / "packet.txt").read_text(encoding="utf-8")),
            )
            self.assertEqual(len(manifest["packet_statuses"][0]["packet_fingerprint"]), 64)
            self.assertTrue(manifest["packet_statuses"][0]["dispatch_ready"])

    def test_verify_dispatch_payload_blocks_shortened_packet_and_returns_fixed_message(self) -> None:
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
            original_packet = (round_root / "risk_manager" / "packet.txt").read_text(encoding="utf-8")
            result = verify_dispatch_payload(round_root, "risk_manager", original_packet[:-12])

            self.assertFalse(result["matched"])
            self.assertEqual(result["expected_length"], len(original_packet))
            self.assertEqual(result["actual_length"], len(original_packet[:-12]))
            self.assertEqual(result["failure_message"], DISPATCH_MISMATCH_MESSAGE)
            with self.assertRaisesRegex(ValueError, DISPATCH_MISMATCH_MESSAGE):
                require_matching_dispatch_payload(round_root, "risk_manager", original_packet[:-12])

    def test_release_dispatch_payload_writes_verified_outgoing_copy(self) -> None:
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
            result = release_dispatch_payload(round_root, "risk_manager")

            outgoing_path = Path(result["outgoing_path"])
            self.assertTrue(outgoing_path.is_file())
            self.assertTrue(result["matched"])
            self.assertEqual(result["expected_length"], result["actual_length"])
            self.assertEqual(
                outgoing_path.read_text(encoding="utf-8"),
                (round_root / "risk_manager" / "packet.txt").read_text(encoding="utf-8"),
            )

    def test_require_released_dispatch_payload_blocks_when_outgoing_copy_is_modified(self) -> None:
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
            result = release_dispatch_payload(round_root, "risk_manager")
            outgoing_path = Path(result["outgoing_path"])
            outgoing_path.write_text(outgoing_path.read_text(encoding="utf-8")[:-8], encoding="utf-8")

            with self.assertRaisesRegex(ValueError, DISPATCH_MISMATCH_MESSAGE):
                require_released_dispatch_payload(round_root, "risk_manager", outgoing_path)

    def test_load_dispatch_packet_rejects_tampered_persisted_packet(self) -> None:
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
            packet_path = round_root / "risk_manager" / "packet.txt"
            packet_path.write_text(packet_path.read_text(encoding="utf-8") + "\n手动篡改", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "persisted packet artifact no longer matches manifest"):
                load_dispatch_packet(round_root, "risk_manager")


if __name__ == "__main__":
    unittest.main()
