# Capture and scalar-merge input ownership

`SemanticSync.capture_common_base_async` now prepares one input slot before
opening the candidate. `merge_local_async_internal` prepares four slots before
cache lookup: saved base (absent on a compact-base hit), left, right and output.
Each slot is an opaque `NotificationPipe` single-read owner. Path strings,
retention links, callbacks and the interrupted-acquisition error are prepared
before the descriptor is acquired; adoption follows open immediately. No
post-open descriptor-list allocation is required.

Known work completion closes each independent slot once. An ordinary operation
failure is recorded before cleanup. A close exception consumes that numeric
close authority, retains its pre-close identity and cause, and keeps the scope
and transaction reply unresolved. Cleanup still attempts the other independent
slots. Repeated cleanup cannot retry an uncertain numeric descriptor, including
when the kernel closed it and the number was recycled. A nested recognized
borrower uncertainty keeps the whole input scope and its admission pending.
This is cooperative owner-loop retention, not aggregate FD/RSS containment.

`retained_inputs` and the per-slot forensic accessors expose retained evidence;
path text is not an inode binding or permission to retry cleanup. Unknown test
fixtures end at process exit, without claiming normal in-process settlement.
Output name ownership remains with the merge caller.

The controls privately replace the close call in compiler-matched notification
owners, recompile their dependent object suffix, and use the actual input scope
inside production transaction admission. Counts one and four cover normal and
ordinary failure, each acquisition failure, each individual close failure,
combined close failures before the kernel and after kernel close with numeric
reuse, original error preservation and repeated-cleanup refusal. A deliberately
close-swallowing implementation must fail a designated assertion. These are
helper-boundary fault controls; they do not claim fault injection at every full
capture/merge instruction.

Separate full-pipeline controls use generated 64 KiB DNGs: actual compact-base
capture, saved-file scalar merge, and compact-base merge with a deliberately
absent fallback file. Both merge paths must produce the exact expected disjoint
XMP scalar reconciliation and preserve all input bytes, restoring descriptor,
transaction, worker, CPU and filesystem-I/O ledgers. Existing six acquisition
errors and eleven explicit post-acquisition exception regressions also run.
No camera, Adobe SDK, real transport or Photo cache is used.

`SemanticMergeCache` internal directories, quota/record descriptors and temporary
names still need their own joint uncertainty owner. This change does not make an
ordinary cache-internal close error a typed uncertainty. The synchronous
reference path remains separate/test-only. Aggregate descendant resource
accounting, broader benchmarks and final integration also remain open.
