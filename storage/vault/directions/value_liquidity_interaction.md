---
direction_tag: value_liquidity_interaction
status: exploring
priority: high
rounds: 3
admits: 0
last_batch: batch_007
last_admits: []
last_goal: 'batch_007 方案 A+B: 合成 3-fundamental rate + 秩差结构，DSL 内验证是否能把 T006 rank-order
  优势转化为 PnL (ls_t>2)。若本批仍零 admit 且 ls_t 无显著改善，方向将在 batch_008 切换到 Python 逃生口 Barra
  residual (R8)。'
last_activity: '2026-04-19T11:16:57Z'
created_batch: batch_005
members: []
merged_into: null
---
# value_liquidity_interaction

## Hypothesis

前两个方向（`amount_volatility_signal` / `turnover_structural_signal`）证实纯流动性-波动率派生量在 Barra 空间里全部撞 `vol_20d` 天花板。脱此出路之一：**引入基本面风格维度**。`$pe_ratio / $pb_ratio / $ps_ratio / $market_cap / $circ_market_cap` 直接对应 `ep_ratio / book_to_price / log_circ_cap` 等基本面 Barra 风格——用它们与流动性特征**交互**，理论上产生跨风格空间的 alpha。

三条经济学线索：

1. **价值陷阱 vs 价值实现**：低 PE/PB 股票在高换手率（放量）下往往是"价值实现" (rerating)；低 PE/PB 股票在低换手率（缩量）下可能是"价值陷阱"（基本面恶化市场已知、无买盘）。交互项 `low_PE × high_turnover` vs `low_PE × low_turnover` 应有方向差异。
2. **小盘流动性溢价**：小市值股票 (low circ_mktcap) 当流动性充足时（高 amount）反映了机构关注，当流动性稀薄时反映了困境。`small_cap × high_liquidity` 做多、`small_cap × low_liquidity` 做空构成反转信号。
3. **基本面-技术面脱钩**：PE 分位数变化快（盈利改善） + amount 变化慢（市场反应滞后）= 潜在价值发现机会。反之则是"已 priced-in"。动量 × 基本面交互。

**结构性约束**（延续前两方向教训）：
- 候选必须引入**至少一个基本面字段** ($pe/pb/ps/mktcap)
- 避免纯流动性派生量（已证伪）
- CP04 alpha_survival < 0.60 一律 reject，dominant_style=vol_20d 也 reject（严守 hypothesis）
- 目标：至少 1 候选 dominant_style ∈ {ep_ratio, book_to_price, log_circ_cap, str_1m}

## Current Focus

batch_005 产出**两个结构性正面发现**：(1) C004 `Div(Delta($pe_ratio, 20), $pe_ratio)` alpha_survival=**0.92** + dominant_style=**str_1m**，方向首次双中 hypothesis 目标（ls_t=-1.22 未达显著 → reserve）；(2) C005 `Div($pb_ratio, Mean($amount, 20))` **positive IC=+0.032** + mono_oos=**+1.0** + cum_dd=**-2.17**（全库最浅），9 年全正——但 Barra 层 70% IC 被 vol_20d 吞。**核心教训**：基本面 × 流动性**乘法**交互 (C001/C002/C003) 全败给量纲主导方；**自归一化变化率** (C004) 和 **分母去市值/去波动率**路径是方向真正出路。下批 batch_006：T003 升级（C004 + amount/turnover 速率）+ C005 分母替换 turnover_rate + 新 T006 (basic × momentum)。

## Threads

