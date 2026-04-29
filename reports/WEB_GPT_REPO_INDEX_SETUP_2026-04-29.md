# Web GPT Repository Index Setup - 2026-04-29

## Scope

Target repository: `MarkDonish/round-table-workspace`

Goal: connect the repository to the logged-in ChatGPT web session through the GitHub / ChatGPT Codex Connector path and trigger GitHub code-search indexing so Web GPT can query the repository through its GitHub tool.

## Actions Completed

- Confirmed local repository state was clean and synced with `origin/main`.
- Opened the GitHub code-search indexing trigger:

```text
https://github.com/search?q=repo%3AMarkDonish%2Fround-table-workspace%20import&type=code
```

- Observed GitHub first report:

```text
This repository's code is being indexed right now. Try again in a few minutes.
```

- Waited for the GitHub indexing window and refreshed the search page.
- Confirmed the search index completed: GitHub code search returned `88 files` for `repo:MarkDonish/round-table-workspace import`.
- Confirmed `ChatGPT Codex Connector` is installed on the `MarkDonish` GitHub account.
- Confirmed repository access for the connector is set to `All repositories`, which includes `MarkDonish/round-table-workspace`.

## Permission Boundary

No GitHub App permission changes were saved during this run.

The connector already had repository coverage through `All repositories`; changing or saving GitHub App permissions was unnecessary and was intentionally avoided.

## Current Status

Status: configured and indexed.

Web GPT should now be able to use the GitHub connector against `MarkDonish/round-table-workspace`, subject to normal ChatGPT web UI/tool availability in the active conversation or project.

## Suggested Web GPT Smoke Test

In the target ChatGPT web project or conversation, enable/use the GitHub tool and ask:

```text
请使用 GitHub connector 读取 MarkDonish/round-table-workspace 的 README.md，并总结 /room 和 /debate 的区别。
```

Expected result: ChatGPT should reference repository files instead of answering only from general memory.
