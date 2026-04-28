# GitHub Release Publication - v0.1.2 - 2026-04-28

This is a historical publication report. It records the GitHub Release page and
Actions publication evidence for `v0.1.2`. Current source-of-truth entry points
remain `README.md`, `docs/`, `prompts/`, `examples/`, and `.codex/skills/`.

## Result

- Tag: `v0.1.2`
- Target commit: `c1a3aed Prepare v0.1.2 patch release`
- Release page: `https://github.com/MarkDonish/round-table-workspace/releases/tag/v0.1.2`
- Published at: `2026-04-28T07:49:56Z`
- Draft: `false`
- Prerelease: `false`
- Workflow run: `https://github.com/MarkDonish/round-table-workspace/actions/runs/25040681309`
- Workflow conclusion: `success`

## Verified Commands

```bash
/tmp/gh_2.91.0_macOS_arm64/bin/gh release view v0.1.2 \
  --repo MarkDonish/round-table-workspace \
  --json tagName,name,isDraft,isPrerelease,publishedAt,targetCommitish,url
```

Returned:

```json
{
  "isDraft": false,
  "isPrerelease": false,
  "name": "v0.1.2",
  "publishedAt": "2026-04-28T07:49:56Z",
  "tagName": "v0.1.2",
  "targetCommitish": "main",
  "url": "https://github.com/MarkDonish/round-table-workspace/releases/tag/v0.1.2"
}
```

```bash
/tmp/gh_2.91.0_macOS_arm64/bin/gh run view 25040681309 \
  --repo MarkDonish/round-table-workspace \
  --json databaseId,status,conclusion,createdAt,updatedAt,headSha,event,displayTitle,url,jobs
```

Confirmed:

- Run status: `completed`
- Run conclusion: `success`
- Event: `push`
- Head SHA: `c1a3aed0e66931cc40b210e03615477d763c6999`
- Publish job conclusion: `success`
- `Publish or update release` step conclusion: `success`

## Current Launch Interpretation

The repository can be launched under the `v0.1.2` Codex local mainline support
scope:

- `/room`
- `/debate`
- `/room -> /debate`
- checked-in prompts, runtime bridges, and validation harnesses
- default Claude Code host-live support only on the validated Mac account
- OpenCode wrapper tooling without OpenCode host-live claim

This report does not widen the release claim to all third-party agent hosts or
real provider-live support.
