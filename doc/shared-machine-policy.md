# Sharing Morrobay with Photo

User direction, 2026-10-15: ordinary development should share the machine.
Exclusive 18-core timing windows must not block all useful Unison work.

## Current user agreement: eight credits each

The authoritative standing agreement is Photo Root's immutable
`SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json`, SHA256
`1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352`.
It records the user's equal8/8 CPU split, with2 credits left for the OS, and
supersedes both10/6 and4/12. Pool integration and runtime qualification remain
pending. The agreement does not alter the live frozen part5 exception.

| Lane | CPU-credit ceiling | Normal work |
| --- | ---: | --- |
| Unison | 8 | Default3+3 endpoint workers plus2 owner credits; current finite profile peaks at2+2+2=6; compiler jobs at most2 |
| Photo | 8 | Native/staging maximum6 plus2 owner credits; Photo's owner qualifies its reduced-grant successor |
| Headroom | 2 | Interactive applications, owners, transport and OS activity |

Memory reservations are32GiB for Unison,64GiB for Photo,32GiB system headroom;
they are not an enforced aggregate process-tree RSS limit. The standing agreement
still needs shared-pool integration and finite qualification before
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
passes `--shared-qualification --loopback-cpu-credits 8 --orchestration-cpu-credits 2`,
admitting at most six declared credits for this fixture. Four workers per endpoint
plus two owner credits would require10 and must be refused under8. These source
changes are not yet runtime-qualified. The frozen worker8 benchmark
has a different, larger allocation and cannot silently run under this split.
Build entry points accept `JOBS`; use2 for ordinary shared development.
The default3+3 profile needs worker3 admission support and post-slot controls;
it is not yet an implemented or tested shared-runtime default.

The capped entry points are implemented, but do not themselves grant a running
slot or acquire global tokens. After standing scheduling acknowledgment:

```sh
SHARED_CPU_CREDITS=8 JOBS=2 OX_PREFIX="$HOME/.opam/5.2.0+ox/bin" \
  make -f tests/Makefile ox-build
SHARED_CPU_CREDITS=8 JOBS=2 STOCK_PREFIX="$HOME/.opam/default/bin" \
  make -f tests/Makefile stock-build
```

Run these serially. They compile/link only and do not execute the resulting
Unison binary or selftests. Their receipts therefore do not replace completed
build-plus-selftest qualifications. `SHARED_CPU_CREDITS` admits1..8, defaults
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
The agreed token layout is Unison0..7, Photo8..15, with16..17 idle. Acquire a
complete required set nonblocking; on contention release every partial lock
before waiting. Never replace token files. The dispatcher currently describes
this accounting in dry-run JSON but does **not** acquire those locks. Its output
explicitly labels token acquisition, memory enforcement and physical IO identity
as unimplemented. Source labels cannot substitute for actual ownership.

[Token primitive source](../tests/shared_cpu_pool.py) is prepared but unexecuted
and not connected to the dispatcher. It reads a bounded pinned manifest, opens
existing inode-bound private regular tokens on fresh descriptions, attempts an
ascending explicit set, and closes a partial acquisition before returning busy.
Close uncertainty retains the coordinator's remaining descriptors and never
retries uncertain descriptor numbers. It has no automatic context-manager or
destructor unlock, and uses close rather than LOCK_UN so inherited copies retain
locks. Its release method consumes the runner's current settlement attestation;
it does not produce kernel proof or independently verify process receipts.
The runner must retain ownership on unknown children/groups. Actual contention,
inheritance, rollback, cancellation and dispatcher integration remain unqualified.

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

The user has confirmed the equal split. Once token integration is qualified,
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

## Implemented shared build/parser owner

The manual dispatcher now acquires the pinned canonical Unison token subset,
passes descriptors to its direct child, and observes group settlement before
wait4 and token closure. Unknown acquisition/settlement or receipt-write failure
retains the owner. Actual inheritance, ten disposable-pool controls, parser and
stock jobs2 build-only evidence is in
[shared-entrypoints-actual-20261016.json](../tests/qualification/shared-entrypoints-actual-20261016.json).
No Photo08..15 token is requested. Shared sync remains refused at execution until
its separate server/group proofs are integrated; dry-run command planning is not
runtime qualification. No physical IO lane or hard CPU/RSS enforcement is claimed.
