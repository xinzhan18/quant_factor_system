---
direction_tag: range_structure
status: saturated
priority: medium
rounds: 8
admits: 2
last_batch: batch_064
last_admits: []
last_goal: T003 round 2 sub-path A — 沿 b056 C001 reserve 的 ATOM1=Std((O-L)/(H-L),20)
  open-lower-position-dispersion 衍生 6 候选 × 6 个跨字段族独立长窗 scale-free RHS（turnover_60
  / H_C_60 / L_C_60 / pb_60 level / H_L_120 (dead-endpoint window 扩展) / 60d-mean-of-20d-autocorr
  novel temporal），目标至少 1 admit 验证 (O-L)/(H-L) atom × 非 b056 已 reject RHS 维度可扩展。规避
  b056 已 reject RHS（amount/volume, pe/pb, vwap/close, pe/ps, turnover/pb, amount/market_cap）+
  死亡 endpoint（overnight_5/turnover_5/amount_20/body_ratio_20/price_vol_20/circ_mktcap_60/H_L_60_geo）+
  daily-return/overnight-gap LHS（b056 C003/C004/C005 三连 reject）+ composite midpoint
  LHS（b056 C006）+ pe/pb/ps fundamental 60d 复合（b056 三连 reject）。设计纪律：mono_is>=0.6 +
  incr_ic>0.015 当 max_corr∈[0.30,0.70] borderline（P006 library-reducer 第 7 次律）+ LHS
  单层 Std 二阶矩 + RHS scale-free positive ratio。规避：rate/delta/ratio LHS（lessons forbidden）+
  higher-moment LHS regime sign-flip（仅 Std-of-scale-free-ratio safe）+ rank-preserving
  单算子包装。
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
last_activity: '2026-04-28T10:32:24Z'
created_batch: batch_043
members:
- F021
merged_into: null
---
# range_structure

> [!abstract]+ 方向概要
> - **状态**　🟢 `productive` · priority `medium` · rounds = 4 · admits = 1 · reserve = 1（历史）
> - **最近**　[[batches/batch_055/judge|batch_055]] 2026-04-25 admit=1 (C005→F{next} upper_shadow_disp_range_compress_rd_20) reserve=0 reject=5 · **range family 首 admit + P002 跨 5 family 第 6 admit 兑现**
> - **一句话**　range/intraday position **结构**（timing、frequency、dispersion、shape、shadow-position）通过 rank-diff geometry 在 cross-section 上突破 vol_20d std-of-return 空间——首条成功路径：upper-shadow position Std × long-window range compression rank-diff

---

## Hypothesis

现有库 13 admits 中与"波动率"有关的都是基于 daily returns 的 std（F001 amount CV、F012 amihud）或 overnight/intraday 分解（F003/F009/F010/F011）——这些都被 Barra 的 `vol_20d` 风格因子 (20d std of daily returns) 广泛吸收。

**(high - low) / close** 是**日内价格路径的测量**，数学上不等于 daily-return std。直觉上相关但不等价：同一 daily return 可以来自"全天缓慢爬升"（低 high-low）或"高波动震荡后收于同价"（高 high-low）。因此 range **magnitude** 可能仍被 vol_20d 吸收（均值-方差一致性），但 range 的**结构**（timing / 频率 / 形状）可能逃离：

- **Timing 信号**：IdxMax((high-low)/close, N)——最大 range 出现在近还是远（event timing），离散的"第几天"不是连续的 vol
- **Frequency 信号**：Mean(Gt((high-low)/close, threshold), N)——高 range 日的频率（count-based 聚合），规避了 power-mean 的 vol 同构
- **Skew 信号**：Skew((high-low)/close, 60)——range 分布的非对称（少数大 range 日 vs 大多数小 range 日 vs 反之），测量事件驱动 vs 噪声驱动
- **短/长比**：Mean((high-low)/close, 5) / Mean((high-low)/close, 60)——range 波动的 regime change，类似 C003 加速度但在 range 空间
- **变化率**：Delta(Mean((high-low)/close, 20), 5)——range 趋势

csi1000 特征：
- 小盘在涨跌幅 10% 约束下，高 range 日是"事件日"（新闻、游资介入）—— timing 可能携带游资脚印
- 连续几个低 range 日 → 高 range 日爆发 (Bollinger-style compression/expansion)

**关键风险**：
- (high-low)/close 与 vol_20d 的 corr 可能 > 0.6（历史已知事实）；本方向需关注**结构化 transformation**后的 residual
- F012 amihud_illiq_20d 已占据"流动性"空间；timing/freq 需独立

> [!warning]+ ⚠️ Hypothesis 修正条款（来自 Phase 5 distillation F001 / F005 / F301）
> - **F001 / F301 vol_20d 吸收律**（high severity, 5+ 次跨方向独立确认）：daily-bar 上任意 magnitude / ratio / power-mean / Std / Quantile / IQR 形态——无论作用于 return / range / amount / turnover——cross-section 均坍缩为 vol_20d 的 monotone derivative，alpha_survival 典型 0.08–0.30。本方向 T002 (range 短长比 + 变化率) 与 batch_045 C002/C003 (Q90 / Q90-Med) 已是该律的本地数据点。**判别规则**：dominant_style=vol_20d + style_r²>0.30 + alpha_survival<0.30 三者同立 = 直接 reject 并切换设计轴，不再尝试同形变体。
> - **F005 OHLC algebraic 共动律**（medium severity）：(H-L)/C 与 prev_close gap / OHLC4_mean 在 csi1000 上 affine 共动；任何"H-L 分母 / prev_close 分母"组合候选起手前必做 algebraic 等价检查（max_corr ≥ 0.85 → cluster；4-field mean ≈ close 退化）。
> - **逃离路径仅四条**（F001 列举）：(a) Python Barra residual orthogonalize（受 coverage<0.80 限制 / 工具链阻塞）；(b) 非 daily-bar 数据（minute / tick）；(c) 非 magnitude 几何——higher-moment 单层 (Kurt) 仅当 mono_is ≥ 0.6 + scale-free RHS；(d) overnight 段独立分解。本方向当前唯一活路 = (c) Kurt-centric。

---

## Current Focus

- **batch_056 (round 5 planning)**：沿 C005 admit 衍生路径——intraday position dispersion 维度 × long-window scale-free RHS 组合
  - LHS atom 候选：(C-L)/(H-L) Std (lower-shadow position)、(C-prev_close)/(H-L) Std (gap-anchored position)、|C-O|/(H-L) median position 等
  - RHS basis 候选：H/L 60d Mean (compression, C005 已用)、$amount/$volume 60d (VWAP level)、Skew/Kurt of body_ratio long-window 等不在饱和 endpoints
