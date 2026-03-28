# Logic-Guided Structured Evolution: Architecture Upgrade Spec

> **Date**: 2026-03-29
> **Status**: Draft
> **Branch**: TBD
> **Goal**: 将 9 篇 LLM 因子挖掘论文的核心 insight 融合进现有架构，突破 OHLCV 信号空间枯竭瓶颈

## 1. 问题陈述

当前系统（Ralph Loop）已录取 26/100 个因子，信号空间日益收窄。`mining-lessons.md` 结论：OHLCV 日频信号空间在 corr<0.7 下接近枯竭。

根本原因不是数据不够，而是**架构能力不足**：
- 因子只能用 Qlib DSL 一行表达式，无法表达条件逻辑、多状态切换
- LLM 自由发散生成因子，没有结构化的探索策略
- LLM 同时负责逻辑设计和参数选择，效率低
- 去重只靠 IC 相关性，抓不到结构等价的冗余因子
- 探索方向（directions）粒度太粗，LLM 经常在同一方向下生成同质化因子

## 2. 核心方法：逻辑引导的结构化进化

一句话：**LLM 负责"想"（市场逻辑 + 代码结构），机器负责"算"（参数调优 + 评估），记忆负责"不重复"（禁区 + 谱系）。**

### 2.1 核心 insight 来源

| 论文 | 拿什么 | 用在哪层 |
|------|-------|---------|
| FactorEngine | 三分离：LLM=逻辑，本地=参数，本地=计算 | 贯穿 L2-L3 |
| FactorEngine | 图灵完备 Python 因子 | L2 因子层 |
| AlphaLogics | 逻辑先行：先定义市场行为假设，再推导因子 | L4 逻辑层 |
| AlphaLogics | 内外双循环：内循环优化因子，外循环进化逻辑 | L4 逻辑层 |
| AlphaAgent | AST 结构去重 + 语义对齐检查 | L1 评估层 |
| CogAlpha | 7 层结构化搜索空间（按金融含义分类覆盖） | L4 逻辑层 |
| CogAlpha | 变异 + 交叉进化算子 | L3 进化层 |
| CogAlpha | 前视偏差自动检测 | L1 评估层 |
| FactorMiner | 禁区记忆（记住哪里不能去） | L2 因子层 |
| R&D-Agent | 调度器分配资源到不同方向 | L5 调度层 |

### 2.2 与现有系统对比

| | 现在 | 升级后 |
|--|-----|-------|
| LLM 职责 | 什么都做：想方向、写表达式、调参数 | 只做两件事：定义市场逻辑 + 写因子结构代码 |
| 因子来源 | LLM 自由发散，每次从头想 | 三条路：创新 / 变异已有因子 / 交叉两个因子 |
| 参数确定 | LLM 拍脑袋写死 | LLM 只定范围，Optuna 自动搜最优值 |
| 去重机制 | IC 相关性 > 0.7 拒绝 | IC 相关性 + AST 结构去重 + 禁区记忆 + 谱系图 |
| 因子表达力 | Qlib DSL 一行表达式 | DSL + Python（条件逻辑、多状态、算子组合） |
| 探索策略 | 人选方向，LLM 填表达式 | 逻辑层定方向，自适应配比定生成模式 |
| 自动化 | 人手动触发每一轮 | 半自动（人触发）+ 全自动（循环模式） |

## 3. 五层架构

```
┌─────────────────────────────────────────────┐
│  L5 调度层 (Scheduler)                       │
│  打分机制分配资源到各逻辑方向                    │
├─────────────────────────────────────────────┤
│  L4 逻辑层 (Market Logic Library)            │
│  结构化市场假设 + 分类覆盖 + 内外双循环          │
├─────────────────────────────────────────────┤
│  L3 进化层 (Evolution Engine)                │
│  三种生成模式 + 自适应配比 + 谱系追踪            │
├─────────────────────────────────────────────┤
│  L2 因子层 (Factor Runtime)                  │
│  双轨执行 + 算子复用 + 参数分离 + 禁区记忆       │
├─────────────────────────────────────────────┤
│  L1 评估层 (Evaluation Pipeline)             │
│  现有 6 阶段 + Python 因子支持 + 安全检查        │
└─────────────────────────────────────────────┘
```

## 4. L1 评估层（增强现有管道）

改动最小的一层。现有 6 阶段管道保留，增加三个能力。

### 4.1 支持 Python 因子评估

统一因子接口：

