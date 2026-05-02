---
batch_id: batch_080
direction: overnight_intraday_split
judged_at: 2026-05-02T08:30:00Z
candidates:
  - {candidate_id: C001, verdict: reject, thread_id: T011}
  - {candidate_id: C002, verdict: reject, thread_id: T011}
  - {candidate_id: C003, verdict: reject, thread_id: T011}
  - {candidate_id: C004, verdict: reject, thread_id: T011}
  - {candidate_id: C005, verdict: reject, thread_id: T011}
  - {candidate_id: C006, verdict: reserve, thread_id: T011}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reserve_count: 1
reject_count: 5
candidate_count: 6
mt_bucket: medium
mt_bucket_breakdown:
  cumulative_score: 0.918
  direction_score: 0.918
  exposure_score: 1.0
  raw_score: 0.926
  bucket: high
  search_adjusted_bucket: medium
---

# batch_080 Judge — overnight_intraday_split T011 axis 6 fresh-atom 全失败 + 1 reserve borderline

> [!warning]+ batch_080 · [[directions/overnight_intraday_split]] · 6 candidates (round 80, zero_admit_streak 3→4)
> ❌ **admit=0** · ⏸ **reserve=1** (C006) · ❌ **reject=5** (C001/C002/C003/C004/C005)
> **核心发现**: T011 (magnitude-weighted product) 扩展轴 6 个 fresh atom geometries 全部受阻 — (a) overnight × volume_delta 短窗 (C001) sign_flip catastrophic (volume rate-of-change 触发 Forbidden Patterns 升格律实证); (b) abs(overnight) × turnover 20d (C002) 9/9 年负向 sign-stable + mono=-0.9 完美但 alpha_surv=0.27 vol_20d-locked + RHS pcf_total_ttm 撞 P010 macro 真饱和; (c) overnight × intraday range (C003) ic_oos=-0.0084 weak ls_t=0.14 essentially zero — range vs body 几何无显著差异; (d) overnight × Sign(intraday) 60d (C004) ic_oos=0.0066 < 0.008 floor — 60d 长窗 sign-asymmetric 在 csi1000 1d primary horizon noise-bound (T011 b059 b066 同律重现); (e) overnight 短-长加速 Mean_5-Mean_20 (C005) ls_t=3.62 + mono=1.0 完美但 **alpha_surv=0.143 critical** — 同字段跨窗差是 vol_20d 二阶载体; (f) **overnight × turnover 60d (C006)** 是本批唯一火种 ic_oos=0.0295 + ls_t=4.06 + 9/9 年同号 + mono=0.9 + alpha_surv=0.61 PASS + cum_ic_mdd=-1.37 极浅但 max_corr=0.56@F018 borderline + **incr_ic=0.0098 < 0.015 F203 borderline gate** + F002/F012/F018/F023 四 anchor 0.40-0.56 cluster 多重压制 → **reserve** (T011 60d window 是 b059 20d admit 的镜像延伸,但库内 4 anchor cluster 占据 cross-section 几何中心,新候选 incr_ic 不达 borderline 闸).
> **MT Budget**: cumulative 438 → 444 · direction 45 → 51 · bucket `medium` (raw=high direction.exposure=1.0 满 + family=0.918 高位 + cumulative=0.918, search_adjusted ≈ 0.30 → low/medium)
> **direction status**: T011 axis (本方向唯一未 disprove thread) **6 fresh atom 0/6 admit** — T011 ANSWERED-bounded 已扩展为 ANSWERED-saturated. zero_admit_streak 3→4. rounds_since_consolidation 7→8 接近 10 阈值. 本方向 9 admit 历史 + T017 reserve + C006 reserve = 2 火种 — **不 dead 但 saturated** (双层 saturated 证据律: 6 closed thread + T011 fresh atom 全失败). 升格 saturated 候选 (Phase 4 archive 后由 Python auto-status 或下批 LLM 翻).

