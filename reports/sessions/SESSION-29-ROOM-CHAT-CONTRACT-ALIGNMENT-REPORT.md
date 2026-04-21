# SESSION 29 - room-chat contract alignment report (F16/F18)

日期: 2026-04-17
工作区: C:\Users\CLH\tools\room-orchestrator-harness

## 本轮目标

处理下一优先级协议债中的第一批低风险 contract 问题:

- F16: `cited_agents` 在多 speaker 场景下的语义歧义
- F18: 2/3/4 speaker 角色分配分支在 `room-chat.md` 中不显式

同时把 harness runtime 的角色分配与 `docs/room-architecture.md §7.2` 对齐,避免文档和运行时分叉。

## 已完成

### 1. room runtime 角色分配改为 architecture 对齐

修改文件:
- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-runtime.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-runtime.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\selection-runtime.test.js`

结果:
- 2 人: `primary + challenge`(若结构相反) / 否则 `primary + support`
- 3 人: `primary + challenge + synthesizer`(若存在结构相反者) / 否则 `primary + support + synthesizer`
- 4 人: `primary`, opposite-highest `challenge`, 剩余高分 `support`,低分 `synthesizer`
- 输出顺序按 role 排序,不再用固定 index 套位

### 2. local dispatch 增加 self-citation 归一化

修改文件:
- `C:\Users\CLH\tools\room-orchestrator-harness\src\local-dispatch.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\local-dispatch.test.js`

结果:
- 每个 speaker 的 `cited_agents` 在聚合前先去重
- 自动剔除“自己引用自己”的 agent_id
- 保留同轮其他 speaker 与历史 speaker 的合法引用

### 3. room-chat prompt 增加 v0.1.3 contract addendum

修改文件:
- `C:\Users\CLH\prompts\room-chat.md`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-chat-prompt-contract.test.js`

新增明确化内容:
- `cited_agents` 是“逐条 speaker 扫描后 union”,不是模糊的“整个 turn 的单一发言者”视角
- 当前正在说话的 speaker 自己不计入 `cited_agents`
- 同轮其他 speaker 与历史 speaker 可以计入
- 显式写出 `speakers.length == 2 / 3 / 4` 的 sanity-check 分支

### 4. README 同步

修改文件:
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`

同步内容:
- room runtime 已按 architecture §7.2 分配角色
- local dispatch 会剔除 self-citation
- 最新测试基线更新为 75/75

## 验证

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\room-runtime.test.js'
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\local-dispatch.test.js'
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\room-chat-prompt-contract.test.js'
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\selection-runtime.test.js'
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'
```

结果:

```text
tests 75
pass 75
fail 0
```

## 结论

P6 低优先级协议债已开始收口,但当前只完成第一批(F16/F18 + runtime 对齐)。

剩余下一优先级建议:
1. F17: 明确 primary 在 user 追问时可以回应上轮 challenge,但仍以主张为核心
2. F11: synthesizer 180 字瓶颈,决定是文档放宽还是保持 v0.1 不动并显式记债
3. selection `§13.6` 其余歧义逐项补 contract test
