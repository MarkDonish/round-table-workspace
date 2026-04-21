# Session 8 Flow F Harness Report

日期: 2026-04-12
范围: `/room` Flow F `/upgrade-to-debate` runtime 替代夹具与最小 harness

## 目标

把之前的 Flow F 协议级 packet 样本，推进到可重复执行的最小工程 harness：

- 校验 `room-upgrade.md` 前置条件中的 2 轮用户显式升级质量例外。
- 校验 `SESSION-8-FLOW-F-VALIDATION-PACKET.json` 是否满足 13 字段 handoff contract。
- 通过 CLI 提供可重复运行入口。

## 新增文件

- `C:\Users\CLH\tools\room-orchestrator-harness\src\flow-f.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\flow-f.test.js`
- `D:\圆桌会议\SESSION-8-FLOW-F-RUNTIME-FIXTURE.json`

## 修改文件

- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
- `D:\圆桌会议\NEXT-STEPS.md`

## TDD 过程

RED:

- 先写 `test/flow-f.test.js` 和 CLI 的 Flow F 用例。
- 初次运行失败点符合预期：`Cannot find module '../src/flow-f.js'`，CLI 也不认识 `--flow-f-fixture`。

GREEN:

- 新增 `validateFlowFReadiness(input)`：覆盖 5 条前置校验。
- 新增 `validateHandoffPacket(packet)`：覆盖 13 字段、candidate solutions、suggested agents 3-5、agent roles、warning flags、conversation_log 泄漏检查。
- 新增 CLI 入口：`--flow-f-fixture <fixture.json>`。

## 验证命令

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js
```

结果:

- tests: 10
- pass: 10
- fail: 0

Flow F CLI:

```powershell
node C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js --flow-f-fixture D:\圆桌会议\SESSION-8-FLOW-F-RUNTIME-FIXTURE.json
```

当前期望:

- `readiness.ready = true`
- `packet.pass = true`
- `readiness.warnings` 包含 `user_forced_early_upgrade`
- `packet.warnings` 包含 `user_forced_early_upgrade`

## 边界

这仍然不是完整真实 `/room` runtime。当前只验证 deterministic 前置校验和 handoff packet 形状；没有调用真实 LLM，也没有执行 `room-upgrade.md` 的 prompt 生成链路。

下一步应该继续把 room state、chat/summary/upgrade prompt 调用逐步接入 harness，而不是一次性重写完整 `/room` runtime。