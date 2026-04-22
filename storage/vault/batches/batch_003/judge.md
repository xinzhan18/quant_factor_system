---
batch_id: batch_003
direction: amount_volatility_signal
judged_at: 2026-04-19T02:16:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reserve}
  - {candidate_id: C005, verdict: reserve}
batch_summary: {total: 5, admit: 0, reserve: 4, reject: 1}
admit_count: 0
reject_count: 1
reserve_count: 4
candidate_count: 5
---

# batch_003 Judge Summary

> [!abstract]+ batch_003 · [[directions/amount_volatility_signal]] · 5 candidates
> ✅ **admit=0** · ⏸ **reserve=4** (C002 norm_slope, C003 top-15%, C004 top-5%, C005 sign-only Corr) · ❌ **reject=1** (C001 hard_gate mono_flip)
> **核心发现**: vol_20d 天花板被确认为**方向级结构瓶颈** — T002 分位数实现 (C003/C004) 虽数据质量过关（C004 mono=-1.0 完美），但 alpha_survival 双双 poor（0.26 / 0.57）、vol_20d 暴露冲至 28.3/35.3（C004 是方向 13 候选绝对最高）；T004 sign-preserved 三分支（C001/C002/C005）——条件均值 mono_flip、归一化 Slope ls_t=-1.29 弱、sign-only Corr ls_t=0.14 崩塌。**没有一个候选能在"避免 F001 重复 × 避免 vol_20d 吞噬 × 产出独立 PnL"三者兼顾**。
> **MT Budget**: cumulative 13 → **18** · direction 13 → **18** · 本批 bucket 全 `low`（search_adjusted: C002/C005 medium, C003/C004 high）· 本批 low=4 / med=0 / high=0 / hard_gate=1

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | mono_sign_flip IS=0.70 OOS=-0.40 | Sign×amount 条件均值同构 C006_b1 跨期分位翻号——T004 第三次撞同一堵墙 | [[batches/batch_003/candidates/C001]] |
| C002 | ⏸ reserve | 🟢·🔴·🟡·🟢·🟢 | ICIR_oos=-0.175 ls_t=-1.29 mono_oos=0.0 max_corr=0.23@F001 | 归一化 Slope 解决 Log 发散（coverage 0.97 vs C007_b1 0.33）但强度不足 + Q5 一桨驱动 | [[batches/batch_003/candidates/C002]] |
| C003 | ⏸ reserve | 🟢·🟡·🔴·🟡·🟢 | ICIR_oos=-0.460 ls_t=-2.59 mono=-0.9 alpha_surv=0.259 | Q85 分位 > 单点 max 但仍触 alpha_survival dealbreaker；split_dispersion=0.115 方向时序最稳 | [[batches/batch_003/candidates/C003]] |
| C004 | ⏸ reserve | 🟢·🟡·🔴·🟡·🟡 | ICIR_oos=-0.543 ls_t=-3.11 mono=-1.0 vol_20d=35.3 alpha_surv=0.574 | 完美单调 + 最强 ls_t 但 vol_20d 暴露 13 候选峰值，"更脏的 F001" | [[batches/batch_003/candidates/C004]] |
| C005 | ⏸ reserve | 🟡·🔴·🔴·🟢·🟡 | ICIR_oos=-0.273 ls_t=0.14 max_corr=0.07@F001 alpha_surv=0.509 | 方向内首个非-CV 机制（corr=0.07 正交）但 ls_t 近零 PnL 坍塌，"有 IC 无 L/S" | [[batches/batch_003/candidates/C005]] |

## 跨候选对比

