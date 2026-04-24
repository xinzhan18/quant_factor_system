# Consolidation Packet — directions/amount_volatility_signal.md

## Current content

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

---

## Current Focus

**方向已收束为 saturated**：batch_033 把唯一剩余的 Python `vol_20d` residualization 逃生口完整跑完，结果 5/5 全部 hard-gate reject，且共同死因是 `coverage < 0.80`。这说明 DSL 层的 `vol_20d` 吞噬虽然能靠残差化修掉，但修掉后留下的是**统计影子而非可执行载体**。**F001 仍是唯一可沉淀的 anchor**；本方向在当前日频数据空间里不再值得继续追加 batch。

---

## Threads

### T001: Amount CV 跨窗口比值 + lookback 扫描 [✓ ANSWERED batch_002]

> [!success]+ Thread 结论
> **Question**: $amount CV 在短 vs 长窗口的比值能否稳定刻画资金"断层"并产生 alpha？最优窗口？鲁棒算子是否开辟新子空间？
>
> **Evidence trail**:
> - [[batches/batch_001/candidates/C001|batch_001 C001]]　`CV_10` → ICIR_OOS=-0.716 ls_t=-3.78 mono=-1.0 → **admit → [[factors/F001]]**
> - [[batches/batch_001/candidates/C002|batch_001 C002]]　`CV_60` → ICIR_OOS=-0.214 mono_OOS=0.0 → reserve
> - [[batches/batch_001/candidates/C003|batch_001 C003]]　`CV10/CV60` → mono_flip IS=0.10→OOS=-1.00 → reject
> - [[batches/batch_002/candidates/C001|batch_002 C001]]　`CV_5` → ICIR_OOS=-0.623 max_corr=0.57@F001 + 换手×1.8 → reserve
> - [[batches/batch_002/candidates/C002|batch_002 C002]]　`CV_20` → vol_20d=37.5 全维劣化 → reserve
> - [[batches/batch_002/candidates/C003|batch_002 C003]]　`MAD/Med_10` → corr=0.967@F001 → reject (near_dup)
>
> **Answer**: 10d CV 是 "alpha 强度 × 风格干净度 × 换手成本" 三维全局最优 —— F001 anchor 地位跨窗口统计正式确立。**比值构造证伪**（C003_b1 mono_flip），**窗口扫描封闭**（5d 成本过高 / 20d 风格恶化），**鲁棒算子空间封闭**（MAD/Med 在右偏分布上近等价）。复活唯一路径 = vol_20d orthogonalize 后的残差版本。

### T002: Amount 分布形状（tail / high-order moment） [◉ ACTIVE] (DSL-bounded, 6 次证伪)

> [!note]+ Thread 当前
> **Question**: 偏度、峰度、max/mean、高分位数 / mean 是否携带独立于 CV 的尾部信息？
>
> **Evidence trail**:
> - [[batches/batch_001/candidates/C004|batch_001 C004]]　`Skew_20` → IC_OOS=-0.003 + mono_flip → reject
> - [[batches/batch_001/candidates/C005|batch_001 C005]]　`Max/Mean_20` → ICIR_OOS=-0.539 mono=-1.0 vol_20d=32.0 → reserve
> - [[batches/batch_001/candidates/C008|batch_001 C008]]　`Kurt_20` → 四重失败（sign+ic+decay+mono）→ reject
> - [[batches/batch_002/candidates/C004|batch_002 C004]]　`Max/Mean_60` → ic_oos=-0.0078 regime-dep 熄灭 → reject
> - [[batches/batch_003/candidates/C003|batch_003 C003]]　`Q0.85/Mean_20` → alpha_survival=0.26 poor → reserve
> - [[batches/batch_003/candidates/C004|batch_003 C004]]　`Q0.95/Mean_20` → vol_20d=35.3（方向最高） max_corr=0.52@F001 → reserve
> - [[batches/batch_008/candidates/C006|batch_008 C006]]　`Skew_20` 重测 → ic_oos=-0.0033 + mono_flip → reject
>
> **Partial Answer**: 20d 高阶矩（skew / kurt）信噪比过低，两次证伪；Max/Mean 延长到 60d regime-dep；分位数实现 mono 极好（-1.0 / -0.9）但 alpha_survival 0.26/0.57 触 CP04 poor，且 vol_20d 暴露冲至方向最高——**右偏 $amount 分布中高分位数代数上必与 CV (F001) 强相关**。**T002 DSL-native 实现空间事实上封闭**。
>
> **Next probes**: Python vol_20d Barra residual —— C003_b8 (rank-order 最强, max_corr=0.07) 或 C002_b3 (mono=-1.0) 残差版。

