# Local semantic phase observations

`-debug semantic-timings` enables optional production worker diagnostics when
its runtime is first created. It does not enable semantics, change validation
policy or authorize a transfer. The separate `semantic-reads` debug tag retains
its existing primary-reader counters and line format.

`SemanticFile.with_read_stats ~measure_stages:true` allocates four reader-local
counters. `SemanticWorkers.set_read_observer ~measure_stages:true` captures that
choice in each immutable submitted job. Worker domains retain the clocks and
mutable counters locally; only immutable completed samples cross the mailbox.
The observer and trace output run on the Lwt owner, after reply settlement.
Changing observer settings still requires an idle, open pool. Snapshots remain
excluded because their independent readers are not measured by the outer reader.

| Tag | Current measured boundaries |
| --- | --- |
| hash | Whole-file `SemanticFile.digest`; SDE full/preserved/region hashing after its manifest has been validated, including reader I/O and final stability checks inside those callbacks. |
| parse | Extension inspection and core manifest validation in `SemanticDelta.inspect`. A normal parser refusal is still a completed parse call. |
| verify | SDE apply's live basis proof, staging preimage proof, and final staging target SHA-256 check. Nested staging readers are included in these intervals, although their read bytes remain outside the primary-reader byte counter. |
| write | SDE apply's changed-window comparison and bounded write loop, including cancellation checks and short-write/EINTR handling. Not filesystem flush, rename or durable publication. |

Samples have a fixed tag, normally returned call count and **inclusive monotonic
seconds**. Parent and child phases overlap: basis verification includes its
parse/hash phases. Never sum tags, subtract unrelated reader totals, or interpret
these intervals as isolated CPU time. They include scheduler delays and I/O;
they exclude queue/admission/delivery outside the worker callback. The benchmark's
separate `job_completion_seconds` includes those owner-side delays.

Ordinary readers and default observers leave timing disabled. Disabled measurement
calls invoke their callback without clock reads or timing-counter updates; this
is not a promise of zero additional closure allocation. POSIX uses
`CLOCK_MONOTONIC`. Clock failure, backwards/nonfinite time, duration overflow or
call-counter exhaustion invalidates the entire reader timing report. There is no
wall-clock fallback. The current Windows backend reports timing unavailable.
`stages=None` means disabled or unavailable; the requesting owner knows which.
`Some []` means enabled with no normally returned measured phase.

A throwing phase callback propagates its original exception and records no
successful interval. If an outer callback catches it, any eventual timing report
therefore excludes that failed interval. An escaping reader/callback/stability
failure returns no reader report at all. Failed/cancelled worker operations do
not become successful diagnostic samples. Timing never establishes process,
file-descriptor, native object or resource-credit closure.

These are local diagnostics, absent from SDE wire records, profile identifiers,
archive authority and content digests. They do not assert pixel equivalence,
physical I/O counts, whole-application read coverage, peak RSS or hard limits.
They currently do **not** measure atomic commit, all component-forest hashing,
legacy paths or validators. Those benchmark requirements remain open. Historical
sealed runs retain their original sources and measurements; no new observations
are assigned to them retroactively.

## Directed qualification

`tests/workers/run.py --stage-stats-only` uses original 4 KiB fixtures. It checks
disabled/enabled-empty reports, callback-exception propagation, exact hashes,
SDE parse/hash and three verification/one write intervals, exact output bytes,
and independent worker samples delivered to owner-only callbacks. The fixture
runs four jobs on two workers and verifies normal pool/CPU closure. Existing
`--read-stats-only` controls separately cover stable-reader failures, parallel
counters, observer reentrancy and observer exceptions.

See [the actual qualification](../tests/qualification/semantic-phase-observations-actual-20261017.json)
for retained stock/Ox production-object tests, full builds/selftests, SDE wire
conformance and actual owning-tool terminals. These controls qualify collection
and compatibility; they are not a synchronization performance matrix.

## Actual stream-format correction

The first real generated cohort exposed Trace.debug prefixing a whole sample
list once. Its original strict result omitted unprefixed later phases, although
all lines were saved. The [actual receipt](../tests/qualification/sync-phase-collection-actual-20261018.json)
binds an explicit per-stream, same-job/ordered/adjacent grouped-line supplement;
derived prefix contexts are identified separately from originally printed text.
No result bytes were changed and no sync was repeated. The emitter now wraps
each phase in its own Trace.debug callback and emits no prefix for an empty
sample list. [Current formatter controls and full builds](../tests/qualification/phase-format-correction-actual-20261018.json)
detect the original grouped-output regression on both compilers. Old sealed
source/document pins remain historical, not unchanged-current-source claims.
