# Room Provider Command-Flow Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote provider-backed execution from dry-run pressure verification into the `/room` command-flow runtime mainline without regressing the existing local path.

**Architecture:** Add a provider-aware command-flow execution layer that can run room turns, `/summary`, and `/upgrade-to-debate` through either `local_sequential` or prompt-executor-backed provider mode. Keep raw `/room` bootstrapping, selection, and state reduction intact, and thread execution mode through CLI and wrapper entrypoints.

**Tech Stack:** Node.js, existing harness CLI, prompt-runner, external executor, chat-completions wrapper, node:test

---

### Task 1: Lock Inputs, Outputs, And Safety Rails

**Files:**
- Create: `C:\Users\CLH\docs\superpowers\plans\2026-04-18-room-provider-command-flow-bridge.md`
- Backup: `C:\Users\CLH\tmp\room-provider-command-flow-bridge-20260418\backup-originals\*.js`

- [x] **Step 1: Backup core runtime and test files**

Run: backup copies into `C:\Users\CLH\tmp\room-provider-command-flow-bridge-20260418\backup-originals`
Expected: all targeted files copied before edits begin

- [x] **Step 2: Define provider bridge scope**

Scope:
- keep `raw /room` bootstrap unchanged
- add provider-backed command-flow execution mode
- preserve existing local command-flow behavior
- do not start full `/room` parser work

### Task 2: Write Failing Provider Command-Flow Tests

**Files:**
- Modify: `C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js`
- Modify: `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`

- [ ] **Step 1: Add a failing CLI test for provider-backed command-flow**

Coverage:
- `--command-flow-fixture`
- `--prompt-executor node --prompt-executor-arg chat-completions-wrapper.js`
- multi-turn `/room` -> `/summary` -> `/upgrade-to-debate`
- assert provider-backed execution mode is visible in output

- [ ] **Step 2: Run targeted CLI test and verify it fails for the right reason**

Run: `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js'`
Expected: failure because provider-backed command-flow is not wired yet

- [ ] **Step 3: Add a failing wrapper test for the same path**

Coverage:
- `run-room-harness.js`
- provider-backed command-flow fixture execution

- [ ] **Step 4: Run targeted wrapper test and verify it fails for the right reason**

Run: `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js'`
Expected: failure because wrapper/CLI does not yet expose provider-backed command-flow runtime

### Task 3: Implement Provider-Aware Command-Flow Runtime

**Files:**
- Modify: `C:\Users\CLH\tools\room-orchestrator-harness\src\command-flow.js`
- Modify: `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- Modify: `C:\Users\CLH\tools\room-orchestrator-harness\src\external-executor.js`

- [ ] **Step 1: Add provider-backed executor plumbing to command-flow**

Implementation:
- allow command-flow steps to run through injected prompt executors
- support provider-backed room turn execution using prompt calls plus state reducer
- support provider-backed `/summary`
- support provider-backed `/upgrade-to-debate`

- [ ] **Step 2: Thread provider execution options through CLI**

Implementation:
- allow `--command-flow-fixture` to work with `--prompt-executor`
- preserve current guardrails for invalid flag combinations
- keep local command-flow as default when no executor is supplied

- [ ] **Step 3: Re-run targeted tests and make them pass**

Run:
- `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js'`
- `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js'`

Expected: new provider-backed command-flow tests pass and existing local tests stay green

### Task 4: Extend Provider Regression Coverage

**Files:**
- Modify: `C:\Users\CLH\tools\room-orchestrator-harness\test\chat-completions-cli.test.js`

- [ ] **Step 1: Add provider-backed command-flow integration test**

Coverage:
- expanded-pool fixture
- local mock Chat Completions-compatible endpoint
- verify prompt-call order and final state

- [ ] **Step 2: Run targeted provider test and make sure it passes**

Run: `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\chat-completions-cli.test.js'`
Expected: provider-backed dry-run tests and new provider-backed command-flow test all pass

### Task 5: Verify, Document, And Report

**Files:**
- Modify: `C:\Users\CLH\tools\room-orchestrator-harness\README.md` (if behavior surface changes)
- Create: `C:\Users\CLH\SESSION-35-PROVIDER-BACKED-COMMAND-FLOW-BRIDGE-REPORT-2026-04-18.md`

- [ ] **Step 1: Run full suite**

Run: `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'`
Expected: full green baseline

- [ ] **Step 2: Document the new runtime path**

Update:
- CLI usage if new combinations are supported
- README runtime notes if provider-backed command-flow is now mainline-capable

- [ ] **Step 3: Write implementation report**

Include:
- files changed
- what bridge is now true
- what is still explicitly out of scope
- latest test baseline
