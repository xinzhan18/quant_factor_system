# 已删除因子记录

记录从因子库中删除的因子及其原因，用于防止类似因子被重新录入。

---

## F005 — upper_shadow_ratio（上影线比率）

- **删除日期**: 2026-03-31
- **批次**: baseline_A
- **表达式**: `Div(Sub($high, If(Greater($close, $open), $close, $open)), Sub($high, $low))`
- **类别**: candlestick

**问题**：

1. **单调性严重不足（monotonicity = -0.10）**：五分位回报几乎无方向性结构
   - Q1=+0.039%, Q2=+0.033%, Q3=+0.060%, Q4=+0.063%, Q5=-0.005%
   - 应有单调递增（IC>0）但Q1≈Q2≈Q3≈Q4，仅Q5为负
2. **L/S 收益为负（-0.045 bps/日）**：IC为正（+0.035）但多空组合却亏损，信号无法被实际利用
3. **无 OOS 验证**：ic_mean_oos = NaN，从未通过样本外测试
4. **信号来源单一**：IC来自Q5极端空头端，无法构建稳定的多头组合

**结论**：IC信号为虚假信号（spurious），来自极端分位的统计噪音，不具备实际交易价值。

---

## F012 — up_day_count_20（20日上涨天数比率）

- **删除日期**: 2026-03-31
- **批次**: batch_009
- **表达式**: `Div(Count(Greater($close, Ref($close,1)), 20), 20)`
- **类别**: momentum

**问题**：

1. **五分位数据灾难性损坏**：
   - Q2 = -77.1%/日（A股涨跌停限制10%，物理上不可能）
   - Q3 = Q4 = Q5 = NaN（3个分位无数据）
   - L/S return = -0.771（显然是数据错误）
2. **IC 过低（0.0107）**：远低于实际有效阈值（0.015），仅勉强通过最低准入线（0.01）
3. **单调性 = -1.0**：数据完全反向（因数据损坏导致）
4. **无 OOS 验证**：ic_mean_oos = NaN

**结论**：评估期间数据管道发生严重错误，因子值计算本身可能存在问题（如分位分箱失败）。即使修复数据，IC过低也不值得重新评估。

---

## 说明

- 以上因子已从 `storage/library/library.yaml` 和 `storage/library/factors/` 中删除
- 已从 `factor_meta` 数据库表中删除
- 已删除对应的 Obsidian vault 报告
- 如需重新探索上影线类因子，应改进表达式以解决单调性问题，而非直接复用 F005 的形式

## 2026-04-02 清理 (本次)

- **factor_040** (inverse_circ_mktcap): 与 F038 表达式完全相同，batch_023 意外重复录入，DB 孤立条目，删除
- **[016] alpha010** (IC=0.017): 库中最弱因子，仅有 IS IC（无 Stage 3 OOS 验证），从库移除
- **[037] inverse_ps** (IC=0.018): 次弱，与 inverse_pb(028, IC=0.028) 概念冗余，从库移除

批量清理:
- 删除 batch_011~017.yaml（未运行，OHLCV 空间已耗尽）
- 删除 alpha101_batch_1,3,4,5.yaml（未运行，alpha101 评估完成）  
- 删除 memory/history/ 所有文件（candidates/ 的冗余副本）
- 删除 25 个 dead direction .md 文件
- 删除 4 个 .pkl 文件
- 删除 python_factors/F001_rolling_std_python.py（实验文件）
- 删除 orphaned direction: alpha024_mutations.md, cross_signal_interaction.md

## 2026-04-02 第二轮清理 (基于全期 IC 数据)

经 report.builder 全期数据验证，以下因子 OOS IC 近乎为零，实际无预测力：
- **[003] vol_regime_reversal** (全期 OOS IC=-0.011, Score=26): 矿掘期 IC=-0.043 在全期失效，regime 切换逻辑无法泛化
- **[006] resi_close_5** (全期 OOS IC=-0.002, Score=31): 全期实际 IC 接近零，mining IC=-0.033 来自噪音窗口  
- **[007] vol_regime_resi_vs_slope** (全期 OOS IC=-0.003, Score=39): 同上，regime × residual 组合无统计显著性
- **[023] signed_sqrt_return** (全期 OOS IC=-0.003, Score=25): 平方根变换未改善信号，OOS 彻底失效
- **[017] alpha034** (OOS IC=0.005, p=0.16 **不显著**): OOS t-stat仅1.41，无法拒绝IC=0假设；IS表现依赖特定期间，移除
