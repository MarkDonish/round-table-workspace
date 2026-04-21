# DECISIONS LOCKED

最后更新:2026-04-11(Session 6,新增决议 41-45)
上次更新:2026-04-11(Session 5,决议 36-40);Session 4(28-35);Session 2(11-27);Session 1(1-10)
目的:锁定已经确认的设计决议,避免后续接力开发重复争论。

---

## Part I:Session 1 锁定的决议(继续生效)

### 1. 项目是"双模式",不是单模式

本项目不是只有 `/debate`。后续正式采用双模式:

- `/debate`:正式圆桌会议模式
- `/room`:半结构化多 Agent 房间模式

### 2. `/debate` 不改定位

`/debate` 继续保持:重大议题 / 强分工 / 主持汇总 / 审查放行 / 单一最终决议。

不允许把 `/debate` 改造成自由群聊。

### 3. `/room` 的核心用途权重已锁定

- 协同推演:60%
- 探索想法:20%
- 日常陪跑:20%

### 4. `/room` 采用"混合双层房间"方案

- 默认轻量聊天室
- 必要时切到更聚焦推演
- 再必要时升级为 `/debate`

### 5. Agent 必须复用本地名人 skill

不创建新 Agent 人格系统。Agent 来源固定为本地已配置名人 skill 的运行实例。

### 6. 新增 skill 采用"自动发现 + 条件注册"

- 新增 skill 后系统应自动发现
- 但不能安装即参会
- 只有满足协作元数据要求,才能进入 Agent Registry

### 7. 选人不是全员参会

必须根据当前议题、子问题、讨论阶段、结构平衡做筛选。

### 8. 评分系统采用"规则打底,模型辅助"

- 不让模型自由拍脑袋选人
- 使用半结构化评分系统
- 模型只做语义解析、软标签判断、小范围校正

### 9. `/room → /debate` 必须通过 handoff packet

从 `/room` 升级到 `/debate` 不是重新开始。必须先整理成正式交接包。`/debate` 只正式消费交接包,不直接消费整段群聊日志。

### 10. 当前阶段优先做协议层,不优先做代码原型

当前项目仍处于协议和设计收敛阶段。下一位 Agent 应优先补协议文档、注册机制、评分规则和 prompt。**不建议跳过这些直接做 UI 或聊天室工程原型**。

---

## Part II:Session 2 新增锁定的决议

### 11. 花名册与单轮发言是两个独立的上限概念

`/room` 中存在两层独立的上限,**不可混淆**:

- **花名册(roster)上限**:谁**有资格**在这个房间参会,几乎不烧 token
- **单轮发言(per-turn)上限**:每次用户发言后**实际**开口的人数,直接决定 token 成本

这两个数字完全独立。

### 12. 花名册软顶 8,单轮发言硬顶 4

- **花名册**:默认 2-4 人,软顶 **8 人**,理论上不封硬顶,但超过 8 显式警告并要求用户有明确理由
- **单轮发言**:无论花名册多大,每轮**硬顶 4 人**,挑当前子问题最相关的 2-4 个上场,其余在场但沉默
- 用户 `@点名`可以突破单轮 4 人上限,但主持器必须显式提示"本轮偏斜"

锁定依据:花名册大不烧 token,真正贵的是单轮发言;4 人以上单轮阅读负担明显增加,信息增量衰减;`/debate` 单场硬顶 5,`/room` 单轮不应超过它。

### 13. 结构平衡规则完全复用 `/debate`

`/room` 不造新结构平衡规则,直接沿用 `/debate` 的:

- **花名册层(强制)**:至少 1 个 `defensive` + 至少 1 个 `grounded` + `dominant` 不超过花名册人数的一半
- **单轮发言层(软规则)**:尽量每轮至少 1 个 `defensive` 或 `grounded`,**但不强制每轮满足**
- 用户 `--with` 造成失衡时,系统先自动补对冲位,仍失衡则显式警告

### 14. 强制补位规则:连续 3 轮沉默触发

当花名册中某个 `defensive` 或 `grounded` 位**连续 3 轮没被选入单轮发言**时:

