# 仓库 Agent 工作约定

## 信息优先级
1. 当前用户需求
2. `docs/exec/current.md`
3. `docs/testing_contract.md`
4. `docs/code_review.md`
5. 代码与测试事实

## 固定工作流
对任何非 trivial 任务：
- 主线程负责 plan、约束、调度、收口。
- `codegen` 只实现 `docs/exec/current.md` 当前 milestone。
- `codegen` 完成后，再并行运行 `integration_tester` 与 `cr`。
- 只有 `codegen` 可以修改产品代码。
- `integration_tester` 只允许修改 `client/` 目录下的集成测试、fixture、helper、测试文档。
- `cr` 只读，不修改任何文件。
- 当前 milestone 没过，不得进入下一个 milestone。

## 命令约定
如果 `docs/exec/current.md` 为当前 milestone 指定了命令，以它为准；否则用下面默认命令：

- install: `<REPLACE_WITH_INSTALL_CMD>`
- lint: `<REPLACE_WITH_LINT_CMD>`
- typecheck: `<REPLACE_WITH_TYPECHECK_CMD>`
- unit: `<REPLACE_WITH_UNIT_TEST_CMD>`
- integration(client): `<REPLACE_WITH_CLIENT_INTEGRATION_TEST_CMD>`

## 代码约束
- 默认不新增 broad fallback 逻辑。
- 默认不新增“先留着以后可能会用”的代码。
- 默认不新增无证据的兼容分支。
- 不允许 silent catch / 吞错 / 默认成功返回。
- 不允许因“怕报错”而塞一堆防御性分支掩盖真实问题。
- 不做无关重构。
- 优先最小可行 diff。
- 优先删除而不是抽象。
- 任何新增 helper / adapter / abstraction，都必须能回答“它减少了什么重复，或者隔离了什么确定存在的变化点”。

## 测试约束
- `codegen` 若修改行为，优先补单元测试。
- `integration_tester` 必须读取本次 diff 中的新增/修改单元测试，并将关键断言映射为 `client/` 下的集成测试。
- 集成测试优先覆盖：
  - 关键 happy path
  - 计划中明确的主要失败路径
  - 跨模块/跨接口联通性
- 测不通就明确报环境/数据问题，不要伪造通过。

## CR 输出要求
`cr` 输出固定为：
1. Blocking findings
2. 高置信 dead code / deletable code
3. 强简化建议
4. 可选 nits

每个 blocking finding 必须包含：
- 文件
- 风险
- 最小修复建议

## 审查准则
参考 `docs/code_review.md`。
