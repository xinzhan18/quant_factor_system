---
direction_tag: value_liquidity_interaction
status: saturated
priority: low
rounds: 9
admits: 1
last_batch: batch_052
last_admits: []
last_goal: "T012 rank-diff 范式第 7 次跨家族泛化——测 value (PE/PB/PS) × liquidity (turnover/amount)\
  \ 在 rank-diff 几何下能否独立兑现。\n\n当前 rank-diff 6 admit 跨 5 family (microstructure×2 /\
  \ overnight×2 / OHLC×1 / gap×1 = F015/F016/F017/F018/F019/F020)。\nvalue_liquidity_interaction\
  \ 仅 F002 (Div($pb,Mean($amount,20)) 原始比率，非 rank-diff)，本方向 7 轮探索仅 1 admit\n且全部 DSL\
  \ 路径 (Mul/Div/Sub-rank) + Python residual 已被验证封闭。本批 reopen 唯一未试角度：rank-diff geometry\n\
  在 value × liquidity 家族首次完整投放，借助 b050/b051 已确立的 4 条几何律设计 LHS/RHS。\n\n设计硬约束：\n(1)\
  \ 每候选 LHS 唯一 — 6 LHS 全不同 atomic value/liquidity 表达；\n(2) 严避免重演 T001-T007 disproven\
  \ 的 Mul/Div/PE_rate 路径；不用 Delta/$pe rate of change (lessons new_dead);\n(3) RHS\
  \ 端避开 RHS 共振饱和律 endpoints (overnight_5/turnover_5/amount_20/turnover_5_cv/price_vol_20-short)；\n\
  \    选 body_ratio_20/60 / |return|_60 / pb_60 / amount_60 / price_vol_60-long 等非饱和\
  \ basis;\n(4) LHS 端避开 size proxy 红线 (|corr|>0.3 vs $market_cap/$circ_market_cap)\
  \ — 不直接放 $market_cap;\n(5) 不重演 T003/T006 PE_rate 自归一化 (lessons.md new_dead 已升格);\n\
  (6) 优先 higher-moment LHS independence axis (Std/Var vs Mean) 复用 b050 T012 教训;\n\
  (7) 不重演 F002 同形 (Div($pb,Mean($amount,20)) 原始比率) — 本批全部 rank-diff 包装。\n\nC001 pe_vol_pricevol_rank_diff_20\
  \ — LHS=Std($pe_ratio,20) higher-moment of PE level (跳出 PE_rate 自归一化死区),\n  RHS=Mean(Std($close,5),60)\
  \ 60d price_vol 长窗 (区别 b051 dead RHS price_vol_20 短窗). 测 PE 横截面波动性\n  与 price_vol\
  \ 长窗的 rank-diff 几何独立性. 预期 max_corr@F002<0.3 (Std vs raw level), max_corr@F019<0.4\
  \ (LHS atomic 不同).\n\nC002 pe_per_turnover_body_ratio_diff_20 — LHS=Mean(Div($pe_ratio,$turnover_rate),20)\
  \ PE 单位换手率\n  (类似 illiquidity-adjusted PE, 不是 PE_rate 也不是 PE/amount = F002 dual),\
  \ RHS=Mean(body_ratio,20)\n  OHLC structural basis (b051 admit C002 已验证 body_ratio\
  \ 是新 RHS 安全类目). 测 \"value per liquidity\" 单调性.\n  预期 max_corr@F002<0.4 (PE/turnover\
  \ vs PB/amount 不同基本面对/不同分母), max_corr@F020<0.3 (LHS gap-vol vs PE-liq).\n\nC003\
  \ pb_turnover_jointvol_absret_diff_60 — LHS=Std(Mul($pb_ratio,$turnover_rate),60)\
  \ PB×turnover 乘积的时序波动 60d\n  (joint volatility of value×liquidity product, second-order\
  \ co-movement; 避开 Qlib Corr/Cov 跨字段 NaN-window shape bug),\n  RHS=Mean(Abs(Div(Delta($close,1),Ref($close,1))),60)\
  \ |daily_return| mean 60d (Amihud 分子无 amount 分母 — b051 C006 已开创该 RHS).\n  测 value-liquidity\
  \ 联合 vol vs return magnitude basis. 预期 max_corr@F012/F015 (Amihud)<0.4, max_corr@F002<0.3.\n\
  \nC004 turnover_vol_pb_long_diff_20 — LHS=Std($turnover_rate,20) turnover higher-moment\
  \ (Std 不是 Mean,\n  与 F033 mean_turnover_5 等 raw mean 不同), RHS=Mean($pb_ratio,60)\
  \ PB 长窗 fundamental basis (60d 而非 20d/40d).\n  \"liquidity volatility 卖方 × value\
  \ level 买方\" — 价值 × 流动性反向交叉. 预期 max_corr@F002<0.3 (LHS/RHS 完全反向),\n  max_corr@F004\
  \ (std_vol_20)<0.4 (turnover vs price std), max_corr@F035 (mean_turnover_20)<0.4\
  \ (Std vs Mean).\n\nC005 ps_amount_ratio_body_ratio_diff_60 — LHS=Mean(Div($ps_ratio,$amount),60)\
  \ PS 单位 amount 长窗 (与 F002 PB/amount_20 不同基本面 + 不同窗口),\n  RHS=Mean(Div(Abs(Sub($close,$open)),Sub($high,$low)),60)\
  \ body_ratio 长窗 60d (与 F019/F020 RHS body_ratio_20 不同窗口).\n  测 PS-based value ×\
  \ intraday body 长窗. 预期 max_corr@F002<0.5 (PS vs PB + 60d vs 20d 双层差异), max_corr@F019/F020<0.4\
  \ (60d vs 20d).\n\nC006 pb_stability_turnover_vol_diff_20 — LHS=Std(Mean($pb_ratio,5),20)\
  \ PB 5d-smoothed level 在 20d 的 stability\n  (compound moment: smooth-then-std, 测\
  \ PB 稳定性 — 类似 PB regime stickiness signal),\n  RHS=Mean(Std($turnover_rate,5),20)\
  \ turnover 5d-vol 20d agg (与 F019 RHS price_vol-style 同结构但用 turnover).\n  \"PB stickiness\
  \ × turnover micro-volatility\" — value persistence × liquidity micro-noise rank-diff.\n\
  \  预期 max_corr@F002<0.3 (compound LHS), max_corr@F019<0.4 (LHS PB vs body_ratio)."
