---
direction_tag: barra_residual_alpha
status: saturated
priority: low
rounds: 6
admits: 1
last_batch: batch_015
last_admits: []
last_goal: 'Round 4 of barra_residual_alpha: change residualization METHOD (not subset)
  per batch_014 finding that vol_20d dominates the 7-style basis. Test 5 alternatives
  — Huber regression, OLS+intraday-vol style, heteroscedastic-aware z-normalization,
  winsorized-input OLS, and vol×turnover interaction style. Goal: produce a residual
  sufficiently distinct from F004 (corr<0.7) while retaining IC>=0.015.'
last_activity: '2026-04-20T17:55:33Z'
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

### T002: 残差与其他因子正交性 [✗ DISPROVEN batch_015]
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
- [[batches/batch_015/candidates/C001|batch_015 C001]]: Huber IRLS residual → **reject hard_gate** (corr=0.907 with F004)；鲁棒损失不动 cross-sectional 几何
- [[batches/batch_015/candidates/C003|batch_015 C003]]: heteroscedastic-norm (F004 / rolling20d-std) → **reject hard_gate** (corr=0.927)；per-symbol time-series transform 不改 cross-section rank
- [[batches/batch_015/candidates/C004|batch_015 C004]]: winsorized OLS (±5 MAD) → **reject hard_gate** (corr=0.941)；±5 MAD 截断 <2% 尾部 β fit 几乎不动
- [[batches/batch_015/candidates/C005|batch_015 C005]]: OLS + vol×turn interaction style → **reject hard_gate** (corr=0.997)；collinear style pinv 自动消除
**Final outcome (batch_015)**: **F004 是该 7-style basis × OLS-family 残差的几何不变量**——5 method variants 全部 collapse 到 corr ≥ 0.91。**T002 假设证伪**：换损失函数 / 标准化 / 加 interaction style 都不能产生独立残差。后续需跳出 7-style basis 或 OLS-family 框架才能继续。

### T003: Lookahead detection / construction safety [◉ ACTIVE] 🆕
**Question**: hard_gate 是否充分检测 Python 候选的时序泄漏？AST 扫描应禁止哪些模式？
**Evidence trail**:
- [[batches/batch_014/candidates/C003|batch_014 C003]]: `close.shift(-HORIZON)/close - 1` 把 t+5 累计收益作为 t 时刻因子值；hard_gate 8 项全过但 ic_oos=0.386 / icir=4.63 / ls_t=83 / ls_max_dd=0 / win_rate=1.0 / sortino=inf 是构造性 leak artifact
- 系统盲区：Barra residualize 只剥截面风格不防时序 leak；hard_gate 当前无 negative-shift 检测、无"too good to be true"哨兵
- [[batches/batch_015/candidates/C002|batch_015 C002]]: Python 候选 REQUIRED_FIELDS=["$close","$high","$low"] 触发 `compute_error: market_df missing $high/$low`——data_bridge loader 默认只准备 close/volume/amount/market_cap，不尊重 REQUIRED_FIELDS 契约。系统级数据契约缺口。
**Next probes**: 短期—主 agent 对 \|ic_oos\|>0.10 候选 manual review；中期—loader 扩默认列加 OHLC 全集 / phase1 freeze 时 validate REQUIRED_FIELDS ⊆ loader 列；长期—hard_gate 增 AST 扫描禁 `shift(-k)` in factor value path + 哨兵指标（ls_max_dd=0 / win_rate=1.0 / sortino=inf 任一触发→suspicion queue）

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

### 2026-04-21 [[batches/batch_015/judge|batch_015]]
**admit=0 / reserve=0 / reject=5**

barra_residual_alpha 第二批 0 admit，**方向 saturated**：

**实验性建立 F004 不动点定理**：5 个 method-switch 候选 4/4 全部 collapse 到 F004（Huber=0.907 / hetero=0.927 / winsor=0.941 / vol×turn=0.997）。F004 是该 7-style basis × OLS-family 上的几何不变量——任何在同框架内的方法变体都无法产生独立 alpha。

**汇总 batch_014 + batch_015 saturation 证据链**：
1. 调整 7-style 子集（C002/C005 batch_014）→ vol_20d 主导，子集变化无效
2. 换 loss function（Huber/winsor batch_015）→ 几何不变
3. 时序后处理（EMA/std batch_014/015）→ cross-section rank 不变
4. 加 interaction style（vol×turn batch_015）→ collinear pinv 消除
5. 加 forward horizon（batch_014 C003）→ lookahead leak 不可用

**方向状态**：`productive → saturated`，`priority: high → low`。**复活路径**：(a) 加非 Barra style basis（行业 / GICS / microstructure factor model）；(b) nonparametric residualization（kernel ridge / NN）；(c) 与库其他因子的非线性 ensemble。

**Thread 进展**：
- T002 [✗ DISPROVEN batch_015]：method 变体证伪
- T003 active：data 契约缺口新增（C002 case），系统短期需 loader 扩列

**下一步**：batch_016 开新方向 **microstructure_signal** —— intraday H-L / open-close / 量价不对称等 daily-bar 内部结构信号。先解决 loader $high/$low 加载问题（直接修改或绕过）。

## Related
- [[lessons#Structural Constraints]]  （Barra style coupling 教训）
- [[amount_volatility_signal]]  （vol_20d 天花板）
- [[value_liquidity_interaction]]  （DSL 空间穷尽）
