---
name: consolidate-library-gap
description: Phase 5 Distillation Specialist — 扫 admitted factors + recent reject patterns 找结构性缺口（未被探索的 signal family），产出 findings/library_gap/{NNN}.md
user_invocable: false
---

# /consolidate-library-gap — 库空间缺口分析（subagent）

**本 skill 在 subagent 独立 context 中跑**，Phase 5 4 specialist 之一。职责：不是找"什么失败"，而是找**库里结构上没有的东西**——哪些 signal family 还没被尝试 / 尝试不足 / 被误以为饱和其实未饱和。

## 输入

Read `storage/vault/_consolidation/packet_specialist_library_gap.md` 全文——含：
- Task 描述
- Admitted factors 表（F{id} / name / expression）
- 最近 N 批 judge.md 全文

## 输出

写到本 specialist 自己的子文件夹：`storage/vault/_consolidation/findings/library_gap/{NNN}.md`，**一个 finding 一个文件**。

- `NNN` 从 `001` 开始，3 位 zero-padded，已有则接续
- 子文件夹 = 命名空间，避免和其他 specialist 撞号
- 路径如不存在请创建（mkdir -p）

```markdown
---
finding_id: 001
specialist: library_gap
severity: medium
affected_directions: []                    # gap 类 finding 通常不直接"影响"现有方向
touches_lessons: false                      # 除非发现需要升格的搜索策略
batches_referenced: [batch_030, ..., batch_044]
suggested_new_direction: "orthogonal_residual_signals"   # 若建议新方向
---

# library_gap/001 · 所有 admitted 都是 single-window，没有 multi-horizon blend

## Observation

现有 14 个 admitted F{id} 全部基于单一窗口（20d / 60d / 120d 之一）。
没有任何 admit 来自"短期 × 长期"的 blend。但 T003 of batch_008 曾 reserve
一个 ratio-of-sharpes-across-horizons 候选，incr_ic=+0.018。

## 建议探索

...
```

`finding_id` 字段填**纯数字**（如 `001`）；specialist 命名空间靠路径 + frontmatter `specialist` 字段表达。Wikilink 用 `[[_consolidation/findings/library_gap/001]]`。

## 识别启发

- **算子族空白**：admitted 全部都用 `Std / Corr / Mean`；从未用过 `Slope / Resi / Skew / CsRank`
- **字段族空白**：admitted 全部基于 OHLCV；`$pe_ratio / $ps_ratio / $pb_ratio` 相关方向少
- **时间尺度空白**：admitted 全部 single-window；缺 multi-horizon blend
- **条件算子空白**：admitted 几乎没有 `IfElse / Mask / Gt` 条件结构
- **复合算子空白**：admitted 绝大多数 depth ≤ 3；深嵌套组合未探索
- **Reserve 积压**：连续 N 批 reserve 累计且共享某特征 → 该特征可能被系统性低估

## severity 判据

- `high`：严重结构缺口 + 有 reserve 证据支持
- `medium`：有结构观察但缺 reserve 证据
- `low`：推测性缺口

## 返回给 orchestrator

≤10 行：

```
# library_gap summary
findings_written: 2
- F004 medium: single-window dominance, multi-horizon 未探索
- F005 low: 条件算子空白 (IfElse/Mask/Gt)
new_directions_proposed: [orthogonal_residual_signals]
```

## 纪律

- **`affected_directions` 可为空**（gap 不一定绑定现有方向）
- **`suggested_new_direction`** 可选字段——若提出新方向 tag
- **不重复 pattern_analyst**：不 re-report 失败律；只 report 缺口
- 宁可报少也不 over-propose 新方向（新方向成本高）
