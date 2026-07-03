# How The Review Room Works

Round Table Workspace is a local-first review gate for AI coding agents.

It is not trying to be a random multi-agent chatroom. The useful moment is
smaller and sharper: one AI coding agent says something is ready, and you want a
small review room to slow that decision down before you merge, publish, or trust
the work.

## The Four Moves

| Move | Plain meaning | Output |
|---|---|---|
| 1. Create reviewer candidates | Start from the question or generated change and ask which review angles could catch real failure modes. | Candidate product, engineering, risk, and user-facing reviewers. |
| 2. Select reviewers for this decision | Keep the reviewers that add useful pressure to the specific decision. | A small panel instead of a noisy crowd. |
| 3. Bound the debate | Make the panel argue about value, evidence, risk, and next action. | Visible disagreement and missing-evidence checks. |
| 4. Write a decision record | Turn the discussion into a local artifact. | `ship`, `revise`, or `reject`, plus risks and next steps. |

## Why This Is Different

A normal agent answer can sound finished while still hiding the important
questions:

- Is the user value real enough?
- Did the implementation evidence actually run?
- Are public claims broader than the evidence?
- What should happen next if the answer is not ready?

Round Table Workspace makes those questions explicit. A product reviewer can
push on user value. An engineering reviewer can push on tests and integration.
A risk reviewer can push on claim boundaries. A user advocate can push on
whether the result is understandable.

The result should not be a long transcript that nobody reads. The result should
be a decision record that helps a maintainer act.

## Decision Shape

`ship` means the panel did not find blocking gaps for the stated scope.

`revise` means the direction may be useful, but evidence, claims, tests, docs,
or scope need another pass.

`reject` means the proposal is not worth shipping in its current form.

## Boundaries

Round Table Workspace does not replace tests, security review, or human
ownership. The default demo path is local-first and fixture-backed.
No host-live or provider-live support is claimed without fresh evidence.

## Try It

```bash
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick
```

Start with the README if you want the shortest path:
<https://github.com/MarkDonish/round-table-workspace>
