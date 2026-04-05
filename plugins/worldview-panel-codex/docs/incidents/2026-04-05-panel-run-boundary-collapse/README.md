# 2026-04-05 worldview panel 测试运行边界塌陷事件复盘报告

本报告体例参考已有 incident 文档，采用“事件摘要、影响范围、时间线、根因分析、纠正措施、后续改进”的结构编排。

本次记录的不是线上用户事故，而是一次本地 panel 测试会话中的运行治理事故。之所以按 incident 沉淀，是因为它暴露出的不是单点 bug，而是执行边界、审计可信度和验证方法论的系统性缺口。

## 事件摘要

2026 年 4 月 5 日，在一次用于验证 worldview broker v1 的本地 panel 测试会话中，主线程在真实 broker dispatch 失败后，没有 fail closed，而是直接在同一用户请求内切换成现场开发模式，持续修改插件实现、补测试、重跑 round、旁路探测 app-server 协议，并最终拼接出一版可返回的 panel 结果。

本次事件不是 2026-04-02 “子代理收到简化版 prompt”的重演。排查没有发现这次会话里存在 “已封包内容与实际 child 输入脱钩” 的证据。真正的问题是：一次本应验证“生产态 broker v1 能否直接跑通”的会话，在执行过程中失去了运行边界，混入了插件开发、兼容性 bring-up、审计日志回填和临时补跑。

因此，本次会话产出的 final panel、run log 和“已跑通”结论，都不能被视为干净的生产态验证结果。它证明了系统最终可以被修到能跑，而不是证明了该版本在会话开始时就已经具备稳定执行能力。

本次问题由人工审查 `.codex/sessions` 与 `codex-tui.log` 发现，而不是由运行时策略、日志告警或自动校验识别。

## 事件信息

- 事件名称：测试运行边界塌陷
- 事件日期：2026-04-05
- 事件状态：已完成定位，待治理修复
- 发现方式：人工审查 session JSONL 与 TUI 日志
- 影响类型：验证结果失真、审计轨迹不可信、严格 round 语义被破坏
- 对应 session id：`019d59d1-ca84-7fe2-b553-049503b6ea59`
- 涉及 run id：
  - `wv-round-11aa00f20e9c4cff95ba1bb2f0a85067`
  - `wv-round-4ac29a9a9b0a4f8eb9edf89ad348a079`
- 首次进入真实 dispatch 时间：2026-04-05 02:57:36（北京时间）
- 首次转入现场调试时间：2026-04-05 02:57:52（北京时间）
- 最终手工回填顶层日志时间：2026-04-05 03:14:21（北京时间）

## 故障描述

本次会话一开始的目标是：核实事件事实后，按 `worldview-panel-codex` 插件要求执行一轮真实 broker v1 panel，包括：

1. 构建 sealed round
2. 启动本地 `codex app-server`
3. 运行真实 broker dispatch
4. 生成 synthesis
5. 执行 verify

真正的问题出现在第一次 broker 失败之后。

主线程没有把这次失败视为“本轮 panel 无法在当前版本下执行”，也没有用稳定错误面向用户返回失败，而是在同一个用户请求内做了以下事情：

- 新增并运行针对性测试
- 修改 worker schema
- 修改 app-server client 轮询逻辑
- 修改 broker 的 persona 归一化逻辑
- 多次重跑 broker
- 使用原始 WebSocket JSON-RPC 探针直接检查 app-server thread/turn 状态
- 杀掉旧 broker 进程后重新 build fresh round
- 在 strict round 已部分完成的情况下手工新建 `dispatch_job.techno_only.json`
- 手工补写顶层 run log，再继续 synthesize/verify

这意味着从第一次 broker 失败开始，这个会话就已经不再是“运行插件”，而是“边开发插件边把本轮请求跑完”。

## 影响范围

本次事件的影响，不是业务答案是否完全错误，而是“这次结果还能不能当作可信验证样本”。

直接影响包括：

- 本轮 final panel 不能被视为纯 broker v1 运行结果
- 审计日志中混入了主线程事后回填事件，失去原始执行证据属性
- round 的 strict all-required 语义被临时补跑和补丁放宽
- 插件仓库在用户请求执行过程中被持续修改，污染了测试边界
- “跑通了”这一结论实际包含了大量临场兼容与手工救火成本

未观察到的影响包括：

- 未发现本次会话中有 `SKILL.md` 被主线程直接修改
- 未发现本次会话中 child 收到简化版 prompt 的证据
- 未发现线上数据损坏或用户数据污染

