# 圆桌会议项目开发进度对接汇报

生成时间: 2026-04-17  
评估人: Codex  
评估范围:

- 交接目录: `D:\圆桌会议`
- 实际代码仓: `C:\Users\CLH\tools\room-orchestrator-harness`
- 技能契约: `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

## 1. 评估口径

本次不是只读 D 盘报告，而是按“文档口径 + 真实代码口径 + 当前测试口径”三线对齐。

百分比定义:

- 100%: 代码已落地，且有测试或 CLI/fixture 路径验证
- 75%: 代码已落地，但仍停留在 harness/contract 层，未完全进入宿主实时流
- 50%: 文档/契约已明确，运行链路未闭合
- 25%: 方向明确，但仅有部分补丁或局部验证
- 0%: 尚未开始

当前实测基线:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'
```

结果:

```text
tests 75
pass 75
fail 0
```

## 2. 当前开发进度总表

| 板块 | 当前进度 | 状态判断 | 量化依据 |
|---|---:|---|---|
| D 盘交接与主线对接 | 100% | 已完成 | 已核对 `NEXT-STEPS.md`、`ROUND-TABLE-TAKEOVER-2026-04-17.md`、`FULL-FOLDER-READTHROUGH...`、`DEVELOPMENT-BOARD...CORRECTED.md` 等主线文档 |
| `/room` 协议/Prompt/Skill 文档层 | 95% | 基本完成 | `room-selection.md`、`room-chat.md`、`room-summary.md`、`room-upgrade.md`、`room-skill` 已成型；剩余是 F11/F17 与 `§13.6` 歧义收口 |
| deterministic harness / validators / reducer / packet builder | 100% | 已完成 | `flow-f.js`、`state.js`、`validators.js`、`packet-builder.js` 均已落地并在 75 测试内回归通过 |
| prompt adapter / external executor / provider wrapper | 100% | 已完成但属可选层 | `prompt-runner.js`、`external-executor.js`、`http-provider-wrapper.js`、`chat-completions-wrapper.js` 已完成，README 明确其为 optional adapter |
| local sequential dispatch foundation | 100% | 已完成 | `local-dispatch.js` 与 `local-dispatch.test.js` 完成；支持 `DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT` |
| room runtime local adapter | 100% | 已完成 | `room-runtime.js` 已完成 `assignTurnRoles()` 与 `runRoomTurnWithLocalDispatch()`，CLI fixture 可直跑 |
| selection -> local runtime 链路 | 100% | 已完成 | `selection-runtime.js` 已完成；`selection-runtime.test.js` 与 CLI `--selection-runtime-fixture` 已验证 |
| `/room` 宿主实时集成层 | 35% | 明显未闭合 | `room-skill` 文档已对齐 `runRoomTurnWithLocalDispatch()`，但 README 明确“Host-runtime subagent invocation wiring”仍在 harness 之外，尚未把真实宿主执行器接到 live `/room` 流程 |
| 协议债收口（F11/F16/F17/F18 + `§13.6`） | 25% | 刚开始 | F16/F18 第一批已补；F17、F11 仍待处理；`VALIDATION-REPORT-selection.md §13.6` 仍有 10 项歧义未系统补齐 |
| Phase 6: 旧 skill mode 升级 | 0% | 未开始 | 文档中仍定义为长期项 |
| Phase 7: 自动发现扫描器 | 0% | 未开始 | 仍停留在规划层，无代码落地 |

## 3. 综合判断

### 3.1 当前主线里程碑综合进度

按“当前 `/room` 本地主线”而不是长期 Phase 6/7 计算，综合进度约为 **72%**。

加权依据:

- 协议/Prompt/Skill 契约: 15% × 95% = 14.25
- harness / reducer / validators: 15% × 100% = 15
- local dispatch / room runtime / selection-runtime 主链: 30% × 100% = 30
- 宿主实时集成层: 25% × 35% = 8.75
- 协议债收口: 15% × 25% = 3.75

合计: **71.75%**，四舍五入为 **72%**

### 3.2 结论一句话

当前项目已经不是“有没有本地 runtime”的问题，而是“本地 runtime 的 harness 主链已打通，下一步要继续补协议债，并把宿主实时集成层补齐”。  
换句话说，**工程底座已成，产品化最后一公里未完成**。

