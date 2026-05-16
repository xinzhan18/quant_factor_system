---
direction_tag: barra_residual_alpha
status: saturated
priority: low
rounds: 8
admits: 1
last_batch: batch_054
last_admits: []
last_goal: 'T014 — 测 rank-diff geometry × residual signals 范式（barra_residual_alpha
  方向 7 轮再启动）。


  方向 saturated 后再开的复活路径：cockpit hint 指出 rank-diff 在 raw OHLCV 4 family 已成熟（5 admit
  跨 microstructure / overnight×2 / OHLC / gap），但**residual-based signal 上的 rank-diff
  尚未验证**——这是完全独立的 paradigm（残差几何 vs raw signal 几何）。同时 6 轮探索仅 1 admit (F004)，大量 thread
  未尝试。


  设计严遵 7+ 条 rank-diff geometry 律：

  (1) C001-C003 测 rank-diff × residual：LHS=residual-derived stat（|res|_mean / res_std
  / res_cumsum），RHS=非饱和原子（turnover_20 / amount_60 / RV_60）；

  (2) C004-C006 测 residual-only 路径（无 rank-diff）：residual 自相关 / 多周期 EMA decay / 累积冲击
  SNR；

  (3) 严避免：F004（库内 residual 自身，本批 LHS 都是 residual 的统计量而非 residual 本身，corr<0.30 期望）；F018
  amount_20 RHS（C002 用 amount_60 长窗）；F012 Amihud_20 RHS（不用 amihud-family）；F020 anti-anchor
  cluster（本批无 OHLC body higher-moment LHS）；

  (4) 全 Python 路径（DSL 无法表达 Barra residual）；

  (5) 严防 lookahead——所有候选用 close.pct_change(1) past return，不用 shift(-k)。


  C001 |residual|_mean × turnover rank-diff — 残差 dispersion vs 原始流动性

  C002 residual_std × amount_60 rank-diff — 残差 second-moment vs 长窗 amount

  C003 residual_cumsum_5 × RV_60 rank-diff — 残差短窗动量 vs 长窗价格 vol

  C004 residual_autocorr_20 — 残差时序持续性（残差只用，无 rank-diff）

  C005 EMA(res,5)-EMA(res,20) — 残差多周期 decay 结构

  C006 |sum(res,20)| / sum(|res|,20) — 残差累积冲击 directional efficiency


  T014 验证目标：rank-diff paradigm 是否能跨出 raw signal 4 family，扩展到 residual 几何空间？若 admit
  ≥1 → barra_residual_alpha 复活；若 0 admit + reserve ≤1 → 该方向真正 dead（5 method-switch
  + residual 路径全证伪）。'
last_activity: '2026-04-25T01:12:38Z'
created_batch: batch_012
members:
- F004
retired_members:
- F005
merged_into: null
---
# barra_residual_alpha

> [!abstract]+ 方向概要
> **状态**　🟡 saturated · priority=low · rounds=8 · admits=1
> **最近**　[[batches/batch_054/judge|batch_054]] · 2026-04-25 · admit=0 / reserve=0 / reject=5 (+1 compute_error)
> **一句话**　F004 是 7-style × OLS-family 残差的几何不变量；basis / 损失 / 标准化 / interaction / 时序后处理 5 类路径全 collapse；rank-diff × residual paradigm (T014) 也证伪——三重 saturated（信号设计层 + 数据契约层 + **P033 跨方向 OOS sign-flip 律共证**，Python residualize 唯一生还路径关闭）。

---

## Hypothesis

