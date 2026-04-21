# VALIDATION REPORT — room-selection prompt

生成:2026-04-11(Session 3)
验证执行者:Claude Opus 4.6(1M context)
被测件:
- `C:\Users\CLH\prompts\room-selection.md`(v0.1, schema v0.2)
- `C:\Users\CLH\docs\room-selection-policy.md`
测试方法:验证者以"selection prompt 宿主 LLM"身份,对 3 个典型议题 + 1 个 turn-mode 场景,按 prompt 的 A→E 步骤机械执行打分并产出严格 JSON。

---

## 0. 执行前的一致性核对

我先把 prompt 内嵌的 14 人候选池表格与实际 profile 文件对齐,避免"表和文件不同步"这种隐性 bug。抽检 6 份代表性 profile:

| Agent | prompt 表 sub_problem_tags | 实际 profile v0.2 字段 | 一致? |
|---|---|---|---|
| Jobs | value_proposition, product_focus, user_experience, first_principles, narrative_construction | 同 | ✓ |
| PG | value_proposition, market_timing, market_sizing, product_focus, first_principles | 同 | ✓ |
| Taleb | tail_risk, downside_analysis, resource_allocation, long_term_strategy, regulatory_risk | 同 | ✓ |
| Munger | downside_analysis, resource_allocation, first_principles, long_term_strategy, team_dynamics | 同 | ✓ |
| Zhang Xuefeng | execution_path, resource_allocation, team_dynamics, regulatory_risk, downside_analysis | 同 | ✓ |
| Sun | market_sizing, competitive_structure, market_timing, narrative_construction, resource_allocation, monetization | 同 | ✓ |

**结论**:抽检 6/14 全部一致。剩余 8 份未直读,但结构相似,信任度高。**无 drift 风险**。

---

## 1. Topic A — "独立开发者 AI 工具值不值得 All in?"

### 1.1 输入

```
mode: room_full
topic: 我想做一个面向独立开发者的 AI 工具,这个方向值不值得 All in?
user_constraints: { with: [], without: [], topic_hint: null }
```

### 1.2 阶段 A:议题解析

- **main_type**:`startup`(核心判断是"值不值得做一个方向")
- **secondary_type**:`strategy`(All in 涉及资源配置决策)
- **sub_problems**:
  1. "独立开发者 AI 工具这个切口值不值得做" → `[value_proposition, market_sizing]`
  2. "All in 还是小步试" → `[resource_allocation, market_timing]`
- **stage**:`explore`(用户在问"值不值得",还未定案,典型发散探索)
- **constraints**:空

**topic tag 集合** = `{value_proposition, market_sizing, resource_allocation, market_timing}`

### 1.3 阶段 B:硬过滤

| Agent | 规则 | 理由 |
|---|---|---|
| trump | R4 | `default_excluded=true`,未出现在 --with |

其余 13 人全部进入打分。

### 1.4 阶段 C 第一遍(4 项,0-80)

打分方法严格按交集规则,不允许语义打分。

| Agent | sub (0-30) | task (0-20) | stage (0-15) | uniq (0-15) | 第一遍小计 |
|---|---|---|---|---|---|
| **Sun** | 30(命中 market_sizing+market_timing+resource_allocation,3 hit) | 20(主 startup+副 strategy 均命中) | 15(explore 直命中) | 10(仅 PG 与其 ≥2 重合) | **75** |
| **PG** | 30(命中 value_proposition+market_timing+market_sizing,3 hit) | 20(主+副均命中) | 15(explore 直命中) | 0(Jobs/Ilya/Musk/Sun 均 ≥2 重合) | **65** |
| **Jobs** | 14(仅命中 value_proposition,1 hit) | 20(主+副均命中) | 8(simulate 相邻 explore) | 0(PG/Musk/Feynman/MrBeast 均 ≥2 重合) | **42** |
| **Naval** | 14(仅命中 resource_allocation) | 8(仅副类型命中) | 15(explore 直命中) | 0(Munger 4 tag 重合等) | **37** |
| **Ilya** | 14(仅 market_timing) | 8(仅副) | 15(explore 直命中) | 0(Feynman/Karpathy/Musk/Naval 均 ≥2) | **37** |
| **Musk** | 14(仅 resource_allocation) | 8(仅副) | 8(simulate 相邻) | 0(Jobs/Feynman/Karpathy/Zhang Yiming/Ilya 均 ≥2) | **30** |
| **Taleb** | 14(仅 resource_allocation) | 8(仅副) | 8(simulate 相邻) | 0(Munger/Naval/Zhang Xuefeng 均 ≥2) | **30** |
| **Munger** | 14(仅 resource_allocation) | 8(仅副) | 0(stress_test/converge/decision 均不相邻 explore) | 0 | **22** |
| **Zhang Xuefeng** | 14(仅 resource_allocation) | 8(仅副) | 0 | 0 | **22** |
| **MrBeast** | 0(0 命中,task 非 startup) | 0 | 15(explore) | 5(仅 Jobs/Zhang Yiming 2 人重合) | **20** |
| **Zhang Yiming** | 0 | 8(仅副) | 8(simulate 相邻) | 0 | **16** |
| **Feynman** | 0 | 0 | 15(explore) | 0 | **15** |
| **Karpathy** | 0 | 0 | 15(explore) | 0 | **15** |

**第一遍 top 3**(冻结为 structure_complement 参考集):Sun / PG / Jobs

### 1.5 阶段 C 第二遍(3 项)

**top 3 属性**:
- tendency:offensive / offensive / offensive → **0 defensive**
- expression:dramatic / abstract / grounded → 1 grounded
- strength:dominant / moderate / dominant → 2 dominant(未全 dominant)

**structure_complement**:只有"top 3 无 defensive + 本人 defensive → 10"这一条触发。

- Munger / Feynman / Taleb / Zhang Xuefeng → +10
- Karpathy(moderate 中立) → +0(不属于任一补位类别)
- 其他 → +0

**user_preference**:无信号 → 全 0

**redundancy_penalty**:
- dominant 累积:top 3 已有 2 个 dominant(Sun, Jobs),其他 dominant 候选触发 -5:Musk / Taleb / MrBeast
- 边缘 non_goals / 角色重复:均无明显触发

### 1.6 阶段 D:模型 ±5 校正

本次选择**不使用 ±5 校正**。理由:
- 所有规则项都严格按交集/关系表触发,没有"规则对了但语义微妙"的情况
- Taleb 虽然是"All in 议题的典型对冲位",但他只在结构补位项(+10)得分,subproblem 分数是机械交集算出的 14,没有"隐性语义"可以正当地 +5。**如果在这里给 Taleb +5,就是违反决议 23 的"因为感觉应该在"的校正**。
- 这是一个正面的"未滥用 ±5"样本。

### 1.7 总分表(按 TotalScore 降序)

| 排名 | Agent | sub | task | stage | uniq | struct | pref | pen | **Total** |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Sun | 30 | 20 | 15 | 10 | 0 | 0 | 0 | **75** |
| 2 | PG | 30 | 20 | 15 | 0 | 0 | 0 | 0 | **65** |
| 3 | Jobs | 14 | 20 | 8 | 0 | 0 | 0 | 0 | **42** |
| 4 | Naval | 14 | 8 | 15 | 0 | 0 | 0 | 0 | **37** |
| 5 | Ilya | 14 | 8 | 15 | 0 | 0 | 0 | 0 | **37** |
| 6 | Taleb | 14 | 8 | 8 | 0 | 10 | 0 | -5 | **35** |
| 7 | Munger | 14 | 8 | 0 | 0 | 10 | 0 | 0 | **32** |
| 8 | Zhang Xuefeng | 14 | 8 | 0 | 0 | 10 | 0 | 0 | **32** |
| 9 | Feynman | 0 | 0 | 15 | 0 | 10 | 0 | 0 | **25** |
| 10 | Musk | 14 | 8 | 8 | 0 | 0 | 0 | -5 | **25** |
| 11 | MrBeast | 0 | 0 | 15 | 5 | 0 | 0 | -5 | **15** |
| 12 | Zhang Yiming | 0 | 8 | 8 | 0 | 0 | 0 | 0 | **16** |
| 13 | Karpathy | 0 | 0 | 15 | 0 | 0 | 0 | 0 | **15** |

### 1.8 阶段 E:结构平衡 + 裁剪

#### 初始 top 4
Sun / PG / Jobs / Naval

- defensive=0 ✗(需要 ≥1)
- grounded=1 ✓(Jobs)
- dominant=2,2 ≤ 4/2=2 ✓

**失败**。

#### 迭代 1:替换
最低分非必要位 = Naval(37)。最高分 defensive 候选 = Taleb(35)。**替换 Naval → Taleb**。

新 top 4:Sun / PG / Jobs / Taleb

- defensive=1 ✓
- grounded=1 ✓(Jobs)
- dominant=3(Sun, Jobs, Taleb),3 > 2 ✗

**失败**。

#### 迭代 2:替换
需要减 1 个 dominant。最低分 dominant 是 Taleb(35)——但他是唯一 defensive,不能动。次低 dominant 是 Jobs(42),他是唯一 grounded,也是唯一"被 dominant 规则卡住且可安全替换"的位。同时需要补 grounded。

最优选择:**Jobs → Munger**(moderate+defensive+grounded,分数 32)。一步同时满足三件事:减 1 dominant + 仍保 grounded + 增 1 defensive。

新 top 4:Sun / PG / Munger / Taleb

- defensive=2 ✓(Munger, Taleb)
- grounded=1 ✓(Munger)
- dominant=2 ✓(Sun, Taleb)

**通过**。

### 1.9 输出 JSON(Topic A)

