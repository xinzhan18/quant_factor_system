
• 可以。src/mining/ 现在最该做的不是“再加功能”，而是把编排、领域规则、存储 IO、运行时依赖拆开。

  当前结构问题

  1. cli.py 过胖，既做 argparse，又做 Qlib 初始化、batch 文件读写、结果序列化、history 落盘。
  2. evaluator.py 过胖，1k+ 行，混了候选预处理、相似度、sandbox、hard gates、batch orchestration。
  3. memory.py 边界不干净，memory store 反向依赖 logic_library、library、evolution 去拼 prompt context。
  4. library.py 同时做 registry 读写、replace history、values cache、DB publish。
  5. init.py 导出过多，等于把包内边界抹平了。

  建议目标
  把 src/mining/ 收敛成 6 个内部子域：

  src/mining/
    __init__.py
    __main__.py

    cli/
      main.py
      commands/
        batch.py
        evaluate.py
        probe.py
        library.py
        memory.py
        logic.py
        forbidden.py
        audit.py
        retire.py

    application/
      batch_service.py
      admission_service.py
      context_service.py
      qlib_runtime.py

    domain/
      schema.py
      results.py
      policies.py
      similarity.py

    evaluation/
      evaluator.py
      gates.py
      candidate_utils.py
      sandbox_runner.py
      preprocessing.py
      metrics.py
      expression.py

    registry/
      library.py
      publisher.py
      history.py
      values_cache.py

    memory/
      store.py
      history.py
      forbidden.py

    logic/
      library.py
      scheduler.py

    operators.py
    ops_adapter.py
    config.py
    evolution.py

  核心边界规则

  1. cli 只解析参数和打印，不直接做业务。
  2. application 负责流程编排。
  3. domain 只放纯规则/纯数据结构，不碰文件、DB、Qlib。
  4. registry 只负责 factor registry 和 publish。
  5. memory 只负责 memory 持久化和读取，不负责拼 research context。
  6. evaluation 只负责计算和筛选。
  7. __init__.py 只保留稳定公开 API，不再全量转发内部模块。

  具体重构计划

  Phase 1: 先拆 CLI，不改行为
  目标：把 cli.py 从 500 行压到一个薄入口。

  - 新建 src/mining/cli/main.py
  - 新建 src/mining/cli/commands/
  - 每个命令一个文件：
      - batch.py
      - evaluate.py
      - probe.py
      - library.py
      - memory.py
      - logic.py
      - forbidden.py
      - audit.py
      - retire.py
  - 旧 cli.py 暂时保留为兼容入口，只做：
      - from .cli.main import main

  先做这一步最值，因为风险最低，收益最大。

  Phase 2: 把 batch 流程抽成 application service
  现在 cmd_batch() 做了太多事。建议拆成：

  - application/batch_service.py
      - run_batch(batch_file, config, skip_stage1)
      - 负责：
          - 读 batch YAML
          - 初始化 evaluator
          - 调 evaluate_batch
          - 保存 result YAML
          - 保存 values cache
          - 保存 eval history
  - application/qlib_runtime.py
      - 统一 Qlib 初始化和 universe 加载
      - 不要在 cmd_batch() 和 cmd_probe() 里重复写

  这样 cmd_batch() 只剩：

  - parse args
  - build config
  - call service
  - print summary

  Phase 3: 拆 evaluator.py
  evaluator.py 是第二大热点，建议只保留 orchestrator，其他拆出去：

  - evaluation/evaluator.py
      - FactorMiningEvaluator
      - 只保留主流程
  - evaluation/gates.py
      - _apply_hard_gates
      - gate rule helpers
  - evaluation/candidate_utils.py
      - _candidate_cache_key
      - _is_python_candidate
      - _clean_factor_dict
  - domain/similarity.py
      - compute_structural_similarity
      - check_lookahead_bias
  - evaluation/sandbox_runner.py
      - python factor sandbox 执行
  - domain/results.py
      - BatchResult

  这样测试也会明显更好写。

  Phase 4: 清理 memory 边界
  memory.py 不应该再 import FactorLibrary、EvolutionEngine、MarketLogicLibrary 来拼上下文。

  建议改成：

  - memory/store.py
      - 保留 ExperienceMemory
      - 只做 YAML read/write
      - save_eval_history
      - save_admission_history
      - forbidden/direction/history 的纯存储
  - application/context_service.py
      - 负责 compose_search_context
      - 从 memory + logic + registry 读取，拼成给 idea/mine 的上下文
  - evolution.py 不再被 memory 反向调用

  这是很关键的一刀。
  否则 memory 继续是“伪 store，真 orchestrator”。

  Phase 5: 拆 registry / library
  library.py 现在职责太杂，建议拆成：

  - registry/library.py
      - FactorLibrary
      - 对外门面 API：admit / replace / retire / list / load
  - registry/history.py
      - replace 前 detail archive
  - registry/values_cache.py
      - _load_values_cache
  - registry/publisher.py
      - DB publish 协调
  - 旧 src/mining/library.py 先保留兼容导出：
      - from .registry.library import FactorLibrary

  这样不需要一次性改全项目 import。

  Phase 6: logic 独立成子包
  把：

  - logic_library.py
  - scheduler.py

  移到：

  - logic/library.py
  - logic/scheduler.py

  这是自然聚类，且和 memory / registry / evaluator 解耦明显。

  Phase 7: 收口包 API
  最后再做这一层：

  - 精简 init.py
  - 只导出稳定对象：
      - MiningConfig
      - FactorMiningEvaluator
      - BatchResult
      - FactorLibrary
      - ExperienceMemory
  - 不再导出 DataSynchronizer 这种跨包对象
  - 内部模块统一改相对导入，减少 from mining.xxx import ... 的自引用

  测试同步计划
  重构时测试目录也一起调整，不然很快失控：

  tests/mining/
    cli/
    application/
    evaluation/
    registry/
    memory/
    logic/
    domain/

  最低要求：

  1. CLI 拆分后，现有 test_cli.py 先不删，只改入口适配。
  2. evaluator 拆分时，把 hard gates、similarity、BatchResult 单独测试。
  3. library 拆分时，加 replace archive / single-index-entry / retire 测试。
  4. memory 拆分时，把 compose_search_context 的测试从 memory 测试里迁出去。

  建议执行顺序

  1. Phase 1: CLI 拆分
  2. Phase 2: batch application service + Qlib runtime
  3. Phase 3: evaluator 拆分
  4. Phase 4: memory 边界清理
  5. Phase 5: registry 拆分
  6. Phase 6: logic 子包化
  7. Phase 7: __init__.py 收口 + import 清理

  不要做的事

  1. 不要一开始就大规模 rename 文件路径并全仓替换 import。
  2. 不要先拆 operators.py，它虽然大，但边界还算清楚，优先级低于 cli/evaluator/memory/library。
  3. 不要把 config.py 过早切碎；当前它还是稳定锚点。

  我对这个 restructuring 的判断
  最有价值的四刀是：

  1. cli.py -> cli/commands + application
  2. evaluator.py -> evaluator + gates + results + utils
  3. memory.py -> store，把 context builder 移出去
  4. library.py -> registry facade + submodules

