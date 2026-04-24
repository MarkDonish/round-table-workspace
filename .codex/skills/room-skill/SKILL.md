---
name: room-skill
description: |
  Explicit-only /room dispatcher and protocol bridge. Coordinates the stateful multi-agent room mode using checked-in docs, prompts, and workflow files as source of truth.
---

# /room 房间模式调度 skill

`/room` 不是新的名人人格，而是状态化多 Agent 房间的上层调度器。

它的职责不是替任何一个 Agent 发言，而是负责：

1. 识别 `/room` 相关命令
2. 维护 `/room` 的状态边界
3. 按协议调用 selection / chat / summary / upgrade prompt
4. 确保 orchestrator 是状态唯一写者
5. 在成立时把 handoff packet 交给 `debate-roundtable-skill`

---

## 只在显式触发时生效

只有当用户明确进入 `/room`，或已经处于某个 `/room` 上下文并继续推进时，才使用本 skill。

允许的显式命令：

- `/room <topic>`
- `/focus <focus text>`
- `/summary`
- `/upgrade-to-debate`
- `/add <agent>`
- `/remove <agent>`

如果用户没有显式进入 `/room`：

- 不主动切到 `/room`
- 不把普通对话伪装成房间状态机
- 不覆盖 `/debate` 或单个 skill 的原有行为

---

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
- `.codex/skills/room-skill/WORKFLOW.md`

如历史报告与以上文件冲突，以上文件优先。

---

## 运行入口

当 `/room` 生效时：

1. 先读取本文件
2. 再读取 `.codex/skills/room-skill/WORKFLOW.md`
3. 若需要 checked-in host bridge，使用 `.codex/skills/room-skill/runtime/room_runtime.py`
4. 需要命令示例和产物路径时，读取 `.codex/skills/room-skill/runtime/README.md`
5. 只在需要解释协议边界时再回到 `docs/room-runtime-bridge.md` 与相关 prompts

`WORKFLOW.md` 是当前 checked-in 的 runtime playbook。

---

## 命令语义

### `/room <topic>`

- 首次进入时：创建房间
- 已有房间上下文时：按宿主行为决定是继续当前房间还是显式新建；如果语义不清，优先保持当前房间，不擅自重置状态

### `/focus <focus text>`

- 更新 `active_focus`
- 保留现有 roster
- 继续正常 `room_turn`

### `/summary`

- 只做阶段总结
- 不自行推进讨论
- 不凭空创造共识

### `/upgrade-to-debate`

- 先确认存在合法 upgrade 条件或用户显式请求
- 只通过 handoff packet 进入 `/debate`

### `/add` / `/remove`

- 视为 roster patch
- 修改现有房间，不重建房间

---

## 最小工作流

### 1. 建房

当用户首次进入 `/room`：

1. 解析议题、约束和显式点名
2. 调用 `prompts/room-selection.md` 的 `room_full`
3. 建立 room state
4. 写入 roster、agent_roles、primary_type、secondary_type、last_stage

### 2. 常规轮次

当房间已经存在并进入下一轮：

1. 调用 `prompts/room-selection.md` 的 `room_turn`
2. 由 orchestrator 按 `docs/room-architecture.md` 分配 `turn_role`
3. 调用 `prompts/room-chat.md` 生成当前 Turn
4. 回写：
   - `silent_rounds`
   - `last_stage`
   - `turn_count`
   - `recent_log`
   - `conversation_log`

### 3. 阶段总结

当用户显式要求 `/summary`，或宿主规则建议做阶段盘点时：

1. 调用 `prompts/room-summary.md`
2. 更新：
   - `consensus_points`
   - `open_questions`
   - `tension_points`
   - `recommended_next_step`
   - `last_summary_turn`

### 4. 升级到 `/debate`

当主持器规则或用户显式请求触发升级时：

1. 先确认 upgrade 条件成立
2. 调用 `prompts/room-upgrade.md`
3. 生成 handoff packet
4. 把 packet 交给 `debate-roundtable-skill`

更细的执行顺序与失败处理，以 `WORKFLOW.md` 为准。

---

## 硬约束

以下规则不能破坏：

1. orchestrator 是 `/room` 状态的唯一写者
2. selection prompt 只读状态，不写状态
3. `turn_role` 由 orchestrator 分配，不由 `room-chat` 重分配
4. `reports/` 只能辅助理解历史，不能覆盖真源
5. 不允许继续引入机器相关绝对路径
6. `/room -> /debate` 只能通过 handoff packet，不允许直接把原始群聊日志当 `/debate` 输入
7. 不把 prompt 当成持久化层
8. 不把历史 session note 当成运行入口

---

## 当前实现边界

当前仓库内：