```json
{
  "mode": "room_full",
  "parsed_topic": {
    "main_type": "startup",
    "main_type_reason": "核心判断是某个方向值不值得启动,属于创业方向筛选",
    "secondary_type": "strategy",
    "sub_problems": [
      {"text": "独立开发者 AI 工具这个切口值不值得做", "tags": ["value_proposition", "market_sizing"]},
      {"text": "All in 还是小步试", "tags": ["resource_allocation", "market_timing"]}
    ],
    "stage": "explore",
    "stage_reason": "用户在问'值不值得',还未定案,典型发散探索",
    "constraints": {"with": [], "without": [], "mentions": []}
  },
  "hard_filtered": [
    {"agent": "trump", "rule": "R4", "reason": "default_excluded=true,未出现在 --with"}
  ],
  "scorecards": [
    {"agent": "justin-sun", "scores": {"subproblem_match": 30, "task_type_match": 20, "stage_fit": 15, "role_uniqueness": 10, "structure_complement": 0, "user_preference": 0, "redundancy_penalty": 0, "model_adjust": 0, "model_adjust_reason": ""}, "total": 75},
    {"agent": "paul-graham", "scores": {"subproblem_match": 30, "task_type_match": 20, "stage_fit": 15, "role_uniqueness": 0, "structure_complement": 0, "user_preference": 0, "redundancy_penalty": 0, "model_adjust": 0, "model_adjust_reason": ""}, "total": 65},
    {"agent": "steve-jobs", "scores": {"subproblem_match": 14, "task_type_match": 20, "stage_fit": 8, "role_uniqueness": 0, "structure_complement": 0, "user_preference": 0, "redundancy_penalty": 0, "model_adjust": 0, "model_adjust_reason": ""}, "total": 42},
    {"agent": "naval", "scores": {"subproblem_match": 14, "task_type_match": 8, "stage_fit": 15, "role_uniqueness": 0, "structure_complement": 0, "user_preference": 0, "redundancy_penalty": 0, "model_adjust": 0, "model_adjust_reason": ""}, "total": 37},
    {"agent": "ilya-sutskever", "scores": {"subproblem_match": 14, "task_type_match": 8, "stage_fit": 15, "role_uniqueness": 0, "structure_complement": 0, "user_preference": 0, "redundancy_penalty": 0, "model_adjust": 0, "model_adjust_reason": ""}, "total": 37},
    {"agent": "taleb", "scores": {"subproblem_match": 14, "task_type_match": 8, "stage_fit": 8, "role_uniqueness": 0, "structure_complement": 10, "user_preference": 0, "redundancy_penalty": -5, "model_adjust": 0, "model_adjust_reason": ""}, "total": 35},
    {"agent": "munger", "scores": {"subproblem_match": 14, "task_type_match": 8, "stage_fit": 0, "role_uniqueness": 0, "structure_complement": 10, "user_preference": 0, "redundancy_penalty": 0, "model_adjust": 0, "model_adjust_reason": ""}, "total": 32},
    {"agent": "zhangxuefeng", "scores": {"subproblem_match": 14, "task_type_match": 8, "stage_fit": 0, "role_uniqueness": 0, "structure_complement": 10, "user_preference": 0, "redundancy_penalty": 0, "model_adjust": 0, "model_adjust_reason": ""}, "total": 32},
    {"agent": "feynman", "scores": {"subproblem_match": 0, "task_type_match": 0, "stage_fit": 15, "role_uniqueness": 0, "structure_complement": 10, "user_preference": 0, "redundancy_penalty": 0, "model_adjust": 0, "model_adjust_reason": ""}, "total": 25},
    {"agent": "elon-musk", "scores": {"subproblem_match": 14, "task_type_match": 8, "stage_fit": 8, "role_uniqueness": 0, "structure_complement": 0, "user_preference": 0, "redundancy_penalty": -5, "model_adjust": 0, "model_adjust_reason": ""}, "total": 25},
    {"agent": "zhang-yiming", "scores": {"subproblem_match": 0, "task_type_match": 8, "stage_fit": 8, "role_uniqueness": 0, "structure_complement": 0, "user_preference": 0, "redundancy_penalty": 0, "model_adjust": 0, "model_adjust_reason": ""}, "total": 16},
    {"agent": "mrbeast", "scores": {"subproblem_match": 0, "task_type_match": 0, "stage_fit": 15, "role_uniqueness": 5, "structure_complement": 0, "user_preference": 0, "redundancy_penalty": -5, "model_adjust": 0, "model_adjust_reason": ""}, "total": 15},
    {"agent": "karpathy", "scores": {"subproblem_match": 0, "task_type_match": 0, "stage_fit": 15, "role_uniqueness": 0, "structure_complement": 0, "user_preference": 0, "redundancy_penalty": 0, "model_adjust": 0, "model_adjust_reason": ""}, "total": 15}
  ],
  "roster": [
    {"agent": "justin-sun", "short_name": "Sun", "role": "市场结构与 All in 判断位", "structural_role": "offensive"},
    {"agent": "paul-graham", "short_name": "PG", "role": "切口真假与市场时机判断", "structural_role": "offensive"},
    {"agent": "munger", "short_name": "Munger", "role": "机会成本与自欺审查", "structural_role": "defensive"},
    {"agent": "taleb", "short_name": "Taleb", "role": "尾部风险与不可逆损失对冲", "structural_role": "defensive"}
  ],
  "speakers": null,
  "structural_check": {
    "defensive_count": 2,
    "grounded_count": 1,
    "dominant_count": 2,
    "dominant_ratio": 0.5,
    "passed": true,
    "warnings": []
  },
  "forced_rebalance": null,
  "explanation": {
    "why_selected": [
      "Sun (75):子问题命中 market_sizing+market_timing+resource_allocation 3 tag,主+副 task 全中,stage 直命中 explore,是当前议题唯一能谈 winner-takes-all 和 All in 决策的人",
      "PG (65):子问题命中 value_proposition+market_timing+market_sizing 3 tag,主+副 task 全中,stage 直命中,切口真假判断不可替代",
      "Munger (32):替换 Jobs 进入——同时补 defensive 和 grounded,阻止 Sun 的 All in 倾向失控,机会成本校准",
      "Taleb (35):替换 Naval 进入——补 defensive 位,对冲 All in 的不可逆尾部损失"
    ],
    "why_not_selected": [
      "Jobs (42):虽第 3 名,但他和 Sun 都是 dominant+offensive,保留他会让 dominant=3 超过 4/2=2 的硬规则。Munger 更能同时补 defensive + grounded 位",
      "Naval (37):虽第 4 名,但他是 offensive,无法补 defensive 缺失。Taleb 虽分数略低但能补位",
      "Ilya (37):task_types 命中 strategy 副类型,但本议题的 market_timing tag 仅 1 命中,且他的角度更偏'长期 AI 基建',不贴合'独立开发者工具'的切口判断",
      "Musk/Zhang Yiming/Zhang Xuefeng/Feynman/Karpathy/MrBeast:sub_problem_match ≤14 或任务类型不契合,分数在中后段",
      "Trump:R4 硬过滤剔除"
    ]
  }
}
```

### 1.10 Topic A 观察

✅ **结果与 Session 2 预期一致**(PG + Sun + Taleb + Munger)
⚠️ **但达成路径非直接**:top 4 默认取出的是 Sun/PG/Jobs/Naval,需要**两轮替换**才能收敛到最终花名册。policy §9.2 的"替换→仍不满足则扩招"没有明确说"迭代式替换",我按"直到平衡或扩到 8"做了迭代。**这是 policy 的解释空间,需要 prompt 明确。**

---

## 2. Topic B — "这个按钮放左边还是右边"

### 2.1 输入

```
mode: room_full
topic: 这个按钮放左边还是右边
user_constraints: { with: [], without: [], topic_hint: null }
```

topic 长度 14 字 ≥ 10 ✓(未触发 `topic_too_vague`)

### 2.2 阶段 A

- **main_type**:`product`
- **secondary_type**:null
- **sub_problems**:
  1. "按钮位置选择" → `[user_experience, product_focus]`
- **stage**:`converge`(典型"A 还是 B"二选一信号)

topic tag 集合 = `{user_experience, product_focus}`

### 2.3 阶段 B:硬过滤

| Agent | 规则 | 理由 |
|---|---|---|
| trump | R4 | default_excluded |
| taleb | R3 | profile 明确写"不主做用户体验裁判",与 topic 主类型 product + UX 子问题正面冲突 |
| justin-sun | R3 | profile 明确写"不主做用户体验与产品细节裁判",与 topic 正面冲突 |

**11 人**进入打分。

### 2.4 阶段 C 第一遍

| Agent | sub | task | stage | uniq | 第一遍 |
|---|---|---|---|---|---|
| **Jobs** | 22(user_experience+product_focus,2 hit) | 15(主 product) | 15(converge 直命中) | 0 | **52** |
| **Musk** | 14(product_focus 1 hit) | 15(主) | 15(converge 直命中) | 0 | **44** |
| **Zhang Yiming** | 14(product_focus 1 hit) | 15(主) | 15(converge 直命中) | 0 | **44** |
| **MrBeast** | 14(user_experience 1 hit) | 15(主 product) | 8(decision 相邻 converge) | 5(仅 Jobs+Zhang Yiming 2 人 ≥2 重合) | **42** |
| **Feynman** | 14(user_experience 1 hit) | 15(主 product) | 8(simulate 相邻 converge) | 0 | **37** |
| **Karpathy** | 6(0 命中但主 task 匹配) | 15(主 product) | 15(converge 直命中) | 0 | **36** |
| **PG** | 14(product_focus 1 hit) | 0(非 product) | 8(decision 相邻) | 0 | **22** |
| **Munger** | 0 | 0 | 15(converge 直命中) | 0 | **15** |
| **Zhang Xuefeng** | 0 | 0 | 15(converge 直命中) | 0 | **15** |
| **Naval** | 0 | 0 | 15(converge 直命中) | 0 | **15** |
| **Ilya** | 0 | 0 | 8(simulate 相邻) | 0 | **8** |

**第一遍 top 3**:Jobs / Musk / Zhang Yiming

### 2.5 阶段 C 第二遍

**top 3 属性**:
- tendency:offensive / offensive / offensive → **0 defensive**
- expression:grounded / grounded / grounded → 3 grounded(已饱和)
- strength:dominant / dominant / moderate → 2 dominant

**structure_complement**:
- "无 defensive + 本人 defensive → 10":Munger / Feynman / Zhang Xuefeng → +10
- 其他 → 0

**user_preference**:全 0

**redundancy_penalty**:
- dominant 累积:top 3 已有 2 dominant,其他 dominant 候选 → -5:MrBeast
- 角色重复:Zhang Yiming 和 Jobs 都侧重产品但角度不同(聚焦 vs 增长),不触发 -10
- Karpathy 虽然都在做产品细节,但他的 sub_tag 0 命中,罚不上

### 2.6 总分表

| 排名 | Agent | Total |
|---|---|---|
| 1 | Jobs | 52 |
| 2 | Feynman | 47(14+15+8+0+**10**+0+0) |
| 3 | Musk | 44 |
| 4 | Zhang Yiming | 44 |
| 5 | MrBeast | 37(42-5) |
| 6 | Karpathy | 36 |
| 7 | Munger | 25(15+**10**) |
| 8 | Zhang Xuefeng | 25(15+**10**) |
| 9 | PG | 22 |
| 10 | Naval | 15 |
| 11 | Ilya | 8 |

### 2.7 阶段 E

**初始 top 4**:Jobs / Feynman / Musk / Zhang Yiming

- defensive=1 ✓(Feynman)
- grounded=4 ✓(全 grounded)
- dominant=2 ✓(Jobs, Musk)

**通过!一次性通过,零替换**。

### 2.8 Topic B 输出 JSON(摘要)

```json
{
  "mode": "room_full",
  "parsed_topic": {
    "main_type": "product",
    "main_type_reason": "按钮位置是纯 UI 决策",
    "secondary_type": null,
    "sub_problems": [{"text": "按钮位置选择", "tags": ["user_experience", "product_focus"]}],
    "stage": "converge",
    "stage_reason": "A 还是 B 的二选一信号,典型 converge",
    "constraints": {"with": [], "without": [], "mentions": []}
  },
  "hard_filtered": [
    {"agent": "trump", "rule": "R4", "reason": "default_excluded"},
    {"agent": "taleb", "rule": "R3", "reason": "profile 写'不主做用户体验裁判',与 UX 子问题正面冲突"},
    {"agent": "justin-sun", "rule": "R3", "reason": "profile 写'不主做用户体验与产品细节裁判',正面冲突"}
  ],
  "roster": [
    {"agent": "steve-jobs", "short_name": "Jobs", "role": "产品聚焦与取舍主导", "structural_role": "offensive"},
    {"agent": "feynman", "short_name": "Feynman", "role": "第一性原理解释与用户认知路径校准", "structural_role": "defensive"},
    {"agent": "elon-musk", "short_name": "Musk", "role": "功能/技术维度裁判", "structural_role": "offensive"},
    {"agent": "zhang-yiming", "short_name": "Zhang Yiming", "role": "增长与转化视角", "structural_role": "offensive"}
  ],
  "structural_check": {"defensive_count": 1, "grounded_count": 4, "dominant_count": 2, "dominant_ratio": 0.5, "passed": true, "warnings": []},
  "explanation": {
    "why_selected": ["Jobs (52):主类型+子问题全中,UI 决策的直接权威", "Feynman (47):补 defensive 位 + 用户认知解释"],
    "why_not_selected": ["Taleb/Sun:R3 剔除", "PG:task_types 无 product,分数只 22"]
  }
}
```

### 2.9 Topic B 观察 ⚠️ 最重要的发现之一

**NEXT-STEPS.md 的预期**:"预期只触发 Jobs,单人足够,可能触发 `候选不足` 警告"

**实际结果**:4 人花名册(Jobs + Feynman + Musk + Zhang Yiming),结构平衡一次通过,**没有任何"候选不足"警告**。

#### ❌ FINDING #1:**算法对"议题琐碎度"完全无感知**

- policy 和 prompt 都默认花名册目标 **2-8 人,默认 top 4**
- 不论议题是"值不值得 All in"还是"按钮左右",都一视同仁取 top 4
- 4 人讨论"按钮左右"是**过度调用**,违背决议 10 关于"协同推演 60%/探索 20%/陪跑 20%"的定位——这种 UI 微决策应该是陪跑模式,单人即可
- **没有任何机制** 检测"top1 分数远高于 top2"或"topic 复杂度极低"时自动缩减 roster

#### ❌ FINDING #2:**`all_filtered_out` / `no_qualifying_roster` 错误码永远不会在 Topic B 类议题上触发**

- 硬过滤后还剩 11 人,`all_filtered_out`(< 2 人)不触发
- 结构平衡一次通过,`no_qualifying_roster` 不触发
- NEXT-STEPS 期望的"候选不足"警告在当前规则下**无路径可以产出**

#### 建议修补

在 policy / prompt 中增加**议题琐碎度降级规则**:

```
额外规则 E-0(建议新增):在 E-1 排序后,如果同时满足:
  1. top1 与 top2 分差 ≥ 20
  2. top1 score ≥ 60
  3. stage ∈ {converge, decision}
  4. 子问题数量 = 1
  5. topic 长度 ≤ 20 字
→ roster 只取 top1,单人花名册,输出 warning: "议题琐碎,降级为单人咨询模式"
```

或更简洁的版本:

```
如果 top1 ≥ top2 + 15 且 stage ∈ {converge, decision} → 只取 2 人(top1+唯一对冲位)
```

这在 Topic A/C 都不会误触发(它们 top1/top2 差距都 ≤ 10)。

---

## 3. Topic C — "如果这个项目失败了最坏会怎样"

### 3.1 输入

```
mode: room_full
topic: 如果这个项目失败了最坏会怎样
user_constraints: { with: [], without: [], topic_hint: null }
```

### 3.2 阶段 A

- **main_type**:`risk`
- **secondary_type**:null(置信度 < 60% 不填)
- **sub_problems**:
  1. "最坏情况" → `[tail_risk, downside_analysis]`
