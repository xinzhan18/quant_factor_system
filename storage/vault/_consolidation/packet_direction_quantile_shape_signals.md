# Consolidation Packet — directions/quantile_shape_signals.md

## Current content

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
> - **状态**　🔵 `exploring` · priority `medium` · rounds = 0 · admits = 0
> - **最近**　未启动 · 首批 batch_044 探 quantile-based shape 信号（非 return、非 power-mean）
> - **一句话**　用 Quantile/Median 算子在非 return 字段（range / turnover / amount）上测 **rank-robust 分布形状**，逃离 vol_20d 的 2nd-moment 吸收

---

## Hypothesis

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

**关键风险**：
- Quantile(field, 60, 0.9) 在 csi1000 小盘 universe 下 60d = 3 months 可能被 Barra `vol_20d` 的 **3 个月 rolling** 部分共线——检查 corr 预警
- turnover/amount IQR 已被 F001 amount CV 和 F012 amihud 部分覆盖——max_corr 关注

---

## Current Focus

- 首批 6 候选覆盖：range Q90-Q50、turnover Median/Mean 比、amount IQR、range Q75-Q25 vs Q90-Q10（两种 spread）、median of range
- 硬闸 max_corr@F001 / F012 / C004_batch_043 reserve < 0.7
- 目标：≥1 候选 **mono_is ≥ 0.5 AND mono_oos ≥ 0.5**（阈值校准诊断新加要件）+ alpha_survival > 0.4

---

## Threads

### T001: Quantile-based shape 信号是否在 range/turnover/amount 上独立 [✗ DISPROVEN batch_044]

> [!failure]+ Thread 结论
> **Question**: Quantile(field, N, p) 差分或比值在非-return 字段上是否产生独立于 vol_20d 和现有流动性簇 (F001/F012) 的 forward IC？
>
> **Answer**: 否，全面证伪。3 个字段上的 Quantile shape 路径全部撞墙：
> - **range 字段**（C001 Q90-Q50 / C004 Q75-Q25 / C005 Median / C006 短长比）：4/4 dom_style=vol_20d (exposure 27–42) + incremental_ic 全负 (-0.020 到 -0.037)。Quantile 对尾部 robust ≠ 对 vol_20d orthogonal
> - **amount 字段**（C003 IQR）：max_corr=0.80@F012 坠入液性簇 + alpha_surv=0.07
> - **turnover 字段**（C002 Med/Mean）：IC 活 ICIR=+0.41 但 ls_t=+0.25 鸿沟，mono_oos U-shape (1.0→0.1)
>
> **Evidence trail**:
> - [[batches/batch_044/candidates/C001|batch_044 C001]]　Q90-Q50 range — mono -1/-0.9 严 ls_t=-2.64 但 vol_20d exp=45 + incr=-0.036 → **reserve**
> - [[batches/batch_044/candidates/C002|batch_044 C002]]　turnover Med/Mean — ICIR=+0.41 但 ls_t=+0.25 + mono_oos U-shape 0.1 → **reserve**
> - [[batches/batch_044/candidates/C003|batch_044 C003]]　amount IQR — max_corr=0.80@F012 + alpha_surv=0.07 → **reject**
> - [[batches/batch_044/candidates/C004|batch_044 C004]]　range Q75-Q25 — mono IS=OOS=-1.0 完美但 vol_20d exp=42 + incr=-0.037 → **reserve**
> - [[batches/batch_044/candidates/C005|batch_044 C005]]　range Median 60d — vol_20d exp=38 + ls_t=-1.93 weak + incr=-0.038 → **reserve**
> - [[batches/batch_044/candidates/C006|batch_044 C006]]　range Median 5d/60d 比 — mono_is -0.3→mono_oos -0.1 崩塌 + incr=-0.020 → **reserve**
>
> **元教训（升格 lessons 候选）**：Quantile 算子的 robust-to-outliers 属性**不等于** Barra vol_20d orthogonality——两个概念在本方向 hypothesis 设计中被混淆。**第 4 次跨方向独立确认 vol_20d 对 2nd-moment 的结构吸收**（+stochastic_position / vwap_proxy / range_structure）。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_044/candidates/C003\|C003]] | `Sub(Quantile($amount, 60, 0.75), Quantile($amount, 60, 0.25))` | max_corr=0.80@F012 near-dup territory + alpha_surv=0.07 + incr_ic=-0.044 |

---

## Related

- 🔴 [[return_distribution_signals]] `dead` — Skew/Kurt on daily-return 全部坍缩到 vol_20d；本方向**不用 return 字段**避开
- 🔵 [[range_structure]] `exploring` — C004 Skew(range, 60) 悖论组合存活但 mono_is 弱；本方向用 **Quantile 差分** 作更 robust 的 shape estimator
- 🟡 [[amount_volatility_signal]] `saturated` — F001 amount CV 占据 "amount 离散度" 空间；本方向用 Quantile IQR 是否独立待测
- 🟡 [[microstructure_illiquidity]] `saturated` — F012 amihud 占据 "量价冲击" 空间
- 📖 [[lessons#Data Facts]] — A 股 10% 涨跌幅约束对 quantile 上限的截断效应

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


## Instructions

Rewrite this direction md to compress long narrative logs, dedupe threads, and preserve Hypothesis + active Threads + Narrative Log (truncated to most recent 20 entries). Do not touch the frontmatter — Python manages that.
