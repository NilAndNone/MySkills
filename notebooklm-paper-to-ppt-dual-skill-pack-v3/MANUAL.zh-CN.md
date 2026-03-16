# 使用手册（双平台版）

这份包里不是一个“伪通用 skill”，而是两份**按平台原生习惯拆开的版本**：

- Codex：走 `.agents/skills`
- Claude Code：走 `.claude/skills`

别试图拿一个 `SKILL.md` 同时糊两个生态。那种“跨平台统一抽象”很多时候只是把细节和坑藏起来，方便以后炸你。

---

## 1. 先看结论

### 这套包适合什么

适合你要做这样的工作流：

1. 输入一篇论文（本地 PDF 优先，也可 URL）
2. 用 NotebookLM 生成 slide deck
3. 下载成 `.pptx`
4. 返回 QA 摘要和风险提示

### 这套包不适合什么

不适合你把它当成“Google 官方稳定后端 API”去做严肃生产流水线。原因很简单：

- 官方 NotebookLM Web 确认有 slide deck 和 `.pptx` 下载
- 但公开 Enterprise API 文档没有列 slide deck generation API
- 自动化这里依赖的是社区 `notebooklm-mcp-cli` 桥接，而不是 Google 官方公开 slide API

这不是不能用；这是**能用，但别装成企业级托底能力**。

---

## 2. 这次根据评审建议改了什么

你上传的评审意见，核心不是挑字眼，而是挑出了几处真正会害 agent 出丑的点。我这次继续补：

### 2.1 Source ingest 失败后的恢复路径

旧版问题：

- source add 一旦失败，skill 只会“流程中断”，没有明确 recovery

新版做法：

- 先 `nlm login --check`
- auth 失效就 `nlm login`
- 重试 source add 一次
- 还失败就停止，并报告真实错误输出

### 2.2 Polling 没有 timeout

旧版问题：

- “轮询直到成功”这种写法很像流程图，但不像能在终端里活下去的脚本

新版做法：

- 默认每 15 秒轮询一次
- 默认 300 秒总超时
- 超时后跑一次最终 `studio status`
- 返回最后状态，不假装成功

### 2.3 对 slide format 参数说得太虚

旧版问题：

- 说了 presenter / detailed，但没交代参数怎么映射
- 这会诱导 agent 编造字段名，纯纯赛博胡扯

新版做法：

- skill 明确要求：**先看运行时 MCP schema**
- 同时把社区 API reference 里确认过的 raw 映射写进 `references/mcp-parameter-notes.md`
- 如果当前安装版本没暴露干净参数，就用默认值并说明限制

### 2.4 CLI fallback 会在 headless 场景卡死

旧版问题：

- 解析不到 notebook id / artifact id 就 `read -p`
- 在 agent / CI / 非交互场景里，这不是兜底，这是自埋

新版做法：

- 自动检测非 TTY
- 支持 `--non-interactive`
- 非交互模式下一旦解析失败就直接报错退出，不再假装还活着

### 2.5 QA 终于不是嘴上检查了

旧版问题：

- 说要检查 `.pptx` 内容
- 但没有任何脚本把 `.pptx` 文本抽出来
- 这就属于“我已经认真看过了”，实际上根本没打开

新版做法：

- 新增 `extract_pptx_text.py`
- 只用 Python 标准库，不额外依赖 `python-pptx`
- `cli_flow_template.sh` 默认会生成 `<output>.slides.txt` 供 agent 做自动 QA

### 2.6 加了真实的最低版本门槛

旧版问题：

- 文档里说旧版本不行
- 但 `check_env.sh` 根本没检查版本

新版做法：

- `check_env.sh` 和 `cli_flow_template.sh` 都会解析 `nlm --version`
- 版本太老就直接拦下，不让它半路掉链子

### 2.7 安装器不再静默抹掉旧 skill

旧版问题：

- 安装脚本直接 `rm -rf` 目标目录
- 你本地自己改过的内容会被一脚踢飞

新版做法：

- 若目标已存在，先备份成时间戳目录
- 再安装新版

### 2.8 Timeout 真的 timeout，不再诱导手工补 artifact id

旧版问题：

