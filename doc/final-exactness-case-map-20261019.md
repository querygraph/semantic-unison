# Exactness (SOL row 1) — case map, 2026-10-19

Read-only mapping; nothing rerun. All receipts pin pre-fix production; see
[production delta impact](production-delta-10c5d159-impact-20261019.md) for why
these paths are unaffected by the later fixes.

| Concern | Tests | Actual evidence | Limits |
| --- | --- | --- | --- |
| First byte / first region | `tests/semantic/conformance` golden `multi` (regions 0+3, 3+2, 11+4, 27+5 of 32 B), `multi/golden`, `multi/truncate`; `tests/clone_range/test.ml` "head only", "head, two chunks and tail" | `current-sde-conformance-actual-20261018.json` session 3582 596b01→9768d4/0 (127 commands, 2224 assertions per compiler); `current-range-components-actual-20261018.json` session 6994 404879→96a5a8/0 (48 cases per compiler) | synthetic bytes; range uses a fake memory copier |
| Last region / EOF | golden region 27+5 ends at EOF; SDE `single-byte-at-signed-int64-eof` accepted, `offset-past-eof`/`extent-past-eof` rejected; range "tail only", source/destination boundary EOF; clone-sync `shorten`/`extend`; whole-file "independent bytes/EOF" | SDE and range receipts; clone-sync 43369/a6d4ef/0, audit 2ec05e/0; whole-clone stock 55677/daab31/0, Ox 99536/6c48f3/0 | DNG goldens place one packet at offset 96, not at EOF |
| Zero length | SDE `zero-file-with-operation`, `length-zero`, `count-zero`, `declared-payload-zero` (rejected); range "empty"; whole-file "empty source" decline; positional "zero and 64KiB" | SDE, range, whole-clone receipts; positional 73365/d6f63a/0 | rejection/component level only |
| Multiple regions | golden `multi`; `maximum-valid-wire-shape`, 64 operations, `region-bytes-1048576`; range multiple chunks and 960-combination matrix; positional multi-attempt patches | SDE, range, positional receipts | not a packetized network test; one XMP packet per DNG fixture |
| Identical file (no-op) | `bench/sync/run.py` no-op fence (inode, SHA, basis unchanged); clone-sync `noop`/`final-noop`; SDK merge no-op | all-ten cohorts 180 rows/540 CLI (e.g. stock1 22685 f83404→a005f2/0); larger128 stock1 52223/3c264e/0 | warm generated fixtures |
| Resource fork | sync-properties seeded and removed a nonempty fork; native-stage forks stripped from stage | sync-properties 28308/7b837c/0, audit 455c91/0; native-stage 5267/cfd95f/0 | selected Darwin properties; stage case proves isolation |
| Mode, mtime, xattr, flags | sync-properties mode 0640→0400, xattr removal, exact ns timestamps, 8-field no-op identity; clone-sync `nodump` policy; restored-mtime refusal | sync-properties receipt; clone-sync; restored-mtime 53737/fd27be/0, audit b3f93e/0 | not all xattrs/ACLs/compression; ACLs only as stage stripping |
| Sparse / holes | native-stage "Real sparse input"; positional sparse offset above 2 GiB; generated sparse creation | 5267/cfd95f/0; 73365/d6f63a/0; `generated-sparse-creation-actual-20261019.json` 465356/0 | positional sparse fixture never read back |
| Path-independent full-file hash | cohort fence: both replicas equal the independently computed expected SHA, basis unchanged; SDE goldens from a stdlib-only reference; clone-sync full compare | cohort, SDE, clone-sync receipts; whole-clone audit e5cf6f/0 | 8 generated files per cohort row |

## Gaps

1. No current execution receipt for the `tests/semantic/test.ml` "Sparse
   metadata" first/last/disjoint/adjacent/full/multi-region apply cases (the
   current hash is pinned only as a source input).
2. Zero-length file: closed by [fs_properties](current-fs-properties-receiving-result-20261020.md)
   (create, grow, shrink, delete on both compilers). Still open: an accepted
   zero-region delta.
3. No DNG with several XMP packets, or a packet at EOF.
4. ACL and xattr transitions now run end to end (fs_properties). Holes arrive
   byte-exact, but remote transfers materialize them. Still open: a fork or
   xattr carried through a semantic DNG update, and BSD flags beyond `nodump`.
5. `tests/transfer_instruction_bounds/probe.ml` covers empty/first/last/multiple
   token frames but its receipt binds 6 of 9 pins.
