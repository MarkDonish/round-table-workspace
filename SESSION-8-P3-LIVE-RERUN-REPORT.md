# Session 8 P3 — §12 / @agent Prompt-Level Live Rerun Report

日期: 2026-04-12
范围: P3 §12 强制补位与 @agent 点名路径

## 结论

本次完成的是 **prompt-level live rerun / fixture rerun**，不是完整真实 `/room` orchestrator 运行。

原因:在以下项目相关目录内只找到 markdown prompt / protocol / report 文件，没有找到可执行的 `/room` orchestrator 实现文件。

- `C:\Users\CLH\docs`
- `C:\Users\CLH\prompts`
- `C:\Users\CLH\.codex\skills\room-skill`
- `C:\Users\CLH\agent-registry`
- `D:\圆桌会议`

因此不能诚实地声称完成了“真实 runtime live rerun”。本次验证覆盖的是 P3 协议的不变量与 Flow E 输入/输出夹具。

## 产物

- `D:\圆桌会议\SESSION-8-P3-LIVE-RERUN-FIXTURES.json`
- `D:\圆桌会议\SESSION-8-P3-LIVE-RERUN-REPORT.md`

## 覆盖场景

### P3-A: 无点名 + Munger 连续沉默 3 轮

输入要点:

- `mode = room_turn`
- `topic = 具体到下一步怎么做?`
- `user_constraints.mentions = []`
- `silent_rounds.Munger = 3`
- 常规 top4: `Sun / PG / Jobs / Karpathy`

预期:

- 触发 forced rebalance
- `Munger` 必须进入本轮 speakers
- 替换最低分 `structural_role=offensive` 的 `Jobs`

验证结果:PASS

### P3-B: `@Jobs` 点名 + Munger 连续沉默 3 轮

输入要点:

- `topic = @Jobs 具体到下一步怎么做?`
- `user_constraints.mentions = [Jobs]`
- `silent_rounds.Munger = 3`
- 常规 top4: `Sun / PG / Karpathy / Taleb`

预期:

- `Jobs` 作为 protected speaker 必须进入 speakers
- 未被点名的 `Munger` 本轮因 `explicit_mention_elsewhere` 跳过强制补位
- `Munger` 不能挤掉 `Jobs`

验证结果:PASS

### P3-C: `@Munger` 点名 + Munger 连续沉默 3 轮

输入要点:

- `topic = @Munger 你来审一下风险`
- `user_constraints.mentions = [Munger]`
- `silent_rounds.Munger = 3`
- 常规 top4: `Sun / PG / Jobs / Karpathy`

预期:

- `Munger` 作为 protected speaker 必须进入 speakers
- §12 不再重复触发 forced rebalance
- skip reason 为 `agent_was_auto_included`

验证结果:PASS

## 验证命令结果

- 首次 RED:验证器失败,暴露 PowerShell 动态属性/数组传参问题。
- 修正验证器后 GREEN:
  - `P3_LIVE_RERUN_FIXTURE_VALIDATION: passed`
  - `P3_LIVE_RERUN_CASES: 3/3 passed`

## 剩余风险

- 真实 LLM 是否会严格按 `room-selection.md v0.1.3-p3` 输出 `forced_rebalance` / `warnings` 字段,仍需实际 prompt 调用验证。
- 真实 `/room` orchestrator 仍不存在可执行实现,当前只有 `room-skill/SKILL.md` 的编排说明。
- 如果后续实现真实 orchestrator,必须把本夹具转成自动化测试,覆盖 `@Jobs`、`@Munger`、无点名强制补位三条路径。

## 下一步

1. 若要继续验证协议链路,优先做 Flow F 真实运行时替代夹具,同样明确 runtime 缺失边界。
2. 若要进入工程实现,先创建最小 `/room` orchestrator harness,把本报告的三个 cases 转为自动化测试。
