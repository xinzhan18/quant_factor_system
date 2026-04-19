---
direction_tag: value_liquidity_interaction
status: exploring
priority: high
rounds: 1
admits: 0
last_batch: batch_005
last_admits: []
last_goal: 'Open third direction value_liquidity_interaction introducing fundamental
  fields ($pe/$pb/$ps) × liquidity ($turnover_rate/$amount/Std-of-close) interactions
  to escape vol_20d/turnover_20d Barra ceiling established in prior 2 directions.
  Goal: at least 1 candidate with dominant_style ∈ {ep_ratio, book_to_price} + alpha_survival
  > 0.70. Test: value×attention (T001/T005), value×stress (T004), fundamental update
  rate (T003), PB/liquidity (T001 variant).'
last_activity: '2026-04-19T05:47:52Z'
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

### T001: Value × Liquidity 交互 [◉ ACTIVE, 乘法结构证伪]
**Question**: PE/PB 分位 × turnover 水平的交互是否产生独立于流动性因子的价值 alpha？价值实现 vs 价值陷阱能否在横截面上区分？
**Evidence trail**:
- [[batches/batch_005/candidates/C001|batch_005 C001]]: Mul($pe,Mean(tr,20)) ICIR_OOS=-0.228 alpha_surv=0.26 dom=vol_20d → **reject (direction dealbreaker)**
- [[batches/batch_005/candidates/C005|batch_005 C005]]: Div($pb, Mean(amount,20)) **IC_OOS=+0.032 mono=+1.0 cum_dd=-2.17 (全库最浅)** alpha_surv=0.30 dom=vol_20d → **reject** (但 positive edge 真实存在被 vol_20d 遮蔽)

**Partial Answer**: 乘法结构 (Mul) 被量纲主导方吞噬；除法结构 (Div by amount) 本质是 size/vol 代理。两种都不跳 Barra 天花板。但 C005 positive IC 证明**底层 value × illiquidity edge 真实存在**。
**Next probes**: C005 分母换 `Mean($turnover_rate, 20)`（去市值）验证残差 edge 是否保留；或 `Div(Rank($pb), Rank(Mean(amount,20)))` 秩差结构。

### T002: Size × Liquidity 反转 [◉ ACTIVE]
**Question**: 小市值 × 高流动性 vs 小市值 × 低流动性 在 A 股中是否构成反转信号？
**Evidence trail**: （批次待跑 — 市值代理红线需谨慎设计）
**Next probes**: 避免直接 $market_cap；改用 log_circ_cap Barra 残差或 tick-level proxies。

### T003: PE 变化率 vs amount 变化率脱钩 [◉ ACTIVE, PARTIAL ANSWERED via C004]
**Question**: 基本面信号更新速率（PE 变化）与技术面反应速率（amount 变化）的差异是否携带价值发现 alpha？
**Evidence trail**:
- [[batches/batch_005/candidates/C004|batch_005 C004]]: Div(Delta($pe,20), $pe) **alpha_surv=0.92 dom=str_1m** ls_t=-1.22 mono=-0.3 → **reserve** (方向首个 rank-order 层 hypothesis 成立)

**Partial Answer**: PE 自归一化变化率**成功跳出流动性风格天花板**（方向首次 dominant=str_1m + alpha_survival 超 0.70）。但 ls_t=-1.22 未达 PnL 显著，rank-order 独立性 ≠ L/S 可交易性。
**Next probes**: `Sub(Div(Delta($pe,20),$pe), Div(Delta(Mean($amount,10),10), Mean($amount,10)))` 补齐 amount 端；延长 horizon（C004 ic 在更长 horizon 更强）。

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

### T006: Fundamental 自归一化速率 (从 C004 抽象) [◉ ACTIVE]
**Question**: 基本面字段 `Div(Delta(X, n), X)` 的自归一化变化率是否普遍跳出流动性风格天花板？PB / PS 的变化率是否与 PE 的变化率（C004）产生互补信号？
**Evidence trail**: （批次待跑 — 从 C004 发现抽象出）
**Next probes**: `Div(Delta($pb_ratio, 20), $pb_ratio)`、`Div(Delta($ps_ratio, 20), $ps_ratio)`。

## Known Failures

- **C001_b5** `Mul($pe_ratio, Mean($turnover_rate, 20))` — alpha_survival=0.26 dealbreaker + dom=vol_20d；PE 原值乘法结构被量纲主导方（turnover）吞噬
- **C002_b5** `Mul(Div(1, $pe_ratio), Mean($turnover_rate, 20))` — alpha_survival=0.22 dealbreaker + dom=turnover_20d；EP×turnover 反向 hypothesis（负 alpha）
- **C003_b5** `Mul($pb_ratio, Std($close, 20))` — alpha_survival=0.083（史上最差）；未归一化 Std 量纲主导，PB 信号被 vol_20d 吞 92%
- **C005_b5** `Div($pb_ratio, Mean($amount, 20))` — 尽管 IC=+0.032 positive + mono=+1.0 + cum_dd=-2%，但 alpha_survival=0.30 + dom=vol_20d 双触 dealbreaker；**$amount 分母退化为 size×vol 毛代理**，保留为正面 direction narrative 证据

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
