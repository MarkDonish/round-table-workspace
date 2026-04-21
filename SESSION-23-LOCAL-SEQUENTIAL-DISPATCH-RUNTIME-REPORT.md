# Session 23: Local Sequential Dispatch Runtime Report

日期: 2026-04-16
工作区: `C:\Users\CLH\tools\room-orchestrator-harness`

## 本次目标

执行纠偏后的 P0: 不再以 provider/API 配置作为主线前置,而是实现 `/room` 的本地 speaker dispatch 基础层。

本轮范围限定为 harness 层的可执行本地顺序调度:

- selected speaker -> `agent-registry/registry.json`
- registry entry -> local skill path / `roundtable-profile.md`
- `room-chat.md` -> speaker task contract/template
- injected local speaker executor -> speaker output
- orchestrator -> 合成 Turn 并交给 state reducer

## 已完成

新增:

- `src/local-dispatch.js`
  - `loadAgentRegistry()`
  - `resolveLocalSpeaker()`
  - `buildLocalSpeakerTask()`
  - `runLocalSequentialChatTurn()`
- `test/local-dispatch.test.js`
  - registry/profile 解析
  - speaker task 构造
  - `local_sequential` 顺序执行与 Turn 合成
  - 无 provider 环境变量仍可执行

修改:

- `src/dry-run.js`
  - 新增 `runDryRunWithLocalDispatch()`
  - dry-run chat step 可用本地 dispatch 输出替代 synthetic turn
- `test/dry-run.test.js`
  - 新增本地 dispatch 替代 synthetic chat output 的集成测试
- `README.md`
  - 增加 Local sequential speaker dispatch 能力说明
  - 明确 provider wrappers 只是 optional adapter/CI/dry-run support,不是 `/room` runtime mainline
  - 测试期望更新为 `57 pass / 0 fail`

## TDD 证据

RED 1:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\local-dispatch.test.js'
```

结果: 失败于 `Cannot find module '../src/local-dispatch.js'`。

GREEN 1:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\local-dispatch.test.js'
```

结果: 4 tests / 4 pass / 0 fail。

RED 2:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\dry-run.test.js'
```

结果: 新增测试失败于 `runDryRunWithLocalDispatch is not a function`。

GREEN 2:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\dry-run.test.js'
```

结果: 7 tests / 7 pass / 0 fail。

全量验证:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'
```

结果:

```text
tests 57
pass 57
fail 0
```

## 当前边界

本轮没有实际调用 Codex `spawn_agent` 或 Claude `Task(...)`。原因是 harness 层不应绑定具体宿主 runtime。当前实现提供 `speakerExecutor` seam,上层 runtime 可以把它接到:

- Codex host 的本地 sequential 执行
- Codex host 允许时的 `spawn_agent(...)`
- Claude host 的 `Task(...)`

重要的是: 当前链路已经不需要 provider API key,也不会读取 `ROOM_CHAT_COMPLETIONS_URL` / `ROOM_CHAT_COMPLETIONS_MODEL` 才能执行本地 dispatch 测试。

## 下一步

P1 建议:

1. 在 harness 或 skill runtime 上层增加 host adapter:
   - `createCurrentAgentSpeakerExecutor()` 或等价命名
   - 使用 `room_speaker_task` 的 profile/context 在当前 agent 内顺序生成 speaker content
2. 继续保持 `speaker task 不能写 room_state`;只有 orchestrator 写 `conversation_log`。
3. 加测试覆盖 executor 异常、单 speaker blocked、warnings 聚合。
4. 再决定是否接 Codex `spawn_agent` 并行模式；没有明确授权时继续使用 `local_sequential`。

## 结论

P0 的可执行本地调度基础层已经落地。provider/API 路线已被降级为 optional adapter,不再阻塞 `/room` 主线。
