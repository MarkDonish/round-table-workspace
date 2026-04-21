# Task Router

这份文档是 Mark 版框架的“快速路由器”。目标只有一个：

> 看到一个问题后，先判断它属于哪类任务，再调用最少且最合适的 skill 组合，而不是凭感觉乱选。

默认原则：

1. 先分任务类型，再选 skill
2. 默认 2-3 个 skill，复杂问题最多 4 个
3. 先控制风险，再做低成本验证，再谈放大
4. 先分工，后汇总

---

## 1. 快速路由总表

| 任务类型 | 典型问题 | 默认 skill 组合 | 为什么这么配 | 不该优先调用的 skill |
| --- | --- | --- | --- | --- |
| `student-founder` | 我该先顾学业、创业、内容还是技能？ | Naval + Munger + Zhang Xuefeng | 一个看长期方向，一个看机会成本，一个看大学生现实约束 | Trump、MrBeast、Ilya |
| `validation` | 这个想法怎么低成本验证？ | Paul Graham + Taleb + Zhang Xuefeng | 一个定义验证目标，一个控验证风险，一个把动作拉回现实 | Trump、Ilya、MrBeast |
| `startup` | 这个创业方向值不值得做？ | Paul Graham + Steve Jobs + Munger | 一个看问题真假，一个看价值主张，一个防自欺 | Trump、MrBeast |
| `product` | 这个功能该不该做？ | Steve Jobs + Zhang Yiming + Elon Musk | 一个做取舍，一个设计反馈闭环，一个拆冗余复杂度 | Trump、Naval |
| `learning` | 这个概念/代码怎么理解？ | Feynman + Karpathy | 一个讲明白，一个给技术直觉 | Trump、MrBeast |
| `output` | 学完后怎么变成内容/作品？ | Feynman + Zhang Xuefeng + MrBeast | 一个结构化，一个接地气，一个增强传播钩子 | Ilya、Trump |
| `content` | 这个选题怎么更容易传播？ | MrBeast + Feynman + Zhang Xuefeng | 一个拿注意力，一个保清晰，一个保现实感 | Ilya、Trump、Naval |
| `content-product-loop` | 内容怎么给产品导流？ | MrBeast + Jobs + Zhang Yiming + Munger | 一个拿流量，一个守主张，一个做机制，一个防伪增长 | Trump、Ilya |
| `risk` | 这个方案哪里会出事？ | Taleb + Munger | 一个看尾部风险，一个看认知偏差 | MrBeast、Trump |
| `planning` | 未来 90 天怎么安排？ | Naval + Munger + Taleb | 一个看长期，一个看配置，一个看脆弱性 | Trump、MrBeast |
| `writing` | 怎么写得更清楚、更有判断力？ | Feynman + Paul Graham + Jobs | 一个讲清楚，一个拉直结构，一个压缩主张 | MrBeast、Trump |

---

## 2. 路由规则

### A. 先看是不是风险问题

如果问题里出现以下特征，优先路由到 `risk`：

- 大额投入
- all-in 倾向
- 不可逆损失
- 学业/现金流/健康可能受影响
- 你自己已经在问“会不会出事”

推荐组合：Taleb + Munger

原因：先把下行控制住，比先追求机会更重要。

不该优先调用：MrBeast、Trump

---

### B. 再看是不是验证问题

如果问题里出现以下特征，优先路由到 `validation`：

- “怎么先试一下”
- “不想先开发完整产品”
- “先验证需求/付费意愿/留存”
- “怎么低成本拿信号”

推荐组合：Paul Graham + Taleb + Zhang Xuefeng

原因：

- Paul Graham 负责定义真正要验证的假设
- Taleb 负责把测试成本压低
- Zhang Xuefeng 负责确保动作适合大学生现实资源

不该优先调用：MrBeast、Trump、Ilya

---

### C. 再看是不是创业方向问题

如果问题核心是“值不值得做”，路由到 `startup`：

- “这个方向是不是伪需求”
- “这个项目有没有机会”
- “该从哪个切口切入”

推荐组合：Paul Graham + Steve Jobs + Munger

原因：

- Paul Graham 看问题真假与切口
- Jobs 看主张是否够集中
- Munger 看你有没有自我感动

不该优先调用：MrBeast、Trump

---

### D. 如果是功能与 MVP 选择，路由到 `product`

触发信号：

- “这个功能要不要做”
- “MVP 先做哪些”
- “该砍掉哪些复杂度”
- “路线图怎么收敛”

推荐组合：Steve Jobs + Zhang Yiming + Elon Musk

原因：

- Jobs 负责删繁就简
- Zhang Yiming 负责反馈系统和迭代节奏
- Musk 负责拆掉伪复杂度

不该优先调用：Trump、Naval

---

### E. 如果是理解问题，路由到 `learning`

触发信号：

- “这到底是什么意思”
- “这段代码怎么理解”
- “给我讲懂这个概念”
- “AI / 模型 / 系统是怎么工作的”

推荐组合：Feynman + Karpathy

原因：

- Feynman 让你真正懂
- Karpathy 让你懂技术直觉和实现感