### T003: Amount 与 return 方向一致性（算子层） [✗ DISPROVEN batch_001]

> [!failure]+ Thread 结论
> **Question**: `Corr($amount, Δclose)` / `Slope(Log($amount))` 能否捕捉 absorption / trend-confirming 状态？
>
> **Evidence trail**:
> - [[batches/batch_001/candidates/C006|batch_001 C006]]　`Corr(amount, Δclose, 20)` → mono_flip IS=0.60→OOS=-0.70 → reject
> - [[batches/batch_001/candidates/C007|batch_001 C007]]　`Slope(Log(amount), 20)` → coverage 0.327 + mono_flip → reject
>
> **Answer**: 两个 baseline 实现结构性失败 —— Corr 分位跨期翻转（regime-dep），Log-Slope 遇 0 成交额发散（NaN 传播压缩样本）。**hypothesis 本身未被证伪**，转 T004 承接替代实现。

### T004: Amount-return 一致性的 NaN-safe 算子族 [✗ DISPROVEN batch_033] (DSL-bounded → Python residualized, 8 次证伪)

> [!failure]+ Thread 结论
> **Question**: 避免 Log 发散 + 分位稳定的前提下，归一化 slope / 幅度 corr / sign-preserved 实现能否落 T003 经济假设？
>
> **Evidence trail**:
> - [[batches/batch_002/candidates/C005|batch_002 C005]]　`Corr(amount, |Δclose|, 20)` → ic_oos=-0.0037 信号过薄 → reject
> - [[batches/batch_003/candidates/C001|batch_003 C001]]　`Sign(Δclose)×amount / Mean` → mono_flip IS=0.70→OOS=-0.40 → reject
> - [[batches/batch_003/candidates/C002|batch_003 C002]]　`Slope(amount/Mean, 20)` → ls_t=-1.29 mono_OOS=0.0 → reserve
> - [[batches/batch_003/candidates/C005|batch_003 C005]]　`Corr(amount, Sign(Δclose), 20)` → **max_corr=0.07@F001** 但 ls_t=0.14 PnL 坍塌 → reserve
> - [[batches/batch_008/candidates/C001|batch_008 C001]]　`Corr(amount, Sign(Δclose), 40)` → 40d mono_flip IS=0.70→OOS=-0.90 → reject
> - [[batches/batch_008/candidates/C004|batch_008 C004]]　`Delta(Mean(amount,20), 5)` → cum_ic_mdd=-73.3 vol_20d=16.2（历史最高暴露）→ reserve
> - [[batches/batch_033/candidates/C003|batch_033 C003]]　`Corr(amount, Sign(Δclose), 20)` residualized → coverage=0.697，虽 ic_oos=-0.0157 / decay=1.17 仍 **reject (hard_gate)**
> - [[batches/batch_033/candidates/C004|batch_033 C004]]　`Delta(Mean(amount,20), 5)` residualized → coverage=0.711 + ic_oos=-0.0062 → **reject (hard_gate)**
> - [[batches/batch_033/candidates/C005|batch_033 C005]]　`Slope(amount/Mean, 20)` residualized → coverage=0.685，虽 ic_oos=-0.0244 / decay=0.88 仍 **reject (hard_gate)**
>
> **Answer**: T004 的经济假设并非完全错误，Python residualization 后 C003/C005 仍保留了真实 rank-order 和稳定 decay；但**唯一逃生口最终被 coverage 硬闸堵死**，说明这条路径在当前日频数据可用性约束下没有可落地实现。DSL-native 空间已封闭，Python residual 也无法把它送进因子库，线程到此判为 `DISPROVEN`。

