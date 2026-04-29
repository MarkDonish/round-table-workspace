# Agent Registry

> Purpose: provide a checked-in, portable registry view for `/room` and `/debate` runtime selection.
> Last reviewed: 2026-04-21

---

## Role

This document is the normalized runtime-facing registry for the current roundtable agent pool.

It does not replace detailed persona files. Instead:

- `.codex/skills/*/roundtable-profile.md` remains the detailed per-agent profile source
- `prompts/room-selection.md` remains the executable selection contract
- this document provides a stable registry view that is safe for orchestrator-level logic

If there is a conflict on selection-critical fields such as `task_types`, `stage_fit`, `structural_role`, or `default_excluded`, this document and `prompts/room-selection.md` should be kept in sync together.

---

## Registry Fields

Each registry entry should expose these portable fields:

- `agent_id`: stable machine-readable id
- `display_name`: lens-oriented user-facing label, such as `Taleb lens`
- `short_name`: user-facing short label
- `cognitive_lens`: the mental model or review angle being applied
- `useful_when`: task situations where the lens is useful
- `avoid`: imitation, unsupported biographical claims, or style risks to avoid
- `style_rule`: plain rule that the system uses the lens without imitating voice
- `structural_role`: `offensive | defensive | moderate`
- `expression`: `grounded | abstract | dramatic`
- `strength`: `dominant | moderate`
- `default_excluded`: whether the agent is excluded unless explicitly requested
- `task_types`: the task families the agent can cover
- `stage_fit`: discussion stages where the agent is naturally useful
- `sub_problem_tags`: normalized tags for selection and complement logic

---

## Current Registry

| agent_id | short_name | structural_role | expression | strength | default_excluded | task_types | stage_fit | sub_problem_tags |
|---|---|---|---|---|---|---|---|---|
| `steve-jobs` | `Jobs` | `offensive` | `grounded` | `dominant` | `no` | `product, startup, strategy` | `simulate, converge, decision` | `value_proposition, product_focus, user_experience, first_principles, narrative_construction` |
| `elon-musk` | `Musk` | `offensive` | `grounded` | `dominant` | `no` | `product, strategy, planning` | `simulate, converge, decision` | `first_principles, execution_path, resource_allocation, technical_feasibility, product_focus` |
| `munger` | `Munger` | `defensive` | `grounded` | `moderate` | `no` | `risk, strategy, planning` | `stress_test, converge, decision` | `downside_analysis, resource_allocation, first_principles, long_term_strategy, team_dynamics` |
| `feynman` | `Feynman` | `defensive` | `grounded` | `moderate` | `no` | `learning, writing, product` | `explore, simulate` | `first_principles, learning_explanation, technical_feasibility, user_experience` |
| `naval` | `Naval` | `offensive` | `abstract` | `moderate` | `no` | `planning, strategy, learning` | `explore, simulate, converge` | `long_term_strategy, resource_allocation, first_principles, team_dynamics` |
| `taleb` | `Taleb` | `defensive` | `abstract` | `dominant` | `no` | `risk, strategy, planning` | `stress_test, simulate, converge` | `tail_risk, downside_analysis, resource_allocation, long_term_strategy, regulatory_risk` |
| `zhangxuefeng` | `Zhang Xuefeng` | `defensive` | `grounded` | `moderate` | `no` | `planning, learning, strategy` | `converge, decision, stress_test` | `execution_path, resource_allocation, team_dynamics, regulatory_risk, downside_analysis` |
| `paul-graham` | `PG` | `offensive` | `abstract` | `moderate` | `no` | `startup, strategy, writing` | `explore, simulate, decision` | `value_proposition, market_timing, market_sizing, product_focus, first_principles` |
| `zhang-yiming` | `Zhang Yiming` | `offensive` | `grounded` | `moderate` | `no` | `product, strategy, content` | `simulate, converge, decision` | `growth_strategy, distribution, product_focus, first_principles, execution_path` |
| `karpathy` | `Karpathy` | `moderate` | `grounded` | `moderate` | `no` | `learning, product, planning` | `explore, simulate, converge` | `technical_feasibility, execution_path, learning_explanation, first_principles` |
| `ilya-sutskever` | `Ilya` | `offensive` | `abstract` | `moderate` | `no` | `learning, strategy, risk` | `explore, simulate` | `long_term_strategy, first_principles, technical_feasibility, market_timing` |
| `mrbeast` | `MrBeast` | `offensive` | `grounded` | `dominant` | `no` | `content, product, writing` | `explore, simulate, decision` | `distribution, narrative_construction, user_experience, growth_strategy` |
| `trump` | `Trump` | `offensive` | `grounded` | `dominant` | `yes` | `content, strategy` | `converge, decision` | `narrative_construction, distribution, team_dynamics` |
| `justin-sun` | `Sun` | `offensive` | `dramatic` | `dominant` | `no` | `strategy, startup, content` | `explore, simulate, decision` | `market_sizing, competitive_structure, market_timing, narrative_construction, resource_allocation, monetization` |

## Cognitive Lens Overlay

The runtime treats people-like labels as shorthand for cognitive lenses, not as
permission to imitate a living or historical person's private views or voice.
Users may still write `--with Jobs,Taleb`, but the internal mapping is
`Jobs lens` and `Taleb lens`.

| agent_id | display_name | cognitive_lens | useful_when | avoid | style_rule |
|---|---|---|---|---|---|
| `steve-jobs` | `Jobs lens` | `product focus, taste, user experience compression` | `product wedge, positioning, experience clarity` | `voice imitation, invented personal opinions, biographical claims` | Use the product judgment lens; do not imitate Steve Jobs' voice. |
| `taleb` | `Taleb lens` | `tail risk, fragility, skin in the game` | `downside risk, fragile assumptions, asymmetric payoff` | `voice imitation, insult style, unverified claims about Taleb` | Use the risk lens; do not imitate Nassim Taleb's voice. |
| `munger` | `Munger lens` | `incentives, inversion, downside control` | `kill rules, decision filters, risk review` | `voice imitation, quotes presented as fact without source` | Use the mental-model lens; do not imitate Charlie Munger's voice. |
| `karpathy` | `Karpathy lens` | `technical feasibility, learning loops, system simplicity` | `AI product loop, implementation thin slice, education workflow` | `voice imitation, claiming private views` | Use the technical-learning lens; do not imitate Andrej Karpathy's voice. |

---

## Runtime Rules

The registry is subject to these hard rules:

1. Not every registered agent should enter a room or debate.
2. Selection must still be topic-driven, stage-driven, and structure-balanced.
3. `default_excluded: yes` means the agent should not join unless explicitly requested or strongly justified by source rules.
4. Runtime logic must not depend on machine-local absolute paths.
5. New agents should not be treated as registered until their profile metadata and selection fields are both checked in.

---

## Change Rules

When adding or updating an agent, do not update only one layer.

The expected sync set is:

1. the agent's `roundtable-profile.md`
2. this registry document
3. `prompts/room-selection.md`
4. any runtime bridge that consumes the registry

This is how we keep `/room` and `/debate` selection behavior portable across machines.
