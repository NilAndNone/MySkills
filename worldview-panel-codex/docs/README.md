# worldview-panel-codex

一个给 **OpenAI Codex** 用的“网络画像多人格面板” skill 套件：

- 用 **Codex skill** 组织入口、共享规则和 panel 编排。
- 用 **24 个 worldview persona agents** 跑多人格并行分析。
- 额外附带一套 **md cache -> site/** 的默认报告渲染链路。
- 默认安装复制 skill 文件、报告工具、默认模板和 24 个 persona agents，不改写 generic built-in agents，也不写 `~/.codex/AGENTS.override.md`。
- 这 24 个 persona subagents 全部显式钉到 **`gpt-5.4` + `xhigh`**。
- 自动进入 worldview panel 依赖 skill 自身的 implicit invocation，不再依赖 home 级 AGENTS 注入。

> repo 根目录里的 `AGENTS.md` 和 `.codex/config.toml` 仍然保留为**项目级、显式 opt-in** 配置；它们不是远程安装器的一部分。

## 目录结构

```text
AGENTS.md
.codex/
  config.toml
  agents/
    <24 worldview personas>.toml
docs/
  README.md
  PERSONAS.md
  PROMPTS.md
  SELFTEST.md
misc/
  claude/settings.local.json
  _symlink_test/
scripts/
  generate_agents.py
  install_bundle.sh
  uninstall_bundle.sh
  install/
    manifest.txt
src/
  personas.json
  refs/
    <24 personas>/
      career.md
      startup.md
      product.md
      relationship.md
      politics.md
      philosophy.md
      public_discourse.md
      psychology.md
  resume_panel_materials/
    index.html
    site.css
    site.js
  skills/
    worldview-panel-codex/
      SKILL.md
      agents/openai.yaml
      references/
        roster.md
        routing-matrix.md
        task-packet.md
      tools/
        export_panel_cache.py
        panel_log.py
        panel_logging.py
        panel_site_common.py
        persona_materials.py
        prepare_context_packets.py
        render_panel_site.py
```

## 这包东西怎么生效

1. **远程一键安装**（推荐给用户级安装）
   - 当前 bundle 还没合进 `NilAndNone/MySkills` 的 `main`，远程安装先走发布分支 `dissociative_identity_disorder`。
   - 运行：

```sh
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh
```

   - 默认会安装到：
     - `~/.codex/skills/worldview-panel-codex`
     - `~/.codex/agents/<24 worldview personas>.toml`
     - `~/.codex/skills/worldview-panel-codex/tools/*.py`
     - `~/.codex/skills/worldview-panel-codex/refs/<persona>/*.md`
     - `~/.codex/skills/worldview-panel-codex/report-ui/*`
     - `~/.codex/skills/worldview-panel-codex/personas.json`
   - 默认**不会**安装或修改：
     - `~/.codex/AGENTS.override.md`
     - `default.toml` / `worker.toml` / `explorer.toml`
     - 项目级 `.codex/config.toml`
   - 安装完后重启 `codex`。

2. **项目级配置**（只给明确想在仓库内复用本地 guidance 的人）
   - 把 repo 根目录里的 `AGENTS.md` 和 `.codex/config.toml` 复制到你的 repo 根目录。
   - 如果你还想保留这套 bundle 的源码与安装链路，再一起复制 `src/`、`scripts/` 和 `docs/`。
   - 进入 repo 后启动 `codex`。
   - 首次使用时把 repo 标成 trusted project，不然 `.codex/config.toml` 不会被加载。

3. **手动用户级安装**（不用脚本时的 fallback）
   - 把 `.codex/agents/<24 worldview personas>.toml` 复制到 `~/.codex/agents/`
   - 把 `src/skills/worldview-panel-codex` 复制到 `~/.codex/skills/worldview-panel-codex`
   - 再把 `src/personas.json`、`src/refs/` 和 `src/resume_panel_materials/{index.html,site.css,site.js}` 复制到：
     - `~/.codex/skills/worldview-panel-codex/personas.json`
     - `~/.codex/skills/worldview-panel-codex/refs/`
     - `~/.codex/skills/worldview-panel-codex/report-ui/`

### 远程安装可选参数

```sh
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh -s -- --dry-run
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh -s -- --force
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/install_bundle.sh | sh -s -- --repo NilAndNone/MySkills --ref dissociative_identity_disorder
```

- `--dry-run`：只打印将写入哪些路径，不落盘
- `--force`：覆盖已安装的 skill / persona agent 文件
- `--repo` / `--ref` / `--subdir`：用于 fork、分支或 monorepo 子目录安装

## 卸载

```sh
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/uninstall_bundle.sh | sh
```

- 默认会移除：
  - `~/.codex/skills/worldview-panel-codex`
  - 本 bundle 安装的 `~/.codex/agents/<24 worldview personas>.toml`
- 默认不会触碰：
  - `~/.codex/AGENTS.override.md`
  - 任何 generic built-in agent 覆盖
- 默认不会删掉和 bundle 内容不一致的同名文件；如果确定要强制移除，追加 `--force`
- 卸载不会恢复安装阶段被覆盖掉的旧文件

### 远程卸载可选参数

```sh
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/uninstall_bundle.sh | sh -s -- --dry-run
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/uninstall_bundle.sh | sh -s -- --force
curl -fsSL https://raw.githubusercontent.com/NilAndNone/MySkills/dissociative_identity_disorder/worldview-panel-codex/scripts/uninstall_bundle.sh | sh -s -- --repo NilAndNone/MySkills --ref dissociative_identity_disorder
```

- `--dry-run`：只打印将删除哪些路径，不落盘
- `--force`：即使本地文件已被修改，也按 manifest 强制删除
- `--repo` / `--ref` / `--subdir`：用于 fork、分支或 monorepo 子目录卸载

## 快速上手

### 方式 A：显式调用 skill

```text
$worldview-panel-codex 分析这个问题：大模型创业还有没有意义？
必须使用 subagents。默认覆盖全部 24 个 worldview agents，任一时刻最多只开 6 个，分批等全部返回后再裁决。
```

### 方式 B：直接点名 agents

```text
必须使用 subagents，只用 existentialist, systems_operator, risk_manager, red_leftist, network_jester 这 5 个 agent 回答：
任一时刻最多只开 6 个，分批跑完再综合裁决。
大模型创业还有没有意义？
等全部返回后再给综合裁决。
```

### 方式 C：自然语言隐式触发

```text
不同人怎么看：婚育、职业和移民怎么一起权衡？
必须使用 subagents，开一个 full panel，覆盖全部 24 个 worldview agents。
任一时刻最多只开 6 个，分批跑完再汇总。
```

## packet-only 协议

- worldview persona subagent 只负责扮演角色并回答，不负责读文件、搜资料、补历史上下文。
- 主线程必须先准备好 subagent 所需的全部上下文任务包，再分发给 subagent。
- 分发 worldview persona subagent 时，默认使用 `fork_context = false`，不要把整段 thread history 直接 fork 进去。
- 如果回答依赖文章、代码、日志或对话材料，应该由主线程先读取并摘录，再放进任务包。
- 默认材料顺序是：`profile` 全量块 → `refs/<persona>/psychology.md` 全文 → `refs/<persona>/<domain>.md` 全文。
- 这两块人格材料是核心功能，不是可选增强项；主线程不能手工省略、缩写或“凭印象代替”。
- 本地 bundle 自带 `tools/persona_materials.py`，主线程在本地执行时必须先用它生成默认的 `[人格底盘材料] + [当前领域材料]`，再 dispatch。
- 任务包格式见 `src/skills/worldview-panel-codex/references/task-packet.md`。
- 如果缺关键材料，子人格必须先用 `缺失变量：...` 或 `缺少材料：...` 点明缺口，再做最小条件回答。

## 运行日志

现在这套 bundle 自带两层运行日志：

- 总日志：`~/.codex/log/worldview-panel-codex.log`
- 单次附件：`~/.codex/log/worldview-panel-codex/runs/<run-id>.log`

规则：

- 总日志只保留简要动作，适合平时直接看最近发生了什么。
- 单次附件按一次运行一份，适合顺着 `run-id` 回看完整动作串。
- 这两层日志都只记录动作和状态，不保存整段人格回答内容。
- 本地 bundle 里的工具现在都支持 `--run-id <run_id>`，会把记录写进同一趟运行的日志里。
- 只有明确需要详细排查时，再加 `--log-detail`，把更多中间动作写进单次附件。
- 如果主线程自己也要记简要动作，可以直接调用 `tools/panel_log.py`。

主线程单独记一条动作：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/panel_log.py --stage run_start --status started --message "starting worldview panel"
```

## 报告缓存与默认站点

这套 bundle 现在内置一条**基础报告链**：

```text
panel -> markdown cache -> Python 校验 -> site/
```

- `export_panel_cache.py`：把规范化 panel JSON 导出成标准缓存目录。
- `render_panel_site.py`：严格校验缓存目录结构，并渲染成 `site/index.html`。
- `report.json` 的核心汇总结构现在以 `common_ground`、`biggest_split`、`strong_but_risky`、`harsh_but_actionable`、`recommended_lenses` 为主；旧的立场分桶只作为兼容层。
- 默认缓存结构按当前示例组织：
  - `<root>/builders/<persona>.md`
  - `<root>/critics/<persona>.md`
  - `<root>/spectators/<persona>.md`
  - `<root>/defenders/<persona>.md`
  - `<root>/experientials/<persona>.md`
  - `<root>/meta.json`
  - `<root>/report.json`
- 默认站点入口固定为：`<root>/site/index.html`

### CLI 示例

Context prep only:

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/prepare_context_packets.py --input /path/to/round.json --stage all --json --run-id demo-run
```

导出缓存：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/export_panel_cache.py --input /path/to/panel.json --run-id demo-run
```

校验并渲染：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/render_panel_site.py --md-root /path/to/report-root --run-id demo-run
```

只校验目录结构：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/render_panel_site.py --md-root /path/to/report-root --validate-only --run-id demo-run
```

### 与 `frontend-skill` 的关系

- `worldview-panel-codex` **不会**在 skill 内部直接调用别的 skill。
- 默认站点这条基础链不依赖 `frontend-skill`。
- 如果当前会话环境里有 `frontend-skill`，主线程可以在默认 `site/` 成功生成后，再额外启一个前端开发 subagent 做二次开发。
- 这条升级链只允许写 `site/`，不允许改 `meta.json`、`report.json` 或原始 markdown cache。

## persona 模型是怎么钉的

- 每个 worldview persona agent 都显式声明：

```toml
model = "gpt-5.4"
model_reasoning_effort = "xhigh"
```

- 这层强约束只覆盖这 24 个 persona agents，不覆盖用户环境里的 generic built-in subagents。
- repo 根目录里的 `.codex/config.toml` 只影响你**显式采纳**这份项目级配置时的主线程默认值；远程安装器不会安装它。

## 代价与坑

- **仍然不便宜**：`gpt-5.4` 配上 `xhigh` 依然会拉高延迟和 token 消耗。
- **仍然会慢**：全量 24 人格即使按 3 个一批跑，也会比较久，输出还会很长。
- **主线程要多做一点脏活**：因为 subagent 被设计成 packet-only，不该自己去补材料，所以主线程需要先做上下文整理。
- **不是绝对强制**：如果你显式切模型、显式指定别的 agent、或者运行环境有额外覆盖，默认行为可能不同。
- **别对精神危机搞梗**：有自伤/伤人风险时，应该直接安全回复，不要开暗黑人格大会。

## 推荐默认策略

- 默认：覆盖全部 24 个 worldview agents，但任一时刻最多只拉起 3 个
- 用户指定分组（正选或排除）：按指示筛选
- 用户点名个人：严格按点名名单执行
- 默认 synthesize 输出：TL;DR → 问题拆解 → 人格面板 → 交叉裁决 → 主推建议 → 可执行下一步

## sandbox_mode 设计说明

24 个 worldview persona agents 设置了 `sandbox_mode = "read-only"`，因为它们只做分析输出，不需要写文件。

但要注意：`read-only` 只是不写文件，不等于天然禁止工具调用。所以这套 bundle 额外用两层协议补强：

- panel workflow 要求主线程先准备完整任务包，再用 `fork_context = false` 分发；
- persona agent 的共享约束明确禁止调用工具、读文件、搜资料和依赖任务包之外的上下文。