## 候选一览

| ID | Verdict | Thread | Expression | 档位 (HG·sign·ic_oos·alpha_surv·max_corr) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|---|---|
| C001 | ❌ reject | T011 | `Sub(CsRank(Mean(Mul(overnight, vol_pct_delta), 20)),CsRank(Mean($num_trades,60)))` | ❌·**flip**·sub-th·N/A·BORDER(0.57@F012) | ic_oos=-0.0033 sign_flip + decay=-5.16 catastrophic | volume rate-of-change 作 weight 触 Forbidden Patterns rate/delta default-skip — 即使 weight 形式仍失败 | [[batches/batch_080/candidates/C001]] |
| C002 | ❌ reject | T011 | `Sub(CsRank(Mean(Mul(\|overnight\|, $turnover_rate),20)),CsRank(Mean($pcf_total_ttm,60)))` | ✓·stable**NEG**·-0.040·0.27 FAIL·BORDER(0.46@F017) | ic_oos=-0.0405 mono=-0.9 ls_t=-2.57 9/9 年负 + cum_ic_mdd=-67.5 深 | 完美 negative-direction 但 alpha_surv<0.30 floor + RHS 撞 P010 macro 真饱和 | [[batches/batch_080/candidates/C002]] |
| C003 | ❌ reject | T011 | `Sub(CsRank(Mean(Mul(overnight, range/Ref(C,1)),20)),CsRank(Mean($dividend_yield_ttm,60)))` | ✓·stable·-0.008·0.35·LOW(0.28@F002) | ic_oos=-0.0084 ls_t=0.14 essentially zero mono=0.30 | overnight × range vs F023 overnight × body 几何同位,range carries broader vol but cross-section rank ≈ body | [[batches/batch_080/candidates/C003]] |
| C004 | ❌ reject | T011 | `Sub(CsRank(Mean(Mul(overnight, Sign(intraday)),60)),CsRank(Mean($peg_ratio_ttm,60)))` | ❌·stable·sub-th·0.43 PASS·LOW(0.18@?) | ic_oos=0.0066 < 0.008 floor + ls_t=1.59 weak | 60d 长窗 sign-asymmetric daily 1d horizon noise-bound (T011 b059 horizon mismatch 复现) | [[batches/batch_080/candidates/C004]] |
| C005 | ❌ reject | T011 | `Sub(CsRank(Sub(Mean(overnight,5),Mean(overnight,20))),CsRank(Mean($num_trades,120)))` | ✓·stable·+0.020·**0.143 CRIT**·BORDER(0.56@F010) | ic_oos=+0.020 ls_t=3.62 mono=1.0 完美但 alpha_surv=0.143 + incr_ic=-0.003 | 短-长加速 Sub_inside_CsRank 是 vol_20d 二阶载体,P004 absorb + P006 reducer | [[batches/batch_080/candidates/C005]] |
| C006 | ⏸ reserve | T011 | `Sub(CsRank(Mean(Mul(overnight, $turnover_rate),60)),CsRank(Std($num_trades,60)))` | ✓·stable·+0.030·0.61 PASS·BORDER(0.56@F018) | ic_oos=0.0295 ls_t=4.06 mono=0.9 9/9 年正 + cum_ic_mdd=-1.37 浅 + worst_q=+0.012 永正 | 本批唯一火种 + 4 anchor cluster (F002 0.48 / F012 0.50 / F018 0.56 / F023 0.40) + incr_ic=0.0098<0.015 F203 borderline gate | [[batches/batch_080/candidates/C006]] |

**档位编码**: ✓ HG 通过 / ❌ HG 失败 / `stable` sign 同号 / `flip` sign 翻号 / `NEG` 负向 alpha / `sub-th` ic_oos<0.008 / `LOW` max_corr<0.30 几何独立 / `BORDER` ∈ [0.30, 0.70].

## Thread 进展