### T001: Value × Liquidity 交互 [◉ ACTIVE, DSL 边界已到，Python residual 待启]
**Question**: PE/PB 分位 × turnover 水平的交互是否产生独立于流动性因子的价值 alpha？价值实现 vs 价值陷阱能否在横截面上区分？
**Evidence trail**:
- [[batches/batch_005/candidates/C001|batch_005 C001]]: Mul($pe,Mean(tr,20)) ICIR_OOS=-0.228 alpha_surv=0.26 dom=vol_20d → **reject (乘法失败)**
- [[batches/batch_005/candidates/C005|batch_005 C005]]: Div($pb, Mean(amount,20)) **IC=+0.032 mono=+1.0 cum_dd=-2.17** alpha_surv=0.30 dom=vol_20d → **reject** (positive edge 真实但 vol_20d 吞)
- [[batches/batch_006/candidates/C003|batch_006 C003]]: Div($pb, Mean(tr,20)) **IC=+0.027 mono=+0.3 cum_dd=-2.64** alpha_surv=0.28 vol_20d=**25.2**(5.5× of C005_b5) → **reserve (诊断证据)**
- [[batches/batch_006/candidates/C004|batch_006 C004]]: Div($pe, Mean(tr,20)) ICIR=+0.284 ls_t=+0.20 alpha_surv=**0.0009**(极端悖论) → **reject (极端 dealbreaker)**
- [[batches/batch_007/candidates/C003|batch_007 C003]]: Sub(CsRank($pb), CsRank(Mean(tr,20))) **alpha_surv=0.71**(2.5× 改善) ICIR=+0.107 ls_t=+0.33 dom=vol_20d → **reserve** (秩差诊断)

**Partial Answer**: 乘法结构 (Mul) 全部被量纲主导方吞噬；除法结构 `Div(fundamental, smoothed_liquidity)` 与 vol_20d **天然共存**（非分母代理问题）——C003 诊断实验证伪"分母去市值"路径。但 C005_b5/C003 positive IC 真实存在 + cum_dd<-3%（全库最浅）证明底层 value×illiquidity edge 真实。DSL 出路剩秩差结构或 Python Barra residual。
**Next probes**: `Sub(CsRank($pb), CsRank(Mean($turnover_rate, 20)))` 秩差；Python 逃生口做 Barra residual。

**batch_007 追加**：C003 秩差 `Sub(CsRank($pb), CsRank(Mean($turnover_rate, 20)))` 已跑：alpha_survival 从 0.28 拉到 **0.71**（2.5× 改善），但 raw IC 从 0.032 削到 0.011（1/3），ls_t=0.33 近零。**秩差消 Barra 但大幅削弱 signal 强度**——Barra 吞噬与 raw IC 的定量 trade-off。dom=vol_20d 仍在。→ **reserve**。Python residual 是唯一未探路径。

### T002: Size × Liquidity 反转 [◉ ACTIVE]
**Question**: 小市值 × 高流动性 vs 小市值 × 低流动性 在 A 股中是否构成反转信号？
**Evidence trail**: （批次待跑 — 市值代理红线需谨慎设计）
**Next probes**: 避免直接 $market_cap；改用 log_circ_cap Barra 残差或 tick-level proxies。

### T003: PE 变化率 vs amount 变化率脱钩 [◉ ACTIVE, PARTIAL ANSWERED via C004_b5]
**Question**: 基本面信号更新速率（PE 变化）与技术面反应速率（amount 变化）的差异是否携带价值发现 alpha？
**Evidence trail**:
- [[batches/batch_005/candidates/C004|batch_005 C004]]: Div(Delta($pe,20), $pe) **alpha_surv=0.92 dom=str_1m** ls_t=-1.22 mono=-0.3 → **reserve**
- [[batches/batch_006/candidates/C005|batch_006 C005]]: Mul(Div(Delta($pe,20),$pe), Mean(tr,20)) alpha_surv=**0.29** dom=vol_20d → **reject (乘法第 5 次证伪)**
- [[batches/batch_007/candidates/C004|batch_007 C004]]: Div(Delta($pe,20), Mean($pe,60)) alpha_surv=**0.86** dom=str_1m ls_t=-1.21 → **reserve** (60d-norm 边际)
- [[batches/batch_007/candidates/C005|batch_007 C005]]: Div(PE_rate, turnover_rate) ls_t=**-2.92**(首个>2) ICIR=-0.284 mono=-0.9 alpha_surv=**0.097**(悖论) → **reject**

