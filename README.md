# Mark 多 Agent 决策框架

这是一个兼容现有名人 skill 的决策系统仓库，也是当前 round-table 工作区的长期真源。

它现在有 3 层使用方式：

1. 日常模式：按任务类型调用单个或少量 skill
2. `/room` 模式：显式触发的状态化多 Agent 房间，用于探索、推进、总结、升级
3. `/debate` 模式：显式触发的重大议题圆桌审议，用于形成审查后的统一决议

`/room` 和 `/debate` 都不是默认模式。只有在用户明确进入对应上下文时才启用。

---

## 当前状态

项目不是 100% 完成，但核心边界已经非常清楚。

### 已完成的核心能力

- `/debate` 的 skill 架构、角色边界、reviewer 协议、红旗规则、主 prompts 已经落地
- `/debate` 已有 checked-in runtime bridge，可把 handoff packet 串到 launch bundle、roundtable record、review packet、review result、reject-followup-rereview chain
- `/room` 的状态模型、selection / chat / summary / upgrade 协议已经落地
- `/room -> /debate` 的 handoff schema 已经落地
- `docs/agent-registry.md` 已提供 runtime-facing 的 agent registry
- `prompts/room-chat.md` 已重建为可读版本
- `docs/room-runtime-bridge.md` 已把缺失的 runtime bridge 责任边界锁成真源
- `.codex/skills/room-skill/runtime/room_runtime.py` 已把 `/room` 的 host-side bridge 代码正式入仓
- `.codex/skills/room-skill/runtime/local_codex_executor.py` 已提供 checked-in 的本地 child-agent 执行器，直接复用本机 Codex 作为 `/room` 和 `/debate` 的 prompt host
- `.codex/skills/room-skill/runtime/local_codex_executor.py` 现在也已提供 checked-in 的 local host preflight，可先验证 `~/.codex` 宿主写入条件和 nested child-agent smoke
- `.codex/skills/room-skill/runtime/local_codex_regression.py` 已提供 checked-in 的本地主线回归入口，可一条命令跑 host preflight + room + debate + integration；已内建 `gpt54_family` 默认 preset，并会额外产出 `runtime-profile.json`
- `.codex/skills/room-skill/runtime/local_codex_second_host_validation.py` 已提供 checked-in 的第二宿主复验入口，可用独立 `codex exec` 宿主重跑整套本地主线，并把外层宿主证据与 nested runtime profile 一起落盘
- `.codex/skills/room-skill/runtime/local_codex_cross_machine_validation.py` 已提供 checked-in 的跨机器验证 lane，可先准备 manifest/runbook，再校验另一台机器回传的 regression report 与 runtime profile
- `.codex/skills/room-skill/runtime/generic_agent_executor.py` 已提供 host-neutral 的本地 CLI agent adapter，可把同一套 prompt task 对接到 Codex、Claude Code 或其他能从 stdin 接任务并返回 JSON 的本地 agent
- `.codex/skills/room-skill/runtime/generic_fixture_agent.py` 已提供 checked-in 的本地 fixture agent，用于验证 generic CLI / Claude Code adapter 路由而不依赖真实第三方 CLI
- `.codex/skills/room-skill/runtime/generic_agent_adapter_validation.py` 已提供 generic local agent adapter 的一键验证入口，可用默认 fixture 或真实 agent command 跑 smoke + `/room -> /debate`
- `.codex/skills/room-skill/runtime/generic_agent_json_wrapper.py` 已提供第三方本地 agent JSON 清洗 wrapper，可把 Markdown fence、stdout 日志或 noisy file output 归一成单个 JSON 对象
- `.codex/skills/room-skill/runtime/generic_agent_json_wrapper_validation.py` 已提供 wrapper 离线验证入口，覆盖 markdown / stdout noise / output file 三类常见脏输出
- `.codex/skills/room-skill/runtime/agent_host_inventory.py` 已提供真实本地 agent 宿主 inventory/preflight，可区分 CLI 缺失、auth 阻塞、可进入 live validation
- `.codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py` 已提供真实本地 agent 宿主 validation matrix/report，可把 missing / blocked / pending / live passed / live failed 分级落盘
- `.codex/skills/room-skill/runtime/agent_consumer_self_check.py` 已提供 clone-friendly 的消费者自检入口，可在不需要 provider URL、不需要第三方付费账号的前提下聚合 source-boundary、release readiness、Claude project skill、generic adapter fixture、JSON wrapper、host matrix 证据
- `.codex/skills/room-skill/runtime/claude_code_live_validation.py` 已提供 checked-in 的真实 Claude Code 本地 CLI validation wrapper；它把 `preflight_only`、`smoke_only`、完整 `/room -> /debate` 分层落盘，只有 `claimable_as_default_claude_code_host_live=true` 才能声明默认 Claude Code host-live 通过
- `.codex/skills/room-skill/runtime/release_candidate_report.py` 已提供 release candidate 总报告入口，可把 release gate、host matrix、provider readiness 汇总成 claim-safe JSON/Markdown
- `.claude/skills/room/SKILL.md` 和 `.claude/skills/debate/SKILL.md` 已提供 Claude Code 原生项目 skill 入口，指回当前真源而不是复制出第二套协议
- `.claude/scripts/validate_project_skills.py` 已提供不依赖 Claude 账号的 Claude Code project skill 结构验证入口
- `.codex/skills/room-skill/runtime/chat_completions_regression.py` 已提供 checked-in 的 provider fallback 回归入口，可自动拉起本地 room/debate mock provider，并一条命令跑 provider preflight + room + debate + integration
- `.codex/skills/room-skill/runtime/chat_completions_readiness.py` 已提供 checked-in 的 provider live readiness 入口，可在不请求真实 endpoint 的前提下区分 env missing / placeholder / ready
- `.codex/skills/room-skill/runtime/chat_completions_live_validation.py` 已提供 checked-in 的真实 provider live wrapper，可先做 room/debate 双侧 preflight，再一键触发真实 `/room -> /debate` integration
- `.codex/skills/room-skill/runtime/release_readiness_check.py` 已提供 checked-in 的 release readiness gate，可把 Codex 本地主线上线范围、P0 阻塞和非阻塞 live 缺口分开报告
- `.codex/skills/room-skill/runtime/room_e2e_validation.py` 已提供 checked-in 的 `/room -> /summary -> /upgrade-to-debate` 验证入口
- `.codex/skills/room-skill/runtime/room_debate_e2e_validation.py` 已提供 checked-in 的 `/room -> /debate` 联调验证入口
- `.codex/skills/room-skill/runtime/mock_chat_completions_server.py` 已提供本地 Chat Completions-compatible mock provider，用于验证 provider-backed 链路
- `.codex/skills/debate-roundtable-skill/runtime/debate_packet_validator.py` 已提供 checked-in 的 `/debate` handoff packet 可执行预检
- `.codex/skills/debate-roundtable-skill/runtime/debate_runtime.py` 已提供 checked-in 的 `/debate` execution bridge，包括 reject -> followup -> re-review validation chain
- `.codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py` 已提供 checked-in 的 `/debate` prompt-host E2E 验证入口，并可直接消费真实 `/room` handoff packet
- `.codex/skills/debate-roundtable-skill/runtime/mock_chat_completions_server.py` 已提供本地 Chat Completions-compatible mock provider，用于验证 `/debate` provider-backed 链路
- `.codex/skills/debate-roundtable-skill/runtime/fixtures/canonical/` 已提供 checked-in 的 debate execution fixtures
- `.codex/skills/room-skill/runtime/fixtures/canonical/` 已提供 checked-in 的首轮验证 fixture
- `/room local_codex` 已在 Mac 上通过 checked-in E2E 验证
- `/debate local_codex` 的 `allow` 与 `reject_followup` 两条链都已在 Mac 上通过 checked-in E2E 验证
- `/room -> /debate local_codex` 已在 Mac 上通过一条完整联调验证，真实消费 `/room` 持久化 handoff packet
- `/room -> /debate generic_cli` 已通过 checked-in fixture agent 跑通完整 adapter integration
- generic local agent adapter kit 已收口成 checked-in 文档和一键验证命令，其他本地 agent 可按同一 stdin / JSON contract 接入
- local agent host inventory 已可输出本机真实宿主 readiness，不会把 auth blocked 或 CLI missing 误报成 live pass
- agent consumer self-check 已可给 Codex、Claude Code 和其他本地 agent 用户生成一份 clone 后可读的 PASS/FAIL 与 next commands 报告
- provider fallback regression 已复跑通过；provider readiness 会把当前真实 `.env.room` / `.env.debate` 的缺失配置报告为 blocked，不误报为 live pass
- release readiness gate 已入仓；上线判断不再只依赖口头汇报或历史 reports
- release candidate scope 和总报告生成器已入仓；当前可声明范围与不可声明范围可以一键生成审查材料
- `/room -> /debate claude_code` 已通过 checked-in fixture agent 跑通 executor route；默认 Claude Code CLI wrapper 也已在本机 Mac 上通过真实 full integration live validation
- Claude Code project skill 包装层已通过 checked-in 结构验证；这证明 Claude Code 用户 clone 仓库后有标准 `.claude/skills/` 入口
- 真实 Claude Code CLI validation 已在本机 Mac 上完成 `preflight_only`、`smoke_only`、完整 `/room -> /debate` 三层验证；full wrapper 返回 `claimable_as_default_claude_code_host_live=true`
- 当前最稳定的 checked-in 本地主线配置已收敛到 `gpt54_family`：`gpt-5.4` 为主模型、`gpt-5.4-mini` 为同家族 fallback，并显式固定 child-task reasoning / timeout；现在还会按 prompt 分层执行，例如 selection 用更短 timeout，chat / roundtable / followup 留更长窗口，summary / upgrade / reviewer 会切到更轻的同家族 lane
- 同一台 Mac 上，除了当前桌面线程，这条本地主线也已通过独立 shell-level `codex exec` 第二宿主复验；当前剩下的不是“第二入口能不能跑”，而是“跨机器是否仍然稳定”
- 本仓库现在已经把“跨机器验证”本身固化成 checked-in 流程：source 机先生成 manifest/runbook，target 机跑本地主线并回传 evidence，source 机再做 schema/commit/config 校验；Windows 本地主线与增强验证证据已落到 `reports/WINDOWS_LOCAL_MAINLINE_VALIDATION.md` 和 `reports/WINDOWS_ENHANCED_VALIDATION.md`