- **T011 (magnitude-weighted product 扩展)** `[◉ ACTIVE → ANSWERED-bounded → ANSWERED-saturated batch_080]`: 6 fresh atom geometries (overnight × {volume_delta, |.| × turnover, intraday range, Sign(intraday), 短-长 Sub_inside_CsRank, turnover 60d}) 全部受阻. 仅 C006 (60d turnover-weighted overnight) 进入 reserve — incr_ic=0.0098 距 F203 0.015 borderline gate 缺口 ~33%. **关键发现**: T011 b059 admit (gap × body 20d × amount_60) → b066 long-window 测试 reserve (Corr_atom) → b080 6 fresh atom 全失败. **T011 axis exhaustion** — magnitude-product family 在 csi1000 daily-bar cross-section 上仅 (overnight × intraday body) 一种 admitted geometry,其他 OHLCV / 加速度 / sign-asymmetric / range / volume_delta 变体均被 vol_20d basis 吸收或 cross-section noise-bound.
- **T017 (Corr atom)** 状态保持 [◉ ACTIVE 1 reserve C005 b066]: 本批未触.

## 跨候选对比 — T011 fresh atom 系统性失败

### 子族 1: overnight × X magnitude product 短窗 20d (C001/C002/C003)

| 候选 | 表达式 LHS | RHS | ic_oos | alpha_surv | mono_oos | 失败模式 |
|---|---|---|---|---|---|---|
| C001 | overnight × volume_pct_delta | num_trades_60 | -0.0033 sign_flip | 0.065 | 0.30 | volume rate-of-change 触 Forbidden Patterns + RHS 撞 |
| C002 | abs(overnight) × turnover | pcf_total_ttm_60 | **-0.0405** strong NEG | 0.27 FAIL | -0.90 完美 | abs() 退化为 vol-magnitude 载体,9/9 年负 stable + RHS 撞 P010 macro |
| C003 | overnight × intraday range | dividend_yield_60 | -0.0084 weak | 0.35 PASS | 0.30 | range vs body cross-section rank ≈ same几何,signal noise-collapsed |

**模式**: 20d 短窗 magnitude-product 即使 RHS 全部 fresh fundamental TTM (4 个 untouched endpoints) 仍 alpha 不显著或 alpha_surv 不足. **机理**: LHS magnitude-product 在 csi1000 cross-section 上的 cross-section ordering 主要由 vol_20d 共线驱动,cross-section ordering 在 magnitude side 已穷竭 (F023 已占据 gap × body 几何),其他 magnitude weighting (volume_delta / abs() / intraday range) 在 cross-section rank 上与 F023 高度同构.

### 子族 2: overnight × X 长窗 60d (C004/C006)

| 候选 | 表达式 LHS | RHS | ic_oos | alpha_surv | ls_t_oos | 关键差异 |
|---|---|---|---|---|---|---|
| C004 | overnight × Sign(intraday) | peg_ratio_60 | 0.0066 sub-th | 0.43 PASS | 1.59 weak | 60d 长窗 sign-asymmetric daily 1d horizon noise-bound |
| C006 | **overnight × turnover_rate** | Std(num_trades,60) | **+0.0295** | **0.61 PASS** | **4.06** | 60d turnover-weighted overnight 是本批唯一火种, 4 anchor cluster |

**关键对比**: C004 (sign-asymmetric) vs C006 (level turnover-weighted) — sign-side 抑制信号强度 (0.0066 vs 0.0295 ~4.5×差距), 与 b059 C003 sign-product 60d horizon noise-bound 同律. **level magnitude-weight (turnover) > sign-asymmetric** 在 60d 长窗下信噪比优势同 b059 b066 长窗 sign vs magnitude 律.

### 子族 3: 同字段跨窗加速 Sub_inside_CsRank (C005)