- 轮询超时后还提示你手工粘 artifact id
- 这跟 skill 里“超时就停并报告状态”是互相打脸

新版做法：

- `cli_flow_template.sh` 超时后直接退出
- 输出最后一次 `studio status`，不继续装会

---

## 3. 平台差异：为什么一定要拆两份

| 维度 | Codex | Claude Code |
|---|---|---|
| Skill 路径 | `.agents/skills/<name>/SKILL.md` | `.claude/skills/<name>/SKILL.md` |
| 手动调用 | `$skill-name` | `/skill-name` |
| 自动触发策略 | 由 `description` + `openai.yaml` policy 控制 | 由 frontmatter 控制 |
| 隔离执行 | 主要靠 Codex 自身与 MCP / 脚本 | `context: fork` 可跑进隔离 subagent |
| 这份包的选择 | `allow_implicit_invocation: false` | `disable-model-invocation: true` + `context: fork` |

为什么都是**手动优先**？

因为这个 workflow 有明显副作用：

- 上传 source
- 触发生成
- 下载文件
- 还依赖 NotebookLM 登录状态和社区桥接版本

让 agent 自动撞上它，不叫智能，叫乱按电梯全部楼层。

---

## 4. 目录说明

### 4.1 Codex 版本

```text
codex/
├── README.md
├── MANUAL.zh-CN.md
├── scripts/
│   ├── install_skill_project.sh
│   ├── install_skill_user.sh
│   └── install_codex_mcp.sh
└── .agents/skills/notebooklm-paper-to-ppt/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── references/
    ├── assets/prompt-examples/
    └── scripts/
```

### 4.2 Claude Code 版本

```text
claude-code/
├── README.md
├── MANUAL.zh-CN.md
├── scripts/
│   ├── install_skill_project.sh
│   ├── install_skill_user.sh
│   └── install_claude_code_mcp.sh
└── .claude/skills/notebooklm-paper-to-ppt/
    ├── SKILL.md
    ├── references/
    ├── assets/prompt-examples/
    └── scripts/
```

---

## 5. 前置条件

两边都要满足：

1. 本机能运行 Python / `uv`
2. 已安装或可安装 `notebooklm-mcp-cli`
3. 你能正常 `nlm login`
4. 你本地装了对应客户端
   - Codex：`codex`
   - Claude Code：`claude`

建议先手动确认：

```bash
uv --version
nlm --help
nlm login --check
```

如果 `nlm` 还没有：

```bash
uv tool install notebooklm-mcp-cli
```

如果登录失效：

```bash
nlm login
```

---

## 6. 安装：Codex

### 6.1 项目级安装

```bash
cd /path/to/your/repo
bash /path/to/notebooklm-paper-to-ppt-dual-skill-pack/codex/scripts/install_skill_project.sh
bash .agents/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_codex.sh
bash .agents/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

### 6.2 用户级安装

```bash
bash /path/to/notebooklm-paper-to-ppt-dual-skill-pack/codex/scripts/install_skill_user.sh
bash ~/.agents/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_codex.sh
bash ~/.agents/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

### 6.3 如何调用

在 Codex 里直接显式调用：

```text
$notebooklm-paper-to-ppt
Use NotebookLM with ./papers/attention-is-all-you-need.pdf.
Generate Chinese presenter-style slides.
Save to ./out/attention-is-all-you-need.pptx.
Return notebook id, artifact id, and a QA note with the most likely hallucination risk.
```

---

## 7. 安装：Claude Code

### 7.1 项目级安装

```bash
cd /path/to/your/repo
bash /path/to/notebooklm-paper-to-ppt-dual-skill-pack/claude-code/scripts/install_skill_project.sh
bash .claude/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_claude_code.sh
bash .claude/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

### 7.2 用户级安装

```bash
bash /path/to/notebooklm-paper-to-ppt-dual-skill-pack/claude-code/scripts/install_skill_user.sh
bash ~/.claude/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_claude_code.sh
bash ~/.claude/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

### 7.3 如何调用

Claude Code 版本是**手动技能**，直接用 `/` 调：

```text
/notebooklm-paper-to-ppt ./papers/attention-is-all-you-need.pdf 输出到 ./out/attention-is-all-you-need.pptx 语言中文 使用 presenter 风格
```

