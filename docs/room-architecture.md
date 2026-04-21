# Room Architecture

> `/room` 模式的**完整架构协议**:房间状态模型 / 命令语义 / 发言机制 / 换人机制 / 主持器职责。
>
> 版本:**v0.2-minimal+p0**(§1-§9 全部完成,采用 Minimal 策略)| 初版:2026-04-11(Session 4 首节)| 完整:2026-04-11(Session 5 主体)| 修订:2026-04-12(Session 8 P0)
> 状态:**§1-§9 全部完成**,命令 `/summary` / `/upgrade-to-debate` / `@<agent>` 为最小占位,完整实现在 Phase 3/4/5

---

## 文档演进历史(v0.1-alpha → v0.2-minimal)

| 版本 | 日期 | 范围 | 交付动机 |
|---|---|---|---|
| **v0.1-alpha** | 2026-04-11(Session 4) | §1-§4(状态所有权)| 修补 FINDING #6 阻塞项。silent_rounds 等 4 个运行时字段的所有权、更新时机、传递路径 |
| **v0.2-minimal** | 2026-04-11(Session 5) | §5-§9(主体完整)| Phase 2 主体交付。采用「Minimal 策略」——核心命令 4 个完整 + 其余 3 个占位,砍掉 3 档换人机制,保留未来扩展空间 |
| **v0.2-minimal+p0** | 2026-04-12(Session 8) | §5.6.2 / §7.2 | P0 补丁:显式写入 previous_summary 必填(决议 44)和 turn_role 由 orchestrator 唯一分配(F8) |

**v0.2 的核心策略**:不追求「完美完整」,追求「可验证的最小可行协议」。每一节都清楚标出**做了什么** / **不做什么** / **未来扩展空间**。

**v0.2 不动的契约**(§1-§4):这 4 章在 v0.1-alpha 已锁,v0.2 **零改动**。任何未来的修订都必须同时修 `room-selection-policy.md` 和 `prompts/room-selection.md`。

---

## §1. 目的与定位

`/room` 是一个**多 Agent 半结构化房间**。与 `/debate` 的「一次性正式圆桌」不同,`/room` 的特征是:

- **持续性**:同一个房间跨多轮用户发言,保留上下文
- **半结构化**:不是自由群聊,但比 `/debate` 宽松,允许随机进出、换人、加减焦点
- **状态驱动**:每一轮的选人和发言决策都依赖「房间当前状态」

「房间状态」是**一个 JSON 对象**,在主持器(orchestrator)层维护,作为所有 prompt 调用的上下文来源。

**定位**:本文档只定义**数据结构和所有权**,不定义:
- 房间命令的语义(`/focus`、`/add`、`/remove` 等) — 留给 Phase 2 §6
- 发言 prompt 的内部流程 — 留给 `prompts/room-chat.md`(Phase 4)
- 主持器的 UI 交互 — 不在本协议范围

---

## §2. 完整房间状态字段清单

下表列出 `/room` 房间的 14 个状态字段。**粗体字段**是 Session 4 本文档**完整定义**的 4 个字段,其余为 Phase 2 占位。

| # | 字段 | 类型 | 所有者 | Session 4 状态 |
|---|---|---|---|---|
| 1 | `room_id` | string | orchestrator | 占位,Phase 2 定义生成规则 |
| 2 | `title` | string | orchestrator | 占位,Phase 2 定义 |
| 3 | `mode` | enum | orchestrator | 占位,候选值 `standard`/`focused`/`upgraded` |
| 4 | `primary_type` | enum(task_type) | selection prompt 写入一次,orchestrator 维护 | 占位 |
| 5 | `secondary_type` | enum(task_type)? | 同上 | 占位 |
| 6 | `agents` | `{agent_id, short_name, structural_role}[]` | selection prompt 写入,orchestrator 维护 | 占位(即 roster) |
| 7 | `agent_roles` | `{[agent_id]: role_text}` | selection prompt 写入 | 占位 |
| 8 | `active_focus` | string? | orchestrator | 占位,`/focus` 命令写入 |
| 9 | `conversation_log` | `Turn[]` | orchestrator | 占位,Phase 2 定义 Turn schema |
| 10 | `consensus_points` | `string[]` | summary prompt 写入 | 占位 |
| 11 | `open_questions` | `string[]` | summary prompt 写入 | 占位 |
| 12 | `tension_points` | `string[]` | summary prompt 写入 | 占位 |
| 13 | `recommended_next_step` | string? | summary prompt 写入 | 占位 |
| 14 | `upgrade_signal` | `UpgradeSignal?` | orchestrator 观察,主持器判定 | 占位 |

---

### §2.1 Session 4 完整定义的 4 个运行时字段

**这 4 个字段不在上表 14 字段列表中**,而是房间状态的**运行时伴生字段**——它们是 selection prompt 和主持器之间**每轮交换**的状态,不需要持久化到房间快照,但必须**正确维护与传递**。

这 4 个字段是 FINDING #6 阻塞项的核心。

| # | 字段 | 类型 | 所有者 | 关联协议 |
|---|---|---|---|---|
| R1 | `silent_rounds` | `{ [agent_id: string]: number }` | **orchestrator** | `room-selection-policy.md §12` 强制补位 |
| R2 | `last_stage` | `enum{explore,simulate,stress_test,converge,decision}` | **orchestrator** | `room-selection-policy.md §5.3` 阶段识别 |
| R3 | `turn_count` | 
umber` | **orchestrator** | 内部计数,用于日志、调试、强制补位窗口判断 |
| R4 | `recent_log` | `CompressedLog` | **orchestrator** | `room-selection-policy.md §3` 输入契约 |

---

## §3. 状态所有权与更新时机(Session 4 核心)

**核心原则**:**selection prompt 是纯消费者**。它不维护任何状态,只读取 orchestrator 传入的 `current_state`,输出决策 JSON。状态的**增量更新责任完全在 orchestrator**。

这一原则写死后,所有「谁该更新 silent_rounds」这类疑问都有唯一答案:**orchestrator**。

### §3.1 silent_rounds — 连续沉默计数器(R1)

**语义**:`silent_rounds[agent_id] = n` 表示 `agent_id` 已经**连续 
` 轮**未被选入 `speakers` 名单,即使他仍在 `roster` 中挂名。

**数据结构**:
```json
{
  "silent_rounds": {
    "taleb": 0,
    "munger": 2,
    "zhang-yiming": 1
  }
}
```

**所有者**:**orchestrator**。selection prompt 只读。

**初始化**:
- `room_full` 建房时,对所有入选 roster 的 agent 初始化为 `0`
- `/add` 加入花名册的 agent,初始化为 `0`

**更新时机**(关键规则):

每次 `room_turn` 选人**产出 speakers 列表后**,orchestrator 执行以下算法:

```
for each agent in roster:
    if agent in speakers:
        silent_rounds[agent] = 0        # 入选者清零
    else:
        silent_rounds[agent] += 1        # 未入选者累加
```

**注意**:计数器**只在 `room_turn` 流程完成后更新**,不在 `room_full` 或 `roster_patch` 中动。

**传递路径**:

下一次 orchestrator 调用 selection prompt(`room_turn` 模式)时,把最新的 `silent_rounds` 写入 `current_state.silent_rounds`,作为 `room-selection-policy.md §12` 强制补位规则的输入。

**清零规则**(强制补位后):
- 当强制补位触发并把某 agent 塞进 speakers 时,该 agent 的 `silent_rounds` 在**本轮结束时**按上面的更新规则自动归零(因为他被选入了 speakers)。
- 不需要额外的「强制补位后清零」特例。

**移除规则**:
- `/remove <agent>` 执行时,orchestrator 从 `silent_rounds` 中**删除该 agent 的键**,而不是留 0。这样 selection prompt 就不会在已移除的 agent 上跑强制补位逻辑。

**豁免与计数的关系**(避免混淆):
- `room-selection-policy.md §12` 豁免条件(stage=decision + agent.stage_fit 不含 decision)**不影响** `silent_rounds` 的累加。豁免只影响**本轮是否被强制补位**,不影响计数器本身。这保证豁免期结束后(stage 切换回来),沉默计数能准确反映累计状态。

