# 圆桌会议 /room 开发板块任务优先级与进度量化表

生成日期: 2026-04-16
审查口径: 基于 D:\圆桌会议 交接文档、Session 8-19 报告、C:\Users\CLH\tools\room-orchestrator-harness 源码与 2026-04-16 本地测试结果。

## 0. 当前基线

- 交接目录: `D:\圆桌会议`
- 真实开发工作区: `C:\Users\CLH`
- 当前 harness 工作区: `C:\Users\CLH\tools\room-orchestrator-harness`
- 最新本地验证: `node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js`
- 当前验证结果: 48 tests / 48 pass / 0 fail
- 当前主线总进度估算: 85%

## 1. 任务优先级总览

| 优先级 | 开发板块 | 任务 | 当前状态 | 下一步判定 |
|---|---|---|---|---|
| P0 | 真实 provider 接入 | 配置真实 `ROOM_CHAT_COMPLETIONS_URL` / `ROOM_CHAT_COMPLETIONS_MODEL` / 可选 `ROOM_PROVIDER_AUTH_BEARER` | wrappers 和本地 mock 集成已完成,真实 endpoint 未配置 | 这是接力后的第一动作 |
| P1 | 真实 prompt-call dry-run | 用 Chat Completions wrapper 跑 `room_chat` / `room_chat` / `room_summary` / `room_upgrade` 三段真实 dry-run | 本地 mock CLI integration 已通过 | P0 配置完成后立即执行 |
| P2 | P3 + Flow F true live rerun | 用真实 provider 输出重跑 @agent / 强制补位 / Flow F handoff packet | deterministic fixture、规则模拟、prompt-level contract 已通过 | P1 通过后执行 |
| P3 | 低优先级协议债 | 处理 F11 / F16 / F17 / F18 等 room-chat 文档清晰度问题 | 未处理,不阻塞真实 provider 接入 | P2 通过后批量处理 |
| P4 | v0.1.3 剩余 selection 歧义 | 处理 `VALIDATION-REPORT-selection.md §13.6` 的中低严重度歧义 | 行为正确性已通过,规则清晰度仍有债 | 与 P3 同批或其后处理 |
| P5 | Phase 6 skill mode 升级 | 将 13 个旧 skill 从 `debate_only` 升级为 `debate_room` | 未开始,明确长期项 | 真实链路稳定后再做 |
| P6 | Phase 7 自动发现扫描 | 实现 registry 自动发现/扫描脚本 | 未开始,明确长期项 | Phase 6 后再做 |
| 禁止/暂缓 | UI / 持久化 / 完整 command parser | 聊天室 UI、room state 落盘、完整 `/room` parser | 当前 scope 外 | 不应抢跑 |

## 2. 开发板块百分比进度表

