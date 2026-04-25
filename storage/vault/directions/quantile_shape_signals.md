---
direction_tag: quantile_shape_signals
status: dead
priority: low
rounds: 1
admits: 0
last_batch: batch_044
last_admits: []
last_goal: 首批探 Quantile/Median 算子在非 return 字段 (range/turnover/amount) 上的 shape 信号是否独立于
  vol_20d 和 F001/F012。覆盖：range Q90-Q50 (top-skew)、turnover Median/Mean 比、amount IQR、range
  Q75-Q25、median of range、Q-range 短/长比。目标 mono_is ≥ 0.5 避免 range_structure C004 的
  IS-weak 悖论。
last_activity: '2026-04-24T02:48:36Z'
created_batch: batch_044
members: []
merged_into: null
---
# quantile_shape_signals

> [!abstract]+ 方向概要
> - **状态**　🔴 `dead` · priority `low` · rounds = 1 · admits = 0
> - **最近**　batch_044 首批即 DISPROVEN · 6 候选 0 admit / 5 reserve / 1 reject
> - **一句话**　Quantile/Median 算子在 range/turnover/amount 上的 shape 信号被 vol_20d 全面吸收——robust-to-outliers ≠ Barra orthogonality

---

## Hypothesis ⚠️ DISPROVEN

> [!warning]+ 方向已证伪（[[lessons|lessons.md]] F001 / F301 升格证据点）
> Quantile 算子的 robust-to-outliers 属性**不等于** Barra `vol_20d` orthogonality——两个概念在本方向 hypothesis 设计中被混淆。**第 4 次跨方向独立确认 vol_20d 对 2nd-moment 的结构吸收**（+stochastic_position / vwap_proxy / range_structure）。任何 magnitude / ratio / power-mean / **quantile** transformation——无论作用于 return / range / amount / turnover——最终都坍缩为 vol_20d 的 monotone derivative。

经过三方向（[[stochastic_position]] / [[vwap_proxy_signals]] / [[range_structure]]）连续 3 批 0 admit 跨方向确认：**csi1000 的 cross-section 几何被 vol_20d 的 2nd-moment 空间主导**，任何 magnitude / ratio / power-mean transformation 都被吸收；只有 **shape（高阶矩 / 分布百分位）+ 非 return 字段** 两条路径可能逃离。

**关键技术观察**：
- [[return_distribution_signals]] dead: Skew/Kurt on returns 失败（|return| ≡ vol rank）
- [[range_structure]] C004 Skew(range, 60) mono_oos=+1.0 完美但 mono_is=0.30 弱——shape 方向有希望但需更稳健 estimator
- **百分位差（Quantile-based）比矩（Skew/Kurt）更鲁棒**：矩受极值主导（与 vol_20d 共线），百分位差对尾部免疫

本方向 hypothesis：**Quantile(field, N, p) 或 Quantile 差分**在 **range / turnover / amount** 三个非-return 字段上，可能产生独立于 vol_20d 的 cross-section 信号。

经济直觉：
- `Quantile((H-L)/C, 60, 0.9) - Quantile((H-L)/C, 60, 0.5)`：高 range 日的典型大小（上尾）vs 中位数——大时表示事件驱动 universe（少数大 range 日拖起 90 分位）；小时表示均匀分布
- `Median($turnover_rate, 20) / Mean($turnover_rate, 20)`：中位数 vs 均值比例——>1 指近期 turnover 分布左偏，<1 指右偏（由高 turnover 少数日驱动）
- `Quantile($amount, 60, 0.75) - Quantile($amount, 60, 0.25)`：amount 的 IQR 范围

相比 return_distribution_signals 的 Skew(return)，quantile 差有三个技术优势：(1) robust to outliers (不被极值主导)，(2) interpretable (直接可读的百分位位置)，(3) 数学上不是 power-mean family（更可能逃离 vol 主轴）

**关键风险**（事后已证实命中）：
- Quantile(field, 60, 0.9) 在 csi1000 小盘 universe 下 60d = 3 months 可能被 Barra `vol_20d` 的 **3 个月 rolling** 部分共线——**实测 vol_20d exposure 27–45，全部命中**
- turnover/amount IQR 已被 F001 amount CV 和 F012 amihud 部分覆盖——**C003 max_corr=0.80@F012 命中**

---

## Threads

