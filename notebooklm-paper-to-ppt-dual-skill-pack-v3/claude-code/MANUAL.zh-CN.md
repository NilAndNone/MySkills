# Claude Code 版使用手册

## 1. 安装位置

Claude Code 当前文档里的 skill 路径是：

- project：`.claude/skills/<skill-name>/SKILL.md`
- user：`~/.claude/skills/<skill-name>/SKILL.md`

本包就是这个结构。

## 2. 安装步骤

### 项目级

```bash
cd /path/to/repo
bash /path/to/pack/claude-code/scripts/install_skill_project.sh
bash .claude/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_claude_code.sh
bash .claude/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

### 用户级

```bash
bash /path/to/pack/claude-code/scripts/install_skill_user.sh
bash ~/.claude/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_claude_code.sh
bash ~/.claude/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

### 安装器行为补充

如果目标路径已经存在旧版 skill，安装脚本现在会先备份成带时间戳的 `.bak.YYYYmmdd-HHMMSS` 目录，再安装新版。

### 环境检查新增项

`check_env.sh` 现在除了命令、登录态和 MCP 可见性外，还会额外检查：

- `nlm --version` 是否满足最低版本要求
- `scripts/export_pptx_slide_images.py` 是否可运行

### PPTX 图片导出与备注写回

skill 内新增：

```text
.claude/skills/notebooklm-paper-to-ppt/scripts/export_pptx_slide_images.py
```

它会从 `.pptx` 里按页导出代表性图片和 `manifest.json`，供后续逐页生成中文 speaker notes。默认目录名是：

```text
<output>.slide-images/
```

例如 `deck.slide-images/`。

## 3. skill 为什么这样写

这个版本的 frontmatter 是：

```yaml
disable-model-invocation: true
context: fork
agent: general-purpose
```

### 3.1 `disable-model-invocation: true`

意思是：**只允许你手动触发**。  
原因很简单，这个 workflow 有副作用，不该让 Claude 看到“做个 PPT 吧”就擅自开始上传和下载文件。

### 3.2 `context: fork`

让 skill 进一个隔离上下文执行。  
好处是：

- 中间的轮询、CLI 输出、status 噪音不会把主对话塞爆
- 做完以后只把结果摘要带回来

### 3.3 `agent: general-purpose`

Claude Code 文档里，`general-purpose` 是适合：

- complex research
- multi-step operations
- code modifications

这正好匹配这种“解析输入 -> 上传 -> 检查 -> 生成 -> 下载 -> 导出图片 -> 写回备注”的工作流。用 Explore 反而不合适，因为 Explore 是偏只读探索型。

## 4. 调用方式

### 本地 PDF

```text
/notebooklm-paper-to-ppt ./papers/attention-is-all-you-need.pdf 输出到 ./out/attention-is-all-you-need.pptx 语言中文 使用 presenter 风格，并写入中文 speaker notes
```

### URL

```text
/notebooklm-paper-to-ppt https://arxiv.org/abs/1706.03762 output ./out/aiyn-detailed.pptx language en detailed deck
```

### 缺省参数行为

如果你只给 source，不给 output path，默认：

```text
~/Documents/ppt_source/notebooklm_output/<slug>_<YYYYMMDDHHmm>.pptx
```

## 5. MCP 安装逻辑

安装脚本优先尝试：

```bash
nlm setup add claude-code
```

如果这个子命令在你机器上的版本不好使，再退到 Claude Code 官方文档里的 stdio MCP 形式：

```bash
claude mcp add --transport stdio --scope user --env NOTEBOOKLM_HL=en notebooklm -- uvx --from notebooklm-mcp-cli notebooklm-mcp
```

## 6. 如何检查环境

