# DEVELOPER MAINTENANCE

给维护这套 bundle 的开发者看。

目标不是解释“它大概是什么”，而是让你在改代码时知道：

1. 该改哪一层
2. 哪些文件必须联动
3. 哪些检查必须跑
4. 哪些默认值不能悄悄改丢

## 维护视角下，这套东西分成什么

### 一层：主 skill 规则

这层决定“主线程应该怎么做事”。

核心文件：

- `src/skills/worldview-panel-codex/SKILL.md`
- `src/skills/worldview-panel-codex/agents/openai.yaml`
- repo 根目录 `AGENTS.md`

这层控制的东西包括：

- 什么时候该命中 worldview panel
- 什么时候必须用 subagents
- 默认 panel 范围
- 默认并发上限
- 主线程先做什么、后做什么
- 任务包协议
- 日志协议
- 汇总结构

### 二层：人格材料和任务包

这层决定“每个 subagent 在收到消息前，主线程应该准备出什么包”。

核心文件：

- `src/personas.json`
- `src/refs/<persona>/*.md`
- `src/skills/worldview-panel-codex/tools/persona_materials.py`
- `src/skills/worldview-panel-codex/tools/context_packet_common.py`
- `src/skills/worldview-panel-codex/tools/prepare_context_packets.py`
- `src/skills/worldview-context-prep/SKILL.md`

这层控制的东西包括：

- 人格注册信息
- 分组归属
- profile 字段
- 每个领域的材料正文
- 任务包必需段落
- 校验失败时是否允许 dispatch
- 任务包落盘结构

### 三层：报告和页面

这层决定“汇总结果如何落地成文件和页面”。

核心文件：

- `src/skills/worldview-panel-codex/tools/export_panel_cache.py`
- `src/skills/worldview-panel-codex/tools/panel_site_common.py`
- `src/skills/worldview-panel-codex/tools/render_panel_site.py`
- `src/resume_panel_materials/index.html`
- `src/resume_panel_materials/site.css`
- `src/resume_panel_materials/site.js`

这层控制的东西包括：

- `report.json` 长什么样
- markdown cache 目录结构
- 哪些根目录文件合法
- 页面模板和渲染方式
- `site/index.html` 的最终入口

### 四层：运行日志

这层决定“执行动作怎么被记录下来”。

核心文件：

- `src/skills/worldview-panel-codex/tools/panel_logging.py`
- `src/skills/worldview-panel-codex/tools/panel_log.py`
- `persona_materials.py`
- `prepare_context_packets.py`
- `export_panel_cache.py`
- `render_panel_site.py`

当前约束不要改丢：

- 总日志固定写到 `~/.codex/log/worldview-panel-codex.log`
- 单次日志固定写到 `~/.codex/log/worldview-panel-codex/runs/<run-id>.log`
- 日志只记动作和状态，不记整段人格回答正文
- 同一趟运行的本地工具必须能复用同一个 `--run-id`
- 默认总日志短行可扫，细节更多的东西只进单次日志

### 五层：安装和交付

这层决定“用户装出去后，哪些文件真的能拿到”。

核心文件：

- `scripts/install/manifest.txt`
- `scripts/install_bundle.sh`
- `scripts/uninstall_bundle.sh`

凡是会被安装到 `~/.codex/skills/worldview-panel-codex/` 或 `~/.codex/agents/` 的文件，只要新增、删除、重命名，就必须同步 `manifest.txt`。

## 现在有哪些默认值

这是当前实现的核心默认值，改任何一个都要同步代码、测试和文档：

- 默认 panel 范围：全部 24 个人格
- 任一时刻最多 6 个 subagents
- 默认先准备任务包，再 dispatch
- 默认报告链：`panel -> markdown cache -> site/`
- 默认日志：总日志 + 单次日志
- 默认日志只记动作和状态
- 默认站点入口：`<root>/site/index.html`

## 改不同东西时，哪些文件必须一起动

### 改 panel 规则、并发、汇总结构

至少同步这些：

- `src/skills/worldview-panel-codex/SKILL.md`
- `src/skills/worldview-panel-codex/agents/openai.yaml`
- `docs/USER_GUIDE.md`
- `docs/USER_PROMPTS.md`
- `docs/DEVELOPER_SELFTEST.md`
- 相关测试

### 改人格注册、材料或分组

至少同步这些：

- `src/personas.json`
- `src/refs/`
- `.codex/agents/*.toml`
- `docs/USER_PERSONAS.md`
- `src/skills/worldview-panel-codex/references/roster.md`
- `scripts/install/manifest.txt`
- `tests/test_persona_materials.py`

### 改任务包格式或 context prep

至少同步这些：

- `context_packet_common.py`
- `prepare_context_packets.py`
- `src/skills/worldview-context-prep/SKILL.md`
- `docs/USER_GUIDE.md`
- `docs/DEVELOPER_SELFTEST.md`
- 相关集成测试

