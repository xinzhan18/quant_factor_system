# TODO: 存储不复权价格 + 复权因子（回测用）

## 背景
当前 price_daily 存的是前复权价格，对因子计算（IC/IR）没有影响，但回测需要真实成交价。

## 需要做的事

1. **拉不复权价格** — `rq.get_price(adjust_type="none")` → price_daily 新增 `open_raw/high_raw/low_raw/close_raw` 列
2. **拉复权因子** — `rq.get_ex_factor()` → 新建 `ex_factor` 表（ex_date, symbol, ex_factor），append-only
3. **DB 已加好列** — `ALTER TABLE price_daily ADD COLUMN IF NOT EXISTS open_raw/high_raw/low_raw/close_raw/adj_factor` 已执行

## 数据架构

```
price_daily (golden source)
  - OHLCV 前复权 → 因子计算用（同步到 Qlib）
  - OHLCV_raw 不复权 → 回测用（真实成交价）
  - volume/amount → 不受复权影响

ex_factor 表 (append-only)
  - 每行 = 一次除权事件，不可变
  - 前复权价 = 不复权价 × ∏(该天之后的 ex_factor) / ∏(全部 ex_factor)
```

## 为什么不急
- 因子挖掘阶段只需要 IC/IR，前复权收益率 = 不复权收益率，结果一致
- 回测阶段才需要真实价格，目前还没到那一步
