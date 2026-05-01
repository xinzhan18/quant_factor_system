---
batch_id: batch_072
direction: institutional_flow_proxy
judged_at: 2026-05-02T00:00:00Z
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
mt_bucket: medium
---

# batch_072 Judge Summary

> [!abstract]+ batch_072 · [[directions/institutional_flow_proxy]] · 6 candidates (NEW direction)
> ✅ **admit=0** · ⏸ **reserve=1** (C006) · ❌ **reject=5**
> **核心发现**: T001-T005 五 thread NEW direction `$num_trades` 字段族探索 — **几何独立但 OOS 全 reversal 方向**。5/5 PASS-hg 候选 OOS IC 全部为负 (mono_oos=-1.0 PERFECT 5/5 + sign_consistency=1.0 5/5)，机理：avg_trade_size 高 = 机构集中 = 高活跃股票 = forward reversal，A 股 retail 主导 reversal 律共振放大。**关键差异 vs b068 C002 raw level**: 大部分候选 vol_20d_exp 显著低 (10-19% vs b068 9.75 但 alpha_surv catastrophic)；**C006 TsRank 60d 形式独特**: alpha_surv=**0.447** (PASS 0.40 default) + max_corr=**0.24@F009** (LOW 几何独立) + style_r²=**0.15** (低) + ls_t=**-7.54** (整库顶级) + mono_oos=**-1.0** PERFECT — 但 incremental_ic=**-0.018 NEG** (P006 library_reducer signature 但未触发 hard_block，alpha_surv>0.30 例外)。**CP 矛盾**: 强 CP3 + 干净 CP4 + 低 CP5 max_corr 但 CP5 incr_ic 微负 → reserve 火种留待 incr_ic 改善判定 (avg_trade_size + retail attention 几何空间未饱和).
> **MT Budget**: cumulative 390 → 396 · direction 0 → 6 · bucket `medium` (新方向 direction 项=0 拉低 score)

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | aligned·strong·**poor**·medium(F016)·stable | ic_oos=-0.061 ls_t=-5.86 mono=-1.00 alpha_surv=**0.17** sty_r²=0.25 vol_20d_exp=**26.7** max_corr=0.31@F016 incr=+0.0127 | Std(avg_trade_size,20) institutional flow volatility — vol_20d_exp=26.7 + alpha_surv=0.17 catastrophic + dom=vol_20d r²=0.25 → 标准 P004 vol_20d 三立吸收。Std 形式 LHS 在 ratio 字段上仍嵌入 vol_20d (Std of amount/num_trades 直接捕捉日内交易量波动)。incr=+0.0127 PASS floor 但 alpha_surv 杀 | [[batches/batch_072/candidates/C001]] |
| C002 | ❌ reject | aligned·strong·acceptable·**high**(F012)·stable | ic_oos=-0.050 ls_t=-5.36 mono=-1.00 alpha_surv=**0.94** sty_r²=**0.59** vol_20d_exp=**30.9** max_corr=**0.75@F012** incr=-0.038 | CsRank($num_trades) 单字段 raw rank — alpha_surv=0.94 假象 PASS 但 max_corr=0.75@F012 NEAR_DUPLICATE >0.70 hard_block + style_r²=0.59 双 vol_20d/turnover 吸收 + incr=-0.038 强 NEG library reducer。$num_trades cross-section level 是 size + Amihud 联合代理 — F012 Amihud (-|return|/$amount,N) 通过 size 共线性同样捕捉 retail attention，**P002 rank-preserving 律边界**: 即使 raw 字段也可能与 admitted 因子结构重叠 | [[batches/batch_072/candidates/C002]] |
| C003 | ❌ reject | hard_gate | sign_flip: train +0.009 / val -0.017 + oos_decay -1.888 + mono_sign_flip 0.70/-1.00 三立 | Sub(CsRank avg_trade_size, CsRank Mean(amount,20)) rank-diff 形式 — train +0.009 OOS -0.017 翻号 + decay 负 + mono 翻号. P001 rank-diff 7 律 #6 RHS amount_20 死亡 endpoints 触发 — RHS amount_20 已被 anchor cluster 整族占据 (F002/F015 etc)，rank-diff 跨 institutional vs general liquidity 不能脱 anchor。设计层失效 | [[batches/batch_072/candidates/C003]] |
| C004 | ❌ reject | aligned·strong·**poor**·low(F016)·stable | ic_oos=-0.039 ls_t=-3.94 mono=-1.00 alpha_surv=**0.25** sty_r²=0.09 vol_20d_exp=**19.1** max_corr=0.19@F016 incr=-0.004 | Corr(avg_trade_size,$close,20) OFI proxy — alpha_surv=0.25 三立 + dom=vol_20d r²=0.09 (style_r² 低但 dominant 仍 vol_20d) + incr=-0.004 微负。20d rolling correlation 量纲化未消除 vol_20d 嵌入路径，OFI proxy 在 csi1000 daily 上携带 reversal 但 alpha 不脱 vol_20d。低 max_corr=0.19 几何独立但 alpha 不存在 | [[batches/batch_072/candidates/C004]] |
| C005 | ❌ reject | aligned·**strong**·borderline·medium(F009)·stable | ic_oos=-0.066 ls_t=-7.32 mono=-1.00 PERFECT alpha_surv=**0.526 PASS** sty_r²=0.27 vol_20d_exp=**11.07** max_corr=0.46@F009 incr=**-0.027** | Mul rank avg_trade_size × rank 5d return — institutional × momentum cross-product. ls_t=-7.32 + alpha_surv=0.526 PASS 0.40 + vol_20d_exp=11.07 (低!), 但 max_corr=0.46@F009 (overnight pv_corr) borderline 中段死区 + incr=-0.027 强 NEG library_reducer。**P006 library_reducer hard_block 4 件套未完整三立** (alpha_surv=0.526>0.30 例外)，但 incr_ic=-0.027 在 P008 "Rank-order ≠ Tradable Alpha" 第二要件触发 → 默认 reject 而非 reserve. F009 (pv_corr_5) cross-product 形式同源吸收 (机构 × momentum 通过 pv_corr 几何重叠) | [[batches/batch_072/candidates/C005]] |
| C006 | ⏸ **reserve** | aligned·**strong**·**good**·**low**(F009)·stable | ic_oos=-0.054 **ls_t=-7.54** mono=-1.00 PERFECT alpha_surv=**0.447 PASS** sty_r²=**0.15** vol_20d_exp=**10.87** max_corr=**0.24@F009 LOW** incr=**-0.018** | TsRank(avg_trade_size,60) — 时序 60d rank 个股层 institutional flow anomaly。ls_t=-7.54 (整库顶级) + mono PERFECT + alpha_surv=0.447 PASS + style_r²=0.15 (低 cross-section 风格暴露!) + max_corr=0.24@F009 几何独立。**TsRank 时序量纲化几何 = 库内极少先例 + 新字段 $num_trades** 双重独立。但 incr_ic=-0.018 微负 (P008 第二要件触发"library 复合可预测") + ic_2015=+0.007 早年异号 (regime stability 边界). **reserve 不 admit 理由**: incr_ic NEG = library 已能复合预测此信号方向 (即使 max_corr=0.24 低)，admit 会引入"伪几何独立但 PnL 重叠"。**reserve 不 reject 理由**: TsRank 时序几何 + 新字段 + 全 CP3/CP4 强 + style_r²=0.15 极清洁 — 设计层是真正 institutional flow proxy 提示，等 incr_ic 改善 (e.g. 配 RHS rank-diff 或换窗口) 可激活 | [[batches/batch_072/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色.

## 跨候选对比

**Mono / sign 聚合**：5/5 PASS-hg 候选 mono_oos = -1.000 PERFECT + sign_consistency = 1.0 + ls_t 全负 (-3.94 ~ -7.54)。**$num_trades 几何空间在 csi1000 daily 上是 reversal 方向**。机理：avg_trade_size 高 = 机构集中 + 高活跃股票 = retail 散户高关注度 → forward reversal (A 股 retail 主导 reversal 律 + institutional flow 短期信息含量饱和后回归)。

**vol_20d 暴露分布**:
- C002 单字段 raw level: vol_20d_exp=**30.9** (size proxy 路径)
- C001 Std rolling: vol_20d_exp=**26.7** (rolling Std 嵌入 vol)
- C004 Corr rolling: vol_20d_exp=19.1 (rolling correlation 边缘)
- C005 Mul rank cross-product: vol_20d_exp=**11.07** (rank 化大幅降低)
- **C006 TsRank 60d**: vol_20d_exp=**10.87** + style_r²=**0.15** (整批最清洁，时序 rank 量纲化彻底)
- C003: hg_fail

**P004 vol_20d 第 11+ direction 部分扩展**: $num_trades 字段族 raw level (C002) + rolling (C001/C004) 形式仍系统性嵌入 vol_20d basis；**但 rank 化 cross-section 形式 (C005)** 和**时序 rank (C006)** 大幅 mitigate vol_20d 暴露 (从 26.7→11，降低 60%)。这是首次发现"时序 rank vs cross-section level"在 vol_20d 抗衡上的几何分离。

**P008 P006 复合判定边界 — alpha_surv > 0.30 例外**: C005/C006 同时满足 mono≥0.85 + |ls_t|≥2.5 + incr_ic<0 + max_corr<0.30 (C006) 或 borderline (C005)，但 alpha_surv 0.447/0.526 显著高于 0.30 → P006 library_reducer hard_block 不触发；进入 P008 "Rank-order ≠ Tradable Alpha" 软判定 (incr_ic<0 单要件触发 reject 默认)。**C005 reject + C006 reserve 的差**:
- C005 max_corr=0.46@F009 borderline cluster 重叠 + incr=-0.027 强 NEG → 默认 reject (设计无独立新几何 — Mul cross-product 已被 F009 pv_corr 同源)
- C006 max_corr=0.24@F009 LOW 几何独立 + incr=-0.018 微 NEG + style_r²=0.15 极清洁 + TsRank 时序几何为库内极少先例 → reserve 火种 (设计层有独立新几何)

**MT 预算**: cumulative 390→396; direction 0→6; bucket `medium` (新方向 direction 项=0 强力拉低)。

## Thread 进展

> [!failure]+ T001 [[directions/institutional_flow_proxy#T001]] — `[~ PARTIAL DISPROVEN batch_072]`
> **Question**: avg_trade_size 时序波动 (Std/TsRank) 是否能脱 raw level 的 vol_20d 吸收？
>
> **Answer**: **Std 形式 (C001) 失败 + TsRank 形式 (C006) 显著进展**。C001 vol_20d_exp=26.7 + alpha_surv=0.17 标准 vol_20d 三立 reject — 20d rolling Std 仍嵌入 vol_20d (Std of ratio 直接捕捉日内交易波动)。**C006 TsRank 60d 是本批最强发现**: vol_20d_exp=10.87 + style_r²=0.15 + alpha_surv=0.447 PASS + max_corr=0.24 几何独立 + ls_t=-7.54 整库顶级 — 时序 rank 量纲化 60d 窗口在个股层 institutional flow anomaly 上首次显化清洁 vol_20d 抗衡。但 incr_ic=-0.018 NEG → reserve.
>
> **Evidence trail**:
> - [[batches/batch_072/candidates/C001|batch_072 C001]] Std avg_trade_size 20d → vol_20d_exp=26.7 alpha_surv=0.17 → reject
> - [[batches/batch_072/candidates/C006|batch_072 C006]] TsRank avg_trade_size 60d → ls_t=-7.54 alpha_surv=0.447 max_corr=0.24 incr=-0.018 → **reserve**
>
> **复活路径**: (a) C006 配 RHS rank-diff (e.g. Sub(CsRank(TsRank avg_trade_size,60), CsRank(F012/F009 直接 RHS)) 测试 incr_ic 改善); (b) 测试 30d/120d 窗口；(c) Python residualize TsRank result on F009 (overnight pv_corr) 后再 CsRank.

> [!failure]+ T002 [[directions/institutional_flow_proxy#T002]] — `[✗ DISPROVEN batch_072]` (born-disproven)
> **Question**: $num_trades 单日 level rank 是否携带 retail attention forward signal？
>
> **Answer**: **DSL 直接版本证伪**. C002 max_corr=0.75@F012 NEAR_DUPLICATE + style_r²=0.59 双 vol_20d/turnover 吸收 + incr=-0.038 强 NEG library reducer. $num_trades raw cross-section level 是 size × Amihud 联合代理 — F012 Amihud (|return|/$amount) 通过 size 共线性同样捕捉 retail attention，新字段不等于新几何空间.
>
> **Evidence trail**:
> - [[batches/batch_072/candidates/C002|batch_072 C002]] CsRank($num_trades) → max_corr=0.75@F012 vol_20d_exp=30.9 incr=-0.038 → reject (near_duplicate)
>
> **复活路径**: (a) $num_trades 必先 size-residualize (Python OLS on log_circ_cap)；(b) 时序变体 (TsRank 已 C006 验证)；(c) cross-sectional rank-diff 配独立基准.

> [!failure]+ T003 [[directions/institutional_flow_proxy#T003]] — `[✗ DISPROVEN batch_072]` (born-disproven, hard_gate)
> **Question**: rank-diff 范式是否能在 institutional concentration vs general liquidity 几何上突破？
>
> **Answer**: **DSL hard_gate 三立失败**. C003 sign_flip + oos_decay -1.888 + mono_sign_flip 0.70/-1.00 三立。RHS Mean(amount,20) 在 P001 rank-diff 7 律 #6 死亡 endpoints amount_20，anchor cluster 跨字段族泛化 — institutional concentration 也不能脱 amount_20 anchor.
>
> **Evidence trail**:
> - [[batches/batch_072/candidates/C003|batch_072 C003]] Sub rank-diff → hg_fail 三立 → reject
>
> **复活路径**: 换 RHS endpoints (脱 amount/turnover/H-L_60 全 family，参考 lessons rank-diff 7 律 #6)；本批不可救.

> [!failure]+ T004 [[directions/institutional_flow_proxy#T004]] — `[✗ DISPROVEN batch_072]` (born-disproven)
> **Question**: Corr(avg_trade_size, $close, 20) OFI proxy 携带机构买涨/买跌 forward signal？
>
> **Answer**: **alpha_surv 杀**. C004 ic_oos=-0.039 ls_t=-3.94 mono PERFECT, 但 alpha_surv=0.25 三立 + dom=vol_20d (style_r²=0.09 低但 dominant 仍 vol_20d). 20d rolling correlation 几何在 csi1000 daily 携带 reversal 但 alpha 不脱 vol_20d basis. low max_corr=0.19 是 noise 独立性非 alpha 独立性.
>
> **Evidence trail**:
> - [[batches/batch_072/candidates/C004|batch_072 C004]] Corr(avg_trade_size,close,20) → alpha_surv=0.25 vol_20d_exp=19 incr=-0.004 → reject
>
> **复活路径**: minute-bar Order Flow Imbalance (需 minute 数据接入，daily 不可行).

> [!failure]+ T005 [[directions/institutional_flow_proxy#T005]] — `[✗ DISPROVEN batch_072]` (born-disproven, library reducer)
> **Question**: institutional × short-momentum cross-product 揭示机构择时方向？
>
> **Answer**: **设计无独立新几何**. C005 ls_t=-7.32 + alpha_surv=0.526 PASS + vol_20d_exp=11.07 (低!), 但 max_corr=0.46@F009 borderline + incr=-0.027 强 NEG → P008 默认 reject. F009 (pv_corr_5 overnight × intraday) cross-product 形式与 C005 (avg_trade_size × 5d momentum) 在 csi1000 cross-section 几何上同源 (机构集中度 × 价格运动方向 ≈ pv_corr 几何变体).
>
> **Evidence trail**:
> - [[batches/batch_072/candidates/C005|batch_072 C005]] Mul rank cross-product → max_corr=0.46@F009 incr=-0.027 alpha_surv=0.526 → reject
>
> **复活路径**: cross-product 在 csi1000 daily 几何空间已被 F009 占位; 跨 family rank-diff 替代.

## 方向级反思

本方向为首批 (round 72) **5 thread 4 born-disproven + 1 partial-progress (T001 via C006 reserve)**：

1. **direction 状态判定**: rounds=1, admit=0, reserve=1 (C006), reject=5. admit/judged=0% 但 reserve 1 火种.
2. **核心 mechanism partial-alive**: 假设 "$num_trades 字段族 (avg_trade_size institutional flow proxy + retail attention proxy) 携带独立 forward signal" — **5/5 PASS-hg 候选 OOS 全 reversal 方向 (mono=-1.0 PERFECT)** 信号方向假设证伪 (机构集中 ≠ forward 强势，是 forward reversal). **但 C006 TsRank 60d 形式独特**: alpha_surv PASS + style_r²=0.15 极清洁 + max_corr=0.24 几何独立，**首次在 csi1000 上看到 $num_trades 字段族干净 cross-section signal** — incr_ic=-0.018 NEG 是唯一阻断, 几何空间未饱和.
3. **关键发现 P009**: **TsRank 时序 60d 形式 vs cross-section level 在 vol_20d 抗衡上有几何分离** — C002 raw rank vol_20d_exp=30.9 → C006 TsRank 同字段 vol_20d_exp=10.87 (降 65%) + style_r² 0.59→0.15 (降 75%). 时序量纲化是新逃 vol_20d 路径候选 (库内 TsRank 极少先例 — 待 lessons 升格).
4. **关键发现 P010**: **alpha_surv > 0.30 但 incr_ic < 0 复合判定**: P008 "Rank-order ≠ Tradable Alpha" 软判定补 P006 hard_block 漏区。C005/C006 触发软判定但根据 max_corr 几何独立性 + 设计层新几何 differentiate reject vs reserve.

**饱和判定**: rounds=1, admit=0, reserve=1, mechanism partial-alive (T001 via C006 火种) — **建议 status: `probing` 维持** (不进 dead, 因为 C006 reserve 提供清洁 fact pattern + 复活路径明确; 也不进 saturated, 因为 rounds<3).

**下一步建议（给 orchestrator）**：

1. **direction-level decision**: [[directions/institutional_flow_proxy]] 维持 `probing` (rounds=1, reserve=1) — C006 复活路径 (a) RHS rank-diff (b) 30d/120d 窗口扫 (c) Python residualize on F009 — 如果下一批续探 C006 火种 incr_ic 仍 NEG 则转 `dead`.
2. **lessons.md 升格候选 (3 条)**:
   - **P009 TsRank time-series rank 抗 vol_20d 吸收路径**: TsRank window≥60d 在 ratio 字段上比 cross-section level 大幅降低 vol_20d_exp (实证 65%↓) + style_r² (75%↓) — 加入 lessons "逃 cluster 启发"段
   - **$num_trades 字段族 raw level 是 size+Amihud 联合代理**: C002 max_corr=0.75@F012 + vol_20d_exp=30.9 — 加入 forbidden pattern "raw $num_trades CsRank default-skip"
   - **P008 alpha_surv>0.30 + incr_ic<0 软判定 reject vs reserve 边界**: 区分依据 = 设计层是否含独立新几何 (max_corr<0.30 + 未被探索的 atom 形式) — 加入 lessons "Rank-order ≠ Tradable Alpha 判别律" 第 3 段
3. **下批方向建议**: 鉴于 zero_admit_streak 已 12 + 三 fundamental 方向 dead (quality_carry/pit_valuation/python_ttm_residual_quality archived/dead) + 本批 reserve only — **强烈建议 orchestrator 启动 Phase 5 consolidation** (rounds_since_consolidation=3 接近 但本批已是 fundamental escape "最后一搏"). 下批不再继续 institutional_flow_proxy 续探，等 consolidation 重写 lessons + INDEX 后再判定.

**饱和叠加 zero_admit_streak**: 12 → 13 (本批仍 0 admit). 三 fundamental 方向 dead + 1 partial-progress (institutional_flow_proxy 留 reserve) — 元 frontier 是否真饱和 vs 阈值过严判定:

**错杀侦测 (calibration trigger 4 条)**:
- ❌ trigger #1 (judge.md "potential over-rejection" 反思): 本批反思无 over-rejection 标记 (5 reject 都有清晰 reject 机理)
- ❌ trigger #2 (连续零 admit + reserve 满足"库空间独立错杀" max_lib_corr<0.30 + incr_ic>0.010): C006 max_corr=0.24<0.30 ✓ 但 incr_ic=-0.018<0.010 ✗ → 不立
- ❌ trigger #3 (累计 reserve/judged > 40%): 本批 reserve 1/6 = 17%, 累计 reserve 1 (C006) — 不立
- ❌ trigger #4 (悖论复现): 无 (低 style_r² + 低 alpha_surv 反直觉指标组合本批未现)

→ **calibration_trigger: false** (绝对禁止"未经诊断就放宽"). 当前真是 alpha 饱和不是阈值过严.

**consolidation_trigger**: **true**（zero_admit_streak=13 + 三 fundamental 方向连续 dead/archived + 本批是 "fundamental escape 最后一搏" + rounds_since_consolidation=3 + 多个 lessons 升格候选堆积 — 强信号触发 Phase 5）
**calibration_trigger**: false（4 trigger 全不立，alpha 真饱和非阈值过严）
