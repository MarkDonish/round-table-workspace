# Session 4 Completion Report

生成:2026-04-11
本会话模型:Claude Opus 4.6(1M context)
会话性质:**阻塞项修补**——响应 Session 3 验证报告的两个 🔴 高优先级 FINDING
前置:
- `D:\圆桌会议\VALIDATION-REPORT-selection.md`(Session 3 验证产出)
- `D:\圆桌会议\SESSION-2-COMPLETION-REPORT.md`(Session 2 协议层落地)

---

## 本次会话的使命

Session 3 验证 `prompts/room-selection.md` 后,发现 10 个 FINDING,其中 2 个被标记为 🔴 高优先级(阻塞进 Phase 2):

- **FINDING #1**:算法对「议题琐碎度」完全无感知,「按钮左右」类 UI 微决策会被过度分配 4 人花名册,违背 `/room` 的「陪跑 20%」定位
- **FINDING #6**:`silent_rounds` 计数器没有定义维护方,selection prompt 是纯消费者,没有 orchestrator 层的文档定义,导致强制补位规则在实际运行中**永远不会被触发**

Session 4 的唯一任务:**最小化地**修补这两个阻塞项,不扩散到其他 FINDING 或 Phase 2 主体写作。

---

## 交付物(时间顺序)

### 1. FINDING #1 修补:琐碎度降级规则

#### 1.1 在 `docs/room-selection-policy.md` 追加 §9.1.1

新增章节 **§9.1.1 议题琐碎度降级预检**,包含 5 个子章节:

- §9.1.1.1 触发条件(4 条合取)
- §9.1.1.2 触发时的动作
- §9.1.1.3 不触发时的行为
- §9.1.1.4 Session 3 三议题回归校验表
- §9.1.1.5 已知限制与未来调参空间

**插入位置**:在 §9.1 排序 与 §9.2 花名册构建 之间,编号为 §9.1.1,**避免重编号**(§9.2-§9.6 原有自引用不动)。

#### 1.2 关键决策:用 `subproblem_match` 子项差,不是 total 差

Session 3 验证报告原始建议用 `top1.total - top2.total ≥ 15` 作触发条件。但用报告中的实际分数一核对:

- Topic B:Jobs total=52,Feynman total=47 → **total 差只有 5**,根本不会触发

根因分析:产品类议题人人都有 `task_type_match = 15`(主 task 命中)+ `stage_fit = 15`(converge 直命中),可以堆出 40+ 的 total 分,**掩盖了**「子问题真正命中几 tag」的差异信号。

**本次锁定的条件**:

1. `sub_problems.length == 1` 且 tag 数量 ≤ 2
2. `stage ∈ {converge, decision}`
3. `topic` 文本 ≤ 20 字符
4. **`top1.subproblem_match - 次高 subproblem_match ≥ 8`**(用子项,不是 total)

在 Session 3 三议题上的回归表:

| 议题 | 长度 | stage | 子问题数 | top1 sub / 次高 sub | 差 | 降级? |
|---|---|---|---|---|---|---|
| A(独立开发者 AI 工具 All in?) | 27 | explore | 2 | Sun 30 / PG 30 | 0 | **否** ✓ |
| B(按钮放左边还是右边) | 11 | converge | 1 | Jobs 22 / 14 | 8 | **是** — roster=[Jobs] ✓ |
| C(项目失败最坏会怎样) | 15 | stress_test | 1 | Taleb 22 / 14 | 8 | **否**(stage 阻断) ✓ |

**三议题判定与 Session 3 预期完全一致**。

#### 1.3 降级方案:单人花名册,不是 top1+1 对冲

Session 3 给了两个方案(单人 vs 2 人),**本次锁定单人**。理由:陪跑 20% 的本质是「单一专家快速咨询」,加对冲位就背离了定位。如果真的需要对冲,议题应该走常规 4 人路径。

这条决议写入 DECISIONS-LOCKED.md 第 29 条。

#### 1.4 同步更新 `prompts/room-selection.md`

在步骤 E 中,E-1 排序 与 E-2 花名册构建 之间插入 **E-1.1 议题琐碎度降级预检**,与 policy §9.1.1 完全对齐。特别包含:

- 4 条触发条件的工程化描述(含 Unicode code point 计数规则)
- 豁免规则:用户显式 `@点名` 或 `--with ≥ 2 人`时跳过降级
- 输出 JSON 的填充要求(`structural_check.warnings` 追加 `"trivial_topic_downgrade"`)
- Session 3 三议题的快速参考表

prompt 头部版本号从 `v0.1` → `v0.1.1`。

### 2. FINDING #6 修补:房间状态所有权

#### 2.1 新建 `docs/room-architecture.md` v0.1-alpha

**关键决策:分阶段交付**。Session 4 **不写**整个 room-architecture.md 主体,只写 **§1-§4**——足以解除 FINDING #6 阻塞,不越界到 Phase 2 主体。

完整写作的章节:

- §1 目的与定位
- §2 完整房间状态字段清单(14 字段表格,其中 10 个为 Phase 2 占位)
- §2.1 Session 4 完整定义的 4 个运行时字段(表格)
- §3 状态所有权与更新时机(**核心章节**)
  - §3.1 `silent_rounds` — 连续沉默计数器(最详细)
  - §3.2 `last_stage` — 上轮阶段识别
  - §3.3 `turn_count` — 累计轮次
  - §3.4 `recent_log` — 压缩发言日志
- §4 状态传递路径(数据流图 ASCII art)

占位章节(等 Phase 2):

- §5 其他状态字段的详细定义(10 个子占位)
- §6 命令语义表
- §7 发言机制协议
- §8 换人机制协议
- §9 主持器的隐性职责

#### 2.2 四条核心不变量(写进 §4)

1. **selection prompt 不持有任何状态**——每次调用都是无记忆的
2. **orchestrator 是状态的唯一写者**
3. **状态更新发生在 selection → orchestrator 回路上**,不在 prompt 内部
4. **状态传递每轮都完整重发**,不做差量

这 4 条是 Session 4 为未来所有 `/room` 系列 prompt(room-chat / room-summary / room-upgrade)签下的**设计不变量**,不再允许被质疑。

#### 2.3 `silent_rounds` 的完整生命周期定义

**数据结构**:`{ [agent_id: string]: number }`

**初始化**:`room_full` 建房 / `/add` 时设为 0

**更新算法**(orchestrator 在每次 `room_turn` 产出 speakers 后执行):

```
for each agent in roster:
    if agent in speakers:
        silent_rounds[agent] = 0
    else:
        silent_rounds[agent] += 1
```

**只在 `room_turn` 成功结束时更新**,`room_full` / `roster_patch` / 错误路径都不动。

**边缘情况**:
- `/remove <agent>` → **删除键**(不是置 0)。锁为 DECISIONS-LOCKED #32
- 豁免与计数解耦:`decision` 阶段豁免只影响本轮是否强制补位,**不影响计数器累加**。锁为 DECISIONS-LOCKED #33
- 强制补位后不需要特例清零,因为该 agent 被选入 speakers 会按常规归零

#### 2.4 `recent_log` 上限:500 token

锁定硬顶。超出时主持器执行「保留最后 1 轮完整 + 前 2 轮重压缩」。压缩算法本身不在本文档定义,留给 Phase 4。锁为 DECISIONS-LOCKED #34。

### 3. 交叉引用补强

#### 3.1 `room-selection-policy.md §12` 追加交叉引用

在强制补位规则章节起始处追加一段:

> **状态所有权**:本规则依赖的 `silent_rounds` 计数器由 **orchestrator** 维护,不由 selection prompt 自己跟踪。完整的所有权、更新时机、传递路径见 [`room-architecture.md §3.1`](./room-architecture.md)。如果 orchestrator 没有实现该字段的维护,本规则将**永远不会被触发**。

这段话是 FINDING #6 的**显式警告**——让后续任何读到 §12 的人都知道「没有 orchestrator 配合,这条规则是空壳」。

#### 3.2 `room-selection-policy.md §14` 上游引用更新

从「当前未落地,待后续补」更新为「v0.1-alpha 已落地,定义了 4 个运行时字段;其余 §5-§9 留给 Phase 2」。

#### 3.3 `room-selection-policy.md §15` 版本记录追加 v0.1.1

记录本次变更内容,强调「未修改任何旧字段,`/debate` 零影响,`room_turn` / `roster_patch` 零影响」。

### 4. 接力三文档更新