last_activity: '2026-04-24T23:56:36Z'
created_batch: batch_005
members:
- F002
merged_into: null
---
# value_liquidity_interaction

> [!abstract]+ 方向概要
> **状态**　🟡 saturated · priority=low · rounds=7 · admits=1 (F002)
> **最近**　[[batches/batch_034/judge|batch_034]] · 2026-04-23 · admit=0 / reserve=0 / reject=5
> **一句话**　基本面 × 流动性交互：DSL 路径和 Python residual 路径都已跑完，剩下的只是不足 `coverage` 的 residual shadow，不再是可继续挖掘的方向。

---

## Hypothesis

> [!note]+ Hypothesis (rank-order 层已部分验证 · PnL 层未兑现)
> 纯流动性-波动率派生量全部撞 `vol_20d` 天花板 ([[amount_volatility_signal]] / [[turnover_structural_signal]] 教训)。脱困出路：引入**基本面风格维度** ($pe/$pb/$ps/$market_cap/$circ_market_cap 对应 ep_ratio / book_to_price / log_circ_cap Barra style)，与流动性特征交互。
>
> **三条经济学线索**：
> 1. **价值陷阱 vs 价值实现**：低 PE/PB × 高换手 = rerating；低 PE/PB × 低换手 = 基本面恶化已知
> 2. **小盘流动性溢价**：small_cap × high_liquidity 多 / small_cap × low_liquidity 空
> 3. **基本面-技术面脱钩**：PE 变化快 + amount 变化慢 = 潜在价值发现
>
> **结构性约束**：
> - 候选必须含 ≥1 基本面字段；避免纯流动性派生量
> - CP04 rubric (2026-04-19 放宽)：alpha_survival<0.30 poor / 0.30-0.50 borderline / >0.50 clean
> - Admit 门槛：`max_corr@F001 < 0.30 且 incremental_ic > 0.010`（Barra 脏但库独立即可）

