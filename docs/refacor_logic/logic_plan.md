下面直接给你一版**按你现有 skill 风格整理后的 `factor-logic v2` 完整文本**。                
我尽量保持和你现在 `/idea`、`/execute`、`/judge` 的写法一致，同时把我们前面讨论的核心制度都落进去。                                                     
                                                                                                                                                        
---                                                                                                                                                     
                                                                                                                                                        
````markdown                                                                                                                                            
---                                                                                                                                                     
name: factor-logic                                                                                                                                      
description: 管理市场逻辑假设（外循环）：提案 → 审查 → 立项/降级 → 调度                                                                                 
user_invocable: true                                                                                                                                    
---                                                                                                                                                     
                                                                                                                                                        
# /logic — Market Logic Management v2                                                                                                                   
                                                                                                                                                        
`factor-logic` 是整个自动因子研究系统的**外循环控制层**。                                                                                               
它不直接生成因子，而负责：                                                                                                                              
                                                                                                                                                        
- 定义哪些市场假设值得研究                                                                                                                              
- 审核新假设能否成为正式 logic                                                                                                                          
- 区分 logic 与 direction                                                                                                                               
- 给 `/idea` 分配探索预算                                                                                                                               
- 根据后续研究证据更新 logic 状态                                                                                                                       
                                                                                                                                                        
---                                                                                                                                                     
                                                                                                                                                        
## 核心原则                                                                                                                                             
                                                                                                                                                        
### 原则 1：模型不能自由发明市场规律                                                                                                                    
新逻辑只能来自以下合法来源：                                                                                                                            
- `canonical`：成熟金融研究常识                                                                                                                         
- `empirical_library`：从库内历史结果归纳                                                                                                               
- `near_miss_generalization`：从差一点成功的方向抽象提升                                                                                                
- `crossover_hypothesis`：两个已有逻辑的受控交叉                                                                                                        
- `external_inspiration`：外部资料启发，但必须经过本地化和审查                                                                                          
                                                                                                                                                        
### 原则 2：logic 必须少而强                                                                                                                            
不是所有新想法都建 logic。                                                                                                                              
很多新想法只是已有 logic 下的 direction、family mutation 或具体实现变体。                                                                               
                                                                                                                                                        
### 原则 3：logic 必须能约束 `/idea`                                                                                                                    
每个 logic 都必须输出 exploration contract，明确：                                                                                                      
- 当前优先级                                                                                                                                            
- 可分配预算                                                                                                                                            
- 推荐 family                                                                                                                                           
- 推荐算子与字段范围                                                                                                                                    
- 应避免的模式                                                                                                                                          
                                                                                                                                                        
### 原则 4：logic 必须有生命周期                                                                                                                        
每个 logic 必须处于以下状态之一：                                                                                                                       
- `proposed`                                                                                                                                            
- `active`                                                                                                                                              
- `warm`                                                                                                                                                
- `productive`                                                                                                                                          
- `saturated`                                                                                                                                           
- `parked`                                                                                                                                              
- `dead`                                                                                                                                                
                                                                                                                                                        
### 原则 5：logic 必须由证据更新                                                                                                                        
不能只靠 coverage 或 admit 数量判断。                                                                                                                   
必须综合：                                                                                                                                              
- probe/eval/admit 结果                                                                                                                                 
- near miss                                                                                                                                             
- overlap/forbidden                                                                                                                                     
- productive family                                                                                                                                     
- failed family                                                                                                                                         
- current bottleneck                                                                                                                                    
                                                                                                                                                        
---                                                                                                                                                     
                                                                                                                                                        
# 一、核心对象                                                                                                                                          
                                                                                                                                                        
## 1. Logic Proposal（草案对象）                                                                                                                        
                                                                                                                                                        
新逻辑先生成 proposal，不直接入库。                                                                                                                     
                                                                                                                                                        
