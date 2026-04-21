# Room → Debate Handoff Protocol

> `/room` 模式升级到 `/debate` 正式决议时的**交接包协议**。定义 13 字段的 handoff packet schema、升级触发条件、防污染规则、默认选人策略。
>
> 版本:**v0.1.3-p1**(packet schema v0.1 / room schema v0.2)| 生成:2026-04-11(Session 6 Phase 3)| 修订:2026-04-12(Session 8 Flow F validation)
> 上游依据:Session 1 大报告 §29 + `docs/room-architecture.md §5.7`(upgrade_signal)+ `§9.2.1`(主持器升级建议)
> 下游消费:`prompts/room-upgrade.md`(Phase 4,P5)按本协议打包 handoff packet

---

## 文档演进

| 版本 | 日期 | 范围 | 交付动机 |
|---|---|---|---|
| v0.1 | 2026-04-11(Session 6)| 完整 13 字段 + 触发 + 防污染 + 默认选人 | Phase 3 交付,为 Phase 4 room-upgrade.md 和 Phase 5 room-skill 提供协议基础 |
| v0.1.3-p0 | 2026-04-12(Session 8)| F20 修补:写入 user_explicit_request 的条件豁免 + field_13 warning_flags | 保持 packet schema 13 字段不变,让提前升级 warning 随 handoff_packet 进入 /debate |
| v0.1.3-p1 | 2026-04-12(Session 8)| F19 修补:要求执行层的 conversation_log freshness guard 复用同一 user_explicit_request 质量例外 | 避免 Flow F 在校验 3 提前拒绝,导致 §4.2 的决议 43 例外无法到达 |

---

## §1. 目的与定位

### §1.1 核心问题

`/room` 模式的**半结构化讨论**不能直接喂给 `/debate` 的**正式圆桌**,因为:

- `/room` 允许探索性、试探性、不完全收敛的内容
- `/debate` 必须面对正式审查与最终决议
- 直接把几十轮 `conversation_log` 塞给 `/debate` 会:
  - **token 爆炸**:`/room` 的日志量级远超 `/debate` 单场的承载
  - **污染决议**:探索期的草率发言会成为审查对象,降低决议质量
  - **结构破坏**:`/debate` 的分工/发言/汇总/审查 4 阶段会被搅乱

### §1.2 本协议解决什么

定义一个**正式的交接对象 `handoff_packet`**,让升级变成:

```
/room 完整状态(可能 50 轮对话)
   → room-upgrade prompt 提取 13 字段
   → 结构化 handoff_packet
   → /debate 只消费 handoff_packet(不直接读 conversation_log)
   → /debate 从这个受控输入开始,跑它自己的 8 步流程
```

**核心不变量**:

1. **`/debate` 不直接读 `conversation_log`**,只读 handoff_packet
2. **`conversation_log` 可以作为附录参考**,但不进入 `/debate` 的审查范围
3. **`/debate` 用自己的选人机制重新确定最终名单**,不机械沿用 `/room` roster
4. **`/debate` 的决议基于 handoff_packet 的 13 字段**,不回溯 `/room` 的过程分歧

---

## §2. 升级的本质:压缩转换,不是重开

`/room → /debate` 不是「开一个新对话」,而是:

> 把房间里已经推演出的**结构化上下文**,压缩成一份**适合正式圆桌审议的输入包**。

用户感知:
- ✅ 「当前讨论进入了更严肃阶段,我把房间里的发现打包交给 /debate 正式决议」
- ❌ 「忽略刚才的对话,重新开始」

### §2.1 什么**可以**跨越边界

| 类别 | 可以跨越吗 | 理由 |
|---|---|---|
| 已达成的共识(consensus_points) | ✅ 可以 | 这是 `/room` 的正向产出 |
| 明确的分歧(tension_points) | ✅ 可以 | 让 `/debate` 直接面对真问题 |
| 未解决的问题(open_questions) | ✅ 可以 | `/debate` 的议程来源 |
| 已出现的事实断言(factual_claims) | ✅ 可以 | 为 `/debate` 审查提供依据 |
| 建议带入的 agent 名单 | ⚠️ 仅作参考 | `/debate` 必须用自己的规则重选 |
| 升级原因 | ✅ 必须 | `/debate` 主持人用于定向 |

### §2.2 什么**不能**跨越边界

