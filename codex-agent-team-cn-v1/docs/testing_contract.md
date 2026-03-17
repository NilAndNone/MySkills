# Client 集成测试契约

> 这是给 `integration_tester` 和主线程看的。先把占位符换掉。

## 目标
- `server` 逻辑以线上 / staging / 远端真实实现为准。
- 所有集成测试都写在 `client/` 目录下。
- `integration_tester` 必须依据本次 diff 中 `codegen` 新增或修改的单元测试，派生出对应的 client 集成测试。

## 测试目录
- client integration test root: `<REPLACE_WITH_CLIENT_INTEGRATION_TEST_DIR>`
- shared fixtures/helpers root: `<REPLACE_WITH_CLIENT_TEST_HELPER_DIR>`

## 运行方式
- install: `<REPLACE_WITH_CLIENT_INSTALL_CMD>`
- integration test command: `<REPLACE_WITH_CLIENT_INTEGRATION_TEST_CMD>`

## 访问目标
- base url env var: `<REPLACE_WITH_BASE_URL_ENV_NAME>`
- auth env var / setup: `<REPLACE_WITH_AUTH_SETUP>`
- extra env: `<REPLACE_WITH_OTHER_REQUIRED_ENVS_OR_NONE>`

## 派生规则
`integration_tester` 在写测试时必须：
1. 先读取 `docs/exec/current.md`
2. 再读取本次 diff 中由 `codegen` 新增/修改的单元测试
3. 抽取关键断言与输入条件
4. 把这些断言映射为 `client/` 下的集成测试
5. 输出“unit test -> integration test”映射关系

## 覆盖优先级
1. milestone 的主 happy path
2. milestone 明确列出的主要失败路径
3. 关键接口连通性
4. client 侧关键状态变化 / 渲染结果 / 错误提示（按你的项目实际情况调整）

## 禁止事项
- 不要在 `client/` 下复制一套 server 业务逻辑
- 不要为了让测试过而 mock 掉真实 server 业务
- 不要因为环境没配好就伪造通过
- 缺 env / 缺账号 / 缺测试数据时，要明确失败并报 prerequisite gap
