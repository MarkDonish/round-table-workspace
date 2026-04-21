# Task Priority Report

日期: 2026-04-13
依据:
- D:\圆桌会议\NEXT-STEPS.md
- D:\圆桌会议\SESSION-9-HARNESS-VALIDATORS-PACKET-BUILDER-REPORT.md
- D:\圆桌会议\HANDOFF.md
- D:\圆桌会议\DECISIONS-LOCKED.md

## 当前已完成的最近任务

- Session 9 已补齐 synthetic chat turn / summary_update schema validators。
- Session 9 已新增 deterministic room-upgrade packet builder fallback。
- dry-run 已串起 synthetic output validators、Flow F readiness、packet builder、packet validator。
- CLI --dry-run-fixture 退出码已依赖 output.pass。
- CLI negative dry-run 回归测试已覆盖非法 synthetic chat output 返回非 0。
- harness 全量测试记录为 26/26 PASS。

## 当前开放任务优先级

### P0 - 立即下一步: packet builder 与 room-upgrade.md 字段级 diff checklist

任务: 将 deterministic packet builder 的输出与 prompts/room-upgrade.md 的期望输出做字段级 diff checklist。

目的:
- 确认 13 字段 handoff packet 的每个字段来源、形状、缺省策略和禁止项都与 prompt contract 一致。
- 在接入真实 LLM prompt call 前，先消除 deterministic fallback 与真实 room-upgrade 输出之间的 schema 偏差。

建议产出:
- 新增一份 checklist 文档或测试夹具。
- 最好同步新增测试，覆盖 13 字段、sub-schema、warning_flags、candidate_solutions、suggested_agents、suggested_agent_roles、conversation_log 不泄露。

### P1 - 接入真实 prompt call 能力

任务: 在 P0 对齐后，逐步把 synthetic chat / summary / upgrade 替换为真实 prompt 输出。

建议顺序:
1. 先接 room-chat.md。
2. 再接 room-summary.md。
3. 最后接 room-upgrade.md。

约束:
- 不要一次性做完整 /room runtime。
- 继续沿用 harness 小步验证。
- prompt 仍是状态消费者；orchestrator/state reducer 才是状态写入方。

### P2 - P3 与 Flow F 的 true live rerun

任务: 有真实 LLM 调用能力后，重新跑 P3 和 Flow F live prompt 调用验证。

覆盖范围:
- P3 §12 强制补位。
- @agent 点名 protected_speakers 路径。
- Flow F user_explicit_request 早期升级例外。
- room-upgrade handoff packet 真实生成。

当前状态:
- 已有协议断言、规则模拟、prompt-level fixture rerun。
- 仍缺真实 /room orchestrator runtime / LLM live rerun。

### P3 - 低优先级协议债: F11/F16/F17/F18

任务: 在 P0-P2 完成后处理 F11/F16/F17/F18 等低优先级协议债。

当前信息:
- NEXT-STEPS 仅明确这些是低优先级协议债。
- 具体每项细节需回查对应 validation report。

### P4 - Phase 6: 原 skill mode 升级到 debate_room

任务: 将 13 个原 skill 的 mode 逐步升级到 debate_room。

约束:
- DECISIONS-LOCKED 记录当前不应提前启动。
- 必须等端到端链路和 v0.1.3/协议债处理稳定后再做。

### P5 - Phase 7: 自动发现扫描脚本

任务: 后续实现自动发现/扫描机制。

约束:
- 当前阶段不做自动发现扫描脚本。
- DECISIONS-LOCKED 中明确当前 registry 仍偏手工维护，自动发现属于长期项。

## 不建议现在做

- 不要回头重写已锁定的 room-architecture §1-§9。
- 不要回头重写 room-selection-policy v0.1.2 / room-selection.md v0.1.2。
- 不要跳过 P0/P1 直接进入 Phase 6 / Phase 7。
- 不要优先做 UI 或完整聊天室工程原型。
- 不要做 room state 持久化；当前协议仍不要求持久化落盘机制。

## 下一步执行建议

下一步开发任务就是 P0: 建立 packet builder 与 room-upgrade.md 的字段级 diff checklist，并尽量把 checklist 转成可运行测试。完成后再进入真实 prompt call 接入。
