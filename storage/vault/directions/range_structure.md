---
direction_tag: range_structure
status: dead
priority: low
rounds: 9
admits: 2
last_batch: batch_083
last_admits: []
last_goal: 'T004 round 1 — P008 escape mechanism cross-direction test: daily-resolution
  intraday range/structure geometry × TsRank 60d. Hypothesis: P008 (single-day OHLC
  ratio + TsRank>=60d wrap escapes vol_20d absorption because per-day denominator
  is not polluted by future cumulative vol) generalizes from F025 (shadow asymmetry,
  midpoint anchor) + F026 (close position, low-anchor) to range_structure direction.
  Test 6 distinct daily-resolution intraday ratios wrapped in TsRank 60d, all max_corr<0.40
  vs F021/F025/F026. C001 raw range/close baseline; C002/C006 open-to-high/open-to-low
  fraction (symmetric pair); C003 body/range (completely different geometry from shadow);
  C004 outer-wrap Std-of-range 5d then TsRank 60d (composite test); C005 range/open
  (denominator robustness vs C001). Skip baseline-first per Step 1.5 exception: all
  15 untouched fields are fundamental TTM, structurally unrelated to OHLC range geometry
  direction.'
last_goal_legacy: T003 round 1 — 沿 F021 (C005 admit) 衍生 intraday position dispersion
  family。6 LHS 全部为不同 numerator 的 close/open/prev_close 在 H-L 范围内的 position Std 二阶矩
  (开盘下/上影位置/return-per-range/gap/range/composite midpoint)，与 F021 atom (H-C)/(H-L)
  不同 numerator 且非 affine 等价；F019 (|C-O|/(H-L) Std) 与 F020 (gap_ret Std) 也完全异源。RHS
  全部 long-window (60d) scale-free fundamental/liquidity 几何 ratio (VWAP magnitude/ROE
  proxy/vwap-close ratio/margin proxy/turn-pb composite/turnover$)，不重叠 F021 RHS H/L_60、不在
  saturated endpoints (overnight_5/turnover_5/amount_20/body_ratio_20/Amihud_20)、避开
  size RHS (b055 C006 教训)、避开 sign-aggregation RHS (b055 C003 教训)。设计纪律：mono_is>=0.6
  硬下界 + 单层 二阶矩 (Std 而非 Skew/Kurt 避 P003 单飞律) + scale-free positive ratio 三条件；规避 TsKurt/TsSkew
  内嵌 CsRank (operators.py:428 bug)；rank-diff geometry 7 律 max_corr@F021<0.30 + max_corr@all_rank_diff<0.30。预期至少
  1 admit 验证 intraday position dispersion family 在 F021 之外可扩展，确认 'lower-shadow / open-position
  / midpoint-deviation 等同 LHS 几何位置 × 不同 RHS basis' 是 range_structure direction 的可挖路径。
last_activity: '2026-05-02T16:33:34Z'
created_batch: batch_043
members:
- F021
merged_into: null
---
# range_structure

> [!abstract]+ 方向概要
> - **状态**　🔴 `dead` · priority `low` · rounds = 9 · admits = 2（F021 + b055 C005 派生）· reserves dangling = 1（b083 C006 (O-L)/(H-L) family ext 仅作 anchor 占位）
> - **关闭理由**　T001 closed / T002 disprove / T003 sub-path A disprove / T004 round 1 disprove；连续 b056+b064+b083 三轮 0 admit；4 个挖掘空间 3 个工具链阻塞；library reducer 律累积 11 次重现
> - **一句话**　range_structure 9 rounds 36 candidates 沉淀出 P008 atom-specific boundary 与 vol_20d 吸收律 11 次本地复现，作为 lessons 升格证据池闭门归档

---

## Hypothesis ⚠️ 证伪

原假设：(high-low)/close 是日内价格路径测量，数学上不等于 daily-return std；range 的**结构**（timing / 频率 / 形状 / 短长比）可能逃离 vol_20d 吸收。

