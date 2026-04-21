# Room Selection Policy

> `/room` 模式下「谁能进花名册 / 谁在本轮开口」的正式协议。
> 本文件是规则来源,`prompts/room-selection.md` 是它的可执行实现。
> 生成:2026-04-10 | schema: v0.2 | 修订:2026-04-12 (Session 8 P3: §12 @agent executable contract)

---

## 1. 目的与定位

这套规则解决的核心问题是:

> 给定一个议题,从 14 个已注册 Agent 里挑出**最小够用**的阵容——
> 既不是人越多越好,也不是分最高的前 N 个,而是**当前这一步最需要谁**。

它不是"选最豪华阵容",而是"选结构最合理、token 最省、信息增量最大的组合"。

## 2. 触发时机

选人流程**不是每轮都全量建房**。`room_full` 只在建房时跑;普通用户发言只跑 `room_turn`,不重建花名册。触发场景如下:

| 触发场景 | 动作 |
|---|---|
| `/room <议题>` 建房 | 全量执行(生成花名册) |
| `/focus <子问题>` 切换焦点 | 只跑单轮选人(不动花名册) |
| 主持器判定阶段切换 | 只跑单轮选人 |
| `/add <name>` / `/remove <name>` | 局部更新花名册 |
| 连续 3 轮某必需对冲位沉默 | 触发强制补位(见 §12) |
| 普通用户发言回应 | 只跑 `room_turn`,复用当前花名册,重选本轮 `speakers[]` |

## 3. 输入

选人流程的标准输入:

```
topic:           原始议题文本
user_constraints:
  with:          [Agent 列表,可空]
  without:       [Agent 列表,可空]
  mentions:      [Agent 列表,可空,@点名解析结果]
  topic_hint:    [主类型偏好,可空,如 product/strategy]
current_state:   (仅在单轮重选时需要)
  roster:        [当前花名册]
  last_stage:    当前已识别的阶段
  recent_log:    最近 3 轮发言摘要(可压缩)
mode:            "room_full" | "room_turn" | "roster_patch"
```

## 4. 五阶段流水线

```
[A] 议题解析        → 主类型 / 子问题标签 / 阶段 / 显式约束
[B] 硬过滤          → 排除不符硬约束的 Agent
[C] 结构化打分      → 7 分项 / 100 分 / 每人一份 scorecard
[D] 模型 ±5 校正    → 附理由,不得突破硬约束或结构规则
[E] 结构平衡 + 裁剪 → 组合优化,输出最终名单与职责
```

这 5 步按顺序执行,上一步的输出是下一步的输入。后面章节逐一展开。

---

## 5. 阶段 A:议题解析

从原始议题中抽取 4 样结构化信号。

### 5.1 主任务类型 + 副类型

在 `/debate` 已有的 8 类中选:
```
startup / product / learning / content / risk / planning / strategy / writing
```
- 必须选出 1 个**主类型**
- 可选 1 个**副类型**(置信度 ≥ 60% 才写)
- 必须附 1 句理由

### 5.2 子问题分解

从议题中识别 1-3 个**子问题**,并为每个子问题分配 1-3 个 sub_problem_tag(来自 v0.2 受控词表,共 20 个)。

20 个合法 tag:
```
value_proposition / market_timing / market_sizing / competitive_structure /
product_focus / user_experience / growth_strategy / distribution /
monetization / tail_risk / downside_analysis / execution_path /
technical_feasibility / resource_allocation / team_dynamics /
regulatory_risk / long_term_strategy / first_principles /
narrative_construction / learning_explanation
```

**不允许使用词表外的自造标签**。如果议题的子问题超出词表,写 `out_of_vocabulary`,并在模型校正环节扣除该子问题的权重。

### 5.3 阶段识别

在 5 种阶段中选 1 个当前最主要的阶段:
```
explore       发散探索,识别可能性,边界还不清晰
simulate      推演假设路径,"如果 X 会发生什么"
stress_test   压力测试,主动找 downside 和黑天鹅
converge      收敛选项,减少分歧,压缩候选集
decision      定案,给统一建议,回答"做不做/选哪个"
```

建房时默认 `explore`,除非议题文本明确表达了其他阶段信号。

#### 5.3.1 阶段锚定词表(v0.1.2 新增)

为了让 LLM 对 stage 判定稳定,提供以下锚定词表。**如果议题文本包含以下关键词,优先按对应 stage 判定**:

| stage | 锚定词 / 短语 |
|---|---|
| `explore` | 「有哪些可能」「我想了解」「探索」「有什么选项」「可能性」「还有什么」 |
| `simulate` | 「如果 X 会怎样」「假设」「推演」「沙盘」「模拟」「我想看看」「会发生什么」「可行吗」「具体路径」「怎么破」「怎么做到」「具体到」 |
| `stress_test` | 「最坏情况」「如果失败」「最糟糕的」「风险是什么」「worst case」「黑天鹅」「极端情况」「压力测试」「最大损失」 |
| `converge` | 「收敛」「排除哪个」「哪个更好」「比较 A 和 B」「优先哪个」「先做哪个」 |
| `decision` | 「A 还是 B」「选 X 还是 Y」「要不要」「做不做」「拍板」「决定」「下一步」「开始」「定案」 |

