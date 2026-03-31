#!/usr/bin/env python3
"""
Generate 24 worldview persona .toml files from personas.json + shared template.

Usage:
    python scripts/generate_agents.py

Reads:  src/personas.json  (persona-specific data)
Writes: .codex/agents/<name>.toml  (one per persona)
"""

import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
PERSONAS_JSON = REPO / "src" / "personas.json"
AGENTS_DIR = REPO / ".codex" / "agents"

SHARED_CONSTRAINTS = """\
Non-negotiable constraints:
- Stay in character without becoming incoherent, abusive, or slogan-only.
- Separate factual claims, value judgments, and recommendations when possible.
- No violence, hate, illegal advice, self-harm encouragement, or extremist recruitment.
- If the user seems acutely unsafe, drop the bit and answer safely.
- Map the same worldview to careers, technology, products, relationships, politics, and philosophy when needed; do not only talk about "life meaning".
- Treat the parent prompt as a closed task packet.
- Do not call tools, inspect files, browse, search, or fetch additional context.
- Do not rely on hidden chat history, repo state, or background that was not explicitly included in the task packet.
- Do not mention other personas or write a synthesis across personas.
- If a critical variable is missing, write `缺失变量：...` or `缺少材料：...` first, then give only a minimal conditional answer from the provided packet instead of going to look for it.

Output in Chinese using exactly these sections unless the parent requests another format:
[人格]
只用一句话说明你是谁，不要提前下结论。
[核心判断]
先写事实判断，再写价值判断，最后给总策略。
[问题诊断]
只解释成因、错位或矛盾，不要在这里给行动建议。
[行动主张]
给出 2-4 条可执行动作，不要写成抽象态度。
[语言风格]
只概括这个人格会怎么说话，不要引入新的核心论点。
[最大盲区]
只坦白这个人格最容易忽略什么，不要补新的主结论。
[过度采用的风险]
只说明长期照做会付出的代价，不要补新的行动建议。
[签名句]
只给一句最像这个人格的话，别把新论证塞进来。

If the task packet is missing key material:
- 如果任务包缺关键材料，先点明缺的变量，再做最小条件回答。
- 先用 `缺失变量：...` 或 `缺少材料：...` 点明缺口，再做最小条件回答。
- 如果主线程没提供 `[人格底盘材料]` 或 `[当前领域材料]`，要明确指出这是缺少核心人格材料。
- 不要像材料齐全一样展开长篇推断。
"""

PROFILE_LABELS = (
    ("archetypes", "对标人物"),
    ("communities", "常见社区"),
    ("reading_list", "参考书单"),
    ("thinking_habits", "思维习惯"),
    ("emotional_triggers", "情绪触发点"),
    ("rhetorical_weapons", "常用招式"),
)

TOML_TEMPLATE = '''\
name = "{name}"
description = "{description}"
model = "gpt-5.4"
model_reasoning_effort = "xhigh"
sandbox_mode = "read-only"
developer_instructions = """
{persona_content}
{profile_content}
{shared_constraints}
"""
'''


def format_profile_content(profile: dict) -> str:
    lines = [
        "默认参考锚点：",
        "如果任务包没有提供更具体的人格材料，可以用这些锚点保持人物纹理；如果任务包已有更细材料，以任务包为准。",
        "",
    ]

    for key, label in PROFILE_LABELS:
        values = profile.get(key) or []
        if not values:
            continue
        lines.append(f"{label}：")
        lines.extend(f"- {value}" for value in values)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main():
    with open(PERSONAS_JSON, encoding="utf-8") as f:
        personas = json.load(f)

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    for p in personas:
        content = TOML_TEMPLATE.format(
            name=p["name"],
            description=p["description"],
            persona_content=p["persona_content"].rstrip() + "\n",
            profile_content=format_profile_content(p["profile"]),
            shared_constraints=SHARED_CONSTRAINTS.rstrip(),
        )
        out = AGENTS_DIR / f'{p["name"]}.toml'
        out.write_text(content, encoding="utf-8")
        print(f"wrote {out.relative_to(REPO)}")

    print(f"\nDone: {len(personas)} agent files generated.")


if __name__ == "__main__":
    main()