可选补位：Ilya 只用于前沿研究方向判断

不该优先调用：MrBeast、Trump

---

### F. 如果是“学完后怎么产出”，路由到 `output`

触发信号：

- “这个知识怎么写成内容”
- “怎么把学习变成输出”
- “怎么讲给别人听”
- “怎么整理成帖子、脚本、作品”

推荐组合：Feynman + Zhang Xuefeng + MrBeast

原因：

- Feynman 保证结构清楚
- Zhang Xuefeng 保证表达不悬空
- MrBeast 保证更容易被点开和传播

不该优先调用：Ilya、Trump

---

### G. 如果是内容本身，路由到 `content`

触发信号：

- “这个选题值不值得写”
- “标题怎么改”
- “怎么更容易传播”
- “内容怎么不空洞”

推荐组合：MrBeast + Feynman + Zhang Xuefeng

原因：

- MrBeast 抓注意力
- Feynman 保信息密度
- Zhang Xuefeng 保现实感和可读性

不该优先调用：Ilya、Trump、Naval

---

### H. 如果内容和产品要联动，路由到 `content-product-loop`

触发信号：

- “怎么用内容带产品”
- “内容怎么导流到产品”
- “产品怎么反哺内容选题”
- “我不想做纯流量内容”

推荐组合：MrBeast + Jobs + Zhang Yiming + Munger

原因：

- MrBeast 拿注意力
- Jobs 守产品主张
- Zhang Yiming 设计转化与反馈机制
- Munger 防止掉进伪增长陷阱

不该优先调用：Trump、Ilya

---

### I. 如果是规划问题，路由到 `planning`

触发信号：

- “未来 30/90 天怎么安排”
- “应该把重心放在哪”
- “哪些事该坚持，哪些该停”

推荐组合：Naval + Munger + Taleb

原因：

- Naval 给方向
- Munger 做取舍
- Taleb 保留缓冲

不该优先调用：Trump、MrBeast

---

### J. 如果是大学生身份约束下的多目标平衡，路由到 `student-founder`

触发信号：

- “我是大学生，现在该优先什么”
- “学业、创业、内容怎么平衡”
- “要不要 all-in 做项目”
- “在学生阶段怎么做最优配置”

推荐组合：Naval + Munger + Zhang Xuefeng

原因：

- Naval 看长期复利
- Munger 看配置错误
- Zhang Xuefeng 把选择拉回现实约束

高风险补位：Taleb

不该优先调用：Trump、MrBeast、Ilya

---

## 3. 不该调用的通用规则

以下情况，不要把这些 skill 放进默认组合：

### 不要默认用 `Trump`

除非问题明确是：

- 强势表达
- 谈判姿态
- 故意制造高冲击注意力

否则都不该优先用。

### 不要默认用 `MrBeast`

除非问题明确是：

- 选题传播
- 标题钩子
- 内容冷启动
- 内容导流

否则在风险、规划、创业判断里都不该让他主导。

### 不要默认用 `Ilya`

除非问题明确是：

- AI 前沿趋势
- 模型哲学
- 研究方向判断

否则在日常执行、学生创业选择、低成本验证里都不该优先用。

### 不要默认用 `Naval`

除非问题明确是：

- 长期方向
- 人生规划
- 杠杆与可持续性

否则在具体功能取舍、短期验证动作里不应优先调用。

---

## 4. 简化规则树

```text
用户提问
│
├─ 是否涉及高风险 / 大额投入 / 不可逆后果？
│  └─ 是 -> risk -> Taleb + Munger
│
├─ 是否在问“怎么先验证、低成本试一下”？
│  └─ 是 -> validation -> Paul Graham + Taleb + Zhang Xuefeng
│
├─ 是否在问“值不值得做一个方向”？
│  └─ 是 -> startup -> Paul Graham + Jobs + Munger
│
├─ 是否在问“功能 / MVP / 产品路线怎么取舍”？
│  └─ 是 -> product -> Jobs + Zhang Yiming + Musk
│
├─ 是否在问“怎么理解一个概念/代码/AI 原理”？
│  └─ 是 -> learning -> Feynman + Karpathy
│
├─ 是否在问“学完后怎么变成内容/作品”？
│  └─ 是 -> output -> Feynman + Zhang Xuefeng + MrBeast
│
├─ 是否在问“内容怎么更容易传播”？
│  └─ 是 -> content -> MrBeast + Feynman + Zhang Xuefeng
│
├─ 是否在问“内容怎么带产品 / 产品怎么喂内容”？
│  └─ 是 -> content-product-loop -> MrBeast + Jobs + Zhang Yiming + Munger
│
├─ 是否在问“未来一段时间怎么安排”？
│  └─ 是 -> planning -> Naval + Munger + Taleb
│
└─ 是否在问“大学生身份下怎么平衡多目标”？
   └─ 是 -> student-founder -> Naval + Munger + Zhang Xuefeng
```

---

## 5. 路由伪代码

