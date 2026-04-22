---
direction_tag: amount_volatility_signal
status: productive
priority: high
rounds: 5
admits: 1
last_batch: batch_008
last_admits: []
last_goal: 验证 vol_20d 结构性瓶颈三条逃脱路径：C005 40d horizon 扩展、amount×turnover_rate 跨字段组合、新机制
  amount acceleration
last_activity: '2026-04-19T12:41:09Z'
created_batch: batch_001
members:
- F001
merged_into: null
---
# amount_volatility_signal

> [!abstract]+ 方向概要
> **状态**　🟢 productive · priority=high · rounds=5 · admits=1
> **最近**　[[batches/batch_008/judge|batch_008]] · 2026-04-19 · admit=0 / reserve=4 / reject=2
> **一句话**　$amount 二阶统计量 core edge 已 admit F001；全方向 vol_20d 结构瓶颈 DSL 无解。

---

## Hypothesis

`$amount`（成交额 = price × volume）比原始 `$volume` 更忠实地反映**资金参与强度**——同等 volume 在高价股和低价股上意味着完全不同的资金规模。由此，`$amount` 的**二阶统计量**（波动率、偏度、峰度、尖峰度）编码了"谁在交易、交易得多稳定"的微观结构信息，而非单纯的流动性水平。

三条经济学线索：

1. **资金参与稳定性断层**：机构资金倾向于持续稳定流入（低 CV），散户 / 事件驱动资金则表现为突发异动（高 CV）。短窗口 CV 相对长窗口 CV 的抬升，标记了资金结构的"断层"。
2. **分布尾部的信息含量**：峰度和偏度揭示异常大单的发生频率。右偏+高峰度 = 少数几天的巨额交易主导均值 —— 可能是信息驱动进场，也可能是拉尾盘 / 砸盘的技术性噪声。
3. **方向与资金的一致性**：`$amount` 与 `Delta($close)` 的相关性区分了 trend-confirming（放量跟随）、absorption（放量逆势 = 接盘 / 抛压）、以及 divergence（缩量变盘）三种市场状态。

**Scale-invariance 优先**：候选必须是 `$amount` 的比值 / 形状 / 相关性变换，避免直接用 `$amount` 水平值 —— 后者与 `$market_cap` 强相关，触 lessons.md 的市值代理红线。

---

## Current Focus

**方向级结构瓶颈已锁定（batch_003 第三次确认 + batch_008 第四次确认）**：累计 19/19 非 hard_gate 候选 `dominant_style=vol_20d`，admit 率 5.3% (1/19)，接近 saturated 临界。DSL 实现空间对 vol_20d 脱敏无解——分位数 (C003/C004 batch_003) alpha_survival 0.26/0.57 触 poor dealbreaker；sign-preserved 三分支 (C001/C002/C005 batch_003) 三种实现 mono_flip/弱 ls_t/PnL 坍塌全落；batch_008 三条逃脱路径（40d horizon / amount×turnover 跨字段 / amount momentum）全部失败。**F001 成为不可撼动 anchor**。下一步唯一逃生口：**Python vol_20d Barra residual**——C003 rank 最强（max_corr=0.07@F001）或 C002 (mono=-1.0) 残差版验证独立 alpha。若仍零 admit，方向转 `saturated`。

---

## Threads

### T001: Amount CV 跨窗口比值 + lookback 扫描 [✓ ANSWERED batch_002]

