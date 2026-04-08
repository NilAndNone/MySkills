# Worldview Panel Product Reframe v2

Date: 2026-04-07  
Status: Draft for review  
Scope: workspace-owned worldview panel product direction  

## TL;DR

当前系统已经具备较强的运行内核，但仍缺少一个可被用户稳定消费的产品层。

问题的核心不再是“能不能跑通”，而是三类问题长期耦合：

- 运行治理与协议兼容
- 多视角内容综合与压缩
- 用户消费界面与产品价值表达

本设计的目标不是继续在现有运行流程上叠加限制，而是先定义一个可成立的产品边界，再据此反推系统分层。

本轮重构采用“产品优先”路径，并做出以下明确约束：

1. 对外产品定位为 **多视角内容工作台**，而不是多人格运行器
2. 首个 wedge 固定为 **争议议题评论 briefing 生成器**
3. Studio 与 Audit 不再承担运行语义，而只定义 **展示表面**
4. 运行策略与结果等级从 Studio/Audit 中剥离，单独定义
5. 在 UI 之前，先定义一个真正可复用的 **内容对象**
6. 内部不再默认以固定人格 roster 驱动，而转向 **role-based panel planning**
7. 在正式重构前，先冻结 benchmark 与质量 rubric，避免“只改外观，不改质量”

一句话概括：

**目标是把 worldview panel 从一个能运行的多人格系统，重构为一个能稳定产出高质量争议议题内容 briefing 的产品。**

## Problem Framing

当前系统已经形成较强的运行能力，但产品层表达仍然主要继承了 broker / artifact / audit 视角。由此产生三个直接后果：

- 为了稳定运行，系统不断增长治理规则、协议边界和输入限制
- 最终产物仍偏向技术聚合，而不是面向用户的内容综合
- 展示层更接近取证界面，而不是创作者可直接消费的结果页

这进一步导致：

- 从运行角度看，系统越来越重
- 从产品角度看，系统越来越难讲清楚
- 从用户角度看，价值落点仍然不清晰

因此，这一轮设计优先回答四个问题：

1. 产品到底是什么
2. 第一阶段先服务谁
3. 用户最终拿走什么结果
4. 系统各层分别回答什么问题

本设计不以“先统一 runtime 命名”或“先改 viewer”为起点，而是以“先定义一个成立的内容产品”为起点。

## Design Objectives

- 把对外产品定位从“多人格运行器”转为“多视角内容工作台”
- 让 panel 成为内部方法，而不是外部卖点
- 让 Studio 默认交付内容结果，而不是运行记录
- 让 Audit 承担复核、证据、失败分析与可信性职责
- 定义一个独立于页面的 canonical 内容对象
- 让证据能力下沉到 claim 级，而不是停留在统一折叠区
- 用更窄的 wedge 缩小输入空间和系统复杂度
- 用 role-based planning 替代固定 persona roster 驱动
- 通过 benchmark 与 rubric 约束后续重构方向

## Non-Goals

- 本设计不直接定义具体代码文件、类名或模块路径
- 本设计不一次覆盖争议解读、复杂决策、团队协作三个方向
- 本设计不把“24 人格聊天体验”作为首要产品目标
- 本设计不试图在本轮中解决全部 runtime 历史兼容问题
- 本设计不展开 UI 视觉细节或前端框架实现

## Product Positioning

### External Positioning

对外产品定位：

**多视角内容工作台**

对外核心承诺：

**把复杂争议议题拆成可判断、可表达、可继续创作的高质量内容 briefing。**

产品的外部价值表达聚焦于：

- 一句话判断
- 共识与分歧
- 少数派提醒
- 风险与适用前提
- 可直接继续写作或表达的骨架

对外不强调“24 个人格”，也不把系统包装成角色扮演或人格聊天室。

### Internal Method

对内仍然使用 worldview panel 作为方法论与运行机制。

也就是说：

- 对内说 `worldview panel`
- 对外不卖 `panel`
- 对外卖 **多视角压缩与内容产出能力**

这样既避免产品价值被“人格数量”绑架，也保留系统真正的差异化：

**它不是普通写作 AI，而是一个能把多种视角压缩成高质量争议议题 briefing 的系统。**

## First Wedge

首个 wedge 进一步收窄为：

**争议议题评论 briefing 生成器**

首批目标用户：

- 自媒体作者
- 知识型写作者
- 研究型内容创作者
- 需要快速形成评论框架的表达者

首版核心使用方式：

用户输入一个争议议题，外加可选材料；系统输出一份可直接进入表达流程的 briefing，而不是一组平铺的人格发言。

首版默认交付内容包括：

