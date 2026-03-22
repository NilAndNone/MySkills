#!/usr/bin/env python3
"""
Generate 24 worldview persona .toml files from personas.json + shared template.

Usage:
    python scripts/generate_agents.py

Reads:  scripts/personas.json  (persona-specific data)
Writes: .codex/agents/<name>.toml  (one per persona)

Does NOT touch default.toml, worker.toml, or explorer.toml.
"""

import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
PERSONAS_JSON = REPO / "scripts" / "personas.json"
AGENTS_DIR = REPO / ".codex" / "agents"

SHARED_CONSTRAINTS = """\
Non-negotiable constraints:
- Stay in character without becoming incoherent, abusive, or slogan-only.
- Separate factual claims, value judgments, and recommendations when possible.
- No violence, hate, illegal advice, self-harm encouragement, or extremist recruitment.
- If the user seems acutely unsafe, drop the bit and answer safely.
- Map the same worldview to careers, technology, products, relationships, politics, and philosophy when needed; do not only talk about "life meaning".

Output in Chinese using exactly these sections unless the parent requests another format:
[人格]
[核心判断]
[问题诊断]
[行动主张]
[语言风格]
[最大盲区]
[过度采用的风险]
[签名句]
"""

TOML_TEMPLATE = '''\
name = "{name}"
description = "{description}"
group = "{group}"
model = "gpt-5.4"
model_reasoning_effort = "xhigh"
sandbox_mode = "read-only"
developer_instructions = """
{persona_content}
{shared_constraints}
"""
'''


def main():
    with open(PERSONAS_JSON, encoding="utf-8") as f:
        personas = json.load(f)

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    for p in personas:
        content = TOML_TEMPLATE.format(
            name=p["name"],
            description=p["description"],
            group=p["group"],
            persona_content=p["persona_content"].rstrip() + "\n",
            shared_constraints=SHARED_CONSTRAINTS.rstrip(),
        )
        out = AGENTS_DIR / f'{p["name"]}.toml'
        out.write_text(content, encoding="utf-8")
        print(f"wrote {out.relative_to(REPO)}")

    print(f"\nDone: {len(personas)} agent files generated.")


if __name__ == "__main__":
    main()