- **关键已封闭路径**：
  - timing (IdxMax) / freq-high (Gt threshold) / magnitude Quantile (Q90/Q90-Med) / Skew 60d/120d / sign-gated Skew / scale-free (Q80-Q20)/Med（b043+b045）
  - **range Std × short-window or saturated RHS**（b055 C001/C002/C003/C004/C006 全 reject，incremental_ic ≤ 0）
  - **60d 长窗 range Std + raw size/value RHS**（b055 C006 教训：style_r²=0.75 vol+size 双吸收，alpha_survival=0.71 假象）
  - **sign-aggregation as RHS basis**（b055 C003：str_1m exp=3.84 RHS 暴露成 short-reversal proxy）
  - **TsKurt-inside-CsRank**（operators.py:428 bug：D.features 不识别自定义算子，需 Python escape hatch 或修复）
- 设计纪律：
  - **mono_is 硬下界 0.6**（b043 C004 paradox / b045 C004 / b055 C004 三次复现验证）
  - **incremental_ic 必须 > 0**（b055 5/6 reject 由此触发）
  - LHS 必须是 intraday position 而非 magnitude (C005 admit 关键差分)
  - RHS 必须 long-window (≥60d) + 几何 ratio + 不在饱和 endpoints
- **退出准则**：round 5 沿 C005 衍生路径仍 0 admit + 80%+ candidate incremental_ic ≤ 0 → 转 `saturated`

---

## Threads

### T001: Range timing/frequency/shape 信号是否独立于 vol_20d [✓ ANSWERED batch_055]

