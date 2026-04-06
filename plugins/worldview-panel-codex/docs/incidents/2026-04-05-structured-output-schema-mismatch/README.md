# 2026-04-05 worldview panel structured output schema 契约失配事件复盘报告

本报告体例参考已有 incident 文档，采用“事件摘要、影响范围、时间线、根因分析、纠正措施、后续改进”的结构编排。

本次记录的不是线上生产事故，而是一次本地 worldview panel 全流程测试中的 fail-closed 运行失败。之所以按 incident 沉淀，是因为它暴露出的不是单个人格内容问题，而是 broker 与当前 `codex app-server` 在 structured output schema 契约上的明确失配。

## 事件摘要

2026 年 4 月 5 日，在一次 24 个人格、4 个批次的 worldview panel 本地全流程测试中，broker 在启动第一个 worker turn 时即被 `codex app-server` 拒绝。拒绝原因不是材料缺失、线程上限或 prompt 退化，而是 worker 输出 schema `worldview_worker_result_v1.json` 不满足当前 app-server 对 structured outputs 的 JSON Schema 约束。

运行时返回的直接错误为：

> `invalid_json_schema`
>
> `Invalid schema for response_format 'codex_output_schema': In context=(), 'additionalProperties' is required to be supplied and to be false.`

本次事件在运行时已按 broker v1 规则 fail closed 收口，没有继续补跑、绕过 strict gate 或手工拼接结果。受影响的 24 个 persona 全部未产出 `attestation.json` 与 `technical_certified_result.json`，因此 `synthesis` 被严格跳过，`verify` 也判定失败。

本次事件不同于 2026-04-02 的“子代理上下文缺失”，也不同于 2026-04-05 早些时候的“测试运行边界塌陷”。这次问题的核心不是运行边界失守，而是插件声明的输出 schema 与当前 app-server 接受的 schema 子集不兼容。

## 事件信息

- 事件名称：structured output schema 契约失配
- 事件日期：2026-04-05
- 事件状态：已完成定位，待修复
- 发现方式：运行时 fail-closed 报错，随后通过 session、run log、audit 和 schema 文件复核确认
- 影响类型：broker dispatch 无法启动、整轮 strict panel 直接失败
- 对应 session id：`019d5cc9-16d3-78e0-a749-a371f25b47d7`
- 对应 turn id：`019d5ccf-9f13-7a02-b348-cf6f75a4c284`
- 对应 run id：`wv-round-bf535af05a034ae9b4b8a6fc74cbeeeb`
- 首次 batch 启动时间：2026-04-05 16:45:13（北京时间）
- 首次 dispatch 失败时间：2026-04-05 16:45:17（北京时间）
- 失败收口时间：2026-04-05 16:45:44（北京时间）

## 故障描述

本轮测试的目标是验证 `worldview-panel-codex` 在当前本地 `codex app-server` 环境下能否按 broker v1 的固定主流程完整跑通：

1. 构建 sealed round
2. 生成 `dispatch_job.json`
3. 启动 broker dispatch
4. 收集 `technical_certified_result.json`
5. 执行 synthesize
6. 执行 verify

前置阶段本身没有异常：

- `panel_select`、`question_classify`、`dispatch_ready`、`context_prepare`、`material_prepare` 均已完成
- round root 已成功构建
- 24 个人格的 `packet.txt`、`ticket.json`、`worker.skill.md` 均已落盘
- 顶层 run log 已进入 `batch_start`

真正的失败发生在 broker 试图为第一个 persona `absurdist_player` 启动 worker turn 时。`codex app-server` 在处理 `response_format` 时直接返回 `400 invalid_json_schema`，指出根对象必须显式提供且设置 `additionalProperties=false`。

由于这个错误发生在第一个 worker turn 启动阶段，broker 还未来得及产出任何一个 persona 的有效结果文件，整轮运行因此直接进入：

- `batch_end: failed`
- `synthesis: failed`
- `run_end: failed`

换言之，这次不是“跑到一半内容质量失真”，而是“还没真正开始生成 worker 结果，协议契约就先失败了”。

## 影响范围

本次事件影响的是整轮 panel 的执行能力，而不是某个单独人格的观点质量。

直接影响包括：

