# 人格素材深度调研任务书

## 背景

我们正在构建一个「世界观面板」(Worldview Panel) 系统——一个由 24 个互联网人格组成的多视角分析引擎。每个人格代表一种真实存在于中文/英文互联网上的思维方式和话语风格（例如"网左"、"技术进步派"、"犬儒抽离派"等）。

当用户提出一个问题时，系统会同时从多个人格视角输出分析，帮助用户看到同一问题的不同侧面。

### 当前状态

每个人格目前只有一段简短的角色定义（约 200 字），包含：核心信念 3 条、说话风格 1 句、盲区 1 句、签名句 1 句。这导致：

- **观点输出过于泛化**，缺乏真实的细节和论据支撑
- **人格之间区分度不够**，不同人格在某些领域的回答趋同
- **缺乏真实世界的锚定**，没有具体的人物、案例、理论来支撑角色的可信度

### 目标状态

为每个人格建立一套**丰富的参考素材体系**，使其在 7 个议题领域中都能输出有血有肉、符合人设的深度观点。

## 24 个人格总览

### 分组结构

| 组 ID | 中文名 | 姿态 | 人格列表 |
|---|---|---|---|
| builders | 建设派 | 改良、修补、往前推 | techno_optimist(技术进步派), systems_operator(系统实用主义者), institutionalist(制度修补派), existentialist(存在主义者), performance_hawk(绩效鹰派) |
| critics | 批判派 | 揭露、反对、要求重分 | red_leftist(网左), online_rightist(网右), collapse_prophet(崩坏预言家), radical_meme_dissident(反建制梗学家) |
| spectators | 旁观派 | 观察、嘲弄、不下场 | network_jester(网络乐子人), terminal_jester(终极乐子人), postmodern_ironist(后现代解构派), cynical_detached(犬儒抽离派), attention_marketer(营销号) |
| defenders | 退守派 | 缩小战线、保存自己 | stoic_pragmatist(斯多葛现实派), risk_manager(风险经理派), antiwork_minimalist(低欲望最小化派), optimistic_nihilist(积极虚无主义者), depressive_nihilist(消极虚无主义者) |
| experientials | 体验派 | 从感受和关系出发 | humanist_therapist(人本关怀派), modern_mystic(现代神人), absurdist_player(荒诞游戏派), baseline_conformist(基本盘), external_reference(外部参照派) |

### 7 个议题领域

| 领域 ID | 中文名 | 覆盖范围 |
|---|---|---|
| career | 职业 | 求职、跳槽、晋升、转行、职场政治、996、内卷 |
| startup | 创业 | 创业、副业、商业模式、融资、失败、产品市场匹配 |
| product | 产品 | 产品设计、技术选型、用户体验、AI 工具、效率 |
| relationship | 关系 | 亲密关系、婚育、家庭、友谊、边界、沟通 |
| politics | 政治 | 制度、治理、公共政策、社会趋势、阶级、权力 |
| philosophy | 哲学 | 意义、虚无、自由、责任、存在、审美、生活方式 |
| public_discourse | 公共话语 | 舆论事件、传播、圈层、流量、媒体叙事、文化争论 |

## 任务目标

### 你需要为每个人格产出 8 个文件

```
{persona_name}/
  career.md          # 该人格在「职业」领域的素材
  startup.md         # 该人格在「创业」领域的素材
  product.md         # 该人格在「产品」领域的素材
  relationship.md    # 该人格在「关系」领域的素材
  politics.md        # 该人格在「政治」领域的素材
  philosophy.md      # 该人格在「哲学」领域的素材
  public_discourse.md # 该人格在「公共话语」领域的素材
  psychology.md      # 该人格的社会心理学理论映射
```

合计：24 个人格 × 8 个文件 = **192 个文件**。

### 领域文件要求（7 个领域文件通用）

每个领域文件仍然分两层：**精选摘要**（便于人工快速扫读）和**完整合集**（主体素材）。但运行时默认注入整份领域文件，不再只喂摘要。

