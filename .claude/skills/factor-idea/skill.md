---
name: factor-idea
description: Phase 1 START+DESIGN — 选方向、设计候选、冻结 manifest
user_invocable: true
---

# /factor-idea — Phase 1 候选设计

## 职责

为 `/factor-mine` 的 Phase 1 提供候选列表并冻结 manifest。单独调用时跳过 Phase 2-5。

## 步骤

### Step 1 — 读上下文
1. 读 `vault/directions/{direction}.md` 的 Hypothesis + 活跃 Threads
2. 读 `vault/lessons.md` 的 Structural Constraints + Operator Registry + Data Facts
3. 读 `vault/INDEX.md` 的最近 batch 统计（了解该 direction 已跑多少轮、admit 多少）

### Step 2 — 设计候选
生成 5-10 个候选表达式。每个候选包含：

```yaml
- candidate_id: C001
  source_type: dsl          # 或 python
  expression: "Mul(Corr($close, $volume, 20), Std($volume, 20))"  # DSL
  # path: batches/batch_{N}/python_candidates/C001.py             # Python
```

**DSL 优先**（R8）。只在以下情况用 Python escape hatch：
- DSL 无法表达的非平凡循环逻辑
- 显式复现已发表论文的 Python 参考实现
- 需要跨截面操作但 DSL 没有对应算子

### Step 3 — DSL 白名单验证

Python 自动检查，LLM 确认。以下是**完整的 DSL 算子白名单**：

**数学/逻辑**：`Add Sub Mul Div Abs Log Power Sign Not And Or Eq Ne Gt Ge Lt Le`
**滚动统计**：`Mean Std Var Skew Kurt Med Mad Sum Prod Count Quantile Min Max`
**时间序列**：`Ref Delta IdxMax IdxMin Correlation Corr Cov Rank Mask EMA WMA Slope Rsquare Resi`
**条件**：`If IfElse Greater Less`
**自定义注册**：`SignedPower Tanh Exp Sigmoid Softmax Scale Zscore Winsorize TsDecay TsMomentum TsAutoCorr RealizedVol TsEntropy TsMax TsMin TsRank TsSkew TsKurt CsRank CsZscore CsDemean AmihudIlliq HHI`

**字段白名单**：`$open $high $low $close $volume $amount $pe_ratio $pb_ratio $ps_ratio $market_cap $circ_market_cap $turnover_rate`

**禁止**：
- `$vwap`（数据为零）
- `Neg()`（未注册，用 `Mul($x, -1)`）
- `SMA()`（未注册，用 `EMA` 或 `Mean`）
- 表达式深度 > 10 层嵌套

### Step 4 — Python 候选验证（R8 contract）

如果 `source_type == "python"`，Python AST 检查必须通过：

**Import 白名单**：`numpy pandas scipy math typing dataclasses functools itertools __future__`
**禁止调用**：`eval exec compile __import__ open input breakpoint getattr setattr delattr`
**模块契约**：
```python
REQUIRED_FIELDS: list[str] = ["$close", "$volume"]  # 必须 $ 前缀
VECTORIZED: bool = True                              # 必须 True（R5）
def compute(df: pd.DataFrame) -> pd.Series:          # 唯一签名
    ...  # df 的 index 是 MultiIndex(time, symbol)
```

### Step 5 — 重复检测

Python 对每个 DSL 候选做 canonical 化：
- 去除空格
- 对交换律算子（`Add`, `Mul`）的参数按字典序排列
- `Mul($volume, $close)` == `Mul($close, $volume)` → 重复

检测范围：
1. 对比 `vault/factors/F*.yaml` 的已 admit 因子 → 拒绝 `duplicate_of_existing_factor`
2. 对比同 batch 内的其他候选 → 拒绝 `duplicate_within_batch`
3. retired 的因子允许重投（不在检测范围内）

### Step 6 — 冻结 manifest

`batch_goal` 必须 ≥ 30 字符（防止 LLM 偷懒提交 "test"）。

Python 原子写入 `batches/batch_{N}/manifest.yaml`：

```yaml
batch_id: batch_103
direction: fundamental_price_divergence
batch_goal: "验证 80d lookback 是否减少 C004 triple product crowding..."
sample_policy_version: v3
candidates:
  - candidate_id: C001
    source_type: dsl
    expression: "Mul(Corr($close, $volume, 20), Std($volume, 20))"
    canonical: "Mul(Corr($close,$volume,20),Std($volume,20))"
  - candidate_id: C002
    source_type: python
    path: "batches/batch_103/python_candidates/C002.py"
```

冻结后 `state.yaml.current_batch_phase` 推进到 `"designed"`。

## 关键约束

- **不看 validation 数据**：候选设计基于 hypothesis + 先验知识，不基于回测结果
- **CsRank / CsZscore 始终在全市场计算**（`D.instruments("all")`），不受 mining universe 影响
- **A-share 约束**：不做空侧 alpha；因子与 `$market_cap` 相关性 `|corr| > 0.3` → 拒绝
