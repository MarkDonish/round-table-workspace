# Session 8 P0 Patch Report

生成:2026-04-12  
范围:v0.1.3-p0 阻塞补丁  
性质:接续 Session 7 `VALIDATION-REPORT-e2e.md` 的 P0 修补

## 1. 本次目标

Session 7 端到端验证已证明 `/room` 主链路能跑出内容,但暴露 7 个严重 Finding。Session 8 本轮先处理 P0 阻塞项,目标是让 Flow F `/upgrade-to-debate` 不再被字面协议冲突挡住,并把职责边界写到权威协议里。

## 2. 已修补项

### F20 · user_explicit_request 与 handoff §4.2 冲突

修改文件:

- `C:\Users\CLH\docs\room-to-debate-handoff.md`
- `C:\Users\CLH\prompts\room-upgrade.md`

处理:

- 写入决议 43 的字面化例外。
- `user_explicit_request` 只允许有条件豁免 early-stage / turn_count 过低这一条。
- summary 空、sub_problems 全 OOV、candidate_solutions 空仍然硬拒绝。
- `user_forced_early_upgrade` 同时写入:
  - `handoff_packet.field_13_upgrade_reason.warning_flags`
  - `packaging_meta.warnings`

关键选择:

- 不新增第 14 个 packet 字段。
- 保持 `/debate` 只消费 `handoff_packet` 的边界。
- `packaging_meta` 仍作为打包器调试元信息,不是 `/debate` 的唯一 warning 承载位置。

### F1 · structural_role 语义漂移

修改文件:

- `C:\Users\CLH\docs\room-architecture.md`
- `C:\Users\CLH\prompts\room-selection.md`
- `C:\Users\CLH\docs\room-selection-policy.md`

处理:

- `structural_role` 收窄为纯 tendency:`offensive | defensive | moderate`。
- `grounded / dominant / abstract` 明确归入 `expression`,不得混入 `structural_role`。
- 旧示例 `defensive/grounded` 已改为 `defensive`。

### F8 · turn_role 分配责任不明

修改文件:

- `C:\Users\CLH\docs\room-architecture.md`
- `C:\Users\CLH\prompts\room-selection.md`
- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

处理:

- `room-selection.md` 只输出按分数排序的 `speakers[]`,不分配 `turn_role`。
- orchestrator 按 `room-architecture.md §7.2` 唯一分配 `primary / support / challenge / synthesizer`。
- `room-chat.md` 只消费已分配的 `turn_role`,不得重分配。

### 决议 44 · previous_summary 必填

修改文件:

- `C:\Users\CLH\docs\room-architecture.md`

处理:

- 显式写入 `previous_summary` 输入契约。
- 首次 summary 也必须传空结构:`consensus_points=[]`, `open_questions=[]`, `tension_points=[]`, `recommended_next_step=null`, `last_summary_turn=null`。
- 缺失 `previous_summary` 属于 orchestrator 错误。

### F2 · E-2 迭代替换候选选择歧义

修改文件:

- `C:\Users\CLH\docs\room-selection-policy.md`

处理:

- 在 §9.2 增加候选 `look-ahead 1 层`。
- 选择 `best_candidate` 时跳过会立即破坏其他结构平衡硬规则的候选。

### F21 · Flow F 缺 parsed_topic / selection_meta

修改文件:

- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

处理:

- Flow F 调用 `room-upgrade.md` 时必须传最近一次 selection 输出的 `parsed_topic / selection_meta`。
- 禁止打包器从 `active_focus` 猜 field_04 sub_problems。

## 3. 版本同步

已更新版本标记:

- `room-to-debate-handoff.md`:v0.1.3-p0,packet schema 仍为 v0.1
- `room-upgrade.md`:v0.1.3-p0,prompt_version 同步为 `room-upgrade v0.1.3-p0`
- `room-selection.md`:v0.1.3-p0
- `room-selection-policy.md`:追加 v0.1.3-p0 版本记录
- `room-architecture.md`:v0.2-minimal+p0
- `room-skill/SKILL.md`:追加 v0.1.3-p0 版本记录

## 4. 验证

执行了文本契约检查,结果:

```text
P0 contract validation passed
```

检查覆盖:

- 必须存在 `user_forced_early_upgrade`
- 必须存在 `handoff_packet.field_13_upgrade_reason.warning_flags`
- 必须存在 `previous_summary` 缺失为 orchestrator 错误的说明
- 必须存在 `turn_role` 由 orchestrator 唯一分配的说明
- 必须存在 `structural_role=offensive|defensive|moderate`
- 必须存在 `look-ahead 1 层`
- 必须存在 `parsed_topic / selection_meta`
- 不得残留字面 `` `n`` 格式错误
- 不得残留旧语义 `grounded|balancer` / `defensive/grounded` / `每人本轮职责`

## 5. 剩余风险

本轮是协议补丁,还没有重新跑完整 Flow F 打包路径。下一步应做:

1. 构造或复用 Session 7 Step 7 的房间状态。
2. 让 `room-upgrade.md v0.1.3-p0` 真实打包 handoff_packet。
3. 检查 `field_13_upgrade_reason.warning_flags` 是否把 `user_forced_early_upgrade` 带入 packet。
4. 检查 `field_04_sub_problems` 是否来自 parsed_topic / selection_meta,而不是 active_focus 猜测。
5. 如果 packet 生成成功,再进入 selection 层 P1 修补:F9 / F15 / F13 / F14。

## 6. 不做事项

- 未改 `/debate` 定位。
- 未做状态持久化。
- 未升级 13 个旧 skill 到 `debate_room`。
- 未启动自动发现扫描器。
- 未新增第 14 个 handoff packet 字段。

_本报告写入于 2026-04-12。下一步:重跑 Flow F `/upgrade-to-debate` 打包验证。_