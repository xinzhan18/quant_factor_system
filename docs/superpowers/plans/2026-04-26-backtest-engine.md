# A-Share Backtest Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-contained, modular A-share portfolio backtest engine that turns admitted factor signals into "live-feel" PnL diagnostics (equity curve, trade log, position snapshots, cost-adjusted metrics) integrated into the Phase 4 report flow.

**Architecture:** State-machine engine over hfq market data. Strict T+1 settlement, board-aware limit detection, time-varying stamp tax, configurable signal recompute, modular components (config / calendar / data_view / tradability / filters / cost / account / strategy / executor / engine / reporter / runner). Output 4 parquet artifacts + metrics.yaml + 6 figures into `storage/vault/factors/F{id}/backtest/`.

**Tech Stack:** Python 3.8+, pandas, numpy, pyarrow (parquet), matplotlib, psycopg2 (TimescaleDB), pytest. Reuses `research.compute` for signal recompute path; integrates into existing `research` CLI dispatcher (`src/research/cli/main.py`).

**Spec:** `docs/superpowers/specs/2026-04-22-backtest-engine-design.md` (commit `8bb52b7`). Read it first — every contract, schema, edge-case policy lives there.

---

## File Structure

### Created
```
src/research/backtest/
├── __init__.py              # public API: run_backtest(...)
├── config.py                # BacktestConfig + sub-dataclasses + 3-layer merge + validate
├── calendar.py              # TradeCalendar
├── data_view.py             # PriceView wrapping hfq parquet
├── tradability.py           # TradabilityProvider (PIT)
├── filters.py               # TradabilityMask + ExecutionPolicy
├── cost.py                  # CostModel (pure function, time-varying stamp)
├── account.py               # Account + Position + Fill (T+1 lock)
├── strategy.py              # Strategy ABC + TopKLongOnly + QuintilePortfolio
├── executor.py              # Executor (target → diff → mask → fills)
├── engine.py                # Engine state machine + reconciliation
├── reporter.py              # parquets + metrics.yaml + figs
└── runner.py                # called by CLI and report subagent

scripts/
├── sync_st_status.py        # one-shot RiceQuant → instrument_st_status
└── sync_instrument_lifecycle.py   # one-shot listing/delisting dates

tests/research/backtest/     # one test file per module
├── __init__.py
├── conftest.py              # shared fixtures
├── test_config.py
├── test_calendar.py
├── test_data_view.py
├── test_tradability.py
├── test_filters.py
├── test_cost.py
├── test_account.py
├── test_strategy.py
├── test_executor.py
├── test_engine.py
├── test_reconciliation.py
├── test_information_set.py
└── test_engine_end_to_end.py
```

### Modified
- `scripts/resync_qlib.py` — add `--adjust hfq` flag + `market_daily_hfq.parquet` output
- `src/research/cli/main.py` — register `backtest` subcommand
- `storage/config.yaml` — add `backtest:` section per spec §3.5

---

## Build Order

```
Phase 0: data foundation
  T1 (hfq parquet sync)         ──┐
  T2 (DB tables for ST/lifecycle) ─┤  parallel
  T3 (config dataclasses)        ──┤
  T4 (TradeCalendar)             ──┘

Phase 1: data + masks
  T5 (PriceView)        ← T1
  T6 (TradabilityProvider) ← T2, T5
  T7 (TradabilityMask + ExecutionPolicy) ← T6
  T8 (CostModel)        ← (none)

Phase 2: state machine pieces
  T9  (Account)        ← T8
  T10 (Strategy)       ← T5
  T11 (Executor)       ← T7, T8, T9, T10
  T12 (Engine)         ← T4, T11

Phase 3: outputs + integration
  T13 (Reporter)       ← T12
  T14 (Runner + CLI)   ← T13
  T15 (Phase 4 subagent integration) ← T14
  T16 (End-to-end smoke on F009 holdout) ← T15
```

T17 (audit recompute on 6 polluted factors) is deferred — it's a follow-up workflow, not part of the engine.

---

## Conventions for All Tasks

- All tests under `tests/research/backtest/`. Run with: `pytest tests/research/backtest/ -v`
- All source under `src/research/backtest/`. Imports use bare module names (project uses `package_dir={"": "src"}`).
- Every commit message follows `<type>(<scope>): <summary>` where `<scope>` ∈ {backtest, backtest-data, backtest-test, backtest-cli}.
- TDD rhythm: failing test → run-fail → minimal impl → run-pass → commit. Don't batch tests with implementation.
- Avoid mocks for math; use small synthetic DataFrames in fixtures (`tests/research/backtest/conftest.py`).
- Use `pytest --import-mode=importlib` (already in `pytest.ini`).

---

## Task 1: Extend `resync_qlib.py` for HFQ output

