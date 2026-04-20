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

## Hypothesis

收益率分布的高阶矩（skewness/kurtosis/quantile range）携带超出 mean/variance 之外的预测信息。Empirical regularities in equity markets:
- **Realized skewness anomaly**: 高 realized skewness 股票（彩票偏好）随后跑输——散户偏好"右尾"（一夜暴富），导致此类股票被高估
- **Kurtosis premium**: 高 kurtosis（fat tails）反映 latent jump risk，理论上应有 risk premium 但 cross-section 实测常常反向
- **Q-range as alternative volatility**: P90-P10 of returns 比 std 对极端值更鲁棒，可能替代 vol_20d 的 risk-axis 角色

经济直觉：return 分布不对称性 / 尾部行为不被 Barra 7-style 完全覆盖（Barra 主要 capture 二阶矩 + 截面 cross-loadings）。三/四阶矩可能在 cross-sectional 上构成新维度，绕过 vol_20d 主导陷阱。

## Current Focus

**新方向首批 batch_016**：扫窗口（20/60d）×（skew/kurt/qrange）的 DSL 实现，建立基线 IC 和与 vol_20d 的相关度。

## Threads

### T001: Realized skewness 是否携带 forward IC [✗ DISPROVEN batch_016]
**Question**: TsSkew(returns, N) 在 N=20/60 上的 OOS IC 是否 >0.008 且 sign 稳定？
**Evidence trail**:
- [[batches/batch_016/candidates/C001|batch_016 C001]]: 20d skew → ic=-0.023 ls_t=0.27 alpha_surv=0.177 dom=vol_20d → reject
- [[batches/batch_016/candidates/C002|batch_016 C002]]: 60d skew → ic=-0.022 ls_t=-0.14 alpha_surv=0.173 (与 20d 几乎相同) → reject
- [[batches/batch_016/candidates/C005|batch_016 C005]]: skew × vol interaction → alpha_surv=0.098 (比单独 skew 更糟) → reject
**Conclusion**: skew 在 cross-section 上是 vol_20d 的 monotone derivative；horizon (20/60) + interaction (× vol) 都不能解耦。

### T002: Kurtosis 是 risk factor 还是 alpha factor [✗ DISPROVEN batch_016]
**Question**: TsKurt(returns, 20) 是否产生显著 IC？sign 与理论 risk premium 一致 vs 反向？
**Evidence trail**:
- [[batches/batch_016/candidates/C003|batch_016 C003]]: 20d kurt → hard_gate sign_flip (train -0.004 / val +0.002) → reject
**Conclusion**: kurtosis sign 在 IS/OOS 翻转，无稳定 risk premium 也无稳定 anomaly 方向。

### T003: Quantile range 与 std 的差异 [✗ DISPROVEN batch_016]
**Question**: Q90-Q10 是否提供 std 之外的独立信息？
**Evidence trail**:
- [[batches/batch_016/candidates/C004|batch_016 C004]]: Q90-Q10 → mono=-0.9 ls_t=-2.28（看似强）但 style_r²=0.845 + alpha_surv=0.008（整库最低之一）→ reject
**Conclusion**: Q90-Q10 ≡ vol_20d 的 monotone 变换；rank-order 强不等于 alpha 真。

## Known Failures
- C001 (batch_016): 20d realized skew — alpha_surv=0.177 + dom=vol_20d (skew→vol collapse)
- C002 (batch_016): 60d realized skew — alpha_surv=0.173 + dom=vol_20d (horizon-invariant)
- C003 (batch_016): 20d realized kurt — hard_gate sign_flip (train -0.004 / val +0.002)
- C004 (batch_016): Q90-Q10 of 20d returns — alpha_surv=0.008 catastrophic (≡ vol_20d monotone)
- C005 (batch_016): skew × vol interaction — alpha_surv=0.098 (worse than C001)
**方向假设直接证伪**——higher-order moments 不是独立 cross-sectional 维度。

## Related
- [[lessons#Structural Constraints]]  （Barra style coupling 教训）
- [[barra_residual_alpha]]  （saturated；本方向是绕过路径）

## Narrative Log
### 2026-04-21 [[batches/batch_016/judge|batch_016]]
**admit=0 / reserve=0 / reject=5 — direction status: exploring → dead**

5 候选首批彻底证伪方向 hypothesis：
- skew (20d/60d/×vol) 三个变体全部 dom=vol_20d + alpha_surv 0.10-0.18 远低 threshold
- kurt 20d sign_flip
- Q90-Q10 mono=-0.9 ls_t=-2.28 看似强但 alpha_surv=0.008 暴露其本质等价 vol_20d

**核心元教训**：A 股 csi1000 universe 的 cross-sectional 几何被 vol_20d 强烈主导——任何 daily-bar 内的 mean-of-power transformation (var/skew/kurt/quantile-range) 都 monotone-equivalent 到 vol rank。突破必须从不同时间频率 (intraday OHLC)、不同信号源 (microstructure / fundamental shocks) 或非 rank 空间 (portfolio-level ensemble) 入手。

**Direction operations**：
- status `exploring → dead`（首批彻底证伪）
- priority `medium → low`
- 不进入 retry pool

**下一步**：本方向 dead，资源转向 (a) 扩 OHLC cache 开 microstructure_signal 方向，或 (b) 进入 Phase 5 consolidation 重写 lessons.md / promising_unexplored，或 (c) 暂停 mining 待数据扩展。
