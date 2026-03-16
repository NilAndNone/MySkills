# Codex 版使用手册

## 1. 安装位置

Codex 官方文档当前的 skill 路径是：

- repo：`.agents/skills/<skill-name>/`
- user：`~/.agents/skills/<skill-name>/`

本包已经按这个结构准备好了。

## 2. 安装步骤

### 项目级

```bash
cd /path/to/repo
bash /path/to/pack/codex/scripts/install_skill_project.sh
bash .agents/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_codex.sh
bash .agents/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

### 用户级

```bash
bash /path/to/pack/codex/scripts/install_skill_user.sh
bash ~/.agents/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_codex.sh
bash ~/.agents/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

### 安装器行为补充

如果目标路径已经存在旧版 skill，安装脚本现在会先备份成带时间戳的 `.bak.YYYYmmdd-HHMMSS` 目录，再安装新版。

### 环境检查新增项

`check_env.sh` 现在除了命令、登录态和 MCP 可见性外，还会额外检查：

- `nlm --version` 是否满足最低版本要求
- `scripts/extract_pptx_text.py` 是否可运行

### PPTX 文本导出

skill 内新增：

```text
.agents/skills/notebooklm-paper-to-ppt/scripts/extract_pptx_text.py
```

它会从 `.pptx` 里抽取每页文字，供 agent 做自动 QA。`cli_flow_template.sh` 默认也会额外产出一个 sidecar 文本文件：

```text
<output>.slides.txt
```

你可以把它当成“机器能读的 deck 摘要”。

## 3. 你会得到什么

```text
.agents/skills/notebooklm-paper-to-ppt/
├── SKILL.md
├── agents/openai.yaml
├── references/
├── assets/prompt-examples/
└── scripts/
```

## 4. 为什么是手动触发

`agents/openai.yaml` 里把：

```yaml
policy:
  allow_implicit_invocation: false
```

显式关掉了自动隐式触发。

原因：

- NotebookLM source add / slides create / download 都有副作用
- 还依赖登录态和社区桥接版本
- 自动误触发的代价比“要多打一行 `$skill-name`”大得多

## 5. 调用方式

### 本地 PDF

```text
$notebooklm-paper-to-ppt
Use NotebookLM with ./papers/attention-is-all-you-need.pdf.
Generate Chinese presenter-style slides.
Save to ./out/attention-is-all-you-need.pptx.
Return notebook id, artifact id, and a QA note with the most likely hallucination risk.
```

### 论文 URL

```text
$notebooklm-paper-to-ppt
Use NotebookLM with https://arxiv.org/abs/1706.03762.
Create a detailed English deck.
Save to ./out/aiyn-detailed.pptx.
Tell me whether the deck likely needs regeneration or just revision.
```

## 6. MCP 安装逻辑

脚本优先尝试：

```bash
nlm setup add codex
```

如果你的 `nlm` 版本太老或 setup 子命令不配合，再退到官方 Codex CLI 的 stdio MCP 配置形式：

```bash
codex mcp add notebooklm --env NOTEBOOKLM_HL=en -- uvx --from notebooklm-mcp-cli notebooklm-mcp
```

## 7. 环境检查

```bash
bash .agents/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

它会检查：

- `uv`
- `codex`
- `nlm`
- `notebooklm-mcp`
- `nlm login --check`
- `nlm doctor`
- `codex mcp list`

## 8. skill 的执行逻辑

### 8.1 解析输入

优先本地 PDF，其次 URL。  
默认输出路径：

```text
./out/<slug>.pptx
```

### 8.2 创建 notebook

Notebook 标题默认从：

1. 用户显式标题
2. 文件名
3. URL 推断

### 8.3 上传 source

优先 MCP。失败再回落 CLI。  
失败时会：

1. `nlm login --check`
2. 必要时 `nlm login`
3. 重试一次

### 8.4 grounding query

会做一个简短 sanity check，确认 ingestion 不是假完成：

```bash
nlm notebook query <notebook> "What is the paper's main contribution in one sentence?" --timeout 120
```

### 8.5 生成 slides

策略：

- 讲者辅助：presenter
- 独立阅读：detailed

但不要假设 CLI 已经稳定暴露这些 flags。  
这就是为什么 `SKILL.md` 里要求**先看运行时 schema**。

### 8.6 轮询与下载

- poll interval：15 秒
- poll timeout：300 秒
- download：`.pptx`

## 9. CLI fallback 脚本

默认会尝试生成：

```text
<output>.slides.txt
```

如果你就是不想要这个 sidecar 文本，可以加：

```bash
--skip-text-dump
```


位于：

```text
.agents/skills/notebooklm-paper-to-ppt/scripts/cli_flow_template.sh
```

### 9.1 常用命令

```bash
bash .agents/skills/notebooklm-paper-to-ppt/scripts/cli_flow_template.sh   ./papers/paper.pdf   ./out/paper.pptx
```

### 9.2 非交互模式

```bash
bash .agents/skills/notebooklm-paper-to-ppt/scripts/cli_flow_template.sh   --non-interactive   --timeout 420   ./papers/paper.pdf   ./out/paper.pptx
```

## 10. 常见问题

### `codex mcp list` 看不到 server

先看：

```bash
codex mcp list
nlm doctor
```

如果已经写入配置但当前会话没刷新，重开 Codex。

### 生成成功但输出文件不存在

先别美化失败。去看：

```bash
nlm studio status <notebook>
```

再重新跑 download。

### slide deck 结构不对

不要第一反应 revise。  
结构错了就 regenerate。官方 NotebookLM 帮助已经把 revise 的限制写得很直白了。

## 11. 推荐使用顺序

1. 先手工跑一次 `cli_flow_template.sh`
2. 再用 `$notebooklm-paper-to-ppt`
3. deck 结构经常错的话，先优化 prompt / audience / language，再考虑 revision

## 12. 相关文件

- `references/workflow.md`
- `references/qa-checklist.md`
- `references/mcp-parameter-notes.md`
- `references/evaluation-applied.md`
