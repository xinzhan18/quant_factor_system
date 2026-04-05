## Research Architecture Simplification

**Date:** 2026-04-05
**Status:** proposed and partially applied

### Problem

当前 `research` 代码、`.claude/skills`、设计文档三层的概念数明显高于真实边界数：

- 代码层有 12 个一级 package：`compute / execute / stats / risk / redundancy / feasibility / logic / judge / governance / controller / storage / domain`
- skill 层拆成 7 个一级 skill：`mine / idea / execute / judge / discovery / logic / report`
- 文档层继续沿着“拆更多层”的方向演化，导致阅读时必须同时记住大量近义边界

结果不是更清晰，而是：

1. `controller` 与 `governance` 都在做流程治理，边界重复
2. `stats / risk / redundancy / feasibility` 都是 execute 产证据的子域，却被提升成并列一级目录
3. `discovery` 本质上只是 `logic review` 的输入渠道，却被单独做成 skill
4. `execute` 与 `judge` 是同一条“评估-裁决”链路，被文档和 skill 讲成两个几乎平级的产品

### Simplified Model

推荐把顶层理解收敛到 4 个工作区，而不是继续扩张并列概念：

1. **State**
   - `domain`
   - `storage`
   - 负责 schema、contracts、持久化对象
2. **Evaluation**
   - `compute`
   - `execute`
   - `stats`
   - `risk`
   - `redundancy`
   - `feasibility`
   - 负责信号计算、证据生成、技术 gate
3. **Decision**
   - `logic`
   - `judge`
   - 负责 hypothesis 生命周期与 verdict
4. **Governance**
   - `governance`
   - 负责写权限、审计、冷启动策略、批次节奏、holdout 队列

### Skill Simplification

skill 层建议只保留 5 个一等入口：

1. `factor-mine`：编排入口
2. `factor-idea`：候选生成
3. `factor-evaluate`：`execute + judge`
4. `factor-logic`：`logic + discovery`
5. `factor-report`：录取后的报告

说明：

- `factor-discovery` 不应继续独立扩张，它只是 `factor-logic` 的异常升级子流程
- `factor-execute` 和 `factor-judge` 可以保留实现文件，但对用户和文档应视作一个评估阶段

### Code Merge Policy

不是一次性大搬家，而是按“一级目录去重优先、内部模块稍后再收”的顺序做：

1. **先合并流程治理目录**
   - `controller -> governance`
2. **再收敛评估子域的对外心智**
   - 文档和入口统一使用 `evaluation` 这个概念
   - 是否物理搬目录，等内部接口稳定后再做
3. **避免继续增加新的一级 package**
   - 新能力优先落到现有 4 个工作区内部

### Applied In This Change

本次已落地：

- `src/research/controller/*` 合并到 `src/research/governance/*`
- `tests/research/controller/*` 合并到 `tests/research/governance/*`
- `research.__init__` 改为描述 4 个工作区，而不是默认接受 12 个并列概念

### Next Recommended Steps

1. 新增一个 `research/evaluation/__init__.py` 作为对外聚合出口，统一暴露 `stats/risk/redundancy/feasibility`
2. skill 文档新增“一级入口 vs 子流程”约束，避免再把子流程扩成独立 skill
3. `StoragePaths` 继续沿单一 `ledger.yaml` 收敛，停止回退到多 ledger 文件模型
