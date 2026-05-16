# 日内 Primitive 层设计

> 日期：2026-05-02
>
> 状态：V0 已接入，后续继续扩展
>
> 范围：保留当前日频因子挖掘和 Phase2 评估体系，新增“日内高频数据低频化”的 Primitive 层，用分钟数据生产日频 primitive。

---

## 1. 背景

当前系统的快路径是：

```text
Phase1 manifest
  -> research.compute.data_bridge.eval_dsl_batch()
  -> Qlib D.features(fields=[...])
  -> Phase2Inputs
  -> research.phases.phase2_execute.run_phase2()
```

这个路径快，是因为 Qlib 能把多个日频 DSL 表达式一起批量计算。

但我们现在讨论的问题发生了变化：不是把系统改成分钟频，也不是替换 Qlib，而是要支持：

```text
用 1min / tick 等高频数据，生成每天每只股票一个值的日频 primitive。
```

例如：

```text
open_10m_ret_v1
tail_amount_share_20m_v1
intraday_vol_v1
reverse_imp_pos_v1
volume_hhi_v1
```

这些字段最终都是日频字段：

```text
1min bars -> date, symbol, feature_value
```

行业研报里大部分“高频因子”也是这个范式：先把日内信息低频化成日频/周频/月频信号，再用 IC、分层、中性化和组合回测评估。真正的 alpha 主要在“如何从日内结构生成 daily primitive”，而不是在后续写很复杂的日频 DSL。

因此系统重心应从：

```text
Qlib-centric daily DSL mining
```

扩展为：

```text
Primitive-engine-centric research + Qlib daily backend
```

Qlib 仍然保留，但定位是日频表达式后端，不是日内低频化语义层。

---

## 2. 当前代码接入点

当前相关模块：

```text
src/data/storage/timescale_storage.py
  已有 market_1min、market_5min、market_daily 表。

src/data/storage/frequency.py
  已有基础频率常量。

src/data/qlib_sync.py
  DataSynchronizer 负责 market_daily -> Qlib day bin。
  sync_minute_aggregates() 是分钟 -> 日频特征的早期原型。

src/research/compute/data_bridge.py
  Phase2 主入口。
  负责 init_qlib、eval_dsl_batch、market_daily cache、Barra、library signals、candidate signals。

src/research/phases/phase2_execute.py
  日频评估器。输入 factor_series 和 forward_returns_by_horizon。

src/research/storage/paths.py
  当前 storage/cache 路径注册中心。
```

当前主要问题：

```text
src/data/qlib_sync.py::sync_minute_aggregates()
```

把数据读取、分钟聚合、feature 定义和 Qlib 导出混在一个方法里，而且有 per-symbol/day 循环。它可以作为原型，但不适合作为长期架构。

---

## 3. 统一设计原则

最高原则：

```text
高频数据低频化由我们自己的 Primitive Layer 负责；
Qlib 保留为高性能日频表达式 backend；
Phase2 继续作为日频评估体系。
```

目标链路：

```text
raw intraday data
  -> primitive materialization
  -> daily primitive store/cache
  -> isolated Qlib daily store 或 daily backend
  -> Qlib daily expression batch
  -> Phase2 daily evaluation
```

硬边界：

1. 原始 1min/tick 数据不能直接进入 Phase2。
2. 每个日内派生日频字段都必须有 registry spec。
3. primitive materialization 必须批量执行，不能每个候选重复扫分钟数据。
4. 最终 daily primitive 必须缓存并跨 mining round 复用。
5. `ret_1m`、`volume_mean`、mask 等中间列默认不长期保存。
6. Qlib 不负责日内窗口、mask、masked reducer、available_time、min_bar_ratio 等语义。

---

## 4. 目标架构

```text
LLM / Phase1
  生成候选，候选引用 daily primitive
        |
        v
Pre-Phase2 primitive materialization
  收集 manifest 里的 primitive dependencies
  查询 registry + cache
  批量物化缺失或过期 primitive
  暴露给 daily backend
        |
        v
Qlib daily backend
  eval_dsl_batch(daily expressions)
        |
        v
Phase2
  IC / quintile / feasibility / Barra / redundancy / diagnostics
        |
        v
Judge / Archive / Consolidate
```

新增组件：

```text
Intraday Primitive Layer
```

它负责：

