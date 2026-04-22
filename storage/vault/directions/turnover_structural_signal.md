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

> [!abstract]+ 方向概要
> - **状态**　🟡 `saturated` · priority `low` · rounds = 1 · admits = 0
> - **最近**　[[batches/batch_004/judge|batch_004]] · 2026-04-19 · admit=0 / reserve=1 / reject=4
> - **一句话**　换手率二阶结构首批即证伪，5/5 候选撞 vol_20d 风格天花板。

---

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

> [!info]+ 方向饱和说明
> batch_004 5/5 候选 `dominant_style=vol_20d`——核心前提"turnover 能脱离 vol_20d 风格空间"在 Barra 分解下被证伪。换手、成交额、波动率在 Barra 基底上高度共线，DSL 层任何 `$turnover_rate` 派生构造（CV / AutoCorr / signed-mean / rank-std / 加速度比值）都被 vol_20d + turnover_20d + str_1m 三簇吞噬 40%-55% IC。唯一幸存 T002 加速度 C003 突破 alpha_survival=1.085 但 Q5 一桨 + cum_ic_mdd=-73.7 实盘价值削弱，仍只能 reserve。DSL 路径 ROI 已饱和。
>
> **复活条件**　Python 逃生口做 vol_20d Barra residual（把 turnover 派生变量 regress 掉 vol_20d 暴露后取残差）；或引入 intraday / tick-level turnover 微结构字段（日频 DSL 无法表达）。单纯在现有日频 OHLCV+turnover 字段上再试任何 DSL 组合已无 ROI。

---

## Threads

### T001: Turnover 持久性 vs 阵发性 [✗ DISPROVEN batch_004]

> [!failure]+ Thread 结论
> **Question**: 换手率的序列相关（AutoCorr）是否在横截面上携带独立 alpha？高持久性（机构长期关注）与阵发性（散户事件驱动）对应未来收益的方向是否一致？
>
> **Evidence trail**:
> - [[batches/batch_004/candidates/C002|batch_004 C002]]　TsAutoCorr_20 → ICIR_OOS=-0.280 ls_t=-2.43 max_corr=0.13@F001 alpha_survival=0.520 vol_20d=25.8 → **reject (soft CP dealbreaker)**
>
> **Conclusion**: AutoCorr 数值上独立于 F001（max_corr=0.13 ok），但 Barra 分解后 48% IC 被 vol_20d 吞，持久性维度不独立于波动率维度。

### T002: Turnover 加速度 / 水平分离 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 短/长窗口换手比值（兴趣度加速度）能否独立于水平值 `Mean(turnover, 20)` 产生 alpha？加速增长是追涨信号还是反转信号？
>
> **Evidence trail**:
> - [[batches/batch_004/candidates/C003|batch_004 C003]]　Div(Mean(tr,5), Mean(tr,20)) → ICIR_OOS=-0.320 ls_t=-3.08 alpha_survival=**1.085** max_corr=0.27@F001 mono_oos=-0.5 cum_ic_mdd=-73.7 → **reserve**
>
> **Partial Answer**: 加速度比值是方向唯一突破 alpha_survival dealbreaker 的构造（残差 IC 反增强）——"变化率"维度似乎独立于 "水平/波动率" 维度。但 Q5 一桨驱动 + 深期回撤削弱实盘价值，需 vol_20d residual 版本 + Q1-Q4 结构修复才能 admit。SOLE SURVIVOR of the direction.
>
> **Next probes**: Python 逃生口做 C003 的 vol_20d Barra residual，验证残差 alpha 是否 style-independent；或改 window 组合 (3/10, 10/60) 看加速度结构的尺度稳定性。

### T003: Turnover CV 对比 F001 [✗ DISPROVEN batch_004]

> [!failure]+ Thread 结论
> **Question**: 同构 F001 (amount CV) 换成 turnover CV 是否有独立 alpha？因为 turnover_rate 已内生规模归一化，理论上 CV 应跟 Barra 风格耦合度不同。
>
> **Evidence trail**:
> - [[batches/batch_004/candidates/C001|batch_004 C001]]　Div(Std(tr,10), Mean(tr,10)) → corr=0.955@F001 → **reject (hard_gate near_dup)**
>
> **Conclusion**: A 股 10d 窗口下 turnover CV ≡ amount CV（shares 短窗近常数，相除抵消 price 波动维度）。"换手率自带规模归一"的构造优势在 CV 形式下被相除结构抹掉。

### T004: Turnover-return 方向耦合 [✗ DISPROVEN batch_004]