### T005: Amount × Turnover_rate 跨字段交互 [✗ DISPROVEN batch_033] (DSL-bounded → Python residualized)

> [!failure]+ Thread 结论
> **Question**: $amount 二阶统计量与 $turnover_rate 组合能否产生独立于 vol_20d 的新信号？
>
> **Evidence trail**:
> - [[batches/batch_008/candidates/C002|batch_008 C002]]　`Std($amount,20) / (Mean($turnover_rate,20)+1e-8)` → mono=-1.0 style_r²=0.784 → reserve
> - [[batches/batch_008/candidates/C005|batch_008 C005]]　`Std($amount,20) / Mean($turnover_rate,20)` (near-dup C002) → max_corr=0.60@F002 → reserve
> - [[batches/batch_008/candidates/C003|batch_008 C003]]　`Div(Corr(amount,volume,20), Corr(amount,volume,60))` → mono=-1.0 **max_corr=0.07@F001** alpha_surv=0.24（mom_12_1 alpha killer）→ reserve
> - [[batches/batch_033/candidates/C001|batch_033 C001]]　`Corr(amount,volume,20) / Corr(amount,volume,60)` residualized by vol_20d → coverage=0.680 + ic_oos=0.0028 → **reject (hard_gate)**
> - [[batches/batch_033/candidates/C002|batch_033 C002]]　同上再控 `mom_12_1` → coverage=0.680 + sign_flip + negative decay → **reject (hard_gate)**
>
> **Answer**: 跨字段路径在 DSL 里先被 `vol_20d` 吞噬，在 Python residualization 里又暴露出 coverage 与稳定性不足。C001 只剩边缘独立性，C002 则直接变成符号翻转噪声。T005 没有打开新轴，线程到此关闭。

---

## Thread 定论（升格自反复经验）

