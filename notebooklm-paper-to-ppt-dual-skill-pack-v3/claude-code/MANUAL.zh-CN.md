# Claude Code 版使用手册

## 1. 安装位置

Claude Code skill 路径是：

- project：`.claude/skills/notebooklm-paper-to-ppt/`
- user：`~/.claude/skills/notebooklm-paper-to-ppt/`

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

如果目标路径已存在旧版 skill，安装脚本会先备份成带时间戳的 `.bak.YYYYmmdd-HHMMSS` 目录。

## 3. 这个 skill 现在支持什么

保留一个入口：

```text
/notebooklm-paper-to-ppt ...
```

但明确分成 3 个模式：

- `mode=full`
  - 默认值
  - NotebookLM 生成 deck，下载 raw `.pptx`，再生成并写回 notes
- `mode=deck-only`
  - 只生成并下载 raw `.pptx`
- `mode=notes-only`
  - 基于现有 `raw_pptx=...` 跑 notes 流程

如果你没写 `mode`，但输入已经带了：

- `raw_pptx=...`
- 以及 `source_pdf=...` / `source_text=...` / `source_url=...`

skill 会自动判定为 `notes-only`。  
其他情况默认 `full`。

## 4. 输入感知规则

推荐显式写这些参数：

- `mode=full|deck-only|notes-only`
- `source=...`
- `output=...`
- `raw_pptx=...`
- `source_pdf=...`
- `source_text=...`
- `source_url=...`
- `title=...`
- `language=...`
- `deck_format=detailed|presenter`
- `length=...`
- `style_file=...`

skill 会把输入识别成这几类：

- `pdf_source`：本地 `.pdf`
- `url_source`：`http(s)://...`
- `text_source`：本地 `.txt` / `.md`
- `raw_deck_input`：本地 `.raw.pptx`

执行前，skill 会先明确输出：

- `workflow_mode`
- `resolved_source_kind`
- `resolved_source_value`
- `resolved_raw_pptx`
- `resolved_final_output`
- `will_generate_deck`
- `will_generate_notes`

如果缺参，只追问当前模式最少缺失项。

## 5. 支持哪些资料输入

### `full` / `deck-only`

`source=` 支持：

- 本地 PDF
- 可直接抓取正文的单页网页 URL

### `notes-only`

必须给：

- `raw_pptx=...`

并且三选一：

- `source_pdf=...`
- `source_text=...`
- `source_url=...`

## 6. 网页输入怎么处理

网页支持范围限定为：

- 只抓你给的那个 URL
- 不递归抓子链接
- 页面必须能直接 HTTP 获取
- 不支持登录、验证码、重度 JS 渲染后才出现正文的页面

新增脚本：

```text
.claude/skills/notebooklm-paper-to-ppt/scripts/fetch_web_source.py
```

它的职责是：

- 输入：`--url` 和 `--output`
- 输出：UTF-8 文本文件
- 优先用 `trafilatura` 抽正文
- 没装 `trafilatura` 时，回退到标准库 HTML 可见文本提取

当网页参与 notes 流程时，默认会生成：

```text
<output>.notes-artifacts/tmp/source_webpage.txt
```

如果你装了 `trafilatura`，网页正文抽取通常会更稳；没装也可以跑，只是会使用降级提取。

## 7. 典型调用方式

### 默认 `full` + 本地 PDF

```text
/notebooklm-paper-to-ppt source=./papers/attention-is-all-you-need.pdf output=./out/attention-is-all-you-need.pptx language=zh-CN deck_format=presenter
```

### 默认 `full` + 网页 URL

```text
/notebooklm-paper-to-ppt source=https://example.com/article output=./out/article-deck.pptx language=zh-CN
```

### 显式 `deck-only` + 网页 URL

```text
/notebooklm-paper-to-ppt mode=deck-only source=https://example.com/article output=./out/article-deck.pptx
```

### 显式 `notes-only` + 网页 URL

```text
/notebooklm-paper-to-ppt mode=notes-only raw_pptx=./out/article-deck.raw.pptx source_url=https://example.com/article output=./out/article-deck.pptx
```

### 显式 `notes-only` + 本地文本

```text
/notebooklm-paper-to-ppt mode=notes-only raw_pptx=./out/article-deck.raw.pptx source_text=./papers/article.txt output=./out/article-deck.pptx
```

## 8. 路径约定

如果你给的是：

```text
output=./out/deck.pptx
```

则默认派生：

- raw deck：`./out/deck.raw.pptx`
- notes artifacts：`./out/deck.notes-artifacts/`
- crawled webpage text：`./out/deck.notes-artifacts/tmp/source_webpage.txt`

