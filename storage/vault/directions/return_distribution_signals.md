---
direction_tag: return_distribution_signals
status: dead
priority: low
rounds: 1
admits: 0
last_batch: batch_016
last_admits: []
last_goal: '首批 5 DSL 候选探索 return 分布高阶矩 (skew/kurt/qrange) on $close-derived 1d returns，窗口
  20/60d。Hypothesis: 三/四阶矩在 Barra 7-style 之外构成新 cross-sectional 维度，绕过 barra_residual_alpha
  的 vol_20d 饱和。目标 ≥1 admit。'
last_activity: '2026-04-20T18:14:42Z'
created_batch: batch_016
members: []
retired_members: []
merged_into: null
---
# return_distribution_signals

> [!abstract]+ 方向概要
> **状态**　🔴 dead · priority=low · rounds=1 · admits=0
> **最近**　[[batches/batch_016/judge|batch_016]] · 2026-04-21 · admit=0 / reserve=0 / reject=5
> **一句话**　Daily-bar return 分布的高阶矩 (skew / kurt / Q90-Q10) 在 csi1000 上 **全部 monotone-equivalent 到 vol_20d**，不构成独立 cross-sectional 维度。本方向为 F301 「magnitude/2nd-moment/quantile 坍缩律」最早一例独立证据点（5+ 方向已重复确认）。

---

## Hypothesis

> [!warning]+ ⚠️ Hypothesis 已证伪（batch_016，5/5 证伪信号；后续 5+ 方向独立复现）
> **原设定**：收益率分布的高阶矩（skewness / kurtosis / quantile-range）携带 mean/variance 之外的预测信息——realized skewness anomaly（彩票偏好导致高 skew 股票被高估）、kurtosis premium（fat tails = latent jump risk）、Q-range 作为 std 的 robust 替代；三/四阶矩在 Barra 7-style 之外构成新 cross-sectional 维度，绕过 [[barra_residual_alpha]] 的 vol_20d 饱和。
>
> **证伪证据**（首批 5 候选全军覆没）：skew 三变体 (20d / 60d / ×vol) 全 `dom=vol_20d` + `alpha_surv` 0.10–0.18 远低 threshold；kurt 20d hard_gate sign_flip (train −0.004 / val +0.002)；Q90-Q10 `mono=-0.9 ls_t=-2.28` 看似强但 `alpha_surv=0.008` 暴露本质 ≡ vol_20d monotone 变换。
>
> **🔑 核心元教训**（F001 + F301，已升格至 [[lessons]]）：**A 股 csi1000 universe 的 cross-sectional 几何被 vol_20d 强烈主导——任何 daily-bar 内的 mean-of-power / quantile / power-mean transformation (var / skew / kurt / quantile-range) 都 monotone-equivalent 到 vol rank**。判别规则：`dominant_style=vol_20d` + `style_r² > 0.30` + `alpha_survival < 0.30` 同时成立 ⇒ "magnitude 空间饱和" 标志，直接 reject。逃离路径仅四条：(a) 不同时间频率（intraday OHLC / minute），(b) 不同信号源（microstructure / fundamental shocks / signed direction），(c) 非 rank 空间（portfolio-level ensemble / true Barra residual，但本身受 coverage<0.80 限制），(d) overnight 段独立分解。
>
> **🔑 第二元教训**（F004 + F300）：高阶矩本质上是 return 的 **power-mean / rate** 形式——本方向同属 "rate/delta/ratio 形式跨 5+ 方向结构性失败律"。Q90-Q10 即 quantile-range "rate" 形式的代表性反例（`ls_t=-2.28` 强 rank-order ≠ 真 alpha）。Level 形式（如 F010 hhi_vol_20 ls_t=7.50）才是 csi1000 稳定信号源。

---

## Threads