- 一句话判断
- 事实 / 价值 / 策略三轴下的共识与分歧
- 反方最强点与少数派提醒
- 写成长文的结构建议
- 做口播或视频的切入角
- 下一步应补的材料

本阶段明确不优先做：

- 通用聊天产品
- 高风险决策建议产品
- 团队观点对齐工具
- 泛化到所有实时、高时效、高合规风险议题

原因不是这些方向没有价值，而是它们要么风险更高，要么离当前系统优势更远。首个 wedge 必须尽量贴近当前系统最强能力：

**对复杂议题进行多视角拆解与内容压缩。**

## Stage 0: Benchmark And Guardrails

在任何产品重构前，先冻结一套最小 benchmark 和质量标准。

目的不是为了研究运行性能，而是为了确保后续重构能回答一个更核心的问题：

**内容质量是否真的变好了。**

### Benchmark Set

建议先固定 15–20 个代表性题目，覆盖但不泛滥：

- 科技与平台议题
- 商业模式与产业判断
- 社会文化争议议题
- 媒体与舆论类争议
- 具有明显正反分歧、但不直接触碰高风险建议的公共讨论题

首版可以显式排除：

- 医疗建议
- 法律建议
- 金融投资建议
- 需要强实时事实核验的敏感政治议题

### Quality Rubric

每轮重构都用同一套 rubric 评估。至少包括：

- **Coverage**：是否覆盖关键视角，而非只重复一个主流立场
- **Compression**：是否对重复观点完成压缩，而非堆砌人格发言
- **Conflict Clarity**：主要分歧是否表述清楚
- **Minority Signal**：少数派提醒是否真实有价值，而非凑数
- **Traceability**：关键判断能否追溯到支持与反对依据
- **Creatability**：是否足够支持用户直接进入写作/口播/评论流程
- **Usefulness**：用户是否能在几分钟内理解并带走可执行内容

### Guardrails

首版产品边界要明确写清：

- 支持的问题类型
- 不支持的问题类型
- 支持的材料形式
- 默认时效要求
- 证据不足时如何降级表达

这一步的目标是：

**先定义什么叫好，再开始重构。**

## Stage 1: Product Positioning And User Promise

这一阶段先冻结产品语义，不先展开技术收口。

需要明确的内容包括：

- 产品外部定位
- 一句话承诺
- 用户类型
- 首个原子任务
- 产品不做什么

本阶段的核心结论如下：

- 产品类别：多视角内容工作台
- 首个原子任务：争议议题评论 briefing 生成
- 核心用户：内容创作者
- 价值交付：把复杂议题整理成可判断、可表达、可继续创作的结构化内容对象

本阶段不再以“多人格数量”或“运行系统复杂度”作为对外主叙事。

## Stage 2: Input Contract

在定义 Studio 页面之前，先定义首版输入契约。否则 Studio 输出无法稳定。

系统的产品入口只回答一个问题：

**用户这次想得到什么类型的内容结果。**

### Required Input

首版建议最小输入包含：

- **issue**：这次要讨论的议题或问题
- **output_intent**：希望产出什么形式的内容，例如 longform / video / thread / briefing
- **stance_mode**：中性比较、倾向支持、倾向反对、保留判断

### Optional Input

可选输入包括：

- **audience**：面向谁表达
- **materials**：用户提供的文章、截图、笔记、摘录
- **scope**：地域、行业、平台、圈层
- **timeframe**：讨论的时间范围
- **constraints**：禁区、语气、篇幅、风格要求

### Intake Normalization

系统应先把用户输入编译成一个产品级 brief，而不是直接进入 runtime 世界。

建议定义：

```json
{
  "issue": "",
  "output_intent": "briefing | longform | video | thread",
  "stance_mode": "neutral_compare | lean_support | lean_oppose | unresolved",
  "audience": "",
  "scope": "",
  "timeframe": "",
  "materials": [],
  "constraints": []
}
```

这个 brief 是产品入口对象，而不是运行 ticket。它的职责是：

**把用户意图编译成一个可被系统理解的内容任务。**

## Stage 3: Canonical Content Object

这是本轮重构最关键的一层。

在任何页面展示之前，系统必须先产出一个真正可复用的内容对象，而不是把人格结果直接喂给 viewer。

建议定义 canonical artifact：

**`content_brief_v1`**

它代表一份已经完成初步压缩、可被不同界面消费的议题 briefing。

### Proposed Structure