### 还没完成的核心能力

- `local_codex` 主链已经在 Mac 上打通，checked-in child-task 执行器现在既可单独调参，也可直接复用 `gpt54_family` preset，避免直接继承宿主全局 `xhigh`；未单独证明的是“完全不加 child-task 调优，直接裸继承宿主默认配置”这一条非目标路径
- `/room` 与 `/debate` 的 Chat Completions-compatible provider 路径仍然保留，但现在应视为 fallback / regression lane，而不是主线
- 还没有完成真实外部 provider 的 `/room -> /summary -> /upgrade-to-debate -> /debate` live run
- provider live readiness 已有 checked-in config-only preflight，但当前真实 `.env.room` / `.env.debate` 仍未 ready
- 当前已完成的是 fixture-driven 验证、mock provider-backed 验证、以及本地 child-agent 主链验证；仍不应误报成所有宿主配置都已 100% 实战验证
- generic CLI adapter 已证明 host abstraction 可以跑完整 `/room -> /debate` 链路；默认 Claude Code wrapper 已在本机 Mac 上 live-validated，其他第三方本地 agent 仍需要各自 live validation
- generic local agent adapter kit 已提供通用接入合同和验证 wrapper；真实第三方 agent 的稳定性仍取决于各自 CLI 是否遵守 stdout / output-file JSON contract
- Claude Code project skill 入口已入仓并可离线验证；真实 Claude Code live support 仍按机器/账号逐次验证，不从本机 Mac 结果外推到所有用户

