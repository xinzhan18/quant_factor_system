---
direction_tag: turnover_structural_signal
status: saturated
priority: low
rounds: 1
admits: 0
last_batch: batch_004
last_admits: []
last_goal: 'Open new direction turnover_structural_signal to escape amount_volatility_signal''s
  vol_20d ceiling. Test 5 orthogonal turnover-rate二阶结构 families: persistence (AutoCorr),
  acceleration (short/long ratio), CV (structural analog of F001), signed turnover
  mean (avoiding Qlib Corr+Delta broadcast issue), CS-rank stability. Goal: at least
  1 candidate with max_corr<0.3@F001 + alpha_survival>0.7 + dominant_style≠vol_20d.'
last_activity: '2026-04-19T05:28:19Z'
created_batch: batch_004
members: []
merged_into: null
---
# turnover_structural_signal

## Hypothesis

`$turnover_rate`（换手率 = volume / shares_outstanding）是**自带规模归一化**的流动性强度指标——比 `$amount` 更直接剥离市值影响，同等换手率在大小盘上的经济含义相近。相比 `amount_volatility_signal` 方向锁定在 vol_20d 风格簇，换手率的**二阶结构**（持久性、加速度、方向耦合、排名稳定性）有概率落在不同的 Barra 风格空间（turnover_20d / str_1m / 残差）。

三条经济学线索（避开已证伪的 vol_20d 陷阱）：

1. **换手持久性 vs 阵发性**：高换手持久（AutoCorr 高）= 稳定关注度；阵发性高换手（AutoCorr 低）= 事件驱动。与 `Mean($turnover_rate, 20)` 的水平值不是同一维度——持久性是"状态特征"而非"水平特征"。
2. **换手加速度**：短/长窗口换手比值刻画兴趣度变化速率。与 F001 `amount CV` 捕获"资金稳定性"不同，这里捕获"兴趣方向"（增长或衰减）。
3. **换手-价格方向耦合**：Corr($turnover_rate, Delta($close)) 分离 trend-followed 换手（顺势换手）与 divergence 换手（逆势换手）。在以 sign(Δclose) 为二元条件的设定下，原始 amount 版本 (C006_b1) 因 $amount 的右偏分布产生 mono_flip，换手率是接近对称分布的百分比变量，有机会规避这一陷阱。

**结构性约束**（避免重蹈 amount_volatility_signal 覆辙）：
- 候选必须能从 `$turnover_rate` 派生出**非 Mean**的维度——否则仍撞 turnover_20d 风格天花板
- 优先比值 / 形状 / 相关性 / 持久性算子；避免单纯 Std（易撞 vol_20d）
- CP04 alpha_survival < 0.60 一律 reject，不做 reserve

## Current Focus

**方向 hypothesis 首批即被证伪**：batch_004 5 候选中 5/5 `dominant_style=vol_20d`，核心前提"turnover 能脱离 vol_20d 风格空间"错误——换手、成交额、波动率在 Barra 空间高度共线。仅 T002 加速度 (C003) 突破 alpha_survival>0.60 dealbreaker (1.085) 但 Q5 一桨 + cum_ic_mdd=-73.7 → reserve。方向 `status: exploring → saturated`（已在 Narrative Log 翻态），`priority: high → low`。复活路径：Python 逃生口 Barra residual。

## Threads

### T001: Turnover 持久性 vs 阵发性 [✗ DISPROVEN batch_004]
**Question**: 换手率的序列相关（AutoCorr）是否在横截面上携带独立 alpha？高持久性（机构长期关注）与阵发性（散户事件驱动）对应未来收益的方向是否一致？
**Evidence trail**:
- [[batches/batch_004/candidates/C002|batch_004 C002]]: TsAutoCorr_20 ICIR_OOS=-0.280 ls_t=-2.43 max_corr=0.13@F001 alpha_survival=0.520 vol_20d=25.8 → **reject (soft CP dealbreaker)**

**Disproven**: AutoCorr 数值上独立于 F001（max_corr=0.13 ok），但 Barra 分解后 48% IC 被 vol_20d 吞，持久性维度不独立于波动率维度。

### T002: Turnover 加速度 / 水平分离 [◉ ACTIVE, SOLE SURVIVOR]
**Question**: 短/长窗口换手比值（兴趣度加速度）能否独立于水平值 `Mean(turnover, 20)` 产生 alpha？加速增长是追涨信号还是反转信号？
**Evidence trail**:
- [[batches/batch_004/candidates/C003|batch_004 C003]]: Div(Mean(tr,5), Mean(tr,20)) ICIR_OOS=-0.320 ls_t=-3.08 alpha_survival=**1.085** max_corr=0.27@F001 mono_oos=-0.5 cum_ic_mdd=-73.7 → **reserve**

**Partial Answer**: 加速度比值是方向唯一突破 alpha_survival dealbreaker 的构造（残差 IC 反增强）——"变化率"维度似乎独立于 "水平/波动率" 维度。但 Q5 一桨驱动 + 深期回撤削弱实盘价值，需 vol_20d residual 版本 + Q1-Q4 结构修复才能 admit。

