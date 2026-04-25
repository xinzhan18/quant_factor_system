---
batch_id: batch_053
direction: intraday_price_formation
judged_at: 2026-04-25T08:30:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reserve_count: 1
reject_count: 5
candidate_count: 6
mt_bucket: high
---

# batch_053 Judge Summary

> [!abstract]+ batch_053 · [[directions/intraday_price_formation]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=1** (C001 max_corr=-0.694@F020 + incr_ic=0.0096 + alpha_surv=0.37 三 borderline) · ❌ **reject=5** (C002 hard_gate quad-fail; C003 max_corr=-0.732@F012 over redundancy red-line + style_r²=0.66 vol_20d high crowding; C004 mono_oos=-0.3 weak + ls_t=-0.14 PnL flat; C005 max_corr=-0.692@F012 + incr_ic=-0.020 库减值 + 5 因子 cluster -0.5x; C006 alpha_surv=0.17 + mono=-0.3/+0.3 sign_flip near-hard-gate)
> **核心发现**：**rank-diff 范式第 7 次跨家族泛化在 intraday_price_formation **失败 — 范式连胜中断 (b047-b051 五连胜后第二次中断, b052 是首次)**。本批揭示三条新结构性约束：(1) **F020 (gap_vol×body_ratio rank-diff) admit 后形成结构性 anti-anchor — 任何 intraday body-position higher-moment LHS 在 rank-diff 几何中必与 F020 强反向 cluster** (C001 max_corr=-0.694, signed_body_pos Std vs Abs body_disp Std)；(2) **F012 (Amihud_20) 在长窗 RHS Amihud_60 复用时形成 -0.7+ cluster**——RHS 共振饱和律的负向版本：同 atomic 不同窗口 RHS 与同 atomic 因子负向共振 (C003/C005 双例)；(3) **intraday family 在 vol_20d 上的天然高暴露**——本批 C003 style_r²=0.656 + C006=0.374 + C004=0.281 验证日内振幅 LHS 全部被 vol_20d 吸收, 即使 rank-diff transformation 也无法剥离。**rank-diff geometry 不是 intraday family 的钥匙——F020 admit 已锁死该 family 50%+ 几何空间**。
> **MT Budget**: cumulative 276 → **282** · direction 16 → **22** · bucket `high` (search_adjusted → medium) · 本批 low=2 (C004/C006) / med=3 (C001/C003/C005) / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟢·🟢·🟠·🟡·🟢 | ic_oos=+0.046 ls_t=3.40 mono=1.0/1.0 alpha_surv=**0.37** max_corr=**-0.694@F020** incr=**0.0096** ls_Sharpe_oos=2.45 | rank-order 真实 + 9 年同号 + ls_Sharpe 2.45 + signed body-pos higher-moment 是 novel atom；但三 borderline 同时叠加 (alpha_surv<0.40 + max_corr>0.50 cluster + incr_ic<0.010) — F020 anti-anchor 几何对称性导致 rank-diff transformation 无法剥离 F020 共振 — reserve 待 b052 升格"factor-anchored cluster RHS 动态律"在新 anchor 复现验证 | [[batches/batch_053/candidates/C001]] |
| C002 | ❌ reject | hard_gate | sign_flip train +0.007 vs val -0.0005 + ic_oos_too_low \|·\|=0.0005 + mono_sign_flip IS=0.90 OOS=-0.70 + oos_decay=-0.069 (四闸同时 fail) | VWAP-proxy OHLC4-mean 偏差是 hypothesis 上的 novel atom，但 OHLC4-mean 在 csi1000 上是 noise estimator (4 字段平均后 ≈ close → 偏差 / range ≈ 0)；signal IS 已经弱 (ic=0.007)，validation 直接翻号崩塌 — 验证"intraday OHLC algebraic mirror 法律"在 4-field arithmetic mean 形态复现 | [[batches/batch_053/candidates/C002]] |
| C003 | ❌ reject | 🟢·🟢·🔴·🔴·🟢 | ic_oos=-0.067 ls_t=-4.27 mono=-1.0/-1.0 ls_Sharpe=-3.08 **alpha_surv=0.36 style_r²=0.656 max_corr=-0.732@F012 incr=-0.024** | 信号本身极强 (mono 双侧完美 + ls_t -4.27 + 9 年同号)，但 (a) max_corr=-0.732 超 0.70 redundancy 红线触 CP05 硬 reject + (b) style_r²=0.656 vol_20d 极重 high crowding (RHS Amihud_60 与 F012 Amihud_20 同 atom 不同窗口 = anchored cluster 负向版本) — **同 atomic 不同窗口 RHS 与同 atomic 因子负向共振**新律 | [[batches/batch_053/candidates/C003]] |
| C004 | ❌ reject | 🟡·🔴·🟡·🟡·🟠 | ic_oos=-0.016 ls_t=-0.14 mono=-1.0/-0.3 alpha_surv=1.01 max_corr=-0.425@F004 incr=-0.001 | mono_is=-1.0 极强但 mono_oos=-0.3 (rank-order OOS 完全失稳) + ls_t=-0.14 PnL flat + incr_ic=-0.001 库减值 — true_range/prev_close higher-moment 是 OOS 失稳形态 (Std 算子 20d 在多 regime 失稳, b051 C006 sign_flip 教训 60d 版本, 本候选 20d 版本 mono 失稳是同律的轻度版本) | [[batches/batch_053/candidates/C004]] |
| C005 | ❌ reject | 🟢·🟢·🔴·🔴·🟢 | ic_oos=-0.049 ls_t=-4.73 mono=-0.9/-1.0 ls_Sharpe=-3.41 alpha_surv=0.53 **max_corr=-0.692@F012 incr=-0.020** 5 因子 cluster -0.55+ | rank-order 真实 + 9 年同号 + ls 强；但与 C003 平行 — RHS Amihud_60 与 F012 Amihud_20 同 atomic 不同窗口 anchored cluster；进一步 5 个 rank-diff 因子 (F002/F012/F015/F016/F018) 都 -0.55+ — 整 rank-diff 家族对 Amihud RHS 形成共振簇 — 库内独立性丧失 | [[batches/batch_053/candidates/C005]] |
| C006 | ❌ reject | 🔴·🔴·🔴·🟡·🟠 | ic_oos=-0.014 ls_t=+0.84 mono=-0.3/+0.3 alpha_surv=**0.17** max_corr=-0.469@F004 | mono_is=-0.3 弱 + mono_oos=+0.3 反号 (近 hard_gate mono_sign_flip 但都 <0.5 阈值未触) + alpha_surv=0.17 严重 vol_20d 吸收 (style_r²=0.37 + vol_20d=53.6 极重) — 信号无 rank-order 结构, ls_t=+0.84 与 mono_is 反号 (-0.3 mono 但 ls 正) 显示日内 ret Std × RV_60 是 vol_20d structural noise 的复刻 | [[batches/batch_053/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色。

## 跨候选对比

**LHS 多元化结构 (本批 6 LHS 全唯一)**:
- C001: `Std((close-open)/(high-low), 20)` — signed body-position higher moment (区别于 F019 Abs(body_disp) Std)
- C002: `Mean((close - OHLC4_mean)/(high-low), 20)` — VWAP-proxy 4-field mean deviation (hard_gate fail)
- C003: `Mean((high-low)/prev_close, 20)` — true_range/prev_close level
- C004: `Std((high-low)/prev_close, 20)` — true_range/prev_close higher moment
- C005: `Mean((close-open)/close, 20)` — signed intraday return level
- C006: `Std((close-open)/close, 20)` — signed intraday return higher moment

**RHS 多元化结构**:
- C001/C003/C005: `Mean(|ret|, 60)` 或 `Mean(Amihud, 60)` Amihud-numerator/denominator family 长窗
- C002: `Std/Mean amount, 60` amount_cv 长窗
- C004/C006: `Mean(Std($close,5), 60)` RV_60 (b051 admit C002 同款)

**关键失败模式分类**:

1. **F020 anti-anchor cluster (C001 例)**: F020 = `Sub(CsRank(Std(gap_ret,20)), CsRank(Mean(body_disp,20)))`，C001 = `Sub(CsRank(Std(body_pos,20)), CsRank(Mean(|ret|,60)))` — LHS 都是 intraday OHLC higher-moment，但因 CsRank Sub 算子是反对称的 + LHS 同源 + RHS 不同 → 形成 ρ=-0.694 强反向 cluster。**新律候选**：rank-diff 几何中 LHS atomic 同源会形成跨候选 anti-cluster，admit 一个就锁死同源 LHS 的整片几何空间。

2. **F012 anchored RHS cluster (C003 + C005 双例)**: F012 = Amihud_20。本批 C003/C005 都用 Amihud-numerator 长窗 60d 作 RHS → 都被 F012 反向 cluster -0.69~-0.73。**新律候选**: 同 atomic 不同窗口 RHS 与同 atomic 因子形成强负向 cluster — RHS 共振饱和律的"窗口家族"扩展形态：饱和不仅是同窗口同 atom，是同 atom 整窗口家族。

3. **vol_20d structural absorption 在 intraday family 不可剥离 (C003 0.66 + C006 0.37 + C004 0.28)**: 三个 LHS (true_range vol/level, signed_ret Std) 都在 dominant_style=vol_20d high crowding。**rank-diff geometry 通过 CsRank 把 ordinal 化但 vol_20d 暴露在 LHS 字段层就已固化** — CsRank 不能剥离原子层的 style exposure。F019 admit (style_r²=0.23) 比本批 C003/C006 低很多，证 F019 LHS body_disp 比本批 LHS 在 vol_20d 上更轻量。

4. **OHLC algebraic mirror 在 OHLC4-mean 复现 (C002)**: 4-field arithmetic mean (O+H+L+C)/4 在 csi1000 上 ≈ close (4 字段中位数集中度高)，导致 (close - OHLC4_mean)/range ≈ 0 + 高频噪声。**升格教训**: OHLC algebraic mirror 律不仅在两字段反相关 (上影线 vs close/high)，多字段 arithmetic mean 也是同律的 degenerate 形态。

**与 b052 反思对照**:
- b052 揭示"基本面 higher-moment regime sign_flip" + "factor-anchored cluster RHS 动态律 (F002 anchor)" + "compound moment LHS over-fit"
- b053 在 OHLC family 揭示**结构对称形态**: F020 anti-anchor (LHS 同源) + F012 RHS 窗口家族 anchored cluster + vol_20d 不可剥离
- **rank-diff 范式两次连续中断 (b052 + b053) 共揭示 6 条新限制**: rank-diff 不是万能钥匙的边界正在迅速被定义清楚。Phase 5 consolidation 升格 lessons.md 的硬证据进一步累积。

**Style 聚合**: 6 候选 dominant_style 全 vol_20d。**intraday OHLC family 天然 vol_20d 重暴露 — 与 b051 C001/C002 不同 (gap_ret 是 intraday-overnight 边界, vol_20d 暴露轻**)。

**MT 预算**: direction_candidates 16 → 22, 远低于 70 上限。本方向 5 轮 (含本批) 仅 2 admit + 0 reserve (本批 reserve 为方向首个), MT 预算空闲不构成放宽阈值依据。

## Calibration Check (Phase 3.5)

四个 calibration trigger 检查:

1. ❌ **错杀 flag**: C001 是本批最强候选, max_corr=-0.694@F020 + incr_ic=0.0096 + alpha_surv=0.37 — 三 borderline 叠加, 不满足"max_corr<0.30 + incr_ic>0.010 + mono\|·\|>0.8 + sign_consistency=1.0 + reject_reason 单一指标"完整错杀 signature。reserve 是合理处置而非错杀。
2. ❌ **连续零 admit**: 本方向 b010 admit=1, b011 admit=0, b053 admit=0 → 中间无其他本方向 batch, 直接连续 admit=0 仅 2 次 (b011 + b053), 未达 3 次硬触发。
3. ❌ **Reserve 积压**: 本方向累计 reserve = 1 (本批 C001) / judged 22 = 4.5% << 40%。
4. ❌ **悖论复现**: 本批 C003/C005 alpha_surv=0.36/0.53 相对 ls_t=-4.27/-4.73 强信号"低 alpha_surv + 强 ls" 是 b051 升格律 "Barra-clean ≠ library-clean" 的负向版本 (本批是 Barra-脏 + library 也脏), 不构成新悖论。

→ **calibration_trigger = false**。本批结果是真实"信号有但被 F020/F012 cluster 锁死 + vol_20d structural absorption", 不是"阈值过严"。Phase 4 archive 正常进行。

## Thread 进展

> [!failure]+ T003 [[directions/intraday_price_formation#T003]] — `[✗ DISPROVEN batch_053]`
> rank-diff geometry × intraday family 第 7 次跨家族泛化 **失败**。本批 6 候选完整投放后揭示三条独立机制：
>
> 1. **F020 anti-anchor cluster** (C001): 同源 LHS atomic 在 rank-diff 中形成跨候选 anti-cluster, admit 一个锁死同源几何整片
> 2. **F012 anchored RHS 窗口家族 cluster** (C003 + C005): Amihud_20 与 Amihud-numerator_60 跨 atomic-family 而非仅同窗口的 RHS 共振饱和律
> 3. **vol_20d 在 intraday OHLC family 不可剥离** (C003 0.66 + C006 0.37): CsRank ordinal-化无法剥离 LHS 字段层固化的 style exposure
>
> **结论**: rank-diff geometry 不是万能。intraday_price_formation 在 OHLC scale-invariant atom 几何空间已穷尽 (b011 标 saturated 时是 raw level Mean 死区, b053 现在 rank-diff geometry 同 family 死区)。下次再开本方向需 (a) Python residual 路径剥离 vol_20d 暴露 / (b) 引入 minute-bar / tick 数据 / (c) 与 fundamental-momentum 全新 family 复合。

## 跨方向元教训 (Phase 5 consolidation 候选)

3 条新教训等待 Phase 5 升格 lessons.md:

1. **"rank-diff anti-anchor 律: LHS atomic 同源会形成跨候选 anti-cluster, admit 一个锁死同源几何整片"** — F020 anti-anchor 在 C001 复现 (max_corr=-0.694)。**candidate to promote** → lessons.md "factor-anchored cluster RHS 动态律" 扩展为 "factor-anchored anti-cluster LHS 律"
2. **"RHS 共振饱和律的窗口家族扩展: 同 atom 整窗口家族 (Amihud_20 vs Amihud_60) 形成强负向 cluster, 不仅同窗口同 atom"** — C003/C005 双例验证。**candidate to promote** → lessons.md RHS 共振饱和律修订
3. **"OHLC algebraic mirror 律的 multi-field 形态: 4-field arithmetic mean 在 csi1000 ≈ close, mean-deviation/range ≈ 0 + noise"** — C002 hard_gate quad-fail 验证。**candidate to promote** → lessons.md OHLC mirror 律扩展

下批建议 (next_hint): zero_admit_streak=2 + rounds_since_consolidation=9 (硬触发 10 还差 1)。下批走 rank-diff 在 ohlc_temporal_aggregation/microstructure_illiquidity 这两 productive direction 的"延伸 admit" 路径 (避开本批揭示的 F020 anti-anchor + F012 RHS 窗口家族 cluster), 或新探索 vwap_proxy_signals 的横向延伸 (F014 仍 D 档, 该方向有空间)。Phase 5 consolidation 已逼近硬触发, 下下批建议主动 trigger.