或者：

```text
/notebooklm-paper-to-ppt https://arxiv.org/abs/1706.03762 output ./out/aiyn.pptx language zh-CN detailed deck
```

它用了 `context: fork` + `agent: general-purpose`，所以会在隔离上下文里执行这套流程，不把一堆轮询和命令输出全塞回主会话里。

---

## 8. skill 的内部逻辑

两边流程一致，差异主要在调用入口和平台元数据。

### Step 1：解析输入

优先顺序：

1. 本地 PDF
2. 明确给出的 paper URL

输出路径默认：

```text
./out/<slug>.pptx
```

### Step 2：创建 notebook

Notebook 标题优先用：

1. 用户给的标题
2. 文件名
3. 从 URL 推断的标题

### Step 3：添加 source 并等待 ingestion

优先走 MCP。  
MCP schema 不对、工具名漂移、或者服务器压根没连上，再回退到 CLI：

```bash
nlm source add <notebook> --file <pdf> --wait
nlm source add <notebook> --url <url> --wait
```

失败恢复策略：

```bash
nlm login --check
nlm login
# retry once
```

### Step 4：grounding query

这一步非常重要。很多人会偷懒跳过，然后让 deck 在垃圾 notebook 状态上继续生成，最后再抱怨“模型幻觉”。

典型查询：

```bash
nlm notebook query <notebook> "What is the paper's main contribution in one sentence?" --timeout 120
```

如果返回：

- 空
- 明显跑题
- 像根本没 ingest 完

那就停止。别硬继续。

### Step 5：创建 slide deck

这里最容易装懂。

官方 Web 帮助页确认 UI 有这些概念：

- Detailed Deck
- Presenter Slides
- output language
- short / default / long

但社区桥接的 CLI 文档目前只清楚写了：

```bash
nlm slides create <notebook> --confirm
```

没有把 slide format / language / length 的 CLI flag 名字正式写出来。

所以新版 skill 的规则是：

1. **优先看当前 MCP tool schema**
2. 如果 schema 里有这些字段，就用
3. 如果没有，就按默认创建，并在结果里说明限制

别在不知道字段名的时候瞎编，AI 最擅长的技能之一就是“胡说时看起来挺像文档”。这点要反着防。

### Step 6：轮询状态

默认：

- interval = 15 秒
- timeout = 300 秒

超时后：

- 最后再查一次 `studio status`
- 把状态和可见 artifact 回报出来
- 停止

### Step 7：下载 PPTX

CLI fallback：

```bash
nlm download slide-deck <notebook> <artifact-id> --format pptx --output ./out/file.pptx
```

注意：PPTX 下载至少要求社区桥接支持到 **v0.3.5+**。

### Step 8：QA

最低限度要查：

- 标题对不对
- 问题 / 方法 / 实验 / 结果 / 局限 有没有
- 有没有明显胡编 benchmark 数字

### Step 9：返回结果

返回这几个东西：

- notebook id
- artifact id
- 输出路径
- 简短 QA note
- caveat
- 是否使用 MCP 还是 CLI fallback

---

## 9. CLI fallback 模板怎么用

两边 skill 目录里都带了：

```text
scripts/cli_flow_template.sh
```

这个脚本不是给你“替代 skill”的，而是给你在以下场景兜底：

- MCP server 没接好
- agent 端 schema 漂移
- 你想先手工跑通一遍

### 9.1 基本用法

```bash
bash scripts/cli_flow_template.sh ./papers/paper.pdf ./out/paper.pptx
```

### 9.2 带超时和非交互

```bash
bash scripts/cli_flow_template.sh   --non-interactive   --timeout 420   --interval 15   --query-timeout 150   ./papers/paper.pdf   ./out/paper.pptx
```

### 9.3 URL 输入

```bash
bash scripts/cli_flow_template.sh   https://arxiv.org/abs/1706.03762   ./out/attention.pptx   "Attention Is All You Need"
```

### 9.4 为什么一定要加 non-interactive guard

