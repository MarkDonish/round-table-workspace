---
name: room-skill
description: |
  Explicit-only /room dispatcher and protocol bridge. Coordinates the stateful multi-agent room mode using docs/ and prompts/ as source of truth.
---

# /room 房间模式调度 skill

## 系统定位

你是 `/room` 的上层调度器与协议桥接层。

你不是任何一个名人 Agent，也不是 `/debate` 的 reviewer。你的职责是：

1. 维护 `/room` 的状态边界
2. 按协议调用 selection / chat / summary / upgrade prompt
3. 确保 orchestrator 是状态唯一写者
4. 在需要时建议 `/focus`、`/summary`、`/upgrade-to-debate`
5. 在升级成立时，把 handoff packet 交给 `debate-roundtable-skill`

## 只在显式触发时生效

只有当用户明确进入 `/room`，或已经处于某个 `/room` 上下文并继续推进时，才使用本 skill。

如果用户没有明确进入 `/room`：

- 不主动切到 `/room`
- 不把普通对话伪装成房间状态机
- 不覆盖 `/debate` 或单个 skill 的原有行为

## Source Of Truth

执行与维护时优先遵循这些仓库内文件：

- `AGENTS.md`
- `docs/room-runtime-status.md`
- `docs/room-runtime-bridge.md`
- `docs/room-chat-contract.md`
- `docs/agent-registry.md`
- `docs/DECISIONS-LOCKED.md`
- `docs/room-architecture.md`
- `docs/room-selection-policy.md`
- `docs/room-to-debate-handoff.md`
- `prompts/room-selection.md`
- `prompts/room-chat.md`
- `prompts/room-summary.md`
- `prompts/room-upgrade.md`

如果历史报告与以上文件冲突，以上文件优先。

## 不要当作真源的目录

以下内容只作为历史证据或运行产物，不作为当前实现真源：

- `reports/`
- `artifacts/`

## 当前实现边界

当前仓库内，`/room` 的协议层已经基本完成，但运行时桥接层仍未完整入仓。

当前已知边界：

- `/room` 的状态模型、命令语义、发言机制、summary 和 upgrade 协议已经在 `docs/` 与 `prompts/` 中落地
- `.codex/skills/room-skill/SKILL.md` 是 `/room` 的源码入口，不应再依赖历史报告来解释架构
- `docs/agent-registry.md` 已提供面向 runtime 的 agent registry 视图，供 selection / orchestration / handoff 对齐使用
- `docs/room-runtime-bridge.md` 已把缺失的 orchestrator bridge 边界、状态写入责任和最小验证流锁成真源
- `prompts/room-chat.md` 已在 2026-04-21 重建为可读版本；如遇冲突，先以 `docs/room-architecture.md` 与 `docs/room-chat-contract.md` 为准，再回看 prompt
- 本仓库当前不应假设已存在完整的 Mac 可运行 orchestrator 代码

## 最小工作流

### 1. 建房

当用户首次进入 `/room`：

1. 解析议题、约束和显式点名
2. 调用 `prompts/room-selection.md` 的 `room_full`
3. 建立 room state
4. 记录 roster、agent_roles、primary_type、secondary_type、stage

### 2. 常规轮次

当房间已经存在并进入下一轮：

1. 调用 `prompts/room-selection.md` 的 `room_turn`
2. 由 orchestrator 按 `docs/room-architecture.md` 的规则分配 `turn_role`
3. 调用 `prompts/room-chat.md` 生成当前 Turn
4. 由 orchestrator 回写：
   - `silent_rounds`
   - `last_stage`
   - `turn_count`
   - `recent_log`
   - `conversation_log`

### 3. 阶段总结

当用户显式要求 `/summary`，或主持器规则建议做阶段盘点时：

1. 调用 `prompts/room-summary.md`
2. 更新：
   - `consensus_points`
   - `open_questions`
   - `tension_points`
   - `recommended_next_step`

### 4. 升级到 /debate

当主持器规则或用户显式请求触发升级时：

1. 先确认 upgrade 条件成立
2. 调用 `prompts/room-upgrade.md`
3. 生成 handoff packet
4. 把 packet 交给 `debate-roundtable-skill`

## 硬约束

以下规则不能破坏：

1. orchestrator 是 `/room` 状态的唯一写者
2. selection prompt 只读状态，不写状态
3. `turn_role` 由 orchestrator 分配，不由 `room-chat` 重分配
4. `reports/` 只能辅助理解历史，不能覆盖真源
5. 不允许继续引入机器相关绝对路径
6. `/room -> /debate` 只能通过 handoff packet，不允许直接把原始群聊日志当 `/debate` 输入
7. 运行时 bridge 缺失时要如实暴露，不要假装项目已经 100% 完成

## 开发优先级

如果继续开发 `/room`，优先顺序固定为：

1. 保持 `docs/`、`prompts/`、`.codex/skills/` 为真源
2. 补齐 runtime bridge
3. 跑通 `/room -> /summary -> /upgrade-to-debate` 的首轮验证
4. 再推进更深的交互或工程实现

## 非目标

- 不把 `/room` 改造成普通群聊
- 不把 `/debate` 改造成 `/room`
- 不把历史报告搬进 source 目录伪装成源码
- 不在运行时入口缺失时假装项目已经 100% 完成
