---
direction_tag: pv_covariance
status: dead
priority: low
rounds: 1
admits: 0
last_batch: batch_039
last_admits: []
last_goal: 'T001+T002 first pass on Cov(.,.,N) form not yet in library: 4 pairs ×
  2 windows × daily return/body variants. Explore whether turnover-return / amount-body
  / volume-body / amount-ret covariance captures orthogonal info vs F009 overnight
  spread (also a covariance derivative). Critical gate: max_corr@F009 < 0.70 else
  near_duplicate.'
last_activity: '2026-04-23T19:24:44Z'
created_batch: null
members: []
merged_into: null
---
# pv_covariance

> [!abstract]+ 方向概要
> - **状态**　🔴 `dead` · priority `low` · rounds = 1 · admits = 0
> - **最近**　[[batches/batch_039/judge|batch_039]] · 2026-04-24 · 0/0/6（首批即方向证伪）
> - **一句话**　Cov(.,.,N) 形态在 csi1000 归簇 F001/F009/F012 三个已有反转簇因子 — 第 4 次跨方向重现 volume × direction 反转簇

> [!warning] ⚠️ Hypothesis 完全证伪（batch_039）
> 原假设：Cov 形态与已有 Std/Mean/Div/Mul 形态正交，在 csi1000 探明新 family。
> 实测：6/6 IC_OOS 负 (-0.042 至 -0.051)、incr_ic 全负 (-0.025 至 -0.032)，无论 x/y 配对、20d/60d 窗口都归簇 F001 amount_cv / F009 overnight spread / F012 amihud。
> **元教训**：第 4 次跨方向重现 "volume × direction 复合" 归簇 F001/F009/F012 反转 family —— 升格至 lessons.md（下次 consolidation）：**csi1000 上 volume/turnover × return/body 各种 DSL 形态（Cov / 线性 Mul / log-compressed Mul）都是同一个反转簇载体**。

---

## Hypothesis

当前库 12 个 admits 覆盖：amount CV (F001)、value/liquidity 比 (F002)、overnight gap magnitude (F003)、Barra residual return (F004)、shadow persistence (F006/F007/F008)、overnight spread + persistence (F009/F010/F011)、amihud illiquidity (F012)、log gap acceptance (F013)。**形态分布**：Std/Mean 比 (F001)、Div (F002/F003/F012)、Mean of body/return (F006-F011)、Mul of sign/log (F013)。**0 个 Cov(.,.,N) 形态**。

`Cov($a, $b, N) = Mean(($a - Mean($a,N)) × ($b - Mean($b,N)), N)` ——捕获两序列在 N 日窗口的协动方向。语义独特：
- **Cov($turnover_rate, daily_ret, N)**：在量价同步上涨日、量价同跌日得正值（"价量配合"）；在量增价跌日、量缩价升日得负值（"背离"）
- **Cov($amount, body_ratio, N)**：在大成交日大阳线、小成交日小阴线一致时得正值（institutional footprint proxy）
- **Cov(daily_ret, $volume, N)**：与 Cov(turnover, ret) 不同——volume 是绝对股数，turnover_rate 是流通股占比，对小盘 universe 信息量不同

预期：**Cov 形态在 csi1000 的协动维度未被现有库探明**，可能解锁 incremental_ic > 0 的新通道。Risk：可能与 F009 overnight spread 共线（overnight spread 也是协动产物）；通过 max_corr 测试。

---

## Current Focus

- 首批 6 候选覆盖 (turnover, ret) / (amount, ret) / (amount, body_ratio) / (turnover, body_ratio) 四组合 + 20d/60d 两窗口
- 若 T001 命中 → T002 探长窗变体；若全 reject → 方向 dead
- 严格 max_corr@F009 < 0.7 否则 near_duplicate

---

## Threads

### T001: Cov(turnover, return) [✗ DISPROVEN batch_039]