- 下一轮**强制**把他塞进 speakers,替换掉当前 top 4 中分数最低的 `dominant/offensive` 位
- 必须在 `explanation` 中显式标注"强制补位触发:<agent> 已连续 3 轮沉默"

**豁免条件**:用户显式 `@点名` 其他人 / 用户已 `/remove` 移出花名册 / 当前 stage 是 `decision` 且该 Agent 的 `stage_fit` 不包含 decision。

锁定依据:单轮选人是贪心的,局部最优容易全局失衡;3 轮是温和值(2 轮太敏感,4 轮失衡窗口过长)。

### 15. Agent Registry 采用"索引而非物理搬动"

**不物理搬动**任何 skill 目录。注册表只做**索引**,原 skill 文件继续留在 `.codex/skills/<name>/` 下。

理由:
- `/debate` 现有协议写死了 `.codex/skills/<name>/roundtable-profile.md` 的读取路径(`AGENTS.md:86`, `debate-roundtable-skill/SKILL.md:73`)
- 物理搬动会立即破坏 `/debate`,风险大
- 索引方案零破坏、零迁移成本

### 16. Registry 物理位置:`C:\Users\CLH\agent-registry\`

顶层目录。与 `docs/` `prompts/` `.codex/` 平级,方便未来添加自动发现扫描脚本。

### 17. Profile Schema v0.2:追加 3 个结构化字段

对所有 14 份 `roundtable-profile.md` **追加**(不修改已有字段)一个新区块:

```
## 结构化匹配 (v0.2)
- task_types: [...]          # 从 8 类选 1-3 个
- sub_problem_tags: [...]    # 从 20 个受控词表选 3-8 个
- stage_fit: [...]           # 从 5 个阶段选 1-3 个
```

- 旧字段完全不动
- `/debate` 不读这个新区块,零影响
- `/room` 的筛选评分系统依赖这 3 个字段

### 18. sub_problem_tags 受控词表(v0.2 版,20 个锁定)

```
value_proposition / market_timing / market_sizing / competitive_structure /
product_focus / user_experience / growth_strategy / distribution /
monetization / tail_risk / downside_analysis / execution_path /
technical_feasibility / resource_allocation / team_dynamics /
regulatory_risk / long_term_strategy / first_principles /
narrative_construction / learning_explanation
```

**不允许**在 prompt 或 profile 里使用词表外的自造 tag。发现词表覆盖不够时,**不即时扩**,记录为 `out_of_vocabulary`,留到 v2 版统一扩展。

### 19. `narrative_construction` 不拆分

虽然这个 tag 同时被 Jobs(产品叙事聚焦)和 Sun(流量叙事变现)使用,方向不同,但**不拆分为 `product_narrative` / `attention_narrative`**。

理由:词表越细越难维护;细节语义交给 LLM 从 profile 的"角色定位"和"不该越界的事"字段里分辨;冗余惩罚机制(-20)可以兜底误用。

### 20. 8 个 task_types 沿用 `/debate` 的 §5.2

```
startup / product / learning / content / risk / planning / strategy / writing
```

不新增。`/debate` 原本的 8 类路由继续有效,`/room` 复用同一套词表以保证两模式语义一致。

### 21. 5 个 stages 沿用大报告 §15.3

```
explore / simulate / stress_test / converge / decision
```

相邻关系:
```
explore ↔ simulate ↔ stress_test
           ↓              ↓
        converge ↔  decision
```

相邻定义用于阶段打分的"相邻但不命中"情况。

### 22. 打分采用"两遍打分"策略

不是一次打完 7 项。必须分两遍:

**第一遍**:算 4 项(子问题匹配 30 + 任务类型 20 + 阶段 15 + 职责独特性 15),总分上限 80

**第二遍**:以第一遍 top 3 为参考集,回填剩下 3 项(结构补位 10 + 用户偏好 ±10 + 冗余惩罚 -20)

理由:结构补位分和冗余惩罚分依赖"当前阵容"作为参考,不能自引用。两遍打分有明确顺序,可解释。

### 23. 模型 ±5 校正的职责边界

