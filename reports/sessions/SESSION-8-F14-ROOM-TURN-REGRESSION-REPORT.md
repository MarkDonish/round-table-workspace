# Session 8 F14 Room Turn Regression Report

日期: 2026-04-12
范围: F14 task_type 权重过重回归与补丁

## RED 复现

使用 Session 7 Step 4 同题:

> 那 All in 的具体路径是什么?Munger 说的零切换成本这件事怎么破?

在 v0.1.3-p1 下,P1 已经把 `role_uniqueness` 与 `redundancy_penalty` 归零,但 `room_turn` 仍使用建房阶段的 0-20 task_type 表。

复算结果:

| Agent | sub | task | stage | role | struct | pref | pen | adj | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Sun | 22 | 20 | 15 | 0 | 0 | 0 | 0 | 3 | 60 |
| PG | 14 | 20 | 15 | 0 | 0 | 0 | 0 | 0 | 49 |
| Jobs | 14 | 20 | 15 | 0 | 0 | 0 | 0 | 0 | 49 |
| Munger | 14 | 8 | 8 | 0 | 10 | 0 | 0 | 3 | 43 |

结论:通用 startup/strategy agent 仍有 `task_type_match + stage_fit = 35` 的底座,F14 仍存在。

## 补丁

修改文件:
- C:\Users\CLH\docs\room-selection-policy.md
- C:\Users\CLH\prompts\room-selection.md

版本:
- `room-selection-policy.md` §7.9 升级到 `v0.1.3-p2`
- `room-selection.md` 升级到 `v0.1.3-p2`

补丁内容:
- 只在 `mode == room_turn` 下弱化 `task_type_match`
- `room_full` 与 `roster_patch` 不受影响,仍使用原 20/15/8/0 表

新的 `room_turn` task_type 表:

| 条件 | room_turn 分数 |
|---|---:|
| 主类型命中 + 副类型命中 | 12 |
| 主类型命中 | 9 |
| 副类型命中 | 5 |
| 均不命中 | 0 |

## GREEN 验证

同题复算结果:

| Agent | sub | task | stage | role | struct | pref | pen | adj | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Sun | 22 | 12 | 15 | 0 | 0 | 0 | 0 | 3 | 52 |
| PG | 14 | 12 | 15 | 0 | 0 | 0 | 0 | 0 | 41 |
| Jobs | 14 | 12 | 15 | 0 | 0 | 0 | 0 | 0 | 41 |
| Munger | 14 | 5 | 8 | 0 | 10 | 0 | 0 | 3 | 40 |

关键指标:
- `room_turn task_type_match` 不再超过 12
- generic offensive vs defensive challenge 的分差从 6 降到 1
- 子问题差异重新成为更明显的信号
- 建房路径不受影响

验证命令输出:

```text
F14 room_turn regression passed
```

## 仍未覆盖

- 还没有真实 LLM live rerun,这是协议级复算。
- 由于 `room_turn` 仍允许 top 2-4,最终是否输出 3 人或 4 人仍取决于可执行 prompt 的人数裁剪判断。
- 下一步应补 §12 强制补位第 3 轮与 @agent 点名路径。