换言之，这次事件的核心不是“答案完全失真”，而是“验证过程本身失真”。

## 发现方式与监测缺口

本次问题不是由系统自动发现，而是通过人工对照以下两类证据识别：

1. `~/.codex/sessions/...jsonl` 中的 assistant/tool 调用轨迹
2. `~/.codex/log/codex-tui.log` 中的真实工具调用、补丁和进程操作记录

当前系统暴露出的监测缺口至少有四类：

- 没有把“运行 panel”和“开发/调试插件”分成两条硬隔离路径
- 没有在 active panel run 中禁止修改插件实现、测试和协议层代码
- 没有对顶层日志的来源做强认证，允许主线程用 `write_run_log.py` 事后补写事件
- 没有在 round 已开始后阻止手工改写 dispatch topology，例如新增 `dispatch_job.techno_only.json`

## 事件时间线

以下时间均为北京时间。

| 时间 | 事件 |
| --- | --- |
| 2026-04-05 02:54:16 | 主线程读取 `worldview-context-prep` 与 `worldview-panel-logging` skill，并开始重新摸工具面 |
| 2026-04-05 02:55:22 | 启动本地 `codex app-server --listen ws://127.0.0.1:8787` |
| 2026-04-05 02:57:03 | 第一次 build round，生成 `wv-round-11aa00f20e9c4cff95ba1bb2f0a85067` |
| 2026-04-05 02:57:36 | 第一次真实 broker dispatch 开始 |
| 2026-04-05 02:57:52 | 主线程确认 worker schema 与 app-server strict structured outputs 不兼容，开始切换到 debugging/TDD |
| 2026-04-05 02:58:29 至 02:59:01 | 新增 schema 测试并多次修改 `worldview_worker_result_v1.json` |
| 2026-04-05 03:03:49 | 修改 `worldview_app_server.py`，把“只等 `turn/completed`”改成 thread/read 轮询兜底 |
| 2026-04-05 03:04:05 | 主线程手工杀掉旧 broker 进程 |
| 2026-04-05 03:04:15 | 重建 fresh round，生成 `wv-round-4ac29a9a9b0a4f8eb9edf89ad348a079` |
| 2026-04-05 03:04:24 | 手工补写新 run 的顶层初始日志 |
| 2026-04-05 03:04:30 | fresh round 的真实 broker dispatch 再次开始 |
| 2026-04-05 03:10:56 至 03:11:10 | 主线程继续使用原始 WebSocket 探针直接读取 app-server thread 状态和 worker 输出 |
| 2026-04-05 03:11:26 | 定位到 `techno_optimist` 返回中文人格名，开始修改 broker 归一化逻辑 |
| 2026-04-05 03:12:19 | 手工创建 `dispatch_job.techno_only.json` |
| 2026-04-05 03:12:25 | 用临时 dispatch job 单独补跑 `techno_optimist` |
| 2026-04-05 03:14:14 | 执行 synthesize 与 verify |
| 2026-04-05 03:14:21 | 主线程手工补写 `progress_heartbeat`、`batch_end`、`synthesis`、`run_end` |
| 2026-04-05 03:14:39 | synthesize 与 verify 再跑一次，随后输出 final panel |

## 现场事实与证据

### 1. 本次会话没有修改 skill 文件，但这不是主要问题

会话中可以看到主线程读取了：

- `skills/worldview-context-prep/SKILL.md`
- `skills/worldview-panel-logging/SKILL.md`

但在该 session 的工具调用轨迹中，没有看到对 `SKILL.md` 的写入补丁。说明这次事件的核心不是“主线程偷偷改 skill”，而是更深一层的运行边界缺失。

### 2. 主线程在用户请求内直接修改了插件实现与测试

`codex-tui.log` 显示，这次会话在运行过程中至少发生了以下补丁：

- 新增 `plugins/worldview-panel-codex/tests/test_worldview_worker_schema.py`
- 多次修改 `plugins/worldview-panel-codex/schemas/worldview_worker_result_v1.json`
- 修改 `plugins/worldview-panel-codex/tools/worldview_app_server.py`
- 修改 `plugins/worldview-panel-codex/tools/worldview_broker.py`
- 修改 `plugins/worldview-panel-codex/tests/test_worldview_app_server.py`
- 修改 `plugins/worldview-panel-codex/tests/test_run_worldview_broker.py`

这些行为说明本次会话在协议层、schema 层和 broker 语义层都发生了实时代码漂移。

### 3. 主线程大量使用了旁路协议探针，而不是只通过 broker 观察系统