- **vol_20d 天花板三重确认**：本批 3/5 候选 (C003/C004/C005) 以及前两批 10/11 通过候选全部 `dominant_style=vol_20d`。C004 暴露 35.3（方向历史最高）、C003 28.3、C005 12.1。`alpha_survival` 本批三档：0.26(C003) / 0.57(C004) / 0.51(C005)——**三者都触 CP04 dealbreaker (<0.60 poor)**，但原因不同：C003/C004 是分位数代数上与 Std 共享右尾驱动；C005 虽机制不同但 12× vol_20d 暴露说明 sign-corr 仍被波动率预测力吸收。
- **T004 sign-preserved 三种实现全盘分化**：条件均值 C001 mono_flip（同 C006_b1）、归一化 Slope C002 ls_t 弱、sign-only Corr C005 ls_t 坍塌——**amount×direction 家族在当前 DSL 空间已第四次撞分位跨期不稳 / PnL 转化失败**。T004 DSL 实现空间事实上封闭。
- **T002 分位数路径虽有进展但未脱敏**：C004 分位数 Quantile_0.95 / Mean_20 证明"分位数 >> 单点 TsMax"（C004 mono=-1.0 完美 vs C005_b1 Max/Mean_20 mono=-1.0 但被吞），但代数上右偏 $amount 分布中高分位数必然与 CV 强相关（C004 corr=0.52@F001），T002 DSL-native 路径本质是"更脏的 F001"。
- **MT 预算**：cumulative/direction 13→18，方向 family term=0.413（继续在同族），validation_exposure 保持 2。search_adjusted 对 C003/C004 仍为 high，对 C002/C005 降至 medium（因 C002/C005 在非-CV 家族）——但"不在 CV 家族"不等于"不在 vol_20d 家族"。
- **Reserve 四选一视角**：若只能留一个，C004（完美 mono + 最强 ls_t）是"分位数代表作"，C002（正交度最高 max_corr=0.23）是"非 CV 机制代表作"；两者互补，保留全部等待 vol_20d residual 实现验证。

## Thread 进展

> [!failure]+ T002 [[directions/amount_volatility_signal#T002]] — DSL-native 路径实质封闭 `[◉ ACTIVE but DSL-bounded]`
> C003 Q85 + C004 Q95 证明分位数实现 >> 单点 TsMax，但 alpha_survival 分别 0.26 / 0.57 触 CP04 poor dealbreaker；vol_20d 暴露 28.3 / 35.3 超过 F001。**T002 DSL-native 出路已探尽**——下一步必须走 vol_20d orthogonalize（Python 逃生口或跨横截面实现）或新字段组合（如 $turnover_rate × $amount）。

> [!failure]+ T004 [[directions/amount_volatility_signal#T004]] — sign-preserved 三分支全盘未 admit `[◉ ACTIVE but DSL-bounded]`
> C001 Sign×amount 条件均值 hard_gate mono_flip（与 C006_b1 continuous Delta 同构失败模式）；C002 归一化 Slope ICIR=-0.175 ls_t=-1.29 弱；C005 sign-only Corr ls_t=0.14 PnL 坍塌。T004 hypothesis（资金方向一致性携带 alpha）仍 ACTIVE 但 DSL 实现空间已证伪四次——**必须跳出 20d 窗口 Corr/Slope/均值 家族**，考虑 Python 逃生口或改变 horizon（C005 ic_by_horizon 20d=-0.038 > 1d=-0.017，可能低频版有救）。

## 方向级反思

本批**仍零 admit**——这不是单候选失败，而是**方向级机制瓶颈**的第三次验证。累计 18 候选里 1 admit (F001) + 6 reserve + 11 reject，admit 率 5.6%。方向级 admit 率通常需 > 15% 才算 productive，目前状态接近 `saturated` 临界。

**方向结构性发现**（超越单批）：
1. **18/18 候选 dominant_style=vol_20d** — 不是样本偏差，是方向本质。`$amount` 的所有二阶统计量 + 方向一致性统计量都被 vol_20d 吸收。
2. **DSL 实现空间对 vol_20d 无解**：分位数（C003/C004）、归一化 Slope（C002）、sign-only Corr（C005）、条件均值（C001）四条子路径均触 alpha_survival < 0.60 或 mono_flip；能逃离 vol_20d 的唯一路径是**向量残差化**，不在 DSL 能力内。
3. **F001 成为不可撼动 anchor**：10d CV 的 alpha 由"最短窗口 + 最低风格耦合 + 最完美单调"三者共同锁定，后续 18 候选无一能在 max_corr × alpha_survival × mono 三维超越。

**下轮决策树**：
- **方案 A（首选）**：暂停本方向，开辟**新方向 turnover_structural_signal** — 用 `$turnover_rate` × $amount 组合或换手率独立特征（换手率 CV、换手率加速度），避开 vol_20d 风格耦合陷阱
- **方案 B**：走 Python 逃生口实现"F001 vol_20d residual" — 验证 C004（完美 mono）剥离 vol_20d 后是否仍有独立 ls 价值
- **方案 C**：彻底改变 horizon，测试 5d/20d 持仓期的 amount 信号（batch_003 多候选 IC 在 20d horizon 显著强于 1d）

若下批选方案 A/C，方向 `status` 保持 productive（未熄火，只是结构瓶颈）；若方案 B 仍零 admit，则 `productive → saturated`。
