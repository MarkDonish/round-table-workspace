# Session Checkpoint: v0.2.0-alpha Release

Date: 2026-04-29
Repo: `/Users/markdonish/Documents/New project/round-table-workspace`
Remote: `git@github.com:MarkDonish/round-table-workspace.git`

## Key User Quotes

- "我把它拆成了 7 个 Epic、27 个开发条目"
- "我建议你下一版先打一个 v0.2.0-alpha，只做这 8 个最关键任务"
- "然后先做第一个任务"
- "好的，把剩下的两个任务给完成"
- "好的，剩下的任务帮我按照最上面那个开发文档去完成"
- "那就把它们配置完"
- "授权完成了 你看一下呀"
- "f可以了"

## Scope Decision

The v0.2.0-alpha iteration was intentionally narrowed from the full 7 Epic / 27 item roadmap to these eight alpha-critical items:

- RTW-001 unified CLI
- RTW-002 README 5-minute path
- RTW-003 transcripts
- RTW-005 protocol spec
- RTW-006 room schema
- RTW-007 debate schema
- RTW-010 initial `roundtable_core` abstraction
- RTW-027 v0.2.0 milestone docs

Later in the session, the user asked to continue beyond the first alpha slice and complete the remaining work according to the original development document. The session then moved through the remaining implementation, validation, release preparation, GitHub release automation, and local GitHub CLI configuration.

## Completed Release State

- Commit created and pushed:
  - `5b29fbb docs: prepare v0.2.0-alpha release`
- Tag created and pushed:
  - `v0.2.0-alpha`
- Remote main points to:
  - `5b29fbbabdafd77398ebae3c24778cfb3f013712`
- Tag exists on remote:
  - `refs/tags/v0.2.0-alpha`
- GitHub Release published:
  - `https://github.com/MarkDonish/round-table-workspace/releases/tag/v0.2.0-alpha`
- Release metadata confirmed:
  - `isDraft: false`
  - `isPrerelease: true`
  - `publishedAt: 2026-04-29T04:43:37Z`
- GitHub Actions workflow confirmed:
  - `Publish GitHub Release`
  - active
  - workflow id `266847033`

## Validation Commands

These checks passed during the release sequence:

```bash
python3 -m unittest discover -v
```

Result: 34 tests passed.

```bash
./rtw release-check --include-fixtures --strict-git-clean --state-root /tmp/round-table-release-check-v020-alpha-strict --timeout-seconds 30
```

Result: no release blockers.

```bash
python3 .codex/skills/room-skill/runtime/release_candidate_report.py --include-fixture-runs --strict-git-clean --state-root /tmp/round-table-release-candidate-v020-alpha-strict --timeout-seconds 30
```

Result: `release_decision` was ready for local Codex mainline scope.

```bash
python3 .codex/skills/room-skill/runtime/post_release_consumer_audit.py --ref v0.2.0-alpha
```

Result: local tag post-release consumer audit passed.

```bash
python3 .codex/skills/room-skill/runtime/post_release_consumer_audit.py --source git@github.com:MarkDonish/round-table-workspace.git --ref v0.2.0-alpha --quick
```

Result: GitHub remote quick post-release audit passed.

```bash
python3 .codex/skills/room-skill/runtime/github_release_publication_check.py --strict-published --state-root /tmp/round-table-github-release-publication-v020-alpha-authenticated-final --timeout-seconds 30
```

Result: release page status was `published`; latest GitHub Actions run succeeded.

## GitHub CLI Configuration

The local GitHub CLI path now resolves to:

```bash
/Users/markdonish/.local/bin/gh
```

The wrapper points to:

```bash
/private/tmp/gh_2.91.0_macOS_arm64/bin/gh
```

The binary was confirmed as:

```text
Mach-O 64-bit executable arm64
```

Authenticated status was confirmed outside the Codex sandbox:

```text
github.com
  ✓ Logged in to github.com account MarkDonish (keyring)
  - Active account: true
  - Git operations protocol: ssh
  - Token scopes: 'gist', 'read:org', 'repo'
```

Important caveat: inside the Codex sandbox, direct `gh auth status` can still report token errors because the sandbox cannot access the macOS keyring the same way. The working source of truth for this session was the escalated, sandbox-outside check.

## Files Added Or Updated In Release Prep

- `docs/releases/v0.2.0-alpha.md`
- `docs/releases/v0.2.0-alpha-github-release.md`
- `CHANGELOG.md`
- `README.md`
- `LAUNCH.md`
- `docs/NEXT-STEPS.md`
- `docs/release-readiness.md`
- `docs/release-candidate-scope.md`
- `docs/user-entry-guide.md`
- `docs/agent-consumer-quickstart.md`
- `.codex/skills/room-skill/runtime/README.md`
- `.codex/skills/room-skill/runtime/extract_github_release_body.py`
- `.codex/skills/room-skill/runtime/github_release_publication_check.py`
- `.github/workflows/publish-github-release.yml`

## Current Repo Status

At checkpoint time:

```text
## main...origin/main
```

No uncommitted release-code changes were present before writing this checkpoint.

## Remaining Notes

- The v0.2.0-alpha release itself is complete and published.
- The GitHub CLI is usable when allowed to access the host keyring.
- If a future Codex run sees `gh auth status` fail inside the sandbox, rerun the check with escalated permissions before treating auth as broken.
