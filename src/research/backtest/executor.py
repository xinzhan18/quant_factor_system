"""Executor — diff target vs current → orders → mask → cost → fills.

Order of operations (per :func:`execute`):

1. Pull execution prices (open or close per ``match_price``) for all
   target+held symbols.
2. Compute desired share counts: target weight × estimated equity / price,
   floored to lot size (100 shares).
3. Diff into sells (current > target) and buys (target > current).
4. Sells first, masked by ``can_sell``. Blocked sells get a 0-share log entry
   tagged ``blocked_sell``; passed sells become real fills, proceeds enter
   the account's ``pending_cash``.
5. Compute the buy budget: ``cash + same-day-sell-proceeds`` if
   ``allow_intraday_netting``, else ``cash`` only.
6. Buys masked by ``can_buy``. If aggregate buy notional > budget, scale
   pro-rata (per ``policy.capital_shortage``). Lot floor + execute.
7. Blocked buys get 0-share log entries tagged ``blocked_buy``.

Uses ``account._positions`` directly to read current shares (private access by
design — ``Account`` is in the same module family).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

import pandas as pd

from research.backtest.account import Account, Fill
from research.backtest.config import CostConfig
from research.backtest.cost import compute_cost
from research.backtest.data_view import PriceView
from research.backtest.filters import ExecutionPolicy, TradabilityMask


LOT_SIZE = 100


@dataclass(frozen=True)
class Executor:
    match_price: str = "open"   # "open" or "close"

    def _exec_prices(
        self, exec_date: date, view: PriceView, syms: list[str]
    ) -> pd.Series:
        df = view.slice_eod(exec_date, syms)
        col = self.match_price
        if col not in df.columns:
            return pd.Series(float("nan"), index=syms)
        return df[col].reindex(syms).astype(float)

    def execute(
        self,
        exec_date: date,
        target: pd.Series,
        account: Account,
        mask: TradabilityMask,
        view: PriceView,
        cost_cfg: CostConfig,
        policy: ExecutionPolicy,
        allow_intraday_netting: bool,
    ) -> list[Fill]:
        fills: list[Fill] = []
        held = account.held_symbols()
        all_syms = sorted(set(target.index) | held)
        if not all_syms:
            return fills

        prices = self._exec_prices(exec_date, view, all_syms)

        # Estimate equity for sizing — use exec-date prices for held positions
        equity = account.cash + account.pending_cash
        for sym in held:
            p = account._positions[sym]
            ref = prices.get(sym)
            ref_price = float(ref) if pd.notna(ref) else p.last_close
            equity += p.shares * ref_price

        # Desired shares per symbol
        desired: dict[str, int] = {}
        for sym, w in target.items():
            price = prices.get(sym)
            if price is None or pd.isna(price) or price <= 0:
                continue
            shares = int(math.floor(w * equity / price / LOT_SIZE)) * LOT_SIZE
            if shares > 0:
                desired[sym] = shares

        # Diff
        sells: list[tuple[str, int]] = []
        buys: list[tuple[str, int]] = []
        for sym in held:
            current = account._positions[sym].shares
            want = desired.get(sym, 0)
            if want < current:
                sells.append((sym, current - want))
        for sym, want in desired.items():
            current = account._positions[sym].shares if sym in account._positions else 0
            if want > current:
                buys.append((sym, want - current))

        # Sell pass
        sell_syms = [s for s, _ in sells]
        if sell_syms:
            can_sell = mask.can_sell(exec_date, sell_syms, account)
            for sym, qty in sells:
                if not can_sell.loc[sym]:
                    fills.append(Fill(
                        side="sell", date=exec_date, symbol=sym, shares=0,
                        fill_price=float(prices.get(sym, 0) or 0),
                        cost_cny=0.0, reason="blocked_sell",
                    ))
                    continue
                available = account.available_shares(sym, exec_date)
                actual = min(qty, available)
                if actual <= 0:
                    continue
                price = float(prices.loc[sym])
                cost = compute_cost("sell", price, actual, exec_date, cost_cfg)
                f = Fill(
                    side="sell", date=exec_date, symbol=sym, shares=actual,
                    fill_price=price, cost_cny=cost, reason="target_diff",
                )
                fills.append(f)
                account.transact(f)

        # Buy budget
        if allow_intraday_netting:
            same_day_proceeds = sum(
                f.fill_price * f.shares - f.cost_cny
                for f in fills
                if f.side == "sell" and f.shares > 0
            )
            buy_budget = account.cash + same_day_proceeds
        else:
            buy_budget = account.cash

        # Buy pass
        buy_syms = [s for s, _ in buys]
        if buy_syms:
            can_buy = mask.can_buy(exec_date, buy_syms)
            allowed = [(s, q) for s, q in buys if can_buy.loc[s]]
            blocked = [s for s, _ in buys if not can_buy.loc[s]]

            notional = sum(
                float(prices.get(s, 0) or 0) * q for s, q in allowed
            )
            # Reserve 0.5% of budget for transaction costs (commission + slippage
            # + stamp). Typical real cost is 10–30 bps; 50 bps is conservative.
            COST_RESERVE = 0.005
            effective_budget = buy_budget * (1 - COST_RESERVE)
            scale = 1.0
            if (
                notional > effective_budget
                and policy.capital_shortage == "pro_rata"
                and notional > 0
            ):
                scale = max(effective_budget / notional, 0.0)

            # Pro-rata scaling already guarantees total buy notional ≤ buy_budget,
            # so we don't need a per-buy affordability check. Under
            # intraday_netting=True, account._cash may go transiently negative
            # by up to (same-day pending_cash), which settles next trading day.
            for sym, qty in allowed:
                price = float(prices.get(sym, 0) or 0)
                if price <= 0:
                    continue
                scaled = int(math.floor(qty * scale / LOT_SIZE)) * LOT_SIZE
                if scaled <= 0:
                    continue
                cost = compute_cost("buy", price, scaled, exec_date, cost_cfg)
                f = Fill(
                    side="buy", date=exec_date, symbol=sym, shares=scaled,
                    fill_price=price, cost_cny=cost, reason="target_diff",
                )
                fills.append(f)
                account.transact(f)

            for sym in blocked:
                fills.append(Fill(
                    side="buy", date=exec_date, symbol=sym, shares=0,
                    fill_price=float(prices.get(sym, 0) or 0),
                    cost_cny=0.0, reason="blocked_buy",
                ))

        return fills
