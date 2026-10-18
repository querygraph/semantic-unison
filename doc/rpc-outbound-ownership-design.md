# Next source work: outbound RPC ownership

The current qualified candidate is frozen at execution source456776d8, with
metadata/request history throughf6472dc2 in `unison-decoded-input-20261018`.
This successor worktree isolates source development from those exact IO requests.
No current outbound implementation or runtime qualification is claimed here.

The existing three dump paths accept a list of `(Bytearray, offset, length)`
slices and enqueue a closure over that list. Queue count and selected logical
bytes have no independent process-wide admission. `performOutput` can run an
immediate action and then drain other queued actions; its returned promise is
not always the earliest settlement of just the original action. Queued waiters
are failed after their closures are removed, while an already executing action
settles separately. A new owner must preserve those distinctions.

Implement and qualify two separate boundaries:

1. Validate all slice offsets/lengths and checked cumulative length before queue
   admission or writes. Reserve nonwaiting aggregate owner/selected-byte credits
   across Normal/Idle and a separately bounded urgent control lane, so bulk queue
   pressure does not consume the allowance needed for protocol abort messages.
   Retain the exact list through actual action settlement, queued cancellation,
   and recognized uncertainty; never release from connection/process absence.
2. Add producer-side allocation reservation for builtin serialization before
   encoded buffer allocation, then migrate known producers. Queue admission
   alone comes after serialization and cannot prove that allocation was bounded.
   Custom codec allocations need their own explicit contract.

A slice length is not necessarily the retained backing allocation: aliased
Bigarray views and repeated references must not be presented as exact heap or
RSS accounting. Fixed connection output buffers and flow-control tokens remain
separate baseline costs. Do not add a copy of every output buffer just to make
a misleading accounting identity; measure any deliberate copying tradeoff.

Controls must distinguish queued cancellation, live write borrower, observer
installation failure, duplicate/independent owners, byte/count overflow,
invalid slices, exact capacity, urgent progress and retained uncertainty. Use
original tiny fixtures and designated safe mutants, then current stock/Ox builds
and real admitted transport; no fuzz/sanitizer campaign or Photo payload grant.

## Concrete first correction in progress

The audit found an inherited count/end mismatch: fillBuffer passed a slice count
to fillBuffer2, whose last argument is an absolute end. An actual original-source
7B golden fails (offset2,count3 should send abc). The successor now validates the
entire list before copying and each dump before queuing, derives checked ends,
checks cumulative integer counts, and skips empty slices without flushing.
Actual pipe controls cover direct, normal, idle and urgent writes across multiple
buffers with production maybeFlush promises observed through settlement. Eight
mutants pass stock/Ox focused controls; full builds/regression are active.
This corrects byte semantics and validation only; it does not yet implement the
queue/allocation/urgent credit ownership proposal above. Queued V3 source requests
were explicitly deferred, originals preserved, pending a qualified fixed successor.

## First correction qualified

The count/end and whole-list/prequeue correction now passes four current stock/
Ox Make/Dune+selftests and the39-negative/compiler union. Actual controller
24512/2a3485/0/no session; each build/control child reaped0/groups absent/CPUclosed.
All582 recorded inputs/compiler/binary hashes and tested-source hashes match.
See rpc-output-slice-validation.md and tests/qualification/rpc-output-slices-actual-20261018.json.
The queue/allocation ownership proposal remains unimplemented; this acceptance
does not replace it or final actual transport/SOL/platform/performance acceptance.

## Queue boundary now qualified

The successor now admits normal/idle and separate urgent selected bytes, parts
and owners, and keeps explicit payload roots through actual consumers. Known
queued cancellation, own-action versus later draining, a nested admission race,
and recognized uncertainty are covered. Four stock/Ox builds+selftests and48
negative participants/compiler passed (inventoryv21). Producer-side allocation
BEFORE serialization remains open: the current sizing pass itself creates
primitive/string/bytearray temporary buffers, so a callback only after measuring
cannot establish that boundary. See rpc-output-queue-ownership.md.