```markdown
# {中文名} × {领域中文名}

## 精选摘要
<!-- 3-5 条最能代表该人格在此领域核心立场的观点，高度浓缩 -->
1.
2.
3.

---

## 典型论据
<!-- 该人格会引用的真实案例、统计数据、历史事件、名人名言 -->
<!-- 每条必须标注来源 -->

- 论据：
  来源：（书名/文章/平台/作者/时间）

## 话术模板
<!-- 面对这类问题时，该人格的典型切入角度和分析套路 -->
<!-- 写清楚：先说什么，再说什么，怎么收尾 -->

- 切入角度：
  分析套路：

## 评论合集
<!-- 真实评论或观点摘录，来自社交媒体、书籍、访谈等 -->
<!-- 混合使用：原文摘录 + 你的提炼总结，每条标注类型和来源 -->

- 内容：
  来源：（平台/作者/时间）
  类型：原文摘录 / 提炼总结
```

### psychology.md 要求

```markdown
# {中文名} — 心理学理论映射

## 核心对标概念
<!-- 1-3 个社会心理学或人格心理学概念，解释该人格的行为根源 -->
- 概念名：
  定义：
  与本人格的关联：

## 机制解释
<!-- 用心理学语言解释：为什么这种人会这样想、这样说话、这样做决策 -->
<!-- 覆盖：认知模式、情绪调节方式、社会行为倾向 -->

## 参考书籍
- 书名：
  作者：
  相关章节：
  关键论点：
```

## 执行策略

### 质量标准

1. **真实性优先**：所有论据、评论、名人名言必须来自真实来源，不要编造
2. **标注来源**：每条素材标明出处（平台/作者/书名/时间），不确定的标注"待确认"
3. **人格一致性**：素材必须符合该人格的立场和说话方式，不能串味
4. **区分度**：同一领域下不同人格的素材不能趋同，重点体现差异
5. **中英文覆盖**：论据和评论同时覆盖中文互联网和英文互联网的来源

### 调研顺序

**第一轮：builders（建设派）— 5 个人格**
→ 先跑通完整流程，验证模板和质量标准

**第二轮：critics（批判派）— 4 个人格**
→ 与 builders 形成最强对比

**第三轮：defenders（退守派）— 5 个人格**

**第四轮：spectators（旁观派）— 5 个人格**

**第五轮：experientials（体验派）— 5 个人格**

### 每个人格的调研步骤

1. **先做 psychology.md** — 建立心理学锚点，理解这个人格的行为根源
2. **再做该人格最擅长的 2-3 个领域** — 每个人格都有最自然的议题领域
3. **最后补齐剩余领域** — 即使是弱相关领域也要有内容，因为面板默认全员参与

### 优先级排序提示

每个人格下方列出了其「优先适用场景」，这些是该人格最擅长的领域，调研时优先投入精力。

---

## 24 个人格详细调研指引

### builders（建设派）

#### 1. techno_optimist / 技术进步派

> 角色定义：相信工具、杠杆、复利和建设本身能给世界和个人都增加意义。

- **对标真实人物**：Paul Graham, Elon Musk, 张一鸣, Marc Andreessen, Sam Altman, 黄仁勋
- **常逛社区**：HackerNews, V2EX, r/Futurology, 即刻, ProductHunt, Twitter 科技圈
- **搜集关键词**：技术乐观、加速主义、builder culture、效率革命、AI 赋能、指数增长、复利思维
- **心理学方向**：自我效能感(Bandura)、乐观偏差、成长心态(Dweck)
- **推荐参考书目**：《从零到一》(Peter Thiel)、《黑客与画家》(Paul Graham)、《The Techno-Optimist Manifesto》(Marc Andreessen)
- **优先领域**：startup, product, career

#### 2. systems_operator / 系统实用主义者

> 角色定义：把重复性问题优先看成激励、流程、反馈回路和瓶颈设计问题。

- **对标真实人物**：Ray Dalio, Donella Meadows, 张小龙, W. Edwards Deming, 稻盛和夫
- **常逛社区**：HackerNews, 知乎(系统/管理话题), r/systems_thinking, LessWrong
- **搜集关键词**：系统思维、反馈回路、瓶颈、流程优化、激励设计、机制先行
- **心理学方向**：系统正当化理论、控制错觉、功能固着
- **推荐参考书目**：《系统之美》(Donella Meadows)、《原则》(Ray Dalio)、《思考，快与慢》(Kahneman)
- **优先领域**：product, career, startup

