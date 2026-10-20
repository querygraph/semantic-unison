# Production delta 1cb9306a → 10c5d159: impact on earlier evidence

Three fixes found by the actual named receiving runs change four production
files (61 insertions, 12 deletions): `helperSupervisor.ml/.mli`,
`supervisedExternal.ml`, `files.ml`. A pin scan found 105 earlier plans and
receipts binding a pre-fix hash of at least one of them; they remain valid
evidence about the pre-fix candidate and are not rewritten. This note states
which behavior changed, so earlier results are not silently relabelled current.

## What changed, by path

| Path | Before | After | Reached only when |
| --- | --- | --- | --- |
| Helper teardown from registered cleanup (cancellation listener or `at_exit`) | SIGKILL group, reap, retire; nothing reported | Same, plus: if group observation is enabled, wait ≤1 s for the killed leader to be terminal, kill leftovers, census, then reap; then call `observe_teardown` | a helper is still owned at cancellation/exit **and** a group-observing trace (`external-process` or `validation-group`) is enabled |
| Helper teardown from internal failure / owner cleanup | kill, reap, retire | unchanged (`notify=false`) | — |
| Ordinary helper completion, timeout, output limit | monitor path | unchanged | — |
| `SupervisedExternal` trace | once, on Lwt result | once, from whichever of Lwt result or `observe_teardown` comes first | external copy/merge/diff helper |
| Merge publication | copyBack replica 1 then replica 2 | adds a pure archive lookup first; on failure of replica 2, restores replica 1's previous archive entry, then re-raises | a merge whose second publication fails |

## Coverage of the changed paths on the new binary

- Stock and OxCaml builds and full selftests at the fix commits (receipts
  `/private/tmp/unison-named-build-{stock,ox}-20261019-04.json`).
- Actual named receiving suite on both compilers at `10c5d159`
  ([result](current-named-receiving-result-20261019.md)): exit-time disposal of
  the interrupted copy helper (4 cases), external copy/merge tracing (9 copies,
  7 merges), second-publication merge rejection and recovery
  (`merge-pass-error`, `merge-pass-wrong-receipt`), validator timeout and
  client SIGINT cancellation with `validation-group` tracing.

## Earlier evidence that touched the changed paths

Validation cancellation with group tracing (for example
`mixed-validation-unknown-lifecycle-actual-20261016.json`,
`validation-live-observer-bridge-actual-20261016.json`) exercised the old
teardown, which skipped the census. Those results stand for the pre-fix
candidate. The new path adds a bounded ≤1 s wait during cancellation of a
traced helper; it is covered for the generated validator by the named suite,
not re-run against the real SDK. Earlier SDK receiving runs did not cancel a
helper and did not fail a merge's second publication.

Other earlier evidence (parser, XMP, clone, publication, archive/RPC, range,
worker, benchmark cohorts) does not reach these paths; its binding to the
pre-fix hashes is a pin difference, not a behavior difference. Re-running it
under new pins is optional and is not claimed here.

## Residual

The restore relies on the stored archive entry already being in stripped form
(`Props.strip`), as `moveArchiveLocal` also assumes; both compilers' real runs
committed identical archives after restoration. No unit-level OCaml test was
added for the three fixes.

## Addendum: `8581f357` (reserved `unison:` merge prefix)

`files.ml` now refuses a merge command that starts with `unison:` but is not
`unison:dng-xmp-scalars/0`, with "Unknown built-in merge policy", instead of
running it through `/bin/sh` (which failed later with status 127). Reached only
by a merge rule naming an unknown `unison:` policy; ordinary external merge
commands and the built-in policy are unchanged. Exercised by the built-in DNG
merge successor's `policy-mismatch` case; no earlier evidence used such a name
except the bare `tests/dng_merge/run.py`, which accepted the old shell failure.
