# Research Execute

## 1. 目标

`research_execute` 是研究系统里的正式证据生成层。

它只回答一件事：

> 在统一研究协议下，这批 candidate 到底产生了什么可比较、可裁决、可复核的统计证据。

它不负责：

- 新 hypothesis 创建
- 新 route 创建
- candidate 自由改写
- admit / reject / replace
- policy 升级
- forbidden 升级

这些属于 `logic`、`idea` 或 `research_judge`。

---

## 2. 核心职责

`research_execute` 负责：

1. 读取 batch candidates
2. 做 source-specific precheck
3. 单链路执行主逻辑，生成 `base_signal`
4. 在统一 pipeline 下得到 `evaluation_ready_signal`
5. 在统一研究样本制度下生成统计证据
6. 做相似性与可实现性代理检查
7. 输出结构化结果包和 `judge_packet` 给 `research_judge`

补充边界：

- `research_execute` 只处理已经被冻结进 batch manifest 的正式 candidate
- candidate freeze 之前允许存在会话内 `quick execute` 往返
- quick execute 只服务快速试错，不进入正式 research result / judge / memory

---

## 3. 样本制度

### 3.1 三层样本

研究系统固定采用三层样本：

1. `train`
2. `validation`
3. `holdout`

当前有效研究数据的统一起点为：

- `2015-01-01`

所有样本切分、rolling review、expanding review 都必须以此为最早可用起点。

### 3.2 `research_execute` 默认只使用 `train + validation`

执行层的日常 batch 只运行：

- `train`
- `validation`

`holdout` 不能进入日常批量执行主循环。

原因：

- `holdout` 是低频复核样本
- 不能作为高频自动搜索反馈源

### 3.3 每次执行都必须记录样本配置

这里的三分法不再采用“全系统永远固定一刀切”的硬分区。

原因：

- 当前有效数据只从 `2015-01-01` 起
- 若把 `train` 永远锁死在 `2015-2020`，会平白损失后续 IS 覆盖
- `holdout` 若只有 1 年，也不适合承担主要统计裁决任务

因此采用：

- `anchored expanding train`
- `primary validation window`
- `overlapping support windows for stress check`
- `holdout pool for release review`

结果中必须保留：

```yaml
sample_policy:
  data_start: "2015-01-01"
  active_train_range: ["2015-01-01", "2021-12-31"]
  active_validation_range: ["2022-01-01", "2023-12-31"]
  support_validation_windows:
    - {window_id: val_2020_2021, range: ["2020-01-01", "2021-12-31"]}
    - {window_id: val_2021_2022, range: ["2021-01-01", "2022-12-31"]}
    - {window_id: val_2022_2023, range: ["2022-01-01", "2023-12-31"]}
  holdout_pool_range: ["2024-01-01", "2025-12-31"]
  holdout_used: false
  validation_policy_version: research_sample_v3
  validation_window_id: val_2022_2023
```

### 3.4 validation 使用必须被审计

执行层必须记录：

- `validation_window_id`
- `validation_exposure_count_before_run`
- `validation_exposure_count_after_run`

如果主 validation window 被高频重复消费，则后续应由 `logic` 和 `research_judge` 触发：

- logic 降温
- 降低本 logic 的正式 batch 配额
- 或进入 holdout review

`validation_exposure_count` 不再使用“全历史只增不减”的单一计数。

必须同时维护：

- `window_exposure_count_to_date`
- `window_exposure_count_recent`
- `global_validation_exposure_count_to_date`

进入 risk bucket 的应优先使用：

- `window_exposure_count_recent`
- `window_exposure_count_to_date`

而不是全局累计值。

### 3.5 validation windows 的真实角色

这里不再把 `val_2020_2021 / val_2021_2022 / val_2022_2023` 描述成“独立 validation rotation”。

原因很直接：

- 它们彼此高度重叠
- 对应 train 长度也不同
- 不能被当成独立验证集轮换

因此当前协议改成：

1. `val_2022_2023` 是默认主 validation window
2. `val_2020_2021 / val_2021_2022` 只作为 support windows
3. support windows 只用于：
   - stress check
   - regime continuity check
   - sign consistency 辅助观察
4. support windows 不参与主 admit 阈值
5. 不把不同 window 的数值表现直接横向比较，也不把它们解释成独立 OOS

只有在 `sample_policy_version` 明确升级时，才允许切换主 validation window。

这意味着：

