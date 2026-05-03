---
batch_id: batch_088
direction: signed_money_flow_oscillator
judged_at: 2026-05-03T08:50:00Z
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
mt_bucket: medium
---

# batch_088 Judge Summary

> [!abstract]+ batch_088 · [[directions/signed_money_flow_oscillator]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6** (all 6 reject)
> **核心发现**: signed money-flow oscillator family (Chaikin / AD / PVT first-moment signed × Vol 累积) 在 csi1000 daily 上**整体落入 F001 vol_20d 吸收律**, 即使 Chaikin(3,10) C001 与 Chaikin(6,20) C005 alpha_survival_ratio 分别 1.35 / 1.57 (Barra-residual 形式独立, 远超 0.40 floor), incremental_ic 双双 NEG (-0.007 / -0.005) + max_corr 0.61-0.63@close-position cluster (F008/F026) 撞死 — 经典 "alpha_surv > 1.0 形式独立 ≠ library 充分条件" 候选律 b086/b087 第 3 次实证. **H1 (family 真度) PARTIAL-DISPROVEN**: form-level 独立成立 (Barra-residual alive) 但 cross-section rank 与库内 close-position-only 几何 (F006/F008/F026) 0.61+ 高度同构 → library_reducer hard_block. **H2 (Vol-dependent path)**: Chaikin (Vol-dependent) 与 PVT (Vol-dependent) 全部撞 vol_20d / cluster, ASI (Vol-independent) 因 daily DSL 不可达本批未测 — H2 仅得 1 边证据. **H3 (vol_20d 吸收律 first-moment 例外)**: PVT(20)/PVT(60) C003/C004 alpha_surv 0.11 / 0.16 < 0.40 floor 直接 vol_20d-absorbed (dom=vol_20d, exposure 7.4 / 5.5) → **F001 vol_20d 律 first-moment signed 累积扩展实证**, 律边界从"second-moment magnitude 全吞噬"扩展到"任何 N-day 累积形式 (含 first-moment signed × Vol Sum) 在 csi1000 daily 全吞噬". Chaikin EMA-差 是 first-moment signed momentum 形态 (短长 EMA 差), 落入"close-position cluster vol_20d 同基底"亚律.
> **MT Budget**: cumulative 486 → **492** · direction 0 → **6** (新方向首批) · bucket `medium` (search_adjusted=medium, family=0.97 + direction=0.07 + exposure=1.0)

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | strong·**borderline-strong**·acceptable·**borderline-high**·perfect | ic_oos=-0.036 ls_t=-6.03 mono=-0.7/-0.7 alpha_surv=1.35 max_corr=0.63@F026 incr_ic=-0.007 9/9_neg | Chaikin(3,10) EMA(AD,3)-EMA(AD,10): Barra-cleanest alpha_surv=1.35 + 9/9 年负 + sign_consistency=1.0 + ls_t=-6.03 强 — **形式独立但库内 close-position cluster (F008 corr=-0.49 / F026 corr=0.63 / F006 corr=-0.30) 几何同构, incr_ic NEG → library_reducer hard_block**. paper csi500 weekly → csi1000 daily 反号 + library overlap 双失败. | [[batches/batch_088/candidates/C001]] |
| C002 | ❌ reject | strong·weak·poor·LOW·marginal | ic_oos=-0.010 ls_t=-2.61 mono_oos=-0.10 alpha_surv=0.466 max_corr=0.36@F006 incr_ic=-0.004 sign_cons=0.75 | AD-Sum-20 (Chaikin base atom 累计): max_corr=0.36 LOW (本批最干净) + alpha_surv=0.466 刚过 0.40 floor + ls_t=-2.61 OK, **但 mono_oos=-0.10 OOS quintile 结构破坏 + sign_consistency=0.75 + style_r²=0.27 接近 poor + incr_ic=-0.004 NEG**. 4/5 borderline 不满足 reserve fire 4 要件. | [[batches/batch_088/candidates/C002]] |
| C003 | ❌ reject | weak·strong·poor·marginal·perfect | ic_oos=-0.043 ls_t=-3.99 alpha_surv=0.11 max_corr=0.48@F027 dom=vol_20d | PVT(20) signed return × Vol Sum: **alpha_surv=0.11 << 0.40 floor (3.6x 缺口)** + dom=vol_20d (exp=7.4) + max_corr=0.48@F027. **F001 律扩展实证** — first-moment signed × Vol Sum 累积也被吸收. | [[batches/batch_088/candidates/C003]] |
| C004 | ❌ reject | weak·strong·poor·marginal·perfect | ic_oos=-0.039 ls_t=-3.96 alpha_surv=0.16 max_corr=0.35@F002 dom=vol_20d | PVT(60) 长窗版本: alpha_surv=0.16 仍 << 0.40 floor + dom=vol_20d + max_corr=0.35@F002. 长窗未 salvage — F001 律 N=20/60 双窗实证一致. | [[batches/batch_088/candidates/C004]] |
| C005 | ❌ reject | strong·**borderline-strong**·acceptable·**borderline-high**·perfect | ic_oos=-0.030 ls_t=-5.43 mono=-0.7/-0.5 alpha_surv=1.57 max_corr=0.61@F008 incr_ic=-0.005 9/9_neg | Chaikin(6,20) 长窗 EMA-差: 与 C001 同律 — alpha_surv=1.57 整批最高, 但 incr_ic=-0.005 NEG + max_corr=0.61@F008. 窗口 ablation 同律: Chaikin EMA-差 family form-independent + library-overlapping. | [[batches/batch_088/candidates/C005]] |
| C006 | ❌ reject | hard_gate (sign_flip) | sign_flip: train_ic=-0.0099 vs val_ic=+0.0111 | PVT 60d rank-diff salvage: **hard_gate sign_flip catastrophic**. PVT raw 已被 vol_20d 吸收 (C003/C004), rank-diff salvage 失败 — lessons "rank-diff salvage 仅当 numerator 自身 alive" 律一致. | [[batches/batch_088/candidates/C006]] |

## 跨候选对比

- **本批整体律 — first-moment signed 累积全 vol_20d-absorbed**: 6/6 reject 中 4 个 hard_gate PASS (C001/C002/C003/C004/C005) + 1 hard_gate fail (C006) — 表面看 5/6 通过门槛, 实质 **incremental_ic 全负** (-0.007 / -0.004 / -0.012 / -0.009 / -0.005). 形式上"signed money-flow oscillator family" 是结构性新空间 (库内零 EMA-money-flow / Sum-AD / Sum-PVT 几何), 但 cross-section rank 全部归簇到 F001 vol_20d / F008-F006-F026 close-position cluster / F002 PB-amount value-liquidity cluster — 律边界**首次扩展到 first-moment signed × Vol 累积**.

- **Chaikin EMA-差 vs PVT Sum 两亚分化清晰**: Chaikin(3,10)/Chaikin(6,20) (C001/C005) 走 close-position cluster 路径 — alpha_surv 1.35/1.57 高 (Barra-residual 形式独立, 因 close-position basis 不在标准 Barra style 中) + max_corr 0.63/0.61@F008/F026 (cross-section rank 与 close-position-only cluster 同构); PVT(20)/PVT(60) (C003/C004) 走 vol_20d 直接吸收路径 — alpha_surv 0.11/0.16 极低 (signed_return × Vol 直接载 vol_20d basis) + max_corr 0.48/0.35@F002/F027. **机制差异**: Chaikin AD = `(2C-H-L)/(H-L) × Vol` 数学上 close-position-in-range 项是连续 [-1,+1] 有界, EMA 差让信号去 trend 但保留 close-position 主成分; PVT = `(C-prevC)/prevC × Vol` 是 daily_return × Vol, 与 vol_20d basis 几何同源 (vol_20d 也是 daily return 的 N-day std).

- **H3 关键测试结论 — F001 vol_20d 律边界扩展实证**: PVT(20) C003 + PVT(60) C004 双窗 alpha_surv 0.11 + 0.16 远 << 0.40 floor → first-moment signed × Vol Sum 累积**也被吸收**. 律边界从 "second-moment magnitude (Std/Var/Skew/Kurt/Quantile)" 扩展到 "first-moment signed × Vol N-day 累积 (Sum/EMA-差)". **唯一未测**: ASI (Wilder, OHLC-only Vol-independent) — 因 4-branch IF + Max-driven scaling 在 Qlib daily DSL 不可达, 需 python_runner 包装. ASI 测试是 H2 (Vol-dependent vs Vol-independent 子路径) 的最后一边证据, 应在 batch_089 (若该方向继续) 上 python_runner 路径补完.

- **paper transferability 反号 + 量级衰减双失败**: 广发金工 42 paper csi500 weekly Chaikin |IC|=1.84% 多空胜率 62.12% (102 因子第 2 名), C001 csi1000 daily ic_oos=-0.036 (绝对值 ~2x 衰减 paper 标称值, **方向翻号**). lessons.md "Paper CSI 300 大盘 → csi1000 小盘 transfer 默认失败 (量级 8x+ 衰减常态, 方向翻号常见)" — 本批 Chaikin 是该律新一例: paper 多空 long 高 close-pos × Vol stock + short 低 → csi1000 daily 上 **反向有效** (高 close-pos × Vol = 强收盘高量 stock 在 csi1000 cross-section 是 over-extended momentum 反转, 而非 paper 所言 institutional accumulation). 但反向也无独立 alpha — 与库内已 admit 的 close-position-only 几何 (F008 upper_shadow_persistence_3d) 同质. F008 已捕获该反向几何 → Chaikin 无独立增量.

- **C002 是本批"形式最干净但 alpha 独立性最弱"特例**: AD-Sum-20 max_corr=0.36 LOW (整批最低) + alpha_surv=0.466 刚过 0.40 floor (整批仅 0.06 余量), 但 mono_oos=-0.10 OOS quintile 结构破坏 + sign_consistency=0.75 (9 年中 8 年负, 2023=-0.009 接近 0) + style_r²=0.27 (poor 边缘) + incr_ic=-0.004 NEG. **不满足 reserve fire 4 要件** (max_corr<0.30 + style_r² clean + sign_consistency=1.0 + incr_ic 至少 borderline). 与 b066 C005 / b080 C006 / b087 C001 三连 reserve fire 不同模式 — 那三例都是 max_corr 0.45-0.56 borderline + alpha_surv ≥0.20 + sign_consistency=1.0; 本批 C002 是 max_corr=0.36 LOW 但 sign_consistency<1.0 + mono_oos<0.5, 是另一种"形式 vs 实质"失败 — **更深层的问题是 first-moment signed × Vol 在 csi1000 daily 持续 alpha 性 (sign-stability) 不足**.

- **incr_ic 全负深度证据 (alpha_surv > 1.0 形式独立 ≠ library 充分条件 候选律 b086/b087 第 3 次实证)**: C001 alpha_surv=1.35 + incr_ic=-0.007; C005 alpha_surv=1.57 + incr_ic=-0.005. 两 candidate Barra-residual IC 都比 raw IC 强 (alpha_surv = barra_residual_ic / raw_ic > 1.0 表征"残差比原 alpha 还强"), 但 cross-section rank 已被库内 close-position cluster 完全 capture, 加入库内不增 ensemble alpha. **该律独立性升格证据已累 ≥3 batch (b086 / b087 / b088), 应 Phase 5 consolidation 升格 lessons "alpha_survival > 1.0 必配 incremental_ic > 0 双门槛, alpha_surv 单边不足"**.

- **MT 预算推进**: direction_candidates 0 → 6 (本方向首批); cumulative 486 → 492. bucket `medium` (search_adjusted=medium, exposure_term=1.0 表 87 batches 已 saturate, family_term=0.97 接近顶, direction_term=0.07 新方向余量).

## Thread 进展

> [!note]+ T001 ASI [[directions/signed_money_flow_oscillator#T001]] — `[◉ DEFERRED → batch_089+ python_runner]`
> 本批未测 (4-branch IF + Max-driven scaling daily DSL 不可达). H2 (Vol-independent path) 关键证据缺失. ASI 是该方向**唯一未撞 vol_20d 吸收律的子路径** (其他 Chaikin/AD/PVT 全 Vol-dependent), 应在 batch_089 (若方向继续) 上 python_runner 包装补完, 测 OHLC-only Wilder swing 8-quantity 累积是否避开 vol_20d basis. 若 ASI 也 alpha_surv<0.40 → H2 全证伪 → 该方向应翻 dead + F001 律升级为"任何 N-day 累积 (含 OHLC-only swing) 全吞噬".

> [!note]+ T002 Chaikin/AD [[directions/signed_money_flow_oscillator#T002]] — `[✗ DISPROVEN-form-independent-but-library-overlap]`
> reject 3 (C001 Chaikin(3,10) / C002 AD-Sum-20 / C005 Chaikin(6,20)). T002 thread 关键问题已回答:
> - **`Vol × signed close-position` first-moment 累积是否独立于 F009 second-moment correlation**: 是 — Barra-residual alpha_surv 1.35-1.57 形式独立; 但**实质上不独立于库内 close-position-only cluster** (F006/F008/F026), max_corr 0.61-0.63 borderline-high + incr_ic NEG.
> - **EMA-差 (Chaikin) vs 纯累加 (AD)**: 两路径同律失败 — 形式都独立但都被 close-position cluster capture; AD-Sum max_corr=0.36 比 Chaikin EMA-差 0.61-0.63 低 (累加更平滑去趋势让 close-position 集中性弱), 但 mono_oos<0.5 + sign-stability 不足.
> 
> Thread 状态升级: 本方向 T002 close 完毕. **机制结论**: csi1000 daily 上 close-position × Vol 信号被 close-position-only 几何 (F006 upper_shadow_persistence_5d / F008 upper_shadow_persistence_3d / F026 daily_close_position_tsrank_60) 完全 capture, Vol 加权未提供独立 cross-section rank — 即 close-position 信号在 csi1000 上**与 Vol 无关**, Vol 加权反而稀释信号 (max_corr 0.61 vs F008 0.95+ 同质).

> [!note]+ T003 PVT [[directions/signed_money_flow_oscillator#T003]] — `[✗ DISPROVEN-vol_20d-absorbed-N=20-and-60]`
> reject 3 (C003 PVT(20) / C004 PVT(60) / C006 PVT-60d-rank-diff salvage). T003 thread 关键问题已回答:
> - **PVT (signed_return × Vol Sum) 是否独立于 F008 ret_vol_cov**: 否 — alpha_surv 0.11/0.16 << 0.40 floor (Barra-residual 直接 dead), dom=vol_20d 直接吸收. 数学根因: signed_return × Vol = ret × Vol 的 N-day Sum, 而 vol_20d Barra basis 是 ret 的 20-day Std → 同 ret-distribution 二阶载体; F008 ret_vol_cov 也是 cov(ret, Vol, 20) = E[ret×Vol] - E[ret]E[Vol] ≈ E[ret×Vol] (csi1000 zero-mean ret stationary, 与 b087 C005 升格律 P028 同律).
> - **6 日 vs 12 日 / 60 日窗口稳健性**: 本批改 N=20/60 ablation, 结论一致 dead. paper N=6 |IC|=2.16% csi500 weekly 在 csi1000 daily 全失效.
> 
> Thread 状态升级: T003 dead. **PVT 复活路径**: (a) Python OLS residualize PVT on (vol_20d, str_1m); (b) 改 evaluation policy 长 horizon 评估 (1d→5d). 但 lessons 已实证 (a) 路径 OOS sign-flip 风险高 (b071 6/6).

> [!note]+ T004 vol-orthogonalized Chaikin [[directions/signed_money_flow_oscillator#T004]] — `[✗ DISPROVEN-precondition-not-met]`
> 本批未测 (deferred to batch_089 if Chaikin 通过 baseline). T002 Chaikin baseline 已实证 form-independent-but-library-overlap, **vol-orthogonalize salvage 前提条件 (Chaikin numerator 自身 OOS-stable alpha) 不满足** (Chaikin EMA-差 raw incr_ic NEG → numerator 与库重叠 → vol-ortho 后仍重叠). lessons round 73 升格 "OLS residualize 不破 vol_20d 非线性吸收 + 仅当 numerator 自身有 OOS-stable alpha 时该路径生效" — 本方向不满足前提, T004 直接关闭无需 batch_089 试错.

## 方向级反思

本方向 round 1 (b088, 首批) 兑现率 0/6 admit + 0/6 reserve, 与 b087 (overnight_intraday_split 0+1) / b086 (range_structure 0+0) 形成**跨方向连续 3 batch zero-admit** 模式. 主要发现:

1. **F001 vol_20d 吸收律边界扩展实证 (升格证据强)**: H3 关键 lesson — first-moment signed × Vol N-day 累积 (Sum / EMA-差) 在 csi1000 daily 上**全部落入 vol_20d 吸收律**. PVT(20)/PVT(60) C003/C004 alpha_surv 0.11/0.16 << 0.40 floor + dom=vol_20d 直接证据. 律边界从原"second-moment magnitude (Std/Var/Skew/Kurt/Quantile/RealizedVol/Mad)" 扩展到"任何 N-day 累积形式 (含 first-moment signed × Vol Sum/EMA-差/Mean)". 应 Phase 5 consolidation 升格 lessons.md "F001 vol_20d 结构性吸收律" 段落新增子律: **"first-moment signed × Vol N-day 累积 (PVT / AD-Sum / Chaikin EMA-差) 在 csi1000 daily 全 vol_20d 吸收, 与 second-moment magnitude 同律. 唯一未实证的是 OHLC-only Vol-independent 累积 (ASI Wilder swing) — 待 python_runner 测试". **该升格直接关闭 signed_money_flow_oscillator 方向的 4 条子路径中的 3 条 (Chaikin/AD/PVT), 仅 ASI 待测**.

2. **alpha_survival > 1.0 形式独立 ≠ library 充分条件 候选律第 3 次实证 (b086/b087/b088)**: C001 alpha_surv=1.35 + incr_ic=-0.007; C005 alpha_surv=1.57 + incr_ic=-0.005. **Barra-residual IC 比 raw IC 还强 (alpha_surv > 1.0)** 但 cross-section rank 完全被库内 close-position cluster (F006/F008/F026) capture. 该律累计证据 ≥3 batch 跨方向 (b086 quantile_shape, b087 overnight_intraday_split, b088 signed_money_flow_oscillator), 应 Phase 5 升格 lessons "Rank-order ≠ Tradable Alpha" 段新增子律: **"alpha_survival > 1.0 必须配 incremental_ic > 0 + max_corr < 0.40 双门槛, alpha_surv 单边形式独立不足以兑现 admit. 机理: alpha_survival 衡量 vs Barra basis 残差强度, 不衡量 vs 库内 admit 因子残差强度; 库内 close-position cluster 不在 Barra basis 内, 故 Barra-residual alive 但库 redundant 是常见结局".**

3. **Paper transferability 反号 + 量级衰减双失败 (Chaikin 是新例)**: 广发金工 42 paper csi500 weekly |IC|=1.84% 多空胜率 62.12% (102 因子第 2 名) → C001 csi1000 daily ic_oos=-0.036 反号 + 量级衰减 ~2x. lessons "Paper transferability" 段新增第 3 条: **"close-position × Vol 类信号 (Chaikin / AD) 在 paper 大盘 weekly 多头有效但 csi1000 daily 反向有效, 且反向被库内 close-position-only 几何 capture, 无独立 alpha — paper 信号在 csi1000 daily 双失败 (反号 + 量级衰减 + library overlap)".**

4. **方向状态翻 dead 强建议**: signed_money_flow_oscillator round 1 (首批) 0/6 admit + 0/6 reserve + 4/4 测试子路径 (Chaikin/AD/PVT 长短窗 + rank-diff salvage) 全部 DISPROVEN + T004 vol-ortho salvage 前提不满足 + T001 ASI 唯一未测但 H2 全证伪概率高 (其他 Vol-dependent 子路径 4/4 dead → ASI 是 OHLC-only Vol-independent 子路径, 边界探针风险高). **建议方向状态从 `exploring` 直接翻 `dead`, 跳过 ASI batch_089**: 理由 (a) F001 律已实证扩展到任何 N-day 累积形式; (b) ASI 4-branch IF + Max-driven scaling python_runner 工程成本高; (c) 即使 ASI alive, 单一子路径不足以 sustain direction productive (剩 3 子路径已 dead).

5. **跨方向 zero-admit streak 升至 5+ (b084-b088 全 zero admit)** + rounds_since_consolidation = 7 (临近 10 阈值). consolidation_trigger 强信号 + 多方向 saturated/dead 显化 (overnight_intraday_split saturated + range_structure dead + ohlc_temporal_aggregation dead + signed_money_flow_oscillator 本批 dead 候选). **优先升格 3 条 lessons** (本批 narrative 已生成证据): (i) F001 vol_20d 律 first-moment 扩展; (ii) alpha_survival > 1.0 单边不足律; (iii) close-position × Vol paper transferability 反号律.

**Edge 评估**: 本方向 alpha edge 直接 dead — 不存在借记 reserve 火种 (与 b066/b080/b087 三连 borderline reserve 模式不同, 本批 6/6 全 reject 无 borderline 火种), 不存在窗口/RHS swap 复活路径 (4 子路径全 dead 形式同质). signed_money_flow_oscillator 方向应在本批后立即翻 dead, 不开 batch_089.

**下一步建议**:
- (a) **本方向翻 dead**: 不再投入 batch_089. 在 narrative log 中记 "DISPROVEN by H1/H3 validation, F001 vol_20d 律扩展实证".
- (b) **触发 consolidation_trigger** (rounds_since_consolidation=6+1=7 临近 10 + 多方向 dead/saturated 累积). 优先升格三条 lessons (上述 narrative 已写明).
- (c) **下批 direction**: 按 cockpit 该方向是 paper-vetted exploring 中最高优先级, 翻 dead 后应回退 cockpit 重选. 候选: (i) 等 consolidation 后由 LLM 重选 (推荐); (ii) 切换到其他 paper-vetted exploring direction (若 cockpit 显示存在); (iii) 系统性 dead-direction skip 后, 触发 calibration 检查是否系统级 alpha 真饱和.
- (d) **ASI python_runner 工程**: 即使本方向 dead, ASI Wilder swing 的 python_runner 包装值得作为 future work 入 lessons "Promising Unexplored" — 4-branch IF Vol-independent 几何在库内确实零先例, 边界探针价值不依赖于 H2 全证伪 (即使 H2 已实证 Vol-dependent 失败, OHLC-only Vol-independent 仍是不同律).

**Calibration trigger 检查** (本 batch 0 admit + 0 reserve):
- 错杀 flag 跨候选反思: 无 — C001/C005 alpha_surv > 1.0 但 incr_ic NEG + max_corr 0.61-0.63, 满足 "default reject: incr_ic < 0 + max_corr ∈ [0.40, 0.50] borderline" 律边界扩展 (本批 0.61-0.63 比该律实证范围 0.40-0.50 更高, 更确定 reject). 不存在错杀候选.
- 连续零 admit 警戒: 跨方向 streak=5 (b084-b088). 累计 reserve 满足"max_lib_corr<0.30 + incremental_ic>0.010"? 本批 0 reserve, b087 C001 max_corr=0.45 incr_ic=0.011 不满足 max_corr<0.30; b080 C006 max_corr=0.56 不满足; b066 C005 max_corr=0.46 不满足. **跨 batch 累计 reserves 全 borderline cluster 不满足 LOW 库独立条件, 无错杀**. 不触发 calibration.
- Reserve 积压: 不评估系统级数据.
- 悖论复现: alpha_surv > 1.0 + incr_ic < 0 悖论 ≥3 次跨方向 (b086 / b087 / b088), 但已被 lessons "Barra-clean ≠ library-clean" 充分解释, 应升格而非 calibration. 不触发 calibration.

无明确 calibration trigger. **触发 consolidation_trigger**: rounds_since_consolidation=6+1=7 临近 10, 多方向 dead/saturated 累积 (overnight_intraday_split saturated + range_structure dead + ohlc_temporal_aggregation dead + signed_money_flow_oscillator dead), zero_admit_streak=5 跨方向. **建议 orchestrator 下轮 consolidate 而非 dispatch 新 batch**.

推进 Phase 4 archive.
