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
> **状态**　🟡 saturated · priority=low · rounds=9 · admits=1 (F002)
> **最近**　[[batches/batch_052/judge|batch_052]] · 2026-04-25 · admit=0 / reserve=0 / reject=6
> **一句话**　基本面 × 流动性交互：DSL/Python residual/rank-diff geometry 三条路径全部跑完。F002 是结构性 anchor 锁死库余量；rank-diff 范式连胜 6 跨家族在本方向中断；继续探索需要全新几何角度。

---

## Hypothesis

> [!note]+ Hypothesis (rank-order 层已部分验证 · PnL 层未兑现)
> 纯流动性-波动率派生量全部撞 `vol_20d` 天花板。脱困出路：引入**基本面风格维度** ($pe/$pb/$ps + Barra ep/btop/log_circ_cap)，与流动性特征交互。
>
> **三条经济学线索**：(1) 价值陷阱 vs 价值实现：低 PE/PB × 高换手 = rerating；(2) 小盘流动性溢价；(3) 基本面-技术面脱钩：PE 变化快 + amount 变化慢 = 价值发现
>
> **结构性约束**：候选必须含 ≥1 基本面字段；CP04 rubric (放宽)：alpha_survival<0.30 poor / 0.30-0.50 borderline / >0.50 clean；Admit 门槛 `max_corr@F001 < 0.30 且 incremental_ic > 0.010`。

> [!warning]+ ⚠️ 方向级硬约束 (consolidation 2026-04-25 + 2026-05-03 regime/alpha_survival 律)
> Saturated 状态由 8 条独立 finding 跨家族证实——任何 reopen 必须先满足以下：
> 1. **F002 anchor cluster 律**：F002 (Div($pb,Mean($amount,20))) 是结构性 anchor，**任何含 amount/turnover 分母**的几何排列被 ±0.4–0.7 cluster 锁死（b052 C002/C004/C005 三例 max_corr 0.40–0.47）。新候选必须**完全脱离 amount/turnover 分母**。
> 2. **Higher-moment raw fundamental 死区** (F003/F201)：`Std/Var/cumsum($pe/$pb/$ps_ratio, N≥20)` 跨 regime 系统性 sign_flip，5 次 retro-confirm（b052 C001/C003 + b054 C002/C003 + b053 C001 borderline）。**禁止** raw fundamental 二阶矩 LHS。
> 3. **Compound moment LHS over-fit 死区**：嵌套 smooth-then-std (b052 C006 ls_t_is=12.18 → ls_t_oos=-0.13) 与单层 higher-moment (F019/F020) 行为相反——单层是 alpha 源头，嵌套是 over-fit 源头。
> 4. **Barra-clean ≠ library-clean** (F007)：CP04 alpha_survival 高不蕴含 CP05 库独立。b052 C004 alpha_surv=0.96 仍被 F002 cluster reject——admit 必须 alpha_surv > 0.5 **且** max_corr@library < 0.30。
> 5. **Python residual coverage ≈ 0.71 边界** (F008)：b034 5/5 全部死于 coverage 0.706–0.712 < 0.80。residual 路径需先 (a) cross-sectional 算子代替 rolling / (b) loader 端预填充 NaN / (c) Phase 1 freeze validate REQUIRED_FIELDS。
> 6. **Rank-diff geometry 不是万能** (F305)：6 admit 跨 5 family 后在本方向中断。reopen 需"全新非-cluster 几何"或工具链突破。
> 7. **2022-2023 regime sign-flip 律**：本方向 raw fundamental 二阶矩 + value×liq joint vol 在 train→validation 边界系统性翻号，是 F003/F201 升格的核心证据。任何跨 regime 的 fundamental higher-moment LHS 须先做 regime-stratified IC validate。
> 8. **Alpha_survival 单条件不足律**：高 alpha_survival 单独不构成 admit 充分条件——必须与 max_corr@library<0.30 同时成立（b052 C004 alpha_surv=0.96 + cluster reject = 教科书反例）。CP4 与 CP5 解耦验证。

---

## Threads

### T001+T002+T007: Value × Liquidity 交互几何全空间 [✗ DISPROVEN batch_034/batch_052]