**给主持器的实现建议**(非强制):
```
每轮完成后:
  orchestrator.updateRoomState(room_id, {
    silent_rounds: computeSilentRounds(roster, speakers, previous_silent_rounds),
    turn_count: turn_count + 1,
    last_stage: parsed_topic.stage,
    recent_log: compress(last_3_turns)
  })
```

---

### §3.2 last_stage — 上轮阶段识别(R2)

**语义**:上一次 selection prompt 输出的 `parsed_topic.stage`,作为**本轮阶段判定的参考基准**。

**数据结构**:
```json
{ "last_stage": "simulate" }
```

**所有者**:**orchestrator**。

**初始化**:`room_full` 建房后,从 selection prompt 输出 `parsed_topic.stage` 读取并存储。

**更新时机**:每次 `room_turn` 完成后,orchestrator 把本轮 selection prompt 输出的 `parsed_topic.stage` 写回 `last_stage`。

**传递路径**:下一次 `room_turn` 调用时,把 `last_stage` 作为 `current_state.last_stage` 传入,让 selection prompt 知道「上一轮我们在哪个阶段」。

**用途**:
1. selection prompt 可以参考 `last_stage` 做「阶段切换是否合理」的判断(当前未强制,但 Phase 2 可能会要求)
2. 强制补位豁免规则依赖 `last_stage` 判定当前阶段是否为 `decision`
3. 主持器用它决定是否建议用户 `/focus` 或 `/upgrade-to-debate`

---

### §3.3 turn_count — 累计轮次(R3)

**语义**:房间自建立以来的**完整发言轮数**,用于日志与调试。不是严格业务逻辑字段,但**强制补位的「连续 3 轮」语义依赖它定义「一轮」**。

**数据结构**:
```json
{ "turn_count": 7 }
```

**所有者**:**orchestrator**。

**初始化**:`room_full` 建房后设为 `0`。

**更新时机**:每次 `room_turn` 完成**并成功产出 speakers**后,`turn_count += 1`。

**关键规则**:
- 建房本身(`room_full`)**不算一轮**,`turn_count` 在建房后仍为 0
- `roster_patch`(`/add` / `/remove`)**不算一轮**,不递增
- `/focus` 切换焦点**不算一轮**,只有实际发言后产生的 `room_turn` 才算
- 如果一次 `room_turn` 调用返回错误(`topic_too_vague` 等),**不递增**

**传递路径**:可选写入 `current_state.turn_count`,selection prompt 当前不强制消费,但 Phase 2 可能会用它做「房间已太长,建议升级」的判定。

---

### §3.4 recent_log — 压缩发言日志(R4)

**语义**:最近 3 轮发言的**压缩摘要**,≤ 500 token 总量。供 selection prompt 做阶段判断与议题漂移检测。

**数据结构**:
```json
{
  "recent_log": "Turn 5 (simulate): Sun 提出三种市场结构假设,PG 认为 2 号最可信;Turn 6 (simulate): Taleb 反驳 All in 路径,Munger 支持谨慎试;Turn 7 (converge): 三人就「先做小步试」达成软共识"
}
```

**所有者**:**orchestrator**。

**格式**:
- 纯文本,不是结构化 JSON
- 每轮一行或一段,格式建议:`Turn N (<stage>): <agent1> <观点片段>; <agent2> <观点片段>; ...`
- 总长**硬顶 500 token**(约 750-1000 字符)
- 超出时主持器负责压缩:保留最后 1 轮完整,前 2 轮做更重的摘要

**初始化**:`room_full` 建房后设为空字符串 `""`。

**更新时机**:每次 `room_turn` 产出 speakers 并执行完**实际发言**(由 `room-chat.md` prompt 处理,Phase 4 交付)后,orchestrator:
1. 追加新一轮的摘要到 `recent_log` 末尾
2. 如果超过 3 轮或 500 token,丢弃最早的一轮,重压缩

**传递路径**:作为 `current_state.recent_log` 字段传入 selection prompt。selection prompt 只做**读操作**,不回写。

**Session 4 范围外**:recent_log 的**压缩算法本身**(从完整发言提取 ≤500 token 摘要的规则)不在本文档定义,留给 Phase 4 的 `room-chat.md` 或单独的 summary prompt。本文档只锁定**所有权(orchestrator)** 和**上限(500 token)**。

---