简化结论：

- `/room`：协议完成、runtime implementation 已入仓，且本地 child-agent 主链已验证；外部 provider live run 仍未完成
- `/debate`：checked-in bridge 完成，本地 child-agent 主链已验证；外部 live host 仍未完成

---

## Source Of Truth

这个仓库里真正应当长期维护的真源目录是：

- `README.md`
- `LAUNCH.md`
- `AGENTS.md`
- `docs/`
- `prompts/`
- `examples/`
- `.codex/skills/debate-roundtable-skill/`
- `.codex/skills/room-skill/`
- `.codex/skills/*/roundtable-profile.md`
- `.claude/skills/`（仅作为 Claude Code project skill 适配层，不是第二套协议实现源）

以下目录不是当前实现真源：

- `reports/`
- `artifacts/`

其中：

- `reports/` 保存开发历史、handoff、validation、session 报告
- `artifacts/` 保存运行产物、fixture、导出文件

---

## 仓库结构

```text
round-table-workspace/
├─ README.md
├─ LAUNCH.md
├─ AGENTS.md
├─ .gitignore
├─ docs/
│  ├─ router.md
│  ├─ debate-skill-architecture.md
│  ├─ agent-role-map.md
│  ├─ reviewer-protocol.md
│  ├─ red-flags.md
│  ├─ room-architecture.md
│  ├─ room-selection-policy.md
│  ├─ room-to-debate-handoff.md
│  ├─ room-chat-contract.md
│  ├─ room-runtime-bridge.md
│  ├─ room-runtime-status.md
│  ├─ host-adapter-architecture.md
│  ├─ generic-local-agent-adapter.md
│  ├─ local-agent-host-recipes.md
│  ├─ third-party-agent-wrapper-recipes.md
│  ├─ provider-live-readiness.md
│  ├─ release-readiness.md
│  ├─ release-candidate-scope.md
│  ├─ releases/v0.1.0-rc4.md
│  ├─ claude-code-skill-adapter.md
│  └─ superpowers/specs/
├─ prompts/
│  ├─ debate-roundtable.md
│  ├─ debate-reviewer.md
│  ├─ debate-followup.md
│  └─ room-*.md
├─ examples/
│  ├─ debate-examples.md
│  └─ room-examples.md
├─ .codex/skills/
│  ├─ debate-roundtable-skill/SKILL.md
│  ├─ room-skill/SKILL.md
│  └─ */roundtable-profile.md
├─ .claude/
│  ├─ README.md
│  ├─ skills/room/SKILL.md
│  ├─ skills/debate/SKILL.md
│  └─ scripts/validate_project_skills.py
├─ reports/
│  ├─ checkpoints/
│  ├─ sessions/
│  └─ setup/
└─ artifacts/
   ├─ runtime/
   ├─ fixtures/
   └─ rendered/
```

