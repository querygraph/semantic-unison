# Component inspection in typed domain workers

`SemanticWorkers.components` accepts an owner-frozen `DngComponents.decoders`
handle, an explicit component/decoder read budget, cancellation and a borrowed
readable regular-file descriptor. It uses the existing queue, domain slots,
CPU permits and optional filesystem gate. There is no worker registry lookup,
archive operation, external helper or automatic component pass for ordinary jobs.

Keep the caller descriptor open and do not seek/read/write it until the promise
settles. Its worker duplicate shares the open-file position. Concurrent jobs
need independently opened descriptors, as in the qualification. The owner must
retain immutable input access during inspection: epoch checks are cooperative
stability observations, not hostile-writer exclusion.

The result is cancellation/shutdown `None`, or an inspection with original file
stats and `components = Ok summary | Error unsupported_reason`. Operational
reader, geometry-capability and component-budget failures fail the job with
`SemanticWorkers.Failed`; they never become no-match or ordinary unsupported.
Negative budgets refuse before descriptor admission. Existing descriptor-close
uncertainty limitations are not expanded into a universal lifecycle guarantee.

A summary contains raw32-byte full-file and layout-view SHA256 values, the five
ordered role projections, bounded decoder outcomes/provenance and charged logical
requested bytes. A missing role projection is unavailable, not an empty pixel
identity. Encoded-unit comparisons do not establish complete images or rendering
identity. Only these compact immutable observations cross the completion mailbox;
component sessions, reader capabilities and snapshots stay inside the worker.

The component budget excludes preceding bounded DNG geometry reads. With the
existing owner read observer enabled, successful stable jobs also report those
delivered logical reads. The original8192B fixture charges8192B without refinement
or8321B with a one-byte decoder read and128B parent rehash. Actual reader reports
8280B/8409B respectively, including88B geometry reads. Neither counter measures
physical IO, prefetch, RSS or elapsed speedup; failed/cancelled partial reads do
not gain a successful reader report.

Cancellation and shutdown suppress completed-but-undelivered component results.
CPU and filesystem ownership remains charged until actual worker completion and
owner settlement. This is the existing typed pool lifecycle, with no new global
pool or native/SDK permission. The shared physical-IO barrier remains an outer
owner responsibility for admitted bulk work.

[Actual evidence](../tests/qualification/component-domain-workers-actual-20261017.json)
records87 checks per stock5.2/Ox5.2+ox compiler, four contained compile/runtime
calls linked to334 production artifacts, two Make builds and two Dune builds
with full selftests/workers3. Tests cover twelve queued jobs on a configured
two-worker pool with separately opened FDs, off-owner refinement, owner-only
read reporting, unchanged full/pixel hashes, unsupported versus operational
errors, successful filesystem admission, queued/late cancellation, shutdown
suppression, permit/queue/localIO settlement and descriptor baseline recovery.
Actual simultaneous CPU computation was not measured. All groups and canonical
Unison8 tokens closed; no EXglobal, camera, Photo payload or Adobe was used.

This makes the component API available to owner consumers. User-facing RPC/UI,
archive identity, persistent-cache binding and real-camera qualification remain
separate work. Summaries are historical observations, not reuse/publication
capabilities. Complete private-field understanding is not required for the
already qualified exact-layout receiving operation.
