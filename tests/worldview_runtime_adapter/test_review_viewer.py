from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from worldview_runtime_adapter import review_viewer


PACKET_TEXT = """[round_input]
question: 这是测试问题
answer_goal: evaluate
domain: public_discourse
persona: risk_manager
profile_id: risk_manager_worker_v3

[hard_constraints]
- 只用中文
- 明确区分事实和判断

[external_materials]
### 1. 事实
source: test
这里是外部材料

[persona_material]
### 风险经理派 / risk_manager
这里是人格材料
"""


RAW_RESULT = {
    "schema_version": "worldview_worker_result_v1",
    "persona": "risk_manager",
    "judgment": {
        "factual": "事实段落",
        "value": "价值判断",
        "strategy": "策略判断",
    },
    "diagnosis": ["诊断 1", "诊断 2"],
    "recommended_actions": ["动作 1", "动作 2"],
    "signature_line": "签名",
    "confidence": 0.82,
}


class TestReviewViewer(unittest.TestCase):
    def test_build_round_payload_collects_persona_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = self._create_round_fixture(Path(tmpdir))

            payload = review_viewer.build_round_payload(round_root)

            self.assertEqual(payload["question"], "这是测试问题")
            self.assertEqual(payload["persona_count"], 1)
            persona = payload["personas"][0]
            self.assertEqual(persona["persona"], "risk_manager")
            self.assertEqual(persona["profile_id"], "risk_manager_worker_v3")
            self.assertEqual(persona["hard_constraints"], ["只用中文", "明确区分事实和判断"])
            self.assertEqual(persona["raw_result"]["judgment"]["factual"], "事实段落")
            self.assertIn("ticket", persona["evidence"])
            self.assertIn("attestation", persona["evidence"])
            self.assertIn("certified", persona["evidence"])

    def test_write_static_viewer_outputs_html_and_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            round_root = self._create_round_fixture(root / "round")
            output_dir = root / "viewer"

            review_viewer.write_static_viewer(round_root, output_dir)

            html_path = output_dir / "index.html"
            data_path = output_dir / "data.json"
            self.assertTrue(html_path.is_file())
            self.assertTrue(data_path.is_file())

            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Worldview Round Viewer", html)
            self.assertIn("question-body", html)
            self.assertIn("persona-list", html)
            self.assertIn("evidence-panel", html)

            data = json.loads(data_path.read_text(encoding="utf-8"))
            self.assertEqual(data["question"], "这是测试问题")
            self.assertEqual(data["personas"][0]["persona"], "risk_manager")

    def _create_round_fixture(self, round_root: Path) -> Path:
        (round_root / "packets" / "risk_manager").mkdir(parents=True)
        (round_root / "tickets").mkdir(parents=True)
        (round_root / "results" / "risk_manager").mkdir(parents=True)
        (round_root / "synthesis").mkdir(parents=True)

        (round_root / "packets" / "risk_manager" / "packet.txt").write_text(
            PACKET_TEXT,
            encoding="utf-8",
        )
        (round_root / "tickets" / "risk_manager.json").write_text(
            json.dumps(
                {
                    "persona": "risk_manager",
                    "profile_id": "risk_manager_worker_v3",
                    "packet_fingerprint": "sha256:test-packet",
                    "packet_length": len(PACKET_TEXT),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (round_root / "results" / "risk_manager" / "raw_result.json").write_text(
            json.dumps(RAW_RESULT, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (round_root / "results" / "risk_manager" / "attestation.json").write_text(
            json.dumps({"packet_fingerprint": "sha256:test-packet", "technical_status": "TECHNICAL_CERTIFIED"}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        (round_root / "results" / "risk_manager" / "technical_certified_result.json").write_text(
            json.dumps(
                {
                    "persona": "risk_manager",
                    "technical_status": "TECHNICAL_CERTIFIED",
                    "result": RAW_RESULT,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (round_root / "synthesis" / "final_panel.json").write_text(
            json.dumps(
                {
                    "schema_version": "final_panel_v1",
                    "run_id": "wv-round-test",
                    "personas": ["risk_manager"],
                    "technical_results": {
                        "risk_manager": {
                            "technical_status": "TECHNICAL_CERTIFIED",
                            "result": RAW_RESULT,
                        }
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        return round_root


if __name__ == "__main__":
    unittest.main()
