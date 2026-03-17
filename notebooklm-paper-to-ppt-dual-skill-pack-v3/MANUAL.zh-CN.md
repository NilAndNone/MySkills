# 使用手册（Claude Code 版）

这份仓库现在只保留 **Claude Code** skill。

之前的 Codex 版本已经从仓库里删除，顶层文档也不再提供 `.agents/skills`、`$skill-name`、`codex mcp` 之类的说明。这里默认你要装和用的，都是 `claude-code/` 下面这一套。

---

## 1. 先看结论

### 这套包适合什么

适合你要做这样的工作流：

1. 输入一篇论文 PDF，或者一个可直接抓正文的单页 URL
2. 用 NotebookLM 生成 slide deck
3. 下载成 `.pptx`
4. 需要时继续补 speaker notes，并返回 QA 摘要和风险提示

### 这套包不适合什么

不适合你把它当成“Google 官方稳定 slide generation API”去做严肃生产托底。原因没变：

- 官方 NotebookLM Web 确认有 slide deck 和 `.pptx` 下载
- 但公开 Enterprise API 文档没有列出 slide deck generation API
- 自动化这里依赖的是社区 `notebooklm-mcp-cli` 桥接，而不是 Google 官方公开 slide API

这不是不能用；这是**能用，但别假装它是企业级后端能力**。

---

## 2. 现在仓库里有什么

```text
notebooklm-paper-to-ppt-dual-skill-pack-v3/
├── README.md
├── MANUAL.zh-CN.md
├── references/
│   ├── SOURCES.md
│   └── EVAL_NOTES_APPLIED.md
└── claude-code/
    ├── README.md
    ├── MANUAL.zh-CN.md
    ├── scripts/
    └── .claude/skills/notebooklm-paper-to-ppt/
```

你真正安装和执行的是：

- `claude-code/scripts/` 里的安装脚本
- `.claude/skills/notebooklm-paper-to-ppt/` 里的 skill、本地脚本、参考资料

如果你还需要 Codex 版本，只能自己从旧提交恢复；当前仓库内容已经不再维护它。

---

## 3. 前置条件

至少满足这些：

1. 本机能运行 Python / `uv`
2. 已安装或可安装 `notebooklm-mcp-cli`
3. 你能正常 `nlm login`
4. 你本地装了 Claude Code 客户端

建议先手动确认：

```bash
uv --version
claude --version
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

## 4. 安装

### 4.1 项目级安装

```bash
cd /path/to/your/repo
bash /path/to/notebooklm-paper-to-ppt-dual-skill-pack-v3/claude-code/scripts/install_skill_project.sh
bash .claude/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_claude_code.sh
bash .claude/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

### 4.2 用户级安装

```bash
bash /path/to/notebooklm-paper-to-ppt-dual-skill-pack-v3/claude-code/scripts/install_skill_user.sh
bash ~/.claude/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_claude_code.sh
bash ~/.claude/skills/notebooklm-paper-to-ppt/scripts/check_env.sh
```

如果目标路径里已经有旧版 skill，安装脚本会先备份成带时间戳的 `.bak.YYYYmmdd-HHMMSS` 目录，再安装新版。

---

## 5. 调用方式

这是一个 **manual-only** Claude Code skill，入口固定为：

```text
/notebooklm-paper-to-ppt ...
```

当前 frontmatter 设计是：

```yaml
disable-model-invocation: true
context: fork
agent: general-purpose
```

意思很直接：

- 不自动乱触发
- 在隔离上下文里跑流程
- 适合这种会上传 source、生成 artifact、下载文件、写 notes 的副作用型工作流

典型调用示例：

```text
/notebooklm-paper-to-ppt source=./papers/attention-is-all-you-need.pdf output=./out/attention-is-all-you-need.pptx language=zh-CN deck_format=presenter
```

```text
/notebooklm-paper-to-ppt source=https://example.com/article output=./out/article-deck.pptx language=zh-CN
```

```text
/notebooklm-paper-to-ppt mode=notes-only raw_pptx=./out/article-deck.raw.pptx source_url=https://example.com/article output=./out/article-deck.pptx
```

---

## 6. 支持的工作模式

保留一个命令入口，但分成 3 个模式：

- `mode=full`
  - 默认值
  - 创建 NotebookLM deck，下载 raw `.pptx`，再走 notes 流程
- `mode=deck-only`
  - 只生成并下载 raw `.pptx`
- `mode=notes-only`
  - 基于现有 `raw_pptx=...` 只跑 notes 流程