```python
class Factor:
    expr: str | None          # Qlib DSL，简单因子
    func: Callable | None     # Python 函数，复杂因子
    logic_id: str             # 所属市场逻辑
    source: "dsl" | "python"
```

Python 因子签名：接收 DataFrame（OHLCV） + params dict + ops 对象，返回 Series。评估器根据 `source` 选执行路径，后续所有阶段（IC、相关性、报告卡）完全共享。

### 4.2 前视偏差检测（来自 CogAlpha）

对 Python 因子自动检测：随机打乱时间轴后重算因子值，如果结果显著变化则标记警告。几行代码即可实现的安全护栏。

### 4.3 AST 结构去重（来自 AlphaAgent）

在现有 IC 相关性去重之外，新增一层：
- DSL 因子：利用 Qlib 内部的 `Expression.load()` 获取表达式树（返回 `ExpressionOps` 对象），递归遍历子节点计算子树编辑距离。不自建 parser，复用 Qlib 已有能力。
- Python 因子：提取 `ops.*` 调用序列作为签名（如 `[cs_rank, realized_vol, ts_decay]`），计算 Jaccard 相似度。

两个因子如果结构高度相似但 IC 相关性恰好低于阈值，标记"结构冗余"供 Judge 参考（不自动拒绝，留给 LLM 判断）。

## 5. L2 因子层（Factor Runtime）

### 5.1 OpsAdapter 接口

`OpsAdapter` 是 Python 因子调用算子的统一接口，封装所有已注册的 Qlib 算子：

```python
class OpsAdapter:
    """将 Qlib 算子暴露为 Python callable。

    所有方法接收 pd.Series 或 pd.DataFrame 列，返回 pd.Series。
    面板语义：输入已按 (date, symbol) 索引对齐，截面算子自动按 date 分组。
    """
    # 时序算子（单股票维度，沿时间轴计算）
    def std(self, series: Series, window: int) -> Series: ...
    def mean(self, series: Series, window: int) -> Series: ...
    def ts_decay(self, series: Series, window: int) -> Series: ...
    def ts_auto_corr(self, series: Series, window: int, lag: int) -> Series: ...
    def realized_vol(self, series: Series, window: int) -> Series: ...
    def ewm(self, series: Series, span: int) -> Series: ...
    def hhi(self, series: Series, window: int) -> Series: ...
    def delta(self, series: Series, period: int) -> Series: ...
    def ts_argmax(self, series: Series, window: int) -> Series: ...
    def ts_argmin(self, series: Series, window: int) -> Series: ...
    def ts_corr(self, x: Series, y: Series, window: int) -> Series: ...
    def ts_cov(self, x: Series, y: Series, window: int) -> Series: ...

    # 截面算子（同一天跨所有股票计算，自动 groupby date）
    def cs_rank(self, series: Series) -> Series: ...
    def cs_zscore(self, series: Series) -> Series: ...

    # 变换算子（逐元素）
    def signed_power(self, series: Series, exp: float) -> Series: ...
    def tanh(self, series: Series) -> Series: ...
    def safe_div(self, x: Series, y: Series) -> Series: ...
    def log1p_abs(self, series: Series) -> Series: ...
```

实现方式：每个方法内部调用对应的 Qlib `Operators._ops` 注册的算子类，处理好 NaN 和边界。截面算子自动按 MultiIndex 的 date 层 groupby。

### 5.2 Python 因子运行时

Python 因子以代码片段形式存在于候选批次 YAML 中，录取后持久化为独立 `.py` 文件。

**批次 YAML 格式扩展**：

```yaml
# storage/candidates/batch_019.yaml
candidates:
  - name: vol_regime_reversal_v2
    type: dsl
    expression: "CsRank(Std($close, 20))"
    logic_id: L001

  - name: conditional_vol_trend
    type: python
    logic_id: L003
    params: {window: 20, vol_thresh: 0.8}
    param_space: {window: [5, 60], vol_thresh: [0.5, 0.95]}
    code: |
      vol_regime = ops.cs_rank(ops.realized_vol(df["close"], params["window"]))
      trend = ops.ts_decay(df["close"].pct_change(), 10)
      high_vol = vol_regime > params["vol_thresh"]
      result = trend.copy()
      result[~high_vol] = -result[~high_vol]
      return result
```

**三分离原则**：
- LLM 只写 `code` 片段和 `param_space`，不写具体参数值
- 参数由 Optuna 在 `param_space` 范围内搜索最优值（见 5.4 参数优化）
- 计算全部本地执行，Python 因子在子进程沙箱中运行（见 5.3 沙箱执行）

