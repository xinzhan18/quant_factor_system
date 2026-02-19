# Quant Factor Trading Platform - 架构设计文档

## 一、项目定位

完整的**量化因子研究与交易平台**，从数据获取到因子分析、回测、实盘交易的一体化解决方案。

---

## 二、目标架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           📊 Dashboard (Web界面)                         │
│   历史因子表现 | 执行回测 | 查看结果 | 任务监控 | 数据管理               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          🔄 Backtest (回测引擎)                           │
│   因子选择 → 股票筛选 → 仓位管理 → 止盈止损 → 收益分析                   │
│                                                                          │
│   输入: 因子组合 + 日期范围 + 初始资金                                    │
│   输出: 交易信号 | 持仓记录 | 绩效指标 | 收益曲线                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        📈 Factor Evaluation (因子评估)                    │
│   因子计算 → 可视化生成 → 保存结果                                       │
│                                                                          │
│   输入: 原始数据                                                         │
│   输出: IC分析图 | 分组收益图 | 多空组合图 | 因子排名                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          💾 Data Layer (数据层)                          │
│   数据下载 | 数据存储 | 数据查询 | 数据清洗                               │
│                                                                          │
│   输入: 米筐API                                                          │
│   输出: 存储到TimescaleDB                                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 三、四大核心模块

### 1. 💾 Data Module (数据模块)

**职责**: 所有外部数据的获取、清洗、存储

```
data/
├── api/                          # API接入
│   ├── ricequant.py             # 米筐数据源
│   └── tushare.py               # 可扩展: 其他数据源
│
├── storage/                      # 存储管理
│   ├── timescale_db.py          # TimescaleDB操作
│   └── postgres_db.py           # PostgreSQL操作
│
├── clean/                        # 数据清洗
│   ├── processor.py             # 数据预处理
│   └── validator.py              # 数据验证
│
└── manager.py                    # 数据管理器（统一入口）
```

**核心功能**:
| 功能 | 说明 |
|-----|------|
| `download_daily()` | 下载日线数据 |
| `download_minute()` | 下载分钟线数据 |
| `save_to_db()` | 保存到数据库 |
| `query_data()` | 查询数据 |
| `get_available_symbols()` | 获取股票列表 |

**对外接口**:
```python
from quant_factor_system.data import DataManager

dm = DataManager()
# 获取股票列表
symbols = dm.get_available_symbols(start_date='2015-01-01', end_date='2024-12-31')

# 下载并保存日线数据
dm.download_and_save_daily(symbols, start_date='2015-01-01', end_date='2024-12-31')

# 查询数据
df = dm.query_daily(symbols=['600000.SH', '000001.SZ'], 
                    start_date='2024-01-01', 
                    end_date='2024-12-31')
```

---

### 2. 📈 Factor Module (因子模块)

**职责**: 因子计算、可视化生成、结果存储

```
factors/
├── basic/                        # 基础因子实现
│   ├── return_factors.py         # 收益率因子 (1d, 5d, 20d, 60d)
│   ├── momentum_factors.py      # 动量因子 (20d, 60d)
│   ├── volatility_factors.py    # 波动率因子
│   └── ma_distance_factors.py   # 均线距离因子
│
├── core/                         # 核心逻辑
│   ├── base.py                  # 因子基类
│   ├── calculator.py            # 因子计算引擎
│   └── registry.py               # 因子注册表
│
├── visualization/                # 可视化模块
│   ├── ic_analyzer.py           # IC分析图
│   ├── group_returns.py         # 分组收益图
│   ├── long_short.py            # 多空组合图
│   └── report.py                # 综合报告
│
└── manager.py                    # 因子管理器
```

**因子计算流程**:
```
1. 输入: 原始价格数据 (from Data Module)
2. 计算: 因子值 = FactorCalculator.compute(data, factor_name)
3. 可视化: 生成IC图、分组收益图等
4. 存储: 保存因子值到数据库 + 保存图表
5. 输出: 因子评估结果
```

**因子评估结果**:
| 指标 | 说明 |
|-----|------|
| IC | 信息系数 |
| IC_T | IC的t统计量 |
| IC胜率 | IC>0的比例 |
| 分组年化收益 | Q1-Q5各组年化收益 |
| 多空收益 | Q5-Q1组合收益 |
| 夏普比率 | 风险调整后收益 |

**对外接口**:
```python
from quant_factor_system.factors import FactorManager

fm = FactorManager()
# 计算因子
result = fm.compute_factor('return_1d', 
                           start_date='2015-01-01',
                           end_date='2024-12-31')

# 生成可视化报告
fm.generate_report('return_1d', output_dir='./reports')

# 获取因子评估结果
ic = result['ic']
icir = result['icir']
group_returns = result['group_returns']
```