| 类别 | 阻断原因 |
|---|---|
| 完整的 `conversation_log` Turn 数组 | 会把探索期的草率发言带进审查 |
| 单条 speaker 发言原文 | 除非已经被压缩为 factual_claim 或 consensus |
| `silent_rounds` / `turn_count` / `recent_log` 等运行时字段 | 这些是 `/room` orchestrator 的私有状态,与 `/debate` 无关 |
| 用户在 `/room` 的隐式偏好 | `/debate` 不做个性化决议 |
| 已 `/remove` 的 agent 的历史发言 | 被移除即不保留 |

---

## §3. Handoff Packet 的 13 字段 Schema

本节是本文档的**核心**。每个字段锁定:类型 / 必填 / 来源 / 填充规则 / 长度约束。

### §3.1 完整 Schema

```json
{
  "handoff_packet": {
    "schema_version": "v0.1",
    "generated_at_turn": 12,
    "source_room_id": "room-20260411-abc123",

    "field_01_original_topic": "",
    "field_02_room_title": "",
    "field_03_type": { "primary": "", "secondary": null },
    "field_04_sub_problems": [],
    "field_05_consensus_points": [],
    "field_06_tension_points": [],
    "field_07_open_questions": [],
    "field_08_candidate_solutions": [],
    "field_09_factual_claims": [],
    "field_10_uncertainty_points": [],
    "field_11_suggested_agents": [],
    "field_12_suggested_agent_roles": {},
    "field_13_upgrade_reason": {
      "reason_code": "",
      "reason_text": "",
      "triggered_by": "",
      "confidence": 0.0
    }
  }
}
```

### §3.2 字段详细定义

| # | 字段 | 类型 | 必填 | 来源 | 填充规则 |
|---|---|---|---|---|---|
| 1 | `field_01_original_topic` | string | ✓ | `room.state.original_topic` (建房时锁定) | 原样复制,不重写 |
| 2 | `field_02_room_title` | string | ✓ | `room.state.title`(§5.1) | 原样复制 |
| 3 | `field_03_type` | `{ primary, secondary }` | ✓ | `room.state.primary_type / secondary_type`(§5.2) | 直接复制 |
| 4 | `field_04_sub_problems` | `SubProblem[]` | ✓ | 最近一次 selection prompt 的 `parsed_topic.sub_problems` + 后续 `/focus` 追加 | 全量,每条带 tags |
| 5 | `field_05_consensus_points` | `string[]` | ✓ | `room.state.consensus_points`(§5.6,最新 summary 产出) | 原样复制 |
| 6 | `field_06_tension_points` | `string[]` | ✓ | `room.state.tension_points`(§5.6) | 原样复制 |
| 7 | `field_07_open_questions` | `string[]` | ✓ | `room.state.open_questions`(§5.6) | 原样复制 |
| 8 | `field_08_candidate_solutions` | `CandidateSolution[]` | ⚠️ 可空 | 从 `conversation_log` 提取 + summary 里的 `recommended_next_step` | 每条必须是具体方案,不是方向 |
| 9 | `field_09_factual_claims` | `FactualClaim[]` | ⚠️ 可空 | 从 `conversation_log` 提取被引用的数字 / 案例 / 机制 | 必须可追溯到 log 某轮某人 |
| 10 | `field_10_uncertainty_points` | `string[]` | ✓ | 从 `conversation_log` 提取 speakers 显式表达的不确定性 | 每条一句话,必须标「谁的不确定性」 |
| 11 | `field_11_suggested_agents` | `string[]`(agent_id) | ✓ | `room.state.agents` 过滤 + 按 §4 默认选人策略 | 3-5 人,不超过 `/debate` 单场硬顶 5 |
| 12 | `field_12_suggested_agent_roles` | `{[agent_id]: role_text}` | ✓ | 为每个 suggested_agents 给一句 `/debate` 里的职责草案 | 每个 role_text 40-80 字 |
| 13 | `field_13_upgrade_reason` | object | ✓ | 见下面 §3.3 | 4 子字段全部必填,`warning_flags` 可选但推荐输出 |

---

### §3.3 复合字段的子 schema

#### §3.3.1 SubProblem(field_04 元素)

```json
{
  "text": "All in 还是小步试",
  "tags": ["resource_allocation", "market_timing"],
  "discussed_in_turns": [1, 3, 5],
  "status": "open" | "converged" | "abandoned"
}
```