- 当前系统做的是 exposure management，不是严格意义上的 independent validation rotation
- overlapping windows 只是帮助判断“这段表现是否过度依赖单一近年窗口”

执行要求：

- execute 必须在每个 support window 上至少计算：
  - `ic_mean_support`
  - `sign_consistency_support`
- 但这些结果只进入 `support_window_checks`
- 不进入主 admit 阈值
- 若两个 support windows 都出现 sign flip，则必须在 judge packet 中标记：
- `support_window_warning: repeated_sign_flip`

support windows 的具体使用规则必须固定：

1. `stress check`
   - 只看 `ic_mean_support` 的方向是否与主 validation 一致
   - 不做跨 window 数值优劣排名
2. `regime continuity check`
   - 只看 support window 中是否出现连续 sign flip
3. `sign consistency`
   - 若一个 support window flip，记：
     - `support_window_warning: single_window_flip`
   - 若两个 support windows 都 flip，记：
     - `support_window_warning: repeated_sign_flip`
   - 若均未 flip，记：
     - `support_window_warning: none`

它们的唯一用途是：

- 作为 judge 的辅助稳定性证据
- 在 repeated sign flip 时把 candidate 推向更保守 verdict

它们不用于：

- 直接 admit
- 直接 reject
- 构造新的主评分

### 3.6 holdout 的职责必须收缩

`holdout` 不承担主要统计显著性裁决职责。

它更适合作为：

- release veto
- sign flip 检查
- structural break 排查

也就是说：

- `admit` 主要基于 `train + validation`
- `holdout` 主要用于“别犯明显错误”

若当前 holdout 有效长度不足，必须把它解释为：

- `supportive`
- `neutral`
- `contradictory`

而不是伪装成高统计效力的硬检验。

---

## 4. 输入对象

执行前至少读取：

```text
storage/candidates/batch_XXX.yaml
storage/candidates/batch_XXX_idea_report.yaml
storage/registry/families/family_registry.yaml
storage/registry/factors/index.yaml
storage/policy/capability_registry.yaml
storage/policy/implementation_policy.yaml
storage/evaluation_profiles/research_eval_v1.yaml
storage/ledger/search_ledger.yaml
storage/ledger/batch_usage.yaml
```

### 4.1 evaluation profile 定义

`storage/evaluation_profiles/research_eval_v1.yaml` 不是幽灵对象。

它是 execute 的主配置快照，至少必须包含：

```yaml
evaluation_profile:
  profile_id: research_eval_v1
  universe_profile: cn_all_tradable_v1
  tradability_profile: cn_t1_limit_v1
  preprocess_profile: default_rank_v1
  neutralization_profile: cap_industry_barra_v1
  delay: 1
  holding_horizon: 5
  primary_pipeline:
    - universe_mask
    - tradability_mask
    - winsorize
    - zscore_or_rank
    - neutralization
  auxiliary_views:
    - raw_view
    - cap_industry_neutral_view
    - barra_residual_view
```

硬规则：

- inline pipeline 描述必须与 profile 对齐
- 若 profile 与正文冲突，以 profile 为准
- report 只引用最终生效的 profile snapshot

每个 candidate 至少包含：

- `candidate_id`
- `logic_id`
- `route_id`
- `experiment_lineage_tag`
- `family_id`
- `route_type`
- `source_type`
- `expression` 或 `code`
- `implementation_reason`
- `rationale`
- `lineage`

### 4.2 family registry 校验

`research_execute` 在做任何 family-level redundancy 之前，必须先校验：

1. `family_id` 是否存在于 `family_registry.yaml`
2. 若 `family_id` 为正式 family，它是否在当前 `logic_id.allowed_families` 内
3. candidate 的 `structure_template / conditioning_type / horizon_bucket` 是否与 family registry 兼容

若校验失败：

- 仍允许继续做正式效果与稳定性评估
- 但 family-level redundancy 必须降级
- 必须输出：
  - `family_registry_check: degraded`
  - `family_assignment_status: provisional / unknown / invalid`

降级规则：

- `registered`：允许完整 family / subspace redundancy
- `provisional`：允许弱 family 比较，但不得据此做强 replace
- `unknown`：只做 pairwise duplication，不做 family-level replace
- `invalid`：family 视图只做 warning，不作为主裁决依据

---

## 5. 统一评估原则

### 原则 1：主逻辑只执行一次

无论 DSL 还是 Python，candidate 主逻辑都只执行一次，得到：

- `base_signal`

后续所有处理都基于这份结果派生。

### 原则 2：主评估只有一个 primary pipeline