> [!failure]+ ⚠️ 证伪后的 Hypothesis（2026-04-21 saturated · 2026-04-25 二次确认）
> **原始假设**：Regress(Returns ~ 7 Barra styles) 的 residual 携带独立于风格因子的 idiosyncratic alpha。
>
> `Barra residual alpha = Regress(Returns ~ vol_20d + str_1m + turnover_20d + log_circ_cap + book_to_price + mom_12_1 + ep_ratio) → Residuals`
>
> **成立部分**：F004 admit 确认 residual IC=0.033 > raw IC=0.024 的 incremental alpha 存在。
>
> **⚠️ 证伪部分**（三层独立 disprove）：
> 1. **信号设计层（T002 + T014 共证）**：在 7-style basis × OLS-family 框架内，F004 是几何不变量——5 类路径 (basis 子集 / 损失函数 / 标准化 / interaction / 时序后处理) 全 collapse 到 corr ≥ 0.91；rank-diff × residual paradigm 跨出 4 raw family 的尝试也失败——残差 higher-moment 在 train/val regime 系统性 sign-flip（[[#F003 升格]]），残差路径几何 (autocorr / SNR) 是 IC<0.01 noise floor。
> 2. **数据契约层（T003 + T014 共证）**：Python residual + rolling 算子在 csi1000 系统性 coverage ≈ 0.71-0.73 << 0.80 hard_gate（[[#F008 升格]]），且 loader 不响应 candidate REQUIRED_FIELDS（[[#F304 升格]]）——多个信号本身健康（C005 alpha_surv=1.57 + style_r²=0.024）的候选纯 coverage 单闸 KO。
> 3. **跨方向 OOS sign-flip 律（P033 · b092 first 实证 · 本方向姊妹律）**：tsrank_candlestick_ratio b092/C001 对 admit cluster 做 single-step Python cross-section OLS residualize → train_ic=+0.030 / val_ic=-0.004 + mono_flip 0.4→-0.4，**Python residualize 在 close-position 域被 b092 首实证关闭为"唯一生还路径"**。机制：cross-section OLS `y = α + β·F_admit + ε` 的 ε 在 train 期含残余 alpha-bearing component，train OLS 过拟合该残余 sign，OOS 噪音独立性使 sign 翻转——与本方向 T002/T014 残差 higher-moment regime sign-flip 同律家族但**适用域更宽**（不限 higher-moment LHS，single-step OLS 也失败）。
>
> **复活条件**（必须 (a)+(b)+(c) 同时满足才有意义再启）：
> (a) **数据契约修复**：T003 loader 扩 REQUIRED_FIELDS 动态联合列 + 残差 NaN 预填充（forward fill 或 industry mean），或改 cross-sectional 算子代替 rolling（CsRank / CsZscore 不需 min_periods 历史）。F202 提议 direction-aware coverage 阈值放宽到 0.70 是临时 workaround。
> (b) **范式跳出**：(i) 加非 Barra style basis（行业 / GICS / microstructure factor model）；(ii) nonparametric residualization（kernel ridge / NN）；(iii) 与库其他因子的非线性 ensemble。**严禁** 再测 raw fundamental / intraday signed / residual_ret 三类 atom 的 higher-moment LHS（F003 / F201 升格 generator pre-block）。
> (c) **P033 几何独立性自检**：候选 design rationale 含 "Python residualize" 字样时 manifest expr_safety 段必须显式自检——(i) atom max_corr vs target prototype < 0.40，(ii) prototype 含 ≥2 admit anchor，(iii) candidate 估算 coverage ≥0.85；三条件任一 fail → Phase 1 freeze rationale 标 `python_residualize_skip`。Reserve revival pool 中所有 "Python residualize on admit" 路径 cross-batch retro 标 `default-skip`，避免 saturated direction 内无限循环 reserve 复活。

---

## Threads

### T001: Barra residual 有效性 [✓ ANSWERED batch_012]

> [!success]+ Thread 结论
> **Question**: Barra residual returns 是否携带独立于风格因子的 alpha？
> **Evidence**:
> - [[batches/batch_012/candidates/C001|b012 C001]]　IC=0.024 ICIR=0.293 ls_t=7.34 Barra_residual_IC=0.033 > raw IC=0.024 → **admit → [[factors/F004]]**
> - [[batches/batch_012/candidates/C003|b012 C003]]　Barra_residual_IC=0.033 但 style_r²=0.289 + vol_20d exposure=15.6 → **reserve**
>
> **Answer**: 假设成立，F004 admit。

### T002: 7-style × OLS 框架内可分离性 [✗ DISPROVEN batch_015]

> [!failure]+ Thread 结论
> **Question**: 调整 basis 子集 / 损失函数 / 标准化 / interaction / 时序后处理能否产生与 F004 独立 (corr<0.7) 的残差？
> **Evidence**（5 类路径全证伪）:
> - **A · basis 子集**：[[batches/batch_014/candidates/C002|b014 C002]] vol_20d-keep+EMA → corr=0.987；[[batches/batch_014/candidates/C004|b014 C004]] strip momentum → sign_flip；[[batches/batch_014/candidates/C005|b014 C005]] keep size only → corr=0.906
> - **B · 损失函数**：[[batches/batch_015/candidates/C001|b015 C001]] Huber IRLS → corr=0.907；[[batches/batch_015/candidates/C004|b015 C004]] winsor ±5MAD → corr=0.941
> - **C · 标准化**：[[batches/batch_015/candidates/C003|b015 C003]] heteroscedastic-norm → corr=0.927
> - **D · interaction**：[[batches/batch_015/candidates/C005|b015 C005]] vol×turn 乘积 style → corr=0.997（collinear 被 pinv 自动消除）
> - **E · 后处理**：[[batches/batch_014/candidates/C006|b014 C006]] F004 × Sign(Δvolume_5d) → ic_oos=0.0071 < 0.008
>
> **旁证**：[[batches/batch_014/candidates/C001|b014 C001]] 纯 vol_20d |IC|=0.063 但 style_r²=0.999 + incremental_ic=-0.046 → magnitude ≠ tradability，residualization 是 12× 清洁度 value-add；[[batches/batch_013/candidates/C002|b013 C002]] vol_20d-only residual → reserve；F005（20d 变体）admit 后于 2026-04-20 retired（bit-for-bit duplicate F004，near_duplicate gate 对 Python 盲区）。
>
> **Answer**: F004 是 7-style basis × OLS-family 上的几何不变量。后续探索必须跳出该框架。

### T014: rank-diff × residual paradigm [✗ DISPROVEN batch_054]

> [!failure]+ Thread 结论
> **Question**: rank-diff geometry 能否跨出 raw signal 4 family（microstructure / overnight×2 / OHLC / gap），扩展到 residual 几何空间？
>
> **Evidence**（6 候选完整投放，4 条独立 disprove 机制）:
> - C001 missing $turnover_rate → T003 数据契约缺口二次复现
> - C002 |residual|_std × amount_60: coverage=0.709 + mono_sign_flip(IS=-0.80→OOS=+0.70) dual-fail
> - C003 residual_cumsum_5 × RV_60: coverage=0.708 + sign_flip + oos_decay=-0.644 triple-fail
> - C004 residual lag-1 autocorr_20: coverage=0.717 + ic_oos=0.006 < 0.008（残差时序日频 noise floor）
> - C005 EMA(res,5)−EMA(res,20): coverage=0.725 单闸 fail（**信号本身极佳**：ICIR_oos=-0.169 + alpha_surv=1.57 + style_r²=0.024 + max_corr=0.441@F008）
> - C006 |sum(res,20)|/sum(|res|,20): coverage=0.717 + ic_oos=0.0003（残差 SNR noise）
>
> **4 条独立 disprove 机制**:
> 1. **数据契约层 coverage<0.80**: residual+rolling 在 csi1000 系统性 0.71-0.73（5/5 候选独立确认；F004 admit 时 coverage=0.999 无 rolling，本批暴跌 28pp）。机理：residual ~1% NaN + rolling min_periods≥10 + csi1000 上市日异质性 三因子复合。**与信号设计无关，是数据契约层结构性边界**——升格 [[#F008]] / [[#F202]] / [[#F304]]。
> 2. **REQUIRED_FIELDS loader 缺口（T003 二次复现）**: C001 missing $turnover_rate, 9 批后跨方向同律失败，升格修复优先级 high。
> 3. **残差 higher-moment regime sign-flip**: C002 mono_sign_flip + C003 sign_flip——加 b052 (PE Std) + b053 (signed body-pos Std)，跨 fundamental/intraday/residual **三大 family 独立确认硬律**——升格 [[#F003]] / [[#F201]] generator pre-block。
> 4. **残差路径几何 statistic 是 noise**: autocorr / directional efficiency 类 IC<0.01——残差已剥离 alpha-bearing component 后无法再生 alpha。
>
> **Answer**: rank-diff geometry × residual signals paradigm **DISPROVEN**——双层（数据契约 1 + 信号设计 3,4）证伪。**rank-diff 范式跨出 raw signal 4 family 第一次明确失败**，与 b052 / b053 合计三次连续中断（升格 [[#F002]] / [[#F305]] rank-diff 7 条硬约束 + 5 律泛化边界）。
>
> **复活路径**：必须先解决 T003 + residual 数据完整性 (cross-sectional 算子代替 rolling，或扩 min_periods 容错)——不是阈值校准能修复的范畴。

### T003: Lookahead detection + 数据契约缺口 [⚠ 二次复现 待系统修复]

> [!note]+ Thread 进度
> **Question**: hard_gate 是否充分检测 Python 候选时序泄漏？REQUIRED_FIELDS 契约是否被 loader 遵守？
>
> **Evidence**:
> - [[batches/batch_014/candidates/C003|b014 C003]]　`close.shift(-HORIZON)/close - 1` 把 t+5 累计收益作为 t 因子值；hard_gate 8 项全过，但 ic_oos=0.386 / icir=4.63 / ls_t=83 / ls_max_dd=0 / win_rate=1.0 / sortino=inf 是构造性 leak artifact
> - [[batches/batch_015/candidates/C002|b015 C002]]　REQUIRED_FIELDS=["$close","$high","$low"] → `compute_error: market_df missing $high/$low`（首次）
> - [[batches/batch_054/candidates/C001|b054 C001]]　REQUIRED_FIELDS=["$close","$turnover_rate"] → `compute_error: market_df missing ['$turnover_rate']`（二次跨方向同律，9 批后；loader 默认列不含 $turnover_rate，T003 中期方案优先级升至 high）
>
> **系统盲区**:
> 1. Barra residualize 只剥截面风格，不防时序 leak
> 2. hard_gate 当前无 negative-shift 检测、无 "too good to be true" 哨兵
> 3. loader 忽视 Python factor 的 REQUIRED_FIELDS 声明（[[#F304]] / [[#F008]] 升格）
>
> **Next probes**:
> - **短期**：主 agent 对 |ic_oos|>0.10 候选 manual review
> - **中期**：loader 扩默认列加 OHLC 全集 / phase1 freeze 时 validate REQUIRED_FIELDS ⊆ loader 列
> - **长期**：hard_gate 增 AST 扫描禁 `shift(-k)` in factor value path + 哨兵指标（ls_max_dd=0 / win_rate=1.0 / sortino=inf 任一触发 → suspicion queue）

---

## Lessons 升格（反复出现经验）

1. **时序平滑/标准化不改 cross-sectional rank**：EMA / rolling-std / heteroscedastic-norm 对截面秩零贡献（T002 路径 A+C 三证）。
2. **鲁棒损失 ≈ OLS 在低尾部污染数据上**：Huber / winsor ±5 MAD 对 A 股日频 β 估计几乎零修正（T002 路径 B 二证）。
3. **共线 style 被 pinv 自动消除**：interaction/duplicate basis 不产生新自由度（vol×turn corr=0.997）。
4. **magnitude ≠ tradability**：|IC|=0.063 的纯 vol_20d style_r²=0.999，residualization 才是 value-add。
5. **Python factor 构造安全必须纳入 hard_gate**：negative-shift / forward-cumulative 等构造性 leak 无法被 IS/OOS 统计指标捕获。
6. **残差 higher-moment regime sign-flip**（[[#F003]] / [[#F201]]）：raw fundamental / intraday signed / residual_ret 三类 atom 的 Std/Var/Cumsum LHS 在 csi1000 train→val regime 系统性翻号。Generator pre-block。Scale-free ratio (body_ratio, gap_ret) 不属此律（F019/F020 admit 反证）。
7. **残差路径几何 (autocorr / SNR / directional efficiency) 是 noise floor**：残差已剥离 alpha-bearing component，path coherence 类 transformation 无法再生 alpha。
8. **Python residual + rolling csi1000 系统性 coverage ≈ 0.71**（[[#F008]] / [[#F202]]）：跨 3 方向 12+ 候选独立确认；residual ~1% NaN + rolling min_periods + 上市日异质性 三因子复合 → 全期均值 < 0.80 hard_gate。修复路径：cross-sectional 算子代替 rolling / loader 端 NaN 预填充 / direction-aware coverage 阈值放宽。
9. **DSL Div / rank-preserving 不替代真 orthogonalization**（[[#F304]]）：CsZscore / Scale / SignedPower / Sigmoid / Tanh / Softmax 在 cross-section 空间对 IC 零贡献；Div(factor, vol_proxy) 不是真去暴露——要么保序、要么 style 搬家。真 orthogonalization 必走 Python OLS / Barra residual（但需独立处理 coverage 问题）。
10. **P033 · Cross-section OLS residual OOS sign-flip 律**（[[#P033]]，b092 first 实证 + 本方向 T002/T014 共证家族扩展）：对 admit cluster 做 single-step Python cross-section OLS residualize 在 csi1000 daily 上 **default OOS sign-flip**——atom 主信号若在 cluster 投影内时，残差是 train 期残余 alpha-bearing 的 sign 噪音，OOS regime drift 后 sign 翻转。本律适用域比 T002/T014 (限 higher-moment LHS) 更宽：single-step OLS 也失败。**Python residualize 路径默认关闭**——仅当 (a) atom max_corr vs prototype < 0.40 + (b) prototype 含 ≥2 admit anchor + (c) coverage ≥0.85 三条件同时满足才可启动。与 T003 数据契约层失败律 (coverage<0.80) 配套，共同封堵 Python residualize 复活路径。

---

## Related findings (Phase 5 升格摘要)

> [!info]- Phase 5 distillation 已就本方向沉淀 7 条 finding（详见 `_consolidation/packet_direction_barra_residual_alpha.md`）
>
> - **F002 / F305** (severity=high) — rank-diff geometry 7 硬约束 + 5 律泛化边界；本方向是范式 disprove 端贡献者
> - **F003 / F201** (severity=high) — higher-moment LHS regime sign-flip 跨 3 family 律 + Phase 1 generator pre-block 提案；本方向 b054 C002/C003 命中
> - **F008 / F202** (severity=medium) — Python residual+rolling csi1000 coverage≈0.71 数据契约边界 + direction-aware coverage 阈值放宽提议（barra_residual_alpha → 0.70）
> - **F304** (severity=medium) — DSL Div / rank-preserving 不替代真 orthogonalization；Python residual coverage 边界
> - **P033** (severity=medium，hypothesis_promoter/025，b092 first 实证) — cross-section OLS residual OOS sign-flip 律 + Python residualize 唯一生还路径关闭警示；本方向 T002/T014 残差 higher-moment sign-flip 是其姊妹律家族成员，P033 适用域更宽（single-step OLS 也失败，不限 higher-moment）

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_012/candidates/C002\|b012 C002]] | Barra residual variant | sign_flip + oos_decay |
| [[batches/batch_012/candidates/C004\|b012 C004]] | 5d rolling residual | IC=0.007 < 0.008 |
| [[batches/batch_012/candidates/C005\|b012 C005]] | 20d momentum residual | IC=-0.0035（方向反转） |
| [[batches/batch_013/candidates/C003\|b013 C003]] | residual × turnover interaction | sign_flip + oos_decay=-1.648 |
| [[batches/batch_013/candidates/C004\|b013 C004]] | 10d Barra styles | redundant with C001 |
| [[batches/batch_013/candidates/C005\|b013 C005]] | size-neutral quintile | compute_error |
| [[batches/batch_014/candidates/C002\|b014 C002]] | vol-20d-keep + 3d EMA | corr=0.987 with F004 |
| [[batches/batch_014/candidates/C003\|b014 C003]] | 5d forward cumulative residual | **lookahead leak** |
| [[batches/batch_014/candidates/C004\|b014 C004]] | strip only momentum cluster | sign_flip + ic_oos_too_low |
| [[batches/batch_014/candidates/C005\|b014 C005]] | strip all except log_circ_cap | corr=0.906 with F004 |
| [[batches/batch_014/candidates/C006\|b014 C006]] | F004 × Sign(Δvolume_5d) | ic_oos=0.0071 |
| [[batches/batch_015/candidates/C001\|b015 C001]] | Huber IRLS residual | corr=0.907 |
| [[batches/batch_015/candidates/C002\|b015 C002]] | OHLC residual variant | compute_error: missing $high/$low |
| [[batches/batch_015/candidates/C003\|b015 C003]] | heteroscedastic-norm | corr=0.927 |
| [[batches/batch_015/candidates/C004\|b015 C004]] | winsorized OLS (±5 MAD) | corr=0.941 |
| [[batches/batch_015/candidates/C005\|b015 C005]] | OLS + vol×turn interaction | corr=0.997 |
| [[batches/batch_054/candidates/C001\|b054 C001]] | rank-diff × turnover (residual LHS) | compute_error: missing $turnover_rate |
| [[batches/batch_054/candidates/C002\|b054 C002]] | \|res\|_std × amount_60 rank-diff | coverage=0.709 + mono_sign_flip |
| [[batches/batch_054/candidates/C003\|b054 C003]] | res_cumsum_5 × RV_60 rank-diff | coverage=0.708 + sign_flip + oos_decay |
| [[batches/batch_054/candidates/C004\|b054 C004]] | residual autocorr_20 | coverage=0.717 + ic_oos=0.006 noise |
| [[batches/batch_054/candidates/C005\|b054 C005]] | EMA(res,5)−EMA(res,20) | coverage=0.725（信号健康，coverage 单闸 KO） |
| [[batches/batch_054/candidates/C006\|b054 C006]] | \|sum(res,20)\|/sum(\|res\|,20) | coverage=0.717 + ic_oos=0.0003 noise |

---

## Related

- 🔴 [[lessons#Structural Constraints]] `reference` — Barra style coupling + rank-diff geometry + Python factor contract 教训汇编
- 🟡 [[amount_volatility_signal]] `saturated` — vol_20d 天花板同源；Python residual coverage 同律共证（b033）
- 🟡 [[value_liquidity_interaction]] `saturated` — DSL 空间穷尽 + Python residual coverage 同律共证（b034）；rank-diff 跨族失败（b052）
- 🟡 [[intraday_price_formation]] `saturated` — rank-diff 跨族失败（b053）+ higher-moment regime sign-flip 共证
- 🔴 [[fundamental_momentum]] `dead` — ep_ratio 已是 Barra style；强化本方向 basis 穷尽结论；higher-moment regime sign-flip 共证（b052）

---

## Narrative Log

> [!quote]+ 2026-05-16 · Phase 5 consolidation · P033 跨方向共证
> **方向维持 saturated**（无新 batch 投放）。Phase 5 hypothesis_promoter/025 升格 **P033 · Cross-section OLS residual OOS sign-flip 律**——tsrank_candlestick_ratio b092/C001 对 admit cluster (F008, F026) 做 single-step Python residualize 首实证 OOS sign-flip (train_ic=+0.030 / val_ic=-0.004 + mono_flip 0.4→-0.4)。**本方向 T002/T014 残差 higher-moment regime sign-flip 是 P033 姊妹律**——P033 适用域更宽（single-step OLS 也失败，不限 higher-moment LHS）。**Python residualize 唯一生还路径在 close-position 域被 b092 首实证关闭**——本方向复活条件新增 (c) P033 几何独立性自检 (atom max_corr<0.40 + ≥2 anchor + coverage≥0.85 三条件 AND)。Reserve revival pool "Python residualize on admit" 路径全标 `default-skip`。

> [!quote]- 2026-04-25 · [[batches/batch_054/judge|batch_054]]
> **admit=0 / reserve=0 / reject=5 (+1 compute_error)** — T014 (rank-diff × residual paradigm) DISPROVEN，**4 条独立机制**：(1) 数据契约层 coverage<0.80 系统性 (5/5 候选 0.708-0.725)；(2) T003 二次复现 missing $turnover_rate；(3) 残差 higher-moment regime sign-flip 跨 3 family 第三次确认；(4) 残差路径几何 statistic 是 noise floor。**rank-diff 范式三连中断 (b052/b053/b054)** 共揭示 9-10 条新限制律，直接驱动 Phase 5 升格 [[#F002]] / [[#F003]] / [[#F008]] / [[#F201]] / [[#F202]] / [[#F304]] / [[#F305]]。**下一步**：方向维持 saturated（不退化为 dead——结构教训知识价值已交付）；future reopen 必须先解决 (a) loader REQUIRED_FIELDS 契约 + (b) residual 数据完整性 (cross-sectional 算子代替 rolling)。

> [!quote]- 2026-04-21 · [[batches/batch_015/judge|batch_015]]
> **admit=0 / reserve=0 / reject=5** — 方向 saturated。**F004 不动点定理（实验性建立）**：5 method-switch 候选全 collapse——Huber=0.907 / hetero=0.927 / winsor=0.941 / vol×turn=0.997。F004 是 7-style basis × OLS-family 上的几何不变量。**跨 b014+b015 saturation 证据链**：basis 子集 (vol_20d 主导) → 损失函数 (几何不变) → 时序后处理 (cross-section rank 不变) → interaction (collinear pinv 消除) → forward horizon (lookahead leak)。**状态转移**：productive → saturated，priority high → low。

> [!quote]- 2026-04-21 · [[batches/batch_014/judge|batch_014]]
> **admit=0 / reserve=1 / reject=5**。三大发现：(1) vol_20d 主导残差空间（C002+C005 双向证明：strip 6 keep vol_20d corr=0.987；strip 6 keep log_circ_cap corr=0.906；其余 6 styles 合计贡献 <10%）；(2) C003 暴露 hard_gate 时序检测盲区（forward shift lookahead leak，8 项 gate 全过但全是 artifact）→ 新建 T003；(3) C001 纯 vol_20d reserve：|IC|=0.063 但 style_r²=0.999 + incremental_ic=-0.046——residualization 是 12× 清洁度 value-add。

> [!quote]- 2026-04-19 · [[batches/batch_013/judge|batch_013]]
> **admit=1 / reserve=1 / reject=3**。C001 admit (F005，60d 变体，后因 F004 duplicate 于 2026-04-20 retired) replicate batch_012；vol_20d dominant (coef=4.44) 但 residual IC > raw IC。C002 reserve：vol_20d-only residual (ICIR=0.243 ls_t=7.28 alpha_surv=1.62) 比全剥离 survival 更高。C003/C004/C005 reject (sign_flip / 重复 / compute_error)。

> [!quote]- 2026-04-19 · [[batches/batch_012/judge|batch_012]]
> **admit=1 / reserve=1 / reject=3** — 方向首批验证假设成立。C001 admit (F004 barra_residual_return)：IC=0.024 ICIR=0.293 ls_t=7.34；Barra_residual_IC=0.033 > raw IC=0.024；incremental_ic=0.032 全新机制空间。C003 reserve (style_r²=0.289 + vol_20d exposure=15.6 耦合严重)。C002/C004/C005 reject。T001 answered；T002 active。
