# Session 15: Provider-agnostic external executor contract report

日期: 2026-04-13
工作区: `C:\Users\CLH\tools\room-orchestrator-harness`

## 本次目标

继续 Session 14 审查后的 P0: 完成 provider-agnostic external executor contract,让 CLI dry-run 可以通过外部命令执行 `room_chat` / `room_summary` / `room_upgrade` 三段 prompt-call,但不绑定具体 provider SDK。

## 已完成

- 新增 `src/external-executor.js`
  - `createExternalExecutor(command, args)`:
    - 每次 prompt call 启动外部命令。
    - 将 prompt request JSON 写入 stdin。
    - 从 stdout 读取返回 JSON 字符串。
    - 非 0 退出码抛出 `external executor failed with code ...` 错误。
  - `createDryRunExternalExecutors(command, args)`:
    - 返回 `room_chat` / `room_summary` / `room_upgrade` 三个 executor。
    - 三段 prompt 共享同一个 provider-agnostic 外部命令,由 request.mode 在外部命令内分发。
- 更新 `src/cli.js`
  - 新增 `--prompt-executor <command>`。
  - 新增可重复 `--prompt-executor-arg <arg>`。
  - `--dry-run-fixture` 支持 external executor 全链路 dry-run。
  - 保留原无 executor 的 deterministic dry-run 路径。
  - CLI 主入口改为 async,以支持外部 executor prompt-call。
- 新增 `test/external-executor.test.js`
  - 覆盖 stdin request / stdout response contract。
  - 覆盖外部命令非 0 退出码错误回传。
  - 覆盖 dry-run 三段 executor factory。
- 更新 `test/cli.test.js`
  - 新增 CLI dry-run 通过外部 executor 执行 chat / summary / upgrade 三段 prompt-call 的端到端测试。
- 更新 `README.md`
  - 增加 external executor contract 能力说明。
  - 当前预期测试结果更新为 43 pass / 0 fail。

## TDD 记录

RED 已确认:

- `test/external-executor.test.js`: 失败于缺少 `src/external-executor.js`。
- `test/cli.test.js`: 失败于 CLI 尚不识别 `--prompt-executor`。

GREEN 已确认:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\external-executor.test.js
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js
```

全量结果: 43 tests / 43 pass / 0 fail。

## 当前状态

已完成从“可注入测试 executor”到“provider-agnostic external command executor”的过渡层。

仍未完成:

- 尚未绑定真实 provider SDK(OpenAI / Claude / 其他)。
- 尚未提供真实 provider wrapper 脚本。
- 尚未执行 P3 与 Flow F true live rerun。
- F11/F16/F17/F18 等低优先级协议债尚未处理。

## 建议下一步

最高优先级: 新增真实 provider wrapper 或最小外部命令包装器。

建议顺序:

1. 选择 provider/命令入口,先实现一个 wrapper: stdin 接收 prompt request JSON,stdout 返回 prompt 输出 JSON。
2. 用 CLI 执行:
   `node src/cli.js --dry-run-fixture D:\圆桌会议\SESSION-8-DRY-RUN-FIXTURE.json --prompt-executor <command> --prompt-executor-arg <wrapper>`
3. 三段真实 prompt-call 通过后,再执行 P3 与 Flow F true live rerun。
4. 最后处理 F11/F16/F17/F18 等低优先级协议债。
