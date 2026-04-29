# /room Current Implementation Boundary

This reference holds long-form implementation status that used to live in
`SKILL.md`. The skill entrypoint keeps only trigger, source, and execution
rules.

## Claimable Local-First Source

- `/room` protocol, workflow, prompts, schemas, and checked-in runtime bridge are
  source-controlled.
- `room_runtime.py`, `room_e2e_validation.py`, `local_codex_executor.py`,
  `local_codex_regression.py`, and related validation scripts remain the
  canonical checked-in runtime entrypoints.
- `generic_agent_executor.py`, `generic_fixture_agent.py`,
  `generic_agent_adapter_validation.py`, and `generic_agent_json_wrapper.py`
  define the fixture-backed generic local agent adapter contract.
- `agent_host_inventory.py`, `local_agent_host_validation_matrix.py`, and
  `live_lane_evidence_report.py` classify host-live lanes without claiming
  unvalidated hosts.
- `chat_completions_readiness.py`, `chat_completions_regression.py`, and
  `chat_completions_live_validation.py` define the provider fallback lane.

## Boundary

- Fixture, mock-provider, wrapper, inventory, and config-readiness passes are
  not host-live or provider-live support.
- Provider fallback remains optional and is not required for the local mainline.
- Historical `reports/` and generated `artifacts/` are evidence, not current
  implementation source.