```json
{
  "issue": {
    "title": "",
    "question": "",
    "scope": "",
    "timeframe": ""
  },
  "summary": {
    "one_line_judgment": "",
    "premises": [],
    "best_use": "",
    "largest_risk": ""
  },
  "analysis": {
    "fact_axis": {
      "consensus": [],
      "conflicts": [],
      "minority_alerts": []
    },
    "value_axis": {
      "consensus": [],
      "conflicts": [],
      "minority_alerts": []
    },
    "strategy_axis": {
      "consensus": [],
      "conflicts": [],
      "minority_alerts": []
    }
  },
  "recommendations": {
    "recommended_angle": "",
    "writing_moves": [],
    "research_gaps": []
  },
  "writing_assets": {
    "article_outline": [],
    "video_outline": [],
    "thread_outline": []
  },
  "claims": [],
  "meta": {
    "surface_defaults": {},
    "execution_summary": {},
    "trace_refs": {}
  }
}
```

### Why This Matters

这一层的职责不是“把系统运行结果显示出来”，而是：

**把多视角结果压缩成一个产品层的内容对象。**

只要这个对象成立：

- Studio 可以消费它
- Audit 可以引用它
- 后续导出长文、脚本、串文都能复用它
- runtime artifact 不再直接污染产品页面

## Stage 4: Claim-Level Evidence Model

首版不能只做“结论 + 统一证据折叠区”。

对于争议议题内容产品，更重要的是：

**每条重要判断都应能局部追溯。**

因此，证据模型要下沉到 claim 级，而不是停留在页面尾部。

### Claim Object

每个关键结论、共识点、分歧点、少数派提醒，建议统一建模为 claim：

```json
{
  "claim_id": "",
  "text": "",
  "claim_type": "consensus | conflict | minority_alert | recommendation",
  "confidence": 0.0,
  "supporting_roles": [],
  "counter_roles": [],
  "source_refs": [],
  "evidence_strength": "low | medium | high",
  "scope_notes": [],
  "freshness_notes": [],
  "caveats": []
}
```

### Product Meaning

这意味着：

- Studio 默认可以折叠证据，但不是没有证据结构
- Audit 可以直接从 claim 追到原始依据
- 内容作者可以判断某一条是否足够稳，能不能公开表达
- 系统不再只能给出“整体可信”或“整体不可信”的粗粒度状态

一句话概括：

**不是最后附一坨证据，而是每个关键判断都自带证据挂钩。**

## Stage 5: Panel Planning And Composer

为了避免系统继续被固定人格 roster 拖重，内部规划从“固定人格全量运行”转向“基于角色的最小充分集”。

### From Persona Roster To Role Set

首版不要求所有人格默认出场，而是先根据任务规划最小角色集合。

例如首版可以优先规划以下角色：

- fact extractor
- systems thinker
- moral critic
- strategist
- practitioner
- contrarian

必要时再根据问题特性增加补充角色，而不是先铺满一个固定 roster。

### Role Planning Principle

角色规划遵循两个原则：

1. **最小充分覆盖**：先保证基本视角覆盖，不追求数量
2. **分歧驱动扩展**：当争议点不足、盲区明显或材料冲突时，再扩展角色

### Composer Responsibility

在 runtime 之后，必须有一层专门的 composer，把角色结果压缩成 `content_brief_v1`。

它的职责包括：

- 去重
- 合并近似观点
- 抽取共识
- 提炼主要冲突
- 标注少数派提醒
- 生成可用于写作的内容资产
- 生成 claim-level evidence linkage

这是系统从“运行系统”变成“内容产品”的关键层。

## Stage 6: Presentation Model

Studio 与 Audit 应该保留，但它们只描述 **presentation surface**，不再承担运行策略含义。

### Three Independent Axes

为了避免语义再次混乱，系统要明确拆分三条独立轴：

#### 1. Presentation Surface

定义给谁看、看什么：

- `studio`
- `audit`

#### 2. Execution Policy

定义这一轮怎么跑：

- `adaptive`
- `strict`

#### 3. Result Grade

定义这一轮最终对用户是否可用：

- `usable`
- `degraded`
- `blocked`

### Why This Separation Matters

这样可以避免以下误绑定：

- `audit` 不再天然等于 `strict`
- `studio` 不再天然等于 `adaptive`
- 同一轮 `strict` 成功结果也可以以 `studio` 方式消费
- 同一轮 `adaptive` 结果也可以进入 `audit` 被复核

这使产品表达、运行策略与结果可用性不再相互污染。

## Stage 7: Studio Surface

`studio` 是默认展示表面，面向普通用户与内容创作者。

它的承诺是：

- 首先交付内容价值
- 尽量减少运行层噪音
- 让用户几分钟内完成理解并进入表达动作

### Studio Default Structure

建议按以下顺序组织：

#### 1. Executive Judgment

用户先看到：

- 一句话判断
- 成立前提
- 最大风险或最大反对点
- 这份结果最适合拿去做什么

#### 2. Tension Map

按三个轴组织：