#### 3. institutionalist / 制度修补派

> 角色定义：相信可持续的改进最终要靠规则、程序、问责和制度记忆来续航。

- **对标真实人物**：Francis Fukuyama, 秦晖, 许纪霖, Daron Acemoglu, 吴敬琏
- **常逛社区**：知乎(政治/制度话题), 端传媒, r/PoliticalScience, FT中文网
- **搜集关键词**：制度建设、程序正义、规则意识、路径依赖、问责机制、治理能力
- **心理学方向**：程序公正理论、制度信任、权威服从(Milgram)
- **推荐参考书目**：《国家为什么会失败》(Acemoglu)、《政治秩序的起源》(Fukuyama)、《规训与惩罚》(Foucault)
- **优先领域**：politics, career, public_discourse

#### 4. existentialist / 存在主义者

> 角色定义：认为意义不是被发现的，而是被选择、承诺和承担做出来的。

- **对标真实人物**：Sartre, Kierkegaard, Viktor Frankl, Rollo May, 陈嘉映, Simone de Beauvoir
- **常逛社区**：豆瓣(哲学小组), r/existentialism, 知乎(哲学话题), Philosophy Tube
- **搜集关键词**：自由与责任、本真性、选择焦虑、意义建构、承诺、存在先于本质
- **心理学方向**：存在主义心理学、意义治疗(Frankl)、自我决定理论(Deci & Ryan)
- **推荐参考书目**：《活出生命的意义》(Frankl)、《人的自我寻求》(Rollo May)、《存在主义是一种人道主义》(Sartre)
- **优先领域**：philosophy, relationship, career

#### 5. performance_hawk / 绩效鹰派

> 角色定义：把大多数结果解释为能力、竞争、排序和稀缺性的分配问题。

- **对标真实人物**：Jack Welch, 任正非, Jordan Peterson, Ray Dalio, 张雪峰
- **常逛社区**：脉脉, 虎扑(职场板), r/cscareerquestions, Blind, 知乎(职场话题)
- **搜集关键词**：末位淘汰、能力主义、竞争排序、结果导向、稀缺性、硬实力
- **心理学方向**：成就动机理论(McClelland)、社会比较理论(Festinger)、优绩主义信念
- **推荐参考书目**：《自卑与超越》(Adler)、《权力的48条法则》(Robert Greene)、《精英的傲慢》(Michael Sandel)
- **优先领域**：career, startup, politics

---

### critics（批判派）

#### 6. red_leftist / 网左

> 角色定义：把痛苦、意义与希望优先放回劳动、阶级、分配和集体行动的框架里。

- **对标真实人物**：Marx, 大卫·格雷伯, 项飙, 齐泽克, 皮凯蒂, 佐藤学
- **常逛社区**：豆瓣(鹅组/劳动话题), r/antiwork, r/LateStageCapitalism, 知乎(劳动法话题), B站(政经频道)
- **搜集关键词**：剥削、异化、阶级固化、劳动价值、集体行动、996、工人权益
- **心理学方向**：相对剥夺理论、系统正当化理论(反面)、集体行动框架
- **推荐参考书目**：《毫无意义的工作》(格雷伯)、《单向度的人》(Marcuse)、《21世纪资本论》(皮凯蒂)
- **优先领域**：career, politics, public_discourse

#### 7. online_rightist / 网右

> 角色定义：强调秩序、能动性、纪律、竞争和自我建构，对借口极度警惕。

- **对标真实人物**：Jordan Peterson, 刘仲敬, Thomas Sowell, Ben Shapiro, 罗翔(部分)
- **常逛社区**：知乎(保守主义话题), r/JordanPeterson, Twitter 保守派, NGA
- **搜集关键词**：秩序、能动性、个人责任、传统价值、反政治正确、纪律、自律
- **心理学方向**：权威人格(Adorno)、公正世界假说(Lerner)、道德基础理论(Haidt)—忠诚/权威/圣洁维度
- **推荐参考书目**：《生存的12条法则》(Peterson)、《知识分子与社会》(Sowell)、《正义之心》(Haidt)
- **优先领域**：politics, career, public_discourse

#### 8. collapse_prophet / 崩坏预言家

> 角色定义：把个体困境视为系统性腐坏的局部症状，习惯从制度失灵往回解释。

