from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "src" / "skills" / "worldview-panel-codex" / "tools"
REPORT_UI_DIR = REPO_ROOT / "src" / "resume_panel_materials"
sys.path.insert(0, str(TOOLS_DIR))

from panel_site_common import build_render_payload, export_panel_cache, render_site_bundle  # noqa: E402


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class PanelSiteCommonTests(unittest.TestCase):
    def test_report_template_uses_neutral_summary_copy(self) -> None:
        html = (REPORT_UI_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn("解释力强但不宜照做", html)
        self.assertIn("虽然难听但有操作性", html)
        self.assertIn("最该借的人格", html)
        self.assertIn("把最值得保留的提醒、最能落地的动作和最该借的视角排清楚", html)
        self.assertNotIn("支持原观点", html)
        self.assertNotIn("反对原观点", html)
        self.assertNotIn("谁在支持、谁在抗辩、谁在把问题转到别处", html)

    def test_frontend_script_keeps_conditional_badge_but_drops_unlabeled_fallback(self) -> None:
        script = (REPORT_UI_DIR / "site.js").read_text(encoding="utf-8")

        self.assertIn("条件回答", script)
        self.assertNotIn("未标注", script)

    def test_build_render_payload_prefers_new_structured_report_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            md_root = Path(tmpdir)
            (md_root / "builders").mkdir()
            (md_root / "critics").mkdir()
            (md_root / "builders" / "existentialist.md").write_text(
                "[人格]\n存在主义者\n\n[核心判断]\n旧正文里的核心判断。\n\n[问题诊断]\n旧正文里的问题诊断。\n",
                encoding="utf-8",
            )
            (md_root / "critics" / "collapse_prophet.md").write_text(
                "[人格]\n崩坏预言家\n\n[核心判断]\n另一段旧正文。\n\n[问题诊断]\n另一段问题诊断。\n",
                encoding="utf-8",
            )
            write_json(
                md_root / "meta.json",
                {
                    "title": "测试页",
                    "description": "描述",
                    "question": "问题",
                    "consensus": ["共识"],
                    "risks": ["风险"],
                    "quote": "引言",
                },
            )
            write_json(
                md_root / "report.json",
                {
                    "report_id": "demo",
                    "report_summary": {
                        "common_ground": ["都承认 AI 已经碰到身份认证"],
                        "biggest_split": ["到底该不该把这视为正常协作"],
                        "strong_but_risky": ["把 AI 当作身份认证边界松动的放大器，解释力强，但不能直接拿去一刀切。"],
                        "harsh_but_actionable": ["别只争论工具纯不纯，先把责任归属、验证环节和使用边界写死。"],
                        "recommended_lenses": [
                            {
                                "slug": "existentialist",
                                "reason": "适合拿来判断“工具协作”和“本人签字”该怎么拆。",
                            },
                            {
                                "slug": "collapse_prophet",
                                "reason": "适合提醒旧制度本身也在漏电。",
                            },
                        ],
                    },
                    "groups": [
                        {
                            "group": "builders",
                            "stance": "要重写规则，不是假装 AI 不存在。",
                            "conflict": "重点在协作与认证怎么拆开。",
                            "split": "内部差异主要在愿不愿意保留强认证环节。",
                        },
                        {
                            "group": "critics",
                            "stance": "这场争论暴露的是旧制度早就虚了。",
                            "conflict": "重点在招聘本来就依赖包装信号。",
                            "split": "内部差异主要在批判制度还是批判组织。",
                        },
                    ],
                    "personas": [
                        {
                            "slug": "existentialist",
                            "stance": "问题不在工具，在谁为结果签字。",
                            "conflict": "不能把“我是这个人”也一起外包出去。",
                            "answer_status": "complete",
                            "content": "ignored",
                        },
                        {
                            "slug": "collapse_prophet",
                            "stance": "AI 只是把旧制度的虚假信号放大了。",
                            "conflict": "真正崩的是招聘机器，不只是工具边界。",
                            "answer_status": "conditional",
                            "answer_status_note": "缺少具体招聘流程材料，只能做条件判断。",
                            "content": "ignored",
                        },
                    ],
                },
            )

            payload = build_render_payload(md_root)

            existentialist = next(item for item in payload["personas"] if item["slug"] == "existentialist")
            self.assertEqual(existentialist["position"], "")
            self.assertEqual(existentialist["stance"], "问题不在工具，在谁为结果签字。")
            self.assertEqual(existentialist["conflict"], "不能把“我是这个人”也一起外包出去。")
            self.assertEqual(existentialist["answer_status"], "complete")

            builders = next(item for item in payload["groups"] if item["slug"] == "builders")
            self.assertEqual(builders["stance"], "要重写规则，不是假装 AI 不存在。")
            self.assertEqual(builders["conflict"], "重点在协作与认证怎么拆开。")
            self.assertEqual(builders["split"], "内部差异主要在愿不愿意保留强认证环节。")

            self.assertEqual(
                payload["report_summary"]["strong_but_risky"],
                ["把 AI 当作身份认证边界松动的放大器，解释力强，但不能直接拿去一刀切。"],
            )
            self.assertEqual(
                payload["report_summary"]["recommended_lenses"][0]["slug"],
                "existentialist",
            )

    def test_build_render_payload_does_not_infer_position_when_report_json_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            md_root = Path(tmpdir)
            (md_root / "builders").mkdir()
            (md_root / "builders" / "existentialist.md").write_text(
                "[人格]\n你是存在主义者。\n\n"
                "[核心判断]\n这段话大体成立，但真正关键的是谁来承担后果。\n\n"
                "[问题诊断]\n真正的矛盾是效率工具和责任归属在同一个面试场景里撞车了。\n\n"
                "[签名句]\n别拿工具替自己签名。\n",
                encoding="utf-8",
            )
            write_json(
                md_root / "meta.json",
                {
                    "title": "测试页",
                    "description": "描述",
                    "question": "问题",
                    "consensus": [],
                    "risks": [],
                    "quote": "",
                },
            )

            payload = build_render_payload(md_root)
            existentialist = payload["personas"][0]

            self.assertEqual(existentialist["stance"], "这段话大体成立，但真正关键的是谁来承担后果。")
            self.assertEqual(existentialist["conflict"], "真正的矛盾是效率工具和责任归属在同一个面试场景里撞车了。")
            self.assertEqual(existentialist["position"], "")
            self.assertEqual(existentialist["answer_status"], "complete")

            builders = payload["groups"][0]
            self.assertTrue(builders["stance"])
            self.assertTrue(builders["conflict"])

    def test_export_panel_cache_preserves_new_report_summary_and_persona_status_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report_root = export_panel_cache(
                {
                    "report_id": "debate-demo",
                    "meta": {
                        "title": "标题",
                        "description": "描述",
                        "question": "问题",
                        "consensus": ["共识"],
                        "risks": ["风险"],
                        "quote": "引言",
                    },
                    "report_summary": {
                        "common_ground": ["都承认身份认证被碰到了"],
                        "biggest_split": ["要不要把实时 AI 视为代答"],
                        "strong_but_risky": ["把所有辅助都直接定性成作弊，解释力强，但容易误伤正常协作。"],
                        "harsh_but_actionable": ["先把责任签字和验证环节写死，再谈工具边界。"],
                        "recommended_lenses": [
                            {
                                "slug": "existentialist",
                                "reason": "适合优先看谁在为结果签字。",
                            }
                        ],
                    },
                    "groups": [
                        {
                            "group": "builders",
                            "stance": "建设派总立场",
                            "conflict": "建设派冲突",
                            "split": "建设派内部差异",
                        }
                    ],
                    "personas": [
                        {
                            "slug": "existentialist",
                            "stance": "存在主义者立场",
                            "conflict": "存在主义者分歧",
                            "answer_status": "conditional",
                            "answer_status_note": "缺少责任归属的明确材料。",
                            "content": "[人格]\n存在主义者\n\n[核心判断]\n详细观点\n",
                        }
                    ],
                },
                output_root=Path(tmpdir) / "debate-demo",
            )

            report_payload = json.loads((report_root / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report_payload["personas"][0]["position"], "")
            self.assertEqual(report_payload["personas"][0]["stance"], "存在主义者立场")
            self.assertEqual(report_payload["personas"][0]["answer_status"], "conditional")
            self.assertEqual(report_payload["groups"][0]["conflict"], "建设派冲突")
            self.assertEqual(report_payload["report_summary"]["biggest_split"], ["要不要把实时 AI 视为代答"])
            self.assertEqual(
                report_payload["report_summary"]["recommended_lenses"][0]["reason"],
                "适合优先看谁在为结果签字。",
            )

    def test_render_site_bundle_uses_courtroom_landmarks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            md_root = Path(tmpdir)
            (md_root / "builders").mkdir()
            (md_root / "critics").mkdir()
            (md_root / "builders" / "existentialist.md").write_text(
                "[人格]\n存在主义者\n\n[核心判断]\n问题不在工具，而在谁替结果签字。\n\n[问题诊断]\n当表达和责任被拆开，身份认证就开始变形。\n",
                encoding="utf-8",
            )
            (md_root / "critics" / "collapse_prophet.md").write_text(
                "[人格]\n崩坏预言家\n\n[核心判断]\nAI 只是把旧制度的虚假信号放大了。\n\n[问题诊断]\n真正崩的是招聘机器，不只是工具边界。\n",
                encoding="utf-8",
            )
            write_json(
                md_root / "meta.json",
                {
                    "title": "测试页",
                    "description": "描述",
                    "question": "问题",
                    "consensus": ["这是身份认证问题"],
                    "risks": ["辅助边界怎么划"],
                    "quote": "法庭只是在给旧争议换一个更硬的灯光。",
                },
            )

            site_index = render_site_bundle(md_root, preset="satire")
            html = site_index.read_text(encoding="utf-8")

            self.assertIn('class="hero-casefiles"', html)
            self.assertIn('class="verdict-band section"', html)
            self.assertIn('id="camp-sidebar"', html)
            self.assertIn('id="camp-detail-stage"', html)


if __name__ == "__main__":
    unittest.main()
