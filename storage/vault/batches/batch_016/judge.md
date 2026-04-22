---
batch_id: batch_016
direction: return_distribution_signals
judged_at: 2026-04-21T02:10:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
batch_summary: {total: 5, admit: 0, reserve: 0, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 0
candidate_count: 5
mt_bucket: low
---

# batch_016 Judge Summary

> [!abstract]+ batch_016 · [[directions/return_distribution_signals]] · 5 candidates (direction 首批)
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=5**
> **核心发现**: **方向假设直接证伪——所有高阶矩 (skew/kurt/Q-range) 在 cross-section 上都 collapse 到 vol_20d**。C004 quantile range mono=-0.9 + ls_t=-2.28 看似强，但 style_r²=0.845 + alpha_survival=0.008 暴露其本质就是 vol_20d 的 monotone 变换。Skew/kurt 不是独立维度。
> **MT Budget**: cumulative 82 → **87** · direction 0 → **5**（首批） · bucket `low`

## 候选一览

| ID | Verdict | 档位 | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟡·🔴·🔴·🟢·🟡 | ic=-0.023 ls_t=0.27 alpha_surv=0.177 | 20d skew 几乎被 vol_20d 完全解释 | [[batches/batch_016/candidates/C001]] |
| C002 | ❌ reject | 🟡·🔴·🔴·🟢·🟡 | ic=-0.022 ls_t=-0.14 alpha_surv=0.173 | 60d skew 与 20d 几乎相同——horizon 无关 | [[batches/batch_016/candidates/C002]] |
| C003 | ❌ reject | hard_gate | sign_flip train -0.004 / val +0.002 | kurtosis sign 不稳，无 risk premium 也无 anomaly 方向 | [[batches/batch_016/candidates/C003]] |
| C004 | ❌ reject | 🔴·🟡·🔴·🟡·🟡 | mono=-0.9 ls_t=-2.28 style_r²=0.845 alpha_surv=0.008 | rank-order 强但 ≡ vol_20d；alpha_surv 整库最低之一 | [[batches/batch_016/candidates/C004]] |
| C005 | ❌ reject | 🟡·🔴·🔴·🟢·🟡 | ic=-0.028 ls_t=0.33 alpha_surv=0.098 | skew × vol 把弱信号更紧耦合到 vol_20d | [[batches/batch_016/candidates/C005]] |

## 跨候选对比

- **方向假设直接打脸**：5/5 候选全部 dom=vol_20d。3/5 alpha_survival < 0.20，C004 跌到 0.008（整库最低之一）。**Higher-order moments (skew/kurt/Q-range) 在 cross-section 上是 vol_20d 的 monotone derivatives**——理论独立性（mean / var / skew / kurt 数学上正交）在 A 股截面 rank space 完全 collapse。
- **C004 是关键证据**：quantile range Q90-Q10 mono=-0.9 ls_t=-2.28（看起来 admit-ready），但 alpha_survival=0.008——**rank-order 强 ≠ alpha 真**。该候选与 batch_014 C001（pure vol_20d，mono=-0.7 alpha_surv=0.5435）同源，但 alpha_surv 更低（因 Q90-Q10 是更纯的 vol proxy）。
- **C001 vs C002 horizon 不变性**：20d 与 60d skew IC=-0.023 vs -0.022 几乎相同——skew 信号不依赖 horizon，进一步证明它是 vol-derivative 而不是独立时间结构。
- **C005 interaction 反而更糟**：skew × vol = 把弱 skew 信号 amplify 进 vol，alpha_surv 0.098 < 单独 skew 0.177。Co-skewness 在本框架下不是 cleaner alpha 而是 worse。
- **MT 预算**：首批 5 候选，direction bucket=low；cumulative 87。

## Thread 进展

> [!failure]+ T001 [[directions/return_distribution_signals#T001]] — `[✗ DISPROVEN batch_016]` realized skewness 假设
> C001/C002/C005 三个 skew 变体（20d/60d/interaction）全部 dom=vol_20d + alpha_surv<0.20。Skew 不是独立 cross-sectional 维度。

> [!failure]+ T002 [[directions/return_distribution_signals#T002]] — `[✗ DISPROVEN batch_016]` kurtosis 假设
> C003 hard_gate sign_flip——kurtosis sign 在 IS/OOS 翻转，无稳定方向。

> [!failure]+ T003 [[directions/return_distribution_signals#T003]] — `[✗ DISPROVEN batch_016]` quantile range 假设
> C004 style_r²=0.845 + alpha_surv=0.008——Q90-Q10 ≡ vol_20d 的 monotone 变换，没有独立信息。

## 方向级反思

**首批即彻底证伪——方向 status: exploring → dead**。

证据链：
1. 三个独立 thread (skew/kurt/Q-range) × 5 候选全部 reject
2. 4/5 dom_style=vol_20d；alpha_survival 范围 0.008-0.177（远低 0.40 threshold）
3. C004 (mono=-0.9 ls_t=-2.28) 看似强但 alpha_surv=0.008 暴露本质——**rank-order 完美 + Barra coupling 极重 = vol_20d 在 disguise**
4. interaction (C005) 让事情更糟，证明 skew/kurt/Q-range 不只独立性弱，连作为 vol_20d 的"调节器"都失败

**核心元教训（已在前几批观察过，本批确认）**：
- A 股 csi1000 universe 的 cross-sectional 几何被 **vol_20d** 强烈主导
- 任何 daily-bar 内的 mean-of-power transformation (var/skew/kurt) 都 monotone-equivalent 到 cross-sectional vol rank
- 突破必须从 **不同时间频率**（intraday）、**不同信号源**（OHLC microstructure / fundamental shocks）、或 **非 rank 空间**（ensemble 组合）入手

**方向操作**：
- direction status `exploring → dead` （首批彻底证伪 hypothesis）
- priority `medium → low`
- 不进入 retry pool；不消耗后续 batch 算力

**Calibration trigger 检查（batch_014/015/016 连续 3 批 0 admit）**:
- 错杀 flag = 0 ✓
- 累计 reserve 中是否有满足"max_lib_corr<0.30 AND incremental_ic>0.010 AND mono>=0.80 AND sign_complement"四条件的候选？
  - batch_014 C001 (vol_20d): max_corr=0.254 ✓ / incr_ic=-0.046 ✗（负）
  - batch_013 C002 (vol-only residual): max_corr=0.12 ✓ / incr_ic=+0.030 ✓ / mono_oos=+0.7 ✗（<0.80）
  - batch_009 C003/C007（已重判过保留 reserve）
- **不触发 calibration**——genuine saturation，不是 over-rejection

**下批决策**：5 个 active 方向中 4 个 saturated/dead，仅 amount_volatility_signal 和 value_liquidity_interaction 名义 productive 但 DSL/Python residual 都已穷尽。**结构性瓶颈**：当前 cache（$close/$volume/$amount/$market_cap）的 alpha 容量已被 F001-F004 + barra residual 充分提取。继续挖需要：
1. **扩 OHLC cache** ($high/$low/$open) → 开 microstructure_signal 方向
2. **扩 industry data** → 开 industry_relative 方向
3. **跨频率** (intraday OHLC) → 全新数据维度
4. **非线性 ensemble** of F001-F004 (e.g. 在 portfolio weight 层面而非因子值)

无前提条件突破，硬继续会持续 0 admit。建议本轮停 mining，进入数据扩展或 consolidation。