> [!failure]+ Thread 合并结论 (Mul/Div/rank-diff/cross-funda 四路径合一)
> **Question**: PE/PB × turnover/amount 在 Mul / Div / Sub-rank / cross-funda rank-diff 任一几何下能否产生独立 alpha？
> **Evidence trail (合并)**:
> - **Mul/Div 路径** [b005-b007]: C001_b5/C002_b5/C005_b5/C003_b6/C003_b7 — 全部 alpha_surv 0.22–0.30 + dom=vol_20d/turnover_20d；rank-diff 包装 (C003_b7) alpha_surv 0.71 但 raw IC 削弱 1/3 + ls_t=0.33
> - **Cross-funda rank-diff** [b009]: C002_b9 level rank-diff mono_sign_flip；C003_b9 9年全正 incr_ic=+0.019 ls_t=0.47；C007_b9 ls_t=-2.43 mono=-1.0 但 vol_20d=18.8 + incr_ic=-0.035
> - **Python residual 路径** [b034]: C001/C002/C003 全部 coverage=0.706–0.712 < 0.80 + sign_flip + decay 负值
> - **Rank-diff geometry** [b052]: C001/C003 hard_gate sign_flip；C002/C004/C005 max_corr 0.40–0.47 @F002 cluster；C006 ls_t_is=12.18→ls_t_oos=-0.13 compound moment 崩塌
>
> **Disproven**: 四路径独立失败，机制可归并为：(a) 量纲主导方吞噬 (Mul) / (b) F002 anchor cluster (Div with amount/turnover) / (c) coverage 硬闸 (residual) / (d) regime sign-flip on raw funda 二阶矩 (rank-diff)。已升格 F305 "rank-diff 不是万能" + F002 anchor cluster 律。

### T003+T006: PE/PB/PS 自归一化速率 [○ ANSWERED rank-order / ✗ PnL 层关闭]

> [!success]+ Thread 合并结论 (PE/PB/PS rate 三点通用性 + composite + residual)
> **Question**: `Div(Delta(X,n), X)` 在 PE/PB/PS 上是否普遍跳出 vol_20d 天花板？合成与 residual 是否兑现 PnL？
> **Evidence trail (合并)**:
> - **三点通用性** [b005-b006]: C004_b5 PE rate alpha_surv=0.92 dom=str_1m / C001_b6 PB rate 0.79 / C002_b6 PS rate 0.72 — 全 reserve, ls_t -1.2 ~ -1.5
> - **合成** [b007]: C001_b7 3-funda 等权 alpha_surv=0.86 ls_t=-1.27；C004_b7 60d-norm alpha_surv=0.86；C005_b7 PE_rate/turnover **ls_t=-2.92 首破 2** 但 alpha_surv=0.097 极端悖论
> - **Self-norm rate × turnover** [b009]: C001/C004/C006 三例 Div(rate, rate_of_change) sign_flip + oos_decay collapse (-16.9 / -32.5)
> - **Residual** [b034]: C004 PE residual baseline alpha_surv=1.09 / C005 composite alpha_surv=1.20，但 coverage=0.712 全 reject
>
> **Answer (rank-order)**：PE/PB/PS 自归一化速率跨 valuation 普适机制确立，dom=str_1m 一致。
> **Closed (PnL)**：ls_t 全 -1.2~-1.5 < 2；DSL 等权合成不产生信噪比增益；residual composite 被 coverage 0.71 卡死。已升格 F008 (coverage 边界) + lessons.md PE_rate 死区。

### T004: PB × 波动率交互 [✗ DISPROVEN batch_005]

> [!failure]+ `Mul($pb, Std($close,20))` alpha_surv=0.083 (史上最差) + dom=vol_20d。`Mul(fundamental, Std(price))` 是教科书波动率 proxy——未归一化 Std 量纲主导，Barra vol_20d 吞 92% IC。

### T005: EP × momentum 交互 [✗ DISPROVEN batch_005]

