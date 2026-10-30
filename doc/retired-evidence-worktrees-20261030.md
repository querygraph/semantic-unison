# Retired evidence worktrees, 2026-10-30

Four worktrees from the 2026-10-17 component qualifications were kept, locked,
at the paths their records name. They held nothing outside Git, and their
commits are in `master`'s history, so they were removed. To check a record that
names one of these paths, recreate the worktree at that path from its commit:

```sh
git -C ~/src/semantic-unison worktree add ~/src/unison-component-workers-20261017 9327553e
```

| Worktree path | Commit | Branch (deleted) | Named by |
| --- | --- | --- | --- |
| `~/src/unison-component-archive-20261017` | `4d1dcc6fc86ecbaadb0cee928cee2888cdec8d86` | `feat/component-archive-hints` | `OPUS-HANDOFF.md` |
| `~/src/unison-component-cache-20261017` | `835df2fcc6f6c7d985722514efb1c52f526b6428` | `feat/component-cache-input-binding` | `OPUS-HANDOFF.md`, `tests/qualification/component-checkpoint-core-actual-20261017.json` (15 paths, no digests) |
| `~/src/unison-component-index-20261017` | `c372213a917d221e8f7c71bf45cd8267324d55bb` | `feat/component-owner-index` | `OPUS-HANDOFF.md` |
| `~/src/unison-component-workers-20261017` | `9327553e2b09a3e0397649b5c5d241cbd6989bfc` | `feat/dng-component-workers` | `OPUS-HANDOFF.md`, `tests/qualification/component-domain-workers-actual-20261017.json` (320 pinned files) |

Before removal, all 320 SHA-256 source pins in
`component-domain-workers-actual-20261017.json` were checked against
`9327553e` and matched.
