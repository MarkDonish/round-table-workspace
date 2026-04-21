# AGENTS.md

Codex global entrypoint for `C:\Users\CLH`. Keep this file short; load detailed rules only when the task actually needs them.

## Always-On Rules

1. Do not fabricate missing facts. If information is insufficient, say `信息缺失`.
2. Keep outputs practical, clear, and structured. Avoid slogans, fluff, and unsupported certainty.
3. For multi-perspective or multi-agent work, distinguish facts, inferences, uncertainties, and recommendations.
4. Do not enter roundtable mode unless the user explicitly starts the message with `/debate`.

## Knowledge Processing

When processing articles or knowledge-base material, preserve the original text exactly. Do not rewrite, delete, or insert comments into the original text.

When working under `D:\vibe coding\`, load the project rules on demand:

- `D:\vibe coding\AGENTS.md`
- `D:\vibe coding\knowledge-processor\rules\`
- `D:\vibe coding\knowledge-processor\templates\`

Knowledge-base outputs should be saved to:

`D:\知识库\{公众号名称}\{序号}_{文章标题}.md`

Use the detailed knowledge-base template from the project rules when needed.

## gstack

Use installed gstack skills only when the user explicitly asks for gstack or the task clearly matches a gstack workflow such as review, investigate, QA, ship, browser testing, freeze/guard, or design review.

If gstack skills fail to load, run:

`cd ~/.codex/skills/gstack && ./setup --host codex`

## dontbesilent

`/dbs` is the explicit router command in hosts that forward slash-prefixed text to the model.
In Codex CLI interactive mode, `/...` is typically reserved for built-in slash commands, so `dbs` must also be invokable via `$dbs` or explicit natural-language requests such as `use dbs` / `用 dbs`.

When a user message starts with `/dbs` or `$dbs`, or explicitly asks to route through `dbs`, always load and use:

- Skill: `C:\Users\CLH\.codex\skills\dbs\SKILL.md`

Treat `/dbs` and `$dbs` as routing entrypoints, not ordinary text. Do not bypass them by answering directly or by jumping straight to another skill before the router runs.
Do not rely on `Trigger:` metadata inside the skill file alone. The top-level routing rule in this `AGENTS.md` is the authoritative entrypoint behavior for `/dbs`, `$dbs`, and explicit `use dbs` requests.

## Debate Roundtable

`/debate` is an explicit-only roundtable dispatcher. It is not the default mode.

On `/debate`, use:

- Skill: `C:\Users\CLH\.codex\skills\debate-roundtable-skill\SKILL.md`
- Full archived spec: `C:\Users\CLH\AGENTS.full-20260411-142320.md`
- Supporting docs, if present:
  - `C:\Users\CLH\docs\debate-skill-architecture.md`
  - `C:\Users\CLH\docs\agent-role-map.md`
  - `C:\Users\CLH\docs\reviewer-protocol.md`
  - `C:\Users\CLH\docs\red-flags.md`
  - `C:\Users\CLH\prompts\debate-roundtable.md`
  - `C:\Users\CLH\prompts\debate-reviewer.md`
  - `C:\Users\CLH\prompts\debate-followup.md`

Default daily mode: route to 1-3 relevant skills only when their trigger conditions are met. Do not auto-run a roundtable.