**Partial Answer**: PE 自归一化变化率**成功跳出流动性风格天花板**（方向首次 dominant=str_1m + alpha_survival 超 0.70）。但 ls_t=-1.22 未达 PnL 显著。升级尝试 (C005_b6) 用 level 乘法被吞 — **rate × level 乘法彻底摧毁 rate 独立性**。
**Next probes**: 秩差 `Sub(CsRank(PE_rate), CsRank(Mean(turnover)))` 或两 rate 除法 `Div(PE_rate, Div(Delta(Mean(tr,10),10), Mean(tr,10)))`；**禁**乘法升级。

**batch_007 追加**：
- C002 `Sub(CsRank(PE_rate), CsRank(Mean(turnover)))` hard_gate fail（sign_flip IS→OOS 反号 + oos_decay=-5.95）— 非对称 rank-diff（rate vs level）IS 信号归零 OOS regime shift。
- C005 `Div(PE_rate, turnover_rate)` **首个 ls_t>2 = -2.92** + ICIR=-0.284 + mono=-0.9 + 9 年全负零翻转（**方向里程碑**），但 alpha_survival=**0.097** 极端 poor（C004_b6 悖论第 2 次复现）→ **reject**。
- 两 rate 除法是 DSL 空间**真正打出 ls_t>2 的结构**，但被 Barra 完全吃掉残差——**"静态正交 ≠ 动态正交"** 几何悖论：因子值 cross-sectional ⊥ Barra-basis (style_r²=0.016)，但 IC 生成的 L/S weights 落在 Barra span 内 (alpha_survival=0.097)。
- T003 DSL 路径事实上封闭；复活需 Python Barra residual。

### T004: PB × 波动率交互 [✗ DISPROVEN batch_005]
**Question**: 低 PB（便宜）× 低波动率是否是"稳定的便宜"（价值），低 PB × 高波动率是否是"不稳定的便宜"（困境）？
**Evidence trail**:
- [[batches/batch_005/candidates/C003|batch_005 C003]]: Mul($pb, Std($close,20)) alpha_surv=**0.083** (史上最差) dom=vol_20d → **reject**

**Disproven**: `Mul(fundamental_ratio, Std(price))` 结构是波动率 proxy 教科书样本——未归一化 Std 量纲主导。Barra vol_20d 吞 92% IC。

### T005: EP × momentum 交互 [✗ DISPROVEN batch_005]
**Question**: 高 E/P（低估） × 正动量是否是 "确认的便宜"？E/P = 1/PE 更稳健（PE 分母可为零）。
**Evidence trail**:
- [[batches/batch_005/candidates/C002|batch_005 C002]]: Mul(Div(1,$pe), Mean(tr,20)) alpha_surv=0.22 dom=turnover_20d → **reject**

**Disproven**: EP×turnover 乘法结构撞 turnover_20d 簇；"便宜+热闹"实测负 alpha 与 hypothesis 反向——A 股语境下高 EP + 高换手更接近散户拥挤。

### T006: Fundamental 自归一化速率 (从 C004_b5 抽象) [✓ ANSWERED batch_006] (rank-order 层)
**Question**: 基本面字段 `Div(Delta(X, n), X)` 的自归一化变化率是否普遍跳出流动性风格天花板？PB / PS 的变化率是否与 PE 的变化率（C004_b5）产生互补信号？
**Evidence trail**:
- [[batches/batch_005/candidates/C004|batch_005 C004]]: Div(Delta($pe,20), $pe) **alpha_surv=0.92** dom=str_1m ls_t=-1.22 → **reserve** (PE rate)
- [[batches/batch_006/candidates/C001|batch_006 C001]]: Div(Delta($pb,20), $pb) **alpha_surv=0.79** dom=str_1m ls_t=-1.49 → **reserve** (PB rate)
- [[batches/batch_006/candidates/C002|batch_006 C002]]: Div(Delta($ps,20), $ps) **alpha_surv=0.72** dom=str_1m ls_t=-1.47 → **reserve** (PS rate)
- [[batches/batch_007/candidates/C001|batch_007 C001]]: Div(Add(Add(PE_rate, PB_rate), PS_rate), 3) **alpha_surv=0.86** dom=str_1m ls_t=-1.27 → **reserve** (3-fundamental 合成)

