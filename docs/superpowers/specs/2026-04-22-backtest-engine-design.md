# A-Share Backtest Engine Design

**Date**: 2026-04-22 (revised v2 after spec review)
**Status**: Design proposal, awaiting approval before implementation
**Goal**: Add a configurable, modular A-share portfolio-level backtest engine that consumes existing admitted factors and produces "live-feel" diagnostics (equity curve, trade log, position snapshots, cost-adjusted metrics) as a Phase 4 report enhancement.

---

## 1. Problem Statement

Each admitted factor `F{id}` currently carries only **截面 IC / IR / Monotonicity / Q1-Q5 ls_stats** in `vault/factors/F{id}.yaml`. These are computed on raw signal × forward returns and assume frictionless, daily-rebalanced equal-weight quintile portfolios. Missing for real evaluation:

- Transaction costs (stamp tax, commission, slippage)
- Tradability constraints (limit-up/down, suspended, ST, T+1 settlement)
- Realistic rebalance frequency (signal HL = 10–20 days)
- Holdout (2024) net curve — Phase 2 by design never sees holdout
- Cash management / lot rounding / dynamic universe membership
- Visual artifacts: net equity curve, drawdown, monthly heatmap, layer decomposition

System constitution (R3 single data source, R4 no recomputation, R6 minimal): the engine consumes existing artifacts (factor values parquet + market data); no Phase 2 re-run; no backwards-compat shims; additive only.

---

## 2. Scope Decisions (resolved during brainstorming)

| Decision | Choice | Rationale |
|---|---|---|
| **Position in pipeline** | Phase 4 diagnostic enhancement (post-admit, called by report subagent) | No CP07; doesn't disturb 6-CP + §7.MT verdict DAG; can legally use holdout |
| **Engine implementation** | Self-built A-share vectorized state-machine engine | A-share rules (T+1, 涨跌停, 印花税) too core to delegate; debuggability per-symbol-per-day required |
| **Strategy archetype** | Top-K=50 long-only **+** Q1-Q5 quintile decomposition (gross, no cost — see §3.6) | Top-K = real tradable; Q1-Q5 = diagnostic decomposition validating monotonicity post-cost |
| **Rebalance** | Every 5 trading days (weekly), trading-day arithmetic | Signal HL 10–20d → ~50% of HL is the follow-but-don't-churn sweet spot |
| **Cost model** | Stamp 10bps/5bps (time-varying) sell + commission 3bps 双边 + slippage 5bps 双边 + min 5 CNY | A-share institutional standard; stamp tax cut 2023-08-28 |
| **Tradability filters** | Block ST, suspended, limit-up at buy, limit-down at sell, post-suspend cooldown 1d | A-share trading rules |
| **Capital** | Initial 10M CNY, no leverage, T+1 cash settlement | Standard size for csi1000 50-holding portfolio |
| **Periods** | Train (2015–2021) + Val (2022–2023) + Holdout (2024) all run separately | Segment-level Sharpe decay is core evidence |
| **Price adjustment** | **HFQ (后复权) as default** | PIT-correct (no future-event leakage); stable across data syncs; A-share quant industry standard |
| **Signal recompute** | Configurable: `signal_recompute: true` (default) \| `false` | Default rigorous (recompute on hfq, full panel pre-built once); fast path opts into cached qfq for ratio-only factors |

The default is now **`signal_recompute: true`**. Reviewer-flagged issue: cached qfq factor values are not PIT-stable under corporate actions even for time-series-window factors that span an event date. Reverse the default: rigor first, fast path is opt-in.

---

## 3. Architecture

### 3.1 Module Layout

```
src/research/backtest/
├── __init__.py
├── config.py        # BacktestConfig dataclass + 3-layer merge (CLI > per-factor > defaults)
├── calendar.py      # TradeCalendar: trading days + dynamic universe@date
├── data_view.py     # PriceView: load hfq OHLCV+returns+limit_up/down, slice by (date, symbol)
├── tradability.py   # TradabilityProvider: PIT is_st / is_suspended / is_limit_up / is_limit_down / is_newly_listed
├── filters.py       # TradabilityMask: combines provider + config flags into can_buy/can_sell masks
├── strategy.py      # Strategy ABC + TopKLongOnly + QuintilePortfolio + execution policies
├── account.py       # Account: cash + pending_cash + positions (with T+1 lock); transact + mark
├── cost.py          # CostModel: time-varying stamp + commission + slippage (pure function)
├── executor.py      # Executor: target_weights → diff orders → masks → fills (lot rounding, partial)
├── engine.py        # Engine: state machine main loop (~150 lines, glue)
├── reporter.py      # Output: 4 parquets + metrics.yaml + figs
└── runner.py        # called by both report subagent and CLI; not a new entry point
```

