# Consolidation Packet — directions/turnover_structural_signal.md

## Current content

---
direction_tag: turnover_structural_signal
status: saturated
priority: low
rounds: 1
admits: 0
last_batch: batch_004
last_admits: []
last_goal: 'Open new direction turnover_structural_signal to escape amount_volatility_signal''s
  vol_20d ceiling. Test 5 orthogonal turnover-rate二阶结构 families: persistence (AutoCorr),
  acceleration (short/long ratio), CV (structural analog of F001), signed turnover
  mean (avoiding Qlib Corr+Delta broadcast issue), CS-rank stability. Goal: at least
  1 candidate with max_corr<0.3@F001 + alpha_survival>0.7 + dominant_style≠vol_20d.'
last_activity: '2026-04-19T05:28:19Z'
created_batch: batch_004
members: []
merged_into: null
---
# turnover_structural_signal

> [!abstract]+ 方向概要
> - **状态**　🟡 `saturated` · priority `low` · rounds = 1 · admits = 0
> - **最近**　[[batches/batch_004/judge|batch_004]] · 2026-04-19 · admit=0 / reserve=1 / reject=4
> - **一句话**　⚠️ 换手率二阶结构首批即证伪，5/5 候选撞 vol_20d 风格天花板——"换 field ≠ 换维度"。

---

## Hypothesis

> [!failure]+ ⚠️ 证伪后 Hypothesis（batch_004 · 4/5 失败 → 改写）
> **原假设**：`$turnover_rate` 自带规模归一化，其二阶结构（持久性 / 加速度 / 方向耦合 / 排名稳定性）可落在 `amount_volatility_signal` 之外的 Barra 风格空间（turnover_20d / str_1m / 残差）。
>
> **证伪结论**：Barra basis（vol_20d / turnover_20d / str_1m）在日频 DSL 层**同时覆盖** `$amount` 与 `$turnover_rate` 派生量——"换 field 逃出 vol_20d 天花板"在 Barra 分解下不成立。5/5 候选 `dominant_style=vol_20d`，IC 被吞 40%–55%。
>
> **仅存一线**（T002）：加速度比值 `Div(Mean(tr,5), Mean(tr,20))` 是唯一突破 alpha_survival dealbreaker 的构造（残差 IC 反增强 = 1.085），提示"变化率"维度可能独立于"水平 + 波动率"维度——但 Q5 一桨驱动 + cum_ic_mdd=-73.7 削弱实盘价值，只能 reserve。
>
> **复活条件**
> 1. **Python 逃生口**：对 turnover 派生量做 vol_20d Barra residual 回归后取残差（见 [[barra_residual_alpha]]）
> 2. **换频率 / 换字段**：intraday / tick-level turnover 微结构（日频 DSL 无法表达）
> 3. 在现有日频 OHLCV + turnover 字段上再试任何 DSL 组合已**无 ROI**。

---

## Threads

### T002: Turnover 加速度 / 水平分离 [◉ ACTIVE · SOLE SURVIVOR]

> [!note]+ Thread 当前
> **Question**: 短/长窗口换手比值（兴趣度加速度）能否独立于水平值 `Mean(turnover, 20)` 产生 alpha？加速增长是追涨还是反转信号？
>
> **Evidence trail**:
> - [[batches/batch_004/candidates/C003|batch_004 C003]]　`Div(Mean(tr,5), Mean(tr,20))` → ICIR_OOS=-0.320 · ls_t=-3.08 · **alpha_survival=1.085**（残差 IC 反增强）· max_corr=0.27@F001 · mono_oos=-0.5 · cum_ic_mdd=-73.7 → **reserve**
>
> **Partial Answer**: 方向内唯一突破 alpha_survival dealbreaker 的构造。"变化率"维度似乎独立于"水平 + 波动率"维度。但 Q5 一桨驱动 + 深期回撤削弱实盘价值。
>
> **Next probes**: Python 逃生口做 C003 的 vol_20d Barra residual；或改 window 组合 (3/10, 10/60) 看加速度结构的尺度稳定性。

### T001: Turnover 持久性（AutoCorr）[✗ DISPROVEN batch_004]

> [!failure]+ Thread 结论
> **Question**: 换手率的序列相关（AutoCorr）是否在横截面上携带独立 alpha？
>
> **Evidence trail**:
> - [[batches/batch_004/candidates/C002|C002]]　`TsAutoCorr($turnover_rate, 20)` → ICIR_OOS=-0.280 · ls_t=-2.43 · max_corr=0.13@F001 · alpha_survival=0.520 · vol_20d=25.8 → **reject**
>
> **Conclusion**: AutoCorr 数值上独立于 F001，但 Barra 分解后 48% IC 被 vol_20d 吞——持久性维度不独立于波动率维度。

### T003+T005: Turnover 结构稳定性（CV / Rank-Std 同类合并）[✗ DISPROVEN batch_004]