> [!failure]+ `Mul(Div(1,$pe), Mean(tr,20))` alpha_surv=0.22 dom=turnover_20d。"便宜+热闹" 在 A 股语境下与 hypothesis 反向——更接近散户拥挤而非价值实现。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_005/candidates/C001\|C001_b5]] | Mul($pe, Mean(tr,20)) | alpha_surv=0.26 + dom=vol_20d |
| [[batches/batch_005/candidates/C002\|C002_b5]] | Mul(1/$pe, Mean(tr,20)) | alpha_surv=0.22；EP×turnover 反向 hypothesis |
| [[batches/batch_005/candidates/C003\|C003_b5]] | Mul($pb, Std($close,20)) | alpha_surv=0.083 (史上最差) |
| [[batches/batch_005/candidates/C005\|C005_b5]] | Div($pb, Mean($amount,20)) | IC=+0.032 mono=+1.0 但 alpha_surv=0.30 dom=vol_20d |
| [[batches/batch_006/candidates/C004\|C004_b6]] | Div($pe, Mean(tr,20)) | alpha_surv=0.0009 极端记录 (低 style_r² ≠ barra-clean) |
| [[batches/batch_006/candidates/C005\|C005_b6]] | Mul(PE_rate, Mean(tr,20)) | rate×level 摧毁 rate 独立性；alpha_surv 0.92→0.29 |
| [[batches/batch_007/candidates/C002\|C002_b7]] | Sub(CsRank(PE_rate), CsRank(Mean(tr,20))) | sign_flip + oos_decay=-5.95 |
| [[batches/batch_007/candidates/C005\|C005_b7]] | Div(PE_rate, turnover_rate) | ls_t=-2.92 但 alpha_surv=0.097 静态≠动态正交悖论 |
| [[batches/batch_009/candidates/C001\|C001_b9]] | PE_rate / Mean(PE_rate,60) | sign_flip；self-norm 放大 regime 漂移 |
| [[batches/batch_009/candidates/C002\|C002_b9]] | Sub(CsRank($pe), CsRank($pb)) | mono_sign_flip IS=-0.60 OOS=0.90 |
| [[batches/batch_009/candidates/C004\|C004_b9]] | PE_rate / turnover_rate_of_change | sign_flip + oos_decay=-16.9 |
| [[batches/batch_009/candidates/C005\|C005_b9]] | (PE_rate + PB_rate)/2 | dom=str_1m alpha_surv=0.883 但 incr_ic=-0.033 库 reducer |
| [[batches/batch_009/candidates/C006\|C006_b9]] | PB_rate / turnover_rate_of_change | sign_flip + oos_decay=-32.5 |
| [[batches/batch_034/candidates/C001-C005\|b34_all]] | residual probes (turnover-EP / PE / cross-funda / composite) | 5/5 coverage=0.706-0.712 < 0.80 + sign_flip + 负 decay |
| [[batches/batch_052/candidates/C001\|C001_b52]] | Sub(CsRank(Std($pe,20)), ...) | hard_gate sign_flip；PE level Std 跨 regime 翻号 |
| [[batches/batch_052/candidates/C002\|C002_b52]] | Sub(CsRank(Mean(PE/turnover,20)), CsRank(body_ratio_20)) | ls_t=0.05 + max_corr=0.40@F020 |
| [[batches/batch_052/candidates/C003\|C003_b52]] | Sub(CsRank(Std(PB×turnover,60)), CsRank(\|return\|_60)) | hard_gate sign_flip；joint vol regime-sensitive |
| [[batches/batch_052/candidates/C004\|C004_b52]] | Sub(CsRank(Std(turnover,20)), CsRank(Mean(PB,60))) | alpha_surv=0.96 (整批最干净) + max_corr=-0.45@F002 cluster |
| [[batches/batch_052/candidates/C005\|C005_b52]] | Sub(CsRank(Mean(PS/amount,60)), CsRank(body_ratio_60)) | alpha_surv=0.12 + amount cluster |
| [[batches/batch_052/candidates/C006\|C006_b52]] | Sub(CsRank(Std(Mean(PB,5),20)), CsRank(Mean(Std(turnover,5),20))) | IS=+12.18 → OOS=-0.13；compound moment over-fit |