- `tags` 必须来自 v0.2 的 20 个合法 sub_problem_tags
- `status` 是 orchestrator 判定:
  - `converged`:该子问题已在 consensus_points 中有对应条目
  - `abandoned`:该子问题连续 5 轮未被任何 speaker 提及
  - `open`:其他

#### §3.3.2 CandidateSolution(field_08 元素)

```json
{
  "solution_text": "先用 2 周做最小可运行原型,再根据第 1 个真实用户反馈决定是否 All in",
  "proposed_by": ["munger", "paul-graham"],
  "support_level": "high" | "medium" | "low",
  "unresolved_concerns": [
    "Taleb 认为 2 周的预算设定本身就是 concave bet"
  ]
}
```

- `proposed_by` 必须是 agent_id,可多人共同提出
- `support_level`:
  - `high`:≥ 2 个 speaker 明确支持
  - `medium`:1 个 speaker 提出,未被反对
  - `low`:1 个 speaker 提出,已有 challenge 未回应
- `unresolved_concerns` 可空

#### §3.3.3 FactualClaim(field_09 元素)

```json
{
  "claim_text": "独立开发者工具市场 2024 年 CAGR ~15%",
  "cited_by": ["paul-graham"],
  "source_hint": "PG 在 Turn 3 提及,未给出来源",
  "reliability": "asserted" | "sourced" | "contested"
}
```

- `reliability`:
  - `sourced`:speaker 给出了明确引用源
  - `asserted`:speaker 断言但无源
  - `contested`:另一位 speaker 明确质疑该数据

#### §3.3.4 UpgradeReason(field_13)

```json
{
  "reason_code": "reached_decision_stage_with_tension",
  "reason_text": "已到 decision 阶段,仍有 2 个未收敛张力点:Sun 的 All in 叙事 vs Taleb 的 barbell 结构",
  "triggered_by": "auto_rule" | "user_explicit",
  "confidence": 0.8,
  "warning_flags": []
}
```

- `reason_code` 必须是 `room-architecture.md §5.7` 4 种 enum 之一:
  - `reached_decision_stage_with_tension`
  - `forced_rebalance_repeated`
  - `token_budget_repeatedly_exceeded`
  - `user_explicit_request`
- `reason_text`:一句话人类可读解释,为 `/debate` 主持人定向
- `triggered_by`:
  - `auto_rule`:主持器的 §9.2.1 规则触发
  - `user_explicit`:用户主动 `/upgrade-to-debate`
- `confidence`:0.0-1.0,主持器对「这次升级是合适的」的置信度
- `warning_flags`:可空数组,用于承载必须随 `handoff_packet` 进入 `/debate` 的升级风险标记。当前合法值包括 `user_forced_early_upgrade`。不要把只给 orchestrator 调试看的 warning 放进这里。

---

## §4. 升级触发条件(何时该升级)

本节**引用** `room-architecture.md §5.7 + §9.2.1`,避免重复,只锁定本文档的契约边界。

### §4.1 4 种合法触发(必须是这 4 种之一)

| reason_code | 对应规则 | 消费者 |
|---|---|---|
| `reached_decision_stage_with_tension` | §9.2.1 建议 1 | 主持器规则引擎 |
| `forced_rebalance_repeated` | §9.2.1 建议 2 | 主持器规则引擎 |
| `token_budget_repeatedly_exceeded` | §9.2.1 建议 3 | 主持器规则引擎 |
| `user_explicit_request` | §9.2.1 建议 4 | 用户输入 `/upgrade-to-debate` |

**不允许**在 `reason_code` 中使用其他值。如果未来需要新 reason,先改 `room-architecture §5.7`,再改本文档。

### §4.2 不该升级的情况(拒绝升级的硬规则)

即使 `upgrade_signal` 已触发,以下情况**主持器拒绝升级**,并提示用户:

1. **问题仍然模糊,边界不清**:`parsed_topic.sub_problems` 为空或 tags 全是 `out_of_vocabulary`
2. **讨论尚未进入 simulate/converge**:`stage ∈ {explore}` 且 `turn_count < 5` —— 还没有真正形成可升级的结构化内容
3. **summary 从未跑过**:`consensus_points.length == 0` 且 `tension_points.length == 0` —— 没有 summary 就没有可打包的内容
4. **candidate_solutions 为空**:`/debate` 需要至少 1 个候选方案作为讨论起点,空的 packet 无法支撑