---

## Threads

### T001: Value × Liquidity 交互 [✗ DISPROVEN batch_034]

> [!failure]+ Thread 结论
> **Question**: PE/PB 分位 × turnover 水平的交互是否产生独立于流动性因子的价值 alpha？
> **Evidence trail**:
> - [[batches/batch_005/candidates/C001|C001_b5]] Mul($pe, Mean(tr,20)) alpha_surv=0.26 dom=vol_20d → reject
> - [[batches/batch_005/candidates/C005|C005_b5]] Div($pb, Mean(amount,20)) **IC=+0.032 mono=+1.0 cum_dd=-2.17(全库最浅)** alpha_surv=0.30 → reject (positive edge 真实但被 vol_20d 吞 70%)
> - [[batches/batch_006/candidates/C003|C003_b6]] Div($pb, Mean(tr,20)) 诊断：分母换 tr 未改善 (0.30→0.28) → reserve
> - [[batches/batch_007/candidates/C003|C003_b7]] Sub(CsRank($pb), CsRank(Mean(tr,20))) **alpha_surv=0.71 (2.5× 改善)** 但 raw IC 0.032→0.011 (1/3 削弱) ls_t=0.33 → reserve
> - [[batches/batch_034/candidates/C001|C001_b34]] turnover-EP residual probe coverage=0.706 + sign_flip + decay=-4.141 → reject
> - [[batches/batch_034/candidates/C002|C002_b34]] deep residual probe 再加 `str_1m` 控制后 coverage=0.706 + sign_flip + decay=-7.403 → reject
>
> **Disproven**: 乘法/除法/秩差三条 DSL 路径都已封闭，而 batch_034 进一步证明连 Python residual 也救不回 T001。C001/C002 一旦剥掉 `vol_20d/turnover_20d/str_1m` 载体，只剩 coverage 不足且符号翻转的弱噪声，说明这条交互 edge 并不会以独立残差信号的形式存活。

### T002: Value × Liquidity rank-diff geometry [✗ DISPROVEN batch_052]

> [!failure]+ Thread 结论
> **Question**: rank-diff geometry (b049/b050/b051 在 microstructure/overnight/OHLC/gap 4 family 6 admit) 能否在 value × liquidity family 第 7 次跨家族兑现？
> **Evidence trail**:
> - [[batches/batch_052/candidates/C001|C001_b52]] Std($pe,20) × Mean(Std(close,5),60) → hard_gate sign_flip + mono_sign_flip
> - [[batches/batch_052/candidates/C002|C002_b52]] Mean(PE/turnover,20) × body_ratio_20 → ic_oos=0.012 ls_t=0.05 alpha_surv=0.46 max_corr=0.40@F020 → reject (三 borderline)
> - [[batches/batch_052/candidates/C003|C003_b52]] Std(PB×turnover,60) × |return|_60 → hard_gate sign_flip
> - [[batches/batch_052/candidates/C004|C004_b52]] Std(turnover,20) × Mean(PB,60) → ic_oos=-0.019 ls_t=-0.91 **alpha_surv=0.96(整批最干净!)** max_corr=-0.45@F002 → reject (CP4 干净但 CP3 弱 + CP5 cluster)
> - [[batches/batch_052/candidates/C005|C005_b52]] Mean(PS/amount,60) × body_ratio_60 → alpha_surv=0.12 严重 Barra 吞噬 + max_corr=0.47@F002 → reject
> - [[batches/batch_052/candidates/C006|C006_b52]] Std(Mean(PB,5),20) × Mean(Std(turnover,5),20) → hard_gate ic_oos=0.0077<0.008 + ls_t_is=12.18 → ls_t_oos=-0.13 崩塌
>
> **Disproven**: rank-diff 范式连胜 6 跨 5 family (microstructure/overnight×2/OHLC/gap) 在 value × liquidity 中断。三条独立失败机制 — 不是 RHS 选择问题（已避开所有 dead RHS endpoints + 引入新 RHS basis），是 LHS 端基本面字段在 rank-diff 几何中固有的 regime-sensitivity + F002 cluster anchor 锁死。**结论：rank-diff geometry 不是万能钥匙——saturated 方向的 anchor factor (本方向 F002) 会消化新候选的库余量**。

