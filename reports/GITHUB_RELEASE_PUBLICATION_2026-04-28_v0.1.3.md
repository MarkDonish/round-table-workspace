# GitHub Release Publication - v0.1.3 - 2026-04-28

This is a historical report. It records the GitHub Release publication evidence
for `v0.1.3`. Current source-of-truth entry points remain `README.md`,
`CHANGELOG.md`, `docs/`, `prompts/`, `examples/`, `.codex/skills/`, and
`.claude/skills/`.

## Scope

- Release tag: `v0.1.3`
- Target commit: `26e8e428cc0bc42d108765c1f4e5d8b47f072427`
- Release page:
  `https://github.com/MarkDonish/round-table-workspace/releases/tag/v0.1.3`
- Publication workflow:
  `https://github.com/MarkDonish/round-table-workspace/actions/runs/25049260899`
- Publication status: published
- Published at: `2026-04-28T11:06:45Z`

## Completed

- Prepared `docs/releases/v0.1.3.md`.
- Prepared `docs/releases/v0.1.3-github-release.md`.
- Updated release publication workflow defaults to `v0.1.3`.
- Updated release publication checker defaults to `v0.1.3`.
- Tagged `v0.1.3`.
- Pushed `main` and `v0.1.3` to `origin`.
- GitHub Actions release publication workflow completed successfully.

## Verification

Pre-tag local validation passed:

```bash
python3 .codex/skills/room-skill/runtime/release_readiness_check.py \
  --include-fixture-runs \
  --strict-git-clean \
  --state-root /tmp/round-table-release-readiness-v0.1.3 \
  --output-json /tmp/round-table-release-readiness-v0.1.3.json
```

```bash
python3 .codex/skills/room-skill/runtime/release_candidate_report.py \
  --include-fixture-runs \
  --strict-git-clean \
  --state-root /tmp/round-table-release-candidate-v0.1.3 \
  --output-json /tmp/round-table-release-candidate-v0.1.3.json \
  --output-markdown /tmp/round-table-release-candidate-v0.1.3.md
```

Fresh-checkout release audit passed:

```bash
python3 .codex/skills/room-skill/runtime/post_release_consumer_audit.py \
  --ref v0.1.3 \
  --state-root /tmp/round-table-post-release-consumer-audit-v0.1.3
```

Authenticated GitHub checks from this Mac:

```bash
/tmp/gh_2.91.0_macOS_arm64/bin/gh run list \
  --repo MarkDonish/round-table-workspace \
  --workflow publish-github-release.yml \
  --branch main \
  --limit 5 \
  --json databaseId,status,conclusion,createdAt,updatedAt,headSha,url,event
```

Latest run result:

```text
databaseId=25049260899
status=completed
conclusion=success
headSha=26e8e428cc0bc42d108765c1f4e5d8b47f072427
url=https://github.com/MarkDonish/round-table-workspace/actions/runs/25049260899
```

```bash
/tmp/gh_2.91.0_macOS_arm64/bin/gh release view v0.1.3 \
  --repo MarkDonish/round-table-workspace \
  --json tagName,name,isDraft,isPrerelease,publishedAt,targetCommitish,url
```

Release result:

```json
{
  "tagName": "v0.1.3",
  "name": "v0.1.3",
  "isDraft": false,
  "isPrerelease": false,
  "publishedAt": "2026-04-28T11:06:45Z",
  "targetCommitish": "main",
  "url": "https://github.com/MarkDonish/round-table-workspace/releases/tag/v0.1.3"
}
```

## Decision

`v0.1.3` is published and launchable within the documented Codex local mainline
scope.

This does not widen the provider-live or OpenCode host-live claims.
