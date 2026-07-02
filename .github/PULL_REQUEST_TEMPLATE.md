# Summary

<!-- What changed, and why? -->

## Verification

Run the checks that match the change:

```bash
python3 -m unittest discover -v
./rtw doctor --quick --quiet
./rtw release-check --include-fixtures --strict-git-clean --quiet
```

## Claim Boundary

- [ ] This PR does not describe fixture-backed success as host-live or provider-live support.
- [ ] New public claims are backed by current evidence, or explicitly marked as unconfigured, blocked, pending, or historical-only.
- [ ] No API keys, tokens, cookies, private account details, or local-only secrets are included.

## User-Facing Changes

- [ ] README/docs updated when behavior or public positioning changed.
- [ ] Screenshots or rendered docs checked when a user-facing surface changed.