### T003: PE 变化率 vs amount 变化率脱钩 [✗ DISPROVEN batch_034]

> [!failure]+ Thread 结论
> **Question**: 基本面更新速率 vs 技术面反应速率的差异是否携带价值发现 alpha？
> **Evidence trail**:
> - [[batches/batch_005/candidates/C004|C004_b5]] Div(Delta($pe,20), $pe) **alpha_surv=0.92 dom=str_1m (方向首次突破天花板)** ls_t=-1.22 → reserve
> - [[batches/batch_006/candidates/C005|C005_b6]] Mul(PE_rate, Mean(tr,20)) alpha_surv=0.92→**0.29 崩塌** → reject (rate×level 乘法摧毁 rate 独立性)
> - [[batches/batch_007/candidates/C004|C004_b7]] Div(Delta($pe,20), Mean($pe,60)) alpha_surv=0.86 ls_t=-1.21 → reserve (60d-norm 边际)
> - [[batches/batch_007/candidates/C005|C005_b7]] Div(PE_rate, turnover_rate) **ls_t=-2.92 首破 2** ICIR=-0.284 mono=-0.9 9年全负 alpha_surv=**0.097 极端悖论** → reject
> - [[batches/batch_034/candidates/C004|C004_b34]] PE residual baseline `ic_oos=-0.0209` + `alpha_surv=1.09`，但 coverage=0.712 → reject
>
> **Disproven**: T003 已经不只是“DSL 封闭”。batch_034 显示即便做 signal-level residualization，PE 自归一化 rate 仍旧无法越过 `coverage` 硬闸。也就是说，这条路径的瓶颈不再是 Barra 风格，而是当前日频数据根本给不出足够可执行的 residual support。

### T006: Fundamental 自归一化速率 [✓ ANSWERED batch_006]

> [!success]+ Thread 结论
> **Question**: 基本面字段 `Div(Delta(X,n), X)` 的自归一化变化率是否普遍跳出流动性风格天花板？
> **Evidence trail**:
> - [[batches/batch_005/candidates/C004|C004_b5]] PE rate alpha_surv=**0.92** dom=str_1m ls_t=-1.22 → reserve
> - [[batches/batch_006/candidates/C001|C001_b6]] PB rate alpha_surv=**0.79** dom=str_1m ls_t=-1.49 → reserve
> - [[batches/batch_006/candidates/C002|C002_b6]] PS rate alpha_surv=**0.72** dom=str_1m ls_t=-1.47 → reserve
> - [[batches/batch_007/candidates/C001|C001_b7]] 3-funda 等权合成 alpha_surv=**0.86** ls_t=-1.27 → reserve
> - [[batches/batch_034/candidates/C005|C005_b34]] residual composite `alpha_surv=1.20` + `barra_residual_ic=-0.0236`，但 coverage=0.712 → reject
>
> **Answer**: **PE/PB/PS 自归一化速率三点通用性确立**——「基本面字段自归一化变化率跳出 vol_20d 天花板」在 rank-order 层是**跨 valuation 指标普适机制**，不是 PE 孤证。但 ls_t 全部 -1.2~-1.5 <2，L/S PnL 层未兑现。DSL 等权合成不产生信噪比增益（合成等权 ≠ 合成加权）。
> **Next**: 无。batch_034 已证明连 residual composite 也被 coverage 上限卡死，线程知识结论充足但工程出口关闭。

### T007: 跨基本面 Rank-Diff [✗ DISPROVEN batch_034]