### 改报告结构或页面模板

至少同步这些：

- `export_panel_cache.py`
- `panel_site_common.py`
- `render_panel_site.py`
- `src/resume_panel_materials/`
- `docs/USER_GUIDE.md`
- `docs/DEVELOPER_SELFTEST.md`
- `tests/test_panel_site_common.py`

### 改日志系统

至少同步这些：

- `panel_logging.py`
- `panel_log.py`
- 接入日志的 CLI
- `docs/USER_GUIDE.md`
- `docs/DEVELOPER_SELFTEST.md`
- `tests/test_panel_logging.py`

如果你改了这些内容：

- 日志路径
- 行格式
- `run_id` 传播方式
- 哪些事件会被记录

那不要只看单测，必须补手工验证。

### 改安装或卸载链路

至少同步这些：

- `scripts/install/manifest.txt`
- `scripts/install_bundle.sh`
- `scripts/uninstall_bundle.sh`
- `docs/USER_GUIDE.md`
- `docs/DEVELOPER_SELFTEST.md`

## 文档维护规则

当前文档分工是：

- 用户文档
  - `docs/USER_GUIDE.md`
  - `docs/USER_PROMPTS.md`
  - `docs/USER_PERSONAS.md`
- 开发者文档
  - `docs/DEVELOPER_SELFTEST.md`
  - `docs/DEVELOPER_MAINTENANCE.md`

发版前至少看这几件事：

### 1. 用户文档有没有说人话

重点看：

- 安装命令还对不对
- 默认并发是不是 6
- 日志路径是不是当前实现
- 页面入口是不是 `site/index.html`
- 示例 prompt 还符不符合当前行为

### 2. 开发者文档有没有说全

重点看：

- 这次改动涉及哪一层
- 哪些联动文件被写清楚了
- 自测命令是不是还能直接复制跑

### 3. 文件名有没有继续保持“按受众分层”

不要再退回不带受众前缀的模糊命名。

这里统一使用：

- `USER_*`
- `DEVELOPER_*`

就是为了让人一眼看出该看哪份。

## 维护者检查清单

### 自动检查

默认先跑：

```sh
python3 -m unittest discover -s worldview-panel-codex/tests
```

### 手工检查

建议顺序：

1. 先检查人格材料
2. 再检查 context prep
3. 再检查报告导出
4. 再检查页面渲染
5. 最后检查日志链

命令示例：

```sh
python3 ~/.codex/skills/worldview-panel-codex/tools/persona_materials.py --persona techno_optimist --domain career --run-id maint-check
python3 ~/.codex/skills/worldview-panel-codex/tools/prepare_context_packets.py --input /path/to/round.json --stage all --json --run-id maint-check
python3 ~/.codex/skills/worldview-panel-codex/tools/export_panel_cache.py --input /path/to/panel.json --run-id maint-check
python3 ~/.codex/skills/worldview-panel-codex/tools/render_panel_site.py --md-root /tmp/codex-worldview-panel/<report-id> --run-id maint-check
tail -n 20 ~/.codex/log/worldview-panel-codex.log
sed -n '1,40p' ~/.codex/log/worldview-panel-codex/runs/maint-check.log
```

### 你应该明确看什么结果

- `persona_materials.py`
  - 输出里有 `[人格底盘材料]` 和 `[当前领域材料]`
- `prepare_context_packets.py`
  - 每个人格目录都有 `packet.txt`、`packet.json`、`validation.json`
- `export_panel_cache.py`
  - 产出合法的 markdown cache 根目录
- `render_panel_site.py`
  - 成功生成 `site/index.html`
- 日志链
  - 总日志和单次日志都能看到同一个 `run_id`
  - 没有整段人格正文泄漏进日志

## 常见维护失误

### 1. 改了工具但没改安装清单

结果就是：

- 本地仓库能跑
- 用户安装出去跑不了

### 2. 改了默认并发但没改文档

结果就是：

- `SKILL.md`、`USER_GUIDE.md`、`USER_PROMPTS.md`、`DEVELOPER_SELFTEST.md` 互相打架

### 3. 改了 `report.json` 结构但没改页面模板

结果就是：

- 导出能过
- 页面渲染错位或空白

### 4. 改了日志格式但没补手工验证

结果就是：

- 单测过了
- 真正查日志时发现找不到关键信息

### 5. 重命名文档但没改引用

结果就是：

- guide 里还在指向旧文件名
- 维护文档里还有旧路径
- 测试还在读旧文件

## 发版前最后一轮检查

至少做这 6 件事：

1. `python3 -m unittest discover -s worldview-panel-codex/tests`
2. 跑一次 `persona_materials.py`
3. 跑一次 `prepare_context_packets.py`
4. 跑一次 `export_panel_cache.py`
5. 跑一次 `render_panel_site.py`
6. 打开用户文档和开发者文档各看一遍，确认名字、内容和当前行为一致