> [!failure]+ T001-T003 · Higher-order moments 三合一证伪 `[✗ DISPROVEN batch_016]`
> **Question**: TsSkew / TsKurt / Q90-Q10 在 csi1000 上是否产生独立于 vol_20d 的 forward IC？
>
> **Evidence trail**:
> - [[batches/batch_016/candidates/C001|C001]] · 20d skew → `ic=-0.023 ls_t=0.27 alpha_surv=0.177 dom=vol_20d` → reject
> - [[batches/batch_016/candidates/C002|C002]] · 60d skew → `ic=-0.022 ls_t=-0.14 alpha_surv=0.173`（horizon-invariant，与 20d 几乎同形）→ reject
> - [[batches/batch_016/candidates/C005|C005]] · skew × vol 交互 → `alpha_surv=0.098`（比单独 skew 更糟，交互放大共线）→ reject
> - [[batches/batch_016/candidates/C003|C003]] · 20d kurt → hard_gate sign_flip (train −0.004 / val +0.002) → reject
> - [[batches/batch_016/candidates/C004|C004]] · Q90-Q10 of 20d returns → `mono=-0.9 ls_t=-2.28` 看似强，`style_r²=0.845` + `alpha_surv=0.008`（整库最低之一）→ reject
>
> **Conclusion**: 三/四阶矩 + quantile-range 在 cross-section 上全部坍缩为 vol_20d 的 monotone derivative；horizon (20/60)、interaction (×vol)、order (skew vs kurt) 都不能解耦。**rank-order 显著 ≠ alpha 真**——Q90-Q10 是最佳反例。本结论后被 F001 / F301 升格为跨 8 方向的"vol_20d 吸收律"。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_016/candidates/C001\|C001]] | 20d realized skew | `alpha_surv=0.177` + `dom=vol_20d` |
| [[batches/batch_016/candidates/C002\|C002]] | 60d realized skew | `alpha_surv=0.173`（horizon-invariant 坍缩）|
| [[batches/batch_016/candidates/C003\|C003]] | 20d realized kurt | hard_gate sign_flip (−0.004 / +0.002) |
| [[batches/batch_016/candidates/C004\|C004]] | Q90-Q10 of 20d returns | `alpha_surv=0.008` catastrophic (≡ vol_20d monotone) |
| [[batches/batch_016/candidates/C005\|C005]] | skew × vol interaction | `alpha_surv=0.098`（比 C001 更糟）|

---

## Related

- 🟡 [[barra_residual_alpha]] `saturated` — vol_20d 主导陷阱的源头；本方向原设定为绕过路径，结果证实高阶矩依旧坍缩回 vol 轴
- 🔴 [[vol_shock_signals]] `dead` — magnitude shock 同源坍缩（F301 第 2 例独立证据）
- 🔴 [[quantile_shape_signals]] `dead` — Quantile robust ≠ orthogonal（F301 第 4 例）
- 🟡 [[stochastic_position]] `saturated` — %K / TsRank 同 2nd-moment 坍缩
- 🟡 [[range_structure]] / 🟡 [[amount_volatility_signal]] `saturated` — magnitude 几何同律
- 🔵 [[lessons#Structural Constraints]] — F001 / F301 vol_20d 吸收律 + F004 / F300 rate-form 失效律

---

## Narrative Log

> [!quote]+ 2026-04-25 · Phase 5 consolidation · `status: dead (unchanged)`
> 接收 4 条 distillation findings：F001（vol_20d 结构性吸收 2nd-moment 空间，跨 8 方向）/ F004（rate/delta/ratio 形式跨 5+ 方向失败律 + Meta-pattern 机械迁移风险）/ F300（rate-form 升格 lessons）/ F301（magnitude/2nd-moment/quantile 坍缩律升格 lessons）。本方向 batch_016 的 Q90-Q10 案例（`ls_t=-2.28` 强 rank-order + `alpha_surv=0.008` 灾难）成为 F001/F301 反复引用的标杆反例。Hypothesis 段已加注两条核心元教训（vol_20d 坍缩律 + rate-form 失效律）；Related 段补全跨方向同律证据网络。F300 / F301 建议状态变更 `dead → archived`，但本系统暂不引入 archived 态，维持 dead + priority=low。

> [!quote]+ 2026-04-21 · [[batches/batch_016/judge|batch_016]] · `status: exploring → dead`
> admit=0 / reserve=0 / reject=5；首批 5 候选彻底证伪 hypothesis：skew (20d/60d/×vol) 三变体全 `dom=vol_20d` + `alpha_surv` 0.10–0.18；kurt sign_flip；Q90-Q10 `ls_t=-2.28` 看似强但 `alpha_surv=0.008` 暴露 ≡ vol_20d。T001/T002/T003 同批次 `[◉ ACTIVE] → [✗ DISPROVEN]`。priority `medium → low`，不进入 retry pool。下一步：(a) 扩 OHLC cache 开 microstructure_signal 方向，或 (b) Phase 5 重写 [[lessons]] / promising_unexplored，或 (c) 暂停 mining 待数据扩展。