> [!failure]+ Thread 结论
> **Question**: 20d/60d Cov($turnover_rate, daily_return) 是否在 csi1000 上携带独立于 F009 spread / F001 amount_cv 的 alpha？
> **Answer**: 否。C001 20d (IC_OOS=-0.049) + C003 60d (IC_OOS=-0.043) + C005 amount_ratio (IC_OOS=-0.051 批内最深) 全部 reject，max_corr@F001 0.20-0.33 清晰归簇。
> **Evidence trail**:
> - [[batches/batch_039/candidates/C001|batch_039 C001]]　20d turnover×ret → **reject**
> - [[batches/batch_039/candidates/C003|batch_039 C003]]　60d turnover×ret → **reject**
> - [[batches/batch_039/candidates/C005|batch_039 C005]]　amount_ratio×ret max_corr=0.33@F001 → **reject**

### T002: Cov(amount or volume, body or ret) [✗ DISPROVEN batch_039]

> [!failure]+ Thread 结论
> **Question**: $amount / $volume × body/ret 配对是否提供与 T001 turnover-pair 不同的信息？
> **Answer**: 否。C002/C004/C006 全部归簇 F012 amihud 或 F009 intraday，alpha_surv 0.34-0.40 poor/borderline。
> **Evidence trail**:
> - [[batches/batch_039/candidates/C002|batch_039 C002]]　amount×body alpha_surv=0.34 → **reject**
> - [[batches/batch_039/candidates/C004|batch_039 C004]]　volume×dClose alpha_surv=0.37 → **reject**
> - [[batches/batch_039/candidates/C006|batch_039 C006]]　turnover×body → **reject**

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_039/candidates/C001\|C001]] | `Cov($turnover_rate, daily_ret, 20)` | misaligned + reducer (incr=-0.029, max_corr=0.20@F001) |
| [[batches/batch_039/candidates/C002\|C002]] | `Cov($amount, close-open, 20)` | misaligned + alpha_surv=0.34 poor |
| [[batches/batch_039/candidates/C003\|C003]] | `Cov($turnover_rate, daily_ret, 60)` | misaligned + reducer |
| [[batches/batch_039/candidates/C004\|C004]] | `Cov($volume, close-prev_close, 20)` | misaligned + alpha_surv=0.37 poor |
| [[batches/batch_039/candidates/C005\|C005]] | `Cov(amt_ratio, daily_ret, 20)` | misaligned + max_corr=0.33@F001 |
| [[batches/batch_039/candidates/C006\|C006]] | `Cov($turnover_rate, close-open, 20)` | misaligned + reducer |

---

## Related

- 🟡 [[gap_acceptance_structure]] `saturated` — F013 来源；本方向避开 sign × sign 形态，直接探 Cov
- 🟡 [[overnight_intraday_split]] `saturated` — F009 spread 是协动的隐式形式；max_corr 防 near_dup
- 🟡 [[amount_volatility_signal]] `saturated` — F001 amount_cv 是 Std/Mean，与 Cov 形态正交但同源数据
- 📖 [[lessons#Structural Constraints]]

---

## Narrative Log

> [!quote]+ 2026-04-24 · [[batches/batch_039/judge|batch_039]]
> **首批即方向完全证伪 → status: exploring → dead** · admit=0 / reserve=0 / reject=6
>
> - 6/6 IC_OOS 负 (-0.042 至 -0.051)，incr_ic 全负 (-0.025 至 -0.032)，max_corr 击中 F001/F009/F012
> - Cov 形态是 csi1000 **第 4 次跨方向重现** 的 "volume × direction 反转簇" 载体
> - 前 3 次：trend_quality_gated (gated momentum = reversal) / log_value_liquidity (value × log-liq → F009 簇) / batch_032 liquidity_acceleration (F001 reducer)
> - MT budget cumulative 192 → **198** · direction 0 → **6** · bucket `medium`
>
> **Operations**　`status: exploring → dead` · `priority: medium → low` · 元教训进 lessons.md（下次 consolidation 升格）

> [!quote]- 2026-04-24 · untested family probe
> **方向：current library 12 admits 没有 Cov 形态，开 1 批探明** · rounds = 0
>
> - 假设：Cov(.,.,N) 在 csi1000 与现有 Std/Mean/Div/Mul 形态正交
> - 主要冲突风险：F009 overnight spread（也是协动产物）、F012 amihud（也含 vol-return 配对结构）
> - 首批目标：6 候选 × 4 配对 × 2 窗口探明