因为旧版解析不到 ID 时会 `read -p`。  
在 agent / CI / headless 场景里，这相当于把流程锁死然后假装自己在工作。新版脚本会自动检测非 TTY，并在需要人工输入时直接报错退出。

---

## 10. 常见故障

### 10.1 `nlm login --check` 失败

处理：

```bash
nlm login
```

如果 Chrome / Chromium 根本拉不起来，再跑：

```bash
nlm doctor
```

### 10.2 MCP server 装了但客户端看不到

Codex：

```bash
codex mcp list
```

Claude Code：

```bash
claude mcp list
```

然后重启客户端会话，再看：

- Codex 里 `/mcp`
- Claude Code 里 `/mcp`

### 10.3 生成很久不结束

先别急着怪宇宙。NotebookLM 官方帮助就写了 slide deck 可能要几分钟。

处理：

```bash
nlm studio status <notebook>
```

如果超时，skill 会返回最后状态，不会硬说“成功”。

### 10.4 deck 结构不对

不要优先 revise。  
官方帮助明确说：

- revise 不能增删页
- revise 不参考 sources

所以结构错了就**重生成**。  
Revision 更适合修文案、布局、图片，不适合拯救错误叙事骨架。

### 10.5 `.pptx` 下载失败

先查版本：

```bash
uv tool list | grep notebooklm
nlm --help
```

如果版本过老，升级：

```bash
uv tool upgrade notebooklm-mcp-cli
```

---

## 11. 推荐工作方式

### 方式 A：先用 CLI 验证 happy path，再上 skill

适合第一次搭环境：

1. `nlm login`
2. 手工跑 `cli_flow_template.sh`
3. 确认能拿到 `.pptx`
4. 再用 Codex / Claude Code skill

优点：排错简单  
缺点：略手工

### 方式 B：直接用 skill

适合你已经有稳定环境：

- Codex：`$notebooklm-paper-to-ppt`
- Claude Code：`/notebooklm-paper-to-ppt`

优点：自然语言体验更顺  
缺点：一旦环境没配好，错误来源更分散

---

## 12. 我建议你怎么用

### 你在做 demo / 个人自动化

主推：**Claude Code 版本**

原因：

- `/skill-name` 的交互感更自然
- `context: fork` 很适合这种会产生大量中间输出的流程
- skill 文件和调用方式更像“命令”

### 你在做 repo 内共享 workflow / 和 Codex 配合

主推：**Codex 版本**

原因：

- `.agents/skills` 更适合跟 repo 一起版本化
- `openai.yaml` 能把 implicit invocation 明确关掉
- 和 repo 内其他 Codex skill 的组织方式一致

### 你两个都要

就都装。  
它们的 skill 元数据不同，但工作流语义基本一致，便于横向比较。

---

## 13. 自检清单

### 基础

- [ ] `uv` 可用
- [ ] `nlm` 可用
- [ ] `nlm login --check` 通过
- [ ] `nlm doctor` 没有关键报错

### Codex

- [ ] `.agents/skills/notebooklm-paper-to-ppt/SKILL.md` 存在
- [ ] `codex mcp list` 看得到 NotebookLM server
- [ ] `$notebooklm-paper-to-ppt` 能被识别

### Claude Code

- [ ] `.claude/skills/notebooklm-paper-to-ppt/SKILL.md` 存在
- [ ] `claude mcp list` 看得到 NotebookLM server
- [ ] `/notebooklm-paper-to-ppt` 能被识别

### Workflow

- [ ] 论文 source ingest 成功
- [ ] grounding query 不为空且不跑题
- [ ] slide deck artifact 完成
- [ ] `.pptx` 文件真实存在
- [ ] QA 通过

---

## 14. 最后的实话

这套东西现在已经够你做一个像样的 `paper -> NotebookLM -> pptx` skill workflow 了。  
但它仍然是：

- 官方 Web 功能
- + 社区 reverse-engineered CLI/MCP bridge
- + 两个 agent 客户端各自不同的 skill 机制

所以它是**能打的工程拼装件**，不是天降神谕的官方平台能力。区别很大。前者能干活，后者会害人立项过度自信。

具体文档出处看：

- `references/SOURCES.md`
- `references/EVAL_NOTES_APPLIED.md`
