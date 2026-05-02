---
batch_id: batch_073
direction: tsrank_timeseries_ratio
judged_at: 2026-05-02T05:00:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: admit, factor_name: trade_density_tsrank_60}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 1, reserve: 0, reject: 5}
admit_count: 1
reject_count: 5
reserve_count: 0
candidate_count: 6
mt_bucket: medium
---

# batch_073 Judge Summary

> [!success]+ batch_073 · [[directions/tsrank_timeseries_ratio]] · 6 candidates (NEW direction, frontier 直接续探)
> ✅ **admit=1** (C004 ⭐) · ⏸ reserve=0 · ❌ **reject=5**
> **核心发现**: T001-T006 frontier validation 续探 — **C004 trade_density TsRank60 全 CP green admit 验证 P008 frontier 真度 (ic_oos=+0.045 / ls_t=+9.08 / mono=+1.00 / alpha_surv=0.58 / style_r²=0.051 整批最低 / max_corr=0.13 整批最低 / incr_ic=+0.0085 POSITIVE)**, **frontier 部分生效 atom 类型律 (P012 升格候选)**: 仅当 ratio atom 自身已 dimensionless (counts per share / [0,1] body ratio) TsRank60 才完全脱 vol_20d basis (C001 amount/volume + C005 turnover/market_cap 含绝对量纲 → vol_20d_exp 11-17 偏高 + alpha_surv 0.24/0.91 边缘); **window 参数曲线 (P013 升格候选)**: C002 60d vs C006 120d 直接对照, 60d **优于** 120d (vol_20d_exp 12.6 vs 21.0 +66% 恶化, alpha_surv 0.99 vs 0.92), frontier 关键参数定锚 ≥60d 但 ≤90d. 终结 13 连零 admit streak. b072 C006 reserve 火种 → b073 C004 admit, frontier 真度铁证.
> **MT Budget**: cumulative 396 → 402 · direction 0 → 6 · bucket `medium`

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | aligned·borderline·**poor**·medium(F009)·stable | ic_oos=-0.040 ls_t=-2.66 mono=-1.00 alpha_surv=**0.24** sty_r²=**0.49** vol_20d_exp=11.1 max_corr=0.37@F009 incr=-0.016 | TsRank(amount/volume,60) VWAP proxy — alpha_surv=0.24 三立 FAIL + style_r²=0.49 极高 (poor 档) + dom=vol_20d 标准 P004 三立吸收. **frontier 真生效边界第一例失败实证**: ratio 含绝对价格 (amount/volume) → cross-section vol_20d 嵌入残留, 非所有 ratio 都享受 frontier 红利 | [[batches/batch_073/candidates/C001]] |
| C002 | ❌ reject | aligned·medium·**good**·low(F022)·stable | ic_oos=-0.037 ls_t=-3.43 mono=-1.00 alpha_surv=**0.99** sty_r²=**0.13** vol_20d_exp=12.6 max_corr=**0.27@F022 LOW** incr=**-0.034 strong NEG** | TsRank((H-L)/C,60) normalized range — frontier 真生效证实 (alpha_surv=0.99 + style_r²=0.13 极清洁 vol_20d 抗衡), 但 incr_ic=-0.034 强 NEG library reducer P008 触发. **frontier 真生效 ≠ admission**: 库已通过 F022 close_position 等几何复合预测此信号方向 | [[batches/batch_073/candidates/C002]] |
| C003 | ❌ reject | aligned·medium·**good**(整批最清洁)·medium(F008)·borderline | ic_oos=-0.036 ls_t=-3.30 mono=-1.00 alpha_surv=**1.14** sty_r²=**0.082** 整批最清洁 max_corr=0.37@F008 incr=**-0.032 strong NEG** ic_2015=+0.017 anomaly | TsRank((C-O)/(H-L),60) body_ratio — alpha_surv=1.14 + style_r²=0.082 整批最清洁 frontier 强证实, 但 incr_ic 强 NEG + max_corr 同 candlestick 几何 F008 重叠 + ic_2015 anomaly P011 ic_by_year sign-stable 红线触发 → reject. 设计预测最强但 admission 三立阻断 | [[batches/batch_073/candidates/C003]] |
| **C004** | ✅ **ADMIT** | **aligned·strong·good·low(F001)·stable** | **ic_oos=+0.045** ls_t=**+9.08** 整库顶级 mono=**+1.00** alpha_surv=**0.58** sty_r²=**0.051** 整批最低 vol_20d_exp=10.6 max_corr=**0.13@F001 LOW 整批最低** incr=**+0.0085 POSITIVE** | TsRank(num_trades/volume,60) trade_density retail attention proxy — **全 CP green**: ic_oos=+0.045 / ls_t=+9.08 整库顶级 / mono PERFECT POSITIVE / alpha_surv=0.58 PASS / style_r²=0.051 整批最低 / max_corr=0.13 整批最低 / **incr_ic=+0.0085 POSITIVE 真新 alpha 贡献** / ic_by_year 2018-2023 全 POS / train_val_decay=3.91 (val>>is). **frontier 真生效 atom 类型律实证**: dimensionless count ratio 是 frontier 真红利 atom. 与 b072 C006 mirror atom (分子分母互换), 信号方向也 mirror (+ vs -) | [[batches/batch_073/candidates/C004]] · [[factors/F024]] |
| C005 | ❌ reject | aligned·medium-strong·acceptable·medium(F022)·stable | ic_oos=-0.047 ls_t=-4.54 mono=-1.00 alpha_surv=**0.91** sty_r²=0.15 vol_20d_exp=**17.4** max_corr=**0.38@F022** incr=**-0.036 strong NEG** | TsRank(turnover/market_cap,60) — alpha_surv PASS 但 incr_ic 强 NEG + max_corr 0.38 + dom=vol_20d 三立. ratio 含 $market_cap 分母 → frontier 部分生效但不彻底 (vs C001 同律: ratio 含绝对量纲 vol_20d 嵌入残留). F022 已通过 amount accel + close_position 复合 turnover/cap 几何 | [[batches/batch_073/candidates/C005]] |
| C006 | ❌ reject | aligned·medium·acceptable·low(F022)·stable | ic_oos=-0.041 ls_t=-3.36 mono=-1.00 alpha_surv=**0.92** sty_r²=0.165 vol_20d_exp=**21.0** ⚠️(vs C002 60d 12.6 +66%) max_corr=0.27@F022 incr=**-0.035 strong NEG** | TsRank((H-L)/C,**120d**) — vs C002 60d 直接对照. **120d 反而 vol_20d_exp 升 66%** (12.6→21.0), alpha_surv 略降 (0.99→0.92), incr_ic 同强 NEG. **frontier window 参数曲线定锚 60d 是最优 mitigation 点**, 120d 引入额外 vol_20d 嵌入路径 (longer window samples 更多 vol cycle) | [[batches/batch_073/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色.

## 跨候选对比 — frontier 真度系统验证

**C004 admit 是 P008 frontier 完整真度铁证 (b072 C006 reserve 火种续探落地)**：

| 指标 | b072 C006 (reserve) | b073 C004 (ADMIT) | 跨批一致性 |
|---|---|---|---|
| atom | TsRank(amount/num_trades,60) avg_trade_size | TsRank(num_trades/volume,60) trade_density | mirror (分子分母互换) |
| ic_oos | -0.054 | **+0.045** | mirror (- vs +) |
| ls_t | -7.54 | **+9.08** 更强 | 同方向 mirror |
| alpha_surv | 0.45 | 0.58 | 都 PASS |
| style_r² | 0.15 | **0.051** 更低 | TsRank60-ratio 真生效 |
| vol_20d_exp | 10.87 | 10.63 | 极接近 (frontier sweet spot) |
| max_corr | 0.24 | **0.13** 更低 | 几何独立性更强 |
| incr_ic | -0.018 微 NEG | **+0.0085 POS** | C004 突破 incr_ic 阻断 |

**frontier 真生效 atom 类型律 (P012 升格候选)**:
- ✓ dimensionless count ratio (counts per share, normalized [0,1] body ratio): C004 trade_density / C002 (H-L)/C / C003 body_ratio — 全部 style_r² ≤ 0.13 frontier 真红利
- ✗ ratio 含绝对价格量纲 (amount/volume): C001 — style_r²=0.49 frontier 失效
- ✗ ratio 含 size/market_cap 分母: C005 turnover/market_cap — vol_20d_exp=17.4 frontier 部分失效
- 教训: ratio 必须 self-normalizing 才能让 TsRank60 完全脱 cross-section vol_20d basis

**frontier window 参数曲线 (P013 升格候选)**:
- C002 60d: alpha_surv=0.99 + vol_20d_exp=12.6 + style_r²=0.13 (frontier sweet spot)
- C006 120d: alpha_surv=0.92 + vol_20d_exp=21.0 + style_r²=0.17 (120d 反向)
- 结论: window ≥60d 必要, ≤90d 充分; 长窗口 120d 引入额外 vol_20d 嵌入路径

**P008 admit/reject 分水岭 (incr_ic 是关键)**:
- C002/C003 frontier 真生效 + 几何独立 (max_corr 0.27/0.37) 但 **incr_ic strong NEG** → reject
- C004 frontier 真生效 + 几何独立 (max_corr 0.13) + **incr_ic POS +0.0085** → admit
- 4 真生效 frontier 候选中, 仅 1 通过 incr_ic 关卡 — **frontier 真生效 ≠ admission**
- 升格教训: P011 alpha_surv ≥ 0.40 + ic_by_year sign-stable + **incr_ic > 0** 是 admission 三必要条件

**MT 预算**: cumulative 396→402; direction 0→6; bucket `medium`.

## Thread 进展

> [!success]+ T004 [[directions/tsrank_timeseries_ratio#T004]] — `[✓ PROVEN batch_073 C004]` (admit, frontier 真度铁证)
> **Question**: trade density (num_trades/volume) 60d TsRank 是否携带 retail attention forward POSITIVE alpha?
>
> **Answer**: **完整证实**. C004 全 CP green admit — ic_oos=+0.045 / ls_t=+9.08 整库顶级 / mono=+1.00 PERFECT POS / alpha_surv=0.58 + style_r²=0.051 (整批最低) + max_corr=0.13@F001 (整批最低) + incr_ic=+0.0085 POSITIVE + ic_by_year 2018-2023 全 POS + train_val_decay=3.91. retail-driven small-order frequency 在 csi1000 daily 上是 dimensionless count ratio 几何 sweet spot.
>
> **Evidence trail**:
> - [[batches/batch_073/candidates/C004|batch_073 C004]] TsRank(num_trades/volume, 60) → admit ⭐
>
> **复活路径** (升格 lessons): atom 互补 b072 C006 (mirror 分子分母互换 + mirror 信号方向); 后续可探索 cross-product `Mul(C004, F001/F015)` / 不同 window TsRank 30d/90d / 直接 size-residualize 拓展.

> [!failure]+ T001 [[directions/tsrank_timeseries_ratio#T001]] — `[✗ DISPROVEN batch_073]`
> **Question**: VWAP proxy (amount/volume) 60d TsRank 是否携带 forward alpha?
> **Answer**: **frontier 失效首例**. C001 alpha_surv=0.24 + style_r²=0.49 + dom=vol_20d 三立 reject. ratio 含绝对价格量纲 → vol_20d 嵌入残留, 非所有 ratio 都享受 frontier 红利.
> **Evidence**: [[batches/batch_073/candidates/C001|C001]] alpha_surv=0.24 → reject

> [!failure]+ T002 [[directions/tsrank_timeseries_ratio#T002]] — `[~ PARTIAL DISPROVEN batch_073]`
> **Question**: Normalized range (H-L)/C 60d TsRank 是否脱 vol_20d?
> **Answer**: **frontier 真生效但 incr_ic 强 NEG**. C002 alpha_surv=0.99 + style_r²=0.13 真生效证实, 但 incr_ic=-0.034 → P008 library reducer reject. F022 close_position 已复合预测.
> **Evidence**: [[batches/batch_073/candidates/C002|C002]] frontier success but library_reducer

> [!failure]+ T003 [[directions/tsrank_timeseries_ratio#T003]] — `[~ PARTIAL DISPROVEN batch_073]`
> **Question**: Body ratio (C-O)/(H-L) 60d TsRank 个股层 conviction signal forward alpha?
> **Answer**: **frontier 强证实但同候 reject**. C003 alpha_surv=1.14 + style_r²=0.082 整批最清洁, 但 max_corr=0.37@F008 同 candlestick 几何 + incr_ic=-0.032 + ic_2015 anomaly 三立阻断.
> **Evidence**: [[batches/batch_073/candidates/C003|C003]] cleanest frontier but admission triple-blocked

> [!failure]+ T005 [[directions/tsrank_timeseries_ratio#T005]] — `[✗ DISPROVEN batch_073]`
> **Question**: Turnover-per-cap 60d TsRank?
> **Answer**: **frontier 部分失效 + library reducer**. C005 alpha_surv=0.91 PASS 但 vol_20d_exp=17.4 + max_corr=0.38 + incr_ic=-0.036. ratio 含 market_cap 分母 → frontier 部分失效.
> **Evidence**: [[batches/batch_073/candidates/C005|C005]] partial frontier + library_reducer

> [!failure]+ T006 [[directions/tsrank_timeseries_ratio#T006]] — `[✗ DISPROVEN batch_073]` (window ablation)
> **Question**: Window 120d 是否优于 60d?
> **Answer**: **120d 不优于 60d, 反向恶化**. C006 vs C002: vol_20d_exp 12.6→21.0 (+66%), alpha_surv 0.99→0.92, style_r² 0.13→0.17. 120d 引入额外 vol_20d 嵌入路径 (longer window samples 更多 vol cycle). frontier window 参数曲线定锚 60d sweet spot.
> **Evidence**: [[batches/batch_073/candidates/C006|C006]] 120d window worse than 60d

## 方向级反思

新方向首批 (round 73) **6 thread 1 PROVEN admit + 5 DISPROVEN/PARTIAL** — **新方向首 admit 即 frontier 真度铁证**:

1. **direction 状态判定**: rounds=1, admit=1 (C004), reserve=0, reject=5. admit/judged=16.7%. status `probing` → **`active`** (首 admit 验证 frontier 真度, priority 维持 high).
2. **核心 mechanism PROVEN**: P008 frontier "TsRank window≥60d on ratio fields = vol_20d-escape 路径" 在 dimensionless count ratio atom (trade_density) 上完整实证 — C004 ic_oos=+0.045 + ls_t=+9.08 + alpha_surv=0.58 + style_r²=0.051 + max_corr=0.13 + incr_ic=+0.0085 全 CP green 落地.
3. **关键发现 P012 (升格候选)**: **frontier 真生效 atom 类型律** — 仅当 ratio atom 自身已 dimensionless (counts per share, normalized [0,1] body ratio) frontier 才完全生效; ratio 含绝对量纲 (amount/volume, turnover/market_cap) → vol_20d 嵌入残留. 4 frontier 真生效候选中仅 1 通过 admission (incr_ic 关卡 + 几何独立).
4. **关键发现 P013 (升格候选)**: **frontier window 参数曲线** — 60d 是 sweet spot, 120d 引入额外 vol_20d 嵌入路径. window ≥60d 必要 ≤90d 充分 (90-120d 区间需后续 ablation).
5. **关键发现 P014 (升格候选)**: **P011 admission 三必要条件** — alpha_surv ≥ 0.40 + ic_by_year sign-stable + **incr_ic > 0** 三立; frontier 真生效 (alpha_surv 高 + style_r² 低) 仍可被 incr_ic NEG 阻断 (4/6 候选案例).
6. **frontier 真度铁证终结 13 连零 admit streak** (round 60-73 累积零 admit 周期); P008 frontier 不再是单点 (b072 C006 reserve) 而是 cross-batch 跨字段族 PROVEN. zero_admit_streak: 13 → 0.
7. **next batch hint**: tsrank_timeseries_ratio 续探 — (a) C004 派生 cross-product `Mul(C004, F001/F015)` 测复合 alpha 是否进一步; (b) window 30d/45d/90d 扫描 frontier 参数曲线 (60d 阈值还是下限?); (c) 跨 atom dimensionless count ratio 拓展 (其他 num_trades 衍生 ratio).

**下批应优先 tsrank_timeseries_ratio 续探**, frontier 真度已落地 + active 方向, 但 frontier sweet spot 边界 (window 参数曲线 / atom 类型) 仍待精细 ablation. **不触 consolidation** (rounds_since=0 刚 round 73 完成).