> [!success]+ Thread 结论
> **Question**: $amount 变异系数（CV = Std/Mean）在短 vs 长窗口的比值，能否稳定刻画资金参与"断层"并产生 alpha？断层向上（短 CV > 长 CV）对应 contrarian 还是 momentum？最优窗口是多少？是否存在鲁棒算子替代？
>
> **Evidence trail**:
> - [[batches/batch_001/candidates/C001|batch_001 C001]]　10d CV → ICIR_OOS=-0.716 ls_t=-3.78 mono=-1.0 → **admit → [[factors/F001]]** (amount_cv_10)
> - [[batches/batch_001/candidates/C002|batch_001 C002]]　60d CV → ICIR_OOS=-0.214 ls_t=-0.85 mono_OOS=0.0 → reserve
> - [[batches/batch_001/candidates/C003|batch_001 C003]]　CV10/CV60 ratio → mono_flip IS=0.10→OOS=-1.00 → reject (hard_gate)
> - [[batches/batch_002/candidates/C001|batch_002 C001]]　cv_5 → ICIR_OOS=-0.623 ls_t=-3.58 mono=-1.0 max_corr=0.57@F001 → reserve
> - [[batches/batch_002/candidates/C002|batch_002 C002]]　cv_20 → ICIR_OOS=-0.579 ls_t=-3.43 vol_20d=37.5 alpha_surv=0.649 → reserve
> - [[batches/batch_002/candidates/C003|batch_002 C003]]　MAD/Med_10 → corr=0.967@F001 → reject (hard_gate near_dup)
>
> **Answer**: 短窗口 CV (10d) 单独是 core edge —— admit C001 amount_cv_10（ICIR_OOS=-0.716 / mono_OOS=-1.0 / ls_t=-3.78 / 9 年同号）。**比值构造被证伪**：C003_b1 `CV10/CV60` hard_gate 挂（mono_flip IS=0.10 OOS=-1.00）。**窗口扫描完成 (batch_002)**：5d 信号完整但 rebalance_stress medium + turnover×1.8；20d 全维劣化 + vol_20d 吞噬升级；**10d 是"alpha 强度 × 风格干净度 × 换手成本"三者平衡的全局最优**，F001 的 anchor 地位正式确立。**算子替换封闭**：MAD/Med_10 与 F001 corr=0.967 → 鲁棒算子替换在右偏 $amount 分布上不开辟新子空间。
>
> **Next probes**: T001 已答——进一步窗口扫描 / 算子替换空间封闭；如需复活需走 vol_20d orthogonalize 后的残差版本。

### T002: Amount 分布形状 [◉ ACTIVE] (DSL-bounded)

> [!note]+ Thread 状态
> **Question**: 成交额的偏度、峰度、max/mean 比值是否携带独立于 CV 的尾部信息？高峰度对应的异常大单有前瞻性（contrarian 反转），还是同步性（noise）？
>
> **Evidence trail**:
> - [[batches/batch_001/candidates/C004|batch_001 C004]]　Skew_20 → IC_OOS=-0.003 太弱 + mono_flip → reject (hard_gate)
> - [[batches/batch_001/candidates/C005|batch_001 C005]]　Max/Mean_20 → ICIR_OOS=-0.539 mono=-1.0 vol_20d=32.0 cum_ic_mdd=-73.7 → reserve
> - [[batches/batch_001/candidates/C008|batch_001 C008]]　Kurt_20 → 四重失败（sign+ic+decay+mono）→ reject (hard_gate)
> - [[batches/batch_002/candidates/C004|batch_002 C004]]　Max/Mean_60 → ic_oos=-0.0078 hard_gate, OOS 量级衰至前期 1/5 → reject (延长窗口子路径 DISPROVEN)
> - [[batches/batch_003/candidates/C003|batch_003 C003]]　Q0.85/Mean_20 → ICIR_OOS=-0.460 mono=-0.9 alpha_survival=0.259 → reserve (Q85 robust tail)
> - [[batches/batch_003/candidates/C004|batch_003 C004]]　Q0.95/Mean_20 → ICIR_OOS=-0.543 mono=-1.0 vol_20d=35.3 (方向最高) alpha_survival=0.574 max_corr=0.52@F001 → reserve (Q95 极值尾)
> - [[batches/batch_008/candidates/C003|batch_008 C003]]　Div(Corr($amount,$volume,20),Corr($amount,$volume,60)) mono=-1.0 icir=-0.240 ls_t=-2.21 max_corr=0.07@F001 alpha_surv=0.241 → reserve (CP04 poor, mom_12_1 alpha killer)
> - [[batches/batch_008/candidates/C006|batch_008 C006]]　Skew($amount,20) → ic_oos=-0.0033 hard_gate + mono_sign_flip → reject (hard_gate ic_oos_too_low)
>
> **Partial Answer**: 20d 窗口下高阶矩（skew/kurt）噪声过大不可用；单点 Max/Mean_20 被 vol_20d 吞；Max/Mean_60 regime-dep 熄灭；**分位数实现 (batch_003 C003/C004) 虽数据质量好 (mono=-1.0 / -0.9)，但 alpha_survival 0.26/0.57 双双触 CP04 poor dealbreaker，vol_20d 暴露冲至 28.3/35.3（C004 是方向绝对最高）**——右偏 $amount 分布中高分位数代数上必与 CV (F001) 强相关。**T002 DSL-native 路径实质封闭**，出路仅剩 vol_20d orthogonalize (Python 逃生口) 或新字段组合。
>
> **Next probes**: **Python vol_20d Barra residual 是唯一未被证伪的子路径**——C003（rank-order 最强，mono=-1.0, max_corr=0.07@F001）或 C002（mono=-1.0, incr_ic=-0.024）残差化验证独立 alpha。DSL 空间 6 次证伪已物理封闭。

