# 量化因子系统集成计划

## 基于因子分析报告的实现计划

---

## 目标

基于 Alphalens、QuantStats、Zipline 的分析，完善我们的量化因子系统。

---

## Task List

### Phase 1: 核心指标 (本周)

| ID | 任务 | 优先级 | 状态 | 来源 |
|----|------|--------|------|------|
| T1.1 | IC 系列 (IC, ICIR, IC decay) | P0 | ✅ 已完成 | Alphalens |
| T1.2 | 分组回测 (5组/10组) | P0 | ✅ 已完成 | Alphalens |
| T1.3 | 因子换手率分析 | P1 | ✅ 已完成 | Alphalens |
| T1.4 | 因子自相关分析 | P1 | ✅ 已完成 | Alphalens |

### Phase 2: 收益统计 (本周)

| ID | 任务 | 优先级 | 状态 | 来源 |
|----|------|--------|------|------|
| T2.1 | 夏普比率 (滚动/历史) | P0 | ✅ 已完成 | QuantStats |
| T2.2 | 最大回撤序列 | P0 | ✅ 已完成 | QuantStats |
| T2.3 | 风险指标 (VaR, CVaR) | P1 | ✅ 已完成 | QuantStats |
| T2.4 | 索提诺比率 | P1 | ✅ 已完成 | QuantStats |
| T2.5 | 卡玛比率 | P2 | ✅ 已完成 | QuantStats |

### Phase 3: Pipeline 架构 (待开始)

| ID | 任务 | 优先级 | 状态 | 来源 |
|----|------|--------|------|------|
| T3.1 | 因子管道 API 设计 | P1 | TODO | Zipline |
| T3.2 | 因子组合支持 | P1 | TODO | Zipline |
| T3.3 | 因子过滤机制 | P2 | TODO | Zipline |

---

## 详细设计

### T1.1: IC 系列实现

#### 来源: Alphalens `factor_information_coefficient()`

```python
# 当前实现 (evaluation/enhanced.py)
def calculate_ic(self, forward_returns: pd.DataFrame) -> pd.DataFrame:
    ic = pd.DataFrame()
    for col in forward_returns.columns:
        ic[col] = self.factor.rank().corr(forward_returns[col], method='spearman')
    return ic

# 需要增强:
# 1. IC decay (不同周期的 IC)
# 2. ICIR (IC / IC_std)
# 3. 分组 IC
```

#### 实现计划:

```
evaluation/enhanced.py
├── 新增:
│   ├── calculate_ic_decay()    # IC 衰减分析
│   ├── calculate_icir()        # IC IR
│   ├── calculate_group_ic()    # 按组 IC
│   └── calculate_rolling_ic() # 滚动 IC
```

### T1.2: 分组回测实现

#### 来源: Alphalens `mean_return_by_quantile()`

```python
# 当前实现已有，需要增强:
# 1. 支持任意分组数 (2-10)
# 2. 支持行业中性
# 3. 支持等权/因子加权
```

#### 实现计划:

```
trading/backtest.py
├── 增强:
│   ├── create_quantile_groups() # 任意分组
│   ├── calculate_group_returns() # 分组收益
│   └── generate_group_report()  # 分组报告
```

### T2.1: 夏普比率实现

#### 来源: QuantStats `sharpe()`

```python
# QuantStats 实现
def sharpe(returns, rf=0.0, periods=252):
    return (np.mean(returns - rf) / np.std(returns)) * np.sqrt(periods)

# 需要实现:
# 1. 滚动夏普
# 2. 动态无风险利率
```

---

## 代码结构

### 新增文件

```
quant_factor_system/
├── evaluation/
│   └── ic_analyzer.py      # IC 分析 (T1.1)
├── trading/
│   └── group_backtest.py   # 分组回测 (T1.2)
└── metrics/
    ├── sharpe.py           # 夏普比率 (T2.1)
    ├── drawdown.py         # 回撤分析 (T2.2)
    └── risk_metrics.py     # 风险指标 (T2.3)
```

### 修改文件

```
quant_factor_system/
├── evaluation/
│   └── enhanced.py         # 集成 IC decay
├── trading/
│   └── selector.py         # 增强选股
└── __init__.py             # 导出新增功能
```

---

## 测试计划

每个功能需要单元测试:

```bash
# 运行测试
python -m pytest tests/

# 具体测试
python -m pytest tests/test_ic.py -v
python -m pytest tests/test_sharpe.py -v
python -m pytest tests/test_drawdown.py -v
```

---

## 进度追踪

### 已完成

| ID | 任务 | 完成时间 | PR |
|----|------|----------|-----|
| T1.1 | IC 系列 | 2026-02-09 | #15 |
| T1.2 | 分组回测 | 2026-02-09 | #15 |
| T1.3 | 因子换手率 | 2026-02-09 | #15 |
| T1.4 | 因子自相关 | 2026-02-09 | #15 |
| T2.1 | 夏普比率 | 2026-02-09 | #16 |
| T2.2 | 最大回撤 | 2026-02-09 | #16 |
| T2.3 | VaR/CVaR | 2026-02-09 | #16 |
| T2.4 | 索提诺比率 | 2026-02-09 | #16 |
| T2.5 | 卡玛比率 | 2026-02-09 | #16 |

### Phase 3: Pipeline 架构 (待开始)

| ID | 任务 | 优先级 | 来源 |
|----|------|--------|------|
| T3.1 | 因子管道 API 设计 | P1 | Zipline |
| T3.2 | 因子组合支持 | P1 | Zipline |
| T3.3 | 因子过滤机制 | P2 | Zipline |

---

## 风险与应对

| 风险 | 可能性 | 影响 | 应对 |
|------|--------|------|------|
| VPN 阻断安装 | 高 | 无法安装依赖 | 使用现有库，不安装新包 |
| API 兼容问题 | 中 | 代码报错 | 隔离测试，逐步集成 |
| 性能问题 | 低 | 运行慢 | 优化算法，使用向量化 |

---

*计划创建时间: 2026-02-09*
*最后更新: 2026-02-09*