- `/room` 的协议层已完整进入真源
- `.codex/skills/room-skill/WORKFLOW.md` 已提供 checked-in 的 runtime playbook
- `.codex/skills/room-skill/runtime/room_runtime.py` 已提供 checked-in 的 host-side bridge
- `.codex/skills/room-skill/runtime/local_codex_executor.py` 已提供 checked-in 的本地 child-agent 执行器
- `.codex/skills/room-skill/runtime/generic_agent_executor.py` 已提供 checked-in 的 host-neutral 本地 CLI agent adapter，用于 Codex 之外的 Claude Code / 其他本地 agent 适配
- `.codex/skills/room-skill/runtime/generic_fixture_agent.py` 已提供 checked-in 的 fixture agent，用于验证 generic CLI / Claude Code adapter 路由
- `.codex/skills/room-skill/runtime/agent_host_inventory.py` 已提供 checked-in 的真实本地 agent 宿主 inventory/preflight
- `.codex/skills/room-skill/runtime/generic_agent_adapter_validation.py` 已提供 checked-in 的 generic local agent adapter kit，可一键跑 smoke + `/room -> /debate`
- `docs/generic-local-agent-adapter.md` 已提供其他本地 agent 的接入合同和通过标准
- `docs/local-agent-host-recipes.md` 已提供真实宿主接入 recipes，并明确 inventory 不等于 live validation
- `.codex/skills/room-skill/runtime/claude_code_live_validation.py` 已提供 checked-in 的真实 Claude Code 本地 CLI live validation wrapper
- `.claude/skills/room/SKILL.md` 已提供 Claude Code 原生 project skill 入口，并指回本文件作为 canonical source
- `.claude/scripts/validate_project_skills.py` 已提供离线结构验证，确保 Claude Code skill wrapper 没有漂移
- `.codex/skills/room-skill/runtime/local_codex_regression.py` 已提供 checked-in 的本地主线回归入口
- `.codex/skills/room-skill/runtime/chat_completions_regression.py` 已提供 checked-in 的 provider fallback 回归入口
- `.codex/skills/room-skill/runtime/chat_completions_readiness.py` 已提供 checked-in 的 provider live readiness 入口
- `.codex/skills/room-skill/runtime/chat_completions_live_validation.py` 已提供 checked-in 的真实 provider live wrapper
- `.codex/skills/room-skill/runtime/release_readiness_check.py` 已提供 checked-in 的 release readiness gate，用来区分 P0 上线阻塞和非阻塞 live 缺口
- checked-in runtime 现在已暴露 `gpt54_family` preset，可把当前验证通过的 `GPT-5.4` 主线参数冻结成最短命令
- `.codex/skills/room-skill/runtime/local_codex_executor.py` 现在也已暴露 checked-in 的 local host preflight，可先验证 `~/.codex` 宿主写入条件和 nested child-agent smoke
- `.codex/skills/room-skill/runtime/room_e2e_validation.py` 已提供 checked-in 的 E2E validation runner
- `.codex/skills/room-skill/runtime/mock_chat_completions_server.py` 已提供本地 mock provider，用于验证 Chat Completions 路径
- `/room local_codex` 已在 Mac 上通过 checked-in E2E 验证
- `/room -> /debate local_codex` 已在 Mac 上通过一条完整联调验证
- `/room -> /debate generic_cli` 和 `claude_code` executor route 已通过 checked-in fixture agent 验证 adapter contract；真实 Claude Code / 其他第三方本地 agent live run 仍需单独证明
- generic local agent adapter kit 已通过 checked-in fixture agent 验证，其他 agent 可复用同一命令做 live readiness check
- local agent host inventory 已可区分 CLI missing、auth blocked、ready for live validation，避免把本机 preflight 阻塞误报成通过
- Claude Code project skill wrapper 已通过结构验证；Claude Code 用户 clone 仓库后具备标准 `.claude/skills/room` 发现入口
- 当前 Mac 上真实 Claude Code preflight 已确认 CLI 可用，但 auth 未登录，live run 被 `claude_code_not_logged_in` 阻塞
- checked-in child-agent 执行器现在可显式控制 child task 的 reasoning effort，不必继承宿主全局 `xhigh`
- 当前最稳定的 Mac 本地主线配置已验证 `gpt-5.4` 主模型；`gpt-5.4-mini` 可作为同家族 fallback
- canonical fixture 已可在 Mac 本地跑通 `/room -> /summary -> /upgrade-to-debate`
- provider fallback regression 已复跑通过，且 readiness 会把当前未配置的真实 `.env.room` / `.env.debate` 报告为 blocked
- 外部 provider 路径仍保留，但应视为 fallback；真实 provider live validation 仍未证明完成

因此，当前状态应视为：

- `protocol-complete`
- `workflow-checked-in`
- `bridge-checked-in`
- `local-child-agent-mainline-validated-on-mac`
- `generic-cli-adapter-validated-with-fixture-agent`
- `e2e-runner-checked-in`
- `fixture-validated-on-mac`
- `mock-provider-validated-on-mac`
- `release-readiness-gate-checked-in`
- `provider-live-not-yet-validated`

而不是“已经 100% 可运行”。

---

## 不要当作真源的目录

以下内容只作为历史证据或运行产物，不作为当前实现真源：

- `reports/`
- `artifacts/`

---

## 开发优先级

如果继续开发 `/room`，优先顺序固定为：

1. 保持 `docs/`、`prompts/`、`examples/`、`.codex/skills/` 为真源
2. 保持 `.codex/skills/room-skill/runtime/` 与 `docs/room-runtime-bridge.md` 同步
3. 让真实宿主复用当前 bridge 的 state writeback 与 schema 校验
4. 跑通一轮带真实 prompt 调用的 `/room -> /summary -> /upgrade-to-debate`
5. 再推进更深的运行时整合

---

## 非目标

- 不把 `/room` 改造成普通群聊
- 不把 `/debate` 改造成 `/room`
- 不把历史报告搬进 source 目录伪装成源码
- 不在宿主执行缺失时假装项目已经 100% 完成