**算子复用**：`compute()` 函数接收 `OpsAdapter` 实例（见 5.1）。LLM 被 prompt 引导使用 `ops.*` 而非手写 pandas rolling 等低级操作。算子是积木块，Python 是胶水 + 控制流。

**录取后持久化**（`storage/factors/FXXX_name.py`）：

```python
META = {
    "name": "conditional_vol_trend",
    "logic_id": "L003",
    "params": {"window": 20, "vol_thresh": 0.8},  # Optuna 搜出的最优值
    "param_space": {"window": (5, 60), "vol_thresh": (0.5, 0.95)},
    "lineage": {"parent": "F011", "mutation_type": "macro", "generation": 2},
}

def compute(df, params, ops):
    vol_regime = ops.cs_rank(ops.realized_vol(df["close"], params["window"]))
    trend = ops.ts_decay(df["close"].pct_change(), 10)
    high_vol = vol_regime > params["vol_thresh"]
    result = trend.copy()
    result[~high_vol] = -result[~high_vol]
    return result
```

### 5.3 沙箱执行

Python 因子在隔离环境中运行，防止 LLM 生成的代码影响主进程：

- **机制**：`multiprocessing.Process` + `pickle` 管道通信。主进程将 DataFrame 序列化发送，子进程执行 `compute()`，返回 Series 结果。
- **限制**：子进程中 `restricted_globals` 只暴露 `pd`, `np`, `ops`, `params`。无网络、无文件系统写入、无 `import`。
- **超时**：单因子计算 60 秒，超时自动 kill 并标记 `reject_reason: timeout`。
- **内存**：通过 `resource.setrlimit` 限制 4GB，超限 kill。
- **错误处理**：异常、超时、内存溢出统一返回 `FactorResult(status="error", reason=...)`，评估管道跳过该因子继续处理批次中其他因子。

### 5.4 参数优化（Optuna 集成）

对有 `param_space` 的 Python 因子，在进入 L1 评估管道之前自动搜参数：

- **目标函数**：训练期 Rank IC（与现有 Stage 1 一致）
- **搜索范围**：从候选 YAML 的 `param_space` 字段读取
- **试验次数**：30 次（`MiningConfig.optuna_trials`，可配置）
- **流程**：候选生成 → **Optuna 搜参** → 最优参数写回候选 dict → 进入现有 6 阶段评估
- **DSL 因子不受影响**：无 `param_space` 字段的因子跳过此步骤
- **资源控制**：每次试验复用同一份 DataFrame（内存中缓存），总超时 10 分钟/因子

### 5.5 因子库 schema 扩展

现有 `library.yaml` 和 `FactorLibrary.admit()` 只处理 `expression` 字段。扩展：

```yaml
# storage/library/library.yaml 中的一条记录
- factor_id: "025"
  name: "conditional_vol_trend"
  source: python               # 新增：dsl | python
  expression: null              # DSL 因子填表达式，Python 因子为 null
  code_path: "storage/factors/F025_conditional_vol_trend.py"  # 新增：Python 因子文件路径
  logic_id: "L003"             # 新增：所属市场逻辑
  category: "volume_price"
  ic: -0.041
  status: active
```

`FactorLibrary.admit()` 修改：
- `source` 字段决定录取路径：`dsl` 走现有逻辑存 `expression`，`python` 走新路径存 `code_path` 并持久化 `.py` 文件
- `_clean_factor_dict` 白名单增加 `source`, `code_path`, `logic_id`, `lineage` 字段
- `FactorPublisher` 对 Python 因子将 `code` 内容写入 `factor_meta.expression` 字段（兼容报告系统展示）

### 5.6 禁区记忆（来自 FactorMiner）

```yaml
# storage/memory/forbidden.yaml
forbidden_regions:
  - pattern: "Std($volume, *) / Mean($volume, *)"
    reason: "volume_cv 变体已饱和，5 次尝试全部 corr>0.7"
    added: 2026-03-15

  - pattern: "close.pct_change(*).rolling(*).std()"
    reason: "realized_vol 家族，与 F001/F024 高度相关"
    added: 2026-03-20
```

- `/idea` 生成候选时自动比对禁区，跳过匹配项
- `/judge` 拒绝因子时，同一模式被拒 3 次以上自动写入禁区
- 禁区有过期机制：当因子库发生替换（库结构变化），相关禁区可重新开放

### 5.7 因子谱系追踪（来自 FactorEngine CoE）

每个因子记录血统：

