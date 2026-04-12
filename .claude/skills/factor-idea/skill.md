---
name: factor-idea
description: Phase 1 START+DESIGN — 选方向、设计候选、冻结 manifest
user_invocable: true
---

# /factor-idea — Phase 1 候选设计

## 职责

为 `/factor-mine` 的 Phase 1 提供候选列表并冻结 manifest。单独调用时跳过 Phase 2-5。

核心产出：
1. `vault/directions/{direction}.md`（若新建方向）
2. `batches/batch_{N}/manifest.yaml`（冻结的候选清单）

---

## Direction 选择逻辑

**一个 batch 只对应一个 direction**（不支持混方向 batch）。

| 场景 | 判断标准 | 动作 |
|---|---|---|
| **继续现存 direction** | 候选表达式都指向同一个假设，是既有 threads 的自然延续 | 直接用该 direction |
| **新建 direction** | 候选假设与所有现存 direction 的 hypothesis 不对齐；或多个 direction 的融合 | 创建新 `vault/directions/{tag}.md` |
| **跨方向融合** | 两个方向的核心思路发现了强关联 | 创建**新 direction**（不混入现存的任何一个） |

---

## Direction.md 完整结构

### Frontmatter（Rule A — Python 机械字段 + LLM 状态字段）

```yaml
---
direction_tag: fundamental_price_divergence
status: productive           # exploring | productive | saturated | dead | merged
priority: high               # high | medium | low（INDEX 排序依据）
rounds: 5                    # Python Phase 4 自动 ++
admits: 3                    # Python Phase 4 自动 + N
last_batch: batch_103        # Python Phase 4 自动更新
last_activity: 2026-04-11    # Python Phase 4 自动更新
created_batch: batch_099     # 初次创建时固定
members: [F018, F019, F020]  # Python Phase 4 自动 append
merged_into: null            # 仅 status=merged 时有值
---
```

| 字段 | 谁更新 | 何时 |
|---|---|---|
| `direction_tag` | Python | 新建时（不变） |
| `status` / `priority` | **LLM** | Phase 4 Narrative Log 或 Phase 5 重写 |
| `rounds` / `admits` / `last_batch` / `last_activity` / `members` | **Python** | Phase 4 archive 后自动 |

### Body（Rule B — LLM 完全维护）

```markdown
## Hypothesis
基本面改善速度 × 便宜估值 conditioner → barra-clean 价值重估 alpha。
<经济学逻辑 2-3 段>

## Threads
### T001: PE/PB/PS 哪种 conditioner 最 barra-clean？ [◉ ACTIVE]
**Question**: ...
**Evidence trail**:
  - batch_101: C003 PE → style_r2=0.12（太脏）
  - batch_102: C004 PB → style_r2=0.08（acceptable）
**Next probes**: PS variant, dual conditioner

### T002: 80d lookback 是否减少 crowding？ [✓ ANSWERED batch_103]
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

Thread 是 direction 内部的**开放研究问题**，跨多个 batch 逐步回答。

| 状态 | 标记 | 含义 |
|---|---|---|
| **ACTIVE** | `[◉ ACTIVE]` | 正在被追问，每轮 batch 更新 evidence trail |
| **ANSWERED** | `[✓ ANSWERED batch_{N}]` | 问题已回答，不再追问 |
| **DISPROVEN** | `[✗ DISPROVEN batch_{N}]` | 路径被证伪 |

- **创建**：LLM 在 Phase 1 设计候选时或 Phase 4 发现新问题时
- **更新**：LLM 在 Phase 4 Narrative Log 中追加 evidence
- **关闭**：LLM 在 Phase 4 或 Phase 5 标记 ANSWERED / DISPROVEN
- **引用**：judge.md 通过 `referenced_context: directions/{dir}.md#T001`

---

## Direction 生命周期

| 状态 | 定义 | 转换条件 |
|---|---|---|
| **exploring** | 新方向，未 admit | 首次 admit → `productive` |
| **productive** | 有 admit，持续有 alpha | 连续 2+ batch reject > 80% → `saturated` |
| **saturated** | ROI 低，不值得继续 | 发现新角度 → `productive`（可复活）|
| **dead** | 假设被证伪 | **不可逆** |
| **merged** | 并入另一方向 | 设置 `merged_into: {target_tag}` |