**证伪结果**（9 rounds，36 candidates，2 admit / 4+ reserve / 30 reject）：
- **range magnitude / ratio / power-mean / Std / Quantile 全部坍缩到 vol_20d**——T002 短长比 + 变化率 (b043 C005/C006)、T001 freq-high (b043 C002)、Q90/Q90-Med/Skew120/scale-free (b045 C002/C003/C004/C006) 11 次本地命中 F001/F301 vol_20d 吸收律
- **逃离仅一窄路**：rank-diff geometry × **intraday position dispersion (NOT magnitude)** × long-window scale-free RHS——由 b055 C005 (Std((H-C)/(H-L), 20) × Mean(H/L, 60)) 兑现首个 admit；但该路径在 b056/b064 沿 (O-L)/(H-L) atom 衍生 12 候选 0 admit，alpha_survival 全部 < 0.40
- **P008 atom-specific NOT wrap-pattern-general**（b083 升格证据）：TsRank≥60d wrap 仅对"位置/比例" geometry (F025/F026) 有效；raw range magnitude (range/close, range/open) 全部 incremental_ic NEG，outer 5d Std-wrap 反将 vol_20d exposure 推到 16.4（本方向史上最高）

> [!warning]+ ⚠️ 已升格 lessons.md 的元教训（本方向直接贡献证据）
> - **F001 / F301 vol_20d 吸收律**（high severity）：daily-bar 任意 magnitude / ratio / power-mean / Std / Quantile / IQR 形态 cross-section 均坍缩为 vol_20d monotone derivative，alpha_survival 典型 0.08–0.30。本方向 11 次本地复现（T002 + b045 C002/C003 + b055 C001/C006 + b056 C003 + b064 C001/C002/C004/C005 + b083 C001/C004/C005）
> - **F005 OHLC algebraic 共动律**（medium severity）：(H-L)/C 与 prev_close gap / OHLC4_mean affine 共动；**daily 频率延伸**（b083 升格）：单日 OHLC TsRank wrap 形式下 open ≈ close 在 vol-orthogonal cross-section 完全同源（C001 vs C005 所有 OOS metric 小数点 2 位以内一致）
> - **P008 atom-specific NOT wrap-pattern-general**（b083 升格）：(a) 仅"位置/比例" geometry (close position F026, shadow asymmetry F025) 有效；(b) raw range magnitude 全部 incremental_ic NEG；(c) outer Std-wrap inner 5d Std 把单日 ratio 聚合成 5d vol，break P008 必要条件"原子分母不被未来累积 vol 污染"
> - **F001 vol_20d ⊃ range_structure 直系律**（5+ direction × 9+ candidate 跨方向独立确认）：本方向是该律最浓缩证据池
> - **mono_is ≥ 0.6 硬下界纪律**：b043 C004 / b045 C004 / b055 C004 三次 IS→OOS mono paradox 复现催生
> - **library reducer 律 11 次累积**（b042-b083）：max_corr<0.40 + incr_ic≤-0.010 + alpha_surv>0.80 模式应升格 hard_block automatic reject

---

## Threads (closed)

### T001: Range timing/frequency/shape 信号是否独立于 vol_20d [✓ ANSWERED batch_055]

> [!success]+ Thread 结论
> **Answer**: 是 — 但路径极窄。**rank-diff geometry × intraday position dispersion (NOT range magnitude) × long-window scale-free RHS** 是首条成功路径，由 b055 C005 兑现首个 admit。已封闭子路径 7+ 条：IdxMax timing / freq-high threshold / freq-low threshold / magnitude Quantile / Skew shape / sign-gated Skew / scale-free Q-ratio / standalone Kurt / range magnitude rank-diff / sign-aggregation RHS / 60d 长窗 range Std + size RHS。
>
> **Key admit**: [[batches/batch_055/candidates/C005|b055 C005]] Sub(CsRank(Std((H-C)/(H-L),20)), CsRank(Mean(H/L,60))) — ic_oos=+0.043, mono_oos=+1.0, cum_mdd=-1.14 库内最浅, ic_by_year 9 年单调增强, max_corr=0.44@F020 反向互补, incr_ic=+0.008, style_crowding=medium。**4 个关键差分**：(a) LHS 是 close 在 H-L 范围内的 position (非 magnitude)；(b) RHS long-window 几何 ratio (60d H/L)；(c) style_crowding=medium；(d) cum_mdd 库内罕见。
>
> **Partial breakthrough**: [[batches/batch_045/candidates/C001|b045 C001]] Kurt((H-L)/C, 60) — mono_is=0.9 + mono_oos=0.9 双高 + style_r²=0.074 clean + max_corr=0.105 + incr_ic=+0.0153 + cum_mdd=-1.42 + ls_t=3.08；alpha_surv=0.17 阻止 admit → reserve（Kurt > Skew on (H-L)/C 验证；TsKurt-inside-CsRank 路径阻塞: operators.py:428 bug 无法 rank-diff 化）。

