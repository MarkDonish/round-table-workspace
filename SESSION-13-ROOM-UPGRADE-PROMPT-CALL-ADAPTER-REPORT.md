# Session 13: Room-upgrade prompt call adapter report

日期: 2026-04-13
工作区: `C:\Users\CLH\tools\room-orchestrator-harness`

## 本次目标

继续 P1 prompt-call 接入,在 `room-chat.md` 与 `room-summary.md` adapter 已完成的基础上,接入 `room-upgrade.md` adapter,使 dry-run 可以用可注入 executor 替换 deterministic packet builder fallback。

## 已完成

- `src/prompt-runner.js`
  - 新增 `room_upgrade` prompt path: `C:/Users/CLH/prompts/room-upgrade.md`
  - 新增 `runRoomUpgradePrompt()`,调用可注入 executor、解析 JSON/fenced JSON。
  - 新增 `validateUpgradePacketOutput()`,组合校验:
    - `validateHandoffPacket()`
    - `validateRoomUpgradeContract()`
    - `validateFlowFReadiness()`
  - 保留 `runRoomChatPrompt()` 与 `runRoomSummaryPrompt()` 行为不变。
- `src/dry-run.js`
  - `runDryRunWithPromptCalls()` 新增 `executors.room_upgrade` 支持。
  - summary 更新写回 state 后,再构造 `room_upgrade` input 并调用 upgrade executor。
  - final packet 优先使用 `room_upgrade` prompt call 输出,否则回退到 `buildHandoffPacketFromUpgradeInput()` deterministic fallback。
  - 保留原同步 `runDryRun()` synthetic fixture 路径不变。
- `test/prompt-runner.test.js`
  - 新增 `buildPromptRequest()` 读取 `room-upgrade.md` 的测试。
  - 新增 `runRoomUpgradePrompt()` 调用 executor 并校验 handoff packet contract 的测试。
- `test/dry-run.test.js`
  - 新增 dry-run 使用 `executors.room_upgrade` 替换 deterministic packet fallback 的测试。
- `README.md`
  - 更新 prompt adapter 能力说明为 chat / summary / upgrade 三段全覆盖。
  - 当前预期测试结果更新为 39 pass / 0 fail。

## TDD 记录

RED 已确认:

- `prompt-runner.test.js` 失败: `unsupported prompt mode: room_upgrade` / `runRoomUpgradePrompt is not a function`。
- `dry-run.test.js` 失败: `prompt_calls.length` 仍为 0,说明 `executors.room_upgrade` 尚未接入 dry-run。

GREEN 已确认:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\prompt-runner.test.js
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\dry-run.test.js
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js
```

全量结果: 39 tests / 39 pass / 0 fail。

## 当前状态

P1 prompt-call adapter layer 已完成三段:

1. `room-chat.md` adapter。
2. `room-summary.md` adapter。
3. `room-upgrade.md` adapter。

仍未完成:

- 尚未绑定真实 provider executor(OpenAI / Claude / 其他)或外部命令 executor。
- 当前 adapter 使用可注入 executor,仍不是实际联网 LLM 调用。
- P3 与 Flow F true live rerun 仍等待真实 executor 可用。
- F11/F16/F17/F18 等低优先级协议债尚未处理。

## 建议下一步

最高优先级: 接入具体 prompt executor,建议先做 provider-agnostic external executor,再接具体 SDK。

建议顺序:

1. 新增通用 external executor contract: 接收 `{ mode, prompt_path, prompt, input }`,返回 JSON 字符串或对象。
2. 给 `runDryRunWithPromptCalls()` 增加一个最小外部执行入口示例,但保留当前可注入 executor 作为测试 seam。
3. 三段 prompt 通过真实 executor 后,再跑 P3 与 Flow F true live rerun。
4. 再处理 F11/F16/F17/F18 等低优先级协议债。