> [!failure]+ Thread 结论
> **Question**: turnover 与 return 的 Corr 是否能规避 amount_volatility_signal T003 失败模式（C006_b1 mono_flip）？turnover 百分比变量的分布对称性可能修复 regime-dependent 分位翻号。
>
> **Evidence trail**:
> - [[batches/batch_004/candidates/C004|batch_004 C004]]　Mean(Sign(Δclose)×tr, 20) → ICIR_OOS=-0.296 ls_t=-2.98 max_corr=0.12@F001 alpha_survival=**0.446** style_r²=0.421 dom=vol_20d+str_1m+turnover_20d 三簇 → **reject (soft CP dealbreaker)**
>
> **Conclusion**: Mean-of-Signed 版规避了 mono_flip（turnover 对称性生效）但引入 str_1m + turnover_20d 三簇共线，风格暴露 55% 超过 signal 残留。"规避 amount 陷阱 ✓ / 规避 Barra 吞噬 ✗"。

### T005: Turnover rank stability [✗ DISPROVEN batch_004]

> [!failure]+ Thread 结论
> **Question**: CS-rank of turnover 在时间序列上的稳定性（Std of rank）是否携带横截面 alpha？排名抖动大的股票是否未来弱？
>
> **Evidence trail**:
> - [[batches/batch_004/candidates/C005|batch_004 C005]]　Std(CsRank(tr), 20) → ICIR_OOS=-0.238 ls_t=**-0.64** decay=0.46 vol_20d=41.4（方向最高） → **reject (soft CP + unstable)**
>
> **Conclusion**: CsRank 嵌套 Std 产出方向最高 vol_20d 暴露（讽刺反向）；IS→OOS decay 0.46 触 unstable；ls_t 近零 PnL 坍塌。横截面归一化 + 时序 Std 组合不独立于波动率维度。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_004/candidates/C001\|C001]] | `Div(Std($turnover_rate,10), Mean($turnover_rate,10))` | `hard_gate` near_dup 0.955@F001（A 股 10d turnover CV ≡ amount CV） |
| [[batches/batch_004/candidates/C002\|C002]] | `TsAutoCorr($turnover_rate, 20)` | `soft_CP` alpha_survival=0.52 dealbreaker（持久性维度不独立于 vol_20d） |
| [[batches/batch_004/candidates/C004\|C004]] | `Mean(Mul(Sign(Delta($close,1)), $turnover_rate), 20)` | `soft_CP` alpha_survival=0.446 dealbreaker（三簇共线 vol_20d+str_1m+turnover_20d 吞 55% IC） |
| [[batches/batch_004/candidates/C005\|C005]] | `Std(CsRank($turnover_rate), 20)` | `soft_CP + unstable` vol_20d=41.4（方向最高）+ decay=0.46 + ls_t=-0.64 塌方 |

---

## Related

- 🟡 [[amount_volatility_signal]] `saturated` — 方向级 vol_20d 天花板教训的上游；本方向尝试"换 field"逃出但同样失败，证实 Barra basis 吞噬是跨 field 现象
- 🟡 [[value_liquidity_interaction]] `saturated` — 同批开辟的替代路径（基本面 × 流动性交互），引入 ep_ratio / log_circ_cap 维度试图脱离纯流动性-波动率 basis
- 🟡 [[barra_residual_alpha]] `saturated` — 本方向 "复活条件" 指向的 Python residual 逃生口方向

---

## Narrative Log

> [!quote]+ 2026-04-19 · [[batches/batch_004/judge|batch_004]]
> **admit=0 / reserve=1 (C003 加速度) / reject=4** — 方向首批即触发 saturated。5/5 候选 `dominant_style=vol_20d`，核心前提"换手率能脱离 vol_20d 风格空间"被 Barra 分解证伪。
> - T001 Turnover 持久性：`[◉ ACTIVE] → [✗ DISPROVEN batch_004]`（AutoCorr 48% IC 被 vol_20d 吞）
> - T002 Turnover 加速度：`[◉ ACTIVE]` 保留（SOLE SURVIVOR，C003 alpha_survival=1.085 但 Q5 一桨 + cum_ic_mdd=-73.7 → reserve）
> - T003 Turnover CV：`[◉ ACTIVE] → [✗ DISPROVEN batch_004]`（C001 corr=0.955@F001，10d 窗口下 turnover CV ≡ amount CV）
> - T004 Turnover-return 耦合：`[◉ ACTIVE] → [✗ DISPROVEN batch_004]`（规避 mono_flip ✓ 但三簇共线 ✗，风格暴露 55%）
> - T005 Turnover rank stability：`[◉ ACTIVE] → [✗ DISPROVEN batch_004]`（vol_20d=41.4 方向最高讽刺反向 + decay=0.46 + ls_t=-0.64 塌方）
> - **核心元教训**：(1) "field 换方向"在 Barra 空间里不等于"维度切换"；(2) Barra basis（vol_20d / turnover_20d / str_1m）覆盖了所有流动性-波动率派生量，脱此天花板必走 Python residual 逃生口；(3) 方向首批 alpha_survival<0.60 率 > 50% → 应立即触发"方向底层 hypothesis 检讨"。
> - **MT budget**　cumulative X→**X+5** · direction 0→**5** · bucket `turnover_structural`
>
> **Operations**　`status: exploring → saturated` · priority `high → low` · 下轮暂停本方向，batch_005 开辟第三方向 `value_liquidity_interaction`