## 4. 当前最高优先级任务排序

以下排序优先遵循 `D:\圆桌会议\NEXT-STEPS.md` 与 `ROUND-TABLE-TAKEOVER-2026-04-17.md` 的接力口径。

| 优先级 | 任务 | 当前状态 | 为什么排在这里 | 建议投入 |
|---|---|---|---|---|
| P1 | F17: 明确 primary 在 user 追问时可回应上轮 challenge，但仍以主张为核心 | 未完成 | 已被接管文档明确列为下一步第一优先级；影响 room-chat contract 的一致性 | 0.5 个 session |
| P2 | F11: 处理 synthesizer 180 字瓶颈，决定是继续记债还是放宽文档 | 未完成 | 直接影响输出质量与长度约束是否稳定；属于 prompt contract 的高频问题 | 0.5 个 session |
| P3 | 补完 `VALIDATION-REPORT-selection.md §13.6` 的 10 项规则歧义，并给每项加最小 contract test | 未完成 | 这是当前规则层最大遗留包，影响 selection 打分一致性和可解释性 | 1-2 个 session |
| P4 | 把宿主实时执行器真正接到 `/room` live flow，而不是只停在 harness seam | 未完成 | 当前最大“看起来完成、实际没接上”的缺口；没有这一步，`/room` 仍主要是可验证底座，而不是可实时运行的产品链路 | 1-2 个 session |
| P5 | 进行 true local `/room` live rerun，验证完整 host runtime 路径 | 未完成 | 这是对 P4 的闭环验证，能把“合同可执行”升级为“产品链路可执行” | 1 个 session |
| P6 | Phase 6: 13 个旧 skill 从 `debate_only` 升级为 `debate_room` | 未开始 | 明确的长期项，主线未收口前不应抢跑 | 后置 |
| P7 | Phase 7: 自动发现扫描器 | 未开始 | 进一步的自动化能力，不该早于主线闭环 | 最后做 |

## 5. `§13.6` 歧义包拆分（便于后续排期）

`VALIDATION-REPORT-selection.md §13.6` 当前仍有 10 项规则歧义，建议再细分为两个包:

| 包 | 条目数 | 代表问题 | 建议优先级 |
|---|---:|---|---|
| A 包：中等严重度 | 4 | `structure_complement` 部分补位阈值、`redundancy_penalty` 的重复阈值、dominant 累积扣分主语、唯一 defensive 的替换规则 | 高 |
| B 包：低严重度 | 6 | role_uniqueness 区分度、top3 自身如何算 structure_complement、tie-breaker 未定义等 | 中 |

建议做法:

1. 先补 A 包并加最小 contract test。
2. 再补 B 包，尽量只改规则文档和测试，不改大框架。

## 6. 现阶段明确不应抢跑的事项

这些事项当前应继续后置，不建议插队:

- provider/API 真接入
- UI
- 持久化存储
- full `/room` command parser
- `/debate` 边界改造

原因很简单: 项目文档已经多次纠偏，当前主线不是这些。

## 7. 管理层可直接使用的汇报结论

| 维度 | 结论 |
|---|---|
| 当前测试健康度 | 100%（75/75 通过） |
| 当前工程底座完成度 | 高，核心 harness 与本地 runtime 链已打通 |
| 当前产品化完成度 | 中高，约 72% |
| 当前最大短板 | 宿主实时集成层未闭合；协议债仍未清空 |
| 当前最优先动作 | 先做 F17、F11，再清 `§13.6`，然后补宿主 live wiring |
| 当前不该做的事 | 回到 provider/API 主线，或提前做 UI/持久化/扫描器 |

## 8. 最终判断

如果按“代码底座是否成型”来看，项目已经过了最危险阶段。  
如果按“用户现在能不能稳定跑真实 `/room` 产品链路”来看，项目还差最后一段集成与规则收口。

所以最准确的管理判断是:

**不是 0 到 1 阶段，也不是已收尾阶段，而是 1 到可用阶段。**

---

## 9. 执行更新（2026-04-17 第二次推进）

本轮已按优先级继续完成以下事项：

1. `F17` 已收口
   - `prompts/room-chat.md` 已明确：
   - `primary` 在用户追问上一轮 challenge 时，可以回应 challenge
   - 但必须仍以新的正向主张开场，不能退化成纯 rebuttal
   - `support/challenge` 必须围绕更新后的主张继续推进

