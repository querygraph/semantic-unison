# Typed worker scheduling qualification

Run seeded mixed hashing/DNG inspection under CPU contention:

```sh
python3 tests/workers/run.py --ocamlopt /usr/local/bin/ocamlopt --stress-only --keep-work --receipt /tmp/worker-stress.json
python3 tests/workers/run.py --ocamlopt ~/.opam/5.2.0+ox/bin/ocamlopt --stress-only --keep-work --receipt /tmp/worker-stress-ox.json
```

Six fixed PRNG seeds each run twenty batches of32 jobs. Four actual worker domains share a budget varying from1 to4 CPU credits. Every batch first reserves every CPU credit, submits a randomized mix of classic/extended DNG inspection and hashing, cancels a randomized subset in shuffled order, and proves cancellation settles while the budget remains held. After release, remaining results must match direct sequential hashes or structural proofs. Every round checks zero pending/running jobs and CPU reservations, and peak execution never exceeds the CPU budget. Shutdown checks descriptor counts against the baseline. Immutable source, compiled binary and log hashes are retained with the receipt; no source photos or Adobe/Lightroom operations are used.

This is root-owned reproducible scheduling evidence, not race-detector coverage, randomized active-write/application/RPC coverage or compiler-proved domain safety. Cancellation timing is deliberately queued; existing focused suites cover active cancellation and mutation separately. Hash/proof baselines use the same production algorithm, so this test checks scheduling parity rather than an independent algorithm oracle. Actual OS ordering may differ despite identical seeds. The existing full suite remains available without selectors; identify-only runs its content-recognition controls. Keep-work is required for durable local artifact references.

The first new fixture compilation used an operator absent from Unison's bundled legacy Lwt. It failed before test execution on both compilers; replacing it with the existing bind/return interface required no production change.

## Private-stage apply cancellation races

Use `--apply-stress-only --keep-work --receipt /tmp/apply-stress.json` with either compiler. Six seeds each schedule four batches of16 independent BigTIFF/CR DNG stages under four domains and shared CPU budgets1..4. Half the jobs receive randomly selected cancellation timers at0,0.1,1 or5ms after submission. Completed artifacts require exact full-byte equality to the target and a16-byte/one-call metadata write report. Cancelled stages are discarded without publication. Each completion verifies caller descriptors remain owned; each batch verifies unchanged basis/target bytes, zero pending/running/reserved resources and bounded peak execution; each pool shutdown checks descriptor parity.

Both retained compiler runs observed384 jobs:192 exact completions and192 cancellations,1255 checks. This races cancellation with submission and worker execution but does not attest cancellation during a particular native write or guarantee all four timing classes reached active execution. No application result is published. The first fixture expectation accidentally used15 rather than the actual16-byte XMP packet length; both failed runs are retained, and the expectation now derives the packet length. No production correction was needed. Earlier seeded hash/inspection receipts retain their earlier immutable source snapshots.

For the checked production boundary, add `--build SNAPSHOT/src`. The runner
verifies matching production source inputs and links the snapshot's actual
compiler-matched CMIs, CMXs and native objects without interface substitution.
The full suite uses at most18 worker credits and includes48 observations whose
complete metadata transcripts and byte proofs must match sequential results.
The [current qualification](../checked_worker/qualification.json) combines these
actual-object tests with compiler negative captures. Plain isolated runs above
remain runtime scheduling controls; their ordinary interfaces do not establish
compiler portability.

## Standing-eight configured-pool parity

`--shared-parity-only --build SNAPSHOT/src --keep-work` links the actual
compiler-matched production objects and runs one 64-byte original fixture at
configured pool sizes1/2/4/8. Sixteen jobs per configuration mix hashing and
structural proof inspection. Four queued cancellations must settle while all
CPU permits are deliberately held; the other twelve must match sequential
results after release. Every shutdown restores the descriptor baseline and
zero pending/running/CPU reservations.

Admission is1/2/4/6 CPU permits respectively. The eight-worker configuration
therefore fits six executing jobs plus two owner credits in the standing Unison
eight-token lane. It does not establish eight simultaneous execution, OS thread
caps, hard RSS/FD bounds, active native-write cancellation, or throughput.
[Actual stock/Ox evidence](../qualification/shared-worker-parity-actual-20261016.json)
retains both production-object pins, actual parent terminals and group/token
closure. No EXglobal IO, camera payload or Adobe operation is used.