## §4. 状态传递路径(数据流图)

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                             │
│  (持有 room state,负责所有字段的读写)                         │
│                                                                 │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  room_state (persistent)                             │    │
│   │   - 14 个持久字段(§2 表)                           │    │
│   │   - 4 个运行时伴生字段(§2.1 表)                   │    │
│   │     · silent_rounds                                  │    │
│   │     · last_stage                                     │    │
│   │     · turn_count                                     │    │
│   │     · recent_log                                     │    │
│   └──────────────────────────────────────────────────────┘    │
│                          │                                     │
│                          │ 1. 读取 current_state 构造 input   │
│                          ▼                                     │
│            ┌─────────────────────────────┐                    │
│            │   selection prompt          │                    │
│            │  (纯消费者,不写状态)      │                    │
│            │                             │                    │
│            │  输出 JSON:                │                    │
│            │   - parsed_topic.stage      │                    │
│            │   - speakers / roster       │                    │
│            │   - forced_rebalance        │                    │
│            │   - structural_check        │                    │
│            └──────────────┬──────────────┘                    │
│                          │                                     │
│                          │ 2. 消费输出,更新 room_state        │
│                          ▼                                     │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  orchestrator.applySelectionResult(output)           │    │
│   │   - silent_rounds[speaker] = 0                       │    │
│   │   - silent_rounds[roster but not speaker] += 1       │    │
│   │   - last_stage = output.parsed_topic.stage           │    │
│   │   - turn_count += 1(仅 room_turn 成功时)           │    │
│   │   - recent_log = compress(recent_log + new_turn)     │    │
│   └──────────────────────────────────────────────────────┘    │
│                          │                                     │
│                          │ 3. 等待用户下一轮发言               │
│                          ▼                                     │
│                    [next turn]                                 │
└─────────────────────────────────────────────────────────────────┘
```

**关键不变量**(contract):
1. **selection prompt 不持有任何状态**——每次调用都是无记忆的
2. **orchestrator 是状态的唯一写者**——selection prompt 的输出必须经过 orchestrator 才能成为下一轮的输入
3. **状态更新发生在 selection → orchestrator 回路上**,不在 selection prompt 内部
4. **状态传递每轮都完整重发**——不做差量,避免状态不一致

---

## §5. 其他状态字段的详细定义(Phase 2 占位)

以下字段只有简短占位描述,等 Phase 2 `docs/room-architecture.md` 主体写作时展开。

### §5.1 room_id / title / mode

#### room_id

**生成规则**:`room_{unix_timestamp_ms}_{random4}`,例:`room_1744368000000_a3f2`

**唯一性范围**:同一用户 session 内唯一。v0.2 不做跨 session 唯一性。

**可读性**:不是对用户展示的 ID,主要用于 orchestrator 内部状态查找。用户看到的是 title。

#### title

**来源**:**自动从 topic 抽取**,不由用户提供。

**抽取规则**(v0.2-minimal):
- 取 `topic` 前 20 字符作为 title
- 超过 20 字符则截断 + 末尾加「…」
- 换行符替换为空格

**理由**:用户建房时只输入 topic(议题本身),再让他额外输入 title 是多余的负担。自动抽取足够用。

**更新时机**:建房时写一次,之后**不变**。即使用户 `/reframe` 换主题,title 也保留原样作为历史标识(可以手动改,v0.3+)。

#### mode(房间级)

**候选值**(enum):

| 值 | 含义 | 触发 |
|---|---|---|
| `standard` | 标准房间 | `/room` 建房默认 |
| `focused` | 进入了 `/focus` 子焦点 | 用户执行 `/focus <子问题>` |
| `upgrading` | 准备升级到 `/debate` | 主持器建议 `/upgrade-to-debate` 且用户确认 |

**状态转移**:

```
standard ──/focus──> focused
focused  ──/unfocus──> standard
standard ──/upgrade-to-debate──> upgrading ──> (交接给 /debate,room 归档)
focused  ──/upgrade-to-debate──> upgrading
```

**约束**:
- `upgrading` 是**终态**,房间不会从 upgrading 回到 standard(走了就走了)
- `focused` 可以**嵌套**?**v0.2 不允许**。进入 focus 时如果已经在 focus,先退出上一级再进下一级(`/unfocus` 然后 `/focus`)

---

### §5.2 primary_type / secondary_type

**来源**:`room_full` 建房时 selection prompt 输出的 `parsed_topic.main_type` / `secondary_type`。

**所有者**:orchestrator 写入,之后只读,**不再变化**(v0.2)。

**能否中途变化?** v0.2 **不允许**中途变化。

**理由**:
- 中途变主类型等于「换议题」,这种场景应该通过 `/room` 建**新房间**来处理,而不是在现房间里偷换概念
- 保持 primary_type 不变也能让 selection prompt 在 `room_turn` 模式下有稳定锚点
- `/reframe` 命令在 v0.2 **不实现**,留给 v0.3+

**Phase 4 影响**:room-chat prompt 每轮都应显式接收 `primary_type`,避免让 LLM 每轮重新判定。

---

### §5.3 agents / agent_roles

#### agents

**数据结构**(与 §2.1 表一致):

```json
{
  "agents": [
    {"agent_id": "justin-sun", "short_name": "Sun", "structural_role": "offensive"},
    {"agent_id": "paul-graham", "short_name": "PG", "structural_role": "offensive"},
    {"agent_id": "munger", "short_name": "Munger", "structural_role": "defensive"},
    {"agent_id": "taleb", "short_name": "Taleb", "structural_role": "defensive"}
  ]
}
```

**写入时机**:
- `room_full` 建房后一次性写入(复用 selection prompt 的 roster)
- `/add` / `/remove` 触发增量更新

**structural_role 定义**:
- `offensive` / `defensive` / `moderate` — 只表示 profile 的 `tendency`
- `grounded` / `dominant` / `abstract` 等表达风格属于 profile 的 `expression`,**不得**混入 `structural_role`
- 如果一个 agent 同时表现出防守倾向和 grounded 表达(例如 Munger),`structural_role` 仍写 `defensive`; grounded 只用于 `expression` / grounded_count 判断

#### agent_roles

**数据结构**:`{ [agent_id: string]: string }` —— 每个 agent 在**本房间的长期角色描述**。

**示例**:

```json
{
  "agent_roles": {
    "justin-sun": "本房间的市场结构与 All in 决策主力,负责推演 winner-takes-all 场景",
    "paul-graham": "切口真假判断与早期信号识别",
    "munger": "机会成本与自欺审查,防止 Sun 的激进倾向",
    "taleb": "尾部风险与不可逆损失对冲"
  }
}
```

**所有者**:orchestrator

**写入时机**:**静态**——`room_full` 建房时由 selection prompt 的 `roster[i].role` 字段一次性写入,**之后不刷新**。

**不做动态刷新的理由**(DECISIONS-LOCKED 第 38 条的前半):
- 动态刷新需要每次 `/focus` 切换时重跑 selection,成本高
- 长期角色稳定可以让用户建立对「这个房间里谁是什么人」的预期
- 单轮发言的**临时角色**(primary/support/challenge/synthesizer)是动态的(在 §5.5.speakers[i].role 里),这才是「本轮职责」——区分了「长期角色」和「本轮角色」

**`/focus` 对 agent_roles 的影响**:无。只影响 `active_focus` 字段和下一轮 `room_turn` 的选人评分,不改写 agent_roles。

---

### §5.4 active_focus

**语义**:用户通过 `/focus <子问题>` 显式聚焦的子问题文本。

**数据结构**:`string | null`

**示例**:
- 
ull` — 房间未进入 focus 模式,讨论主议题全部
- `"技术可行性是否成立"` — 用户让房间聚焦在这个子问题上

**所有者**:orchestrator

**写入时机**:
- 建房时默认 
ull`
- `/focus <text>` 写入该 text,同时 `mode` 从 `standard` 转 `focused`
- `/unfocus` 或 `/focus clear` 写入 
ull`,`mode` 回 `standard`

**对下游的影响**:
- selection prompt 下一次 `room_turn` 调用时,如果 `active_focus != null`,应该把它当作**当前议题的子问题焦点**,对只涉及该 focus 的子问题的 Agent 加分(v0.2 暂不严格实现,留给 v0.1.3 补丁)
- room-chat prompt(Phase 4)应该让 speaker 围绕 focus 发言

**与 stage 的绑定关系**(v0.2 决议):**focus 和 stage 是独立的**。进入 focus 不强制重置 stage 为 explore。用户可以在一个 decision stage 的房间里 `/focus` 到某个子问题继续做决策,或者在 explore 阶段 `/focus` 到子问题继续发散。**focus 只限定范围,不限定阶段**。

**嵌套 focus**:v0.2 **不允许**。进入 focus 时如果已经在 focus,必须先 `/unfocus` 再 `/focus`。原因见 §5.1 mode 转移规则。

**退出 focus 的触发条件**:
- 用户显式 `/unfocus`
- 用户新建另一个房间(当前房间归档)
- 升级到 `/debate`(mode 转 `upgrading`,focus 自动清空)

### §5.5 conversation_log

**语义**:房间自建立以来的**完整结构化发言历史**,append-only。`conversation_log` 是**权威日志**,`recent_log`(§3.4)是基于它的滚动压缩视图。

**数据结构**:

```json
{
  "conversation_log": [
    {
      "turn_id": 1,
      "timestamp": "2026-04-11T10:23:45Z",
      "stage": "simulate",
      "active_focus": null,
      "user_input": "那 All in 的话具体路径是什么",
      "speakers": [
        {
          "agent_id": "justin-sun",
          "short_name": "Sun",
          "role": "primary",
          "content": "All in 的第一步是单点打穿..."
        },
        {
          "agent_id": "paul-graham",
          "short_name": "PG",
          "role": "support",
          "content": "Sun 说的单点打穿是对的,但切口要再窄一级..."
        },
        {
          "agent_id": "taleb",
          "short_name": "Taleb",
          "role": "challenge",
          "content": "即使单点打穿,也要先算最坏情况的退出成本..."
        }
      ],
      "cited_agents": ["justin-sun"],
      "tokens_used": 1280,
      "forced_rebalance": null
    }
  ]
}
```

