# TODO: 跨频率因子挖掘引擎（脱离 Qlib）

## 问题
Qlib 表达式引擎是单频率的，无法在因子表达式中直接操作分钟数据。当前只能预聚合分钟→日频特征，再用 Qlib 组合。这限制了挖掘空间——聚合方式是人定的，不能自动搜索。

## Qlib 在我们系统中实际只做两件事
1. 表达式解析+求值（字符串 → 计算图 → pandas Series）
2. 二进制数据存储格式（.day.bin）

评估逻辑（IC/IR/分层）、候选生成、审判流程、数据同步全是自己写的。Qlib 可替代。

## 目标架构：两层表达式引擎

```
因子 = DailyOp( MinuteAgg( minute_fields, agg_func, agg_params ), daily_window )

例如：
  Mean( RV($close_1min, 5), 20 )
       └── 第1层：分钟→日 ──┘  └ 第2层：日频滚动 ┘

  Corr( VolConc($volume_1min, 30min), $turnover_rate, 10 )
       └── 第1层：成交量集中度 ──────┘              └ 第2层 ┘
```

### 第1层：分钟→日聚合（新增）
- 输入：每天 ~240 根 1min bar
- 输出：每天 1 个标量
- 可搜索的聚合函数：
  - 已实现矩：RV, RSkew, RKurt（参数：窗口 1/5/15/30min）
  - 成交量分布：VolConc, VWAP_Dev, VolRatio（参数：时段）
  - 价格路径：MaxDD, DirChanges, IntraDayAutoCorr, PriceImpact
  - 时段分解：AM_Ret, PM_Ret, LunchGap, Last15_Ret
  - 信息论：RetEntropy, PV_MI

### 第2层：日频组合（现有）
- 用现有的 72 个算子对第1层输出做滚动/组合
- 可以混合日频字段（$close, $turnover_rate）和第1层输出

### 挖掘循环
- 候选生成同时搜索两层：聚合函数 × 聚合参数 × 日频组合
- 评估流程不变（IC/IR/相关性/分层）

## 实现路径
1. �� pandas/numpy 写自己的��达式求值器，替代 Qlib
2. 数据直接从 TimescaleDB 读（不再需要 .day.bin 中间格式）
3. 第1层聚合函数可注册，类似现有的自定义算子
4. 候选搜索空间：定义聚合模板 + 参数范围

## 前置条件
- ���前日频新字段（turnover/market_cap/PE）挖掘验证完成
- 确认 Qlib 日频挖掘的 ROI 已经饱和
- DB 里 market_1min 5.29亿行数据可用

## 数据规模考量
- 5495 只股票 × 2728 天 × 240 bar = ~36 亿次计算/因子
- 需要考虑计算效率：按股票分片 + 缓存聚合结果