**使用规则**:
1. 扫描 topic 文本,优先匹配这个词表
2. 如果命中多个 stage 的锚定词,按**最明确的信号**选(「A 还是 B」+「最坏会怎样」→ 两种解读都合理,按前者优先 → `decision`)
3. 如果都不命中,按 §5.3 的**默认值**(explore)
4. 活体回归(Session 4 §11)发现 LLM 对 converge/decision 的边界感不稳,本词表是主要修补

#### 5.3.2 阶段识别的稳定性要求

LLM 必须:
- 在每次 `room_full` / `room_turn` 调用中**显式给出 stage_reason**,引用锚定词或议题文本中的具体信号
- **不允许**只写「这个议题感觉像 X 阶段」作为理由
- 在 `room_turn` 模式下,如果 `current_state.last_stage` 存在,**优先保持一致**,除非有强锚定词触发切换

### 5.4 显式约束抽取

从 `user_constraints` 和 `topic` 文本中读出:
- `--with` 强制包含列表
- `--without` 强制排除列表
- `@Xxx` 点名硬约束(优先读 `user_constraints.mentions`,并与 `topic` 文本里解析出的点名取并集)
- 隐式偏好(例如"请谨慎一点"→偏 defensive)

---

## 6. 阶段 B:硬过滤

硬过滤只做**能不能进池**的判断,不算分。以下 Agent **直接剔除**,不进入打分:

| 规则 | 判定 |
|---|---|
| **R1 状态不符** | registry.json 中 `status != registered` |
| **R2 显式排除** | 出现在 `--without` 列表 |
| **R3 non_goals 正面冲突** | 读 profile 的 `## 不该越界的事` 字段,若与当前**主任务类型**正面冲突则剔除 |
| **R4 默认排除位** | registry.json 中 `default_excluded: true`(如 Trump),除非出现在 `--with` |

R3 的判定示例:
- 议题主类型 `risk` + 某 Agent 的"不该越界"中写了"不主做风险兜底" → 剔除
- 议题主类型 `learning` + 某 Agent 的"不该越界"中写了"不主做教育解释" → 剔除

**R3 不做语义扩展**——只剔除文本明确写出的正面冲突,不做推断。宁可少剔,不错剔。

---

## 7. 阶段 C:结构化打分(7 分项)

通过硬过滤的候选者,**每个人**填一张 scorecard。总分 100,加减分都要写理由。

### 7.1 子问题匹配分 `0-30`(权重最高)

对比 Agent 的 `sub_problem_tags` 与**当前议题已识别的子问题标签集合**。

**规则表**(v0.1.2 调整):
| 命中数 | 分数 |
|---|---|
| 命中 ≥ 3 个子问题标签 | 30 |
| 命中 2 个 | 22 |
| 命中 1 个 | 14 |
| 0 命中但同主任务类型 | **3**(v0.1.2 从 6 下调) |
| 0 命中且非主任务类型 | 0 |

**严格规则**:只看标签交集,不允许 LLM 按语义"觉得像"就给分。这是评分稳定性的第一道防线。

