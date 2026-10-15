# Sharing Morrobay with Photo

User direction, 2026-10-15: ordinary development should share the machine.
Exclusive 18-core timing windows must not block all useful Unison work.

## Default split proposed to Photo Root

| Lane | CPU-credit ceiling | Normal work |
| --- | ---: | --- |
| Unison | 4 | Serial builds with `JOBS=2`, bounded functional tests and generated fixtures |
| Photo | 12 | Its own workers, compiler jobs and native backend combined |
| Headroom | 2 | Interactive applications, owners, transport and OS activity |

This is a proposed standing allocation, pending Photo Root acknowledgment and
shared-pool integration. It does not preempt an existing retained native owner.
There is no Unison dispatch merely because this document exists.

Credits are cooperative admission limits, not CPU affinity or a kernel CPU cap.
Native backend threads count toward their owner's lane. Memory, descriptors and
disk activity also need bounded workloads; CPU sharing alone does not bound them.
Allow one substantial Unison fixture job at a time, without production-photo or
catalog access. Do not start overlapping Unison builds and tests that together
exceed its four-credit lane.

For loopback synchronization, count **both endpoints**. The existing finite
`sync-functional` target passes `--loopback-cpu-credits 4` and selects workers1/2.
It is suitable for shared functional work. The prepared frozen worker8 benchmark
has a different, larger allocation and cannot silently run under this split.
Build entry points accept `JOBS`; use2 for ordinary shared development.

## Separate CPU sharing from native ownership

Photo Root retains ownership of Lightroom/UI operations, catalog/cache writes,
renderers, preview publication and its canonical IO lease. Adobe SDK validation
remains a separately coordinated native operation. Ordinary Adobe-free Unison
builds/tests do not require the Photo lease.

Both projects should use the same stable CPU-token pool, with grants held through
actual owned-child settlement. Never create a second pool and assume its tokens
coordinate with Photo. Unknown outcomes retain ownership; a result frame or
missing PID alone is insufficient release evidence.

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
