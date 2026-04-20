---
direction_tag: barra_residual_alpha
status: productive
priority: high
rounds: 5
admits: 1
last_batch: batch_014
last_admits: []
last_goal: 'Round 3 of barra_residual_alpha: explore style-subset variations (size-only,
  momentum-only strip), horizon variation (5d-fwd cumulative), vol-20d-keep smoothed
  extension of batch_013/C002 reserve, pure vol_20d baseline, and residual × volume-sign
  interaction. Tests probes #1-#3 from direction.md Next probes.'
last_activity: '2026-04-20T17:39:38Z'
created_batch: batch_012
members:
- F004
retired_members:
- F005
merged_into: null
---
# barra_residual_alpha

## Hypothesis

All existing directions hit vol_20d/str_1m style coupling as structural bottleneck — every DSL candidate either has Barra dominant style exposure or is near-duplicate of existing factors. The residual from regressing returns on Barra style factors represents idiosyncratic alpha orthogonal to known risk.

** Barra residual alpha  = Regress(Returns ~ vol_20d + str_1m + turnover_20d + log_circ_cap + book_to_price + mom_12_1 + ep_ratio) → Residuals

经济直觉：Barra 风格因子吸收了市场 common risk；如果 residual 仍携带 IC，说明存在风格无法解释的异质波动。

## Current Focus

**新方向首批 batch**：测试 Barra residual IC 是否 > 0 且独立于现有因子库（F001/F002/F003）。

## Threads

### T001: Barra residual 有效性 [✓ ANSWERED batch_012]
**Question**: Barra residual returns是否携带独立于风格因子的 alpha？
**Evidence trail**:
- [[batches/batch_012/candidates/C001|batch_012 C001]]: IC=0.024 ICIR=0.293 ls_t=7.34 Barra_residual_IC=0.033 > raw IC=0.024 → **admit → [[factors/F004]]**
- [[batches/batch_012/candidates/C003|batch_012 C003]]: Barra_residual_IC=0.033（与 C001 相当）但 style_r²=0.289 + vol_20d exposure=15.6 耦合严重 → **reserve**
**Next probes**: 扩展 Barra residual + volume 交互候选

### T002: 残差与其他因子正交性 [◉ ACTIVE]
**Question**: Barra residual 与 F001/F002/F003 的增量 IC 是否 > 0？vol-20d-only residual 是否可行？
**Evidence trail**:
- [[batches/batch_012/candidates/C001|batch_012 C001]]: incremental_ic=0.032 max_corr=0.15（F002） → 正交
- [[batches/batch_013/candidates/C001|batch_013 C001]]: Barra_residual_alpha_60d → **admit→retire** (F005, 2026-04-20 retired as bit-for-bit duplicate of F004; near_duplicate gate was blind to Python factors at commit time)
- [[batches/batch_013/candidates/C002|batch_013 C002]]: vol-20d-only residual → reserve (ICIR=0.243 ls_t=7.28 alpha_surv=1.62 incremental_ic=0.030 max_corr=0.12)；比全剥离 survival 更高
- [[batches/batch_014/candidates/C001|batch_014 C001]]: 纯 vol_20d 本体（无 residual）→ reserve (ic_oos=-0.063 mono=-0.7 cum_dd=-98 style_r²=0.999 incremental_ic=-0.046)；\|IC\| 大但 style_r²=0.999 + 与库反向
- [[batches/batch_014/candidates/C002|batch_014 C002]]: vol-20d-keep residual + 3d EMA → **reject hard_gate** (corr=0.987 with F004)；时序平滑不改 cross-sectional 结构
- [[batches/batch_014/candidates/C004|batch_014 C004]]: strip only momentum (str_1m+mom_12_1) → **reject hard_gate** (sign_flip + ic_oos_too_low)；momentum 簇带 regime 依赖，不可单独剥离
- [[batches/batch_014/candidates/C005|batch_014 C005]]: strip 6 styles, keep log_circ_cap → **reject hard_gate** (corr=0.906 with F004)；log_circ_cap 在 7-style basis 中只贡献边际信息
- [[batches/batch_014/candidates/C006|batch_014 C006]]: F004 residual × Sign(Δvolume_5d) → **reject hard_gate** (ic_oos=0.0071 < 0.008)；attention/volume-confirmation 在 daily 频率证伪
**Next probes**: vol_20d 是残差空间唯一主导维度（C002+C005 双向证明）；改 residualization 方法（robust regression / kernel / 加新 styles）才能继续推进——调整 7-style basis 子集已穷尽

### T003: Lookahead detection / construction safety [◉ ACTIVE] 🆕
**Question**: hard_gate 是否充分检测 Python 候选的时序泄漏？AST 扫描应禁止哪些模式？
**Evidence trail**:
- [[batches/batch_014/candidates/C003|batch_014 C003]]: `close.shift(-HORIZON)/close - 1` 把 t+5 累计收益作为 t 时刻因子值；hard_gate 8 项全过但 ic_oos=0.386 / icir=4.63 / ls_t=83 / ls_max_dd=0 / win_rate=1.0 / sortino=inf 是构造性 leak artifact
- 系统盲区：Barra residualize 只剥截面风格不防时序 leak；hard_gate 当前无 negative-shift 检测、无"too good to be true"哨兵
**Next probes**: 短期—主 agent 对 \|ic_oos\|>0.10 候选 manual review；长期—hard_gate 增 AST 扫描禁 `shift(-k)` in factor value path + 哨兵指标（ls_max_dd=0 / win_rate=1.0 / sortino=inf 任一触发→suspicion queue）

