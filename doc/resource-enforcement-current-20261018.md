# Remaining resource enforcement work, current source review

This review is tied to `resource-enforcement-current-20261018.json`, not the
historical line numbers in resource-lifetime-inventory.md. It reads source and
metadata only. It does not establish actual OS FD peaks, RSS bounds or a new
execution grant. The full SOL M6 resource requirement remains open.

Current admission is useful but narrower than that requirement. Runtime defaults
reserve 512 MiB of estimated payload/backend credits and 512 descriptor credits.
The worker pool has a 4096 pending limit, domain admission, CPU permits and
endpoint-local device admission. Submission duplicates its input, and Apply and
Snapshot also duplicate output, before waiting for IO/CPU. Successful input and
operation duplicates are closed before worker completion is published. Payload
credits do not measure the OCaml heap, arbitrary plugin/native allocations,
helper RSS, remote decoded arguments, or transport/runtime baseline FDs.

## Close uncertainty is an enforcement prerequisite

`SemanticWorkers.close_noerr` suppresses Unix close errors. Both worker completion
and pre-transfer cleanup use it. A worker can consequently publish completion,
and its owner can decrement pending/release reservations, after a close attempt
whose OS settlement has not been independently established. This is a source
finding, not an observed leaked FD and not proof that any previous successful
run leaked resources. In particular, retrying a failed close by numeric FD would
be incorrect: the kernel might have already closed and reused that number.

`SemanticFile.with_fd_internal` consumes its channel/descriptor ownership marker
before the close attempt. A normal-path close exception propagates, but cleanup
then suppresses further close failures. Worker execution converts Unix errors
into ordinary failure responses. Thus propagating a plain error alone would not
preserve the admission obligation. Snapshot opens independent source/output
readers sequentially, while its worker also has an outer reader; its omitted
primary-reader sample is intentionally not a measured zero.

A strict successor needs all of these properties together:

1. Allocate an ownership record and capture pre-close identity before acquiring
   or transferring a new descriptor. Track explicit entries, including separate
   duplicates of the same inode; never use unique-inode counts as FD capacity.
2. Consume numeric-close authority once. A failed close records uncertainty and
   its original cause; no numeric retry or claim that the descriptor is live or
   settled based only on its current number.
3. Deliver uncertainty through worker responses and all mapping/cleanup layers
   without converting it to a normal failed operation. Preserve input, operation
   and nested-reader close failures together instead of replacing one cause.
4. Keep the owning job/reservation reachable and prevent reuse of its credit
   until a qualified settlement boundary exists. Neither cancellation nor an
   ordinary failed result is that boundary. Process exit can settle process FDs,
   but does not retroactively prove ordinary per-job cleanup.
5. Reserve capacity before every admitted acquisition, with rollback only for
   known-settled entries. Separately account transient native probes, pool pipes,
   publication contexts, helper launch FDs and transport baseline. Pending count
   alone excludes those classes and is not an OS ceiling.
6. Qualify normal close, close-error-after-kernel-close/number reuse, error before
   settlement, simultaneous primary+cleanup failures, cancellation and shutdown
   using original fixed injections on stock and OxCaml. Preserve raw evidence;
   never turn a fault-injection failure into a passing lifecycle receipt.

This is a required implementation sequence, not a claim that introducing a
carrier by itself would satisfy whole-process FD bounds. Existing callers and
native adapters must be audited before enabling a strict enforcement mode.

## Memory and benchmark obligations remain separate

Credit estimates and sampled RSS are not hard RSS enforcement. A hard process or
process-tree limit needs a supported OS containment mechanism, a platform refusal
when unavailable, and tests of descendants/native allocations as well as OCaml
allocations. Current macOS helper address-space-limit rejection is not a working
RSS cap. Do not enable a purported hard mode using the existing estimates.

The new fixed repeated shared-eight benchmark request can gather wall/CPU,
primary reads and inclusive phase measurements without claiming these bounds.
Its pending admission does not block source review, and this review changes none
of its pinned execution sources. Future enforcement code must use a fresh source
snapshot and qualification; do not mutate an admitted/frozen run in place.
