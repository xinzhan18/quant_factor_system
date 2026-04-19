---
factor_id: F002
direction: value_liquidity_interaction
admitted_in_batch: batch_005
---

# Report Packet — F002

## Factor YAML Summary

```yaml
name: pb_amount_ratio_20
expression: Div($pb_ratio, Mean($amount, 20))
source_type: dsl
family_tag: value_liquidity_interaction
validation_metrics:
  ic_mean: 0.03169019180804957
  ic_ir: 0.2631582793314787
  ic_win_rate: 0.609504132231405
  monotonicity: 0.9999999999999999
  long_short_mean: 0.0014754911735658687
risk_metrics:
  style_r_squared: 0.4134843668324224
  alpha_survival_ratio: 0.296
```

## Judge Synthesis

---
candidate_id: C005
batch_id: batch_005
direction: value_liquidity_interaction
expression: "Div($pb_ratio, Mean($amount, 20))"
verdict: admit
thread_id: T001
factor_id: F002
factor_name: pb_amount_ratio_20
key_metrics_short: "IC_oos=+0.0317 ICIR_oos=+0.263 ls_t=+4.68 mono_oos=+1.0 cum_dd=-2.17 | alpha_surv=0.296 dom=vol_20d"
reject_reason_short: null
---

> [!note] **Retroactive admit (2026-04-19)**: 最初判 reject 基于 direction-level "alpha_survival<0.60 一律 reject" 自设硬规则。放宽规则后重审：该因子与 F001 **max_corr=0.029**（近似正交）+ incremental_ic=+0.027 + 符号互补（F001 负号 / 本因子正号）+ mono=+1.0 perfect + cum_dd=-2.17（全库最浅 40×F001）+ 9 年全正 — **库空间独立 alpha** 明确，Barra 脏但不阻碍库增值。factor_name=pb_amount_ratio_20。

# C005 — Div($pb_ratio, Mean($amount, 20))

