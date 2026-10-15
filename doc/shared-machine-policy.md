# Sharing Morrobay with Photo

User direction, 2026-10-15: ordinary development should share the machine.
Exclusive 18-core timing windows must not block all useful Unison work.

## Current source proposal from Photo Root

The current proposal is
`/Users/alexy/src/photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v1.json`,
SHA256 `2924dc03ce15cc44e9d03018d247b105b6a632fdb4fb0af5ddda0775f94b50c4`.
It supersedes the earlier Unison4/Photo12 proposal. It is a source contract,
not a runtime grant or qualification.

| Lane | CPU-credit ceiling | Normal work |
| --- | ---: | --- |
| Unison | 10 | Up to4 workers per loopback endpoint plus2 orchestration/hash credits; compiler jobs at most2 |
| Photo | 6 | Up to4 native/staging workers plus2 orchestration credits; compiler jobs at most2 |
| Headroom | 2 | Interactive applications, owners, transport and OS activity |

Memory reservations are32GiB for Unison,64GiB for Photo,32GiB system headroom;
they are not an enforced aggregate process-tree RSS limit. This standing source
proposal still needs shared-pool integration and finite qualification before
runtime use. It does not preempt an existing retained native owner.
There is no Unison dispatch merely because this document exists.

Credits are cooperative admission limits, not CPU affinity or a kernel CPU cap.
Native backend threads count toward their owner's lane. Memory, descriptors and
disk activity also need bounded workloads; CPU sharing alone does not bound them.
Allow one substantial Unison fixture job at a time, without production-photo or
catalog access. Do not start overlapping Unison builds and tests that together
exceed its project lane.

For loopback synchronization, count **both endpoints**. The existing finite
`sync-functional` target selects workers1/2. In the new shared source mode it
passes `--loopback-cpu-credits 10 --orchestration-cpu-credits 2`, admitting at most
six declared credits for that smaller fixture. The ordinary shared ceiling is
4+4+2=10. These source changes are not yet runtime-qualified. The frozen worker8 benchmark
has a different, larger allocation and cannot silently run under this split.
Build entry points accept `JOBS`; use2 for ordinary shared development.

The capped entry points are implemented, but do not themselves grant a running
slot or acquire global tokens. After standing scheduling acknowledgment:

```sh
SHARED_CPU_CREDITS=10 JOBS=2 OX_PREFIX="$HOME/.opam/5.2.0+ox/bin" \
  make -f tests/Makefile ox-build
SHARED_CPU_CREDITS=10 JOBS=2 STOCK_PREFIX="$HOME/.opam/default/bin" \
  make -f tests/Makefile stock-build
```

Run these serially. They compile/link only and do not execute the resulting
Unison binary or selftests. Their receipts therefore do not replace completed
build-plus-selftest qualifications. `SHARED_CPU_CREDITS` admits1..10, defaults
compiler jobs to the smaller of2 and the grant minus2 owner credits, and rejects
more than2 compiler jobs or an over-budget total. Shared builds need at least3
credits. The new source behavior awaits post-part5 checks.
Legacy entry points keep their existing behavior when the variable is absent.

The same shared flag admits pure parser/interface checks and `sync-functional`
(six declared credits required); it rejects other targets whose whole test budget has
not been qualified. That rejection does not prevent source work or a separately
scheduled invocation. This dispatcher is a local command-budget guard, not a
global pool allocator, memory bound, OS thread cap or scheduling acknowledgment.
The [pure entrypoint controls](../tests/manual_shared_test.py) launch no children.

## Separate CPU sharing from native ownership

Photo Root retains ownership of Lightroom/UI operations, catalog/cache writes,
renderers, preview publication and its canonical IO lease. Adobe SDK validation
remains a separately coordinated native operation. Ordinary Adobe-free Unison
builds/tests do not require the Photo lease.

Both projects should use the same stable CPU-token pool, with grants held through
actual owned-child settlement. Never create a second pool and assume its tokens
coordinate with Photo. Unknown outcomes retain ownership; a result frame or
missing PID alone is insufficient release evidence.

Canonical existing pool manifest:
`/Users/alexy/src/photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json`.
Use its existing directory and inode-bound files, never create a competing pool.
The proposed Unison set is indexes0..9, Photo10..15, with16..17 idle. Acquire a
complete required set nonblocking; on contention release every partial lock
before waiting. Never replace token files. The dispatcher currently describes
this accounting in dry-run JSON but does **not** acquire those locks. Its output
explicitly labels token acquisition, memory enforcement and physical IO identity
as unimplemented. Source labels cannot substitute for actual ownership.

For bulk IO, identify the physical device/container first: Ten/Quasar or two APFS
volumes cannot be assumed independent from volume names alone. One bulk scan,
hash, copy or fixture stream per physical device by default; small metadata may
coexist. A common physical-device lane and memory admission remain integration
gaps, with concurrent synthetic qualification required after the quiet run.

Photo's currently inspected engine-v8 native adapter reserves all18 tokens even
for a smaller native thread target. Its owner must qualify a successor accepting
an explicit reduced grant and a backend thread target within that grant before
such rendering can share CPU credits. Existing qualified18-token admissions stay
unchanged. This document does not implement or qualify that Photo successor.

Once Root acknowledges the standing split and the applicable pool protocol,
routine bounded Adobe-free work should proceed within the Unison lane without
a new per-test scheduling approval. Announce actual handles and release evidence
for substantial jobs so either owner can see current usage.

## Measurements and exceptional windows

Functional correctness can be checked while both projects run. Timing collected
then is explicitly background-contended, with workload observations retained;
do not call it quiet or compare it unconditionally with isolated measurements.

Only a named peak-concurrency or quiet timing experiment should request an
exclusive window, with an agreed duration and actual closure. Such a request
does not block unrelated source preparation or make all remaining goal work
depend on that benchmark. Existing frozen results, the failed part3, and timing
disclosures remain untouched. No automatic retry, sample exclusion, replacement
or successor allocation follows from this policy.