- 第一个 persona `absurdist_player` 在 `dispatch_started` 后立即 `dispatch_failed`
- 后续 23 个 persona 未进入实际 dispatch
- 24 / 24 个 persona 均未生成 `attestation.json`
- 24 / 24 个 persona 均未生成 `technical_certified_result.json`
- `synthesis` 因 `certified_total=0` 被严格跳过
- `verify` 对全部 24 个 persona 报告 missing attestation / missing technical_certified_result
- 本轮请求被判定为作废，不能产生可交付 panel 结果

未观察到的影响包括：

- 未发现 `packet.txt`、`ticket.json` 或 `worker.skill.md` 落盘异常
- 未发现 child 收到简化版 prompt 或上下文缺失
- 未发现主线程在本轮失败后继续边修边跑或补拼结果
- 未发现 app-server 未启动或连接不可达

这意味着本次事件的核心影响是：**严格 panel 根本无法启动进入结果生成阶段。**

## 发现方式与监测缺口

本次问题一部分是被运行时直接发现的，另一部分仍然暴露出明显的前置监测缺口。

运行时已具备的发现能力：

1. app-server 在第一时间拒绝了非法 schema，没有放任错误进入 worker 执行阶段
2. broker 在第一个 dispatch 失败后没有继续推进后续 persona
3. 顶层 run log 明确记录了 `batch_end failed`、`synthesis failed`、`run_end failed`
4. `verify_worldview_round.py` 能确认没有任何 persona 产出可认证结果

当前仍存在的监测缺口：

1. schema 不兼容直到真实 dispatch 时才暴露，缺少前置 contract preflight
2. 现有测试覆盖了“结果内容长什么样”，但没有覆盖“这个 schema 能不能被当前 app-server 接受”
3. run log 能记录失败状态，但不能直接指出是哪份 schema 文件违反了哪条约束
4. round build 可以完全成功，即便它绑定的 worker 输出 schema 注定无法通过 app-server 校验

这表明当前系统虽然具备 fail-closed 能力，但还不具备足够早的 fail-fast 能力。

## 事件时间线

以下时间均为北京时间。

| 时间 | 事件 |
| --- | --- |
| 2026-04-05 16:45:03 | 顶层 run log 记录 `panel_select completed`，`persona_total=24`，`batch_size=6` |
| 2026-04-05 16:45:03 | 顶层 run log 记录 `run_start started` |
| 2026-04-05 16:45:03 | 顶层 run log 记录 `question_classify completed`，`domain=public_discourse` |
| 2026-04-05 16:45:03 | 顶层 run log 记录 `dispatch_ready completed`，`batch_total=4` |
| 2026-04-05 16:45:03 | 顶层 run log 记录 `context_prepare completed`，sealed round 构建完成 |
| 2026-04-05 16:45:03 | 顶层 run log 记录 `material_prepare completed` |
| 2026-04-05 16:45:13 | 顶层 run log 记录 `batch_start started`，broker 开始第 1 批 dispatch |
| 2026-04-05 16:45:13 | `audit/events.jsonl` 记录 dispatch job `dispatch_started` |
| 2026-04-05 16:45:13 | `audit/events.jsonl` 记录 persona `absurdist_player` 的 `dispatch_started` |
| 2026-04-05 16:45:17 | `audit/events.jsonl` 记录 `absurdist_player` 的 `dispatch_failed`，错误为 `invalid_json_schema` |
| 2026-04-05 16:45:20 | session 中 broker 进程退出，堆栈停在 `worldview_app_server.py:start_turn()` |
| 2026-04-05 16:45:44 | 顶层 run log 记录 `synthesis failed`，`certified_total=0` |
| 2026-04-05 16:45:44 | 顶层 run log 记录 `batch_end failed`，`persona_total=24` |
| 2026-04-05 16:45:44 | 顶层 run log 记录 `run_end failed`，消息为 `panel failed closed due invalid broker/app-server schema contract` |

## 现场事实与证据

### 1. round 构建是完整的，失败不在材料侧

对应 round root：

- `/storage/emulated/0/projects/test/.tmp/worldview-rounds/wv-round-bf535af05a034ae9b4b8a6fc74cbeeeb/`

其中可以确认存在：

- `dispatch_job.json`
- `governance_seal.json`
- `round_manifest.json`
- 24 个人格的 `packets/*/packet.txt`
- 24 个人格的 `tickets/*.json`
- 24 个人格的 `identities/*/worker.skill.md`

