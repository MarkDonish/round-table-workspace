# D:\圆桌会议 全量读档与主线纠偏审查报告

日期: 2026-04-16  
工作区: `C:\Users\CLH`  
交接目录: `D:\圆桌会议`  
审查目的: 补齐全量文档阅读,校正 `/room` 接力开发主线,明确下一步优先级。

## 1. 结论先行

我前面确实偏离了开发逻辑主线。

偏离点不是“写了 provider wrapper 相关代码本身完全没价值”,而是我把它错误提升成了当前 P0。完整读完 `D:\圆桌会议` 后,主线应重新校正为:

> `/room` 是本地 skill / 本地 Agent 编排器,参考 gstack workflow skill 的本地调用逻辑。provider / external executor / Chat Completions wrapper 只能作为 harness、CI、dry-run、外部适配层,不能成为本地 `/room` 运行的前置依赖。

当前正确优先级:

1. P0: 把 `room-skill` 的“本地 Agent 调用契约”落成可执行本地调度层,至少先支持 `local_sequential`。
2. P1: 对接 Agent Registry / local skill profile,把 selected speaker 解析为本地 skill/profile 任务。
3. P2: 用 `room-chat.md` 作为 speaker task 模板,而不是用 provider API 生成角色发言。
4. P3: 将每个 speaker 的本地输出合成 Turn 对象,写入 `conversation_log`,并跑 summary / upgrade 链路。
5. P4: 将 Session 8 P3 / Flow F fixtures 迁移为本地 dispatch e2e 测试。
6. P5: 再处理 F11/F16/F17/F18 与 selection §13.6 规则歧义。
7. P6: Phase 6 旧 skill mode 升级。
8. P7: Phase 7 自动发现扫描器。

## 2. 已核对事实

当前 `D:\圆桌会议` 无子目录,共 43 个文件。所有文件已逐项读取或核对:

- `.md` 报告: 已按 UTF-8 阅读。
- `.json` 夹具: 已 `ConvertFrom-Json` 解析并核对结构。
- `.html`: 已核对为 2026-04-10 development report 的 HTML 导出版。
- `.pdf`: 已核对 PDF header 与大小,视为同名 development report 的 PDF 导出版；本机没有 `pdftotext`,内容依据同名 `.md` / `.html` 核对。

当前 harness 测试基线:

```text
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'
tests 52
pass 52
fail 0
```

## 3. 文件清单与角色定位