**字段详细定义**:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `turn_id` | integer | ✓ | 从 1 起递增,与 `turn_count`(§3.3)同步。turn_id 是持久的轮次标识,turn_count 是运行时计数器,两者同值 |
| `timestamp` | ISO 8601 string | ✓ | orchestrator 写入时间戳 |
| `stage` | enum | ✓ | 本轮的 stage,应与 selection prompt 输出的 `parsed_topic.stage` 一致 |
| `active_focus` | string \| null | ✓ | 本轮的焦点子问题。
ull` 表示未聚焦 |
| `user_input` | string | ✓ | 触发本轮的用户发言原文 |
| `speakers` | Speaker[] | ✓ | 本轮实际发言的 2-4 人(硬顶 4,见决议 12) |
| `cited_agents` | string[] | ✓ | 本轮发言中显式引用的其他 agent(用于 §7 的「最多 2 跳」引用规则) |
| `tokens_used` | integer | ✓ | 本轮总输出 token 估计(orchestrator 粗算,用于监控预算) |
| `forced_rebalance` | object \| null | ✓ | 若本轮触发强制补位,记录 `{agent, reason}`,与 §12 对齐 |

**Speaker 子对象**:

| 字段 | 类型 | 说明 |
|---|---|---|
| `agent_id` | string | 候选池 14 个 id 之一 |
| `short_name` | string | 展示用简称 |
| `role` | enum | 本轮发言角色:`primary` / `support` / `challenge` / `synthesizer`(详见 §7.1) |
| `content` | string | 发言正文,80-180 字(软限,详见 §7.3) |

#### §5.5.1 持久化策略(v0.2-minimal)

**当前阶段**:`conversation_log` **只在会话运行时存在于内存**,不写入磁盘。房间关闭后历史丢失。

**决议依据**:Session 2 锁定的「当前阶段不做状态持久化」(决议 27)仍然生效。Phase 2 不破坏这条。

**未来扩展**(v0.3+,不在本次交付):
- 持久化到 `.codex/state/rooms/<room_id>.jsonl`(每 Turn 一行)
- `/room resume <id>` 命令从磁盘恢复
- 但 v0.2 **不做**,Session 2 决议继续生效

#### §5.5.2 与 recent_log(§3.4)的关系

**核心区别**:

| 维度 | `conversation_log`(§5.5,本节) | `recent_log`(§3.4) |
|---|---|---|
| 结构 | 结构化 JSON 对象数组 | 纯文本压缩摘要 |
| 完整性 | 完整历史(所有轮次) | 仅最近 3 轮 |
| 目的 | 权威来源 / 导出 / 调试 | 快速喂给 selection prompt 做 stage 判断 |
| 读者 | orchestrator / 未来的分析工具 | selection prompt / 主持器 |
| 大小 | 累积增长,无上限 | 硬顶 500 token |

**双轨制的理由**(DECISIONS-LOCKED 第 37 条):
- 结构化 log 利于未来导出、分析、回放,但直接喂给 prompt 太冗长
- 压缩 log 省 token,但丢失细节,不能做权威判断
- 两个字段互补,都由 orchestrator 维护,不冲突

#### §5.5.3 压缩算法的契约(recent_log 的计算来源)

`recent_log` 不是 orchestrator 自由编写的,而是**从 `conversation_log` 的最后 3 个 Turn 机械压缩出来的**。

**契约**(不是实现细节,但 Phase 4 的 summary prompt 必须遵守):

- **输入**:`conversation_log.slice(-3)`(最后 3 个 Turn 对象)
- **输出**:`recent_log` 文本,总长 ≤ 500 token

**每轮的压缩模板**:
```
Turn <turn_id> (<stage>): <speaker1_short> <观点片段>; <speaker2_short> <观点片段>; <speaker3_short> <观点片段>
```

**观点片段的长度约束**:每位发言者 15-30 字,总长 3 位 × 25 字 ≈ 75-100 字/轮,3 轮 ≤ 300 字 ≈ 450 token,留 50 token 安全缓冲。

**不在本文档定义**:具体的摘要提取算法(「如何从 180 字发言中挑出 25 字核心观点」)——这是 Phase 4 `room-summary.md` 或独立 summarizer 的工作。本文档只锁定**输入 / 输出契约**。

#### §5.5.4 Token 预算参考

Session 2 未显式锁定 token 预算,Phase 2 在此补齐:

| 类别 | 目标 | 硬顶 |
|---|---|---|
| 单 Turn 总输出(4 speakers × 180 字 × 2 token/字)| 1200-1500 token | 2500 token |
| 每位 speaker 发言长度 | 80-180 字(软限)| 220 字(硬限) |
| 单 Turn 的 `tokens_used` 字段估算 | 总 token × 1.2(含引用开销)| — |
| 超出硬顶的处理 | orchestrator 截断最长发言 + warning |

**预算超支的动作**:
- 单条 speaker 超 220 字 → orchestrator 截断到 220,末尾加「[...]」,在 warning 记录
- Turn 总 token 超 2500 → 同样截断最长发言直到合规
- 连续 3 轮都触发截断 → 主持器建议用户 `/focus` 或 `/upgrade-to-debate`(§9)

### §5.6 consensus_points / open_questions / tension_points / recommended_next_step

这 4 个字段共同构成**房间的「当前共识快照」**,由主持器在关键时刻更新。

#### 字段定义

| 字段 | 类型 | 语义 |
|---|---|---|
| `consensus_points` | `string[]` | 房间内已经达成的共识条目 |
| `open_questions` | `string[]` | 仍然悬而未决的问题,需要后续轮次回答 |
| `tension_points` | `string[]` | Agent 之间的分歧点,已明确但未收敛 |
| `recommended_next_step` | `string \| null` | 主持器给用户的下一步建议 |

**示例**:

```json
{
  "consensus_points": [
    "独立开发者 AI 工具这个切口确实存在真实需求",
    "如果要做,起点应该是单一高频场景"
  ],
  "open_questions": [
    "All in 的启动资金规模是 6 个月还是 12 个月?",
    "冷启动的获客渠道从哪里开始?"
  ],
  "tension_points": [
    "Sun 主张 All in,Munger/Taleb 认为应保留 50% 储备应对尾部"
  ],
  "recommended_next_step": "建议先用 2 周做最小可运行原型,再根据第 1 个真实用户反馈决定是否 All in"
}
```

#### §5.6.1 更新时机(v0.2-minimal)

**Minimal 策略**:**只在用户执行 `/summary` 命令时更新**,不做每轮自动更新。

**理由**:
- 每轮自动更新需要额外 LLM call(Q1 的混合模式里,主持器是规则引擎,不是每轮 LLM)
- 用户显式触发能精准控制「什么时候需要盘点」
- v0.3+ 可以改为「每 3 轮自动盘点 + 阶段切换时自动盘点」

#### §5.6.2 覆盖 vs 追加策略

**输入契约(v0.1.3 / 决议 44)**:

每次调用 `room-summary.md` 时,orchestrator 必须传入 `previous_summary`。首次 summary 也必须传,但 4 个数组为空、`recommended_next_step = null`、`last_summary_turn = null`。`previous_summary` 缺失属于 orchestrator 错误,summary prompt 不应自行猜测历史状态。

**consensus_points / tension_points**:**追加 + 去重**

每次 `/summary` 把新达成的共识**追加**到数组末尾,但如果新条目和已有条目语义重复(由 summary prompt 判定),**合并**成一条而不是重复。

**open_questions**:**替换式更新**

每次 `/summary` 重新生成完整的 open_questions 数组(旧的问题如果已被回答就移除,新问题加入)。不保留历史「已回答」的问题。

**recommended_next_step**:**完全覆盖**

每次更新就是新的建议。历史建议不保留。

#### §5.6.3 写入者

**所有者**:orchestrator(通过调用 Phase 4 的 `room-summary.md` prompt)

**流程**:
1. 用户发 `/summary`
2. orchestrator 把 `conversation_log`(或最近 N 轮)喂给 `room-summary.md`
3. summary prompt 输出 4 个字段的新值
4. orchestrator 按上面的合并策略更新 room state

`room-summary.md` 本体不在 Phase 2 交付,是 Phase 4 的任务。本文档只锁定**写入者 + 策略**。

#### §5.6.4 读者

- 主持器(决定是否建议 `/upgrade-to-debate`,见 §9)
- room-upgrade prompt(Phase 4)—— upgrade 时把这 4 个字段打包进 handoff packet 传给 `/debate`
- 用户(可以通过 `/status` 或 `/summary show` 查看,v0.2 不实现专门命令)

---

### §5.7 upgrade_signal

**语义**:主持器判定「这个议题应该升级到 `/debate`」时写入的信号对象。

**数据结构**(v0.2-minimal):

```json
{
  "upgrade_signal": {
    "triggered_at_turn": 12,
    "reason": "reached_decision_stage_with_tension",
    "tension_unresolved": true,
    "confidence": 0.8,
    "handoff_ready": false
  }
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `triggered_at_turn` | integer | 第几轮被触发 |
| `reason` | enum | 触发原因代码(见下) |
| `tension_unresolved` | boolean | 是否仍有未收敛的 tension_points |
| `confidence` | float 0-1 | 主持器对升级建议的置信度 |
| `handoff_ready` | boolean | handoff packet 是否已打包完成 |

**触发原因 enum**(Phase 2 初版,v0.3+ 可扩):

| reason | 含义 |
|---|---|
| `reached_decision_stage_with_tension` | 到了 decision 阶段但仍有张力点未收敛 |
| `forced_rebalance_repeated` | 连续 2 轮触发强制补位(§12)—— 意味着正常单轮选人不够 |
| `token_budget_repeatedly_exceeded` | 连续 3 轮 Turn 总 token 超 2500 硬顶 |
| `user_explicit_request` | 用户主动 `/upgrade-to-debate` |

**触发后的动作**:

1. 主持器检测条件 → 写 upgrade_signal(不直接升级,只**建议**)
2. 在用户界面提示:「当前讨论可能需要升级到 `/debate` 正式决议,输入 `/upgrade-to-debate` 确认」
3. 用户输入 `/upgrade-to-debate` → 调用 `room-upgrade.md` prompt(Phase 4)打包 handoff packet → `handoff_ready = true`
4. handoff packet 交给 `/debate` skill → 房间 mode 转 `upgrading` → 归档

**handoff packet 的 schema**:不在本文档定义,留给 `docs/room-to-debate-handoff.md`(Phase 3 交付)。本文档只锁定 **upgrade_signal 作为触发器**。

**v0.2-minimal 的落地范围**:
- ✅ 本文档定义 upgrade_signal 字段 + 4 种触发 reason
- ✅ 主持器的规则引擎实现前 3 种自动触发(§9)
- ❌ **不做** `room-upgrade.md` prompt(Phase 4)
- ❌ **不做** `room-to-debate-handoff.md` 协议(Phase 3)
- ❌ **不做** `/upgrade-to-debate` 命令的完整实现(Phase 5)

**现状**:v0.2 只做**信号的存在和触发条件**,不做**升级的完整链路**。这足以让 §9 主持器职责能写完整,不会因为缺接口而悬空。

---

## §6. 命令语义表

**v0.2-minimal 交付范围**:本节**完整定义 4 个核心命令**(`/room` / `/focus` / `/add` / `/remove`),另 3 个命令(`/summary` / `/upgrade-to-debate` / `@<agent>`)提供**最小占位**,完整实现在 Phase 4/5。

每个命令的定义格式:**输入 → 前置检查 → 状态副作用 → 输出 → 错误情况**。

---

### §6.1 `/room <议题>` 建房(核心)

**输入**:`topic` 文本(议题原文)

**前置检查**:
- `topic.length ≥ 10`(< 10 字符 → 错误 `topic_too_vague`,见 room-selection-policy.md §13)
- 当前无活跃房间,或用户显式允许多房间并存(v0.2 默认单房间,建新房自动归档旧房)

**状态副作用**:

1. orchestrator 生成 `room_id`(§5.1 规则)
2. 生成 `title`(§5.1 抽取规则)
3. 调用 `room-selection.md` prompt 的 `room_full` 模式,传入 `topic`
4. 从 selection 输出填充:
   - `primary_type` / `secondary_type` ← `parsed_topic.main_type` / `secondary_type`
   - `agents` ← `roster`(含 agent_id / short_name / structural_role)
   - `agent_roles` ← `roster[i].role`(写一次,之后不变)
5. 初始化运行时字段:
   - `silent_rounds = {}`(每个 roster 成员初始化为 0)
   - `last_stage = parsed_topic.stage`
   - `turn_count = 0`
   - `recent_log = ""`
   - `conversation_log = []`
6. 初始化 summary 字段:
   - `consensus_points = []`,`open_questions = []`,`tension_points = []`,`recommended_next_step = null`
7. 初始化 `active_focus = null`,`mode = "standard"`,`upgrade_signal = null`

**输出**:
- 房间初始化完成的确认消息 + roster 展示 + 每人 role 简介
- 如果 selection prompt 触发 `trivial_topic_downgrade`(§9.1.1):单人房间 + warning 展示

**错误情况**:
- selection prompt 返回 `topic_too_vague` / `all_filtered_out` / 
o_qualifying_roster` → 向用户展示错误 + 建议
- `--with` / `--without` 冲突 → 要求用户调整约束

**示例**:
```
> /room 我想做一个面向独立开发者的 AI 工具,这个方向值不值得 All in?
< 房间已开启:"我想做一个面向独立开发者的 AI 工具…"
  参会者(4 人):
    - Sun (offensive) - 市场结构与 All in 判断位
    - PG (offensive) - 切口真假与市场时机判断
    - Munger (defensive) - 机会成本与自欺审查
    - Taleb (defensive) - 尾部风险与不可逆损失对冲
  发言,或用 /focus / /add / /remove / /summary
```

---

### §6.2 `/focus <子问题>` 切换焦点(核心)

**输入**:`focus_text` 字符串,描述要聚焦的子问题

**前置检查**:
- 存在活跃房间
- `mode != "upgrading"`(升级中的房间不允许 focus)
- `mode != "focused"` OR 用户先执行了 `/unfocus`(v0.2 不允许嵌套)
- `focus_text.length ≥ 5`(避免空聚焦)

**状态副作用**:

1. `active_focus = focus_text`
2. `mode = "focused"`
3. **不**重跑 selection prompt(focus 不改变 roster)
4. **不**重置 silent_rounds / turn_count / conversation_log

**输出**:确认 focus 生效 + 下一轮发言将围绕该子问题

**错误情况**:
- 已在 focus 中 → 提示用户先 `/unfocus`
- focus_text 过短 → 提示补充描述

**`/unfocus` 逆操作**:
- `active_focus = null`
- `mode = "standard"`
- 其他状态不动

---

### §6.3 `/add <agent_short_name>` 加入花名册(核心)

**输入**:agent 的 `short_name`(例如 `Taleb`)或 `agent_id`(例如 `taleb`)

**前置检查**:
- 存在活跃房间
- agent 在候选池 14 人中(否则 `invalid_agent`)
- agent 不在当前 roster 中(否则 `already_in_roster`)
- `mode != "upgrading"`

**状态副作用**:

1. 调用 `room-selection.md` 的 `roster_patch` 模式,action=add,target=agent
2. selection prompt 跑硬过滤 R1+R2+R4(注意:**R3 non_goals 检查不做**——用户显式 /add 视为越界许可)
3. 如果通过:
   - `agents.push(new_agent_entry)`
   - `agent_roles[agent_id] = <role_from_selection>`(selection prompt 应该生成一个针对本议题的 role)
   - `silent_rounds[agent_id] = 0`(初始化)
4. 如果 `roster.length > 8`:orchestrator **只警告,不拒绝**(Session 2 决议 12)

**输出**:确认加入 + 新人简介 + 警告(如果超软顶 8)

**错误情况**:
- agent 被 R4 过滤(例如 Trump 无 `--with`)→ 提示用户需要显式 `--with`
- agent 被 R2 过滤(在 `--without`)→ 矛盾,拒绝

**R3 豁免说明**:
用户主动 `/add` 视为「我知道他的非目标范围,但我想听他说」的显式授权。例如 `/add taleb` 到一个 UX 决策议题——taleb 的 profile 写了不主做 UX 裁判,但用户 `/add` 后,他**可以**加入 roster,但应该在 agent_roles 里标注「用户显式 override 了 non_goals,可能给出非典型视角」。

---

### §6.4 `/remove <agent_short_name>` 移出花名册(核心)

**输入**:agent 的 `short_name` 或 `agent_id`

**前置检查**:
- 存在活跃房间
- agent 在当前 roster 中(否则 
ot_in_roster`)
- 移除后 `roster.length ≥ 2`(否则 `roster_too_small`,拒绝)
- `mode != "upgrading"`

