# Room Examples

## 案例 1：从开放探索开始一个房间

### 输入

`/room 我想讨论一个面向大学生的 AI 学习产品，先别急着下结论，先把方向、切口、风险一步一步推出来。`

### 期望系统动作

- 把请求识别为 `/room` 的显式进入，而不是普通 skill 路由
- 调用 `prompts/room-selection.md` 的 `room_full`
- 建立 room state，并写入 `room_id / title / primary_type / secondary_type / agents / agent_roles / last_stage`
- 让首轮发言围绕“方向真假 + 切口大小 + 下行风险”展开，而不是直接输出最终决策

### 期望输出特征

- roster 在 2-8 人之间
- 首轮 stage 通常是 `explore`
- 首轮 speakers 通常是 2-4 人
- 输出带有可继续推进的房间状态，而不是一次性结论

### 后续可接命令

- `/focus 先只盯最小可验证切口`
- `/summary`
- `/upgrade-to-debate`

---

## 案例 2：在既有房间里收窄讨论范围

### 前置状态

房间已经建立，讨论过“方向值不值得做”，但子问题仍然太散。

### 输入

`/focus 先只盯“最小可验证切口”，不要继续扩展到融资和长期护城河。`

### 期望系统动作

- 保留原房间，不新建房间
- 更新 `active_focus`
- 调用 `prompts/room-selection.md` 的 `room_turn`
- 基于当前 roster 选出最适合这个焦点的 2-4 个 speakers
- 新一轮 conversation 只围绕当前 focus 推进

### 期望输出特征

- `conversation_log` 新增一轮 Turn
- `recent_log` 与 `silent_rounds` 被回写
- 发言更集中，不再把主题重新拉回全局创业判断

---

## 案例 3：在房间中做阶段总结

### 前置状态

房间已经跑过数轮，出现了若干共识、分歧和未解问题。

### 输入

`/summary`

### 期望系统动作

- 调用 `prompts/room-summary.md`
- 从 `conversation_log` 提取而不是创造总结内容
- 更新 4 个 summary 字段：
  - `consensus_points`
  - `open_questions`
  - `tension_points`
  - `recommended_next_step`

### 期望输出特征

- 共识点是房间里已经出现过的内容，不是主持器臆测
- open questions 是当前仍未回答的问题，而不是历史遗留问题的原样复制
- `recommended_next_step` 必须是具体动作，不是“继续讨论”这种空话

---

## 案例 4：从 `/room` 升级到 `/debate`

### 前置状态

房间已经到 `decision` 附近，但 tension 仍然没有收敛，或者用户明确要求正式审议。

### 输入

`/upgrade-to-debate`

### 期望系统动作

- 先确认存在合法的 `upgrade_signal`
- 调用 `prompts/room-upgrade.md`
- 把当前 room state + summary + conversation_log 打包成 handoff packet
- 把 packet 交给 `.codex/skills/debate-roundtable-skill/SKILL.md`

### 期望输出特征

- `/room -> /debate` 通过 handoff packet 过渡，而不是直接把原始群聊日志当 `/debate` 输入
- packet 至少包含：原始议题、子问题、共识点、分歧点、未解问题、候选方案、建议参会 agent
- 升级原因可追溯到 `upgrade_signal.reason`

---

## 案例 5：对房间 roster 做局部调整

### 前置状态

房间已经建立，但当前阵容不够合适，想加一个人或移除一个人。

### 输入

- `/add Taleb`
- `/remove Trump`

### 期望系统动作

- 调用 `prompts/room-selection.md` 的 `roster_patch`
- 在当前房间上局部修改 roster，而不是重建整个房间
- 变更后重新检查结构平衡

### 期望输出特征

- roster 更新可解释
- 被移除或新增的 agent 在说明里有明确理由
- 房间仍然保持 `defensive / grounded / offensive|moderate` 的基本平衡要求

---

## 使用提醒

- `/room` 是显式模式，不是默认模式
- `/room` 适合连续推进、阶段总结、保留状态的讨论
- `/debate` 适合需要正式审议和最终决议的重大判断
- `reports/` 只用于回看历史，不应覆盖这些 examples 所依赖的真源文件