### T002: Range 短/长比与变化率是否独立于 F001 amount CV [✗ DISPROVEN batch_043]

> [!failure]+ Thread 结论
> **Answer**: 否 — range magnitude/ratio 在 csi1000 与 F001/F009 共享反转簇载体；IC 稳定 9 年同号但 incremental_ic 全部为负。
>
> **本 thread 是 F001 / F301 vol_20d 吸收律的第 3 次跨方向独立确认**（+stochastic_position / +vwap_proxy_signals），已升格 lessons.md。
>
> **Evidence**:
> - [[batches/batch_043/candidates/C005|b043 C005]] Div(Mean((H-L)/C, 5), Mean((H-L)/C, 60)) 短长比 — IC_OOS=-0.038 强 mono=-0.9 ls_t=-2.18 但 **incr_ic=-0.025** + vol_20d exp=27.7 + cum_mdd=-82
> - [[batches/batch_043/candidates/C006|b043 C006]] Delta(Mean((H-L)/C, 20), 5) 变化率 — ls_t=-2.74 但 mono_is=-0.7→mono_oos=-0.10 崩塌 + **incr_ic=-0.017**

### T003: intraday position dispersion 衍生路径是否构成可扩展 alpha family [✗ DISPROVEN batch_083]

> [!failure]+ Thread 结论
> **Answer**: 否 — 沿 b055 C005 admit 衍生的 intraday position dispersion family 不可扩展；b056 + b064 共 12 candidates / 0 admit / 5 reserve / 7 reject。
>
> **关键发现**：
> - **5 alive 候选 alpha_survival 全部 < 0.40** [0.134, 0.283]——LHS 几何 (O-L)/(H-L) 与 vol_20d / turnover_20d 紧密耦合
> - **L/C N-d 与 H/L N-d 反号几何对偶** ([[batches/batch_064/candidates/C003|b064 C003]] ic_oos=-0.044, 9 年单调恶化, library reducer 第 8 次)——**永久库 reducer 模式**
> - **fundamental-level RHS (PB/PE/PS) 通过 barra style 渗漏** ([[batches/batch_064/candidates/C004|b064 C004]] PB level → book_to_price 2.16 + vol_20d 13.4 双载体 = P004 vol_20d 9+ direction 律第 10 次)
> - **temporal-statistic RHS 信噪比下界**: TsAutoCorr 60d-Mean 在 csi1000 cross-section 区分度过低（[[batches/batch_064/candidates/C006|b064 C006]] ic_std_oos=0.068 远低于其它候选 0.12-0.14）
> - **H/L geometry dead 是 geometry-specific 而非 window-specific**——120d 仍 vol-loaded（[[batches/batch_064/candidates/C005|b064 C005]] vol_20d=13.0）
> - **"strong-mono+strong-ls_t but library reducer" 陷阱第 5 次复现**（[[batches/batch_056/candidates/C004|b056 C004]] ls_t=4.62 + mono=+1.0 但 incr_ic=-0.0024）
>
> 升格 lessons 候选 4 项已交 Phase 5 distillation。

### T004: daily-resolution intraday range/structure geometry × TsRank 60d 是否构成 P008 escape 机制的可扩展 alpha family [✗ DISPROVEN batch_083]