```text
function route(question):
    if contains(question, [高风险, all-in, 大额投入, 不可逆, 会不会出事]):
        return risk, [Taleb, Munger]

    if contains(question, [低成本验证, 先试, 访谈, MVP前验证, 需求验证, 付费验证]):
        return validation, [Paul Graham, Taleb, Zhang Xuefeng]

    if contains(question, [值不值得做, 有没有机会, 是不是伪需求, 切口]):
        return startup, [Paul Graham, Steve Jobs, Munger]

    if contains(question, [功能要不要做, MVP, 优先级, 路线图, 砍功能]):
        return product, [Steve Jobs, Zhang Yiming, Elon Musk]

    if contains(question, [怎么理解, 讲懂, 原理, 代码怎么读, AI怎么工作]):
        return learning, [Feynman, Karpathy]

    if contains(question, [怎么输出, 怎么写成内容, 怎么讲给别人, 学完怎么产出]):
        return output, [Feynman, Zhang Xuefeng, MrBeast]

    if contains(question, [选题, 标题, 传播, 爆款, 内容怎么写]):
        return content, [MrBeast, Feynman, Zhang Xuefeng]

    if contains(question, [内容带产品, 导流, 转化, 产品反哺内容]):
        return content_product_loop, [MrBeast, Jobs, Zhang Yiming, Munger]

    if contains(question, [未来90天, 季度规划, 重心放哪, 怎么安排]):
        return planning, [Naval, Munger, Taleb]

    if contains(question, [大学生, 学业和创业, 身份约束, 该优先什么]):
        return student_founder, [Naval, Munger, Zhang Xuefeng]

    return startup, [Paul Graham, Munger]
```

---

## 6. 使用建议

### 最简用法

以后遇到问题，先做这 3 步：

1. 先问：这是风险、验证、方向、产品、学习、输出、内容、联动、规划里的哪一类？
2. 直接套用该类默认组合。
3. 再看是否需要加一个对冲 skill，而不是再多加一个同类 skill。

### 记忆口诀

- 先控风险：Taleb + Munger
- 先做验证：Paul Graham + Taleb + 张雪峰
- 做创业判断：Paul Graham + Jobs + Munger
- 做产品取舍：Jobs + 张一鸣 + Musk
- 做学习理解：Feynman + Karpathy
- 做学习输出：Feynman + 张雪峰 + MrBeast
- 做内容传播：MrBeast + Feynman + 张雪峰
- 做长期规划：Naval + Munger + Taleb

### 最后原则

如果你不确定选哪类，优先问自己：

> 我现在最需要的是降低风险、拿到验证信号，还是优化表达？

在 Mark 版框架里，默认优先级永远是：

`风险 > 验证 > 方向/产品 > 输出/内容 > 表达优化`

---

## 7. 与本地 skill 调用方式的兼容规则

当前路由器里的 `Jobs`、`Paul Graham`、`Taleb`、`Feynman` 等写法，默认是“认知角色简称”，不是对本地 skill 目录名的替换。

实际在 Codex 中调用时，优先使用你本地已安装的精确 skill 名：

| 路由器简称 | 本地实际调用名 |
| --- | --- |
| Jobs / Steve Jobs | `steve-jobs-skill` |
| Musk / Elon Musk | `elon-musk-skill` |
| Munger | `munger-skill` |
| Feynman | `feynman-skill` |
| Naval | `naval-skill` |
| Taleb | `taleb-skill` |
| Zhang Xuefeng | `zhangxuefeng-skill` |
| Paul Graham | `paul-graham-skill` |
| Zhang Yiming | `zhang-yiming-skill` |
| Karpathy | `karpathy-skill` |
| Ilya | `ilya-sutskever-skill` |
| MrBeast | `mrbeast-skill` |
| Trump | `trump-skill` |

### 推荐做法

- 看路由：可以看简称
- 真调用时：请写精确 skill 名

例如：

- 路由器推荐：`Paul Graham + Jobs + Munger`
- 实际调用写法：`paul-graham-skill + steve-jobs-skill + munger-skill`

---

## 8. `/debate` 专用路由说明

当用户明确输入 `/debate` 时，`router.md` 的日常路由规则要让位于圆桌模式，改为以下逻辑：

1. 先把议题分类到 `startup / product / learning / content / risk / planning / strategy / writing`
2. 自动选择 3-5 个默认 Agent 组合
3. 自动补对冲 Agent
4. 自动指定主持人和审查 Agent
5. 必须经过审查放行后才输出最终决议

`/debate` 下的默认组合如下：

- `startup`: Paul Graham + Steve Jobs + Munger + Taleb
- `product`: Steve Jobs + Zhang Yiming + Elon Musk + Munger
- `learning`: Karpathy + Feynman + Ilya Sutskever
- `content`: MrBeast + Feynman + Zhang Xuefeng + Naval
- `risk`: Taleb + Munger + Elon Musk
- `planning`: Naval + Munger + Taleb
- `strategy`: Paul Graham + Munger + Taleb + Zhang Yiming
- `writing`: Feynman + Naval + Zhang Xuefeng + Paul Graham

兼容原则保持不变：

- 路由器里的人名是角色简称
- 真正调用时优先回退到本地精确 skill 名
- 不改原有 skill 的独立调用方式