**Answer**: **三点通用性确立** — PE/PB/PS 自归一化速率形态高度一致（alpha_survival 0.92/0.79/0.72，dom=str_1m，ls_t -1.2 到 -1.5）。"基本面字段自归一化变化率跳出 vol_20d 天花板" 在 rank-order 层是**跨 valuation 指标普适机制**。但 ls_t 全部弱 <2 → L/S PnL 层未兑现。
**batch_007 合成尝试**：
- C001 `Div(Add(Add(PE_rate, PB_rate), PS_rate), 3)` alpha_surv=0.86 dom=str_1m 保持 + 三点通用性再验证，但 ls_t=-1.27 未改善（PE/PB/PS 中位）→ **reserve**。**DSL 等权合成不产生信噪比增益**（Q5 一桨驱动是方向机制层的单边结构）。
- C004 `Div(Delta($pe,20), Mean($pe,60))` 60d-norm 变体 alpha_surv=0.86 dom=str_1m ls_t=-1.21 ≈ C004_b5 → **reserve**。分母工程已触底。
**Next probes**: Python 逃生口做 str_1m 加权 residual 合成（方案 D / R8 trigger）。

## Known Failures

- **C001_b5** `Mul($pe_ratio, Mean($turnover_rate, 20))` — alpha_survival=0.26 dealbreaker + dom=vol_20d；PE 原值乘法结构被量纲主导方（turnover）吞噬
- **C002_b5** `Mul(Div(1, $pe_ratio), Mean($turnover_rate, 20))` — alpha_survival=0.22 dealbreaker + dom=turnover_20d；EP×turnover 反向 hypothesis（负 alpha）
- **C003_b5** `Mul($pb_ratio, Std($close, 20))` — alpha_survival=0.083（史上最差）；未归一化 Std 量纲主导，PB 信号被 vol_20d 吞 92%
- **C005_b5** `Div($pb_ratio, Mean($amount, 20))` — 尽管 IC=+0.032 positive + mono=+1.0 + cum_dd=-2%，但 alpha_survival=0.30 + dom=vol_20d 双触 dealbreaker；**$amount 分母退化为 size×vol 毛代理**，保留为正面 direction narrative 证据
- **C004_b6** `Div($pe_ratio, Mean($turnover_rate, 20))` — alpha_survival=0.0009 极端记录 + ls_t=+0.20；低 style_r² (0.08) + 极低 alpha_survival 悖论 — 因子 IC 完全在 Barra 子空间内运动，"低 style_r² ≠ barra-clean" 教训标本
- **C005_b6** `Mul(Div(Delta($pe_ratio, 20), $pe_ratio), Mean($turnover_rate, 20))` — rate × level 乘法结构彻底摧毁 rate 独立性；alpha_survival 从 C004_b5 的 0.92 崩塌到 0.29；乘法结构第 5 次跨候选证伪
- **C002_b7** `Sub(CsRank(Div(Delta($pe_ratio, 20), $pe_ratio)), CsRank(Mean($turnover_rate, 20)))` — 非对称 rank-diff (rate vs level) hard_gate sign_flip IS→OOS 反号 + oos_decay=-5.95；rank-diff 两侧必须同级量纲
- **C005_b7** `Div(Div(Delta($pe_ratio, 20), $pe_ratio), Div(Delta($turnover_rate, 20), $turnover_rate))` — **首个 ls_t>2 (-2.92) + 9 年全负零翻转 + mono=-0.9 + cum_dd=-19** 但 alpha_survival=**0.097** 极端 poor + style_r²=0.016（C004_b6 悖论第 2 次复现）；"**静态正交 ≠ 动态正交**" — 因子值 ⊥ Barra basis 但 IC weights ∈ span(Barra)

