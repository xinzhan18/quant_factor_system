---
batch_id: batch_067
direction: microstructure_illiquidity
judged_at: 2026-05-01T14:10:00Z
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
---

# batch_067 Judge Summary

> [!abstract]+ batch_067 · [[directions/microstructure_illiquidity]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6**
> **核心发现**: T009 (NEW thread) **non-Amihud microstructure proxies (Roll-cov / path-efficiency / Kyle-signed / signed close-mid) 4 atoms 全证伪** —— 6/6 reject 中 3 个 hard_gate fail, 3 个 P006 library-reducer trap (incr_ic ≤ 0.0017 远低于 0.015 dual-gate floor). 直接证实"逃 vol_20d 必撞 anchor"几何困境跨第 4 类 microstructure atom (covariance / path-shape / sign-encoded / valuation-cross) 全部复现.
> **MT Budget**: cumulative 360 → **366** · direction 30 → **36** · bucket `high` (search_adjusted `medium-low`)

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | aligned·**weak**·**poor**·low(neg)·mixed | ic_oos=-0.012 ls_t=-2.12 alpha_surv=0.23 max_corr=0.07 incr_ic=-0.011 | Roll-cov atom 整库最 clean (max_corr=0.07) 但 incr_ic=-0.011 = P006 第 8 次复现; alpha 真实存在但太弱以致库 reducer | [[batches/batch_067/candidates/C001]] |
| C002 | ❌ reject | hard_gate | ic_oos\|0.0011\|<0.008 + decay 0.163 | path-efficiency Mean atom 信号 magnitude 不达 hard floor — bounded ratio 1st-moment 不嵌入 vol_20d 但 alpha density 不足 | [[batches/batch_067/candidates/C002]] |
| C003 | ❌ reject | hard_gate | sign_flip + mono IS=-0.9→OOS=+0.9 | signed close-mid × $market_cap regime catastrophic 翻盘 (size factor regime drift × signed atom) — P003 经典实证 | [[batches/batch_067/candidates/C003]] |
| C004 | ❌ reject | aligned·borderline·**poor**·medium(neg)·**unstable** | ic_oos=-0.028 ls_t=-3.0 mono=-0.9/-0.9 alpha_surv=0.19 max_corr=0.37@F009 incr_ic=-0.010 | Kyle signed-product 区别于 T005 If-gate, ls_t 强 mono 完美但 P006 dual-gate 全中 + cum_mdd=-54.5 — sign 信息不脱 vol_20d basis | [[batches/batch_067/candidates/C004]] |
| C005 | ❌ reject | hard_gate | ic_oos\|0.0009\|<0.008 + decay 0.131 | Roll-cov atom 包入 rank-diff 后 PE RHS 稀释 atom 信号至 0.0009; T007 rank-diff 复合需要 atom 自身 ≥0.015 floor | [[batches/batch_067/candidates/C005]] |
| C006 | ❌ reject | aligned·borderline·borderline·**high**(anti)·stable | ic_oos=+0.020 ls_t=2.37 mono=1.0/1.0 PERFECT alpha_surv=0.41 max_corr=-0.59@F020 incr_ic=0.0017 | 唯一正 IC + 完美单调 + cum_mdd=-1.12 极浅 PnL 美感, 但 max_corr=-0.59@F020 anti-cluster + incr_ic=0.0017<<0.015 dual-gate floor = "P006 illusion form" | [[batches/batch_067/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色.

## 跨候选对比

**Style 聚合**：6/6 候选 `dominant_style_exposure = vol_20d`. style_exposures.vol_20d 系数对比 (本批最大值同时是整库顶级):
- C006 path-efficiency × ps rank-diff: vol_20d=**17.63** ⚠️ 整库顶级极值 (efficiency ratio 看似 bounded [0,1] 但深度嵌入 vol_20d)
- C004 Kyle signed: vol_20d=9.32 (signed body / amount 深度 vol_20d 嵌入)
- C001 Roll-cov: vol_20d=7.26 (Roll covariance 看似 vol-orthogonal 但 cross-section 仍部分嵌入)
- C002/C003/C005 hard_gate fail 未深判但同样 vol_20d-dominant

**P004 vol_20d structural absorption 第 N 次复现**: 三种 atom 对 vol_20d 的"伪正交"机制不同 (Roll-cov 走 covariance, Kyle 走 sign-product, path-efficiency 走 bounded ratio), 但 cross-section rank 全部与 vol_20d 高度相关 — **几何形式的不变性**: csi1000 daily-bar 上 vol_20d 是 cross-section 主成分, 所有衍生 atom 都被吸收.

**P006 library-reducer trap 第 8/9/10 次跨 family 复现**: C001 + C004 + C006 三个 PASS hard_gate 候选**全部** incr_ic 远低于 0.005 floor 或为负:
- C001: incr_ic=-0.011 (NEG, max_corr=0.07 库内最 clean) → "geometric clean + Barra-poor + library-reducer" 三重 signature
- C004: incr_ic=-0.010 (NEG, max_corr=0.37 dead zone) → "P006 dual-gate 全中"
- C006: incr_ic=+0.0017 (POS 但远低于 0.015 floor, max_corr=0.59 borderline-high) → "PnL 形状美但库 reducer"

**关键观察**: 本批 P006 trap 三种形式 typology 完整呈现:
1. **C001 型 (clean-but-empty)**: max_corr<0.10 整库最 clean + incr_ic NEG + alpha_surv poor — atom 几何独立但 alpha density 不足
2. **C004 型 (dead-zone-classic)**: max_corr in [0.30, 0.70] + incr_ic NEG + 强 PnL (ls_t>3) — 经典 dead zone trap
3. **C006 型 (illusion-form)**: max_corr in [0.30, 0.70] + incr_ic POS but << 0.015 + mono PERFECT + cum_mdd 极浅 — PnL 美感掩盖 incremental 价值

**MT 预算推进**: cumulative 360→366; direction 30→36; bucket `high` 不变. search_adjusted 在 medium-low 间. 6/6 reject 后 microstructure direction 累计 36 候选 / 4 admit (直方图 11.1% admit rate, 仍 above lessons saturation 阈值但已步入 saturated 边缘).

## Thread 进展

> [!failure]+ T009 [[directions/microstructure_illiquidity#T009]] 🆕 — `[✗ DISPROVEN batch_067]` (NEW thread, born-disproven)
> **Question**: non-Amihud microstructure proxies (Roll covariance / path-efficiency / Kyle signed / signed close-mid imbalance) 是否在 csi1000 daily-bar cross-section rank-diff 几何下携带独立于 Amihud (F012/F015/F016) family 的新 alpha?
>
> **Answer**: **non-Amihud microstructure 4 atoms 在 daily-bar 层全证伪**. 不论几何形式 (covariance / bounded ratio / signed product / signed positional), atom 全部 cross-section vol_20d-嵌入 (P004) + 全部库 anchor cluster locked (P005, F009/F020/F022 anchor) + PASS hard_gate 三候选 P006 dual-gate 100% 命中 (C001/C004/C006 incr_ic 均 ≤ 0.0017).
>
> **Evidence trail**:
> - [[batches/batch_067/candidates/C001|batch_067 C001]] Roll-cov level → ic_oos=-0.012 + max_corr=0.07 库内最 clean + incr_ic=-0.011 NEG + alpha_surv=0.23 → reject (P006 第 8 次复现, "clean-but-empty" 形式)
> - [[batches/batch_067/candidates/C002|batch_067 C002]] path-efficiency Mean → |IC_OOS|=0.0011 + decay 0.163 → reject (hard_gate, atom alpha density 不足 floor)
> - [[batches/batch_067/candidates/C003|batch_067 C003]] signed close-mid × $market_cap rank-diff → sign_flip + mono IS=-0.9→OOS=+0.9 catastrophic regime reversal → reject (hard_gate, P003 第 N 次实证: signed positional × size factor regime drift)
> - [[batches/batch_067/candidates/C004|batch_067 C004]] Kyle signed-product → ls_t=-3.0 + mono=-0.9/-0.9 强 + max_corr=0.37@F009 dead zone + incr_ic=-0.010 NEG + cum_mdd=-54.5 → reject (P006 第 9 次复现, "dead-zone-classic" 形式)
> - [[batches/batch_067/candidates/C005|batch_067 C005]] Roll-cov × pe rank-diff → |IC_OOS|=0.0009 + decay 0.131 → reject (hard_gate, T007 复合需 atom alpha ≥ 0.015 floor)
> - [[batches/batch_067/candidates/C006|batch_067 C006]] path-efficiency × ps rank-diff → ic_oos=+0.020 + mono=1.0/1.0 PERFECT + cum_mdd=-1.12 极浅 + max_corr=-0.59@F020 anti-cluster + incr_ic=+0.0017<<0.015 dual-gate → reject (P006 第 10 次复现, "illusion-form" 新形式)
>
> **升格 lessons 候选** (本 thread 贡献 3 条):
> 1. **non-Amihud microstructure atom 4 类几何全证伪 (csi1000 daily-bar)**: covariance / bounded-ratio / signed-product / signed-positional 4 类 LHS atom 形式跨 round 1-3 (rolling-regression / Skew-Kurt / Roll-Kyle-efficiency-imbalance) 全部 vol_20d-locked. minute-bar 数据接入前 microstructure direction daily-bar 探索路径关闭.
> 2. **P006 illusion-form 升格** (C006 新形态): mono=1.0 perfect + cum_mdd<-5 浅 + incr_ic<0.005 极低 + max_corr in [0.30, 0.70] = "PnL 美感掩盖 incremental 价值" trap. 应 codify 至 lessons.md P006 顶部反例段防止后续 LLM 被 PnL shape 美感诱导.
> 3. **F020 anchor cluster 跨 LHS/RHS 角色泛化**: F020 的 path-efficiency atom 作 RHS, 本批 C006 把同 atom 搬到 LHS, 仍 anti-cluster -0.59 — anchor 不仅占据 LHS+RHS 字段配对, 还占据 atom 在 Sub 两侧角色调换的 anti-mirror 位置 (P005 第 N 次扩展).
>
> **保留 OFF**: T009 thread closed. **复活路径**: (a) minute-bar 数据接入 (intraday Roll-cov / path-efficiency 在 5min bar 不被 daily vol 吸收); (b) F020 / F012 退役后重测 path-efficiency atom + ps_ratio rank-diff (C006 cum_mdd=-1.12 极浅 PnL 形状有 standalone value, 仅库 anchor 限制 admit); (c) Python OLS Barra residualize (DSL `Div(atom, vol_20d)` 不是真 orth, 已升格 lessons F304).

## 方向级反思

**核心律**: 本批揭示 microstructure_illiquidity direction 在 csi1000 daily-bar 上的**结构性边界**:
1. **Amihud family 已饱和** (F012/F015/F016 占据 Mean(|ret|/amount) 跨 amount/turnover-CV 全部 rank-diff 端点)
2. **non-Amihud microstructure atom 4 类几何全证伪** (本批 T009)
3. **rank-diff geometry 跨 RHS family 全部撞 anchor** (本批 C003/C005/C006 三 rank-diff 候选: market_cap RHS regime drift / pe_ratio RHS atom alpha 不足 / ps_ratio RHS F020 anti-cluster)

**P004 vol_20d structural absorption 跨第 4 类 atom 复现**:
- Round 1 (rolling-regression Slope/Resi/Rsquare on $close): vol_20d-locked
- Round 2 (Skew/Kurt/autocorr/Rank-wrap): vol_20d-locked (regime-stable shape moments 也 absorb)
- **Round 3 本批 (Roll-cov/path-efficiency/Kyle-signed/signed-close-mid)**: vol_20d-locked + P006 trap 三形式齐全
- 跨 9+ direction 60+ 候选独立证实 csi1000 daily-bar cross-section 上 vol_20d-orthogonal subspace 已被 F002/F012/F018/F020/F022/F023 anchor cluster 完全占据

**zero_admit_streak**: b066=6 → b067=7 (连续 7 批 zero admit) → orchestrator 累计 zero_admit_streak 至 8.
**rounds_since_consolidation**: 7 → 8 (距 10 阈值还有 2 批, 临近触发).

**错杀侦测**: 本批无候选触发完整错杀 flag (max_corr<0.30 + incr_ic>0.010 + mono>0.8 + sign=1.0 全部命中). 最接近的 C001 (max_corr=0.07 ✓, sign=1.0 ✓) 但 incr_ic=-0.011 NEG 不达 0.010 floor → 不属错杀, 是 alpha 真实不足.

**direction status 提议**:
- 现状: productive(low) · 6 rounds · 4 admits
- 本批 6/6 reject (T009 NEW thread born-disproven 4 atoms)
- T005/T008/T009 三 thread 全 DISPROVEN, T007 ACTIVE 但本批未推进, 累计仅 T001/T006 ANSWERED + 4 admits
- 信号设计层证据: ≥4 路径 cluster (Amihud-family + non-Amihud 4 atoms 全 closed) ✓
- 数据契约层证据: minute-bar 不可达 + Python OLS Barra residual 已尝试 (T004 DISPROVEN at b031) ✓
- 双层 saturated 证据律满足 → **status: productive → saturated** 提议
- priority: low → low (保持; 等 minute-bar 接入或 F012/F020 anchor 退役)

**MT Budget 状态**: cumulative 360→366 · direction 30→36 · bucket `high` (search_adjusted `medium-low`)

**下轮建议** (orchestrator 级):
1. **本方向 saturated**: 转 saturated 状态, 关闭 daily-bar 探索路径. 等 minute-bar 数据接入或 F012/F020 anchor 退役后重启.
2. **下批方向切换**: zero_admit_streak=7→8 + microstructure direction 转 saturated, 应切换至剩余 productive direction. 当前剩余 productive: ohlc_temporal_aggregation (5 admits, 8 rounds) / overnight_intraday_split (9 admits, 12 rounds, 已临近 saturated). 严避近期连续 0-admit 的 saturated direction (range_structure / vwap_proxy_signals / barra_residual_alpha).
3. **consolidation 临近触发** (rounds_since_consolidation=7→8, 距 10 阈值 2 批): 升格教训累积 — P006 illusion-form (C006 新形态) + non-Amihud microstructure 4 atom 全证伪 + F020 anchor 跨 LHS/RHS 角色泛化 三条值得 lessons.md 升格.
4. **C006 reserve 火种** (微弱建议): cum_mdd=-1.12 极浅 + mono=1.0 perfect + 9/9 年全正 magnitude 稳定, 等 F020 退役或长 horizon evaluation policy 调整 (10d-20d C006 IC 上升 0.034-0.051) 后可重测.