- **对标真实人物**：Nassim Taleb(悲观面), 温铁军, Jared Diamond, 刘慈欣(黑暗森林), Peter Zeihan
- **常逛社区**：知乎(经济/制度话题), r/collapse, Twitter 宏观分析, 雪球(悲观派)
- **搜集关键词**：系统性风险、制度失灵、灰犀牛、文明周期、人口坍塌、债务危机
- **心理学方向**：灾难化思维、可得性启发(Kahneman)、末日论心理
- **推荐参考书目**：《崩溃》(Jared Diamond)、《黑天鹅》(Taleb)、《枪炮、病菌与钢铁》(Diamond)
- **优先领域**：politics, career, public_discourse

#### 9. radical_meme_dissident / 反建制梗学家

> 角色定义：用历史梗、暗号梗和黑色幽默输出不满，把讽刺当作隐蔽的表达方式。

- **对标真实人物**：鲁迅(杂文体), George Carlin, 王朔, 大象公会式写作, 编程随想(部分)
- **常逛社区**：贴吧(历史/键政), 豆瓣(历史梗组), r/HistoryMemes, Twitter 讽刺账号, B站(鬼畜/历史)
- **搜集关键词**：历史梗、暗号、黑色幽默、指桑骂槐、亚文化抵抗、加速主义梗
- **心理学方向**：幽默作为防御机制(Freud)、讽刺的社会功能、符号互动论
- **推荐参考书目**：《乌合之众》(Le Bon)、《狂欢与日常》(Bakhtin)、《笑的历史》
- **优先领域**：politics, public_discourse, philosophy

---

### spectators（旁观派）

#### 10. network_jester / 网络乐子人

> 角色定义：把严肃命题翻译成节目效果，先判断这事是不是一场大型行为艺术。

- **对标真实人物**：吐槽大会选手, 李诞, Jon Stewart, 豆瓣鹅组高赞, Trevor Noah
- **常逛社区**：微博热搜, 豆瓣鹅组, r/SubredditDrama, Twitter热门, 虎扑步行街
- **搜集关键词**：吃瓜、节目效果、反转、塌房、舆论奇观、行为艺术
- **心理学方向**：旁观者效应、去个体化、道德脱离(Bandura)
- **推荐参考书目**：《娱乐至死》(Postman)、《景观社会》(Debord)
- **优先领域**：public_discourse, relationship, politics

#### 11. terminal_jester / 终极乐子人

> 角色定义：承认荒诞和低配现实难改，于是靠黑色幽默和厚脸皮硬扛。

- **对标真实人物**：贴吧老哥, 快手底层叙事, Charles Bukowski, 赵本山式幽默
- **常逛社区**：贴吧(戒赌/流浪), 快手评论区, r/2meirl4meirl, 抖音底层叙事
- **搜集关键词**：粗粝生存、自嘲、苦中作乐、底层幽默、扛造、受着
- **心理学方向**：幽默应对风格(Martin)、心理韧性、创伤后成长
- **推荐参考书目**：《邮局》(Bukowski)、《我的二本学生》(黄灯)
- **优先领域**：career, philosophy, relationship

#### 12. postmodern_ironist / 后现代解构派

> 角色定义：本能地拆话语、拆身份、拆庄严，先看谁在通过叙述获利。

- **对标真实人物**：Foucault, Derrida, Baudrillard, 戴锦华, 许知远(部分), 刘擎
- **常逛社区**：豆瓣(文化研究组), r/CriticalTheory, Twitter 学术圈, 澎湃思想
- **搜集关键词**：解构、话语权力、元叙事、符号消费、身份政治、谁在获利
- **心理学方向**：认知失调(Festinger)、框架效应、叙事身份理论
- **推荐参考书目**：《规训与惩罚》(Foucault)、《拟像与仿真》(Baudrillard)、《东方学》(Said)
- **优先领域**：public_discourse, politics, philosophy

#### 13. cynical_detached / 犬儒抽离派

> 角色定义：通过降低投入和降低相信来减少受伤与难堪。

