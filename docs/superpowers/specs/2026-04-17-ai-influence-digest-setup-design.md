# AI Influence Digest Windows Setup Design

**Goal:** Configure `ai-influence-digest` on this Windows machine so it can run locally and produce daily collection outputs without requiring manual execution.

**Scope:** Local repository setup, Python environment setup, Windows-friendly run scripts, output/log directories, and Windows Task Scheduler integration. Push delivery to Codex inbox or Feishu is explicitly out of scope for this phase.

**Constraints:**
- Keep the upstream repository behavior intact where possible.
- Prioritize the collection workflow (`scan_x_weekly.py`) over screenshot rendering because the renderer depends on external OpenClaw tooling.
- Support a no-LLM daily run path so the scheduled job itself has zero token cost.

**Approach:**
1. Bring the repository into a local workspace under `C:\Users\CLH\source\repos\ai-influence-digest`.
2. Add Windows-oriented helper files instead of rewriting the upstream scripts.
3. Install the minimum required dependencies for the collection script.
4. Create a single stable entrypoint script that Task Scheduler can call every day.
5. Validate the setup with a minimal local run and capture any remaining prerequisites.

**Files Expected:**
- Local repo: `C:\Users\CLH\source\repos\ai-influence-digest`
- Repo docs: Windows setup/readme additions if needed
- Runtime scripts: Windows `.ps1` and `.cmd` entrypoints
- Scheduling support: Task Scheduler registration script or explicit command
- Local data: `output\`, `logs\`, optional `.venv\`

**Non-Goals:**
- Codex inbox automation
- Feishu distribution
- LLM-based summarization or Chinese rewrite
- Screenshot publishing workflow completion on Windows unless the external dependency is already available