> [!failure]+ Thread 结论
> **Question**: 两种"结构稳定性"构造——CV（Std/Mean）与 CsRank 时序 Std——能否借"换手率自带规模归一"脱离 F001 与 vol_20d？
>
> **Evidence trail**:
> - [[batches/batch_004/candidates/C001|C001]]　`Div(Std(tr,10), Mean(tr,10))` → **corr=0.955@F001** → reject `hard_gate near_dup`
> - [[batches/batch_004/candidates/C005|C005]]　`Std(CsRank(tr), 20)` → ICIR_OOS=-0.238 · ls_t=**-0.64** · decay=0.46 · vol_20d=**41.4**（方向最高） → reject `soft_CP + unstable`
>
> **Conclusion**: A 股 10d 窗口下 turnover CV ≡ amount CV（shares 短窗近常数，相除抵消 price 波动维度）；CsRank 嵌套 Std 反而产出方向最高 vol_20d 暴露（讽刺反向）。**规模归一优势在"相除 / 排名"结构下被抹掉**。

### T004: Turnover-return 方向耦合 [✗ DISPROVEN batch_004]

> [!failure]+ Thread 结论
> **Question**: `Mean(Sign(Δclose) × tr, 20)` 能否用 turnover 对称分布规避 amount 版（C006_b1 mono_flip）的 regime-dependent 分位翻号？
>
> **Evidence trail**:
> - [[batches/batch_004/candidates/C004|C004]]　`Mean(Mul(Sign(Delta($close,1)), $turnover_rate), 20)` → ICIR_OOS=-0.296 · ls_t=-2.98 · max_corr=0.12@F001 · **alpha_survival=0.446** · style_r²=0.421 · dom=vol_20d+str_1m+turnover_20d → **reject**
>
> **Conclusion**: turnover 对称分布修复了 mono_flip ✓，但引入 vol_20d+str_1m+turnover_20d 三簇共线，风格暴露 55%。**"规避 amount 陷阱 ✓ / 规避 Barra 吞噬 ✗"**。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_004/candidates/C001\|C001]] | `Div(Std($turnover_rate,10), Mean($turnover_rate,10))` | `hard_gate` near_dup 0.955@F001 |
| [[batches/batch_004/candidates/C002\|C002]] | `TsAutoCorr($turnover_rate, 20)` | `soft_CP` alpha_survival=0.52（vol_20d 吞 48% IC） |
| [[batches/batch_004/candidates/C004\|C004]] | `Mean(Mul(Sign(Delta($close,1)), $turnover_rate), 20)` | `soft_CP` alpha_survival=0.446（三簇共线吞 55%） |
| [[batches/batch_004/candidates/C005\|C005]] | `Std(CsRank($turnover_rate), 20)` | `soft_CP + unstable` vol_20d=41.4 + decay=0.46 + ls_t=-0.64 |

---

## 升格经验（direction-level lessons）

1. **"换 field"不等于"换维度"**：Barra basis（vol_20d / turnover_20d / str_1m）在日频 DSL 层覆盖了所有流动性-波动率派生量，`$amount` 与 `$turnover_rate` 在风格空间上高度共线——脱此天花板必走 **Python residual 逃生口** 或 **新频率 / 新字段**。
2. **规模归一优势易在二阶算子下抹掉**：turnover CV ≡ amount CV（10d 窗口相除抵消）；CsRank 嵌套 Std 反而最大化 vol_20d 暴露。
3. **首批 alpha_survival < 0.60 率 > 50% → 立即触发"方向底层 hypothesis 检讨"**，不要继续在同 basis 内换表达式。
4. **"变化率"维度是仅存希望**：T002 加速度比值 alpha_survival=1.085 是唯一突破点——提示比值 / 差分 / 残差类构造可能独立于"水平 + 波动率"维度。

---

## Related

- 🟡 [[amount_volatility_signal]] `saturated` — 方向级 vol_20d 天花板教训的上游；本方向"换 field 逃出"失败，证实 Barra basis 吞噬是跨 field 现象
- 🟡 [[value_liquidity_interaction]] `saturated` — 同批开辟的替代路径（基本面 × 流动性交互）
- 🟡 [[barra_residual_alpha]] `saturated` — 本方向"复活条件"指向的 Python residual 逃生口

---

## Narrative Log

> [!quote]+ 2026-04-19 · [[batches/batch_004/judge|batch_004]] · 方向首批即 saturated
> admit=0 / reserve=1 (C003 加速度) / reject=4。5/5 候选 `dominant_style=vol_20d`，核心前提"换手率能脱离 vol_20d 风格空间"被 Barra 分解证伪。
> - T001 持久性 → DISPROVEN（AutoCorr 吞 48% IC）
> - T002 加速度 → ACTIVE（SOLE SURVIVOR，alpha_survival=1.085，Q5 一桨 → reserve）
> - T003 CV → DISPROVEN（10d 窗口下 ≡ F001，合并入 T003+T005）
> - T004 方向耦合 → DISPROVEN（三簇共线吞 55%）
> - T005 rank 稳定性 → DISPROVEN（vol_20d=41.4 讽刺反向 + ls_t=-0.64 塌方；合并入 T003+T005）
> - **MT budget**　cumulative X→X+5 · direction 0→5 · bucket `turnover_structural`
>
> **Operations**　`status: exploring → saturated` · priority `high → low` · 下轮暂停本方向，batch_005 开辟 `value_liquidity_interaction`


## Instructions

Rewrite this direction md to compress long narrative logs, dedupe threads, and preserve Hypothesis + active Threads + Narrative Log (truncated to most recent 20 entries). Do not touch the frontmatter — Python manages that.
