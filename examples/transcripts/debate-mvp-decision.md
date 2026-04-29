This is an illustrative transcript, not host-live or provider-live validation evidence.

# Transcript: `/debate` MVP Decision

This example shows the shape of a formal `/debate` review. It is hand-written
to demonstrate the protocol and should not be read as output from a live host,
provider, or release validation run.

Topic: 面向大学生的 AI 学习产品是否值得先做 MVP

## User Starts A Debate

```text
/debate 面向大学生的 AI 学习产品，是否值得先做一个 MVP？
```

## Step 1. Identify The Issue

- 议题原文：面向大学生的 AI 学习产品，是否值得先做一个 MVP？
- 问题边界：判断是否进入 MVP，而不是直接判断是否长期创业。
- 议题在问什么：是否存在足够强的早期验证理由，以及 MVP 应该多轻。

## Step 2. Classify The Task

- 主分类：`startup`
- 副分类：`product`
- 分类理由：核心是方向是否值得启动，同时涉及 MVP 范围与产品主张。
- 为什么不是纯 `product`：还没有稳定需求证据，不能只讨论功能取舍。

## Step 3. Select Panel

| Agent | Role In This Debate | Why Included |
|---|---|---|
| `paul-graham` / PG | 机会真假与切口审查 | 判断是否有足够窄、足够真实的问题 |
| `steve-jobs` / Jobs | 价值主张与体验聚焦 | 防止 MVP 变成功能清单 |
| `munger` / Munger | 机会成本与偏差审查 | 检查创始人投射和错误配置 |
| `taleb` / Taleb | 下行风险与脆弱性 | 防止重投入和伪信号 |

主持人：圆桌调度器
审查 Agent：讨论质量审查者

## Step 4. Assign Work

- PG：判断这个问题是否真实、切口是否够窄；不负责风险兜底。
- Jobs：判断用户价值主张是否可感知；不负责市场规模推演。
- Munger：检查偏差、机会成本、资源错配；不负责包装叙事。
- Taleb：评估不对称风险和脆弱性；不负责鼓励启动。

## Step 5. Agent Statements

### PG

1. 角色职责：判断机会真假与切口。
2. 核心结论：值得做验证，不值得直接做完整 MVP。
3. 判断依据：
   - “大学生学习”太宽，但“考试前 48 小时复习路径”更像具体痛点。
   - 早期最该验证的是是否有人交出真实资料并愿意付费或复用。
   - 如果手工服务没有需求，软件化会放大错误。
4. 当前方案最大问题：MVP 范围容易过大。
5. 我反对的常见误判：把“学生很多”误当成“需求很强”。
6. 具体建议：先做 10 个学生、1 门课、48 小时复习路径的 concierge test。
7. 置信度：中。
8. 不确定项：真实学生是否愿意为复习路径付费。

### Jobs

1. 角色职责：判断价值主张和体验聚焦。
2. 核心结论：MVP 必须卖结果，不要卖 AI。
3. 判断依据：
   - 用户不会因为“AI 学习产品”本身行动。
   - “考试前知道先复习什么”比“智能学习助手”更直接。
   - 首版体验应围绕一次明确交付，而不是账号、图谱、社区等功能。
4. 当前方案最大问题：价值主张还不够尖。
5. 我反对的常见误判：把功能列表当作产品体验。
6. 具体建议：把 MVP 定义成“一份可执行复习路径 + 重点题型解释”。
7. 置信度：中。
8. 不确定项：不同课程对“可执行路径”的要求差异。

### Munger

1. 角色职责：检查偏差和机会成本。
2. 核心结论：只有在成本极低时才值得做。
3. 判断依据：
   - 创始人容易把自己的学习方式投射成普遍需求。
   - 学生价格敏感，感谢和付费不是一回事。
   - 若一开始做系统，机会成本会高于信号价值。
4. 当前方案最大问题：容易把兴趣当市场。
5. 我反对的常见误判：把“愿意试用”当成“愿意持续使用”。
6. 具体建议：预设退出条件：10 人里少于 3 人愿意付费或复用，就暂停。
7. 置信度：高。
8. 不确定项：校园渠道是否能显著降低获客成本。

### Taleb

1. 角色职责：识别脆弱性和尾部风险。
2. 核心结论：可以做小下注，不能做重产品。
3. 判断依据：
   - 考试周需求有尖峰，复用频率可能不足。
   - 课程差异会制造隐藏交付成本。
   - 过早自动化会让失败成本不对称。
4. 当前方案最大问题：MVP 容易伪装成大工程。
5. 我反对的常见误判：把一次高压场景的需求外推到长期留存。
6. 具体建议：只用人工、表单、共享文档和现成 AI 工具完成第一轮。
7. 置信度：高。
8. 不确定项：某些资格考试或统一课程是否能形成更稳定需求。

## Step 6. Moderator Summary

- 议题重述：是否值得先做大学生 AI 学习产品 MVP。
- 共识点：
  - 值得做低成本验证。
  - 不值得直接开发完整产品。
  - 首轮必须缩到一个高压考试场景。
  - MVP 应验证付费、复用和交付成本。
- 核心分歧：需求是否能从考试周尖峰扩展成长期产品。
- 隐含假设：
  - 学生真的愿意为“复习路径”付出成本。
  - 一门课的验证能代表相邻课程。
- 初步建议：做 concierge MVP，不做软件化 MVP。
- 审查重点：下一步是否足够具体，停止条件是否明确。

## Step 7. Reviewer Result

1. 本轮讨论总体评分：8。
2. 履职最好的 Agent：Munger，明确给出机会成本和退出条件。
3. 偷懒或空泛的 Agent：无。
4. 缺证据的论点：没有真实学生访谈或付费数据，必须标为不确定。
5. 逻辑跳跃点：不能从 10 人测试直接推导长期留存。
6. 被忽略的关键问题：首批学生来源和课程选择标准。
7. 是否允许进入最终决议：允许。
8. 如果不允许，需要补充什么：无。

## Step 8. Final Decision

单一最终建议：值得做一个极轻 concierge MVP，不值得开发完整软件 MVP。

核心理由：四位 Agent 的可见发言都指向同一结构：痛点可能存在，但当前证据不足以支持重投入；最有信息量的下一步是低成本服务化验证。

关键风险：

- 学生愿意试用但不愿付费。
- 考试周高峰需求无法转成稳定留存。
- 课程差异导致人工交付成本失控。

下一步动作：

1. 只选 1 门高压考试课程。
2. 找 10 个真实学生交付资料。
3. 用人工方式交付 48 小时复习路径。
4. 记录是否付费、是否复用、是否推荐同学。

停止条件：10 人里少于 3 人愿意付费或复用，暂停产品化，只保留学习记录；如果超过 5 人愿意付费或主动推荐，再讨论自动化 MVP。

## What This Transcript Demonstrates

- `/debate` only starts after an explicit `/debate` command.
- The flow follows identify, classify, select panel, assign work, speak,
  summarize, review, and final decision.
- Reviewer approval is based only on visible discussion artifacts.
- The final decision is single, actionable, and claim-safe.
