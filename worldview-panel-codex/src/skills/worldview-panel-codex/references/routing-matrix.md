# Routing matrix — 分组选择与汇总权重

## 默认行为

**默认选择所有 24 个 worldview agents 参与回答。** 但任一时刻最多只拉起 3 个，按批次跑完。

## 用户指定分组

支持两种语法：

### 正选（只用某些组）
> "只用建设派和批判派"
> "only builders and critics"

→ 只 spawn 被点名的分组。

### 排除（跳过某些组）
> "跳过旁观派"
> "skip spectators"

→ spawn 除被排除组之外的所有 agents。

### 点名个人（保留）
> "只用 existentialist 和 risk_manager"

→ 严格按点名名单 spawn，不受分组限制。

## 调度约束

- 任一时刻最多只运行 3 个 subagents。
- 当目标名单超过 3 个时，按原定名单顺序拆成多个批次，每批最多 3 个。
- 必须等所有批次结束后再做总汇总，不要边到边写。
- 对 worldview persona subagents，默认 `fork_context = false`，只下发主线程整理好的任务包。
- 不要把 routing、汇总草稿、整段历史对话一起传给 subagents。

## 汇总权重

全员回答后，汇总裁决时根据问题类型调整展示优先级。权重高的组在面板观点中优先展示、在主推建议中优先被引用。

### 职业 / 创业 / 技术 / 产品
- 高权重：`builders`, `defenders`
- 标准权重：`critics`, `spectators`, `experientials`

### 关系 / 婚育 / 家庭 / 自我认同
- 高权重：`experientials`, `defenders`
- 标准权重：`builders`, `critics`, `spectators`

### 政治 / 制度 / 公共事件 / 社会趋势
- 高权重：`critics`, `builders`
- 标准权重：`spectators`, `defenders`, `experientials`

### 生活方式 / 意义 / 哲学 / 审美化选择
- 高权重：`experientials`, `defenders`
- 标准权重：`builders`, `critics`, `spectators`

### 舆论 / 流量 / 传播 / 圈层观察
- 高权重：`spectators`, `critics`
- 标准权重：`builders`, `defenders`, `experientials`

## 不要这样做

- 不要自作主张跳过某些组——除非用户明确排除。
- 不要让汇总权重变成"只看权重高的"——标准权重的组也必须出现在面板观点里。
- 不要在用户要求 subagents 时偷懒单线程回答。