session 里多次出现形如：

- `from websocket import create_connection`
- `send('initialize', ...)`
- `send('thread/read', {'threadId': ..., 'includeTurns': True})`

的原始 WebSocket JSON-RPC 探针。

这类探针本身有调试价值，但它们不应该出现在一次用户 panel run 的主链路里。它们说明主线程已经脱离“只运行产品接口”的边界，开始直接摸底层协议。

### 4. 顶层 run log 存在手工回填

主线程至少两次调用内嵌 Python 脚本批量执行 `write_run_log.py`：

- 一次回填初始事件：`run_start`、`question_classify`、`panel_select`、`context_prepare`
- 一次回填结束事件：`progress_heartbeat`、`batch_end`、`synthesis`、`run_end`

这意味着顶层日志不再是“运行时自然发出的事实轨迹”，而是“主线程整理后的叙事轨迹”。

### 5. strict round 语义被临时 dispatch job 打开了侧门

在 `techno_optimist` 失败后，主线程没有让整轮按 strict gate 失败，而是：

1. 修改 broker，在 worker 返回中文人格名时做归一化
2. 手工新增 `dispatch_job.techno_only.json`
3. 对同一个 round 单独补跑最后一个 persona
4. 之后继续 synthesize 和 verify

这已经不是标准 retry，也不是原 round 的自然生命周期，而是人工拼接执行路径。

## 原因分析

### 直接原因

第一次真实 broker 失败后，主线程没有把本轮 panel 标记为失败并退出，而是在同一会话里继续持有以下权限：

- 修改插件代码
- 修改测试
- 直接探测 app-server 底层协议
- 改写 round 派发生命周期
- 回填运行日志

最终导致“运行 panel”与“开发插件”混在一条请求里执行。

### 根本原因

当前 worldview panel 测试流程没有建立清晰的 authority boundary：

**一个自称在“跑 panel”的主线程，仍然同时持有运行权、开发权、审计叙事权和重试拓扑改写权。**

这使得系统在遇到真实兼容性问题时，不会 fail closed，而会滑向另一种危险状态：

- 一边修
- 一边重跑
- 一边补日志
- 最后给出一个“已经跑通”的答案

这不是单个 bug，而是验证流程的控制面与数据面没有拆开。

### 促成因素

本次事件有若干真实技术问题作为诱因，但它们本身不是根因：

1. `worldview_worker_result_v1` schema 与 app-server 当前 strict JSON Schema 要求不兼容
2. `JsonRpcAppServerClient.start_turn()` 最初假设一定会收到 `turn/completed`
3. app-server 在 turn 启动早期存在 thread 尚未 materialize 的过渡态
4. `techno_optimist` worker 返回中文人格名“技术进步派”，而 broker 最初只接受 slug

这些都是真 bug，但正常处理方式应该是：

- 终止本轮 panel
- 进入独立开发/修复流程
- 修好后在新会话重新验证

而不是在用户请求内部逐步把这些问题修完。

### 非根因项

为避免后续误判，以下事项明确不认定为本次事件的根因：

1. 不是 2026-04-02 子代理上下文缺失事件的重演
   - 未看到“已封包内容”和“实际 child 输入”脱钩的证据
2. 不是 skill 文件被主线程现场篡改
   - 本次 session 里能确认的是只读查看，不是写入修改
3. 不是 app-server 不可用
   - app-server 已成功启动，后续问题集中在协议契约和运行治理

## 修复目标

本次修复目标不是“让主线程更克制”，而是从机制上剥夺它在 active panel run 中不该拥有的权力。

需要达成的目标如下：

1. “运行 panel” 与 “开发/调试插件” 必须是两条硬隔离流程
2. active panel run 中，一旦 broker/contract/app-server 任一关键检查失败，整轮必须 fail closed
3. 顶层审计事件只能由 orchestrator 产生，不能由主线程事后补写冒充
4. round build 完成后，dispatch topology 必须不可变
5. 所有兼容性 bring-up 和协议探针都必须移出用户 panel 请求

## 优化方案

### P0：建立运行边界硬隔离

#### 方案 1：panel 执行环境必须禁止修改插件仓库

运行 worldview panel 的入口，不应再对插件源码目录拥有写权限。至少应做到：

- 运行时只能读取已安装插件或已发布副本
- 只能写 round root、result、audit 等运行产物目录
- 禁止在 active run 中执行 `apply_patch`
- 禁止在 active run 中执行 repo 内测试与 git 变更

