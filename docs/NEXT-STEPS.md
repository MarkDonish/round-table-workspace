# NEXT STEPS

生成日期：2026-04-10
目的：明确下一位 Agent 应从哪里继续，不要空转。

## 当前最优先任务

### 1. 把大报告拆成最小可执行开发入口

不是为了维护美观，而是为了后续实现时边界清晰。优先补这些正式文件：

- `docs/room-architecture.md`
- `docs/agent-registry.md`
- `docs/room-selection-policy.md`
- `docs/room-to-debate-handoff.md`
- `prompts/room-chat.md`
- `prompts/room-summary.md`
- `prompts/room-upgrade.md`

### 2. 把 `/room` 的协议层写成正式规则

重点落成三块：

- 发言机制
- 换人机制
- 升级到 `/debate` 的交接协议

这些内容已经在主报告里设计好了，但还没有拆成正式协议文档。

### 3. 定义 Agent Registry 的元数据标准

下一位 Agent 需要决定：

- 使用 `roundtable-profile.md` 继续承载，还是新增 `agent-profile.json`
- `registered / discovered_but_incomplete / disabled` 的判定规则怎么写
- 自动扫描目录的入口放在哪里

### 4. 把半结构化评分系统写成可执行规则

需要进一步补的不是大方向，而是细项：

- 评分字段的数据结构
- 模型小范围校正如何记录理由
- 组合优化的裁剪规则如何表达
- 是否加入历史有效性分

## 建议开发顺序

1. 文档协议化
2. 注册机制文档化
3. 评分机制文档化
4. Prompt 拆出
5. 再决定是否实现真正的状态层

## 不建议现在做的事

- 不要先写一个看起来热闹的聊天室原型
- 不要先让所有 skill 自动入池
- 不要先把 `/debate` 改成更自由的群聊
- 不要跳过协议层直接做工程实现

## 验收标准

下一阶段完成后，至少要达到：

- 下一个 Agent 只看协议文件，就能知道 `/room` 怎么工作
- 新增 skill 时，知道什么条件下能进入候选池
- 选人规则不再只存在于大报告中，而是有明确独立文档
- `/room` 和 `/debate` 的边界不会再反复被讨论
