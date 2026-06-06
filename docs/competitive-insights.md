# Competitive Insights

This note records the benchmark scan used to sharpen Round Table Workspace's public positioning. It is intentionally source-attributed and principle-level only: No source code was copied, vendored, translated, or structurally reproduced from the benchmark repositories.

## Benchmark set

| Repository | Public positioning observed | What it teaches at the product level |
| --- | --- | --- |
| `addyosmani/agent-skills` | Production-grade engineering skills for AI coding agents; lifecycle commands such as spec, plan, build, test, review, ship. | Make the workflow legible as a small number of named user journeys, not as a bag of prompts. |
| `FoundationAgents/MetaGPT` | Multi-agent software-company metaphor; roles, SOPs, and documents generated from one requirement. | Explain why multiple roles exist and what artifact each role contributes. |
| `camel-ai/camel` | Research-oriented multi-agent societies, tasks, simulated environments, and scaling-law framing. | Make the difference between reusable protocol, experiments, and demos explicit. |
| `pydantic/pydantic-ai` | Production-grade agent framework with type safety, evals, observability, model/provider flexibility, and durable execution. | Serious agent tools win reviewer trust by naming validation, observability, and boundaries. |
| `plandex-ai/plandex` | AI coding agent for large tasks and real-world projects, with install path, docs, examples, and self-hosting path. | Reviewers need a fast path from landing page to install, demo, and verification evidence. |

## What we learned without copying code

1. Lead with a sentence a reviewer can repeat. Round Table Workspace uses: “Make your AI agents argue before they ship.”
2. Package the lifecycle. The public surface should show `/room` for exploration, `/debate` for deeper review, and `ship-check` for the final ship / revise / reject gate.
3. Treat evidence as a product feature. The repository should point to commands, tests, schemas, release notes, demo pages, and claim boundaries.
4. Keep the install / verification path short. A reviewer should be able to clone, run `./rtw doctor --quick`, run `./rtw launch-kit --json`, and run the unit suite.
5. State what is not claimed. The current public surface is fixture-backed and local-first; provider-live or host-live support should only be claimed when separate evidence exists.

## Differentiation for Round Table Workspace

Round Table Workspace is not trying to be a full agent runtime, model provider SDK, or cloned skill marketplace. Its narrower position is a decision layer for AI coding agents:

- Before building: convert vague work into structured exploration.
- Before merging: force competing perspectives into a visible decision record.
- Before public claims: preserve claim boundaries and evidence trails.
- Before applying for credits: give reviewers copy-ready answers, a public demo, and reproducible local checks.

That makes the project credible for credit / grant review without pretending that fixture-backed workflows are already host-live or provider-live automation.

## Near-term optimization backlog

- Add small transcript examples that show the difference between a single-agent answer and a round-table decision.
- Keep adding reviewer-facing assets to `./rtw launch-kit --json` so external reviewers do not need to hunt through the repo.
- Add provider-live evaluation lanes only after the fixture-backed local suite remains stable.
- Maintain an explicit benchmark note so future improvements are inspired by market patterns, not copied from competitor implementations.
