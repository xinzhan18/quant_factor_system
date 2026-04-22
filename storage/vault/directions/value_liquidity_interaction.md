---
direction_tag: value_liquidity_interaction
status: productive
priority: high
rounds: 6
admits: 1
last_batch: batch_009
last_admits: []
last_goal: str_1m 突破验证：self-norm rate + cross-funda rank-diff + amount-rate 交互，6 候选
last_activity: '2026-04-19T13:07:56Z'
created_batch: batch_005
members:
- F002
merged_into: null
---
# value_liquidity_interaction

> [!abstract]+ 方向概要
> **状态**　🟢 productive · priority=high · rounds=6 · admits=1 (F002)
> **最近**　[[batches/batch_009/judge|batch_009]] · 2026-04-19 · admit=0 / reserve=2 / reject=5
> **一句话**　基本面 × 流动性交互：DSL 空间已实质封闭，rank-order 层突破已成 (alpha_survival 0.92 / dom=str_1m)，PnL 层 ls_t 仍未兑现；Python Barra residual 是唯一未走的路径。

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

### T001: Value × Liquidity 交互 [◉ ACTIVE · DSL 已封闭]

> [!note]+ Thread 进展
> **Question**: PE/PB 分位 × turnover 水平的交互是否产生独立于流动性因子的价值 alpha？
> **Evidence trail**:
> - [[batches/batch_005/candidates/C001|C001_b5]] Mul($pe, Mean(tr,20)) alpha_surv=0.26 dom=vol_20d → reject
> - [[batches/batch_005/candidates/C005|C005_b5]] Div($pb, Mean(amount,20)) **IC=+0.032 mono=+1.0 cum_dd=-2.17(全库最浅)** alpha_surv=0.30 → reject (positive edge 真实但被 vol_20d 吞 70%)
> - [[batches/batch_006/candidates/C003|C003_b6]] Div($pb, Mean(tr,20)) 诊断：分母换 tr 未改善 (0.30→0.28) → reserve
> - [[batches/batch_007/candidates/C003|C003_b7]] Sub(CsRank($pb), CsRank(Mean(tr,20))) **alpha_surv=0.71 (2.5× 改善)** 但 raw IC 0.032→0.011 (1/3 削弱) ls_t=0.33 → reserve
>
> **Partial Answer**: 乘法结构全部被量纲主导方吞噬；除法结构 `Div(fundamental, smoothed_liquidity)` 与 vol_20d 天然共存（非分母代理问题，已由 C003_b6 诊断证伪「分母去市值」假说）。秩差结构以 2.5× Barra cleanliness 换 3× raw signal 削弱的定量权衡。positive edge 真实存在但 DSL 路径事实封闭。
> **Next**: Python Barra residual (vol_20d / turnover_20d)。

### T002: Size × Liquidity 反转 [◉ ACTIVE · 未跑]