> [!success]+ Thread 结论
> **Question**: (high-low)/close 的离散结构化 transformation（IdxMax 时序 / Gt-threshold 频率 / Skew shape / Kurt 4 阶矩 / Quantile 分位 / scale-free ratio / **rank-diff geometry**）在 cross-section 上是否逃离 vol_20d 连续 std 空间，产生独立 forward IC？
>
> **Answer (b055)**: 是 — 但路径极窄。**rank-diff geometry × intraday position dispersion (NOT range magnitude) × long-window scale-free RHS** 是首条成功路径，由 C005 (Std((H-C)/(H-L), 20) × Mean(H/L, 60)) 兑现首个 admit。其它 6 条已封闭路径（IdxMax timing / freq threshold / magnitude Quantile / Skew shape / sign-gated Skew / scale-free Q-ratio / standalone Kurt / range magnitude rank-diff / sign-aggregation RHS / 60d 长窗 range Std + size RHS）均 disprove。
>
> **Evidence trail**:
> - [[batches/batch_043/candidates/C001|batch_043 C001]]　IdxMax((H-L)/C, 20) timing — mono_oos=-0.90 一桨 Q5, ls_t=-1.40 弱, incr_ic=-0.008 → **reject**（信号太弱）
> - [[batches/batch_043/candidates/C002|batch_043 C002]]　Mean(Gt((H-L)/C > 1.5×60d_baseline), 20) freq-high — vol_20d exp=47.9 + alpha_surv=0.23 + incr_ic=-0.019 → **reject**（**freq-high threshold 仍在 vol_20d 空间，子路径 DISPROVEN**）
> - [[batches/batch_043/candidates/C003|batch_043 C003]]　Mean(Lt((H-L)/C < 0.5×60d_baseline), 20) freq-low — max_corr=0.16@F002 独立但 mono_oos=0.0 + ls_t=-0.23 → **reserve**（compression 机制存活但信号弱）
> - [[batches/batch_043/candidates/C004|batch_043 C004]]　Skew((H-L)/C, 60) ⚠️ — mono_oos=+1.00 完美 + ls_t=+2.46 + incr_ic=+0.014 + max_corr=0.117@F012 + cum_mdd=-2.01 最浅；但 mono_is=0.30 弱 + alpha_survival=0.14 poor → **reserve**（诊断为非真错杀：mono IS→OOS 异常放大非稳健机制）
> - [[batches/batch_045/candidates/C001|batch_045 C001]]　**Kurt((H-L)/C, 60)** 4 阶矩 — **mono_is=0.90 + mono_oos=0.90 双高 + style_r²=0.074 clean + max_corr=0.105@F012 + incr_ic=0.0153 + cum_mdd=-1.42 极浅 + ls_t=3.08 strong**；但 alpha_survival=0.17 poor + ic_oos=0.0113 moderate → **reserve**（**首次 shape 路径 partial breakthrough**；Kurt 比 Skew 在 (H-L)/C 分布上更稳健）
> - [[batches/batch_045/candidates/C002|batch_045 C002]]　Quantile((H-L)/C, 60, 0.9) Q90 — vol_20d exp=47.0 + style_r²=0.60 + incr_ic=-0.042 库负冗余 + cum_mdd=-85 长期失效 → **reject**（**magnitude robust 估计仍进入 vol_20d 簇**）
> - [[batches/batch_045/candidates/C003|batch_045 C003]]　Q90 - Median((H-L)/C, 60) — vol_20d exp=44.7 + style_r²=0.46 + incr_ic=-0.036 → **reject**（相减两 location 估计量未脱离 vol_20d）
> - [[batches/batch_045/candidates/C004|batch_045 C004]]　**Skew((H-L)/C, 120)** 长窗 — mono_is=0.50 / mono_oos=1.00 **完美复现 batch_043 C004 paradox** + alpha_surv=0.088 极 poor → **reject**（**违反 direction mono_is ≥ 0.6 硬下界纪律，首次执行命中**）
> - [[batches/batch_045/candidates/C005|batch_045 C005]]　Sign(close-close_{t-5}) × Skew((H-L)/C, 60) — ls_t_IS=+1.75 vs ls_t_OOS=-1.87 **符号翻转** + str_1m exp=2.49 拖向短反转空间 + mono_oos=-0.60 弱 → **reject**（sign-gated shape 在 csi1000 不稳健）
> - [[batches/batch_045/candidates/C006|batch_045 C006]]　(Q80-Q20)/Median((H-L)/C, 60) scale-free — vol_20d exp 减半 (20.4) + alpha_surv=0.70 good 但 mono_is=-1.0 / mono_oos=-0.30 **崩塌** + incr_ic=-0.010 → **reject**（scale-free 能降吸收但不能单独撑起稳健 rank-order）
> - [[batches/batch_055/candidates/C001|batch_055 C001]]　rank-diff Sub(CsRank(Std((H-L)/C,20)), CsRank(Mean(volume,60))) — ls_t=-0.40 weak + incr_ic=-0.013 NEG (F012 reducer) + style_r²=0.50 + mono partial flip → **reject**（range Std × volume rank-diff 同 vol+liquidity 簇 reducer）
> - [[batches/batch_055/candidates/C002|batch_055 C002]]　rank-diff Sub(CsRank(Std((H-L)/(H+L),20)), CsRank(Mean(pe,60))) — mono_oos=-1.0 完美 ls_t=-2.92 但 incr_ic=-0.008 NEG → **reject**（"看似强 alpha 但库减值"陷阱第 4 次复现）
> - [[batches/batch_055/candidates/C003|batch_055 C003]]　rank-diff Sub(CsRank(Std(H/L,20)), CsRank(Mean(Sign(Δclose),20))) — vol_20d=58.1 (本批最高) + str_1m=3.84 + incr_ic≈0 → **reject**（sign-RHS 未起独立维度 + 双 style 强吸收）
> - [[batches/batch_055/candidates/C004|batch_055 C004]]　rank-diff Sub(CsRank(Mean((H-L)/prev_close,20)), CsRank(Mean(VWAP,60))) — mono paradox -1.0→-0.30 + ls_t=-0.65 + incr_ic=-0.007 NEG → **reject**（b043/b045 C004 paradox 第 3 次复现 + F005 algebraic mirror trap）
> - [[batches/batch_055/candidates/C005|batch_055 C005]]　**rank-diff Sub(CsRank(Std((H-C)/(H-L),20)), CsRank(Mean(H/L,60))) — ic_oos=+0.043 + mono_oos=+1.0 完美 + cum_mdd=-1.14 库内最浅 + ic_by_year 9 年单调增强 (+0.013→+0.046) + max_corr=0.44@F020 反向互补 + incr_ic=+0.008 库增值 + style_crowding=medium (本批唯一非 high) → admit → F{next} upper_shadow_disp_range_compress_rd_20**
> - [[batches/batch_055/candidates/C006|batch_055 C006]]　rank-diff Sub(CsRank(Std((H-L)/C,60)), CsRank(Mean(circ_market_cap,60))) — style_r²=0.75 (本批最高) + alpha_surv=0.71 假象 + mono OOS collapse 0.40→-0.10 + incr_ic=-0.012 NEG → **reject**（60d 长窗 Std 未替代 Kurt 稳健性，反而深陷 vol+size 双 style）
>
> **累积发现**（3 batches, 17 candidates, 1 admit + 1 reserve + 15 reject）:
> - **shape 路径仅 C001 Kurt60 reserve + C005 rank-diff admit 兑现**——突破点是 **rank-diff geometry × intraday position 维度**而非 range magnitude
> - **5/6 b055 candidate incremental_ic ≤ 0** 揭示 **rank-diff geometry 已饱和到组合层 (P005 动态饱和律)**——即使 max_corr<0.55 看似独立，多个独立 RHS 通过 vol_20d common cause 仍构成"组合层冗余"
> - **C005 admit 4 个关键差分**：(a) LHS atom 是 close 在 H-L 范围内的 position (非 range magnitude)；(b) RHS 是 long-window 几何 ratio (60d H/L)；(c) style_crowding=medium (其它 5 候选 high)；(d) cum_mdd=-1.14 库内罕见
> - **TsKurt-inside-CsRank 路径阻塞**: operators.py:428 bug 阻止 D.features 识别自定义算子；P002 endorsed 的 higher-moment LHS 升级需 Python escape hatch 或修复 _build_cs_cache
>
> **Next probes (T003 接力)**: 沿 C005 衍生 intraday position dispersion 维度——见 [[directions/range_structure#T003]]

### T003: intraday position dispersion 衍生路径是否构成可扩展 alpha family [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 在 C005 admit (Std((H-C)/(H-L), 20) × Mean(H/L, 60)) 验证"intraday position dispersion × long-window scale-free RHS"成功后，该 LHS atom family 是否可扩展？具体试 (C-L)/(H-L) Std (lower-shadow position)、(C-prev_close)/(H-L) Std (gap-anchored position)、Mean(body_position, N) Std 等其它 intraday position atoms × 不同 long-window scale-free RHS。
>
> **Evidence trail**:
> - [[batches/batch_056/candidates/C001|batch_056 C001]]　Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(amount/volume,60))) — open lower-shadow position dispersion × 60d VWAP magnitude — ic_oos=+0.021 + mono_oos=+1.0 完美 + cum_mdd=-4.06 极浅 + incr_ic=+0.0085 库增值 + max_corr=0.50@F019 + 9 年 U-shape 近 3 年同号加强；但 alpha_survival=0.24 < 0.40 + style_r²=0.17 边界 + ICIR=0.17 weak + max_lib_corr=0.50 medium → **reserve**（family 部分扩展验证；C001 真错杀诊断挂起）
> - [[batches/batch_056/candidates/C002|batch_056 C002]]　Sub(CsRank(Std((H-O)/(H-L),20)), CsRank(Mean(pe/pb,60))) — open upper-shadow position × ROE proxy — hard_gate fail (sign_flip train+0.002 vs val-0.008 + oos_decay=-4.34) → **reject**（IS/OOS 完全反转）
> - [[batches/batch_056/candidates/C003|batch_056 C003]]　Sub(CsRank(Std((C-prev_C)/(H-L),20)), CsRank(Mean(amount/(close*volume),60))) — daily return-per-range × VWAP/close 60d — mono collapse -0.90→-0.10 + incr=-0.006 + vol_20d=47.2 + max_corr=0.65@F014 → **reject**（hypothesis vol_20d 吸收律完整命中）
> - [[batches/batch_056/candidates/C004|batch_056 C004]]　Sub(CsRank(Std((O-prev_C)/(H-L),20)), CsRank(Mean(pe/ps,60))) — overnight-gap-per-range × margin proxy — ls_t=4.62 strong + mono=+1.0 完美 但 incr=-0.0024 NEG + alpha_surv=0.27 → **reject**（"strong-mono+strong-ls_t but library reducer" 第 5 次复现）
> - [[batches/batch_056/candidates/C005|batch_056 C005]]　Sub(CsRank(Std((H-prev_C)/(H-L),20)), CsRank(Mean(turnover/pb,60))) — high-overnight-gap-per-range × turn-pb composite — hard_gate fail (ic_oos=-0.0042 < 0.008 + mono_oos=-0.90 strong-but-weak-IC) → **reject**
> - [[batches/batch_056/candidates/C006|batch_056 C006]]　Sub(CsRank(Std(((C+O)-(H+L))/(H-L),20)), CsRank(Mean(amount/market_cap,60))) — composite midpoint deviation × turnover-by-value 60d — ic_oos=+0.025 表面 strong 但 alpha_surv=0.0725 极端 + ls_t=0.90 weak + vol_20d=30.67 + incr≈0 → **reject**（"vol_20d IC 假象"诊断典型）
> - [[batches/batch_064/candidates/C001|batch_064 C001]]　Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(turnover_rate,60))) — open lower-shadow position × 60d turnover level — ic_oos=+0.0305 + mono_oos=+1.0 + cum_mdd=-2.13 极浅 + ic_by_year 单调加强 + incr=+0.0053 边缘 + max_corr=0.46@F017 turnover-family；但 alpha_surv=0.283 + dom=turnover_20d (9.23) crowding=high → **reserve**（turnover-60 RHS 与 F017 turnover-5 共载）
> - [[batches/batch_064/candidates/C002|batch_064 C002]]　Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(H/C,60))) — × 60d H/C ratio level — ic_oos=+0.0392 + mono_oos=+1.0 + cum_mdd=-2.46 + incr=+0.0089 库增值 + max_corr=0.44@F020 (反号-0.445)；但 alpha_surv=0.230 + vol_20d=22.0 极深暴露 → **reserve**（H/C 60d RHS 实质独立但 vol_20d 单载体过深）
> - [[batches/batch_064/candidates/C003|batch_064 C003]]　Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(L/C,60))) — × 60d L/C ratio level — ic_oos=-0.0436 mono_oos=-1.0 完美但反号 + ls_t=-1.91 weak + incr_ic=-0.008 NEG (库 reducer 第 8 次重现) + cum_ic_mdd=-57.7 警戒线 + ic_by_year 9 年单调恶化 + 与 F021 H/L 60d 反号几何对偶 corr=-0.46 → **reject**（**L/C 60d 是永久库 reducer，与 H/L geometry 反号对偶**）
> - [[batches/batch_064/candidates/C004|batch_064 C004]]　Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(pb_ratio,60))) — × 60d PB level — ic_oos=+0.0252 + mono=+1.0 + ls_t=2.40；但 alpha_surv=0.179 + style_r²=0.388 + dom=vol_20d (13.4) × book_to_price (2.16) 双载体 + incr=0.0054 边缘 → **reject**（**PB level RHS 通过 book_to_price barra style 渗漏；P004 vol_20d 9+ direction 律第 10 次重现**）
> - [[batches/batch_064/candidates/C005|batch_064 C005]]　Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(H/L,120))) — × 120d H/L Mean (dead-endpoint window 扩展) — ic_oos=+0.0393 + ls_t=2.62 + mono_oos=+1.0 + cum_mdd=-1.79 (本批最浅) + ic_by_year 单调加强 (2022-2023 双新高) + incr=+0.0103 (本批最高) + max_corr=0.425@F020；但 alpha_surv=0.261 + vol_20d=13.0 + MT high → **reserve**（**H/L geometry 120d 仍 vol-loaded — dead 是 geometry-specific 而非 window-specific**）
> - [[batches/batch_064/candidates/C006|batch_064 C006]]　Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(TsAutoCorr($close,20),60))) — × 60d-Mean of 20d temporal autocorrelation — hard_gate fail (ic_oos=+0.0014 < 0.008) + ls_t=0.13 → **reject**（**TsAutoCorr 60d-Mean cross-section 信噪比近 0；temporal-statistic RHS 在 csi1000 daily 频率失败**）
>
> **Round 2 sub-path A 累积发现** (T003 共 12 candidates 跨 b056+b064, 0 admit + 2 reserve + 10 reject):
> - **5 alive 候选 alpha_survival 全部 < 0.40** [0.134, 0.283]——LHS 几何 (O-L)/(H-L) 与 vol_20d / turnover_20d 紧密耦合，RHS 跨字段族独立性失败
> - **L/C N-d Mean RHS 永久库 reducer**（与 H/L geometry 反号几何对偶，第 8 次 library-reducer 律重现）
> - **fundamental level RHS 通过 barra style 渗漏**：PB→book_to_price，PE→ep_ratio，需 ortho-by-style 才能 vol-orthogonal
> - **temporal-statistic RHS 信噪比下界**：TsAutoCorr 60d-Mean 在 csi1000 cross-section 区分度过低，下次设计前需 RHS stand-alone IC pretest
> - **H/L geometry 120d 仍 dead**——dead-endpoint 是 geometry-specific 而非 window-specific（升格新 lessons 候选）
>
> **Next probes**: T003 sub-path A 已基本回答不可行；sub-path B [(C-L)/(H-L)] 必要性需评估（建议先休 1-2 batch 等 ortho-by-style 工具或新 RHS 类型出现）。若再 1-2 batch 仍 admit=0 → T003 整体 DISPROVEN + direction status: saturated → dead。