正式主比较只针对：

- `evaluation_ready_signal`

这条是 primary pipeline。

允许少量辅助比较视图：

- `raw_view_signal`
- `cap_industry_neutral_signal`
- `barra_residual_signal`

这些视图只服务：

- risk model review
- 风格残留判断

### 原则 3：执行层不做研究裁决，但可以做技术性分流

执行层可以输出：

- 是否可计算
- 是否足以进入正式 judge
- feasibility 状态
- overlap 风险

但不能输出：

- admit
- reject
- replace

---

## 6. 完整流程

### Step 1：Precheck

#### DSL candidate

至少检查：

- `parser_check`
- `operator_whitelist_check`
- `field_whitelist_check`
- `expression_depth_check`
- `constant_factor_check`
- `valid_ratio_precheck`
- `forbidden_pattern_check`

#### Python candidate

至少检查：

- `syntax_check`
- `helper_whitelist_check`
- `vectorization_check`
- `param_schema_check`
- `output_shape_check`
- `forbidden_pattern_check`
- `smoke_test`

#### Precheck 输出

```yaml
precheck:
  status: passed   # passed / failed / performance_rejected
  reason_codes: []
```

### Step 2：执行主逻辑

输出：

- `base_signal`

同时只允许提取少量 cheap diagnostics：

- `base_valid_ratio`
- `base_variance`
- `base_outlier_ratio`
- `base_skew`
- `base_kurtosis`

### Step 3：primary pipeline 与辅助视图

依次应用：

1. universe mask
2. tradability mask
3. delay / horizon alignment
4. missing / invalid handling
5. winsorize
6. standardize
7. neutralization

输出：

- `evaluation_ready_signal`

若 risk review 需要，可额外输出：

- `raw_view_signal`
- `cap_industry_neutral_signal`
- `barra_residual_signal`

### Step 4：正式统计证据

正式统计证据只在 `train + validation` 上生成。

#### A. Effect Strength

- `ic_mean_train`
- `ic_ir_train`
- `ic_mean_validation`
- `ic_ir_validation`
- `ic_win_rate_validation`
- `monotonicity_validation`

#### B. Stability

- `sign_consistency`
- `train_validation_decay_ratio`
- `split_stability`
- `regime_stability`
- `horizon_consistency`

#### Stability 操作定义

##### `split_stability`

`split_stability` 必须按固定切分规则计算，不能自由挑切法。

默认规则：

- 仅在 `active_validation_range` 上计算
- 将 validation 按时间顺序切成 `4` 个连续等长 split
- 每个 split 至少需要 `60` 个交易日
- 若 4 个 split 不满足最小长度，则降到 `3` 个 split
- 若仍不足 `3` 个有效 split，则输出：
  - `split_stability: insufficient_splits`

计算：

- 对每个 split 计算 `split_ic_mean`
- `split_sign_consistency = 同向 split 数 / 有效 split 数`
- `split_dispersion = std(split_ic_mean) / (abs(mean(split_ic_mean)) + 1e-6)`

分桶：

- `high`: `split_sign_consistency >= 0.75` 且 `split_dispersion <= 0.75`
- `medium`: `split_sign_consistency >= 0.50` 且 `split_dispersion <= 1.25`
- `low`: 其余情况

##### `regime_stability`

`regime_stability` 必须先定义 regime，再做稳定性判断。

默认使用与 `universe_profile` 对应的 benchmark 指数，按每日收盘序列计算：

- `r60 = trailing_60d_return`
- `sigma20 = trailing_20d_realized_vol`

主 regime 先按收益方向划分：

- `bull`: `r60 > 0.08`
- `bear`: `r60 < -0.08`
- `range`: 其余

辅助波动 regime 按 `sigma20` 在 active validation 内的分位数划分：

- `high_vol`: `sigma20 >= p67`
- `mid_vol`: `p33 < sigma20 < p67`
- `low_vol`: `sigma20 <= p33`

默认 `regime_stability` 以 `bull / bear / range` 三个主 regime 为主；
若某个主 regime 有效样本少于 `40` 个交易日，则输出：

- `regime_stability: insufficient_regime_coverage`

计算：

- 对每个主 regime 计算 `regime_ic_mean`
- `regime_sign_consistency = 同向 regime 数 / 有效 regime 数`
- `regime_strength_ratio = max(abs(regime_ic_mean)) / (max(min(abs(regime_ic_mean)), 1e-4))`

分桶：