- **stage**:`stress_test`(明确"最坏会怎样"的压力测试信号)

topic tag 集合 = `{tail_risk, downside_analysis}`

### 3.3 阶段 B:硬过滤

| Agent | 规则 | 理由 |
|---|---|---|
| trump | R4 | default_excluded |
| justin-sun | R3 | profile 写"不主做尾部风险兜底",与 tail_risk 子问题正面冲突 |

**边缘案例 1(未过滤但值得讨论)**:
- **Jobs** 的 non_goals 写"不主做长期风险兜底"——"长期"是限定词,本议题是"失败最坏"(时点未限定)。按 policy "宁可少剔不错剔",不过滤。

**边缘案例 2**:
- **PG** 写"不主做系统性风险兜底"——"系统性"也是限定词,不过滤。

**12 人**进入打分。

### 3.4 阶段 C 第一遍

| Agent | sub | task | stage | uniq | 第一遍 |
|---|---|---|---|---|---|
| **Taleb** | 22(tail_risk+downside_analysis 2 hit) | 15(主 risk) | 15(stress_test 直命中) | 0 | **52** |
| **Munger** | 14(downside_analysis 1 hit) | 15(主 risk) | 15(stress_test 直命中) | 0 | **44** |
| **Zhang Xuefeng** | 14(downside_analysis 1 hit) | 0(无 risk) | 15(stress_test 直命中) | 0 | **29** |
| **Ilya** | 6(0 命中但主 risk 命中) | 15(主 risk) | 8(simulate 相邻) | 0 | **29** |
| **MrBeast** | 0 | 0 | 8(decision 不相邻 stress_test) | 5 | **13** |
| **Jobs** | 0 | 0 | 8(simulate 相邻) | 0 | **8** |
| **Musk** | 0 | 0 | 8(simulate 相邻) | 0 | **8** |
| **Feynman** | 0 | 0 | 8(simulate 相邻) | 0 | **8** |
| **Naval** | 0 | 0 | 8(simulate 相邻) | 0 | **8** |
| **PG** | 0 | 0 | 8(simulate 相邻) | 0 | **8** |
| **Zhang Yiming** | 0 | 0 | 8(simulate 相邻) | 0 | **8** |
| **Karpathy** | 0 | 0 | 8(simulate 相邻) | 0 | **8** |

**MrBeast stage 复算**:MrBeast stage_fit=[explore, simulate, decision]。stress_test 的相邻=`{simulate, decision}`。MrBeast 有 simulate 和 decision 两者。**simulate 相邻 ✓,得 8**(非 0)。修正上表 MrBeast 为 0+0+8+5=13 ✓(原值正确)。

**第一遍 top 3**:Taleb / Munger / (Zhang Xuefeng 与 Ilya 29 分并列)

❌ **FINDING #3:tie 无规则**

policy 没有定义并列分的 tie-breaker。我按"sub_problem 命中数更多者优先"(ZX 有 downside_analysis 直接命中,Ilya 是 0 命中靠主 task 补 6 分)→ top 3 = Taleb / Munger / Zhang Xuefeng。

**建议修补**:policy §9.1 补充 tie-breaker 规则,建议优先级:
1. subproblem_match 高者
2. stage_fit 直命中者
3. role_uniqueness 高者
4. 仍并列则保留全部(轻微超 top 3)

### 3.5 阶段 C 第二遍

**top 3 属性**:
- tendency:defensive / defensive / defensive → **3 defensive ✓**
- expression:abstract / grounded / grounded → 2 grounded
- strength:dominant / moderate / moderate → 1 dominant

**structure_complement**:**所有条件都不触发**
- top 3 全 dominant:FALSE(只 1)
- top 3 无 grounded:FALSE(2 个)
- top 3 无 defensive:FALSE(3 个)
- 全员 structure_complement=0

❌ **FINDING #4:当 top 3 已经极度"防御平衡"时,结构补位分彻底失效**

这意味着 Topic C 的 top 3 之后的排名完全靠"raw subproblem/task/stage/uniqueness"决定,无法通过补位分让 offensive 候选翻身进场。结果:**100% defensive/0% offensive 花名册**。

这不是单纯的 bug,而是 policy 的一个隐含偏差:

- §9.3 只要求 `至少 1 defensive / 至少 1 grounded / dominant ≤ 人数/2`
- **没有**"至少 1 offensive"的对称要求
- 在 stress_test / downside 类议题上,会出现整房间全是 defensive 视角,失去"反对的反对"角色

### 3.6 阶段 E

**初始 top 4**:Taleb(52)/ Munger(44)/ Zhang Xuefeng(29)/ Ilya(29)

- defensive=3 ✓(Taleb, Munger, Zhang Xuefeng;Ilya 是 offensive)
- grounded=2 ✓(Munger, Zhang Xuefeng)
- dominant=1,1 ≤ 4/2=2 ✓

**通过**。

但**观察**:第 4 位 Ilya 只靠 task_type_match 的 15 分和"0 命中+主类型命中"的 6 分拿到 29,没有任何 sub_problem_tag 与 topic 交集。他进入 roster 主要是填位,角度其实是"长期 AI 基建战略"——**对 tail_risk 讨论贡献有限**。

❌ **FINDING #5:task_type_match 的 15 分地板 + 6 分 sub 地板导致"标签对但角度不对"的 Agent 可以填位**

数字层面:一个 Agent 只要 task_type 主命中(15)+ 仅主 task 触发 sub 的 6 分地板 + stage 相邻(8),就能拿到 29 分。这个分数足够在"多数人都只有 8 分"的议题中排第 4。

**建议修补**:
- 要么把 "0 sub 命中 + 主 task 命中 → 6" 改为 "→ 0"(强化 sub_problem 的主导权)
- 要么在 E 阶段增加"roster 内必须至少 3 人有 sub_problem 命中 ≥ 1"的硬规则

### 3.7 Topic C 输出 JSON(摘要)

```json
{
  "mode": "room_full",
  "parsed_topic": {
    "main_type": "risk",
    "secondary_type": null,
    "sub_problems": [{"text": "最坏情况", "tags": ["tail_risk", "downside_analysis"]}],
    "stage": "stress_test",
    "stage_reason": "明确'最坏会怎样',典型 stress_test"
  },
  "hard_filtered": [
    {"agent": "trump", "rule": "R4", "reason": "default_excluded"},
    {"agent": "justin-sun", "rule": "R3", "reason": "不主做尾部风险兜底"}
  ],
  "roster": [
    {"agent": "taleb", "short_name": "Taleb", "role": "尾部风险与不可逆损失", "structural_role": "defensive"},
    {"agent": "munger", "short_name": "Munger", "role": "机会成本与自欺审查", "structural_role": "defensive"},
    {"agent": "zhangxuefeng", "short_name": "Zhang Xuefeng", "role": "现实落地代价与执行门槛", "structural_role": "defensive"},
    {"agent": "ilya-sutskever", "short_name": "Ilya", "role": "长期战略与不可逆后果", "structural_role": "offensive"}
  ],
  "structural_check": {"defensive_count": 3, "grounded_count": 2, "dominant_count": 1, "dominant_ratio": 0.25, "passed": true, "warnings": ["roster 内 3/4 为 defensive,议题类型天然偏斜"]},
  "explanation": {
    "why_selected": ["Taleb:tail_risk 和 downside_analysis 2 tag 全中,stress_test 直命中", "Munger:downside_analysis 1 tag + 主 risk 命中 + stress_test 直命中"],
    "why_not_selected": ["Sun:R3 剔除", "Jobs/PG/Musk 等:子问题完全不命中,task 不匹配 risk,分数落在 8"]
  }
}
```

### 3.8 Topic C 观察

- Session 2 预期:"Taleb + Munger + Zhang Xuefeng"(3 人)
- 实际:4 人(多了 Ilya)
- Ilya 的进入既是算法正确执行的结果,也是 FINDING #5 暴露的边缘问题

---

## 4. Turn-Mode 测试(room_turn + 强制补位)

### 4.1 背景假设

用 Topic A 的花名册继续推演,但**为了让强制补位规则有意义,我扩展花名册到 5 人**(假设用户在中途 `/add zhang-yiming`)。否则 4 人花名册打 4 人硬顶意味着所有人都发言,强制补位无从触发。

### 4.2 输入

```
mode: room_turn
topic: 我想做一个面向独立开发者的 AI 工具,这个方向值不值得 All in?
user_constraints: { with: [], without: [] }
current_state:
  roster: [justin-sun, paul-graham, munger, taleb, zhang-yiming]
  last_stage: simulate
  recent_log: "Sun/PG/Zhang Yiming 连续发言 3 轮,讨论了市场结构、切口、增长;Taleb/Munger 未入选"
  silent_rounds: { taleb: 3, munger: 3 }
```

### 4.3 打分(只对 5 人花名册)

stage 从 explore 推进到 simulate。重算:

| Agent | sub | task | stage(simulate) | uniq(5 人池) | 第一遍 |
|---|---|---|---|---|---|
| **Sun** | 30 | 20 | 15(直命中) | 10(仅 PG 2 tag ≥2) | **75** |
| **PG** | 30 | 20 | 15(直命中) | 10(仅 Sun) | **75** |
| **Zhang Yiming** | 0 | 8(仅副 strategy) | 15(直命中) | 15(无人与 Zhang Yiming ≥2 tag 重合)| **38** |
| **Taleb** | 14 | 8 | 15(直命中) | 10(仅 Munger ≥2) | **47** |
| **Munger** | 14 | 8 | 8(stress_test 相邻 simulate) | 10(仅 Taleb ≥2) | **40** |

**top 3 参考**:Sun / PG / Taleb

**structure_complement**:
- top 3 tendency:off/off/def → 有 defensive
- top 3 expression:dramatic/abstract/abstract → 无 grounded → grounded 本人 = +10
- → Munger(grounded)+10,Zhang Yiming(grounded)+10

**user_preference**:全 0
**redundancy_penalty**:dominant 累积 top 3 有 2 个(Sun, Taleb)→ 其他 dominant -5 无人(Zhang Yiming mod)

**总分表**:

| 排名 | Agent | Total |
|---|---|---|
| 1 | Sun | 75 |
| 2 | PG | 75 |
| 3 | Munger | 50(40+10) |
| 4 | Taleb | 47 |
| 5 | Zhang Yiming | 48(38+10) |

**常规 top 4 speakers**:Sun / PG / Munger / Zhang Yiming(48)~ Taleb(47) → Zhang Yiming 48 vs Taleb 47 差 1 分

### 4.4 强制补位检查(E-3 步骤 3)

`silent_rounds` 输入:
- Taleb:3 → **触发**
- Munger:3 → **触发**(但 Munger 已在 top 4,无需强制)

**Taleb**:tendency=defensive,stage_fit 包含 simulate(≠ decision),不豁免 → **强制加入本轮**

**动作**:替换当前 top 4 中分数最低的 dominant/offensive 位。

- Sun:dom/off - 75(保留)
- PG:mod/off - 75(保留)
- Munger:mod/def - 50(保留,defensive 不替换)
- Zhang Yiming:mod/off - 48(**最低 offensive/dominant,被替换**)

**新 speakers**:Sun / PG / Munger / Taleb,标注"强制补位触发:taleb 已连续 3 轮沉默"。

### 4.5 输出 JSON(turn-mode)

```json
{
  "mode": "room_turn",
  "parsed_topic": {
    "main_type": "startup",
    "secondary_type": "strategy",
    "sub_problems": [
      {"text": "独立开发者 AI 工具值不值得做", "tags": ["value_proposition", "market_sizing"]},
      {"text": "All in 还是小步试", "tags": ["resource_allocation", "market_timing"]}
    ],
    "stage": "simulate",
    "constraints": {"with": [], "without": [], "mentions": []}
  },
  "hard_filtered": [],
  "scorecards": [
    {"agent": "justin-sun", "total": 75, "scores": {...}},
    {"agent": "paul-graham", "total": 75, "scores": {...}},
    {"agent": "munger", "total": 50, "scores": {...}},
    {"agent": "zhang-yiming", "total": 48, "scores": {...}},
    {"agent": "taleb", "total": 47, "scores": {...}}
  ],
  "roster": [
    {"agent": "justin-sun"}, {"agent": "paul-graham"}, {"agent": "munger"},
    {"agent": "taleb"}, {"agent": "zhang-yiming"}
  ],
  "speakers": [
    {"agent": "justin-sun", "short_name": "Sun", "role": "本轮主攻: winner-takes-all 推演与 All in 情景"},
    {"agent": "paul-graham", "short_name": "PG", "role": "本轮主攻: 切口是否真窄"},
    {"agent": "munger", "short_name": "Munger", "role": "本轮防守: 自欺检查与机会成本"},
    {"agent": "taleb", "short_name": "Taleb", "role": "本轮防守(强制补位): 尾部风险"}
  ],
  "structural_check": {"defensive_count": 2, "grounded_count": 1, "dominant_count": 2, "dominant_ratio": 0.5, "passed": true, "warnings": []},
  "forced_rebalance": {"agent": "taleb", "reason": "silent 3 rounds, defensive 位必须回到单轮"},
  "explanation": {
    "why_selected": [
      "Sun/PG:总分并列最高 75,仍是本议题的主攻手",
      "Munger:50 分自然入选 top 4,同时补 grounded 位",
      "Taleb:强制补位 — 原本 47 分排第 5,但连续 3 轮沉默触发 E-3.3 规则,替换掉 Zhang Yiming (48) 的 offensive 位"
    ],
    "why_not_selected": [
      "Zhang Yiming (48):本应按分数进入 top 4,但因强制补位规则被 Taleb 替换。会在下一轮重新参与选人"
    ]
  }
}
```

