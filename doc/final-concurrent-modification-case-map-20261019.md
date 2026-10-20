# Concurrent modification (SOL row 5) — case map, 2026-10-19

Read-only mapping of existing tests and actual receipts; nothing was rerun.
All runs below pin pre-fix production (`files.ml` 0f2c6157,
`helperSupervisor.ml` 43686f6c, `supervisedExternal.ml` 7ac6b9c2). The
[delta impact note](production-delta-10c5d159-impact-20261019.md) explains why
these paths are unaffected by `10c5d159`; no rerun under new pins is claimed.

| Concern | Tests | Actual evidence | Scope / limits |
| --- | --- | --- | --- |
| Source changed during transfer / after scan | `tests/clone_stage.ml` (live basis rewritten; "clone snapshot, isolation, modes and exclusive output: ok"); `tests/clone_lease/test.ml` "source fd replacement returns actual identity and stops before any copy", "rename/path replacement preserves the enrolled held source and does not select new path"; `tests/workers/restored_mutation.ml` | Native stage 5267/cfd95f/0, audit 2a4ba1/0 (`final-native-stage-v2-actual-20261019.json`, BOTH_COMPILERS_PASS_CLOSED); CloneLease cases in native publication 74637/dd4390/0 | held snapshot bytes survive a live rewrite; primitive level only, no end-to-end transfer case |
| Receiver destination changed before publish | `tests/final_publication/test.ml` "target mutation after existing observation", "target inode replacement with same bytes", "published target replacement foreign sentinel retained"; clone_lease "mid-transfer destination fd replacement never writes or closes the replacement sentinel" | 74637/dd4390/0, 177 cases/compiler ordinary+timed, audit 748b45/0; guard ablation reproduced "candidate mutation was published" | directed native primitives; injected syscall errors, not disk exhaustion or power loss |
| Symlink substitution | `test.ml` "candidate symlink never admitted or removed", "expected symlink replaced without following", "effective directory rebound"; `producerTest.ml` final-component and resume symlink cases; `tests/semantic/dng_components.ml` mid-lookup rename+symlink checks | 74637/dd4390/0; DNG components 38297/b5ca6f/0, audit cbcdaf/0; predecessor `dng-cache-lookup-race-actual-20261017.json` 42365/6e723a/0 | primitive scope; DNG run is not camera-semantic or pixel qualification |
| Inode/device change, hardlinks | `test.ml` "candidate inode replacement with same bytes", "candidate late hardlink rejected but alias preserved", "candidate preexisting hardlinks never admitted", "expected target hardlinks remain legal"; `producerTest.ml` inode-disagreement and replacement-after-prefix cases | 74637/dd4390/0; clone-sync 43369/a6d4ef/0 (held reader + hardlink kept old bytes) | clone-sync is sequential policy, not every concurrency scenario |
| Cache invalidation by concurrent change | `tests/workers/components.ml` stale-generation/changed-input checks; `dng_components.ml` "cache reuse delivered stale current-input view" | worker state 88752/cde84c/0 ("PASS 126 component worker checks"), audit e8f0ef/0; DNG 38297/b5ca6f/0 | tiny fixtures; `doc/component-hashes.md`: checks "do not exclude a hostile concurrent writer" |
| Late completion after cancel/shutdown | `tests/workers/late_cancel.ml` completed-before-owner success/cancel/shutdown; `components.ml` late-cancellation check | 88752/cde84c/0 (three PASS settlement lines); predecessor `worker-late-owner-completion-actual-20261017.json` 11412/66fb24/0 (built from the main checkout) | deterministic tiny source; not on the receiving transport |
| Exact restored mtime | `tests/final_publication/restored_mtime.ml` (2 cases); `tests/workers/restored_mutation.ml` | publication 53737/fd27be/0, 12 children incl. 2 designated guard removals exit 2; audit b3f93e/0; worker 88752/cde84c/0 | two same-size mutation cases/compiler; not an uncooperative-writer cure |
| Uncooperative check→rename race | none, by design | documented as remaining in `final-native-publication-result-20261019.md`, `sol-clone-final-case-map-20261019.md`, `implementation-status.md`, `acceptance-matrix-audit.md` | no atomic namespace compare-and-swap against hostile writers |

## Gaps

- No end-to-end Unison transfer case where the sender changes mid-transfer;
  evidence stops at native primitives and worker recognizers.
- `implementation-status.md` still lists a systematic live
  source/destination path/inode/symlink replacement matrix at every
  transfer/commit boundary as missing (its restored-mtime item is now covered).
- The named receiving suite contains no concurrent-modification cases.
- For DNG cache and worker tests the names above are assertion messages, not
  emitted inventory names; publication and clone-lease names are inventoried.