- `high`: 无 sign flip，且 `regime_strength_ratio <= 2.0`
- `medium`: 最多 1 个弱 regime，且 `regime_strength_ratio <= 3.0`
- `low`: 其余情况

#### C. Statistical Reliability

- `expanding_window_ic_stability`
- `expanding_window_sign_consistency`
- `expanding_window_pass`
- `bootstrap_stability_score`
- `bootstrap_sign_consistency`
- `purged_walk_forward_score`
- `purged_walk_forward_pass`
- `purged_walk_forward_status`
- `multiple_testing_risk_bucket`
- `search_adjusted_strength_bucket`
- `support_window_checks`

#### D. Redundancy

- `max_lib_corr`
- `nearest_factor_id`
- `family_overlap_score`
- `incremental_ic_proxy`
- `subspace_redundancy_score`
- `residual_incremental_ic`

#### Redundancy 定义

`redundancy` 不再只看 pairwise corr，而分三层：

1. `pairwise duplication`
2. `family-level redundancy`
3. `local subspace redundancy`

##### 1. pairwise duplication

用于处理：

- 表达式近重复
- 参数微扰重复
- 与单一已入库因子高度相似

##### 2. family-level redundancy

`family` 采用规则化标签，而不是事后按 IC 聚类定义。

这里必须区分：

- `family_id`：机制级 family，例如 `FM_breakout`
- `structure_template`
- `conditioning_type`
- `horizon_bucket`

例如：

- `family_id = FM_breakout`
- `structure_template = gated`
- `conditioning_type = volume`
- `horizon_bucket = short`

`family_overlap_score` 不应直接裸输出为黑盒分数，至少应由以下组成项构成：

- `same_family_corr_p90`
- `structure_overlap_score`
- `residual_survival_ratio`

其中：

- `same_family_corr_p90`：candidate 与同 family 已入库因子在 validation 上 `abs(corr)` 的 90 分位
- `structure_overlap_score`：与同 family basis 因子在 `structure_template / conditioning_type / horizon_bucket` 上的重叠度，定义为三项命中数 / 3，归一到 `[0,1]`
- `residual_survival_ratio = residual_incremental_ic / raw_incremental_ic_proxy`

聚合公式：

```text
family_overlap_score =
0.50 * same_family_corr_p90
+ 0.30 * structure_overlap_score
+ 0.20 * (1 - clip(residual_survival_ratio, 0, 1))
```

分桶：

- `low`: `< 0.45`
- `medium`: `0.45 ~ 0.70`
- `high`: `> 0.70`

建议执行层至少同时输出：

- `family_overlap_score`
- `family_overlap_bucket`
- `same_family_corr_p90`
- `structure_overlap_score`
- `residual_survival_ratio`

##### 3. local subspace redundancy

`subspace_redundancy_score` 不做全库 PCA，而做局部 basis 解释度。

局部 basis 选择规则：

1. 优先同 `family_id` 已入库因子
2. 若 family 不足，再补同 `logic_id` 最相近因子
3. basis 因子数最多 `K = 3`

在 validation 上，对每日横截面做局部 ridge 回归：

```text
candidate_signal_t = B_t * beta_t + residual_t
```

定义：

- `subspace_redundancy_score = median_t(R²_t)`
- `residual_incremental_ic = mean_t corr(residual_t, fwd_return_t)`

额外应输出：

- `basis_factor_ids`
- `basis_method`
- `subspace_confidence`

其中：

- 若 `family_size < 2`，则不计算 `subspace_redundancy_score`，只输出 `subspace_confidence: insufficient_family_size`
- 若 `basis_factor_count < 2`，则输出 `subspace_confidence: insufficient_basis`
- 若 `basis_factor_count = 2` 且 `validation_days >= 120`，输出 `subspace_confidence: low`
- 若 `basis_factor_count = 3` 且 (`family_size <= 5` 或 `validation_days < 250`)，输出 `subspace_confidence: medium`
- 若 `basis_factor_count = 3` 且 `family_size >= 6` 且 `validation_days >= 250`，输出 `subspace_confidence: high`

#### E. Risk Model Review

- `raw_view_ic`
- `cap_industry_neutral_ic`
- `barra_residual_ic`
- `alpha_survival_ratio`
- `dominant_style_exposure`
- `style_crowding_risk`

#### F. Feasibility

- `turnover`
- `coverage`
- `half_life`
- `holding_period_proxy`
- `liquidity_coverage_ratio`
- `tail_trade_concentration`
- `small_cap_concentration`
- `rebalance_stress_proxy`