> [!failure]+ Thread 结论
> **Answer**: 否 — P008 escape mechanism is **atom-specific NOT wrap-pattern-general**。raw range magnitude 全部 incremental_ic NEG 落回 vol-CV family；outer Std-wrap 反深陷 vol_20d (16.4 本方向史上最高)。
>
> **关键 boundary 数据点**（升格 lessons 已成立）：
> - **C001 (H-L)/C / C005 (H-L)/O**: incr_ic=-0.033, vol_20d 12.6/12.5, mono Q5 一桨, cum_ic_mdd=-106——P008 NEGATIVE for raw range magnitude；同时验证 daily open ≈ close 在 vol-orthogonal cross-section 完全同源 (F005 daily 频率延伸)
> - **C004 outer 5d Std-wrap**: dom=vol_20d=**16.4 (本方向史上最高)** + incr_ic=-0.017 + cum_mdd=-82.7——P008 KEY NEGATIVE：inner 5d Std 把单日 ratio 聚合成 5d vol，break"原子分母不被未来累积 vol 污染"
> - **C002 (H-O)/(H-L) / C006 (O-L)/(H-L)**: max_corr=0.65@F025 cluster；(H-O)/(H-L) + (O-L)/(H-L) = 1 严格几何约束在 TsRank 60d wrap 下破坏 (corr ≈ -0.5 而非 -1.0)；anchor 方向 (from-high vs from-low) 在 csi1000 信号含量不对称
> - **C006 reserve 占位**：9 年 sign-consistent + cum_mdd=-2.15 库内最浅 + style_r²=0.06 极 clean，但 ls_t=+0.48 weak + incr_ic=+0.0038 borderline + max_corr=0.65@F025；非真错杀，作 anchor 占位等下批 family ext，本方向 dead 后将悬挂

---

## Known Failures (Top reject 一览)

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_043/candidates/C001\|b043 C001]] | `IdxMax((H-L)/C, 20)` | timing 弱（mono_oos=-0.9 一桨 + ls_t=-1.4 + incr_ic=-0.008）|
| [[batches/batch_043/candidates/C002\|b043 C002]] | `Mean(Gt((H-L)/C > 1.5×60d_base), 20)` | freq-high 仍在 vol_20d 空间 (vol_20d=47.9, alpha_surv=0.23, incr_ic=-0.019) |
| [[batches/batch_045/candidates/C002\|b045 C002]] | `Quantile((H-L)/C, 60, 0.9)` | magnitude robust 估计仍 vol_20d 簇 (vol_20d=47, incr_ic=-0.042, cum_mdd=-85) |
| [[batches/batch_045/candidates/C004\|b045 C004]] | `Skew((H-L)/C, 120)` | mono_is=0.5 < 0.6 硬下界 + IS/OOS paradox + alpha_surv=0.088 |
| [[batches/batch_045/candidates/C006\|b045 C006]] | `(Q80-Q20)/Med((H-L)/C, 60)` | scale-free 降吸收但 mono OOS 崩塌 (-1.0→-0.30) |
| [[batches/batch_055/candidates/C002\|b055 C002]] | `Sub(CsRank(Std((H-L)/(H+L),20)), CsRank(Mean(pe,60)))` | "强 alpha 但库减值"陷阱第 4 次 (mono_oos=-1, ls_t=-2.92, incr_ic=-0.008) |
| [[batches/batch_055/candidates/C006\|b055 C006]] | `Sub(CsRank(Std((H-L)/C,60)), CsRank(Mean(circ_market_cap,60)))` | style_r²=0.75 vol+size 双吸收, alpha_surv=0.71 假象 |
| [[batches/batch_056/candidates/C004\|b056 C004]] | `Sub(CsRank(Std((O-prev_C)/(H-L),20)), CsRank(Mean(pe/ps,60)))` | strong-mono+strong-ls_t but library reducer 第 5 次（升格 lessons）|
| [[batches/batch_064/candidates/C003\|b064 C003]] | `Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(L/C,60)))` | L/C 60d 与 H/L 60d 反号几何对偶，库 reducer 第 8 次 |
| [[batches/batch_064/candidates/C004\|b064 C004]] | `Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(pb_ratio,60)))` | PB level 通过 book_to_price barra style 渗漏，P004 第 10 次 |
| [[batches/batch_083/candidates/C001\|b083 C001]] | `TsRank((H-L)/C, 60)` | P008 NEGATIVE for raw range magnitude (incr_ic=-0.033, vol_20d=12.6) |
| [[batches/batch_083/candidates/C004\|b083 C004]] | `TsRank(Std((H-L)/C, 5), 60)` | P008 KEY NEGATIVE: outer Std-wrap 破 P008 必要条件 (vol_20d=16.4 史高) |
| [[batches/batch_083/candidates/C005\|b083 C005]] | `TsRank((H-L)/O, 60)` | open ≈ close 同源 (F005 daily 延伸) — 与 C001 数值小数点 2 位以内一致 |

完整 23 项 reject 详细诊断保留在各 batch judge.md 内。