2. `F11` 已收口
   - `prompts/room-chat.md` 已明确：
   - synthesizer 仍保持 `80-180` 字软约束，不在 v0.1 放宽
   - 字数预算优先保留：主张保留 / 反方吸收 / 下一步动作
   - 优先压缩 recap，不得先删掉 concrete next step

3. `selection §13.6` 已补最小 contract coverage
   - 新增 `room-selection` prompt 澄清附录，覆盖：
   - `structure_complement` 的 `10/5/0` 边界
   - `redundancy_penalty` 的 `>=2 tag overlap` 阈值
   - `dominant` 过载惩罚扣在“当前候选人”而不是 retroactive 回扣
   - stage 冲突 tie-breaker
   - `stage adjacency` 只看直接相邻，不看 2 跳
   - `role_uniqueness` 的比较池与时序
   - top3 边界并列时的参考集 tie-breaker
   - `E-2` 替换时遇到唯一 `defensive/grounded` 必须跳过
   - `role_uniqueness` 公式弱点当前只冻结，不做临场公式漂移

4. `room-skill` 宿主兼容性已补一层
   - `C:\Users\CLH\.codex\skills\room-skill\SKILL.md` 已明确：
   - Codex 宿主默认走 `execution_mode: local_sequential`
   - 默认由当前 agent 充当 host/current-agent speaker executor
   - 只有用户显式要求并行委托时，才允许用 `spawn_agent(...)`

## 10. 当前验证结果

- 定向测试：
  - `room-chat-prompt-contract.test.js` 通过
  - `room-selection-prompt-contract.test.js` 通过
  - `room-skill-local-dispatch-contract.test.js` 通过
- 全量测试：
  - `82 / 82 pass`

## 11. 更新后的板块进度（本轮后重估）

| 板块 | 上轮 | 本轮后 | 说明 |
|---|---:|---:|---|
| `room-chat` 协议债收口 | 60% | 100% | `F11/F17` 已补齐；`F16/F18` 之前已落地 |
| `selection` 规则清晰度 | 25% | 90% | `§13.6` 10 项已明文化/冻结；仅剩未来可能的公式升级，不属当前 prompt 歧义 |
| `room-skill` 宿主兼容对齐 | 35% | 50% | 默认执行路径已与 Codex 现实约束对齐，但还没有真正的 `/room` 可执行入口 |
| 项目综合进度 | 72% | 79% | 当前主要缺口集中在真实 `/room` 宿主运行入口与 live rerun |

## 12. 下一步真正的 P1

下一步不再是补 prompt 文案，而是二选一的实现决策：

1. 做“最小可执行 `/room` 入口”
   - 目标：让 skill 能通过一个明确入口真正调用 harness runtime，而不是只停留在 `SKILL.md`
2. 做“true local `/room` live rerun”
   - 目标：选一条真实输入路径，把当前 host/current-agent 默认执行链完整跑一遍

当前我倾向先做 **最小可执行 `/room` 入口**，再做 live rerun。这样 rerun 跑出来的结果才有真实宿主落点。

---

## 13. 执行更新（2026-04-17 第三次推进）

本轮已完成“最小可执行 `/room` 入口”这一项，而不是只停留在 skill 文档说明层。

### 13.1 已完成内容

