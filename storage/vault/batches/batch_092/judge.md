---
batch_id: batch_092
direction: tsrank_candlestick_ratio
judged_at: 2026-05-16T03:00:00Z
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

# batch_092 Judge Summary

> [!abstract]+ batch_092 · [[directions/tsrank_candlestick_ratio]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6** (2× hard_gate fail + 4× cluster/vol-proxy collapse)
> **核心发现**: Reserve revival pool #2 (b076/C005 复活路径) **彻底证伪** — 5 条 revival path 沿 5 个独立 axes 全部 disproven。**(1) Python residualize on (F008, F026)** sign-flip OOS (train +0.030 → val -0.004) — round 73 警告律 first实证, residualize 在 close-position cluster 上 produce 残差噪音; **(2) RHS swap close→Mean(close,5)** 反而进入 F027 close-MA cluster (max_corr=0.60@F027, sty_r²=0.128 vol_20d 嵌入); **(3) 30d 短窗** 撞 F026 几何同源 (max_corr=0.83 near_duplicate); **(4) rank-diff form** 信号自抵消 (ic_oos=0.0015 hard_gate fail); **(5) open-close 中点** 仍 max_corr=0.64@F026; **(6) range/close 范围/收盘** 重现 b076/C004 vol_20d proxy pattern (sty_r²=0.133 + incr_ic=-0.030 NEG + alpha_surv=0.986 边缘 — P030 多 CP 集体失败).
> **方向状态**: status=saturated 维持, b077 frontier 上限饱和铁证 + b092 reserve revival 彻底失败 = **direction 全死铁证**, b093+ 不再 retry tsrank_candlestick_ratio 任何 path. F025 absorbing prototype 律 (P021) 进一步实证: 高 alpha 单 reserve b076/C005 也无法逃 F008/F026 cluster.
> **MT Budget**: cumulative 510 + 6 = **516** · direction 12 → **18** · bucket `high` (上界)

## 候选一览

| ID | Verdict | 档位 (CP02·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | **hard_gate (sign_flip)** | train_ic=+0.030 / val_ic=-0.004, mono_flip 0.4→-0.4, max_corr=0.23 clean **but** sign_consistency=0.5 | Python residualize on (F008, F026) 残差化后 atom 信号塌缩为噪音, 残差 sign 在 train/val 翻转 (round 73 lesson 警告律 first实证) | [[batches/batch_092/candidates/C001]] |
| C002 | ❌ reject | aligned · weak · **borderline** · **high** · stable | ic_oos=-0.025, ls_t=-1.80 weak, **max_corr=0.60@F027** cluster, sty_r²=0.128, vol_20d_exp=15.0, incr_ic=-0.020 NEG | RHS swap close→Mean(close,5) 反而把信号送进 F027 (4-MA cluster of close) 几何, vol_20d 嵌入加重 | [[batches/batch_092/candidates/C002]] |
| C003 | ❌ reject | aligned · strong · acceptable · **near_dup** · stable | ic_oos=+0.036, ls_t=+4.69, alpha_surv=1.48 顶级, **max_corr=0.83@F026** near_duplicate, incr_ic=+0.009 | 30d 短窗反而进入 F026 几何同源 — 短窗 mid/close TsRank ≈ F026 (close-position 60d TsRank) sign-flipped duplicate | [[batches/batch_092/candidates/C003]] |
| C004 | ❌ reject | **hard_gate (ic_oos_too_low + oos_decay)** | ic_oos=0.0015 < 0.008, oos_decay=0.107 < 0.2 | rank-diff form (Sub(TsRank60, TsRank20)) 双窗 self-cancellation, OOS 信号塌至 0 | [[batches/batch_092/candidates/C004]] |
| C005 | ❌ reject | aligned · strong · acceptable · **high** · stable | ic_oos=+0.033, ls_t=+2.80, alpha_surv=1.37, **max_corr=0.64@F026** cluster, incr_ic=+0.016 | open-close 中点 = monotonic 等价 O/C ratio, 通过 close-position 几何撞 F026 | [[batches/batch_092/candidates/C005]] |
| C006 | ❌ reject | aligned · strong · **borderline** · **low** · stable | ic_oos=-0.037, ls_t=-3.43, mono PERFECT (-1.0), **max_corr=0.30@F027 clean**, **sty_r²=0.133 OVER**, **vol_20d_exp=12.6**, **alpha_surv=0.986**, **incr_ic=-0.030 NEG** | range/close 重现 b076/C004 vol-proxy 几何 — max_corr 库空间独立 (0.30!) 但 cross-section ranking 完全由 vol_20d 主导 (P030 多 CP 失败: incr_ic NEG + alpha_surv 边缘 + sty_r² OVER) | [[batches/batch_092/candidates/C006]] |

## 跨候选对比

本批 6 候选沿 6 个独立 axes 探索 b076/C005 (T001 + T003) revival pool #2:

| Axis | Candidate | revival path | 结论 |
|---|---|---|---|
| Python residualize | C001 | finding/013 主路径: OLS on (F008, F026) | **DISPROVEN** — sign_flip OOS (train→val IC flip + mono_flip), 残差化丢失了 atom 真信号. round 73 警告律 (cross-section OLS residual OOS sign-flip) **first 实证案例** |
| RHS swap | C002 | close → Mean(close,5) 切 F008 同源 | **DISPROVEN** — 反而进入 F027 (Mean close 4-window MA) cluster, max_corr 0.60 > 0.30; sty_r²=0.128 over, vol_20d_exp=15.0 高于原 atom |
| Window sweep 短 | C003 | 60d → 30d | **DISPROVEN** — 30d max_corr=0.83@F026 near_duplicate; 短窗 mid/close TsRank 与 F026 close-position TsRank 几何收敛 |
| Rank-diff | C004 | Sub(TsRank60, TsRank20) 同 atom 跨窗 | **DISPROVEN** — hard_gate ic_oos=0.0015 (信号自抵消); rank-diff axis 在 close-position 域 self-cancellation 极严重 |
| Alt midpoint | C005 | (O+C)/2 替 (H+L)/2 | **DISPROVEN** — max_corr=0.64@F026 cluster; (O+C)/(2C) monotonic ≈ O/C, 仍是 close-position 几何家族 |
| P008 third ratio | C006 | (H-L)/close 替 mid/close | **DISPROVEN** (intentional probe) — max_corr 唯一 LOW (0.30@F027) 但 sty_r²=0.133 + dom_style=vol_20d + incr_ic=-0.030 NEG + alpha_surv=0.986 边缘. P030 多 CP 集体失败铁证 — alpha_surv 单边并非充分 |

**跨候选相关性 / 几何收敛模式**:

- **C002/C003/C005 都撞 F026/F027 cluster** (close-position 60d TsRank 或 close 4-window MA family) — 任何 numerator/denominator/window 微调都不改 cross-section ranking 几何
- **C006 唯一 max_corr 脱 0.30** (撞 F027 但 just under line) 但 vol_20d 几何接管 — 印证 finding/013 expected_outcome failure mode: max_corr 与 sty_r² 是两个独立维度, 库空间独立 ≠ alpha 独立
- **C001 唯一 OOS sign-flip** (round 73 警告律) — Python residualize 路径在 close-position cluster 是错误的方向 (cluster 内不存在残差 alpha, residual 是噪音)
- **C004 rank-diff 唯一信号塌缩** (ic_oos=0.0015) — rank-diff axis 在 close-position TsRank 域 (与 b091/C004 amount/num_trades 不同) self-cancellation 极严重, axis 在该 atom 类不普适

## Thread 进展

### T001 — Close position & shadow ratio `[✗ DISPROVEN deepened batch_092]`

**Round 91 state**: partial DISPROVEN — cross-section 几何同源律 (close_position / shadow ratio 单原子 60d TsRank 与库 F006/F008/F011 共线性 0.4-0.5 不可解).

**Round 92 update**: **复活路径全失败铁证** — Python residualize (C001 hard_gate sign_flip), RHS swap (C002 max_corr 0.60 cluster), 短窗 (C003 max_corr 0.83 near_dup), open midpoint (C005 max_corr 0.64) 全 disproven. close-position cluster (F008 / F025 / F026 / F027 / F028) 形成 cross-section 几何盆地, atom 几何变体无法逃逸.

### T003 — Range / midprice / asymmetry `[✗ DISPROVEN deepened batch_092]`

**Round 91 state**: PROVEN (F025 admit) — 高阶 composition 真红利铁证.

**Round 92 update**: **复活 reserve 中边缘 (b076/C005 max_corr=0.449) 失败铁证** — 5 条 axes 全 disproven. F025/F026 absorbing 律 (P021 round 91) 在 round 92 加深: **admit prototype 在 cluster 半径 0.45 内的所有几何变体都被吞噬, 包括 reserve 边缘候选**. 唯一进一步路径 (Python residualize) 因 cross-section OLS OOS sign-flip 也被关闭.

### T004 — admit-后 frontier 上限测试 `[✗ DISPROVEN deepened batch_092]`

**Round 91 state**: DISPROVEN — frontier 上限饱和 (b077 6/6 reject).

**Round 92 update**: **reserve revival 也失败 — frontier 上限 + reserve cluster 联合饱和**, direction 整体 dead 铁证.

## 候选反思（4 层）

### Layer 1 — 候选间结构对比

**Cluster collapse axis** (C002/C003/C005): 三种 RHS / window / numerator 变体都撞 close-position TsRank cluster (F026 是主吸引子):
- C002 max_corr=0.60@F027 (close 4-window MA)
- C003 max_corr=0.83@F026 (close-position 60d TsRank)
- C005 max_corr=0.64@F026
- **机制**: TsRank 时序量纲化在 60d 窗口内对 close-position 几何形成 cross-section ranking attractor, F026 是几何中心, 任何 (h+l)/2 / close 或其变体在 60d TsRank 都 monotonic-related to F026

**Vol-proxy axis** (C006): 唯一 max_corr LOW (0.30@F027) 但 sty_r²=0.133 + dom_style=vol_20d:
- range/close = (H-L)/C 直接是日内 vol proxy, cross-section ranking 由 vol_20d 主导而非 close-position 几何
- **机制**: 库空间独立 (max_corr<0.30) 与 alpha 独立 (alpha_surv>>1.0) 是**两个独立维度**, 单一指标不能 substitute. P030 round 91 升格律在本批 first实证

**Sign-flip axis** (C001): Python residualize 失败:
- train_ic=+0.030 / val_ic=-0.004, monotonicity train +0.4 / val -0.4
- 残差化丢失了 atom 真信号 — atom IC 主要由 F008+F026 投影承载, residual 是噪音
- **机制**: 当 atom 与 (F008, F026) 共线性高 (b076 实测 max_corr=0.449 / b092 cp05 0.43@F008 + 部分 F026 投影), residual 等于 "removed dominant projection 后剩下的噪音", 该噪音在 train 因 OLS 过拟合表现出 sign, OOS 噪音独立性使 sign 消失/翻转

**Self-cancellation axis** (C004): rank-diff form 信号塌缩:
- ic_oos=0.0015 hard_gate fail (vs C002/C003/C005 ic_oos 0.025-0.036 量级)
- 与 b091/C004 (amount/num_trades 域 rank-diff alpha_surv=0.86 escape success) 强烈对比 — rank-diff axis 在不同 atom 类有不同 behavior. close-position 域 60d-20d 双窗在 cross-section 是高度 redundant (短窗已经 contain 长窗 ranking 主要信息), Sub 让有效信息相互抵消

### Layer 2 — MT 预算

- batch-level cumulative_candidates 510→516, bucket `high` 维持
- direction-level 12→18 (本批 6 全 judged)
- 所有 5 个 hard_gate 通过候选 mt_bucket=high → CP03 即使 strong 也降至 borderline
- C001 / C004 hard_gate fail 直接 reject 不进 MT bucket weighting

### Layer 3 — Thread 进展

**T001 / T003 / T004** 全部从 partial-disproven / disproven 加深至 **fully-disproven**. 本批 6/6 reject 是 direction-level dead 的铁证 — F025/F026 absorbing prototype + close-position cluster 联合形成不可逃逸盆地.

### Layer 4 — Cockpit hint 验证（round 92 generator self-check 4 hard rules first实证）

本批是 round 92 新增 4 hard rule 的 first-batch 实证窗口:

1. **P030 (alpha_surv unilateral ≠ admit 充分)**: **PROVEN in C006** — alpha_surv=0.986 + mono PERFECT + max_corr=0.30 clean 但 sty_r²=0.133 + incr_ic=-0.030 NEG, P030 多 CP 失败模式 first实证案例. 升格"P030 multi-CP 集体保护"律: alpha_surv / mono / max_corr 任 1 单边 + 另 2 反向时直接 reject, 不依赖 single CP score
2. **P004-deep (N-day path-integral default reject)**: 本批无候选触发 (全 single-step TsRank), 自检 pass — 但 round 92 lesson 升格"TsRank(x, N) 是 single-step rank, 不是 N-day cumulative" 与 Sub(TsRank60, TsRank20) 不是 path-integral 已 codified at round 91
3. **Cov-equiv (cross-field Cov bug)**: 本批无 Cov 候选, 自检 pass
4. **Reciprocal monotonic duplicate**: 本批 C001-C006 6 候选无 reciprocal 互换 — generator self-check ✓. round 91 cockpit "TsRank(1/x,N) ≈ N+1-TsRank(x,N)" 实证 first已于 b091/C005, round 92 进一步细化: reciprocal 律对 (h+l)/2/close 与 close/(h+l)/2 (Div numer/denom 互换) **同律生效**, 不另设 reciprocal probe

**P008 escape window upper bound** (round 91 cockpit): b091 实测 TsRank window>90d alpha_surv 反单调下降. 本批 C003 (30d) max_corr=0.83 实证 TsRank window<60d on close-position ratio 进入 F026 几何盆地 — **window 下界**也确认: TsRank window<60d 撞 admit prototype (F026 is 60d TsRank). 完整律: **TsRank window 在 close-position 域只在 60d sweet spot, <30d 撞 admit prototype, >90d 进入 cumulative-style 几何**. 本批升格 round 92 新发现.

**F024 anchor basin width≥90d** (round 91): 本批 C006 max_corr=0.30@F027 (close 4-MA cluster), close-position family 与 trade-density family (F024 anchor) 几何独立 — F024 basin 不延伸到 close-position 域. 但 close-position 域有**自己的** anchor: F026 (b082 admit) + F025 (b076 admit) + F027/F028 (close-MA cluster). **升格: cross-family anchor basin 是 family-internal 现象, 不互相延伸**.

## 给 b093 的建议

1. **direction status 维持 saturated**, b093+ 不再触碰 tsrank_candlestick_ratio (T001/T003/T004 全 fully-disproven), 6/6 reject 铁证 + reserve revival 全失败
2. **切换到 untested family** — 当前 28 admit 集中于 OHLC / liquidity / valuation; 推荐探索:
   - **跨期 momentum 残差** (overnight - intraday consistency family, F009/F010 邻域未深探)
   - **microstructure low-correlation family** (F024 trade-density 是孤岛, 该 family 可深探)
   - **fundamentals × OHLC product** (TTM × ohlc shape, batch_080/C006 overnight×turnover rank-diff 复活路径 finding/013 path 3)
3. **Python residualize 路径升格律** — **不在 close-position cluster 上 residualize** (close-position 是 inseparable cluster, residual = 噪音). Python residualize 适用场景: atom 与库 factor cluster 距离 0.30-0.50 borderline 时, 且 atom signal not dominated by cluster projection (b076/C005 实测 max_corr 0.449 + alpha_surv 1.43 — atom 主信号在 cluster 投影内, residualize 自然失败). 适用 candidate filter: max_corr ∈ [0.30, 0.45] **且** barra_residual_ic > 0.020 (signal not dominated by style proj). 升格 → lessons round 92
4. **rank-diff axis** 在不同 atom 类有不同 behavior — b091 amount/num_trades 域 escape success (alpha_surv=0.86), b092 close-position 域 self-cancellation (ic_oos=0.0015). 升格: rank-diff axis 有效需 atom cross-section dispersion 高 (b091 amount 域 cross-section IC dispersion 大, b092 close-position 域 dispersion 小)
5. **next direction candidate**: 推荐 b093 切 `cross_period_momentum_residual` (F009/F010 邻域) 或 fundamental_ttm 路径 (last admit batch_068 之前)

## Calibration check

- 错杀 flag: 本批无候选 4+ CP top 仅 1 边缘卡 — C006 mono PERFECT + max_corr clean 但 alpha_surv=0.986 + incr_ic NEG + sty_r²OVER 三边缘 = P030 多 CP 集体失败, 不是错杀
- 连续零 admit 警戒: zero_admit_streak 5 → **6** (本批 0 admit). 本批 reserve=0 也无满足 (max_lib_corr<0.30 + incr_ic>0.010) 的 reserve 火种 — C001 max_corr=0.23 LOW 但 hard_gate sign_flip; C006 max_corr=0.30 LOW 但 incr_ic=-0.030 NEG. **calibration trigger=false** (满足 (a) 连续零 admit ≥3 但 不满足 (b) reserve 火种存在)
- Reserve 积压: 累计 reserve/judged < 40% (round 91 reserve pool snapshot 87/total = ~10%)
- 悖论复现: 本批 first实证 P030 多 CP 集体失败模式 (C006), 不是悖论是 P030 升格律的 first应用
- **结论**: calibration_trigger=false, **consolidation_trigger=false** (round_since_consolidation=1, 远 <10), 但 **direction-saturation-trigger** 触发: tsrank_candlestick_ratio direction 进入 fully-dead 状态, b093 须切下一 direction