> [!failure]+ Thread 结论
> **Question**: 不同基本面字段 ($pe/$pb/$ps) 之间的 rank 差异是否携带独立于 Barra 的价值发现信号？
> **Evidence trail**:
> - [[batches/batch_009/candidates/C002|C002_b9]] Sub(CsRank($pe), CsRank($pb)) mono_sign_flip → reject (level rank-diff 非对称 shift)
> - [[batches/batch_009/candidates/C003|C003_b9]] Sub(CsRank(PE_rate), CsRank(PB_rate)) 9年全正 cum_dd=-1.54 **incr_ic=+0.019 (库增值真实)** ls_t=0.47 → reserve
> - [[batches/batch_009/candidates/C007|C007_b9]] Sub(CsRank(turnover), CsRank(PE)) **ls_t=-2.43 mono=-1.0 (方向 PnL 最强)** vol_20d=18.8 incr_ic=-0.035 → reserve
> - [[batches/batch_034/candidates/C003|C003_b34]] cross-funda residual probe max_corr=0.027 仍极低，但 coverage=0.712 + ic_oos=-0.0069 → reject
>
> **Disproven**: T007 最后的希望是把 C003/C007 这组互补悖论放到 Python residual 环境里重验。batch_034 证明即便保留极低库相关，跨基本面 rank-diff 也只能留下过弱、低覆盖的 residual shadow，无法兑现为可 admit alpha。

### T004: PB × 波动率交互 [✗ DISPROVEN batch_005]

> [!failure]+ Thread 结论
> **Question**: 低 PB × 低波动率 = 稳定的便宜（价值）vs 低 PB × 高波动率 = 不稳定的便宜（困境）？
> **Evidence trail**: [[batches/batch_005/candidates/C003|C003_b5]] Mul($pb, Std($close,20)) alpha_surv=**0.083 (史上最差)** dom=vol_20d → reject
> **Disproven**: `Mul(fundamental_ratio, Std(price))` 是波动率 proxy 教科书样本——未归一化 Std 量纲主导，Barra vol_20d 吞 92% IC。

### T005: EP × momentum 交互 [✗ DISPROVEN batch_005]