C005 `Sub(CsRank(Sub(Mean(overnight,5),Mean(overnight,20))),CsRank(Mean($num_trades,120)))` — 关键设计: Sub 在 CsRank **内部** 不违反 Rank-Diff 7-rule constraint #3 (该律仅禁 Sub(CsRank(X_5),CsRank(X_20)) 外部跨窗 rank-diff). LHS = overnight 短-长加速度. ic_oos=+0.020 ls_t=3.62 mono_oos=1.0 表面强但 **alpha_surv=0.143 critical** + incr_ic=-0.003 P006 reducer. **机理**: overnight 短长 Sub 加速度仍 monotone-equivalent vol_20d (high-vol stocks 短期 overnight extreme 远超长期 mean → 加速度 cross-section rank 与 vol_20d rank 共变 ≈ 与 F010 corr=0.56 borderline). **新升格 lessons 候选**: "Sub_inside_CsRank 加速度形式 cross-section rank 仍 vol_20d-locked, 与 b066 T015 形状 moment 同律 — 同字段不同窗口的代数差也属于 vol_20d basis 二阶载体".

## 跨方向对照与机理

### T011 axis exhaustion 律 (本方向唯一未 disprove thread 也 saturated)

T011 axis 历史 admit 路径:
- **b059 admit**: `Mean((O-Ref(C,1))×(C-O), 20)` × Mean($amount,60) → F023 gap×body magnitude product 20d (ic_oos=0.044 ls_t=4.89 mono=1.0 9/9 年正)
- **b066 reserve**: `Corr($volume, overnight_gap_raw, 20)` × Std($volume,60) → C005 Barra-clean reserve (alpha_surv=1.16 库内首 candidate Barra residual IC > raw IC, 但 max_corr=0.46 anchor cluster + ls_t=1.26 < 2 不投资)
- **b080 reserve**: `Mean(overnight × turnover_rate, 60)` × Std($num_trades,60) → C006 60d turnover-weighted overnight (ic_oos=0.030 ls_t=4.06 mono=0.9 9/9 年正 + cum_mdd=-1.37 浅 + worst_q 永正, 但 max_corr=0.56@F018 + incr_ic=0.0098<0.015 F203 borderline gate)
- **b080 fresh atom 5/6 reject**: 短窗 20d × {volume_delta, abs× turnover, intraday range} + 60d × {sign-asymmetric} + 加速度 5d-20d Sub.

**律**: T011 magnitude-weighted product 在 csi1000 daily-bar cross-section 上仅 (overnight × intraday body 短窗 + amount RHS) 一种几何能 admit,其他 weighting field / 窗口 / RHS 组合或被 vol_20d basis 吸收 (alpha_surv<0.30/0.40 floor) 或被 anchor cluster (F018/F023) 占据 (max_corr 0.46-0.56 borderline + incr_ic<0.015).

### "逃 vol_20d 必撞 anchor cluster" 几何困境再实证 (b066 律泛化)

- C006: alpha_surv=0.61 vol_20d_exp=27 + max_corr=0.56@F018 + incr_ic=0.0098 borderline → 既 vol_20d-locked 又 anchor cluster
- C005: alpha_surv=0.14 critical + max_corr=0.56@F010 → vol_20d 完全失守
- C002: alpha_surv=0.27 + max_corr=0.46@F017 → 双失守

**唯一突破方向**: T017 reserve (Barra-clean alpha_surv=1.16 + max_corr=0.46) — Barra-clean 路径但 ls_t<2 不投资,等 evaluation policy 调长 horizon (10d-20d).

### Forbidden Patterns 实证扩展 (C001 升格证据)

C001 `Mul(overnight_ret, volume_pct_delta)` 触发 lessons.md "Rate / delta / ratio / sign-conditional / Cov 形式 default-skip" 律 — 即使 volume_delta 作为 weight (而非 standalone) 仍 sign_flip catastrophic (decay=-5.16 极端). **机理**: volume rate-of-change cross-section 上 noise-dominated, 用作 weight 让 overnight signal 被 noise 主导. 升格 lessons 候选: "rate/delta 形式作为 weight 也 default-skip, 与 standalone 形式同律".

