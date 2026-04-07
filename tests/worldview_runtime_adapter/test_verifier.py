from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from worldview_runtime_adapter import verifier


class TestVerifier(unittest.TestCase):
    def test_verify_round_accepts_blocked_round_without_product_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = self._create_blocked_round_fixture(Path(tmpdir) / "round")

            verdict = verifier.verify_round(round_root)

            self.assertTrue(verdict["ok"])
            self.assertEqual(verdict["errors"], [])

    def test_verify_round_fails_when_claim_trace_target_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            round_root = self._create_usable_round_fixture(Path(tmpdir) / "round")
            payload = json.loads((round_root / "content_brief.json").read_text(encoding="utf-8"))
            payload["meta"]["trace_refs"] = {
                "claims": {
                    "fact_axis-consensus-1": [
                        "results/missing_persona/technical_certified_result.json#result.judgment.factual"
                    ]
                }
            }
            (round_root / "content_brief.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            verdict = verifier.verify_round(round_root)

            self.assertFalse(verdict["ok"])
            self.assertIn(
                "missing claim trace target: results/missing_persona/technical_certified_result.json",
                verdict["errors"],
            )

    def _create_usable_round_fixture(self, round_root: Path) -> Path:
        round_root.mkdir(parents=True)
        (round_root / "runtime_adapter").mkdir(parents=True)
        (round_root / "round_input.json").write_text(
            json.dumps({"issue": "测试议题"}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (round_root / "dispatch_job.json").write_text(
            json.dumps({"schema_version": "dispatch_job_v1"}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (round_root / "content_brief.json").write_text(
            json.dumps(
                {
                    "schema_version": "content_brief_v1",
                    "summary": {"one_line_judgment": "一句话判断"},
                    "meta": {
                        "execution_summary": {
                            "run_status": "completed",
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
                    "status": {"result_grade": "usable"},
                    "executive_judgment": {"one_line_judgment": "一句话判断"},
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
                    "status": {"result_grade": "usable"},
                    "execution": {"run_status": "completed"},
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (round_root / "runtime_adapter" / "run_summary.json").write_text(
            json.dumps(
                {
                    "run_status": "completed",
                    "result_grade": "usable",
                    "panel_emitted": True,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return round_root

    def _create_blocked_round_fixture(self, round_root: Path) -> Path:
        round_root.mkdir(parents=True)
        (round_root / "runtime_adapter").mkdir(parents=True)
        (round_root / "round_input.json").write_text(
            json.dumps({"issue": "被阻塞议题"}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (round_root / "dispatch_job.json").write_text(
            json.dumps({"schema_version": "dispatch_job_v1"}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (round_root / "runtime_adapter" / "run_summary.json").write_text(
            json.dumps(
                {
                    "run_status": "blocked",
                    "result_grade": "blocked",
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
                    "result_grade": "blocked",
                    "failed_personas": ["risk_manager"],
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