1. **vol_20d 结构性耦合是方向级物理约束**：19/19 候选 `dominant_style=vol_20d`，DSL 层任何比值 / 形状 / 相关性变换无法脱敏——右偏 $amount 分布的代数性质决定。
2. **F001 anchor 不可撼动**：10d CV 是 "alpha 强度 × 风格干净度 × 换手成本" 三维全局最优；任何新候选必须通过 `incremental_ic` & `max_corr@F001` 双关。
3. **20d 高阶矩死路**：skew / kurt 两次证伪，信噪比结构性过低，不再重测。
4. **mono_flip 是 DSL 空间的主要死因**：比值、条件均值、Corr 横向跨期、40d horizon Corr 全部 IS→OOS 翻号——regime-dependent 编码是 DSL 空间对 `$amount × direction` 的系统性弱点。
5. **Python residualization 只能验证“是否有统计影子”，不能自动变成可执行载体**：C003_b33 / C005_b33 说明去掉 `vol_20d` 后仍有 rank-order，但 coverage 0.697 / 0.685 使其无法入库。对这个方向而言，`vol_20d` 不是最后一个问题，样本可用性才是残差化后的终点约束。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_001/candidates/C003\|C003_b1]] | `CV10/CV60 ratio` | mono_flip (IS=0.10 OOS=-1.00) |
| [[batches/batch_001/candidates/C004\|C004_b1]] | `Skew($amount, 20)` | IC_OOS=-0.003 + mono_flip |
| [[batches/batch_001/candidates/C006\|C006_b1]] | `Corr($amount, Δclose, 20)` | mono_flip regime-dep |
| [[batches/batch_001/candidates/C007\|C007_b1]] | `Slope(Log($amount), 20)` | Log 发散 coverage 0.327 + mono_flip |
| [[batches/batch_001/candidates/C008\|C008_b1]] | `Kurt($amount, 20)` | 四重失败 (sign+ic+decay+mono) |
| [[batches/batch_002/candidates/C003\|C003_b2]] | `MAD/Med($amount, 10)` | corr=0.967@F001 near_dup |
| [[batches/batch_002/candidates/C004\|C004_b2]] | `Max/Mean($amount, 60)` | ic_oos=-0.0078 regime-dep |
| [[batches/batch_002/candidates/C005\|C005_b2]] | `Corr(amount, \|Δclose\|, 20)` | ic_oos=-0.0037 去方向化过薄 |
| [[batches/batch_003/candidates/C001\|C001_b3]] | `Sign(Δclose)×amount / Mean` | mono_flip (IS=0.70 OOS=-0.40) |
| [[batches/batch_003/candidates/C003\|C003_b3]] | `Q0.85/Mean($amount, 20)` | alpha_survival=0.26 poor |
| [[batches/batch_003/candidates/C004\|C004_b3]] | `Q0.95/Mean($amount, 20)` | vol_20d=35.3（方向最高） max_corr=0.52@F001 |
| [[batches/batch_008/candidates/C001\|C001_b8]] | `Corr(amount, Sign(Δclose), 40)` | 40d mono_flip (IS=0.70 OOS=-0.90) |
| [[batches/batch_008/candidates/C006\|C006_b8]] | `Skew($amount, 20)` 重测 | ic_oos=-0.0033 + mono_flip（高阶矩 6 次证伪）|
| [[batches/batch_033/candidates/C001\|C001_b33]] | `Corr(amount,volume,20) / Corr(amount,volume,60)` residualized | coverage=0.680 + ic_oos=0.0028 |
| [[batches/batch_033/candidates/C002\|C002_b33]] | `Corr(amount,volume,20) / Corr(amount,volume,60)` residualized + mom_12_1 | coverage=0.680 + sign_flip + decay<0 |
| [[batches/batch_033/candidates/C003\|C003_b33]] | `Corr(amount, Sign(Δclose), 20)` residualized | coverage=0.697 hard_gate |
| [[batches/batch_033/candidates/C004\|C004_b33]] | `Delta(Mean(amount,20), 5)` residualized | coverage=0.711 + ic_oos=-0.0062 |
| [[batches/batch_033/candidates/C005\|C005_b33]] | `Slope(amount/Mean(amount,20), 20)` residualized | coverage=0.684 hard_gate |

---

## Related