### T002: Range 短/长比与变化率是否独立于 F001 amount CV [✗ DISPROVEN batch_043]

> [!failure]+ Thread 结论
> **Question**: range 的短长窗比 ratio 和 Delta 变化率（活跃度 regime shift）是否与 F001 amount CV 同向冲突（负 incremental_ic）还是独立？
>
> **Answer**: 否，range magnitude/ratio 在 csi1000 与 F001/F009 共享同一反转簇载体。两候选 IC 稳定 9 年同号但 **incremental_ic 全部为负**，vol_20d exposure 13.9–27.7。
>
> **Evidence trail**:
> - [[batches/batch_043/candidates/C005|batch_043 C005]]　Div(Mean((H-L)/C, 5), Mean((H-L)/C, 60)) 短长比 — IC_OOS=-0.038 本批最强 mono=-0.9 ls_t=-2.18 但 **incr_ic=-0.025 NEGATIVE** + vol_20d exp=27.7 + cum_mdd=-82 → **reserve**（orthogonalize 路径待工具链）
> - [[batches/batch_043/candidates/C006|batch_043 C006]]　Delta(Mean((H-L)/C, 20), 5) 变化率 — ls_t=-2.74 但 mono_is=-0.7→mono_oos=-0.10 崩塌 + **incr_ic=-0.017 NEGATIVE** → **reserve**（Q5 一桨驱动 + 库负冗余）
>
> **元教训**：本 thread 是 F001 / F301 **vol_20d 吸收律**的第 3 次跨方向独立确认（+stochastic_position / +vwap_proxy_signals），已升格 lessons.md。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_043/candidates/C001\|batch_043 C001]] | `IdxMax((H-L)/C, 20)` | mono_oos=-0.90 一桨 Q5 + ls_t=-1.40 弱 + incr_ic=-0.008 负（库减值）|
| [[batches/batch_043/candidates/C002\|batch_043 C002]] | `Mean(Gt((H-L)/C > 1.5×60d_base), 20)` | vol_20d exposure=47.9 极端 + alpha_surv=0.23 poor + incr_ic=-0.019（freq-high 未逃离 vol_20d）|
| [[batches/batch_045/candidates/C002\|batch_045 C002]] | `Quantile((H-L)/C, 60, 0.9)` | vol_20d exp=47.0 + style_r²=0.60 + incr_ic=-0.042 库负冗余 + cum_mdd=-85 长期失效史（magnitude robust 估计仍进入 vol_20d 簇）|
| [[batches/batch_045/candidates/C003\|batch_045 C003]] | `Q90 - Median((H-L)/C, 60)` | vol_20d exp=44.7 + style_r²=0.46 + incr_ic=-0.036 + cum_mdd=-84（location 估计量相减未 scale-free）|
| [[batches/batch_045/candidates/C004\|batch_045 C004]] | `Skew((H-L)/C, 120)` | mono_is=0.50 违反 direction ≥ 0.6 硬下界纪律 + IS/OOS mono paradox 0.5→1.0 复现 batch_043 C004 + alpha_surv=0.088 极 poor |
| [[batches/batch_045/candidates/C005\|batch_045 C005]] | `Sign(Δclose_5d) × Skew((H-L)/C, 60)` | ls_t_IS=+1.75 vs ls_t_OOS=-1.87 符号翻转 + str_1m exp=2.49 + mono_oos=-0.60 弱 + incr_ic=-0.013 与 F007 同构 |
| [[batches/batch_045/candidates/C006\|batch_045 C006]] | `(Q80-Q20)/Med((H-L)/C, 60)` | mono_is=-1.0 / mono_oos=-0.30 OOS 崩塌 + Q5 一桨 + incr_ic=-0.010 + ls_t=-1.65 weak（scale-free 部分成功但 rank-order 不稳健）|
| [[batches/batch_055/candidates/C001\|batch_055 C001]] | `Sub(CsRank(Std((H-L)/C,20)), CsRank(Mean(volume,60)))` | ls_t_OOS=-0.40 weak + incr_ic=-0.013 NEG (F012 reducer) + style_r²=0.50 vol_20d exp=38.8 + mono partial flip 0.40→-0.50 + ls_t IS+2.42 OOS-0.40 翻号 |
| [[batches/batch_055/candidates/C002\|batch_055 C002]] | `Sub(CsRank(Std((H-L)/(H+L),20)), CsRank(Mean(pe,60)))` | mono_oos=-1.0 完美 + ls_t=-2.92 strong 但 incr_ic=-0.008 NEG (rank-diff cluster reducer) + cum_mdd=-64.5 9 年负向加深 — "看似强 alpha 但库减值"陷阱第 4 次复现 |
| [[batches/batch_055/candidates/C003\|batch_055 C003]] | `Sub(CsRank(Std(H/L,20)), CsRank(Mean(Sign(Δclose),20)))` | vol_20d exp=58.1 (本批最高) + str_1m exp=3.84 双 style 强吸收 + incr_ic≈0 (库零增值) + ls_t IS-5.23 OOS-1.39 衰减 0.27 — sign-aggregation as RHS basis 路径封闭 |
| [[batches/batch_055/candidates/C004\|batch_055 C004]] | `Sub(CsRank(Mean((H-L)/prev_close,20)), CsRank(Mean(VWAP,60)))` | mono paradox -1.0→-0.30 第 3 次复现 (b043+b045+b055 C004) + ls_t=-0.65 weak + incr_ic=-0.007 NEG + LHS 触 F005 algebraic mirror |
| [[batches/batch_055/candidates/C006\|batch_055 C006]] | `Sub(CsRank(Std((H-L)/C,60)), CsRank(Mean(circ_market_cap,60)))` | style_r²=0.75 (本批最高) + log_circ_cap exp=0.586 + alpha_surv=0.71 假象 + mono OOS collapse 0.40→-0.10 + incr_ic=-0.012 NEG — 60d 长窗 Std 未替代 Kurt 稳健性反深陷 vol+size 双吸收 |
| [[batches/batch_056/candidates/C002\|batch_056 C002]] | `Sub(CsRank(Std((H-O)/(H-L),20)), CsRank(Mean(pe/pb,60)))` | hard_gate fail：sign_flip train +0.002 vs val -0.008 + oos_decay=-4.34 + mono_oos 从 +1.0 崩到 +0.10 + ic_by_year 2015-2018 全正后 2019-2023 全负 regime shift（pe/pb ROE proxy + open upper-shadow 在 csi1000 IS/OOS 完全反转）|
| [[batches/batch_056/candidates/C003\|batch_056 C003]] | `Sub(CsRank(Std((C-prev_C)/(H-L),20)), CsRank(Mean(amount/(close*volume),60)))` | mono collapse -0.90→-0.10 (Q5 一桨驱动) + incr_ic=-0.006 NEG (与 F014 max_corr=0.65 高) + vol_20d=47.2 极端 + style_r²=0.29 + alpha_surv=0.09 + cum_mdd=-38（daily return-per-range 完整命中 hypothesis vol_20d 吸收律警告）|
| [[batches/batch_056/candidates/C004\|batch_056 C004]] | `Sub(CsRank(Std((O-prev_C)/(H-L),20)), CsRank(Mean(pe/ps,60)))` | ls_t=4.62 strong + mono=+1.0 完美 但 incr_ic=-0.0024 NEG + alpha_surv=0.27 + dom=vol_20d (exp=12.1) — "strong-mono+strong-ls_t but library reducer" 陷阱第 5 次复现 (b042 C005 / b043 C005-C006 / b045 C006 / b055 C002 / b056 C004)，应升格 lessons.md |
| [[batches/batch_056/candidates/C005\|batch_056 C005]] | `Sub(CsRank(Std((H-prev_C)/(H-L),20)), CsRank(Mean(turnover/pb,60)))` | hard_gate fail：ic_oos=-0.0042 < 0.008 + mono_oos=-0.90 strong-but-weak-IC + sign_consistency=0.75 — high-overnight-gap-per-range × turn-pb composite RHS 即使 mono 完美 IC 量级不通过门槛 |
| [[batches/batch_056/candidates/C006\|batch_056 C006]] | `Sub(CsRank(Std(((C+O)-(H+L))/(H-L),20)), CsRank(Mean(amount/market_cap,60)))` | ic_oos=+0.025 表面 strong + mono=+0.90 + cum_mdd=-2.75 极浅 + ic_by_year 9 年单调增强；但 alpha_survival=**0.0725** 极端 poor (本批最低) + vol_20d_exp=30.67 极端 + ls_t_oos=0.90 weak + incr_ic≈0 — "vol_20d IC 假象"诊断典型，alpha_survival << 0.10 比 style_r² 边界更敏感地揭示残余 alpha 几乎为零 |
| [[batches/batch_064/candidates/C003\|batch_064 C003]] | `Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(L/C,60)))` | ic_oos=-0.0436 + ls_t=-1.91 weak + incr_ic=-0.008 NEG (**library reducer 第 8 次重现**) + cum_ic_mdd=-57.7 < -50 警戒线 + ic_by_year 9 年单调恶化 (2015 +0.0007 → 2023 -0.047) + style_r²=0.365 + alpha_surv=0.134 + vol_20d_exp=47.0 极端 + 与 F021 H/L 60d 反号几何对偶 (corr=-0.4629) — **L/C 60d 与 H/L 60d 是 csi1000 反号对偶载体，永久库 reducer 模式** |
| [[batches/batch_064/candidates/C004\|batch_064 C004]] | `Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(pb_ratio,60)))` | ic_oos=+0.0252 + mono=+1.0 + ls_t=2.40 表面健康；但 alpha_survival=0.179 + style_r²=0.388 + dom=vol_20d (13.42) × book_to_price (2.16) **双载体渗漏** + incr_ic=0.0054 admit 下界边缘 + MT bucket=high — **PB level RHS 通过 book_to_price barra style 渗漏；P004 vol_20d 9+ direction 律第 10 次跨方向独立确认** |
| [[batches/batch_064/candidates/C006\|batch_064 C006]] | `Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(TsAutoCorr($close,20),60)))` | hard_gate fail：ic_oos=+0.0014 < 0.008 + ICIR=0.020 + ls_t=0.13 + ic_std_oos=0.068 (远小于其它候选 0.12-0.14) — **TsAutoCorr 60d-Mean cross-section 区分度过低**；TsAutoCorr 是 [-1,1] unitless 数，60d Mean 在 csi1000 大量股票收敛到相近均值 → CsRank 后区分度被压扁 → **temporal-statistic RHS 在 csi1000 daily 频率信噪比下界律** |

