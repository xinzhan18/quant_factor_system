---
name: factor-idea
description: Phase 1 START+DESIGN — 选方向、设计候选、冻结 manifest
user_invocable: true
---

# /factor-idea — Phase 1 候选设计

## 职责

为 `/factor-mine` 的 Phase 1 提供候选列表。单独调用时跳过 Phase 2-5。

## 步骤

1. 读 `vault/INDEX.md` 选方向 → follow link 到 `vault/directions/{direction}.md`
2. 读该 direction 的 Hypothesis + 活跃 Threads + 历史 batch 记录
3. 读 `vault/lessons.md` 获取 Structural Constraints（特别是 forbidden fields/operators、A-share 约束、market-cap guardrail）
4. 设计 5-10 个候选：
   - 默认 DSL（Qlib expression），Python 只在 DSL 无法表达时使用
   - 每个候选附 `candidate_id`（C001-C010）、`expression`（或 `path`）、`source_type`（dsl/python）
5. 写 `batch_goal`（≥ 30 字符，说明本轮目标）
6. Python 验证：DSL whitelist + 重复检测（含交换律 `Mul(A,B) == Mul(B,A)`）+ Python AST 校验
7. Python 冻结 `batches/batch_{N}/manifest.yaml`

## 关键约束

- **不看 validation 数据**：候选设计基于 hypothesis + 先验知识，不基于回测结果
- **重复检测**：canonical 化后对比 `vault/factors/F*.yaml` 的已有表达式
- **batch_goal 非空**：防止 LLM 偷懒提交 "test" 作为目标