---

### 3. 🔄 Backtest Module (回测模块)

**职责**: 真实回测框架，完整的交易模拟

```
backtest/
├── engine/                        # 回测引擎
│   ├── core.py                    # 核心引擎
│   ├── simulator.py               # 交易模拟器
│   └── optimizer.py               # 参数优化
│
├── selection/                      # 选股模块
│   ├── factor_selector.py         # 因子选择
│   ├── stock_filter.py            # 股票过滤
│   └── ranker.py                  # 排名打分
│
├── position/                      # 仓位管理
│   ├── equal.py                  # 等权仓位
│   ├── factor_weighted.py        # 因子加权
│   └── kelly.py                  # Kelly公式
│
├── stoploss/                      # 止损模块
│   ├── fixed.py                  # 固定止损
│   ├── atr.py                    # ATR止损
│   └── trailing.py               # 移动止损
│
├── analysis/                      # 绩效分析
│   ├── metrics.py                # 绩效指标
│   ├── performance.py            # 收益分析
│   └── risk.py                   # 风险分析
│
└── result/                        # 结果管理
    ├── recorder.py               # 交易记录
    └── exporter.py               # 结果导出
```

**回测流程**:
```
1. 因子选择: Select factors (IC筛选/手动选择)
       │
       ▼
2. 股票筛选: Filter stocks (行业/市值/流动性)
       │
       ▼
3. 因子打分: Rank stocks (因子值加权)
       │
       ▼
4. 仓位管理: Allocate capital (等权/因子加权)
       │
       ▼
5. 交易执行: Execute trades (买入/卖出)
       │
       ▼
6. 止盈止损: Risk management (固定/ATR/移动)
       │
       ▼
7. 绩效分析: Performance analysis
```

**对外接口**:
```python
from quant_factor_system.backtest import BacktestEngine

# 配置回测
config = {
    'factors': ['return_1d', 'momentum_20'],
    'weights': [0.6, 0.4],
    'selection': {'top_n': 100, 'industry': None},
    'position': {'method': 'equal'},
    'stoploss': {'method': 'atr', 'multiplier': 2},
    'capital': 1000000,
    'start_date': '2022-01-01',
    'end_date': '2024-12-31',
}

# 运行回测
engine = BacktestEngine(config)
result = engine.run()

# 查看结果
result.summary()           # 绩效摘要
result.cumulative_returns() # 累计收益曲线
result.trade_log()         # 交易记录
result.performance()        # 详细绩效
```

**绩效指标**:
| 指标 | 说明 |
|-----|------|
| 年化收益率 | Annual Return |
| 夏普比率 | Sharpe Ratio |
| 最大回撤 | Max Drawdown |
| 胜率 | Win Rate |
| 盈亏比 | Profit/Loss Ratio |
| 交易次数 | Number of Trades |

---

### 4. 📊 Dashboard Module (仪表盘)

**职责**: 集中展示、历史表现、执行回测

```
dashboard/
├── pages/                        # 页面
│   ├── Home.py                   # 首页/概览
│   ├── Data.py                  # 数据管理
│   ├── Factors.py               # 因子评估 ⭐
│   ├── BacktestResult.py        # 回测结果
│   ├── StrategyConfig.py        # 策略配置
│   └── TaskMonitor.py           # 任务监控
│
├── components/                   # 组件
│   ├── charts/                   # 图表组件
│   │   ├── ic_chart.py
│   │   ├── returns_chart.py
│   │   └── performance_chart.py
│   ├── forms/                    # 表单组件
│   │   ├── factor_selector.py
│   │   └── backtest_config.py
│   └── tables/                   # 表格组件
│       ├── factor_table.py
│       └── trade_log_table.py
│
└── utils/                       # 工具
    ├── cache.py                  # 缓存管理
    └── session.py                # Session状态
```

**Dashboard功能**:
| 页面 | 功能 |
|-----|------|
| Home | 系统概览、快速入口 |
| Data | 数据下载、历史数据查询 |
| Factors | 因子评估、IC分析、分组收益 |
| BacktestResult | 回测结果展示、对比 |
| StrategyConfig | 回测策略配置 |
| TaskMonitor | 后台任务状态 |

---

## 四、数据流转图

