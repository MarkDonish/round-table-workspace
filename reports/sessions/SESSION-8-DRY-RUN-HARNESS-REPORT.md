# Session 8 Dry-Run Harness Report

日期: 2026-04-12
范围: 不调用 LLM 的端到端 runtime substitute

## 目标

把当前 harness 从模块级验证推进到第一条完整 dry-run 链路：

selection result -> chat input -> synthetic chat output -> state reducer -> summary input -> synthetic summary output -> Flow F input -> Flow F readiness

## 新增文件

- `C:\Users\CLH\tools\room-orchestrator-harness\src\dry-run.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\dry-run.test.js`
- `D:\圆桌会议\SESSION-8-DRY-RUN-FIXTURE.json`

## 修改文件

- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
- `D:\圆桌会议\NEXT-STEPS.md`

## TDD 过程

RED:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\dry-run.test.js
```

初次失败符合预期：`Cannot find module '../src/dry-run.js'`。

随后为 CLI 增补 `--dry-run-fixture` 测试，初次失败符合预期：CLI 不认识该参数。

GREEN:

- 新增 `runDryRun(fixture)`。
- 新增 synthetic dry-run fixture，明确标注不是 LLM 输出。
- 新增 CLI 入口：`--dry-run-fixture <fixture.json>`。

## 验证命令

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js
```

结果:

- tests: 17
- pass: 17
- fail: 0

Dry-run CLI:

```powershell
node C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js --dry-run-fixture D:\圆桌会议\SESSION-8-DRY-RUN-FIXTURE.json
```

结果关键字段:

- `mode = room_dry_run`
- `chat_inputs.length = 2`
- `summary_input.conversation_log.length = 2`
- `final_state.turn_count = 2`
- `upgrade_input.mode = room_upgrade`
- `readiness.ready = true`
- `readiness.warnings = ["user_forced_early_upgrade"]`

## 边界

这仍不是 live LLM rerun。`synthetic_turn` 和 `synthetic_summary` 是夹具里的假输出，只用于验证状态链路与输入形状。

下一步建议:

1. 为 synthetic chat/summary 输出增加 schema validator。
2. 接 `room-upgrade.md` packet builder 的 deterministic fallback，减少对手写 packet 样本的依赖。
3. 有真实 LLM 调用能力后，把 synthetic steps 替换为 prompt call 结果。