> [!failure]+ Thread 结论
> **Question**: 高 E/P × 正动量 = 确认的便宜？
> **Evidence trail**: [[batches/batch_005/candidates/C002|C002_b5]] Mul(Div(1,$pe), Mean(tr,20)) alpha_surv=0.22 dom=turnover_20d → reject
> **Disproven**: EP×turnover 乘法撞 turnover_20d 簇；"便宜+热闹"在 A 股语境下实测负 alpha 与 hypothesis 反向——更接近散户拥挤。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_005/candidates/C001\|C001_b5]] | Mul($pe, Mean(tr,20)) | alpha_surv=0.26 + dom=vol_20d；PE 乘法被量纲吞 |
| [[batches/batch_005/candidates/C002\|C002_b5]] | Mul(1/$pe, Mean(tr,20)) | alpha_surv=0.22 + dom=turnover_20d；EP×turnover 反向 hypothesis |
| [[batches/batch_005/candidates/C003\|C003_b5]] | Mul($pb, Std($close,20)) | alpha_surv=0.083 (史上最差)；未归一化 Std 波动率 proxy |
| [[batches/batch_005/candidates/C005\|C005_b5]] | Div($pb, Mean($amount,20)) | IC=+0.032 mono=+1.0 但 alpha_surv=0.30 + dom=vol_20d；$amount 分母退化 |
| [[batches/batch_006/candidates/C004\|C004_b6]] | Div($pe, Mean(tr,20)) | **alpha_surv=0.0009 极端记录**；"低 style_r² ≠ barra-clean" 标本 |
| [[batches/batch_006/candidates/C005\|C005_b6]] | Mul(PE_rate, Mean(tr,20)) | rate×level 乘法摧毁 rate 独立性；alpha_surv 0.92→0.29 崩塌 |
| [[batches/batch_007/candidates/C002\|C002_b7]] | Sub(CsRank(PE_rate), CsRank(Mean(tr,20))) | 非对称 rank-diff hard_gate sign_flip + oos_decay=-5.95 |
| [[batches/batch_007/candidates/C005\|C005_b7]] | Div(PE_rate, turnover_rate) | ls_t=-2.92 首破 2 但 alpha_surv=0.097；静态正交 ≠ 动态正交悖论 |
| [[batches/batch_009/candidates/C001\|C001_b9]] | PE_rate / Mean(PE_rate, 60) | sign_flip + ic_oos_too_low；self-norm 放大 regime 漂移 |
| [[batches/batch_009/candidates/C002\|C002_b9]] | Sub(CsRank($pe), CsRank($pb)) | mono_sign_flip IS=-0.60 OOS=0.90；level rank-diff 非对称 shift |
| [[batches/batch_009/candidates/C004\|C004_b9]] | PE_rate / turnover_rate_of_change | sign_flip + oos_decay=-16.9；ratio 放大 sign 不稳 |
| [[batches/batch_009/candidates/C005\|C005_b9]] | (PE_rate + PB_rate) / 2 | dom=str_1m 首次 alpha_surv=0.883 但 incr_ic=-0.033 库 reducer |
| [[batches/batch_009/candidates/C006\|C006_b9]] | PB_rate / turnover_rate_of_change | sign_flip + oos_decay=-32.5；ratio 放大 regime 崩溃 |
| [[batches/batch_034/candidates/C001\|C001_b34]] | residualized turnover rank + EP rank | coverage=0.706 + sign_flip + decay=-4.141；T001 residual 失效 |
| [[batches/batch_034/candidates/C002\|C002_b34]] | deep residualized turnover rank + EP rank | coverage=0.706 + sign_flip + decay=-7.403；加 `str_1m` 控制后更差 |
| [[batches/batch_034/candidates/C003\|C003_b34]] | residualized PE_rate rank - PB_rate rank | coverage=0.712 + ic_oos=-0.0069；库干净但强度过弱 |
| [[batches/batch_034/candidates/C004\|C004_b34]] | residualized PE_rate baseline | `alpha_surv=1.09` 但 coverage=0.712；真实残差无可执行覆盖 |
| [[batches/batch_034/candidates/C005\|C005_b34]] | residualized funda-rate composite | `alpha_surv=1.20` 但 coverage=0.712；合成 residual 仍卡硬闸 |
| [[batches/batch_052/candidates/C001\|C001_b52]] | Sub(CsRank(Std($pe,20)), CsRank(...)) | hard_gate sign_flip + mono_sign_flip；PE level Std 跨 regime 翻号 |
| [[batches/batch_052/candidates/C002\|C002_b52]] | Sub(CsRank(Mean(PE/turnover,20)), CsRank(body_ratio_20)) | ls_t=0.05 + max_corr=0.40@F020；body_ratio_20 RHS 第二次复用退化为共振 |
| [[batches/batch_052/candidates/C003\|C003_b52]] | Sub(CsRank(Std(PB×turnover,60)), CsRank(\|return\|_60)) | hard_gate sign_flip；joint vol of value×liq product 同样 regime-sensitive |
| [[batches/batch_052/candidates/C004\|C004_b52]] | Sub(CsRank(Std(turnover,20)), CsRank(Mean(PB,60))) | **alpha_surv=0.96(整批最干净)** + max_corr=-0.45@F002；F002 anchor cluster reject |
| [[batches/batch_052/candidates/C005\|C005_b52]] | Sub(CsRank(Mean(PS/amount,60)), CsRank(body_ratio_60)) | alpha_surv=0.12 严重 Barra 吞噬 + amount-family 全 cluster |
| [[batches/batch_052/candidates/C006\|C006_b52]] | Sub(CsRank(Std(Mean(PB,5),20)), CsRank(Mean(Std(turnover,5),20))) | hard_gate ic_oos_too_low + IS=+12.18 → OOS=-0.13；compound moment LHS over-fit |

**失败模式系统化**：
- `Mul(A, B)` 交互 → 量纲主导方吞噬 (5 次证伪)
- `Div(A, $amount)` → size×vol 毛代理
- `Div(rate, rate_of_change)` → self-normalization 放大 regime 漂移 (3 次 sign_flip)
- `Sub(CsRank(level_A), CsRank(level_B))` → 非对称 shift
- **有效结构**：`Div(Delta(X), X)` 自归一化 / `Sub(CsRank(rate_A), CsRank(rate_B))` 对称 rank-diff