| 文件 | 状态 | 角色定位 | 对主线的结论 |
|---|---|---|---|
| `DECISIONS-LOCKED.md` | 已读 | 决策锁 | `/room` 与 `/debate` 双模式共存；复用本地名人 skill；当前阶段禁止 UI/持久化/自动发现抢跑。 |
| `HANDOFF.md` | 已读 | Session 6 后交接 | Session 7 最重要动作是 `/room` end-to-end live validation,不是 provider 接入。 |
| `NEXT-STEPS.md` | 已读 | 累积后续路线 | 后期出现 provider wrapper,但它是 harness adapter 后续项,不能覆盖本地 Agent 主线。 |
| `PROJECT-STRUCTURE.md` | 已读 | 项目结构地图 | `D:\圆桌会议` 是交接目录；真实项目文件在 `C:\Users\CLH`。 |
| `TASK-PRIORITY-REPORT-2026-04-13.md` | 已读 | Session 9 后优先级 | 当时 P0 是 packet builder vs `room-upgrade.md` checklist,不是真实 provider 配置。 |
| `DEVELOPMENT-BOARD-PRIORITY-PROGRESS-2026-04-16.md` | 已读 | 我前面写的进度表 | 将 provider 配置误提为 P0,需要废弃该优先级口径。 |
| `room-debate-development-report-2026-04-10.md` | 已读 | 初始总设计报告 | `/room` 的 Agent 来源明确是本地名人 skill；当前阶段先协议/文档,再决定实现载体。 |
| `room-debate-development-report-2026-04-10.html` | 已核对 | 初始报告 HTML 导出 | 与同名 `.md` 内容同源。 |
| `room-debate-development-report-2026-04-10.pdf` | 已核对 | 初始报告 PDF 导出 | 与同名报告同源导出,未作为独立规范源。 |
| `VALIDATION-REPORT-selection.md` | 已读 | selection 活体验证 | v0.1.2 行为正确；§13.6 留下 10 个 v0.1.3 规则歧义。 |
| `VALIDATION-REPORT-e2e.md` | 已读 | Session 7 E2E 验证 | 用 subagent 模拟完整 `/room` 链路；暴露 F1-F23；证明本地 orchestrator/subagent 方向是主线。 |
| `SESSION-2-COMPLETION-REPORT.md` | 已读 | Agent Registry / selection 初版 | 强调 protocol layer,本地 skill 不移动目录,registry 只是索引。 |
| `SESSION-4-COMPLETION-REPORT.md` | 已读 | Phase 1.5 修补 | prompt 是消费者,orchestrator 拥有状态与边界。 |
| `SESSION-5-COMPLETION-REPORT.md` | 已读 | Phase 2 架构 | hybrid orchestrator: rules every turn, LLM only key nodes；state in memory。 |
| `SESSION-6-COMPLETION-REPORT.md` | 已读 | room-chat/summary/upgrade/skill 完成 | `room-skill` 是 glue layer 与 state writer；Session 7 应跑 E2E。 |
| `SESSION-8-P0-PATCH-REPORT.md` | 已读 | v0.1.3 P0 修补 | 修 F20/F1/F8/决议44/F2/F21,仍未真实 runtime 打包。 |
| `SESSION-8-P1-SELECTION-PATCH-REPORT.md` | 已读 | selection P1 修补 | room_turn 不再重算 roster 级信息增量,修 F9/F15/F13。 |
| `SESSION-8-FLOW-F-VALIDATION-REPORT.md` | 已读 | Flow F 协议验证 | 修 user_explicit 2 轮质量例外,仍非完整 runtime。 |
| `SESSION-8-FLOW-F-VALIDATION-PACKET.json` | 已解析 | Flow F handoff packet 样本 | 13 字段 packet 合法,包含 `user_forced_early_upgrade` warning。 |
| `SESSION-8-F14-ROOM-TURN-REGRESSION-REPORT.md` | 已读 | F14 回归 | 下调 room_turn task_type 权重,让子问题信号重新占主导。 |
| `SESSION-8-P3-SECTION12-AGENT-MENTION-REPORT.md` | 已读 | @agent / 强制补位补丁 | `user_constraints.mentions` 与 protected speakers 成为可执行契约。 |
| `SESSION-8-P3-LIVE-RERUN-REPORT.md` | 已读 | prompt-level rerun | 明确当时没有可执行 `/room` runtime,不能声称 true live runtime。 |
| `SESSION-8-P3-LIVE-RERUN-FIXTURES.json` | 已解析 | P3 fixture | 三例:无点名强制 Munger、@Jobs protected、@Munger already included。 |
| `SESSION-8-P3-HARNESS-IMPLEMENTATION-REPORT.md` | 已读 | 最小 orchestrator harness | 新增 deterministic rule harness,不是完整 `/room` orchestrator。 |
| `SESSION-8-FLOW-F-RUNTIME-FIXTURE.json` | 已解析 | Flow F runtime substitute | 明确 `runtime_available=false`,只验证 precheck + packet shape。 |
| `SESSION-8-FLOW-F-HARNESS-REPORT.md` | 已读 | Flow F harness | 新增 readiness 和 packet validator。 |
| `SESSION-8-STATE-REDUCER-HARNESS-REPORT.md` | 已读 | state reducer | 维护 conversation_log/silent_rounds/summary/upgrade input,不生成观点。 |
| `SESSION-8-PROMPT-INPUT-BUILDERS-HARNESS-REPORT.md` | 已读 | prompt input builders | 构造 chat/summary input,不调用 LLM。 |
| `SESSION-8-DRY-RUN-FIXTURE.json` | 已解析 | dry-run fixture | synthetic 输出验证状态链路,不是 LLM generation。 |
| `SESSION-8-DRY-RUN-HARNESS-REPORT.md` | 已读 | dry-run harness | 第一条完整 synthetic chain: selection -> chat -> state -> summary -> upgrade。 |
| `SESSION-9-HARNESS-VALIDATORS-PACKET-BUILDER-REPORT.md` | 已读 | validators + packet builder | 增加 chat/summary validators 与 deterministic handoff packet builder。 |
| `SESSION-10-ROOM-UPGRADE-CONTRACT-CHECKLIST-REPORT.md` | 已读 | upgrade contract checklist | 将 packet builder 与 `room-upgrade.md` 字段级对齐。 |
| `SESSION-11-ROOM-CHAT-PROMPT-CALL-ADAPTER-REPORT.md` | 已读 | room-chat adapter | 新增可注入 executor 边界,不绑定 provider。 |
| `SESSION-12-ROOM-SUMMARY-PROMPT-CALL-ADAPTER-REPORT.md` | 已读 | room-summary adapter | summary synthetic 可替换为 executor 输出。 |
| `SESSION-13-ROOM-UPGRADE-PROMPT-CALL-ADAPTER-REPORT.md` | 已读 | room-upgrade adapter | 三段 prompt-call adapter 完成,仍未绑定真实 provider。 |
| `SESSION-14-DEVELOPMENT-PROGRESS-AUDIT.md` | 已读 | 进度审查 | 85% 口径是当时 harness milestone,其中 true live rerun 仍 0%。 |
| `SESSION-15-EXTERNAL-EXECUTOR-CONTRACT-REPORT.md` | 已读 | external executor | provider-agnostic 外部命令 contract,用于 wrapper/dry-run。 |
| `SESSION-16-HTTP-PROVIDER-WRAPPER-REPORT.md` | 已读 | HTTP wrapper | 通用 HTTP JSON contract,不是本地 `/room` 主线。 |
| `SESSION-17-CHAT-COMPLETIONS-WRAPPER-REPORT.md` | 已读 | Chat Completions wrapper | 将 prompt request 映射为 chat-completions body。 |
| `SESSION-18-CHAT-COMPLETIONS-CLI-INTEGRATION-REPORT.md` | 已读 | wrapper CLI 集成 | 本地 mock endpoint 四段 prompt-call 通过。 |
| `SESSION-19-PAUSE-HANDOFF-REPORT.md` | 已读 | pause handoff | 明确下一步等待真实 provider,但这是 Session 15-18 adapter 路线下的交接。 |
| `SESSION-20-PROVIDER-CONFIG-PREFLIGHT-REPORT.md` | 已读 | 我写的 provider preflight | 工程上可用,但优先级归类错误,应降为 optional adapter support。 |
| `SESSION-21-ENV-FILE-PROVIDER-CONFIG-REPORT.md` | 已读 | 我写的 env-file support | 同上,属于 optional adapter support。 |
| `SESSION-22-LOCAL-SUBAGENT-DISPATCH-CONTRACT-REPORT.md` | 已读 | 本地 dispatch 契约纠偏 | 与用户指出的 gstack-style 本地 Agent 主线一致,但仍需实现 executable local dispatch。 |