### T001: Quantile-based shape 信号是否在 range/turnover/amount 上独立 [✗ DISPROVEN batch_044]

> [!failure]+ Thread 结论
> **Question**: Quantile(field, N, p) 差分或比值在非-return 字段上是否产生独立于 vol_20d 和现有流动性簇 (F001/F012) 的 forward IC？
>
> **Answer**: 否，全面证伪。3 个字段上的 Quantile shape 路径全部撞墙：
> - **range 字段**（C001 Q90-Q50 / C004 Q75-Q25 / C005 Median / C006 短长比）：4/4 dom_style=vol_20d (exposure 27–42) + incremental_ic 全负 (-0.020 到 -0.037)
> - **amount 字段**（C003 IQR）：max_corr=0.80@F012 坠入液性簇 + alpha_surv=0.07
> - **turnover 字段**（C002 Med/Mean）：IC 活 ICIR=+0.41 但 ls_t=+0.25 鸿沟，mono_oos U-shape (1.0→0.1)
>
> **Evidence trail**:
> - [[batches/batch_044/candidates/C001|C001]] Q90-Q50 range — vol_20d exp=45 + incr=-0.036 → **reserve**
> - [[batches/batch_044/candidates/C002|C002]] turnover Med/Mean — ICIR=+0.41 但 ls_t=+0.25 + mono_oos U-shape → **reserve**
> - [[batches/batch_044/candidates/C003|C003]] amount IQR — max_corr=0.80@F012 + alpha_surv=0.07 → **reject**
> - [[batches/batch_044/candidates/C004|C004]] range Q75-Q25 — mono IS=OOS=-1.0 完美但 vol_20d exp=42 + incr=-0.037 → **reserve**
> - [[batches/batch_044/candidates/C005|C005]] range Median 60d — vol_20d exp=38 + incr=-0.038 → **reserve**
> - [[batches/batch_044/candidates/C006|C006]] range Median 5d/60d 比 — mono_is -0.3→mono_oos -0.1 崩塌 + incr=-0.020 → **reserve**

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_044/candidates/C003\|C003]] | `Sub(Quantile($amount, 60, 0.75), Quantile($amount, 60, 0.25))` | max_corr=0.80@F012 near-dup + alpha_surv=0.07 + incr_ic=-0.044 |

---

## Related

- 📖 [[lessons]] F001 / F301 — vol_20d 吸收律（本方向是第 4 次独立确认证据点）
- 🔴 [[return_distribution_signals]] `dead` — Skew/Kurt on daily-return 全部坍缩到 vol_20d
- 🔴 [[vol_shock_signals]] `dead` — magnitude shock 同律坍缩
- 🟡 [[stochastic_position]] `saturated` — %K / TsRank 同源（vol_20d exp 8.7–16.5）
- 🔵 [[range_structure]] `exploring` — 已收窄至 Kurt-only + 非 vol RHS rank-diff
- 🟡 [[amount_volatility_signal]] `saturated` — F001 amount CV 占据 amount 离散度空间
- 🟡 [[microstructure_illiquidity]] `saturated` — F012 amihud 占据量价冲击空间

---

## Narrative Log

> [!quote]+ 2026-04-24 · [[batches/batch_044/judge|batch_044]]
> **首批即方向 DISPROVEN · Quantile ≠ orthogonalize** · admit=0 / reserve=5 / reject=1
>
> - T001 hypothesis 在 3 字段上全部证伪（range/amount/turnover）——Quantile 差分/Median/短长比都被 vol_20d 吸收
> - 6 候选 incremental_ic 全负（仅 C002=+0.006 borderline 正），方向 ROI = 0
> - 阈值校准 diagnosis：5 reserve 中无真错杀（4 个 incr_ic 负 + 1 个 mono_oos 不成立）
> - **第 4 次跨方向独立确认** vol_20d 主导律：stochastic_position + vwap_proxy_signals + range_structure + quantile_shape_signals
> - MT budget cumulative 222 → **228** · direction 0 → **6** · bucket `medium`
>
> **Operations**　`status: exploring → dead`（hypothesis 根本证伪非回头路）· `priority: medium → low`
> **后续 distillation**　[[lessons]] F001（pattern_analyst）+ F301（hypothesis_promoter）已将本方向作为 5+ 次跨方向证据之一升格"vol_20d 吸收律"为 Structural Constraints 顶级条目