这可以排除“材料未准备好”或“round 没 build 完”的可能性。

### 2. 顶层 run log 表明本轮在第 1 批启动后立即失败

单轮运行日志：

- `/data/data/com.termux/files/home/.codex/log/worldview-panel-codex/runs/wv-round-bf535af05a034ae9b4b8a6fc74cbeeeb.log`

其中可以看到：

- `batch_start` 仅出现一次
- 没有任何 `agent_result`
- `synthesis`、`batch_end`、`run_end` 均以 `failed` 收口
- `run_end` 明确写出 `invalid broker/app-server schema contract`

这说明系统并不是在中途结果收集中断，而是在 broker 启动阶段就已经失败。

### 3. audit 证据显示只触发了第一个 persona 的 dispatch

`audit/events.jsonl` 中只有三类关键事件：

1. dispatch job 的 `dispatch_started`
2. `absurdist_player` 的 `dispatch_started`
3. `absurdist_player` 的 `dispatch_failed`

没有看到：

- 第二个人格的 `dispatch_started`
- 任意人格的 `dispatch_completed`
- 任意人格的 attestation 写入相关证据

这说明 broker 在第一个 worker turn 即遭到 app-server 拒绝，并按 strict 语义终止。

### 4. session 与堆栈记录了 app-server 返回的原始错误

对应 session：

- `/data/data/com.termux/files/home/.codex/sessions/2026/04/05/rollout-2026-04-05T16-36-15-019d5cc9-16d3-78e0-a749-a371f25b47d7.jsonl`

其中 `run_worldview_broker.py` 的失败堆栈显示：

- broker 进入 `worldview_broker.py:run_broker`
- 在 `worldview_app_server.py:start_turn()` 抛出 `RuntimeError`
- 内层错误来自 app-server 返回的 `invalid_json_schema`
- 关键信息为：
  - `response_format 'codex_output_schema'`
  - `additionalProperties is required to be supplied and to be false`
  - `param = text.format.schema`

这说明失败发生在 structured output schema 提交给 app-server 的校验阶段，而不是 worker 运行后的内容解析阶段。

### 5. 当前 worker schema 本身就不满足该约束

对应 schema 文件：

- `/data/data/com.termux/files/home/plugins/worldview-panel-codex/schemas/worldview_worker_result_v1.json`

该文件当前特征包括：

- 根对象设置了 `additionalProperties: true`
- `judgment` 仅声明为 `type: object`
- `judgment` 没有明确 `properties`
- `judgment` 没有明确 `required`
- `judgment` 没有明确 `additionalProperties: false`

而 app-server 返回的错误已经明确要求：

- object schema 需要显式提供 `additionalProperties`
- 且该值必须为 `false`

这说明 schema 文件与运行时契约存在直接冲突。

### 6. verify 结果证明本轮没有任何 persona 产出有效结果

`verify_worldview_round.py` 对应输出显示：

- `status = failed`
- 24 个 persona 全部 `missing attestation`
- 24 个 persona 全部 `missing technical_certified_result`

这与顶层 run log 中的 `certified_total=0` 一致。

## 原因分析

### 直接原因

broker 在为第一个 persona 提交 `codex_output_schema` 时，向 app-server 发送了一个不被接受的 JSON Schema。app-server 当场返回 `400 invalid_json_schema`，导致第一个 worker turn 无法完成，整轮 dispatch 被 strict gate 直接中止。

### 根本原因

`worldview-panel-codex` 当前声明的 worker 输出 schema，没有与当前 `codex app-server` 所接受的 structured outputs schema 子集保持同步。

更具体地说，系统里存在一个未被显式治理的契约断层：

1. 插件侧把 `worldview_worker_result_v1.json` 当作合法输出 schema
2. broker 直接把这份 schema 传给 app-server 作为 `response_format`
3. app-server 对 object schema 的要求比插件当前 schema 更严格
4. 两边之间没有前置兼容性校验或版本协商

因此，本次问题不是“某个 persona 内容写坏了”，而是“插件输出契约本身不再被执行环境承认”。

### 促成因素

除直接根因外，本次事件还有几项明显促成因素：

1. 缺少 schema 级 contract test
   - 现有测试会喂给 app-server client 一段已经生成好的 JSON 文本
   - 但没有测试把真实 `worldview_worker_result_v1.json` 作为 `response_format` 提交给 app-server 或等价校验器

