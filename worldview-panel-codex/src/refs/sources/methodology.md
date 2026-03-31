# Source methodology（v2.0）

## 本包这轮到底做了什么
1. 以上一版 24 人格 × 8 文件骨架为底板，保留全部 192 个原文件。
2. 把《Persona Profile Second Pass》里新增的 archetypes / communities / reading_list / thinking_habits / emotional_triggers / rhetorical_weapons 结构化抽出。
3. 为每个人格新增 `profile_2_0.md`，并把 2.0 补丁注入到全部 `psychology.md` 和 7 个领域文件里。
4. 额外产出 `src_personas_patch_v2.json` 与 `runtime_domain_hooks_v2.json/csv`，方便直接回填工程侧配置，而不是继续手工抄。
5. 追加一份 `persona_differentiation_guide.md`，专门压制相邻人格串味。
6. 额外核对并整理一批官方/原始页面到 `sources/web_verified_sources_v2.md`。

## 信心等级
- A：`profile_2_0.md`、`psychology.md`、以及 machine-readable 的 JSON/CSV patch。
- A-：priority domains。相比上一版，人物味、雷点和修辞武器更明确。
- B+：非 priority domains。仍然不是最终补链稿，但已经不再只是空泛模板话。

## 已知限制
- 这仍然不是“每条评论都带精确帖子 URL”的终稿；那种口头吹满格只会骗自己。
- 第二轮最核心的提升是“区分度”和“工程可回填性”，不是把 168 个领域文件全部重写成手工专栏。
- 评论合集里大量条目仍是提炼总结；若你后续要对外发布，建议再补原文短摘录。

## 下一轮最值得补的内容
1. 给 A / A- 文件补精确 URL，尤其 priority domains。
2. 给每个 persona 至少补 1 条中文原文短摘录 + 1 条英文原文短摘录。
3. 对 politics / public_discourse 追加更细的现实案例库。
4. 拿真实用户问题做 panel smoke test，专查串味与空话复发。
