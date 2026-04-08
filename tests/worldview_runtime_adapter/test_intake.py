from __future__ import annotations

import unittest

from worldview_runtime_adapter import intake


class TestIntake(unittest.TestCase):
    def test_normalize_product_input_keeps_only_product_contract(self) -> None:
        payload = {
            "issue": "平台是否应该更严格标注 AI 生成的政治广告？",
            "output_intent": "briefing",
            "stance_mode": "neutral_compare",
            "audience": "中文内容创作者",
            "scope": "平台治理",
            "timeframe": "2025-2026",
            "constraints": ["只用中文"],
            "materials": [
                {
                    "title": "平台公告摘录",
                    "source": "用户粘贴内容",
                    "content": "平台正在测试更明显的 AI 标签。",
                }
            ],
        }

        brief = intake.normalize_product_input(payload)

        self.assertEqual(brief["issue"], payload["issue"])
        self.assertEqual(brief["output_intent"], "briefing")
        self.assertEqual(brief["stance_mode"], "neutral_compare")
        self.assertEqual(
            brief["meta"]["quality_rubric"],
            [
                "Coverage",
                "Compression",
                "Conflict Clarity",
                "Minority Signal",
                "Traceability",
                "Creatability",
                "Usefulness",
            ],
        )
        self.assertNotIn("question", brief)
        self.assertNotIn("answer_goal", brief)


if __name__ == "__main__":
    unittest.main()