## Standing-eight mixed workers and weighted helpers

`--shared-mixed-only --build SNAPSHOT/src --keep-work` links actual
compiler-matched production objects. Budgets1/2/4/6 each submit sixteen hashes
of an original64-byte fixture and two real `/bin/sleep` helpers with weights1
and min(2,budget). Completion requires exact sequential hash parity, successful
helper waits, zero remaining permits/queues and restored descriptor count.
These are synthetic helper stand-ins, not ExifTool/Adobe validation or measured
CPU utilization/throughput; six permits plus two owner credits fits Unison8.

[Actual stock/Ox qualification](../qualification/shared-mixed-worker-helper-actual-20261016.json)
passed64 hashes/eight helpers per compiler, with both outer owners/groups and
canonical tokens closed. An initial test-only compile error (mistaking the
direct helper result for an optional admission result) ran no test helpers;
its idle outer owner required independently scoped recovery after the runner
was reaped. [Preserved recovery](../qualification/shared-mixed-first-compile-recovery-20261016.json)
records actual outer exit137, no fabricated normal exit or original wait4
receipt, and subsequent fresh whole-token acquisition. The corrected successor
checks known nonzero outcomes before releasing settled outer ownership.

The [group-observed successor](../qualification/shared-mixed-helper-groups-actual-20261016.json)
records all eight helper PIDs per compiler, actual direct wait0 and the qualified
macOS `observe_group` callback reporting zero other members before leader reap.
Missing/unknown/nonzero observations fail this host-specific test; no historical
PID is signaled. This is a diagnostic census plus separate supervisor wait, not
a durable descendant absence proof or support for deliberately escaped groups.
Hash parity, permit/queue settlement and descriptor baseline checks still pass.

## CPU-working helpers mixed with worker hashes

`--shared-mixed-hash-only --build SNAPSHOT/src` runs four permit budgets1/2/4/6,
with16parent file-hash jobs and two supervised original CPU-hash helpers per
budget. Helpers compute SHA-256 over an owned64KiB string32times per declared
domain (width1 or2), join the domains, and compare with the portable reference;
parent checks the exact transcript. No SDK, ExifTool, Photo payload or EXglobal
IO is used. Existing `--shared-mixed-only` retains its sleeping-helper scenario.

[Stock/Ox actual qualification](../qualification/shared-mixed-cpu-hash-actual-20261016.json)
records64parentjobs/eighthelpers percompiler, actual group-before-reap
observations, settled shared budget/pool and restored parent descriptor baseline.
The test-only spawn marker becomes `Domain.Safe.spawn` on OxCaml; compiled test
source hashes are retained. Production sources are unchanged. Budget6 plus two
owner credits fits standingUnison8. This is functional mixed-work accounting,
not sampled CPU overlap, hard OSthread/RSS ceilings, SDK/ExifTool qualification or
throughput evidence. The compiler's scheduler warning remains visible.
# Completed reply before owner delivery

`late_cancel.ml` is an additional deterministic component, linked to the actual
qualified production objects. A trusted tiny-file recognizer waits on an Atomic
barrier. The owner releases it and stops pumping Lwt until `W.usage` observes
running0 under the mutex that also publishes the completion. The reply promise
must still sleep while CPU/IO/pending-job accounting remains charged. Normal
delivery returns its result; cancellation or shutdown before owner delivery
must return None. Shutdown must not change the caller's cancellation token.
Each case checks empty ledgers, caller-source identity and restored FD baseline.

[Current stock/Ox evidence](../qualification/worker-late-owner-completion-actual-20261017.json)
contains exact compiler argv, linked-object pins, executable hashes and actual
compile/run/group settlements for all three cases/compiler. To reproduce, copy
the participant into a new private work directory before invoking the recorded
compiler with the matching production object snapshot; use that directory as
the executable cwd. The first run emitted compiler companions beside the source;
its three newly generated companions were retained in the Ox workspace afterward.
No production source/build objects were changed. This is a worker delivery race
control, not a publication commit, arbitrary async-fault or hard-resource proof.
Actual owning session11412/66fb24/0/no running session; Unison8 closed. No SDK,
camera/Photo/media or canonical IO access. The frozen mixed326 source pins match.
