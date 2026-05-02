---
batch_id: batch_074
direction: tsrank_timeseries_ratio
judged_at: 2026-05-02T00:30:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 0, reject: 6}
admit_count: 0
reject_count: 6
reserve_count: 0
candidate_count: 6
mt_bucket: high
calibration_diagnosis:
  potential_over_rejection: false
  reason: "C001/C002/C003 metrics 强 (ic_oos 0.040-0.047, mono OOS 1.00, ls_t 8.5-9.4) 但 max_corr to F024 ≥0.91 是 hard_gate near_duplicate ceiling — 不是错杀，是 F024 已饱和该 atom × window 几何 plateau。C004 hard-gate pass 但 incr_ic=-0.038 NEG + mono OOS=-0.30 sign decay 双独立 reject。C005 mirror atom corr=-0.957 几乎等价 F024。C006 Mul cross-product alpha_surv=0.068 collapse + triple sign-flip — geometry 已 5+ 次 fail。所有 reject 都是 ≥2 独立失败链路触发，无错杀候选。"
---

# batch_074 Judge Summary

> [!fail]+ batch_074 · [[directions/tsrank_timeseries_ratio]] · 6 candidates (continue_direction 续探 F024 admit hot streak)
> ❌ **admit=0** · ⏸ reserve=0 · ❌ **reject=6** — 全军覆没
> **核心发现**: F024 已饱和此 direction 核心几何空间。三轴 ablation (window/cross-atom/cross-product) 全部 reject — (a) **window ablation 30/45/90d 全部 corr ≥0.91 to F024 hard_gate near_duplicate fail** (TsRank rolling 在 ±2x window-ratio 内 plateau, P015 升格候选); (b) **cross-atom $num_trades/$circ_market_cap 60d 重演 b073 C005 cap-denominator frontier 失效** (vol_20d_exp=19.1 + style_r²=0.150 borderline + incr_ic=-0.038 NEG, P016 升格候选); (c) **mirror atom $volume/$num_trades 60d corr=-0.957 镜像反号几乎等价 F024** (TsRank reciprocal-invariance, P017 升格候选); (d) **Mul(F024_atom, CsRank momentum) triple hard_gate fail + alpha_surv=0.068 collapse** (Mul cross-product 普遍失败几何, P018 升格候选)。**P013 修正**: 60d 不是 ic_oos 单点最大 (90d 高 0.002) 而是 risk-adjusted 综合最优 (mono PERFECT + lowest style_r² 0.051 + alpha_surv 0.58)。
> **MT Budget**: cumulative 396→402 ✅(预期 408 但 b073 已纳入) · direction 6→12 · bucket `high`
> **direction 状态变更建议**: active → **saturated** (核心 atom × window 几何已 admit 占领, 三轴 ablation 完成 frontier scope 测绘)。

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate·strong·good·**near_dup**·stable | ic_oos=+0.040 ls_t=+8.54 mono=**+1.00** alpha_surv=0.67 sty_r²=0.036 max_corr=**0.914@F024** incr=+0.021 POS | TsRank(num_trades/volume,**30d**) F024 atom window ablation — 全部 frontier 真生效证据 (mono PERFECT + style_r² 0.036 + alpha_surv 0.67) 但 corr 0.914 to F024 触发 hard_gate near_dup ceiling。incr_ic POS 但 absolute corr 阻断 — P015 实证: TsRank rolling 在 ±2x window-ratio 内 entropy 同信号 | [[batches/batch_074/candidates/C001]] |
| C002 | ❌ reject | hard_gate·strong·good·**near_dup**·stable | ic_oos=+0.043 ls_t=+8.73 mono=**+1.00** alpha_surv=0.61 sty_r²=0.043 max_corr=**0.977@F024** 整批最高 incr=+0.029 POS | TsRank(num_trades/volume,**45d**) — corr=0.977 整批最高 (TsRank ±15d window-shift 几乎等价 F024)。incr_ic 看似最强但 entropy 上是同信号 — P015 强化证据 | [[batches/batch_074/candidates/C002]] |
| C003 | ❌ reject | hard_gate·strong·acceptable·**near_dup**·stable | ic_oos=**+0.047** 整批最高 ls_t=**+9.37** mono=+0.90 (退化) alpha_surv=0.56 sty_r²=0.064 (升 +0.013 vs 60d) max_corr=**0.962@F024** incr=+0.025 POS | TsRank(num_trades/volume,**90d**) — ic_oos 整批最高但 mono OOS 0.90 退化 + style_r² 升 — **P013 修正实证**: 60d 不是 ic_oos 单点最大但综合 risk-adjusted 最优。corr 0.962 hard_gate fail | [[batches/batch_074/candidates/C003]] |
| C004 | ❌ reject | aligned·medium·**borderline**·medium(F022)·**unstable** | ic_oos=-0.035 ls_t=-3.11 mono OOS=**-0.30 (sign decay 0.40)** alpha_surv=1.16 PASS sty_r²=**0.150** borderline vol_20d_exp=**19.1** max_corr=0.44@F022 incr=**-0.038 strong NEG** | TsRank(num_trades/circ_market_cap,60d) cross-atom — hard_gate pass but **重演 b073 C005 ($turnover/$market_cap) 同失败模式**: cap 分母 → vol_20d 嵌入残留 + frontier 部分失效 + library reducer NEG (F022 已捕捉)。**P016 升格候选**: dim-less count ratio frontier scope 仅适用于两端 microstructure-only 字段 | [[batches/batch_074/candidates/C004]] |
| C005 | ❌ reject | hard_gate·strong·good·**near_dup**·stable | ic_oos=-0.045 ls_t=-9.01 mono=**-1.00** PERFECT NEG (F024 完全镜像) alpha_surv=0.52 sty_r²=0.055 max_corr=**0.957@F024** 镜像反号 incr=**-0.034 NEG** | TsRank(volume/num_trades,60d) F024 reciprocal mirror — corr=-0.957 镜像反号几乎完全等价 F024 (mono +1→-1, ic_oos +0.045→-0.045)。**P017 升格候选**: TsRank rolling rank 对 reciprocal atom 几乎不变 (corr ≥0.95) | [[batches/batch_074/candidates/C005]] |
| C006 | ❌ reject | hard_gate·**weak**·**poor**·medium(F024)·**unstable** | ic_is=**-0.024** / ic_oos=**+0.029 sign_flip** mono IS=-0.60/OOS=+0.70 both >0.5 oos_decay=**-1.20 NEG** alpha_surv=**0.068 COLLAPSE** sty_r²=0.108 borderline max_corr=0.64@F024 incr=**-0.023 NEG** | Mul(TsRank(num_trades/volume,60), CsRank(close-close[5])) — **triple hard_gate fail** (sign_flip + oos_decay + mono_flip both >0.5) + alpha_surv collapse 0.068 + incr_ic NEG。**Mul cross-product wrapper 在 csi1000 daily 第 5+ 次失败** (b070-b074), **P018 升格候选**: F admitted × F admitted 普遍 alpha_surv collapse + sign instability — Mul 改变 cross-section moment structure → Barra style basis 重新捕捉 + sign 取决于联合分布 quartile (regime drift 触发 sign flip) | [[batches/batch_074/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色.

## 跨候选对比 — frontier scope 测绘 (round 73 + 74 拼接)

**Window ablation curve (单 atom × 不同 window)**：

| Window | Source | ic_oos | mono_oos | alpha_surv | style_r² | dom_style_exp(vol_20d) | corr to F024 60d | incr_ic | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 30d | b074 C001 | +0.040 | +1.00 | 0.67 | 0.036 | 10.7 | 0.914 | +0.021 | hard_gate near_dup |
| 45d | b074 C002 | +0.043 | +1.00 | 0.61 | 0.043 | mid | 0.977 | +0.029 | hard_gate near_dup |
| **60d** | **F024 b073 C004** | **+0.045** | **+1.00** | **0.58** | **0.051** | **12.6** | **1.00** | **+0.0085** | **✅ ADMIT** |
| 90d | b074 C003 | +0.047 | +0.90 | 0.56 | 0.064 | mid | 0.962 | +0.025 | hard_gate near_dup |
| 120d (Div(H-L,C)) | b073 C006 | -0.041 | -1.00 | 0.92 | 0.165 | 21.0 | n/a | -0.035 | reject (different atom) |

**P013 修正结论**: 60d 在 ic_oos 维度不是单点最大 (90d 高 +0.002)，但综合 mono PERFECT + lowest style_r² 0.051 + alpha_surv 0.58 + lowest dom=vol_20d_exp 12.6 是 **risk-adjusted 综合最优**；30/45/90d 全部 corr ≥0.91 to F024 → window 单变量 ablation 不是 library expansion 路径。

**Atom expansion (不同 ratio family × TsRank60)** — 跨 b073/b074 整合：

| Ratio (numerator/denominator) | Source | atom 类型 | frontier 真生效 | admission | Reject reason |
|---|---|---|---|---|---|
| amount/volume (VWAP proxy) | b073 C001 | 含绝对量纲 | ✗ (style_r² 0.49) | reject | frontier 失效 |
| (H-L)/C (normalized range) | b073 C002 | dim-less | ✓ | reject | incr_ic=-0.034 NEG |
| (C-O)/(H-L) (body ratio) | b073 C003 | dim-less [0,1] | ✓ (style_r² 0.082) | reject | incr_ic=-0.032 + max_corr 0.37 |
| **num_trades/volume** | **b073 C004** | **dim-less count** | **✓ (style_r² 0.051)** | **✅ admit (F024)** | — |
| turnover/market_cap | b073 C005 | cap 分母 | ✗ partial (vol_20d_exp 17.4) | reject | incr_ic=-0.036 + cap 嵌入 |
| **num_trades/circ_market_cap** | **b074 C004** | **cap 分母** | **✗ partial (vol_20d_exp 19.1)** | **reject** | **incr_ic=-0.038 + cap 嵌入 (重演 b073 C005)** |
| **volume/num_trades (mirror F024)** | **b074 C005** | **dim-less count** | **✓ (style_r² 0.055)** | **reject** | **corr -0.957 to F024 几乎等价** |

**P016 升格候选**: dim-less count ratio frontier scope 仅适用于两端都是 microstructure-only 字段 (volume, num_trades) — cap 分母 ($circ_market_cap/$market_cap) 双实证 (b073 C005 + b074 C004) 触发 vol_20d 嵌入残留 → frontier 部分失效。

**P017 升格候选**: TsRank rolling rank operator 对 reciprocal atom 几乎不变 (corr ≥0.95)。

**P018 升格候选**: Mul cross-product wrapper 在 csi1000 daily 普遍失败几何 (b070-b074 5+ 次实证) — F admitted × F admitted 类型 alpha_surv collapse + sign instability。

## Thread 进展

> [!fail]+ T007 [[directions/tsrank_timeseries_ratio#T007]] — `[✗ DISPROVEN batch_074 C001/C002/C003]` (window ablation plateau)
> **Question**: F024 (60d) 是单点 sweet spot 还是 plateau? 30/45/90d ablation 完整曲线。
> **Answer**: ic_oos 30→90d 单调上升 (0.040→0.043→0.047) 但 corr to F024 ≥0.91 全 hard_gate near_dup fail。**60d 不是 ic_oos 单点最大但是 risk-adjusted 综合最优** (mono PERFECT + lowest style_r² + alpha_surv)。TsRank rolling 在 ±2x window-ratio 内 plateau (P015 升格候选).

> [!fail]+ T008 [[directions/tsrank_timeseries_ratio#T008]] — `[✗ DISPROVEN batch_074 C004]` (cap 分母 frontier 失效)
> **Question**: $num_trades/$circ_market_cap 60d 是否享受 P012 dim-less count ratio frontier 红利?
> **Answer**: frontier 部分失效 + library reducer。alpha_surv=1.16 PASS 但 vol_20d_exp=19.1 + style_r²=0.150 borderline + mono OOS sign decay + incr_ic=-0.038 NEG to F022。**重演 b073 C005 cap-denominator 同失败模式** (P016 升格候选).

> [!fail]+ T009 [[directions/tsrank_timeseries_ratio#T009]] — `[✗ DISPROVEN batch_074 C005]` (mirror atom 等价)
> **Question**: F024 reciprocal ($volume/$num_trades = avg trade size) 是否独立信号?
> **Answer**: corr=-0.957 镜像反号几乎等价 F024 + incr_ic=-0.034 NEG library reducer。TsRank reciprocal-invariance (P017 升格候选).

> [!fail]+ T010 [[directions/tsrank_timeseries_ratio#T010]] — `[✗ DISPROVEN batch_074 C006]` (Mul cross-product collapse)
> **Question**: Mul(F024_atom, CsRank short-momentum) 是否产生独立复合 alpha?
> **Answer**: triple hard_gate fail + alpha_surv collapse 0.068 + incr_ic NEG。Mul cross-product wrapper 在 csi1000 daily 第 5+ 次失败 (P018 升格候选).

## Calibration check (Phase 3.5)

- **错杀 flag**: false。所有 6 reject 都 ≥2 独立失败链路触发 (hard_gate fail + library reducer NEG / hard_gate fail + alpha_surv collapse / hard_gate fail + mono OOS decay) — 无单点阈值边缘错杀候选。
- **连续零 admit 警戒**: false (上批 admit F024，zero_admit_streak 终结后本批 1)。
- **Reserve 积压**: false (本批 0 reserve)。
- **悖论复现**: false (b074 C004 与 b073 C005 cap-denominator 同模式属 P016 升格证据而非悖论)。

**calibration_trigger=false** — 进入 Phase 4 archive。

## Direction status & next-batch hint

**direction status 建议**: active → **saturated** — 核心 atom × window 几何已被 F024 占领；本批六轴 ablation 完成 frontier scope 测绘。

**unexplored 路径** (留给 Phase 5 / 跨方向):
1. higher-moment LHS on count ratio (Std/Skew(num_trades/volume, n)) — 需先验证不触发 higher-moment trap (lessons 红线)。
2. cross-direction residualize: F024 残差在另一方向 (e.g. residualize on F009 pv_corr_times_vol family) — 需 Python tooling。
3. minute-bar 数据接入后的 intraday count-ratio frontier — 需数据层升级。

**next batch 推荐**: switch to fresh direction (从 lessons Promising Unexplored 或 hypothesis_promoter findings 取新方向)；保留 saturated tsrank_timeseries_ratio 的 P015-P018 升格知识；不再分配预算到此族 frontier 单变量探索。