如果没写 `mode`，但输入已经带了：

- `raw_pptx=...`
- 加上 `source_pdf=...` / `source_text=...` / `source_url=...` 其中之一

skill 会自动判定为 `notes-only`。其他情况默认 `full`。

---

## 7. 输入与输出约定

### 支持的输入

`full` / `deck-only` 的 `source=` 支持：

- 本地 PDF
- 可直接抓正文的单页网页 URL

`notes-only` 必须给：

- `raw_pptx=...`

并且三选一：

- `source_pdf=...`
- `source_text=...`
- `source_url=...`

### 输出约定

如果 final output 是：

```text
./out/deck.pptx
```

则默认派生：

- raw deck：`./out/deck.raw.pptx`
- notes artifacts：`./out/deck.notes-artifacts/`
- 网页 grounding 文本：`./out/deck.notes-artifacts/tmp/source_webpage.txt`

### 网页输入边界

网页支持范围限定为：

- 只抓你给的那个 URL
- 不递归抓子链接
- 页面必须能直接 HTTP 获取
- 不支持登录态、验证码、重度 JS 渲染后才出现正文的页面

相关辅助脚本是：

```text
.claude/skills/notebooklm-paper-to-ppt/scripts/fetch_web_source.py
```

它会优先用 `trafilatura` 抽正文；没有的话，回退到标准库 HTML 文本提取。

---

## 8. 内部流程边界

### `full`

1. 创建 notebook
2. source add
3. grounding query
4. 生成 slide deck
5. 下载 `<output>.raw.pptx`
6. 预处理 notes 上下文
7. Claude 生成 `notes.json`
8. `validate-notes`
9. `apply-notes`

### `deck-only`

做到 raw `.pptx` 下载完成为止，不进入 notes 流程。

### `notes-only`

跳过 notebook 创建、source add、grounding query、slide generation、raw 下载，直接从 notes 前处理开始。

---

## 9. 常见故障

### 9.1 `nlm login --check` 失败

处理：

```bash
nlm login
```

如果浏览器登录链路本身有问题，再跑：

```bash
nlm doctor
```

### 9.2 Claude Code 看不到 MCP server

先查：

```bash
claude mcp list
nlm doctor
```

然后重开 Claude Code 会话，再确认 `/mcp` 里能看到 NotebookLM server。

### 9.3 deck 结构不对

不要优先 revise。官方帮助已经写了：

- revise 不能增删页
- revise 不参考 sources

所以结构错了就**重生成**，别拿 revision 硬救错误叙事骨架。

### 9.4 `.pptx` 下载失败

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

## 10. 推荐工作方式

### 方式 A：先用 CLI 验证 happy path，再上 skill

适合第一次搭环境：

1. `nlm login`
2. 手工跑 `cli_flow_template.sh`
3. 确认能拿到 `.pptx`
4. 再用 `/notebooklm-paper-to-ppt`

优点：排错简单  
缺点：略手工

### 方式 B：直接用 skill

适合你已经有稳定环境：

- `/notebooklm-paper-to-ppt`

优点：自然语言体验更顺  
缺点：环境没配好时，错误来源会更分散

---

## 11. 自检清单

- [ ] `.claude/skills/notebooklm-paper-to-ppt/SKILL.md` 存在
- [ ] `claude mcp list` 看得到 NotebookLM server
- [ ] `/notebooklm-paper-to-ppt` 能被识别
- [ ] `uv` 可用
- [ ] `nlm` 可用
- [ ] `nlm login --check` 通过
- [ ] 论文 source ingest 成功
- [ ] grounding query 不为空且不跑题
- [ ] slide deck artifact 完成
- [ ] `.pptx` 文件真实存在
- [ ] QA 通过

---

## 12. 建议阅读顺序

1. 顶层概览：`README.md`
2. Claude Code 快速说明：`claude-code/README.md`
3. Claude Code 详细手册：`claude-code/MANUAL.zh-CN.md`
4. 文档出处：`references/SOURCES.md`
5. 评审修订记录：`references/EVAL_NOTES_APPLIED.md`

---

## 13. 最后的实话

这套东西现在就是一个面向 Claude Code 的 `paper -> NotebookLM -> pptx` skill workflow。

它依然是：

- 官方 Web 功能
- 加上社区 reverse-engineered CLI / MCP bridge
- 再加上 Claude Code skill 机制

所以它是**能干活的工程拼装件**，不是官方承诺过 SLA 的平台能力。这个边界别写丢了。