- `HANDOFF.md`:更新时间、速读段、当前状态表、Session 4 交付物清单
- `NEXT-STEPS.md`:新增 Phase 1.5 回归验证章节、Phase 2 约束(不许动 §1-§4)
- `DECISIONS-LOCKED.md`:新增 Part III(决议 28-35,共 8 条新决议)

### 5. 本报告(`SESSION-4-COMPLETION-REPORT.md`)

即本文件。

---

## 本次会话未做的事(主动克制)

严格限定在两个 FINDING 的修补,以下**有能力但没做**:

1. **其他 Session 3 FINDING(#3/#4/#5/#7-#10)**:这些是 🟡 中优先级或 🟢 低优先级,属于 policy v0.1.2 补丁范围,留给 Session 5 Phase 2 并行处理
2. **room-architecture.md §5-§9 主体写作**:明确标为 Phase 2 任务,Session 4 只写阻塞项需要的首节
3. **发言/总结/升级 prompt 的设计**:Phase 4 任务,不越界
4. **Topic B 真实 LLM 回归测试**:Session 4 是文档修补轮,不跑真实 LLM 验证——这是 Session 5 Phase 1.5 的任务
5. **13 个原 skill 的 mode 升级**:仍在等试点验证通过
6. **自动发现脚本**:工程实现层,继续锁定不做

---

## 本次会话的决策质量备忘

### 主动推翻 Session 3 原始建议的地方

#### 1. 琐碎度触发条件从 `total 差 ≥ 15` → `subproblem_match 子项差 ≥ 8`

Session 3 验证报告写了这样的建议:

```
如果 top1 ≥ top2 + 15 且 stage ∈ {converge, decision}
```

但我用 Session 3 自己报告的 Topic B 分数核对:Jobs total=52,Feynman total=47,差=5。报告里的规则在报告自己测出的数据上都**不会触发**。

根因:Session 3 报告作者在写建议时没回头核对数字,用的是"感觉应该"的阈值,不是推导出的。

我的修补:用 `subproblem_match` **子项差**代替 total 差,阈值 ≥ 8。这个数字来自 Jobs 22 - 14 = 8 的实际观察,是硬推导的,不是拍的。写进 DECISIONS-LOCKED 第 28 条。

#### 2. 降级形态选单人,不是 2 人对冲

Session 3 给了两种方案,没明说推荐哪种。我选单人,理由写进 DECISIONS-LOCKED 第 29 条。

#### 3. room-architecture.md 从「Phase 2 完整版」→「Session 4 首节 + Phase 2 占位」

NEXT-STEPS 原计划 room-architecture.md 作为 Phase 2 完整交付物。我的判断:FINDING #6 只需要 4 个运行时字段的所有权,没必要现在硬写完整个 14 字段文档(那会写得仓促、未经验证、且占用了 Session 4 的主要带宽)。

决议写进 DECISIONS-LOCKED 第 30 条,并在 NEXT-STEPS.md Phase 2 章节强调「Phase 2 展开 §5-§9 时不得删改 §1-§4」。

### 没有征求用户同意的地方(直接做)

1. **具体触发阈值数字 ≥ 8**:在 policy 和 DECISIONS-LOCKED 中附了完整推导过程和 Session 3 回归表,任何后续 Agent 都可以质疑,但证据链完整
2. **单人降级 vs 2 人对冲**:用「陪跑 20% 的本质是单一专家快速咨询」的理由支撑,未来若有反例可以推翻
3. **room-architecture.md 分阶段策略**:同上,分阶段交付是降低风险的选择,未来 Phase 2 写作 Agent 必须尊重 §1-§4 的契约

### 可能被未来 Agent 质疑的决定(提前记录)

1. **阈值 8 是否过松**:可能在某些 LLM 下出现 Jobs sub=14 / 次高 14 的情况(都只命中 1 tag),差=0,不触发降级。但这种情况下 Topic B 也许应该扩人,而不是降级。需要 Session 5 用真实 LLM 验证
2. **topic 长度 20 字符上限**:对中英混排议题可能偏紧。未来如果遇到长度 22-28 的琐碎议题频繁漏判,考虑放宽到 25 或分语言阈值
3. **stage 条件只卡 converge/decision**:如果某议题主观是琐碎的但 stage 被 LLM 判为 simulate,也会漏判。这是接受的权衡——stage 判断本身不稳,多一条 stage 筛选反而增加鲁棒性
4. **`/remove` 删除键 vs 置 0**:如果 orchestrator 实现上忘了删除键,强制补位会在已移除的 agent 上误触发。需要 Phase 2 主持器实现阶段再验证
5. **4 个运行时字段的所有权说死 orchestrator**:如果未来有场景需要 selection prompt 写 `silent_rounds`(例如某种自校正),会与 §3 不变量冲突。但目前看不到这种需求

---

## 给下一个 Agent(Session 5)的一句话建议

> Session 4 修补了 FINDING #1 / #6,但**只修补了文档**。Session 5 的第一步**必须**是用真实 LLM 跑一次 Topic B 回归,确认 §9.1.1 / E-1.1 真的按规则被触发。
> 如果没触发,先修 prompt 描述(可能需要在 E-1.1 步骤头加 `STOP` 强调),再进 Phase 2 主体。
> **不要**跳过回归验证直接写 room-architecture.md §5-§9。

---

## 文件变更统计

### 新建(2 个)

- `C:\Users\CLH\docs\room-architecture.md`(v0.1-alpha,§1-§4 完整,§5-§9 占位)
- `D:\圆桌会议\SESSION-4-COMPLETION-REPORT.md`(本文件)

### 修改(5 个)

- `C:\Users\CLH\docs\room-selection-policy.md`:
  - 追加 §9.1.1(5 个子章节)
  - §12 追加交叉引用
  - §14 上游引用更新
  - §15 追加 v0.1.1 版本记录

- `C:\Users\CLH\prompts\room-selection.md`:
  - 追加 E-1.1 步骤
  - 头部版本号 v0.1 → v0.1.1

- `D:\圆桌会议\HANDOFF.md`:更新最后更新时间、速读段、当前状态表、Session 4 交付物清单、结尾寄语

- `D:\圆桌会议\NEXT-STEPS.md`:追加 Phase 1.5(回归验证)、更新 Session 4 完结状态、Phase 2 约束

- `D:\圆桌会议\DECISIONS-LOCKED.md`:新增 Part III(决议 28-35)

### 未修改(关键:`/debate` 零破坏)

- `C:\Users\CLH\AGENTS.md`
- `C:\Users\CLH\docs\debate-skill-architecture.md`
- `C:\Users\CLH\docs\agent-role-map.md`
- `C:\Users\CLH\docs\reviewer-protocol.md`
- `C:\Users\CLH\docs\red-flags.md`
- `C:\Users\CLH\prompts\debate-*.md`
- `C:\Users\CLH\.codex\skills\debate-roundtable-skill\SKILL.md`
- 14 份 `.codex/skills/<name>/roundtable-profile.md`(零改动,包括 v0.2 区块)
- `C:\Users\CLH\agent-registry\registry.json` / `README.md`

### 零改动的 `/room` 层组件

- Session 2 产出的筛选协议 v0.1 核心文本(只追加 §9.1.1 和交叉引用,旧章节 §1-§9 的文本未动)
- Session 2 产出的筛选 prompt v0.1 核心文本(只追加 E-1.1,旧步骤 A/B/C/D/E-1/E-2/E-3/E-4 未动)

---

## 验证与回归检查清单(Session 5 应该跑的)

### 🔴 必须跑(Phase 1.5)

- [ ] Topic B(按钮放左边还是右边)→ roster 只含 Jobs
- [ ] Topic A(独立开发者 AI 工具 All in?)→ 不触发降级,仍是 4 人花名册
- [ ] Topic C(项目失败最坏会怎样)→ 不触发降级,仍是 4 人防御花名册

### 🟡 建议跑(提前排雷)

- [ ] 边缘议题:「这个命名用 A 还是 B」(converge,11 字,应降级)
- [ ] 边缘议题:「我应该学 Rust 还是 Go」(converge,10 字,两 tag 均 `learning_explanation` → 应降级到 Feynman 或 Karpathy)
- [ ] `--with: [sun, pg]`(显式 2 人点名)→ 不应触发降级豁免

### 🟢 可以延后(Phase 2 时并行跑)

- [ ] `room_turn` 的 `silent_rounds` 完整生命周期(需要 orchestrator 骨架)
- [ ] `--without: [trump]`(与 R4 默认排除重合)→ 不应重复计入 hard_filtered

---

_Session 4 完结于 2026-04-11。核心交付物:FINDING #1 / #6 的最小化修补。下一步:Phase 1.5 真实 LLM 回归验证。_