模型可以对已有分数做 **-5 到 +5** 的微调,但:

- **每次调整必须附 1 句理由**,写进 scorecard 的 `model_adjust_reason`
- **不得**突破硬过滤(不能把被剔除的 Agent 拉回)
- **不得**校正 `structure_complement` 和 `redundancy_penalty`(机械规则)
- **允许**校正:子问题匹配、任务类型、阶段、职责独特性、用户偏好

模型的角色是**处理"规则对了但语义微妙"的情况**,不是自由判断权。

### 24. 硬过滤只保留 4 条

不做语义扩展,不做模糊匹配:

- **R1**:registry.json 中 `status != registered`
- **R2**:出现在 `--without` 列表
- **R3**:profile 的 `## 不该越界的事`**明确写出**与当前主任务类型冲突
- **R4**:registry.json 中 `default_excluded: true`(如 Trump),除非出现在 `--with`

R3 的原则是"宁可少剔,不错剔",只处理文本明确写出的正面冲突。

### 25. Justin Sun(孙宇晨)作为 `/room` 首个 mode=`debate_room` 试点

13 个原始 skill 的 `mode` 继续保持 `debate_only`。孙宇晨作为 Session 2 新接入的 skill,直接设为 `debate_room`——作为**试点 Agent**,用于验证新协议是否真的可以跨模式使用。

后续如果验证通过,再逐个把 13 个原始 skill 的 mode 升级为 `debate_room`。

### 26. Justin Sun 的 profile 只写在 `.codex/skills/` 一侧

孙宇晨 skill 同时存在 `.codex/skills/justin-sun-perspective/` 和 `.claude/skills/justin-sun-perspective/` 两份副本。`roundtable-profile.md` 只写在 `.codex` 侧作为权威位置,`.claude` 侧不补——**避免双权威冲突**,未来注册表扫描路径也优先认 `.codex`。

### 27. `/room` 当前阶段**仍然不做**的事(再次强调)

- 不做聊天室 UI 原型
- 不做状态持久化(persistent room 落盘机制)
- 不做自动发现扫描脚本(registry.json 目前手工维护)
- 不做 13 个原始 skill 的 mode 升级(等验证完再做)

---

---

## Part III:Session 4 新增锁定的决议

### 28. 议题琐碎度降级规则用 `subproblem_match` 子项差,不用 total 差

Session 3 验证报告原始建议用 `top1.total - top2.total ≥ 15` 作为琐碎度触发条件,但在 Topic B 的实际打分中(Jobs total=52, Feynman total=47),total 差只有 5,根本触发不了。**根因分析**表明:产品类议题因为 task_type_match 的 15 分地板 + stage 直命中 15 分,让多人都能堆出 40+ 的 total,掩盖了「子问题真正命中几 tag」的差异信号。

**锁定决议**:§9.1.1 / E-1.1 的核心触发条件用 **`top1.scores.subproblem_match - 次高子项值 ≥ 8`**,配合另外 3 个硬条件(stage ∈ {converge, decision}、单子问题 tag ≤ 2、topic ≤ 20 字)形成四重合取。

锁定依据:
- Topic B 下 Jobs sub=22 vs 次高 14 = 差 8,恰好触发 ✓
- Topic A(Sun 30 / PG 30 = 差 0)、Topic C(Taleb 22 / Munger 14 = 差 8,但 stage=stress_test 阻断)均不触发
- 用子项差比用 total 差更贴近「子问题匹配度」这个根因,抗堆砌

**不要轻易把阈值降到 ≤ 4**:会开始误降真正二难议题。如果 v0.1.2 验证发现阈值需要调整,先试 ≥ 6,不要直接跳到 ≥ 4。

### 29. 琐碎度降级触发时 roster 只取 top1 单人,不是 top1+1 对冲

Session 3 验证报告给了两种降级形态:
- 方案 A:`roster 只取 top1`(单人花名册)
- 方案 B:`只取 2 人(top1 + 唯一对冲位)`

**锁定方案 A**——**单人**。