### T005: Amount × Turnover_rate 跨字段交互 [◉ ACTIVE] 🆕 batch_008

> [!note]+ Thread 状态
> **Question**: `$amount` 的二阶统计量与 `$turnover_rate` 组合能否产生独立于 vol_20d 的新信号？
>
> **Evidence trail**:
> - [[batches/batch_008/candidates/C002|batch_008 C002]]　Div(Std($amount,20),Add(Mean($turnover_rate,20),1e-8)) mono=-1.0 icir=-0.156 style_r²=0.784 → reserve (Barra 高暴露 vol_20d 吞噬)
> - [[batches/batch_008/candidates/C005|batch_008 C005]]　Div(Std($amount,20),Mean($turnover_rate,20)) near-dup C002 style_r²=0.784 max_corr=0.60@F002 → reserve
> - [[batches/batch_008/candidates/C003|batch_008 C003]]　Div(Corr($amount,$volume,20),Corr($amount,$volume,60)) mono=-1.0 alpha_surv=0.24 → reserve (mom_12_1 alpha killer)
>
> **Next probes**: Python vol_20d Barra residual（唯一逃生口）；跨字段 DSL 路径 Barra 脏。

### T003: Amount 与 return 方向一致性（算子实现层） [✗ DISPROVEN batch_001]

> [!failure]+ Thread 结论
> **Question**: Corr($amount, Delta($close)) 和 Slope(Log($amount)) 能否捕捉 absorption / trend-confirming 的市场状态，并在跨期产生 alpha？符号预期：负相关（放量逆势 → 承接信号）→ long absorption pattern；正趋势斜率（资金持续流入）→ momentum。
>
> **Evidence trail**:
> - [[batches/batch_001/candidates/C006|batch_001 C006]]　Corr(amount,Δclose,20) → mono_flip IS=0.60→OOS=-0.70 → reject (hard_gate)
> - [[batches/batch_001/candidates/C007|batch_001 C007]]　Slope(Log(amount),20) → coverage 0.327 + mono_flip → reject (hard_gate)
>
> **Answer (算子层)**: 两个当前 baseline 实现都触结构性失败 —— Corr 分位跨期翻转（regime-dependent），Log-Slope 遇 0 成交额发散（NaN 传播压缩样本到 32.7%）。**hypothesis 本身（资金与价格方向一致性）未被证伪**，但当前 DSL 表达式族失败，需新开 T004 替代实现。

### T004: Amount-return 一致性的 NaN-safe 算子族 [◉ ACTIVE] (DSL-bounded)