```yaml                                                                                                                                                 
proposal_id: P021                                                                                                                                       
schema_version: v2                                                                                                                                      
                                                                                                                                                        
name: 缩量盘整后放量突破                                                                                                                                
origin_type: canonical                                                                                                                                  
category: volume_price                                                                                                                                  
                                                                                                                                                        
thesis: >                                                                                                                                               
  当成交量持续收缩且价格波动压缩后，后续成交放大更可能伴随方向性价格发现。                                                                              
                                                                                                                                                        
mechanism: >                                                                                                                                            
  压缩期通常对应分歧收敛与仓位静止，后续放量意味着新信息进入、                                                                                          
  仓位重建或突破确认，因此价格更易延续。                                                                                                                
                                                                                                                                                        
observable_proxy:                                                                                                                                       
  required_fields: [volume, close, high, low]                                                                                                           
  optional_fields: [amount]                                                                                                                             
  notes:                                                                                                                                                
    - 用成交量相对均值偏离描述缩量/放量                                                                                                                 
    - 用振幅或波动率描述价格压缩                                                                                                                        
                                                                                                                                                        
expected_horizon:                                                                                                                                       
  formation_window: [5, 60]                                                                                                                             
  holding_window: [5, 20]                                                                                                                               
                                                                                                                                                        
implementation_space:                                                                                                                                   
  preferred_families: [breakout, compression_spread, gated_trend]                                                                                       
  suggested_ops: [Mean, Std, Rank, TsDecay]                                                                                                             
  discouraged_ops: [deep_nested_interaction]                                                                                                            
                                                                                                                                                        
novelty_claim: >                                                                                                                                        
  区别于纯价格突破逻辑，这里强调量能压缩与释放的条件触发。                                                                                              
                                                                                                                                                        
probe_readiness:                                                                                                                                        
  can_probe: true                                                                                                                                       
  suggested_probe_forms:                                                                                                                                
    - "..."                                                                                                                                             
    - "..."                                                                                                                                             
                                                                                                                                                        
relations_guess:                                                                                                                                        
  possible_parent_logic: null                                                                                                                           
  overlaps_with: [L011]                                                                                                                                 
                                                                                                                                                        
submitted_at: ...                                                                                                                                       
````                                                                                                                                                    
                                                                                                                                                        
---                                                                                                                                                     
                                                                                                                                                        
## 2. Logic Review（审查对象）                                                                                                                          
                                                                                                                                                        
```yaml                                                                                                                                                 
proposal_id: P021                                                                                                                                       
schema_version: v2                                                                                                                                      
                                                                                                                                                        
mechanism_review:                                                                                                                                       
  verdict: pass                                                                                                                                         
  score: 0.84                                                                                                                                           
  comments:                                                                                                                                             
    - "存在较明确的价格发现与仓位重建机制"                                                                                                              
                                                                                                                                                        
feasibility_review:                                                                                                                                     
  verdict: pass                                                                                                                                         
  score: 0.92                                                                                                                                           
  comments:                                                                                                                                             
    - "OHLCV 可实现，当前字段足够"                                                                                                                      
                                                                                                                                                        
novelty_review:                                                                                                                                         
  verdict: borderline                                                                                                                                   
  score: 0.52                                                                                                                                           
  comments:                                                                                                                                             
    - "与已有 breakout family 有局部重叠，但条件触发不同"                                                                                               
                                                                                                                                                        
research                                                                                                                                                
… +324 lines …                                                                                                                                          
第1步：读取当前上下文                                                                                                                                   
                                                                                                                                                        
```bash                                                                                                                                                 
PYTHONPATH=src python3 -m mining logic coverage                                                                                                         
PYTHONPATH=src python3 -m mining logic list                                                                                                             
cat storage/memory/forbidden.yaml                                                                                                                       
cat storage/memory/state.yaml                                                                                                                           
ls storage/memory/history/                                                                                                                              
cat storage/library/library.yaml                                                                                                                        
cat storage/memory/mining-lessons.md                                                                                                                    
```                                                                                                                                                     
                                                                                                                                                        
### 第2步：识别 proposal 来源                                                                                                                           
                                                                                                                                                        
可从以下来源生成 proposal：                                                                                                                             
                                                                                                                                                        
* canonical                                                                                                                                             
* empirical_library                                                                                                                                     
* near_miss_generalization                                                                                                                              
* crossover_hypothesis                                                                                                                                  
* external_inspiration                                                                                                                                  
                                                                                                                                                        
### 第3步：生成 2-5 个 proposal（不直接入库）                                                                                                           
                                                                                                                                                        
每个 proposal 必须完整填写：                                                                                                                            
                                                                                                                                                        
* `origin_type`                                                                                                                                         
* `thesis`                                                                                                                                              
* `mechanism`                                                                                                                                           
* `observable_proxy`                                                                                                                                    
* `expected_horizon`                                                                                                                                    
* `implementation_space`                                                                                                                                
* `novelty_claim`                                                                                                                                       
* `probe_readiness`                                                                                                                                     
                                                                                                                                                        
### 第4步：写入草案文件                                                                                                                                 
                                                                                                                                                        
保存到：                                                                                                                                                
                                                                                                                                                        
```text                                                                                                                                                 
storage/logic/proposals/proposal_XXX.yaml                                                                                                               
```                                                                                                                                                     
                                                                                                                                                        
---                                                                                                                                                     
                                                                                                                                                        
## /logic review — 审查 proposal                                                                                                                        
                                                                                                                                                        
### 第1步：读取 proposal                                                                                                                                
                                                                                                                                                        
读取最近或指定的 proposal 文件。                                                                                                                        
                                                                                                                                                        
### 第2步：执行四类审查                                                                                                                                 
                                                                                                                                                        
必须逐项审查：                                                                                                                                          
                                                                                                                                                        
* **Mechanism Review**：有没有独立市场机制                                                                                                              
* **Feasibility Review**：当前平台能否实现                                                                                                              
* **Novelty Review**：是否和已有 logic 重叠，是否其实只是 direction                                                                                     
* **Research Value Review**：值不值得占预算                                                                                                             
                                                                                                                                                        
### 第3步：输出 review card                                                                                                                             
                                                                                                                                                        
保存到：                                                                                                                                                
                                                                                                                                                        
