---
batch_id: batch_017
direction: ohlc_temporal_aggregation
judged_at: 2026-04-21T02:30:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: admit, factor_name: upper_shadow_persistence_5d}
batch_summary: {total: 5, admit: 1, reserve: 1, reject: 3}
admit_count: 1
reject_count: 3
reserve_count: 1
candidate_count: 5
mt_bucket: low
---

# batch_017 Judge Summary

> [!abstract]+ batch_017 · [[directions/ohlc_temporal_aggregation]] · 5 candidates (direction 首批)
> ✅ **admit=1** (C005 → upper_shadow_persistence_5d) · ⏸ **reserve=1** (C003 bullish-freq) · ❌ **reject=3** (C001 C002 C004)
> **核心发现**: **方向假设验证成立** —— 5 日聚合 OHLC patterns 在 close-strength 维度（C005 upper-shadow / C004 close/high）携带**真正独立的 alpha**（与单日 saturated 形成对比）。**关键判别**：alpha_survival 区分"独立载体"（C005=1.508 ✓）vs "vol_20d 镜像"（C004=0.003 ✗）——这是方向首次出现 Barra-clean 信号。**4 轮以来首个 admit！**
> **MT Budget**: cumulative 87 → **92** · direction 0 → **5**（首批） · bucket `low`

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟢·🟢·🟡·🟡·🟠 | ic=-0.043 ls_t=-2.87 incr_ic=-0.050 cum_dd=-105 | 5d signed body：CP03 强但 incr_ic 负 + cum_dd 整库最深 | [[batches/batch_017/candidates/C001]] |
| C002 | ❌ reject | 🟢·🟢·🔴·🟡·🟡 | ic=-0.042 r²=0.638 ls_t=-2.62 | 20d body：longer window 加深 vol_20d 耦合（r² 0.234→0.638） | [[batches/batch_017/candidates/C002]] |
| C003 | ⏸ reserve | 🟢·🟢·🟢·🟡·🟡 | ic=-0.033 ls_t=-3.55 mono=-0.80 alpha_surv=1.014 incr_ic=-0.031 | sign-frequency：CP02-04 完美但 incr_ic 负；与 C005 mirror | [[batches/batch_017/candidates/C003]] |
| C004 | ❌ reject | 🟢·🔴·🔴·🟢·🟡 | ic=+0.052 mono=+0.9 alpha_surv=0.003 ls_t=1.91 | close/high：alpha_surv=0.003 → 本质 vol_20d 衍生；ls_t<2 | [[batches/batch_017/candidates/C004]] |
| C005 | ✅ **admit** | 🟢·🟡·🟡·🟢·🟡 | ic=+0.024 ls_t=3.20 mono=+0.90 alpha_surv=1.508 incr_ic=+0.031 cum_dd=-3.5 | 5d upper-shadow：alpha_surv>1 + incr_ic positive + cum_dd 整库最浅 | [[batches/batch_017/candidates/C005]] · [[factors/F006]] |

## 跨候选对比

- **方向核心机制确立**：5/5 候选 dom_style=vol_20d，但 alpha_survival 分布**两极化**：
  - 独立 alpha 区：C005 (1.508) / C001 (1.076) / C003 (1.014) — residual IC 等于或强于 raw
  - vol-derived 区：C004 (0.003) / C002 (0.657)
  - **alpha_survival 是关键判别量**：r² 高（vol 共线）但 alpha_surv > 1 = "Barra 空间正交载体"，与 r²/alpha_surv 双低的"vol 衍生"完全不同。这是该方向首次系统性观察。
- **C003 vs C005 镜像对**：同为 5d-aggregation reversal 信号但符号互补：
  - C005 ic=+0.024 (持续抛压 → 反转上涨)
  - C003 ic=-0.033 (持续买盘 → 反转下跌)
  - 两者 max_lib_corr 都 < 0.13，alpha_surv > 1.0 都干净；区别仅在 incr_ic 符号（C005+/C003-）
  - 下批可探索 C005 - C003 长短组合（symmetric reversal index）