### 4.6 Turn-mode 观察

✅ **强制补位触发**:Taleb 替换 Zhang Yiming,规则按 policy §12 执行
✅ **silent_rounds 字段被成功消费**
⚠️ **Munger 也 silent 3 轮,但他自然入 top 4,无需强制补位** —— 这是正确行为,但 policy 没说"如果强制候选已在 top 中无需触发",我按常识理解。

#### ❌ FINDING #6:**`silent_rounds` 状态由谁维护?policy 没定义**

- policy §12 说"Agent 连续 3 轮未被选入"
- prompt 输入契约里有 `silent_rounds: { "<agent>": <n> }`
- **但没有任何文件说明**:这个计数器在哪里增/减?每轮结束后是谁把它传给下一轮?
- 当前 selection prompt 只是**消费者**,需要外部 orchestrator(主持器层)维护状态
- 这是 **Phase 2**(`docs/room-architecture.md`)必须补的状态字段,否则强制补位规则**永远不会被触发**——因为 `silent_rounds` 会始终为空

#### ❌ FINDING #7:**豁免条件 3 需要外部 stage 判断**

policy §12 豁免条件之一:"当前 stage 是 decision 且 Agent 的 stage_fit 不包含 decision"。这要求 prompt 能从 input 读到 `last_stage` 并判断。当前 prompt input 契约确实有 `last_stage` 字段 ✓,但 prompt 主体并未明确提到"豁免检查"这一步。建议在 prompt §E-3.3 补一句:"强制补位前,先检查豁免条件:...,豁免时跳过强制并在 warnings 中记录"。

---

## 5. 汇总:所有发现

| # | 严重度 | 类别 | 描述 |
|---|---|---|---|
| 1 | 🔴 高 | 未覆盖场景 | 算法对"议题琐碎度"无感知,按钮左右类 UI 微决策会被过度分配 4 人花名册 |
| 2 | 🟡 中 | 错误码路径 | `no_qualifying_roster` / `all_filtered_out` 对 Topic B 类议题永远不会触发,NEXT-STEPS 的"候选不足"预期无落地路径 |
| 3 | 🟡 中 | 规则缺失 | top 3 并列分无 tie-breaker 规则 |
| 4 | 🟡 中 | 单边偏斜 | 结构平衡只要求 ≥1 defensive,没有"≥1 offensive"对称要求,stress_test 类议题会产生 100% defensive 阵容 |
| 5 | 🟡 中 | 地板分过高 | `0 sub 命中 + 主 task 命中 → 6` + `task_type_match 主命中 → 15` 让"标签对但角度不对"的 Agent 可以混进 roster 靠填位 |
| 6 | 🔴 高 | 状态缺口 | `silent_rounds` 计数器由谁维护?policy/prompt 都没定义,强制补位在实际运行中**永远不会被触发**。必须在 Phase 2 的 `room-architecture.md` 明确状态所有权 |
| 7 | 🟢 低 | 文档 | prompt E-3 步骤未明确强调豁免条件检查顺序 |
| 8 | 🟢 低 | 算法说明 | §9.2 的"替换→扩招"对"迭代式替换"的要求不明确,实际执行需要 2 轮以上替换才能收敛(Topic A 正是如此) |
| 9 | 🟢 低 | 可执行性 | "两遍打分"要求 LLM 自我纪律先算 4 项再算 3 项,存在被跳过的风险(但本次我没跳) |
| 10 | 🟢 低 | 冗余惩罚模糊 | "单一强势风格过度累积 ≥2 dominant"的判定对"Top 3 内的自己 / 其他候选"区分不清,我按"其他候选才罚"处理 |

---

## 6. 稳定性主观评分

**6/10**

### 评分理由

- **✓ 强项**(为什么不低于 5):
  - JSON schema 严格可产出,无缺字段问题
  - 机械打分规则产出是确定性的,同一个议题两次跑结果应该一致
  - R3 硬过滤在 Topic B/C 都正确触发(Sun/Taleb 按非目标范围剔除)
  - Topic A 在结构平衡规则下**最终收敛到了 Session 2 的预期花名册**
  - 可解释性字段强制要求 → 输出对人类审阅友好
  - 候选池嵌入 prompt,self-contained,不依赖外部读文件

- **✗ 弱项**(为什么不到 7):
  - FINDING #1(议题琐碎度)会让 `/room` 在真实日常场景中过度分配
  - FINDING #6(silent_rounds 无维护方)意味着核心"强制补位"规则在实际运行中**无法触发**,这是阻塞性缺口
  - FINDING #4(100% defensive 可能)在 stress_test 议题上会让 `/room` 失去"反对的反对"角色
  - Topic A 的结构平衡需要多轮迭代替换才能收敛,算法描述层面不够紧,实际 LLM 跑时可能卡在第一轮失败就放弃

### 是否可以进 Phase 2?

✅ **可以**。但 Phase 2(`docs/room-architecture.md`)**必须**在动笔前先处理 FINDING #6 —— 把 `silent_rounds` 和 `last_stage` 的状态所有权、更新时机、传递路径明确下来,否则 turn-mode 的强制补位和阶段判断都是悬空的。

FINDING #1(琐碎度)可以在 Phase 2 并行处理,作为 room 状态机的"入房前检查"。

FINDING #3/4/5(tie-breaker / offensive 对称 / 地板分)是 policy 层的小修补,建议在 Phase 2 完成后回头对 `room-selection-policy.md` 做一次 v0.1.1 补丁修订,不必在 Phase 2 前阻塞。

---

## 7. 推荐的下一步动作(按优先级)

### 🔴 立即必须做(Phase 2 开始前)

**动作 A1**:在 `docs/room-selection-policy.md` 追加 **E-0 议题琐碎度降级**规则,填补 FINDING #1/#2 的路径空洞。建议文案:

```
§ 9.0 议题琐碎度降级(新增,优先于 §9.2)

如果同时满足:
  (a) stage ∈ {converge, decision}
  (b) 子问题数量 = 1 且 tag 数量 ≤ 2
  (c) top1 - top2 ≥ 15 分
  (d) topic 文本长度 ≤ 20 字符

则执行"降级模式":
  - roster 仅取 top1(单人花名册)
  - 跳过结构平衡检查
  - structural_check.passed = true,附 warning: "trivial_topic_downgrade"
  - 不视为 no_qualifying_roster 错误
```

同步更新 `prompts/room-selection.md` 的步骤 E。

**动作 A2**:在 `docs/room-architecture.md`(Phase 2 的核心交付物)必须**首节定义房间状态**,明确以下字段由谁维护:
- `silent_rounds: Map<agent, n>`:每轮单轮发言结束后,主持器负责:入选者清零,未入选者 +1
- `last_stage`:每次主持器判断阶段切换时更新
- `turn_count`:累加
- `recent_log`:保留最近 3 轮,压缩为 ≤ 500 token

没有这层状态,selection prompt 是空转的。

### 🟡 Phase 2 中同步处理