**决议 43 的字面化例外(v0.1.3)**:

当 `upgrade_signal.reason == "user_explicit_request"` 时,用户控制优先,但不能无条件绕过质量下限。主持器只允许豁免上面的第 2 条(early stage / turn_count 过低),且必须同时满足:

- `consensus_points.length > 0`
- `tension_points.length > 0`
- `open_questions.length > 0`
- `candidate_solutions.length > 0` 或打包器能从 summary 的 `recommended_next_step` 构造至少 1 个 candidate_solution

豁免后必须同时在 `handoff_packet.field_13_upgrade_reason.warning_flags` 与 `packaging_meta.warnings` 追加 `user_forced_early_upgrade`,让正式圆桌首轮知道这是「用户强制提前升级」。第 1 / 3 / 4 条仍然是硬拒绝,`user_explicit_request` 不能豁免。执行层如果额外设置 `conversation_log.length >= 3` freshness guard,必须复用同一质量例外:用户显式升级 + conversation_log 至少 2 轮 + consensus/tension/open_questions/recommended_next_step 均非空时可以进入打包,并写入同一个 `user_forced_early_upgrade` warning。

**拒绝时的用户提示**:

```
升级建议被拒绝,原因:<具体的 §4.2 条目>
建议先运行 /summary 盘点共识和分歧,再考虑升级。
```

---

## §5. 防污染规则(核心不变量)

这 5 条规则是**本协议最重要的部分**。违反任一条会让 `/debate` 的决议质量崩溃。

### §5.1 Rule 1:`/debate` 不直接消费 `conversation_log`

**`/debate` 的输入只有 handoff_packet 一个对象**。原始的 Turn 数组、speaker content、cited_agents 等**都不进入** `/debate` 的任何流程。

**执行方**:Phase 5 的 `.codex/skills/room-skill/SKILL.md` 在调用 `/debate` 时,**只传 handoff_packet**,不传 conversation_log。

### §5.2 Rule 2:`conversation_log` 作为附录,不进审查

如果 `/debate` 的 reviewer 需要回溯某条 factual_claim 或 consensus 的出处,**可以**读 conversation_log 作为**附录参考**,但:

- 附录**只用于溯源**,不用于审查
- `/debate` reviewer **不得**把 conversation_log 中的原始发言作为审查对象
- `/debate` 的最终决议**必须**只基于 handoff_packet + `/debate` 自己跑出来的新发言

### §5.3 Rule 3:`/debate` 用自己的选人机制重新确定名单

`field_11_suggested_agents` 是**建议名单**,不是**锁定名单**。`/debate` 在接收 packet 后必须:

1. 读 `field_11_suggested_agents` 作为**候选池**
2. 按 `/debate` 自己的 §4.3 任务类型路由规则做选人
3. 按 `/debate` 自己的结构平衡规则做对冲
4. **最终名单可能与 `field_11` 不完全一致**,这是设计意图,不是 bug

具体默认策略见 §6。

### §5.4 Rule 4:决议基于 packet,不回溯过程分歧

`/debate` 的 reviewer 如果发现 packet 里的某个 consensus 或 factual_claim 值得质疑,**可以**在 `/debate` 内部发起 follow-up,但:

- follow-up 的审查对象是 **`/debate` 内部产生的发言**,不是 `/room` 的历史
- `/debate` 不得因为「某 agent 在 `/room` 里说过别的话」而质疑其当前发言
- `/debate` 不得把 `/room` 的 tension_points 作为自己的判据 —— 它只是议题的**启动材料**

### §5.5 Rule 5:handoff_packet 不可回写

`/debate` 的输出**不回写** `/room` state。两种模式**单向交接**:

- `/room → /debate`:把 packet 传过去
- `/debate → /room`:**不回传**。`/debate` 输出的是自己的决议,不是 `/room` 的状态更新

**房间的归档**:
- `/debate` 启动后,`/room` 的 `mode` 字段(§5.1)变为 `upgraded`
- `conversation_log` 保留在内存(或持久化存档),作为审计追溯
- `/room` 不再接受新 user_input,进入归档状态

**这条规则的意义**:`/debate` 是最终裁决点,不能被 `/room` 的后续讨论「覆盖」决议。两个模式是**单向漏斗**,不是循环。

---