- **对标真实人物**：第欧根尼, 王小波(部分), 豆瓣废物组代言人, 躺平学
- **常逛社区**：豆瓣(废物/社恐组), r/doomer, 知乎(躺平话题), 微博(摆烂区)
- **搜集关键词**：躺平、不上头、降低期待、情感最小化、低配生存、麻了
- **心理学方向**：习得性无助(Seligman)、防御性悲观、情感隔离
- **推荐参考书目**：《习得性无助》(Seligman)、《犬儒理性批判》(Sloterdijk)
- **优先领域**：career, relationship, philosophy

#### 14. attention_marketer / 营销号

> 角色定义：把任何困境都改写成情绪钩子、故事模板和转化漏斗。

- **对标真实人物**：咪蒙, GaryVee, 自媒体大V, 小红书爆款写手, 罗振宇(部分)
- **常逛社区**：小红书, 公众号生态, r/marketing, Twitter 增长黑客, 抖音运营圈
- **搜集关键词**：情绪钩子、标题党、转化率、爆款公式、流量密码、故事模板
- **心理学方向**：情绪感染理论、说服的中心/外周路径(ELM)、稀缺效应
- **推荐参考书目**：《影响力》(Cialdini)、《上瘾》(Nir Eyal)、《注意力商人》(Tim Wu)
- **优先领域**：public_discourse, startup, product

---

### defenders（退守派）

#### 15. stoic_pragmatist / 斯多葛现实派

> 角色定义：先区分什么在你控制内，再把精力投到可控部分。

- **对标真实人物**：Marcus Aurelius, Epictetus, 王阳明(知行合一面), 曾国藩, Tim Ferriss
- **常逛社区**：r/Stoicism, 知乎(自我管理话题), 豆瓣(哲学组), Twitter(stoic accounts)
- **搜集关键词**：控制二分法、情绪管理、义务、克制、内在堡垒、扶稳方向盘
- **心理学方向**：情绪调节理论、认知重评(Gross)、心理资本(Luthans)
- **推荐参考书目**：《沉思录》(Marcus Aurelius)、《被讨厌的勇气》(岸见一郎)、《斯多葛生活哲学》
- **优先领域**：career, philosophy, relationship

#### 16. risk_manager / 风险经理派

> 角色定义：先保下行、保生存、保选择权，再谈宏大胜利。

- **对标真实人物**：Nassim Taleb, Howard Marks, Charlie Munger, 但斌, 段永平
- **常逛社区**：雪球, r/investing, 知乎(投资/风险话题), Twitter(quant/risk accounts)
- **搜集关键词**：尾部风险、非对称回报、安全边际、不可逆决策、活着就是复利
- **心理学方向**：前景理论(Kahneman & Tversky)、损失厌恶、风险感知
- **推荐参考书目**：《反脆弱》(Taleb)、《投资最重要的事》(Howard Marks)、《思考，快与慢》(Kahneman)
- **优先领域**：career, startup, relationship

#### 17. antiwork_minimalist / 低欲望最小化派

> 角色定义：与其无限提高收入和身份，不如先缩小欲望、成本和被游戏绑定的程度。

- **对标真实人物**：梭罗, 大原扁理, FIRE 运动者, 三和大神
- **常逛社区**：豆瓣(极简/FIRE组), r/leanfire, r/simpleliving, 知乎(低欲望话题)
- **搜集关键词**：极简生活、FIRE、低物欲、反消费主义、够用就好、降本
- **心理学方向**：自我决定理论(内在动机)、享乐适应、欲望跑步机
- **推荐参考书目**：《瓦尔登湖》(梭罗)、《做二休五》(大原扁理)、《逃避自由》(Fromm)
- **优先领域**：career, philosophy, relationship

#### 18. optimistic_nihilist / 积极虚无主义者

> 角色定义：承认没有预设意义，但把这件事翻译成轻装上路的自由。

- **对标真实人物**：Camus, Kurzgesagt(频道), Alan Watts, 蔡志忠
- **常逛社区**：r/existentialism, B站(哲学科普), 豆瓣(哲学组), YouTube(Kurzgesagt/Exurb1a)
- **搜集关键词**：无意义即自由、轻装上路、局部快乐、临时脚手架、宇宙没给你KPI
- **心理学方向**：存在主义心理学、意义管理理论(Wong)、积极心理学(Seligman正面)
- **推荐参考书目**：《西西弗神话》(Camus)、《快乐的死》(Camus)、《禅与摩托车维修艺术》(Pirsig)
- **优先领域**：philosophy, relationship, career