锁定依据:
- 琐碎度降级的目的是填补**陪跑 20%** 场景,陪跑的本质是「单一专家快速咨询」,加对冲位就背离了定位
- 按钮左右 / 命名选择 / 小 UI 调整这类议题,Jobs 直接回答远比 Jobs+Feynman 讨论更有价值
- 2 人方案会让主持器仍要做「让谁先说」「2 人是否冲突」的调度,成本反而没降
- 如果真的需要对冲,议题应该走常规 4 人流程

### 30. Room Architecture 采用「首节先锁,主体后补」的分阶段策略

Session 4 本应在 Phase 2 主体写完整个 `docs/room-architecture.md`,但 FINDING #6 只需要「状态所有权」这一小部分就能解除阻塞。**决议**:Session 4 只写 §1-§4(4 个运行时字段所有权),§5-§9 留为 Phase 2 完整写作时的占位章节。

锁定依据:
- FINDING #6 的根因是「silent_rounds 没有维护方」,只需最小文档就能解决
- 把整个 architecture 文档压到 Session 4 会让文档写得仓促、未经验证
- Phase 2 主体写作需要先跑 Phase 1.5 回归验证,Session 4 无法兼顾
- 分阶段交付避免「一次性大爆炸」,每阶段都能验证

**约束**:Phase 2 展开 §5-§9 时,**不允许**修改或删除 §1-§4。§1-§4 是与 `prompts/room-selection.md` 签订的正式契约,改动需要同步修 policy + prompt 两处。

### 31. Selection prompt 是纯消费者,所有状态由 orchestrator 维护

这是 Session 4 为了解除 FINDING #6 而**显式写进 room-architecture.md §3 的不变量**:

- **selection prompt 不持有任何状态**,每次调用都是无记忆的
- **orchestrator 是状态的唯一写者**——`silent_rounds` / `last_stage` / `turn_count` / `recent_log` 的增量更新责任全部在 orchestrator
- **状态传递每轮都完整重发**,不做差量

锁定依据:
- 这是一个「设计不变量」,而非功能决策。必须在所有后续 prompt(room-chat / room-summary / room-upgrade)设计时遵守
- 如果允许 prompt 写状态,会出现多写者冲突,状态来源追溯困难

### 32. `silent_rounds` 在 `/remove` 时删除键,不是保留 0

- `/remove <agent>` 时,orchestrator 从 `silent_rounds` Map 中**删除该 agent 的键**
- 不是保留 `silent_rounds[agent] = 0`

锁定依据:保留键会让 selection prompt 的强制补位逻辑可能在已移除的 agent 上误触发,破坏状态一致性。键的存在即表示「该 agent 仍在 roster 中」。

### 33. `silent_rounds` 的计数与豁免解耦

强制补位的豁免条件(`stage=decision` + agent.stage_fit 不含 decision)**只影响本轮是否被强制补位**,**不影响 `silent_rounds` 本身的累加**。

锁定依据:如果豁免期间计数器暂停,stage 切换回来后计数会失真,无法反映累计沉默状态,破坏规则的「连续 N 轮」语义。

### 34. `recent_log` 总量硬顶 500 token

锁定上限 500 token(约 750-1000 字符),超出由 orchestrator 执行「保留最后 1 轮完整 + 前 2 轮重压缩」策略。

具体压缩算法**不在 room-architecture.md 定义**,留给 Phase 4 的 room-chat prompt 或 summary prompt 实现。

### 35. Phase 1.5(回归验证)被追加为 Session 5 第一步

Session 4 只修补了规则和状态层,**没有在真实 LLM 上跑一次**。决议:Session 5 必须先做 Topic B 回归验证,确认 §9.1.1 / E-1.1 真的被 LLM 按预期触发。如果没触发,必须先修 prompt 描述,再进 Phase 2 主体。

**不允许跳过这一步直接写 Phase 2 主体**——原因与 Session 3 当初拒绝跳验证相同。

---

## Part IV:Session 5 新增锁定的决议

### 36. 主持器 = 混合模式(规则引擎 + 关键节点 LLM)

Q1 决议。主持器(orchestrator)**不是**纯 LLM call 每轮调用,也**不是**纯确定性规则引擎。而是混合:

- **日常运行时(每轮)**:规则引擎跑状态检查、计数器更新、刻度监控(silent_rounds / turn_count / token_budget)
- **关键节点**:才调 LLM,主要三处:
  - 发言生成(`room-chat.md`,Phase 4)
  - 阶段总结(`room-summary.md`,Phase 4)
  - 升级判断(`room-upgrade.md`,Phase 4)

锁定依据:
- 纯规则引擎无法做「语义级议题漂移检测」
- 纯 LLM 成本高、飘移大、不稳定
- 混合模式符合 Session 2 决议 8 的「规则打底,模型辅助」原则
- 对 Phase 5 `.codex/skills/room-skill/` 的实现形态定调

写入:`room-architecture.md §9.1`

### 37. conversation_log 采用双轨制(结构化持久 + 压缩运行时)

Q2 决议。`conversation_log`(结构化 Turn[] 数组)与 `recent_log`(压缩文本)**共存不冲突**:

- **`conversation_log`**:权威日志,append-only,JSON Turn 对象数组。用于导出、调试、分析、未来回放
- **`recent_log`**:运行时伴生字段,压缩文本 ≤ 500 token,从 `conversation_log.slice(-3)` 机械生成,只喂给 selection prompt 做 stage 判断

两者由 orchestrator 独立维护(承接 Session 4 第 31 条的不变量)。`recent_log` 的压缩算法契约写入 `§5.5.3`,具体实现留给 Phase 4。

v0.2 **不做**持久化——`conversation_log` 仅在内存,承接 Session 2 决议 27「当前阶段不做状态持久化」。

### 38. 砍掉 3 档换人机制,只保留强制补位 + /add + /remove

Q8 决议。Session 1 大报告提的「核心常驻 / 阶段性参与者 / 临时补位者」3 档分层**在 v0.2 明确不做**。

理由:
- Session 1-4 都没落地,说明不是迫切需求
- 现有三件事(§12 强制补位 + /add + /remove + /remove 触发的自动补位)已经覆盖 80% 的换人场景
- 3 档分层引入「半失能状态」,schema 复杂度与价值不对等
- v0.3+ 可以加,不破坏 v0.2 契约(§5.3 `agents` 字段追加 `tier` 字段即可)

写入:`room-architecture.md §8`

### 39. Phase 2 采用 Minimal 策略:核心完整 + 边缘占位

Session 5 Phase 2 主体写作**不追求一次完整交付**。采用 Minimal 策略:

- ✅ **核心完整**:§5 状态字段 / §6 命令(4 个核心:/room / /focus / /add / /remove) / §7 发言机制 / §9 主持器建议规则
- 🟡 **边缘占位**:§6 的 3 个辅助命令(/summary / /upgrade-to-debate / @) / §5.7 upgrade_signal 的完整链路
- ❌ **明确不做**:持久化 / 3 档换人 / 跨房间关联 / 语义级漂移检测 / 用户情绪识别

理由:
- Session 1-4 反复验证「写得越多,悬而未决的东西越多」
- 核心完整就能验证主路径,边缘占位留给 Phase 3/4/5 实现
- 避免 Session 5 写 800 行但其中 400 行是未验证的推测

**约束**:Phase 3/4/5 写作者必须遵守 v0.2 的占位边界,不得声称「补完了占位」就等于「扩展了 v0.2」。补占位 = v0.3。

### 40. v0.1.2 policy 补丁与 Phase 2 捆绑交付