状态由 **LLM 在 Phase 4 Narrative Log 中说明理由后修改 frontmatter**。Python 只校验值合法。

---

## 步骤

### Step 1 — 读上下文
1. 读 `vault/directions/{direction}.md` 的 Hypothesis + 活跃 Threads
2. 读 `vault/lessons.md` 的 Structural Constraints + Operator Registry + Data Facts
3. 读 `vault/INDEX.md` 的最近 batch 统计（了解该 direction 已跑多少轮、admit 多少）

### Step 2 — 设计候选
生成候选表达式。**数量由 LLM 自主决定**（建议 3-12 个，视方向广度和 thread 活跃度而定。窄方向 2-3 个够了，broad exploration 可以 10+）。每个候选包含：

```yaml
- candidate_id: C001
  source_type: dsl          # 或 python
  expression: "Mul(Corr($close, $volume, 20), Std($volume, 20))"  # DSL
  # path: batches/batch_{N}/python_candidates/C001.py             # Python
  lineage:                  # 可选，仅当候选是既有因子的变体时
    parent_batch: batch_102
    parent_candidate_id: C004
    transformation: "extend_lookback_60d_to_80d"
```

**DSL 优先**（R8）。只在以下情况用 Python escape hatch：
- DSL 无法表达的非平凡循环逻辑
- 显式复现已发表论文的 Python 参考实现
- 需要跨截面操作但 DSL 没有对应算子

**Lineage 字段**：当候选是对既有 admitted factor 的改进变体时填写（调参数、扩窗口、改 conditioner）。全新思路不填。Python 校验 parent_batch 存在。

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
  - candidate_id: C003
    source_type: dsl
    expression: "Mul(Corr($pe_ratio, Mean($close, 80), 80), $turnover_rate)"
    canonical: "Mul($turnover_rate,Corr(Mean($close,80),$pe_ratio,80))"
    lineage:
      parent_batch: batch_102
      parent_candidate_id: C004
      transformation: "extend_lookback_60d_to_80d"
```

冻结后 `state.yaml.current_batch_phase` 推进到 `"designed"`。

---

## Obsidian Wikilink 约定

**Direction → Factor**：`[[../factors/F020|F020]]`
**Direction → Lessons**：`[[../lessons#Structural Constraints]]`
**Direction → Direction**：`[[timing_range]]`（同目录简写）
**Factor → Direction**：`[[../directions/fundamental_price_divergence#Hypothesis]]`
**Judge → Direction Thread**：`directions/fundamental_price_divergence.md#T001`（referenced_context 格式）
**INDEX → Direction**：`[[fundamental_price_divergence]]`

---

## 更新时间表

| Phase | 文件 | 谁 | 做什么 |
|---|---|---|---|
| **Phase 1** | `manifest.yaml` | Python | 冻结（不可变） |
| **Phase 1** | `direction.md` | LLM（若新建）| 写 Hypothesis + 初始 Threads |
| **Phase 4** | `direction.md` body | **LLM** | 追加 Narrative Log + 更新 Thread evidence |
| **Phase 4** | `direction.md` frontmatter | **Python** | rounds++ / admits++ / members append / last_batch |
| **Phase 4** | `direction.md` frontmatter | **LLM**（可选）| status / priority 转换（在 Narrative Log 中说明理由）|
| **Phase 5** | `direction.md` 全文 | **LLM** | 整体重写（压缩 Narrative Log、整理 Threads、审视 Hypothesis）|

**关键**：Phase 4 中 LLM 写 body **先于** Python 改 frontmatter。不能颠倒（防 LLM 覆盖 Python 的 counter）。

---

## 关键约束

- **不看 validation 数据**：候选设计基于 hypothesis + 先验知识，不基于回测结果
- **CsRank / CsZscore 始终在全市场计算**（`D.instruments("all")`），不受 mining universe 影响
- **A-share 约束**：不做空侧 alpha；因子与 `$market_cap` 相关性 `|corr| > 0.3` → 拒绝
- **一个 batch 一个 direction**：跨方向融合 → 新建 direction，不混 batch
