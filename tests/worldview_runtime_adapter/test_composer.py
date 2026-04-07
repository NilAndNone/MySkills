from __future__ import annotations

import unittest

from worldview_runtime_adapter import composer


def _brief() -> dict[str, object]:
    return {
        "issue": "平台应不应该默认限制匿名爆料帖？",
        "output_intent": "briefing",
        "stance_mode": "neutral_compare",
        "audience": "中文内容创作者",
        "scope": "平台治理",
        "timeframe": "2026",
        "constraints": ["只用中文"],
        "materials": [],
        "meta": {
            "benchmark_topics": ["technology and platform issues"],
            "quality_rubric": ["Coverage"],
            "guardrails": {},
        },
    }


def _role_plan() -> list[dict[str, str]]:
    return [
        {
            "role_id": "fact_extractor",
            "role_name": "Fact Extractor",
            "persona": "external_reference",
            "reason": "facts",
        },
        {
            "role_id": "moral_critic",
            "role_name": "Moral Critic",
            "persona": "humanist_therapist",
            "reason": "values",
        },
        {
            "role_id": "strategist",
            "role_name": "Strategist",
            "persona": "risk_manager",
            "reason": "strategy",
        },
    ]


def _technical_result(
    persona: str,
    factual: str,
    value: str,
    strategy: str,
    signature_line: str,
    confidence: float,
) -> dict[str, object]:
    return {
        "schema_version": "technical_certified_result_v1",
        "persona": persona,
        "technical_status": "TECHNICAL_CERTIFIED",
        "result": {
            "schema_version": "worldview_worker_result_v1",
            "persona": persona,
            "judgment": {
                "factual": factual,
                "value": value,
                "strategy": strategy,
            },
            "diagnosis": [f"{persona} diagnosis"],
            "recommended_actions": [f"{persona} action"],
            "voice_style": "plain",
            "blind_spot": f"{persona} blind spot",
            "overuse_risk": f"{persona} overuse risk",
            "signature_line": signature_line,
            "confidence": confidence,
        },
    }


class TestComposer(unittest.TestCase):
    def test_axis_claim_source_refs_use_real_result_field_paths(self) -> None:
        certified_results = {
            "external_reference": _technical_result("external_reference", "same", "value one", "strategy one", "angle a", 0.91),
            "humanist_therapist": _technical_result("humanist_therapist", "same", "value one", "strategy one", "angle a", 0.86),
            "risk_manager": _technical_result("risk_manager", "different", "value two", "strategy two", "angle b", 0.72),
        }

        content_brief = composer.build_content_brief(
            _brief(),
            _role_plan(),
            certified_results,
            execution_policy="adaptive",
            result_grade="usable",
            run_status="completed_with_failures",
            failed_personas=[],
        )

        fact_claim = next(claim for claim in content_brief["claims"] if claim["claim_id"].startswith("fact_axis"))
        value_claim = next(claim for claim in content_brief["claims"] if claim["claim_id"].startswith("value_axis"))
        strategy_claim = next(claim for claim in content_brief["claims"] if claim["claim_id"].startswith("strategy_axis"))

        self.assertTrue(all(ref.endswith("#result.judgment.factual") for ref in fact_claim["source_refs"]))
        self.assertTrue(all(ref.endswith("#result.judgment.value") for ref in value_claim["source_refs"]))
        self.assertTrue(all(ref.endswith("#result.judgment.strategy") for ref in strategy_claim["source_refs"]))

    def test_majority_bucket_stays_in_consensus(self) -> None:
        certified_results = {
            "external_reference": _technical_result("external_reference", "same", "v1", "s1", "angle a", 0.91),
            "humanist_therapist": _technical_result("humanist_therapist", "same", "v1", "s1", "angle a", 0.86),
            "risk_manager": _technical_result("risk_manager", "different", "v2", "s2", "angle b", 0.72),
        }

        content_brief = composer.build_content_brief(
            _brief(),
            _role_plan(),
            certified_results,
            execution_policy="adaptive",
            result_grade="usable",
            run_status="completed",
            failed_personas=[],
        )

        fact_axis = content_brief["analysis"]["fact_axis"]
        self.assertEqual([claim["text"] for claim in fact_axis["consensus"]], ["same"])
        self.assertEqual([claim["text"] for claim in fact_axis["minority_alerts"]], ["different"])
        self.assertEqual(fact_axis["conflicts"], [])

    def test_tied_signature_lines_do_not_fall_back_to_role_order(self) -> None:
        certified_results = {
            "external_reference": _technical_result("external_reference", "same", "v1", "s1", "angle a", 0.91),
            "humanist_therapist": _technical_result("humanist_therapist", "same", "v1", "s1", "angle b", 0.86),
        }

        content_brief = composer.build_content_brief(
            _brief(),
            _role_plan()[:2],
            certified_results,
            execution_policy="adaptive",
            result_grade="usable",
            run_status="completed",
            failed_personas=[],
        )

        self.assertEqual(content_brief["summary"]["one_line_judgment"], "本轮没有形成单一判断，建议围绕主要分歧组织表达。")
        self.assertEqual(content_brief["recommendations"]["recommended_angle"], "")

    def test_recommendation_claim_only_counts_agreeing_roles(self) -> None:
        certified_results = {
            "external_reference": _technical_result("external_reference", "same", "v1", "s1", "angle a", 0.61),
            "humanist_therapist": _technical_result("humanist_therapist", "same", "v1", "s1", "angle a", 0.64),
            "risk_manager": _technical_result("risk_manager", "same", "v1", "s1", "angle b", 0.95),
        }

        content_brief = composer.build_content_brief(
            _brief(),
            _role_plan(),
            certified_results,
            execution_policy="adaptive",
            result_grade="usable",
            run_status="completed",
            failed_personas=[],
        )

        recommendation_claim = next(
            claim
            for claim in content_brief["claims"]
            if claim["claim_type"] == "recommendation"
        )
        self.assertEqual(recommendation_claim["text"], "angle a")
        self.assertEqual(recommendation_claim["supporting_roles"], ["external_reference", "humanist_therapist"])
        self.assertEqual(recommendation_claim["counter_roles"], ["risk_manager"])
        self.assertAlmostEqual(recommendation_claim["confidence"], 0.64)
        self.assertEqual(recommendation_claim["evidence_strength"], "medium")


if __name__ == "__main__":
    unittest.main()