#### Feasibility 操作定义

以下 proxy 全部基于统一的 `proxy long-short portfolio` 计算。

默认 proxy 组合定义：

- 在每个调仓日，对 `evaluation_ready_signal` 做横截面排序
- long 端取 top `20%`
- short 端取 bottom `20%`
- 端内等权
- 只在可交易股票上构建

##### `holding_period_proxy`

由 `half_life` 推导：

- `short`: `half_life <= 3`
- `medium`: `3 < half_life <= 10`
- `long`: `half_life > 10`

##### `small_cap_concentration`

定义：

- 先按当日 `market_cap` 分位数定义小盘：
  - `small_cap_flag = market_cap <= cross_section_p30`
- `small_cap_concentration = proxy_portfolio_abs_weight` 中落在 `small_cap_flag` 股票上的权重占比

##### `liquidity_coverage_ratio`

定义流动性代理：

- `liq20 = median($amount, 20)`
- 在每个调仓日，把可交易股票按 `liq20` 做横截面分位
- `liquid_flag = liq20 >= cross_section_p30`

定义：

- `liquidity_coverage_ratio = proxy_portfolio_abs_weight` 中落在 `liquid_flag` 股票上的权重占比

##### `tail_trade_concentration`

定义：

- 对每个调仓日，计算 proxy 组合的单名绝对目标权重
- 取绝对权重最大的前 `10` 个名字
- `tail_trade_concentration = 这 10 个名字绝对权重之和`
- 最终对全样本取时间均值

##### `rebalance_stress_proxy`

定义：

```text
rebalance_stress_raw =
turnover * tail_trade_concentration / max(liquidity_coverage_ratio, 0.10)
```

分桶：

- `low`: `< 0.20`
- `medium`: `0.20 ~ 0.50`
- `high`: `> 0.50`

---

## 7. Statistical Reliability Protocol

### 7.0 冷启动协议

当前系统在前几轮里，不具备成熟的历史背景。

因此必须区分：

- `bootstrap_phase`
- `steady_phase`

最低保护期条件：

- `completed_batches >= 5`
  且
- `admitted_factor_count >= 10`

这不是“到了门槛后一切 suddenly 可靠”的全局开关。

execute 侧应逐项解锁：

1. `multiple_testing` 历史项
   - 从第 1 轮起就可用，但历史权重随 batch 数逐步增加
2. `family_overlap`
   - `family_size >= 3` 时进入正常解释
3. `subspace_redundancy`
   - `basis_factor_count >= 2` 时进入正常解释
4. `promote_family` 相关累计结论
   - 至少跨 `2` 个 batch 后才允许输出
5. `forbidden` 升级相关提示
   - 只在 `policy_upgrade_ledger` 达标后进入正式建议

在 `bootstrap_phase`：

1. `multiple_testing_risk_bucket` 不能只靠历史累计值
2. 必须额外参考：
   - `current_batch_candidate_count`
   - `current_logic_candidate_count`
3. `family_overlap / subspace_redundancy` 允许输出：
   - `insufficient_family_history`
4. `promote_family`、`productive`、`saturated` 等累计型结论默认不启用
5. `policy_upgrade_ledger` 只允许积累，不允许正式升级 forbidden

执行细则：

- 若 `logic_attempt_count_to_date = 0`，则 `multiple_testing_risk_bucket` 不能默认直接记 `low`
- 冷启动阶段至少还要看：
  - 本 batch candidate 总数
  - 本 logic candidate 数
  - 当前 validation window 的使用次数
- 若 `family_size < 2`，则 `family_overlap_score` 可保留，但必须标：
  - `family_history_status: insufficient`
- 若 `basis_factor_count < 2`，则 `subspace_redundancy_view.confidence = insufficient_family_size`

这意味着冷启动前 `N` 轮：

- 可以做 admit / reserve / reject
- 但不能假装很多累计治理机制已经可靠工作

这里不再把学术检验工具写成“必须同时做到”的刚性套餐。

原因：

- 当前有效数据从 `2015-01-01` 起
- 日频因子研究的 validation 长度有限
- candidate 生成是连续搜索，不满足独立 trial 假设

所以执行层改成两层协议。

### 7.1 基础必做协议

#### A. Expanding-Window IC Stability

这是当前阶段最重要的基础检查，必须输出：

- `expanding_window_ic_path`
- `expanding_window_ic_stability`
- `expanding_window_sign_consistency`
- `expanding_window_decay_ratio`
- `expanding_window_pass`

