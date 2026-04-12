---
name: factor-idea
description: Phase 1 START+DESIGN — 选方向、设计候选、冻结 manifest
user_invocable: true
---

# /factor-idea — Phase 1 START+DESIGN

## R2 职责分工

| 角色 | 职责 |
|---|---|
| **Python** | refresh INDEX stats, DSL whitelist validation, Python file AST checking, freeze manifest.yaml, audit batch_goal length |
| **LLM** | read INDEX, select direction, decide batch_goal and active threads, generate 5-10 candidate expressions with rationale |

核心产出：
1. `vault/directions/{direction}.md`（若新建方向）
2. `batches/batch_{N}/manifest.yaml`（冻结的候选清单）

---

## Direction 选择

**一个 batch 只对应一个 direction**（不支持混方向 batch）。

LLM 读 INDEX.md → 按优先级选取 direction → 跟随 wikilink 读 direction.md 全文。若现有方向均不适合，创建新 `vault/directions/{tag}.md`。

---

## Direction.md 完整结构

### Frontmatter

```yaml
---
direction_tag: fundamental_price_divergence
status: productive           # exploring | productive | saturated | dead | merged
priority: high               # high | medium | low
rounds: 5                    # Python auto-update
admits: 3                    # Python auto-update
last_batch: batch_103        # Python auto-update
last_activity: 2026-04-11    # Python auto-update
created_batch: batch_099     # 初次创建时固定
members: [F018, F019, F020]  # Python auto-update
merged_into: null            # 仅 status=merged 时有值
---
```

| 字段 | 谁更新 | 何时 |
|---|---|---|
| `direction_tag` | LLM | 新建时（不变） |
| `status` / `priority` | **LLM** | Phase 4 Narrative Log 或 Phase 5 重写 |
| `rounds` / `admits` / `last_batch` / `last_activity` / `members` | **Python** | Phase 4 archive 后自动 |

### Body（LLM 完全维护）

```markdown
## Hypothesis
基本面改善速度 × 便宜估值 conditioner → barra-clean 价值重估 alpha。
<经济学逻辑 2-3 段>

## Current Focus
当前最值得探索的方向和下一步计划。

## Threads

### T001: PE/PB conditioner 最优选择 [◉ ACTIVE]
**Question**: PE/PB/PS 哪种 conditioner 最 barra-clean？
**Evidence trail**:
- batch_101: C003 PE → style_r2=0.12（太脏）
- batch_102: C004 PB → style_r2=0.08（acceptable）
**Next probes**: PS variant, dual conditioner

### T002: 80d lookback 减少 crowding [✓ ANSWERED batch_103]
**Question**: 80d lookback 是否减少 crowding？
**Answer**: 是。F020 (80d) crowding=low vs C004 (60d) crowding=medium。

## Known Failures
- `Mul($pe_ratio, $close)` → pure size proxy, corr=0.45 to $market_cap
- 40d lookback → IC collapse below 0.01

## Related
- [[../lessons#Structural Constraints]]
- [[timing_range]] — similar conditioner issue

## Narrative Log
### 2026-04-11 batch_103
Admitted [[../factors/F020|F020]] triple 80d PB。
Rejected: C002 (weak), C005 (style contamination).
T002 answered: 80d is the sweet spot.
→ Next: explore PS variant + dual conditioner (T001 still active)
```

### Thread 概念

Thread 是 direction.md body 中的 `###` 子节，代表跨多个 batch 逐步回答的**开放研究问题**。

| 状态标记 | 含义 |
|---|---|
| `[◉ ACTIVE]` | 正在探索的子问题 |
| `[✓ ANSWERED batch_X]` | 已回答（admit 或 refute） |
| `[✗ DISPROVEN batch_X]` | 子假设被证伪 |

Thread 结构：Question → Evidence trail → Answer/Next probes。

**Thread 生命周期完全由 LLM 维护**。Python 不管理 thread 状态、不校验 thread 数量、不自动更新 thread 标记。LLM 在 Phase 1 创建新 thread，在 Phase 4 更新 evidence 和状态标记。

---

## Direction 生命周期

| 状态 | 定义 | 转换条件 |
|---|---|---|
| **exploring** | 新方向，未 admit | 首次 admit → `productive` |
| **productive** | 有 admit，持续有 alpha | 连续 2+ batch reject > 80% → `saturated` |
| **saturated** | ROI 低，不值得继续 | 发现新角度 → `productive`（可复活）|
| **dead** | 假设被证伪 | **不可逆** |
| **merged** | 并入另一方向 | 设置 `merged_into: {target_tag}` |

状态由 **LLM** 修改 frontmatter（在 Narrative Log 中说明理由）。Python 只校验值合法。

---

## 步骤

### Step 1 — Python refresh INDEX lower half

Python 自动刷新 `vault/INDEX.md` 下半段的统计数据（方向列表、factor count、admit rate 等）。

### Step 2 — LLM read INDEX → select direction → read direction.md

1. 读 `vault/INDEX.md` → 全局 overview + 方向优先级排序
2. 选择目标 direction（或决定新建）
3. 跟随 wikilink 读 `vault/directions/{direction}.md` 全文（hypothesis + threads + narrative log）

