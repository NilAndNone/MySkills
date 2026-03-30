# 人格输出丰富化设计

## 目标

让 24 个人格的观点输出更贴合角色、更有细节，同时为每个人格建立可调研填充的参考素材体系。

## 决策记录

| 决策项 | 结论 |
|---|---|
| persona_content 深化 | 新增 `profile` 对象嵌入 JSON |
| 独立参考文件组织 | 矩阵式，按人格分目录 |
| 领域列表 | career / startup / product / relationship / politics / philosophy / public_discourse（7 个） |
| 参考文件内容来源 | 用户调研搜集，混合原文+提炼，标注来源 |
| 参考文件体量 | 不设上限 |
| task packet 注入策略 | 两层结构：文件顶部精选摘要（必读）+ 下方完整合集（按需） |
| 心理学理论 | 每个人格目录下独立 `psychology.md` |
| 人物对标 | 真实人物（archetypes / reading_list） |
| 社区覆盖 | 中英文全覆盖 |
| emotional_triggers | 泛化类型 |

## 一、persona_content 深化（嵌入 personas.json）

在现有 JSON 结构基础上，每个人格增加 `profile` 对象：

```json
{
  "name": "techno_optimist",
  "description": "...",
  "group": "builders",
  "chinese_name": "技术进步派",
  "persona_content": "...现有内容保留不动...",
  "profile": {
    "archetypes": ["Paul Graham", "Elon Musk", "张一鸣"],
    "communities": ["HackerNews", "V2EX", "r/Futurology", "即刻"],
    "reading_list": ["《从零到一》Peter Thiel", "《黑客与画家》Paul Graham"],
    "thinking_habits": ["先问'这个能不能工程化'", "用复利思维评估长期价值"],
    "emotional_triggers": ["有人说技术不能解决社会问题", "反科学叙事"],
    "rhetorical_weapons": ["技术类比", "指数增长论证", "历史进步举例"]
  }
}
```

## 二、独立参考文件（矩阵式）

### 目录结构

```
src/refs/{persona}/
  career.md
  startup.md
  product.md
  relationship.md
  politics.md
  philosophy.md
  public_discourse.md
  psychology.md
```

8 个文件 x 24 个人格 = 192 个文件。

### 领域文件模板（career.md 等 7 个）

```markdown
# {chinese_name} x {domain_chinese}

## 精选摘要
<!-- 主线程必读区，3-5 条最能代表该人格在此领域立场的核心观点 -->

---

## 典型论据
<!-- 常引用的案例、数据、事件、名言，标注来源 -->

## 话术模板
<!-- 面对这类问题时的典型切入角度和分析套路 -->

## 评论合集
<!-- 调研搜集的真实评论/观点摘录，标注来源 -->
```

### psychology.md 模板

```markdown
# {chinese_name} — 心理学理论映射

## 核心对标概念
<!-- 1-3 个社会心理学 / 人格心理学概念 -->

## 机制解释
<!-- 这个人格的行为模式如何用心理学机制解释 -->

## 参考书籍
<!-- 对应的心理学著作 -->
```

## 三、SKILL.md 改动

workflow 步骤 2（准备 task packet）增加：

- 根据问题识别出的 domain，读取 `src/refs/{persona}/{domain}.md` 的「精选摘要」部分
- 放进任务包的 `[已知材料]` 字段
- 如果精选摘要不足以覆盖问题细节，可追加读取完整合集中的相关条目

## 四、文件数量统计

| 类别 | 数量 |
|---|---|
| personas.json 改动 | 1 个文件，24 个人格增加 profile |
| 领域参考文件 | 24 x 7 = 168 个 |
| 心理学文件 | 24 个 |
| SKILL.md 改动 | 1 个文件 |
| **合计** | 192 个新文件 + 2 个改动文件 |
