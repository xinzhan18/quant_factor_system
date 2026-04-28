---
batch_id: batch_061
direction: microstructure_illiquidity
judged_at: 2026-04-28T04:35:00Z
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

# batch_061 Judge Summary

> [!abstract]+ batch_061 · [[directions/microstructure_illiquidity]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6** (C001/C002/C003/C004/C005/C006)
> **核心发现**: T008 NEW thread (atp = $amount/$volume avg-trade-price as new microstructure atom) **全军覆没** — 4 代 atp 几何变体 (atp-close-deviation Mean/Std + atp_range_position Mean) × 4 个 fresh RHS basis (Std turnover_60 / Mean pe_60 / Mean ps_60 / Med turnover_20) **6 候选全 reject**。**关键升格**: **F017 anchor cluster 范围扩大** — F017 (overnight × turnover_5 rank-diff) 不仅是 turnover_5 RHS 的 anchor,也是 **任何 amount-derived LHS × turnover-family RHS** 几何位置的 cross-section 占位 anchor; 4/6 候选 (C001/C004/C006/C003 nearby) max_corr 0.51-0.60@F017 验证。**T005 quantile-Amihud 路径 P006 library-reducer 陷阱** (C005: mono=1.0/1.0 + ls_t=3.21 但 incr_ic=-0.0023 NEG + alpha_surv=0.39) — 强单调强 ls_t 但库内冗余,**P006 第 6 次跨 family 复现**。
> **MT Budget**: cumulative 318 → **324** · direction 24 → **30** · bucket `high` 持续 (search_adjusted ≈ 0.51 → medium) · 本批 6 候选 5/6 high bucket。**zero_admit_streak 1 → 2**

## 候选一览

| ID | Verdict | 档位 (CP3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟠·🟢·🔴·🟢 | ic_oos=0.039 ls_t=1.60 mono=0.9/0.9 alpha_surv=0.45 incr_ic=+0.0098 max_corr=0.531@F017 | T008 baseline atp-close-deviation Mean 20d × Std(turnover,60) — atp/close LHS 是 NEW atom (vs F012/F015/F016 Amihud family OK + 与 F019/F020/F021 OHLC family 全 corr<0.30 OK) BUT max_corr=0.53@F017 cluster co-resonance + **incr_ic=0.0098 < 0.015 borderline 死区** (CP05 high 决策档下界 0.015 未达) + ls_t_oos=1.60 essentially zero (本批 atp-close-dev 类候选共有问题: cross-section IC 健康但 long-short tradable 不显著)。**关键发现**: atp atom 真实正交于 F012/F015/F016 (Amihud family — corr 全 -0.10 to 0.04) + 正交于 F019/F020/F021 OHLC family (corr 0.19/-0.23/0.30) BUT 与 F017/F018 overnight rank-diff family corr=0.53/0.16 → atp/close 几何位置是 overnight × turnover RHS family rank-diff 范式的 cross-section partial mirror。 | [[batches/batch_061/candidates/C001]] |
| C002 | ❌ reject | 🔴·🔴·🔴·🟢 | ic_oos=-0.035 ls_t=-2.74 mono=-1.0/-1.0 alpha_surv=0.17 incr_ic=-0.0086 max_corr=0.282@F002 | T008 higher-moment atp 派生量 — Std(atp-close-deviation,20d) × Mean(pe,60) — **alpha_surv=0.17 critical** (vol_20d=51.79 极端 + book_to_price=0.62 + str_1m=0.45) + 9/9 yr 同号负 (mono perfect) + ls_t=-2.74 strong + cum_ic_mdd=-55.89 catastrophic + worst_quarter_ic=-0.057。**P003 higher-moment regime sign-flip 律 + P006 library-reducer 双重命中**: 9/9 yr 单调改进 sign consistency 1.0 但 IS-OOS 同号深亏 → vol_20d 嵌入 Std(atp-close-dev,20) 几何 (atp-close-dev 单日 magnitude 与 vol_20d 在 cross-section 上同构,Std 二阶聚合放大耦合) + Mean(pe,60) RHS PE Barra basis。**P003 跨 family 第 N 次复现**: atp-close-deviation 即使是 NEW atom,wrap Std/Var 二阶聚合后立刻被 vol_20d 吸收 — **higher-moment LHS independence axis 不能通用迁移到 atp-close family** (单日 atp-close 与单日 |return| 共享 vol_20d 几何位置)。 | [[batches/batch_061/candidates/C002]] |
| C003 | ❌ reject | 🔴·🟠·🟡·🟠 | ic_oos=0.030 ls_t=0.94 mono=1.0/0.9 alpha_surv=0.32 incr_ic=+0.0084 max_corr=0.305@F021 | T008 atp_range_position Mean 20d × Mean(ps,60) — 第二个 NEW atom (atp 在日内 range 中位置 vs F022 close 在 range 中位置) — 几何 fresh + max_corr=0.305@F021 borderline + alpha_surv=0.32 (rank-diff floor 0.30 刚过) + **ls_t=0.94 < 2 weak** (CP03 阻断档) + incr_ic=0.0084 < 0.015 borderline 死区 + ls_sharpe=0.68 long-short 弱投资。**关键发现**: atp_range_position 与 F021 (upper_shadow_disp_range_compress) 几何位置接近 (corr=0.305) — atp 在 range 中的位置 vs upper_shadow 在 range 中的扩展 是 OHLC range 内部位置的两个 facet, F021 已 partial 占据 atp_range_position 的 cross-section 几何投影 (range 内部位置类信号通用 RHS 锁定)。 | [[batches/batch_061/candidates/C003]] |
| C004 | ❌ reject | 🟠·🟠·🔴·🟢 | ic_oos=0.048 ls_t=1.48 mono=0.9/1.0 alpha_surv=0.33 incr_ic=+0.0117 max_corr=0.603@F017 | T008 atp_range_position Mean 5d × Med(turnover,20) — 短窗变体 + Median (而非 Mean) RHS 测稳健性 — IC_oos=0.048 是本批 atp 系列最高 + ls_sharpe=1.07 + alpha_surv=0.33 (rank-diff floor 刚过) BUT **max_corr=0.603@F017 cluster co-resonance + incr_ic=0.0117 < 0.015 borderline 死区** + ls_t=1.48 < 2。**与 C001 同病**: atp/close LHS 在 5d 短窗 + Median turnover 仍落在 F017 anchor cluster (overnight × turnover-family RHS) — Mean/Median RHS 替换不脱 F017 几何吸收。**Anchor rule 5 同批 LHS 共享 anchor**: C003 与 C004 共 atp_range_position LHS,只能 admit 1,但本批 C003/C004 都不达标。 | [[batches/batch_061/candidates/C004]] |
| C005 | ❌ reject | 🟢·🟠·🔴·🟢 | ic_oos=0.0114 **ls_t=3.21** mono=1.0/1.0 alpha_surv=0.39 **incr_ic=-0.0023** max_corr=0.542@F012 | T005 ANSWERED restart — quantile-Amihud P90-P10 rolling 20d × Mean(pe,60) — **本批最强 ls_t (3.21) + 完美单调 mono=1.0/1.0 + 9/9 yr 全正 + ls_sharpe=2.31 ls_calmar=3.04 整批最优 PnL 形状 + alpha_surv=0.39 (rank-diff floor 0.30 刚过) + style_r²=0.20 (本批最低) + vol_20d=7.47 (本批最低 — 最干净)** BUT **incr_ic=-0.0023 NEGATIVE → P006 library-reducer 第 6 次跨 family 复现** (mono≥0.85 + |ls_t|≥2.5 + incr_ic<0 + alpha_surv<0.40 全部命中)。**T005 quantile path 结果**: P90-P10 of |return|/$amount 真实独立于 F012 (Mean) 与 F015 (CV=Std/Mean) — corr=0.542@F012 仅 borderline,但与 F015/F016 corr=0.366/0.360 → quantile spread 几何位置在 F012/F015/F016 三 Amihud rank-diff anchor 上 partial 重叠,加入它让组合信号变弱。**Phase 5 升格 lessons 候选**: "Amihud quantile spread (P90-P10) 与 Mean (F012) + CV (F015/F016) 几何线性独立但 Barra 投影组合冗余 — 三 Amihud factor 联合已捕获分布形状 sufficient statistic"。**T005 thread DISPROVEN** (quantile path 是被 library 吸收的)。 | [[batches/batch_061/candidates/C005]] |
| C006 | ❌ reject | 🟠·🟢·🔴·🟢 | ic_oos=0.038 ls_t=1.48 mono=0.9/1.0 alpha_surv=0.45 incr_ic=+0.0089 max_corr=0.529@F017 | T008 长窗变体 atp-close-deviation Mean 60d × Std(turnover,60) — C001 的 60d 版本测窗口 sweet spot — IC_oos / ls_sharpe / alpha_surv 与 C001 几乎相同 (说明 atp-close-dev 信号 20d/60d 同构) + max_corr=0.529@F017 同样 cluster + incr_ic=0.0089 < 0.015 borderline 死区。**Anchor rule 5 同批 LHS 共享 anchor**: C001 与 C006 共 atp-close-deviation LHS + Std(turnover,60) RHS, 数学完全 LHS 等价仅窗口差异 — pre-dedup 应识别。**窗口 sweet spot 结论**: atp-close-deviation 在 20d 与 60d 跨窗口几何同构,验证 atp/close LHS 信号是 stationary process (低频信号),非短窗 transient。 | [[batches/batch_061/candidates/C006]] |

**档位编码**: 🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色。

## 跨候选对比

- **F017 anchor cluster 范围扩大 (本批升格证据)**: 4/6 候选 (C001/C004/C006 atp-close-dev/atp_range_position × turnover-family RHS) max_corr 0.51-0.60@F017。F017 (overnight_5 × turnover_5 rank-diff) 不仅锁定 turnover_5 RHS endpoint,而是占据 **任意 amount/volume-derived LHS × turnover-family RHS** 几何位置的 cross-section anchor 槽。**升格 lessons 候选**: "anchor factor 占位律泛化 — admitted rank-diff factor 的几何 anchor 不局限于其原 LHS 字段, 任何与原 LHS 同 family 几何 (amount-derived, gap-derived) 配 RHS 同 family 几何 (turnover-derived, amount-derived) 的新候选都落入同一 cluster ridge"。F017 anchor cluster 现明确包含: turnover_5 / Std(turnover,60) / Med(turnover,20) — turnover-family 任意聚合形式都 RHS-redundant。
- **Style 聚合**: 6/6 候选 dominant_style_exposure=`vol_20d` (vol_20d=7.47-51.79,极值 C002=51.79 长窗 Std-of-amount-derived 二阶聚合)。本批 5/6 候选 alpha_survival ∈ [0.32, 0.45] (rank-diff floor 0.30 - 默认 0.40 之间) → **rank-diff geometry 在 microstructure 方向 alpha-quality 整体下滑** (vs F015/F016 admit 时 0.63/0.54)。
- **atp atom 几何独立性首次实证 (但库内冗余)**: 6 候选 corr 矩阵分析 — atp-close-deviation 与 F012/F015/F016 (Amihud family) corr 全 |corr|<0.13 (C001 vs F012=-0.10), atp_range_position 与 F019/F020/F021 (OHLC range family) corr 0.19/-0.20/0.31 borderline → atp atom 真实是 NEW dimension。BUT atp 加 Mean/Std 二阶聚合后 cross-section rank position **集中映射到 F017 anchor cluster** (turnover-family RHS 几何吸收),独立 atom 不等于 admit-eligible factor。
- **T005 quantile path P006 library-reducer 实证**: C005 是 b061 唯一 ls_t≥3 + mono perfect + 9/9 yr 全正 + lowest vol_20d exposure 候选,看似 "Phase 5 hypothesis-promoter 优秀样本", BUT incr_ic=-0.0023 NEG → 加入它让 library 组合信号变弱。**P006 库内 reducer 第 6 次跨 family 复现**: 此前 b042 C005 / b043 C005-C006 / b045 C006 / b055 C002 / b056 C004 五次, 本批 C005 第六次。**升格 lessons 候选**: "quantile spread (Pq_high - Pq_low) of magnitude-distribution 在 csi1000 cross-section 上是已 admit Mean + CV 因子的几何线性独立 BUT Barra 投影 + library 组合层冗余 — 单个因子 mono+ls_t 强不等于 incr_ic 正"。
- **higher-moment LHS in atp family 失败 (C002)**: F019/F020 (Std body_ratio / Std gap_ret) higher-moment LHS independence axis 横跨 OHLC + gap family 兑现, 本批 C002 (Std atp-close-deviation) **不能迁移**: alpha_surv=0.17 critical + 9/9 yr 同号负 cum_mdd=-55.89。**关键升格教训**: higher-moment LHS axis 兑现条件须 atom 自身与 vol_20d 正交; F019 body_ratio (intraday 内部对称) + F020 gap_ret (跨 session) 与 vol_20d 几何正交 (b050/b051 实证), atp-close-deviation **嵌入 vol_20d 几何位置** (atp = avg-trade-price, atp-close 单日变化与 |daily_return| 强相关 — 单日有大涨/大跌时 avg-trade-price 与 close 会偏离), 故 Std 二阶聚合直接落入 vol_20d 吸收基。**P003 跨 family 硬律边界进一步收窄**: higher-moment family-agnostic 迁移仅当 atom 几何与 vol_20d 正交,新 atom 必须 pre-check single-day 与 |return|/range 同构性。

## Thread 进展

> [!warning]+ T005 [[directions/microstructure_illiquidity#T005]] — `[◉ ACTIVE → ✗ DISPROVEN batch_061]`
> **quantile-Amihud P90-P10 rolling 路径 P006 library-reducer 实证**: 此前 T005 thread 状态 "仅 quantile-based asymmetry (P90-P10 rolling Amihud) 未测", 本批 C005 测试: ls_t=3.21 + mono=1.0/1.0 + 9/9 yr 全正 + ls_sharpe=2.31 + lowest vol_20d=7.47 + style_r²=0.20 (整批最干净 risk profile) BUT **incr_ic=-0.0023 NEG** → P006 库内 reducer。**Thread DISPROVEN**: T005 复活路径仅剩 minute-bar/tick 数据接入或 F012/F015/F016 退役后 quantile path 复活, 当前 daily-bar + 三 Amihud factor 健在条件下 quantile spread 是 library-reducer。**升格 lessons 候选**: 见跨候选对比 P006 第 6 次复现一段。

> [!failure]+ T008 (NEW) [[directions/microstructure_illiquidity#T008]] — `[新建 batch_061 → ✗ DISPROVEN batch_061]`
> **atp = $amount/$volume avg-trade-price atom 探索全军覆没**: 4 代 atp 几何变体 (atp-close-deviation Mean 20d/60d C001/C006 + atp-close-deviation Std 20d C002 + atp_range_position Mean 20d/5d C003/C004) × 4 个 fresh RHS (Std turnover_60 / Mean pe_60 / Mean ps_60 / Med turnover_20) **6 候选全 reject**。**Thread 状态 DISPROVEN at 创建批**。
>
> **关键发现**:
> 1. **atp atom 真实是 NEW dimension** — 与 F012/F015/F016 Amihud family corr 全 |<0.13|, 与 F019/F020/F021 OHLC family corr 全 ≤|0.31| → atp 几何独立。
> 2. **atp + amount-derived RHS 几何位置落入 F017 anchor cluster** — 4/6 候选 max_corr 0.51-0.60@F017, F017 anchor 范围已升格至 turnover-family RHS 任意聚合形式 (turnover_5 / Std turnover_60 / Med turnover_20 同 cluster)。
> 3. **higher-moment LHS in atp family 失败** — atp-close-deviation 与 |daily_return| 单日同构, Std 二阶聚合直接落入 vol_20d 吸收 (P003 边界)。
> 4. **atp_range_position 几何位置接近 F021** — corr=0.305@F021, range 内部位置类信号 RHS 被 F021 partial 锁定 (P005 saturation 扩展)。
>
> **复活路径**: (a) atp × non-amount/non-OHLC RHS (如 cross-day momentum / lag-shifted reference) 是否能脱 F017 cluster — 待测; (b) F017 退役后 atp-close-dev 重测; (c) minute-bar 数据接入后 intraday atp variance / kurtosis 路径。

## 方向级反思

本方向第 6 批,4 admit (F012/F015/F016 + b047 reserve)。本批 zero admit, **direction.score 0.84 升至 (0.901 family + 0.735 direction + 1.0 exposure 满) MT bucket 持续 high**, search_adjusted 0.51 → medium。**alpha_surv 中位数 0.36** (本批最强 C001=0.45 / C006=0.45 / C005=0.39 / C004=0.33 / C003=0.32 / C002=0.17) 较 b047 admit 时的 0.54-0.66 显著下滑 → microstructure 方向 alpha quality 结构性衰减。

**T005 + T008 双 thread DISPROVEN**: T005 quantile-Amihud P90-P10 path 是本方向 last 残余 ACTIVE thread, 本批确认 P006 library-reducer。T008 (NEW) atp atom 创建批即被全 reject (atp 与 F017 anchor cluster 几何重合) → microstructure 方向 daily-bar 几何剩余 ACTIVE thread = T007 (rank-diff 跨 direction 泛化 T007 ACTIVE,但本批未推进 T007)。

**zero_admit_streak 1 → 2**: 本方向连续 zero admit 1 批, 全系统 zero_admit_streak 1→2。距 calibration trigger 累计 3 批 + reserve 储备 ≥1 满足独立性 (max_lib_corr<0.30 + incr_ic>0.010) 还差 1 批,但 b061 reserve=0 → reserve 独立性件不达。

**direction status 评估**: 仍 productive (4 admits + F015/F016 A 级) 但 priority 应从 medium → low (T005/T008 双关闭, T007 未推进且其他探索路径已等论文/数据)。**本轮调整 priority: medium → low**。

**升格 lessons 候选** (本批共贡献 3 条):
1. **F017 anchor cluster 占位律泛化** — admitted rank-diff factor 几何 anchor 跨 RHS family 任意聚合形式锁定,而非局限原 RHS 字段窗口。
2. **higher-moment LHS axis 迁移条件收窄** — atom 必须与单日 |daily_return| / range 几何正交,否则 Std/Var 二阶聚合直接落入 vol_20d 吸收 (P003 边界)。
3. **quantile spread of magnitude-distribution = library-reducer 跨 family 律** — Mean + CV 双 admit 后, quantile-spread (P90-P10) 几何线性独立但库内组合层冗余 (P006 第 6 次复现, 跨 microstructure 第 1 次直接命中)。

**consolidation 信号**: rounds_since_last_consolidation=1 → 仍 < 10 阈值, 不触发。但 zero_admit_streak=2 + lessons 升格候选 3 条 → 距 consolidation 触发距离缩短。

**calibration_trigger=false**: 本批 zero admit + 累计 3 批 zero (b057 vwap_proxy + b060 overnight + b061 microstructure) **但** 中间 b058/b059 是 admit + reserve 独立性件 b061 reserve=0 不满足 → 不触发 calibration。