2. 缺少 dispatch 前 preflight
   - round build 已经成功
   - `dispatch_job.json` 已经生成
   - 直到第一个 worker turn 真正启动时才发现 schema 非法

3. 当前错误暴露粒度仍偏后
   - 错误发生在运行时 dispatch 阶段
   - 而不是在插件安装、启动自检或 round prepare 阶段

### 非根因项

为避免后续误判，以下因素明确不认定为本次事件的根因：

1. 不是子代理上下文缺失
   - 没有证据表明 child 收到简化版 prompt 或封包内容脱钩

2. 不是运行边界塌陷
   - 本轮没有出现边修边跑、补拼结果、侧门补 dispatch 的行为

3. 不是材料准备失败
   - round root 中的 packet、ticket、identity 文件均已完整落盘

4. 不是 app-server 未启动或不可连
   - 错误是来自 app-server 的明确协议响应，而非连接失败

5. 不是 verify 逻辑本身出错
   - verify 只是忠实反映了所有结果文件缺失这一事实

## 修复目标

本次修复的目标，不是让报错信息更好看，而是确保插件在进入真实 dispatch 前就能确认“当前输出 schema 一定可被当前 app-server 接受”。

需要达成的目标如下：

1. `worldview_worker_result_v1.json` 必须满足当前 app-server 的 structured output schema 约束
2. broker dispatch 前必须具备 schema preflight 能力
3. schema 契约不兼容时，应在 round build 完成前或至少 batch_start 前失败
4. 测试中必须覆盖“schema 可被执行环境接受”这一条件，而不只覆盖结果 JSON 的内容形状
5. incident 与 run log 应能区分“运行治理问题”和“协议契约问题”

## 优化方案

### P0：修正 worker schema 为严格可接受形状

建议至少完成以下调整：

1. 根对象改为 `additionalProperties: false`
2. `judgment` 改为显式声明 `properties`
3. `judgment` 补齐 `required`
4. `judgment` 也显式声明 `additionalProperties: false`
5. 如 app-server 对嵌套 object 还有其他限制，应全部同步到 schema 文件

如果只把根对象改成 `false`，而不继续收紧嵌套 object，后续极有可能在更深层 object 上再次失败。

### P0：在 broker dispatch 前增加 schema preflight

建议在真实 `turn/start` 前增加一道明确的 schema 兼容性校验，至少满足以下要求：

1. 直接校验 broker 将要提交给 app-server 的那份 schema
2. 失败时返回结构化错误，指出违反约束的 schema 路径
3. preflight 失败则整轮直接中止，不进入 `batch_start`

### P1：补齐 contract regression tests

建议至少新增以下测试场景：

1. `worldview_worker_result_v1.json` 根对象必须显式 `additionalProperties: false`
2. 所有嵌套 object 节点必须满足当前 app-server 的约束
3. broker 使用真实 schema 调用 app-server client 时，不应触发 `invalid_json_schema`
4. 当 schema 非法时，系统必须在 dispatch 前失败，并给出可定位的错误

### P1：改善日志与验证分层

建议增强如下：

1. 顶层 run log 增加 `schema_preflight` 阶段
2. audit 事件里记录被提交 schema 的版本和指纹
3. `run_end failed` 时，把失败类别区分为：
   - `schema_contract_failure`
   - `runtime_transport_failure`
   - `worker_result_validation_failure`

### P2：建立插件安装或启动自检

如果 worldview panel 未来要长期依赖 structured outputs，建议在安装或启动时加入轻量自检：

1. 读取当前 worker schema
2. 用本地 validator 或 app-server 兼容性探针校验
3. 若失败则直接阻止该插件进入“可运行”状态

## 结论

本次事件是一轮干净、可信的 fail-closed 失败样本。它证明 broker v1 在面对 schema 契约失配时能够及时中止，而不会继续产生不可信结果；但它也同时证明，当前插件仍缺少把这类问题提前到 dispatch 之前暴露出来的能力。

因此，这次 incident 的重点不是“失败后有没有收口”，而是“为什么会允许一份注定无法通过 app-server 校验的 schema 进入真实 panel 流程”。只有把这层契约前移为明确的 preflight 和回归测试，本类问题才算真正修完。
