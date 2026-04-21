# Session 8 P3 — Minimal Orchestrator Harness Implementation Report

日期: 2026-04-12
范围: P3 §12 / @agent deterministic rule harness

## 目标

把 P3 prompt-level fixture 从一次性 PowerShell 验证升级成可复用的最小工程 harness。

## 新增文件

- `C:\Users\CLH\tools\room-orchestrator-harness\src\orchestrator.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\p3-fixtures.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`

## 实现范围

- 解析 `@short_name`
- 构造 `protected_speakers = with ∪ mentions ∪ topic @short_name`
- protected speaker 入场时替换最低分非 protected speaker
- §12 forced rebalance:
  - 无点名时,沉默 3 轮的 Munger 入场
  - 替换顺序:offensive → moderate → 非 protected 低分位
  - 有其他 @agent 时,未被点名的沉默者本轮跳过 forced rebalance
  - 被点名者已入场时,不重复 forced rebalance

## TDD 过程

RED:

- 先写 `test/p3-fixtures.test.js`
- 初次运行失败:`Cannot find module '../src/orchestrator.js'`

GREEN:

- 写入 `src/orchestrator.js` 最小实现
- 处理 fixture JSON BOM 读取问题
- 修正 fixture P3-C 期望:按“最低分非 protected speaker”规则,`@Munger` 应替换 `Karpathy`,不是 `Jobs`

## 验证结果

命令:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\p3-fixtures.test.js
```

结果:

- pass: 3
- fail: 0
- covered cases:
  - P3-A no mention forced rebalance
  - P3-B @Jobs protected
  - P3-C @Munger already included


## CLI

第一版已经可以直接运行 CLI。

单 case:

```powershell
node C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js --fixture D:\圆桌会议\SESSION-8-P3-LIVE-RERUN-FIXTURES.json --case P3-A-no-mention-forced-rebalance
```

全量 fixture:

```powershell
node C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js --fixture D:\圆桌会议\SESSION-8-P3-LIVE-RERUN-FIXTURES.json --all
```

实测全量结果:

- total: 3
- pass: 3
- fail: 0

## 边界

这不是完整 `/room` orchestrator。它只覆盖 P3 所需 deterministic rule engine。完整实现仍需要后续接入 room state、chat/summary/upgrade prompt 调用和命令解析。