---

## 如何使用

### 日常模式

直接用原有 skill：

- `用 steve-jobs-skill 判断这个功能该不该做`
- `用 feynman-skill 讲明白 attention`
- `用 taleb-skill 审查这个方案风险`

### `/room` 模式

适合需要连续推进、保留状态、阶段总结、必要时升级成正式审议的场景。

示例：

- `/room 我想讨论一个面向大学生的 AI 学习产品，从方向、切口、风险一步步推进`
- `/focus 先只盯“最小可验证切口”`
- `/summary`
- `/upgrade-to-debate`

### `/debate` 模式

适合重大判断、需要明确分工和审查放行的场景。

示例：

- `/debate 这个创业方向值不值得做`
- `/debate 我是否应该给产品加这个功能`
- `/debate --with Jobs,Taleb 这个方向值不值得做`
- `/debate --without Trump 这个方案怎么定`
- `/debate --quick 我该不该先做这个 MVP`

系统会自动按任务类型路由到合适的 Agent 组合。

---

## 关键入口

### 通用入口

- 最短启动入口：`LAUNCH.md`
- 项目规则：`AGENTS.md`
- 真源边界图：`docs/source-truth-map.md`
- 快速路由：`docs/router.md`
- 开发同步协议：`docs/development-sync-protocol.md`
- 发布 readiness：`docs/release-readiness.md`
- 发布 readiness 检查：`python3 .codex/skills/room-skill/runtime/release_readiness_check.py`
- release candidate scope：`docs/release-candidate-scope.md`
- release candidate 总报告：`python3 .codex/skills/room-skill/runtime/release_candidate_report.py`
- agent continuity checkpoints：`docs/agent-continuity-checkpoints.md`
- development checkpoint writer：`python3 .codex/skills/room-skill/runtime/development_checkpoint.py`
- 历史材料边界审计：`docs/historical-materials-audit.md`
- source boundary audit：`python3 .codex/skills/room-skill/runtime/source_boundary_audit.py`
- changelog：`CHANGELOG.md`
- 当前 release candidate notes：`docs/releases/v0.1.0-rc4.md`
- 本地 Superpowers 集成：`docs/superpowers/local-development-integration.md`
- generic local agent 适配：`docs/generic-local-agent-adapter.md`
- agent consumer quickstart：`docs/agent-consumer-quickstart.md`
- agent consumer self-check：`python3 .codex/skills/room-skill/runtime/agent_consumer_self_check.py`
- generic local agent adapter 验证：`python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py`
- third-party agent wrapper recipes：`docs/third-party-agent-wrapper-recipes.md`
- generic agent JSON wrapper 验证：`python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper_validation.py`
- local agent host recipes：`docs/local-agent-host-recipes.md`
- local agent host inventory：`python3 .codex/skills/room-skill/runtime/agent_host_inventory.py`
- local agent host validation matrix：`python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py`
- provider live readiness：`docs/provider-live-readiness.md`
- provider readiness check：`python3 .codex/skills/room-skill/runtime/chat_completions_readiness.py`
- Claude Code skill 适配：`docs/claude-code-skill-adapter.md`
- Claude Code project skill 结构验证：`python3 .claude/scripts/validate_project_skills.py`

