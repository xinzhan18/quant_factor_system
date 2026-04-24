---
direction_tag: range_structure
status: exploring
priority: medium
rounds: 1
admits: 0
last_batch: batch_043
last_admits: []
last_goal: 首批探 range (high-low) 结构是否独立于 vol_20d 的 std-return 空间。5 子形式：IdxMax 时序 timing、高
  range 频率、低 range 频率、range 分布 skew、短/长窗 ratio、range 变化率。硬闸 max_corr@F001 / F012 /
  F013 < 0.7 防流动性簇吸收；目标 dominant_style ≠ vol_20d。
last_activity: '2026-04-24T02:18:59Z'
created_batch: batch_043
members: []
merged_into: null
---
# range_structure

> [!abstract]+ 方向概要
> - **状态**　🔵 `exploring` · priority `medium` · rounds = 0 · admits = 0
> - **最近**　未启动 · 首批 batch_043 探 5 子形式 (timing / freq / skew / 短长比 / 变化率)
> - **一句话**　high-low range **结构**（timing、frequency、skew、短/长比）是否独立于 vol_20d 的 std-of-return 空间

---

## Hypothesis

现有库 13 admits 中与"波动率"有关的都是基于 daily returns 的 std（F001 amount CV、F012 amihud）或 overnight/intraday 分解（F003/F009/F010/F011）——这些都被 Barra 的 `vol_20d` 风格因子 (20d std of daily returns) 广泛吸收。

**(high - low) / close** 是**日内价格路径的测量**，数学上不等于 daily-return std。直觉上相关但不等价：同一 daily return 可以来自"全天缓慢爬升"（低 high-low）或"高波动震荡后收于同价"（高 high-low）。因此 range **magnitude** 可能仍被 vol_20d 吸收（均值-方差一致性），但 range 的**结构**（timing / 频率 / 形状）可能逃离：

- **Timing 信号**：IdxMax((high-low)/close, N)——最大 range 出现在近还是远（event timing），离散的"第几天"不是连续的 vol
- **Frequency 信号**：Mean(Gt((high-low)/close, threshold), N)——高 range 日的频率（count-based 聚合），规避了 power-mean 的 vol 同构
- **Skew 信号**：Skew((high-low)/close, 60)——range 分布的非对称（少数大 range 日 vs 大多数小 range 日 vs 反之），测量事件驱动 vs 噪声驱动
- **短/长比**：Mean((high-low)/close, 5) / Mean((high-low)/close, 60)——range 波动的 regime change，类似 C003 加速度但在 range 空间
- **变化率**：Delta(Mean((high-low)/close, 20), 5)——range 趋势

csi1000 特征：
- 小盘在涨跌幅 10% 约束下，高 range 日是"事件日"（新闻、游资介入）—— timing 可能携带游资脚印
- 连续几个低 range 日 → 高 range 日爆发 (Bollinger-style compression/expansion)

**关键风险**：
- (high-low)/close 与 vol_20d 的 corr 可能 > 0.6（历史已知事实）；本方向需关注**结构化 transformation**后的 residual
- F012 amihud_illiq_20d 已占据"流动性"空间；timing/freq 需独立

---

## Current Focus

- 首批 6 候选各打一个形式：timing、两种 freq（高/低 range 阈值）、skew、短长比、变化率
- 硬闸 max_corr@F012 / F001 / F013 < 0.7 防液性/amount 簇吸收
- 目标：≥1 候选 dominant_style ≠ `vol_20d` + alpha_survival > 0.4

---

## Threads

### T001: Range timing/frequency/shape 信号是否独立于 vol_20d [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: (high-low)/close 的离散结构化 transformation（IdxMax 时序 / Gt-threshold 频率 / Skew shape）在 cross-section 上是否逃离 vol_20d 连续 std 空间，产生独立 forward IC？
>
> **Evidence trail**:
> - [[batches/batch_043/candidates/C001|batch_043 C001]]　IdxMax((H-L)/C, 20) timing — mono_oos=-0.90 一桨 Q5, ls_t=-1.40 弱, incr_ic=-0.008 → **reject**（信号太弱）
> - [[batches/batch_043/candidates/C002|batch_043 C002]]　Mean(Gt((H-L)/C > 1.5×60d_baseline), 20) freq-high — vol_20d exp=47.9 + alpha_surv=0.23 + incr_ic=-0.019 → **reject**（**freq-high threshold 仍在 vol_20d 空间，子路径 DISPROVEN**）
> - [[batches/batch_043/candidates/C003|batch_043 C003]]　Mean(Lt((H-L)/C < 0.5×60d_baseline), 20) freq-low — max_corr=0.16@F002 独立但 mono_oos=0.0 + ls_t=-0.23 → **reserve**（compression 机制存活但信号弱）
> - [[batches/batch_043/candidates/C004|batch_043 C004]]　Skew((H-L)/C, 60) ⚠️ — **mono_oos=+1.00 完美 + ls_t=+2.46 + incr_ic=+0.014 + max_corr=0.117@F012 + cum_mdd=-2.01 最浅**；但 mono_is=0.30 弱 + alpha_survival=0.14 poor → **reserve**（subagent flag 悖论组合，**阈值校准诊断为非真错杀**：mono IS→OOS 异常放大非稳健机制，详见 [[batches/batch_043/judge|batch_043 judge]] §阈值校准诊断）
>
> **本批发现**：timing / freq-high 两子路径封闭；shape(skew/低频 threshold) 路径存活但需重新设计——下轮应加 **mono_is 硬下界 0.6** 防 OOS-only 统计波动，并试 Kurt / Quantile-based shape 变体。