---

## Narrative Log

> [!quote]+ 2026-05-02 · [[batches/batch_083/judge|batch_083]] · T004 round 1 — P008 escape mechanism cross-direction test FAILS
> admit=0 / reserve=1 / reject=5 · 升格 lessons 候选 3 项 + library reducer 律 11 次累积 + direction `saturated → dead`
>
> - C001/C005 raw range magnitude × TsRank 60d → reject：incr_ic=-0.033 同, vol_20d 12.5/12.6, max_corr 0.27@F022 反号同源 — **P008 NEGATIVE for raw range magnitude**；F005 共动律 daily 频率延伸（open ≈ close 在 vol-orthogonal cross-section 完全同源）
> - C004 TsRank(Std((H-L)/C, 5), 60) outer Std-wrap → reject：dom=vol_20d=**16.4 本方向史上最高** + incr_ic=-0.017 + cum_mdd=-82.7 — **P008 KEY NEGATIVE: 5d Std inner-wrap break P008 必要条件"原子分母不被未来累积 vol 污染"**
> - C002/C003 → reject：(H-O)/(H-L) F025 退化变体 (max_corr=0.65) / |C-O|/(H-L) IS_ic=+0.0015 ≈ 0 + train_val_decay=5.75 OOS regime overfit
> - C006 (O-L)/(H-L) → reserve：9 年 sign-consistent + cum_mdd=-2.15 库内最浅 + style_r²=0.06 极 clean 但 ls_t=+0.48 weak + max_corr=0.65@F025 cluster — 非真错杀，作 anchor 占位
> - **结构性发现升格 lessons**: (1) P008 atom-specific NOT wrap-pattern-general; (2) Daily open ≈ close in vol-orthogonal cross-section; (3) Geometric pair break under TsRank wrap; (4) library reducer 律 11 次重现 → 升格 hard_block

> [!quote]- 2026-04-28 · [[batches/batch_064/judge|batch_064]] · T003 round 2 sub-path A — RHS 跨字段族独立性失败
> admit=0 / reserve=3 / reject=3
>
> - C001/C002/C005 reserve：alpha_survival 全 < 0.40，C005 (H/L 120d) 最强但 MT bucket=high + dead-endpoint 扩展受限
> - C003 → reject：L/C 60d 与 H/L 60d 反号几何对偶，库 reducer 第 8 次（永久减值模式）
> - C004 → reject：PB level → book_to_price + vol_20d 双载体渗漏，P004 第 10 次
> - C006 → reject (hard_gate)：TsAutoCorr 60d-Mean 区分度过低，temporal-statistic RHS 在 csi1000 daily 频率信噪比下界律
> - **升格 lessons 候选 4 项**：(1) L/C N-d ↔ H/L N-d 反号对偶库 reducer; (2) fundamental-level RHS barra style 渗漏; (3) unitless temporal-statistic 长窗 mean 信噪比下界; (4) H/L geometry dead 是 geometry-specific 非 window-specific

> [!quote]- 2026-04-25 · [[batches/batch_056/judge|batch_056]] · T003 round 1 — intraday position dispersion 沿 C005 衍生
> admit=0 / reserve=1 (C001) / reject=5
>
> - C001 (O-L)/(H-L) Std × VWAP magnitude → reserve：ic_oos=+0.021 + mono=+1.0 + cum_mdd=-4.06 + 9 年 U-shape；alpha_surv=0.24 + max_corr=0.50@F019 阻 admit
> - C002/C005 hard_gate fail；C003 daily return-numerator 完整命中 vol_20d 吸收律警告（mono collapse + max_corr=0.65@F014 + vol_20d=47.2）
> - C004 ls_t=4.62 strong + mono=+1.0 但 incr_ic=-0.0024 — **strong-mono+strong-ls_t but library reducer 陷阱第 5 次复现**（升格 lessons）
> - C006 alpha_survival=**0.0725** 极端 poor — alpha_survival << 0.10 比 style_r² 边界更敏感诊断"vol_20d 完全吞噬"