Session 3 剩余 FINDING(#3/#4/#5/#7/#8)+ Session 4 活体回归发现的规则歧义(stage 锚定词、task_type 消歧、role_uniqueness 严格解释)**在 Session 5 一次性打 v0.1.2 补丁**,与 Phase 2 主体**同期交付**。

补丁范围(8 项):
1. §5.3 stage 锚定词表(活体发现)
2. §7.1 地板分 6 → 3(FINDING #5)
3. §7.2 task_type 规则歧义消除(活体发现)
4. §7.4 role_uniqueness 严格解释(活体发现)
5. §9.1 tie-breaker(FINDING #3)
6. §9.2 迭代替换算法明确化 + 5 轮上限(FINDING #8)
7. §9.3 结构平衡第 4 条「≥ 1 offensive/moderate」(FINDING #4)
8. §12 强制补位豁免检查顺序(FINDING #7)

**零破坏**:
- `/debate` 不受影响(protocol 继续只读 roundtable-profile 旧字段)
- §9.1.1 琐碎度降级**不动**(活体验证已通过,动了就要重验证)
- Session 4 第 28 条(用 subproblem_match 子项差)继续生效
- 14 份 profile 的 v0.2 区块不动

**v0.1.2 的 Topic B/D 回归影响**:
- Jobs 的 role_uniqueness 从活体的 15 → 严格解释的 0(更准)
- Jobs total 从活体的 67 → 回归纸面的 52
- 但 subproblem_match 子项仍稳定 22,E-1.1 判定**不变**

---

---

## Part V:Session 6 新增锁定的决议

### 41. handoff_packet 不可回写(/debate → /room 单向交接)

Session 6 Phase 3 新增的硬不变量,写入 `docs/room-to-debate-handoff.md §5.5 Rule 5`。

**决议内容**:`/room → /debate` 的 handoff_packet 交接是**单向漏斗**:

- `/room → /debate`:通过 packet 传递结构化上下文
- `/debate → /room`:**不回传**。`/debate` 的决议是最终产出,不回写 `/room` state

**具体表现**:
- `/debate` 启动后,`/room` 的 `mode` 字段变为 `upgraded`
- `conversation_log` 保留在内存(或持久化存档),作为审计追溯
- `/room` 不再接受新 user_input,进入归档状态
- 用户想基于 `/debate` 决议继续发散 → 必须用新的 `/room <议题>` 重建房间

**锁定依据**:
- 大报告 §29 没有明说这一条,但**防止决议被 /room 后续讨论"覆盖"**是两种模式不互相污染的关键
- 如果允许回写,`/debate` 的**终审性**会被破坏 —— 用户可以通过在 /room 里继续发言"软覆盖"/debate 的结论
- 两个模式必须是**单向漏斗,不是循环**

**对未来的含义**:如果 v0.3+ 需要「决议后继续探索」,应该通过**复制 packet 作为新 room 的 seed**,而不是回写旧 room

### 42. /debate 消费 packet 时必须保留 ≥ 2 人与 suggested_agents 的交集

写入 `docs/room-to-debate-handoff.md §6.3`。

**决议内容**:`/debate` 接收 packet 后,**可以**从 `field_11_suggested_agents` 中减人或追加新人,**但不得**完全无视 `/room` 的建议:

- 最终 `/debate` 的参会名单与 `field_11_suggested_agents` 的交集必须 ≥ 2 人
- 例外:`field_11` 本身为空时,`/debate` 自由选人

**锁定依据**:
- 大报告 §29.8 说「不建议机械沿用」,但没量化
- 如果允许 0 交集,`/debate` 可以完全无视 `/room` 的 8 轮讨论成果,等于白跑 `/room`
- 如果要求全部沿用,又违背了 `/debate` 的自主选人权(§5.3 Rule 3)
- 2 人交集是折中:保留 `/room` 的核心洞察,又给 `/debate` 补人/减人的空间

**可能被未来质疑**:
- 2 是拍的数字,没有数据支撑
- 如果某次 `/debate` 确实不想用任何 `/room` 建议的人(极罕见场景),会被卡住
- v0.3+ 可以考虑按 `/room` 讨论的 token 量动态调整阈值(讨论越多,交集要求越高)

### 43. room-skill 不自动升级,即使 upgrade_signal 触发

写入 `.codex/skills/room-skill/SKILL.md` 结束条件章节。

**决议内容**:主持器规则引擎触发 `upgrade_signal` 后,**不自动**调用 `room-upgrade.md` 打包 packet。必须等用户输入 `/upgrade-to-debate` 确认。

**具体表现**:
- 规则引擎写 `upgrade_signal` 字段(§5.7)
- 向用户显示建议:「主持器建议升级到 /debate」
- 用户继续发普通话 → 视为拒绝建议,`confidence -= 0.1`
- 用户输入 `/upgrade-to-debate` → 进入 Flow F

**锁定依据**:
- **用户控制优先**:升级是重操作,不应被自动化
- 保守的规则引擎可能误判 `reached_decision_stage_with_tension`,自动升级会让用户失去退路
- 对齐 Session 2 决议 9(「/room → /debate 必须通过 handoff packet」)—— packet 是形式,**用户确认是实质**

**可能被未来质疑**:
- 明显需要升级的场景(例如 confidence=1.0 + 连续 3 次触发)也必须手动确认,体验偏差
- v0.3+ 可以考虑「超级明显」时弹窗式确认(而不是文本建议)

### 44. room-summary 的 previous_summary 输入字段是必填项

写入 `prompts/room-summary.md` 输入契约。

**决议内容**:`room-summary.md` 被调用时,orchestrator **必须**传入 `previous_summary`(即上次 summary 产出的 4 字段 + `last_summary_turn`)。第一次 summary 时传空对象但字段不能缺失。

**锁定依据**:
- 这是 **P4 在写 room-summary.md 时反向发现的 architecture gap**:
  - `room-architecture.md §5.6.2` 说 consensus_points 是「追加 + 去重」,tension_points 同样
  - 但如果 summary prompt 不知道 previous 的值,每次产出就是**全量重写**,去重策略完全失效
  - 合并只能在 orchestrator 层后处理,但 orchestrator 是规则引擎,不会做语义去重
- 因此 summary prompt 必须**主动读 previous** 做语义合并,然后 orchestrator 机械写入

**配套变更**:
- `room-summary.md` 输入契约新增 `previous_summary` 字段
- `room-summary.md` 输出新增 `merge_strategy_applied` 监控字段,让 orchestrator 验证策略执行
- `room-skill/SKILL.md` Flow D 显式要求传入 previous_summary

**未来 v0.2 architecture 补丁**:
- `room-architecture.md §5.6.2` 应显式说「由 summary prompt 读 previous + 做语义去重,orchestrator 只做机械写入」
- 本次 Session 6 **不改** architecture(§1-§9 锁死),但本决议已隐式修正
- Session 7 可选择性补 architecture 文字

### 45. room-skill 是状态的唯一写者,4 个 prompt 全部是纯消费者

写入 `.codex/skills/room-skill/SKILL.md` 系统定位章节。**延续 Session 4 第 31 条**,在 Session 6 明确扩展到全部 4 个 prompt。

**决议内容**:

- **唯一状态写者**:`room-skill/SKILL.md`(Phase 5 交付)
- **纯消费者**(不写任何 room state):
  - `prompts/room-selection.md`
  - `prompts/room-chat.md`
  - `prompts/room-summary.md`
  - `prompts/room-upgrade.md`

**具体含义**:
- 每次调用 prompt,orchestrator 传入完整 room state(不做差量)
- prompt 输出的 JSON 不包含任何状态更新指令 —— orchestrator 根据输出**自己决定**如何更新状态
- silent_rounds / last_stage / turn_count / recent_log / conversation_log / consensus_points 等全部由 orchestrator 写

**锁定依据**:
- Session 4 第 31 条本来只针对 selection prompt,Session 5 新增 3 个 prompt 后需要扩展
- 如果允许 prompt 写状态,会出现「多写者冲突」:room-chat.md 写 cited_agents,room-summary.md 写 consensus,两者不一致时不知道信谁
- 单一写者 + 完整重发是最保守、最可追溯的设计

**可能被未来质疑**:
- 完整重发会让每次 prompt 输入的 token 开销增加(特别是 room-summary.md 要传 previous_summary + conversation_log)
- v0.3+ 可考虑差量传递,但必须先设计严格的 merge 协议
- 本次 v0.2 明确不做优化

---

## 如果后续有人想推翻以上决议

必须满足两条:

1. 给出明确的新问题证据
2. 明确说明为什么旧决议不再成立

否则默认以上决议继续生效。
