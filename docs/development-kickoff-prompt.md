# Development Kickoff Prompt

> Purpose: provide a reusable start-of-task prompt for local agents working on this repository.
> Last reviewed: 2026-04-21

---

## Use This Prompt

Copy the prompt block below and send it to the local agent when starting a new development task for this repository.

This prompt is designed to force a correct startup sequence:

1. inspect the local repo first
2. analyze the whole project structure from source-of-truth files
3. quantify development progress by section
4. rank remaining tasks by priority
5. give a short execution plan before editing
6. then continue development

---

## Reusable Prompt

```text
项目路径：
/Users/markdonish/Documents/Codex/2026-04-21-mac-github-https-github-com-mark/round-table-workspace

继续这个项目开发。

执行要求：

1. 先按以下文件作为真源启动，不要跳步：
   - AGENTS.md
   - README.md
   - docs/development-sync-protocol.md
   - docs/
   - prompts/
   - examples/
   - .codex/skills/

2. 开始前先检查本地仓库状态：
   - git status -sb
   - git log --oneline -5
   - git remote -v

3. 必须先综合分析整个项目文件，再开始任何代码改动。分析时要明确区分：
   - 哪些是 source of truth
   - 哪些是历史报告 / artifacts
   - 哪些是已完成的核心能力
   - 哪些是未完成的核心能力
   - 哪些是当前真正的上线阻塞项

4. 先输出一份“项目开发进度汇报”，必须按板块逐项量化，用百分点统计，不允许只写模糊描述。

   进度汇报至少包含以下板块：
   - 仓库与开发同步链路
   - /debate 协议与 skill 层
   - /room 协议层
   - /room runtime bridge
   - /room live provider integration
   - prompts 层
   - docs / examples / skills 真源层
   - 验证与测试层
   - 上线 readiness

   输出格式要求：

   | 板块 | 当前进度 | 状态判断 | 依据 | 剩余工作 |
   |---|---:|---|---|---|

   百分点要求：
   - 用 0%-100% 量化
   - 必须给出判断依据
   - 不要假设项目已经 100% 完成
   - 如果某板块只是 fixture 验证通过，但 live 未验证，不能按 100% 计算

5. 在板块汇报之后，再给一份“剩余开发任务优先级列表”，按优先级排序。

   输出格式要求：

   | 优先级 | 任务 | 当前状态 | 为什么现在做 | 完成标准 |
   |---|---|---|---|---|

   优先级至少分：
   - P0：当前上线阻塞项
   - P1：主链路关键任务
   - P2：重要但不阻塞上线
   - P3：清理、补文档、低优先级债务

6. 在真正改代码或改文档之前，先给一个简短执行计划。

   执行计划要求：
   - 只写接下来准备做的 3-5 步
   - 必须是从当前真实状态出发，不要重复仓库介绍
   - 如果存在明显阻塞，要先写阻塞

7. 然后再继续开发，不要停留在分析层。

8. 开发时遵守以下硬约束：
   - docs/、prompts/、examples/、.codex/skills/ 是真源
   - reports/ 是历史记录，不是唯一真源
   - artifacts/ 是运行产物，不是实现源
   - 不要把整个用户主目录当项目根目录
   - 不要把旧 Windows 路径当当前实现入口
   - 不要假设项目已经 100% 完成
   - 除非明确要求，否则不要重构仓库结构

9. 每完成一个已验证的小里程碑后：
   - 自查改动范围
   - 进行最相关的本地验证
   - commit
   - push 到 GitHub main
   - 汇报：改了什么、怎么验证的、还剩什么

10. 最终汇报必须明确区分：
   - 已完成
   - 部分完成
   - 未完成
   - 被阻塞

本次具体任务：
<把这里替换成你这次真正要做的任务>
```

---

## Notes

This prompt is intentionally strict.

Its job is to prevent three common failures:

1. skipping repo analysis and editing too early
2. overstating progress without percentage-based evidence
3. confusing historical reports with current checked-in source
