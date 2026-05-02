---
batch_id: batch_076
direction: tsrank_candlestick_ratio
judged_at: 2026-05-02T00:30:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: admit, factor_name: shadow_asymmetry_tsrank_60}
batch_summary: {total: 6, admit: 1, reserve: 2, reject: 3}
admit_count: 1
reserve_count: 2
reject_count: 3
candidate_count: 6
mt_bucket: medium
---

# batch_076 Judge — tsrank_candlestick_ratio NEW direction 首批

> [!success]+ batch_076 · [[directions/tsrank_candlestick_ratio]] · 6 candidates (NEW direction)
> ✅ **admit=1** (C006 → F025 ⭐) · ⏸ **reserve=2** (C001 close_position, C005 midprice/close) · ❌ **reject=3** (C002 weak shadow, C003 hard_gate body, C004 vol-proxy)
> **核心发现**: NEW direction 首批落地 1 admit (F025 shadow_asymmetry_tsrank_60) — TsRank-60 frontier 真生效在 OHLC shape 域**首例铁证**. **方向升格律**: 高阶 composition (ratio-of-derived-quantity) 比 single-atom ratio 更彻底破 cross-section 几何同源 — C006 max_corr=0.29 vs C001/C005 single-atom 0.45-0.47.
> **MT Budget**: cumulative 414 → 420 · direction 0 → 6 · bucket `medium`

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | aligned·strong·good·**medium(F008)**·stable | ic_oos=-0.047 ls_t=-6.36 mono=-1.00 alpha_surv=1.18 sty_r²=0.062 vol_20d_exp=8.55 max_corr=**0.47@F008** incr=-0.040 | TsRank close_position 60d — 信号顶级 (ls_t -6.36 mono PERFECT NEG sign-stable 8/9) 但 cross-section 几何与 F008 upper_shadow 同源 (close 偏低 = 上影长 同根), TsRank time-series 量纲化未破解几何同源 | [[batches/batch_076/candidates/C001]] |
| C002 | ❌ reject | aligned·**weak**·good·medium(F007)·mixed | ic_oos=-0.018 ls_t=-0.44 mono=-0.30 alpha_surv=1.14 sty_r²=0.058 max_corr=0.38@F007 incr=-0.017 | TsRank upper_shadow 60d — 信号弱 + 库 overlap. raw shadow 长窗时序量纲化破坏短期信号 (F006/F008 用 3d/5d 短窗更优) | [[batches/batch_076/candidates/C002]] |
| C003 | ❌ reject | hard_gate · - · - · - · - | sign_flip train -0.005 vs val +0.008; oos_decay -1.77 | TsRank body_ratio 60d — train→val regime drift sign_flip. body_ratio 是日内动量, 60d TsRank mean-reverted 信号碎片化 | [[batches/batch_076/candidates/C003]] |
| C004 | ❌ reject | aligned·borderline·**poor**·low(F022)·mixed | ic_oos=-0.037 ls_t=-3.43 mono=-0.40 alpha_surv=0.99 sty_r²=**0.133** max_corr=0.27@F022 incr=-0.034 | TsRank range/close 60d — vol proxy 直接载体 sty_r² OVER 0.12 poor + alpha_surv 边缘 (just-below 1.0). frontier 局部失效 | [[batches/batch_076/candidates/C004]] |
| C005 | ⏸ reserve | aligned·strong·good·**medium(F008)**·stable | ic_oos=+0.038 ls_t=+4.84 mono=+0.90 alpha_surv=**1.43** batch best sty_r²=0.064 vol_20d_exp=10.56 max_corr=**0.45@F008** incr=**+0.042** | TsRank midprice/close 60d — 信号 batch 强度第一 (alpha_surv 1.43 顶级) 但与 F008 几何同源 (midprice>close ⇔ 上影长). 与 C001 同失败模式 | [[batches/batch_076/candidates/C005]] |
| **C006** | ✅ **ADMIT** | **aligned·strong·good·low(F007)·stable** | **ic_oos=+0.019 ls_t=+6.19 mono=+1.00** alpha_surv=1.15 sty_r²=**0.029** batch min vol_20d_exp=**6.03** batch min max_corr=**0.29@F007** UNDER 0.30 incr=**+0.014 POS** | TsRank shadow_asymmetry 60d — **全 CP green**: frontier 真生效顶级 (vol_20d_exp 6.03 比 F024 还低 40%) + 库独立 (max_corr 0.29 UNDER 0.30 line) + sign-stable POS 8/9 + incr_ic POS 真新 alpha. **高阶 composition 破共线性铁证** | [[batches/batch_076/candidates/C006]] · [[factors/F025]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）.

## 跨候选对比 — 高阶 composition 破共线性律

**C006 admit vs C001/C005 reserve 对比 — 几何独立机制实证**:

| 指标 | C001 close_position | C005 midprice/close | **C006 shadow_asymmetry** |
|---|---|---|---|
| atom 形式 | single ratio (close-low)/(high-low) | single ratio midprice/close | **double-shadow ratio (高阶 composition)** |
| ic_oos | -0.047 | +0.038 | +0.019 |
| ls_t | -6.36 | +4.84 | +6.19 |
| mono | -1.00 PERFECT NEG | +0.90 | +1.00 PERFECT POS |
| alpha_surv | 1.18 | **1.43 batch best** | 1.15 |
| style_r² | 0.062 | 0.064 | **0.029 batch min** |
| vol_20d_exp | 8.55 | 10.56 | **6.03 batch min** |
| max_corr | **0.47@F008** ⚠ | **0.45@F008** ⚠ | **0.29@F007** ✓ |
| incr_ic | -0.040 | +0.042 | +0.014 |
| Verdict | reserve | reserve | **ADMIT (F025)** |

**关键洞察**: C001/C005 信号本身比 C006 强 (ls_t 6.36/4.84 vs 6.19; alpha_surv 1.18/1.43 vs 1.15), 但**库 overlap 阻断 admit**. C006 信号中等但**几何独立性**碾压 (max_corr 0.29 vs 0.45-0.47). 机制: C006 是 ratio of two derived shadow lengths, cross-section 上分子分母同消 base scale + base volatility, 与 single-atom Mean shadow (F008) 几何独立.

**P019 升格 candidate (b076 升格)**: TsRank-60 frontier 真度律分级 — frontier 真生效 ≠ admission, 几何独立性是 admission 关键阻断. **高阶 composition (ratio-of-derived-quantity) 是 single-atom ratio 之外 dim-less ratio frontier 真红利第二阶**. 库内现状: F025 是首例 high-order OHLC composition admit; 后续 frontier 续探优先 (shadow/body 倍率) × (body/range) 三层 composition.

**P020 升格 candidate (b076 升格)**: Cross-section 几何同源律 — TsRank time-series 量纲化无法破解 cross-section 几何同源量 (close_position ⇔ upper_shadow_position 同根 = "收盘相对日内位置" 同义); 削弱但未破解 cross-section 共线性 (corr 仅从 raw form ~0.7 降到 ~0.45). 破解需高阶 composition (b076 实证) 或换 universe.

## Thread 进展

> [!success]+ T003 [[directions/tsrank_candlestick_ratio#T003]] — `[~ PARTIAL ANSWERED batch_076 C006]` (admit, 高阶 composition 路径 PROVEN)
> **Question**: range/midprice/asymmetry 类 OHLC shape ratio 60d TsRank 是否携带 forward alpha 且与库独立?
>
> **Answer**: **partial PROVEN**. shadow_asymmetry (高阶 composition C006) admit, 验证高阶 composition 路径 — 全 CP green, frontier 真生效顶级 (vol_20d_exp 6.03 batch 最低), 库独立 (max_corr 0.29 UNDER line), sign-stable POS 8/9. range_to_close (C004) 因 vol proxy 直接载 vol_20d basis 失效 (sty_r² 0.133 poor). midprice/close (C005) reserve 火种, 信号顶级但与 F008 几何同源.
>
> **Evidence trail**:
> - [[batches/batch_076/candidates/C006|batch_076 C006]] TsRank shadow_asymmetry 60d → admit ⭐
> - [[batches/batch_076/candidates/C004|batch_076 C004]] range/close → reject (vol proxy)
> - [[batches/batch_076/candidates/C005|batch_076 C005]] midprice/close → reserve (geometric overlap)

> [!failure]+ T001 [[directions/tsrank_candlestick_ratio#T001]] — `[~ PARTIAL DISPROVEN batch_076]`
> **Question**: close_position / upper_shadow ratio 60d TsRank 是否与库 F006/F008/F011 几何独立?
> **Answer**: **partial DISPROVEN**. cross-section 几何同源律实证 — 单原子 atom 与库 F006/F008 共线性 0.4-0.5 不可解 (TsRank 时序量纲化仅削弱). 信号本身 (C001) 顶级强但 admission 库 overlap 阻断.
> **Evidence trail**: [[batches/batch_076/candidates/C001|b076 C001]] max_corr=0.47@F008 reserve / [[batches/batch_076/candidates/C002|b076 C002]] max_corr=0.38@F007 weak signal reject.

> [!failure]+ T002 [[directions/tsrank_candlestick_ratio#T002]] — `[✗ DISPROVEN batch_076]`
> **Question**: body_ratio 60d TsRank 是否携带 forward NEG alpha (趋势耗尽假设)?
> **Answer**: **DISPROVEN**. C003 hard_gate fail — train→val regime drift sign_flip + oos_decay -1.77. body_ratio 是日内动量信号, 60d TsRank time-series form 把动量 mean-reverted, 信号碎片化.
> **Evidence trail**: [[batches/batch_076/candidates/C003|b076 C003]] body_ratio TsRank 60 hard_gate fail.

## 方向级反思

NEW direction 首批 (round 76) **3 thread 1 PARTIAL PROVEN admit + 1 PARTIAL DISPROVEN + 1 DISPROVEN** — **frontier 真度铁证 + 高阶 composition 路径开辟**:

1. **direction 状态判定**: rounds=1, admit=1 (C006→F025), reserve=2 (C001 close_position, C005 midprice), reject=3. admit/judged=16.7%. status `probing` → **`active`** (首 admit 验证 frontier 真度, priority 维持 high).
2. **核心 mechanism PROVEN**: P008 frontier (TsRank window≥60d on dim-less ratio = vol_20d-escape 路径) 在 OHLC candlestick shape 域**首次实证** — C006 ic_oos=+0.019 + ls_t=+6.19 + alpha_surv=1.15 + style_r²=0.029 + vol_20d_exp=6.03 + max_corr=0.29 + incr_ic=+0.014 全 CP green 落地.
3. **P019 升格候选**: 高阶 composition (ratio-of-derived-quantity) 比 single-atom ratio 更彻底破 cross-section 共线性 — single atom (C001/C005) max_corr 0.45-0.47 库 overlap 阻断, 高阶 composition (C006) max_corr 0.29 突破. 高阶 composition 是 dim-less ratio frontier 真红利第二阶.
4. **P020 升格候选**: Cross-section 几何同源律 — TsRank time-series 量纲化无法破解 cross-section 几何同源 (close_position ⇔ upper_shadow 同根 = "收盘相对日内位置" 同义). 仅削弱 cross-section 共线性 (raw 形式 ~0.7 → TsRank 形式 ~0.45). 破解需高阶 composition 或换 universe.
5. **frontier 真度铁证扩展**: F024 (count ratio frontier) → F025 (geometric ratio + 高阶 composition frontier). TsRank-60 frontier 不再是 count ratio 单点空间, 而是 cross-domain 跨 atom 类型 PROVEN (count ratio + OHLC shape composition).
6. **zero_admit_streak 重置**: b075 1 → b076 0 (admit reset).

## 阈值校准段

无错杀风险 (admit C006 全 CP green, max_corr=0.29 UNDER 0.30 prefer line); 无 P008/P011 alpha_survival 红线踩踏 (alpha_surv=1.15 PASS + ic_by_year sign-stable + incr_ic POS); 无市值代理风险 (无 $market_cap atom); 无 P016 cap-denominator 几何 (无 cap 分母).