## §6. 默认选人策略(field_11 怎么填)

### §6.1 基本规则(3 步)

```
1. 从 room.state.agents 取所有当前 roster(最多 8 人)
2. 应用以下过滤:
   - 移除 structural_role 纯 offensive 且 total_score < 第 3 分位的人
   - 移除近 5 轮沉默 ≥ 3 次的 agent(silent_rounds[id] ≥ 3 且没被强制补位过)
   - 保留所有 defensive / grounded / moderate 位
3. 如果过滤后 < 3 人,回填最近 5 轮 `cited_agents` 中出现过的 agent(说明被别人引用,仍有贡献)
4. 取 top 3-5 人,写入 field_11_suggested_agents
```

### §6.2 保留偏向:谁优先入选

按以下顺序加权:

1. **在 tension_points 中出现过的 agent**(他们是分歧的焦点,`/debate` 需要他们对峙)
2. **在 consensus_points 中出现过的 agent**(他们是共识的奠基者,`/debate` 需要他们确认)
3. **在 factual_claims 中提供过来源的 agent**(他们有数据责任)
4. **其他按 total_score 排序**

### §6.3 `/debate` 的重选权(§5.3 Rule 3 的具体化)

`/debate` 接收 packet 后,**可以**:

- 从 `field_11` 中**减去**某些不适合正式审议的 agent(例如 Sun 的 dramatic 风格在正式决议中可能被降权)
- 从 `/debate` 候选池中**追加**某些 `/room` 没用但 `/debate` 需要的 agent(例如 Trump 在某些谈判议题中可能被 `/debate` 通过 `--with` 强制加入,即使 `/room` 没用过)
- **但不得**完全无视 `field_11`,必须保留 ≥ 2 人的交集(除非 `field_11` 为空)

### §6.4 `field_12_suggested_agent_roles` 的填充

每个在 `field_11` 中的 agent,必须给一句 40-80 字的 `/debate` 职责草案。

**来源**:
- 首选:该 agent 在 `room.state.agent_roles` 中的 long_role(§5.3)
- 次选:该 agent 在 tension/consensus 中的角色,改写为 `/debate` 的职责口吻

**示例**:

```json
{
  "justin-sun": "在 /debate 中继续持 winner-takes-all + All in 叙事的立场,提供市场结构与竞争维度的判断,但 /debate 主持人应要求他显式量化假设",
  "taleb": "在 /debate 中担任 tail_risk 对冲位,对 All in 类建议做凸性 / 凹性检查,负责 /debate 的 red-flag 识别"
}
```

---

## §7. `/debate` 的消费边界(upgraded 之后发生什么)

### §7.1 `/debate` 读 packet 的具体流程

```
1. room-upgrade.md 产出 handoff_packet(Phase 4,P5)
2. room-skill SKILL.md(Phase 5,P6)把 packet 交给 debate-roundtable-skill
3. debate-roundtable-skill 读 packet 后:
   - field_01_original_topic → 作为 /debate 的议题输入
   - field_03_type → 直接用作 /debate 的 task_type(跳过自己的 §4.3 路由)
   - field_11_suggested_agents → 作为候选池,跑 /debate 的 §4.4 对冲规则
   - field_05_consensus_points + field_09_factual_claims → 作为 /debate 步骤 1(识别议题)的前置材料
   - field_06_tension_points + field_07_open_questions → 作为 /debate 步骤 2(识别任务类型)的补充
   - field_08_candidate_solutions → 作为 /debate 步骤 5(逐个发言)的讨论起点
4. /debate 按自己的 8 步流程跑(不因为 packet 而修改步骤)
5. /debate 输出统一决议,决议不回写 /room state
```

### §7.2 `/debate` 不必做的事(packet 已经做过)

- ❌ 不用重跑议题边界识别(packet 已有 field_01 + field_04)
- ❌ 不用重新定义 sub_problems(packet 已有 field_04)
- ❌ 不用从 0 讨论共识(packet 已有 field_05)
- ❌ 不用发掘 tension(packet 已有 field_06)

### §7.3 `/debate` 必须做的事(packet 不能替代)

- ✅ 用自己的 §4.3 规则确认最终 agent 名单
- ✅ 跑完整的 8 步流程(Step 1-8)
- ✅ 让 reviewer 审查 `/debate` 内部发言(不审查 `/room` 原始日志)
- ✅ 输出一个统一决议 —— 即使 packet 里的 candidate_solutions 有多个,`/debate` 最终必须收敛到 1 个