- 🟢 [[directions/turnover_structural_signal|turnover_structural_signal]] `productive` — batch_003 决策树方案 A 派生新方向，绕开 vol_20d 耦合
- 🔵 [[lessons#Structural Constraints]] — 市值代理红线 / 向量化约束
- 🔵 [[lessons#Data Facts]] — `$amount` 有数据；`$vwap` 全零

---

## Narrative Log

> [!quote]+ 2026-04-23 · [[batches/batch_033/judge|batch_033]] · admit=0 / reserve=0 / reject=5
> **方向正式收束为 saturated**。batch_033 把 direction 文档里写明的唯一逃生口 `Python vol_20d residualization` 完整跑完，结果 5/5 全部 hard-gate reject，且共同死因是 `coverage < 0.80`。最关键的结论不是“残差化无效”，恰恰相反：C003/C005 说明残差化确实修掉了历史上的 CP04 `vol_20d` 吞噬，留下了 `ic_oos=-0.0157/-0.0244`、`decay=1.17/0.88` 的统计影子；但这些影子没有足够 coverage 进入可执行空间。**Thread**: T004 `DISPROVEN batch_033`（Python 逃生口被 coverage 堵死）/ T005 `DISPROVEN batch_033`（cross-field residualization 变成低覆盖或 sign-flip 噪声）。**结论**：本方向在当前日频 `$amount` 数据空间里已经 answer 掉，不再继续追加 batch；若未来复活，只能依赖更高频数据或更好的残差化样本覆盖。

> [!quote]+ 2026-04-19 · [[batches/batch_008/judge|batch_008]] · admit=0 / reserve=4 / reject=2
> **方向级 vol_20d 结构性瓶颈第 4 次确认**。19/19 非 hard_gate 候选 100% `dominant_style=vol_20d`。三条逃脱路径全部失败：40d horizon（C001 mono_flip）/ 跨字段组合（C002/C005 style_r²=0.78；C003 alpha_surv=0.24）/ amount momentum（C004 cum_ic_mdd=-73.3）。**最大矛盾 C003**：mono=-1.0 / max_corr=0.07@F001 / 9 年全负 / 符号一致性=1.0 的完美 rank-order 正交信号，但 CP04 alpha_survival=0.24 触 poor dealbreaker。C002 vs C005 near-duplicate（incr_ic 负，对库无增值）。新开 T005（amount × turnover_rate），同被 Barra 阻断。**Thread**: T001 ANSWERED / T002 ACTIVE DSL-bounded（6 次证伪）/ T003 DISPROVEN / T004 ACTIVE DSL-bounded（5 次证伪）/ T005 新增 ACTIVE。**下轮唯一逃生口**：Python vol_20d Barra residual（C003_b8 rank 最强 或 C002_b3 mono=-1.0）。若仍零 admit，方向 `productive → saturated`。

> [!quote]- 2026-04-19 · [[batches/batch_003/judge|batch_003]] · admit=0 / reserve=4 / reject=1
> 方向级结构瓶颈第 3 次确认，18/18 候选全部 vol_20d 主导。DSL 实现空间对 vol_20d 无解：分位数（C003 0.26 / C004 0.57）、归一化 Slope（C002）、sign-only Corr（C005）四条子路径 alpha_survival 全部 <0.60 poor；条件均值（C001）mono_flip hard_gate。F001 anchor 跨 18 候选未被超越。**C005 唯一正面发现**：max_corr=0.07@F001 证明方向内仍有非-CV 独立机制，但 DSL 实现 PnL 坍塌——需 vol_20d residual 或 horizon 拉长。Thread: T002 / T004 hypothesis 仍成立但 DSL 事实上封闭。**决策树**（batch_004 三选一）: A 暂停本方向开辟 turnover_structural_signal / B Python vol_20d Barra residual / C 持仓期拉长重测 C005。

> [!quote]- 2026-04-19 · [[batches/batch_002/judge|batch_002]] · admit=0 / reserve=2 / reject=3
> **T001 窗口扫描正式定案**：10d (F001) 全局最优；5d 换手×1.8 + half_life 减半；20d 全维劣化 + vol_20d×1.5。**T001 算子空间封闭**：MAD/Med_10 corr=0.967@F001 近等价。**T002 延长窗口证伪**：Max/Mean_60 OOS 衰至 1/5（新 regime 失效）。**T004 幅度版证伪**：C005 去方向化过薄（ic_oos=-0.0037）。13/13 累计候选全部 vol_20d 主导——vol_20d orthogonalize 不做无法离开 anchor rule。

> [!quote]- 2026-04-18 · [[batches/batch_001/judge|batch_001]] · admit=1 (C001 amount_cv_10) / reserve=2 / reject=5
> 方向从 `exploring` 转 `productive`（首次 admit 触发）。**T001 短窗口 CV 是 core edge**：C001 完美单调 -1.0 + 9 年同号 + ICIR_OOS=-0.716；比值（C003）和长基线（C002）都不是 alpha 来源。**8/8 候选 vol_20d 主导**（平均暴露 ~17，C005 最高 32.0）——方向级结构发现：$amount 多数二阶统计量在 Barra 空间中与 vol_20d 强共线。T002 高阶矩 20d 窗口噪声大不可用；T003 baseline 算子族双双结构性失败，hypothesis 未证伪转 T004 承接。


## Instructions

Rewrite this direction md to compress long narrative logs, dedupe threads, and preserve Hypothesis + active Threads + Narrative Log (truncated to most recent 20 entries). Do not touch the frontmatter — Python manages that.
