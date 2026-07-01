# Round Table Workspace（圆桌会议工作区）

[![CI](https://github.com/MarkDonish/round-table-workspace/actions/workflows/ci.yml/badge.svg)](https://github.com/MarkDonish/round-table-workspace/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Local First](https://img.shields.io/badge/local--first-yes-2ea44f)
![AI Agents](https://img.shields.io/badge/AI%20agents-round--table-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

在线演示：https://markdonish.github.io/round-table-workspace/

让你的 AI 编程代理在交付前，先开一场圆桌会。

Round Table Workspace 是一个本地优先的决策层，面向 Codex、Claude Code
以及其他 CLI agent。它把模糊的产品和工程问题转成结构化的 `/room` 探索，在
高风险选择前升级到 `/debate`，并提供 `ship-check` 出货前检查门：在你相信
某个 AI 生成答案之前，先拿到一个务实的 ship / revise / reject 评审结果。

```bash
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw room "What is the smallest useful MVP for this idea?"
./rtw debate "Is this launch ready?"
./rtw doctor --quick
```

`ship-check` 的输出大致长这样：

```text
Decision: revise
Panel: product, engineering, risk, user-advocate
Why: useful direction, but public claims and evidence need tightening
Next: run tests, add a visible demo, keep claims local-first unless validated
```

## 为什么做这个

AI 编程代理很快，有时候快过头了。

它们可能在还没人问清楚之前，就已经写出一个功能：

- 这个东西真的应该做吗？
- 什么证据会改变我们的判断？
- 我们忽略了什么用户风险？
- 它是真的可以发布，还是只是看起来合理？
- 我们有没有在没有证据的情况下声称 host-live / provider-live 支持？

Round Table Workspace 在执行前加了一层决策协议。它不是另一个聊天 UI，而是
一个可提交到仓库里的协议、CLI、schema、带 fixture 的运行时，以及一套证据
记录方式，用来让 AI 辅助决策可以被复盘、审查和追责。

## 30 秒快速体验

运行新的出货前决策门：

```bash
./rtw ship-check "Launch the new AI-generated onboarding flow"
```

运行适合新 clone 的自检：

```bash
./rtw doctor --quick
```

尝试带 fixture 的 room / debate 命令面：

```bash
./rtw room "I want to build an AI study product for college students"
./rtw debate "Should this MVP be shipped this week?"
```

不配置 provider，也可以跑黄金路径演示：

```bash
./rtw demo startup-idea
```

大多数命令都支持适合自动化读取的输出：

```bash
./rtw ship-check "Should we merge this?" --output-json /tmp/ship-check.json --quiet
./rtw room "topic" --json
./rtw release-check --include-fixtures --quiet --output-json /tmp/rtw-release-check.json
```

## 工作方式

```mermaid
flowchart TD
    A[模糊想法或 AI 生成改动] --> B[/room 探索]
    B --> C[summary + handoff packet]
    C --> D[/debate 决策评审]
    D --> E{ship-check gate}
    E -->|ship| F[带证据继续推进]
    E -->|revise| G[修风险 / 补证据]
    E -->|reject| H[停止或重新定义问题]
    F --> I[JSON + Markdown artifacts]
    G --> I
    H --> I
```

核心命令面：

| 命令 | 什么时候用 | 输出 |
|---|---|---|
| `ship-check` | 在信任 AI 生成工作前，需要快速得到 ship / revise / reject 评审 | panel 投票、风险、缺失证据、下一步 |
| `/room` / `./rtw room` | 还在探索主题，需要一个有状态的多 agent 讨论 | 被选中的 panel、结构化轮次、总结、可选 handoff packet |
| `/debate` / `./rtw debate` | 高风险决策需要圆桌评审 | launch bundle、round-table record、reviewer result、allow/reject/follow-up outcome |
| `doctor` | 想知道新 clone 能不能在本地跑起来 | 指定 state root 下的 JSON / Markdown 证据 |
| `release-check` | 需要 release 范围的验证证据，但不想用历史报告替代当前状态 | 聚合后的 readiness evidence |

## 适合场景

- AI 生成代码或文档的发布前评审
- 做 MVP 前的产品决策审查
- 重构前的架构取舍审查
- 对外发布声明前的风险审查
- 本地优先的 agent 工作流实验
- 为 Codex / Claude Code 项目生成决策证据
- 训练团队不要盲信单个自信的 agent 答案

## 当前支持范围

当前版本：current release is `v0.2.2-pages-launch-kit`。

这个仓库目前可以用于：

- Codex 本地主线 `/room`
- Codex 本地主线 `/debate`
- Codex 本地主线 `/room -> /debate`
- 基于 fixture 的 `ship-check` 决策门脚手架
- 已提交的协议文档、prompts、skill 入口、runtime bridge 和验证 harness
- 作为 adapter layer 的 Claude Code 项目级 skill discovery 结构
- 经过 fixture 验证的通用本地 agent adapter contract
- 适合新 clone 的自检和发布后 consumer audit
- host / provider live-lane 证据报告
- Chat Completions 兼容 fallback 与 mock regression 工具

这个仓库目前不声称：

- 通用支持所有本地 agent host
- 已支持 OpenCode host-live
- 在各自 validation row 报告 `live_passed` 前，已支持 Gemini CLI、Aider、
  Goose 或 Cursor Agent host-live
- 在有效 `.env.room` / `.env.debate` 存在且 live validation 通过前，已支持
  真实 Chat Completions 兼容 provider-live
- 在所有机器和账号环境下都具备通用生产稳定性

本项目会刻意保守处理对外声明。fixture 通过、wrapper 存在、config preflight
通过，都不会被描述成真实 host-live 或 provider-live 支持；只有匹配的验证证据
存在时才会这样说。

## 仓库结构

```text
round-table-workspace/
├─ README.md
├─ LAUNCH.md
├─ AGENTS.md
├─ CHANGELOG.md
├─ docs/
├─ schemas/
├─ agents/
├─ config/
├─ roundtable_core/
├─ scripts/
├─ skills_src/
├─ evals/
├─ prompts/
├─ examples/
├─ .codex/skills/
├─ .claude/skills/
├─ reports/
└─ artifacts/
```

当前事实源：

- `AGENTS.md`
- `LAUNCH.md`
- `docs/`
- `schemas/`
- `agents/`
- `config/`
- `roundtable_core/`
- `scripts/`
- `skills_src/`
- `evals/`
- `prompts/`
- `examples/`
- `.codex/skills/`
- 作为 adapter layer 的 `.claude/skills/`

历史或生成材料：

- `reports/`
- `artifacts/`

如果某份 report 或 artifact 暴露了仍然有效的规则，应把规则迁移到 active source
文件，而不是继续让历史材料充当权威来源。

## 关键文档

| 文档 | 用途 |
|---|---|
| `LAUNCH.md` | 新 clone 的最短安全启动路径 |
| `docs/index.md` | 按用户、协议、运行时、验证和历史区域组织的文档地图 |
| `docs/user-entry-guide.md` | 用普通语言解释仓库逻辑的入口指南 |
| `docs/agent-consumer-quickstart.md` | Codex、Claude Code 和通用本地 agent 的使用命令 |
| `docs/source-truth-map.md` | source 与历史 / 输出材料的边界 |
| `docs/release-readiness.md` | release gate 规则 |
| `docs/release-candidate-scope.md` | 支持范围和对外声明边界 |
| `docs/roadmap.md` | 项目路线图和 release horizon |
| `docs/milestones/v0.2.0.md` | v0.2.0 milestone scope 和 issue 拆分 |
| `docs/launch-copy.md` | 面向 X、Hacker News、Reddit 和社区帖的发布文案 |
| `docs/demo.html` | 可用于 GitHub Pages 或截图的静态视觉 demo |
| `docs/protocol-spec.md` | `/room`、`/debate` 和 handoff 协议总览 |
| `docs/protocol-versioning.md` | release、protocol、schema、runtime、prompt、fixture 的版本边界 |
| `docs/decision-quality-rubric.md` | 可机器检查的决策质量 rubric |
| `docs/schema-validation-subset.md` | Draft 2020-12 fallback validator 边界 |
| `docs/skill-generation.md` | 生成 skill 的摘要和 drift-check 维护方式 |
| `docs/agent-factory-architecture.md` | Agent Factory manifest、profile 和 registry 生命周期 |
| `agents/registry.json` | runtime bridge 使用的机器可读 agent registry |
| `config/agent-registry.json` | Agent Factory custom / candidate registry |
| `schemas/room-session.schema.json` | 可移植的 `/room` session state schema |
| `schemas/debate-session.schema.json` | 可移植的 `/debate` session state schema |
| `schemas/debate-result.schema.json` | 可移植的 `/debate` result schema |
| `schemas/room-to-debate-handoff.schema.json` | 可移植的 `/room -> /debate` handoff schema |
| `schemas/agent-manifest.schema.json` | Agent Factory manifest schema |
| `schemas/agent-registry.schema.json` | Agent Factory custom / candidate registry schema |
| `schemas/agent-selection-request.schema.json` | 未来 selection bridge request schema |
| `docs/room-architecture.md` | `/room` 协议和行为 |
| `docs/debate-skill-architecture.md` | `/debate` 协议和行为 |
| `docs/room-to-debate-handoff.md` | 从探索到评审的 handoff contract |
| `docs/generic-local-agent-adapter.md` | 通用本地 CLI agent contract |
| `examples/transcripts/` | `/room`、`/debate` 和 handoff 的示例 walkthrough |
| `reports/claim-boundary-dashboard.md` | 仅为生成快照；当前状态请运行 `./rtw evidence` 或 `./rtw release-check` |
| `CHANGELOG.md` | release 历史 |

## Host 和 Provider 边界

默认路径是 local-first。Provider URL 是可选项，只属于 Chat Completions 兼容
fallback 或 live validation lane。

在对 host 或 provider 做支持声明前，先生成证据：

```bash
python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --state-root /tmp/round-table-live-lane-evidence
```

Codex 本地主线可运行：

```bash
python3 .codex/skills/room-skill/runtime/local_codex_regression.py \
  --state-root /tmp/round-table-local-codex-regression
```

release 范围检查可运行：

```bash
./rtw release-check --include-fixtures --state-root /tmp/round-table-release-check
```

## 贡献

欢迎贡献，但必须保留 claim boundary：不要把 fixture 通过说成 host-live 或
provider-live 支持。请从 `CONTRIBUTING.md` 开始，默认保持 local-first，并在 PR
里附上新的验证证据。

## 开发备注

仓库级规则在 `AGENTS.md`。后续开发应先读：

1. `AGENTS.md`
2. `docs/source-truth-map.md`
3. `docs/development-sync-protocol.md`
4. `docs/release-readiness.md`

默认开发规则：

- 本地开发
- 本地验证
- 提交已验证改动
- 推送到 `origin/main`
- 报告改了什么、验证了什么，以及哪些内容仍在 claim boundary 之外
