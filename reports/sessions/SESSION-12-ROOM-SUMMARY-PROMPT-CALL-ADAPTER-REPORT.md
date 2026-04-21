# Session 12: Room-summary prompt call adapter report

日期: 2026-04-13
工作区: `C:\Users\CLH\tools\room-orchestrator-harness`

## 本次目标

继续 P1 prompt-call 接入,在 Session 11 已完成 `room-chat.md` adapter 的基础上,接入 `room-summary.md` adapter,使 dry-run 可以用可注入 executor 替换 synthetic summary output。

## 已完成

- `src/prompt-runner.js`
  - 新增 `room_summary` prompt path: `C:/Users/CLH/prompts/room-summary.md`
  - 新增通用 `runPromptWithValidation()` 内部流程,复用 prompt 加载、executor 调用、JSON/fenced JSON 解析、输出校验和错误回传。
  - 新增 `runRoomSummaryPrompt()`,复用 `validateSummaryUpdateOutput()` 校验 summary-update 输出。
  - 保留 `runRoomChatPrompt()` 行为不变。
- `src/dry-run.js`
  - `runDryRunWithPromptCalls()` 新增 `executors.room_summary` 支持。
  - final summary step 允许优先使用 `room_summary` prompt call 输出,否则回退到原 synthetic fixture 输出。
  - 保留原同步 `runDryRun()` synthetic fixture 路径不变。
- `test/prompt-runner.test.js`
  - 新增 `buildPromptRequest()` 读取 `room-summary.md` 的测试。
  - 新增 `runRoomSummaryPrompt()` 调用 executor、解析 JSON、校验 summary output 的测试。
- `test/dry-run.test.js`
  - 新增 dry-run 使用 `executors.room_summary` 替换 synthetic summary output 的测试。
- `README.md`
  - 更新 prompt adapter 能力说明。
  - 当前预期测试结果更新为 36 pass / 0 fail。

## TDD 记录

RED 已确认:

- `prompt-runner.test.js` 最初失败: `unsupported prompt mode: room_summary` / `runRoomSummaryPrompt is not defined`。
- `dry-run.test.js` 最初失败: summary step 仍依赖 synthetic summary,缺少 prompt-call summary 输出接入。

GREEN 已确认:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\prompt-runner.test.js
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\dry-run.test.js
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js
```

全量结果: 36 tests / 36 pass / 0 fail。

## 当前状态

P1 已完成两段:

1. `room-chat.md` prompt call adapter。
2. `room-summary.md` prompt call adapter。

仍未完成:

- `room-upgrade.md` prompt call adapter 尚未接入。
- 尚未绑定真实 provider executor(OpenAI / Claude / 其他)。
- P3 与 Flow F true live rerun 仍等待三段 prompt adapter 与真实 executor 可用。
- F11/F16/F17/F18 等低优先级协议债尚未处理。

## 建议下一步

最高优先级: 继续 P1,接入 `room-upgrade.md` prompt call adapter。

建议顺序:

1. 在 `prompt-runner.js` 中增加 `runRoomUpgradePrompt()`。
2. 读取 `C:/Users/CLH/prompts/room-upgrade.md` 并绑定 `room_upgrade` 输入。
3. 复用 `validateHandoffPacket()` 与 `validateRoomUpgradeContract()` 校验输出。
4. 在 dry-run prompt-call 路径中允许 `executors.room_upgrade` 替换 deterministic packet builder fallback。
5. 三个 prompt adapter 全部跑通后,再接真实 provider SDK 或外部 executor。