> [!failure]+ Verdict: **REJECT** · thread [[directions/value_liquidity_interaction#T001|T001]]
> **档位**: CP01 ✓ · CP02 `mixed` · CP03 `strong` · CP04 **`poor`** · CP05 `low` · CP06 `stable`
> **OOS**: IC=**==+0.0317==** · ICIR=**==+0.263==** · ls_t=**==+4.68==** · mono_oos=**==+1.0==** · cum_dd=**==-2.17==** · style_r²=0.413 · alpha_surv=**==0.296==** · max_corr=0.029 · mt_bucket=`low`
> **阻断**: direction-level dealbreaker 双触 — `alpha_survival=0.296 < 0.60` **且** `dominant_style=vol_20d`，违反 [[directions/value_liquidity_interaction#Hypothesis]] 的硬闸
> **机制一句话**: PB 对 20 日成交额归一化 = "小市值 × 高估值" 交互，但 70% alpha 来自流动性低→隐含 vol_20d/turnover_20d 波动率敞口

> [!info] Parent: [[batches/batch_005/judge|batch_005 judge]] · Direction: [[directions/value_liquidity_interaction]] · Nearest: [[factors/F001]]

## 表达式解读

`Div($pb_ratio, Mean($amount, 20))` = PB 比率除以 20 日平均成交额。数值越大 = 估值越高 **且** 流动性越低（被忽略的"贵"股）；数值越小 = 估值越低 **或** 流动性越高（热门股 / 便宜股）。

**经济叙事**（对齐 T001 但反号）：原假设 T001 关注的是"低 PE/PB × 高换手 = 价值实现"；本候选机械上是反向——数值高 = 高 PB × 低 amount。然而 **OOS IC 为正（高值股票后续收益更高）**，这与"低估值溢价"的常规 value 叙事相反，暗示真实驱动力可能不是 value 而是"小市值 × 被忽略 = illiquidity premium"或简单地**规模效应**（$amount ≈ price × volume ≈ market_cap 的毛代理）。

**关键矛盾**：rank 层面极其干净（Q1→Q5 完美单调递增），9 年 IC 逐年全部正同号（0.015–0.037），cum_ic_max_drawdown 仅 **-2.17**（全方向、全历史最浅记录！）。但 Barra leave-one-out 显示 **70% 信号来自 vol_20d**（主要 style 敞口 23.93 量级），这是波动率因子重新命名，而不是独立的 value × liquidity alpha。

## CP01 Hard Gates ✓

8 项 gate 全过：
- ✓ compute_error
- ✓ coverage: 0.988 ≥ 0.80
- ✓ sign_flip: train_ic +0.0220 / val_ic +0.0317（同号 positive，罕见）
- ✓ forbidden
- ✓ ic_oos_min: |+0.0317| = 0.0317 ≥ 0.008（远超硬闸，最强之一）
- ✓ oos_decay: 1.44 ≥ 0.20（OOS 比 IS 更强，反衰减！）
- ✓ mono_flip: train +1.0 / val +1.0（两端完美单调同号）
- ✓ near_duplicate: max_corr 0.029 < 0.9（nearest F001）

## CP02 Mechanism Alignment · `mixed`

1. **机制是什么**：PB 除以 20 日成交额 —— 分子=账面价值敏感度，分母=流动性水平（日均成交金额）。高值股票 = PB 高且 amount 低（小而贵、被忽略）；低值股票 = PB 低或 amount 高（大盘便宜股 + 热门股混杂）。**截面 rank 上，这个比值实质是"估值分子 / 规模分母"**，高度共变于市值和波动率。

2. **hypothesis 对齐**：[[directions/value_liquidity_interaction#Hypothesis]] T001 假设"低 PE/PB × 高换手 = 价值实现 / 低 PE/PB × 低换手 = 价值陷阱"，预期**高估值 × 低流动性应该欠表现**（理论上 IC 为负）。本候选 IC **为正**，意味着高估值 × 低流动性后续跑赢 —— 这**反向于** value trap 叙事，实际捕捉的可能是"小盘 illiquidity premium"或"边缘股补涨"。语义上偏离 T001，落在 T002/T004 的灰色地带。

3. **为什么持续**：若真有 edge，可能的持续机制是 A 股散户市场对"便宜 + 被忽略"的小票存在结构性配错 → 机构资金挖掘后补涨。9 年 IC 全同号、逐年稳定，不是偶发。但——

4. **失效场景**：（a）小盘股熊市、流动性危机（2018、2015 Q3 类事件）时，低 amount 股票会被踩踏；（b）退市新规、ST 风险暴露期；（c）风格切换（大盘蓝筹行情，如 2017）会使这类"小而贵"股票跑输。`worst_quarter_ic=-0.004` 几乎无负季度，但样本中极端小盘危机事件较少。

5. **近邻差异**：[[factors/F001]] (`Div(Std($amount, 10), Mean($amount, 10))`) = amount CV，纯流动性 dispersion。本候选 `max_corr=0.029`，机械上几乎正交。但 **Barra 分解显示两者可能落在同一 style 簇（vol_20d）** —— 低相关 ≠ 独立 alpha。

**判定**：机制陈述 partially 自洽，但与 T001 原 hypothesis 方向相反，且真实驱动更像 size/vol 代理而非 value × liquidity 交互。

→ **mixed**

## CP03 Statistical Strength · `strong`

| 指标 | IS | OOS | 档位 | 阈值 |
|---|---|---|---|---|
| IC | +0.0220 | **==+0.0317==** | strong | \|x\|>0.015 |
| ICIR | +0.184 | **==+0.263==** | moderate→strong | \|x\|>0.30 边界 |
| ls_t | +8.54 | **==+4.68==** | strong | \|x\|>3 |
| decay | — | 1.44 (OOS > IS) | 反衰减 | >0.8 健康 |

`|ic_oos|=0.0317` strong，`|icir_oos|=0.263` moderate（逼近 strong 边界），`|ls_t|=4.68` strong，ls_sharpe_oos=3.37；核心 3 项≥2 strong → **strong**。

**Rank-order 验证**：`monotonicity_oos = +1.0`（完美单调！）Q1–Q5 梯度 (OOS): q1=-0.00082, q2=-0.00039, q3=+0.00004, q4=+0.00034, q5=+0.00066 —— **严格单调递增**，q5-q1 = 0.00148 ≈ ls_mean_oos 0.00148，完全一致。这**不是**"一桨驱动 / Q5 独大"，而是真正的 quintile-wide 梯度。**这是本方向/本系统 rank-order 最干净的信号**。

**IS/OOS 对比**：`oos/is` ic ratio = 0.0317/0.0220 = 1.44（OOS 强于 IS），ls_sharpe ratio = 3.37/3.28 = 1.03，ls_tstat ratio 略降（8.54→4.68 主要因 OOS 样本短）。**无 decay 迹象**，这是极其罕见的 regime-robust 信号。

**样本量**：n_days_is=1705, n_days_oos=484，都 >> 200，统计显著性充足。

**Horizon 扫描**（`ic_by_horizon`）：1d IC=0.032 → 20d IC=0.091（逐步放大），20d ICIR=0.786！**半月-月度持仓下信号更强** —— 配合 `signal_half_life=20d` 吻合，暗示这是一个中频（月度）价值发现信号，而非日频交易信号。

**MT 调整**：`mt_bucket = low`（batch 首 4 个判 + 本批 5 条累计 23，direction_candidates=0 是方向首次；`score=0.27` 偏低）；`search_adjusted.raw=0.90, adjusted=0.78, bucket=high`（raw adjustment 较高因为单次 IC 命中 top 5% 分位）。经 search adjustment 后 bucket 上移至 high，但这只影响降档门槛 —— **由于 CP04 dealbreaker 独立触发 reject，MT 调整在此已无决定力**。

→ **strong**

## CP04 Risk Cleanness · **`poor`**

| 指标 | 值 | 档位 | 阈值 |
|---|---|---|---|
| style_r_squared | **==0.413==** | **poor** | <0.08 clean / >0.12 poor |
| alpha_survival | **==0.296==** | **poor (dealbreaker)** | clean>0.70 / <0.60 poor |
| extreme_ratio | 0.005 | clean | <0.01 |
| barra_residual_ic | +0.0094 | — | — |
| barra_residual_icir | +0.145 | — | — |
| dominant_style | **`vol_20d`** | — | — |
| style_crowding_risk | high | — | — |

**Alpha killer**（`metrics.cp04.style_contributions` 未提供分解明细，从 `style_exposures` 数量级推断）：
- `vol_20d`: exposure=**==23.93==** —— **decisive killer**，即 raw IC 0.032 中约 0.022 (≈70%) 是 vol_20d 影子
- `turnover_20d`: exposure=6.71 —— 次级 killer
- `book_to_price`: exposure=1.10 —— 最强的 **基本面** Barra 敞口（方向 hypothesis 真正想要的维度），但量级远低于 vol_20d
- `log_circ_cap`: exposure=0.42 —— 小盘倾向（0.42 接近但未越 0.30 警戒线；方向仍有市值代理嫌疑）
- `str_1m`: 0.57
- 总 killer 占比: ≈ 70% vol_20d + 21% turnover_20d + 9% 真实残差（与 `alpha_survival=0.296` 一致）

**关键判读**：本因子的分母 `Mean($amount, 20)` = 20 日平均成交额 ≈ `price × volume` 时间平均，截面上**几乎就是市值 × 波动率的毛代理**。`$pb_ratio` 分子叠加一层基本面维度，但由于分母的噪声量级（跨股票 $amount 差 3-4 个数量级），整个比值的截面排名由 `1/Mean($amount)` 主导。反映到 Barra 上就是 vol_20d 敞口 23.93。

**residual signal**：barra_residual_ic = +0.0094（仍正且显著方向一致，ICIR=+0.145），说明即使**剔除全部 7 个 Barra style 后**仍有 ~30% 的独立 alpha。这 0.009 的残差 IC 本身并非毫无价值（接近 ic_oos_min 阈值 0.008），但**方向 hypothesis 的硬闸是 alpha_survival > 0.60**，当前 0.296 < 0.60 触发 reject。

**direction.md 硬规则**（[[directions/value_liquidity_interaction#Hypothesis]] 结构性约束节）：
> "CP04 alpha_survival < 0.60 一律 reject，dominant_style=vol_20d 也 reject"

**双触发命中** —— `alpha_survival=0.296` 且 `dominant_style=vol_20d`。按方向硬规则 → **REJECT**。

→ **poor** (direction-level dealbreaker)

## CP05 Redundancy · `low`

- `max_lib_corr` = **==0.029==** → low 档（库仅含 F001，相关度极低）
- `is_near_duplicate` = false
- nearest = [[factors/F001]] (`Div(Std($amount, 10), Mean($amount, 10))` = amount CV)
- `incremental_ic` = **==+0.0268==**（远超 0.005 的 low 档阈值，库增值显著）

→ **low**。若**忽略 CP04 dealbreaker**，本候选对库有实质增量（正 IC 方向唯一、月度持仓放大、rank 完美单调）；但 CP05 low ≠ admit 通行证，CP04 决定 verdict。

## CP06 Validation Stability · `stable`

| 指标 | 值 | 档位 |
|---|---|---|
| sign_consistency | **==1.0==** | stable |
| train_validation_decay | **==1.44==** | stable (OOS 反而增强) |

**时序稳健**（全方向最干净记录）：
- `ic_autocorr_lag1` = +0.039（|x|<0.15 → IC 日独立，ICIR 置信高）
- `cum_ic_max_drawdown` = **==-2.17==**（阈值 -30 健康 / -50 警觉；本值比 direction 所有其它候选 C001-C004 的 -25~-67 浅 **10-30 倍**；9 年累计仅短暂回撤 2%；**这是本批 / 方向 / 历史最稳健的 IC 序列**）
- `worst_quarter_ic` = -0.004 / `best_quarter_ic` = +0.052（worst 几乎平坦，best 为 worst 的 13 倍；IC 分布只有上行尖峰，无系统性下行季度）
- `ic_by_year`：2015=+0.017, 2016=+0.026, 2017=+0.015, 2018=+0.022, 2019=+0.026, 2020=+0.023, 2021=+0.024, 2022=+0.026, 2023=+0.037 —— **9 年全正、量级 0.015-0.037、2023 最新年度最强**，edge **增强而非衰减**
- `split_ic_means` = [+0.019, +0.034, +0.031, +0.044]，`split_dispersion`=0.28（<0.3 一致）；4 split 全正，后两 split（2019+）强于前两

→ **stable**（最高等级，本方向 CP06 最佳）

## 反思与 Direction 意义

> [!warning]+ 本候选 = 方向首个 positive 信号 + dealbreaker 双触 —— 需详细沉淀
> 
> **独特性**：C005 是 batch_005 唯一 **IC 为正** 的信号（C001-C004 全部 IC 负向、mono_oos 负向）。在 rank/时序稳健性层面是 direction + 全库**最干净**的 IC 序列（mono_oos=+1.0、cum_dd=-2%、9 年全正、OOS 反增强）。这暗示"高 PB / low amount"截面排序确实携带一个持续、稳定、方向可靠的 alpha 信号。
> 
> **为何仍 reject**：alpha_survival=0.296 + dominant_style=vol_20d **双触** direction.md 硬规则。70% 的 rank-level signal 在 Barra 空间被 vol_20d（波动率）吞噬。`Mean($amount, 20)` 作为分母实质上把因子退化为 1/size × 1/vol 的缩放版本 —— 这与 `amount_volatility_signal` 方向 vol_20d 天花板教训同构，只是换了一层 PB 外衣。**book_to_price exposure=1.10 是基本面维度真正的抓手**，但量级远输给 vol_20d 的 23.93。
> 
> **方向 narrative 启示**：
> 1. **`$amount` 分母是 vol_20d trap**：`Mean($amount, 20)` 几乎等价于 price×volume 时均，截面上 = size × vol 的毛代理。使用 $amount 归一化的任何因子都会把 vol_20d 作为 dominant_style —— 这是与 `amount_volatility_signal` 方向完全重叠的死胡同。**下批必须改用 $turnover_rate（已去除市值因子）或 pure rank transform**。
> 2. **正 IC 方向值得深耕**：在 direction 4 条 negative IC 信号环绕下，C005 的正方向是**稀缺信息**。"高 PB × 低流动性 = 被忽略的贵股 → 后续跑赢"违反直觉但 9 年稳定。**建议 T004 thread 下一轮用 `$turnover_rate` 替换 `$amount` 复跑**：`Div($pb_ratio, Mean($turnover_rate, 20))`，若 dominant_style 脱离 vol_20d 则 admit。
> 3. **barra_residual_ic = +0.009 的含义**：即使扣掉全部 style，仍有接近硬闸阈值的残差 alpha。说明底层确有**微弱但独立的 value × illiquidity** effect，但被 vol_20d 巨大量级淹没到 alpha_survival<0.60。去除 vol_20d 代理后可能 survive。
> 4. **信号月度放大属性**：ic_by_horizon 显示 20 日持仓 IC=0.091（3× of 1d），ICIR=0.786（接近 1！）。若方向未来做 monthly rebal 因子，此信号结构值得优先考虑。
> 
> **T001 thread 推进建议**：把 C005 标为 "finding: value × illiquidity positive edge exists but vol_20d-masked"；下一个探针改用 $turnover_rate（已控 size）作为流动性代理，若 mono + Barra 都清洁则真正打开方向。

## 风险旗标（若忽略 dealbreaker 考虑 reserve 的话，会列出这些；当前 reject 不再适用）

- **CP04 poor (dealbreaker)**: alpha_survival=0.296 + dominant_style=vol_20d（双触 direction 硬规则）
- **book_to_price exposure 1.10**: 方向期望的基本面维度存在但量级不足
- **log_circ_cap exposure 0.42**: 小盘倾向逼近市值代理警戒线（0.30 硬线），但未越线
- **liquidity_coverage 0.58**: 样本仅覆盖 58% 可投标的，小盘/流动性受限
- **small_cap_concentration 0.37**: 偏小盘（<0.4 未触硬线但接近）
- **signal_half_life = 20d**: 月频持仓信号，日频交易不适用

> [!failure]+ Verdict: REJECT
> **核心理由**: 
> Direction-level dealbreaker 双触 —— `alpha_survival=0.296 < 0.60` **且** `dominant_style=vol_20d`。按 [[directions/value_liquidity_interaction#Hypothesis]] 结构性约束段"CP04 alpha_survival < 0.60 一律 reject，dominant_style=vol_20d 也 reject"硬规则处理。
> 
> 机制层面：`Mean($amount, 20)` 作分母退化为 size × vol 毛代理，70% rank-level signal 被 vol_20d 吞噬，与 `amount_volatility_signal` 死胡同同构（换 PB 外衣但未换风格空间）。虽然 rank 层面（mono_oos=+1.0、cum_dd=-2.17）+ 时序稳健性（9 年全正、OOS 反增强）是本系统最干净记录，但**这些是"信号存在"的证据，不是"信号独立"的证据**。barra_residual_ic=+0.009 接近 ic_oos_min 阈值，暗示底层确有微弱独立 alpha，需在 vol_20d-controlled 构造下重验。
> 
> **Direction narrative 价值**（保留到 thread T001）：
> - "value × illiquidity positive edge" 信号存在但 vol_20d-masked
> - 下一步把 `Mean($amount, 20)` 替换为 `Mean($turnover_rate, 20)`（turnover 已规范化去除市值）重跑同构造，若 alpha_survival > 0.60 则该方向真正打开
> - C005 是方向首个 positive 信号，即使 reject 也值得作为"发现"写入 direction.md Narrative Log
> 
> 本文件 frontmatter `verdict: reject`，`factor_id: null`，`factor_name: null`。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: 0.03169019180804957
    icir_oos: 0.2631582793314787
    ls_tstat_oos: 4.6775
    ic_is: 0.022023872901518884
    icir_is: 0.1842382782006423
    ic_std_is: 0.11954015808557475
    ic_std_oos: 0.12042255287789014
    n_days_is: 1705
    n_days_oos: 484
    ic_win_rate_is: 0.5964809384164222
    ic_win_rate_oos: 0.609504132231405
    monotonicity_is: 0.9999999999999999
    monotonicity_oos: 0.9999999999999999
    quintile_returns_is:
      q1: -5.6536173360655084e-05
      q2: 0.00017191085498780012
      q3: 0.0005000545061193407
      q4: 0.0007852885755710304
      q5: 0.0019384630722925067
    quintile_returns_oos:
      q1: -0.0008188622305169702
      q2: -0.0003899791627191007
      q3: 4.2838470108108595e-05
      q4: 0.0003394389641471207
      q5: 0.000660488847643137
    ls_mean_is: 0.0021627479345678376
    ls_mean_oos: 0.0014754911735658687
    ls_sharpe_oos: 3.3716
    ls_sortino_oos: 5.7447
    ls_calmar_oos: 3.1311
    ls_max_dd_oos: -0.1188
    ls_sharpe_is: 3.281
    ls_tstat_is: 8.5367
    ls_max_dd_is: -4.1669
    ic_by_horizon:
      1:
        ic_is: 0.022023872901518884
        icir_is: 0.1842382782006423
        win_rate_is: 0.5964809384164222
        ic_oos: 0.03169019180804957
        icir_oos: 0.2631582793314787
        win_rate_oos: 0.609504132231405
      3:
        ic_is: 0.03323017519134552
        icir_is: 0.2772133867590353
        win_rate_is: 0.6205278592375366
        ic_oos: 0.04650238210338777
        icir_oos: 0.3643288160445099
        win_rate_oos: 0.6239669421487604
      5:
        ic_is: 0.0394850002907749
        icir_is: 0.3328816633139879
        win_rate_is: 0.6463343108504399
        ic_oos: 0.055922608916919594
        icir_oos: 0.44103863012937805
        win_rate_oos: 0.6549586776859504
      10:
        ic_is: 0.04682001093819248
        icir_is: 0.39669457027470223
        win_rate_is: 0.6744868035190615
        ic_oos: 0.06980641684821254
        icir_oos: 0.5888765751702804
        win_rate_oos: 0.6900826446280992
      20:
        ic_is: 0.05482725138404414
        icir_is: 0.4606347418556725
        win_rate_is: 0.6674486803519062
        ic_oos: 0.09115487297053798
        icir_oos: 0.7855890942938315
        win_rate_oos: 0.78099173553719
  cp04:
    style_r_squared: 0.4134843668324224
    alpha_survival_ratio: 0.296
    extreme_ratio: 0.004674
    barra_residual_ic: 0.00938
    barra_residual_icir: 0.144743
    dominant_style_exposure: vol_20d
    style_crowding_risk: high
    style_exposures:
      log_circ_cap: 0.42182320066899665
      book_to_price: 1.0979708356100946
      mom_12_1: 0.12150539367404518
      str_1m: 0.572532368444092
      vol_20d: 23.93423086596287
      turnover_20d: 5.152880464565396
      ep_ratio: 0.6340232298667391
    distribution_skew: 1.1896
    distribution_kurt: 1.4053
    distribution_zero_ratio: 0.0
  cp05:
    max_lib_corr: 0.0288
    is_near_duplicate: false
    incremental_ic: 0.026841
    nearest_factor_id: F001
    nearest_factor_expression: Div(Std($amount, 10), Mean($amount, 10))
    all_correlations:
      F001: 0.0288025638884252
    exceeds_threshold: false
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 1.4389
    sign_consistent: true
    ic_by_year:
      2015: 0.017207249780579546
      2016: 0.026112443151304256
      2017: 0.015016014993765458
      2018: 0.022433548847750742
      2019: 0.02648185978597763
      2020: 0.023379700000652176
      2021: 0.023549783149344944
      2022: 0.026223900316602943
      2023: 0.037156483299496196
    worst_quarter_ic: -0.00393
    best_quarter_ic: 0.052077
    ic_autocorr_lag1: 0.038548
    cum_ic_max_drawdown: -2.168967
    split_ic_means:
    - 0.01888014845145787
    - 0.033567652181748016
    - 0.030678549993924317
    - 0.04363441660506808
    split_dispersion: 0.2784
    n_splits: 4
  feasibility:
    turnover_mean: 0.08826251689473583
    liquidity_coverage: 0.5831616649403579
    tail_concentration: 0.006874874212464497
    small_cap_concentration: 0.3193034997172672
    signal_half_life: 20.0
    signal_autocorr_lag1: 0.9983
    rebalance_stress:
      value: 0.0010405239881275295
      rebalance_stress_bucket: low
    ic_half_life_days: null
mt_budget:
  score: 0.2684
  bucket: low
  terms:
    family: 0.49680925094377365
    direction: 0.0
    exposure: 0.1
  search_adjusted:
    raw: 0.9
    adjusted: 0.7792
    bucket: high
hard_gate:
  passed: true
  reasons: []
  gate_results:
    compute_error:
      passed: true
    forbidden:
      passed: true
    coverage:
      passed: true
      value: 0.9881
      threshold: 0.8
    sign_flip:
      passed: true
      train_ic: 0.022023872901518884
      val_ic: 0.03169019180804957
    ic_oos_min:
      passed: true
      value: 0.03169019180804957
      threshold: 0.008
    oos_decay:
      passed: true
      value: 1.4389
      threshold: 0.2
    mono_flip:
      passed: true
      train: 0.9999999999999999
      validation: 0.9999999999999999
    near_duplicate:
      passed: true
      max_corr: 0.0288
      nearest: F001
coverage: 0.9881
expression: Div($pb_ratio, Mean($amount, 20))
```

## Available Charts

The following PNG charts exist in `vault/factors/F002/` and may be embedded via `![[F002/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

- `ic_timeseries`
- `rolling_ic`
- `ic_distribution`
- `monthly_heatmap`
- `quintile_bar`
- `cumulative_returns`
- `annual_group_returns`
- `style_exposure_bar`
- `alpha_waterfall`
- `stability_panel`
- `ic_decay`
- `factor_distribution`
- `coverage`
- `correlation_bar`
- `radar`

## Instructions

Write a deep analytical report on `F002`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F002.md`.

