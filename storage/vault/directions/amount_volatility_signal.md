---
direction_tag: amount_volatility_signal
status: saturated
priority: low
rounds: 6
admits: 1
last_batch: batch_033
last_admits: []
last_goal: 测试 amount_volatility_signal 的唯一 Python 逃生口：对历史 reserve 候选做 signal-level
  residualization，重点验证 C003_b8/C005_b3/C004_b8/C002_b3 在去除 vol_20d 或关键 killer style
  后，能否把强 rank-order 从 DSL reserve 提升为可 admit 的独立 alpha。
last_activity: '2026-04-23T15:31:53Z'
created_batch: batch_001
members:
- F001
merged_into: null
---
# amount_volatility_signal

> [!abstract]+ 方向概要
> **状态**　⚪ saturated · priority=low · rounds=6 · admits=1
> **最近**　[[batches/batch_033/judge|batch_033]] · 2026-04-23 · admit=0 / reserve=0 / reject=5
> **一句话**　F001 仍是唯一 anchor；Python residualization 也只留下低 coverage 的统计影子，方向在当前日频 `$amount` 空间已收束。

---

## Hypothesis

> [!info]+ Hypothesis — exploring bounded by vol_20d
> `$amount`（成交额 = price × volume）比原始 `$volume` 更忠实地反映**资金参与强度**——同等 volume 在高价股和低价股上意味着完全不同的资金规模。由此，`$amount` 的**二阶统计量**（波动率、偏度、峰度、尖峰度）编码了"谁在交易、交易得多稳定"的微观结构信息，而非单纯的流动性水平。
>
> **三条经济学线索**
> 1. **资金参与稳定性断层**：机构资金倾向于持续稳定流入（低 CV），散户 / 事件驱动资金则表现为突发异动（高 CV）。短窗口 CV 相对长窗口 CV 的抬升，标记了资金结构的"断层"。
> 2. **分布尾部的信息含量**：峰度和偏度揭示异常大单的发生频率。右偏 + 高峰度 = 少数几天的巨额交易主导均值 —— 可能是信息驱动进场，也可能是拉尾盘 / 砸盘的技术性噪声。
> 3. **方向与资金的一致性**：`$amount` 与 `Delta($close)` 的相关性区分了 trend-confirming（放量跟随）、absorption（放量逆势 = 接盘 / 抛压）、divergence（缩量变盘）三种市场状态。
>
> **Scale-invariance 优先**：候选必须是 `$amount` 的比值 / 形状 / 相关性变换，避免直接用 `$amount` 水平值 —— 后者与 `$market_cap` 强相关，触 lessons.md 市值代理红线。

> [!warning]+ Hypothesis ⚠️ — 跨方向 vol_20d 吸收律 (升格自 F001 / F301)
> 本方向 19/19 候选 `dominant_style=vol_20d` 是 **csi1000 daily-bar magnitude/2nd-moment 几何整体被 vol_20d rank 占据**这一系统性规律的源头数据点，已在 ≥8 个独立方向（return_distribution_signals / vol_shock_signals / stochastic_position / range_structure / quantile_shape_signals / intraday_price_formation / turnover_structural_signal + 本方向）独立证伪。**经济线索 1/2 在 DSL 空间被结构性吞噬**：CV / 高阶矩 / 分位数 / 比值 / 鲁棒算子全部 monotone-equivalent 到 vol_20d。**经济线索 3 在 Python residual 通道又被 F008 coverage≈0.71 律封死**——residualization 数学上可剥离 vol_20d 但样本可用性不足以入库。**逃离路径只有四条**（来自 F001）：(a) Python Barra residual（受 F008 限制）；(b) 非 daily-bar 数据（minute / tick）；(c) 非 magnitude 几何——sign 聚合 / cross-family rank-diff；(d) overnight 段独立分解。

---

## Current Focus

**方向已收束为 saturated**：batch_033 把唯一剩余的 Python `vol_20d` residualization 逃生口完整跑完，5/5 全部 hard-gate reject，共同死因 `coverage < 0.80`（系 F008 跨方向数据契约边界，非信号设计问题）。**F001 是唯一可沉淀的 anchor**；本方向在当前日频数据空间不再追加 batch。复活前置条件：minute/tick 数据接入 **或** F008 coverage gate 修复路径（cross-sectional 算子代替 rolling residual / loader NaN 预填充）。

---

## Threads

### T001: Amount CV 跨窗口比值 + lookback 扫描 [✓ ANSWERED batch_002]

