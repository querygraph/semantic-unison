# Outbound RPC ownership and remaining work

Queue ownership is qualified at4c4f305d in this source successor. The separate
frozen IO candidate remains execution source72560ca4, request metadata18c9b822
in `unison-outbound-accounting-20261018`; do not repin it from this worktree.
The initial audit and milestones below retain their historical scope.
The additive encoder hook and standard builtin RPC producer owners are now
qualified separately; admitted external transport remains a distinct gate.

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


## Producer allocation hook qualified at c48f92eb

An internal output sink now distinguishes measuring wire length from writing
bytes. Builtin char/int32/int64/string/bytearray sizing avoids payload buffers;
callbacks/conversions, boxing, closures and traversal remain outside that claim.
Both byte sink passes validate source slices; cumulative payload plus header
uses checked addition, and second-pass destination bounds use subtraction.

`Umarshal.marshal_to_bytearray_accounted` reserves cumulative selected bytes
before framed-result/header/builtin scratch allocations. Bytearray scratch is
conservatively charged at full payload length even if a platform chunks it.
Local rejection precedes aggregate callback admission. Callback errors propagate
unchanged, no retry or refund. The partial result is published immediately after
allocation, before header copy or second-pass conversion; its caller must root
it and charges until independently established settlement. This is not all-heap,
RSS, depth, collection-count or arbitrary conversion-allocation containment.

Directed controls currently pass stock and Ox against the real mli, including
wire parity, malformed slices/size drift, no builtin sizing buffers, reservation
ordering, local/aggregate refusal and partial-root failures. Designated omission
participants must fail before unreserved allocation. Four stock/Ox builds and directed regressions passed for that additive hook.
The producer integration described next now supplies standard owner lifetimes.

That integration must reserve an owner slot before serialization, retain each
published result including partial failure, and carry the same owner into queued
consumption. The existing stateless marshaling function type cannot silently
return a debit without an owner. A synchronous context may be scoped only over
actual serialization and restored on every exception; it must never be installed
across asynchronous server work. An explicit owned-message envelope is preferable
where it avoids global context. Retained uncertainty must preserve all partial
roots and cumulative charges; normal output settlement releases once, separately
from the queue's selected logical bytes and part count. Legacy/custom producers
cannot be silently claimed covered. Existing result consumer scopes, server
reply continuations, cancellation and urgent output must retain their semantics.


## Standard producer integration qualified

[Producer ownership](rpc-producer-ownership.md) now wraps ordinary builtin
request/reply/exception and stream builders. Owners are admitted before encoding;
partial result roots are prepared before codec allocation and published before
pass two. Contexts restore before asynchronous work. Known queued failure and
actual own consumption release once, independently of unrelated later draining;
recognized uncertainty retains exact selected roots and charges. A throwing
classifier cannot turn unacquired-slot refusal into uncharged retained work.
Four stock/Ox Make+Dune+selftests and53 negatives/compiler pass; all584 recorded
inputs/compiler/binary hashes match (inventoryv23). Raw/string/custom producers,
caller/conversion/backing/baseline families and legacy result lifetimes remain
separate. No allheap/RSS/SDK/Photo/actualtransport/full SOL claim follows.