```text
primitive registry
primitive templates
minute materializer
primitive cache/store
Qlib daily export bridge
manifest dependency resolver
leakage / availability checks
```

---

## 5. 推荐模块结构

MVP 阶段贴合当前仓库结构，不新增过重的平台层。

```text
src/data/primitive/
  __init__.py
  schema.py              # PrimitiveSpec schema / validation
  registry.py            # 加载 registry yaml，计算 spec_hash，解析 feature_id
  templates.py           # 固定 primitive 模板
  cache.py               # primitive cache hit/miss、日期覆盖检查

src/data/materializers/
  __init__.py
  minute_materializer.py # 批量 1min -> daily primitive wide panel

src/data/exporters/
  __init__.py
  qlib_daily_exporter.py # daily primitive panel -> isolated Qlib day bin

src/research/compute/
  primitive_bridge.py    # Pre-Phase2: ensure primitives materialized
```

当前 V0 已落地的文件：

```text
src/data/primitive/schema.py
src/data/primitive/registry.py
src/data/primitive/cache.py
src/data/materializers/minute_materializer.py
src/data/exporters/qlib_daily_exporter.py
src/research/compute/primitive_bridge.py
```

现有 Phase2 接入点：

```text
src/research/compute/data_bridge.py
  build_phase2_inputs() 在 init_qlib() 前执行 ensure_primitives_materialized()

src/research/phases/phase2_execute.py
  result.yaml 写入 batch 级 primitive_materialization
  candidates[].primitive_dependencies / primitive_provenance 透传到下游
```

存储结构：

```text
storage/vault/primitive_registry/minute/
  open_10m_ret_v1.yaml
  tail_amount_share_20m_v1.yaml
  reverse_imp_pos_v1.yaml

storage/cache/primitive_store/minute/
  feature_id=open_10m_ret_v1/
    spec_hash=.../
      year=2024.parquet

storage/cache/primitive_panels/
  batch_042.parquet      # 可选，用于批次宽表诊断
```

Qlib 实验输出：

```text
~/.qlib/qlib_data/cn_data_1d_exp/
```

第一版默认写入 `storage/config.yaml.qlib_data_dir`。如果使用实验目录：

```yaml
primitive:
  qlib_data_dir: ~/.qlib/qlib_data/cn_data_1d_exp
```

这个目录必须能同时读取基础日频字段和 primitive 字段。否则类似
`Corr($tail_amount_share_20m_v1, $amount, 20)` 的表达式会因为基础字段缺失而失败。

---

## 6. Primitive Registry 规范

每个日频 primitive 必须有 YAML spec。

示例：

```yaml
feature_id: tail_amount_share_20m_v1
feature_type: primitive
source_type: minute_bar
source_freq: 1min
output_freq: daily

template: window_share
params:
  field: amount
  numerator_window: "14:40-15:00"
  denominator_window: "09:30-15:00"

time_semantics:
  event_time: "T intraday"
  available_time: "T 15:00"
  allowed_labels:
    - close_to_close_1d

data_policy:
  include_auction: false
  min_bar_ratio: 0.8
  missing_bar: ignore
  suspended_day: nan

cache:
  data_version: market_1min_v1
  calendar_version: cn_a_session_v1
  engine_version: primitive_engine_v0.1

status: experimental
```

必需字段：

```text
feature_id
source_type
source_freq
output_freq
template
params
time_semantics.available_time
data_policy
cache.data_version
cache.calendar_version
cache.engine_version
status
```

registry loader 需要计算：

```text
spec_hash = sha256(canonical_yaml_without_runtime_fields)
```

cache key 至少包含：

```text
feature_id
spec_hash
data_version
calendar_version
date_range
engine_version
```

---

## 7. MVP Primitive 模板

第一版不要做自由 DSL，先做固定模板。

### 7.1 window_share

```text
Sum(field in numerator_window) / Sum(field in denominator_window)
```

例子：

```text
tail_amount_share_20m_v1
open_30m_volume_share_v1
```

### 7.2 window_ratio

```text
Sum(field in left_window) / Sum(field in right_window)
```

例子：

```text
morning_vs_afternoon_open_volume_ratio_v1
```

### 7.3 window_return

```text
Last(close in window) / First(open in window) - 1
```

例子：

```text
open_10m_ret_v1
open_30m_ret_v1
tail_30m_ret_v1
```