### Step 3 — LLM decide batch_goal + active threads

1. 设定 `batch_goal`（>=30 chars，说明本 batch 要验证什么）
2. 声明 `active_threads_referenced`：本 batch 要推进的 thread 编号列表

### Step 4 — LLM write 5-10 candidate expressions + rationale

生成 5-10 个候选表达式。每个候选包含：

```yaml
- candidate_id: C001
  source_type: dsl          # 或 python
  expression: "Mul(Corr($close, $volume, 20), Std($volume, 20))"
  rationale: "测试 PV 相关性 × 波动率交互信号"
  parent_batch: batch_102                    # 可选
  parent_candidate_id: C004                  # 可选
  transformation: "extend_lookback_60d_to_80d"  # 可选

- candidate_id: C002
  source_type: python
  python_ref: "batches/batch_103/python_candidates/C002.py"
  dependencies: [numpy, pandas]
  rationale: "复现论文中的 cross-sectional dispersion 因子"
```

**DSL 优先**（R8）。只在以下情况用 Python escape hatch：
- DSL 无法表达的非平凡循环逻辑
- 显式复现已发表论文的 Python 参考实现
- 需要跨截面操作但 DSL 没有对应算子

### Step 5 — Python DSL whitelist validation

Python 自动检查所有 DSL 候选。以下是**完整的 DSL 算子白名单**：

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

**Python 候选 AST 检查**（`source_type == "python"`）：

**Import 白名单**：`numpy pandas scipy math typing dataclasses functools itertools __future__`
**禁止调用**：`eval exec compile __import__ open input breakpoint getattr setattr delattr`
**模块契约**：
```python
REQUIRED_FIELDS: list[str] = ["$close", "$volume"]  # 必须 $ 前缀
VECTORIZED: bool = True                              # 必须 True（R5）
def compute(df: pd.DataFrame) -> pd.Series:          # 唯一签名
    ...  # df 的 index 是 MultiIndex(time, symbol)
```

**重复检测**（DSL 候选）：
- canonical 化：去空格，交换律算子（`Add`, `Mul`）参数按字典序排列
- 对比 `vault/factors/F*.yaml` 已 admit 因子 → 拒绝
- 对比同 batch 内其他候选 → 拒绝
- retired 因子允许重投

### Step 6 — Python freeze manifest.yaml

Python 原子写入 `batches/batch_{N}/manifest.yaml`，审计 `batch_goal` >= 30 chars。

```yaml
batch_id: batch_103
round: 5
created_at: "2026-04-11T14:30:00+08:00"
direction: fundamental_price_divergence
direction_md_ref: vault/directions/fundamental_price_divergence.md
batch_goal: "验证 80d lookback 是否减少 C004 triple product crowding..."
active_threads_referenced: [T001, T002]
sample_policy:
  train_start: "2016-01-01"
  train_end: "2023-12-31"
  test_start: "2024-01-01"
  test_end: "2024-12-31"
candidates:
  - candidate_id: C001
    source_type: dsl
    expression: "Mul(Corr($close, $volume, 20), Std($volume, 20))"
    rationale: "测试 PV 相关性 × 波动率交互信号"
  - candidate_id: C002
    source_type: python
    python_ref: "batches/batch_103/python_candidates/C002.py"
    dependencies: [numpy, pandas]
    rationale: "复现论文中的 cross-sectional dispersion 因子"
  - candidate_id: C003
    source_type: dsl
    expression: "Mul(Corr($pe_ratio, Mean($close, 80), 80), $turnover_rate)"
    rationale: "80d lookback 版本 — 对比 60d 的 crowding"
    parent_batch: batch_102
    parent_candidate_id: C004
    transformation: "extend_lookback_60d_to_80d"
frozen_at: "2026-04-11T14:31:00+08:00"
```

冻结后 `state.yaml` 推进 phase。

---

## Obsidian Wikilink 约定

**Direction → Factor**：`[[../factors/F020|F020]]`
**Direction → Lessons**：`[[../lessons#Structural Constraints]]`
**Direction → Direction**：`[[timing_range]]`（同目录简写）
**Factor → Direction**：`[[../directions/fundamental_price_divergence#Hypothesis]]`
**Judge → Direction Thread**：`directions/fundamental_price_divergence.md#T001`（referenced_context 格式）
**INDEX → Direction**：`[[fundamental_price_divergence]]`

---

## 关键约束

- **不看 validation 数据**：候选设计基于 hypothesis + 先验知识，不基于回测结果
- **CsRank / CsZscore 始终在全市场计算**（`D.instruments("all")`），不受 mining universe 影响
- **A-share 约束**：不做空侧 alpha；因子与 `$market_cap` 相关性 `|corr| > 0.3` → 拒绝
- **一个 batch 一个 direction**：跨方向融合 → 新建 direction，不混 batch
- **R2 原则**：Python validates and freezes. LLM decides and creates. Python 不校验 direction 内容（hypothesis 长度、thread 数量等）——那是 LLM judgment
