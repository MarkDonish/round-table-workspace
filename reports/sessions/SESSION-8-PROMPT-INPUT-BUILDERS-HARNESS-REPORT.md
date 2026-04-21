# Session 8 Prompt Input Builders Harness Report

日期: 2026-04-12
范围: `room-chat.md` / `room-summary.md` 输入构造层

## 目标

在不调用 LLM 的前提下，把 harness 推进到 prompt input 可校验阶段：

- 从 room state + selected speakers 构造 `room_chat` 输入。
- 从 room state + previous summary 构造 `room_summary` 输入。
- 保证 `previous_summary` 必传，不由 summary prompt 猜历史。
- 保证 chat input 中的 speakers 被补齐 long_role / structural_role / turn_role。

## 新增文件

- `C:\Users\CLH\tools\room-orchestrator-harness\src\prompt-inputs.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\prompt-inputs.test.js`

## TDD 过程

RED:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\prompt-inputs.test.js
```

初次失败符合预期：`Cannot find module '../src/prompt-inputs.js'`。

GREEN:

实现最小构造层：

- `buildChatInput(roomState, options)`
- `buildSummaryInput(roomState, options)`
- `buildConversationHistory(conversationLog)`

## 验证结果

单文件验证:

- `prompt-inputs.test.js`: 2/2 PASS

全量 harness 验证:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js
```

结果:

- tests: 15
- pass: 15
- fail: 0

## 边界

当前模块只构造 prompt input，不生成 chat turn，不生成 summary_update，也不判断 prompt 输出质量。

下一步建议:

1. 做一个端到端 runtime substitute fixture：selection result -> chat input -> synthetic chat output -> state reducer -> summary input -> synthetic summary output -> Flow F input。
2. 再接 `room-upgrade.md` input builder 与 packet validator，形成完整 dry-run 链路。
3. 最后才接真实 LLM 调用。