## Related
- [[lessons#Structural Constraints]]  （市值代理红线 / 向量化约束）
- [[amount_volatility_signal]]  （vol_20d 天花板教训）
- [[turnover_structural_signal]]  （"field 换方向 ≠ 维度切换"教训）

## Narrative Log

### 2026-04-19 [[batches/batch_005/judge|batch_005]]
**admit=0 · reserve=1 (C004 PE change rate) · reject=4**。方向 `status: exploring` 保持；priority `high`。

**两项结构性正面发现**（高于前两方向的信息增量）：
1. **C004 突破 Barra 天花板**：`Div(Delta($pe_ratio, 20), $pe_ratio)` alpha_survival=**0.92** + dominant_style=**str_1m** → 方向首次双中 hypothesis 目标。ls_t=-1.22 未达 PnL 显著 → reserve（rank-order 层 hypothesis 成立，交易性待升级）
2. **C005 positive IC 孤证**：`Div($pb_ratio, Mean($amount, 20))` **IC_OOS=+0.032 / mono_oos=+1.0（PERFECT）/ cum_dd=-2.17（全库最浅）/ 9 年全正**。70% IC 被 vol_20d 吞 → 底层 positive edge 真实，被 Barra 遮蔽。

**四候选失败模式系统化** (T004/T005 证伪 + T001 乘法结构证伪)：
- `Mul(A, B)` 交互 = 量纲主导方吞噬信号 (C001/C002/C003)
- `Div(A, $amount)` = size×vol 毛代理，分母退化 (C005)
- **有效出路**: 自归一化变化率 `Div(Delta(X), X)` (C004)、分母去市值（turnover_rate 替代 amount）

**Thread 进展**:
- T001: ACTIVE 乘法结构证伪，除法结构证伪（C005 positive 但 Barra 吞）
- T002: 未跑
- T003: ACTIVE PARTIAL ANSWERED（C004 rank-order 层 hypothesis 成立）
- T004: DISPROVEN batch_005（PB×Std 是波动率 proxy）
- T005: DISPROVEN batch_005（EP×turnover 反向 hypothesis）
- T006: 新增 ACTIVE（从 C004 抽象：基本面字段自归一化速率通用性）

**跨方向元教训**（累计 4 batches / 3 directions / 28 候选 / 1 admit）：
- Barra 天花板的物理出口仍是 Python 逃生口 Barra residual
- 乘法交互 ≠ 维度交互；必用 `Div(Delta(X),X)` 或 `Sub(Rank(A),Rank(B))` 自归一化/秩差结构
- "方向首批 hypothesis 证伪率" 是方向级评估最高效信号

**下轮 (batch_006)**:
1. T003 升级：C004 + amount/turnover 自归一化速率交互
2. T001 修复：C005 分母 $amount → $turnover_rate 去市值
3. T006 新增：$pb 自归一化速率 + $ps 自归一化速率探通用性
4. 保持 ≤ 5 候选，continue hypothesis 精度优先

### 2026-04-19 [[batches/batch_006/judge|batch_006]]
**admit=0 · reserve=3 (C001 PB rate, C002 PS rate, C003 PB/turnover) · reject=2 (C004 极端悖论, C005 乘法失败)**。方向 `status: exploring` 保持；priority high。

**三项 batch 核心发现**：
1. **T006 三点通用性确立**（最重要）：PE/PB/PS 自归一化速率在 rank-order 层形态高度一致（alpha_survival 0.92/0.79/0.72、dom=str_1m、ls_t 弱）。**这是跨 valuation 普适机制**，不是 PE 孤证。
2. **T001 "分母去市值"路径证伪**：C003 诊断实验 (amount→turnover) 未改善 Barra ceiling (0.30→0.28)；positive edge 真实但与 vol_20d 天然共存。
3. **C004 极端悖论**：style_r²=0.08 clean + alpha_survival=0.0009 极端 poor 共存；**低 style_r² ≠ barra-clean**（因子 IC 可完全在 Barra 子空间内运动）。

**累计 5 batches / 3 directions / 33 候选 / 1 admit** — 方向关键转折：rank-order 层突破已成，PnL 层需合成 + 正交化工程步骤。

**Thread 进展**：
- T001: ACTIVE（DSL 出路仅剩秩差/Python residual）
- T003: ACTIVE PARTIAL ANSWERED（乘法升级证伪）
- T006: ANSWERED rank-order 层（PE/PB/PS 三点通用性）

**下轮决策树（batch_007，4 方案）**：
- **方案 A**: T006 合成 — `Div(Add(Add(PE_rate, PB_rate), PS_rate), 3)` 三基本面平均 rate
- **方案 B**: 秩差结构 — `Sub(CsRank(PE_rate), CsRank(Mean(tr)))` 显式放大基本面-流动性差异
- **方案 C**: 高阶 positive signal — C005_b5 / C003 的 `Div(Add($pe,$pb), Mean(tr))` 双字段分子版
- **方案 D（R8 触发）**: Python 逃生口做 C004_b5 + C001 + C002 + C003 合成 Barra residual — 这是方向可兑现的唯一路径

**建议 batch_007 优先 方案 A + 方案 B 各 2-3 候选**（DSL 内可验证合成/秩差是否把 ls_t 推过 2），若失败 batch_008 转 方案 D。

### 2026-04-19 [[batches/batch_007/judge|batch_007]]
**admit=0 · reserve=3 (C001 合成, C003 rank-diff PB, C004 60d-norm) · reject=2 (C002 hard_gate, C005 alpha_survival 极端悖论)**。

**三项里程碑发现**（信息密度最高一批）：
1. **C005 首个 ls_t>2**：`Div(PE_rate, turnover_rate)` ls_t=**-2.92** + ICIR=-0.284 + mono=-0.9 + 9 年全负零翻转。**方向 15 候选首次跨过 PnL 显著阈值**。
2. **"静态正交 ≠ 动态正交"悖论确立**（C004_b6 + C005_b7）：style_r² 极低 (0.016) + alpha_survival 极低 (0.097)。几何含义：因子值 ⊥ Barra basis，但 IC 生成的 L/S weights 落在 Barra span 内。
3. **Rank-diff (C003) 定量权衡**：alpha_survival 0.28→**0.71**（2.5× 改善），但 raw IC 0.032→0.011（1/3 削弱）。**Barra 吞噬消除必须付出 raw signal 削弱的代价**。

**方向决策：DSL 空间完全探尽**。6 种结构化尝试（乘法 / 除法 / 合成 / 秩差 / 分母工程 / 两 rate 除法）全部触天花板。R8 Python 逃生口触发条件完成。

**Thread 进展**：
- T001: ACTIVE（DSL 边界已到，Python residual 待启）
- T003: ACTIVE（首个 ls_t>2 + 悖论；DSL 事实封闭）
- T006: ACTIVE（合成 PnL 天花板，rank-order 层完成）

**下轮决策（batch_008，必须方案 D / R8 触发）**：
1. Python 逃生口实现 `python_factors/value_rate_residual.py`
2. 对 C004_b5 / C001_b7 / C005_b7 做 Barra residual (vol_20d / turnover_20d / str_1m 三风格)
3. 若残差版 ls_t>2 + alpha_survival>0.6 保留 → 方向首个 admit
4. 若残差版 ls_t 仍弱 → 方向 saturated，开辟第 4 方向（如 momentum × fundamental）

**跨方向总览（累计 6 batches / 3 directions / 38 候选 / 1 admit）**：
- amount_volatility_signal: productive, 3 batches, 1 admit (F001), 6 reserve
- turnover_structural_signal: saturated, 1 batch, 1 reserve
- value_liquidity_interaction: exploring, 3 batches, 8 reserve, 里程碑最密集

**Phase 5 consolidation 触发进度**：rounds_since_last=7（<10 阈值）；lessons.md 79 行（<400）；directions 各 <500 行；active ≥ 20 (当前 2，含 value)。**暂不触发 consolidation**；batch_008 后会到 8，仍不触发。

**元洞察入 lessons.md 候选（Phase 5）**：
- "DSL 空间对 vol_20d 天花板物理极限" — 需要物理残差才能推进
- "静态正交 ≠ 动态正交" 悖论 — style_r² 不是 Barra-clean 硬判据
- "Barra 吞噬与 raw IC 定量 trade-off" — rank-diff 以 signal 换 cleanliness 1:2.5
- "方向首批 hypothesis 证伪率"是方向级最高效信号
