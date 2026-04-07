from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from worldview_runtime_adapter import review_viewer


class TestReviewViewer(unittest.TestCase):
    def test_build_round_payload_ignores_stale_product_surfaces_for_blocked_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = Path(tmpdir) / "round"
            round_root.mkdir(parents=True)
            (round_root / "round_input.json").write_text(
                json.dumps({"issue": "带旧文件的 blocked 测试"}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (round_root / "runtime_adapter").mkdir(parents=True)
            (round_root / "runtime_adapter" / "run_summary.json").write_text(
                json.dumps(
                    {
                        "run_id": "wv-round-blocked-stale",
                        "run_status": "completed_with_failures",
                        "panel_emitted": False,
                        "result_grade": "blocked",
                        "execution_policy": "adaptive",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (round_root / "runtime_adapter" / "failure_summary.json").write_text(
                json.dumps(
                    {
                        "failed_personas": ["risk_manager"],
                        "message": "successful roles did not reach the minimum ratio required for content brief generation",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (round_root / "content_brief.json").write_text(
                json.dumps(
                    {
                        "issue": {"title": "stale title", "question": "stale question"},
                        "meta": {
                            "execution_summary": {
                                "run_id": "stale-run",
                                "run_status": "completed",
                                "execution_policy": "adaptive",
                                "result_grade": "usable",
                                "successful_personas": ["external_reference"],
                                "failed_personas": [],
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (round_root / "studio_surface.json").write_text(
                json.dumps(
                    {
                        "schema_version": "studio_surface_v1",
                        "status": {"label": "可用", "result_grade": "usable"},
                        "executive_judgment": {"one_line_judgment": "stale"},
                        "perspective_cards": [{"persona": "external_reference", "signature_line": "stale"}],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (round_root / "audit_surface.json").write_text(
                json.dumps(
                    {
                        "schema_version": "audit_surface_v1",
                        "status": {"label": "adaptive usable", "result_grade": "usable"},
                        "execution": {
                            "run_status": "completed",
                            "execution_policy": "adaptive",
                            "successful_personas": ["external_reference"],
                            "failed_personas": [],
                        },
                        "round_root": str(round_root),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            payload = review_viewer.build_round_payload(round_root)

            self.assertEqual(payload["default_surface"], "audit")
            self.assertIsNone(payload["studio"])
            self.assertEqual(payload["audit"]["status"]["label"], "quorum failed")
            self.assertEqual(payload["audit"]["status"]["result_grade"], "blocked")
            self.assertEqual(payload["audit"]["execution"]["failed_personas"][0]["persona"], "risk_manager")

    def test_build_round_payload_ignores_stale_product_surfaces_for_old_format_blocked_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = Path(tmpdir) / "round"
            round_root.mkdir(parents=True)
            (round_root / "round_input.json").write_text(
                json.dumps({"issue": "旧格式 blocked 测试"}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (round_root / "runtime_adapter").mkdir(parents=True)
            (round_root / "runtime_adapter" / "run_summary.json").write_text(
                json.dumps(
                    {
                        "run_id": "wv-round-old-blocked",
                        "run_status": "completed_with_failures",
                        "panel_emitted": False,
                        "execution_policy": "adaptive",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (round_root / "runtime_adapter" / "failure_summary.json").write_text(
                json.dumps(
                    {
                        "failed_personas": [{"persona": "risk_manager", "failure_reason": "schema", "failure_class": "protocol_schema_error"}],
                        "message": "successful roles did not reach the minimum ratio required for content brief generation",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (round_root / "content_brief.json").write_text(
                json.dumps(
                    {
                        "issue": {"title": "stale title", "question": "stale question"},
                        "meta": {
                            "execution_summary": {
                                "run_id": "stale-run",
                                "run_status": "completed",
                                "execution_policy": "adaptive",
                                "result_grade": "usable",
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (round_root / "studio_surface.json").write_text(
                json.dumps(
                    {
                        "schema_version": "studio_surface_v1",
                        "status": {"label": "可用", "result_grade": "usable"},
                        "executive_judgment": {"one_line_judgment": "stale"},
                        "perspective_cards": [{"persona": "external_reference", "signature_line": "stale"}],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (round_root / "audit_surface.json").write_text(
                json.dumps(
                    {
                        "schema_version": "audit_surface_v1",
                        "status": {"label": "adaptive usable", "result_grade": "usable"},
                        "execution": {
                            "run_status": "completed",
                            "execution_policy": "adaptive",
                            "successful_personas": ["external_reference"],
                            "failed_personas": [],
                        },
                        "round_root": str(round_root),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            payload = review_viewer.build_round_payload(round_root)

            self.assertEqual(payload["default_surface"], "audit")
            self.assertIsNone(payload["studio"])
            self.assertEqual(payload["audit"]["status"]["label"], "quorum failed")
            self.assertEqual(payload["audit"]["execution"]["failed_personas"][0]["persona"], "risk_manager")

    def test_build_round_payload_reads_strict_blocked_fallback_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = Path(tmpdir) / "round"
            round_root.mkdir(parents=True)
            (round_root / "round_input.json").write_text(
                json.dumps({"issue": "严格阻断测试"}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (round_root / "runtime_adapter").mkdir(parents=True)
            (round_root / "runtime_adapter" / "run_summary.json").write_text(
                json.dumps(
                    {
                        "run_id": "wv-round-strict-blocked",
                        "run_status": "failed",
                        "panel_emitted": False,
                        "result_grade": "blocked",
                        "execution_policy": "strict",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (round_root / "runtime_adapter" / "failure_summary.json").write_text(
                json.dumps(
                    {
                        "failed_personas": ["risk_manager"],
                        "message": "successful roles did not reach the minimum ratio required for content brief generation",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            payload = review_viewer.build_round_payload(round_root)

            self.assertEqual(payload["default_surface"], "audit")
            self.assertIsNone(payload["studio"])
            self.assertEqual(payload["audit"]["status"]["label"], "strict fail closed")
            self.assertIsInstance(payload["audit"]["execution"]["failed_personas"][0], dict)
            self.assertEqual(payload["audit"]["execution"]["failed_personas"][0]["persona"], "risk_manager")

    def test_build_round_payload_reads_blocked_run_without_product_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = Path(tmpdir) / "round"
            round_root.mkdir(parents=True)
            (round_root / "round_input.json").write_text(
                json.dumps({"issue": "这是 blocked 测试问题"}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (round_root / "runtime_adapter").mkdir(parents=True)
            (round_root / "runtime_adapter" / "run_summary.json").write_text(
                json.dumps(
                    {
                        "run_id": "wv-round-blocked",
                        "run_status": "completed_with_failures",
                        "panel_emitted": False,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (round_root / "runtime_adapter" / "failure_summary.json").write_text(
                json.dumps(
                    {
                        "failed_personas": ["risk_manager"],
                        "message": "successful roles did not reach the minimum ratio required for content brief generation",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            payload = review_viewer.build_round_payload(round_root)

            self.assertEqual(payload["question"], "这是 blocked 测试问题")
            self.assertEqual(payload["default_surface"], "audit")
            self.assertIsNone(payload["studio"])
            self.assertEqual(payload["audit"]["status"]["result_grade"], "blocked")

    def test_build_round_payload_collects_product_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = self._create_round_fixture(Path(tmpdir) / "round")

            payload = review_viewer.build_round_payload(round_root)

            self.assertEqual(payload["question"], "这是测试问题")
            self.assertEqual(payload["default_surface"], "studio")
            self.assertEqual(payload["studio"]["status"]["label"], "可用")
            self.assertEqual(payload["studio"]["executive_judgment"]["one_line_judgment"], "签名")
            self.assertEqual(payload["audit"]["execution"]["successful_personas"], ["external_reference"])
            self.assertEqual(
                payload["view_state"],
                {
                    "default_surface": "studio",
                    "studio_available": True,
                    "audit_available": True,
                },
            )

    def test_build_round_payload_keeps_studio_as_default_surface_for_degraded_round(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = self._create_degraded_round_fixture(Path(tmpdir) / "round")

            payload = review_viewer.build_round_payload(round_root)

            self.assertEqual(payload["default_surface"], "studio")
            self.assertIsNotNone(payload["studio"])
            self.assertEqual(payload["studio"]["status"]["result_grade"], "degraded")
            self.assertEqual(payload["view_state"]["default_surface"], "studio")
            self.assertTrue(payload["view_state"]["studio_available"])

    def test_build_round_payload_defaults_blocked_rounds_to_audit_with_no_studio_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = self._create_blocked_round_fixture(Path(tmpdir) / "round")

            payload = review_viewer.build_round_payload(round_root)

            self.assertEqual(payload["default_surface"], "audit")
            self.assertIsNone(payload["studio"])
            self.assertEqual(payload["audit"]["status"]["result_grade"], "blocked")
            self.assertEqual(
                payload["view_state"],
                {
                    "default_surface": "audit",
                    "studio_available": False,
                    "audit_available": True,
                },
            )

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
            self.assertIn("studio-summary", html)
            self.assertIn("audit-panel", html)
            self.assertIn("title.textContent", html)
            self.assertIn("body.textContent", html)
            self.assertNotIn("innerHTML", html)
            self.assertIn("payload.view_state", html)
            self.assertIn("viewState.default_surface", html)
            self.assertIn("viewState.studio_available", html)

            data = json.loads(data_path.read_text(encoding="utf-8"))
            self.assertEqual(data["question"], "这是测试问题")
            self.assertEqual(data["studio"]["status"]["label"], "可用")
            self.assertEqual(data["view_state"]["default_surface"], "studio")
            self.assertTrue(data["view_state"]["studio_available"])

    def test_write_static_viewer_renders_surface_switcher_and_studio_first_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            round_root = self._create_round_fixture(root / "round")
            output_dir = root / "viewer"

            review_viewer.write_static_viewer(round_root, output_dir)

            html = (output_dir / "index.html").read_text(encoding="utf-8")
            self.assertIn('data-surface="studio"', html)
            self.assertIn('data-surface="audit"', html)
            self.assertIn('id="surface-switcher"', html)
            self.assertIn("Executive Judgment", html)
            self.assertIn("Tension Map", html)
            self.assertIn("Creation Layer", html)
            self.assertIn("Writing Moves", html)
            self.assertIn('id="studio-surface"', html)
            self.assertIn('id="audit-surface"', html)
            self.assertIn('id="surface-toggle-studio"', html)
            self.assertIn('id="surface-toggle-audit"', html)

    def test_write_static_viewer_wires_blocked_view_state_into_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            round_root = self._create_blocked_round_fixture(root / "round")
            output_dir = root / "viewer"

            review_viewer.write_static_viewer(round_root, output_dir)

            html = (output_dir / "index.html").read_text(encoding="utf-8")
            data = json.loads((output_dir / "data.json").read_text(encoding="utf-8"))

            self.assertEqual(data["view_state"]["default_surface"], "audit")
            self.assertFalse(data["view_state"]["studio_available"])
            self.assertIn("studioButton.disabled = !viewState.studio_available", html)
            self.assertIn('activateSurface(viewState.default_surface)', html)

    def test_build_round_payload_keeps_failed_personas_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = self._create_degraded_round_fixture(Path(tmpdir) / "round")

            payload = review_viewer.build_round_payload(round_root)

            self.assertEqual(payload["run_status"], "completed_with_failures")
            self.assertTrue(payload["panel_emitted"])
            self.assertEqual(payload["default_surface"], "studio")
            self.assertEqual(payload["audit"]["execution"]["failed_personas"][0]["persona"], "risk_manager")
            self.assertEqual(payload["audit"]["status"]["label"], "adaptive degraded")

    def test_build_round_payload_reads_blocked_run_from_runtime_adapter_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = self._create_blocked_round_fixture(Path(tmpdir) / "round")

            payload = review_viewer.build_round_payload(round_root)

            self.assertEqual(payload["question"], "这是 blocked 测试问题")
            self.assertEqual(payload["run_status"], "completed_with_failures")
            self.assertFalse(payload["panel_emitted"])
            self.assertEqual(payload["failure_summary"]["failed_personas"], ["risk_manager"])
            self.assertEqual(payload["audit"]["execution"]["failed_personas"][0]["persona"], "risk_manager")
            self.assertEqual(payload["audit"]["status"]["label"], "quorum failed")

    def _create_round_fixture(self, round_root: Path) -> Path:
        round_root.mkdir(parents=True)
        (round_root / "content_brief.json").write_text(
            json.dumps(
                {
                    "schema_version": "content_brief_v1",
                    "issue": {
                        "title": "这是测试问题",
                        "question": "这是测试问题",
                        "scope": "",
                        "timeframe": "",
                    },
                    "summary": {
                        "one_line_judgment": "签名",
                        "premises": ["事实段落"],
                        "best_use": "先做 briefing",
                        "largest_risk": "r",
                    },
                    "analysis": {
                        "fact_axis": {"consensus": [], "conflicts": [], "minority_alerts": []},
                        "value_axis": {"consensus": [], "conflicts": [], "minority_alerts": []},
                        "strategy_axis": {"consensus": [], "conflicts": [], "minority_alerts": []},
                    },
                    "recommendations": {
                        "recommended_angle": "签名",
                        "writing_moves": ["动作 1"],
                        "research_gaps": ["补材料"],
                    },
                    "writing_assets": {
                        "article_outline": ["一、开场"],
                        "video_outline": ["先说判断"],
                        "thread_outline": ["1/ 先抛问题"],
                    },
                    "claims": [],
                    "meta": {
                        "execution_summary": {
                            "run_id": "wv-round-test",
                            "run_status": "completed",
                            "execution_policy": "adaptive",
                            "result_grade": "usable",
                            "successful_personas": ["external_reference"],
                            "failed_personas": [],
                            "perspective_cards": [
                                {
                                    "persona": "external_reference",
                                    "role_id": "fact_extractor",
                                    "signature_line": "签名",
                                    "strongest_insight": "诊断 1",
                                    "largest_blind_spot": "b",
                                    "fit_condition": "动作 1",
                                }
                            ],
                        }
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (round_root / "studio_surface.json").write_text(
            json.dumps(
                {
                    "schema_version": "studio_surface_v1",
                    "status": {"label": "可用", "result_grade": "usable"},
                    "executive_judgment": {
                        "one_line_judgment": "签名",
                        "premises": ["事实段落"],
                        "best_use": "先做 briefing",
                        "largest_risk": "r",
                    },
                    "tension_map": {
                        "fact_axis": {"consensus": [], "conflicts": [], "minority_alerts": []},
                        "value_axis": {"consensus": [], "conflicts": [], "minority_alerts": []},
                        "strategy_axis": {"consensus": [], "conflicts": [], "minority_alerts": []},
                    },
                    "perspective_cards": [
                        {
                            "persona": "external_reference",
                            "signature_line": "签名",
                            "strongest_insight": "诊断 1",
                            "largest_blind_spot": "b",
                            "fit_condition": "动作 1",
                        }
                    ],
                    "creation_layer": {
                        "recommended_angle": "签名",
                        "writing_moves": ["动作 1"],
                        "article_outline": ["一、开场"],
                        "video_outline": ["先说判断"],
                        "thread_outline": ["1/ 先抛问题"],
                        "research_gaps": ["补材料"],
                    },
                    "expandable_trace": {"claims": [], "materials": []},
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (round_root / "audit_surface.json").write_text(
            json.dumps(
                {
                    "schema_version": "audit_surface_v1",
                    "status": {"label": "adaptive usable", "result_grade": "usable"},
                    "execution": {
                        "run_status": "completed",
                        "execution_policy": "adaptive",
                        "successful_personas": ["external_reference"],
                        "failed_personas": [],
                    },
                    "claims_with_weak_evidence": [],
                    "round_root": str(round_root),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return round_root

    def _create_degraded_round_fixture(self, round_root: Path) -> Path:
        self._create_round_fixture(round_root)
        payload = json.loads((round_root / "content_brief.json").read_text(encoding="utf-8"))
        payload["meta"]["execution_summary"]["run_status"] = "completed_with_failures"
        payload["meta"]["execution_summary"]["result_grade"] = "degraded"
        payload["meta"]["execution_summary"]["failed_personas"] = [
            {
                "persona": "risk_manager",
                "failure_reason": "invalid_json_schema",
                "failure_class": "protocol_schema_error",
            }
        ]
        (round_root / "content_brief.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        studio = json.loads((round_root / "studio_surface.json").read_text(encoding="utf-8"))
        studio["status"] = {"label": "可用但降级", "result_grade": "degraded"}
        (round_root / "studio_surface.json").write_text(json.dumps(studio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        audit = json.loads((round_root / "audit_surface.json").read_text(encoding="utf-8"))
        audit["status"] = {"label": "adaptive degraded", "result_grade": "degraded"}
        audit["execution"]["run_status"] = "completed_with_failures"
        audit["execution"]["failed_personas"] = [
            {
                "persona": "risk_manager",
                "failure_reason": "invalid_json_schema",
                "failure_class": "protocol_schema_error",
            }
        ]
        (round_root / "audit_surface.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return round_root

    def _create_blocked_round_fixture(self, round_root: Path) -> Path:
        round_root.mkdir(parents=True)
        (round_root / "round_input.json").write_text(
            json.dumps({"issue": "这是 blocked 测试问题"}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (round_root / "runtime_adapter").mkdir(parents=True)
        (round_root / "runtime_adapter" / "run_summary.json").write_text(
            json.dumps(
                {
                    "run_id": "wv-round-blocked",
                    "round_root": str(round_root),
                    "run_status": "completed_with_failures",
                    "panel_emitted": False,
                    "persona_total": 1,
                    "successful_persona_count": 0,
                    "failed_persona_count": 1,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (round_root / "runtime_adapter" / "failure_summary.json").write_text(
            json.dumps(
                {
                    "success_ratio": 0.0,
                    "minimum_success_ratio": 0.67,
                    "successful_persona_count": 0,
                    "failed_personas": ["risk_manager"],
                    "message": "successful roles did not reach the minimum ratio required for content brief generation",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (round_root / "content_brief.json").write_text(
            json.dumps(
                {
                    "schema_version": "content_brief_v1",
                    "issue": {
                        "title": "这是 blocked 测试问题",
                        "question": "这是 blocked 测试问题",
                        "scope": "",
                        "timeframe": "",
                    },
                    "summary": {
                        "one_line_judgment": "",
                        "premises": [],
                        "best_use": "",
                        "largest_risk": "结果不足，不建议直接使用。",
                    },
                    "analysis": {
                        "fact_axis": {"consensus": [], "conflicts": [], "minority_alerts": []},
                        "value_axis": {"consensus": [], "conflicts": [], "minority_alerts": []},
                        "strategy_axis": {"consensus": [], "conflicts": [], "minority_alerts": []},
                    },
                    "recommendations": {
                        "recommended_angle": "",
                        "writing_moves": [],
                        "research_gaps": ["先补关键材料"],
                    },
                    "writing_assets": {"article_outline": [], "video_outline": [], "thread_outline": []},
                    "claims": [],
                    "meta": {
                        "execution_summary": {
                            "run_id": "wv-round-blocked",
                            "run_status": "completed_with_failures",
                            "execution_policy": "adaptive",
                            "result_grade": "blocked",
                            "successful_personas": [],
                            "failed_personas": [
                                {
                                    "persona": "risk_manager",
                                    "failure_reason": "invalid_json_schema",
                                    "failure_class": "protocol_schema_error",
                                }
                            ],
                            "perspective_cards": [],
                        }
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (round_root / "studio_surface.json").write_text(
            json.dumps(
                {
                    "schema_version": "studio_surface_v1",
                    "status": {"label": "本轮不建议使用", "result_grade": "blocked"},
                    "executive_judgment": {
                        "one_line_judgment": "",
                        "premises": [],
                        "best_use": "",
                        "largest_risk": "结果不足，不建议直接使用。",
                    },
                    "tension_map": {
                        "fact_axis": {"consensus": [], "conflicts": [], "minority_alerts": []},
                        "value_axis": {"consensus": [], "conflicts": [], "minority_alerts": []},
                        "strategy_axis": {"consensus": [], "conflicts": [], "minority_alerts": []},
                    },
                    "perspective_cards": [],
                    "creation_layer": {
                        "recommended_angle": "",
                        "writing_moves": [],
                        "article_outline": [],
                        "video_outline": [],
                        "thread_outline": [],
                        "research_gaps": ["先补关键材料"],
                    },
                    "expandable_trace": {"claims": [], "materials": []},
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (round_root / "audit_surface.json").write_text(
            json.dumps(
                {
                    "schema_version": "audit_surface_v1",
                    "status": {"label": "quorum failed", "result_grade": "blocked"},
                    "execution": {
                        "run_status": "completed_with_failures",
                        "execution_policy": "adaptive",
                        "successful_personas": [],
                        "failed_personas": [
                            {
                                "persona": "risk_manager",
                                "failure_reason": "invalid_json_schema",
                                "failure_class": "protocol_schema_error",
                            }
                        ],
                    },
                    "claims_with_weak_evidence": [],
                    "round_root": str(round_root),
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
