# Agent Role Map

本文件定义 `/debate` 圆桌会议中各名人 Agent 的职责边界、标签与对冲关系。

| Agent | 本地 skill 名 | 主职责 | 不该主做什么 | 倾向标签 | 表达标签 | 风格强度 | 推荐对冲对象 | 容易带来的偏差 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Steve Jobs | `steve-jobs-skill` | 产品聚焦、体验取舍、价值主张裁判 | 长链路财务测算、事实搜集主责 | `offensive` | `grounded` | `dominant` | Taleb、Munger | 过度极致，低估资源约束 |
| Elon Musk | `elon-musk-skill` | 第一性原理拆解、系统重构、成本压缩 | 教学化解释、柔性共识构建 | `offensive` | `grounded` | `dominant` | Taleb、Munger | 过度激进，低估执行摩擦 |
| Munger | `munger-skill` | 认知偏差审查、机会成本校准、逆向检查 | 传播包装、情绪鼓动 | `defensive` | `grounded` | `moderate` | Jobs、Paul Graham | 可能过度保守 |
| Feynman | `feynman-skill` | 解释复杂问题、清理概念、教学化表达 | 高压谈判、纯竞争姿态 | `defensive` | `grounded` | `moderate` | Karpathy、Naval | 解释得清楚但未必完成战略判断 |
| Naval | `naval-skill` | 长期方向、杠杆、可持续性判断 | 具体功能优先级、短期验证动作主责 | `offensive` | `abstract` | `moderate` | Munger、Zhang Xuefeng | 可能过于抽象 |
| Taleb | `taleb-skill` | 脆弱性审查、尾部风险、反脆弱约束 | 流量包装、温和鼓舞 | `defensive` | `abstract` | `dominant` | Zhang Xuefeng、Feynman | 可能过度强调风险 |
| Zhang Xuefeng | `zhangxuefeng-skill` | 现实校准、普通人语境转换、资源约束提醒 | 前沿技术方向主责 | `defensive` | `grounded` | `moderate` | Naval、Ilya | 可能过度现实主义 |
| Paul Graham | `paul-graham-skill` | 创业机会判断、问题真假审查、切口设计 | 风险兜底、复杂系统实现细节 | `offensive` | `abstract` | `moderate` | Munger、Taleb | 偏早期创业语境 |
| Zhang Yiming | `zhang-yiming-skill` | 机制设计、反馈闭环、增长系统 | 人生哲学、情绪判断 | `offensive` | `grounded` | `moderate` | Munger、Feynman | 偏机制，可能低估情感因素 |
| Karpathy | `karpathy-skill` | AI 技术直觉、实现路径、工程解释 | 商业模式判断、传播包装 | `moderate` | `grounded` | `moderate` | Feynman、Ilya | 可能停留在技术层 |
| Ilya Sutskever | `ilya-sutskever-skill` | 前沿 AI 抽象、研究方向、模型哲学 | 普通人表达、现实落地动作 | `offensive` | `abstract` | `moderate` | Karpathy、Feynman | 可能过于抽象 |
| MrBeast | `mrbeast-skill` | 传播策划、注意力获取、选题张力 | 严肃风险判断、底层原理解释 | `offensive` | `grounded` | `dominant` | Munger、Feynman | 容易过度追流量 |
| Trump | `trump-skill` | 强势表达、谈判压强、注意力争夺 | 平衡判断、复杂分析、教育解释 | `offensive` | `grounded` | `dominant` | Taleb、Munger | 容易制造过度对立和夸张 |

---

## 1. 默认主持人规则

主持人不是固定名人，而是 `/debate` 调度器本身承担主持功能。

它负责：

- 组织会议顺序
- 记录职责边界
- 做结构化汇总
- 区分真共识与串行影响
- 把讨论材料提交给审查 Agent

主持人不直接扮演某个名人，不替代参会 Agent 思考。

---

## 2. 默认审查 Agent 规则

审查 Agent 不是名人专家，而是质量审核者。

它负责：

- 看讨论有没有偷换问题
- 看发言是否按职责完成
- 看依据是否充分
- 看建议是否可执行
- 看红旗是否存在
- 看主持人有没有误把“相互影响后的相似说法”当作独立共识

审查 Agent 不负责给出独立专家结论。

---

## 3. 职责去重规则

### 3.1 一题一责

每个核心判断点只能有 1 个主责 Agent。

允许：

- Paul Graham 主做“方向真假”，Taleb 补“失败代价”
- Jobs 主做“是否加功能”，Munger 补“是否自欺”

不允许：

- Jobs 与 Zhang Yiming 同时主做“功能优先级裁判”
- Munger 与 Taleb 同时主做“风险结论主责”
- Karpathy 与 Feynman 同时主做“解释主责”却没有清晰切分

### 3.2 常见职责切分模板

- `startup`：Paul Graham 看问题真假，Jobs 看价值主张，Munger 看自欺，Taleb 看下行风险
- `product`：Jobs 看体验裁剪，Zhang Yiming 看机制闭环，Musk 看结构简化，Munger 看错误配置
- `learning`：Feynman 看解释清晰，Karpathy 看实现路径，Ilya 看方向重要性
- `content`：MrBeast 看传播张力，Feynman 看讲明白，Zhang Xuefeng 看接地气，Naval 看长期定位

---

## 4. 标签平衡规则

每次会议选人后必须检查：

1. 至少 1 个 `defensive`
2. 至少 1 个 `grounded`
3. `dominant` Agent 不超过参会人数一半
4. 出现 `abstract` Agent 时，优先搭配 `grounded` Agent
5. 出现多个 `offensive` Agent 时，优先补 `Taleb` 或 `Munger`

如果不满足：

- 优先自动补位
- 若受 `--with / --without` 限制仍无法满足，主持人必须显式提示当前会议结构偏斜

---

## 5. Roundtable Profile 规则

圆桌模式优先读取各 skill 目录下的 `roundtable-profile.md`。

该文件只负责提供：

- 角色边界
- 典型关注点
- 讨论中的语气约束
- 默认不该越界的区域

禁止：

- 在圆桌模式中整段注入完整 skill prompt
- 因为某个 Agent profile 缺失，就把它的完整人格说明塞进会议上下文

缺 profile 时的回退机制：

- 使用本文件中的角色卡摘要
- 明确标记“使用简化角色卡”
- 保持职责边界，不扩张人格表演