```bash
bash .claude/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

它会检查：

- `uv`
- `claude`
- `nlm`
- `notebooklm-mcp`
- `nlm login --check`
- `nlm doctor`
- `claude mcp list`

## 7. skill 内部流程

### 7.1 解析 `$ARGUMENTS`

Claude Code skills 支持 `$ARGUMENTS`。  
所以你在 `/notebooklm-paper-to-ppt ...` 后面跟的内容，会被 skill 当成参数输入，再和当前请求一起解析。

### 7.2 创建 notebook

自动从文件名 / URL / 用户要求中推导标题。

### 7.3 source add 与恢复

失败时：

1. `nlm login --check`
2. 必要时 `nlm login`
3. retry once
4. 还失败就停

### 7.4 grounding query

这一步不是装样子。它的目的就是防止：

- source 其实没 ingest 好
- 然后你还硬去生成 slides
- 最后得到一个结构完整但内容跑偏的 deck

### 7.5 slide 生成参数

新版 skill 不再硬编码“看起来合理”的字段名。  
它会：

1. 先看当前 MCP schema
2. 如果 schema 暴露了 slide format / language / length，就用
3. 否则退回默认设置，并在结果里明确说明

### 7.6 下载与中文备注

完成后会输出：

- notebook id
- artifact id
- final ppt path
- raw ppt path
- notes json path
- slide-images dir
- notes_status
- notes_artifacts
- notes_summary
- caveat
- MCP / CLI fallback 标记

默认流程不是下载后 QA，而是：

1. 先把 NotebookLM 产物下载成 `<output>.raw.pptx`
2. 导出 `<output>.slide-images/`
3. 逐页基于图片生成中文 speaker notes
4. 写回最终 `<output>.pptx`

这些中文备注只写到 PowerPoint speaker notes，不改幻灯片可见内容。  
生成 notes 时默认不注入任何 style 文件，让 NotebookLM 自己决定 deck 的视觉风格。只有你显式指定 style 文件时，skill 才会把那个文件的内容注入生成 prompt。

## 8. CLI fallback 模板

CLI 模板现在只负责下载 raw `.pptx`，不直接调模型生成 notes。

如果你想单独测试“下载之后”的流程，直接运行：

```bash
python3 .claude/skills/notebooklm-paper-to-ppt/scripts/postprocess_downloaded_pptx.py \
  export-assets \
  --input ./out/paper.raw.pptx \
  --assets-dir ./out/paper.slide-images
```

再准备一个符合约定的 `notes.json`，然后执行：

```bash
python3 .claude/skills/notebooklm-paper-to-ppt/scripts/postprocess_downloaded_pptx.py \
  apply-notes \
  --input ./out/paper.raw.pptx \
  --notes-json ./out/paper.notes.json \
  --output ./out/paper.pptx
```

路径：

```text
.claude/skills/notebooklm-paper-to-ppt/scripts/cli_flow_template.sh
```

### 基本运行

```bash
bash .claude/skills/notebooklm-paper-to-ppt/scripts/cli_flow_template.sh   ./papers/paper.pdf   ./out/paper.raw.pptx
```

### 非交互运行

```bash
bash .claude/skills/notebooklm-paper-to-ppt/scripts/cli_flow_template.sh   --non-interactive   --timeout 420   --query-timeout 150   ./papers/paper.pdf   ./out/paper.raw.pptx
```

## 9. 常见问题

### `/notebooklm-paper-to-ppt` 不出现

先确认文件在：

```text
.claude/skills/notebooklm-paper-to-ppt/SKILL.md
```

然后重开 Claude Code 会话，或者重新载入插件/skills。

### `claude mcp list` 没有 NotebookLM server

手动检查：

```bash
claude mcp list
nlm doctor
```

### source add 会随机报 auth 问题

这是社区桥接最常见的毛病之一。  
先做：

```bash
nlm login --check
nlm login
```

### deck 生成出来但内容骨架歪了

不要一股脑 revise。  
先看用户想要的是：

- presenter support
- detailed read-ahead
- 中文 / 英文
- 面向 beginners / experts

这些前置没设对，revision 只能修表皮。

## 10. 推荐工作方式

最稳的一种：

1. 先用 `nlm login`
2. 手工跑一次 `cli_flow_template.sh`
3. 确认 `.pptx` 真能下载
4. 再把流程交给 `/notebooklm-paper-to-ppt`

## 11. 相关文件

- `references/workflow.md`
- `references/notes-checklist.md`
- `references/mcp-parameter-notes.md`
- `references/evaluation-applied.md`