CLI entry registered into existing `src/research/cli/` dispatcher (extend `__main__.py`'s subcommand table), not a new `python3 -m research.backtest` namespace.

Total target: ~1700 LOC engine + ~600 LOC tests.

### 3.2 Data Layer

**New parquet** (one-time sync, ~30 min):
```
storage/cache/market_daily_hfq.parquet
  cols: $open, $high, $low, $close, $volume, $amount, $market_cap,
        $turnover_rate, $limit_up, $limit_down, returns_1d, ...
  index: (datetime, instrument)
  range: 2015-01-05 to 2024-12-31 (extended to cover holdout)
```

Sync command (extends `scripts/resync_qlib.py`):
```bash
PYTHONPATH=src python3 scripts/resync_qlib.py --adjust hfq --start 2015-01-01 --end 2024-12-31 \
    --extra-fields limit_up,limit_down,turnover_rate
```

Existing qfq parquet (`market_daily.parquet`) is untouched.

#### 3.2.1 Tradability Data Inventory (resolves Blocker B1)

Every tradability fact the engine reads, its source, and its PIT semantics:

| Fact | Source | Type | PIT |
|---|---|---|---|
| OHLCV + amount + market_cap | `market_daily_hfq.parquet` | float, hfq-adjusted | ✓ values for date `t` measured at end of `t` |
| `$limit_up`, `$limit_down` | qlib binary (already exists in `~/.qlib/qlib_data/cn_data_1d/features/{sym}/limit_{up,down}.day.bin`); pulled into hfq parquet during sync | float, raw price (NOT hfq-adjusted) | ✓ today's limit-band prices, set at open |
| `limit_pct(date, sym)` | Resolved by `board_of(sym)` × time-varying schedule (see below) | float | ✓ |
| `is_suspended(date, sym)` | Derived: `volume == 0 OR amount == 0` on `date` for `sym` (proxy) | bool | ✓ end-of-day; documented limitation: half-day suspension not detected |
| `is_st(date, sym)` | New table `instrument_st_status (datetime, instrument, is_st bool)` synced once via RiceQuant `instruments.list_st_stocks` API; if sync fails, fall back to `block_st: false` and emit warning | bool | ✓ status as of `date` |
| `listing_date(sym)`, `delisting_date(sym)` | New table `instrument_lifecycle` synced from RiceQuant `instruments.get_securities_meta`; if missing, use first/last appearance in market_daily | date | ✓ |
| `csi1000_at(date)` | Existing `index_constituents` table (2.7M rows); query `WHERE index_code='000852' AND start_date <= date AND (end_date IS NULL OR end_date > date)` | set[str] | ✓ |

**Limit detection rule** (resolves Important I2):
- For `match_price=open`: a buy order is blocked if `open ≥ prev_close × (1 + limit_pct − ε)` (price gapped to limit-up at open); sell order blocked if `open ≤ prev_close × (1 − limit_pct + ε)`. `ε = 0.001` for tick-size noise.
- For `match_price=close`: compare `close` against `limit_up` / `limit_down` from the parquet (with 0.01 CNY tolerance).

**Limit pct schedule** (time-varying, resolves NEW-3):
- ST stocks (any date, any board): ±5%
- Beijing Stock Exchange (BJ4xxxxx / BJ8xxxxx prefix): ±30% — out of scope (csi1000 doesn't include BSE)
- ChiNext (SZ300xxx) / STAR (SH688xxx): **±10% before 2020-08-24, ±20% from 2020-08-24 onwards**
- Main board (everything else): ±10%
- Newly listed stocks first 5 trading days: no limit — handled by `newly_listed_days=60` filter that already blocks them from the candidate pool

The resolver lives in `tradability.py:limit_pct(dt, sym)` and is unit-tested for the 2020-08-24 ChiNext regime change.

**Suspended detection** (acknowledged proxy): `volume[date,sym] == 0`. Limitation documented in `metrics.yaml.assumptions.suspended_proxy: "volume==0 (intraday halt not detected)"`.

**ST hard requirement**: if `block_st=true` and the ST table is missing, the engine refuses to start with a clear error — silent fallback would produce false-cost backtests.

### 3.3 Component Contracts

```python
# config.py
@dataclass(frozen=True)
class BacktestConfig:
    universe: str
    initial_capital: float
    rebalance: RebalanceConfig
    portfolio: PortfolioConfig
    matching: MatchingConfig
    cost: CostConfig          # see §3.5
    filters: FilterConfig
    periods: PeriodsConfig
    benchmark: BenchmarkConfig
    output: OutputConfig
    signal_recompute: bool

    def validate(self) -> None:
        """Hard checks: rebalance.freq_days >= 2 unless matching.allows_t0=True (not implemented);
           periods.run subset of {train, val, holdout}; capital > 0; etc."""

    @classmethod
    def merge(cls, defaults: dict, per_factor: dict, cli: dict) -> "BacktestConfig":
        """Nested deep-merge; later wins."""

# calendar.py
class TradeCalendar:
    def trading_days(self, start: date, end: date) -> pd.DatetimeIndex: ...
    def add_trading_days(self, base: date, n: int) -> date: ...
    def universe_at(self, dt: date) -> set[str]: ...
    def rebalance_schedule(self, start: date, end: date,
                           freq_days: int, anchor: str | date) -> pd.DatetimeIndex:
        """Generates trading-day-aligned rebalance days. Anchor 'monday' resolves
           to first Monday-or-later trading day in [start, end]; then steps by
           freq_days trading days. Holiday-bridges (e.g. CNY) just skip — no make-up."""

# data_view.py
class PriceView:
    def __init__(self, parquet_path: Path): ...
    @property
    def snapshot_ts(self) -> datetime: ...   # max(datetime) at load time, written into metrics.yaml
    def slice_eod(self, dt: date, symbols: list[str]) -> pd.DataFrame:
        """Returns at-end-of-dt: open, high, low, close, volume, amount, limit_up, limit_down."""
    def slice_panel(self, start, end, symbols) -> pd.DataFrame: ...

# tradability.py
class TradabilityProvider:
    """All methods are PIT — caller passes the date."""
    def is_st(self, dt: date, sym: str) -> bool: ...
    def is_suspended(self, dt: date, sym: str) -> bool: ...
    def is_newly_listed(self, dt: date, sym: str, n_days: int = 60) -> bool: ...
    def listing_date(self, sym: str) -> date: ...
    def delisting_date(self, sym: str) -> date | None: ...
    # Vectorized helpers for cross-section at a date:
    def st_mask(self, dt: date, syms: list[str]) -> pd.Series[bool]: ...
    def suspended_mask(self, dt: date, syms: list[str]) -> pd.Series[bool]: ...

# filters.py
class TradabilityMask:
    def __init__(self, view: PriceView, provider: TradabilityProvider,
                 config: FilterConfig, calendar: TradeCalendar): ...
    def can_buy(self, exec_date: date, symbols: list[str]) -> pd.Series[bool]: ...
    def can_sell(self, exec_date: date, symbols: list[str], account: "Account") -> pd.Series[bool]:
        """Also filters out shares still under T+1 lock — see Account.available_shares."""

# strategy.py
class Strategy(ABC):
    @abstractmethod
    def target_weights(self, decision_date: date,
                       factor_values: pd.Series,           # NaN-allowed; strategy filters
                       universe: set[str],
                       price_view: PriceView) -> pd.Series:
        """Index = symbol, value = target weight in [0, max_single_weight]; sum ≤ 1.0.
           NaN factor values are excluded from the candidate pool but counted in the
           denominator for diagnostic reporting."""

class TopKLongOnly(Strategy): ...

class QuintilePortfolio(Strategy):
    """Five sub-portfolios. Engine creates 5 separate Account instances — see §3.6 on
       gross-vs-net policy for the diagnostic role."""
    def target_for_quintile(self, q: int, factor_values: pd.Series,
                             universe: set[str], price_view: PriceView) -> pd.Series: ...

# account.py
@dataclass
class Position:
    symbol: str
    shares: int           # multiple of 100 (lot)
    locked_until: date    # T+1: shares not sellable before this date
    avg_cost: float
    last_close: float

@dataclass
class Fill:
    side: Literal["buy", "sell"]
    date: date            # execution date
    symbol: str
    shares: int
    fill_price: float
    cost_cny: float
    reason: Literal["target_diff", "force_liquidate_st", "force_liquidate_delisted"]

class Account:
    def __init__(self, initial_capital: float): ...
    @property
    def cash(self) -> float: ...
    @property
    def pending_cash(self) -> float:
        """Cash from sells on date d, available on d+1 (T+1 cash settlement)."""
    def settle_cash(self, on_date: date) -> None:
        """Move pending_cash → cash for sells executed on previous trading day."""
    def available_shares(self, sym: str, exec_date: date) -> int:
        """shares - locked_until > exec_date subset; floor(0)."""
    def transact(self, fill: Fill) -> None: ...
    def mark_to_market(self, dt: date, prices: pd.Series) -> float:
        """For positions with stale price (delisted / data missing), use last known close.
           If stale > stale_position_days_max, force-liquidate at last known."""
    def positions_snapshot(self, dt: date) -> pd.DataFrame: ...

# cost.py
def compute_cost(side: Literal["buy", "sell"],
                 price: float, shares: int,
                 dt: date, config: CostConfig) -> float:
    """Pure function. Stamp rate looked up from config.stamp_schedule (time-varying)."""

# executor.py
class Executor:
    def execute(self, exec_date: date, target: pd.Series,
                account: Account, mask: TradabilityMask,
                price_view: PriceView, cost_config: CostConfig,
                policy: ExecutionPolicy) -> list[Fill]:
        """Differences current vs target → orders → mask → cost → lot rounding → fills.
           Blocked orders deferred or dropped per ExecutionPolicy."""

# engine.py
class Engine:
    def run(self, start: date, end: date) -> BacktestResult: ...

# reporter.py
class Reporter:
    def write(self, result: BacktestResult, out_dir: Path) -> None: ...

# Result
@dataclass
class BacktestResult:
    equity_curve: pd.DataFrame      # main account
    quintile_curves: list[pd.DataFrame]
    trades: pd.DataFrame
    positions: pd.DataFrame
    metrics: dict                    # to be written as metrics.yaml
    config_snapshot: dict
    runtime_meta: dict               # snapshot_ts, hfq_parquet_mtime, signal_recompute, factor_cache_key
```

### 3.4 State Machine

#### 3.4.0 Information-Set Invariant (resolves Blocker B3)

At any decision time on day `dt`:
- **Available**: all data with timestamp `≤ dt's close` (factor values, prices, tradability flags, universe membership).
- **Forbidden**: any data from `dt+1` or later, including `next_dt`'s open/close, factor values, splits, dividends.

Orders are placed for execution on `next_dt` at `match_price` (open by default). This means the executor knows `next_dt`'s open price and limit-up/down — that's the execution date's information, used at execution time, not decision time. The decision uses only `dt`-and-earlier information.

Test: a poison-data unit test that inserts an arbitrary value at `next_dt` and asserts the strategy's `target_weights(dt, ...)` output is identical with or without the poison.

#### 3.4.1 Main Loop

```python
def run(self, start: date, end: date) -> BacktestResult:
    cal, view, mask, cost_cfg = self.calendar, self.price_view, self.mask, self.config.cost
    days = cal.trading_days(start, end)
    rebalance_days = set(cal.rebalance_schedule(start, end,
                                                self.config.rebalance.freq_days,
                                                self.config.rebalance.anchor))

    main_account = Account(self.config.initial_capital)
    quintile_accounts = [Account(self.config.initial_capital) for _ in range(5)]

    for i, dt in enumerate(days):
        # (a) Settle cash from previous day's sells (T+1 cash settlement)
        if i > 0:
            main_account.settle_cash(on_date=dt)
            for qa in quintile_accounts:
                qa.settle_cash(on_date=dt)

        # (b) Mark to close-of-dt for all held positions (uses dt's close, end-of-day fact)
        held = main_account.held_symbols() | union(qa.held_symbols() for qa in quintile_accounts)
        prices_eod = view.slice_eod(dt, list(held))
        main_account.mark_to_market(dt, prices_eod.close)
        for qa in quintile_accounts:
            qa.mark_to_market(dt, prices_eod.close)

        # (c) Force-liquidations triggered by ST event / delisting (executes next trading day)
        # See §3.7 universe-lifecycle policy for queueing.
        self._enqueue_force_liquidations(dt, main_account, quintile_accounts)

        # (d) Decision step — only uses information ≤ dt's close
        if dt in rebalance_days:
            factor_vals = self.factor_loader.at(dt)              # PIT contract
            universe = cal.universe_at(dt)

            main_target = self.main_strategy.target_weights(dt, factor_vals, universe, view)
            quintile_targets = [self.quintile_strategy.target_for_quintile(q, factor_vals, universe, view)
                                for q in range(5)]
        else:
            main_target = None
            quintile_targets = None

        # (e) Execution — at next_dt's open
        next_dt = days[i + 1] if i + 1 < len(days) else None
        if next_dt is not None:
            if main_target is not None:
                fills = self.executor.execute(next_dt, main_target, main_account, mask, view,
                                               cost_cfg, self.main_policy)
                for f in fills: main_account.transact(f)
            if quintile_targets is not None:
                for q, qa in enumerate(quintile_accounts):
                    qfills = self.executor.execute(next_dt, quintile_targets[q], qa, mask, view,
                                                    cost_cfg, self.quintile_policy)
                    for f in qfills: qa.transact(f)
            # Process force-liquidations (executes regardless of rebalance day)
            self._execute_force_liquidations(next_dt, main_account, quintile_accounts, mask, view, cost_cfg)

        # (f) Snapshot
        self._snapshot(dt, main_account, quintile_accounts)

    return self._build_result(...)
```

Comment correction (resolves Important I6): `(b)` is "mark at `dt`'s close — that is, end-of-day-of-dt"; not "yesterday's close".

### 3.5 Configuration Schema

Append to `storage/config.yaml`:

```yaml
backtest:
  defaults:
    universe: csi1000
    initial_capital: 10_000_000
    signal_recompute: true        # default true; set false to use cached qfq factor values

    rebalance:
      freq_days: 5                # in trading days
      anchor: monday              # 'monday' | 'first_trade_day' | YYYY-MM-DD
      # Engine validates freq_days >= 2 (T+1 enforcement)

    portfolio:
      holdings_n: 50
      weight_scheme: equal
      max_single_weight: 0.05

    matching:
      match_price: open           # open | close
      price_adjust: hfq

    cost:
      stamp_schedule:
        - {from: 2015-01-01, to: 2023-08-27, sell_bps: 10}
        - {from: 2023-08-28, to: 9999-12-31, sell_bps: 5}
      commission_bps: 3           # 双边
      slippage_bps: 5             # 双边
      min_commission_cny: 5

    capital:
      allow_intraday_netting: false   # default rigorous: same-day sell proceeds NOT available
                                      # for same-day buys (strict A-share T+1 cash settlement).
                                      # Set true for the more lenient "intraday net" approximation.

    filters:
      block_st: true              # requires instrument_st_status table; engine refuses if missing
      block_suspended: true
      block_limit_up_at_buy: true
      block_limit_down_at_sell: true
      cooldown_days_after_unsuspend: 1
      newly_listed_days: 60       # block buying stocks listed < 60 days
      stale_position_days_max: 5  # force-liquidate position whose last close > 5 days old

    periods:
      train:   [2015-01-01, 2021-12-31]
      val:     [2022-01-01, 2023-12-31]
      holdout: [2024-01-01, 2024-12-31]
      run: [train, val, holdout]

    benchmark:
      kind: csi1000_total_return  # csi1000_total_return | csi1000_equal_weight_tradable
      # csi1000_total_return: weighted by csi1000 official weights, hfq-priced, no costs
      # csi1000_equal_weight_tradable: equal-weight on tradable subset of csi1000 each day,
      #   weekly rebalance, no costs (apples-to-apples for portfolio-style)

    output:
      save_trades: true
      save_positions: true
      figs: [equity, drawdown, monthly_heatmap, layer_decomp, cost_drag, blocked_trades]
```

**Per-factor override** (optional): `storage/vault/factors/F{id}.backtest.yaml` — only fields to override.

**CLI override** (highest priority, registered in existing `src/research/cli/__main__.py` dispatcher):
```
research backtest --factor F009
research backtest --factor F009 --no-signal-recompute --rebalance-freq-days 10
research backtest --factor F009 --periods holdout
```

Merge order: `cli > per_factor_yaml > config.yaml.backtest.defaults`.

### 3.6 Quintile Decomposition Policy (resolves Important I4)

The Q1–Q5 decomposition is a **diagnostic**, not a deployable strategy. Its purpose: validate that the factor's monotonicity survives realistic frictions. To make Q1–Q5 comparable to each other, the engine runs them **gross of cost and gross of capital constraint** (the executor uses cost=0 and unlimited cash), but **respects tradability filters** (limit-up/down/suspended). This means:

- Each quintile holds ~200 names (csi1000 / 5)
- Each quintile is fully invested every rebalance (no cash drag)
- Cost-drag is reported only on the main Top-K strategy
- The diagnostic answers: "after blocking unfillable trades, does Q5 > Q4 > Q3 > Q2 > Q1 still hold?"

The configuration `quintile.cost_mode: gross` is fixed in this design (not user-configurable) to keep the diagnostic interpretable.

### 3.7 Universe and Lifecycle Policy (resolves Blocker B5)

| Event | Engine response |
|---|---|
| Stock leaves csi1000 mid-cycle (still tradable) | Hold until next rebalance, then drop from `target` (sold normally) |
| Stock enters csi1000 mid-cycle | Eligible for next rebalance's candidate pool, subject to `newly_listed_days` filter |
| Held stock becomes ST mid-cycle | Enqueue force-liquidate; sell on next trading day at open (unless limit-down → defer with retry up to 5 trading days) |
| Held stock delisted | Mark at last available close; `mark_to_market` returns `last_close × shares`; on the trading day after delisting announce, force-liquidate at last_close. Logged as `delisted_writeoff` — there is no real counterparty, so proceeds credit `cash` directly (NOT `pending_cash`); no T+1 settlement applies. |
| Held stock has stale price (> `stale_position_days_max=5`) | Same as delisted — force-liquidate at last_close |
| New listing day | Excluded from candidate pool until `listing_date + newly_listed_days` |

Reconstitution dates (June, December): handled as ordinary universe-membership change. The first rebalance after reconstitution will see the new universe.

### 3.8 Execution Policy (resolves Important I3 + I9)

```python
class ExecutionPolicy:
    blocked_buy: Literal["drop", "carry_over_n_days"]    = "drop"
    blocked_sell: Literal["carry_over_n_days"]           = "carry_over_n_days"
    blocked_sell_max_carry_days: int                      = 5
    capital_shortage: Literal["pro_rata", "drop_smallest"]= "pro_rata"
    lot_residual: Literal["floor"]                        = "floor"     # always floor to 100s
    nan_factor: Literal["exclude_from_pool"]              = "exclude_from_pool"
```

Concrete behavior:

- **Blocked buy** (limit-up, suspended, ST, newly-listed): order dropped; the would-be allocation goes to cash. Logged with reason in `trades.parquet` as `blocked_buy_<cause>`.
- **Blocked sell**: position retained; retry on next trading day's match_price; after 5 days of failed sells, escalate to force-liquidate-at-any-price (still log if blocked).
- **Capital shortage** (target weights × prices > available buy budget): scale all buy orders pro-rata to fit. Buy budget depends on `capital.allow_intraday_netting`:
  - `false` (default, rigorous): buy budget = `cash` only. Sell orders' proceeds enter `pending_cash` and become spendable on the next trading day.
  - `true` (lenient): buy budget = `cash + same-day sell proceeds`. Same-day netting; documented in `metrics.yaml.assumptions.intraday_netting=true`.
- **Cooldown after unsuspend**: a stock that was `is_suspended(dt-1, sym)=True` and `is_suspended(dt, sym)=False` has `can_buy(dt, sym)=False` for `cooldown_days_after_unsuspend` trading days (default 1). `can_sell` is unaffected.
- **Lot residual**: `floor(target_value / price / 100) × 100`. The dropped fractional lot's value goes to cash.
- **NaN factor value**: symbol excluded from candidate pool; for Top-K, the K is filled from non-NaN universe; for Quintile, the cross-section is restricted to non-NaN before partitioning.
- **All-NaN day** (e.g., factor cache hole): rebalance skipped entirely with a warning.

### 3.9 Output Layout

```
storage/vault/factors/F{id}/backtest/
├── equity_curve.parquet
│   cols: date, total_equity, cash, pending_cash, holdings_value, drawdown,
│          benchmark_equity, benchmark_drawdown, gross_equity (no-cost virtual line)
├── trades.parquet
│   cols: date, symbol, side, shares, target_value_cny, fill_price, cost_cny,
│          stamp_cny, commission_cny, slippage_cny, reason
├── positions.parquet
│   cols: date, symbol, shares, locked_until, mkt_value, weight, days_held
├── metrics.yaml         # see §3.10
└── figs/
    ├── equity.png
    ├── drawdown.png
    ├── monthly_heatmap.png
    ├── layer_decomp.png
    ├── cost_drag.png
    └── blocked_trades.png   # # of blocked-buy / blocked-sell per month
```

`F{id}.md` gets a new section **"Live-feel Backtest"** with metrics table + figures.

### 3.10 Metrics + Reconciliation (resolves Important I1)

`metrics.yaml` structure:
```yaml
runtime:
  snapshot_ts: 2026-04-22T08:30:00Z   # max(datetime) of hfq parquet at run
  hfq_parquet_mtime: ...
  factor_cache_key: <sha256>
  signal_recompute: true
  config_hash: <sha256 of resolved config>

assumptions:
  suspended_proxy: "volume==0 (intraday halt not detected)"
  capital_shortage_policy: pro_rata
  intraday_settlement_for_capital: true
  st_data_source: "rqdatac.list_st_stocks (synced 2026-04-22)"

per_period:
  train:
    sharpe: ...
    sortino: ...
    calmar: ...
    max_dd: ...
    max_dd_duration: ...
    turnover_annual: ...
    cost_drag_bps_annual: ...
    hit_rate: ...
    avg_holding_days: ...
    blocked_buy_count: ...
    blocked_sell_count: ...
    forced_liquidation_count: ...
    n_trading_days: ...
  val: { ... }
  holdout: { ... }
  full: { ... }

quintile_diagnostic:
  q1: { ann_return, sharpe, max_dd }
  ...
  q5: { ... }
  monotonicity_post_filter: <float>      # rank-corr(quintile_idx, ann_return)

reconciliation:
  invariant_violations: 0                 # count of days where invariant broke
  max_violation_bps: 0.0                  # max single-day deviation in bps of equity
  avg_violation_bps: 0.0
```

**Reconciliation invariant** (asserted every trading day, on **all 6 accounts** — main + 5 quintile; quintile accounts run gross so the invariant simplifies to lot-rounding noise only and is a useful canary for engine bugs):

```
equity[t] = cash[t] + pending_cash[t] + Σ shares_after_trades[t] × close[t]

Δequity[t] = equity[t] − equity[t-1]
           = Σ shares_held_overnight[t] × (close[t] − close[t-1])              # MTM of overnight holdings
           + Σ buy.shares × (close[t] − fill_price)                            # intraday move on new buys
           + Σ sell.shares × (fill_price − close[t-1])                         # gain locked in by sells
           − Σ trade.cost_cny                                                  # commissions + stamp + slippage
```

Reasonable tolerance: **5bps of `equity[t-1]` per day, or 5000 CNY whichever is larger** (accounts for integer-lot rounding × 50 holdings × ~5 CNY). Cumulative violations across the run reported in `reconciliation.invariant_violations`. A single-day violation > 50bps fails the run loud (exception); persistent < 50bps drifts are logged but don't fail.

### 3.11 Dividends and Corporate Actions Convention (resolves Important I10)

The hfq price series encodes all dividends and splits as multiplicative price drift. The engine therefore:
- Marks positions to hfq close — total return is implicit in the price series.
- Does **not** process explicit cash-dividend events; no cash credit on ex-div date.
- Does **not** adjust share counts on splits (the hfq price already absorbs the ratio).

The benchmark **must** also be hfq total-return (`csi1000_total_return` in the schema) for fair comparison. A non-adjusted benchmark would diverge from the strategy's hfq equity by ~2-3% annually (typical csi1000 dividend yield).

This is a deliberate accounting choice: it sacrifices "see the dividend cash flow" realism for cleaner total-return semantics. Future option (流派 2 Zipline-style with raw prices + corporate-action event stream) is reserved by the module boundaries — `PriceView` and a future `CorporateActionStream` are independent — but is out of scope for this design.

---

## 4. Trigger Flow

**Automatic**: Phase 4 report subagent (`/factor-report`) calls `runner.run_backtest(factor_id, config)` after generating the existing analysis sections. Backtest artifacts written to `storage/vault/factors/F{id}/backtest/`. The report appends the new "Live-feel Backtest" section.

**Manual CLI**:
```bash
research backtest --factor F009
research backtest --factor F009 --no-signal-recompute --rebalance-freq-days 10
research backtest --factor F009 --periods holdout --holdings-n 100
```

The `--no-signal-recompute` flag flips the new default (true) for fast diagnostic runs on ratio-only factors.

---

## 5. Signal Loading (Two Modes)

**Default — `signal_recompute: true`** (rigorous, the new default):

At engine start, the factor expression is evaluated **once on the hfq panel** for the full backtest window using the existing `research.compute` pipeline (vectorized, ~1-3 minutes per factor). The result is cached at `storage/cache/factor_values_hfq/{sha256(expression + price_adjust=hfq + snapshot_ts)}.parquet`. Subsequent runs of the same factor in the same data snapshot reuse the cache.

This pre-compute step is cached, so the runtime SLA is:
- First run on a factor: ~3-5 minutes (compute + backtest)
- Subsequent runs (cache hit): ~30-60 seconds (backtest only)

**Opt-in — `signal_recompute: false`** (fast):

Reads existing qfq cache `storage/cache/factor_values/{sha256_qfq}.parquet`. Trading is still done on hfq prices (returns are mathematically identical), but the cross-sectional rank of factor values may differ from a true PIT-hfq computation for any factor whose time-series window crosses a corporate-action date.

**Intended use**: confirmed-pure-ratio factors only (e.g., F006, F007, F008 — `Mean(Div(...high...low...))` style). The CLI emits a warning if `--no-signal-recompute` is used on a factor whose expression contains `$close`, `$open`, `$high`, `$low`, `$amount`, or `$market_cap` outside a `Div(...)` immediate parent.

**Cache key invariant**: the cache key includes (a) expression sha256, (b) `price_adjust` flag, (c) data snapshot timestamp (`max(datetime)` of the underlying parquet at compute time). A new sync that bumps the snapshot invalidates qfq cache entries — preventing the silent PIT bug where a future corporate action retroactively changes cached qfq values.

---

## 6. Validation Strategy

### 6.1 Unit tests
- `test_calendar.py`: `trading_days`, `add_trading_days`, `universe_at` boundaries (csi1000 reconstitution dates), `rebalance_schedule` across CNY-bridge weeks
- `test_tradability.py`: ST mask date-varying; suspended proxy; newly_listed window; ChiNext +20% limit
- `test_filters.py`: each block flag; `can_sell` honors T+1 lock
- `test_cost.py`: stamp 10bps pre-2023-08-28, 5bps post; commission both sides; slippage both sides; min commission floor
- `test_account.py`: T+1 lock (buy on T → not sellable until T+1); pending_cash settles next day; mark_to_market with stale price; force-liquidate path
- `test_strategy.py`: TopKLongOnly returns ≤ K (drops NaN); QuintilePortfolio assigns each non-NaN sym to exactly one quintile
- `test_executor.py`: blocked buy → cash; blocked sell → carry over; capital shortage → pro-rata; lot floor; reasons logged
- `test_reconciliation.py`: synthetic 3-day scenario with known PnL, assert invariant within 5bps
- `test_information_set.py`: poison-data test on `next_dt`; assert decision unchanged

### 6.2 Integration tests
- `test_engine_end_to_end.py`: F009 on 2024 holdout (1-month window); assert equity_curve length, trades non-empty, all metrics finite, reconciliation passes
- `test_signal_recompute_difference.py`: F019 (`Std($close, 5)`) — assert metrics differ between recompute=true and recompute=false (proves Mode A path is wired and meaningfully different)
- `test_corporate_action_pit.py`: pick a stock with a known dividend in 2018 holdable on the date; verify backtest result matches under recompute=true regardless of when the data was synced (re-sync test)

### 6.3 Smoke
- F009 full 2015-2024: ~3-5 min cold cache, ~30s warm. metrics.yaml fully populated, reconciliation 0 violations.

---

## 7. Sub-tasks (build sequence)

| # | Task | Approx LOC | Depends |
|---|---|---|---|
| 1 | `scripts/resync_qlib.py --adjust hfq` (extend) | +50 | none |
| 2 | New TimescaleDB tables: `instrument_st_status`, `instrument_lifecycle`; sync scripts | 200 | none |
| 3 | `config.py` + `BacktestConfig` + 3-layer merge + validate | 200 | none |
| 4 | `calendar.py` (trading_days, universe_at, rebalance_schedule) | 130 | DB tables |
| 5 | `data_view.py` (PriceView with snapshot_ts) | 80 | hfq parquet |
| 6 | `tradability.py` (TradabilityProvider) | 150 | DB tables, parquet |
| 7 | `filters.py` (TradabilityMask combining provider + config) | 130 | tradability, calendar |
| 8 | `cost.py` (time-varying stamp, commission, slippage) | 70 | none |
| 9 | `account.py` (Account with T+1 lock, pending_cash, mark) | 220 | cost |
| 10 | `strategy.py` (TopKLongOnly, QuintilePortfolio, NaN policy) | 220 | data_view |
| 11 | `executor.py` (with execution policies) | 230 | account, filters, cost |
| 12 | `engine.py` (state machine + reconciliation) | 200 | all above |
| 13 | `reporter.py` (4 parquets + metrics.yaml + figs) | 280 | engine |
| 14 | `runner.py` + register CLI subcommand into existing dispatcher | 80 | reporter |
| 15 | Phase 4 report subagent integration | +50 | runner |
| 16 | Tests (unit + integration) | 600 | corresponding modules |
| 17 | Optional: recompute-on-hfq audit pass for the 6 polluted factors; produce a side-by-side report (does NOT auto-update vault metadata; surfaces decisions to the LLM judge for follow-up) | 100 | hfq compute |

**Estimated total**: ~2900 LOC engine + tests.

Sub-task 17 explicitly does **not** auto-rewrite `vault/factors/F{id}.yaml` — recomputing might shift IC enough to fail CP01, which is a workflow question beyond this design's scope (resolves N5).

---

## 8. Open Questions Deferred to Plan

- Multi-factor combination backtest (Path B from brainstorming) — out of scope
- Full corporate-action event stream (流派 2 Zipline-style) — module boundaries reserved; out of scope
- Sector / size / Barra decomposition of `holdings_value` in `equity_curve.parquet` — defer to first iteration feedback
- Daily rebalance support (`freq_days=1`) — requires intraday matching model not in this design; rejected by config validator

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| HFQ data sync time exceeds expectation | Sync as a background prereq; engine work proceeds on existing qfq for unit-test development; switch parquet path on completion |
| ST table sync fails (RiceQuant API down) | Engine refuses to start with `block_st=true`; documented escape: `--block-st false` with warning in `metrics.yaml.assumptions` |
| Factor cache key (qfq sha256) clashes with hfq | Cache key includes `price_adjust` and `snapshot_ts`; new sync invalidates stale entries |
| Universe@date queries hit DB on every rebalance day → slow | Pre-load full csi1000 membership table once per run as in-memory dict |
| State machine bug → silent PnL mismatch | Per-day reconciliation (§3.10); fail-loud on > 50bps single-day; cumulative violations reported |
| Auto-trigger from report subagent times out | Cold-cache SLA ~3-5 min; hot-cache ~30-60s; report subagent invokes `runner.run_backtest` with timeout 10 min |
| `signal_recompute=true` (recompute) cost-blows-up runtime | Pre-compute full panel once at run-start (vectorized like Phase 2), persist to hfq cache; per-date loop is O(read) only |
| csi1000 constituent membership before 2015-Q3 may be sparse / less reliable in `index_constituents` | Validate coverage at engine init: assert `|universe_at(dt)| ≥ 800` for every dt in run; warn if below |

---

## 10. Constitution Compliance

- **R1** (YAML/MD split): config.yaml has the schema; F{id}.md gets the report section ✓
- **R2** (LLM 主驾): LLM controls when to backtest (via report subagent) and judges results in F{id}.md narrative; engine is pure execution ✓
- **R3** (single data source): hfq parquet is canonical; factor cache split by (expression, price_adjust, snapshot_ts) ✓
- **R4** (no recomputation): default `signal_recompute=true` does compute factor on hfq ONCE per factor per snapshot, then caches — this is one-shot computation, not Phase-2 re-execution; doesn't re-run Phase 2's CP gates ✓
- **R5** (full vectorization): Per-day state mutations vectorized across symbols; only the per-day loop is Python (~2500 iterations × ms-level work) ✓
- **R6** (code minimal): No backwards compat; existing qfq pipeline untouched; no shims ✓
- **R7** (auditable): Every run leaves `trades.parquet` (full provenance), `metrics.yaml.runtime` (snapshot ts, cache key, config hash) ✓
- **R8** (DSL first): Backtest does not touch DSL; orthogonal to factor expression layer ✓