**状态副作用**:

1. 从 `agents` 数组中移除对应条目
2. 从 `agent_roles` 中**删除该 agent_id 的键**
3. **从 `silent_rounds` 中删除该 agent_id 的键**(DECISIONS-LOCKED 第 32 条)
4. 跑一次 §9.3 结构平衡检查:
   - 如果仍然平衡 → 完成
   - 如果失衡 → orchestrator **自动补位 1 人**(调用 selection prompt `roster_patch` add 模式,挑分数最高的缺失位)
   - 如果无人可补 → 仅 warning,不拒绝

**输出**:确认移除 + 如果自动补位则展示补位者 + 如果失衡未补则警告

**错误情况**:
- 移除后少于 2 人 → 拒绝,提示用户先 `/add` 其他人再 /remove
- agent 不在 roster → 提示检查 short_name

---

### §6.5 `/summary` 触发主持器总结(占位,Phase 4 完整实现)

**v0.2 的最小行为**:
- 触发调用 `room-summary.md` prompt(Phase 4 交付)
- prompt 输入:`conversation_log` 最近 3-5 轮
- prompt 输出:4 个 summary 字段的新值(§5.6)
- orchestrator 按 §5.6.2 的覆盖 vs 追加策略更新 room state
- 向用户展示更新后的 consensus/tensions/next_step

