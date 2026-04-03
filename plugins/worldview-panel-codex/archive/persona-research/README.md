# Worldview Panel 人格素材研究包（v2.0）

## 这包里有什么
- 24 个人格 × 9 个 persona-level 文件 = **216 个 persona 文件**
  - 原有 8 个：7 个领域文件 + 1 个 `psychology.md`
  - 新增 1 个：`profile_2_0.md`
- 额外附带：
  - `persona_profile_second_pass.md` + `.csv` + `.json`
  - `persona_overview.csv` + `.json`（已合并 second-pass 字段）
  - `src_personas_patch_v2.json`
  - `runtime_domain_hooks_v2.csv` + `.json`
  - `persona_differentiation_guide.md`
  - `global_bibliography.md`
  - `sources/web_verified_sources_v2.md`
  - 原始任务书 `persona-research-guide.md`

## 这轮升级的重点
上一版的主要问题不是“没东西”，而是**人物味不够硬、相邻人格容易串味、工程回填不顺手**。
所以 2.0 的主攻方向不是继续堆模板字数，而是：
1. 把 second-pass 里的 archetypes / thinking_habits / emotional_triggers / rhetorical_weapons 变成结构化资产；
2. 为每个人格补一张 `profile_2_0.md` 人格增强卡；
3. 把 2.0 补丁注入全部 192 个旧文件，让任何单文件命中时都能带出更明显的人设；
4. 补一份 `src_personas_patch_v2.json` 与 `runtime_domain_hooks_v2.*`，方便直接接工程。

## 推荐使用方式
1. **做人设 grounding**：先读 `profile_2_0.md`
2. **做人格底盘**：再读 `psychology.md`
3. **做具体回答**：最后读对应领域文件
4. **防串味**：高风险场景先看 `persona_differentiation_guide.md`
5. **接代码**：若要回填 `personas.json`，先看 `src_personas_patch_v2.json`

## 版本边界
- 2.0 不是“168 个领域文件已经全部补到逐条精确 URL”的终稿。
- 2.0 的提升重点是**区分度、可回填性、可检索性**。
- 想继续往 3.0 走，最值钱的动作不是再写漂亮话，而是给 A / A- 文件补真链接、真摘录、真案例。

## 最先该抽查哪里
- builders：`techno_optimist/profile_2_0.md`、`systems_operator/product.md`
- critics：`red_leftist/public_discourse.md`、`collapse_prophet/politics.md`
- defenders：`stoic_pragmatist/psychology.md`、`antiwork_minimalist/philosophy.md`
- spectators：`attention_marketer/startup.md`、`postmodern_ironist/public_discourse.md`
- experientials：`humanist_therapist/relationship.md`、`absurdist_player/philosophy.md`