### T002: Range 短/长比与变化率是否独立于 F001 amount CV [✗ DISPROVEN batch_043]

> [!failure]+ Thread 结论
> **Question**: range 的短长窗比 ratio 和 Delta 变化率（活跃度 regime shift）是否与 F001 amount CV 同向冲突（负 incremental_ic）还是独立？
>
> **Answer**: 否，range magnitude/ratio 在 csi1000 与 F001/F009 共享同一反转簇载体。两候选 IC 稳定 9 年同号但 **incremental_ic 全部为负**，vol_20d exposure 13.9–27.7。
>
> **Evidence trail**:
> - [[batches/batch_043/candidates/C005|batch_043 C005]]　Div(Mean((H-L)/C, 5), Mean((H-L)/C, 60)) 短长比 — IC_OOS=-0.038 本批最强 mono=-0.9 ls_t=-2.18 但 **incr_ic=-0.025 NEGATIVE** + vol_20d exp=27.7 + cum_mdd=-82 → **reserve**（orthogonalize 路径待工具链）
> - [[batches/batch_043/candidates/C006|batch_043 C006]]　Delta(Mean((H-L)/C, 20), 5) 变化率 — ls_t=-2.74 但 mono_is=-0.7→mono_oos=-0.10 崩塌 + **incr_ic=-0.017 NEGATIVE** → **reserve**（Q5 一桨驱动 + 库负冗余）
>
> **元教训**：**第 3 次跨方向独立确认**（stochastic_position / vwap_proxy_signals / range_structure）——csi1000 的 cross-section 几何被 vol_20d 主导 2nd-moment 空间，magnitude/ratio 形态全部坍缩到 vol 簇。**升格至 lessons**（下次 consolidation）。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_043/candidates/C001\|C001]] | `IdxMax((H-L)/C, 20)` | mono_oos=-0.90 一桨 Q5 + ls_t=-1.40 弱 + incr_ic=-0.008 负（库减值）|
| [[batches/batch_043/candidates/C002\|C002]] | `Mean(Gt((H-L)/C > 1.5×60d_base), 20)` | vol_20d exposure=47.9 极端 + alpha_surv=0.23 poor + incr_ic=-0.019（freq-high 未逃离 vol_20d）|

## Narrative Log

> [!quote]+ 2026-04-24 · [[batches/batch_043/judge|batch_043]]
> **首批分裂结论：magnitude/ratio 全败，shape 存活但悖论组合** · admit=0 / reserve=4 / reject=2
>
> - **T002 DISPROVEN**：C005 短长比 + C006 变化率，IC 稳定 9 年同号但 incremental_ic 全负 (-0.025 / -0.017)，vol_20d exposure 13.9–27.7——range ratio/velocity 与 F001/F009 共享反转簇载体。**第 3 次跨方向独立确认**（+stochastic / +vwap_proxy）升格 lessons 元教训
> - **T001 部分存活**：C001 timing (IdxMax) + C002 freq-high 封闭；C003 freq-low + C004 shape(skew) 存活 reserve
> - **C004 悖论诊断**：4 个 error-kill 指标全过（max_corr=0.117, incr_ic=+0.014, mono_oos=+1.0, cum_mdd=-2.01 最浅）但 **mono_is=0.30 弱** + alpha_surv=0.14 poor——诊断为**非真错杀**（mono IS→OOS 异常放大不是稳健 alpha），不调阈不追溯；建议升格错杀侦测要件加 mono_is 硬下界 0.6
> - MT budget cumulative 216 → **222** · direction 0 → **6** · bucket `medium`
>
> **Operations**　`priority: medium → low`（shape 路径需重新设计 + 工具链阻塞）· `status: exploring` 保持（首批不足判 saturated）

---

## Related

- 🔴 [[return_distribution_signals]] `dead` — daily-return skew/kurt/Q-range 全部坍缩到 vol_20d；本方向用 range (high-low) 而非 return，**数学上不同**——关键测试
- 🟡 [[stochastic_position]] `saturated` — (close - TsMin) / (TsMax - TsMin) rank-order 崩塌；本方向是 range 大小 & timing 而非 close 在 range 内的位置
- 🟡 [[intraday_price_formation]] `saturated` — 单日 (close-low)/(high-low) mono_sign_flip；本方向在 N 日窗口而非单日 intrabar
- 🟡 [[liquidity_acceleration]] `saturated` — 流动性 ratio 全部落入 F001 吸收簇；T002 要看 range ratio 是否同样命运
- 📖 [[lessons#Data Facts]] — A 股 10% 涨跌幅约束对 range 上限的结构影响
- 📖 [[lessons#Operator Registry]] — TsSkew / IdxMax 自定义算子，C.kernels=1