**失败模式系统化**：
- `Mul(A, B)` → 量纲主导方吞噬 (5 次证伪)
- `Div(A, $amount/turnover)` → F002 anchor cluster
- `Div(rate, rate_of_change)` → self-norm 放大 regime 漂移 (3 次 sign_flip)
- `Sub(CsRank(level_A), CsRank(level_B))` → 非对称 shift
- `Std/Var($pe/$pb/$ps_ratio, N≥20)` → regime sign_flip (F003/F201)
- 嵌套 compound moment (smooth-then-std) → IS over-fit
- **有效结构**：`Div(Delta(X), X)` 自归一化 (rank-order 层 only，PnL 未兑现)

---

## Related

- 🟢 [[amount_volatility_signal]] `productive` — vol_20d 天花板教训来源
- 🟡 [[turnover_structural_signal]] `saturated` — "field 换方向 ≠ 维度切换"
- 🔴 [[fundamental_momentum]] `dead` — PE/PB/PS 纯变化率全败
- 🟡 [[barra_residual_alpha]] `saturated` — coverage 0.71 边界共享 (F008)
- 🟡 [[intraday_price_formation]] `saturated` — anchor cluster 律姊妹方向 (F002/F305)
- [[lessons#Structural Constraints]] — 市值代理 / rank-diff 7 律 / regime sign-flip pre-block / alpha_survival 单条件不足律

---

## Narrative Log

> [!quote]+ 2026-04-25 · [[batches/batch_052/judge|batch_052]] (rank-diff 终曲)
> admit=0 · reject=6。T002 rank-diff × value × liquidity 完整投放后 DISPROVEN。三条独立机制：
> - **基本面 second-order moment 跨 regime sign_flip** (C001 PE Std + C003 PB×turnover joint vol)：raw 基本面字段 higher-moment 在 rank-diff 几何中天然 regime-sensitive (→ F003/F201)
> - **value × liquidity ratio 必 cluster F002** (C002/C004/C005 max_corr 0.40-0.47)：anchor 律 (→ F002/F305)
> - **compound moment LHS over-fit** (C006 ls_t_is=12.18 → ls_t_oos=-0.13)：嵌套 smooth-then-std 与单层行为相反
>
> **CP4 alpha-survival 分布**：C005=0.12 / C002=0.46 / C004=0.96。C004 最干净仍 cluster reject——第二次复现 "Barra-clean ≠ library-clean" + alpha_survival 单条件不足律 (→ F007)。**rank-diff geometry 7 跨家族泛化在 value × liquidity 中断**。维持 saturated。

> [!quote]+ 2026-04-23 · [[batches/batch_034/judge|batch_034]] (Python residual 终曲)
> admit=0 · reject=5。Barra residual 逃生口完成后零 admit。**5/5 全部死于 coverage 0.706-0.712 < 0.80** (→ F008)。T001 彻底关闭；T003/T006 残差 alpha_surv 1.09/1.20 真实但 coverage 阻断；T007 cross-funda residual max_corr=0.027 库干净但 PnL 弱。Python residual 路径在本方向工程上限确认，方向转 saturated。

> [!quote]- 2026-04-19 · b005-b009 早期演化 (DSL 6 路径触顶 → Python residual 触发)
> b005-b007: 乘法/除法/合成/秩差/分母工程/两 rate 除法 6 种 DSL 结构全部触 vol_20d/turnover_20d 天花板。亮点：**C004_b5 PE rate** alpha_surv=0.92 dom=str_1m 方向首次双中 hypothesis；**C005_b7 PE_rate/turnover** ls_t=-2.92 首破 2 但 alpha_surv=0.097 静态≠动态正交悖论；rank-diff 定量权衡 alpha_surv 0.28→0.71 (2.5×) 但 raw IC 削弱 1/3。b009: self-norm rate × turnover 全灭 (sign_flip + oos_decay collapse)；C005 dom=str_1m 历史首次但 incr_ic=-0.033。R8 Python 逃生口触发条件完成 → b034。

> [!quote]- 跨方向元教训累计 (4 batches / 3 directions / 28 候选 / 1 admit)
> Barra 天花板物理出口仍是 Python Barra residual；乘法交互 ≠ 维度交互，必用自归一化或秩差结构；"方向首批 hypothesis 证伪率"是方向级最高效信号；"静态正交 ≠ 动态正交" 悖论 — style_r² 不是 Barra-clean 硬判据；Barra 吞噬与 raw IC 定量 trade-off (1:2.5)。
