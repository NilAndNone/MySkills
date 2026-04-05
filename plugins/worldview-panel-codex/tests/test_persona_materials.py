from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
PERSONAS_JSON = REPO_ROOT / "runtime" / "persona-index.json"
PERSONAS_ROOT = REPO_ROOT / "runtime" / "personas"
SKILL_PATH = REPO_ROOT / "skills" / "worldview-panel-entry" / "SKILL.md"
OPENAI_AGENT_PATH = REPO_ROOT / "skills" / "worldview-panel-entry" / "agents" / "openai.yaml"
ROUTING_MATRIX_PATH = REPO_ROOT / "skills" / "worldview-panel-entry" / "references" / "routing-matrix.md"
USER_GUIDE_PATH = REPO_ROOT / "docs" / "user" / "USER_GUIDE.md"
PROFILE_FIELDS = (
    "archetypes",
    "communities",
    "reading_list",
    "thinking_habits",
    "emotional_triggers",
    "rhetorical_weapons",
)
REF_FILENAMES = (
    "career.md",
    "startup.md",
    "product.md",
    "relationship.md",
    "politics.md",
    "philosophy.md",
    "public_discourse.md",
    "psychology.md",
)


def load_persona_materials_module(test_case: unittest.TestCase):
    module_path = TOOLS_DIR / "persona_materials.py"
    test_case.assertTrue(module_path.is_file(), "persona_materials.py should exist in the worldview tools directory.")

    spec = importlib.util.spec_from_file_location("persona_materials", module_path)
    test_case.assertIsNotNone(spec)
    test_case.assertIsNotNone(spec.loader)

    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        spec.loader.exec_module(module)
    finally:
        if sys.path and sys.path[0] == str(TOOLS_DIR):
            sys.path.pop(0)
    return module