## 4. 真实主线复原

从 2026-04-10 到 2026-04-13 的主线不是“接 API”,而是:

1. Session 1: 定义 `/room` 产品形态,明确 Agent = 本地名人 skill 的房间化实例。
2. Session 2: 建 Agent Registry / selection protocol。
3. Session 4-6: 补 architecture / selection / chat / summary / upgrade / room-skill。
4. Session 7: 用 subagent 做 E2E live-style 验证,暴露 F1-F23。
5. Session 8: 修关键协议 bug,并承认真实 runtime 不存在,于是开始最小 harness。
6. Session 8-10: 将 deterministic rule/state/packet 链路转成可测试 harness。
7. Session 11-13: 建 prompt-call adapter,仍是 executor seam,不是 provider 主线。
8. Session 15-18: 建 external executor / HTTP / Chat Completions wrapper,用于外部执行和本地 mock 测试。
9. Session 20-21: 我延续了 Session 19 的 provider handoff,但忽略了更上层本地 Agent 主线,因此优先级判断错误。
10. Session 22: 将主线纠回本地 gstack-style Agent dispatch contract。

## 5. 对我前两步开发的审查

### Session 20: provider config preflight

结论: 工程上没有破坏测试,但作为 P0 是错误的。

保留价值:

- 可以避免真实 wrapper dry-run 泄露 token 或 endpoint。
- 可作为 CI/harness adapter preflight。

问题:

- 它不解决 `/room` 本地运行。
- 它把用户误导到“需要 API”。
- 它与 `/room` 本地 skill / Agent 编排主线不一致。

归类修正: `Optional Harness Adapter Support`,不是 product runtime P0。

### Session 21: env-file provider config

结论: 同 Session 20。属于外部 provider wrapper 的便利工具,不应阻塞 `/room`。

归类修正: `Optional Harness Adapter Support`,不是 product runtime P0。

### Session 22: local subagent dispatch contract

结论: 方向正确,但还只是文档契约 + 防回归测试,不是完整实现。

价值:

- 明确 `room-chat.md 不替代本地 Agent`。
- 明确 provider/external executor 不作为 `/room` 主线依赖。
- 明确 Codex 类 runtime 不允许并行子 Agent 时必须退化为 `local_sequential`。