如果 `notes-only` 输入是：

```text
raw_pptx=./out/deck.raw.pptx
```

且你没给 `output=`，则默认 final output 是：

```text
./out/deck.pptx
```

## 9. 内部流程边界

### `full`

1. 创建 notebook
2. source add
3. grounding query
4. 生成 slide deck
5. 下载 `<output>.raw.pptx`
6. 如果 source 是 PDF，直接 `prepare-context --source-pdf`
7. 如果 source 是网页，先 `fetch_web_source.py` 再 `prepare-context --source-text`
8. Claude 生成 `notes.json`
9. `validate-notes`
10. `apply-notes`

### `deck-only`

和 `full` 的前半段一致，但只做到 raw `.pptx` 下载完成为止。  
不会进入：

- `fetch_web_source.py`
- `prepare-context`
- `validate-notes`
- `apply-notes`

### `notes-only`

跳过：

- notebook 创建
- source add
- grounding query
- slide generation
- raw 下载

直接从 notes 前处理开始：

- `source_pdf` -> `prepare-context --source-pdf`
- `source_text` -> `prepare-context --source-text`
- `source_url` -> `fetch_web_source.py` -> `prepare-context --source-text`

## 10. CLI fallback 模板

CLI 模板路径：

```text
.claude/skills/notebooklm-paper-to-ppt/scripts/cli_flow_template.sh
```

它仍然只负责 NotebookLM deck 下载，不负责 notes 生成。

基本运行：

```bash
bash .claude/skills/notebooklm-paper-to-ppt/scripts/cli_flow_template.sh \
  ./papers/paper.pdf \
  ./out/paper.raw.pptx
```

下载之后，如果你想单独测试 notes 流程：

```bash
python3 .claude/skills/notebooklm-paper-to-ppt/scripts/postprocess_downloaded_pptx.py \
  prepare-context \
  --input ./out/paper.raw.pptx \
  --source-text ./papers/paper.txt
```

如果 notes 来源是网页：

```bash
python3 .claude/skills/notebooklm-paper-to-ppt/scripts/fetch_web_source.py \
  --url https://example.com/article \
  --output ./out/paper.notes-artifacts/tmp/source_webpage.txt

python3 .claude/skills/notebooklm-paper-to-ppt/scripts/postprocess_downloaded_pptx.py \
  prepare-context \
  --input ./out/paper.raw.pptx \
  --source-text ./out/paper.notes-artifacts/tmp/source_webpage.txt
```

## 11. `check_env.sh` 现在会检查什么

- `uv`
- `python3`
- `claude`
- `nlm`
- `notebooklm-mcp`
- `nlm --version`
- `nlm login --check`
- `nlm doctor`
- `claude mcp list`
- `export_pptx_slide_images.py --help`
- `inject_pptx_speaker_notes.py --help`
- `postprocess_downloaded_pptx.py --help`
- `fetch_web_source.py --help`

## 12. 返回结果约定

### `full`

会返回：

- `workflow_mode`
- `resolved_source_kind`
- notebook id
- artifact id
- final output path
- raw output path
- `notes_status`
- `notes_artifacts`
- `notes_summary`

### `deck-only`

会返回：

- `workflow_mode`
- `resolved_source_kind`
- notebook id
- artifact id
- raw output path
- caveat

不会返回 notes 相关字段。

### `notes-only`

会返回：

- `workflow_mode`
- `resolved_source_kind`
- final output path
- raw input path
- `notes_status`
- `notes_artifacts`
- `notes_summary`

如果 notes 来源是网页，还会额外返回抓下来的 `source_webpage.txt` 路径。

## 13. 常见问题

### `/notebooklm-paper-to-ppt` 不出现

先确认文件在：

```text
.claude/skills/notebooklm-paper-to-ppt/SKILL.md
```

然后重开 Claude Code 会话。

### `claude mcp list` 没有 NotebookLM server

手动检查：

```bash
claude mcp list
nlm doctor
```

### 网页 URL 能加到 NotebookLM，但 notes 抓不到正文

这是两段不同的能力：

- NotebookLM ingest URL
- skill 本地抓网页正文做 notes grounding

如果第二段失败，优先检查：

- 页面是否登录态
- 页面是否需要 JS 渲染
- 页面正文是否过短

这种情况下，最稳的是手工导出成 `.txt`，改用 `source_text=...` 再跑 `notes-only`。

## 14. 相关文件

- `references/workflow.md`
- `references/notes-checklist.md`
- `references/mcp-parameter-notes.md`
- `references/evaluation-applied.md`
