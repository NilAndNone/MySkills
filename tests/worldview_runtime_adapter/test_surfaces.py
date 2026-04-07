from __future__ import annotations

import unittest

from worldview_runtime_adapter import composer, surfaces

from tests.worldview_runtime_adapter.test_composer import _brief, _role_plan, _technical_result


class TestSurfaces(unittest.TestCase):
    def test_audit_surface_uses_runtime_facing_success_label(self) -> None:
        content_brief = composer.build_content_brief(
            _brief(),
            _role_plan(),
            {
                "external_reference": _technical_result("external_reference", "same", "v1", "s1", "angle a", 0.91),
                "humanist_therapist": _technical_result("humanist_therapist", "same", "v1", "s1", "angle a", 0.86),
                "risk_manager": _technical_result("risk_manager", "same", "v1", "s1", "angle a", 0.82),
            },
            execution_policy="adaptive",
            result_grade="usable",
            run_status="completed",
            failed_personas=[],
        )

        audit = surfaces.build_audit_surface(
            content_brief,
            successful_personas=["external_reference", "humanist_therapist", "risk_manager"],
            failed_personas=[],
            round_root="/tmp/example-round",
        )

        self.assertEqual(audit["status"]["label"], "quorum passed")

    def test_build_studio_surface_uses_product_sections(self) -> None:
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
            run_status="completed_with_failures",
            failed_personas=[{"persona": "cynical_detached", "failure_reason": "bad output"}],
        )

        studio = surfaces.build_studio_surface(content_brief)

        self.assertEqual(studio["schema_version"], "studio_surface_v1")
        self.assertEqual(studio["status"]["label"], "可用")
        self.assertEqual(studio["executive_judgment"]["one_line_judgment"], "angle a")
        self.assertEqual(len(studio["tension_map"]["fact_axis"]["consensus"]), 1)
        self.assertEqual(len(studio["perspective_cards"]), 3)
        self.assertEqual(studio["creation_layer"]["recommended_angle"], "angle a")

    def test_build_audit_surface_keeps_runtime_and_claim_risks_visible(self) -> None:
        certified_results = {
            "external_reference": _technical_result("external_reference", "same", "v1", "s1", "angle a", 0.91),
            "humanist_therapist": _technical_result("humanist_therapist", "same", "v1", "s1", "angle a", 0.86),
        }
        content_brief = composer.build_content_brief(
            _brief(),
            _role_plan()[:2],
            certified_results,
            execution_policy="adaptive",
            result_grade="degraded",
            run_status="completed_with_failures",
            failed_personas=[{"persona": "risk_manager", "failure_reason": "invalid_json_schema", "failure_class": "protocol_schema_error"}],
        )

        audit = surfaces.build_audit_surface(
            content_brief,
            successful_personas=["external_reference", "humanist_therapist"],
            failed_personas=[{"persona": "risk_manager", "failure_reason": "invalid_json_schema", "failure_class": "protocol_schema_error"}],
            round_root="/tmp/example-round",
        )

        self.assertEqual(audit["schema_version"], "audit_surface_v1")
        self.assertEqual(audit["status"]["label"], "adaptive degraded")
        self.assertEqual(audit["execution"]["run_status"], "completed_with_failures")
        self.assertEqual(audit["execution"]["failed_personas"][0]["persona"], "risk_manager")
        self.assertTrue(isinstance(audit["claims_with_weak_evidence"], list))


if __name__ == "__main__":
    unittest.main()