> [!success]+ Thread 结论
> **Question**: $amount CV 在短 vs 长窗口的比值能否稳定刻画资金"断层"并产生 alpha？最优窗口？鲁棒算子是否开辟新子空间？
>
> **Answer**: 10d CV 是 "alpha 强度 × 风格干净度 × 换手成本" 三维全局最优 —— **F001 anchor**（[[batches/batch_001/candidates/C001|C001_b1]] ICIR_OOS=-0.716, mono=-1.0）。**比值构造证伪**（C003_b1 mono_flip IS=0.10→OOS=-1.00）；**窗口扫描封闭**（5d 换手×1.8 / 20d vol_20d=37.5 全维劣化）；**鲁棒算子空间封闭**（MAD/Med_10 corr=0.967@F001）。复活唯一路径 = vol_20d orthogonalize 后的残差版本（→ T004 承接 → DISPROVEN）。

### T002: Amount 分布形状（tail / high-order moment） [✗ DISPROVEN batch_008] (DSL-bounded, 6 次证伪)

> [!failure]+ Thread 结论
> **Question**: 偏度、峰度、max/mean、高分位数 / mean 是否携带独立于 CV 的尾部信息？
>
> **Answer**: 20d 高阶矩信噪比结构性过低（Skew / Kurt 两次证伪 b001+b008，IC_OOS≈-0.003 + mono_flip）；Max/Mean 延长到 60d regime-dep 熄灭；分位数 mono 极好（-1.0/-0.9）但 alpha_survival 0.26/0.57 触 CP04 poor，且 vol_20d 暴露冲至方向最高（C004_b3 vol_20d=35.3）——**右偏 $amount 分布中高分位数代数上必与 CV (F001) 强相关**。**T002 DSL-native 实现空间封闭**；与 Hypothesis ⚠️ vol_20d 吸收律一致。

### T003+T004: Amount 与 return 方向一致性（algo+NaN-safe） [✗ DISPROVEN batch_033] (DSL → Python residualized, 10 次证伪)

> [!failure]+ Thread 结论
> **Question**: `Corr($amount, Δclose)` / `Slope(Log($amount))` / 归一化 slope / 幅度 corr / sign-preserved 实现能否捕捉 absorption / trend-confirming 状态？
>
> **DSL 阶段死因**: Log 发散（C007_b1 coverage=0.327）、mono_flip regime-dep（C006_b1 / C001_b3 / C001_b8 40d horizon）、去方向化过薄（C005_b2 ic_oos=-0.0037）、PnL 坍塌（C005_b3 max_corr=0.07@F001 但 ls_t=0.14）。
>
> **Python residual 阶段死因 (batch_033)**: C003 `Corr(amount,Sign(Δclose),20)` 残差化后 ic_oos=-0.0157 / decay=1.17 信号健康，但 coverage=0.697 < 0.80 hard_gate；C005 `Slope(amount/Mean,20)` 残差化后 ic_oos=-0.0244 / decay=0.88，coverage=0.685；C004 `Delta(Mean(amount,20),5)` 残差化 coverage=0.711。
>
> **Answer**: T004 经济假设并非完全错误——residualization 修掉了 vol_20d 吞噬，C003/C005 仍有真实 rank-order；但**唯一逃生口被 F008 跨方向 coverage≈0.71 数据契约边界堵死**，无可执行载体。DSL-native 与 Python residual 双通道封闭。

### T005: Amount × Turnover_rate 跨字段交互 [✗ DISPROVEN batch_033] (DSL-bounded → Python residualized)

