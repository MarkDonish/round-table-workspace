# Session 10 Room Upgrade Contract Checklist Report

日期: 2026-04-13
范围: `C:\Users\CLH\tools\room-orchestrator-harness`

## 目标

完成 Session 9 建议下一步 P0: 将 deterministic packet builder 与 `prompts/room-upgrade.md` 的期望输出做字段级 diff checklist,并把 checklist 变成可运行测试。

## 新增文件

- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-upgrade-contract.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-upgrade-contract.test.js`

## 修改文件

- `C:\Users\CLH\tools\room-orchestrator-harness\src\packet-builder.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\packet-builder.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`

## 已完成

- 新增 `validateRoomUpgradeContract()` 作为 prompt-level contract checklist。
- checklist 覆盖内容:
  - `mode == room_upgrade`
  - `handoff_packet` 存在
  - `handoff_packet.schema_version / generated_at_turn / source_room_id`
  - `field_01..field_13` 完整字段集
  - `field_01/02/03/05/06/07` 与 `room_state` 的直接复制契约
  - `field_04_sub_problems` 的 SubProblem schema
  - `field_08_candidate_solutions` 的 CandidateSolution schema
  - `field_09_factual_claims` 的 FactualClaim schema
  - `field_10_uncertainty_points` 数组形状
  - `field_11_suggested_agents` 3-5 个已知 agent id
  - `field_12_suggested_agent_roles` 覆盖 field_11
  - `field_13_upgrade_reason` reason_code / reason_text / triggered_by / confidence / warning_flags
  - `user_forced_early_upgrade` 在 warning_flags 与 packaging_meta.warnings 中同步
  - `packaging_meta` counters 与数组字段
  - `meta.next_action == pass_packet_to_debate_skill`
  - packet 不包含 `conversation_log`
- 修正 `buildHandoffPacketFromUpgradeInput()` 输出以对齐 `room-upgrade.md`:
  - 将 `schema_version / generated_at_turn / source_room_id` 放入 `handoff_packet`
  - `field_03_type` 改为 `{ primary, secondary }`
  - `field_04_sub_problems` 从字符串数组规范化为 SubProblem 对象数组
  - `field_08_candidate_solutions` 改为 `solution_text / proposed_by / support_level / unresolved_concerns`
  - `field_13_upgrade_reason` 增加 `reason_text`
  - 增加 `packaging_meta.turns_scanned / solutions_extracted / claims_extracted / agents_filtered_out / agents_upgraded_in / warnings`
  - 增加 `meta.generated_at_turn / prompt_version / next_action`
- 修复一处实现细节: builder 不再原地修改 `readiness.warnings` 数组。

## TDD 记录

RED:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\room-upgrade-contract.test.js
```

失败点:

- 初次失败: `Cannot find module '../src/room-upgrade-contract.js'`
- contract checker 落地后失败: builder 缺 `handoff_packet` metadata、`field_03_type` 形状不符、CandidateSolution schema 不符、`reason_text` 缺失、`packaging_meta` 不完整、`meta.next_action` 缺失
- 加入 SubProblem 负向测试后,确认 checklist 能捕获 `field_04_sub_problems` 子 schema 错误

GREEN:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js
```

结果:

- tests: 28
- pass: 28
- fail: 0

## 当前状态

P0 已完成。deterministic packet builder 现在不仅通过原有 13 字段 presence validator,也通过 `room-upgrade.md` prompt-level contract checklist。

## 仍未完成

- 尚未接入真实 LLM prompt 调用。
- `room-chat.md` / `room-summary.md` / `room-upgrade.md` 仍未替换 synthetic outputs。
- P3 与 Flow F 的 true live prompt rerun 仍等待真实 prompt call 能力。
- F11/F16/F17/F18 等低优先级协议债尚未处理。

## 建议下一步

1. 进入 P1: 接入真实 prompt call 能力,建议先从 `room-chat.md` 开始。
2. 接入时保持小步验证:先让 dry-run 的单个 synthetic chat output 可替换为真实 room-chat 输出,再处理 summary,最后处理 upgrade。
3. 真实 prompt call 全链路可用后,再做 P3 与 Flow F true live rerun。