> [!note]+ Thread 状态
> **Question**: 在避免 Log 发散 + 分位稳定的前提下，能否用归一化 slope / 幅度 corr / 多窗口 robust 实现捕捉 T003 的经济假设？
>
> **Evidence trail**:
> - [[batches/batch_002/candidates/C005|batch_002 C005]]　Corr(amount, |Δclose|, 20) ic_oos=-0.0037 信号过薄 → reject (hard_gate ic_oos_too_low) (幅度版 Corr 子路径 DISPROVEN)
> - [[batches/batch_003/candidates/C001|batch_003 C001]]　Mean(Sign(Δclose)×amount, 20)/Mean(amount, 20) mono IS=0.70 OOS=-0.40 → reject (hard_gate mono_sign_flip) (Sign×amount 条件均值子路径 DISPROVEN)
> - [[batches/batch_003/candidates/C002|batch_003 C002]]　Slope(Div($amount, Mean($amount,20)), 20) ICIR_OOS=-0.175 ls_t=-1.29 mono_OOS=0.0 → reserve (归一化 Slope 弱)
> - [[batches/batch_003/candidates/C005|batch_003 C005]]　Corr(amount, Sign(Δclose), 20) ICIR_OOS=-0.273 ls_t=0.14 max_corr=0.07@F001 alpha_surv=0.509 → reserve (sign-only Corr PnL 坍塌但机制独立)
> - [[batches/batch_008/candidates/C001|batch_008 C001]]　Corr($amount, Sign(Δclose), 40) mono_sign_flip IS=0.70 OOS=-0.90 → reject (hard_gate mono_sign_flip, 40d horizon 未解决 regime 依赖)
> - [[batches/batch_008/candidates/C004|batch_008 C004]]　Delta(Mean($amount,20),5) icir=-0.256 ls_t=-3.00 mono=-0.10 incr_ic=-0.032 vol_20d=16.20 → reserve (cum_ic_mdd=-73.3, vol_20d 历史最高暴露)
>
> **Partial Answer**: T004 hypothesis 仍成立（C005 max_corr=0.07 证明有非-CV 的独立机制），但 DSL 实现空间**五次撞墙**——幅度-only/条件均值/归一化 Slope/sign-only Corr 20d/40d 五条子路径分别因信号过薄、mono_flip、ls_t 弱、PnL 坍塌、horizon 不解决 regime 依赖全部未能 admit。**T004 DSL-native 实现空间事实上封闭**。
>
> **Next probes**: Python vol_20d Barra residual（同 T002）——C003 sign-only Corr 机制（max_corr=0.07@F001）残差版是最后希望。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_001/candidates/C003\|C003_b1]] | `CV10/CV60 ratio` | mono_sign_flip (IS=0.10 OOS=-1.00)，断层信号不来自比值 |
| [[batches/batch_001/candidates/C004\|C004_b1]] | `Skew($amount, 20)` | 20d 高阶矩噪声过大，IC_OOS=-0.003 + mono 翻转 |
| [[batches/batch_001/candidates/C006\|C006_b1]] | `Corr($amount, Δclose, 20)` | 分位跨期翻号 (IS=0.60 OOS=-0.70)，regime-dependent |
| [[batches/batch_001/candidates/C007\|C007_b1]] | `Slope(Log($amount), 20)` | Log 遇 0 发散，coverage 0.327 + mono 翻转 |
| [[batches/batch_001/candidates/C008\|C008_b1]] | `Kurt($amount, 20)` | 20d 四阶矩四重失败 (sign+ic+decay+mono) |
| [[batches/batch_002/candidates/C003\|C003_b2]] | `MAD/Med($amount, 10)` | corr=0.967@F001，鲁棒算子不开辟新子空间 |
| [[batches/batch_002/candidates/C004\|C004_b2]] | `Max/Mean($amount, 60)` | 60d 尾部 regime-dep，OOS 衰至 1/5，ic_oos=-0.0078 |
| [[batches/batch_002/candidates/C005\|C005_b2]] | `Corr(amount, \|Δclose\|, 20)` | 幅度版去方向化信号过薄，ic_oos=-0.0037 |
| [[batches/batch_003/candidates/C001\|C001_b3]] | `Sign(Δclose)×amount / Mean` | mono_sign_flip (IS=0.70 OOS=-0.40)，条件均值不稳 |
| [[batches/batch_003/candidates/C002\|C002_b3]] | `Slope(amount/Mean, 20)` | 归一化 Slope ls_t=-1.29 弱 + mono_OOS=0.0 |
| [[batches/batch_003/candidates/C003\|C003_b3]] | `Q0.85/Mean($amount, 20)` | alpha_survival=0.259 poor，vol_20d=28.3 |
| [[batches/batch_003/candidates/C004\|C004_b3]] | `Q0.95/Mean($amount, 20)` | vol_20d=35.3 方向最高，max_corr=0.52@F001，"更脏 F001" |
| [[batches/batch_003/candidates/C005\|C005_b3]] | `Corr(amount, Sign(Δclose), 20)` | 机制正交 (max_corr=0.07) 但 ls_t=0.14 PnL 坍塌 |
| [[batches/batch_008/candidates/C001\|C001_b8]] | `Corr(amount, Sign(Δclose), 40)` | 40d horizon mono_sign_flip (IS=0.70 OOS=-0.90) |
| [[batches/batch_008/candidates/C006\|C006_b8]] | `Skew($amount, 20)` 重测 | ic_oos=-0.0033 + mono_sign_flip，高阶矩 6 次证伪 |