### 7.4 distribution_stats

```text
Std(series)
Skew(series)
Kurt(series)
HHI(series)
Quantile(series, q)
```

例子：

```text
intraday_vol_v1  = Std(Return1m(close))
intraday_skew_v1 = Skew(Return1m(close))
volume_hhi_v1    = Sum((volume / Sum(volume)) ** 2)
amount_hhi_v1    = Sum((amount / Sum(amount)) ** 2)
```

### 7.5 masked_return_mean

```text
Mean(Return1m(close) where mask)
```

例子：

```text
reverse_imp_pos_v1 =
  -Mean(ret_1m where ret_1m > 0 and volume > Mean(volume) + Std(volume))
```

这个模板要求 batch 内复用：

```text
ret_1m
volume_mean
volume_std
volume_up_mask
positive_return_mask
```

### 7.6 price_volume_corr

```text
Corr(series_a, series_b within symbol-day)
```

例子：

```text
corr_ret_amount_v1
corr_price_amount_v1
```

---

## 8. 批量执行语义

materializer 的入口必须是多个 primitive：

```python
materialize_many(
    feature_ids=[
        "open_10m_ret_v1",
        "tail_amount_share_20m_v1",
        "intraday_vol_v1",
        "reverse_imp_pos_v1",
    ],
    start="2015-01-01",
    end="2025-12-31",
)
```

不能这样做：

```text
每个 primitive 单独 scan market_1min
```

应该这样做：

```text
1. 读取请求日期范围内所需 raw columns
2. 添加共享列：date、time-of-day、session/window flags
3. 一次性计算共享序列：ret_1m、amount_sum_full_day、volume_mean、volume_std
4. 用一次或少数几次 groupby 输出所有 requested reducers
5. 返回 daily wide panel
```

输出示例：

```text
date        symbol    open_10m_ret_v1  tail_amount_share_20m_v1  intraday_vol_v1
2024-01-02  SH600000  0.0031           0.1224                    0.0018
2024-01-02  SZ000001 -0.0017           0.0982                    0.0024
```

---

## 9. 缓存策略

长期缓存：

```text
最终 daily primitive values
```

默认不长期缓存：

```text
ret_1m
volume_mean
volume_std
window masks
condition masks
```

只有当中间列被长期大量复用时，才升级成正式 primitive。

重新物化只在以下情况触发：

```text
1. feature_id 第一次出现
2. spec_hash 改变
3. data_version 改变
4. calendar/session version 改变
5. engine_version 改变
6. 请求日期范围超过已有 cache 覆盖范围
7. cache 缺失或损坏
```

每轮 mining 只做依赖和 cache 检查，不应该重算所有日内信息。

---

## 10. Phase2 接入方式

当前 `src/research/compute/data_bridge.py::build_phase2_inputs()` 仍然是 Phase2 主装配点。

在解析 config/range 后、Qlib daily expression 计算前新增：

```text
ensure_primitives_materialized(batch_manifest, paths, config)
```

建议位置：

```text
build_phase2_inputs()
  init_qlib(...)
  resolve train/validation ranges
  ensure_primitives_materialized(...)
  load_market_data(...)
  build_barra_style_matrix(...)
  load_library_signals(...)
  evaluate_candidates(...)
  return Phase2Inputs
```

MVP manifest 只做兼容扩展：

```yaml
candidates:
  - candidate_id: C001
    source_type: dsl
    expression: Rank($tail_amount_share_20m_v1)
    primitive_dependencies:
      - tail_amount_share_20m_v1
    hypothesis: "尾盘成交额占比高可能代表拥挤交易，次日存在反转风险。"
```

bridge 负责：

```text
1. 收集 primitive_dependencies
2. 解析 registry specs
3. 检查 primitive cache 覆盖
4. 批量物化缺失 features
5. 导出到 configured Qlib daily backend
6. 继续走现有 eval_dsl_batch()
```

Phase2 本身保持日频：

```text
factor_series: MultiIndex(datetime, instrument)
forward returns: returns_1d / returns_3d / ...
IC series: daily
diagnostics: daily parquet
```

---

## 11. Qlib 定位

Qlib 继续负责：

```text
daily field loading
daily rolling ops
cross-sectional rank
Ref / Mean / Std / Corr over daily panels
batch expression execution
```

Qlib 不负责：