> [!failure]+ Thread 结论
> **Question**: $amount 二阶统计量与 $turnover_rate 组合能否产生独立于 vol_20d 的新信号？
>
> **Answer**: DSL 阶段被 vol_20d 吞噬（C002_b8 / C005_b8 style_r²=0.78；C003_b8 mono=-1.0 / max_corr=0.07@F001 但 alpha_surv=0.24 mom_12_1 killer）；Python residualization 阶段 C001_b33 coverage=0.680 + ic_oos=0.0028 边缘独立，C002_b33 sign-flip + decay<0 噪声化。跨字段路径**没有打开新轴**（与 turnover_structural_signal 方向 "换 field ≠ 换维度" 升格证据一致）。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_001/candidates/C003\|C003_b1]] | `CV10/CV60 ratio` | mono_flip (IS=0.10 OOS=-1.00) |
| [[batches/batch_001/candidates/C004\|C004_b1]] | `Skew($amount, 20)` | IC_OOS=-0.003 + mono_flip |
| [[batches/batch_001/candidates/C006\|C006_b1]] | `Corr($amount, Δclose, 20)` | mono_flip regime-dep |
| [[batches/batch_001/candidates/C007\|C007_b1]] | `Slope(Log($amount), 20)` | Log 发散 coverage 0.327 |
| [[batches/batch_001/candidates/C008\|C008_b1]] | `Kurt($amount, 20)` | 四重失败 (sign+ic+decay+mono) |
| [[batches/batch_002/candidates/C003\|C003_b2]] | `MAD/Med($amount, 10)` | corr=0.967@F001 near_dup |
| [[batches/batch_002/candidates/C004\|C004_b2]] | `Max/Mean($amount, 60)` | ic_oos=-0.0078 regime-dep |
| [[batches/batch_003/candidates/C003\|C003_b3]] | `Q0.85/Mean($amount, 20)` | alpha_survival=0.26 poor |
| [[batches/batch_003/candidates/C004\|C004_b3]] | `Q0.95/Mean($amount, 20)` | vol_20d=35.3（方向最高） |
| [[batches/batch_008/candidates/C001\|C001_b8]] | `Corr(amount, Sign(Δclose), 40)` | 40d mono_flip (IS=0.70 OOS=-0.90) |
| [[batches/batch_008/candidates/C006\|C006_b8]] | `Skew($amount, 20)` 重测 | 高阶矩 6 次证伪 |
| [[batches/batch_033/candidates/C001\|C001_b33]] | `Corr(amt,vol,20)/Corr(amt,vol,60)` resid | coverage=0.680 hard_gate |
| [[batches/batch_033/candidates/C003\|C003_b33]] | `Corr(amount, Sign(Δclose), 20)` resid | coverage=0.697 hard_gate (信号健康) |
| [[batches/batch_033/candidates/C005\|C005_b33]] | `Slope(amount/Mean(amount,20), 20)` resid | coverage=0.684 hard_gate (信号健康) |

---

## Related

- 🟢 [[directions/turnover_structural_signal|turnover_structural_signal]] `productive` — batch_003 决策树方案 A 派生新方向，绕开 vol_20d 耦合
- 🔵 [[lessons#Structural Constraints]] — vol_20d 吸收律（F001/F301 升格）/ 市值代理红线 / 向量化约束
- 🔵 [[lessons#Python Factor Contract]] — F008 Python residual + rolling 系统性 coverage≈0.71 边界
- 🔵 [[lessons#Data Facts]] — `$amount` 有数据；`$vwap` 全零

---

## Narrative Log

> [!quote]+ 2026-04-23 · [[batches/batch_033/judge|batch_033]] · admit=0 / reserve=0 / reject=5
> **方向正式收束为 saturated**。Python `vol_20d` residualization 唯一逃生口跑完，5/5 全部 hard-gate reject，共同死因 `coverage < 0.80`。关键结论非"残差化无效"反之亦然：C003/C005 残差化确实修掉历史 CP04 vol_20d 吞噬，留下 ic_oos=-0.0157/-0.0244、decay=1.17/0.88 的统计影子；但样本可用性使其无法入库。**Thread**: T004 / T005 双 DISPROVEN。**结论**：当前日频 `$amount` 数据空间已 answer 掉，复活只能依赖更高频数据或 F008 coverage 修复路径。

> [!quote]+ 2026-04-19 · [[batches/batch_008/judge|batch_008]] · admit=0 / reserve=4 / reject=2
> **方向级 vol_20d 结构性瓶颈第 4 次确认**。19/19 非 hard_gate 候选 100% `dominant_style=vol_20d`。三条逃脱路径全失败：40d horizon mono_flip / 跨字段组合 style_r²=0.78 / amount momentum cum_ic_mdd=-73.3。**最大矛盾 C003**：mono=-1.0 / max_corr=0.07@F001 / 9 年全负 / 符号一致性=1.0 完美 rank-order 正交，但 alpha_survival=0.24 触 poor dealbreaker。**下轮唯一逃生口**：Python vol_20d Barra residual。若仍零 admit，方向 saturated。

> [!quote]- 2026-04-18 · [[batches/batch_001/judge|batch_001]] · admit=1 (C001 amount_cv_10) / reserve=2 / reject=5
> 方向从 `exploring` 转 `productive`（首次 admit 触发）。**T001 短窗口 CV 是 core edge**：C001 完美单调 -1.0 + 9 年同号 + ICIR_OOS=-0.716。**8/8 候选 vol_20d 主导**（平均暴露 ~17，C005 最高 32.0）——方向级结构发现：$amount 多数二阶统计量在 Barra 空间中与 vol_20d 强共线。T002 高阶矩 20d 窗口噪声大不可用；T003 baseline 算子族双双结构性失败，hypothesis 未证伪转 T004 承接。