class PersonaMaterialsTests(unittest.TestCase):
    def test_persona_index_stays_lightweight(self) -> None:
        personas = json.loads(PERSONAS_JSON.read_text(encoding="utf-8"))
        self.assertEqual(len(personas), 24)

        for persona in personas:
            self.assertEqual(
                sorted(persona.keys()),
                ["chinese_name", "description", "group", "name", "persona_brief"],
            )
            self.assertNotIn("profile", persona)

    def test_runtime_persona_library_contains_expected_files_for_each_persona(self) -> None:
        personas = json.loads(PERSONAS_JSON.read_text(encoding="utf-8"))
        self.assertTrue(PERSONAS_ROOT.is_dir(), "runtime/personas should exist.")

        for persona in personas:
            persona_dir = PERSONAS_ROOT / persona["name"]
            self.assertTrue(persona_dir.is_dir(), f"{persona['name']} should have a runtime persona directory.")

            for filename in REF_FILENAMES:
                self.assertTrue((persona_dir / filename).is_file(), f"{persona['name']} should include {filename}.")
            self.assertTrue((persona_dir / "profile_2_0.md").is_file(), f"{persona['name']} should include profile_2_0.md.")

    def test_build_persona_material_packet_includes_full_psychology_and_domain_material_by_default(self) -> None:
        module = load_persona_materials_module(self)

        bundle = module.build_persona_material_packet("techno_optimist", "career")

        self.assertEqual(bundle["persona"], "techno_optimist")
        self.assertEqual(bundle["domain"], "career")
        self.assertIn("人格底盘材料", bundle["packet_material"])
        self.assertIn("当前领域材料", bundle["packet_material"])
        self.assertIn("自我效能感", bundle["psychology_anchor"])
        self.assertIn("技术乐观", bundle["domain_summary"])
        self.assertIn("职业", bundle["packet_material"])
        self.assertIn("Paul Graham", bundle["packet_material"])
        self.assertIn("## 2.0 行为画像补丁", bundle["psychology_full_text"])
        self.assertIn("## 典型论据", bundle["domain_full_text"])
        self.assertIn("### psychology.md（全文）", bundle["packet_material"])
        self.assertIn("### career.md（全文）", bundle["packet_material"])
        self.assertIn("指数增长与复利叙事", bundle["packet_material"])
        self.assertIn("把职业先看成可复利的系统", bundle["packet_material"])

    def test_build_persona_material_packet_supports_other_domain_without_fixed_file(self) -> None:
        module = load_persona_materials_module(self)

        bundle = module.build_persona_material_packet("risk_manager", "other")

        self.assertEqual(bundle["domain"], "other")
        self.assertIn("### 其他 / 无固定领域文件", bundle["packet_material"])
        self.assertIn("人格底盘材料", bundle["packet_material"])
        self.assertTrue(bundle["psychology_anchor"])
        self.assertIn("### psychology.md（全文）", bundle["packet_material"])
        self.assertIn("## 机制解释", bundle["psychology_full_text"])
        self.assertEqual(bundle["domain_summary"], "")
        self.assertEqual(bundle["domain_full_text"], "")

    def test_build_persona_instruction_seed_uses_runtime_backed_material(self) -> None:
        module = load_persona_materials_module(self)
        personas = json.loads(PERSONAS_JSON.read_text(encoding="utf-8"))
        risk_manager_brief = next(persona["persona_brief"] for persona in personas if persona["name"] == "risk_manager")

        seed = module.build_persona_instruction_seed("risk_manager")

        self.assertEqual(seed["persona"], "risk_manager")
        self.assertEqual(seed["persona_name"], "风险经理派")
        self.assertIn("人格底盘材料", seed["instruction_seed"])
        self.assertIn("### psychology.md（全文）", seed["instruction_seed"])
        self.assertIn("### 其他 / 无固定领域文件", seed["instruction_seed"])
        self.assertNotEqual(seed["instruction_seed"], risk_manager_brief)

    def test_local_plugin_layout_keeps_runtime_tools_and_split_skills_together(self) -> None:
        persona_names = {persona["name"] for persona in json.loads(PERSONAS_JSON.read_text(encoding="utf-8"))}
        runtime_dirs = {path.name for path in PERSONAS_ROOT.iterdir() if path.is_dir() and path.name in persona_names}

        self.assertEqual(len(runtime_dirs), 24)
        self.assertTrue((REPO_ROOT / "tools" / "persona_materials.py").is_file())
        self.assertTrue((REPO_ROOT / "tools" / "build_worldview_round.py").is_file())
        self.assertTrue((REPO_ROOT / "tools" / "run_worldview_broker.py").is_file())
        self.assertTrue((REPO_ROOT / "tools" / "write_run_log.py").is_file())
        self.assertTrue((REPO_ROOT / "tools" / "run_log.py").is_file())
        self.assertTrue((REPO_ROOT / "skills" / "worldview-context-prep" / "SKILL.md").is_file())

    def test_user_guide_mentions_context_prep_cli(self) -> None:
        guide_text = USER_GUIDE_PATH.read_text(encoding="utf-8")

        self.assertIn("只做 round 构建", guide_text)
        self.assertIn("build_worldview_round.py", guide_text)
        self.assertIn("run_worldview_broker.py", guide_text)
        self.assertIn("synthesize_worldview_panel.py", guide_text)
        self.assertIn("verify_worldview_round.py", guide_text)
        self.assertIn("worldview-panel-codex.log", guide_text)
        self.assertIn("runs/<run-id>.log", guide_text)
        self.assertIn("audit/events.jsonl", guide_text)
        self.assertIn("不要再使用任何 legacy prompt-side dispatch 工具。", guide_text)
        self.assertIn("这次请求已作废，请重新发准备好的上下文。", guide_text)
        self.assertIn("technical_certified_result.json", guide_text)
        self.assertIn("attestation.json", guide_text)

    def test_skill_makes_runtime_backed_material_injection_mandatory(self) -> None:
        skill_text = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("build_worldview_round.py", skill_text)
        self.assertIn("The round must contain `packets/`, `tickets/`, and `identities/`.", skill_text)
        self.assertIn("The round root is the only valid handoff into dispatch.", skill_text)
        self.assertIn("Do not hand-write worker prompts.", skill_text)

    def test_default_prompt_marks_persona_materials_as_required(self) -> None:
        prompt_text = OPENAI_AGENT_PATH.read_text(encoding="utf-8")

        self.assertIn("build the sealed round with ../../tools/build_worldview_round.py", prompt_text)
        self.assertIn("dispatch only through ../../tools/run_worldview_broker.py", prompt_text)
        self.assertIn("synthesize only through ../../tools/synthesize_worldview_panel.py", prompt_text)
        self.assertIn("verify through ../../tools/verify_worldview_round.py", prompt_text)
        self.assertIn("这次请求已作废，请重新发准备好的上下文。", prompt_text)

    def test_core_runtime_docs_point_to_broker_v1_flow(self) -> None:
        skill_text = SKILL_PATH.read_text(encoding="utf-8")
        prompt_text = OPENAI_AGENT_PATH.read_text(encoding="utf-8")

        self.assertIn("run_worldview_broker.py", skill_text)
        self.assertIn("synthesize_worldview_panel.py", skill_text)
        self.assertIn("verify_worldview_round.py", skill_text)
        self.assertIn("worldview broker v1", prompt_text)

    def test_skill_documents_observability_stage_contract(self) -> None:
        skill_text = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("run_id", skill_text)
        self.assertIn("write_run_log.py", skill_text)
        self.assertIn("Classify the user request", skill_text)
        self.assertIn("Verify with `../../tools/verify_worldview_round.py`.", skill_text)

    def test_skill_documents_exact_packet_dispatch_contract(self) -> None:
        skill_text = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("Handoff is `dispatch_job.json`, not raw prompt text.", skill_text)
        self.assertIn("Only technically certified broker results may continue.", skill_text)
        self.assertIn("If any requested persona is not technically certified, fail closed.", skill_text)

    def test_build_persona_material_packet_includes_profile_anchor_block(self) -> None:
        module = load_persona_materials_module(self)

        bundle = module.build_persona_material_packet("techno_optimist", "career")
        packet_text = bundle["packet_material"]
        psychology_anchor = bundle["psychology_anchor"]

        self.assertIn("### profile_2_0.md（提炼）", packet_text)
        self.assertIn("- 对标人物：Paul Graham；Elon Musk；张一鸣；Marc Andreessen；Sam Altman；黄仁勋", packet_text)
        self.assertIn("- 思维习惯：先问哪里能加杠杆和自动化；把焦虑翻译成建设任务和学习率问题；用复利、作品和长期增量评估选择", packet_text)
        self.assertIn("自我效能感(Bandura)", psychology_anchor)
        self.assertIn("成长心态(Dweck)", psychology_anchor)
        self.assertIn("认知模式：倾向把模糊困境重新编码为可优化问题", psychology_anchor)

    def test_default_prompt_requires_broker_dispatch_gate(self) -> None:
        prompt_text = OPENAI_AGENT_PATH.read_text(encoding="utf-8")
        prep_skill_text = (REPO_ROOT / "skills" / "worldview-context-prep" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("build the sealed round with ../../tools/build_worldview_round.py", prompt_text)
        self.assertIn("dispatch only through ../../tools/run_worldview_broker.py", prompt_text)
        self.assertIn("synthesize only through ../../tools/synthesize_worldview_panel.py", prompt_text)
        self.assertIn("`../../tools/build_worldview_round.py` is the supported entrypoint for worldview broker v1", prep_skill_text)


if __name__ == "__main__":
    unittest.main()