1. 新增 skill 侧最小可执行 wrapper
   - 路径：`C:\Users\CLH\.codex\skills\room-skill\scripts\run-room-harness.js`
   - 作用：从 `room-skill` 目录直接桥接到 `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
   - 边界：它仍然不是 full `/room` command parser，但已经是**真实可执行入口**

2. `room-skill` 文档已同步命令入口
   - `SKILL.md` 新增“最小可执行入口”章节
   - 明确支持：
   - `--room-turn-fixture`
   - `--selection-runtime-fixture`

3. 新增入口级回归测试
   - `room-skill-entrypoint.test.js`
   - 覆盖：
   - wrapper 文件存在
   - skill 文档包含入口说明
   - wrapper 能真实执行 `room-turn` fixture

4. 实跑验证已通过
   - 通过 skill wrapper 实际执行：
   - `--selection-runtime-fixture D:\圆桌会议\SESSION-28-SELECTION-TO-LOCAL-RUNTIME-FIXTURE.json`
   - 结果：`pass = true`

### 13.2 当前验证结果

- 全量测试：`84 / 84 pass`
- skill wrapper 命令链：已实跑通过

### 13.3 更新后的板块进度（本轮后重估）

| 板块 | 上轮 | 本轮后 | 说明 |
|---|---:|---:|---|
| `room-skill` 宿主兼容对齐 | 50% | 75% | 已有 skill 侧真实入口，但仍未完成“真实用户输入驱动”的 `/room` live 流程 |
| 最小可执行 `/room` 入口 | 0% | 100% | skill → harness runtime 的最小桥接已落地 |
| true local `/room` live rerun | 0% | 20% | 已有真实入口与可执行命令，但仍是 fixture 驱动，不是最终 live user path |
| 项目综合进度 | 79% | 83% | 当前主要剩余缺口是“非 fixture 的 true local live rerun” |

### 13.4 下一步

下一步只剩一个高优先级主线任务：

1. 做 **true local `/room` live rerun**
   - 目标：从真实 `/room` 输入路径进入，而不是从 fixture 直接喂给 harness
   - 要求：保留当前 `local_sequential` / current-agent executor 主线，不回退到 provider/API

### 13.5 风险边界

当前仍然**不能**过度宣称的点：

- 还没有 full `/room` command parser
- 还没有真实用户输入到 room state 的完整 live 命令入口
- 还没有非 fixture 场景下的 true local `/room` end-to-end rerun

所以当前准确口径是：

**“最小可执行入口已完成，真实 live 产品链路验证仍在最后一段。”**

## 14. 执行更新（2026-04-17 第四次推进）

本轮完成了 `host-assisted true local rerun` 的最小闭环，不再停留在 deterministic speaker fixture。

### 14.1 本轮新增能力

- harness 新增两段式 live bridge：
  - `prepareSelectionToLocalRuntime()` / `runPreparedSelectionToLocalRuntime()`
  - `prepareRoomTurnWithLocalDispatch()` / `runPreparedRoomTurnWithLocalDispatch()`
- CLI 新增：
  - `--prepare-selection-runtime-fixture`
  - `--selection-runtime-bundle --speaker-output-file`
- `room-skill` wrapper 与 `SKILL.md` 已同步支持上述命令

### 14.2 本轮真实执行证据

已保存产物：

- `C:\Users\CLH\ROOM-SELECTION-LIVE-BUNDLE-2026-04-17.json`
- `C:\Users\CLH\ROOM-LIVE-SPEAKER-OUTPUTS-2026-04-17.json`
- `C:\Users\CLH\ROOM-LIVE-RERUN-RESULT-2026-04-17.json`
- 说明报告：`C:\Users\CLH\SESSION-30-HOST-ASSISTED-LIVE-RERUN-REPORT-2026-04-17.md`

实际结果：

- `mode = selection_to_room_turn_local_runtime`
- `pass = true`
- `turn_count = 1`
- 全量回归：`86 / 86 pass`
- 已确认 reducer 写回：
  - `conversation_log`
  - `silent_rounds`
  - `turn_count`
  - `last_stage`
  - `recent_log`

### 14.3 当前口径修正

这一步已经可以诚实地称为：

**“host-assisted true local `/room` selection-to-runtime / one-turn room runtime rerun 已完成。”**

但仍然**不能**称为：

- full `/room <topic>` command parser 已完成
- raw user command 直达 `room_full` 的完整产品链路已完成

### 14.4 更新后的板块进度

| 板块 | 上轮 | 本轮后 | 说明 |
|---|---:|---:|---|
| `room-skill` 宿主兼容对齐 | 75% | 90% | 已从“最小入口”推进到“可重复 live bridge” |
| true local `/room` live rerun | 20% | 75% | host-assisted local mainline 已打通；剩 raw `/room <topic>` 解析入口 |
| 项目综合进度 | 83% | 89% | 当前主缺口已收缩为 full command-flow live rerun |

### 14.5 下一步

唯一仍值得继续推进的主线是：

1. 把 raw `/room <topic>` 输入直接接到 `room_full` 初始化路径
2. 在不引入 provider 依赖的前提下，形成真正的 command-flow rerun