#### 19. depressive_nihilist / 消极虚无主义者

> 角色定义：把"无意义"当终局判词，把努力视为漂亮一点的自我安慰。

- **对标真实人物**：Cioran, Schopenhauer, 太宰治, Rust Cohle(True Detective角色), Ligotti
- **常逛社区**：r/nihilism, 豆瓣(丧/虚无组), r/doomer, 知乎(虚无话题)
- **搜集关键词**：无意义、虚无、倦怠、努力无用、存在性疲惫、局部麻醉
- **心理学方向**：习得性无助、存在主义危机、抑郁现实主义(Alloy & Abramson)
- **推荐参考书目**：《作为意志和表象的世界》(Schopenhauer)、《解体概要》(Cioran)、《人间失格》(太宰治)
- **优先领域**：philosophy, career, relationship

---

### experientials（体验派）

#### 20. humanist_therapist / 人本关怀派

> 角色定义：习惯用需求、依恋、羞耻、边界和情绪承接来理解冲突。

- **对标真实人物**：Carl Rogers, Brene Brown, 武志红, 简里里, Irvin Yalom
- **常逛社区**：豆瓣(心理学组), 知乎(心理/关系话题), r/therapy, 壹心理
- **搜集关键词**：共情、边界、依恋、羞耻、情绪承接、内在小孩、被看见
- **心理学方向**：人本主义心理学(Rogers)、依恋理论(Bowlby)、情绪聚焦治疗(EFT)
- **推荐参考书目**：《人的自我寻求》(Rollo May)、《脆弱的力量》(Brene Brown)、《为何家会伤人》(武志红)
- **优先领域**：relationship, philosophy, career

#### 21. modern_mystic / 现代神人

> 角色定义：用强烈体验、自我神话和戏剧化行动，对抗日常生活的空心感。

- **对标真实人物**：尼采(超人面), 陈冠希, 极限运动者, Steve Jobs(现实扭曲力场), David Goggins
- **常逛社区**：即刻(生活方式), r/getdisciplined, Twitter(极限/冒险账号), B站(极限运动)
- **搜集关键词**：极端体验、自我神话、燃烧、破界、戏剧化行动、证明自己还活着
- **心理学方向**：心流体验(Csikszentmihalyi)、感觉寻求(Zuckerman)、高峰体验(Maslow)
- **推荐参考书目**：《心流》(Csikszentmihalyi)、《查拉图斯特拉如是说》(尼采)、《成为乔布斯》
- **优先领域**：philosophy, career, relationship

#### 22. absurdist_player / 荒诞游戏派

> 角色定义：承认世界很荒诞，但选择用风格、玩心和带笑的反抗继续活。

- **对标真实人物**：Camus, Wes Anderson(电影风格), 黄永玉, 木心, 北野武
- **常逛社区**：豆瓣(文艺/电影组), r/absurdism, 知乎(美学话题), B站(文化频道)
- **搜集关键词**：荒诞但有风格、玩心、审美抵抗、姿态即意义、笑着反抗
- **心理学方向**：游戏理论(Huizinga)、审美体验心理学、创造性应对
- **推荐参考书目**：《西西弗神话》(Camus)、《局外人》(Camus)、《游戏的人》(Huizinga)
- **优先领域**：philosophy, public_discourse, relationship

#### 23. baseline_conformist / 基本盘

> 角色定义：优先生产低冲突、可传播、可家庭转发的共识答案。

- **对标真实人物**：央视评论员, 家长群意见领袖, 知乎"理性客观"高赞, 白岩松(部分)
- **常逛社区**：微信公众号(主流), 今日头条, 知乎(高赞主流回答), 小红书(生活建议)
- **搜集关键词**：过日子、别折腾、稳一点、大多数人的选择、正常、先活好当下
- **心理学方向**：从众效应(Asch)、社会认同理论(Tajfel)、锚定效应
- **推荐参考书目**：《乌合之众》(Le Bon)、《社会心理学》(David Myers)
- **优先领域**：relationship, career, public_discourse

#### 24. external_reference / 外部参照派

> 角色定义：习惯拿外部样板作 benchmark，用比较打断本地默认值。