```text                                                                                                                                                 
storage/logic/reviews/review_XXX.yaml                                                                                                                   
```                                                                                                                                                     
                                                                                                                                                        
---                                                                                                                                                     
                                                                                                                                                        
## /logic admit — 立项 / 降级 / 拒绝                                                                                                                    
                                                                                                                                                        
### 第1步：读取 review 结果                                                                                                                             
                                                                                                                                                        
### 第2步：根据 gate 规则做决策                                                                                                                         
                                                                                                                                                        
四种可能结果：                                                                                                                                          
                                                                                                                                                        
* `create_logic`                                                                                                                                        
* `downgrade_to_direction`                                                                                                                              
* `park`                                                                                                                                                
* `reject`                                                                                                                                              
                                                                                                                                                        
### 第3步：执行动作                                                                                                                                     
                                                                                                                                                        
#### create_logic                                                                                                                                       
                                                                                                                                                        
* 分配 `logic_id`                                                                                                                                       
* 写入 `storage/logic/cards/logic_LXXX.yaml`                                                                                                            
* 初始状态设为 `active` 或 `warm`                                                                                                                       
                                                                                                                                                        
#### downgrade_to_direction                                                                                                                             
                                                                                                                                                        
* 不创建新 logic                                                                                                                                        
* 将该 proposal 记录到某个已有 logic 的方向候选池                                                                                                       
                                                                                                                                                        
#### park                                                                                                                                               
                                                                                                                                                        
* 写入 parked proposals，暂不进入 active pool                                                                                                           
                                                                                                                                                        
#### reject                                                                                                                                             
                                                                                                                                                        
* 写入 reject ledger，并记录原因                                                                                                                        
                                                                                                                                                        
### 第4步：更新 logic registry                                                                                                                          
                                                                                                                                                        
更新：                                                                                                                                                  
                                                                                                                                                        
```text                                                                                                                                                 
storage/logic/registry.yaml                                                                                                                             
```                                                                                                                                                     
                                                                                                                                                        
---                                                                                                                                                     
                                                                                                                                                        
## /logic schedule — 调度当前研究预算                                                                                                                   
                                                                                                                                                        
### 第1步：读取所有正式 logic card                                                                                                                      
                                                                                                                                                        
### 第2步：根据 priority score + lifecycle 状态计算本轮调度                                                                                             
                                                                                                                                                        
必须明确输出：                                                                                                                                          
                                                                                                                                                        
* active pool                                                                                                                                           
* warm pool                                                                                                                                             
* parked pool                                                                                                                                           
* blocked pool                                                                                                                                          
* 每个 active logic 的 budget                                                                                                                           
* global constraints                                                                                                                                    
                                                                                                                                                        
### 第3步：写入 schedule snapshot                                                                                                                       
                                                                                                                                                        
保存到：                                                                                                                                                
                                                                                                                                                        
```text                                                                                                                                                 
storage/logic/snapshots/schedule_YYYYMMDD_HHMMSS.yaml                                                                                                   
```                                                                                                                                                     
                                                                                                                                                        
### 第4步：输出给 `/idea` 的 exploration contract                                                                                                       
                                                                                                                                                        
---                                                                                                                                                     
                                                                                                                                                        
## /logic review-state — 查看当前 logic 状态                                                                                                            
                                                                                                                                                        
输出内容包括：                                                                                                                                          
                                                                                                                                                        
* 当前 logic 总数                                                                                                                                       
* 各状态数量                                                                                                                                            
* 各 category 覆盖                                                                                                                                      
* active logic 列表                                                                                                                                     
* saturated / parked / dead 列表                                                                                                                        
* 当前预算分配情况                                                                                                                                      
* 最近新建/退休 logic 摘要                                                                                                                              
                                                                                                                                                        
---                                                                                                                                                     
                                                                                                                                                        
# 九、当前 skill 的最终目标                                                                                                                             
                                                                                                                                                        
`factor-logic v2` 的目标不是“帮系统想更多方向”，而是：                                                                                                  
                                                                                                                                                        
* 让新逻辑来源合法                                                                                                                                      
* 让 logic 池保持少而强                                                                                                                                 
* 让 logic 成为真正的研究命题对象                                                                                                                       
* 让 logic 真正控制 `/idea` 的搜索空间                                                                                                                  
* 让后续研究结果持续更新 logic 层                                                                                                                       
* 让整个系统有清晰的外循环                                                                                                                              
                                                                                                                                                        
---                                                                                                                                                     
                                                                                                                                                        
# 十、简短总结                                                                                                                                          
                                                                                                                                                        
> `factor-logic v2` 应该是一套对市场假设进行**提案、审查、立项、调度、反馈和生命周期管理**的研究命题系统，而不是简单的“新方向生成器”。                  
                                                                                                                                                        
```                                                                                                                                                     
                                                                                                                                                        
这版已经可以作为你后续重构的母版了。                                                                                                                    
                                                                                                                                                        
下一步最顺的做法，是我继续帮你把它和 `/idea` 对齐，直接写出一版 **`factor-idea v2` 应该如何消费 logic contract**。  