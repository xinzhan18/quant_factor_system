# Quant Factor System - 开发计划 (v4.0)

## 📋 项目概述

量化因子研究和交易平台，支持：
- **TimescaleDB** 存储 (只支持这个，SQLite已删除)
- 日线/分钟数据存储和检索
- 因子计算和存储 (APPEND ONLY)
- 单因子/多因子选股
- 仓位管理和止盈止损
- 回测引擎和绩效分析
- Streamlit Dashboard

## ⚠️ 重要: 只支持 TimescaleDB

```bash
# 启动 TimescaleDB (必须)
docker run -d --name timescaledb \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=quant123 \
  timescale/timescaledb:latest-pg14
```

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Quant Factor System                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    数据层 (TimescaleDB)                   │   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │              TimescaleDB (必须)                   │   │   │
│  │  │  • price_1min  - 1分钟数据 (按周分区)           │   │   │
│  │  │  • price_5min  - 5分钟数据 (按月分区)           │   │   │
│  │  │  • price_daily - 日线数据 (按年分区)            │   │   │
│  │  │  • 自动压缩 (7天/1月/1年后)                    │   │   │
│  │  │  • 增量更新                                    │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │              米筐数据源                          │   │   │
│  │  │  • 日线/分钟数据                               │   │   │
│  │  │  • 需要 rqdatac SDK                          │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    因子层 (Factors)                      │   │
│  │                                                         │   │
│  │  • MinuteAggregator  - 分钟聚合到日频                  │   │
│  │  • Factor Factory    - 因子工厂                        │   │
│  │  • Factor Registry   - 因子注册表                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    选股层 (Selector)                    │   │
│  │                                                         │   │
│  │  • SingleFactorSelector - 单因子选股                    │   │
│  │  • MultiFactorCombiner - 多因子组合                    │   │
│  │  • IntersectionFilter   - 交集过滤                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   仓位层 (Position)                      │   │
│  │                                                         │   │
│  │  • EqualWeightManager  - 等权分配                       │   │
│  │  • FactorWeightedManager - 因子加权                     │   │
│  │  • KellyManager       - 凯利公式                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  止盈止损层 (StopLoss)                   │   │
│  │                                                         │   │
│  │  • FixedStopLoss    - 固定止盈止损                      │   │
│  │  • ATRStopLoss      - ATR动态止损                       │   │
│  │  • TrailingStopLoss - 移动止损                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   回测层 (Backtest)                       │   │
│  │                                                         │   │
│  │  • BacktestEngine   - 回测引擎                          │   │
│  │  • PerformanceAnalyzer - 绩效分析                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Dashboard层                            │   │
│  │                                                         │   │
│  │  • Home.py            - 首页                           │   │
│  │  • StrategyConfig.py  - 策略配置                       │   │
│  │  • BacktestResult.py  - 回测结果                       │   │
│  │  • TaskMonitor.py     - 任务监控                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
quant_factor_system/
├── __init__.py                 # 包入口 (只导出 TimescaleDB)
├── setup.py                    # 安装配置
├── requirements.txt            # 依赖列表
├── cli.py                      # CLI入口
├── config.py                   # 配置
├── logger.py                   # 日志
├── exceptions.py               # 异常定义
│
├── data/                       # 数据层 (只支持 TimescaleDB)
│   ├── __init__.py
│   ├── timescale_storage.py    # ⭐ TimescaleDB 存储 (唯一)
│   ├── ricequant_source.py    # 米筐数据源
│   ├── data_manager.py        # 数据管理器
│   ├── factor_storage.py      # 因子存储
│   ├── factor_version.py      # 因子版本管理
│   └── postgres_db.py         # PostgreSQL连接
│
├── factors/                   # 因子层
│   ├── __init__.py
│   ├── aggregator.py         # ⭐ 分钟聚合器
│   ├── factory.py            # 因子工厂
│   ├── registry.py           # 因子注册表
│   └── basic/
│       ├── __init__.py
│       ├── factors.py        # 基础因子
│       └── return_factors.py # 收益率因子
│
├── selector/                  # 选股层
│   ├── __init__.py
│   ├── single.py            # ⭐ 单因子选股
│   ├── multi.py             # ⭐ 多因子组合
│   └── filter.py            # ⭐ 交集过滤
│
├── position/                  # 仓位层
│   ├── __init__.py
│   ├── equal.py             # ⭐ 等权分配
│   ├── factor.py            # ⭐ 因子加权
│   └── kelly.py             # ⭐ 凯利公式
│
├── stoploss/                # 止盈止损层
│   ├── __init__.py
│   ├── fixed.py             # ⭐ 固定止盈止损
│   └── atr.py               # ⭐ ATR动态止损
│
├── backtest/                # 回测层
│   ├── __init__.py
│   ├── engine.py            # ⭐ 回测引擎
│   └── analyzer.py           # ⭐ 绩效分析
│
├── dashboard/               # Dashboard层
│   ├── Home.py             # ⭐ 首页
│   ├── config.py
│   └── pages/
│       ├── Data.py          # 数据浏览
│       ├── Factors.py       # 因子评估
│       ├── Pipeline.py      # Pipeline
│       ├── StrategyConfig.py # ⭐ 策略配置
│       ├── BacktestResult.py # ⭐ 回测结果
│       └── TaskMonitor.py   # ⭐ 任务监控
│
├── examples/                 # 示例
│   ├── timescale_example.py   # ⭐ TimescaleDB示例
│   └── ricequant_pipeline.py # ⭐ 米筐数据流程
│
└── docs/
    └── DEVELOPMENT_PLAN.md   # 本文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