## 升格候选

### Lessons 升格候选 (b080 实证)

1. **T011 axis exhaustion 律** (新升格): "magnitude-weighted product (overnight × X) 在 csi1000 daily-bar cross-section 上仅 (overnight × intraday body 短窗 20d × amount_60 RHS) 一种几何 admitted (F023). 其他 weighting field (volume_delta / abs() / intraday range / turnover_rate / num_trades / Sign(intraday)) / 窗口 (20d / 60d / 加速度 5-20) / RHS 组合 在 b080 6 fresh atom 全失败 (1 reserve incr_ic=0.0098 borderline). T011 axis 已结构性饱和, 不投同形式候选."
2. **Sub_inside_CsRank 加速度 vol_20d-locked 律** (b080 C005 实证): "同字段不同窗口的代数差 (Mean_5 - Mean_20) 即使在 CsRank 内部不违反 Rank-Diff constraint #3, cross-section rank 仍 monotone-equivalent vol_20d basis (alpha_surv=0.14 critical + max_corr=0.56@F010 双立). 与 b066 T015 形状 moment / b066 T014 autocorr atom 同律 — 加速度也是 vol_20d 二阶载体."
3. **Forbidden Patterns rate/delta 作 weight 同律** (b080 C001 实证): "rate/delta 形式 (volume_pct_delta) 作 weight 也 default-skip, 与 standalone 形式同律. 即使 weight 形式 cross-section 上 noise-dominated, 让 overnight signal 被 noise 主导导致 sign_flip catastrophic (decay=-5.16 b080 C001)."

## Operations

direction `productive` 保持但显著 saturated 化 (Phase 4 archive 后建议下批 LLM 翻 saturated):
- T011 `[◉ ACTIVE → ANSWERED-saturated batch_080]`: 唯一未 disprove thread 也已 saturated, 仅 C006 reserve 火种.
- T017 `[◉ ACTIVE]` 保持 (1 reserve C005 b066 unchanged).

zero_admit_streak 3 → 4. rounds_since_last_consolidation 7 → 8 (距 10 阈值 2 批). **临近 consolidation trigger** — 若下 2 批仍 zero_admit (本方向或跨方向), 应优先触 consolidation (lessons 升格 T011 axis exhaustion + Sub_inside_CsRank vol_20d-locked + Forbidden Patterns rate/delta weight 同律).

**Calibration trigger 检查**:
- 错杀 flag: 本批无 (C006 reserve 是合理 borderline 决策, 不是错杀)
- 连续零 admit 警戒: 4 批累计 admit=0 (b066/b079/b080 + 1 跨方向待查) — **接近警戒线**, 需检查 reserve pool: T017 b066 C005 (alpha_surv=1.16 max_corr=0.46) + b080 C006 (alpha_surv=0.61 max_corr=0.56 incr_ic=0.0098) — **不满足完整错杀 signature** (max_corr<0.30 + incr_ic>0.010 + mono>0.8 + sign_consistency=1.0 五条件): C006 max_corr=0.56 borderline + incr_ic=0.0098<0.010
- Reserve 积压: 累计 reserve/judged 比例需查询全局 (本批 reserve/judged=1/6=17%, 单批不触 40% 警戒)
- 悖论复现: T011 axis 未提供 paradox signature

→ **calibration_trigger=false** (本批 reserve 是合理 borderline 决策, 不是 over-rejection).

**MT budget**: cumulative 438 → 444 · direction 45 → 51 · bucket `medium` (raw=high direction.exposure=1.0 满 + family=0.918 高位, search_adjusted ≈ 0.30 → low/medium).

Phase 4 archive 后 commit message: `[mine] batch_080 | overnight_intraday_split | admits=0 reserves=1 rejects=5`
