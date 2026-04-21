# Debate Skill Architecture

## 1. 系统目标

`/debate` 是一个重大议题圆桌会议调度 skill。

它不是普通聊天器，也不是新名人人格，而是一个上层协调系统。它的目标是：

- 围绕重大议题组织多 Agent 结构化讨论
- 让讨论过程可审计、可复用、可返工
- 让最终结论经过显式审查，而不是凭感觉收尾
- 与已有名人 skill 的独立使用逻辑共存

---

## 2. 系统角色

### 2.1 用户

- 提供议题
- 明确是否使用 `/debate`
- 接收最终决议

### 2.2 `/debate` 调度器

职责：

- 识别议题
- 路由任务类型
- 选择参会 Agent
- 分配角色职责
- 组织发言顺序
- 指定主持人与审查 Agent
- 根据审查结果决定放行或返工

### 2.3 参会 Agent

来源：本地已配置的名人 skill

职责：

- 在指定岗位内发言
- 提供基于职责的可见推理产物
- 说明依据、反对的误判、建议、不确定项

### 2.4 圆桌主持人

职责：

- 重述议题
- 记录参会 Agent 与职责
- 汇总共识、冲突和隐含假设
- 形成初步建议
- 向审查 Agent 明确提交可审查材料

### 2.5 审查 Agent

职责：

- 只审查可见推理产物
- 不代替专家发言
- 不宣称看到了隐藏思考链
- 扫描红旗并决定是否放行

---

## 3. 触发语义

`/debate` 只在用户明确输入 `/debate` 时触发。

允许形式：

- `/debate 这个创业方向值不值得做`
- `/debate 我要不要加这个功能`
- `/debate 这个方案风险大不大`

不允许自动触发：

- 普通问题
- 模糊发散讨论
- 只需要单个 skill 的简单请求

因此 `/debate` 只作为上层调度 skill 生效，不污染日常 skill 调用。

---

## 4. 路由机制

### 4.1 任务类型

- `startup`
- `product`
- `learning`
- `content`
- `risk`
- `planning`
- `strategy`
- `writing`

### 4.2 默认 Agent 组合

| 任务类型 | 默认组合 | 说明 |
| --- | --- | --- |
| `startup` | Paul Graham + Steve Jobs + Munger + Taleb | 机会、主张、偏差、风险 |
| `product` | Steve Jobs + Zhang Yiming + Elon Musk + Munger | 体验、机制、第一性原理、偏差控制 |
| `learning` | Karpathy + Feynman + Ilya Sutskever | 技术直觉、解释清晰、前沿方向 |
| `content` | MrBeast + Feynman + Zhang Xuefeng + Naval | 传播、清晰、接地气、长期定位 |
| `risk` | Taleb + Munger + Elon Musk | 脆弱性、偏差、系统性拆解 |
| `planning` | Naval + Munger + Taleb | 长期方向、配置、下行保护 |
| `strategy` | Paul Graham + Munger + Taleb + Zhang Yiming | 机会质量、偏差、风险、机制 |
| `writing` | Feynman + Naval + Zhang Xuefeng + Paul Graham | 清晰、方向感、落地表达、论证结构 |

### 4.3 对冲机制

- 有 `Steve Jobs / Elon Musk / MrBeast / Trump` 这类进攻型 Agent 时，必须有 `Taleb` 或 `Munger` 之一
- 有 `Naval / Ilya / Paul Graham` 这类抽象型 Agent 时，必须有 `Zhang Xuefeng`、`Feynman` 或 `Zhang Yiming`
- `Trump` 不是默认组合成员，只能在明确需要“强势表达 / 谈判姿态”时增补
- 强势风格 Agent 不得单独主导会议

---

## 5. 圆桌会议流程

### Step 1. 识别议题

输出：

- 议题原文
- 议题边界
- 问题类型提示：是否做 / 怎么做 / 先做什么 / 为什么有问题

### Step 2. 识别任务类型

输出：

- 任务类型
- 路由理由
- 为什么不选相邻类型

### Step 3. 选择参会 Agent

输出：

- 参会 Agent 名单（3-5 个）
- 主持人
- 审查 Agent
- 选择理由

### Step 4. 给每个 Agent 分工

输出：

- Agent 名称
- 职责
- 为什么需要它
- 它不该做什么

### Step 5. 逐个发言

每个 Agent 都必须按统一发言模板输出。

### Step 6. 主持人汇总

输出：

- 议题重述
- 参会 Agent 与职责
- 共识点
- 核心分歧
- 隐含假设
- 初步建议
- 需要审查 Agent 重点检查的地方

### Step 7. 审查 Agent 审核

输出：

- 评分
- 履职最好者
- 偷懒或空泛者
- 缺证据点
- 逻辑跳跃点
- 被忽略问题
- 是否允许进入最终决议
- 若不允许，需要补充什么

### Step 8. 输出最终决议

前提：只有审查通过才允许输出。

内容必须包含：

- 单一最终建议
- 建议背后的核心理由
- 关键风险
- 下一步动作
- 停止条件 / 复盘点

---

## 6. 审查机制

### 6.1 审查对象

审查 Agent 只能审查：

- Agent 的显式发言
- 主持人的显式汇总
- 讨论中显式列出的事实、推断、不确定项和建议

不能审查：

- 不可见的内部思考链
- 未输出的草稿
- 模型隐含过程

### 6.2 审查标准

- 是否按职责发言
- 是否给出具体依据
- 是否区分事实和推断
- 是否如实说明不确定性
- 是否提出可执行建议
- 是否遗漏关键反方视角
- 是否存在红旗

### 6.3 放行规则

- 评分低于 7 分：默认不允许进入最终决议
- 存在严重红旗：默认不允许进入最终决议
- 若关键论点无依据：默认不允许进入最终决议
- 若建议不可执行：默认不允许进入最终决议

---

## 7. 最终输出机制

最终决议必须满足：

1. 只有一个主建议
2. 明确说明为什么是这个建议
3. 写出关键风险和不确定项
4. 给出具体下一步动作
5. 给出停止条件或复盘节点

禁止：

- 并列多个互相冲突的答案
- 只给方向，不给动作
- 用抽象口号代替建议

---

## 8. 与现有名人 skill 的关系

`/debate` 是上层 skill，不替代以下本地 skill 的独立调用：

- `steve-jobs-skill`
- `elon-musk-skill`
- `munger-skill`
- `feynman-skill`
- `naval-skill`
- `taleb-skill`
- `zhangxuefeng-skill`
- `paul-graham-skill`
- `zhang-yiming-skill`
- `karpathy-skill`
- `ilya-sutskever-skill`
- `mrbeast-skill`
- `trump-skill`

兼容原则：

- 不改目录结构
- 不改原 skill 的触发逻辑
- 只在 `/debate` 模式下作为独立 Agent 被召唤参会

---

## 9. 推荐维护方式

当新增 Agent 或新场景时：

1. 先更新 `agent-role-map.md`
2. 再更新路由组合
3. 再检查对冲机制是否被破坏
4. 最后补示例与审查规则

维护顺序优先保证系统清晰，而不是追求更多 Agent。
