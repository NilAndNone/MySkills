from __future__ import annotations

import unittest

from worldview_runtime_adapter import role_planner


class TestRolePlanner(unittest.TestCase):
    def test_role_planner_uses_minimum_sufficient_subset_before_expansion(self) -> None:
        brief = {
            "issue": "平台应不应该默认限制匿名爆料帖？",
            "output_intent": "briefing",
            "stance_mode": "lean_support",
            "materials": [],
            "scope": "",
            "timeframe": "",
        }

        role_plan = role_planner.plan_roles(brief)

        self.assertEqual(
            [entry["role_id"] for entry in role_plan],
            ["fact_extractor", "moral_critic", "strategist"],
        )


if __name__ == "__main__":
    unittest.main()