剩余:

- 还没有真正把 speaker -> local skill/profile -> speaker task -> Turn assembly 跑起来。

## 6. 当前代码状态核对

已核对当前真实文件:

- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`
- `C:\Users\CLH\prompts\room-chat.md`
- `C:\Users\CLH\prompts\room-summary.md`
- `C:\Users\CLH\prompts\room-upgrade.md`
- `C:\Users\CLH\prompts\room-selection.md`
- `C:\Users\CLH\docs\room-architecture.md`
- `C:\Users\CLH\docs\room-selection-policy.md`
- `C:\Users\CLH\docs\room-to-debate-handoff.md`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\*`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\*`

发现:

1. `room-skill/SKILL.md` 已有“本地 Agent 调用契约（参考 gstack）”。
2. `room-skill-local-dispatch-contract.test.js` 已锁住“不回退到 provider-first”。
3. `room-orchestrator-harness/README.md` 仍写 `Current expected result: 50 pass / 0 fail`,但当前实际为 52 pass。
4. README 仍保留 provider wrapper 命令说明,需要补充“optional adapter, not runtime mainline”口径。
5. harness 还没有 local dispatch runtime 模块。

## 7. 修正后的任务优先级

| 优先级 | 任务 | 状态 | 验收标准 |
|---|---|---|---|
| P0 | 实现 local dispatch resolver | 未开始 | selected speaker 能解析到 agent registry / local skill profile。 |
| P1 | 实现 `local_sequential` speaker execution | 未开始 | 不用 provider API,按 speaker 顺序生成候选发言片段。 |
| P2 | Turn assembly + state reducer 接通 | 部分已有 reducer | 本地 speaker 输出合成 `room_chat` Turn,写入 `conversation_log`。 |
| P3 | 本地 dispatch dry-run e2e | 未开始 | 复用 Session 8 dry-run fixture,但 chat output 来自 local speaker tasks。 |
| P4 | `/summary` 与 `/upgrade-to-debate` 本地链路验证 | 部分已有 harness | summary/update/handoff 在本地模式下通过 validators。 |
| P5 | README / NEXT-STEPS 口径修正 | 未开始 | provider 相关全部标注为 optional adapter。 |
| P6 | 低优先级协议债 F11/F16/F17/F18 + §13.6 | 未开始 | 文档规则清晰度补丁 + tests。 |
| P7 | Phase 6 skill mode 升级 | 未开始 | 13 个旧 skill 从 debate_only 升级为 debate_room。 |
| P8 | Phase 7 自动发现扫描器 | 未开始 | 条件注册 / discovered_but_incomplete 流程可运行。 |

## 8. 下一步开发建议

下一步不要再问用户 provider 信息。

直接开发 P0/P1:

1. 新增 `local-dispatch.js` 或等价模块。
2. 读取 `agent-registry/registry.json`。
3. 解析 selected speakers 的 `id / short_name / skill_path / roundtable-profile`。
4. 构造 per-speaker room task:
   - `room_state`
   - `recent_log`
   - `user_input`
   - `turn_role`
   - `long_role`
   - `structural_role`
   - local profile constraints
5. 先实现 `execution_mode: local_sequential`。
6. 若当前 Codex runtime 不允许实际 `spawn_agent`,则在当前 agent 内按 profile 约束执行 speaker task,并显式写 `warnings: ["local_sequential_fallback"]`。
7. 用测试锁住:
   - 不读取 provider env。
   - 缺 API key 不阻塞。
   - selected speakers 全部被执行。
   - speaker task 不能直接写 room_state。
   - Turn assembly 只由 orchestrator 写入。

## 9. 禁止继续偏离的约束

1. 不再把 provider config 当 P0。
2. 不要求用户提供 API key 才能继续 `/room` 开发。
3. 不把 `room-chat.md` 当成唯一智能源。
4. 不把 `/room` 改成新的名人人格系统。
5. 不进入 UI / 持久化 / 自动发现扫描器,直到本地 dispatch 主线跑通。
6. 不修改 `/debate` 既有边界。

## 10. 当前审查结论

我已完成 `D:\圆桌会议` 全量文件读档和当前实现核对。接力开发应从本地 Agent 调度层继续,而不是 provider API。

下一步应执行:

```text
P0: implement executable local_sequential /room speaker dispatch
```

provider wrapper 与 env-file 支持保留为可选 harness 能力,但不进入主线优先级。