---

## Related

- 🟢 [[amount_volatility_signal]] `productive` — vol_20d 天花板教训来源，F001 admitted
- 🟡 [[turnover_structural_signal]] `saturated` — "field 换方向 ≠ 维度切换" 教训
- 🔴 [[fundamental_momentum]] `dead` — PE/PB/PS 纯变化率全败，印证 rank-diff 路径更优
- 🟡 [[barra_residual_alpha]] `saturated` — 本方向 DSL 已触顶，Python residual 路径交集
- [[lessons#Structural Constraints]] — 市值代理红线 / 向量化约束

---

## Narrative Log

> [!quote]+ 2026-04-25 · [[batches/batch_052/judge|batch_052]]
> admit=0 · reserve=0 · reject=6。方向第 8 轮探索，T002 rank-diff × value × liquidity 完整投放后宣告 DISPROVEN。三条独立机制揭示：
> - **基本面 second-order moment 跨 regime sign_flip** (C001 PE Std + C003 PB×turnover joint vol 双例)：raw 基本面字段 (PE/PB/PS) 的 higher-moment (Std/Var/joint-vol) 在 rank-diff 几何中天然 regime-sensitive，区别于 PE_rate (lessons.md 已 promote) 死区，是更基础的 raw level second-order 死区
> - **value × liquidity ratio 必 cluster F002 anchor** (C002/C004/C005 三例 max_corr 0.40-0.47)：F002 在本方向是结构性 anchor，任何含 amount/turnover 分母的几何排列都被锁死。"RHS 共振饱和律" 在 saturated 方向进阶为 "factor-anchored cluster"
> - **compound moment LHS over-fit** (C006 ls_t_is=12.18 → ls_t_oos=-0.13 戏剧崩塌)：嵌套 smooth-then-std 与单层 higher-moment (b051 admit C002 单层 Std(gap_ret) 行为完全相反) — 单层是 alpha 源头，嵌套是 over-fit 源头
>
> **CP4 alpha-survival 整批分布最完整**：C005=0.12 严重吞噬 / C002=0.46 borderline / C004=0.96 整批最干净。C004 干净但 cluster F002 reject，第二次复现 b051 升格律 "Barra-clean ≠ library-clean"。
>
> **方向决策**：维持 saturated（不退 dead——本批 3 条新结构教训知识价值已交付）。下次再开本方向需 (a) 完全脱离 amount/turnover 分母的新几何 / (b) Python residual 路径有新工具 / (c) 跨家族 rank-diff 在新 family 兑现后回流。**rank-diff geometry 7 跨家族泛化在 value × liquidity 中断——证明范式不是万能**。

> [!quote]+ 2026-04-23 · [[batches/batch_034/judge|batch_034]]
> admit=0 · reserve=0 · reject=5。方向唯一保留的 Python Barra residual 逃生口完成后仍然零 admit，方向正式转 `saturated`。
> - **5/5 全部死于 coverage < 0.80**，区间仅 0.7055-0.712，说明真正的工程上限已经从“Barra 吞噬”切换为“residual signal 可用性不足”
> - **T001 彻底关闭**：C001/C002 额外出现 sign_flip + 负 decay，证明 turnover-PE rank-diff 离开原始 style 载体后不再稳定
> - **T003/T006 残差真实但不可执行**：C004/C005 的 `alpha_surv` 分别为 1.09 / 1.20，`barra_residual_ic` 也接近 raw IC，但依然被 coverage 硬闸阻断
> - **T007 悖论终结**：C003 继续保留极低库相关，却没能把 batch_009 的“库干净但 PnL 弱”提升为可 admit alpha
>
> **方向决策**：Python residual 已验证完，后续继续在本方向加 batch 只会重复制造 residual shadow reject。下一步转去新方向。

> [!quote]+ 2026-04-19 · [[batches/batch_009/judge|batch_009]]
> admit=0 · reserve=2 (C003, C007) · reject=5。方向第 5 批零 admit。
> - **Self-norm rate × turnover 结构全灭** (C001/C004/C006 三个 Div(rate, rate_of_change) sign_flip + oos_decay collapse)
> - **C005 dom=str_1m breakthrough**：方向 22 候选历史首次 dominant_style=str_1m (alpha_surv=0.883) 但 incr_ic=-0.033 库 reducer → reject
> - **C007 ls_t=-2.43 方向 PnL 最强**，mono=-1.0 完美，但 vol_20d=18.8 暴露 + incr_ic=-0.035 库冲突
> - **C003 cum_dd=-1.54 方向最浅**，incr_ic=+0.019 库增值真实，但 ls_t=0.47
> - 新开 T007（跨基本面 rank-diff）：C003/C007 互补悖论
>
> **下轮唯一出口**：Python Barra residual。若残差版仍零 admit → 方向转 `saturated`，开第 4 方向。

> [!quote]- 2026-04-19 · [[batches/batch_007/judge|batch_007]]
> admit=0 · reserve=3 · reject=2。三项里程碑发现：
> 1. **C005 首个 ls_t>2**：Div(PE_rate, turnover_rate) ls_t=-2.92 + ICIR=-0.284 + 9 年全负零翻转（方向 15 候选首次跨 PnL 显著阈值）
> 2. **"静态正交 ≠ 动态正交" 悖论确立**：style_r²=0.016 极低 + alpha_survival=0.097 极低共存
> 3. **Rank-diff 定量权衡**：alpha_survival 0.28→0.71 (2.5×) 但 raw IC 0.032→0.011 (1/3)
>
> **方向决策**：DSL 空间完全探尽（乘法/除法/合成/秩差/分母工程/两 rate 除法 6 种结构全部触天花板）。R8 Python 逃生口触发条件完成。
>
> **元洞察入 lessons.md 候选**：
> - DSL 空间对 vol_20d 天花板的物理极限
> - "静态正交 ≠ 动态正交" 悖论 — style_r² 不是 Barra-clean 硬判据
> - Barra 吞噬与 raw IC 定量 trade-off (1:2.5)

> [!quote]- 2026-04-19 · [[batches/batch_006/judge|batch_006]]
> admit=0 · reserve=3 · reject=2。三项核心发现：
> 1. **T006 三点通用性确立**（最重要）：PE/PB/PS 自归一化速率在 rank-order 层形态高度一致 (alpha_surv 0.92/0.79/0.72、dom=str_1m)——跨 valuation 普适机制
> 2. **T001 "分母去市值"路径证伪**：C003 诊断 (amount→turnover) 未改善 Barra ceiling (0.30→0.28)
> 3. **C004 极端悖论**：style_r²=0.08 clean + alpha_survival=0.0009 共存——低 style_r² ≠ barra-clean
>
> rank-order 层突破已成，PnL 层需合成 + 正交化工程步骤。

> [!quote]- 2026-04-19 · [[batches/batch_005/judge|batch_005]]
> admit=0 · reserve=1 (C004 PE rate) · reject=4。两项结构性正面发现：
> 1. **C004 突破 Barra 天花板**：Div(Delta($pe,20), $pe) alpha_survival=0.92 + dominant_style=str_1m，方向首次双中 hypothesis 目标
> 2. **C005 positive IC 孤证**：Div($pb, Mean($amount,20)) IC_OOS=+0.032 / mono_oos=+1.0 / cum_dd=-2.17 (全库最浅) / 9 年全正，70% IC 被 vol_20d 吞
>
> **四候选失败模式系统化**：
> - Mul(A,B) = 量纲主导方吞噬
> - Div(A, $amount) = size×vol 毛代理
> - **有效出路**：Div(Delta(X), X) 自归一化 / 分母去市值 (turnover_rate 替代 amount)
>
> **跨方向元教训**（累计 4 batches / 3 directions / 28 候选 / 1 admit）：
> - Barra 天花板物理出口仍是 Python Barra residual
> - 乘法交互 ≠ 维度交互；必用自归一化或秩差结构
> - "方向首批 hypothesis 证伪率"是方向级最高效信号