**Next probes**: Python 逃生口做 C003 的 vol_20d Barra residual，验证残差 alpha 是否 style-independent；或改 window 组合 (3/10, 10/60) 看加速度结构的尺度稳定性。

### T003: Turnover CV 对比 F001 [✗ DISPROVEN batch_004]
**Question**: 同构 F001 (amount CV) 换成 turnover CV 是否有独立 alpha？因为 turnover_rate 已内生规模归一化，理论上 CV 应跟 Barra 风格耦合度不同。
**Evidence trail**:
- [[batches/batch_004/candidates/C001|batch_004 C001]]: Div(Std(tr,10), Mean(tr,10)) corr=0.955@F001 → **reject (hard_gate near_dup)**

**Disproven**: A 股 10d 窗口下 turnover CV ≡ amount CV（shares 短窗近常数，相除抵消 price 波动维度）。"换手率自带规模归一"的构造优势在 CV 形式下被相除结构抹掉。

### T004: Turnover-return 方向耦合 [✗ DISPROVEN batch_004]
**Question**: turnover 与 return 的 Corr 是否能规避 amount_volatility_signal T003 失败模式（C006_b1 mono_flip）？turnover 百分比变量的分布对称性可能修复 regime-dependent 分位翻号。
**Evidence trail**:
- [[batches/batch_004/candidates/C004|batch_004 C004]]: Mean(Sign(Δclose)×tr, 20) ICIR_OOS=-0.296 ls_t=-2.98 max_corr=0.12@F001 alpha_survival=**0.446** style_r²=0.421 dom=vol_20d+str_1m+turnover_20d 三簇 → **reject (soft CP dealbreaker)**

**Disproven (partial)**: Mean-of-Signed 版规避了 mono_flip（turnover 对称性生效）但引入 str_1m + turnover_20d 三簇共线，风格暴露 55% 超过 signal 残留。"规避 amount 陷阱 ✓ / 规避 Barra 吞噬 ✗"。

### T005: Turnover rank stability [✗ DISPROVEN batch_004]
**Question**: CS-rank of turnover 在时间序列上的稳定性（Std of rank）是否携带横截面 alpha？排名抖动大的股票是否未来弱？
**Evidence trail**:
- [[batches/batch_004/candidates/C005|batch_004 C005]]: Std(CsRank(tr), 20) ICIR_OOS=-0.238 ls_t=**-0.64** decay=0.46 vol_20d=41.4（方向最高） → **reject (soft CP + unstable)**

**Disproven**: CsRank 嵌套 Std 产出方向最高 vol_20d 暴露（讽刺反向）；IS→OOS decay 0.46 触 unstable；ls_t 近零 PnL 坍塌。横截面归一化 + 时序 Std 组合不独立于波动率维度。

## Known Failures

- **C001_b4** `Div(Std($turnover_rate, 10), Mean($turnover_rate, 10))` — hard_gate near_dup 0.955@F001。A 股 10d 窗口下 turnover CV ≡ amount CV
- **C002_b4** `TsAutoCorr($turnover_rate, 20)` — alpha_survival=0.52 dealbreaker；持久性维度不独立于 vol_20d
- **C004_b4** `Mean(Mul(Sign(Delta($close, 1)), $turnover_rate), 20)` — alpha_survival=0.446 dealbreaker；三簇共线（vol_20d + str_1m + turnover_20d）吞噬 55% IC
- **C005_b4** `Std(CsRank($turnover_rate), 20)` — vol_20d=41.4（方向最高，讽刺反向）+ decay=0.46 unstable + ls_t=-0.64 塌方

## Related
- [[lessons#Structural Constraints]]  （市值代理红线 / 向量化约束）
- [[amount_volatility_signal]]  （方向级 vol_20d 天花板教训）

## Narrative Log

### 2026-04-19 [[batches/batch_004/judge|batch_004]]
**admit=0 · reserve=1 (C003 加速度) · reject=4** — **方向首批即触发 saturated**。status `exploring → saturated`；priority `high → low`。

**核心发现（方向 hypothesis 证伪）**：
1. 5/5 候选 `dominant_style=vol_20d` → "换手率能脱离 vol_20d 风格空间" 前提错误
2. C001 turnover CV 与 F001 amount CV 相关 **0.955**（hard_gate near_dup）→ shares 短窗近常数，CV 构造在 $amount 和 $turnover_rate 上等价
3. T001/T003/T004/T005 四 thread hypothesis 全部证伪
4. 唯一存活 T002 加速度 C003：alpha_survival=1.085（残差 IC 反增强罕见正面信号）但 Q5 一桨 + cum_ic_mdd=-73.7

**元教训（供 consolidation）**：
- "field 换方向"在 Barra 空间里不等于"维度切换"
- Barra basis（vol_20d / turnover_20d / str_1m）覆盖了所有流动性-波动率派生量，脱此天花板必走 Python residual 逃生口
- 方向首批 alpha_survival<0.60 率 > 50% → 应立即触发"方向底层 hypothesis 检讨"

**下轮**：暂停本方向。batch_005 开辟第三方向 `value_liquidity_interaction`（基本面 × 流动性交互），目标引入 ep_ratio / book_to_price / log_circ_cap 风格维度。
