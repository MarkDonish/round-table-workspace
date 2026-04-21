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

补充能力：

- 支持 `--with / --without` 做用户干预
- 支持主分类 + 副分类
- 支持 `--quick` 轻量模式
- 圆桌模式优先读取各名人 skill 的 `roundtable-profile.md`
- 默认按 token 预算优先压缩中间过程
- 审查不通过时最多只做 1 次定向补充，不整场重跑

如果你没有输入 `/debate`，系统就保持普通模式，不会自动拉起圆桌会议。

---

## 适用场景

`/debate` 适合：

- 创业方向判断
- 重大产品取舍
- 高风险方案审查
- 多维战略判断
- 重大人生与职业选择
- 学习路径与表达方式的结构化评审

不适合：

- 普通闲聊
- 单一问题的简单解释
- 明显只需要一个 skill 就能处理的小任务
- 缺少议题边界的空泛发散

---

## 文件结构

```text
C:\Users\CLH
├─ AGENTS.md
├─ README.md
├─ docs\
│  ├─ router.md
│  ├─ debate-skill-architecture.md
│  ├─ agent-role-map.md
│  ├─ reviewer-protocol.md
│  ├─ red-flags.md
│  └─ skill-compatibility-check.md
├─ prompts\
│  ├─ debate-roundtable.md
│  ├─ debate-reviewer.md
│  ├─ debate-followup.md
│  └─ daily-templates.md
├─ examples\
│  └─ debate-examples.md
└─ .codex\skills\
   ├─ debate-roundtable-skill\
   │  └─ SKILL.md
   ├─ steve-jobs-skill\
   │  └─ roundtable-profile.md
   └─ ... 其他名人 skill 的 roundtable-profile.md
```

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

## `/debate` 的稳定性设计

1. 只有显式输入 `/debate` 才进入圆桌模式。
2. 参会 Agent 默认 3-5 个，且必须先分工后发言。
3. 每轮必须产出主分类，最多补 1 个副分类。
4. 默认用 `compact` 模板，只有小会才升到 `full`。
5. 选人后必须做标签平衡：至少 1 个 `defensive`、至少 1 个 `grounded`、`dominant` 不得过半。
6. 审查 Agent 只看可见产物，不看隐藏思考链。
7. 审查不过最多返工 1 次，之后输出阻塞结论而不是伪装确定答案。
8. 圆桌模式优先读 `roundtable-profile.md`；缺失时只用简化角色卡，避免把完整 skill prompt 全塞进上下文。

---

## 与已有名人 skill 的关系

- 原有名人 skill 继续独立存在
- `/debate` 只是上层调度器，不改动原 skill 目录和触发方式
- 文档里可用人名简称
- 真正调用时优先使用精确 skill 名

例如：

- 文档写法：`Paul Graham + Jobs + Munger`
- 本地调用：`paul-graham-skill + steve-jobs-skill + munger-skill`

---

## 如何新增 Agent

1. 确认本地 skill 已存在且可独立使用
2. 在 [agent-role-map.md](/C:/Users/CLH/docs/agent-role-map.md) 补齐职责边界、标签、擅长问题、偏差、搭配对象
3. 在 [debate-skill-architecture.md](/C:/Users/CLH/docs/debate-skill-architecture.md) 中决定它适合进入哪些任务组合
4. 为该 skill 增加 `roundtable-profile.md`
5. 如果它偏进攻、偏抽象或偏强势，必须指定对冲 Agent
6. 不要让新 Agent 直接进入所有默认会议组合

---

## 如何新增新场景

1. 在 [router.md](/C:/Users/CLH/docs/router.md) 增加任务类型或路由规则
2. 在 [debate-skill-architecture.md](/C:/Users/CLH/docs/debate-skill-architecture.md) 增加推荐组合
3. 在 [prompts/debate-roundtable.md](/C:/Users/CLH/prompts/debate-roundtable.md) 明确场景适配方式
4. 在 [examples/debate-examples.md](/C:/Users/CLH/examples/debate-examples.md) 增加真实案例
5. 更新审查规则，确认不会让系统变乱

---

## 如何避免系统混乱

1. 不输入 `/debate`，就不要进入圆桌模式
2. 单次会议最多 5 个 Agent
3. 先分工，后发言，禁止自由混战
4. 审查 Agent 只审查可见推理产物
5. 审查不过最多返工 1 次，不直接输出最终结论
6. 进攻型、抽象型、强势型 Agent 必须配对冲角色
7. 主持人必须输出统一决议，而不是并列多个答案
8. 默认使用 `compact` 发言模板，只有小会才自动切到 `full`
9. 圆桌模式用轻量 profile，不用完整 skill prompt
10. 快速模式只用于中等重要度问题，不应用于高代价决策

---

## 关键入口

- 系统规则：[AGENTS.md](/C:/Users/CLH/AGENTS.md)
- 路由器：[router.md](/C:/Users/CLH/docs/router.md)
- 圆桌架构：[debate-skill-architecture.md](/C:/Users/CLH/docs/debate-skill-architecture.md)
- 角色边界：[agent-role-map.md](/C:/Users/CLH/docs/agent-role-map.md)
- 审查协议：[reviewer-protocol.md](/C:/Users/CLH/docs/reviewer-protocol.md)
- 主提示词：[debate-roundtable.md](/C:/Users/CLH/prompts/debate-roundtable.md)
- 圆桌 skill：[SKILL.md](/C:/Users/CLH/.codex/skills/debate-roundtable-skill/SKILL.md)
