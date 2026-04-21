# HANDOFF

生成日期：2026-04-10
目的：给下一个接力开发的 Agent 提供最短上手路径。

## 这是什么项目

这是一个面向 Mark 的“多 Agent / 多 skill 决策操作系统”。

当前系统已经有正式的 `/debate` 模式：
- 只在用户显式输入 `/debate` 时触发
- 基于本地名人 skill 组织 3-5 个 Agent 参会
- 强调分工、主持、审查、统一决议

本轮新增需求是设计第二种模式 `/room`：
- 用于半结构化多 Agent 房间
- 核心用途是协同推演，不是闲聊
- 与 `/debate` 共存，不替代 `/debate`

## 当前已经完成什么

已经完成的不是代码实现，而是协议层和产品层设计：

- 重新确认并固化了现有 `/debate` 的系统边界
- 定义了 `/room` 的产品定位和与 `/debate` 的关系
- 定义了 `/room` 的命令语义
- 定义了 `/room` 的房间状态模型
- 明确 `/room` 和 `/debate` 都必须复用本地名人 skill
- 设计了新增 skill 的“自动发现 + 条件注册”机制
- 设计了后台筛选参会 Agent 的半结构化评分系统
- 补完了 `/room` 的发言机制、换人机制、`/room -> /debate` 交接协议

## 最重要的边界

1. `/debate` 继续保持正式圆桌会议模式，不要把它改成聊天室。
2. `/room` 是半结构化多 Agent 房间，核心是协同推演。
3. 不创建新人格体系，Agent 必须来自本地已安装名人 skill。
4. 新增 skill 不能安装即参会，必须先自动发现，再条件注册。
5. 选人不是全员参会，而是按议题、子问题、阶段和结构平衡筛选。

## 接手顺序

先看：
1. `room-debate-development-report-2026-04-10.md`
2. `DECISIONS-LOCKED.md`
3. `NEXT-STEPS.md`

## 主报告位置

- `D:\圆桌会议\room-debate-development-report-2026-04-10.pdf`
- `D:\圆桌会议\room-debate-development-report-2026-04-10.md`

## 接手建议

不要重新讨论“要不要做 `/room`”。
这个问题已经定了。下一位 Agent 应直接进入协议落地和文档/实现层继续开发。