> [!note]+ Thread 进展
> **Question**: 小市值 × 高流动性 vs 小市值 × 低流动性 在 A 股是否构成反转信号？
> **Evidence trail**: 批次待跑 —— 市值代理红线 ([[lessons#Structural Constraints]]) 需谨慎设计
> **Next**: 避免直接 $market_cap；改用 log_circ_cap Barra 残差或 tick-level proxy

### T003: PE 变化率 vs amount 变化率脱钩 [◉ ACTIVE · DSL 封闭]

> [!note]+ Thread 进展
> **Question**: 基本面更新速率 vs 技术面反应速率的差异是否携带价值发现 alpha？
> **Evidence trail**:
> - [[batches/batch_005/candidates/C004|C004_b5]] Div(Delta($pe,20), $pe) **alpha_surv=0.92 dom=str_1m (方向首次突破天花板)** ls_t=-1.22 → reserve
> - [[batches/batch_006/candidates/C005|C005_b6]] Mul(PE_rate, Mean(tr,20)) alpha_surv=0.92→**0.29 崩塌** → reject (rate×level 乘法摧毁 rate 独立性)
> - [[batches/batch_007/candidates/C004|C004_b7]] Div(Delta($pe,20), Mean($pe,60)) alpha_surv=0.86 ls_t=-1.21 → reserve (60d-norm 边际)
> - [[batches/batch_007/candidates/C005|C005_b7]] Div(PE_rate, turnover_rate) **ls_t=-2.92 首破 2** ICIR=-0.284 mono=-0.9 9年全负 alpha_surv=**0.097 极端悖论** → reject
>
> **Partial Answer**: PE 自归一化变化率**首次跳出 vol_20d 天花板** (dom=str_1m + alpha_surv>0.70)，但 ls_t 全部 <2。两 rate 除法 (C005_b7) 终于跨过 PnL 显著阈值，却被 Barra 完全吃掉残差——确立 **「静态正交 ≠ 动态正交」** 几何悖论（因子值 ⊥ Barra basis style_r²=0.016，但 IC 生成的 L/S weights 落在 Barra span 内 alpha_surv=0.097）。
> **Next**: 禁乘法升级；Python Barra residual。

### T006: Fundamental 自归一化速率 [✓ ANSWERED batch_006 · rank-order 层三点通用性]

> [!success]+ Thread 结论
> **Question**: 基本面字段 `Div(Delta(X,n), X)` 的自归一化变化率是否普遍跳出流动性风格天花板？
> **Evidence trail**:
> - [[batches/batch_005/candidates/C004|C004_b5]] PE rate alpha_surv=**0.92** dom=str_1m ls_t=-1.22 → reserve
> - [[batches/batch_006/candidates/C001|C001_b6]] PB rate alpha_surv=**0.79** dom=str_1m ls_t=-1.49 → reserve
> - [[batches/batch_006/candidates/C002|C002_b6]] PS rate alpha_surv=**0.72** dom=str_1m ls_t=-1.47 → reserve
> - [[batches/batch_007/candidates/C001|C001_b7]] 3-funda 等权合成 alpha_surv=**0.86** ls_t=-1.27 → reserve
>
> **Answer**: **PE/PB/PS 自归一化速率三点通用性确立**——「基本面字段自归一化变化率跳出 vol_20d 天花板」在 rank-order 层是**跨 valuation 指标普适机制**，不是 PE 孤证。但 ls_t 全部 -1.2~-1.5 <2，L/S PnL 层未兑现。DSL 等权合成不产生信噪比增益（合成等权 ≠ 合成加权）。
> **Next**: Python 逃生口做 str_1m 加权 residual 合成（方案 D / R8 trigger）。

### T007: 跨基本面 Rank-Diff [◉ ACTIVE · batch_009 新开]

> [!note]+ Thread 进展
> **Question**: 不同基本面字段 ($pe/$pb/$ps) 之间的 rank 差异是否携带独立于 Barra 的价值发现信号？
> **Evidence trail**:
> - [[batches/batch_009/candidates/C002|C002_b9]] Sub(CsRank($pe), CsRank($pb)) mono_sign_flip → reject (level rank-diff 非对称 shift)
> - [[batches/batch_009/candidates/C003|C003_b9]] Sub(CsRank(PE_rate), CsRank(PB_rate)) 9年全正 cum_dd=-1.54 **incr_ic=+0.019 (库增值真实)** ls_t=0.47 → reserve
> - [[batches/batch_009/candidates/C007|C007_b9]] Sub(CsRank(turnover), CsRank(PE)) **ls_t=-2.43 mono=-1.0 (方向 PnL 最强)** vol_20d=18.8 incr_ic=-0.035 → reserve
>
> **Partial Answer**: 互补悖论——C003 库干净但 PnL 弱 / C007 PnL 最强但库冲突。两 rate 做 rank-diff 优于 level rank-diff (C002 非对称 shift 失败)。
> **Next**: Python Barra residual(C003 或 C007) 验证独立 alpha。

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
