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

## Explicit local details

With an enabled semantic profile (for example `-semanticdng true`), the additional
off-by-default `-semanticcomponents true` preference appends component comparisons
to explicit details requests. Ordinary scanning, transfer and reconciliation do
not start this extra pass. Each endpoint reads its complete file, plus bounded DNG
geometry, using an empty frozen decoder set and the existing owner transaction,
filesystem gate and domain pool. The component read budget is the opened file's
size; no extra private refinement is selected implicitly.

`SemanticReport.render_components` compares exact full bytes independently of
the versioned projection contract. It reports five role lanes and treats missing
lanes as unknown. Different projection-contract versions suppress component
comparison, while exact full SHA256 values can still be compared. Layout views
also encode knowledge refinement and are not physical-layout change proofs.
Malformed digests, duplicate roles and invalid counts refuse; displayed schema
text is escaped. No SIR/0 or SIR/1 bytes change.

The owner retains local source stats and checks path replacement/change before
accepting the result. Both the earlier report snapshot and component snapshot
join the existing one-shot details-cache invalidation. This is cooperative epoch
binding, not exclusion of a hostile concurrent writer. Remote roots now require
the separate `semantic-components-v0` capability and an enabled DNG profile.
The new [SIC/0 protocol](component-report-v0.md) returns only bounded nonce/contract-
bound observations. Older report negotiation grants no component capability.
The earlier qualification below proves the local stage; actual new-command
transport qualification remains separate.

[Owner qualification](../tests/qualification/component-owner-local-actual-20261017.json)
records current stock/Ox Make+Dune builds, full Make selftests,1272 source checks
and production-linked owner/cache controls on both compilers. The initial
zero-payload admission refusal is preserved; the positive summary-envelope
minimum passed final controls. All groups and CPU grants closed, no real media,
SDK or canonical IO barrier used. The details-cache tests exercise the linked
owner functions; they are not an interactive GUI or remote-transport trial.

The [remote-source successor qualification](../tests/qualification/component-remote-source-actual-20261017.json)
adds SIC/0 codec controls and current Make/Dune/local-owner builds. Its new RPC
implementation is not yet an actual loopback or mixed-version transport result.

Archive identity, persistent-cache binding and real-camera qualification remain
separate work. Summaries are historical observations, not reuse/publication
capabilities. Complete private-field understanding is not required for the
already qualified exact-layout receiving operation.
