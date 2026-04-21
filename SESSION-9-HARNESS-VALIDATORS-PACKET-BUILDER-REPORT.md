# Session 9 Harness Validators + Packet Builder Report

日期: 2026-04-12
范围: `C:\Users\CLH\tools\room-orchestrator-harness`

## 目标

按接力优先级补齐 Session 8 dry-run harness 的两个最高优先级缺口:

1. synthetic chat / summary 输出 schema validators。
2. deterministic room-upgrade packet builder fallback,从 dry-run final_state 自动生成 13 字段 handoff packet,并复用现有 `validateHandoffPacket()` 验证。

## 新增文件

- `C:\Users\CLH\tools\room-orchestrator-harness\src\validators.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\validators.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\packet-builder.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\packet-builder.test.js`

## 修改文件

- `C:\Users\CLH\tools\room-orchestrator-harness\src\dry-run.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\dry-run.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`

## 已完成

- 新增 `validateChatTurnOutput()`:
  - 校验 `turn_id`
  - 校验 `stage`
  - 校验 `speakers[]`
  - 校验 speaker `agent_id / short_name / role / content`
  - 校验 `cited_agents` 如存在必须是数组
- 新增 `validateSummaryUpdateOutput()`:
  - 校验 `summary_update` 对象
  - 校验 `consensus_points / open_questions / tension_points` 为数组
  - 校验 `recommended_next_step` 为 string 或 null
- 新增 `buildHandoffPacketFromUpgradeInput()`:
  - 从 `upgrade_input.room_state` 生成 13 字段 handoff packet
  - 不复制 `conversation_log`
  - 从 `recommended_next_step` 生成最小 candidate solution
  - 从 `agents / agent_roles` 生成 `field_11_suggested_agents` 与 `field_12_suggested_agent_roles`
  - 将 readiness warnings 同步到 `field_13_upgrade_reason.warning_flags` 与 `packaging_meta.warnings`
- `runDryRun()` 已串起:
  - chat input builder
  - chat synthetic output validator
  - state reducer
  - summary input builder
  - summary synthetic output validator
  - Flow F readiness
  - deterministic packet builder
  - packet validator
- CLI 的 `--dry-run-fixture` 退出码改为依赖 `output.pass`,不再只看 `readiness.ready`。

## TDD 验证

RED 已确认:

- `validators.test.js` 初次失败于 `Cannot find module '../src/validators.js'`。
- `packet-builder.test.js` 初次失败于 `Cannot find module '../src/packet-builder.js'`。
- `dry-run.test.js` / `cli.test.js` 初次失败于缺少 `chat_output_validations / packet_validation / packet` 输出字段。

GREEN:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js
```

结果:

- tests: 26
- pass: 26
- fail: 0

## 当前 dry-run 语义

`--dry-run-fixture` 现在验证的不只是状态链路,还包括:

- synthetic chat Turn schema 合法
- synthetic summary_update schema 合法
- Flow F readiness 合法
- deterministic handoff packet contract 合法
- packet 未泄露 `conversation_log`

## 仍未完成

- 仍未接入真实 LLM prompt 调用。
- packet builder 是 deterministic fallback,不是 `room-upgrade.md` 的真实自然语言打包输出。
- F11/F16/F17/F18 等低优先级协议债尚未处理。

## 建议下一步

1. 将 deterministic packet builder 与 `room-upgrade.md` prompt 输出做一次字段级 diff checklist，为真实 LLM 接入做准备。
2. 有真实 prompt call 能力后,逐步把 synthetic chat / summary / upgrade 替换为真实 prompt 输出。

## 追加验证:CLI negative dry-run fixture

本轮补充 `cli.test.js` 回归覆盖:

- 构造临时 dry-run fixture。
- 将第一条 synthetic chat output 的 speaker content 置空。
- 执行 `--dry-run-fixture <invalid fixture>`。
- 断言 CLI exit code 为 1。
- 断言 stdout 中 `pass=false`,且 `chat_output_validations[0]` 包含 `speaker[0].content must be non-empty string`。

该测试首次运行即通过,说明 Session 9 主实现已经具备该行为;本追加只补覆盖,未改生产代码。



