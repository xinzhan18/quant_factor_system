---
generated_at: 2026-04-22T14:16:01Z
round: 29
total_active_directions: 8
total_factors_admitted: 10
last_batch: batch_029
last_consolidation_round: null
---

# 🗺️ Factor Research Index

> [!info] MOC · Map of Content
> 路口页。人看下方 Bases 三表；**LLM 启动读此文件顶部 Cockpit 块**（派生状态 + 下一步指令）；拿数据用 `PYTHONPATH=src python3 -m research memory snapshot`。

<!-- BEGIN COCKPIT -->

> [!note]+ 🧭 LLM Cockpit
> **状态** · round=**29** · phase=`null` (idle) · no batch in flight
> **上一批** · [[batches/batch_029/judge|batch_029]] → [[directions/return_momentum_acceleration]] · admit=**0**/3 (reserve=0, reject=3) · direction.status=`dead`
> **健康** · rounds_since_consolidation=**8** · active_directions=**8** · zero-admit streak=**3**
>
> **🎯 下一步（按优先级）**
> 1. 🧪 **阈值校准**：连续 3 批零 admit → 先按 `lessons.md#Threshold Calibration` 扫 reserve 候选识别错杀；确认有库空间独立错杀 → 调阈；否则继续
> 2. 🧭 **硬性前置**：`research doctor`（drift 检测）→ `snapshot`（数据）→ 读目标 `directions/{tag}.md` → 进 `/factor-idea`

<!-- END COCKPIT -->

<!-- BEGIN INSIGHT -->
> [!tip] 💡 最近洞察
> _（consolidation_log.md 尚无 ## 标题分段）_
<!-- END INSIGHT -->

## 🎯 方向总览 (Bases)

![[_bases/directions.base]]

## 📚 因子库 (Bases)

![[_bases/factors.base]]

## 📊 最近 Batch (Bases)

![[_bases/recent_batches.base]]

---

> [!abstract]- 系统状态
> - Round: **29** · Admitted: **10** · Active directions: **8**
> - Last batch: **batch_029**
> - Last consolidation: **—**
> - 格式 audit：运行 `research audit index` 检查漂移
