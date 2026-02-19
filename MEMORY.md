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

### Data Source
- **Primary**: RiceQuant (米筐) - 唯一数据源
- 所有数据通过 `ricequant_source.py` 获取

### 正确的执行模式 ⭐⭐⭐

**永远不要创建 adhoc 脚本！** 所有任务必须使用项目模块执行：

```python
# 正确方式：直接在命令行使用项目模块
cd /Users/xinzhan/.openclaw/workspace
/Users/xinzhan/miniconda3/envs/quantfactor/bin/python -c "
import os
os.environ['RQDATAC_CONF'] = '米筐配置字符串'

from quant_factor_system.data import RiceQuantSource, TimescaleDB

# 使用项目API执行任务
source = RiceQuantSource()
db = TimescaleDB()

# 获取数据
data = source.get_daily_data(symbols=['600000.SH'], start_date='20150101', end_date='20151231')

# 保存
db.insert_price(data, table='price_daily')
"

# 关键点：
# 1. 使用 conda 环境的完整路径: /Users/xinzhan/miniconda3/envs/quantfactor/bin/python
# 2. 设置 RQDATAC_CONF 环境变量
# 3. 从 quant_factor_system 导入模块
# 4. 使用项目的 API (get_daily_data, insert_price 等)
```

**环境配置**：
- Conda 环境: `quantfactor`
- Python 路径: `/Users/xinzhan/miniconda3/envs/quantfactor/bin/python`
- RQDATAC_CONF: 从 `~/.zshrc` 读取或硬编码在脚本中

### Industry Factor Management

#### 行业数据特点
- **行业归属信息**: 不是每天更新，通常**季度或年度**调整（如财报公布后）
  - 中信行业分类: 季度更新
  - 申万行业分类: 年度/季度更新
- **行业因子值**: 每天可计算
  - 行业收益率 (industry_return)
  - 行业动量 (industry_momentum)
  - 行业波动率 (industry_volatility)

#### 存储策略
```sql
-- 行业归属表 (低频更新)
CREATE TABLE industry_classification (
    stock_code TEXT,
    industry TEXT,
    sub_industry TEXT,
    update_date DATE,  -- 生效日期
    PRIMARY KEY (stock_code, update_date)
);

-- 行业因子表 (每日更新)
CREATE TABLE factor_industry_daily (
    time TIMESTAMP,
    industry TEXT,
    factor_name TEXT,
    factor_value DOUBLE PRECISION,
    PRIMARY KEY (time, industry, factor_name)
);
```

#### 因子更新频率
| 因子类型 | 更新频率 | 示例 |
|---------|---------|------|
| 行业归属 | 季度 | 中信一级行业 |
| 行业收益率 | 每日 | 行业日收益率 |
| 行业动量 | 每日 | 20日行业累计收益 |
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
