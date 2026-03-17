# Codex 多 subagent 中文模板（v1）

这套模板适用于下面这种工作流：

- 主线程自己负责 plan / 决策 / 调度
- `codegen` 只实现当前 milestone
- `integration_tester` 不碰 server 产品代码，只在 `client/` 下补或改集成测试
- `cr` 只做严格审查，重点抓：
  - fallback 逻辑
  - dead code / unreachable branch
  - 过度兜底
  - 缺失测试
  - 不必要的抽象

## 目录说明

- `AGENTS.md`：仓库级总规则
- `.codex/config.toml`：项目级 Codex 配置
- `.codex/agents/*.toml`：3 个自定义 subagent
- `.agents/skills/*`：repo-local skills
- `docs/exec/current.md`：当前任务的执行计划（你和 Codex 讨论出来的 plan 落这里）
- `docs/code_review.md`：CR 规则，专门放 fallback / deadcode 检查项
- `docs/testing_contract.md`：client 集成测试契约
- `prompts/*.md`：你平时直接复制粘贴给 Codex 的操作模板

## 你要先改的地方

先把下面这些占位符换掉，不然代理会在空气里打拳：

1. `AGENTS.md`
   - 安装命令
   - lint / typecheck / unit / integration 命令
   - 如果有 monorepo，补充每个 package 的测试入口
2. `docs/testing_contract.md`
   - `client/` 里的集成测试目录
   - 线上 / staging 访问方式
   - 鉴权 token / cookie / 测试账号准备方式
   - 实际执行命令
3. `docs/exec/current.md`
   - 把你当前已经聊出来的 plan 填进去
   - 每个 milestone 都写 touched files / validation commands / acceptance

## 推荐执行顺序

### 0. 从仓库根目录启动 Codex
不要在半路子目录启动，然后再问为什么 agent 看不见整个项目结构。

### 1. 先确认配置生效
在 Codex CLI 或 App 的会话里先跑：

- `/status`
- `/debug-config`

目的：
- 看当前模型、审批策略、sandbox
- 看 `.codex/config.toml` 有没有真的被加载
- 看项目是不是 trusted

### 2. 先更新 plan，不要直接开写
打开 `prompts/00_更新计划.md`，把里面的提示词发给 Codex。

结果应该是：
- `docs/exec/current.md` 被更新
- 当前 milestone 明确
- 验证命令明确

### 3. 执行当前 milestone
打开 `prompts/01_执行当前里程碑.md`，发给 Codex。

编排固定为：
- 先 `codegen`
- 再并行 `integration_tester` + `cr`
- 最后主线程汇总

### 4. 有 blocker 就走修复回路
打开 `prompts/02_修复阻塞项.md`。

### 5. 当前 milestone 通过后，推进下一个
打开 `prompts/03_推进下一个里程碑.md`。

### 6. 最后补一刀 `/review`
打开 `prompts/04_最终审查.md`，或者直接在会话里输入 `/review`。

## 这个模板里最重要的 3 个约束

1. **只有 `codegen` 能改产品代码**
   - `integration_tester` 只允许改 `client/` 里的集成测试、fixture、helper
   - `cr` 是只读

2. **integration_tester 必须根据本次 diff 中的 unit tests 派生 client integration tests**
   - 不是凭空脑补测试
   - 不是另起一套和实现无关的“漂亮测试”

3. **CR 默认对 fallback / deadcode 极度不友好**
   - 不接受“先留着以后可能有用”
   - 不接受“先兜底，出了问题再说”
   - 不接受没有调用路径、没有触发条件、没有证据的兼容分支

## 关于 network access

这个模板默认：
- 全局 `workspace-write` + `network_access = false`
- 仅 `integration_tester` agent 打开 `network_access = true`

原因很简单：
- `codegen` 和 `cr` 一般不该上网
- 你的 `client` 集成测试要碰线上 / staging server，测试 agent 才需要网络

## 重要限制（别装作没看见）

原生 Codex 项目级配置里，`workspace-write` 的“工作区”通常就是你当前项目根目录。
这意味着：
- **不能靠 `writable_roots` 把写权限精确收窄到 `client/**`**
- 这里对 `integration_tester` 的“只能改 client”主要依赖：
  - agent 指令
  - skills
  - review 兜底
  - 你自己的人工审查

如果你想要**硬隔离**，更靠谱的做法是：
- 给 `client` 单独开项目 / worktree
- 或者用外层 Agents SDK / MCP 再包一层策略

## 技能目录兼容性说明

本模板按最新技能文档使用 `.agents/skills/`。
如果你本地版本因为历史原因没有发现这些 skills，可以临时把同一份技能目录复制到 `.codex/skills/` 做兼容。
不建议两个路径同时长期保留同名 skill，不然容易出现重复条目。

## 你日常只要记住这几句

- `docs/exec/current.md` 是唯一执行计划来源
- 一个 milestone 一个 milestone 地过，不要一口吞掉整个 feature
- 先 codegen，后 integration_tester + cr
- 单测驱动集成测试，不要让测试 agent 脑补业务
- CR 重点抓 fallback、deadcode、假抽象、测试漏项