- **窗口长度敏感性**：C001 (5d body) r²=0.234 vs C002 (20d body) r²=0.638——**longer aggregation 加深 vol_20d 耦合**。短窗（5d）保留更多 idiosyncratic flow，长窗（20d）平滑掉非 vol 部分。**5d 是当前数据上的 sweet spot**。
- **alpha_survival vs incremental_ic 不对齐**：C004 alpha_surv=0.003 (vol 衍生) 但 incr_ic=+0.034 (库 adder)；C003 alpha_surv=1.014 (clean) 但 incr_ic=-0.031 (库 reducer)。**两个指标测度不同维度**：alpha_surv = "Barra 空间内的独立性"；incremental_ic = "与 admitted library 的方向匹配"。C005 难得地 BOTH positive (alpha_surv=1.508 + incr_ic=+0.031)。
- **MT 预算**：cumulative 92, direction 5 (首批)，bucket low。

## Thread 进展

> [!success]+ T001 [[directions/ohlc_temporal_aggregation#T001]] — `[✓ ANSWERED batch_017]`
> 5d/20d signed body：5d (C001) Barra-clean (alpha_surv=1.076) 但 incr_ic 负 库 reducer；20d (C002) vol-coupling 严重 reject。**Hypothesis "smoothed body 携带 persistent flow" 部分成立**——5d 窗口确实保留 idiosyncratic 信号，但与库 F003 同向冲突。

> [!success]+ T002 [[directions/ohlc_temporal_aggregation#T002]] — `[◉ ACTIVE]`
> Sign-of-body 频率（C003）CP02-04 完美 + mono=-0.80 + alpha_surv=1.014——证明 discrete sign 信号在 5d 窗口确实独立于 vol_20d；但 incr_ic 负仍 reserve。

> [!success]+ T003 [[directions/ohlc_temporal_aggregation#T003]] — `[✓ ANSWERED batch_017]`
> Close-vs-high 强度（C004 close/high + C005 upper-shadow）双探：C004 alpha_surv=0.003 vol-derived reject；**C005 alpha_surv=1.508 + incr_ic=+0.031 → 方向首 admit**。**Hypothesis "持续 close near high 携带 demand 信号" 完整验证成立**：C005 upper-shadow 形式（高 upper-shadow = 持续抛压 → forward 反转上涨）是该 hypothesis 的成功载体。

## 方向级反思

batch_017 是 ohlc_temporal_aggregation **首批即 admit**——4 轮 0-admit 之后的关键突破。

**核心元发现（系统层级）**：
1. **alpha_survival 是新关键判别量**：4 轮以来累计 18 reject 中 8 个被错过的"vol_20d 衍生" pattern（high mono + clean style + low cum_dd 但 alpha_surv 接近 0）暴露——本批 C004 vs C005 的对照组首次系统性区分了"Barra 空间独立载体"vs "vol 衍生 monotone"。**C005 admit 的核心证据是 alpha_survival=1.508**，不是 ls_t 也不是 mono。
2. **5d aggregation 是 sweet spot**：单日 (intraday_price_formation 全 saturated) ↔ 20d (本批 C002 vol-coupled) 之间的 **5d** 窗口是 OHLC 信号"既保留 idiosyncratic 又过滤噪声"的 sweet spot。后续 OHLC 探索默认从 5d 开始，再 ablate。
3. **upper-shadow 机制独立性**：C005 (high - close) / (high - low) 在 5d mean 下 max_corr=0.069 with F003 (overnight gap) — 完全机制正交，是 OHLC pattern 空间的**真正新维度**，不是已 saturated 信号的微调。

**Calibration trigger 检查**:
- 错杀 flag = 0 ✓
- 连续零 admit 已被 batch_017 admit 中止 ✓
- Reserve 积压：cumulative 92 / 累计 reserve ~14 = 15% < 40% ✓
- 悖论复现 = 无 ✓

**下批决策（batch_018）**：
1. **优先**: 同方向继续 deepen — 5d 窗口的 OHLC pattern 变体（lower-shadow / body-position-in-range / signed body × range / 跨日 body 一致性）。**目标**: 在 ohlc_temporal_aggregation 内再产 1-2 个 admit，或显式饱和该 5d 窗口。
2. **次选**: C003 (sign-frequency reserve) + C005 (admit) symmetric-pair design — 5d frequency-asymmetry 信号
3. **观察**: 该方向是否 escape 了"vol_20d 主导陷阱"——C005 是首个 admitted factor 同时 dom=vol_20d **AND** alpha_surv > 1.0 + incr_ic > 0，是方向是否能持续产 admit 的关键指标