```
                          米筐API
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                        Data Module                                │
│  download_daily() → save_to_db() → query_data()                 │
│                                                                  │
│  输出: price_daily, price_1min, price_5min                     │
└──────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Factor Module│   │Factor Module │   │ Backtest     │
│  (因子评估)   │   │  (批量计算)   │   │  (回测)      │
│              │   │              │   │              │
│ 输入:        │   │ 输入:        │   │ 输入:        │
│ price_daily │   │ price_daily │   │ price_daily │
│              │   │              │   │ + factors    │
│ 流程:        │   │ 流程:        │   │              │
│ 1.计算因子值 │   │ 1.批量计算   │   │ 流程:        │
│ 2.IC分析    │   │ 2.生成报告   │   │ 1.选股      │
│ 3.分组收益  │   │ 3.存数据库   │   │ 2.打分      │
│              │   │              │   │ 3.仓位      │
│ 输出:        │   │ 输出:        │   │ 4.回测      │
│ factor_xxx  │   │ factor_xxx  │   │ 5.绩效分析  │
│ + 图表      │   │ + 图表      │   │              │
└──────────────┘   └──────────────┘   │              │
                                      │ 输出:        │
                                      │ trade_log   │
                                      │ performance │
                                      └──────────────┘
```

---

## 五、当前状态分析

### 已完成 ✅

| 模块 | 状态 | 说明 |
|-----|------|------|
| Data Module | ✅ 完成 | ricequant_source, timescale_storage |
| Factor Module | ✅ 完成 | basic factors, calculation |
| Backtest Engine | ✅ 完成 | engine, analyzer |
| Position | ✅ 完成 | equal, factor, kelly |
| StopLoss | ✅ 完成 | fixed, atr |
| Dashboard | ⚠️ 部分 | Factors页面重构中 |

### 待完善 ⏳

| 模块 | 问题 | 优先级 |
|-----|------|--------|
| Data Module | 缺少统一入口DataManager | ⭐⭐ |
| Factor Module | 缺少可视化报告生成器 | ⭐⭐⭐ |
| Factor Module | 缺少因子结果存储 | ⭐⭐ |
| Backtest Module | 选股逻辑分散 | ⭐⭐ |
| Backtest Module | 缺少交易信号输出 | ⭐⭐ |
| Dashboard | Factors页面重构 | ⭐⭐ |
| 整体 | 缺少文档 | ⭐ |

---

## 六、重构计划

### Phase 1: 完善Data Module (1-2天)
- [ ] 创建 `data/manager.py` 统一入口
- [ ] 添加 `data/api/tushare.py` (可选)
- [ ] 完善 `data/clean/processor.py`

### Phase 2: 增强Factor Module (2-3天)
- [ ] 创建 `factors/visualization/` 模块
- [ ] 实现 `factors/core/calculator.py`
- [ ] 添加因子结果存储到DB
- [ ] 完善Factors.py Dashboard页面

### Phase 3: 优化Backtest Module (2-3天)
- [ ] 重构 `backtest/selection/` 选股模块
- [ ] 添加交易信号生成器
- [ ] 完善绩效分析指标

### Phase 4: 完善Dashboard (1-2天)
- [ ] 重构所有页面
- [ ] 添加因子对比功能
- [ ] 添加回测对比功能

---

## 七、依赖关系

```
Data Module (无依赖)
    │
    ▼
Factor Module (依赖Data Module)
    │
    ▼
Backtest Module (依赖Data Module + Factor Module)
    │
    ▼
Dashboard (依赖所有模块)
```

---

## 八、配置文件

```python
# config.py

# 数据库配置
DATABASE = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'quant_data',
    'user': 'postgres',
    'password': 'xxx'
}

# 米筐配置
RICEQUANT = {
    'user_id': 'xxx',
    'password': 'xxx'
}

# 回测配置
BACKTEST = {
    'default_capital': 1000000,
    'commission': 0.0003,
    'slippage': 0.0001,
}

# 因子配置
FACTORS = {
    'return_1d': {'class': 'Return1dFactor', 'params': {}},
    'return_5d': {'class': 'Return5dFactor', 'params': {}},
    'momentum_20': {'class': 'MomentumFactor', 'params': {'period': 20}},
}
```

---

## 九、扩展性

### 添加新因子
```python
# factors/basic/my_factor.py
from quant_factor_system.factors.core.base import BaseFactor

class MyFactor(BaseFactor):
    name = 'my_factor'
    
    def calculate(self, data):
        # 实现因子计算逻辑
        return self.values
```

### 添加新数据源
```python
# data/api/my_api.py
from quant_factor_system.data.base import BaseDataSource

class MyDataSource(BaseDataSource):
    def download_daily(self, symbols, start_date, end_date):
        # 实现数据下载
        return data
```

### 添加新止损策略
```python
# backtest/stoploss/my_stoploss.py
from quant_factor_system.backtest.stoploss.base import BaseStopLoss

class MyStopLoss(BaseStopLoss):
    def should_stop(self, position, current_price):
        # 实现止损逻辑
        return False
```

---

*文档版本: v1.0*
*最后更新: 2026-02-19*
