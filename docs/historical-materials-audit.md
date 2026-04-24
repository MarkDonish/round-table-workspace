# Historical Materials Audit

本页说明如何审计 `reports/` 和 `artifacts/`，防止后续 agent 把历史记录或运行产物误当成当前实现真源。

## 审计命令

```bash
python3 .codex/skills/room-skill/runtime/source_boundary_audit.py --output-json /tmp/round-table-source-boundary-audit.json
```

这个命令只读取仓库文件并输出 JSON，不移动、不删除、不重写任何历史材料。

## 审计范围

当前真源和 active support layer：

- `AGENTS.md`
- `README.md`
- `CHANGELOG.md`
- `docs/`
- `prompts/`
- `examples/`
- `.codex/skills/`
- `.claude/skills/`
- `.claude/scripts/`
- `.env.room.example`
- `.env.debate.example`

边界说明文件：

- `reports/README.md`
- `artifacts/README.md`

历史和产物层：

- `reports/`
- `artifacts/`

## 结果解释

`basename_collisions` 表示历史目录中存在和当前真源同名的文件。例如 `HANDOFF.md`、`NEXT-STEPS.md`、`DECISIONS-LOCKED.md` 这类名称可能同时出现在 `docs/` 和 `reports/checkpoints/`。

这不是错误，也不要求删除历史文件。正确解释是：

- 当前实现、协议、prompt、release claim 必须从 active source 读取。
- `reports/` 只用于历史考古、验证证据和旧决策背景。
- `artifacts/` 只用于运行证据、fixture、rendered export。
- 如果历史材料里有仍然有效的规则，应先提升到 `docs/`、`prompts/`、`examples/` 或 `.codex/skills/`，再引用 active source。

## 上线判断

这个审计不是 release gate 的替代品。上线判断仍以以下入口为准：

```bash
python3 .codex/skills/room-skill/runtime/release_readiness_check.py --include-fixture-runs
```

`source_boundary_audit.py` 的作用是降低误读风险。只要 required source roots 存在，同名历史文件本身不阻塞 local-first release。