**v0.1.2 下调理由**(Session 3 FINDING #5):
- 原 6 分地板与 task_type_match 15 分主命中 + stage_fit 15 分直命中叠加,让「标签对但角度不对」的 Agent 可以靠 30+ 分的基础地板混进 roster
- 下调到 3 分,让 sub_problem_match 子项成为更主导的差异信号
- 对 Session 3 / Session 4 三议题的回归不受影响(Topic B/D 的 Karpathy 从 6 → 3,Jobs 仍稳定 22,sub 差依然 = 8)

### 7.2 任务类型匹配分 `0-20`

对比 Agent 的 `task_types` 与议题主/副类型。

**v0.1.2 规则歧义消除**(Session 4 活体回归发现):原版「主/副类型命中」的措辞有两种解释,本版本**明确锁定**为以下解释:

- **「主类型命中」** = 议题的 `parsed_topic.main_type` 出现在 Agent 的 `task_types` 列表中(不论在 Agent 的 task_types 里是第几位)
- **「副类型命中」** = 议题的 `parsed_topic.secondary_type`(如果有)出现在 Agent 的 `task_types` 列表中
- **如果议题没有 secondary_type** (null),则「副类型命中」**恒为 false**,即使 Agent 的 task_types 有多个也不算副命中

| 条件 | 分数 |
|---|---|
| 议题主类型命中 + 副类型命中(议题必须有 secondary_type) | 20 |
| 议题主类型命中(副类型不存在或不命中) | 15 |
| 议题副类型命中但主类型不命中(议题必须有 secondary_type) | 8 |
| 均不命中 | 0 |

**校准例子**:
- 议题 main=product, secondary=null。Agent Karpathy 的 task_types=[learning, product, planning]。按 v0.1.2 判定:**主类型 product 命中 Karpathy 的 task_types → 15 分**。Karpathy 的 task_types 里 learning 在第 1 位,product 在第 2 位,这**不影响**判定——只要 Agent 的列表里有议题的 main_type 就算主命中
- 议题 main=startup, secondary=strategy。Agent Munger 的 task_types=[risk, strategy, planning]。按 v0.1.2 判定:**主类型 startup 不命中(Munger 没有 startup)→ 副类型 strategy 命中 → 8 分**

### 7.3 阶段适配分 `0-15`

对比 Agent 的 `stage_fit` 与议题当前 stage。

| 条件 | 分数 |
|---|---|
| stage 直接命中 | 15 |
| stage 不命中但与其 stage_fit 相邻(见 §7.3.1) | 8 |
| 完全不命中 | 0 |

#### 7.3.1 阶段相邻定义

```
explore ↔ simulate ↔ stress_test
           ↓             ↓
        converge ←→ decision
```
相邻的定义:上图连线直接相连的两个 stage。

### 7.4 职责独特性分 `0-15`

衡量这个 Agent 带来的**信息增量**。

**v0.1.2 严格解释**(Session 4 活体回归发现):

**计算步骤**:
1. 取本 Agent 的 `sub_problem_tags` 集合(记为 `self_tags`)
2. 对**其他所有通过硬过滤的候选者**逐一检查:取该候选者的 `sub_problem_tags` 集合(记为 `other_tags`),计算 `|self_tags ∩ other_tags|`
3. 统计「其他候选者中,与本人 tag 交集 ≥ 2 的人数」,记为 `N`
4. 按下表评分:

| `N`(与本人 ≥2 tag 重合的其他候选者人数) | 分数 |
|---|---|
| 0 | 15 |
| 1 | 10 |
| 2 | 5 |
| ≥ 3 | 0 |

**严格解释要点**(避免 Session 3 与活体回归的分歧):
- **只看「本人 vs 其他每个候选」** 的两两比较,不做全局配对统计
- 不是「池子里有多少对 ≥ 2 tag 重合」,而是「有多少其他人跟**本人**这一个 ≥ 2 tag 重合」
- 同一议题下,不同 agent 的 role_uniqueness 可能都拿 15(如果他们彼此的 tag 重合都 < 2)

**校准例子**(Topic B/D):
- Jobs 的 tags = [value_proposition, product_focus, user_experience, first_principles, narrative_construction]
- PG 的 tags = [value_proposition, market_timing, market_sizing, product_focus, first_principles] → Jobs ∩ PG = [value_proposition, product_focus, first_principles] = 3 ≥ 2 ✓(重合)
- Musk 的 tags = [first_principles, execution_path, resource_allocation, technical_feasibility, product_focus] → Jobs ∩ Musk = [product_focus, first_principles] = 2 ≥ 2 ✓(重合)
- Feynman 的 tags = [first_principles, learning_explanation, technical_feasibility, user_experience] → Jobs ∩ Feynman = [first_principles, user_experience] = 2 ≥ 2 ✓(重合)
- ...
- 数下来,Jobs 与 **3 人以上**(PG / Musk / Feynman / 其他)有 ≥ 2 tag 重合 → `N ≥ 3` → **Jobs role_uniqueness = 0**

**活体 LLM 的 15 分判定是错的**(Session 4 §11.1.3 发现):活体认为「无人与 Jobs ≥ 2 tag 重合」,这是对规则的宽松解释,v0.1.2 明确为严格解释后,**Jobs 的 role_uniqueness 回归到 Session 3 的 0 分**。

### 7.5 结构补位分 `0-10`

检查当前**已选高分候选**(top 3)的标签分布,本 Agent 能否补短板。

| 条件 | 分数 |
|---|---|
| 当前 top 3 全是 dominant 且本人 defensive | 10 |
| 当前 top 3 无 grounded 且本人 grounded | 10 |
| 当前 top 3 无 defensive 且本人 defensive | 10 |
| 仅部分补位 | 5 |
| 无补位作用 | 0 |

**注意**:这一项每人打分时要以"当前 top 3"为参考,所以打分顺序是:
1. 先按前 4 项(最高 80 分)初算
2. 取初算 top 3 为参考集
3. 再为所有候选回填第 5 项
4. 最后算第 6、7 项

### 7.6 用户偏好分 `-10 到 +10`

| 条件 | 分数 |
|---|---|
| 出现在 `--with` 列表 | +10 |
| 议题中被 `@点名` | +10 |
| 隐式偏好正向(如"请帮我一起推进")且本人 offensive | +3 |
| 隐式偏好负向(如"请谨慎")且本人 defensive | +3 |
| 隐式偏好与本人倾向冲突 | -5 |
| (--without 在硬过滤已剔除,不在此重复) | — |

### 7.7 冗余与越权惩罚 `-20 到 0`

| 条件 | 扣分 |
|---|---|
| 当前议题正面命中其 `## 不该越界的事` 但未触发 R3(边缘冲突) | -10 |
| 角色定位与已选 top 3 中某人重复度极高 | -10 |
| 单一强势风格过度累积(已有 ≥ 2 个 dominant 高分位时) | -5 |

### 7.8 总分公式

```
TotalScore =
    subproblem_match      (0  ~ 30)
  + task_type_match       (0  ~ 20)
  + stage_fit             (0  ~ 15)
  + role_uniqueness       (0  ~ 15)
  + structure_complement  (0  ~ 10)
  + user_preference       (-10~ +10)
  + redundancy_penalty    (-20~ 0)
--------------------------------
  理论区间 [-30, 100]
```

### 7.9 `room_turn` 评分覆盖规则(v0.1.3-p2)

`room_turn` 是**固定花名册内的单轮调度**,不是重新建房。因此以下 roster 级别字段不得因候选池从 14 人缩小到当前花名册而重新波动:

1. `role_uniqueness`:在 `mode == room_turn` 时统一填 `0`,并在 `model_adjust_reason` 或 `explanation` 中说明「单轮调度不重算 roster 级信息增量」。不要拿当前 2-8 人花名册重新计算 §7.4,否则同一 Agent 的独特性会随花名册大小变化。
2. `redundancy_penalty`:在 `mode == room_turn` 时统一填 `0`。单轮选人只负责当前子问题下谁先发言,不使用「与 top 3 重复」或「dominant 过载」惩罚挤掉已入 roster 的成员。
3. `room_turn` 仍然保留 `subproblem_match` / `task_type_match` / `stage_fit` / `user_preference` / `model_adjust`,并继续执行 §9.5 的单轮结构软规则与 §12 强制补位规则。
4. `room_turn task_type_match 上限`:由于 `room_full` 已经用 task_type 建过花名册,单轮调度只用 task_type 做弱信号。`mode == room_turn` 时使用下表替代 §7.2 的 0-20 表:

| 条件 | room_turn 分数 |
|---|---|
| 议题主类型命中 + 副类型命中(secondary 存在) | 12 |
| 议题主类型命中(副不存在或不命中) | 9 |
| 议题副类型命中但主类型不命中(secondary 存在) | 5 |
| 均不命中 | 0 |

5. `room_full` 与 `roster_patch` 不受本覆盖规则影响,仍按 §7.2 / §7.4 / §7.7 完整计算。

---

## 8. 阶段 D:模型 ±5 校正

打分完成后,允许 LLM 对**已有分数**做 **-5 到 +5** 的调整,但必须满足:

1. **每次调整必须附 1 句理由**,写进 scorecard 的 `model_adjust_reason` 字段
2. **不允许**突破硬过滤(即不能把被剔除的 Agent 拉回)
3. **不允许**一次调整超过 ±5
4. **不允许**对结构补位分和冗余惩罚分做校正(这两项是机械规则,不是语义判断)
5. 允许做校正的分项:子问题匹配、任务类型、阶段适配、职责独特性、用户偏好

模型的校正职责是处理"规则打底但表达微妙"的情况,例如:
- "这个子问题表面是 `product_focus`,但实质在讨论 `first_principles`"
- "这个 Agent 的 task_types 写了 strategy,但当前议题更贴近他的副职 planning"

**不允许**的校正行为:
- 因为"感觉 Taleb 应该在场"而强行 +5
- 因为"不喜欢 Trump"而 -5

---

## 9. 阶段 E:结构平衡 + 人数裁剪

### 9.1 排序

按 TotalScore 降序排列所有候选。

**v0.1.2 tie-breaker**(Session 3 FINDING #3):当 TotalScore 并列时,按以下优先级**依次**打破平局:

1. `subproblem_match` 子项高者优先
2. `stage_fit` 子项高者
3. `role_uniqueness` 子项高者
4. 仍并列 → 按 `agent_id` 字母序(deterministic 兜底)

**为什么这个顺序**:
- subproblem_match 是最直接的「议题契合度」信号,并列时优先选真正命中的
- stage_fit 次之,反映阶段适配
- role_uniqueness 再次,反映信息增量
- agent_id 字母序是最后的 deterministic 兜底,保证同一输入下输出唯一

### 9.1.1 议题琐碎度降级预检(仅 room_full)

在进入 §9.2 花名册构建之前,先检查议题是否「琐碎到不值得多人讨论」。此规则填补**陪跑 20%** 场景的覆盖空洞——UI 微决策、简单 A/B、命名选择等不应被分配 4 人花名册。

此规则**只在 `mode == room_full`** 下执行。`room_turn` 与 `roster_patch` 不跑此检查。

#### 9.1.1.1 触发条件(必须同时满足 4 条)

1. **单一窄子问题**:`parsed_topic.sub_problems.length == 1`,且该唯一子问题的 `tags.length ≤ 2`
2. **收敛期阶段**:`parsed_topic.stage ∈ {converge, decision}`
3. **议题文本极短**:`topic` 长度 ≤ **20** 字符(按 Unicode code point 计,中文字算 1)
4. **子问题匹配度压倒性领先**:在通过硬过滤的候选池中,`top1.scores.subproblem_match - next_highest_subproblem_match ≥ 8`,其中 
ext_highest_subproblem_match` 是**去掉 top1 后**候选中 `subproblem_match` 的最高值

> 注意:条件 4 用的是 `subproblem_match` **子项**的差,**不是 total 分差**。这是刻意为之——差异化的信号来自「子问题真正命中了几 tag」,而不是堆砌出来的 task_type+stage 基础分。用 total 差会因为「产品类议题人人都有 task_type=product 的 15 分底」而无法识别琐碎度。

#### 9.1.1.2 触发时的动作

- `roster` 仅取 `top1`(**单人花名册**)
- **跳过** §9.3 的结构平衡硬规则检查
- `structural_check.passed = true`
- `structural_check.warnings` 追加字符串 `"trivial_topic_downgrade"`
- **不视为** 
o_qualifying_roster` 错误,**不走** §13 的错误路径
- `explanation.why_selected` **必须**显式写出降级理由,例如:
  > "议题琐碎降级:converge 阶段 + 单一窄子问题 + topic 仅 11 字 + top1 子问题匹配度领先次高者 8 分,陪跑场景单人咨询足够"
- `explanation.why_not_selected` 可以简化为一句:「其余候选未进入花名册,触发琐碎度降级」

#### 9.1.1.3 不触发时的行为

4 条中任一不满足 → **不降级**,按常规进入 §9.2 花名册构建。

#### 9.1.1.4 Session 3 验证议题回归校验

为证明本规则不会误降真正需要多视角的议题,用 Session 3 三个测试议题回归:

| 议题 | 长度 | stage | 子问题数 | top1 sub / 次高 sub | 差 | 4 条全满足? | 降级? |
|---|---|---|---|---|---|---|---|
| A(独立开发者 AI 工具 All in?) | 27 | explore | 2 | Sun 30 / PG 30 | 0 | ✗ 条件 1、2、3、4 全不满足 | **否** ✓ |
| B(按钮放左边还是右边) | 11 | converge | 1 | Jobs 22 / 次高 14 | 8 | ✓ 4 条全满足 | **是** — roster=[Jobs] ✓ |
| C(项目失败最坏会怎样) | 15 | stress_test | 1 | Taleb 22 / Munger 14 | 8 | ✗ 条件 2 不满足 | **否** ✓ |

三议题判定与 Session 3 验证报告 §1-3 的预期一致。

#### 9.1.1.5 已知限制与未来调参空间

- **阈值 ≥ 8 是保守值**。如果未来发现 Topic B 类议题在某些模型上 subproblem_match 子项差被压缩到 6,可以考虑在 v0.1.1 下调到 ≥ 6。但**不建议**把阈值降到 ≤ 4,会开始误降真正二难的议题。
- **topic 长度 20 字符上限**是为中英混排留余地。纯英文场景如果常见 25-30 字符,可以考虑单独设英文阈值。v0.1 暂时不分语言。
- **条件 2 的 stage 集合**刻意不包含 `explore`。即使一个 explore 议题文本极短,也应当保留多视角,因为 explore 的目的就是发散。
- **用户 `@点名`或 `--with` 的互斥**:如果用户显式点名了 2 人以上,**跳过本降级规则**,走常规 §9.2 流程。用户的显式意图优先于自动降级。

### 9.2 花名册构建(room_full 模式)

**花名册目标人数:2-8 人,软顶 8**。

**v0.1.2 迭代替换算法明确化**(Session 3 FINDING #8):

**步骤**:

```
1. 取 top 4 作为 current_roster
2. iter_count = 0
3. while iter_count < 5:
     check = check_structural_balance(current_roster)  # §9.3
     if check.passed:
       return current_roster  # 成功
     
     # 尝试替换:找「缺失位最强候选」替换「冗余位最弱成员」
     missing_role = check.missing_role  # defensive / grounded / balance_offensive
     best_candidate = find_best_candidate_with_role(remaining_pool, missing_role)
     weakest_redundant = find_weakest_redundant_in(current_roster)
     
     if best_candidate and weakest_redundant:
       current_roster.replace(weakest_redundant, best_candidate)
       iter_count += 1
       continue
     
     # 无法替换,尝试扩招
     if len(current_roster) < 8:
       current_roster.append(best_candidate)  # 从 remaining_pool
       iter_count += 1
       continue
     
     # 超过 8 人仍不满足
     break

4. 最终:
   - if passed → 返回 current_roster
   - if len > 8 → 错误 no_qualifying_roster_oversized
   - if iter_count >= 5 → 错误 no_qualifying_roster(扩到 5 轮仍不平衡)
```

**关键规则**:
- **单次最多 5 轮迭代**(避免无限循环)
- **替换优先于扩招**(保持花名册紧凑)
- **候选 look-ahead 1 层(v0.1.3)**:选择 `best_candidate` 时,必须跳过会导致其他结构平衡硬规则立即失败的候选。例:补 `grounded` 时,如果最高分 grounded 候选会让 `dominant > floor(n/2)`,应跳过他,选下一个能让全部 §9.3 规则同时通过的候选。
- **扩招到 8 人即停**(软顶)
- **`--with` 锁定的人不能被替换**(Session 2 决议)

**原版的歧义**(Session 3 FINDING #8):原版写「不满足时替换 → 仍不满足再扩招」没明确「替换失败后才扩招」还是「交替进行」。v0.1.2 明确为**先尝试替换,替换成功则继续下轮检查,替换无解才扩招**,并限制 5 轮迭代上限。

### 9.3 结构平衡硬规则(继承 /debate)

花名册**必须同时**满足:

- **至少 1 个 defensive**(tendency=defensive)
- **至少 1 个 grounded**(expression=grounded)
- **dominant ≤ 花名册人数的一半**(向下取整)
- **至少 1 个 offensive 或 moderate**(v0.1.2 新增,Session 3 FINDING #4)

补位优先级:
```
defensive 缺失 → Munger / Taleb / Zhang Xuefeng / Feynman(按分数)
grounded  缺失 → Musk / Munger / Feynman / Zhang Xuefeng / MrBeast(按分数)
offensive/moderate 缺失 → Sun / PG / Jobs / Musk / Naval / Karpathy(按分数,v0.1.2 新)
dominant 过载 → 降级最低分的 dominant,换 moderate 或 defensive
```

**v0.1.2 第 4 条规则的设计理由**(Session 3 FINDING #4):
- 原版只要求「≥ 1 defensive」,没有对称要求「≥ 1 offensive」
- 在 stress_test / risk 类议题上,候选池可能全是 defensive(Topic C 就暴露了这个情况)
- 全 defensive 的 roster 会失去「反对的反对」角色,讨论变成单边批判,失去 offensive 视角提供的「建设性假设」
- v0.1.2 追加「≥ 1 offensive 或 moderate」,保证花名册始终有**建设性 + 批判性**两极
- 为什么允许 `moderate` 计入:moderate 位可以作为「中性桥梁」,在全 defensive 议题上也能扮演 offensive 的弱化版角色(例如 Karpathy 虽然 moderate,但能在 stress_test 议题上提供技术可行性的中性视角)

**Topic C 的回归影响**(Session 3 议题):
- 原版 Topic C 花名册 = Taleb / Munger / Zhang Xuefeng / Ilya(3 defensive + 1 offensive)→ 已经满足 v0.1.2 第 4 条
- 但如果 Ilya 分数不够高,原版可能会产出 Taleb / Munger / Zhang Xuefeng / Feynman(全 defensive)—— v0.1.2 下会**强制补入 offensive 位**

### 9.4 单轮发言裁剪(room_turn 模式)

**单轮发言硬顶 4 人**。

流程:
1. 以花名册为候选池(而非全 14 人)
2. 运行阶段 A→D,但只给花名册内成员打分
3. 取当前子问题下的 top 2-4
4. 检查 §9.5 的单轮发言结构规则
5. 输出本轮 `speakers[]` 名单;不写 `turn_role`,该字段由 orchestrator 按 `room-architecture.md §7.2` 分配

### 9.5 单轮发言结构规则(比花名册略宽松)

- **尽量**每轮至少带 1 个 defensive **或** 1 个 grounded
- **不强制**每轮满足,但**不得连续 3 轮**都没有 defensive 上场(详见 §12)
- 如果用户 `@点名` 某 Agent,该 Agent 必须上场,可突破结构规则,但主持器必须在状态里显式标记"本轮偏斜"

### 9.6 花名册补丁(roster_patch 模式)

响应 `/add` 或 `/remove`:
- `/add`:直接走一次硬过滤(R1+R2+R4),通过即加入花名册;若花名册超过 8,显式警告但不阻止
- `/remove`:直接移除,然后运行一次 §9.3 结构平衡校验,若失衡则自动补位一个

---

## 10. 输出格式

选人流程的标准输出:

```json
{
  "mode": "room_full" | "room_turn" | "roster_patch",
  "parsed_topic": {
    "main_type": "product",
    "secondary_type": "strategy",
    "sub_problems": [
      {"text": "切口够不够窄", "tags": ["value_proposition", "product_focus"]},
      {"text": "是不是 winner-takes-all", "tags": ["competitive_structure", "market_sizing"]}
    ],
    "stage": "explore",
    "constraints": {"with": [], "without": [], "mentions": []}
  },
  "hard_filtered": [
    {"agent": "trump", "reason": "default_excluded, 未出现在 --with"}
  ],
  "scorecards": [
    {
      "agent": "justin-sun",
      "scores": {
        "subproblem_match": 22,
        "task_type_match": 15,
        "stage_fit": 15,
        "role_uniqueness": 15,
        "structure_complement": 0,
        "user_preference": 0,
        "redundancy_penalty": 0,
        "model_adjust": 0,
        "model_adjust_reason": ""
      },
      "total": 67
    }
  ],
  "roster": [
    {"agent": "justin-sun", "short_name": "Sun", "role": "市场结构与 All in 判断位", "structural_role": "offensive"},
    {"agent": "taleb", "short_name": "Taleb", "role": "尾部风险对冲", "structural_role": "defensive"},
    {"agent": "paul-graham", "short_name": "PG", "role": "切口真假判断", "structural_role": "offensive"},
    {"agent": "munger", "short_name": "Munger", "role": "机会成本与自欺审查", "structural_role": "defensive"}
  ],
  "structural_check": {
    "defensive_count": 2,
    "grounded_count": 1,
    "dominant_count": 1,
    "dominant_ratio": 0.25,
    "passed": true
  },
  "explanation": {
    "why_selected": [
      "justin-sun: 子问题命中 competitive_structure + market_sizing,stage 命中 explore,当前议题唯一能谈 winner-takes-all 的人",
      "taleb: 结构平衡要求补 defensive,对冲 Sun 的 All in 倾向"
    ],
    "why_not_selected": [
      "jobs: 子问题 0 命中,当前议题不涉及产品聚焦",
      "karpathy: 非 strategy 主类型,分数偏低"
    ]
  }
}
```

**explanation 字段是强制的**,不允许省略——可解释性是这套系统的核心要求。

---

## 11. 可解释性要求

任何一次选人的输出**必须能回答以下问题**:

1. 为什么选了 A 没选 B
2. A 在本次讨论承担的具体职责是什么
3. 结构平衡是否通过,通过的依据是哪几个字段
4. 硬过滤剔除了谁、为什么

如果 LLM 生成的输出无法回答上述任一问题,视为**失败**,由调用方重跑或退回。

---

## 12. 强制补位规则

一个连续性规则,跨单轮运行。

> **状态所有权**:本规则依赖的 `silent_rounds` 计数器由 **orchestrator** 维护,不由 selection prompt 自己跟踪。完整的所有权、更新时机、传递路径见 [`room-architecture.md §3.1`](./room-architecture.md)。如果 orchestrator 没有实现该字段的维护,本规则将**永远不会被触发**(selection prompt 会收到空的 silent_rounds 字段)。

**判定条件**:
- 花名册中存在某个 `structural_role=defensive` 或 `expression=grounded` 的 Agent
- 该 Agent 连续 **3 轮**未被选入单轮发言者
- 当前议题没有明确脱离其覆盖范围

**动作**:
- 下一轮执行单轮选人时,**强制**将该 Agent 加入发言者名单
- 替换目标必须排除 `protected_speakers`(`--with` 与 `@点名`命中的 Agent)
- 替换顺序:先替换当前单轮 top 4 中分数最低的 `structural_role=offensive` 位;如果没有 offensive,替换分数最低的 `structural_role=moderate` 位;如果仍没有,替换分数最低的非 protected 位
- 如果该 Agent 已在本轮 top 4 或 `protected_speakers` 中,不重复加入,只记录对应 reason
- 在 `explanation` 中显式说明:"强制补位触发:<agent> 已连续 3 轮沉默"

**豁免情况**(v0.1.3-p3 明确检查顺序,Session 8 §12/@agent 补丁):

强制补位触发前,**必须按以下顺序依次检查豁免条件**。任一满足即跳过本轮强制补位,并在 `structural_check.warnings` 追加对应 reason:

1. **`removed_from_roster`**:用户已执行 `/remove` 把该 Agent 移出花名册。这是最硬的豁免——人都不在了,谈何补位
2. **`stage_mismatch`**:当前 `last_stage == "decision"` 且该 Agent 的 `stage_fit` 不包含 `decision`。强制一个明确不擅长 decision 的人入场,反而降低质量
3. **`explicit_mention_elsewhere`**:用户在最新一轮明确 `@点名`了其他 agent,且当前待补位 Agent 不在 `protected_speakers` 中。本轮结构已被用户意图覆盖,跳过这个未被点名 Agent 的强制补位
4. **`agent_was_auto_included`**:该 agent 已经在**本轮 top 4**的常规选人中入选,或已经在 `protected_speakers` 中被硬约束选入(不需要强制重复)

**豁免与计数的关系**:
- **豁免只影响本轮是否强制补位**
- **不影响 `silent_rounds` 的累加**(见 `room-architecture.md §3.1` 的决议)
- 下一轮 stage 切换或点名改变后,强制补位规则重新评估

---

## 13. 边界情况

| 情况 | 处理 |
|---|---|
| 硬过滤后候选不足 2 人 | 拒绝建房,显式要求用户放宽 `--without` |
| 所有候选分数 < 20 | 视为议题与现有 Agent 池不匹配,建议用户换议题或补充 skill |
| `--with` 导致结构严重失衡 | 先自动补对冲位,仍失衡则警告但不拒绝 |
| 子问题全部 `out_of_vocabulary` | 阶段 A 重跑一次,若仍失败,子问题分全员清零,仅靠其他分项选人 |
| 议题文本过短(< 10 字) | 阶段 A 要求调用方补充上下文后再重试 |

---

## 14. 与其他协议的关系

- **上游**:[`docs/room-architecture.md`](./room-architecture.md)(房间状态模型)——**v0.1-alpha 已落地**(Session 4),定义了 `silent_rounds` / `last_stage` / `turn_count` / `recent_log` 4 个运行时字段的所有权与传递路径;其余章节(§5-§9)留给 Phase 2
- **同级**:`docs/agent-registry.md`(注册表协议)——当前以 `agent-registry/README.md` 承载
- **下游实现**:`prompts/room-selection.md`(可执行 prompt)
- **不影响**:`docs/debate-skill-architecture.md`(`/debate` 协议完全独立)
- **共享**:14 份 `roundtable-profile.md`(同时被 `/debate` 和 `/room` 使用)

---

## 15. 版本记录

- **v0.1 (2026-04-10)**:首版协议,基于 D 盘大报告 §13-18 + 决策讨论
- **v0.1.1 (2026-04-11, Session 4)**:新增 §9.1.1 议题琐碎度降级预检,修补 Session 3 验证报告 FINDING #1 + #2
- **v0.1.2 (2026-04-11, Session 5)**:Phase 2 同期补丁,修补 Session 3 剩余 FINDING + Session 4 活体回归发现的规则歧义:
  - **§5.3 stage 识别**:新增锚定词表(§5.3.1),修补 Session 4 活体回归发现的 stage 识别不稳定
  - **§7.1 子问题匹配分**:「0 命中 + 同主任务类型」地板从 6 → 3(FINDING #5)
  - **§7.2 task_type_match**:明确规则歧义(活体回归发现)——锁定为「议题 main_type/secondary_type 是否出现在 Agent 的 task_types 列表中」
  - **§7.4 role_uniqueness**:明确严格解释(活体回归发现)——只看「本人 vs 其他每个候选」的两两比较,不做全局配对
  - **§9.1 排序**:新增 tie-breaker 规则(FINDING #3)——按 subproblem_match / stage_fit / role_uniqueness / agent_id 字母序依次打破平局
  - **§9.2 花名册构建**:明确迭代替换算法(FINDING #8)——5 轮迭代上限,替换优先于扩招
  - **§9.3 结构平衡硬规则**:新增第 4 条「至少 1 个 offensive 或 moderate」(FINDING #4)——防止 stress_test 议题产生全 defensive 花名册
  - **§12 强制补位豁免**:明确检查顺序(FINDING #7)——4 条豁免按优先级依次检查,并与 silent_rounds 计数器的关系写入
  - **未修改**:§9.1.1 琐碎度降级规则(v0.1.1 已活体验证通过,不动)、§1-§8 的其他主结构
  - `/debate` 零影响,`/room` 的 `room_full` / `room_turn` / `roster_patch` 三个模式都需要按新规则重新打分,但**E-1.1 琐碎度降级不受影响**(因为只依赖 subproblem_match 子项,该字段的规则没变)
- **v0.1.3-p0 (2026-04-12, Session 8)**:P0 阻塞补丁。
  - **F1**:将 `structural_role` 收窄为纯 `tendency`(`offensive/defensive/moderate`),`grounded/dominant/abstract` 只属于 `expression`。
  - **F2**:在 §9.2 迭代替换中新增候选 `look-ahead 1 层`,跳过会立即破坏其他结构硬规则的候选。
- **v0.1.3-p1 (2026-04-12, Session 8)**:P1 selection 稳定性补丁。
  - **F9/F15**:新增 §7.9 `room_turn` 评分覆盖规则,单轮调度不重算 `role_uniqueness`,且不使用跨候选 `redundancy_penalty` 挤掉固定花名册成员。
  - **F13**:补充 simulate 阶段锚定词「具体路径 / 怎么破 / 怎么做到 / 具体到」。
  - **Flow 一致性**:修正 §2 普通用户发言触发描述,明确普通发言只跑 `room_turn`,不全量重建花名册。
- **v0.1.3-p2 (2026-04-12, Session 8)**:F14 权重补丁。
  - **F14**:新增 §7.9 `room_turn task_type_match 上限`,单轮调度使用 12/9/5/0 替代 20/15/8/0;`room_full` 和 `roster_patch` 不受影响。
- **v0.1.3-p3 (2026-04-12, Session 8)**:§12 / @agent 可执行契约补丁。
  - 新增 `user_constraints.mentions` 输入契约,把 `@点名` 从 prompt 猜测升级为主持器解析后的硬约束。
  - §12 强制补位替换目标排除 `protected_speakers`,并将旧的表达风格混入替换目标问题收敛为 `structural_role=offensive/moderate` 的确定替换顺序。










