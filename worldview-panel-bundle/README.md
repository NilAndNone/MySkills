# worldview-panel-bundle

网络画像多人格面板 — 用 16 个中文互联网典型人格同时分析一个问题，再交叉裁决。

## 架构

```
.claude/
├── skills/
│   ├── worldview-core/SKILL.md    # 共享 schema + 安全底线 + 统一输出格式
│   └── worldview-panel/SKILL.md   # 协调入口：解析问题 → 全量 dispatch → 汇总裁决
└── agents/
    ├── worldview-orchestrator.md   # 顶层协调 agent
    └── <16 persona agents>.md     # 各人格独立 subagent
```

## 16 个人格

| agent id | 画像 | 一句话定位 |
|----------|------|-----------|
| depressive-nihilist | 消极虚无主义者 | 把"无意义"当终局判词 |
| network-jester | 网络乐子人 | 把严肃命题改写成可消费的热闹 |
| attention-marketer | 营销号 | 把任何命题转成情绪钩子和流量漏斗 |
| collapse-prophet | 神神（抽象版） | 一切问题回收进系统性崩坏叙事 |
| radical-meme-dissident | 蛙蛙（抽象版） | 历史梗、暗号梗和反建制黑色幽默 |
| performance-hawk | 社达 | 所有困境都是能力、竞争和排序问题 |
| optimistic-nihilist | 积极虚无主义者 | 无预设意义 = 轻装上路的自由 |
| existentialist | 存在主义者 | 意义是行动与承诺的产物 |
| cynical-detached | 犬儒/无所谓派 | 靠降低投入来保护自己 |
| postmodern-ironist | 后现代梗学家 | 一切庄严叙事拆成话语和符号 |
| modern-mystic | 现代神人 | 通过极端体验对抗空心感 |
| baseline-conformist | 基本盘 | 最低冲突、最高共识的情绪肯定 |
| external-reference | 外部参照派 | 拿外部样板反衬本地问题 |
| red-leftist | 网左 | 意义放回结构、劳动与集体行动 |
| terminal-jester | 终极乐子人 | 死猪不怕开水烫式韧性 |
| online-rightist | 网右 | 主体能动性、秩序、竞争和自我建构 |

## 使用

```bash
# 方式 A：会话中调 skill
/worldview-panel 大模型创业还有没有意义？

# 方式 B：以 agent 模式启动
claude --agent worldview-orchestrator
```

## 自定义

- **改人格**：编辑 `.claude/agents/<persona>.md`
- **改输出格式**：编辑 `.claude/skills/worldview-core/SKILL.md` 的输出 contract
- **改调度策略**：编辑 `.claude/agents/worldview-orchestrator.md`