## Known Failures
- C002 (batch_012): sign_flip + oos_decay 双杀（IS→OOS alpha 逆转）
- C004 (batch_012): 5d rolling residual IC=0.007 < 0.008（太弱）
- C005 (batch_012): 20d momentum residual IC=-0.0035（方向反转）
- C003 (batch_013): Barra residual × turnover interaction → sign_flip (IS=-0.0066, OOS=+0.011) + oos_decay=-1.648
- C004 (batch_013): 10d Barra styles — redundant with C001 (identical metrics)
- C005 (batch_013): size-neutral quintile — compute_error (quintile shape mismatch)
- C002 (batch_014): vol-20d-keep + 3d EMA — corr 0.987 with F004（时序平滑不动 cross-sectional 结构）
- C003 (batch_014): 5d forward cumulative residual — **lookahead leak**（forbidden 构造，非真信号）
- C004 (batch_014): strip only momentum cluster — sign_flip + ic_oos_too_low（momentum regime-dep）
- C005 (batch_014): strip all except log_circ_cap — corr 0.906 with F004（size 仅边际贡献）
- C006 (batch_014): F004 × Sign(Δvolume_5d) — sign 调制把 IC 0.024→0.0071 稀释（volume confirmation 证伪）

## Narrative Log
### 2026-04-19 [[batches/batch_012/judge|batch_012]]
**admit=1 / reserve=1 / reject=3**

Barra residual alpha 方向首批验证假设成立：
- **C001 admit**（barra_residual_return）：IC=0.024 ICIR=0.293 ls_t=7.34 Barra_residual_IC=0.033 > raw IC=0.024；incremental_ic=0.032 全新机制空间
- **C003 reserve**：Barra_residual_IC=0.033 但 style_r²=0.289 + vol_20d exposure=15.6，耦合严重
- **C002/C004/C005 reject**：IC 不足或 sign_flip

**Thread 进展**：
- T001 answered：Barra residual alpha 假设验证成立
- T002 active：C001 证明增量 IC=0.032 > 0

**下一步**：
1. 下一批扩展 Barra residual + volume 交互候选
2. 监控 C003（若 style_r² 改善可 admit）
3. 注意 2021 后 Barra residual edge 衰减趋势

### 2026-04-19 [[batches/batch_013/judge|batch_013]]
**admit=1 / reserve=1 / reject=3**

Barra residual alpha 第二批验证：
- **C001 admit**（barra_residual_alpha_60d）：ICIR=0.293 ls_t=7.34；replicate batch_012 结果；vol_20d dominant (coef=4.44) 但 residual IC > raw IC
- **C002 reserve**：vol-20d-only residual；ICIR=0.243 ls_t=7.28 alpha_surv=1.62；incremental_ic=0.030 max_corr=0.12；比全剥离 survival 更高(1.62 vs 1.35)
- **C003 reject**：Barra residual × turnover interaction — sign_flip (IS=-0.0066, OOS=+0.011) + oos_decay=-1.648
- **C004 reject**：10d Barra styles — identical metrics to C001; no incremental value
- **C005 reject**：size-neutral quintile — compute_error (quintile shape mismatch)

**Thread 进展**：
- T001 answered (batch_012)：Barra residual alpha 存在
- T002 active：C001 admit 确认 vol_20d 主要吞噬来源但 residual 仍显著；C002 reserve 说明 vol-20d-only residual 可行

**下一步**：
1. C002 reserve 值得再观察一批 — incremental_ic=0.030 + max_corr=0.12 满足库空间独立条件
2. 纯 vol_20d 信号 vs Barra residual 哪个 IC 更高？
3. 20d 窗口的 Barra residual 是否比 60d 衰减更快？

### 2026-04-21 [[batches/batch_014/judge|batch_014]]
**admit=0 / reserve=1 / reject=5**

Barra residual alpha 方向首批 0 admit。三大发现：

1. **vol_20d 主导残差空间（C002+C005 双向证明）**：strip 6 keep vol_20d → corr 0.987 with F004；strip 6 keep log_circ_cap → corr 0.906 with F004。F004 的 alpha 几乎完全来自剥离 vol_20d 这一动作，其余 6 styles 加起来贡献 < 10% 可分离方差。**调整 7-style basis 子集已穷尽**。
2. **C003 暴露 hard_gate 时序检测盲区**：`close.shift(-5)/close - 1` 是 lookahead leak，hard_gate 8 项全过但指标 (ic_oos=0.386, ls_max_dd=0, win_rate=1.0) 是 artifact。新建 T003 thread 跟踪。
3. **C001 (纯 vol_20d 本体) reserve**：\|IC\|=0.063 > F004 \|IC\|=0.024 但 style_r²=0.999 + incremental_ic=-0.046 → magnitude 大不等于可投资，residualization 是真正的 12× 清洁度 value-add。

**Thread 进展**：
- T002 active：vol_20d 主导残差空间 → 探索路径必须改残差化方法（robust regression / kernel / 加新 styles），不再调 7-style 子集
- T003 active 🆕：lookahead detection 系统盲区记录，等待 hard_gate 增 AST 扫描

**下一步**：
1. batch_015 同方向但换残差化方法：robust regression（Huber/quantile）、加 intraday vol style
2. 若 batch_015 仍 0 admit，方向 `productive → saturated`，开新方向（cross-field interaction / microstructure）
3. 监控 admit 率：当前 4 batches/2 admits = 50%，若 batch_015 跌到 2/5=40% 触发 saturated 检讨

## Related
- [[lessons#Structural Constraints]]  （Barra style coupling 教训）
- [[amount_volatility_signal]]  （vol_20d 天花板）
- [[value_liquidity_interaction]]  （DSL 空间穷尽）