```yaml
lineage:
  parents: [F011]           # 列表：变异为单亲，交叉为双亲 [F001, F011]
  mutation_type: macro      # genesis(全新) / macro(LLM改结构) / micro(调参数) / crossover(交叉)
  logic_id: L003
  generation: 3
```

交叉因子的 `parents` 为双亲列表。变异计数按每个亲本独立统计（交叉算作两个亲本各一次衍生）。禁区归属跟随主亲本（`parents[0]`）的逻辑方向。

形成因子森林，LLM 在变异时能看到哪些路径已经走过。

## 6. L3 进化层（Evolution Engine）

### 6.1 三种因子生成模式

- **创新（Genesis）**：LLM 从市场逻辑出发生成全新因子。现有 `/idea` 的增强版。
- **变异（Mutate）**：取库中一个因子，LLM 做宏变异（换算子、加条件分支、改组合方式），Optuna 做微变异（搜参数）。
- **交叉（Crossover）**：取两个低相关因子，LLM 合并信号逻辑（如"高波动时用因子A信号，低波动时用因子B信号"）。

### 6.2 自适应配比

根据因子库规模和当前逻辑状态动态调整：

| 库规模 | 创新 | 变异 | 交叉 |
|--------|-----|------|------|
| <30 | 60% | 30% | 10% |
| 30-60 | 40% | 40% | 20% |
| 60+ | 20% | 50% | 30% |

额外规则：
- 某逻辑连续 3 轮 0 录取 → 该逻辑内切到纯变异/交叉
- 某因子已被变异 5 次以上且无录取 → 降低该因子的变异优先级

### 6.3 谱系图

```
F001 (std_returns_20)
├── F001_m1 (变异: 加 CsRank) → 拒绝，corr 0.85
├── F001_m2 (变异: 换 EWM) → 录取为 F025
│   └── F025_m1 (变异: 加条件门控) → 录取为 F031
└── F001 × F011 (交叉) → 拒绝，IC 不足
```

与禁区互补：禁区是"别去那片区域"，谱系是"这个因子的这条路走过了"。

## 7. L4 逻辑层（Market Logic Library）

### 7.1 市场逻辑定义

```yaml
# storage/logic/L003_volume_breakout.yaml
id: L003
name: 缩量横盘后放量突破
status: active            # active / saturated / dead
category: volume_price

hypothesis:
  condition: "成交量连续 N 天低于均值，同时价格振幅收窄"
  behavior: "后续大概率出现放量突破，方向跟随突破方向"
  timeframe: "5-20 交易日"
  direction: long_on_breakout

constraints:
  required_fields: [volume, close, high, low]
  suggested_ops: [Std, Mean, CsRank, TsDecay]
  window_range: [5, 60]
  output_sign: positive

stats:
  factors_generated: 12
  factors_admitted: 2
  best_ic: 0.041
  rounds_without_admit: 0
```

对比现有 directions：粒度从"volume 方向"细化到"缩量横盘后放量突破"，有结构化假设（条件/行为/时间/方向）和 constraints 字段约束 LLM 生成。

### 7.2 分类覆盖（来自 CogAlpha 7 层）

```yaml
# storage/logic/taxonomy.yaml
categories:
  market_structure:  "趋势、动量、均值回归"
  volume_price:      "量价关系、流动性、放量缩量"
  volatility:        "波动率聚集、regime 切换、波动率曲面"
  microstructure:    "日内模式、开盘收盘效应、涨跌停"
  cross_sectional:   "截面排名、相对强弱"
  tail_risk:         "极端事件、尾部风险、回撤几何"
  multi_scale:       "多周期共振、分形、跨频率信号"
```

**与现有 category 系统的关系**：现有 `MiningConfig.categories`（momentum, volatility, volume, regime, candlestick 等 11 个）是因子级别的标签，保留不变。新 taxonomy 是逻辑级别的分类，用于覆盖追踪。两者独立：一个 `volume_price` 逻辑下可以产出 `candlestick` 或 `volume` category 的因子。

LLM 在外循环生成新逻辑时，系统提示哪些 category 覆盖不足，引导系统性探索。

### 7.3 内外双循环（来自 AlphaLogics）

- **内循环**：在一个逻辑下生成因子 → 评估 → 录取/拒绝。就是现有 `/mine` 一轮。
- **外循环**：当内循环跑不动（连续 3 轮无录取），LLM 回到逻辑层面 — 修改假设、标记 dead、或生成新逻辑。

### 7.4 LLM 控制机制

L4 的核心不是算法，是**给 LLM 组装高质量的 prompt context**。LLM 在 `/idea` 执行时看到 5 层信息：

