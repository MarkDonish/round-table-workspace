# Session 17: Chat Completions-compatible wrapper report

日期: 2026-04-13
工作区: `C:\Users\CLH\tools\room-orchestrator-harness`

## Token 使用审查

本轮继续低 token 模式:

- 未浏览网络。
- 未读取大文件。
- 未安装依赖或接入 SDK。
- 只新增一个 Chat Completions 风格 wrapper 与一个测试文件。
- 使用本地 mock HTTP server 验证 contract,不消耗真实 provider token。

## 本次目标

在 `http-provider-wrapper.js` 的通用 HTTP JSON contract 之外,新增一个 Chat Completions-compatible wrapper,用于把 prompt request 转换成常见 chat-completions 请求体。仍不绑定具体 provider SDK。

## 已完成

- 新增 `src/chat-completions-wrapper.js`
  - 从 stdin 读取 prompt request JSON。
  - 读取 `ROOM_CHAT_COMPLETIONS_URL` 与 `ROOM_CHAT_COMPLETIONS_MODEL`。
  - 可选 `ROOM_PROVIDER_AUTH_BEARER` 写入 Authorization Bearer header。
  - 将 `request.prompt` 写入 system message。
  - 将 `request.input` 序列化后写入 user message。
  - 请求体带 `response_format: { type: "json_object" }`。
  - 从 `choices[0].message.content` 提取 assistant content 并写到 stdout。
- 新增 `test/chat-completions-wrapper.test.js`
  - 使用本地 mock HTTP server 验证消息映射、model、Bearer header、stdout 输出。
  - 验证缺少 endpoint/model 的失败路径。
- 更新 `README.md`
  - 增加 `chat-completions-wrapper.js` 能力说明。
  - 当前预期测试结果更新为 47 pass / 0 fail。

## TDD 记录

RED 已确认:

- `chat-completions-wrapper.test.js` 初始失败于缺少 `src/chat-completions-wrapper.js`。

GREEN 已确认:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\chat-completions-wrapper.test.js
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js
```

全量结果: 47 tests / 47 pass / 0 fail。

## 当前状态

现在有两种 provider wrapper:

1. `http-provider-wrapper.js`: provider 直接理解 room prompt request JSON。
2. `chat-completions-wrapper.js`: provider 接收 Chat Completions-style body,返回 `choices[0].message.content`。

仍未完成:

- 尚未配置真实 `ROOM_CHAT_COMPLETIONS_URL` / `ROOM_CHAT_COMPLETIONS_MODEL`。
- 尚未用真实 provider 跑三段 prompt-call dry-run。
- P3 与 Flow F true live rerun 仍等待真实 provider 输出。

## 建议下一步

1. 配置真实 Chat Completions-compatible endpoint 环境变量。
2. 用 external executor CLI 调用 `chat-completions-wrapper.js` 跑 dry-run。
3. 三段真实 prompt-call 通过后,执行 P3 与 Flow F true live rerun。
