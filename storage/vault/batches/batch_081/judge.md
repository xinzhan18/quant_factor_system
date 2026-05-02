---
batch_id: batch_081
direction: ohlc_temporal_aggregation
judged_at: 2026-05-02T15:00:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: high
---

# batch_081 Judge Summary

> [!abstract]+ batch_081 · [[directions/ohlc_temporal_aggregation]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=1** (C006 P008 TsRank-escape 路径首例机制验证) · ❌ **reject=5**
> **核心发现**: T012 第三轮 — **5/6 reject 中 4 个为 P006 library-reducer hard-block 同律（max_corr≥0.40 + incr_ic≤0 + alpha_surv≤0.30）**；ohlc_temporal_aggregation 60d-window 长尾**机制层面饱和**于库内已 admitted F018/F021/F012 cluster。但 C006 **P008 TsRank ratio-field≥60d escape 路径首次机制验证**（alpha_survival=0.993 ≈ 1.0 = Barra 空间独立载体）— 虽 incr_ic=-0.035 强负不达 admit，但保留 reserve 等待 P008 复现。
> **MT Budget**: cumulative 444 → **450** · direction 34 → **40**（继续接近 70 cap）· bucket `high`（search_adjusted `medium`）· 本批 high=5（除 C002 hard_gate）
> **zero_admit_streak**: 4 → **5**（b063/b076/b079/b080/b081 五批连续）· **consolidation_trigger=true**（rounds_since=8→9，下批继续 zero_admit 即超 10 上限）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟡·🔴·🔴·🔴·🟡 | IC=-0.061 ls_t=-2.12 max_corr=0.68@F021 incr_ic=-0.013 | hl_norm_sym 60d Mean 与 F021 RHS Mean(H/L,60) 数学同构；vol_20d=47.81 整库罕见 → b063 "atom 即 realized vol proxy" 教训复现 | [[batches/batch_081/candidates/C001]] |
| C002 | ❌ reject | hard_gate | ic_oos=-0.0041 < 0.008 | Skew(body_ratio,60) 3 阶矩在 60d 窗口下 OOS IC 不达显著性下限；机制方向 OK 但统计显著性不足（mono_oos=-1.0 vs alpha_surv=1.32 vol_clean） | [[batches/batch_081/candidates/C002]] |
| C003 | ❌ reject | 🟡·🔴·🔴·🔴·🟡 | ls_t=-0.20 max_corr=0.61@F012 incr_ic=-0.006 alpha_surv=0.078 | num_trades RHS 实证与 turnover/F012 流动性 cluster 同源；alpha_surv=0.078 critical poor + IS/OOS 单调性符号翻转 + ic_by_year 2017 跨样本符号翻转 | [[batches/batch_081/candidates/C003]] |
| C004 | ❌ reject | 🟡·🟠·🔴·🟡·🟡 | IC=-0.042 ls_t=-3.36 max_corr=0.39@F018 incr_ic=-0.014 | co_norm_sym 60d Mean = sustained directional drift，与 F018 overnight_sign 同源（institutional accumulation drift）；功能性 P006 库减项（max_corr 0.385 接近 0.40 边界但负 incr_ic 强 + low alpha_surv） | [[batches/batch_081/candidates/C004]] |
| C005 | ❌ reject | 🟡·🟠·🔴·🔴·🟢 | ls_t=+3.47 mono=+1.0 max_corr=0.58@F012 alpha_surv=0.07 | rank-diff Skew(body_ratio,60) × amount_60 — 时序稳健性极佳（cum_ic_mdd=-2.0 + 9/9 yr 同号增强 + mono=+1.0 完美单调）但 alpha_surv=0.07 critical + amount cluster halo + incr_ic=0.005 borderline 死区 | [[batches/batch_081/candidates/C005]] |
| C006 | ⏸ reserve | 🟢·🟠·🟢·🟡·🟡 | ICIR=-0.37 ls_t=-3.64 max_corr=0.27@F022 alpha_surv=0.99 incr_ic=-0.035 | **P008 TsRank ratio-field≥60d escape 首例机制验证**（alpha_survival≈1.0 = Barra 空间独立）+ max_corr=0.268 库内最干净；但 incr_ic=-0.035 整批最严重负 + mono_oos=-0.40 弱单调 + cum_ic_mdd=-108 极深 | [[batches/batch_081/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色。

## 跨候选对比

- **vol_20d 结构性吸收持续**（P004 律第 12 次跨方向命中）：C001 vol_20d=47.81 / C003=23.56 / C004=17.77 / C005=20.93——4/6 候选 vol_20d 暴露 ≥17（high cluster）。仅 **C006 vol_20d=12.56** 显著低（中等暴露），证 P008 TsRank ratio-field 60d escape 路径机制有效。
- **P006 library-reducer hard-block 集体触发**：C001/C003 严格满足三件套（max_corr≥0.40 + incr_ic≤0 + alpha_surv≤0.30）；C004/C005 功能性等价（max_corr 接近 0.40 + 强负或边界 incr_ic + low alpha_surv）。**5/6 候选实证 ohlc_temporal_aggregation 60d-window 长窗 Mean/Skew × cross-section RHS 范式于 F018/F021/F012 cluster 饱和**。
- **mean-reversion vs momentum 平衡**：cockpit 提示"库内多数为 momentum/dispersion，long-window mean-reversion 候选稀缺" — 本批 C001/C004/C006 三 candidate 设计 mean-reversion direction，2/3 验证机制方向 OK 但库已捕获该 alpha basis（仅 C006 部分逃逸）。
- **MT 预算推进**：direction_candidates 34 → **40**（vs cap 70）+6；cumulative 444 → 450 +6；search_adjusted 0.486 medium 维持。**direction 接近 cap 60% 警戒线**。
- **OHLC 时间聚合方向饱和度信号**：连续 5 批 zero_admit（b063/b076/b079/b080/b081）+ direction MT 接近 cap 60% + 仅 C006 reserve 存活——**方向已过其饱和点**，建议 status `productive → saturated` 转换。

## Thread 进展

> [!note]+ T012 [[directions/ohlc_temporal_aggregation#T012]] — `[◉ ACTIVE]`
> 本批延续 b063 教训：60d 长窗下 hl_norm_sym/co_norm_sym/num_trades_60/amount_60 RHS 全部被 F018/F021/F012 cluster 饱和。**第三件 next probes 路径"P008 TsRank ratio-field 60d"机制层面验证有效（C006 alpha_survival=0.993）但库增值不达**——保留 reserve 等待 P008 复现。下批应切方向（如 cockpit 提示的 alpha191_universal_subset / anchor_proximity_momentum / up_fraction_regime_gating 等 productive/exploring 方向），不再延伸 ohlc_temporal_aggregation 60d-window probe。

> [!note]+ T013: TsRank ratio-field own-history mean-reversion (P008 escape 路径) 🆕 — `[◉ ACTIVE]`
> 承接 C006 P008 escape 机制验证。**Question**: TsRank window≥60d on bounded scale-free OHLC ratios (hl_norm_sym, body_ratio, range/prev_close) 是否构成可复现的 vol_20d-escape 路径并产生 admittable alpha？C006 单例验证机制可行（alpha_survival=0.993 ≈ 1.0）但库增值不达（incr_ic=-0.035）。下批可在跨方向（非 ohlc_temporal_aggregation）测 P008 escape 在其他 ratio atom 复现性。

## 方向级反思

**本方向 edge 已饱和于已 admitted F018/F021/F012 cluster**：
- T012 next probes (1) F019/F020 atom Skew/Kurt: 本批 C002 (Skew body_ratio,60) hard_gate fail + C005 (rank-diff Skew × amount_60) alpha_surv=0.07 critical = **路径 (1) 实证不可行**
- T012 next probes (2) F008 upper_shadow 3d Skew: 未触（已知 F006/F021 cluster）
- 60d Mean/Skew × cross-section RHS 范式整体饱和

**降档建议**：`status: productive → saturated`（连续 5 批 zero_admit，direction MT 40/70 = 57% cap）；priority 维持 `low`（cockpit 已建议转 productive 方向）。

**P008 TsRank escape 路径单独标记**：C006 是 ohlc_temporal_aggregation 方向饱和后的"逃逸窗口验证"——alpha_survival=0.993 是 P008 lessons.md 升格价值。但需在跨方向（如 anchor_proximity_momentum / range_structure）复现 TsRank ratio-field 60d 机制再裁决是否升格 admit-eligible 路径。

**下轮建议**：转 cockpit 推荐的 productive 方向（alpha191_universal_subset / anchor_proximity_momentum / up_fraction_regime_gating），ohlc_temporal_aggregation 暂停。consolidation_trigger=true（rounds=8→9，下批继续 zero_admit 必触 10 上限）。