**Files:**
- Modify: `scripts/resync_qlib.py`
- Test: manual smoke (no unit test — it's a one-shot data sync script)

- [ ] **Step 1: Add `--adjust` CLI flag**

Edit `scripts/resync_qlib.py` to accept `--adjust qfq|hfq` (default `qfq`). The flag chooses both:
1. The `adjust_type` passed to `RiceQuantSource.get_daily(adjust_type=...)` (re-fetch from RiceQuant if cache miss)
2. The output parquet path: `storage/cache/market_daily.parquet` for qfq, `storage/cache/market_daily_hfq.parquet` for hfq.

```python
import argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--adjust", choices=["qfq", "hfq"], default="qfq")
    args = p.parse_args()

    out_path = Path("storage/cache") / (
        "market_daily.parquet" if args.adjust == "qfq" else "market_daily_hfq.parquet"
    )
    df = load_from_db_with_adjust(args.adjust)   # extend existing load_from_db
    df.to_parquet(out_path)
    rebuild_qlib_binary(df, suffix="" if args.adjust == "qfq" else "_hfq")
```

- [ ] **Step 2: Run sync for hfq (one-time, ~30 min)**

```bash
PYTHONPATH=src python3 scripts/resync_qlib.py --adjust hfq
```

Expected: `storage/cache/market_daily_hfq.parquet` exists, ~9M rows for 2015-2024, columns include `$open, $high, $low, $close, $volume, $amount, $market_cap, $turnover_rate, $limit_up, $limit_down, returns_1d`.

- [ ] **Step 3: Sanity check the parquet**

```bash
PYTHONPATH=src python3 -c "
import pandas as pd
df = pd.read_parquet('storage/cache/market_daily_hfq.parquet')
print('rows:', len(df))
print('cols:', sorted(df.columns.tolist()))
print('date range:', df.index.get_level_values(0).min(), '~', df.index.get_level_values(0).max())
assert 'limit_up' in df.columns or '\$limit_up' in df.columns, 'limit_up missing'
"
```

Expected: rows ~9M, date range 2015-01-05 to 2024-12-31 (or latest available), `limit_up` and `limit_down` present.

- [ ] **Step 4: Commit**

```bash
git add scripts/resync_qlib.py
git commit -m "feat(backtest-data): add --adjust hfq flag to resync_qlib"
```

---

## Task 2: ST status + lifecycle DB tables + sync

**Files:**
- Create: `scripts/sync_st_status.py`
- Create: `scripts/sync_instrument_lifecycle.py`
- Test: manual smoke

- [ ] **Step 1: Create `instrument_st_status` table**

Run via `./scripts/db.sh shell` or `psql`:

```sql
CREATE TABLE IF NOT EXISTS instrument_st_status (
    datetime DATE NOT NULL,
    instrument VARCHAR(16) NOT NULL,
    is_st BOOLEAN NOT NULL,
    PRIMARY KEY (datetime, instrument)
);
CREATE INDEX IF NOT EXISTS idx_st_datetime ON instrument_st_status(datetime);
```

- [ ] **Step 2: Write `scripts/sync_st_status.py`**

Pull ST history from RiceQuant for 2015-2024. RiceQuant exposes `is_st_stock(date)` returning a list of ST symbols on each date.

```python
"""Sync A-share ST status history into instrument_st_status table."""
import psycopg2
import rqdatac as rq
import pandas as pd
from datetime import date, timedelta

rq.init()

conn = psycopg2.connect(host="localhost", port=5432, dbname="quant_data",
                        user="postgres", password="postgres")
cur = conn.cursor()

start, end = date(2015, 1, 1), date(2024, 12, 31)
all_syms = rq.all_instruments(type="CS").order_book_id.tolist()

dates = pd.bdate_range(start, end).date
rows = []
for dt in dates:
    st_symbols = [s for s in all_syms if rq.is_st_stock(s, dt) is True]
    rows.extend([(dt, s, True) for s in st_symbols])
    if len(rows) >= 50000:
        cur.executemany(
            "INSERT INTO instrument_st_status VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
            rows,
        )
        conn.commit()
        rows.clear()

if rows:
    cur.executemany(
        "INSERT INTO instrument_st_status VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
        rows,
    )
    conn.commit()

print("ST status synced:",
      cur.execute("SELECT COUNT(*) FROM instrument_st_status").fetchone()[0])
```

- [ ] **Step 3: Run ST sync**

```bash
PYTHONPATH=src python3 scripts/sync_st_status.py
```

Expected: ~500K-1M rows.

- [ ] **Step 4: Create `instrument_lifecycle` table**

```sql
CREATE TABLE IF NOT EXISTS instrument_lifecycle (
    instrument VARCHAR(16) PRIMARY KEY,
    listing_date DATE NOT NULL,
    delisting_date DATE,
    board VARCHAR(16) NOT NULL    -- main | chinext | star | bse
);
```

- [ ] **Step 5: Write `scripts/sync_instrument_lifecycle.py`**

```python
"""Sync listing/delisting dates + board classification."""
import psycopg2
import rqdatac as rq

rq.init()

def board_of(sym: str) -> str:
    if sym.startswith("SH688"):  return "star"
    if sym.startswith("SZ300"):  return "chinext"
    if sym.startswith(("BJ8","BJ4")): return "bse"
    return "main"

instruments = rq.all_instruments(type="CS")
rows = []
for _, r in instruments.iterrows():
    rows.append((r.order_book_id, r.listed_date, r.de_listed_date, board_of(r.order_book_id)))

conn = psycopg2.connect(host="localhost", port=5432, dbname="quant_data",
                        user="postgres", password="postgres")
cur = conn.cursor()
cur.executemany(
    "INSERT INTO instrument_lifecycle (instrument, listing_date, delisting_date, board) "
    "VALUES (%s,%s,%s,%s) ON CONFLICT (instrument) DO UPDATE "
    "SET listing_date=EXCLUDED.listing_date, delisting_date=EXCLUDED.delisting_date, "
    "    board=EXCLUDED.board",
    rows,
)
conn.commit()
print("instruments synced:", len(rows))
```

- [ ] **Step 6: Run lifecycle sync**

```bash
PYTHONPATH=src python3 scripts/sync_instrument_lifecycle.py
```

Expected: ~5500 rows.

- [ ] **Step 7: Commit**

```bash
git add scripts/sync_st_status.py scripts/sync_instrument_lifecycle.py
git commit -m "feat(backtest-data): add ST status + instrument lifecycle sync scripts"
```

---

## Task 3: Config dataclasses + 3-layer merge

**Files:**
- Create: `src/research/backtest/__init__.py`
- Create: `src/research/backtest/config.py`
- Create: `tests/research/backtest/__init__.py`
- Create: `tests/research/backtest/conftest.py`
- Create: `tests/research/backtest/test_config.py`
- Modify: `storage/config.yaml` (append `backtest:` section per spec §3.5)

- [ ] **Step 1: Append `backtest:` section to `storage/config.yaml`**

Copy the full block from spec §3.5 verbatim. Verify YAML parses:

```bash
PYTHONPATH=src python3 -c "
from research.storage.yaml_io import load_yaml
cfg = load_yaml('storage/config.yaml')
assert 'backtest' in cfg, 'backtest section missing'
print('OK, defaults keys:', list(cfg['backtest']['defaults'].keys()))
"
```

- [ ] **Step 2: Write the failing test**

`tests/research/backtest/test_config.py`:
```python
from datetime import date
import pytest
from research.backtest.config import BacktestConfig, load_default_config


def test_load_default_returns_validated_config():
    cfg = load_default_config(factor_id="F009")
    assert cfg.universe == "csi1000"
    assert cfg.initial_capital == 10_000_000
    assert cfg.signal_recompute is True
    assert cfg.rebalance.freq_days == 5
    assert cfg.cost.commission_bps == 3
    assert cfg.matching.price_adjust == "hfq"
    assert cfg.capital.allow_intraday_netting is False


def test_per_factor_override_takes_precedence_over_defaults(tmp_path, monkeypatch):
    # Write a per-factor override
    pf = tmp_path / "F009.backtest.yaml"
    pf.write_text("portfolio:\n  holdings_n: 100\n")
    monkeypatch.setattr("research.backtest.config._per_factor_path",
                        lambda fid: pf)
    cfg = load_default_config(factor_id="F009")
    assert cfg.portfolio.holdings_n == 100   # overridden
    assert cfg.portfolio.weight_scheme == "equal"   # unchanged


def test_cli_override_takes_precedence_over_per_factor(tmp_path, monkeypatch):
    pf = tmp_path / "F009.backtest.yaml"
    pf.write_text("portfolio:\n  holdings_n: 100\n")
    monkeypatch.setattr("research.backtest.config._per_factor_path",
                        lambda fid: pf)
    cfg = load_default_config(factor_id="F009",
                               cli_overrides={"portfolio": {"holdings_n": 30}})
    assert cfg.portfolio.holdings_n == 30


def test_validate_rejects_freq_days_below_2():
    with pytest.raises(ValueError, match="freq_days"):
        load_default_config(factor_id="F009",
                             cli_overrides={"rebalance": {"freq_days": 1}})


def test_periods_run_subset_of_train_val_holdout():
    with pytest.raises(ValueError, match="periods.run"):
        load_default_config(factor_id="F009",
                             cli_overrides={"periods": {"run": ["nonsense"]}})


def test_stamp_schedule_resolves_for_date():
    cfg = load_default_config(factor_id="F009")
    assert cfg.cost.stamp_bps_at(date(2020, 1, 1)) == 10
    assert cfg.cost.stamp_bps_at(date(2024, 1, 1)) == 5
```

- [ ] **Step 3: Run tests — expect failure**

```bash
pytest tests/research/backtest/test_config.py -v
```

Expected: ImportError (module doesn't exist).

- [ ] **Step 4: Implement `config.py`**

Sub-dataclasses must be `frozen=True`. Implementation sketch (~200 LOC):

```python
"""BacktestConfig — frozen dataclasses + 3-layer merge."""
from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import date as Date
from pathlib import Path
from typing import Any, Literal

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml


@dataclass(frozen=True)
class RebalanceConfig:
    freq_days: int
    anchor: str   # 'monday' | 'first_trade_day' | YYYY-MM-DD

@dataclass(frozen=True)
class PortfolioConfig:
    holdings_n: int
    weight_scheme: Literal["equal", "rank", "ic_weighted"]
    max_single_weight: float

@dataclass(frozen=True)
class MatchingConfig:
    match_price: Literal["open", "close"]
    price_adjust: Literal["hfq", "qfq", "none"]

@dataclass(frozen=True)
class StampScheduleEntry:
    from_date: Date
    to_date: Date
    sell_bps: float

@dataclass(frozen=True)
class CostConfig:
    stamp_schedule: tuple[StampScheduleEntry, ...]
    commission_bps: float
    slippage_bps: float
    min_commission_cny: float

    def stamp_bps_at(self, dt: Date) -> float:
        for e in self.stamp_schedule:
            if e.from_date <= dt <= e.to_date:
                return e.sell_bps
        raise ValueError(f"no stamp schedule covers {dt}")

@dataclass(frozen=True)
class CapitalConfig:
    allow_intraday_netting: bool

@dataclass(frozen=True)
class FilterConfig:
    block_st: bool
    block_suspended: bool
    block_limit_up_at_buy: bool
    block_limit_down_at_sell: bool
    cooldown_days_after_unsuspend: int
    newly_listed_days: int
    stale_position_days_max: int

@dataclass(frozen=True)
class PeriodsConfig:
    train: tuple[Date, Date]
    val: tuple[Date, Date]
    holdout: tuple[Date, Date]
    run: tuple[str, ...]

@dataclass(frozen=True)
class BenchmarkConfig:
    kind: Literal["csi1000_total_return", "csi1000_equal_weight_tradable"]

@dataclass(frozen=True)
class OutputConfig:
    save_trades: bool
    save_positions: bool
    figs: tuple[str, ...]

@dataclass(frozen=True)
class BacktestConfig:
    universe: str
    initial_capital: float
    signal_recompute: bool
    rebalance: RebalanceConfig
    portfolio: PortfolioConfig
    matching: MatchingConfig
    cost: CostConfig
    capital: CapitalConfig
    filters: FilterConfig
    periods: PeriodsConfig
    benchmark: BenchmarkConfig
    output: OutputConfig

    def validate(self) -> None:
        if self.rebalance.freq_days < 2:
            raise ValueError(
                f"rebalance.freq_days must be >= 2 (T+1 enforcement); got {self.rebalance.freq_days}"
            )
        valid_run = {"train", "val", "holdout"}
        if not set(self.periods.run).issubset(valid_run):
            raise ValueError(f"periods.run must be subset of {valid_run}; got {self.periods.run}")
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be > 0")


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Recursively merge overlay into base; overlay wins."""
    out = dict(base)
    for k, v in overlay.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _per_factor_path(factor_id: str) -> Path:
    return StoragePaths.factors_dir() / f"{factor_id}.backtest.yaml"


def _build_from_dict(d: dict) -> BacktestConfig:
    """Convert resolved dict into nested frozen dataclasses."""
    stamp = tuple(
        StampScheduleEntry(e["from"], e["to"], float(e["sell_bps"]))
        for e in d["cost"]["stamp_schedule"]
    )
    return BacktestConfig(
        universe=d["universe"],
        initial_capital=float(d["initial_capital"]),
        signal_recompute=bool(d["signal_recompute"]),
        rebalance=RebalanceConfig(**d["rebalance"]),
        portfolio=PortfolioConfig(**d["portfolio"]),
        matching=MatchingConfig(**d["matching"]),
        cost=CostConfig(
            stamp_schedule=stamp,
            commission_bps=float(d["cost"]["commission_bps"]),
            slippage_bps=float(d["cost"]["slippage_bps"]),
            min_commission_cny=float(d["cost"]["min_commission_cny"]),
        ),
        capital=CapitalConfig(**d["capital"]),
        filters=FilterConfig(**d["filters"]),
        periods=PeriodsConfig(
            train=tuple(d["periods"]["train"]),
            val=tuple(d["periods"]["val"]),
            holdout=tuple(d["periods"]["holdout"]),
            run=tuple(d["periods"]["run"]),
        ),
        benchmark=BenchmarkConfig(**d["benchmark"]),
        output=OutputConfig(
            save_trades=d["output"]["save_trades"],
            save_positions=d["output"]["save_positions"],
            figs=tuple(d["output"]["figs"]),
        ),
    )


def load_default_config(
    factor_id: str,
    cli_overrides: dict | None = None,
) -> BacktestConfig:
    base = load_yaml("storage/config.yaml")["backtest"]["defaults"]
    pf_path = _per_factor_path(factor_id)
    pf = load_yaml(pf_path) if pf_path.exists() else {}
    cli = cli_overrides or {}
    merged = _deep_merge(_deep_merge(base, pf), cli)
    cfg = _build_from_dict(merged)
    cfg.validate()
    return cfg
```

- [ ] **Step 5: Run tests — expect pass**

```bash
pytest tests/research/backtest/test_config.py -v
```

Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add storage/config.yaml src/research/backtest/__init__.py src/research/backtest/config.py \
        tests/research/backtest/__init__.py tests/research/backtest/conftest.py \
        tests/research/backtest/test_config.py
git commit -m "feat(backtest): add BacktestConfig with 3-layer merge + validate"
```

---

## Task 4: TradeCalendar

**Files:**
- Create: `src/research/backtest/calendar.py`
- Create: `tests/research/backtest/test_calendar.py`

- [ ] **Step 1: Write the failing test**

`tests/research/backtest/test_calendar.py`:
```python
from datetime import date
from research.backtest.calendar import TradeCalendar


def test_trading_days_excludes_weekends_and_holidays():
    cal = TradeCalendar.from_db()
    days = cal.trading_days(date(2024, 5, 1), date(2024, 5, 10))
    # 2024-05-01..05 is May Day holiday in China
    days_str = [d.isoformat() for d in days]
    assert "2024-05-01" not in days_str
    assert "2024-05-06" in days_str   # first trading day after holiday


def test_add_trading_days_skips_holidays():
    cal = TradeCalendar.from_db()
    # 2024-04-30 (Tue) + 1 trading day → 2024-05-06 (skip May Day)
    assert cal.add_trading_days(date(2024, 4, 30), 1) == date(2024, 5, 6)


def test_universe_at_returns_csi1000_membership():
    cal = TradeCalendar.from_db()
    syms = cal.universe_at(date(2024, 6, 28))
    assert isinstance(syms, set)
    assert 800 <= len(syms) <= 1000


def test_rebalance_schedule_monday_anchor_5day_freq():
    cal = TradeCalendar.from_db()
    sched = cal.rebalance_schedule(
        start=date(2024, 6, 1), end=date(2024, 6, 30),
        freq_days=5, anchor="monday",
    )
    # First Monday on/after 2024-06-03 is 2024-06-03 itself
    assert sched[0] == date(2024, 6, 3)
    # +5 trading days → 2024-06-11 (2024-06-10 is Dragon Boat holiday)
    assert sched[1] == date(2024, 6, 11)


def test_rebalance_schedule_skips_holiday_bridges():
    cal = TradeCalendar.from_db()
    # Around CNY: anchor on a Monday before CNY, +5 should land after holiday
    sched = cal.rebalance_schedule(
        start=date(2024, 1, 29), end=date(2024, 2, 28),
        freq_days=5, anchor="monday",
    )
    assert sched[0] == date(2024, 1, 29)   # first Monday
    # +5 trading days from 2024-01-29: 30,31, Feb 1,2, Feb5  (Feb 5 is Mon)
    assert sched[1] == date(2024, 2, 5)
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest tests/research/backtest/test_calendar.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `calendar.py`**

```python
"""TradeCalendar — trading days + dynamic universe + rebalance schedule."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from functools import lru_cache

import pandas as pd
import psycopg2

DB_DSN = dict(host="localhost", port=5432, dbname="quant_data",
              user="postgres", password="postgres")


@dataclass(frozen=True)
class TradeCalendar:
    _trading_days: pd.DatetimeIndex
    _universe_index: dict[date, set[str]]   # date → csi1000 members on that date

    @classmethod
    def from_db(cls) -> "TradeCalendar":
        conn = psycopg2.connect(**DB_DSN)
        cur = conn.cursor()
        # All trading days from market_daily
        cur.execute("SELECT DISTINCT time::date FROM market_daily ORDER BY 1")
        td = pd.DatetimeIndex([r[0] for r in cur.fetchall()])
        # csi1000 membership: index_constituents has start_date / end_date per (index_code, instrument)
        cur.execute(
            "SELECT instrument, start_date, end_date "
            "FROM index_constituents WHERE index_code = '000852'"
        )
        rows = cur.fetchall()
        # Build a date → set mapping
        membership: dict[date, set[str]] = {d.date(): set() for d in td}
        for sym, s, e in rows:
            for d in pd.bdate_range(s, e or td.max().date()).date:
                if d in membership:
                    membership[d].add(sym)
        conn.close()
        return cls(_trading_days=td, _universe_index=membership)

    def trading_days(self, start: date, end: date) -> list[date]:
        mask = (self._trading_days.date >= start) & (self._trading_days.date <= end)
        return [d.date() for d in self._trading_days[mask]]

    def add_trading_days(self, base: date, n: int) -> date:
        days = list(self._trading_days.date)
        idx = days.index(base) if base in days else _bisect_right(days, base) - 1
        return days[idx + n]

    def universe_at(self, dt: date) -> set[str]:
        return self._universe_index.get(dt, set())

    def rebalance_schedule(self, start: date, end: date,
                           freq_days: int, anchor: str | date) -> list[date]:
        days = self.trading_days(start, end)
        if not days:
            return []
        if anchor == "monday":
            # First Monday-or-later trading day in range
            first = next((d for d in days if d.weekday() == 0), days[0])
        elif anchor == "first_trade_day":
            first = days[0]
        elif isinstance(anchor, date):
            first = anchor if anchor in days else days[0]
        else:
            raise ValueError(f"bad anchor: {anchor}")
        first_idx = days.index(first)
        return [days[i] for i in range(first_idx, len(days), freq_days)]


def _bisect_right(xs, target) -> int:
    lo, hi = 0, len(xs)
    while lo < hi:
        mid = (lo + hi) // 2
        if xs[mid] <= target:
            lo = mid + 1
        else:
            hi = mid
    return lo
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/research/backtest/test_calendar.py -v
```

Expected: 5 passed (requires DB running with csi1000 data).

- [ ] **Step 5: Commit**

```bash
git add src/research/backtest/calendar.py tests/research/backtest/test_calendar.py
git commit -m "feat(backtest): add TradeCalendar with universe + rebalance schedule"
```

---

## Task 5: PriceView

**Files:**
- Create: `src/research/backtest/data_view.py`
- Create: `tests/research/backtest/test_data_view.py`

- [ ] **Step 1: Failing test**

```python
from datetime import date
from pathlib import Path
import pytest
from research.backtest.data_view import PriceView


@pytest.fixture
def price_view():
    return PriceView.from_parquet(Path("storage/cache/market_daily_hfq.parquet"))


def test_snapshot_ts_returns_max_datetime(price_view):
    assert price_view.snapshot_ts.year >= 2023


def test_slice_eod_returns_required_cols(price_view):
    df = price_view.slice_eod(date(2024, 6, 28), ["SH600000", "SH600036"])
    for col in ["open", "high", "low", "close", "volume", "amount", "limit_up", "limit_down"]:
        assert col in df.columns, f"missing {col}"
    assert len(df) == 2


def test_slice_eod_missing_symbol_omitted(price_view):
    df = price_view.slice_eod(date(2024, 6, 28), ["SH600000", "INVALID"])
    assert "INVALID" not in df.index


def test_slice_panel_inclusive(price_view):
    df = price_view.slice_panel(date(2024, 6, 24), date(2024, 6, 28), ["SH600000"])
    assert len(df) == 5  # 5 trading days
```

- [ ] **Step 2: Run — expect fail**

```bash
pytest tests/research/backtest/test_data_view.py -v
```

- [ ] **Step 3: Implement `data_view.py`**

```python
"""PriceView — wraps the hfq parquet for date/symbol slicing."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class PriceView:
    _df: pd.DataFrame   # MultiIndex (datetime, instrument)

    @classmethod
    def from_parquet(cls, path: Path) -> "PriceView":
        df = pd.read_parquet(path)
        # Normalize column names: strip leading $ if present
        df.columns = [c.lstrip("$") for c in df.columns]
        if df.index.nlevels != 2:
            raise ValueError(f"PriceView expects MultiIndex(datetime, instrument); got {df.index.nlevels}")
        return cls(_df=df)

    @property
    def snapshot_ts(self) -> datetime:
        return self._df.index.get_level_values(0).max().to_pydatetime()

    def slice_eod(self, dt: date, symbols: list[str]) -> pd.DataFrame:
        try:
            day = self._df.xs(pd.Timestamp(dt), level=0)
        except KeyError:
            return pd.DataFrame(columns=self._df.columns)
        return day.loc[day.index.intersection(symbols)]

    def slice_panel(self, start: date, end: date, symbols: list[str]) -> pd.DataFrame:
        sub = self._df.loc[(slice(pd.Timestamp(start), pd.Timestamp(end)), symbols), :]
        return sub
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/research/backtest/test_data_view.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/research/backtest/data_view.py tests/research/backtest/test_data_view.py
git commit -m "feat(backtest): add PriceView wrapping hfq parquet"
```

---

## Task 6: TradabilityProvider

**Files:**
- Create: `src/research/backtest/tradability.py`
- Create: `tests/research/backtest/test_tradability.py`

- [ ] **Step 1: Failing test**

```python
from datetime import date
import pytest
import pandas as pd
from research.backtest.tradability import TradabilityProvider


@pytest.fixture
def provider():
    return TradabilityProvider.from_db()


def test_st_status_time_varying(provider):
    # Pick a known ST stock and a known date when it was ST
    # (The script sync_st_status.py must have run.)
    syms = ["SH600000", "SH600036"]   # neither typically ST
    mask = provider.st_mask(date(2024, 6, 28), syms)
    assert isinstance(mask, pd.Series)
    assert mask.dtype == bool


def test_listing_date_present(provider):
    assert provider.listing_date("SH600000") <= date(2000, 1, 1)


def test_is_newly_listed_window(provider):
    # Stock listed today: newly listed for first 60 days
    listed_today = provider.listing_date("SH600000")
    assert provider.is_newly_listed(listed_today, "SH600000", n_days=60) is True
    assert provider.is_newly_listed(date(2024, 6, 28), "SH600000", n_days=60) is False


def test_limit_pct_chinext_pre_2020():
    p = TradabilityProvider.from_db()
    # ChiNext +10% before 2020-08-24, +20% from then on
    assert p.limit_pct(date(2019, 1, 1), "SZ300001") == pytest.approx(0.10)
    assert p.limit_pct(date(2021, 1, 1), "SZ300001") == pytest.approx(0.20)


def test_limit_pct_st_overrides():
    p = TradabilityProvider.from_db()
    # If a symbol is ST, limit_pct = 0.05 regardless of board
    # We need a stock that is ST on a specific date — use a known one or mock
    # For now, test the resolution logic via a hypothetical
    assert p._resolve_limit_pct(date(2024, 1, 1), "main", is_st=True) == pytest.approx(0.05)
    assert p._resolve_limit_pct(date(2024, 1, 1), "main", is_st=False) == pytest.approx(0.10)
    assert p._resolve_limit_pct(date(2024, 1, 1), "chinext", is_st=False) == pytest.approx(0.20)
    assert p._resolve_limit_pct(date(2019, 1, 1), "chinext", is_st=False) == pytest.approx(0.10)


def test_suspended_mask_via_volume_zero(provider):
    syms = ["SH600000"]
    # Trust the proxy: volume==0 → suspended
    mask = provider.suspended_mask(date(2024, 6, 28), syms)
    assert isinstance(mask, pd.Series)
```

- [ ] **Step 2: Run — fail**

- [ ] **Step 3: Implement `tradability.py`**

```python
"""TradabilityProvider — PIT facts about stock tradability."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from functools import lru_cache

import pandas as pd
import psycopg2

from research.backtest.data_view import PriceView

DB_DSN = dict(host="localhost", port=5432, dbname="quant_data",
              user="postgres", password="postgres")

CHINEXT_LIMIT_REGIME_CHANGE = date(2020, 8, 24)


@dataclass(frozen=True)
class TradabilityProvider:
    _st: pd.DataFrame                     # MultiIndex (datetime, instrument), col is_st
    _lifecycle: pd.DataFrame              # index instrument, cols listing_date / delisting_date / board
    _price_view: PriceView | None

    @classmethod
    def from_db(cls, price_view: PriceView | None = None) -> "TradabilityProvider":
        conn = psycopg2.connect(**DB_DSN)
        st = pd.read_sql(
            "SELECT datetime, instrument, is_st FROM instrument_st_status",
            conn,
        )
        st["datetime"] = pd.to_datetime(st["datetime"])
        st = st.set_index(["datetime", "instrument"])
        lc = pd.read_sql(
            "SELECT instrument, listing_date, delisting_date, board "
            "FROM instrument_lifecycle",
            conn,
            index_col="instrument",
        )
        conn.close()
        return cls(_st=st, _lifecycle=lc, _price_view=price_view)

    def st_mask(self, dt: date, syms: list[str]) -> pd.Series:
        ts = pd.Timestamp(dt)
        try:
            day = self._st.xs(ts, level=0)
            present = day["is_st"].reindex(syms).fillna(False)
        except KeyError:
            present = pd.Series(False, index=syms)
        return present.astype(bool)

    def is_st(self, dt: date, sym: str) -> bool:
        return bool(self.st_mask(dt, [sym]).iloc[0])

    def suspended_mask(self, dt: date, syms: list[str]) -> pd.Series:
        if self._price_view is None:
            return pd.Series(False, index=syms)
        df = self._price_view.slice_eod(dt, syms)
        # volume == 0 OR amount == 0 → suspended (proxy)
        v = df["volume"].reindex(syms).fillna(0)
        a = df["amount"].reindex(syms).fillna(0)
        return ((v == 0) | (a == 0)).astype(bool)

    def is_suspended(self, dt: date, sym: str) -> bool:
        return bool(self.suspended_mask(dt, [sym]).iloc[0])

    def listing_date(self, sym: str) -> date:
        return self._lifecycle.loc[sym, "listing_date"]

    def delisting_date(self, sym: str) -> date | None:
        d = self._lifecycle.loc[sym, "delisting_date"]
        return None if pd.isna(d) else d

    def is_newly_listed(self, dt: date, sym: str, n_days: int = 60) -> bool:
        ld = self.listing_date(sym)
        return (dt - ld).days < n_days

    def board_of(self, sym: str) -> str:
        return self._lifecycle.loc[sym, "board"]

    def _resolve_limit_pct(self, dt: date, board: str, is_st: bool) -> float:
        if is_st:
            return 0.05
        if board == "chinext" or board == "star":
            return 0.20 if dt >= CHINEXT_LIMIT_REGIME_CHANGE else 0.10
        if board == "bse":
            return 0.30
        return 0.10

    def limit_pct(self, dt: date, sym: str) -> float:
        try:
            board = self.board_of(sym)
        except KeyError:
            board = "main"
        return self._resolve_limit_pct(dt, board, self.is_st(dt, sym))
```

- [ ] **Step 4: Run — pass**

- [ ] **Step 5: Commit**

```bash
git add src/research/backtest/tradability.py tests/research/backtest/test_tradability.py
git commit -m "feat(backtest): add TradabilityProvider with board-aware limit pct"
```

---

## Task 7: TradabilityMask + ExecutionPolicy

**Files:**
- Create: `src/research/backtest/filters.py`
- Create: `tests/research/backtest/test_filters.py`

- [ ] **Step 1: Failing test**

```python
from datetime import date
import pandas as pd
import pytest
from research.backtest.filters import TradabilityMask, ExecutionPolicy
from research.backtest.config import FilterConfig


def test_can_buy_blocks_limit_up_at_open(price_view, tradability_provider, calendar):
    cfg = FilterConfig(block_st=True, block_suspended=True, block_limit_up_at_buy=True,
                        block_limit_down_at_sell=True, cooldown_days_after_unsuspend=1,
                        newly_listed_days=60, stale_position_days_max=5)
    mask = TradabilityMask(price_view, tradability_provider, cfg, calendar)
    # Find a stock that gapped up >9.9% on 2024-06-28's open
    syms = ["SH600000", "SZ000001"]
    can_buy = mask.can_buy(date(2024, 6, 28), syms)
    assert isinstance(can_buy, pd.Series)


def test_can_sell_blocks_t1_lock(price_view, tradability_provider, calendar, account_with_t1_lock):
    cfg = FilterConfig(block_st=True, block_suspended=True, block_limit_up_at_buy=True,
                        block_limit_down_at_sell=True, cooldown_days_after_unsuspend=1,
                        newly_listed_days=60, stale_position_days_max=5)
    mask = TradabilityMask(price_view, tradability_provider, cfg, calendar)
    # Stock bought yesterday → can_sell today = False
    can_sell = mask.can_sell(date(2024, 6, 28), ["SH600000"], account_with_t1_lock)
    assert can_sell.loc["SH600000"] == False


def test_execution_policy_defaults():
    p = ExecutionPolicy()
    assert p.blocked_buy == "drop"
    assert p.blocked_sell == "carry_over_n_days"
    assert p.blocked_sell_max_carry_days == 5
    assert p.capital_shortage == "pro_rata"
    assert p.lot_residual == "floor"
    assert p.nan_factor == "exclude_from_pool"
```

- [ ] **Step 2: Run — fail**

- [ ] **Step 3: Implement `filters.py`**

```python
"""TradabilityMask + ExecutionPolicy."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

import pandas as pd

from research.backtest.calendar import TradeCalendar
from research.backtest.config import FilterConfig
from research.backtest.data_view import PriceView
from research.backtest.tradability import TradabilityProvider


@dataclass(frozen=True)
class ExecutionPolicy:
    blocked_buy: Literal["drop", "carry_over_n_days"] = "drop"
    blocked_sell: Literal["carry_over_n_days"] = "carry_over_n_days"
    blocked_sell_max_carry_days: int = 5
    capital_shortage: Literal["pro_rata", "drop_smallest"] = "pro_rata"
    lot_residual: Literal["floor"] = "floor"
    nan_factor: Literal["exclude_from_pool"] = "exclude_from_pool"


@dataclass(frozen=True)
class TradabilityMask:
    view: PriceView
    provider: TradabilityProvider
    config: FilterConfig
    calendar: TradeCalendar

    def can_buy(self, exec_date: date, symbols: list[str]) -> pd.Series:
        syms = list(symbols)
        df = self.view.slice_eod(exec_date, syms)
        prev_dt = self.calendar.add_trading_days(exec_date, -1)
        prev = self.view.slice_eod(prev_dt, syms)

        opens = df["open"].reindex(syms).astype(float)
        prev_close = prev["close"].reindex(syms).astype(float)

        # Limit-up at open: open >= prev_close * (1 + limit_pct - eps)
        limit_pcts = pd.Series(
            [self.provider.limit_pct(exec_date, s) for s in syms], index=syms
        )
        eps = 0.001
        gapped_up = opens >= prev_close * (1 + limit_pcts - eps)

        st = self.provider.st_mask(exec_date, syms)
        suspended = self.provider.suspended_mask(exec_date, syms)
        newly_listed = pd.Series(
            [self.provider.is_newly_listed(exec_date, s, self.config.newly_listed_days) for s in syms],
            index=syms,
        )
        # Cooldown: was_suspended yesterday, not today
        was_suspended_y = self.provider.suspended_mask(prev_dt, syms)
        cooldown = was_suspended_y & ~suspended

        ok = pd.Series(True, index=syms)
        if self.config.block_st:
            ok &= ~st
        if self.config.block_suspended:
            ok &= ~suspended
        if self.config.block_limit_up_at_buy:
            ok &= ~gapped_up
        ok &= ~newly_listed
        ok &= ~cooldown
        return ok

    def can_sell(self, exec_date: date, symbols: list[str], account) -> pd.Series:
        syms = list(symbols)
        df = self.view.slice_eod(exec_date, syms)
        prev_dt = self.calendar.add_trading_days(exec_date, -1)
        prev = self.view.slice_eod(prev_dt, syms)

        opens = df["open"].reindex(syms).astype(float)
        prev_close = prev["close"].reindex(syms).astype(float)
        limit_pcts = pd.Series(
            [self.provider.limit_pct(exec_date, s) for s in syms], index=syms
        )
        eps = 0.001
        gapped_down = opens <= prev_close * (1 - limit_pcts + eps)

        suspended = self.provider.suspended_mask(exec_date, syms)
        # T+1 lock from account
        t1_locked = pd.Series(
            [account.available_shares(s, exec_date) == 0 and s in account.held_symbols() for s in syms],
            index=syms,
        )

        ok = pd.Series(True, index=syms)
        if self.config.block_suspended:
            ok &= ~suspended
        if self.config.block_limit_down_at_sell:
            ok &= ~gapped_down
        ok &= ~t1_locked
        return ok
```

- [ ] **Step 4: Add fixtures to `conftest.py`** (synthetic price view + provider for tests that don't need DB)

- [ ] **Step 5: Run — pass**

- [ ] **Step 6: Commit**

```bash
git add src/research/backtest/filters.py tests/research/backtest/test_filters.py \
        tests/research/backtest/conftest.py
git commit -m "feat(backtest): add TradabilityMask + ExecutionPolicy"
```

---

## Task 8: CostModel

**Files:**
- Create: `src/research/backtest/cost.py`
- Create: `tests/research/backtest/test_cost.py`

- [ ] **Step 1: Failing test**

```python
from datetime import date
import pytest
from research.backtest.cost import compute_cost
from research.backtest.config import CostConfig, StampScheduleEntry


@pytest.fixture
def cost_cfg():
    return CostConfig(
        stamp_schedule=(
            StampScheduleEntry(date(2015, 1, 1), date(2023, 8, 27), 10.0),
            StampScheduleEntry(date(2023, 8, 28), date(9999, 12, 31), 5.0),
        ),
        commission_bps=3.0, slippage_bps=5.0, min_commission_cny=5.0,
    )


def test_buy_cost_pre_2023_no_stamp(cost_cfg):
    # buy 1000 shares at 10 CNY → notional 10000
    # commission 3bps + slippage 5bps = 8bps × 10000 = 8 CNY
    cost = compute_cost("buy", price=10.0, shares=1000, dt=date(2020, 1, 1), config=cost_cfg)
    assert cost == pytest.approx(8.0)


def test_sell_cost_pre_2023_with_10bps_stamp(cost_cfg):
    # sell 1000 shares at 10 CNY → 10000 notional
    # 10bps stamp + 3bps commission + 5bps slippage = 18bps × 10000 = 18 CNY
    cost = compute_cost("sell", price=10.0, shares=1000, dt=date(2020, 1, 1), config=cost_cfg)
    assert cost == pytest.approx(18.0)


def test_sell_cost_post_2023_with_5bps_stamp(cost_cfg):
    # sell post 2023-08-28: 5bps stamp + 3 + 5 = 13bps × 10000 = 13
    cost = compute_cost("sell", price=10.0, shares=1000, dt=date(2024, 1, 1), config=cost_cfg)
    assert cost == pytest.approx(13.0)


def test_min_commission_floor(cost_cfg):
    # buy 100 shares at 1 CNY → notional 100; 8bps = 0.08; commission portion alone is 0.03
    # min_commission 5 CNY floor: total = 5 (stamp) + 0 + slippage(0.05) = ~5.05
    # Actually: stamp doesn't apply on buy; commission floor: max(commission_calc, min) = 5
    cost = compute_cost("buy", price=1.0, shares=100, dt=date(2020, 1, 1), config=cost_cfg)
    # commission floor at 5; slippage 5bps × 100 = 0.05
    assert cost == pytest.approx(5.05)
```

- [ ] **Step 2: Run — fail**

- [ ] **Step 3: Implement `cost.py`**

```python
"""CostModel — pure function compute_cost."""
from __future__ import annotations
from datetime import date
from typing import Literal

from research.backtest.config import CostConfig


def compute_cost(side: Literal["buy", "sell"], price: float, shares: int,
                 dt: date, config: CostConfig) -> float:
    notional = price * shares
    commission = max(notional * config.commission_bps / 1e4, config.min_commission_cny)
    slippage = notional * config.slippage_bps / 1e4
    stamp = notional * config.stamp_bps_at(dt) / 1e4 if side == "sell" else 0.0
    return commission + slippage + stamp
```

- [ ] **Step 4: Run — pass**

- [ ] **Step 5: Commit**

```bash
git add src/research/backtest/cost.py tests/research/backtest/test_cost.py
git commit -m "feat(backtest): add CostModel with time-varying stamp schedule"
```

---

## Task 9: Account (with T+1 lock + pending_cash)

**Files:**
- Create: `src/research/backtest/account.py`
- Create: `tests/research/backtest/test_account.py`

- [ ] **Step 1: Failing test**

```python
from datetime import date
import pandas as pd
import pytest
from research.backtest.account import Account, Fill


def test_buy_locks_shares_until_next_day():
    acc = Account(initial_capital=1_000_000)
    acc.transact(Fill(side="buy", date=date(2024, 6, 28), symbol="SH600000",
                       shares=1000, fill_price=10.0, cost_cny=10.0,
                       reason="target_diff"))
    assert acc.cash == 1_000_000 - 10_000 - 10
    assert acc.available_shares("SH600000", date(2024, 6, 28)) == 0
    assert acc.available_shares("SH600000", date(2024, 7, 1)) == 1000


def test_sell_proceeds_go_to_pending_cash_then_settle():
    acc = Account(initial_capital=100_000)
    acc.transact(Fill(side="buy", date=date(2024, 6, 28), symbol="SH600000",
                       shares=1000, fill_price=10.0, cost_cny=10.0,
                       reason="target_diff"))
    # Next day: sell
    acc.settle_cash(on_date=date(2024, 7, 1))
    acc.transact(Fill(side="sell", date=date(2024, 7, 1), symbol="SH600000",
                       shares=1000, fill_price=11.0, cost_cny=15.0,
                       reason="target_diff"))
    assert acc.cash == 100_000 - 10_000 - 10
    assert acc.pending_cash == 11_000 - 15
    # Settle next day
    acc.settle_cash(on_date=date(2024, 7, 2))
    assert acc.pending_cash == 0
    assert acc.cash == pytest.approx(100_000 - 10_000 - 10 + 11_000 - 15)


def test_mark_to_market_uses_close_prices():
    acc = Account(initial_capital=100_000)
    acc.transact(Fill(side="buy", date=date(2024, 6, 28), symbol="SH600000",
                       shares=1000, fill_price=10.0, cost_cny=0.0,
                       reason="target_diff"))
    prices = pd.Series({"SH600000": 12.0})
    equity = acc.mark_to_market(date(2024, 7, 1), prices)
    assert equity == pytest.approx(100_000 - 10_000 + 12_000)


def test_force_liquidate_delisted_credits_cash_immediately():
    acc = Account(initial_capital=100_000)
    acc.transact(Fill(side="buy", date=date(2024, 6, 28), symbol="SH600000",
                       shares=1000, fill_price=10.0, cost_cny=0.0,
                       reason="target_diff"))
    acc.transact(Fill(side="sell", date=date(2024, 7, 1), symbol="SH600000",
                       shares=1000, fill_price=10.0, cost_cny=0.0,
                       reason="delisted_writeoff"))
    # delisted_writeoff goes to cash directly, no T+1
    assert acc.cash == pytest.approx(100_000 - 10_000 + 10_000)
    assert acc.pending_cash == 0
```

- [ ] **Step 2: Run — fail**

- [ ] **Step 3: Implement `account.py`**

```python
"""Account — cash + positions with strict T+1 settlement."""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

import pandas as pd


@dataclass
class Position:
    symbol: str
    shares: int = 0
    locked_until: date | None = None    # shares not sellable before this date
    avg_cost: float = 0.0
    last_close: float = 0.0


@dataclass(frozen=True)
class Fill:
    side: Literal["buy", "sell"]
    date: date
    symbol: str
    shares: int
    fill_price: float
    cost_cny: float
    reason: str


WRITEOFF_REASONS = {"delisted_writeoff"}


class Account:
    def __init__(self, initial_capital: float):
        self._cash = float(initial_capital)
        self._pending: dict[date, float] = defaultdict(float)   # date → cash to be released next trading day
        self._positions: dict[str, Position] = {}

    @property
    def cash(self) -> float:
        return self._cash

    @property
    def pending_cash(self) -> float:
        return sum(self._pending.values())

    def settle_cash(self, on_date: date) -> None:
        """Release pending cash from sells executed on date < on_date."""
        to_settle = [d for d in self._pending if d < on_date]
        for d in to_settle:
            self._cash += self._pending.pop(d)

    def held_symbols(self) -> set[str]:
        return {s for s, p in self._positions.items() if p.shares > 0}

    def available_shares(self, sym: str, exec_date: date) -> int:
        p = self._positions.get(sym)
        if p is None or p.shares == 0:
            return 0
        if p.locked_until is not None and exec_date < p.locked_until:
            return 0
        return p.shares

    def transact(self, fill: Fill) -> None:
        p = self._positions.setdefault(fill.symbol, Position(symbol=fill.symbol))
        if fill.side == "buy":
            new_total = p.shares + fill.shares
            p.avg_cost = (p.avg_cost * p.shares + fill.fill_price * fill.shares) / max(new_total, 1)
            p.shares = new_total
            p.locked_until = self._next_day(fill.date)
            self._cash -= fill.fill_price * fill.shares + fill.cost_cny
        else:  # sell
            p.shares -= fill.shares
            proceeds = fill.fill_price * fill.shares - fill.cost_cny
            if fill.reason in WRITEOFF_REASONS:
                # Writeoff: no real settlement, cash credits immediately
                self._cash += proceeds
            else:
                self._pending[fill.date] += proceeds
            if p.shares == 0:
                p.locked_until = None
                p.avg_cost = 0.0

    def mark_to_market(self, dt: date, prices: pd.Series) -> float:
        for sym, p in self._positions.items():
            if sym in prices.index and pd.notna(prices.loc[sym]):
                p.last_close = float(prices.loc[sym])
        holdings = sum(p.shares * p.last_close for p in self._positions.values())
        return self._cash + self.pending_cash + holdings

    def positions_snapshot(self, dt: date) -> pd.DataFrame:
        rows = [
            dict(date=dt, symbol=s, shares=p.shares,
                 locked_until=p.locked_until,
                 mkt_value=p.shares * p.last_close,
                 avg_cost=p.avg_cost)
            for s, p in self._positions.items() if p.shares > 0
        ]
        return pd.DataFrame(rows)

    def _next_day(self, dt: date) -> date:
        # Account doesn't know calendar; uses calendar-day +1 as a conservative lock.
        # Engine ensures settle_cash runs at the start of every actual trading day,
        # which clears locked_until naturally.
        from datetime import timedelta
        return dt + timedelta(days=1)
```

- [ ] **Step 4: Run — pass**

- [ ] **Step 5: Commit**

```bash
git add src/research/backtest/account.py tests/research/backtest/test_account.py
git commit -m "feat(backtest): add Account with T+1 share lock + pending cash"
```

---

## Task 10: Strategy (TopKLongOnly + QuintilePortfolio)

**Files:**
- Create: `src/research/backtest/strategy.py`
- Create: `tests/research/backtest/test_strategy.py`

- [ ] **Step 1: Failing test**

```python
from datetime import date
import numpy as np
import pandas as pd
import pytest
from research.backtest.strategy import TopKLongOnly, QuintilePortfolio


def test_topk_returns_k_equal_weighted_excluding_nan():
    factor = pd.Series({"A": 1.0, "B": 2.0, "C": np.nan, "D": 3.0, "E": 4.0})
    universe = {"A", "B", "C", "D", "E"}
    s = TopKLongOnly(holdings_n=3, max_single_weight=0.5)
    target = s.target_weights(date(2024, 6, 28), factor, universe, price_view=None)
    # NaN excluded → top 3 of {A=1, B=2, D=3, E=4} = {B, D, E}
    assert set(target.index) == {"B", "D", "E"}
    for w in target.values:
        assert w == pytest.approx(1/3)


def test_topk_max_single_weight_clamps():
    factor = pd.Series({"A": 1.0, "B": 2.0})
    universe = {"A", "B"}
    s = TopKLongOnly(holdings_n=2, max_single_weight=0.4)
    target = s.target_weights(date(2024, 6, 28), factor, universe, price_view=None)
    # Equal weight 0.5 each, but max=0.4 → 0.4 each, rest stays as cash
    assert target.loc["A"] == pytest.approx(0.4)
    assert target.loc["B"] == pytest.approx(0.4)


def test_quintile_partitions_universe():
    factor = pd.Series({f"S{i}": float(i) for i in range(100)})
    universe = set(factor.index)
    qp = QuintilePortfolio()
    target_q1 = qp.target_for_quintile(0, factor, universe, price_view=None)
    target_q5 = qp.target_for_quintile(4, factor, universe, price_view=None)
    assert len(target_q1) == 20   # 100 / 5
    assert len(target_q5) == 20
    assert set(target_q1.index).isdisjoint(set(target_q5.index))


def test_strategy_filters_universe_intersection():
    # factor has more symbols than universe; strategy uses intersection
    factor = pd.Series({"A": 1.0, "B": 2.0, "C": 3.0, "X": 99.0})
    universe = {"A", "B", "C"}   # X not in universe
    s = TopKLongOnly(holdings_n=2, max_single_weight=0.5)
    target = s.target_weights(date(2024, 6, 28), factor, universe, price_view=None)
    assert "X" not in target.index
    assert set(target.index) == {"B", "C"}
```

- [ ] **Step 2: Run — fail**

- [ ] **Step 3: Implement `strategy.py`**

```python
"""Strategy ABCs and concrete classes."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd


class Strategy(ABC):
    @abstractmethod
    def target_weights(self, decision_date: date, factor_values: pd.Series,
                       universe: set[str], price_view) -> pd.Series:
        ...


@dataclass(frozen=True)
class TopKLongOnly(Strategy):
    holdings_n: int
    max_single_weight: float

    def target_weights(self, decision_date, factor_values, universe, price_view):
        eligible = factor_values.dropna()
        eligible = eligible[eligible.index.isin(universe)]
        if eligible.empty:
            return pd.Series(dtype=float)
        ranked = eligible.sort_values(ascending=False)
        top = ranked.head(self.holdings_n)
        # Equal weight, clamped to max_single_weight
        ew = 1.0 / len(top)
        weight = min(ew, self.max_single_weight)
        return pd.Series(weight, index=top.index)


@dataclass(frozen=True)
class QuintilePortfolio(Strategy):
    """Five sub-portfolios. target_for_quintile(q) returns equal-weight on q-th quintile.
       q=0 is lowest factor, q=4 is highest."""
    n_quintiles: int = 5

    def target_weights(self, decision_date, factor_values, universe, price_view):
        # Default: top quintile (q=4)
        return self.target_for_quintile(self.n_quintiles - 1, factor_values, universe, price_view)

    def target_for_quintile(self, q: int, factor_values: pd.Series,
                             universe: set[str], price_view) -> pd.Series:
        eligible = factor_values.dropna()
        eligible = eligible[eligible.index.isin(universe)]
        if eligible.empty:
            return pd.Series(dtype=float)
        ranked = eligible.sort_values(ascending=False)
        n = len(ranked)
        size = n // self.n_quintiles
        # q=0 is lowest → bottom of ranked descending; q=4 is highest → top
        # In descending sort: index 0..size-1 = highest, last size = lowest
        idx_top = self.n_quintiles - 1 - q   # convert q-from-bottom to slot from top
        start = idx_top * size
        end = start + size
        sliced = ranked.iloc[start:end]
        return pd.Series(1.0 / len(sliced), index=sliced.index)
```

- [ ] **Step 4: Run — pass**

- [ ] **Step 5: Commit**

```bash
git add src/research/backtest/strategy.py tests/research/backtest/test_strategy.py
git commit -m "feat(backtest): add TopKLongOnly + QuintilePortfolio strategies"
```

---

## Task 11: Executor

**Files:**
- Create: `src/research/backtest/executor.py`
- Create: `tests/research/backtest/test_executor.py`

- [ ] **Step 1: Failing test**

Cover (a) target → diff → orders, (b) lot floor, (c) blocked buy → cash, (d) blocked sell → carry over, (e) capital shortage pro-rata, (f) intraday netting flag.

```python
from datetime import date
import pandas as pd
import pytest
from research.backtest.executor import Executor
from research.backtest.account import Account, Fill
from research.backtest.filters import ExecutionPolicy


def test_target_diff_generates_correct_buy(mock_view, mock_mask, mock_cost_cfg):
    acc = Account(initial_capital=100_000)
    target = pd.Series({"SH600000": 0.5})  # 50% target = 50k → 5000 shares at 10 CNY
    e = Executor()
    fills = e.execute(date(2024, 6, 28), target, acc, mock_mask, mock_view, mock_cost_cfg,
                       ExecutionPolicy(), allow_intraday_netting=False)
    assert any(f.side == "buy" and f.symbol == "SH600000" for f in fills)


def test_lot_floor_rounds_to_100s(mock_view, mock_mask, mock_cost_cfg):
    acc = Account(initial_capital=10_000)
    target = pd.Series({"SH600000": 1.0})   # full 10k at 10 CNY → 1000 shares (10 lots)
    e = Executor()
    fills = e.execute(date(2024, 6, 28), target, acc, mock_mask, mock_view, mock_cost_cfg,
                       ExecutionPolicy(), allow_intraday_netting=False)
    f = next(f for f in fills if f.side == "buy")
    assert f.shares % 100 == 0


def test_blocked_buy_drops_to_cash(mock_view, mock_mask_block_all, mock_cost_cfg):
    acc = Account(initial_capital=100_000)
    target = pd.Series({"SH600000": 1.0})
    e = Executor()
    fills = e.execute(date(2024, 6, 28), target, acc, mock_mask_block_all,
                       mock_view, mock_cost_cfg, ExecutionPolicy(),
                       allow_intraday_netting=False)
    # No buy executed; logged blocked
    assert all(f.reason.startswith("blocked_buy") or f.side == "sell" for f in fills)


def test_intraday_netting_false_uses_only_cash(mock_view, mock_mask, mock_cost_cfg):
    acc = Account(initial_capital=10_000)
    # Pre-load with 1 sell to generate pending_cash
    acc.transact(Fill(side="buy", date=date(2024, 6, 27), symbol="SH600036",
                       shares=1000, fill_price=10.0, cost_cny=0,
                       reason="target_diff"))
    # Sell on 6/28 should produce pending_cash of ~10k; with intraday=False, can't reuse
    target = pd.Series({"SH600036": 0.0, "SH600000": 1.0})
    e = Executor()
    fills = e.execute(date(2024, 6, 28), target, acc, mock_mask, mock_view, mock_cost_cfg,
                       ExecutionPolicy(), allow_intraday_netting=False)
    buy_notional = sum(f.fill_price * f.shares for f in fills if f.side == "buy")
    assert buy_notional <= acc.cash + 1   # only original cash spent; pending excluded
```

- [ ] **Step 2: Run — fail**

- [ ] **Step 3: Implement `executor.py`**

```python
"""Executor — diff target vs current → orders → mask → cost → fills."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date

import math
import pandas as pd

from research.backtest.account import Account, Fill
from research.backtest.config import CostConfig
from research.backtest.cost import compute_cost
from research.backtest.data_view import PriceView
from research.backtest.filters import ExecutionPolicy, TradabilityMask


LOT_SIZE = 100


@dataclass
class Executor:
    def execute(self, exec_date: date, target: pd.Series,
                account: Account, mask: TradabilityMask, view: PriceView,
                cost_cfg: CostConfig, policy: ExecutionPolicy,
                allow_intraday_netting: bool) -> list[Fill]:
        fills: list[Fill] = []

        # 1. Pull execution prices (open by default)
        all_syms = set(target.index) | account.held_symbols()
        prices_df = view.slice_eod(exec_date, list(all_syms))
        prices = prices_df["open"].reindex(list(all_syms)).astype(float)

        # 2. Compute desired shares per symbol; floor to lot
        equity_estimate = account.cash + account.pending_cash + sum(
            account._positions[s].shares * prices.get(s, account._positions[s].last_close)
            for s in account.held_symbols()
        )
        desired_shares: dict[str, int] = {}
        for sym, w in target.items():
            if sym not in prices.index or pd.isna(prices.loc[sym]) or prices.loc[sym] <= 0:
                continue
            target_value = w * equity_estimate
            shares = int(math.floor(target_value / prices.loc[sym] / LOT_SIZE)) * LOT_SIZE
            if shares > 0:
                desired_shares[sym] = shares

        # 3. Diff: sells first, then buys
        sells, buys = [], []
        for sym in account.held_symbols():
            current = account._positions[sym].shares
            want = desired_shares.get(sym, 0)
            if want < current:
                sells.append((sym, current - want))
        for sym, want in desired_shares.items():
            current = account._positions.get(sym, type("p",(),{"shares":0}))().shares if sym not in account._positions else account._positions[sym].shares
            if want > current:
                buys.append((sym, want - current))

        # 4. Sell pass — apply mask
        sell_syms = [s for s, _ in sells]
        can_sell = mask.can_sell(exec_date, sell_syms, account)
        for sym, qty in sells:
            if not can_sell.loc[sym]:
                fills.append(Fill(side="sell", date=exec_date, symbol=sym, shares=0,
                                   fill_price=float(prices.get(sym, 0)),
                                   cost_cny=0.0, reason=f"blocked_sell"))
                continue
            available = account.available_shares(sym, exec_date)
            actual = min(qty, available)
            if actual <= 0:
                continue
            price = float(prices.loc[sym])
            cost = compute_cost("sell", price, actual, exec_date, cost_cfg)
            fills.append(Fill(side="sell", date=exec_date, symbol=sym, shares=actual,
                               fill_price=price, cost_cny=cost, reason="target_diff"))
            account.transact(fills[-1])

        # 5. Compute buy budget
        if allow_intraday_netting:
            same_day_proceeds = sum(f.fill_price * f.shares - f.cost_cny
                                     for f in fills if f.side == "sell" and f.shares > 0)
            buy_budget = account.cash + same_day_proceeds
        else:
            buy_budget = account.cash

        # 6. Buy pass — apply mask + budget
        buy_syms = [s for s, _ in buys]
        can_buy = mask.can_buy(exec_date, buy_syms)
        ok_buys = [(s, q) for s, q in buys if can_buy.loc[s]]
        # Pro-rata if over budget
        notional = sum(prices.loc[s] * q for s, q in ok_buys)
        scale = 1.0
        if notional > buy_budget and policy.capital_shortage == "pro_rata" and notional > 0:
            scale = buy_budget / notional
        for sym, qty in ok_buys:
            scaled = int(math.floor(qty * scale / LOT_SIZE)) * LOT_SIZE
            if scaled <= 0:
                continue
            price = float(prices.loc[sym])
            cost = compute_cost("buy", price, scaled, exec_date, cost_cfg)
            fills.append(Fill(side="buy", date=exec_date, symbol=sym, shares=scaled,
                               fill_price=price, cost_cny=cost, reason="target_diff"))
            account.transact(fills[-1])

        # 7. Log blocked buys
        for sym, _ in buys:
            if not can_buy.loc[sym]:
                fills.append(Fill(side="buy", date=exec_date, symbol=sym, shares=0,
                                   fill_price=float(prices.get(sym, 0)),
                                   cost_cny=0.0, reason=f"blocked_buy"))
        return fills
```

- [ ] **Step 4: Add fixtures `mock_view`, `mock_mask`, `mock_mask_block_all`, `mock_cost_cfg` to `conftest.py`**

- [ ] **Step 5: Run — pass**

- [ ] **Step 6: Commit**

```bash
git add src/research/backtest/executor.py tests/research/backtest/test_executor.py \
        tests/research/backtest/conftest.py
git commit -m "feat(backtest): add Executor with mask + lot floor + capital pro-rata"
```

---

## Task 12: Engine state machine + reconciliation

**Files:**
- Create: `src/research/backtest/engine.py`
- Create: `tests/research/backtest/test_engine.py`
- Create: `tests/research/backtest/test_reconciliation.py`
- Create: `tests/research/backtest/test_information_set.py`

- [ ] **Step 1: Failing test (information-set invariant)**

`test_information_set.py`:
```python
from datetime import date
from research.backtest.engine import Engine


def test_decision_does_not_use_next_day_data(small_engine, factor_panel):
    # Run engine, then poison next-day factor values; result should be unchanged
    result1 = small_engine.run(date(2024, 6, 24), date(2024, 6, 28))
    # Poison: rewrite factor at 2024-06-28 to crazy values
    poisoned = factor_panel.copy()
    poisoned.loc[date(2024, 6, 28)] *= 1000
    small_engine.factor_loader._panel = poisoned
    result2 = small_engine.run(date(2024, 6, 24), date(2024, 6, 27))   # only up to 6/27
    # Decisions on 6/24 should be identical (since they use ≤6/24 info)
    assert result1.equity_curve.loc[date(2024, 6, 25), "total_equity"] == \
           result2.equity_curve.loc[date(2024, 6, 25), "total_equity"]
```

- [ ] **Step 2: Failing test (reconciliation)**

`test_reconciliation.py`:
```python
from datetime import date
from research.backtest.engine import Engine


def test_reconciliation_invariant_holds_across_run(small_engine):
    result = small_engine.run(date(2024, 6, 24), date(2024, 6, 28))
    assert result.metrics["reconciliation"]["invariant_violations"] == 0
    assert result.metrics["reconciliation"]["max_violation_bps"] < 5.0
```

- [ ] **Step 3: Implement `engine.py`**

```python
"""Engine — state machine main loop + reconciliation invariant."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

from research.backtest.account import Account, Fill
from research.backtest.calendar import TradeCalendar
from research.backtest.config import BacktestConfig
from research.backtest.data_view import PriceView
from research.backtest.executor import Executor
from research.backtest.filters import ExecutionPolicy, TradabilityMask
from research.backtest.strategy import Strategy, TopKLongOnly, QuintilePortfolio


@dataclass
class BacktestResult:
    equity_curve: pd.DataFrame
    quintile_curves: list[pd.DataFrame]
    trades: pd.DataFrame
    positions: pd.DataFrame
    metrics: dict
    config_snapshot: dict
    runtime_meta: dict


class Engine:
    def __init__(self, config: BacktestConfig, calendar: TradeCalendar,
                 view: PriceView, mask: TradabilityMask,
                 main_strategy: Strategy, quintile_strategy: QuintilePortfolio,
                 factor_loader, executor: Executor | None = None):
        self.config = config
        self.calendar = calendar
        self.view = view
        self.mask = mask
        self.main_strategy = main_strategy
        self.quintile_strategy = quintile_strategy
        self.factor_loader = factor_loader
        self.executor = executor or Executor()

    def run(self, start: date, end: date) -> BacktestResult:
        days = self.calendar.trading_days(start, end)
        rebalance_set = set(self.calendar.rebalance_schedule(
            start, end, self.config.rebalance.freq_days, self.config.rebalance.anchor
        ))

        main_acc = Account(self.config.initial_capital)
        q_accs = [Account(self.config.initial_capital) for _ in range(5)]
        all_accounts = [main_acc] + q_accs

        equity_rows, trade_rows, position_rows = [], [], []
        recon_violations = 0
        recon_max_bps = 0.0
        prev_equity = {id(a): self.config.initial_capital for a in all_accounts}

        for i, dt in enumerate(days):
            for a in all_accounts:
                a.settle_cash(dt)

            # Mark to close-of-dt
            held = set().union(*(a.held_symbols() for a in all_accounts))
            prices_eod = self.view.slice_eod(dt, list(held)) if held else pd.DataFrame()
            close = prices_eod["close"] if "close" in prices_eod.columns else pd.Series(dtype=float)
            for a in all_accounts:
                eq = a.mark_to_market(dt, close)
                # Reconcile
                bps = abs(eq - prev_equity[id(a)]) / max(prev_equity[id(a)], 1) * 1e4
                if bps > 50.0:
                    raise RuntimeError(f"Reconciliation breach: {dt} {bps:.1f}bps")
                if bps > 5.0:
                    recon_violations += 1
                recon_max_bps = max(recon_max_bps, bps)
                prev_equity[id(a)] = eq

            # Decide on rebalance day
            main_target = q_targets = None
            if dt in rebalance_set:
                factor_vals = self.factor_loader.at(dt)
                universe = self.calendar.universe_at(dt)
                main_target = self.main_strategy.target_weights(dt, factor_vals, universe, self.view)
                q_targets = [
                    self.quintile_strategy.target_for_quintile(q, factor_vals, universe, self.view)
                    for q in range(5)
                ]

            # Execute on next_dt
            next_dt = days[i + 1] if i + 1 < len(days) else None
            if next_dt is not None:
                if main_target is not None:
                    fills = self.executor.execute(
                        next_dt, main_target, main_acc, self.mask, self.view,
                        self.config.cost, ExecutionPolicy(),
                        allow_intraday_netting=self.config.capital.allow_intraday_netting,
                    )
                    trade_rows.extend(self._fill_to_row(f, "main") for f in fills)
                if q_targets is not None:
                    for q, qa in enumerate(q_accs):
                        qfills = self.executor.execute(
                            next_dt, q_targets[q], qa, self.mask, self.view,
                            self.config.cost,
                            ExecutionPolicy(blocked_buy="drop"),
                            allow_intraday_netting=True,   # Quintile = gross
                        )
                        trade_rows.extend(self._fill_to_row(f, f"q{q+1}") for f in qfills)

            equity_rows.append(dict(
                date=dt,
                total_equity=main_acc.mark_to_market(dt, close),
                cash=main_acc.cash,
                pending_cash=main_acc.pending_cash,
                **{f"q{q+1}_equity": qa.mark_to_market(dt, close) for q, qa in enumerate(q_accs)},
            ))
            position_rows.extend(
                main_acc.positions_snapshot(dt).to_dict("records")
            )

        equity_curve = pd.DataFrame(equity_rows).set_index("date")
        # Drawdown
        peak = equity_curve["total_equity"].cummax()
        equity_curve["drawdown"] = equity_curve["total_equity"] / peak - 1
        trades = pd.DataFrame(trade_rows)
        positions = pd.DataFrame(position_rows)

        metrics = self._compute_metrics(equity_curve, trades)
        metrics["reconciliation"] = dict(
            invariant_violations=recon_violations,
            max_violation_bps=recon_max_bps,
        )
        return BacktestResult(
            equity_curve=equity_curve,
            quintile_curves=[],   # populated by reporter from equity_curve
            trades=trades,
            positions=positions,
            metrics=metrics,
            config_snapshot=self._config_to_dict(),
            runtime_meta=dict(
                snapshot_ts=str(self.view.snapshot_ts),
                signal_recompute=self.config.signal_recompute,
            ),
        )

    @staticmethod
    def _fill_to_row(f: Fill, account_label: str) -> dict:
        return dict(
            account=account_label, date=f.date, symbol=f.symbol, side=f.side,
            shares=f.shares, fill_price=f.fill_price, cost_cny=f.cost_cny,
            reason=f.reason,
        )

    def _compute_metrics(self, equity: pd.DataFrame, trades: pd.DataFrame) -> dict:
        ret = equity["total_equity"].pct_change().dropna()
        ann = ret.mean() * 252
        vol = ret.std() * (252 ** 0.5)
        sharpe = ann / vol if vol > 0 else 0.0
        max_dd = equity["drawdown"].min()
        return dict(
            full=dict(
                ann_return=float(ann), volatility=float(vol),
                sharpe=float(sharpe), max_dd=float(max_dd),
                n_days=len(equity),
            ),
        )

    def _config_to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self.config)
```

- [ ] **Step 4: Run — pass**

- [ ] **Step 5: Commit**

```bash
git add src/research/backtest/engine.py tests/research/backtest/test_engine.py \
        tests/research/backtest/test_reconciliation.py \
        tests/research/backtest/test_information_set.py
git commit -m "feat(backtest): add Engine state machine + reconciliation invariant"
```

---

## Task 13: Reporter (parquets + metrics + figs)

**Files:**
- Create: `src/research/backtest/reporter.py`
- Create: `tests/research/backtest/test_reporter.py`

- [ ] **Step 1: Failing test**

```python
from pathlib import Path
import pytest
from research.backtest.reporter import Reporter


def test_writes_4_parquets_and_metrics_yaml(small_result, tmp_path):
    Reporter().write(small_result, tmp_path)
    assert (tmp_path / "equity_curve.parquet").exists()
    assert (tmp_path / "trades.parquet").exists()
    assert (tmp_path / "positions.parquet").exists()
    assert (tmp_path / "metrics.yaml").exists()


def test_writes_figs(small_result, tmp_path):
    Reporter().write(small_result, tmp_path)
    figs_dir = tmp_path / "figs"
    for name in ["equity", "drawdown", "monthly_heatmap", "layer_decomp", "cost_drag"]:
        assert (figs_dir / f"{name}.png").exists()
```

- [ ] **Step 2: Implement `reporter.py`** (~200 LOC; matplotlib for figs; yaml for metrics)

```python
"""Reporter — write 4 parquets + metrics.yaml + figures."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yaml

from research.backtest.engine import BacktestResult


@dataclass
class Reporter:
    def write(self, result: BacktestResult, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        result.equity_curve.to_parquet(out_dir / "equity_curve.parquet")
        result.trades.to_parquet(out_dir / "trades.parquet")
        result.positions.to_parquet(out_dir / "positions.parquet")
        with open(out_dir / "metrics.yaml", "w") as f:
            yaml.safe_dump({
                "metrics": result.metrics,
                "config_snapshot": result.config_snapshot,
                "runtime_meta": result.runtime_meta,
            }, f, sort_keys=False, allow_unicode=True)
        figs_dir = out_dir / "figs"
        figs_dir.mkdir(exist_ok=True)
        self._plot_equity(result, figs_dir / "equity.png")
        self._plot_drawdown(result, figs_dir / "drawdown.png")
        self._plot_monthly_heatmap(result, figs_dir / "monthly_heatmap.png")
        self._plot_layer_decomp(result, figs_dir / "layer_decomp.png")
        self._plot_cost_drag(result, figs_dir / "cost_drag.png")
        self._plot_blocked(result, figs_dir / "blocked_trades.png")

    def _plot_equity(self, r: BacktestResult, p: Path):
        fig, ax = plt.subplots(figsize=(10, 4))
        r.equity_curve["total_equity"].plot(ax=ax)
        ax.set_title("Net Equity Curve")
        fig.savefig(p, dpi=100); plt.close(fig)

    def _plot_drawdown(self, r: BacktestResult, p: Path):
        fig, ax = plt.subplots(figsize=(10, 3))
        r.equity_curve["drawdown"].plot(ax=ax, color="red")
        ax.set_title("Drawdown"); ax.set_ylabel("DD")
        fig.savefig(p, dpi=100); plt.close(fig)

    def _plot_monthly_heatmap(self, r: BacktestResult, p: Path):
        ret = r.equity_curve["total_equity"].pct_change().dropna()
        monthly = ret.resample("M").apply(lambda s: (1+s).prod() - 1)
        if monthly.empty:
            fig = plt.figure(); fig.savefig(p); plt.close(fig); return
        pivot = monthly.to_frame("ret")
        pivot["year"] = pivot.index.year
        pivot["month"] = pivot.index.month
        hm = pivot.pivot(index="year", columns="month", values="ret")
        fig, ax = plt.subplots(figsize=(10, 4))
        im = ax.imshow(hm.values, cmap="RdYlGn", aspect="auto")
        ax.set_yticks(range(len(hm.index))); ax.set_yticklabels(hm.index)
        ax.set_xticks(range(12)); ax.set_xticklabels(range(1,13))
        plt.colorbar(im, ax=ax)
        fig.savefig(p, dpi=100); plt.close(fig)

    def _plot_layer_decomp(self, r: BacktestResult, p: Path):
        fig, ax = plt.subplots(figsize=(10, 4))
        for q in range(1, 6):
            col = f"q{q}_equity"
            if col in r.equity_curve.columns:
                r.equity_curve[col].plot(ax=ax, label=f"Q{q}")
        r.equity_curve["total_equity"].plot(ax=ax, label="Top-K", linewidth=2, color="black")
        ax.legend(); ax.set_title("Quintile decomposition + Top-K")
        fig.savefig(p, dpi=100); plt.close(fig)

    def _plot_cost_drag(self, r: BacktestResult, p: Path):
        fig, ax = plt.subplots(figsize=(10, 3))
        if not r.trades.empty:
            r.trades.groupby("date")["cost_cny"].sum().cumsum().plot(ax=ax)
        ax.set_title("Cumulative cost drag (CNY)")
        fig.savefig(p, dpi=100); plt.close(fig)

    def _plot_blocked(self, r: BacktestResult, p: Path):
        fig, ax = plt.subplots(figsize=(10, 3))
        if not r.trades.empty:
            blocked = r.trades[r.trades["reason"].str.startswith("blocked", na=False)]
            if not blocked.empty:
                blocked.groupby("date").size().plot(ax=ax, kind="bar")
        ax.set_title("Blocked trades per day")
        fig.savefig(p, dpi=100); plt.close(fig)
```

- [ ] **Step 3: Run — pass**

- [ ] **Step 4: Commit**

```bash
git add src/research/backtest/reporter.py tests/research/backtest/test_reporter.py
git commit -m "feat(backtest): add Reporter for parquets + metrics + figs"
```

---

## Task 14: Runner + CLI subcommand registration

**Files:**
- Create: `src/research/backtest/runner.py`
- Modify: `src/research/cli/main.py`

- [ ] **Step 1: Write `runner.py`**

```python
"""Runner — entry point called by both CLI and report subagent."""
from __future__ import annotations
from datetime import date
from pathlib import Path

import pandas as pd

from research.backtest.calendar import TradeCalendar
from research.backtest.config import BacktestConfig, load_default_config
from research.backtest.data_view import PriceView
from research.backtest.engine import Engine
from research.backtest.executor import Executor
from research.backtest.filters import TradabilityMask
from research.backtest.reporter import Reporter
from research.backtest.strategy import TopKLongOnly, QuintilePortfolio
from research.backtest.tradability import TradabilityProvider
from research.storage.paths import StoragePaths


class CachedFactorLoader:
    """signal_recompute=False mode: reads cached factor parquet keyed by sha256 expression."""

    def __init__(self, factor_id: str):
        self.factor_id = factor_id
        self._panel: pd.DataFrame | None = None

    def load(self):
        # ... lookup F{id}.yaml expression → sha256 → cache parquet ...
        # See research.compute for details.
        from research.research_factor_loader import load_cached_factor   # placeholder
        self._panel = load_cached_factor(self.factor_id)

    def at(self, dt: date) -> pd.Series:
        if self._panel is None:
            self.load()
        return self._panel.loc[pd.Timestamp(dt)]


def run_backtest(factor_id: str, cli_overrides: dict | None = None) -> None:
    cfg = load_default_config(factor_id, cli_overrides)
    cal = TradeCalendar.from_db()
    view_path = (
        Path("storage/cache/market_daily_hfq.parquet")
        if cfg.matching.price_adjust == "hfq"
        else Path("storage/cache/market_daily.parquet")
    )
    view = PriceView.from_parquet(view_path)
    provider = TradabilityProvider.from_db(view)
    mask = TradabilityMask(view, provider, cfg.filters, cal)
    main = TopKLongOnly(holdings_n=cfg.portfolio.holdings_n,
                         max_single_weight=cfg.portfolio.max_single_weight)
    quint = QuintilePortfolio()
    factor_loader = CachedFactorLoader(factor_id)   # extend later for signal_recompute=True
    engine = Engine(cfg, cal, view, mask, main, quint, factor_loader, Executor())

    # Run all configured periods
    for period_name in cfg.periods.run:
        start, end = getattr(cfg.periods, period_name)
        result = engine.run(start, end)
        out_dir = StoragePaths.factors_dir() / factor_id / "backtest" / period_name
        Reporter().write(result, out_dir)
        print(f"[{factor_id}] {period_name}: Sharpe={result.metrics['full']['sharpe']:.2f} "
              f"MaxDD={result.metrics['full']['max_dd']:.2%}")
```

- [ ] **Step 2: Register CLI subcommand in `src/research/cli/main.py`**

Add after the `cache` block, before the audit block:

```python
    # ── backtest ──────────────────────────────────────────────────────
    bt_p = sub.add_parser("backtest", help="Run portfolio backtest on an admitted factor")
    bt_p.add_argument("--factor", required=True, help="Factor ID (e.g. F009)")
    bt_p.add_argument("--rebalance-freq-days", type=int, default=None)
    bt_p.add_argument("--holdings-n", type=int, default=None)
    bt_p.add_argument("--periods", type=str, default=None,
                       help="comma-separated subset of train,val,holdout")
    bt_p.add_argument("--no-signal-recompute", action="store_true")
```

In the dispatcher block (after parse_args):

```python
    if args.command == "backtest":
        from research.backtest.runner import run_backtest
        cli = {}
        if args.rebalance_freq_days is not None:
            cli["rebalance"] = {"freq_days": args.rebalance_freq_days}
        if args.holdings_n is not None:
            cli["portfolio"] = {"holdings_n": args.holdings_n}
        if args.periods is not None:
            cli["periods"] = {"run": args.periods.split(",")}
        if args.no_signal_recompute:
            cli["signal_recompute"] = False
        run_backtest(args.factor, cli_overrides=cli)
        return
```

- [ ] **Step 3: Smoke test the CLI**

```bash
PYTHONPATH=src python3 -m research backtest --factor F009 --periods holdout
```

Expected: prints `[F009] holdout: Sharpe=... MaxDD=...` and writes `storage/vault/factors/F009/backtest/holdout/` with 4 parquets + metrics.yaml + figs.

- [ ] **Step 4: Commit**

```bash
git add src/research/backtest/runner.py src/research/cli/main.py
git commit -m "feat(backtest-cli): add backtest subcommand + runner orchestrator"
```

---

## Task 15: Phase 4 report subagent integration

**Files:**
- Modify: `.claude/skills/factor-report/skill.md` (or whichever file the Phase 4 subagent reads from)

- [ ] **Step 1: Locate the Phase 4 report subagent definition**

```bash
grep -rln "factor-report\|report subagent\|F005" .claude/skills/ src/research/archive/ 2>/dev/null
```

- [ ] **Step 2: Add a "Live-feel Backtest" instruction**

Append to the report subagent's instruction file: after the existing analysis sections are generated, the subagent invokes:

```bash
PYTHONPATH=src python3 -m research backtest --factor {{FACTOR_ID}}
```

Then in the F{id}.md template, add a new section:

```markdown
## Live-feel Backtest

| Period | Sharpe | MaxDD | Turnover_ann | Cost_drag_bps |
|---|---|---|---|---|
| Train | <metrics.yaml.train.sharpe> | ... | ... | ... |
| Val | ... | ... | ... | ... |
| Holdout | ... | ... | ... | ... |

![[F{id}/backtest/holdout/figs/equity.png]]
![[F{id}/backtest/holdout/figs/drawdown.png]]
![[F{id}/backtest/holdout/figs/layer_decomp.png]]
![[F{id}/backtest/holdout/figs/cost_drag.png]]
```

The exact insertion depends on the existing skill template — read it first and integrate idiomatically.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/factor-report/skill.md
git commit -m "feat(backtest): integrate backtest run into Phase 4 report subagent"
```

---

## Task 16: End-to-end smoke on F009 holdout

- [ ] **Step 1: Run F009 backtest on holdout**

```bash
PYTHONPATH=src python3 -m research backtest --factor F009 --periods holdout
```

Expected runtime: ~30-60 seconds with cached factor. Output written to `storage/vault/factors/F009/backtest/holdout/`.

- [ ] **Step 2: Inspect outputs**

```bash
ls storage/vault/factors/F009/backtest/holdout/
cat storage/vault/factors/F009/backtest/holdout/metrics.yaml | head -40
PYTHONPATH=src python3 -c "
import pandas as pd
e = pd.read_parquet('storage/vault/factors/F009/backtest/holdout/equity_curve.parquet')
t = pd.read_parquet('storage/vault/factors/F009/backtest/holdout/trades.parquet')
print('equity rows:', len(e))
print('trades rows:', len(t))
print('Sharpe:', (e.total_equity.pct_change().mean() * 252) /
                  (e.total_equity.pct_change().std() * (252**0.5)))
print('blocked buys:', (t.reason == 'blocked_buy').sum())
print('reconciliation_violations: see metrics.yaml')
"
```

Verify:
- equity_curve has ~242 rows (2024 trading days)
- trades has 50+ rows (one per buy/sell at each rebalance)
- reconciliation_violations should be 0
- All figures rendered

- [ ] **Step 3: Run full suite tests**

```bash
pytest tests/research/backtest/ -v
```

Expected: all green.

- [ ] **Step 4: Commit any test data fixtures or final tweaks**

```bash
git status
git add -A
git commit -m "test(backtest): F009 holdout smoke verified end-to-end"
```

---

## Task 17 (deferred): Audit recompute on 6 polluted factors

Out of scope for this plan. Tracked as a follow-up: write `scripts/audit_polluted_factors.py` that recomputes F002/F012/F015/F016/F018/F019 on hfq and produces a side-by-side metrics report `docs/superpowers/findings/2026-04-26-qfq-vs-hfq-factor-audit.md`. **Do not auto-update vault metadata** (per spec §7).

---

## After Plan Execution

1. Run full test suite once more: `pytest tests/research/ -v`
2. Run F009 backtest on all 3 periods: `python3 -m research backtest --factor F009`
3. Verify the F009 deep report (`storage/vault/factors/F009.md`) auto-includes the Live-feel Backtest section after `/factor-report F009`
4. If everything passes, finalize-the-branch via superpowers:finishing-a-development-branch