- 事实判断
- 价值判断
- 策略判断

每个轴只回答：

- 共识是什么
- 主要分歧是什么
- 少数派提醒是什么

#### 3. Perspective Cards

视角卡片作为支持层，而不是主舞台。每张卡片只展示：

- 核心立场
- 最强洞见
- 最大盲区
- 适用条件

#### 4. Creation Layer

允许用户直接带走：

- 长文起稿结构
- 视频或口播切入角
- 串文展开顺序
- 下一步建议补充的材料

#### 5. Expandable Trace

在需要时可展开：

- claim 级依据
- 角色贡献
- 材料来源
- 简化运行摘要

### Studio Status Language

Studio 中不直接暴露运行术语作为主语言，而使用产品化语义：

- 可用
- 可用但降级
- 本轮不建议使用

## Stage 8: Audit Surface

`audit` 面向系统维护者、调试者和高级用户。

它的承诺是：

- 真实展示本轮运行发生了什么
- 能追溯到角色结果、协议状态与失败原因
- 支持对 Studio 结论进行复核

### Audit Focus

Audit 重点回答：

- 这一轮运行是否完整
- 哪些角色成功、哪些失败
- 失败属于什么类型
- 哪些 claim 证据较弱
- 这一轮结果是否值得复用或复跑

### Audit Status Language

Audit 继续使用运行层术语，例如：

- strict fail closed
- adaptive degraded
- quorum passed
- quorum failed
- certification incomplete

### Relationship To Studio

Studio 与 Audit 应能互相跳转，但默认体验应明确区分：

- 普通用户默认进入 Studio
- 高级用户或维护者可切换到 Audit
- Audit 是黑匣子，不是默认首页
- Studio 是驾驶舱，不是运行日志页

## Stage 9: System Layering

本轮重构不追求把系统拆得更复杂，而追求每一层只回答一种问题。

### 1. Product Intake Layer

只回答：

**用户这次想得到什么结果。**

职责：

- 解析议题
- 解析输出用途
- 解析立场模式
- 归一化材料与范围约束
- 生成内容任务 brief

### 2. Runtime Core

只回答：

**这一轮能否可靠地产生足够的角色结果。**

职责：

- 分发
- 重试
- 协议兼容
- 认证
- 健康度判断

### 3. Composer Layer

只回答：

**如何把多角色结果压缩成产品级内容对象。**

职责：

- 去重压缩
- 冲突建模
- 结论生成
- claim-level evidence 绑定
- writing assets 生成

### 4. Presentation Layer

只回答：

**不同用户应看到什么版本的结果。**

职责：

- `studio` 消费内容对象
- `audit` 消费运行证据与复核信息
- 控制展示语言与默认层级

### 5. Artifact And Trace Layer

只回答：

**结果如何被追踪、存档、复查与导出。**

职责：

- 保存 runtime artifacts
- 保存 canonical content object
- 保存 claim trace refs
- 支持 UI 与导出功能复用

## Recommended Delivery Order

重构顺序建议渐进推进，而不是一次性推倒：

1. 先冻结 benchmark、rubric 与风险边界
2. 再冻结产品定位与首个原子任务
3. 再定义输入契约
4. 再定义 `content_brief_v1` 与 claim model
5. 再实现 role-based planning 与 composer
6. 再拆分 Studio / Audit 展示表面
7. 最后再统一内部命名、兼容层和旧语义

原因是：

如果先做技术收口，再做产品定义，很容易在新的代码结构上再次固化旧的运行视角。

## Success Criteria

当本轮重构方向成立时，应达到以下结果：

- 用户可以在一句话内理解产品价值，不需要先理解 worldview panel 或 broker
- Studio 首先呈现内容价值，而不是系统工件
- Audit 与 Studio 的语义和默认体验明显区分
- 系统能够产出可复用的 `content_brief_v1`，而不是仅产出人格结果集合
- 关键判断可以 claim 级追溯，而不是只能整体折叠查看证据
- 首个 wedge 能稳定演示“争议议题评论 briefing 生成”这一能力
- 后续实现可以按阶段推进，而不是被迫一次性改造全部系统

## Recommendation

推荐采用：

**方案 A：产品优先，但以 benchmark 和内容对象为约束。**

本轮重构的核心顺序应是：

1. 先定义什么叫好
2. 再定义产品是什么
3. 再定义用户拿到什么
4. 然后才决定系统如何支持它

最终目标不是把 worldview panel 做成一个更复杂的多人格运行框架，而是把它做成一个：

**能够稳定生成高质量争议议题 briefing 的多视角内容产品。**

这一步完成之后，系统才真正从“有发动机和黑匣子”走向“有驾驶舱、有内容对象、也有清晰产品价值”。