1. **分类覆盖地图**：哪些 category 空白（← CogAlpha）
2. **禁区列表**：哪些模式别再试（← FactorMiner）
3. **各逻辑的内循环证据**：什么有效什么无效（← AlphaLogics）
4. **谱系图**：哪些变异路径走过了（← FactorEngine）
5. **因子库当前状态**：26 个因子的分布

信息越结构化越完整，LLM 输出越受控。这与现有 skill prompt 设计思路一脉相承。

## 8. L5 调度层（Scheduler）

### 8.1 调度打分

每轮 `/mine` 前，对每个 active 逻辑计算优先级：

```
score(logic) = potential - fatigue

potential:
  +3  该 category 下录取因子少（覆盖不足）
  +2  最近一轮有录取（热方向）
  +1  最佳 IC 高于库平均（天花板高）

fatigue（上限 -5，防止永远无法恢复）:
  -N  连续 N 轮无录取（N capped at 5）
  -1  禁区数量 > 3（剩余空间小）
  -2  已生成 > 10 且录取 == 0（转化率为零）

新逻辑默认分: +3（鼓励探索新方向）
```

选得分最高的 1-2 个逻辑进入本轮内循环。全部负分 → 触发外循环。

### 8.2 两种运行模式

**半自动**（现阶段）：
1. 用户执行 `/mine`
2. 调度器推荐逻辑和生成模式
3. 用户确认或调整
4. 执行一轮 → judge → report
5. 等待用户下次触发

两种模式共享同一套调度逻辑，区别仅在于谁触发下一轮。

> **Future Work: 全自动模式**
> 半自动模式验证 L1-L4 后，可扩展为全自动循环（`/ralph-loop start --rounds N`），增加停止条件（连续 N 轮 0 录取 / token 预算 / 里程碑暂停）。核心调度逻辑相同，仅需加循环壳和预算控制。不在本次实现范围内。

### 8.3 Skill 映射

```
现有 Skill              升级后
────────────────────────────────────────
/mine                →  /mine（内部先调度再执行）
  /idea              →  调度器选逻辑 + /idea 在选定逻辑下生成
  /execute           →  /execute（不变）
  /judge             →  /judge + 更新逻辑状态 + 更新谱系
  /factor-report     →  /factor-report（不变）

新增:
/ralph-loop          →  全自动循环模式
/logic new           →  外循环：LLM 生成新市场逻辑
/logic review        →  查看所有逻辑状态和调度建议
```

## 9. 现有资产保护

- 26 个已录取因子不动，继续走 Qlib DSL 路径，`logic_id` 补为 `legacy`
- 现有评估管道（6 阶段）完整保留，Python 因子走新执行路径但共享后续阶段
- `storage/memory/directions/` 保留不动，作为历史记录。新逻辑写入 `storage/logic/`，两套并存，不做迁移。`/idea` skill 优先读 `storage/logic/`，降级读 `directions/` 作为上下文参考
- `storage/library/` schema 扩展（见 5.5），向后兼容
- 报告系统不变
- 所有现有 test 保持通过

## 10. 不做的事

- 不做因子-模型协同优化（R&D-Agent 路线）— 当前阶段先把因子挖好
- 不训练专用小模型（AlphaAgentEvo 路线）— 成本太高，当前规模不需要
- 不做组合级回测和交易成本 — 是重要的，但和这次架构升级正交，可以独立做
- 不做完整 MCTS 树搜索 — 自适应配比 + 谱系图已经覆盖核心 insight
- 不扩展数据源（$vwap/$amount 修复、分钟级数据）— 独立项目，不阻塞本次升级

## 11. 论文参考

1. **FAMA** (ACL 2024) — Cross-Sample Selection, Chain-of-Experience
2. **AlphaAgent** (KDD 2025) — AST subtree isomorphism, triple regularization
3. **R&D-Agent-Quant** (NeurIPS 2025) — Factor-model co-optimization, bandit scheduler
4. **FactorMiner** (Tsinghua 2026) — Correlation Red Sea, forbidden regions, experience memory
5. **Beyond Prompting** (HKUST 2026) — (minimal contribution)
6. **FactorEngine** (BUPT 2026) — Three separations, Turing-complete factors, MCTS, multi-island
7. **AlphaLogics** (Shenzhen U 2026) — Logic-first paradigm, dual loop, formalized market logics
8. **CogAlpha** (China Mobile 2025) — 7-level structured search, mutation/crossover, lookahead detection
9. **AlphaAgentEvo** (2025) — RL-trained specialist LLM
