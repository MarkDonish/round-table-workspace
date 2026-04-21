# Roundtable `/room` 新对话交接 Prompt

把下面整段直接发到新对话里即可：

```text
继续 roundtable `/room` 项目开发。先不要重新发散，请直接基于现有代码和文档主线接力。

你当前要接手的是 `C:\Users\CLH\tools\room-orchestrator-harness` 这条 `/room` 主线，不是从零开始。

## 当前真实基线

- 当前日期：2026-04-18
- 最新真实测试基线：`116/116 pass`, `0 fail`
- 最新真实代码状态已经完成到 Session 37
- `D:\圆桌会议` 主文档目前只追平到 Session 35-36 / `114/114 pass`
- 所以当前是“代码领先 D 盘文档一轮”，不是文档领先代码

## 已完成的关键开发里程碑

### Session 35
- provider-backed execution 已正式进入 `/room` 的 multi-turn `command-flow` 主链
- 不再只停留在 dry-run / pressure verification

### Session 36
- full `/room` parser 已落地
- 当前支持：
  - `/room [--with ...] [--without ...] [--focus <text>] <topic>`
  - `/focus <text>`
  - `/unfocus`
  - `/add <agent>`
  - `/remove <agent>`
  - `/summary`
  - `/upgrade-to-debate`
  - `@agent ...`
  - 普通房间发言

### Session 37
- 当 `ROOM_CHAT_COMPLETIONS_URL` 和 `ROOM_CHAT_COMPLETIONS_MODEL` 存在时，`--command-flow-fixture` 现在默认走 provider-backed
- 新增显式回退：
  - `--execution-mode local_sequential`
  - `--execution-mode provider_backed`
- 仍保留自定义 `--prompt-executor`
- 本地 command-flow 回归测试现在会显式清空 provider env，避免机器环境把 local 回归偷切成 provider-backed

## 这几份文件是当前真源，先读

### 最新会话报告
- `C:\Users\CLH\SESSION-35-PROVIDER-BACKED-COMMAND-FLOW-BRIDGE-REPORT-2026-04-18.md`
- `C:\Users\CLH\SESSION-36-FULL-ROOM-PARSER-REPORT-2026-04-18.md`
- `C:\Users\CLH\SESSION-37-DEFAULT-PROVIDER-RUNTIME-REPORT-2026-04-18.md`

### 当前核心代码
- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\command-flow.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-command-parser.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\raw-room-command.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`

### 当前关键测试
- `C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\chat-completions-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\expanded-pool-fixtures.js`

### 当前 D 盘交接文档
- `D:\圆桌会议\NEXT-STEPS.md`
- `D:\圆桌会议\HANDOFF.md`
- `D:\圆桌会议\DEVELOPMENT-BOARD-PRIORITY-PROGRESS-2026-04-16-CORRECTED.md`

注意：这 3 份 D 盘文档目前还没写入 Session 37 和 `116/116 pass`。

## 当前最重要的项目判断

- `/debate` 已稳定闭环，不是当前主线
- `/room` 已经不是“能不能跑起来”的阶段
- `/room` 当前处于“runtime 主链基本闭环，剩余是文档追平和产品化收口”的阶段
- 现在最真实的 gap 已经从 parser / provider bridge，转移到：
  1. D 盘主文档追平 Session 37
  2. persistent room storage / resume
  3. UI 后置

## 当前建议优先级

### P1
先把 Session 37 和 `116/116 pass` 正式回写到：
- `D:\圆桌会议\NEXT-STEPS.md`
- `D:\圆桌会议\HANDOFF.md`
- `D:\圆桌会议\DEVELOPMENT-BOARD-PRIORITY-PROGRESS-2026-04-16-CORRECTED.md`

### P2
完成文档追平后，进入 `persistent room storage / resume` 的设计和实现

### P3
UI / 产品交互层继续后置

## 继续开发时必须记住的约束

- 不要回退已完成的 Session 35-37 能力
- 不要把 provider-backed 默认化改成“只能 provider 跑”，必须保留 local fallback
- 不要破坏 full `/room` parser 的现有命令面
- 不要把 local regression 测试重新暴露给 ambient provider env
- 除非用户明确要求，否则不要做大规模架构重写

## 当前可直接复跑的验证命令

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'
```

当前预期结果：

```text
tests 116
pass 116
fail 0
```

## 你进入新对话后的第一步

1. 先快速读 Session 37 报告和 D 盘 3 份主文档
2. 确认“代码领先文档一轮”这个判断
3. 直接执行 P1：把 Session 37 / `116/116 pass` 回写进 D 盘主文档
4. 回写后再汇报新的百分点量化进度，并进入 persistent room storage / resume

如果你发现代码状态与上述交接内容不一致，优先相信本地代码与测试结果，再指出文档哪里落后，不要反过来按旧文档回退代码。
```

## 交接包说明

- 这份 prompt 的目标不是“总结历史”，而是让新对话直接接住主线
- 当前最关键的事实是：
  - 代码已到 Session 37
  - D 盘文档还停在 Session 35-36
  - 下一步先同步文档，再进入 persistent storage / resume

