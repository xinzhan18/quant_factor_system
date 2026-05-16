# Field × Atom Coverage Audit — 2026-05-16T00:42:50Z

**Whitelist size**: 34 fields · **Atom families tracked**: 9 · **Candidates scanned**: 520 across 90 batches

## 1. Untouched fields (zero atom coverage)

**15** fields have **never** appeared as a direct atom argument in any candidate. These are pure blind spots.

- `$account_receivable_turnover_rate_ttm`
- `$book_value_per_share_ttm`
- `$current_ratio_ttm`
- `$debt_to_asset_ratio_ttm`
- `$debt_to_equity_ratio_ttm`
- `$gross_profit_margin_ttm`
- `$inventory_turnover_ttm`
- `$net_asset_growth_ratio_ttm`
- `$net_profit_growth_ratio_ttm`
- `$operating_cash_flow_per_share_ttm`
- `$operating_profit_margin_ttm`
- `$operating_revenue_growth_ratio_ttm`
- `$return_on_asset_ttm`
- `$return_on_invested_capital_ttm`
- `$total_asset_turnover_ttm`

## 2. Single-atom fields (one form tested only)

**3** fields have been tried under **only one** atom family. Other atom forms are unverified.

- `$open` — only `CrossFieldCov`
- `$pcf_ratio` — only `CrossFieldCov`
- `$return_on_equity_ttm` — only `CsRank`

## 3. Coverage matrix

| Field | CsRank | TsRank | Mean | Std | Skew | AnnualChange | DeviationFromMA | PairwiseRatio | CrossFieldCov | Σ |
|---|---|---|---|---|---|---|---|---|---|---|
| `$account_receivable_turnover_rate_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$book_value_per_share_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$current_ratio_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$debt_to_asset_ratio_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$debt_to_equity_ratio_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$gross_profit_margin_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$inventory_turnover_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$net_asset_growth_ratio_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$net_profit_growth_ratio_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$operating_cash_flow_per_share_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$operating_profit_margin_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$operating_revenue_growth_ratio_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$return_on_asset_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$return_on_invested_capital_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$total_asset_turnover_ttm` | · | · | · | · | · | · | · | · | · | 0 |
| `$open` | · | · | · | · | · | · | · | · | 1 | 1 |
| `$pcf_ratio` | · | · | · | · | · | · | · | · | 1 | 1 |
| `$return_on_equity_ttm` | 1 | · | · | · | · | · | · | · | · | 1 |
| `$eps_ttm` | 1 | · | · | · | · | · | · | 1 | · | 2 |
| `$peg_ratio_ttm` | 1 | · | 1 | · | · | · | · | · | · | 2 |
| `$market_cap` | 1 | · | · | · | · | · | · | 2 | · | 3 |
| `$pcf_ratio_total_ttm` | · | 1 | 1 | · | · | · | · | · | 1 | 3 |
| `$circ_market_cap` | · | · | 3 | · | · | · | · | 2 | · | 5 |
| `$dividend_yield_ttm` | 6 | · | 1 | · | · | · | · | · | 1 | 8 |
| `$ps_ratio` | 2 | · | 4 | · | · | · | · | 2 | · | 8 |
| `$low` | · | · | 2 | · | · | · | · | 10 | 1 | 13 |
| `$pb_ratio` | 6 | · | 12 | · | · | · | · | 2 | 1 | 21 |
| `$pe_ratio` | 6 | · | 10 | 1 | · | · | · | 3 | 2 | 22 |
| `$high` | · | · | 12 | · | · | · | · | 12 | 1 | 25 |
| `$close` | · | 5 | 11 | 11 | · | · | 3 | 5 | 4 | 39 |
| `$num_trades` | 1 | · | 7 | 1 | · | · | · | 30 | 4 | 43 |
| `$volume` | · | · | 12 | 2 | · | · | · | 36 | 4 | 54 |
| `$turnover_rate` | 3 | 2 | 36 | 10 | · | · | · | 3 | 2 | 56 |
| `$amount` | · | 1 | 50 | 14 | 2 | · | · | 52 | 3 | 122 |

## 4. Recommended baseline candidates

For each untouched field, run a `CsRank` + `TsRank-60` baseline **before** any composite. For single-atom fields, fill the most informative remaining atom (`AnnualChange` for fundamentals, `Std/Skew` for price-volume).

### Untouched-field baselines (priority: highest)

- `$account_receivable_turnover_rate_ttm`:
  - `CsRank($account_receivable_turnover_rate_ttm)`
  - `TsRank($account_receivable_turnover_rate_ttm, 60)`
  - `Sub($account_receivable_turnover_rate_ttm, Ref($account_receivable_turnover_rate_ttm, 252))`