## Narrative Log

> [!quote]+ 2026-04-28 · [[batches/batch_064/judge|batch_064]]
> **T003 round 2 sub-path A：(O-L)/(H-L) atom × 6 RHS 跨字段族系统验证 → 0 admit / 3 reserve / 3 reject — RHS 跨字段族独立性失败**
>
> - **C001/C002/C005 → reserve**：3 reserve 信号实在但 alpha_survival 全 < 0.40。C005 是本批最强（incr_ic=0.0103 + cum_mdd=-1.79 + ic_by_year 单调加强 + ls_t=2.62）但 (a) MT bucket=high 强制压制 + (b) 与 C001/C002 共 LHS atom 受 P005 #5 anchor rule 限制 + (c) 直接扩展 H/L geometry dead-endpoint 到 120d。C002 incr=0.0089 库增值清晰但 vol_20d 暴露 22.0 极深。C001 incr=0.0053 边缘 + dom=turnover_20d crowding=high。
> - **C003 → reject (库 reducer 第 8 次重现)**：L/C 60d × LHS — ic_oos=-0.0436 + ls_t=-1.91 + incr=-0.008 NEG + cum_mdd=-57.7 警戒线 + 9 年单调恶化 + 与 F021 H/L 60d 反号几何对偶 (corr=-0.46)。**L/C N-d 与 H/L N-d 在 csi1000 是反号对偶载体——独立使用必反号载体**（升格 lessons 候选）。
> - **C004 → reject (P004 vol_20d 9+ direction 律第 10 次)**：PB level 60d × LHS — alpha_surv=0.179 + style_r²=0.388 + dom=vol_20d (13.4) × book_to_price (2.16) 双载体。**fundamental-level RHS 通过 barra style 直接渗漏**——PB→book_to_price，PE→ep_ratio，需 ortho-by-style 工具才能拯救。
> - **C006 → reject (hard_gate, temporal-statistic RHS 信噪比下界律)**：TsAutoCorr 60d-Mean × LHS — ic_oos=0.0014 < 0.008，ic_std_oos=0.068 远小于其它候选 → cross-section 区分度过低。**TsAutoCorr 是 [-1,1] unitless 数，60d Mean 在 csi1000 收敛到相近均值，CsRank 后压扁**。下次类似设计需 RHS stand-alone IC pretest。
> - **结构性发现（升格 lessons 候选 4 项）**：(1) L/C N-d Mean 与 H/L N-d Mean 反号几何对偶，库 reducer；(2) fundamental-level RHS (PB/PE/PS) 通过 barra style 渗漏；(3) temporal-statistic RHS (TsAutoCorr 60d) 在 csi1000 cross-section 信噪比下界；(4) **H/L geometry dead 是 geometry-specific 而非 window-specific——120d 仍 vol-loaded**（与 b055 C006 60d Std + size 教训对应；几何 vs 窗口 dead 边界确立）。
> - **错杀侦测扫描**：5 alive 候选 max_lib_corr ∈ [0.376, 0.4629] **均 > 0.30**，无单候选满足 over-rejection criteria 第 1 条；calibration_trigger=false。C005 接近 over-rejection 边界（mono_oos=1.0 + sign=1.0 + cum_mdd=-1.79 + nearest 反号）但 max_corr=0.425 不构成 flag。
> - MT budget cumulative 342 → **348** · direction 24 → **30** · bucket `high` (adjusted `medium`)
>
> **下一步**: T003 sub-path A 已基本回答不可行；sub-path B [(C-L)/(H-L)] 必要性待评估——若再做 sub-path B 重蹈 (O-L)/(H-L) alpha_surv 全 poor 模式则 T003 整体 DISPROVEN。**建议 orchestrator 先休 1-2 batch range_structure**（让 ortho-by-style 工具或全新 RHS 类型出现）；若不出现则下批确认 T003 DISPROVEN + direction `saturated → dead`。
>
> **Operations**: `status: saturated` 维持（本批 0 admit 与 saturated 一致；连续 b056 + b064 admit=0；累积 7 rounds 探索深 + 30 direction candidates）· `priority: medium` 维持（reserve 数据点真实，且 calibration trigger 触发线 reserve_积压 % 检查交 orchestrator）
>
> **新 dead patterns 候选（交 /pattern-scout 或 Phase 5 升格 lessons.md）**:
> 1. "L/C N-d 与 H/L N-d 反号对偶，独立使用是永久库 reducer"
> 2. "fundamental level RHS (PB/PE/PS) 通过 barra style 渗漏，非 vol-orthogonal"
> 3. "unitless temporal-statistic 长窗 mean RHS 在 csi1000 cross-section 信噪比下界，需 stand-alone IC pretest"
> 4. "H/L geometry dead 是 geometry-specific 而非 window-specific（60d/120d 都 vol-loaded）"