### `/room`

- skill：`.codex/skills/room-skill/SKILL.md`
- Claude Code project skill：`.claude/skills/room/SKILL.md`
- 架构：`docs/room-architecture.md`
- selection：`docs/room-selection-policy.md`
- handoff：`docs/room-to-debate-handoff.md`
- chat contract：`docs/room-chat-contract.md`
- bridge contract：`docs/room-runtime-bridge.md`
- host adapters：`docs/host-adapter-architecture.md`
- generic local agent adapter：`docs/generic-local-agent-adapter.md`
- local agent host recipes：`docs/local-agent-host-recipes.md`
- 当前边界：`docs/room-runtime-status.md`
- runtime bridge：`.codex/skills/room-skill/runtime/README.md`
- generic local agent adapter：`.codex/skills/room-skill/runtime/generic_agent_executor.py`
- generic local agent adapter validation：`.codex/skills/room-skill/runtime/generic_agent_adapter_validation.py`
- generic agent JSON wrapper：`.codex/skills/room-skill/runtime/generic_agent_json_wrapper.py`
- generic agent JSON wrapper validation：`.codex/skills/room-skill/runtime/generic_agent_json_wrapper_validation.py`
- local agent host inventory：`.codex/skills/room-skill/runtime/agent_host_inventory.py`
- local agent host validation matrix：`.codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py`
- generic fixture agent：`.codex/skills/room-skill/runtime/generic_fixture_agent.py`
- Claude Code live validation：`.codex/skills/room-skill/runtime/claude_code_live_validation.py`
- local child-agent executor：`.codex/skills/room-skill/runtime/local_codex_executor.py`
- local mainline regression：`.codex/skills/room-skill/runtime/local_codex_regression.py`
- local second-host validation：`.codex/skills/room-skill/runtime/local_codex_second_host_validation.py`
- local cross-machine validation：`.codex/skills/room-skill/runtime/local_codex_cross_machine_validation.py`
- local host preflight：`python3 .codex/skills/room-skill/runtime/local_codex_executor.py --check-host-preflight --preset gpt54_family`
- provider fallback regression：`.codex/skills/room-skill/runtime/chat_completions_regression.py`
- provider live readiness：`.codex/skills/room-skill/runtime/chat_completions_readiness.py`
- provider live validation：`.codex/skills/room-skill/runtime/chat_completions_live_validation.py`
- release candidate 总报告：`.codex/skills/room-skill/runtime/release_candidate_report.py`
- runtime validation：`.codex/skills/room-skill/runtime/room_e2e_validation.py`
- mock provider：`.codex/skills/room-skill/runtime/mock_chat_completions_server.py`
- live provider sample：`.env.room.example`
- examples：`examples/room-examples.md`

### `/debate`

- skill：`.codex/skills/debate-roundtable-skill/SKILL.md`
- Claude Code project skill：`.claude/skills/debate/SKILL.md`
- bridge contract：`docs/debate-runtime-bridge.md`
- runtime validation：`docs/debate-e2e-validation.md`
- runtime bridge：`.codex/skills/debate-roundtable-skill/runtime/README.md`
- runtime implementation：`.codex/skills/debate-roundtable-skill/runtime/debate_runtime.py`
- runtime E2E runner：`.codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py`
- mock provider：`.codex/skills/debate-roundtable-skill/runtime/mock_chat_completions_server.py`
- live provider sample：`.env.debate.example`
- 架构：`docs/debate-skill-architecture.md`
- 角色边界：`docs/agent-role-map.md`
- 审查协议：`docs/reviewer-protocol.md`
- 红旗：`docs/red-flags.md`
- examples：`examples/debate-examples.md`
