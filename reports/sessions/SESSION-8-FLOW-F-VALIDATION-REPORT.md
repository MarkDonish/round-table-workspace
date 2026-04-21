# Session 8 Flow F Validation Report

日期: 2026-04-12
范围: /room → /debate Flow F /upgrade-to-debate 协议级验证

## 结论

P0 后仍存在一个执行层缺口:F19。当前真实的 Session 7 summary 后状态只有 2 轮 `conversation_log`,会在 `room-upgrade.md` 校验 3 被提前拒绝,到不了 P0 新增的校验 5 user_explicit_request 例外。

本轮已补丁:
- C:\Users\CLH\prompts\room-upgrade.md:校验 3 增加 user_explicit_request 的 2 轮质量例外。
- C:\Users\CLH\.codex\skills\room-skill\SKILL.md:Flow F 前置校验同步 2 轮质量例外,避免 orchestrator 提前拒绝。
- C:\Users\CLH\docs\room-to-debate-handoff.md:版本升到 v0.1.3-p1,说明执行层 freshness guard 必须复用决议 43 的质量例外。

## RED 复现

使用 Session 7 的真实 summary 后状态:
- trigger=user_explicit
- reason=user_explicit_request
- conversation_log.length=2
- consensus=3, tension=3, open_questions=5
- recommended_next_step 非空
- stage=explore, turn_count=2

旧规则结果:校验 3 `conversation_log.length >= 3` 为 false,提前返回 `room_too_fresh`。

## GREEN 验证

补丁后同一状态的前置检查:

- check1_upgrade_signal: True
- check2_summary_nonempty: True
- check3_conversation_length_or_quality_exception: True
- check4_subproblems: True
- check5_stage_or_user_quality_exception: True

结果:Flow F 可以进入打包流程,但 packet 必须携带 `user_forced_early_upgrade` warning。

## Packet 样本

已生成验证样本:

D:\圆桌会议\SESSION-8-FLOW-F-VALIDATION-PACKET.json

注意:这是协议级验证夹具,不是 live runtime 的完整原始 conversation_log 重放。字段依据来自 D:\圆桌会议\VALIDATION-REPORT-e2e.md 的 Session 7 摘要;`source_room_id` 和 `field_02_room_title` 为验证夹具值。

验证覆盖:
- 5 条前置校验均可通过。
- `field_08_candidate_solutions.length` >= 1。
- `field_11_suggested_agents.length` == 4,位于 3-5 硬约束内。
- `field_12_suggested_agent_roles` 覆盖每个 suggested agent。
- `handoff_packet.field_13_upgrade_reason.warning_flags` 与 `packaging_meta.warnings` 均包含 user_forced_early_upgrade。
- packet 未泄露 `conversation_log`。

## 仍未完成

- 还没用真实 /room 运行时调用 `room-upgrade.md`;当前是协议级夹具验证。
- F14 task_type 权重仍暂缓,需要下一步用 Step 4 同题重跑 `room_turn` 后再决定。
- §12 强制补位第 3 轮、@agent 点名路径仍未覆盖。