> [!quote]- 2026-04-25 · [[batches/batch_056/judge|batch_056]]
> **T003 round 1：intraday position dispersion family 沿 C005 衍生 0 admit / 1 reserve / 5 reject — 但 C001 (open lower-shadow position × VWAP magnitude) reserve 维持 family 部分可扩展**
>
> - **C001 → reserve**：Sub(CsRank(Std((O-L)/(H-L), 20)), CsRank(Mean(amount/volume, 60)))。ic_oos=+0.021 + mono_oos=+1.0 完美 + cum_mdd=-4.06 极浅 + incr_ic=+0.0085 库增值 + 9 年 U-shape 近 3 年同号加强 + max_corr=0.50@F019 medium；但 alpha_survival=0.24 < 0.40 + style_r²=0.17 边界 + ICIR=0.17 weak + max_lib_corr=0.50 阻止 admit。**真错杀诊断挂起**：等待 round 2 沿 (O-L)/(H-L) atom 衍生 1-2 独立 RHS 候选后再判 (Calibration trigger 候选 #1)。
> - **C002/C005 → reject (CP01 hard_gate fail)**：C002 sign_flip+oos_decay 双失败 (pe/pb ROE proxy + open upper-shadow IS/OOS 完全反转)；C005 ic_oos=-0.0042 < 0.008 (high-overnight-gap-per-range × turn-pb composite RHS 即使 mono 完美 IC 不达门槛)。
> - **C003 → reject**：daily return-per-range × VWAP/close 60d，mono collapse -0.90→-0.10 + incr=-0.006 + vol_20d=47.2 + max_corr=0.65@F014 — **完整命中 hypothesis vol_20d 吸收律警告**（daily return as numerator 是设计违规）。
> - **C004 → reject (library reducer 第 5 次复现)**：overnight-gap-per-range × pe/ps margin proxy，ls_t=4.62 strong + mono=+1.0 完美但 incr_ic=-0.0024 + alpha_surv=0.27——"strong-mono+strong-ls_t but library reducer" 陷阱第 5 次独立确认 (b042/b043/b045/b055/b056)，**应升格 lessons.md**。判别要件已稳定：mono_oos≥0.9 + |ls_t_oos|≥3.0 + incr_ic<0 + alpha_surv<0.30。
> - **C006 → reject (vol_20d IC 假象诊断典型)**：composite midpoint deviation × turnover-by-value 60d，ic_oos=+0.025 表面 strong 但 alpha_survival=**0.0725** 极端 poor + ls_t_oos=0.90 weak + vol_20d_exp=30.67 极端 + incr≈0——揭示 **alpha_survival << 0.10 比 style_r² 边界更敏感地诊断"vol_20d 完全吞噬"**（本案 style_r²=0.21 仅 borderline 但 alpha 几乎全被 style 占走）。
> - **rank-diff geometry library reducer 第 5 次复现 + alpha_survival 灵敏度细化** 是本批两条结构性发现，应升格 lessons.md
> - MT budget cumulative 288 → **294** · direction 12 → **18** · bucket `high` (adjusted `medium`)
>
> **下一步**: T003 round 2 — sub-path A: 沿 C001 (O-L)/(H-L) atom 衍生 × 不同长窗几何 RHS (H/L 60d / 其它 turnover-orthogonal 长窗 ratio)；sub-path B: (C-L)/(H-L) Std lower-shadow-close-position × C001 同款 RHS。避免：daily return / overnight gap as numerator (b056 C003/C004/C005)、composite midpoint (b056 C006)、pe/pb 60d / pe/ps 60d / turnover/pb 60d 类 fundamental composite RHS (三连 reject)。
>
> **Operations**: `status: productive` 保持（C001 reserve 维持 family 可扩展嫌疑 + 库增值数据点）· `priority: medium` 保持（admit=0 但 reserve 数据点真实，未达 saturated 触发）

> [!quote]- 2026-04-25 · [[batches/batch_055/judge|batch_055]]
> **range family 首 admit！P002 rank-diff geometry 跨 5 family 第 6 admit 兑现** · admit=1 (C005→F{next} upper_shadow_disp_range_compress_rd_20) / reserve=0 / reject=5
>
> - **C005 → admit**：Sub(CsRank(Std((H-C)/(H-L), 20)), CsRank(Mean(H/L, 60)))。ic_oos=+0.043 + mono_oos=+1.00 完美 + cum_mdd=-1.14 库内最浅 + ic_by_year 9 年单调增强 (+0.013→+0.046) + max_corr=0.44@F020 反向互补 + incr_ic=+0.008 库增值 + style_crowding=medium (本批 6 候选唯一非 high)。突破点：**LHS 是 close 在 H-L 范围内的 position dispersion 而非 range magnitude**——这是 vol_20d 吸收律之外首条成功路径。
> - **C001/C002/C003/C004/C006 → reject** (5 全 reject)：incremental_ic 全部 ≤ 0 (-0.013/-0.008/≈0/-0.007/-0.012)——**rank-diff geometry 已饱和到组合层** (P005 动态饱和律)，即使 max_corr<0.55 看似独立，多 RHS 通过 vol_20d common cause 仍构成"组合层冗余"。
> - **C002 strong-but-negative 陷阱第 4 次复现** (mono_oos=-1.0 完美 ls_t=-2.92 但 incr=-0.008)，与 b042 C005 / b043 C005-C006 / b045 C006 同模式，应升格 lessons.md
> - **C004 mono paradox 第 3 次复现** (mono_is=-1.0 → mono_oos=-0.30)：与 b043 C004 + b045 C004 同模式，已升格 mono_is>=0.6 硬下界纪律有效但需补充 mono_oos>=0.5 下界
> - **C003 sign-aggregation as RHS** 路径正式封闭：str_1m exp=3.84 RHS 暴露成 short-reversal proxy，与 LHS vol_20d 双 style 吸收
> - **C006 60d 长窗 Std + size RHS** 教训：alpha_surv=0.71 假象 vs style_r²=0.75 矛盾——alpha_survival 高仅意味"残差信号还在"，但因子已被 risk model 完全分解为 style 组合
> - **TsKurt 路径阻塞**：operators.py:428 bug 阻止 D.features 识别自定义算子；P002 endorsed 的 higher-moment LHS 升级 (b045 C001 reserve Kurt60) 在 DSL 下无法 rank-diff 化，需 Python escape hatch 或修复 _build_cs_cache
> - MT budget cumulative 282 → **288** · direction 6 → **12** · bucket `high` (adjusted `medium`)
>
> **下一步**: 沿 C005 衍生 intraday position dispersion 维度——T003 thread 接力。LHS 候选：(C-L)/(H-L) Std (lower-shadow position) / (C-prev_close)/(H-L) Std (gap-anchored position) / body_position Mean Std；RHS 候选：H/L Mean 60d (C005 已用 anchor) / amount/volume Mean 60d / 其它 long-window 几何 ratio。规避：60d 长窗 + size RHS / sign-aggregation as RHS / 短窗 RHS。
>
> **Operations**: `status: exploring → productive` (首次 admit) · `priority: low → medium` (admit 验证 direction 仍有可挖空间)

> [!quote]- 2026-04-25 · [[batches/batch_045/judge|batch_045]]
> **shape 路径首次 partial breakthrough：Kurt60 reserve** · admit=0 / reserve=1 (C001) / reject=5
>
> - **C001 Kurt60 → reserve**：mono_is=0.90 + mono_oos=0.90 + style_r²=0.074 clean + max_corr=0.105 + incr_ic=0.0153 + cum_mdd=-1.42 + ls_t=3.08；alpha_surv=0.17 + ic_oos=0.0113 阻止 admit。**Kurt 4 阶矩 > Skew 3 阶矩在 (H-L)/C 上**——T001 shape 路径首次 partial breakthrough。
> - **C002/C003 Q90/Q90-Med → reject**：vol_20d exp 44–47, style_r² 0.46–0.60, incr_ic 严重负——**robust 分位估计仍在二阶矩空间**（F001 本地数据点）。
> - **C004 Skew120 → reject**：mono_is=0.50 < 0.6 + 复现 batch_043 C004 mono paradox（0.5→1.0）。**升格的 mono_is ≥ 0.6 硬下界纪律首次执行命中**。
> - **C005 sign-gated Skew → reject**：ls_t IS/OOS 符号翻转 + str_1m exp=2.49——sign-gated shape 在 csi1000 不稳健。
> - **C006 (Q80-Q20)/Median → reject**：scale-free 归一化 vol_20d exp 44→20 减半 + alpha_surv 0.35→0.70，但 mono_is=-1.0 / mono_oos=-0.30 OOS 崩塌——scale-free 不能单独撑起稳健 rank-order。
> - MT budget cumulative 228 → **234** · direction 6 → **12** · bucket `high` (adjusted `medium`)
>
> **下一步**：收缩到 Kurt-centric（Kurt90/Kurt120 长窗 + Kurt × non-vol RHS orthogonalize）；不再尝试 Skew/Quantile/IQR-ratio 变体；round 3 仍 0 admit → 转 `saturated`。
>
> **Operations**: `priority: medium → low`（MT 消耗快 + 2 rounds 0 admit + 设计空间收窄至 Kurt 变体）· `status: exploring` 保持

> [!quote]- 2026-04-24 · [[batches/batch_043/judge|batch_043]]
> **首批分裂结论：magnitude/ratio 全败，shape 存活但悖论组合** · admit=0 / reserve=4 / reject=2
>
> - **T002 DISPROVEN**：C005 短长比 + C006 变化率，IC 稳定 9 年同号但 incr_ic 全负 (-0.025 / -0.017)，vol_20d exp 13.9–27.7——range ratio/velocity 与 F001/F009 共享反转簇载体。**第 3 次跨方向独立确认**（+stochastic / +vwap_proxy）升格 lessons 元教训。
> - **T001 部分存活**：C001 timing (IdxMax) + C002 freq-high 封闭；C003 freq-low + C004 shape (Skew60) 存活 reserve。
> - **C004 悖论诊断**：4 个 error-kill 指标全过（max_corr=0.117, incr_ic=+0.014, mono_oos=+1.0, cum_mdd=-2.01 最浅）但 **mono_is=0.30 弱** + alpha_surv=0.14 poor——诊断为**非真错杀**；建议升格错杀侦测要件加 mono_is 硬下界 0.6。
> - MT budget cumulative 216 → **222** · direction 0 → **6** · bucket `medium`
>
> **Operations**　`priority: medium → low`（shape 路径需重新设计 + 工具链阻塞）· `status: exploring` 保持

---

## Related

- 🔴 [[return_distribution_signals]] `dead` — daily-return skew/kurt/Q-range 全部坍缩到 vol_20d；本方向用 range (high-low) 而非 return，**数学上不同**——关键测试（F301 同源）
- 🟡 [[stochastic_position]] `saturated` — (close - TsMin) / (TsMax - TsMin) rank-order 崩塌；本方向是 range 大小 & timing 而非 close 在 range 内的位置
- 🟡 [[intraday_price_formation]] `saturated` — 单日 (close-low)/(high-low) mono_sign_flip；本方向在 N 日窗口而非单日 intrabar（F005 algebraic 共动律同源）
- 🟡 [[liquidity_acceleration]] `saturated` — 流动性 ratio 全部落入 F001 吸收簇；T002 已确认 range ratio 同样命运
- 🔴 [[quantile_shape_signals]] `dead` — Quantile robust ≠ vol_20d orthogonal（F301 同源）；本方向 batch_045 C002/C003 是该律的本地复现
- 📖 [[lessons#Structural Constraints]] — F001 / F301 vol_20d 吸收律 + F005 OHLC algebraic 共动律
- 📖 [[lessons#Data Facts]] — A 股 10% 涨跌幅约束对 range 上限的结构影响
- 📖 [[lessons#Operator Registry]] — TsSkew / IdxMax / Kurt 自定义算子，C.kernels=1