---

## §8. 边界情况

| 情况 | 处理 |
|---|---|
| packet 的 `field_05/06/07` 全为空 | 主持器拒绝升级(§4.2 条目 3) |
| packet 的 `field_11_suggested_agents.length < 3` | 追加 `conversation_log` 最近 5 轮出现过的 cited_agents |
| packet 的 `field_11_suggested_agents.length > 5` | 按 §6.2 保留偏向削到 5 人 |
| user 显式 `/upgrade-to-debate` 但 room_state 未进入 converge/decision | 打包 packet 但 `reason_text` 追加「用户强制升级,房间仍在 explore 阶段」警告 |
| packet 生成时 `previous_summary == null`(从未跑过 summary) | 主持器拒绝升级(§4.2 条目 3),先建议 `/summary` |
| `/debate` 跑完后用户想回到 `/room` 继续 | **不支持**。`/room` 已归档,必须用新的 `/room <议题>` 建房(可以用旧 packet 初始化) |
| `conversation_log` 超过 1000 turns 的极长房间 | room-upgrade prompt 只读最近 20 轮 + 所有 summary 产出,避免 token 爆炸 |

---

## §9. 与其他协议的关系

| 协议 | 关系 |
|---|---|
| `room-architecture.md §5.6` | field_05/06/07 的来源(4 字段定义) |
| `room-architecture.md §5.7` | field_13.reason_code 的合法枚举 |
| `room-architecture.md §9.2.1` | 升级触发的 4 种规则 |
| `room-selection-policy.md` | field_11 的默认选人策略的细化规则基础 |
| `prompts/room-selection.md` | field_04 sub_problems 的原始来源 |
| `prompts/room-chat.md` | conversation_log 的写入者(Turn schema) |
| `prompts/room-summary.md` | field_05/06/07 的实际填充者(通过写入 room.state.*) |
| `prompts/room-upgrade.md`(Phase 4,P5) | 本协议的**实际执行者**,按本文档 schema 打包 |
| `.codex/skills/debate-roundtable-skill/SKILL.md` | 本协议的**消费者**,按 §7 规则处理 packet |
| `AGENTS.md` | `/debate` 的使命文档,定义 packet 之后怎么跑 |

---

## §10. v0.1 已知限制(不做的)

本协议 v0.1 **明确不做**以下事项,留给 v0.2+ 或更高版本:

1. **不做 packet 的持久化**:生成后在内存里传给 `/debate`,不落盘 —— 与 Session 2 决议 27(不做持久化)一致
2. **不做 packet 的版本迁移**:如果未来 schema 升级到 v0.2,老 packet 不自动升级
3. **不做反向 handoff**:`/debate → /room` 不支持(§5.5 Rule 5)
4. **不做 packet 的外部审计接口**:外部工具无法订阅 upgrade 事件
5. **不做多 packet 合并**:如果用户有 2 个相关 `/room` 想一起升级,必须分别升级,不能合并 packet
6. **不做 packet 的增量更新**:packet 是「一次性生成 + 发送」,不支持流式传递

---

## §11. 版本记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-04-11(Session 6) | 首版。Phase 3 交付。完整定义 13 字段 + 4 种复合子 schema + 5 条防污染规则 + 默认选人策略 + `/debate` 消费边界。对接 Phase 4 room-upgrade.md(P5) |
| v0.1.3-p0 | 2026-04-12(Session 8) | F20 补丁。把决议 43 写入 §4.2: user_explicit_request 只可有条件豁免 early-stage 拒绝;新增 field_13_upgrade_reason.warning_flags 承载 user_forced_early_upgrade |
| v0.1.3-p1 | 2026-04-12(Session 8) | F19 补丁。明确执行层 conversation_log freshness guard 也必须复用决议 43 的质量例外,并写同一 warning |

---

_本协议的规则源头是 `docs/room-architecture.md §5.7 / §9.2.1`(升级触发)+ Session 1 大报告 §29(13 字段雏形)。Phase 4 的 `prompts/room-upgrade.md` 是本协议的可执行实现层。Phase 5 的 `.codex/skills/room-skill/SKILL.md` 是调用入口。`/debate` 的 `AGENTS.md` 是 packet 的最终消费者。_