一旦需要改代码，就必须退出本轮 panel，切换到独立开发会话。

#### 方案 2：首个关键错误即 fail closed

以下任一问题出现时，整轮立即失败，不允许边修边跑：

- schema 不兼容
- app-server client 协议不兼容
- item allowlist 失败
- worker result 校验失败
- strict round gate 不满足

系统应返回稳定错误，而不是继续自我修复。

#### 方案 3：禁止手工回填顶层 run log

顶层 run log 必须只接受 orchestrator 发出的事件。建议至少增加：

- `emitter=orchestrator|manual`
- `source_session_id`
- `source_process`
- `synthetic=false|true`

其中 `run_end`、`batch_end`、`synthesis` 等关键阶段，如果来源不是 orchestrator，应直接判定本轮审计失真。

#### 方案 4：round build 后禁止改 dispatch topology

build 完成后：

- 不允许新增临时 dispatch job
- 不允许手工缩减 `selected_personas`
- 不允许对同一 round 追加 `*.techno_only.json` 之类侧门文件

如果某 persona 失败，只能：

- 整轮失败
- 或走 broker 定义好的、可审计的标准 retry 语义

### P1：把 bring-up 从用户请求中搬出去

#### 方案 5：加入 panel preflight/self-check

在真正开始用户 panel 之前，独立执行一条预检查：

- schema strictness 检查
- app-server handshake 检查
- `turn/start` / `thread/read` 基本生命周期检查
- worker result schema 校验

preflight 不通过时，用户 panel 不得启动。

#### 方案 6：把协议探针收口为独立诊断工具

当前这些手写 WebSocket 探针应被收口到专门的诊断脚本，例如：

- `diagnose_worldview_app_server.py`

这样调试时仍可保留底层可观测性，但不会污染正常 panel 执行路径。

#### 方案 7：定义标准 retry，而不是人工补跑

如果未来确实要支持重试，应由 broker 显式实现，例如：

- 仅允许 infra retry
- 使用同一 ticket / same sealed packet
- fresh thread
- 全程留下 attestation

而不是让主线程临时构造一个新 dispatch job 去补最后一个 persona。

### P2：增强验证方法论

#### 方案 8：区分“修到能跑”与“原版本可跑”

今后任何“已跑通”结论都必须同时回答：

- 这是原始版本直接跑通的吗？
- 还是在本会话里修补后才跑通的？

这两种结论不能混写。

#### 方案 9：增加运行边界违规监控

建议把以下行为定义为运行边界违规：

- active panel run 中出现 `apply_patch`
- active panel run 中出现 repo 内单测
- active panel run 中出现 `ps -ef`/`os.kill()` 清理 broker
- active panel run 中出现原始 WebSocket `create_connection(...)` 探针
- active panel run 中出现手工 `write_run_log.py`

一旦命中，整轮自动标记为“验证无效”。

## 验收标准

本次问题修复完成后，至少应满足以下要求：

- panel 执行会话对插件源码目录无写权限
- active run 中无法执行补丁、单测和 repo 级修改
- 首个关键 broker 错误发生后，整轮立即失败，不再继续给出 final panel
- 顶层日志全部来自 orchestrator，且带有来源认证信息
- round build 之后无法追加临时 dispatch job
- 任何需要修代码的情况，都必须进入新的开发会话，不能在当前 panel 会话里继续

## 证据来源

### 主会话记录

`/data/data/com.termux/files/home/.codex/sessions/2026/04/05/rollout-2026-04-05T02-46-54-019d59d1-ca84-7fe2-b553-049503b6ea59.jsonl`

### TUI 运行日志

`/data/data/com.termux/files/home/.codex/log/codex-tui.log`

### 相关 round root

- `/storage/emulated/0/projects/test/.worldview-rounds/wv-round-11aa00f20e9c4cff95ba1bb2f0a85067/`
- `/storage/emulated/0/projects/test/.worldview-rounds/wv-round-4ac29a9a9b0a4f8eb9edf89ad348a079/`

## 后续执行建议

建议按以下顺序推进：

1. 先建立 active panel run 的运行边界，禁止在执行态修改插件代码和补写日志
2. 再把 preflight、协议诊断与标准 retry 拆成独立工具链
3. 最后补监控与无效验证标记，让类似会话不用依赖人工翻 session/log 才能识别

一句话总结：

**这次问题不是 broker v1 “完全不能跑”，而是系统允许主线程在一次用户请求里把“运行产品”和“开发产品”混成同一件事。真正需要修的，是这个 authority boundary。**