| 板块 | 进度 | 状态 | 依据 | 剩余工作 |
|---|---:|---|---|---|
| `/debate` 现有闭环 | 100% | 已完成 | AGENTS / docs / prompts / skill 既有闭环,本项目要求零改动 | 无 |
| 交接文档与决策锁 | 95% | 基本完成 | `HANDOFF.md`, `NEXT-STEPS.md`, `DECISIONS-LOCKED.md`, Session 8-19 报告已连续同步 | 本报告追加后补齐最新审查视图 |
| `/room` 协议层 | 92% | 可用但有协议债 | `room-architecture.md`, `room-selection-policy.md`, `room-to-debate-handoff.md` 已落地,Session 8 P0/P1/P3 修补关键阻塞 | F11/F16/F17/F18 与 §13.6 部分清晰度补丁 |
| `/room` prompt 层 | 95% | 主链路完成 | `room-selection.md`, `room-chat.md`, `room-summary.md`, `room-upgrade.md` 已落地并进入 harness 调用链 | 真实 provider 输出验证后可能需要微调 |
| `room-skill` 调度入口 | 90% | 协议入口完成 | Flow A-F、状态唯一写者、prompt 纯消费者边界已写入 | 真实运行后校正 Flow F / @agent 边缘路径 |
| deterministic orchestrator harness | 100% | 当前 scope 完成 | P3 fixtures、Flow F fixture、dry-run chain、state reducer、validators、packet builder 均有测试 | 无,除非真实 rerun 暴露新增测试需求 |
| packet builder + upgrade contract checklist | 100% | 完成 | Session 10 已把 checklist 转成 `validateRoomUpgradeContract()` 与测试 | 无 |
| prompt-call adapter layer | 100% | 完成 | `runRoomChatPrompt`, `runRoomSummaryPrompt`, `runRoomUpgradePrompt`, `runDryRunWithPromptCalls` 已接入并测试 | 无 |
| external executor contract | 100% | 完成 | `createExternalExecutor()`, CLI `--prompt-executor`, 本地外部命令 dry-run 测试通过 | 无 |
| provider wrappers 本地 contract | 100% | 完成 | `http-provider-wrapper.js`, `chat-completions-wrapper.js`, 本地 mock 测试通过 | 无 |
| 真实 provider 配置与 dry-run | 0% | 阻塞中 | Session 19 明确缺 `ROOM_CHAT_COMPLETIONS_URL` / `ROOM_CHAT_COMPLETIONS_MODEL` | 配置 endpoint/model/auth 并跑真实 dry-run |
| P3 / Flow F true live rerun | 0% | 未开始 | 仍等待真实 provider 输出 | P1 真实 dry-run 通过后执行 |
| 低优先级协议债 | 0% | 未开始 | F11/F16/F17/F18 等仍列为后续项 | P2 后处理 |
| Phase 6: 13 旧 skill mode 升级 | 0% | 长期项 | 决议要求先验证孙宇晨试点和真实链路 | 主线稳定后逐个升级 |
| Phase 7: 自动发现扫描器 | 0% | 长期项 | 决议 6/16/27 已定位为后续能力 | Phase 6 后再规划 |
| Full `/room` parser / persistent storage / UI | 0% | 明确 out of scope | README 与决议均不纳入当前主线 | 不做 |

## 3. 当前主线完成度拆分

| 主线范围 | 权重 | 当前完成 | 折算贡献 |
|---|---:|---:|---:|
| 协议与 prompt 契约 | 25% | 94% | 23.5% |
| deterministic harness 与测试 | 25% | 100% | 25.0% |
| prompt-call adapter / external executor / wrapper contract | 25% | 100% | 25.0% |
| 真实 provider dry-run 与 live rerun | 20% | 0% | 0.0% |
| 协议债收口与接力文档 | 5% | 60% | 3.0% |
| 合计 | 100% | 约 76.5% | 76.5% |

说明: 上表是“端到端真实可用”的严格口径。如果采用 Session 19 的“当前里程碑功能闭环”口径,因为真实 provider 配置属于外部阻塞而非本地开发缺口,总进度仍可记为 85%。建议对外汇报使用 85%,对工程交付使用 76.5% 严格口径。

## 4. 建议审查结论

1. 现在不应再做新的协议发散,也不应进入 Phase 6/7。
2. 最高优先级是拿到真实 Chat Completions-compatible endpoint,用现有 CLI 跑真实 dry-run。
3. 真实 dry-run 成功前,F11/F16/F17/F18 和 §13.6 歧义先不要抢跑,避免修完又被真实输出推翻。
4. 若真实 dry-run 失败,优先把失败转成 harness 测试,再改 prompt 或 wrapper。
5. 若真实 dry-run 通过,立即执行 P3 + Flow F true live rerun,然后批量收口协议债。

## 5. 接力执行命令

真实 provider dry-run 命令:

```powershell
$env:ROOM_CHAT_COMPLETIONS_URL = '<真实 endpoint>'
$env:ROOM_CHAT_COMPLETIONS_MODEL = '<真实 model>'
$env:ROOM_PROVIDER_AUTH_BEARER = '<可选 token>'
node C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js --dry-run-fixture D:\圆桌会议\SESSION-8-DRY-RUN-FIXTURE.json --prompt-executor node --prompt-executor-arg C:\Users\CLH\tools\room-orchestrator-harness\src\chat-completions-wrapper.js
```

本地稳定基线命令:

```powershell
node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js
```
