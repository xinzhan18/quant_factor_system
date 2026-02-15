# Long-Term Memory

## Project: Quant Factor Trading Platform

### Overview
Complete quantitative factor research and trading platform with:
- **Data Layer**: TimescaleDB (production) + SQLite (lightweight)
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
- TimescaleDB (production) / SQLite (lightweight)
- PostgreSQL support

### Storage Architecture

#### SQLite (Lightweight)
- Path: `./data/factor_data.db`
- Suitable: < 100 stocks
- Tables: price_data, factor_data, factor_config

#### TimescaleDB (Production)
- Database: `quant_data`
- Tables: price_1min, price_5min, price_daily, factor_xxx
- Features: Auto-partitioning, auto-compression
- Capacity: ~50 GB for 5000 stocks × 20 years

### Key Design Decisions

1. **APPEND ONLY Storage**: Factor values cannot be modified - ensures data integrity
2. **TimescaleDB Compression**: 
   - 1min: Compress after 7 days (10x-20x compression)
   - 5min: Compress after 1 month
   - Daily: Compress after 1 year
3. **Modular Design**: Each module (selection, position, stoploss) is independent and extensible

### Usage Pattern
```python
from quant_factor_system import (
    SingleFactorSelector,
    EqualWeightManager,
    BacktestEngine,
    FixedStopLoss,
    Storage,
    TimescaleDB,
)

# SQLite (lightweight)
storage = Storage()
storage.save_factor('SH600000', '2024-03-15', 'ret20', 0.15)
df = storage.get_factor('ret20')

# TimescaleDB (production)
from quant_factor_system.data import QuantDataManager
manager = QuantDataManager()
manager.initialize()
manager.update_daily()
df = manager.get_price(symbols=['SH600000'], frequency='daily')

# Select stocks
selector = SingleFactorSelector(top_n=10)
result = selector.select(factor_df, factor_col='ret20')

# Allocate positions
manager = EqualWeightManager(max_positions=10)
positions = manager.calculate_positions(result.selected_symbols)

# Run backtest
engine = BacktestEngine()
result = engine.run(strategy, price_data, start_date, end_date)
```

### File Structure
```
quant_factor_system/
├── data/                    # Data layer
│   ├── storage.py          # SQLite unified storage
│   ├── timescale_storage.py # TimescaleDB storage
│   └── ricequant_source.py # RiceQuant adapter
├── factors/                 # Factor layer
│   └── aggregator.py       # Minute aggregator
├── selector/               # Selection layer
│   ├── single.py          # Single factor
│   ├── multi.py           # Multi factor
│   └── filter.py          # Filter
├── position/               # Position layer
│   ├── equal.py           # Equal weight
│   ├── factor.py          # Factor weighted
│   └── kelly.py           # Kelly formula
├── stoploss/              # Stop-loss layer
│   ├── fixed.py           # Fixed stop
│   └── atr.py             # ATR stop
├── backtest/              # Backtest layer
│   ├── engine.py          # Engine
│   └── analyzer.py        # Analyzer
├── dashboard/            # Dashboard
│   └── pages/            # Pages
└── examples/              # Examples
```

---

*Last updated: 2026-02-15*