**v0.2 不做**:
- `/summary show`(展示当前 summary 字段但不重算)—— 留给 v0.3
- 自动阶段切换时触发 summary —— 留给 v0.3
- 跨 focus 的 summary 合并 —— 留给 v0.3

---

### §6.6 `/upgrade-to-debate` 升级(占位,Phase 3+4+5 完整实现)

**v0.2 的最小行为**:
- 检查 `upgrade_signal != null`(主持器必须先建议过,或者用户强制触发)
- 如果 `upgrade_signal == null` 且用户强制:`upgrade_signal.reason = "user_explicit_request"`
- 调用 `room-upgrade.md` prompt(Phase 4)打包 handoff packet —— **v0.2 不实现**
- `mode = "upgrading"`
- 房间归档

**v0.2 不做完整升级链路**,只做:
- ✅ mode 转 `upgrading`
- ✅ 显示「升级建议已记录,完整升级功能在 Phase 3 落地」
- ❌ 实际打包 handoff packet
- ❌ 实际交给 `/debate`

---

### §6.7 `@<agent>` 点名发言(占位,Phase 4 完整实现)

**v0.2 的最小行为**:
- 用户在普通发言中出现 `@<short_name>`,例如 `@Taleb 你觉得呢?`
- orchestrator 识别 @ 后的 agent short_name
- 下一轮 `room_turn` 调用时,把该 agent 写入 `user_constraints.mentions`,并在 selection 输出的 `parsed_topic.constraints.mentions` 中回显
- selection prompt 把 `user_constraints.mentions` 视为 `protected_speakers` 硬约束处理 —— 该 agent 必须入本轮

**v0.2 的限制**:
- @ 只影响下一轮的 speakers,不改 roster
- @ 不能突破硬过滤 R3/R4(如果 agent 被硬过滤,@ 也召不回)
- @ 可以突破单轮 4 人硬顶 —— **v0.2 不实现此突破**,硬顶保持 4 人,被 @ 者替换掉原 top 4 中分数最低的非 protected speaker
- 不能同时 @ ≥ 2 人触发琐碎度降级豁免 —— v0.2 的 E-1.1 豁免规则沿用 room-selection-policy.md §9.1.1 的既有定义

**v0.2 不做的 @ 功能**:
- @ 突破单轮硬顶(例如 5 人发言)—— Phase 4
- @<非花名册成员>(让路人入场)—— Phase 4
- @all —— Phase 4

---

### §6.8 命令速查表

| 命令 | v0.2 状态 | 主要状态副作用 |
|---|---|---|
| `/room <topic>` | ✅ 完整 | 初始化所有 room state 字段 |
| `/focus <text>` | ✅ 完整 | `active_focus` / `mode=focused` |
| `/unfocus` | ✅ 完整 | `active_focus=null` / `mode=standard` |
| `/add <agent>` | ✅ 完整 | `agents` / `agent_roles` / `silent_rounds` |
| `/remove <agent>` | ✅ 完整 | 上三字段 + 可能触发补位 |
| `/summary` | 🟡 占位 | 触发 Phase 4 prompt,更新 §5.6 四字段 |
| `/upgrade-to-debate` | 🟡 占位 | `mode=upgrading`,完整链路 Phase 3 |
| `@<agent>` | 🟡 占位 | `constraints.mentions`,Phase 4 完整 |

---

---

## §7. 发言机制协议

本章定义**每一轮 room_turn 里,被选中的 2-4 位 speaker 如何发言**。selection prompt 负责**选谁**,本章定义**怎么说**。

本章只定义**协议**(角色、上限、约束、规则),**不定义**具体 prompt 实现——后者由 Phase 4 `prompts/room-chat.md` 交付。

---

### §7.1 4 类发言角色

每位 speaker 在**本轮**被分配一个角色,写入 `conversation_log.speakers[i].role`(§5.5)。这是**本轮角色**,与 §5.3 的**长期角色**(agent_roles)不同。

#### primary(主讲)

**职责**:对当前议题 / 焦点做**正面主张**。提出立场 + 最核心的论据。

**数量**:每轮**恰好 1 人**。

**选取规则**:`room_turn` 输出的 speakers 中,**TotalScore 最高者**自动担任 primary。

#### support(支持)

**职责**:**补强** primary 的论据,从另一个角度提供证据、案例、或延伸。

**数量**:每轮 **0-1 人**。

**选取规则**:speakers 中,与 primary 的 `structural_role` **相同**(都 offensive 或都 defensive)且 TotalScore 第二高者。

#### challenge(挑战)

**职责**:对 primary 的主张**提出反对或怀疑**,基于不同角度(例如 downside / tail_risk / 可行性)。

**数量**:每轮 **0-1 人**。

**选取规则**:speakers 中,与 primary 的 `structural_role` **相反**(primary offensive → challenge defensive)且 TotalScore 最高者。

#### synthesizer(综合)

**职责**:在 primary / support / challenge 发言后,**综合三方观点**,提出「考虑到 X 和 Y,下一步应该…」式的**收拢建议**。

**数量**:每轮 **0-1 人**,仅当 speakers ≥ 3 时才需要 synthesizer。

**选取规则**:speakers 中,剩余最后一人(不是 primary / support / challenge 任一角色)。优先选 `expression=grounded` 或 `expression=abstract` 的 agent。

---

### §7.2 角色分配算法(单轮 2-4 人的完整路径)

**输入**:selection prompt 输出的 `speakers[]`(2-4 人,已排序)

**责任边界(v0.1.3 / F8)**:
- `room-selection.md` 只负责选出并排序 `speakers[]`,不得写入 `turn_role`
- orchestrator 是 `turn_role` 的唯一分配者,必须按本节算法把 `primary/support/challenge/synthesizer` 写入 speakers 后再调用 `room-chat.md`
- `room-chat.md` 只消费已分配的 `turn_role`,不得重新分配或修改

**算法**:

```
if len(speakers) == 2:
    speakers[0].role = "primary"
    if speakers[1].structural_role != speakers[0].structural_role:
        speakers[1].role = "challenge"
    else:
        speakers[1].role = "support"
    # 无 synthesizer(2 人不需要综合)

elif len(speakers) == 3:
    speakers[0].role = "primary"
    # 挑 challenge 位(结构相反且最高分)
    challenger_idx = find_first_opposite_structural_role(speakers, primary=0)
    if challenger_idx is not None:
        speakers[challenger_idx].role = "challenge"
        # 剩下那位当 synthesizer(不强制 grounded)
        remaining_idx = {1, 2} - {challenger_idx}
        speakers[remaining_idx.pop()].role = "synthesizer"
    else:
        # 3 人全同 structural_role(极少见,结构平衡硬规则应阻止这种情况)
        speakers[1].role = "support"
        speakers[2].role = "synthesizer"

elif len(speakers) == 4:
    speakers[0].role = "primary"
    # 挑 challenge(结构相反最高分)
    challenger_idx = find_first_opposite_structural_role(speakers, primary=0)
    if challenger_idx is None:
        # 回退:把分数最低者当 challenge
        challenger_idx = 3
    speakers[challenger_idx].role = "challenge"
    # 剩下两人:分数高者 support,分数低者 synthesizer
    remaining = [i for i in [1, 2, 3] if i != challenger_idx]
    remaining.sort(key=lambda i: speakers[i].total, reverse=True)
    speakers[remaining[0]].role = "support"
    speakers[remaining[1]].role = "synthesizer"
```

**特殊情况**:
- 强制补位(§12)的 agent,如果不在常规 top 4,替换目标必须排除 protected speaker,并按 `room-selection-policy.md §12` 的 offensive → moderate → 非 protected 低分顺序选择;角色仍由本节 §7.2 算法分配
- 用户 `@点名` 的 agent 必须入本轮,覆盖原 speakers 中分数最低的非 protected speaker,新角色根据其 `structural_role` 判定

---

