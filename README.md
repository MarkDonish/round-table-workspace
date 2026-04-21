# Mark 多 Agent 决策框架

这是一个兼容现有名人 skill 的决策系统。

它有两种工作模式：

1. 日常模式：按任务类型调用单个或少量名人 skill
2. `/debate` 模式：明确触发重大议题圆桌会议，由上层 skill 调度 3-5 个 Agent 参会并追加审查 Agent

`/debate` 不是另一个名人人格，也不会替代你原来单独使用 `steve-jobs-skill`、`munger-skill`、`taleb-skill` 等本地 skill 的方式。

---

## `/debate` 是什么

`/debate` 是一个重大议题圆桌会议 skill。

当你明确输入：

- `/debate 这个创业方向值不值得做`
- `/debate 我要不要给产品加这个功能`
- `/debate 这个重大选择应该怎么判断`
- `/debate --with Jobs,Taleb 这个方向值不值得做`
- `/debate --without Trump 这个方案怎么定`
- `/debate --quick 我该不该做这个功能`

系统会：

1. 识别议题
2. 产出主分类与副分类
3. 自动选择 3-5 个最合适的名人 Agent
4. 给每个 Agent 分工
5. 逐个发言
6. 由主持人汇总
7. 由审查 Agent 审核
8. 审查通过后输出最终决议

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
│  └─ superpowers/specs/
├─ prompts/
│  ├─ debate-roundtable.md
│  ├─ debate-reviewer.md
│  ├─ debate-followup.md
│  └─ room-*.md
├─ examples/
│  └─ debate-examples.md
├─ .codex/skills/
│  ├─ debate-roundtable-skill/SKILL.md
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

说明：

- `docs/`、`prompts/`、`examples/`、`.codex/skills/` 是项目真源。
- `reports/` 保存开发历史、handoff、validation、session 报告。
- `artifacts/` 保存运行产物、fixture、导出文件。

---

## 如何使用

### 日常模式

直接用原有 skill：

- `用 steve-jobs-skill 判断这个功能该不该做`
- `用 feynman-skill 讲明白 attention`
- `用 taleb-skill 审查这个方案风险`

### 圆桌模式

明确输入 `/debate`：

- `/debate 这个创业方向值不值得做`
- `/debate 产品要不要加这个功能`
- `/debate 我该不该 all-in 做这个项目`
- `/debate --with Jobs,Taleb 这个方向值不值得做`
- `/debate --without Trump 这个方案怎么定`
- `/debate --quick 我该不该先做这个 MVP`

系统会自动按任务类型路由到合适的 Agent 组合。

---

## 关键入口

- 系统规则：`AGENTS.md`
- 路由器：`docs/router.md`
- 圆桌架构：`docs/debate-skill-architecture.md`
- 角色边界：`docs/agent-role-map.md`
- 审查协议：`docs/reviewer-protocol.md`
- 主提示词：`prompts/debate-roundtable.md`
- 圆桌 skill：`.codex/skills/debate-roundtable-skill/SKILL.md`