> [!quote]- 2026-04-25 · [[batches/batch_055/judge|batch_055]] · range family 首 admit！P002 rank-diff geometry 跨 family 第 6 admit
> admit=1 (C005) / reserve=0 / reject=5 · `status: exploring → productive`
>
> - **C005 → admit**: Sub(CsRank(Std((H-C)/(H-L), 20)), CsRank(Mean(H/L, 60)))。ic_oos=+0.043 + mono_oos=+1.0 + cum_mdd=-1.14 库内最浅 + ic_by_year 9 年单调增强 + style_crowding=medium 唯一非 high。**突破点：LHS 是 close 在 H-L 范围内的 position dispersion 而非 range magnitude——vol_20d 吸收律之外首条成功路径**
> - 5/6 reject incr_ic 全 ≤ 0 — rank-diff geometry 已饱和到组合层（P005 动态饱和律）
> - C002 strong-but-negative 陷阱第 4 次复现；C004 mono paradox 第 3 次（mono_is>=0.6 硬下界纪律有效）；C003 sign-aggregation as RHS 路径封闭；C006 60d 长窗 Std + size RHS 教训（alpha_surv=0.71 假象 vs style_r²=0.75）；TsKurt-inside-CsRank operators.py:428 bug 阻塞

> [!quote]- 2026-04-25 · [[batches/batch_045/judge|batch_045]] · shape 路径首次 partial breakthrough
> admit=0 / reserve=1 (C001 Kurt60) / reject=5
>
> - C001 Kurt((H-L)/C, 60) → reserve：mono_is=0.9 + mono_oos=0.9 双高 + style_r²=0.074 clean + max_corr=0.105 + incr_ic=+0.0153 + cum_mdd=-1.42 + ls_t=3.08；alpha_surv=0.17 阻 admit。**Kurt 4 阶矩 > Skew 3 阶矩**——T001 shape 路径首次 partial breakthrough
> - C002/C003 Q90/Q90-Med → reject：robust 分位估计仍在二阶矩空间（vol_20d exp 44-47, F001 本地数据点）
> - C004 Skew120 → reject：mono_is=0.50 < 0.6 + 复现 b043 C004 paradox — **mono_is ≥ 0.6 硬下界纪律首次执行命中**
> - C005/C006 sign-gated Skew / scale-free Q-ratio → reject

> [!quote]- 2026-04-24 · [[batches/batch_043/judge|batch_043]] · 首批分裂结论：magnitude/ratio 全败，shape 存活但悖论组合
> admit=0 / reserve=4 / reject=2
>
> - **T002 DISPROVEN**：C005 短长比 + C006 变化率，IC 稳定 9 年同号但 incr_ic 全负——range ratio/velocity 与 F001/F009 共享反转簇载体。**第 3 次跨方向独立确认（升格 lessons 元教训）**
> - **T001 部分存活**：C001 timing / C002 freq-high 封闭；C003 freq-low / C004 shape (Skew60) 存活 reserve
> - C004 悖论诊断：4 个 error-kill 指标全过但 mono_is=0.30 弱 + alpha_surv=0.14 poor — 非真错杀；催生 mono_is ≥ 0.6 硬下界纪律

---

## Related

- 🔴 [[return_distribution_signals]] `dead` — daily-return skew/kurt/Q-range 全部坍缩到 vol_20d；本方向用 range 而非 return 但同源 F301
- 🟡 [[stochastic_position]] `saturated` — (close - TsMin) / (TsMax - TsMin) rank-order 崩塌；本方向是 range 大小 & timing 而非 close 在 range 内位置
- 🟡 [[intraday_price_formation]] `saturated` — 单日 (close-low)/(high-low) mono_sign_flip；F005 algebraic 共动律同源（b083 daily 频率延伸验证）
- 🟡 [[liquidity_acceleration]] `saturated` — 流动性 ratio 全部落入 F001 吸收簇；T002 已确认 range ratio 同样命运
- 🔴 [[quantile_shape_signals]] `dead` — Quantile robust ≠ vol_20d orthogonal（F301 同源）；本方向 b045 C002/C003 是该律的本地复现
- 📖 [[lessons#Structural Constraints]] — F001 / F301 vol_20d 吸收律 + F005 OHLC algebraic 共动律 + P008 atom-specific boundary
- 📖 [[lessons#Data Facts]] — A 股 10% 涨跌幅约束对 range 上限的结构影响
- 📖 [[lessons#Operator Registry]] — TsSkew / IdxMax / Kurt 自定义算子，C.kernels=1；TsKurt-inside-CsRank operators.py:428 bug
