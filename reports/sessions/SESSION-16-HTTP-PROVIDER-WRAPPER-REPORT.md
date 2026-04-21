# Session 16: HTTP provider wrapper report

日期: 2026-04-13
工作区: `C:\Users\CLH\tools\room-orchestrator-harness`

## Token 使用审查

本轮按低 token 模式执行:

- 没有浏览网络。
- 没有读取大文件或无关历史报告。
- 没有引入 SDK 或安装依赖。
- 只围绕最高优先级新增 1 个 wrapper 与 1 个测试文件。
- 发现测试超时时,直接定位到 `spawnSync` 阻塞 mock HTTP server 的根因,没有扩大排查范围。

## 本次目标

在 Session 15 的 external executor contract 之后,新增一个最小 HTTP provider wrapper,作为真实 provider wrapper 的通用入口。它不绑定 OpenAI / Claude / 其他 SDK,只定义可验证的 HTTP JSON contract。

## 已完成

- 新增 `src/http-provider-wrapper.js`
  - 从 stdin 读取 prompt request JSON。
  - 使用 Node 内置 `fetch` POST 到 `ROOM_PROVIDER_URL`。
  - 可选 `ROOM_PROVIDER_AUTH_BEARER` 写入 Authorization Bearer header。
  - 支持 provider 返回 `{ output: ... }`,并将 `output` 解包写入 stdout。
  - 缺少 `ROOM_PROVIDER_URL` 时快速失败。
- 新增 `test/http-provider-wrapper.test.js`
  - 使用本地 mock HTTP server 验证 request POST、Bearer header、stdout JSON 输出。
  - 验证缺少 `ROOM_PROVIDER_URL` 的失败路径。
- 更新 `README.md`
  - external executor 能力说明增加 `http-provider-wrapper.js`。
  - 当前预期测试结果更新为 45 pass / 0 fail。

## TDD 记录

RED 已确认:

- `http-provider-wrapper.test.js` 初始失败于缺少 `src/http-provider-wrapper.js`。

实现中修正:

- 首轮测试超时不是 wrapper provider 逻辑失败,而是测试中 `spawnSync` 阻塞了同进程 mock HTTP server 的事件循环。
- 已将测试改为 async `spawn`,目标测试转 GREEN。

GREEN 已确认:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\http-provider-wrapper.test.js
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js
```

全量结果: 45 tests / 45 pass / 0 fail。

## 当前状态

已完成最小 HTTP provider wrapper,可以通过 Session 15 的 external executor CLI 作为外部命令入口使用。

仍未完成:

- 尚未接入真实 provider endpoint。
- 尚未用真实 provider 运行 `room_chat` / `room_summary` / `room_upgrade` 三段 prompt-call dry-run。
- 尚未执行 P3 与 Flow F true live rerun。
- F11/F16/F17/F18 等低优先级协议债尚未处理。

## 建议下一步

1. 配置一个真实 `ROOM_PROVIDER_URL` endpoint,或写一个 provider-specific 适配服务。
2. 用 CLI 执行:
   `node src/cli.js --dry-run-fixture D:\圆桌会议\SESSION-8-DRY-RUN-FIXTURE.json --prompt-executor node --prompt-executor-arg C:\Users\CLH\tools\room-orchestrator-harness\src\http-provider-wrapper.js`
3. 三段真实 prompt-call 通过后,执行 P3 与 Flow F true live rerun。
