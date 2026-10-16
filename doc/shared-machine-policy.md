# Sharing Morrobay with Photo

The user agreed to **8 Unison / 8 Photo / 2 system**. The authoritative policy is
Photo Root's `SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json`, SHA256
`1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352`.
It supersedes the historical10/6 and4/12 proposals. Routine bounded Adobe-free
work inside this standing lane needs no new whole-machine scheduling approval.

| Lane | Canonical tokens | Normal budget |
| --- | --- | --- |
| Unison | 00..07 | Both loopback endpoints3+3 plus2 owner credits; compiler jobs at most2 |
| Photo | 08..15 | Photo-owned reduced-grant adapter and its qualified workload |
| System | 16..17 idle | Two physical cores of scheduling headroom |

Credits are cooperative admission limits, not CPU affinity or hard kernel CPU
caps. Memory reservations32/64/32GiB are not enforced process-tree RSS limits.
Photo owns the qualification of its shared native successor; this document does
not permit its historical fixed18 adapter to run under an eight-credit grant.

## Implemented ownership and evidence

The existing stable pool is described by
`/Users/alexy/src/photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json`.
Its exact trusted manifest and existing inode identities are checked; no token
file is created, replaced or explicitly LOCK_UN'd. Acquire the complete explicit
set in ascending order using fresh descriptions and nonblocking flock. Contention
closes all partial acquisitions before returning busy. Unison selects only a
subset of authorized00..07; caller-selected indexes cannot authorize borrowing.

The manual dispatcher refuses an interpreter without waitid(WNOWAIT)/wait4
before reading/acquiring the pool. It retains token descriptors through direct-child and group
settlement. It passes descriptors to the runner; inherited copies keep a lock
when the parent's copy closes. Indeterminate close never retries that numeric
FD. Unknown acquisition/settlement retains the owner even if receipt writing
fails; ordinary errors or timeouts do not establish release.
Target entry scripts and declared helper modules are pinned before child launch
and checked after settlement. Source changes invalidate qualification while
known child/token closure remains separately recorded.

[Ten disposable controls, actual parsers and a jobs2 stock build](../tests/qualification/shared-entrypoints-actual-20261016.json)
passed. The bounded [shared functional sync](../tests/qualification/shared-functional-actual-20261016.json)
also passed: stock/Ox, three modes, workers1/2/3, two private2MiB files per row,
18rows/54CLI. Both direct client and supervisor groups use strict absence
observations before wait4. All native-server/pump receipts are separately audited
before the runner is reaped and tokens close. An outer deadline retains the live
sync coordinator instead of discarding its server ownership handles.

These are finite functional/ownership qualifications, not quiet timing, aggregate
RSS, full camera-corpus or physical IO isolation proofs. The timed benchmark audit
remains separate and still rejects this zero-warmup/one-repetition profile.

## Entry points

Invoke from the repository root, serially within the Unison lane:

```sh
SHARED_CPU_CREDITS=8 JOBS=2 STOCK_PREFIX="$HOME/.opam/default/bin" \
  make -f tests/Makefile stock-build
SHARED_CPU_CREDITS=8 JOBS=2 OX_PREFIX="$HOME/.opam/5.2.0+ox/bin" \
  make -f tests/Makefile ox-build
SHARED_CPU_CREDITS=8 make -f tests/Makefile shared-sync-controls
SHARED_CPU_CREDITS=8 STOCK_RECEIPT=/path/stock-build-selftest.json \
  OX_RECEIPT=/path/ox-build-selftest.json make -f tests/Makefile sync-functional
```

Build-only commands compile/link and do not execute the resulting binary or
selftests. They do not replace build-plus-selftest qualification; sync requires
existing successful selftest receipts with unchanged production-source/artifact
pins. Shared inspector builds (`inspect-stock`/`inspect-ox`) retain a pinned binary with
zero inspector executions and one compiler job. `inspect-file` reuses a trusted
pinned build with one synchronous worker plus2 owner credits, without rebuilding;
copy consent and physical IO coordination remain independent. Shared builds accept3..8 credits
and at most2 compiler jobs plus2 owner
credits. Shared sync requires the complete8-credit lane. Pure parser/interface
scopes can use a smaller authorized subset. Unscoped tests remain refused in
shared mode; they need an appropriate resource owner rather than an arbitrary
claim that their budget fits. Legacy commands retain their behavior without
`SHARED_CPU_CREDITS`. `DRY_RUN=1` only prints a plan, acquiring no tokens.

## Independent resources and exceptional timing

Photo Root retains ownership of Lightroom/UI, catalog/cache writes, renderers,
preview publication and canonical Photo IO lease. Adobe SDK validation needs
separate coordination. CPU tokens grant none of these operations.

For bulk IO, identify the physical device/container: distinct APFS volume names
do not imply independent devices. One bulk scan/hash/copy/fixture stream per
physical device is the default. A common physical-device lane and memory
admission remain integration gaps; do not claim peaceful concurrent heavy IO.

Named peak-concurrency or quiet timing experiments require separate scheduling
and actual closure. Ordinary shared timing is background-contended. Preserve
workload disclosures; no absolute quiet claim. Frozen results, incompletepart3,
and all timing caveats remain unchanged. No automatic retry, replacement or
successor allocation follows from a resource release.
