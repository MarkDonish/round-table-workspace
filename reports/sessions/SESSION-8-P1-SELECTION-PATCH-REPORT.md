# Session 8 P1 Selection Patch Report

日期: 2026-04-12
范围: /room selection 协议稳定性补丁

## 本轮已修

### F9 / F15: room_turn 单轮调度稳定性

修改文件:
- C:\Users\CLH\docs\room-selection-policy.md
- C:\Users\CLH\prompts\room-selection.md

新增规则:
- `mode == room_turn` 时,`role_uniqueness = 0`
- `mode == room_turn` 时,`redundancy_penalty = 0`
- `room_turn` 不再拿当前 2-8 人花名册重算 roster 级信息增量
- `room_turn` 不再用「与 top 3 重复」或「dominant 过载」惩罚挤掉已入 roster 的成员
- `room_full` / `roster_patch` 仍保留原完整打分规则

修复意图:
- 花名册负责「谁有资格参会」
- 单轮调度负责「本轮谁先发言」
- 避免同一 agent 在不同轮次因为候选池缩小或冗余惩罚而随机出入

### F13: simulate 阶段锚定词覆盖

修改文件:
- C:\Users\CLH\docs\room-selection-policy.md
- C:\Users\CLH\prompts\room-selection.md

新增 simulate 锚定词:
- 具体路径
- 怎么破
- 怎么做到
- 具体到

### Flow 一致性:普通用户发言触发描述

修改文件:
- C:\Users\CLH\docs\room-selection-policy.md

修正:
- 原文旧表述「普通用户发言不重跑」已改为「普通用户发言只跑 `room_turn`,不全量重建花名册」
- 与 `C:\Users\CLH\.codex\skills\room-skill\SKILL.md` 的 Flow E 保持一致

## 本轮暂缓

### F14: task_type 权重过重

暂缓原因:
- 这是权重层调参,会影响 Session 3 / Session 4 已验证过的三题分布
- 当前 F9/F15 修改已经改变了 `room_turn` 的总分构成,需要先做活体回归再决定是否下调 `task_type_match` 或加入 subproblem 放大系数

建议下一步:
- 用 Session 7 Step 4 的同一题重跑 room_turn
- 观察 PG / Jobs / Munger 的相对顺序
- 如果 `task_type_match + stage_fit` 仍明显压制子问题信号,再进入 F14 权重补丁

## 验证

已运行协议级断言:

```text
P1 selection contract validation passed
```

验证覆盖:
- policy / prompt 均包含 P1 room_turn 覆盖规则
- policy / prompt 均包含新增 simulate 锚定词
- policy 普通用户发言触发描述已修正
- policy 不再保留旧的「输出本轮发言者名单 + 每人本轮职责」描述
- prompt 不再保留旧的「每人本轮职责」描述
- 未检测到 PowerShell 替换引入的 CRLF 转义字面量

## 变更文件

- C:\Users\CLH\docs\room-selection-policy.md
- C:\Users\CLH\prompts\room-selection.md
- D:\圆桌会议\SESSION-8-P1-SELECTION-PATCH-REPORT.md