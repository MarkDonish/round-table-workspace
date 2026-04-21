# Mark 多 Agent 决策框架

这是一个兼容现有名人 skill 的决策系统仓库，也是当前 round-table 工作区的长期真源。

它现在有 3 层使用方式：

1. 日常模式：按任务类型调用单个或少量 skill
2. `/room` 模式：显式触发的状态化多 Agent 房间，用于探索、推进、总结、升级
3. `/debate` 模式：显式触发的重大议题圆桌审议，用于形成审查后的统一决议

`/room` 和 `/debate` 都不是默认模式。只有在用户明确进入对应上下文时才启用。

---

## 当前状态

项目不是 100% 完成，但核心边界已经非常清楚。

### 已完成的核心能力

- `/debate` 的 skill 架构、角色边界、reviewer 协议、红旗规则、主 prompts 已经落地
- `/room` 的状态模型、selection / chat / summary / upgrade 协议已经落地
- `/room -> /debate` 的 handoff schema 已经落地
- `docs/agent-registry.md` 已提供 runtime-facing 的 agent registry
- `prompts/room-chat.md` 已重建为可读版本
- `docs/room-runtime-bridge.md` 已把缺失的 runtime bridge 责任边界锁成真源
- `.codex/skills/room-skill/runtime/room_runtime.py` 已把 `/room` 的 host-side bridge 代码正式入仓
- `.codex/skills/room-skill/runtime/fixtures/canonical/` 已提供 checked-in 的首轮验证 fixture

### 还没完成的核心能力

- `/room` 的 provider-backed live host integration 还没和真实模型调用链完全接上线，但仓库里已经有 `.env` + Chat Completions-compatible adapter 入口
- 还没有完成一轮带真实 prompt 调用的 `/room -> /summary -> /upgrade-to-debate` live run
- 当前已完成的是 fixture-driven 的本地 bridge 验证，不应误报成所有宿主都已 100% 实战验证

简化结论：

- `/debate`：已可视为结构完成
- `/room`：协议完成、bridge 已定义，但 runtime implementation 还差最后接线

---

## Source Of Truth

这个仓库里真正应当长期维护的真源目录是：

- `README.md`
- `AGENTS.md`
- `docs/`
- `prompts/`
- `examples/`
- `.codex/skills/debate-roundtable-skill/`
- `.codex/skills/room-skill/`
- `.codex/skills/*/roundtable-profile.md`

以下目录不是当前实现真源：

- `reports/`
- `artifacts/`

其中：

- `reports/` 保存开发历史、handoff、validation、session 报告
- `artifacts/` 保存运行产物、fixture、导出文件

---

## 仓库结构

```text
round-table-workspace/
├─ README.md
├─ AGENTS.md
├─ .gitignore
├─ docs/
│  ├─ router.md
│  ├─ debate-skill-architecture.md
│  ├─ agent-role-map.md
│  ├─ reviewer-protocol.md
│  ├─ red-flags.md
│  ├─ room-architecture.md
│  ├─ room-selection-policy.md
│  ├─ room-to-debate-handoff.md
│  ├─ room-chat-contract.md
│  ├─ room-runtime-bridge.md
│  ├─ room-runtime-status.md
│  └─ superpowers/specs/
├─ prompts/
│  ├─ debate-roundtable.md
│  ├─ debate-reviewer.md
│  ├─ debate-followup.md
│  └─ room-*.md
├─ examples/
│  ├─ debate-examples.md
│  └─ room-examples.md
├─ .codex/skills/
│  ├─ debate-roundtable-skill/SKILL.md
│  ├─ room-skill/SKILL.md
│  └─ */roundtable-profile.md
├─ reports/
│  ├─ checkpoints/
│  ├─ sessions/
│  └─ setup/
└─ artifacts/
   ├─ runtime/
   ├─ fixtures/
   └─ rendered/
```

---

## 如何使用

### 日常模式

直接用原有 skill：

- `用 steve-jobs-skill 判断这个功能该不该做`
- `用 feynman-skill 讲明白 attention`
- `用 taleb-skill 审查这个方案风险`

### `/room` 模式

适合需要连续推进、保留状态、阶段总结、必要时升级成正式审议的场景。

示例：

- `/room 我想讨论一个面向大学生的 AI 学习产品，从方向、切口、风险一步步推进`
- `/focus 先只盯“最小可验证切口”`
- `/summary`
- `/upgrade-to-debate`

### `/debate` 模式

适合重大判断、需要明确分工和审查放行的场景。

示例：

- `/debate 这个创业方向值不值得做`
- `/debate 我是否应该给产品加这个功能`
- `/debate --with Jobs,Taleb 这个方向值不值得做`
- `/debate --without Trump 这个方案怎么定`
- `/debate --quick 我该不该先做这个 MVP`

系统会自动按任务类型路由到合适的 Agent 组合。

---

## 关键入口

### 通用入口

- 项目规则：`AGENTS.md`
- 快速路由：`docs/router.md`

### `/room`

- skill：`.codex/skills/room-skill/SKILL.md`
- 架构：`docs/room-architecture.md`
- selection：`docs/room-selection-policy.md`
- handoff：`docs/room-to-debate-handoff.md`
- chat contract：`docs/room-chat-contract.md`
- bridge contract：`docs/room-runtime-bridge.md`
- 当前边界：`docs/room-runtime-status.md`
- runtime bridge：`.codex/skills/room-skill/runtime/README.md`
- live provider sample：`.env.room.example`
- examples：`examples/room-examples.md`

### `/debate`

- skill：`.codex/skills/debate-roundtable-skill/SKILL.md`
- 架构：`docs/debate-skill-architecture.md`
- 角色边界：`docs/agent-role-map.md`
- 审查协议：`docs/reviewer-protocol.md`
- 红旗：`docs/red-flags.md`
- examples：`examples/debate-examples.md`