#### B. Split / Regime Stability

必须输出：

- `split_stability`
- `regime_stability`
- `train_validation_decay_ratio`

#### C. Multiple Testing Context

必须结合 `search_ledger` 与 `batch_usage` 输出：

- `family_attempt_count_to_date`
- `logic_attempt_count_to_date`
- `validation_exposure_count_before_run`
- `validation_exposure_count_after_run`
- `multiple_testing_risk_bucket`

这里的 `multiple_testing_risk_bucket` 只是研究风险分层，不宣称具有严格 FDR 含义。

默认映射必须固定为：

```text
multiple_testing_risk_score =
0.50 * clip(log1p(family_attempt_count_to_date) / log(25), 0, 1)
+ 0.30 * clip(log1p(logic_attempt_count_to_date) / log(60), 0, 1)
+ 0.20 * clip(validation_exposure_count_after_run / 12, 0, 1)
```

分桶：

- `low`: `< 0.40`
- `medium`: `0.40 ~ 0.70`
- `high`: `> 0.70`

#### D. Bootstrap Stability

若样本量允许，推荐输出：

- `bootstrap_stability_score`
- `bootstrap_sign_consistency`

若统计检验力不足，则应明确输出：

- `bootstrap_status: low_power`

`bootstrap_stability_score` 的默认方案固定为：

- 在 active validation 的每日 IC 序列上做 `moving block bootstrap`
- 重采样次数 `B = 200`
- block length `L = min(60, max(20, round(sqrt(T))))`
  - `T` 为 validation 有效交易日数

定义：

- `bootstrap_sign_consistency = 同号 bootstrap 样本占比`
- `bootstrap_median_abs_ratio = median(abs(bootstrap_mean_ic)) / max(abs(raw_validation_ic), 1e-6)`
- `bootstrap_stability_score = 0.7 * bootstrap_sign_consistency + 0.3 * clip(bootstrap_median_abs_ratio, 0, 1)`

解释阈值：

- `good`: `>= 0.65`
- `borderline`: `0.45 ~ 0.65`
- `poor`: `< 0.45`

### 7.2 高级可选诊断

#### A. Purged Walk-Forward

只有在 purge / embargo 后仍能形成足够有效 split 时才输出：

- `purged_walk_forward_score`
- `purged_walk_forward_pass`

若有效 split 数不足，则必须写清：

- `purged_walk_forward_status: low_power`

#### B. Search-Adjusted Strength

默认不强制照搬论文原始 `deflated t-stat` 定义。

执行层只需输出更诚实的研究代理：

- `search_adjusted_strength_bucket`

它结合：

- `family_attempt_count_to_date`
- `logic_attempt_count_to_date`
- `validation_exposure_count`
- 当前结果相对同 family 历史基线的位置

这个字段是研究风险修正代理，不宣称具有严格 deflated t-stat 的统计含义。

操作定义：

```text
raw_validation_strength =
0.40 * clip(abs(ic_mean_validation) / 0.02, 0, 1)
+ 0.30 * clip(abs(ic_ir_validation) / 0.20, 0, 1)
+ 0.20 * clip(abs(monotonicity_validation) / 0.40, 0, 1)
+ 0.10 * indicator(expanding_window_pass)

search_adjusted_strength_score =
raw_validation_strength * (1 - 0.50 * multiple_testing_risk_score)
```

分桶：

- `high`: `>= 0.70`
- `medium`: `0.40 ~ 0.70`
- `low`: `< 0.40`

这个分数只用于研究排序和 judge 辅助解释，不用于替代正式统计检验。

---

## 8. Execution Gate

这里只处理技术不可评估与明显坏样本，不做研究 admission 裁决。

建议分成四类：

### 8.1 Computation Gate

- 可计算
- 非全空
- 非近常数

### 8.2 Basic Quality Gate

- 覆盖率不极低
- validation 上符号不完全塌陷
- 单边异常值不过高

### 8.3 Stability Gate

- train 和 validation 不完全翻脸
- 主要分段不出现完全反向崩塌

### 8.4 Feasibility Gate

- turnover 不极端
- 流动性覆盖不过低
- tail concentration 不极端

`execution_gate` 的输出建议是：

```yaml
execution_gate:
  status: pass   # pass / warn / fail_technical
  reason_codes:
    - valid_ratio_too_low
```

状态含义必须固定：

