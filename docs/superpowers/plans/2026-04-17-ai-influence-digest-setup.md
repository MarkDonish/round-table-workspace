# AI Influence Digest Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure `ai-influence-digest` on this Windows machine so it can run locally and produce daily candidate digests automatically.

**Architecture:** Keep the upstream collection script as the core engine, then wrap it with Windows-friendly setup and scheduling scripts. The scheduled task should call one stable PowerShell entrypoint that activates the local environment, runs the collector, and writes logs.

**Tech Stack:** Git, Python 3.13, PowerShell, Windows Task Scheduler, npm/OpenCLI (for Google search), Python `requests`

---

### Task 1: Create the local workspace and capture prerequisites

**Files:**
- Create: `C:\Users\CLH\source\repos\ai-influence-digest\`
- Test: environment checks for `git`, `python`, `node`, `npm`, `opencli`

- [ ] **Step 1: Confirm the intended local repository path**

Use: `C:\Users\CLH\source\repos\ai-influence-digest`

- [ ] **Step 2: Clone or recreate the upstream repository locally**

Preferred run:

```powershell
git clone https://github.com/koffuxu/ai-influence-digest.git C:\Users\CLH\source\repos\ai-influence-digest
```

- [ ] **Step 3: Verify prerequisite tools**

Run:

```powershell
git --version
python --version
node --version
npm --version
opencli --help
```

Expected: `git`, `python`, `node`, and `npm` succeed; `opencli` may require installation.

### Task 2: Install runtime dependencies

**Files:**
- Create: `C:\Users\CLH\source\repos\ai-influence-digest\.venv\`
- Modify: `C:\Users\CLH\source\repos\ai-influence-digest\requirements-windows.txt` (if missing)
- Test: import checks and collector help output

- [ ] **Step 1: Create a local virtual environment**

Run:

```powershell
python -m venv .venv
```

- [ ] **Step 2: Install Python dependency**

Run:

```powershell
.venv\Scripts\python -m pip install requests
```

- [ ] **Step 3: Install OpenCLI if it is missing**

Run:

```powershell
npm install -g @jackwener/opencli
```

- [ ] **Step 4: Verify the collector entrypoint**

Run:

```powershell
.venv\Scripts\python .\scripts\scan_x_weekly.py --help
```

Expected: usage information prints successfully.

### Task 3: Add Windows-friendly runtime and scheduling files

**Files:**
- Create: `C:\Users\CLH\source\repos\ai-influence-digest\scripts\run_daily_digest.ps1`
- Create: `C:\Users\CLH\source\repos\ai-influence-digest\scripts\run_daily_digest.cmd`
- Create: `C:\Users\CLH\source\repos\ai-influence-digest\scripts\register_daily_task.ps1`
- Create: `C:\Users\CLH\source\repos\ai-influence-digest\logs\`
- Test: script dry run and log file creation

- [ ] **Step 1: Write the PowerShell runtime wrapper**

It should:
- resolve the repo root
- create `output\ai-influence-digest` and `logs`
- activate `.venv` implicitly by calling `.venv\Scripts\python.exe`
- run `scripts\scan_x_weekly.py`
- write stdout/stderr to a dated log file
- exit non-zero on failure

- [ ] **Step 2: Write a `.cmd` shim for Task Scheduler compatibility**

It should call:

```cmd
powershell -ExecutionPolicy Bypass -File scripts\run_daily_digest.ps1
```

- [ ] **Step 3: Write a Task Scheduler registration script**

It should register a daily task that points at the `.cmd` shim or PowerShell script, with configurable trigger time.

### Task 4: Validate the local workflow

**Files:**
- Test: `output\ai-influence-digest\candidates.json`
- Test: `output\ai-influence-digest\candidates.md`
- Test: `logs\digest-*.log`

- [ ] **Step 1: Run the daily wrapper manually**

Run:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\run_daily_digest.ps1
```

- [ ] **Step 2: Confirm expected artifacts exist**

Expected:
- output directory created
- log file created
- collector artifacts created when network/search prerequisites are satisfied

- [ ] **Step 3: Capture any blocked external prerequisites**

Examples:
- `opencli` not authenticated/configured
- Google search blocked
- firewall/network restrictions

### Task 5: Document the final operator workflow

**Files:**
- Modify: `C:\Users\CLH\source\repos\ai-influence-digest\README.md`
- Create: `C:\Users\CLH\source\repos\ai-influence-digest\WINDOWS_SETUP.md`

- [ ] **Step 1: Document one-time setup**
- [ ] **Step 2: Document manual run command**
- [ ] **Step 3: Document daily scheduling command**
- [ ] **Step 4: Document where outputs and logs are stored**
