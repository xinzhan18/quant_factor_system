---
name: factor-idea
description: 发散探索方向 → 探针验证 → 收敛生成候选因子
user_invocable: true
---

# 因子创意生成 — /idea

通过三阶段流程生成候选因子：Strategy（发散方向）→ Probe（探针验证）→ Decide（收敛生成）。

## 第1步：确定批次编号

扫描 `storage/candidates/` 目录，找到现有 `batch_XXX.yaml` 中最大的编号，+1 作为本批次编号。如果目录为空，从 `batch_001` 开始。

## 第2步：Strategy — 发散候选方向

从三个知识通道收集候选方向。

### 2a. 通道1：记忆（必选）

读取以下文件：

**方向索引：**
```
storage/memory/directions.yaml
```

**全局状态：**
```
storage/memory/state.yaml
```
特别关注 `next_round_hint` 字段 — 上一轮 judge 留下的建议。

**最近批次历史（最近2个）：**
```
ls storage/memory/history/
```

**当前因子库：**
```
storage/library/library.yaml
```

**工程经验：**
```
storage/memory/mining-lessons.md
```

从记忆中提取：
- 哪些方向是 `active` 或 `new`（优先选择）
- 哪些方向是 `exhausted` 或 `dead`（避开）
- 因子库的覆盖空白（哪些类别因子少）
- 上轮建议（next_round_hint）

### 2b. 通道2：Web 搜索（可选）

**触发条件**：`active` + `new` 状态的方向少于 3 个，OR 用户指定了新主题。

如果触发：
1. 根据当前缺口构造搜索词（如 "A股 日频 OHLCV 因子 新方法"、"Alpha191 公式"）
2. 执行 web search
3. 从结果中提取可操作的因子公式或思路
4. 为每个有价值的线索创建新的方向文件（status=new）：
   ```
   storage/memory/directions/{slug}.md
   ```

### 2c. 通道3：变异分析（自动）

1. 读取因子库中 IC 绝对值 top 5 的因子
2. 对每个因子，读取对应方向文件（如果存在），检查是否已做过变异
3. 未做过变异的因子 → 生成变异方向（窗口扫描、Rank 变换、组合）
4. 如果变异方向不存在，创建新方向文件（status=new）

### 2d. Strategy 输出

综合三个通道，选出 6-8 个候选方向。每个方向需要：
- 方向名称
- 来源（memory / search / mutation）
- 理由（一句话）
- 探针表达式（一个 Qlib 表达式）

**验证清单**（检查每个探针表达式）：
- [ ] 所有算子都可用？（参考 mining-lessons.md 中的可用/不可用列表）
- [ ] 所有字段都可用？（$close, $open, $high, $low, $volume — $amount/$vwap 不可用）
- [ ] 与 dead 方向不重叠？

## 第3步：打印上下文摘要（强制）

```
=== 挖掘上下文 (批次 XXX) ===

因子库状态：
- 规模：X/100 个因子
- IC 均值：0.0XXX
- 覆盖：[按类别列出数量]

方向状态：
- Active: N 个 [列出名称]
- New: N 个 [列出名称]
- Exhausted: N 个
- Dead: N 个
- Blocked: N 个

上轮建议：
[next_round_hint 内容]

知识通道：
- 记忆：已读取 [列出文件]
- 搜索：[触发/未触发]，[如触发，列出搜索词和结果摘要]
- 变异：[分析了哪些因子]

候选方向（6-8 个）：
1. [名称] (来源: xxx) — [理由] — 探针: [表达式]
2. ...
```

## 第4步：Probe — 探针验证

对每个候选方向的探针表达式，运行轻量评估（全量股票，2024年数据，只算IC）：

```bash
PYTHONPATH=src python3 -m mining probe "探针表达式" --start 2024-01-01 --end 2024-12-31
```

逐个运行，每个约10-20秒。

打印探针结果：
```
=== 探针结果 ===
方向1: williams_r_window_7    IC=+0.061  ✓ 强信号
方向2: alpha191_045           IC=-0.002  ✗ 无信号
方向3: volume_regime_cross    IC=-0.015  ✗ 弱信号
方向4: trend_resi_combo       IC=-0.038  ✓ 中等信号
...
```

信号分类：
- |IC| >= 0.03: 强信号 ✓
- 0.01 <= |IC| < 0.03: 中等信号 ~
- |IC| < 0.01: 无信号 ✗

## 第5步：Decide — 收敛生成

基于探针 IC 选择 top 2-3 个方向。选择时综合考虑：
1. 探针 IC 强度（主要依据）
2. 方向在记忆中的历史（连续失败 → 降权）
3. 与已有因子的预期相关性（结构相似 → 降权）
4. 方向多样性（不要全选同类）

**排除**：探针 IC 为"无信号"(|IC| < 0.01) 的方向直接排除。

对选中的每个方向，展开为 2-3 个正式候选：
- 窗口变异：探针用的 N=X，展开为 N=X/2, X, X*1.5
- 结构变异：加 Rank 变换、与其他信号组合
- 参数微调

**验证清单**（检查每个正式候选）：
- [ ] 所有算子都可用？
- [ ] 所有字段都可用？
- [ ] 表达式深度 ≤ 10？
- [ ] 与因子库中的因子不是近似重复？

## 第6步：写入候选文件

将候选写入 `storage/candidates/batch_XXX.yaml`：

```yaml
batch_id: "batch_XXX"
timestamp: "YYYY-MM-DDTHH:MM:SS"
candidates:
  - name: "descriptive_name"
    expression: "Qlib_expression_here"
    category: "category"
    rationale: "该因子应该有效的原因"
    direction: "所属方向名称"
```

注意新增 `direction` 字段 — 标记每个候选来自哪个方向，供 judge 阶段按方向聚合。

## 第7步：更新方向状态

将本轮参与 probe 的方向状态从 `new` 更新为 `probing` → 基于探针结果更新为 `active` 或 `dead`：
- 读取方向文件
- 更新 frontmatter 中的 status
- 在 Probe Records 部分追加本次探针结果
- 更新 directions.yaml 索引

## 第8步：完成提示

```
候选已生成：storage/candidates/batch_XXX.yaml（N 个候选，来自 M 个方向）
方向分布：[方向1] x 3, [方向2] x 3, [方向3] x 2
运行 /execute 开始评估，或 /mine 继续完整流程。
```

---

## 预处理说明

评估器会自动对因子值和收益率进行预处理后再计算 IC。**不需要在因子表达式中添加 Winsorize/Zscore/Scale** — 管道会统一处理：

1. **股票池过滤**：排除停牌股（成交量=0）和涨跌停股
2. **因子清洗**：inf→NaN，MAD 缩尾（5倍），zscore 标准化
3. **收益率遮罩**：不可交易股票的前向收益率设为 NaN