- `pass`：进入 `research_judge`
- `warn`：仍进入 `research_judge`，但必须携带 warning reason codes，供 judge 在 admit / reserve 间更保守处理
- `fail_technical`：不进入 `research_judge`，但这只表示“当前不可正式评估”，不等同于研究意义上的 `reject`

`warn` 适用的典型场景：

- coverage 偏低但未低到技术失效
- train / validation 有明显衰减，但未达到 sign flip
- feasibility 边缘化，但未到 hard failure

---

## 9. 多重检验记录

执行层必须产出 `multiple_testing_ledger` 所需字段，供 `research_judge` 使用。

至少记录：

```yaml
search_context:
  batch_id: batch_042
  logic_id: L021
  route_id: R021_01
  family_id: FM_breakout
  route_type: genesis
  route_candidate_count_this_batch: 3
  family_attempt_count_to_date: 27
  logic_attempt_count_to_date: 64
  validation_window_id: val_2022_2023
  validation_exposure_count_before_run: 11
  validation_exposure_count_after_run: 12
  multiple_testing_risk_bucket: medium
```

执行层不负责做最终统计修正决策，但必须把修正所需上下文补齐。

---

## 10. 相似性制度

### 10.1 Batch 内去重

至少识别：

- 表达式近重复
- 参数微扰重复
- 信号高度近似

### 10.2 Library 相似性

至少输出：

- `max_lib_corr`
- `nearest_factor_id`
- `family_overlap_score`
- `subspace_redundancy_score`
- `residual_incremental_ic`

推荐同时输出完整视图：

```yaml
family_redundancy_view:
  family_id: FM_breakout
  structure_template: gated
  conditioning_type: volume
  horizon_bucket: short
  same_family_corr_p90: 0.81
  structure_overlap_score: 0.67
  residual_survival_ratio: 0.24
  overlap_bucket: high

subspace_redundancy_view:
  basis_method: local_ridge
  basis_factor_ids: [F011, F013, F018]
  subspace_redundancy_score: 0.74
  residual_incremental_ic: 0.002
  confidence: medium
```

### 10.3 不在执行层直接做 replace

执行层只输出：

- `replacement_candidate_hint`

最终是否 replace，由 `research_judge` 决定。

---

## 11. Holdout Review Trigger

执行层默认不使用 holdout。

但以下情况应输出：

- `holdout_review_recommended: true`

典型触发条件：

1. candidate 同时满足强统计、低冗余、低风格残留等高置信特征
2. `multiple_testing_risk_bucket = high` 但 validation 表现很好
3. 单轮结果可能影响 policy / forbidden 升级

这里的判断只能基于规则触发，
不能由 execute 预测 judge 最终会不会 admit / replace。

---

## 12. 输出对象

### 12.1 Candidate Result

每个 candidate 至少输出：

```yaml
candidate_id: C042_03
logic_id: L021
route_id: R021_01
experiment_lineage_tag: ELT_L021_breakout_compression_gate_v1
family_id: FM_breakout
route_type: genesis
source_type: dsl

sample_policy:
  active_train_range: ["2015-01-01", "2021-12-31"]
  active_validation_range: ["2022-01-01", "2023-12-31"]
  holdout_used: false
  validation_window_id: val_2022_2023

precheck:
  status: passed
  reason_codes: []

diagnostics:
  base_valid_ratio: 0.88
  base_variance: 1.42
  base_outlier_ratio: 0.06

evaluation:
  ic_mean_train: 0.018
  ic_ir_train: 0.22
  ic_mean_validation: 0.010
  ic_ir_validation: 0.13
  ic_win_rate_validation: 0.55
  monotonicity_validation: 0.39
  sign_consistency: true
  train_validation_decay_ratio: 0.56
  split_stability: medium
  regime_stability: medium
  horizon_consistency: medium
  expanding_window_ic_stability: 0.63
  expanding_window_sign_consistency: 0.71
  expanding_window_pass: true
  bootstrap_stability_score: 0.67
  bootstrap_sign_consistency: 0.81
  purged_walk_forward_score: 0.58
  purged_walk_forward_status: low_power
  multiple_testing_risk_bucket: medium
  search_adjusted_strength_bucket: medium
  support_window_checks:
    - window_id: val_2021_2022
      ic_mean_support: 0.007
      sign_consistency_support: true
    - window_id: val_2020_2021
      ic_mean_support: 0.005
      sign_consistency_support: true
  support_window_review:
    support_window_warning: none

risk_review:
  raw_view_ic: 0.010
  cap_industry_neutral_ic: 0.008
  barra_residual_ic: 0.005
  alpha_survival_ratio: 0.50
  dominant_style_exposure: size
  style_crowding_risk: medium

similarity:
  max_lib_corr: 0.64
  nearest_factor_id: F013
  family_overlap_score: 0.72
  subspace_redundancy_score: 0.61
  residual_incremental_ic: 0.003
  replacement_candidate_hint: false
  family_redundancy_view:
    family_id: FM_breakout
    structure_template: gated
    conditioning_type: volume
    horizon_bucket: short
    same_family_corr_p90: 0.81
    structure_overlap_score: 0.67
    residual_survival_ratio: 0.24
    overlap_bucket: high
  subspace_redundancy_view:
    basis_method: local_ridge
    basis_factor_ids: [F011, F013, F018]
    subspace_redundancy_score: 0.61
    residual_incremental_ic: 0.003
    confidence: medium

feasibility:
  turnover: 0.34
  coverage: 0.86
  half_life: 6.2
  holding_period_proxy: medium
  liquidity_coverage_ratio: 0.79
  tail_trade_concentration: 0.18
  small_cap_concentration: 0.31
  rebalance_stress_proxy: medium

execution_gate:
  status: pass
  reason_codes: []

search_context:
  batch_id: batch_042
  route_candidate_count_this_batch: 3
  family_attempt_count_to_date: 27
  logic_attempt_count_to_date: 64
  validation_window_id: val_2022_2023
  validation_exposure_count_before_run: 11
  validation_exposure_count_after_run: 12

holdout_review:
  recommended: false
  trigger_reason_codes: []

support_window_review:
  support_window_warning: none   # none / single_window_flip / repeated_sign_flip
```