### §7.3 单条发言长度约束

**软目标**:80-180 字(与 Session 1 大报告的 `chat-compact` 规格一致)

**硬上限**:220 字(§5.5.4 已锁)

**超限处理**:
- orchestrator 在 room-chat prompt 的输出后检测长度
- 超过 220 字 → 截断到最近一个完整句号,末尾加「[...]」
- 在 `conversation_log.speakers[i].content` 记录截断后的内容
- 在 `forced_rebalance` 或新字段(v0.3)记录「truncated」

**为什么不让 prompt 自己控制长度**:
- LLM 对「字数」的估计很不准
- 硬规则在 orchestrator 层截断更可靠
- 截断后加「[...]」保留「这段话被打断了」的语义信号,用户可以 `@该 agent 继续` 让他下轮补完

---

### §7.4 互相引用规则(最多 2 跳)

**目的**:让 speakers 可以**引用**其他 agent 的观点(不只是本轮的 speakers,也包括 conversation_log 中的历史发言),但避免无限嵌套。

**定义「一跳」**:speaker A 的发言中显式提到 speaker B 的观点(例如「Sun 刚才说 winner-takes-all,但…」),算作 A → B 一跳引用。

**规则**:
- **最多 2 跳**:A 引 B,B 引 C,到此为止,不能 C 再引 D
- 本轮 speakers 之间可以引用,也可以引用**历史 turns** 的发言者(读 `conversation_log`)
- 每轮 speaker 的发言中,`cited_agents` 字段(§5.5)记录**本轮 speaker 引用的所有 agent_id**
- 2 跳的追溯由 orchestrator 根据 `cited_agents` 构建

**违反规则的后果**:
- room-chat prompt 生成的发言中,如果检测到 3 跳嵌套,orchestrator 截断最深那跳,强制终止
- 在 warning 记录「nested_citation_exceeded」

**为什么限制 2 跳**:
- 3 跳以上的引用链在阅读上非常费力
- 长链引用的价值递减(第 3 跳通常只是重复早期观点)
- 强制深度限制让每位 speaker 的发言更**独立**,而不是退化成「互相 cite」的回音室

---

### §7.5 发言生成流程(每轮完整路径)

```
1. selection prompt (room_turn 模式) → speakers[] + 每人的 role
2. orchestrator 调用 §7.2 算法分配角色(primary / support / challenge / synthesizer)
3. orchestrator 调用 room-chat.md prompt(Phase 4),传入:
   - 当前 stage
   - active_focus
   - primary_type / secondary_type
   - agents[] + agent_roles(长期角色)
   - speakers[] + 每人的本轮 role
   - conversation_log 最近 3 轮(或 recent_log 压缩版)
   - 用户最新输入
4. room-chat prompt 产出 N 条发言(N = speakers.length)
5. orchestrator:
   - 对每条发言做 §7.3 长度截断
   - 解析 `cited_agents`(通过正则或 LLM 提取 @ 引用)
   - 构建新 Turn 对象,追加到 conversation_log
   - 更新 silent_rounds(入选归 0,其他 +1)(§3.1)
   - 更新 last_stage / turn_count / recent_log(§3.2 / §3.3 / §3.4)
6. 主持器检查是否触发 upgrade_signal(§9)
7. 向用户展示本轮发言
```

**关键不变量**:
- 步骤 1-2 是**规则引擎**(deterministic),无 LLM 参与
- 步骤 3-4 是**LLM 调用**(room-chat prompt,Phase 4 交付)
- 步骤 5 是**规则引擎**(状态更新)
- 步骤 6 **v0.2 是规则引擎**,v0.3+ 可升级为混合(Q1 决议)

**这与 Q1 的「混合模式」决议一致**:日常跑规则,关键决策节点(步骤 3 的发言生成 + 步骤 6 的升级判断)才调 LLM。

---

### §7.6 发言机制的边界情况

| 情况 | 处理 |
|---|---|
| speakers 中只有 1 人(极端琐碎议题) | 单人独讲,role=primary,无 support/challenge/synthesizer |
| 3 人全同 structural_role(结构平衡规则应阻止,但以防万一) | 最高分 primary,其余 support + synthesizer |
| 强制补位塞入第 5 人 | v0.2 不允许超过 4 人,替换最低分非 protected speaker,并按 §12 的 offensive → moderate → 非 protected 顺序选择 |
| 用户 @ 点名了非 speakers 中的 agent | 该 agent 替换 top 4 最低分者(不是扩展到 5 人)|
| conversation_log 为空(第 0 轮) | room-chat 读空历史,只靠 user_input + agent_roles |
| 某 speaker 的发言被截断 | 截断后加「[...]」,cited_agents 可能不完整,警告记录 |

---

---

## §8. 换人机制协议

### §8.1 v0.2 的 Minimal 决议:砍掉 3 档分层

Session 1 大报告提出的**3 档分层**(核心常驻 / 阶段性参与者 / 临时补位)在 v0.2 **不实现**。

**决议依据**(DECISIONS-LOCKED 第 38 条):
1. Session 1-4 都没落地这个设计,说明不是迫切需求
2. 现有机制(花名册 + 强制补位 + `/add` + `/remove`)已经覆盖了「换人」的核心场景
3. 3 档分层会引入「某 agent 虽在 roster 但被降权」这种半失能状态,增加 schema 复杂度但价值不明
4. 如果真的需要,v0.3+ 再加,不破坏 v0.2 契约

### §8.2 v0.2 的换人机制(实际只做 3 件事)

**1. 强制补位**(连续 3 轮沉默)
- 由 `room-selection-policy.md §12` 定义
- 由 `room-architecture.md §3.1` 的 `silent_rounds` 维护
- 本文档不重复,只引用

**2. 用户显式 `/add` / `/remove`**
- 由 §6.3 / §6.4 定义
- 用户决定谁进谁出,orchestrator 只做硬过滤和结构平衡兜底

**3. `/remove` 触发的自动补位**
- 由 §6.4 定义:移除后如果结构失衡,orchestrator 自动补一人
- 补位者通过 `room-selection.md` 的 `roster_patch` add 模式选出

**就这三件事,不多不少**。v0.2 没有任何其他换人触发路径。

### §8.3 为什么这是够用的

对比 Session 1 大报告的 3 档分层:

| 场景 | Session 1 3 档方案 | v0.2 Minimal 方案 |
|---|---|---|
| 某 agent 阶段不匹配当前 stage | 降级为「阶段性」,低权重保留 | 不入本轮 speakers(selection prompt 的 stage_fit 打分已处理) |
| 某 agent 被连续跳过 | 进入「临时补位」队列,等机会 | 连续 3 轮触发强制补位(§12) |
| 用户想踢人 | 移到「非核心」慢慢边缘化 | `/remove` 直接移出 |
| 用户想加人 | 先放「临时补位」观察 | `/add` 直接加入 |
| 议题漂移,原阵容不合适 | 重排分层 | 主持器建议 `/upgrade-to-debate` 或用户新建房间 |

**每个场景 v0.2 都有覆盖方案,只是更简单**。3 档分层是「优雅但不必要」的设计。

### §8.4 未来扩展空间(不在 v0.2 交付)

如果 v0.3+ 决定加 3 档分层:
- 在 §5.3 的 `agents` 字段里增加 `tier` 字段(enum: `core / stage_rotating / backup`)
- 在 selection prompt 里增加 tier 权重(core 加分 / backup 减分)
- 在 `/add` / `/remove` 里增加 tier 参数(可选)
- 需要同步扩 DECISIONS-LOCKED 的决议 12(花名册软顶)

**本文档 v0.2 明确不做**,但保留扩展接口。

---

---

## §9. 主持器的隐性职责

**主持器**(orchestrator)不是对话 Agent,也不是 LLM call —— 它是一个**规则引擎**,在关键时刻基于 room state 发出建议。

### §9.1 Q1 决议:混合模式(规则打底 + 关键决策调 LLM)

主持器的工作方式:

| 频率 | 做什么 | 由谁做 |
|---|---|---|
| **每轮运行时** | 读状态、跑规则、发建议 | 规则引擎(deterministic,无 LLM)|
| **关键节点** | 生成发言、做 summary、判断升级 | LLM call(room-chat / room-summary / 本章的主持器 LLM 判定)|