```text
intraday window semantics
symbol-day masks
masked reducers
available_time
min_bar_ratio
primitive registry
spec_hash cache
multi-source point-in-time rules
```

后续可以 benchmark Qlib 1min：

```text
IntradayEngine backend = qlib_1min | polars | duckdb | timescale_sql
```

但即使用 Qlib 1min，Primitive Layer 仍然拥有 registry、planner、cache、daily output semantics。

---

## 12. MVP 任务

### V0：打通闭环

目标：

```text
1min bars -> daily primitive -> isolated Qlib daily store -> existing Phase2
```

任务：

1. 增加 primitive registry schema 和 loader。
2. 增加 5-10 个固定 minute primitives。
3. 增加 `MinuteMaterializer.materialize_many()`。
4. 增加 primitive parquet cache。
5. 增加 daily primitive Qlib exporter，输出到 `cn_data_1d_exp`。
6. 增加 `primitive_bridge.ensure_primitives_materialized()`。
7. 扩展 manifest，支持 `primitive_dependencies`。
8. 用新字段上的简单 Qlib expression 跑通 Phase2。

初始 primitives：

```text
open_10m_ret_v1
open_30m_ret_v1
tail_30m_ret_v1
tail_amount_share_20m_v1
intraday_vol_v1
volume_hhi_v1
amount_hhi_v1
reverse_imp_pos_v1
```

验证：

```text
pytest tests/data/primitive/
pytest tests/research/compute/test_primitive_bridge.py
PYTHONPATH=src python3 -m research execute <batch_with_primitive_dependencies>
```

### V1：批量依赖和缓存纪律

目标：

```text
多个候选共享 primitive 依赖，不重复扫描 raw minute data。
```

任务：

1. 按 feature/date range 检查 cache coverage。
2. 增加 batch wide panel cache。
3. 归一化重复 primitive dependency。
4. 在 result metadata 中记录 primitive cache status。
5. 增加 primitive cache health audit 命令。

### V2：Factor IR

目标：

```text
候选从 Qlib expression only 进化到 Factor IR。
```

任务：

1. 定义 Factor IR schema。
2. IR -> primitive tasks。
3. IR -> Qlib daily expressions。
4. 基于 available_time 和 label 增加 leakage checker。
5. admitted factor 归档 primitive dependencies 和 spec hashes。

### V3：多源 primitive

目标：

```text
扩展到 tick / fundamental / event/news。
```

任务：

1. Tick adapter/materializer。
2. Fundamental point-in-time adapter。
3. Event/news aggregation adapter。
4. 统一 event_time、available_time、decision_time。

### V4：可选 native daily backend

目标：

```text
Qlib 在部分日频表达式上可替换。
```

任务：

1. 实现 Rank/Ref/Mean/Std/Corr 的小型 native daily backend。
2. 与 Qlib 输出对齐测试。
3. 只在速度或维护性更好时启用。

---

## 13. MVP 非目标

V0 不做：

```text
自由 intraday DSL
tick data
fundamental/news primitives
完整 Factor IR 迁移
Qlib 替换
完整 AST optimizer
长期缓存中间分钟列
多 label 评估
intraday Phase2
```

MVP 只证明：

```text
现有日频 mining loop 能否评估以 minute-derived daily primitive 为输入的因子。
```

---

## 14. 验收标准

V0 完成标准：

1. manifest 可以引用至少一个 minute-derived primitive。
2. Pre-Phase2 能物化缺失 primitive 并缓存。
3. primitive 能作为 Qlib daily field 出现在隔离 Qlib 目录。
4. `eval_dsl_batch()` 能计算基于该字段的表达式。
5. 现有 Phase2 能正常产出 result.yaml。
6. 重跑同一个 batch 命中 primitive cache，不重新全量扫描分钟表。
7. admitted factor 归档 primitive dependencies 和 spec hashes。

---

## 15. 总结

系统不应该变成分钟频研究系统。

目标是：

```text
带有高频低频化 Primitive 层的日频因子研究系统
```

研究重心转移到：

```text
如何从日内结构定义有用的 daily primitive
```

工程重心转移到：

```text
批量物化、缓存正确性、时间语义、Qlib 日频集成
```

最终定位：

```text
Primitive Layer = intraday-to-daily 语义所有者
Qlib = daily expression backend
Phase2 = daily evaluator
```