### 12.2 Batch Result

保存为：

```text
storage/results/batch_XXX_research_result.yaml
```

### 12.3 Judge Packet

保存为：

```text
storage/packets/batch_XXX_judge_packet.yaml
```

它只保留 judge 真正需要的压缩上下文，不重复存全量原始对象。

最小 schema 固定如下：

```yaml
judge_packet:
  batch_id: batch_042
  sample_policy_version: research_sample_v3
  evaluation_profile_id: research_eval_v1
  active_logic_ids: [L021, L008]

  candidate_briefs:
    - candidate_id: C042_03
      logic_id: L021
      route_id: R021_01
      route_type: genesis
      family_id: FM_breakout
      experiment_lineage_tag: ELT_L021_breakout_compression_gate_v1
      execution_gate_status: pass
      validation_effect_bucket: borderline
      stability_bucket: medium
      redundancy_bucket: high
      feasibility_bucket: acceptable
      support_window_warning: none
      holdout_review_recommended: false

  policy_snapshot_ref:
    implementation_policy: policy/implementation_policy.yaml
    forbidden: memory/forbidden.yaml

  search_context:
    validation_window_id: val_2022_2023
    validation_exposure_count_before_run: 11
    validation_exposure_count_after_run: 12
    by_logic:
      L021:
        logic_attempt_count_to_date: 64
    by_family:
      FM_breakout:
        family_attempt_count_to_date: 27
    by_experiment_tag:
      ELT_L021_breakout_compression_gate_v1:
        batches_seen: 3
        latest_verdict: continue

  support_window_review:
    support_window_warning: none
```

省略规则：

1. 不放完整 timeseries
2. 不放可重算原始 signal
3. 不放 report 展示专用图表字段
4. 只保留 judge 真正裁决所需的压缩证据和引用

### 12.4 Execute Report

保存为：

```text
storage/results/batch_XXX_execute_report.yaml
```

至少记录：

- batch 基本信息
- 样本配置
- validation exposure 变化
- DSL / Python 数量
- precheck 失败分布
- baseline fail 分布
- feasibility 分布
- 高相似 candidate 分布
- strict stats 分布
- risk review 分布
- holdout review 建议

---

## 13. 职责边界

`research_execute` 负责：

- 统一计算
- 统一样本制度落地
- 统一研究证据生成
- 相似性与 feasibility 证据整理

`research_execute` 不负责：

- 最终录取
- forbidden 升级
- policy 升级
- logic 生命周期结论

---

## 14. 最终原则

`research_execute` 不是“跑回测脚本”的别名。

它是一套研究证据生成协议，目标是：

1. 让不同 candidate 在同一口径下比较
2. 让 `judge` 拿到干净、结构化、可复核的证据
3. 让研究系统减少样本污染和叙事型裁决
