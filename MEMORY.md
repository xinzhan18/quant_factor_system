# Long-Term Memory

## Project: Quant Factor Trading Platform

### Overview
Complete quantitative factor research and trading platform with:
- **Data Layer**: TimescaleDB (production)
- **Factor Layer**: Minute-to-daily aggregation, multiple methods
- **Selection Layer**: Single/multi-factor selection, filtering
- **Position Layer**: Equal weight, factor weighted, Kelly formula
- **Stop-Loss Layer**: Fixed, ATR-based, trailing stops
- **Backtest Engine**: Full simulation and performance analysis
- **Dashboard**: Strategy config, results display, task monitoring

### Technical Stack
- Python 3.8+
- Streamlit for Dashboard
- Pandas/NumPy/SciPy for data processing
- TimescaleDB (production only, SQLite removed)

### Storage Architecture

#### TimescaleDB (Production)
- Database: `quant_data`
- Tables: price_1min, price_5min, price_daily, factor_xxx
- Features: Auto-partitioning, auto-compression
- Capacity: ~50 GB for 5000 stocks × 20 years

### Key Design Decisions

1. **APPEND ONLY Storage**: Factor values cannot be modified - ensures data integrity
2. **TimescaleDB Only**: SQLite completely removed
3. **TimescaleDB Compression**: 
   - 1min: Compress after 7 days (10x-20x compression)
   - 5min: Compress after 1 month
   - Daily: Compress after 1 year
4. **Modular Design**: Each module (selection, position, stoploss) is independent and extensible

### Repository Rules ⭐

**要求: 每次代码更新后必须push到云端**

```bash
# 1. 添加所有更改
git add -A

# 2. 提交 (包含描述)
git commit -m "feat: 描述你的更改"

# 3. 推送到云端
git push origin main
```

**未推送的更改不算完成!**

### File Structure
```
quant_factor_system/
├── __init__.py              # 统一API入口
├── data/                    # 数据层
│   ├── timescale_storage.py # TimescaleDB存储
│   ├── ricequant_source.py  # 米筐数据源
│   ├── data_manager.py      # 数据管理器
│   └── postgres_db.py       # PostgreSQL工具
├── factors/                 # 因子层
│   ├── aggregator.py        # 聚合器
│   ├── factory.py           # 工厂
│   ├── registry.py          # 注册表
│   └── basic/               # 基础因子
├── selector/                # 选股层
│   ├── single.py            # 单因子选股
│   ├── multi.py             # 多因子组合
│   └── filter.py            # 过滤
├── backtest/               # 回测层
│   ├── engine.py            # 回测引擎
│   └── analyzer.py          # 绩效分析
├── position/                # 仓位层
│   ├── equal.py             # 等权
│   ├── factor.py            # 因子加权
│   └── kelly.py             # Kelly公式
└── stoploss/               # 止损层
    ├── fixed.py             # 固定止损
    └── atr.py               # ATR止损
```

### Usage Pattern
```python
# 数据
from quant_factor_system.data import QuantDataManager, RiceQuantSource

# 因子
from quant_factor_system.factors import FactorAggregator, FactorFactory

# 选股
from quant_factor_system.selector import SingleFactorSelector

# 回测
from quant_factor_system.backtest import BacktestEngine, PerformanceAnalyzer

# 仓位
from quant_factor_system.position import EqualWeightManager

# 止损
from quant_factor_system.stoploss import FixedStopLoss
```

---

*Last updated: 2026-02-16*