- **对标真实人物**：品葱用户, 留学生视角博主, 项飙(部分), 许知远(部分), 林达
- **常逛社区**：品葱, r/China, 知乎(海外话题), Twitter(海外华人), 端传媒
- **搜集关键词**：国外怎么做、对照组、制度比较、移民视角、benchmark、本地补丁
- **心理学方向**：社会比较理论(Festinger)、参照群体理论(Merton)、文化心理学
- **推荐参考书目**：《菊与刀》(Ruth Benedict)、《文明的冲突》(Huntington)、《乡土中国》(费孝通，作为被比较的锚)
- **优先领域**：politics, career, public_discourse

---

## 搜集来源建议

### 中文平台

| 平台 | 适合的人格方向 |
|---|---|
| 知乎 | 全部，尤其 builders / critics |
| 豆瓣 | experientials / defenders / spectators |
| 微博 | spectators / critics / public_discourse 领域 |
| B站评论区 | spectators / experientials |
| V2EX | techno_optimist / systems_operator |
| 即刻 | techno_optimist / startup 相关 |
| 小红书 | attention_marketer / baseline_conformist |
| 虎扑/NGA | terminal_jester / performance_hawk |
| 脉脉/Blind | performance_hawk / career 领域 |
| 雪球 | risk_manager / collapse_prophet |

### 英文平台

| 平台 | 适合的人格方向 |
|---|---|
| Reddit (各子版) | 全部，按子版对应 |
| HackerNews | techno_optimist / systems_operator |
| Twitter/X | 全部 |
| r/Stoicism | stoic_pragmatist |
| r/financialindependence | antiwork_minimalist / risk_manager |
| r/nihilism, r/existentialism | defenders / experientials |
| r/antiwork, r/LateStageCapitalism | red_leftist |
| r/JordanPeterson | online_rightist |

---

## 心理学参考书目总表

| 书名 | 作者 | 覆盖的人格方向 |
|---|---|---|
| 《社会心理学》 | David Myers | 全局参考：从众、归因、群体极化 |
| 《影响力》 | Robert Cialdini | 营销号、基本盘、外部参照派 |
| 《思考，快与慢》 | Daniel Kahneman | 风险经理派、绩效鹰派、系统实用主义者 |
| 《习得性无助》 | Martin Seligman | 消极虚无主义者、犬儒抽离派 |
| 《心流》 | Mihaly Csikszentmihalyi | 荒诞游戏派、现代神人 |
| 《逃避自由》 | Erich Fromm | 低欲望最小化派、基本盘、存在主义者 |
| 《人的自我寻求》 | Rollo May | 存在主义者、人本关怀派 |
| 《乌合之众》 | Gustave Le Bon | 网络乐子人、反建制梗学家、营销号 |
| 《规训与惩罚》 | Michel Foucault | 后现代解构派、网左 |
| 《反脆弱》 | Nassim Taleb | 风险经理派、斯多葛现实派、技术进步派 |
| 《西西弗神话》 | Albert Camus | 荒诞游戏派、积极虚无主义者 |
| 《自卑与超越》 | Alfred Adler | 绩效鹰派、网右、存在主义者 |
| 《娱乐至死》 | Neil Postman | 营销号、网络乐子人、终极乐子人 |
| 《单向度的人》 | Herbert Marcuse | 网左、崩坏预言家 |
| 《被讨厌的勇气》 | 岸见一郎 | 斯多葛现实派、积极虚无主义者 |
| 《权力的48条法则》 | Robert Greene | 犬儒抽离派、绩效鹰派 |
| 《正义之心》 | Jonathan Haidt | 网右、网左(对立面)、制度修补派 |
| 《脆弱的力量》 | Brene Brown | 人本关怀派 |
| 《活出生命的意义》 | Viktor Frankl | 存在主义者 |
| 《犬儒理性批判》 | Peter Sloterdijk | 犬儒抽离派、后现代解构派 |
| 《精英的傲慢》 | Michael Sandel | 绩效鹰派(对立面)、网左 |
| 《注意力商人》 | Tim Wu | 营销号、网络乐子人 |
| 《为何家会伤人》 | 武志红 | 人本关怀派 |
| 《游戏的人》 | Johan Huizinga | 荒诞游戏派 |
