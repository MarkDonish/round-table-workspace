# Session 11 Room Chat Prompt Call Adapter Report

日期: 2026-04-13
范围: `C:\Users\CLH\tools\room-orchestrator-harness`

## 目标

执行 P1 的第一步: 先接入 `room-chat.md` 的真实 prompt call 边界,让 dry-run 的 chat output 可以从 synthetic fixture 输出替换为 prompt executor 输出。

本轮不绑定具体 OpenAI / Claude SDK,而是落地可注入 executor 接口。真实 provider 后续只需要实现 executor,不需要改 state reducer 和 dry-run 主链路。

## 新增文件

- `C:\Users\CLH\tools\room-orchestrator-harness\src\prompt-runner.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\prompt-runner.test.js`

## 修改文件

- `C:\Users\CLH\tools\room-orchestrator-harness\src\dry-run.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\dry-run.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`

## 已完成

- 新增 `buildPromptRequest(mode, input, options)`:
  - 读取 `C:\Users\CLH\prompts\room-chat.md`
  - 将 prompt markdown 与结构化 `room_chat` input 绑定成 request
- 新增 `parsePromptJson(response)`:
  - 支持 raw JSON
  - 支持 ```json fenced JSON
  - 支持响应文本中包裹 JSON 对象的情况
- 新增 `runRoomChatPrompt(chatInput, executor, options)`:
  - 调用注入的 executor
  - 解析 JSON 输出
  - 复用 `validateChatTurnOutput()` 校验 Turn schema
  - invalid JSON 时返回 `pass=false` 与 `error.code=invalid_json`
- 新增 `runDryRunWithPromptCalls(fixture, executors)`:
  - 保留原 `runDryRun()` 同步 synthetic 路径不变
  - 新异步路径可用 `executors.room_chat` 替换 chat synthetic output
  - 替换后继续复用 state reducer、summary synthetic output、Flow F readiness、packet builder、packet validator
- 新增 dry-run 集成测试:
  - 删除 fixture 第一条 `synthetic_turn`
  - 使用 fake `room_chat` executor 返回 JSON Turn
  - 确认 prompt call output 被写入 `conversation_log`

## TDD 记录

RED:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\prompt-runner.test.js
```

失败点:

- 初次失败: `Cannot find module '../src/prompt-runner.js'`

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\dry-run.test.js
```

失败点:

- 新增集成测试失败: `runDryRunWithPromptCalls is not a function`

GREEN:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js
```

结果:

- tests: 33
- pass: 33
- fail: 0

## 当前状态

P1 已完成第一段: `room-chat.md` 的 prompt call adapter 和 dry-run 替换边界已落地。

这还不是完整真实 LLM 接入:当前没有绑定具体 provider SDK,也没有 CLI 参数直接调用云端模型。executor 接口已经留好,下一步可以安全接具体 provider。

## 仍未完成

- 尚未接入真实 provider executor(OpenAI / Claude / 其他)。
- `room-summary.md` 的 prompt call adapter 仍未接入。
- `room-upgrade.md` 的 prompt call adapter 仍未接入。
- P3 与 Flow F true live rerun 仍等待真实 prompt call 能力。
- F11/F16/F17/F18 等低优先级协议债尚未处理。

## 建议下一步

1. 继续 P1: 为 `room-summary.md` 增加同样的 prompt runner adapter,让 summary synthetic output 也可被 executor 输出替换。
2. 然后接 `room-upgrade.md` prompt runner adapter,复用 Session 10 的 `validateRoomUpgradeContract()` 做输出校验。
3. 三个 prompt adapter 都跑通后,再绑定真实 provider SDK 或外部 executor。
