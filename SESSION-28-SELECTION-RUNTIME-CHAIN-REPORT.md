# SESSION 28 - selection output -> local runtime chain report

日期: 2026-04-17
工作区: C:\Users\CLH\tools\room-orchestrator-harness

## 本轮目标

完成 `selection output -> runRoomTurnWithLocalDispatch()` 的完整本地链路,不回退到 provider/API 主线。

## 已完成

1. 新增 `src/selection-runtime.js`
   - `mapSelectedSpeakersToRoomState()`
   - `runSelectionToLocalRuntime()`
2. 新增 selection-to-runtime 防回归测试
   - `test/selection-runtime.test.js`
3. 扩展 CLI
   - 新增 `--selection-runtime-fixture`
   - 使用 `SESSION-28-SELECTION-TO-LOCAL-RUNTIME-FIXTURE.json`
4. CLI 输出压缩
   - 不打印完整 `room_chat_contract`
   - 不打印 `profile_text`
5. README 同步
   - 增加 selection-to-runtime 运行方式

## 新增 D 盘 fixture

- `D:\圆桌会议\SESSION-28-SELECTION-TO-LOCAL-RUNTIME-FIXTURE.json`

## 验证

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\selection-runtime.test.js'
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js'
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'
```

当时结果:

```text
tests 68
pass 68
fail 0
```

## 结论

selection 输出已经能进入本地 runtime mainline,并穿过 state reducer 落地到最终 room state。下一步不再是“有没有本地链路”,而是“协议细节是否与 architecture 完全对齐”。