---

## Related

- 🟢 [[turnover_structural_signal]] `productive` — batch_003 决策树方案 A 派生新方向，绕开 vol_20d 耦合
- 🔵 [[lessons#Structural Constraints]] — 市值代理红线 / 向量化约束
- 🔵 [[lessons#Data Facts]] — `$amount` 有数据；`$vwap` 全零

---

## Narrative Log

> [!quote]+ 2026-04-19 · [[batches/batch_008/judge|batch_008]]
> **admit=0 · reserve=4 (C002 C003 C004 C005) · reject=2 (C001 C006)**。方向第 4 次确认 vol_20d 结构性瓶颈。
> - **核心发现 1**: 19/19 非 hard_gate 候选 100% dominant_style=vol_20d — 结构性瓶颈不可绕过，DSL 无解
> - **核心发现 2**: 三条逃脱路径全部失败 — horizon 40d (C001 mono_sign_flip) / 跨字段组合 (C002/C005 style_r²=0.78; C003 alpha_surv=0.24) / amount momentum (C004 cum_ic_mdd=-73.3)
> - **核心发现 3**: C003 是本批最大矛盾 — mono=-1.0 / max_corr=0.07@F001 / 9年全负 / 符号一致性=1.0 完美 rank-order + 正交信号，但 CP04 alpha_survival=0.24 触 poor dealbreaker
> - **核心发现 4**: C002 vs C005 near-duplicate — metrics 几乎 identical，incremental_ic 负值，对库无增值
> - **核心发现 5**: 新开 T005 (amount × turnover_rate 跨字段交互) — 同被 Barra 高暴露阻断
> - **Thread 进展**: T001 ANSWERED / T002 ACTIVE but DSL-bounded (第 6 次证伪) / T003 DISPROVEN / T004 ACTIVE but DSL-bounded (第 5 次证伪) / T005 新增 ACTIVE
> - **下轮唯一逃生口**: Python vol_20d Barra residual — C003 (rank 最强) 或 C002 (mono=-1.0) 残差版验证独立 alpha。若仍无独立 alpha，方向 `productive → saturated`。

> [!quote]- 2026-04-19 · [[batches/batch_003/judge|batch_003]]
> **admit=0 · reserve=4 (C002 norm_slope, C003 top-15%, C004 top-5%, C005 sign-only Corr) · reject=1 (C001 hard_gate mono_flip)**。方向累计 18 候选 / 1 admit / 6 reserve / 11 reject（admit 率 5.6%，saturated 临界）。
> - **方向级结构瓶颈第三次确认**：18/18 候选全部 dominant_style=vol_20d — 不是样本偏差，是方向本质
> - DSL 实现空间对 vol_20d 无解：分位数 (C003 0.26 / C004 0.57)、归一化 Slope (C002)、sign-only Corr (C005) 四条子路径 alpha_survival 全部 <0.60 poor；条件均值 (C001) mono_flip hard_gate
> - T002 / T004 hypothesis 仍成立但 DSL 实现空间事实上封闭
> - F001 成为不可撼动 anchor：10d CV 的 "最短窗口 × 最低风格耦合 × 完美单调" 三维组合未被 18 候选中任何一个超越
> - C005 带来唯一正面结构发现：max_corr=0.07@F001 证明方向内仍有非-CV 的独立机制，但 20d Corr DSL 实现 PnL 坍塌——需要 vol_20d residual 或 horizon 拉长重启
> - **Thread 进展**: T001 ANSWERED / T002 ACTIVE but DSL-bounded (分位数路径探尽) / T003 DISPROVEN / T004 ACTIVE but DSL-bounded (四子路径全落)
> - **下轮决策树**（batch_004 三选一）: 方案 A 首选——暂停本方向一轮，开辟新方向 turnover_structural_signal（绕开 vol_20d 耦合）；方案 B——Python 逃生口 vol_20d Barra residual；方案 C——改 horizon 把 C005 sign-only Corr 在 5d/20d 持仓期重测
> - 若方案 A/C 仍零 admit 或方案 B 未执行，方向 `productive → saturated`

> [!quote]- 2026-04-19 · [[batches/batch_002/judge|batch_002]]
> **admit=0 · reserve=2 (C001 cv_5, C002 cv_20) · reject=3 (C003 near_dup, C004 ic_too_low, C005 ic_too_low)**。方向保持 `productive` —— 非 admit 不代表熄火，而是 T001 窗口扫描正式定案。
> - **T001 窗口扫描答案**：10d (F001) 是 CV 机制的全局最优窗口。5d (C001) 信号完整但换手×1.8 + half_life 减半 + rebalance_stress medium；20d (C002) 所有维度劣化 + vol_20d 暴露×1.5。F001 的 anchor 地位经跨窗口统计正式确立
> - **T001 算子空间封闭**：C003 MAD/Med_10 与 F001 相关 0.967 — 鲁棒算子替换在右偏 $amount 分布上不开辟新子空间
> - **T002 延长窗口子路径被证伪**：C004 (Max/Mean_60) OOS 量级衰至前期 1/5，2021+ 新 regime 下尾部信号 regime-dependent 失效。T002 整体 hypothesis 仍 ACTIVE，下一步转向 robust tail 指标
> - **T004 幅度版 Corr 子路径被证伪**：C005 去方向化丢失 T003 方向一致性信息，信号过薄。下一步保留符号的 NaN-safe 实现（归一化 Slope / Sign×amount 条件均值）优先
> - **方向级结构验证加强**：13/13 累计候选全部 dominant_style=vol_20d — vol_20d orthogonalize 不做就无法离开 anchor rule 束缚
> - **Thread 进展**: T001 ANSWERED ✓（窗口扫描 + 算子替换均封闭）/ T002 ACTIVE (60d 延长子路径证伪；robust tail 方向未动) / T003 DISPROVEN (不变) / T004 ACTIVE (幅度-only 子路径证伪；sign-preserved 实现未动)
> - **下一步** batch_003 候选池 ≤5: T004 sign-preserved 实现 / T002 robust tail / vol_20d orthogonalize 尝试（Python 逃生口）

> [!quote]- 2026-04-18 · [[batches/batch_001/judge|batch_001]]
> 首批落锤：**admit=1 (C001 amount_cv_10) · reserve=2 (C002, C005) · reject=5**。方向从 `exploring` 转 `productive`（首次 admit 触发）。
> - T001 短窗口 CV 是 core edge —— C001 完美单调 (-1.0) + 9 年同号 + ICIR_OOS=-0.716；比值（C003）和长基线（C002）都不是 alpha 来源
> - **8/8 候选 dominant_style=vol_20d**（平均暴露 ~17，C005 最高 32.0）—— 方向级结构发现：`$amount` 的多数二阶统计量在 Barra 空间中与 vol_20d 强共线，下轮必做 orthogonalization 验证独立 alpha
> - T002 高阶矩（skew / kurt）20d 窗口噪声大不可用；仅 max/mean 比值保留"信号完整"但被 vol_20d 吞噬
> - T003 当前 baseline 算子族（Log-Slope, Corr-Delta）双双因结构性问题挂掉，但 hypothesis 本身未被证伪，新开 T004 承接替代实现
> - **Thread 进展**: T001 ANSWERED（短 CV 胜 / 长 CV 衰 / 比值伪）/ T002 ACTIVE (max/mean 保留，待 orthogonalize) / T003 DISPROVEN 算子层 (hypothesis 待 T004 重测) / T004 新增 ACTIVE (NaN-safe 归一化 + 幅度 corr 实现)
> - **下一步**（batch_002 候选池）: C005 vol-orthogonalize 版本 / C001 lookback 扫描 (cv_5/cv_20/cv_30) + MAD 变体 / T004 新算子族 (归一化 slope / 幅度 corr) / 批次候选数 ≤ 5 (search_adjusted 已 high，收窄搜索)
