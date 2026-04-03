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
AGENTS_ROOT = REPO_ROOT / "runtime" / "agents"
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

    def test_local_plugin_layout_keeps_runtime_tools_and_split_skills_together(self) -> None:
        persona_names = {persona["name"] for persona in json.loads(PERSONAS_JSON.read_text(encoding="utf-8"))}
        runtime_dirs = {path.name for path in PERSONAS_ROOT.iterdir() if path.is_dir() and path.name in persona_names}

        self.assertEqual(len(runtime_dirs), 24)
        self.assertTrue((REPO_ROOT / "tools" / "persona_materials.py").is_file())
        self.assertTrue((REPO_ROOT / "tools" / "prepare_context_packets.py").is_file())
        self.assertTrue((REPO_ROOT / "tools" / "write_run_log.py").is_file())
        self.assertTrue((REPO_ROOT / "tools" / "run_log.py").is_file())
        self.assertTrue((REPO_ROOT / "tools" / "dispatch_packet_guard.py").is_file())
        self.assertTrue((REPO_ROOT / "skills" / "worldview-context-prep" / "SKILL.md").is_file())

    def test_user_guide_mentions_context_prep_cli(self) -> None:
        guide_text = USER_GUIDE_PATH.read_text(encoding="utf-8")

        self.assertIn("Context prep only", guide_text)
        self.assertIn("prepare_context_packets.py", guide_text)
        self.assertIn("worldview-panel-codex.log", guide_text)
        self.assertIn("runs/<run-id>.log", guide_text)
        self.assertIn("有 `run_end` 才算完整结束", guide_text)
        self.assertIn("没有 `run_end` 就是未完成", guide_text)
        self.assertIn("单次日志优先", guide_text)
        self.assertIn("dispatch_packet_guard.py", guide_text)
        self.assertIn("这次请求已作废，请重新发准备好的上下文。", guide_text)
        self.assertIn("matched=true", guide_text)
        self.assertIn("outgoing copy", guide_text)

    def test_skill_makes_runtime_backed_material_injection_mandatory(self) -> None:
        skill_text = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn(
            "如果在本地 plugin 里执行，必须先用 `../../tools/persona_materials.py --persona <slug> --domain <domain>` 生成默认材料块",
            skill_text,
        )
        self.assertIn("runtime/personas/<persona>/", skill_text)
        self.assertIn(
            "如果任务包缺少 `[人格底盘材料]` 或 `[当前领域材料]`，视为主线程协议违规：不要分发 subagent，先补材料再 dispatch。",
            skill_text,
        )

    def test_default_prompt_marks_persona_materials_as_required(self) -> None:
        prompt_text = OPENAI_AGENT_PATH.read_text(encoding="utf-8")

        self.assertIn("must generate runtime-backed persona materials before dispatch", prompt_text)
        self.assertIn("never hand-wave or manually omit", prompt_text)
        self.assertIn("question_classify", prompt_text)
        self.assertIn("dispatch_ready", prompt_text)
        self.assertIn("progress_heartbeat", prompt_text)
        self.assertIn("60s", prompt_text)

    def test_core_runtime_docs_raise_concurrency_cap_to_six(self) -> None:
        skill_text = SKILL_PATH.read_text(encoding="utf-8")
        prompt_text = OPENAI_AGENT_PATH.read_text(encoding="utf-8")
        routing_text = ROUTING_MATRIX_PATH.read_text(encoding="utf-8")

        self.assertIn("Never run more than 6 subagents at once. If the panel is larger, dispatch in batches of up to 6.", skill_text)
        self.assertIn("任一时刻最多只运行 6 个 subagents", skill_text)
        self.assertIn("每批最多 6 个", skill_text)
        self.assertIn("keep at most 6 active at a time", prompt_text)
        self.assertIn("任一时刻最多只运行 6 个 subagents", routing_text)
        self.assertIn("每批最多 6 个", routing_text)

    def test_skill_documents_observability_stage_contract(self) -> None:
        skill_text = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("question_classify", skill_text)
        self.assertIn("panel_select", skill_text)
        self.assertIn("dispatch_ready", skill_text)
        self.assertIn("agent_result", skill_text)
        self.assertIn("progress_heartbeat", skill_text)
        self.assertIn("run_end` 统一只用三种状态", skill_text)
        self.assertIn("每完成 6 个材料打一条进度", skill_text)
        self.assertIn("如果 60 秒内没有任何新返回，就写一条 `progress_heartbeat`", skill_text)
        self.assertIn("如果日志里没有 `run_end`，就按“外部中断或未完成”理解", skill_text)

    def test_skill_documents_exact_packet_dispatch_contract(self) -> None:
        skill_text = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("只允许从已准备好的成品包里取内容，不要临时手写一个缩略版再 dispatch。", skill_text)
        self.assertIn("派发前必须先核对将要发送的文本与落盘 `packet.txt` 完全一致。", skill_text)
        self.assertIn("只要不一致，就立刻中止整轮并要求用户重新发准备好的上下文。", skill_text)
        self.assertIn("只有拿到 `matched=true` 的结果，才允许把该副本发给 subagent。", skill_text)

    def test_generated_agent_includes_profile_anchor_block(self) -> None:
        agent_text = (AGENTS_ROOT / "techno_optimist.toml").read_text(encoding="utf-8")

        self.assertIn("默认参考锚点：", agent_text)
        self.assertIn("对标人物：", agent_text)
        self.assertIn("- Paul Graham", agent_text)
        self.assertIn("思维习惯：", agent_text)
        self.assertIn("[核心判断]\n先写事实判断，再写价值判断，最后给总策略。", agent_text)
        self.assertIn("[问题诊断]\n只解释成因、错位或矛盾，不要在这里给行动建议。", agent_text)
        self.assertIn("如果任务包缺关键材料，先点明缺的变量，再做最小条件回答。", agent_text)
        self.assertIn("如果主线程没提供 `[人格底盘材料]` 或 `[当前领域材料]`，要明确指出这是缺少核心人格材料。", agent_text)

    def test_default_prompt_requires_release_gate_not_claim_only(self) -> None:
        prompt_text = OPENAI_AGENT_PATH.read_text(encoding="utf-8")
        prep_skill_text = (REPO_ROOT / "skills" / "worldview-context-prep" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("create an outgoing copy", prompt_text)
        self.assertIn("must produce a `matched=true` result before any subagent send", prompt_text)
        self.assertIn("Do not dispatch any subagent until the CLI reports the batch is ready and the dispatch release step reports `matched=true`.", prep_skill_text)


if __name__ == "__main__":
    unittest.main()