- `$book_value_per_share_ttm`:
  - `CsRank($book_value_per_share_ttm)`
  - `TsRank($book_value_per_share_ttm, 60)`
  - `Sub($book_value_per_share_ttm, Ref($book_value_per_share_ttm, 252))`
- `$current_ratio_ttm`:
  - `CsRank($current_ratio_ttm)`
  - `TsRank($current_ratio_ttm, 60)`
  - `Sub($current_ratio_ttm, Ref($current_ratio_ttm, 252))`
- `$debt_to_asset_ratio_ttm`:
  - `CsRank($debt_to_asset_ratio_ttm)`
  - `TsRank($debt_to_asset_ratio_ttm, 60)`
  - `Sub($debt_to_asset_ratio_ttm, Ref($debt_to_asset_ratio_ttm, 252))`
- `$debt_to_equity_ratio_ttm`:
  - `CsRank($debt_to_equity_ratio_ttm)`
  - `TsRank($debt_to_equity_ratio_ttm, 60)`
  - `Sub($debt_to_equity_ratio_ttm, Ref($debt_to_equity_ratio_ttm, 252))`
- `$gross_profit_margin_ttm`:
  - `CsRank($gross_profit_margin_ttm)`
  - `TsRank($gross_profit_margin_ttm, 60)`
  - `Sub($gross_profit_margin_ttm, Ref($gross_profit_margin_ttm, 252))`
- `$inventory_turnover_ttm`:
  - `CsRank($inventory_turnover_ttm)`
  - `TsRank($inventory_turnover_ttm, 60)`
  - `Sub($inventory_turnover_ttm, Ref($inventory_turnover_ttm, 252))`
- `$net_asset_growth_ratio_ttm`:
  - `CsRank($net_asset_growth_ratio_ttm)`
  - `TsRank($net_asset_growth_ratio_ttm, 60)`
  - `Sub($net_asset_growth_ratio_ttm, Ref($net_asset_growth_ratio_ttm, 252))`
- `$net_profit_growth_ratio_ttm`:
  - `CsRank($net_profit_growth_ratio_ttm)`
  - `TsRank($net_profit_growth_ratio_ttm, 60)`
  - `Sub($net_profit_growth_ratio_ttm, Ref($net_profit_growth_ratio_ttm, 252))`
- `$operating_cash_flow_per_share_ttm`:
  - `CsRank($operating_cash_flow_per_share_ttm)`
  - `TsRank($operating_cash_flow_per_share_ttm, 60)`
  - `Sub($operating_cash_flow_per_share_ttm, Ref($operating_cash_flow_per_share_ttm, 252))`
- `$operating_profit_margin_ttm`:
  - `CsRank($operating_profit_margin_ttm)`
  - `TsRank($operating_profit_margin_ttm, 60)`
  - `Sub($operating_profit_margin_ttm, Ref($operating_profit_margin_ttm, 252))`
- `$operating_revenue_growth_ratio_ttm`:
  - `CsRank($operating_revenue_growth_ratio_ttm)`
  - `TsRank($operating_revenue_growth_ratio_ttm, 60)`
  - `Sub($operating_revenue_growth_ratio_ttm, Ref($operating_revenue_growth_ratio_ttm, 252))`
- `$return_on_asset_ttm`:
  - `CsRank($return_on_asset_ttm)`
  - `TsRank($return_on_asset_ttm, 60)`
  - `Sub($return_on_asset_ttm, Ref($return_on_asset_ttm, 252))`
- `$return_on_invested_capital_ttm`:
  - `CsRank($return_on_invested_capital_ttm)`
  - `TsRank($return_on_invested_capital_ttm, 60)`
  - `Sub($return_on_invested_capital_ttm, Ref($return_on_invested_capital_ttm, 252))`
- `$total_asset_turnover_ttm`:
  - `CsRank($total_asset_turnover_ttm)`
  - `TsRank($total_asset_turnover_ttm, 60)`
  - `Sub($total_asset_turnover_ttm, Ref($total_asset_turnover_ttm, 252))`

### Single-atom baselines (priority: medium)

- `$open` (CrossFieldCov done, missing CsRank): `CsRank($open)`
- `$open` (CrossFieldCov done, missing TsRank): `TsRank($open, 60)`
- `$pcf_ratio` (CrossFieldCov done, missing CsRank): `CsRank($pcf_ratio)`
- `$pcf_ratio` (CrossFieldCov done, missing TsRank): `TsRank($pcf_ratio, 60)`
- `$return_on_equity_ttm` (CsRank done, missing TsRank): `TsRank($return_on_equity_ttm, 60)`
- `$return_on_equity_ttm` (CsRank done, missing AnnualChange): `Sub($return_on_equity_ttm, Ref($return_on_equity_ttm, 252))`