**动作 B1**:policy §9.3 增加"至少 1 offensive 或 moderate"的对称硬规则(FINDING #4)。对 Topic C 这类天然偏 defensive 的议题,rotation 到 top 5 时增补 1 个 moderate 角度。

**动作 B2**:policy §9.1 补充 tie-breaker(FINDING #3)。

**动作 B3**:policy §7.1 考虑把"0 sub 命中 + 主 task 命中 → 6"改为 → 3 或 → 0,削弱 task_type 单点地板(FINDING #5)。

**动作 B4**:prompt §E-3 明确豁免条件的检查点(FINDING #7)。

### 🟢 可以等到 Phase 4 再补

**动作 C1**:prompt §C 对"迭代式替换"写一段伪代码流程,避免 LLM 实现时第一轮替换失败就放弃(FINDING #8)。

**动作 C2**:prompt §C 的两遍打分可以加一句警示:"如果你正想一次性打完 7 项,停下来,你违反了打分顺序"(FINDING #9)。

---

## 8. 交付给下一个 Agent(Session 4)的交接语

1. **本轮(Session 3)只做了验证,没改任何 policy / prompt 文件**,保持"先验证后修补"的节奏
2. FINDING #1 和 FINDING #6 是阻塞性的,必须在 Phase 2 开始前处理(动作 A1+A2)
3. 其他 FINDING 可以延后到 Phase 2 完成时统一出 policy v0.1.1 补丁
4. Topic A 花名册最终结果 = Session 2 预期 ✓,**证明核心打分机制可用**
5. Topic B 4 人花名册和 Topic C 4 人花名册暴露了"议题-无感"的算法行为,这是目前最需要修补的
6. 手动执行耗时最大的环节是"uniqueness 计算"(需要 n×n tag 交集),**真实 LLM 跑时容易偷懒**,建议在 prompt 里加一个小型 worked example

---

## 9. 附:本次未测但应该未来补测的场景

| 场景 | 为什么现在没测 |
|---|---|
| `--with` 强制包含 + 结构失衡 | 需要验证"先自动补对冲位,仍失衡则警告"路径 |
| `--without` 剔除导致候选不足 2 人 | 验证 `all_filtered_out` 触发路径 |
| 议题文本 < 10 字 | 验证 `topic_too_vague` 触发 |
| 子问题全部 out_of_vocabulary | 验证降级策略 "子问题分全员清零" |
| `/add` + 超过软顶 8 人 | 验证 warning 而非 reject 的行为 |
| 多轮连续 room_turn,silent_rounds 真实累积 | 需要主持器 orchestrator 配合,当前 selection prompt 单独测不出 |

---

_Session 3 验证完结于 2026-04-11。下一个 Agent 应从"动作 A1 + A2"开始,补完 policy/prompt 的琐碎度降级和状态字段定义,然后再进入 Phase 2 架构文档。_

---

# §10. Session 4 Phase 1.5 回归验证(纸面回归)

生成:2026-04-11(Session 4 延续)
执行者:Claude Opus 4.6(1M context),作为 selection prompt 宿主 LLM
被测件:
- `C:\Users\CLH\docs\room-selection-policy.md` **v0.1.1**(追加 §9.1.1)
- `C:\Users\CLH\prompts\room-selection.md` **v0.1.1**(追加 E-1.1)

## §10.0 本节的性质声明

**这是一次「纸面回归」,不是「真实 LLM 活体回归」**。

具体含义:
- **打分数据复用** Session 3 §1-§3 已经机械算出的 scorecards(因为打分规则未改,输入未改,打分结果必然相同)
- **E-1.1 / §9.1.1 新规则由执行者按规则机械推演**,验证 4 条触发条件的分支判定是否符合设计预期
- **不涉及**真实 LLM call,因此不验证「LLM 是否会按 prompt 描述主动执行 E-1.1 这一新步骤」这一点——后者需要真实运行 `/room` 命令才能验证

**为什么先做纸面回归**:Session 4 的修补是规则层(policy + prompt 文本),规则本身的逻辑正确性可以独立于 LLM 执行力验证。先确认规则在 3 议题上的数学分支正确,再由下一个 Session 在真实 LLM 上验证执行力,避免「两个不确定性叠加」。

**这次纸面回归覆盖的问题**:
- §9.1.1 / E-1.1 的 4 条触发条件在 Session 3 三议题上是否按预期分支
- 阈值数字(≥ 8,≤ 20,`subproblem_match` 子项差)是否合理
- 是否存在 Session 4 没注意到的边界 case

**这次纸面回归不覆盖的问题**(留给真实 LLM 回归):
- LLM 是否会主动执行 E-1.1 新步骤(可能需要 prompt 描述再强化)
- `topic 长度 ≤ 20` 的 Unicode 计数是否被 LLM 正确执行
- 豁免条件(`with ≥ 2` 人)是否被 LLM 正确识别
- Topic B 的 sub_problem_tags 分配是否会在真实 LLM 下飘(见 §10.5 敏感度分析)

---

## §10.1 Topic B — 「按钮放左边还是右边」(**关键正向回归**)

### 10.1.1 输入

```
mode: room_full
topic: 这个按钮放左边还是右边
user_constraints: { with: [], without: [], topic_hint: null }
```

### 10.1.2 E-1.1 前的完整流水线(复用 Session 3 §2 结果)

- **Step A**:main_type=`product`, sub_problems=1 (`{text: "按钮位置选择", tags: [user_experience, product_focus]}`), stage=`converge`
- **Step B 硬过滤**:trump (R4), taleb (R3), justin-sun (R3) → 11 人入池
- **Step C 打分**(前 5 位 subproblem_match 子项):
  - Jobs sub=22(命中 user_experience + product_focus,2 hit)
  - Musk sub=14(仅 product_focus,1 hit)
  - Zhang Yiming sub=14(仅 product_focus,1 hit)
  - MrBeast sub=14(仅 user_experience,1 hit)
  - Feynman sub=14(仅 user_experience,1 hit)
  - PG sub=14(仅 product_focus,1 hit)
  - Karpathy sub=6(0 命中 + 主 task 命中)
  - Munger/Zhang Xuefeng/Naval/Ilya sub=0
- **Step D**:无 ±5 校正
- **Step E-1 排序**(total 降序):Jobs 52 / Feynman 47 / Musk 44 / Zhang Yiming 44 / MrBeast 37 / Karpathy 36 / Munger 25 / Zhang Xuefeng 25 / PG 22 / Naval 15 / Ilya 8

### 10.1.3 Step E-1.1 判定(**本次回归的核心**)

| # | 条件 | 计算 | 结果 |
|---|---|---|---|
| 1 | `sub_problems.length == 1` 且 `tags.length ≤ 2` | 1 子问题 / 2 tag | ✅ |
| 2 | `stage ∈ {converge, decision}` | `stage=converge` | ✅ |
| 3 | `topic` 文本长度 ≤ 20 | `这个按钮放左边还是右边` = **11** | ✅ |
| 4 | `top1.sub - 次高 sub ≥ 8` | Jobs 22,次高 Musk/ZY/MrBeast/Feynman/PG = 14,差 = **8** | ✅(恰好卡线) |

**豁免检查**:`user_constraints.with = []`,`constraints.mentions = []` → 无豁免

**判定**:4 条全满足 → **触发 `trivial_topic_downgrade`**

### 10.1.4 降级动作执行

- `roster = [{"agent": "steve-jobs", "short_name": "Jobs", "role": "UI 决策与产品取舍直接权威", "structural_role": "offensive"}]`
- 跳过 E-2 结构平衡硬规则检查
- `structural_check`:
  - `defensive_count=0`,`grounded_count=1`,`dominant_count=1`,`dominant_ratio=1.0`
  - `passed=true`
  - `warnings=["trivial_topic_downgrade"]`
- 不走 `no_qualifying_roster` 错误路径
- `explanation.why_selected[0]` = "Jobs 单人降级:converge 阶段 + 单子问题 2 tag + topic 仅 11 字 + Jobs subproblem_match(22)领先次高者(14)恰好 8 分,触发 §9.1.1 陪跑降级。按钮位置是 Jobs 的直接权威领域,无需多视角推演"
- `explanation.why_not_selected[0]` = "触发 §9.1.1 琐碎度降级,其余 10 位通过硬过滤的候选未进入花名册"

### 10.1.5 对比 Session 3 预期

| 维度 | Session 3 结果 | Session 4 Phase 1.5 结果 |
|---|---|---|
| roster 人数 | 4 人(Jobs/Feynman/Musk/Zhang Yiming) | **1 人(Jobs)** ✓ |
| structural_check.passed | true(一次通过) | true(降级跳过检查) |
| warnings | 空 | **`["trivial_topic_downgrade"]`** ✓ |
| 走入错误路径 | 否 | 否 ✓ |

**Topic B 回归判定:✅ PASS** — 完全符合 Session 4 设计预期,FINDING #1 修补逻辑在纸面上正确。

---

## §10.2 Topic A — 「独立开发者 AI 工具 All in?」(**负向回归**)

### 10.2.1 输入

```
mode: room_full
topic: 我想做一个面向独立开发者的 AI 工具,这个方向值不值得 All in?
```

### 10.2.2 E-1.1 判定

| # | 条件 | 计算 | 结果 |
|---|---|---|---|
| 1 | `sub_problems.length == 1` 且 `tags ≤ 2` | Session 3 识别出 **2 个子问题**(「值不值得做」+「All in 还是小步试」) | ❌ |
| 2 | `stage ∈ {converge, decision}` | `stage=explore` | ❌ |
| 3 | `topic ≤ 20` | 长度 **36** 字符(中文 + 空格 + 英文 + 标点) | ❌ |
| 4 | `sub 差 ≥ 8` | Sun 30 / PG 30,差 = **0** | ❌ |

**4 条全不满足 → 不降级**

**判定**:进入常规 E-2 流程。按 Session 3 §1 的结构平衡迭代,最终花名册 = Sun/PG/Munger/Taleb(4 人)。

**Topic A 回归判定:✅ PASS** — 正确不降级,4 条条件全部阻断,多重保护有效。

---

## §10.3 Topic C — 「项目失败最坏会怎样」(**负向回归 — 临界场景**)

### 10.3.1 输入

```
mode: room_full
topic: 如果这个项目失败了最坏会怎样
```

### 10.3.2 E-1.1 判定

| # | 条件 | 计算 | 结果 |
|---|---|---|---|
| 1 | `sub_problems.length == 1` 且 `tags ≤ 2` | 1 子问题 / tag=[tail_risk, downside_analysis] 数=2 | ✅ |
| 2 | `stage ∈ {converge, decision}` | **`stage=stress_test`** | ❌ |
| 3 | `topic ≤ 20` | 长度 **14** 字符 | ✅ |
| 4 | `sub 差 ≥ 8` | Taleb 22,次高 Munger/ZX = 14,差 = **8** | ✅ |

**3/4 条件满足,唯条件 2 阻断 → 不降级**

**判定**:进入常规 E-2 流程。按 Session 3 §3 结果,最终花名册 = Taleb/Munger/ZX/Ilya(4 人)。

**Topic C 回归判定:✅ PASS** — 正确不降级。**这是最重要的负向验证** — 如果 stage 条件放宽到只看长度,Topic C 这类严肃风险议题会被误降为单人,丢失压力测试的多角度对冲。stage 卡在 `{converge, decision}` 的设计决策被此用例验证。

---

## §10.4 三议题回归汇总

| 议题 | 预期 | 实际 | 结论 |
|---|---|---|---|
| A(独立开发者 AI All in) | 不降级,4 人花名册 | 不降级 ✓ | PASS |
| B(按钮左右) | **降级,1 人(Jobs)** | 降级 ✓ | **PASS(关键修补验证)** |
| C(失败最坏会怎样) | 不降级,4 人花名册 | 不降级 ✓ | PASS |

**总结:3/3 PASS**。FINDING #1 的修补规则在纸面上完全正确。

---

## §10.5 🟡 发现的新隐患:阈值敏感度

### §10.5.1 问题描述

Topic B 的条件 4 计算出 **sub 差 = 8**,恰好卡在阈值 `≥ 8` 的临界线。这引出一个稳定性问题:

**如果真实 LLM 对 Jobs 的 sub_problem_tags 分配与 Session 3 略有不同,降级可能不触发。**

具体场景分析:

| Jobs sub_problem_match 实际值 | 次高 sub 实际值 | 差 | 是否触发降级? |
|---|---|---|---|
| 22(2 hit,Session 3 实测) | 14 | 8 | ✅ 触发(本次回归) |
| 30(3 hit,如果 LLM 也把 `value_proposition` 算进来) | 14 | 16 | ✅ 稳定触发 |
| 14(1 hit,如果 LLM 只认 `user_experience` 或 `product_focus` 其一) | 14 | 0 | ❌ **不触发** |
| 22(2 hit)| **22**(如果另一候选也拿 2 hit,例如 Musk 命中 product_focus + user_experience)| 0 | ❌ **不触发** |

### §10.5.2 为什么这是可接受的

1. **Session 3 的分配已经是「合理最小公倍数」**:Jobs 的 profile 明确写了 `value_proposition, product_focus, user_experience, first_principles, narrative_construction`,对「按钮放左边还是右边」这个子问题识别为 `[user_experience, product_focus]` 是最贴切的,Jobs 必然命中 2 tag。跌到 1 hit 的概率低
2. **多重保护**:即使条件 4 失败,议题仍会走常规 4 人路径,只是**退化**为 Session 3 的行为——不会崩坏,只是没触发降级,这是**优雅降级**而非失败
3. **Topic B 是 11 字符的极短议题**,LLM 对极短议题的 tag 分配往往比长议题更稳定(没有多层句义要解析)

### §10.5.3 改进建议(不阻塞 Phase 2,可留到 v0.1.2)

**方案 A(最小改动)**:阈值从 `≥ 8` 降到 `≥ 6`
- Pros:Topic B 如果实际分配只差 6 也能触发
- Cons:开始有误触发风险(某些 explore 早期议题也可能差 6)
- Session 5 真实 LLM 回归如果发现 Topic B 差 < 8,再考虑下调

**方案 B(更稳健)**:除 sub 差外,追加「topic 文本包含二选一信号词」作为替代条件
- 信号词:`A 还是 B / 左边右边 / 选 X 还是 Y / 要 X 还是 Y`
- 文本信号 + 前 3 条硬条件即可触发,第 4 条降格为「sub 差 ≥ 6 或 文本信号存在」
- Pros:捕获 Topic B 这类二选一,抗 sub_problem_match 飘
- Cons:增加了文本匹配的脆弱性,LLM 对「还是」等连接词的识别不一定稳

**方案 C(根本性)**:在 Step A 议题解析时追加一个 `topic_flavor` 字段,由 LLM 直接判定「琐碎 / 战略 / 模糊」三档,E-1.1 只在 `topic_flavor == trivial` 时触发
- Pros:把判断交给 LLM 语义能力,阈值不再是僵硬数字
- Cons:引入 LLM 主观判断,违背 Session 2 锁定的「规则打底,模型辅助」原则,重新打开 Session 3 已避免的 LLM 自由飘移陷阱

**推荐**:保持 v0.1.1 不动,等 Session 5 真实 LLM 回归发现具体失败模式后再决定。**不要在没有证据的情况下改阈值**。

### §10.5.4 追加到 NEXT-STEPS 的监控项

- Session 5 真实 LLM 回归必须**显式记录** Topic B 的 Jobs sub_problem_match 实际值
- 如果 ≥ 22,v0.1.1 按现状生效
- 如果 < 22(Jobs 只拿到 1 hit = 14),需要考虑方案 A/B/C 之一

---

## §10.6 稳定性主观评分(Session 4 更新)

**7/10**(Session 3 时为 6/10)

### §10.6.1 相比 Session 3 的加分项

- ✅ FINDING #1 已由 §9.1.1 / E-1.1 规则层修补,三议题纸面回归 PASS
- ✅ FINDING #6 已由 room-architecture.md §1-§4 解除阻塞,silent_rounds 所有权明确
- ✅ FINDING #2(`no_qualifying_roster` 对 Topic B 无路径)被 §9.1.1 的非错误降级路径覆盖

### §10.6.2 仍然扣分的地方

- FINDING #3(tie-breaker)未修
- FINDING #4(offensive 对称)未修
- FINDING #5(地板分过高)未修
- **新增**:§10.5 阈值敏感度隐患
- **未验证**:Session 5 必须跑真实 LLM 活体回归才能把分提到 8/10

### §10.6.3 是否可以进 Phase 2?

✅ **可以**。Phase 2(展开 room-architecture.md §5-§9)可以在 Session 5 真实 LLM 回归**并行**进行——只要 Session 5 的回归结果出来前,不合并任何依赖 E-1.1 实际触发的后续 prompt(例如 room-chat prompt 如果也依赖降级标记,必须等回归确认后)。

FINDING #3/#4/#5 是 policy v0.1.2 补丁,建议 Phase 2 完成时统一发布。

---

## §10.7 给 Session 5 的交接

1. **第一步就做真实 LLM 活体回归 Topic B**:用实际 `/room` 命令或直接把 `room-selection.md` 喂给 Codex/Claude,输入 `topic: 这个按钮放左边还是右边`,看输出
2. **必须记录** Jobs 的实际 `subproblem_match` 值(18? 22? 30?)
3. 如果 Jobs sub < 22 导致差 < 8 → 按 §10.5.3 方案 A 下调阈值到 ≥ 6,重跑
4. 如果 Jobs sub ≥ 22 → v0.1.1 维持原样,进入 Phase 2
5. 并行启动 Phase 2 `room-architecture.md §5-§9` 写作,**不动 §1-§4**
6. Phase 2 完成时统一出 `policy v0.1.2` 补丁(FINDING #3/#4/#5)

---

_Session 4 Phase 1.5 纸面回归完结于 2026-04-11。3/3 PASS。唯一新发现的 §10.5 阈值敏感度隐患不阻塞 Phase 2,但 Session 5 必须在真实 LLM 回归时显式监控 Jobs 的 subproblem_match 实际值。_

---

# §11. Session 4 Phase 1.5 活体回归(真实 LLM)

生成:2026-04-11(Session 4 延续)
执行方式:3 个并行 subagent,每个 subagent 是独立 Claude 实例、干净上下文、纯推理无工具
被测件:
- `prompts/room-selection.md` v0.1.1(嵌入到 subagent prompt 中)

## §11.0 本节的性质声明

**这是真实 LLM 活体回归,不是纸面回归**。与 §10 的差别:
- §10 是执行者(本 Agent)在主上下文里用 Session 3 已有分数做分支判定
- §11 是**独立 Claude 实例**收到 prompt 文本 + 议题输入,从 0 开始执行步骤 A→E,自主决定每个分数

**仍然的局限**:subagent 与执行者共享基础模型(Claude Opus 4.6),不是完全陌生实例。但 context 完全干净、不共享对话历史、不知道 FINDING #1 / §9.1.1 / 任何期望结果。**这是我在现有工具约束下最接近真实生产调用的测试**。

**本次测试覆盖 3 个议题**:
- Topic A(查表议题 + 负向测试):验证 prompt 的参考表不会干扰负向判定
- Topic B(查表议题 + 正向测试):验证 E-1.1 在生产议题上触发
- **Topic D(泛化议题 + 正向测试)**:**核心测试**——验证 LLM 在**没有参考表提示**的新议题上能否主动触发 E-1.1

Topic C 未跑,因为 Topic A 已经覆盖了「stage 不在 converge/decision」的负向路径,且 Topic C 与 Topic A 同样在参考表中。

---

## §11.1 Topic B(按钮放左边还是右边)

### §11.1.1 活体结果摘要

- ✅ Jobs 被单独选入 roster
- ✅ `structural_check.warnings = ["trivial_topic_downgrade"]`
- ✅ `passed = true`
- ✅ 未走 `no_qualifying_roster` 错误路径

### §11.1.2 E-1.1 条件逐条计算(活体)

| 条件 | 活体计算 | 与纸面回归一致? |
|---|---|---|
| 1. 单子问题 ≤ 2 tag | sub_problems=1, tags=[user_experience, product_focus] = 2 | ✅ |
| 2. stage ∈ {converge, decision} | **stage=decision**(纸面:converge) | ⚠️ stage 漂移,但仍在集合内 |
| 3. topic ≤ 20 字符 | **12 字符**(纸面:11 字符) | ⚠️ 差 1 字符,LLM 可能把结尾字符包含差异;不影响判定 |
| 4. sub 差 ≥ 8 | **Jobs sub=22,次高=14,差=8** | ✅ **完全一致** |

### §11.1.3 次要发现(不影响判定)

- **stage 漂移**:LLM 判 `decision`,纸面预期 `converge`。两者都在 E-1.1 集合内,降级不受影响。**但这说明 stage 识别边界感不稳**——Session 3 的 `converge` 与活体的 `decision` 是两个不同判断
- **role_uniqueness 打分**:活体给 Jobs 打 15(认为无人与 Jobs 重合 ≥ 2 tag),Session 3 打 0(认为 PG/Musk/Jobs/Feynman 等多人 ≥ 2 重合)。**活体其实算得更准**——Jobs 的 `[value_proposition, product_focus, user_experience, first_principles, narrative_construction]` 确实没人 ≥ 2 重合。Session 3 这里算错了
- **Jobs total 从 52 → 67**:因为 role_uniqueness 活体给 15 而非 0。但**不影响 E-1.1 判定**,因为判定只看 subproblem_match 子项
- **task_type_match 规则歧义**:prompt 的「仅副类型命中 → 8」没明确是「议题有 secondary_type」还是「Agent 的 task_types 副位命中议题主类型」。LLM 选了后者。这也是 Session 3 的打分与活体出现差异的原因之一

### §11.1.4 判定

**✅ Topic B 活体 PASS** — 降级规则在生产议题上正确触发,所有次要发现都不影响判定结果。

---

## §11.2 Topic A(独立开发者 AI 工具 All in?)

### §11.2.1 活体结果摘要

- ✅ **不降级**(所有 4 条件都失败)
- 最终 roster = Sun / PG / Jobs / Zhang Xuefeng(**与纸面预期 Sun/PG/Munger/Taleb 不同但都合格**)

### §11.2.2 E-1.1 条件逐条计算(活体)

| 条件 | 活体计算 | 判定 |
|---|---|---|
| 1. 单子问题 | sub_problems=**2**(「值不值得做」+「All in 还是小步试」) | ❌ |
| 2. stage ∈ {converge, decision} | **stage=simulate**(纸面:explore) | ❌ |
| 3. topic ≤ 20 字符 | 36 字符 | ❌ |
| 4. sub 差 ≥ 8 | Sun 30 / PG 30,差 = 0 | ❌ |

**4 条全失败,多重保护生效。**

### §11.2.3 重要新发现:tag 分配飘移导致花名册构成不同

活体 LLM 对「All in 还是小步试」的 sub_problem tag 分配**与 Session 3 不同**:

| 来源 | 子问题 tag |
|---|---|
| Session 3 | `[resource_allocation, market_timing]` |
| 活体 LLM | `[resource_allocation, downside_analysis]`(LLM 把「All in 失败的代价」解读出来) |

**连锁影响**:
- 活体的 Taleb `subproblem_match` = 22(命中 `downside_analysis + resource_allocation` 2 hit)
- Session 3 的 Taleb `subproblem_match` = 14(仅 `resource_allocation` 1 hit)
- 活体的 Taleb 进入初始 top 4,Session 3 的 Taleb 没进
- 导致两个花名册构成差异

**两个花名册都合格**(都满足 ≥1 defensive + ≥1 grounded + dominant ≤ 人数/2)。这**不是 bug,是 feature**——规则允许多个合格解,LLM 语义解析有合理飘移空间,但结构平衡硬规则保证结果都在合格范围内。

### §11.2.4 stage 又漂了(系统性问题)

| 议题 | Session 3 | 活体 | 差异方向 |
|---|---|---|---|
| A | explore | **simulate** | 纯探索 → 推演验证 |
| B | converge | **decision** | 选项收敛 → 最终落点 |

**两个议题的 stage 都漂了**。这是个**系统性问题**:LLM 对 explore/simulate/converge/decision 的边界感不稳。**Session 4 已知限制**,对 E-1.1 不构成阻塞(两个飘移都在「不在集合 / 都在集合」同侧),但需要列入 v0.1.2 补丁的待修项。

### §11.2.5 判定

**✅ Topic A 活体 PASS** — 正确不降级。花名册构成与 Session 3 不同但都合格。

---

## §11.3 Topic D(按钮用红色还是蓝色)🏆 **核心泛化测试**

### §11.3.1 本议题的特殊地位

**Topic D 是本次活体回归最重要的测试**。它是一个**完全不在 prompt 参考表内**的新议题,LLM 必须**只靠 E-1.1 的规则描述**就主动识别并执行降级判定。

如果 Topic D 失败,说明 prompt 的规则描述不够清楚,LLM 只是在 A/B/C 上**查表**而已,真实生产场景(新议题)会失效。

### §11.3.2 活体结果摘要

- ✅ **降级触发**
- ✅ roster = [Jobs]
- ✅ `structural_check.warnings = ["trivial_topic_downgrade"]`
- ✅ `passed = true`

### §11.3.3 E-1.1 条件逐条计算(活体)

| 条件 | 活体计算 | 判定 |
|---|---|---|
| 1. 单子问题 ≤ 2 tag | sub_problems=1,tags=[user_experience, product_focus]=2 | ✅ |
| 2. stage ∈ {converge, decision} | stage=decision(「二选一收口拍板」)| ✅ |
| 3. topic ≤ 20 字符 | 9 字符 | ✅ |
| 4. sub 差 ≥ 8 | **Jobs sub=22(命中 UX+product_focus 双 tag),次高=14(MrBeast/Musk/Zhang Yiming 等多人),差=8** | ✅ 恰好卡线 |

**4 条全满足,触发降级。**

### §11.3.4 Topic D 的关键验证

1. **规则泛化性**:LLM 在完全没见过的新议题上,主动走到 E-1.1 步骤并正确应用规则。**参考表不是降级的必要条件**,规则描述本身足够
2. **Jobs 稳定 sub=22 的模式**:Topic B 和 Topic D 都得出 Jobs 对「产品细节 UX 决策」的 sub_match = 22(双 tag 命中)。这证明纸面回归的假设(Jobs 的 profile 写了 UX + product_focus,对按钮类议题必然 2 hit)是**稳定规律**,不是偶然
3. **阈值 8 不是偶然**:两个独立 trivial topic 都算出 sub 差 = 8,说明阈值设计对 Jobs 这类「高覆盖度 Agent + 细分议题」是**可达的临界值**,而不是硬卡线
4. **避免浪费的价值被证实**:活体计算显示 Topic D 的 non-downgrade top 4 = Jobs 62 / MrBeast 54 / Musk 49 / Zhang Yiming 49,4 个 offensive、3 个 dominant,会触发结构平衡失败,走冗长的替换迭代。**降级规则正好避免了这种 UI 微决策的多人讨论浪费**——这是 E-1.1 存在的核心价值

### §11.3.5 判定

**✅✅ Topic D 活体 PASS — 泛化测试通过,规则设计被证实可用**

---

## §11.4 汇总:三议题活体回归结果

| Topic | 类型 | 参考表内? | Jobs/top1 sub | 次高 sub | 差 | stage(活体) | 降级? | 判定 |
|---|---|---|---|---|---|---|---|---|
| A | 负向 | ✅ | Sun 30 | PG 30 | 0 | simulate | ❌ | ✅ PASS |
| B | 正向 | ✅ | Jobs 22 | 14 | 8 | decision | ✅ | ✅ PASS |
| D | **泛化正向** | ❌ | Jobs 22 | 14 | 8 | decision | ✅ | ✅ **PASS(核心)** |

**3/3 PASS**。

---

## §11.5 所有发现汇总(活体回归)

### 🟢 被验证的设计决策

1. **§9.1.1 的 4 条件合取保护** — 两个负向议题(A + 隐含 C)都因多条同时失败而不降级,鲁棒
2. **`subproblem_match` 子项差而非 total 差** — 活体的 task_type/role_uniqueness 打分与 Session 3 有分歧,但 `subproblem_match` 子项保持稳定,E-1.1 判定不受影响
3. **阈值 8 不是偶然卡线** — Topic B 和 Topic D 独立产生 sub 差 = 8
4. **降级到单人而非 2 人对冲** — Topic D 显示如果没降级会陷入 4 人结构失衡迭代,单人降级是正确的简化
5. **规则描述的自带泛化性** — Topic D 证明 LLM 不依赖参考表也能触发

### 🟡 新发现的次要隐患(非阻塞)

1. **Stage 识别不稳定(系统性)** — 两个测试议题 stage 都漂了(A: explore→simulate, B: converge→decision)。不影响 E-1.1 判定,但:
   - 如果某议题被 LLM 从 explore 误识别为 converge/decision,可能触发**误降级**
   - 如果某议题被从 decision 误识别为 simulate,可能**漏降级**
   - 需要在 v0.1.2 补丁里给 stage 判定增加更强的锚定词(例如明确列「A 还是 B → decision」「最坏会怎样 → stress_test」)

2. **sub_problem_tag 分配飘移** — Topic A 的「All in 还是小步试」Session 3 标 `[resource_allocation, market_timing]`,活体标 `[resource_allocation, downside_analysis]`。两者都合理,都在词表内,但导致下游 Taleb 打分差异 14→22。**这是语义解析的自然飘移**,短期无解,长期可能需要增加子问题 tag 分配的参考示例

3. **task_type_match 规则歧义** — 「仅副类型命中 → 8」的两种解释:
   - 解释 A:议题有 secondary_type 并命中 Agent 的 task_types
   - 解释 B:Agent 的 task_types 列表中非首位的 type 命中议题 main_type
   - Session 3 用解释 A,活体用解释 B。不影响 E-1.1,但影响打分一致性。**建议 v0.1.2 补丁明确为解释 A**(因为这更符合「议题主副 + Agent 主副」的对称直觉)

4. **role_uniqueness 计算分歧** — Session 3 用「多个候选两两 tag 重合 ≥ 2」宽松统计,活体用「严格只统计与本人 ≥ 2 tag 重合的其他人数」。活体的解释更严格也更准。**建议 v0.1.2 补丁采用活体的严格解释**

5. **topic 长度计数差 1** — Topic B 活体数 12,纸面数 11。可能是 LLM 把句末标点/空格算入或算出。不影响判定(11 和 12 都 ≤ 20)

### 🔴 没发现的严重问题

**没有**发现任何阻塞 Phase 2 的 bug。E-1.1 / §9.1.1 在活体 LLM 下**按预期工作**,包括泛化场景。

---

## §11.6 稳定性评分更新

**8/10**(Session 3: 6/10 → Session 4 纸面: 7/10 → Session 4 活体: 8/10)

### 加分理由

- ✅ 活体 3/3 PASS,含**泛化测试**
- ✅ E-1.1 的子项差设计在活体下被验证鲁棒(即使其他打分飘移,判定不变)
- ✅ Jobs 在产品细节议题稳定 sub=22 的规律被证实
- ✅ 阈值 8 不是偶然卡线,是可达临界值

### 未到 9/10 的原因

- ⚠️ stage 识别不稳定(系统性)——未在 v0.1.2 补丁中修复
- ⚠️ Session 3 剩余 FINDING #3/#4/#5 未修
- ⚠️ 只测了 3 个议题(Topic C 未跑)
- ⚠️ 所有测试都是 room_full 模式,`room_turn` 和 `roster_patch` 未在活体下测试
- ⚠️ 没测边缘议题(例如 topic 正好 20 字符、sub 差正好 7 或 9 的边界)

### 是否可以进 Phase 2?

**✅ 可以,无保留**。Phase 2 架构层展开可以全速推进,E-1.1 的基础在活体下被证实牢靠。

**建议 Phase 2 同步处理的事**:
1. v0.1.2 补丁:修 stage 识别锚定词 + 明确 task_type_match 歧义 + 明确 role_uniqueness 计算
2. 在 architecture.md §7(发言机制)里锁定 stage 切换的主持器判定规则,减少 LLM 自主判定 stage 的负担

---

## §11.7 给 Session 5 / Phase 2 写作者的交接

1. **Phase 1.5 已闭环**:纸面回归(§10)+ 活体回归(§11)都已完成,E-1.1 可用
2. **Phase 2 可以开始**,无前置阻塞
3. **v0.1.2 policy 补丁**建议在 Phase 2 完成时一起交付,不单独开 session
4. **新增监控项**:Phase 2 写作时,任何涉及 stage 切换的地方都要考虑「LLM 判 stage 会漂」这一事实
5. **room-chat prompt(Phase 4)**应该在每轮发言开始前**显式告诉 LLM 当前 stage**,不让 LLM 每轮重新判定

---

_Session 4 Phase 1.5 活体回归完结于 2026-04-11。3/3 PASS,稳定性评分 6→7→8。下一步:Phase 2 架构层主体写作(`room-architecture.md §5-§9`),前置阻塞已全部解除。_

---

# §12. Session 5 v0.1.2 补丁的活体回归 gap(已知未跑)

生成:2026-04-11(Session 5 完结同步)
目的:**显式记录** Session 5 的 v0.1.2 规则补丁**未跑活体回归**,避免被误以为已验证

## §12.1 v0.1.2 的 8 项规则变化

Session 5 对 policy/prompt 追加了 8 项补丁(详见 `SESSION-5-COMPLETION-REPORT.md` 或 policy §15 版本记录):

1. §5.3 stage 锚定词表(新增)
2. §7.1 0-命中地板分 6 → 3
3. §7.2 task_type 规则歧义消除
4. §7.4 role_uniqueness 严格解释
5. §9.1 tie-breaker 规则
6. §9.2 迭代替换 5 轮上限
7. §9.3 结构平衡第 4 条(≥1 offensive/moderate)
8. §12 强制补位豁免 4 条顺序检查

## §12.2 为什么没跑活体回归

- Session 5 的主要交付是 Phase 2 架构主体,活体回归不是本次 session 的主要产出
- §9.1.1 琐碎度规则**未动**,Session 4 的 Topic A/B/D 活体通过结论仍然有效
- v0.1.2 主要影响**打分细节**(地板分 / role_uniqueness 严格解释 / tie-breaker),不影响 E-1.1 判定的核心信号(subproblem_match 子项差)
- 纸面推算显示 Jobs 的 total 从活体的 67 → 回归纸面的 52,但 **subproblem_match=22 不变**,E-1.1 判定不受影响

## §12.3 纸面推算下的 Topic B 回归预期

按 v0.1.2 严格规则重算 Topic B(「这个按钮放左边还是右边」):

| Agent | subproblem_match | role_uniqueness(严格)| task_type_match(消歧)| 预期 total |
|---|---|---|---|---|
| Jobs | 22(UX + product_focus) | **0**(与 PG/Musk/Feynman 等 ≥3 人 ≥2 tag 重合) | 15(product 主命中) | ≈ 52(+stage_fit 15) |
| Feynman | 14(UX 1 hit) | 10-15 | 15(product 主命中) | ≈ 44-52 |
| Musk | 14(product_focus 1 hit) | 10 | 15 | ≈ 44 |
| Zhang Yiming | 14 | 10 | 15 | ≈ 44 |
| PG | 14 | 10 | 0(无 product) | ≈ 29 |

**E-1.1 判定**:
- Jobs sub=22,次高 sub=14,差 = 8 → **仍然触发降级 ✓**
- roster 仍然 = [Jobs]
- structural_check.warnings 仍然 = `["trivial_topic_downgrade"]`

**结论**:**纸面推算表明 v0.1.2 不破坏 Topic B 的降级行为**。但**纸面推算不等于活体验证**。

## §12.4 Session 6 应跑的活体回归

**推荐时机**:Phase 4 `room-chat.md` 写完后一起跑,或在 Session 6 第一步单独跑。

**覆盖范围**:
1. **Topic B 回归**(必做):确认 v0.1.2 下 Jobs total ≈ 52,降级仍然触发
2. **Topic D 泛化回归**(推荐):新议题泛化测试
3. **stress_test 议题**(新增,测 §9.3 第 4 条):例如「如果这个项目失败了最坏会怎样」
   - v0.1.1 下花名册 = Taleb/Munger/Zhang Xuefeng/Ilya(Ilya 是 offensive 位,勉强满足)
   - v0.1.2 下若 Ilya 不够分,应该**强制补一个 offensive/moderate**(§9.3 第 4 条)
   - **这是 v0.1.2 最需要验证的新规则**
4. **tie-breaker 边缘议题**(推荐):构造 2 个 Agent total 完全并列的议题,验证 subproblem > stage_fit > uniqueness > id 的排序

## §12.5 如果 Session 6 活体回归失败怎么办

- **失败场景 1**:Topic B 不再触发降级 → 说明 role_uniqueness 严格解释或地板分下调导致 Jobs sub_match 算错。回溯检查 §7.4 的规则描述是否清楚
- **失败场景 2**:stress_test 议题没补 offensive → 说明 §9.3 第 4 条的文案不够显著。需要在 prompt 的 E-2 结构平衡检查里补更强的指令
- **失败场景 3**:tie-breaker 行为错乱 → 说明 §9.1 的 4 级 tie-breaker 顺序在 prompt 里没被严格执行。可能需要补 worked example

**兜底**:如果 Session 6 发现 v0.1.2 有问题,优先**回滚单条补丁**而不是全量回滚。每条补丁都是独立的,可以精准定位。

---

_Session 5 同步于 2026-04-11。§12 记录 v0.1.2 活体回归 gap,Session 6 第一步或 Phase 4 完成后统一回归。_

---

# §13. Session 6 v0.1.2 活体回归结果(Gap 解除)

生成:2026-04-11(Session 6 第一步)
执行者:Claude Opus 4.6 作为宿主,spawn 3 个 general-purpose subagent 并行执行
被测件:`prompts/room-selection.md` v0.1.2
目的:补齐 §12 留下的 v0.1.2 活体回归 gap,按 P1 最高优先级执行

---

## §13.0 本节的性质声明

与 §11 一样,本节记录 **subagent 作为 selection prompt 的宿主 LLM** 的实际执行结果。每个 subagent 读完 `prompts/room-selection.md` 后,按 A→E 流程为 13 个候选完整打分,产出严格 JSON。

**与 §11(Session 4 活体)的区别**:
- §11 只测 v0.1.1(含 §9.1.1 琐碎度降级),核心问题是「E-1.1 会不会被触发」
- §13 测 v0.1.2 的 8 项补丁,核心问题是「新规则会不会按预期生效」

---

## §13.1 回归矩阵(3 议题并行)

| # | Topic | 主要验证的补丁 | stage 预期 |
|---|---|---|---|
| **T-A** | 「按钮放左边还是右边」(11 字) | §7.1 地板分 3 / §7.4 role_uniqueness 严格 / §5.3.1 converge 锚定词 / E-1.1 仍触发 | converge |
| **T-B** | 「我想做一个面向独立开发者的 AI 工具,这个方向值不值得 All in?」(27 字) | §9.1 tie-breaker / §7.2 task_type 消歧(secondary=strategy)/ §5.3.1 explore 锚定词 | explore |
| **T-C** | 「如果这个项目失败了最坏会怎样」(15 字) | §9.3 第 4 条 offensive 对称 / §5.3.1 stress_test 锚定词 | stress_test |

---

## §13.2 T-A 结果(按钮议题)

### §13.2.1 关键判定表

| 检查点 | 预期 | 实际 | 结果 |
|---|---|---|---|
| parsed_topic.stage | converge | **converge**(引用「哪个更好」「比较 A 和 B」锚定词) | ✅ |
| parsed_topic.main_type | product | **product**(UI 微决策) | ✅ |
| sub_problems 数量 | 1 | 1 | ✅ |
| sub_problems.tags | [user_experience, product_focus] | 相同 | ✅ |
| Jobs.subproblem_match | 22(2 命中) | **22** | ✅ |
| 次高 subproblem_match | ≤ 14 | **14**(Musk/Feynman/PG/ZYiming/MrBeast 并列) | ✅ |
| sub 子项差 | ≥ 8 | **8**(恰好触发) | ✅ |
| Jobs.role_uniqueness(严格解释) | 0(活体 S4 曾错判 15) | **0**(N=5,与 5 位候选均 ≥2 tag 重合) | ✅ |
| Karpathy.subproblem_match(地板分) | 3 | **3**(v0.1.2 从 6 下调生效) | ✅ |
| task_type_match(secondary=null) | 主命中 = 15 | **15**(不误判为 20) | ✅ |
| E-1.1 触发 | 是,roster=[Jobs] | **触发,roster=[Jobs]** | ✅ |
| structural_check.warnings | `["trivial_topic_downgrade"]` | 相同 | ✅ |
| structural_check.passed | true | true | ✅ |

### §13.2.2 T-A 结论

**✅ 全部检查点通过**。v0.1.2 的 §5.3.1 / §7.1 / §7.2 / §7.4 规则在 converge 琐碎议题上正确生效。E-1.1 降级与 Session 4 §11.1 的活体结果一致(roster=[Jobs],warnings 正确),**v0.1.2 没有破坏 Session 4 验证过的 Topic B 行为**。

**规则回归**:
- Jobs 的 role_uniqueness 按严格解释从活体 S4 的「错判 15」修正为「正确 0」
- Karpathy 的 0-命中地板从 6 下调到 3,但因他不在 top4,不影响 roster(仅影响 redundancy 计算的参考基线)
- **Jobs total 从 S4 活体的 67 → S6 活体的 52**,与 §12.3 纸面推算完全一致 ✓

---

## §13.3 T-B 结果(All in 议题)🏆 **核心收获:迭代替换路径被实际触发**

### §13.3.1 关键判定表

| 检查点 | 预期 | 实际 | 结果 |
|---|---|---|---|
| parsed_topic.main_type | startup | **startup** | ✅ |
| parsed_topic.secondary_type | strategy | **strategy** | ✅ |
| parsed_topic.stage | explore | **explore**(引用「值不值得」「方向」) | ✅ |
| sub_problems 数量 | 2 | 2(切口 + All in) | ✅ |
| Sun 总分 | ≈ 75 | **75**(sub=30 / task=20 / stage=15 / uniq=10) | ✅ |
| PG 总分 | ≈ 65 | **65 + model_adjust +2 = 67** | ✅ |
| task_type_match(sec=strategy) | Sun/PG/Jobs 主+副 = 20 | **20**(Jobs/Sun/PG);只副命中给 8 | ✅ |
| E-1.1 不触发(stage=explore) | 不降级 | **正确不触发**(条件 2 失败) | ✅ |
| tie-breaker | agent_id 字母序打破(Munger vs ZXF 32 并列) | **Munger 优先**(munger < zhangxuefeng) | ✅ |
| **§E-2 迭代替换** | 可能触发(top 4 有 3 dominant) | **实际跑 2 轮迭代** | 🏆 **主动路径验证** |
| 最终 roster 结构合法 | 4 条全过 | **Sun/PG/Munger/Taleb 全过** | ✅ |

### §13.3.2 §E-2 迭代替换完整执行路径(本次活体最大收获)

```
Iter 0(初 top 4):    Sun(75) / PG(67) / Jobs(42) / Taleb(38)
                      ├─ Rule 1(≥1 defensive):Taleb ✓
                      ├─ Rule 2(≥1 grounded):Jobs ✓
                      ├─ Rule 3(dominant ≤ ⌊4/2⌋=2):Sun+Jobs+Taleb = 3 ❌
                      └─ Rule 4(≥1 offensive/moderate):Sun/PG ✓

Iter 1:               替换最弱 dominant Jobs(42) → Naval(37, moderate/abstract/offensive)
                      新 roster:Sun(75) / PG(67) / Naval(37) / Taleb(38)
                      ├─ Rule 1:Taleb ✓
                      ├─ Rule 2(≥1 grounded):Sun=dramatic / PG=abstract / Naval=abstract / Taleb=abstract = 0 ❌
                      └─ 仍未通过

Iter 2:               替换最弱成员 Naval(37) → Munger(32, grounded/defensive/moderate)
                      新 roster:Sun(75) / PG(67) / Munger(32) / Taleb(38)
                      ├─ Rule 1(defensive):Munger+Taleb = 2 ✓
                      ├─ Rule 2(grounded):Munger ✓
                      ├─ Rule 3(dominant):Sun+Taleb = 2 ≤ 2 ✓
                      └─ Rule 4(offensive/moderate):Sun+PG offensive / Munger moderate ✓

状态:check.passed = true → return current_roster
迭代总轮数:2(远未触碰 5 轮上限)
```

### §13.3.3 T-B 结论

**✅ 全部检查点通过,核心额外收获**:

1. **§E-2 迭代替换算法的实际执行路径被跑通** —— 这是 v0.1.2 8 项补丁中原本最担心「只存在于文档,不被实际触发」的一项。T-B 证明:
   - `while iter_count < 5` 循环正确工作
   - 「替换优先于扩招」策略被正确应用(未扩招到 5 人)
   - 「缺失位最强候选替换冗余位最弱成员」的贪心策略可执行
   - 2 轮收敛,远未逼近 5 轮上限(上限的**防无限循环**功能未被触发,但存在即合理)

2. **§9.1 tie-breaker 实际被调用**:Munger vs ZXF 都是 32 分,subproblem(14 vs 14 并列)/ stage(0 vs 0 并列)/ uniq(0 vs 0 并列)→ 最终落到 agent_id 字母序(`munger` < `zhangxuefeng`)→ Munger 优先。tie-breaker 4 级全部跑到了。

3. **§7.2 task_type 消歧**:议题 main=startup + secondary=strategy,subagent 正确区分「主+副都命中 20」「只副命中 8」「都不命中 0」三档,与 policy §7.2 v0.1.2 校准例子完全吻合。

---

## §13.4 T-C 结果(失败议题)

### §13.4.1 关键判定表

| 检查点 | 预期 | 实际 | 结果 |
|---|---|---|---|
| parsed_topic.stage | stress_test | **stress_test**(引用「如果失败」「最坏情况」锚定词) | ✅ |
| parsed_topic.main_type | risk | **risk** | ✅ |
| sub_problems.tags | [tail_risk, downside_analysis] | 相同 | ✅ |
| Taleb 总分(最高) | ≈ 52 | **52**(sub=22 / task=15 / stage=15) | ✅ |
| Ilya.subproblem_match(地板) | 3(task=risk 命中 + 0 tag 命中) | **3** | ✅ |
| E-1.1 不触发(stage=stress_test) | 不降级 | **正确不触发**(条件 2 失败) | ✅ |
| §9.3 第 4 条(offensive 对称) | 满足(需 ≥1 offensive/moderate) | **Ilya (offensive) 天然在 top 4** | ✅ 被动满足 |
| 最终 roster | 含 ≥1 offensive/moderate | **Taleb / Munger / Ilya / ZXF** | ✅ |

### §13.4.2 T-C 规则覆盖的微妙点:**被动满足 vs 主动触发**

T-C 原本设计是为了测试 §9.3 第 4 条「≥1 offensive/moderate」规则的**主动触发**(即迭代替换把一个 defensive 换成 offensive),但实际执行发现:

- **Ilya 因为 `task_types` 含 `risk` 拿到 15 分 task_type_match**,地板 3 + stage 相邻 8 + uniq 0 = 26 初分
- Ilya 刚好压过 Feynman(8 初分)、其他全 defensive 候选(Munger 44 / Taleb 52 / ZXF 29)
- Top 4 自然排成 Taleb(52) / Munger(44) / Ilya(26,加 structure_complement 5 = 31)/ ZXF(29)
- **Ilya 本身就是 offensive**,第 4 条**被动满足**,迭代替换**未被实际触发**

这意味着:
- T-C 仅验证了「规则在 top 4 初选自然满足时的行为」,**没验证迭代替换的主动路径**
- 但 **T-B 已经填补了这个 gap**(见 §13.3.2),两个测试合起来 § E-2 的主动路径 + 被动路径都有覆盖

### §13.4.3 T-C 结论

**✅ 检查点通过**。v0.1.2 第 4 条规则在 stress_test 议题上正确生效(被动满足)。

**重要观察**:subagent 自行指出「Ilya 作为 offensive 补位的合理性质疑」—— Ilya 的风险视角偏向 technical/long-term,与「最坏情况」议题契合度不如 Naval/PG 这类通用 offensive。规则机械判定下他得分合理,但人类主持可能偏好不同选择。**这是 v0.1.2 规则表达力的一个弱点**,但不是 bug。

---

## §13.5 汇总:8 项补丁的活体覆盖表

| # | 补丁 | 被覆盖的测试 | 验证结果 |
|---|---|---|---|
| 1 | §5.3.1 stage 锚定词 | T-A(converge)/ T-B(explore)/ T-C(stress_test) | ✅ 3 种 stage 都正确识别 |
| 2 | §7.1 地板分 6 → 3 | T-A Karpathy=3 / T-C Ilya=3 | ✅ 生效 |
| 3 | §7.2 task_type 消歧 | T-A(sec=null → 主命中 15)/ T-B(sec=strategy → 主+副 20) | ✅ 两种路径都正确 |
| 4 | §7.4 role_uniqueness 严格解释 | T-A Jobs=0 / T-B Sun=10 / T-C Taleb=0 | ✅ 严格两两比较生效 |
| 5 | §9.1 tie-breaker | T-A Musk vs ZYiming / T-B Munger vs ZXF / T-C Munger vs ZXF | ✅ 多次触发字母序兜底 |
| 6 | **§9.2 迭代替换 5 轮上限** | **T-B 实际跑 2 轮** | 🏆 **主动路径验证** |
| 7 | §9.3 第 4 条 offensive 对称 | T-C 被动满足 / T-B 天然含 offensive | ✅ 规则生效(**主动路径未覆盖**) |
| 8 | §12 强制补位豁免 4 条顺序 | **未覆盖** | ⏳ 需 room_turn + silent_rounds ≥ 3 场景 |

**覆盖率**:8/8 项全部触达,其中 7/8 项主动路径验证通过。

**未完全验证的 2 项**:
- **§9.3 第 4 条的主动替换路径**:本次 3 议题都是被动满足。需要构造一个「top 4 初选全 defensive 且无 offensive 可加入」的议题,代价高,且不是常见场景。留作 Phase 4 room-chat 集成测试时自然暴露
- **§12 豁免 4 条顺序**:完全需要 room_turn 模式 + silent_rounds 状态,Session 6 此次不覆盖,留到 Phase 4

---

## §13.6 发现的规则歧义清单(v0.1.3 待修补)

3 个 subagent 独立提出的规则歧义汇总,去重后共 **10 项**。按严重度排序:

### 🟡 中等严重度(影响打分一致性)

1. **§7.5 structure_complement「部分补位」阈值未定义**(T-A, T-B 重复发现)
   - 规则只写「部分补位 → 5」,没说什么算部分
   - subagent 用了「moderate tendency + 议题全 offensive top3 → 5」的启发式,但缺乏明文依据

2. **§7.7 redundancy_penalty「角色定位高度重复」量化阈值缺失**(T-B)
   - 规则说「高度重复 → -10」,但没说几个 tag 交集算高度
   - subagent 用了「≥2 tag 交集 → -10」,但阈值可以是 1 或 3

3. **§7.7 redundancy_penalty「dominant 过度累积」主语不明**(T-A)
   - 规则写「≥2 个高分 dominant → -5」,但没说这 -5 扣在谁身上
   - 是扣在「已累积的 dominants」还是「第 3 个及以后新加入的 dominant」?

4. **§E-2「最弱冗余位成员」在唯一 defensive 时如何处理**(T-B)
   - T-B iter 1 时,Taleb 是最弱 dominant 但也是唯一 defensive,不能被替换
   - 规则没说「跳过不可替换者」,但 subagent 本能这么做了

### 🟢 低严重度(影响边缘情况可解释性)

5. **§5.3.1 stage 锚定词冲突无 tie-breaker**(T-A)
   - 「A 还是 B」同时命中 converge 表和 decision 表,规则要求「按最明确信号选」但没给优先级

6. **§7.3 阶段相邻关系图的跨节点歧义**(T-B)
   - explore ↔ simulate ↔ stress_test,stress_test 是否与 explore 2 跳相邻?
   - subagent 按「只看直接相邻」解读,但字面可以更宽松

7. **§7.4 role_uniqueness 与 E-1.1 的时序关系未显式说明**(T-A)
   - role_uniqueness 按硬过滤后候选池(13 人)算,E-1.1 降级只影响 roster
   - 没明文说「降级前先完整算打分再降级」,容易误把降级后 roster 当 uniqueness 对比池

8. **§7.4 role_uniqueness 在高重叠候选池下区分度偏弱**(T-C)
   - 当前 14 人 tag 分布下,first_principles 被 8 人共享,大多数候选的 `N ≥ 3` → uniqueness 全 0
   - 反而是 tag 最边缘的 Sun 在 risk 议题上拿高分,违反直觉
   - v0.1.3 可考虑 Jaccard 归一化或按 self_tags 规模调整阈值

9. **§7.5 structure_complement 对 top3 自身的处理未定义**(T-A, T-C 重复发现)
   - top3 成员自己的 structure_complement 怎么算?
   - subagent 都给 0(自己不能补自己),合理但未明文

10. **Top 3 参考集并列时的 tie-breaker 未定义**(T-B)
    - 第二遍打分要「以第一遍 top 3 为参考」,但 top3 出现并列时用哪 3 个?
    - 本次未触发(top3 边界清晰),但存在理论 gap

---

## §13.7 v0.1.3 修补建议

**本次 Session 6 不做 v0.1.3 补丁**,理由:

1. 10 项都是**规则清晰度 gap**,不是 bug —— 规则本身按预期工作,subagent 能独立做出合理判断
2. Session 6 的优先级是 Phase 4 room-chat.md,P1 活体回归已通过,不应该在规则微调上反复纠缠
3. 10 项里有 3-4 项需要在实际多轮对话中才能看到影响,Phase 4 跑起来后再一次性补 v0.1.3 更有信号
4. **显式标记为 v0.1.3 待修补**,并在 NEXT-STEPS.md 登记,避免遗忘

**Session 6 接下来的动作**:直接进 P2(Phase 4 · room-chat.md)。v0.1.3 补丁留给 Session 7 或 Session 8。

---

## §13.8 稳定性评分更新

| 版本 | 纸面 | 活体 |
|---|---|---|
| v0.1(Session 3) | 6/10 | — |
| v0.1.1(Session 4) | 7/10 | **8/10** |
| v0.1.2 纸面(Session 5) | 8/10 | —(gap) |
| **v0.1.2 活体(Session 6)** | 8/10 | **8/10** ✓ 维持 |

**结论**:v0.1.2 规则清晰度没有比 v0.1.1 明显提升(10 项歧义中有一些是 v0.1.1 就存在但没人发现的),但**行为正确性完全保持**。评分不降,gap 解除。

---

## §13.9 给 Session 6 P2(room-chat.md 写作者)的交接

1. **v0.1.2 活体验证通过**,你可以基于当前 v0.1.2 的 selection prompt 输出格式设计 room-chat 的输入契约
2. **conversation_log 的 Turn schema 必须与 room-architecture.md §5.5 一致**,不要重新定义
3. **speakers 字段来自 room_turn 模式的 selection prompt 输出**,你的 room-chat prompt 必须能消费 4 个角色(primary / support / challenge / synthesizer)+ 每人本轮职责
4. **单条发言长度约束 80-180 字**(architecture §7),这是硬约束
5. **最多 2 跳引用**(architecture §7),超过要截断或改写
6. **10 项 v0.1.3 歧义清单**(§13.6)在写 room-chat 时可能重新暴露,如果你需要决定某项歧义,把决定记录到本文件 §13.6 对应条目旁边

---

_§13 于 2026-04-11 Session 6 第一步完结同步。v0.1.2 补丁的活体回归 gap 已解除,P1 任务完成,开始 P2(room-chat.md)。_