**为什么混合**:
- 纯规则引擎对「语义级漂移检测」无能为力(例如「用户讨论从 `startup` 漂到了 `product`」)
- 纯 LLM 成本高、飘、不稳
- 混合模式用规则引擎处理 80% 的日常监控(刻度 + 阈值),用 LLM 处理 20% 的语义判定(建议 / 升级 / summary)

本章只定义**规则引擎部分**的触发条件。LLM 部分的 prompt 是 Phase 4 交付。

### §9.2 主持器的 3 个隐性建议

主持器在**每轮 `room_turn` 完成后**,按顺序检查以下 3 个条件,最多触发 1 个建议(优先级从高到低):

#### §9.2.1 建议 `/upgrade-to-debate`(最高优先级)

**触发条件**(4 种 reason 之一,见 §5.7):

1. **`reached_decision_stage_with_tension`**:
   - `last_stage == "decision"` AND
   - `tension_points.length ≥ 2` AND
   - 距离上次 summary ≥ 3 turns(避免 summary 刚跑完就建议)
   - → 写 `upgrade_signal`,提示用户

2. **`forced_rebalance_repeated`**:
   - 最近 2 轮的 `conversation_log[i].forced_rebalance != null`
   - → 正常单轮选人无法稳定,讨论需要更结构化的 `/debate`

3. **`token_budget_repeatedly_exceeded`**:
   - 最近 3 轮中有 ≥ 2 轮 `tokens_used > 2500`
   - → 讨论密度过高,单轮无法承载,建议升级

4. **`user_explicit_request`**:
   - 用户发 `/upgrade-to-debate`
   - → 直接进入升级流程

**动作**:

1. 写 `upgrade_signal` 字段(§5.7)
2. 向用户展示建议:
   ```
   主持器建议:
   [已到 decision 阶段但存在 2 个未收敛张力点]
   输入 /upgrade-to-debate 升级,或继续讨论。
   ```
3. **不强制升级**。用户继续发言即视为拒绝建议,`upgrade_signal.confidence` 下轮减 0.1

#### §9.2.2 建议 `/summary`(中优先级)

**触发条件**:

- 距离上次 `/summary` ≥ **5 turns** AND
- 最近 5 轮内 stage 发生过切换(`conversation_log[-5:]` 的 stage 有 ≥ 2 种) AND
- `consensus_points.length < 2`(当前共识稀薄,值得盘点)

**动作**:

```
主持器建议:已讨论 5 轮,阶段有切换,建议运行 /summary 盘点共识和分歧。
```

#### §9.2.3 建议 `/focus`(最低优先级)

**触发条件**:

- `active_focus == null`(当前未聚焦) AND
- `parsed_topic.sub_problems.length ≥ 2`(议题有多个子问题) AND
- 最近 3 轮的发言内容语义分散(v0.2 用一个简单启发式:最近 3 轮 speakers 的 `cited_agents` 交集 ≤ 1 人)
- → 讨论正在漂移,建议聚焦到某个子问题

**动作**:

```
主持器建议:讨论涉及多个方向,考虑用 /focus <子问题> 聚焦其中之一。
```

### §9.3 建议的优先级与互斥

**规则**:每轮**最多建议 1 个**。按 §9.2.1 → §9.2.2 → §9.2.3 的顺序检查,**第一个触发的就停止检查**。

**理由**:用户收到多个主持器建议会眩晕。一次一个,清楚。

### §9.4 主持器**不做**的事(v0.2 明确边界)

以下事情 v0.2 **明确不做**,避免 scope creep:

- ❌ **语义级 stage 漂移检测**(「用户实际上在讨论别的议题了」)—— 这需要 LLM call,v0.3+
- ❌ **自动 rewrite summary**(不等用户 `/summary` 就自己更新 §5.6 字段)—— v0.3+
- ❌ **主动踢人**(识别某 agent 质量下降自动 remove)—— v0.3+,且可能永远不做
- ❌ **跨房间关联**(检测用户在多个房间讨论相关议题)—— 不在 `/room` 范围
- ❌ **用户情绪识别**(检测用户不耐烦了建议结束)—— 不在 `/room` 范围

### §9.5 主持器的实现位置(Phase 5)

**v0.2 不实现**具体代码,只定义**规则**。Phase 5 的 `.codex/skills/room-skill/SKILL.md` 才是真正的主持器实现入口。

当 Phase 5 实现时:
- 规则引擎 = Phase 5 的 skill 里的 deterministic code(JavaScript / shell / 配置文件)
- LLM 部分 = 调用 `room-chat.md` / `room-summary.md` / `room-upgrade.md`(Phase 4)

本文档 §9 是 Phase 5 主持器**必须实现的最小规则集**。

---

---

## §10. 与其他协议的关系

- **消费本文档的**:`prompts/room-selection.md`(读 `current_state` 的 4 个运行时字段)
- **被本文档消费的**:`docs/room-selection-policy.md`(§12 强制补位 + §3 输入契约)
- **平级**:`docs/room-to-debate-handoff.md`(Phase 3 交付,`upgrade_signal` 字段对接)
- **独立**:`docs/debate-skill-architecture.md`(`/debate` 协议完全不读本文档)

---

## §11. 版本记录

- **v0.1-alpha (2026-04-11, Session 4)**:首节完成。覆盖 FINDING #6 阻塞项,定义 4 个运行时伴生字段(`silent_rounds` / `last_stage` / `turn_count` / `recent_log`)的所有权、更新时机、传递路径。其余章节(§5-§9)留为占位,等 Phase 2 完整交付。
- **v0.2-minimal (2026-04-11, Session 5)**:Phase 2 主体完成。
  - **§5 状态字段**:完整定义 10 个字段(room_id / title / mode / primary_type / secondary_type / agents / agent_roles / active_focus / conversation_log / 4 个 summary 字段 / upgrade_signal),其中 conversation_log 含完整 Turn schema 与持久化策略,v0.2 内存运行不写盘(继承 Session 2 决议 27)
  - **§6 命令语义表**:完整定义 4 个核心命令(`/room` / `/focus` / `/add` / `/remove`),最小占位 3 个辅助命令(`/summary` / `/upgrade-to-debate` / `@<agent>`)
  - **§7 发言机制协议**:完整定义 4 类发言角色(primary / support / challenge / synthesizer)、角色分配算法(2-4 人)、发言长度约束(软 80-180 字 / 硬 220 字)、互相引用规则(最多 2 跳)、发言生成完整流程
  - **§8 换人机制**:**Minimal 决议**——砍掉 3 档分层,只保留强制补位 + `/add` / `/remove` + 自动补位
  - **§9 主持器隐性职责**:**混合模式决议**——规则引擎 + 关键节点 LLM call。3 个隐性建议(/upgrade / /summary / /focus)按优先级每轮最多触发 1 个
  - **§1-§4 零改动**(Session 4 契约保持)
  - 本次交付不涉及 prompt 层改动,所有规则变化留给同期的 `room-selection-policy.md v0.1.2` 补丁
- **v0.2-minimal+p0 (2026-04-12, Session 8)**:P0 补丁。显式写入 `previous_summary` 必填契约(决议 44),并锁定 `turn_role` 责任边界:selection 只选人排序,orchestrator 分配 primary/support/challenge/synthesizer,chat 只消费。
- **v0.2-minimal+p3 (2026-04-12, Session 8)**:§12 / @agent 补丁。`@<agent>` 由 orchestrator 解析到 `user_constraints.mentions`,selection 将其作为 protected speaker 硬约束;强制补位替换不得挤掉 protected speaker。

---

_Session 5 Phase 2 主体完成于 2026-04-11。下一位 Agent:如果你要做 Phase 3(room-to-debate-handoff 协议)或 Phase 4(3 个对话 prompt),本文档已经提供完整的状态字段 schema 和触发条件。如果你要修改 §1-§4(Session 4 契约),必须同步修 `room-selection-policy.md` 和 `prompts/room-selection.md`,并在 DECISIONS-LOCKED 第 30 条下追加「解锁 §1-§4」决议。_