cd /path/to/quant_factor_system

# 安装依赖
pip install -r requirements.txt

# 安装项目
pip install -e .
```

### 2. 启动 TimescaleDB (必须!)

```bash
# Docker 方式 (推荐)
docker run -d --name timescaledb \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=quant123 \
  timescale/timescaledb:latest-pg14
```

### 3. 初始化数据库

```python
from quant_factor_system.data import QuantDataManager

# 初始化 (创建所有表)
manager = QuantDataManager()
manager.initialize()
```

### 4. 更新数据

```python
# 更新日线数据
manager.update_daily(
    symbols=['SH600000', 'SH600001'],
    start_date='20240101',
    end_date='20240131'
)

# 更新分钟数据
manager.update_minute(
    symbols=['SH600000'],
    start_date='20240101',
    end_date='20240131',
    frequency='1min'
)
```

### 5. 查询数据

```python
# 日线
df = manager.get_price(
    symbols=['SH600000'],
    start_date='2024-01-01',
    end_date='2024-01-31',
    frequency='daily'
)

# 分钟
df = manager.get_price(
    symbols=['SH600000'],
    start_date='2024-01-01',
    end_date='2024-01-31',
    frequency='1min'
)
```

### 6. 运行回测

```python
from quant_factor_system import (
    SingleFactorSelector,
    EqualWeightManager,
    BacktestEngine,
    FixedStopLoss,
)

# 选股
selector = SingleFactorSelector(top_n=10)
result = selector.select(factor_df, factor_col='ret20')

# 仓位
manager = EqualWeightManager(max_positions=10)
positions = manager.calculate_positions(result.selected_symbols)

# 回测
engine = BacktestEngine()
result = engine.run(
    strategy=result,
    price_data=price_data,
    start_date='2024-01-01',
    end_date='2024-03-31'
)
```

### 7. 启动 Dashboard

```bash
cd quant_factor_system/dashboard
streamlit run Home.py
```

访问: http://localhost:8501

## 📊 数据存储容量 (5000只股票 × 20年)

| 数据类型 | 原始大小 | 压缩后 | 分区策略 |
|---------|---------|--------|---------|
| 1分钟 | ~500 GB | ~40 GB | 按周分区, 7天后压缩 |
| 5分钟 | ~100 GB | ~8 GB | 按月分区, 1月后压缩 |
| 日线 | ~2 GB | ~0.5 GB | 按年分区, 1年后压缩 |

**总容量**: ~50 GB (压缩后)

## 🔧 配置选项

### TimescaleDB 连接配置

```python
TIMESCALE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'quant_data',
    'user': 'postgres',
    'password': 'quant123',
}
```

### 分区配置

```python
CHUNK_CONFIG = {
    'price_1min': '1 week',      # 1分钟数据按周分区
    'price_5min': '1 month',     # 5分钟数据按月分区
    'price_daily': '1 year',    # 日线数据按年分区
}

COMPRESSION_POLICY = {
    'price_1min': '7 days',      # 7天后自动压缩
    'price_5min': '1 month',     # 1月后自动压缩
    'price_daily': '1 year',    # 1年后自动压缩
}
```

## 📦 依赖

```
pandas>=1.5.0
numpy>=1.21.0
scipy>=1.10.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
matplotlib>=3.5.0
plotly>=5.10.0
streamlit>=1.20.0
python-dateutil>=2.8.0
pytz>=2023.3
rqdatac>=1.0.0  # 可选
```

## 🧪 测试

```bash
# 运行测试
pytest tests/

# 运行覆盖率
pytest --cov=quant_factor_system tests/
```

## 📝 更新日志

### v4.0 (2026-02-15)
- ⚠️ **移除 SQLite，只保留 TimescaleDB**
- ✨ 新增 TimescaleDB 存储支持
- ✨ 新增压缩策略 (自动压缩历史数据)
- ✨ 新增增量更新功能
- ✨ 优化项目结构
- ✨ 添加 requirements.txt
- 📚 更新文档

### v3.0 (2026-02-15)
- ✨ 完整的因子回测系统
- ✨ Dashboard 界面
- ✨ 选股/仓位/止盈止损模块

## 📄 许可证

MIT License

## 👤 作者

QuantFactorSystem

---

*文档版本: 4.0*
*最后更新: 2026-02-15*
