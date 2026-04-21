# Session 8 P3 — §12 强制补位与 @agent 点名路径补丁报告

日期: 2026-04-12
范围: `/room` 的 `room_turn` 单轮调度协议

## 目标

把 §12 第 3 轮强制补位与 `@agent` 点名路径从“prompt 文字建议”收敛为可执行契约。

## RED 结果

协议断言按预期失败,缺口如下:

- selection policy 输入 schema 未暴露 `user_constraints.mentions`
- selection prompt 输入 schema 未暴露 `user_constraints.mentions`
- `room_turn` 未在强制补位前保护点名者
- §12 强制补位替换目标未明确排除点名者
- Flow E 未把 `@short_name` 解析结果传入 `user_constraints.mentions`
- architecture 的 `@<agent>` 路径仍使用 `parsed_topic.constraints.mentions`,不是输入侧硬约束

## 修改文件

- `C:\Users\CLH\docs\room-selection-policy.md`
- `C:\Users\CLH\prompts\room-selection.md`
- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`
- `C:\Users\CLH\docs\room-architecture.md`

## 关键变更

1. 新增 `user_constraints.mentions` 输入契约。
2. Flow E 在调用 `room-selection.md` 前解析 `@short_name`,并写入 `user_constraints.mentions`。
3. `room_turn` 先构造 `protected_speakers = with ∪ mentions ∪ topic 中的 @short_name`。
4. `protected_speakers` 必须进入本轮 `speakers[]`,但仍受硬过滤和当前 roster 限制。
5. §12 强制补位替换目标必须排除 `protected_speakers`。
6. §12 替换顺序收敛为:
   - 先替换分数最低的 `structural_role=offensive`
   - 再替换分数最低的 `structural_role=moderate`
   - 最后替换分数最低的非 protected speaker
7. 清理旧冲突口径:
   - 不再写 `dominant/offensive 位` 作为替换目标
   - architecture 不再写“替换最低分非 primary / 非 challenge”作为强制补位规则
8. 同步 E-1.1 琐碎度降级豁免口径:多点名判断改用 `user_constraints.with ∪ user_constraints.mentions ∪ topic @short_name`。

## GREEN 验证

已通过文本契约断言:

- `room-selection-policy.md` 包含 `mentions:      [Agent 列表,可空,@点名解析结果]`
- `room-selection.md` 包含 `mentions:        [Agent short_name 列表,@点名解析结果]`
- `room-selection.md` 包含 `先解析 --with / @点名 为 protected_speakers`
- `room-selection-policy.md` 包含 `替换目标必须排除 protected_speakers`
- `room-skill/SKILL.md` 包含 `user_constraints.mentions = 从 user_input 中解析出的 @short_name 列表`
- `room-architecture.md` 包含 `user_constraints.mentions`
- `room-selection-policy.md` 不再包含旧替换目标 `dominant/offensive 位`
- `room-architecture.md` 的强制补位说明已包含 protected speaker 排除规则

已通过规则模拟:

- 无点名时: `Munger` 连续沉默 3 轮,强制补位进入 speakers,替换最低分 offensive `Jobs`
- `@Jobs` 时: `Jobs` 被 protected,未被 `Munger` 的强制补位挤掉;`Munger` 本轮因 `explicit_mention_elsewhere` 跳过强制补位
- `@Munger` 时: `Munger` 作为 protected speaker 入场,不重复触发 forced rebalance

## 仍未完成

- 尚未跑真实 LLM / `/room` orchestrator live rerun。
- P3 当前是协议与规则模拟通过,不是端到端活体通过。

## 建议下一步

1. 用真实 `/room` orchestrator 跑一次 `@Jobs` 与 `silent_rounds >= 3` 的 live rerun。
2. 然后做 Flow F 真实运行时调用验证。
3. 再处理 F16/F17/F18/F11 等低优先级协议债。

