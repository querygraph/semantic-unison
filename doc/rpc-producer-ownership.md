# Builtin RPC producer allocation ownership

This source successor integrates the separately qualified Umarshal encoder hook
with standard command request/reply/exception and stream builders. It is not
repinned into the frozen V4 transport requests. Current source passed four stock/Ox Make/Dune+selftests and53 designated
negatives/compiler; see `tests/qualification/rpc-producer-ownership-actual-20261018.json`.

`with_produced_output` prepares an explicit owner and uncertainty link before
slot admission. Normal/idle producers share `rpcencodebudget` (512 MiB selected
cumulative bytes), `rpcencodeslots` (256), and `rpcencodebuffers` (65536). Urgent
producers have independent `rpcurgentencodebytes` (65536),
`rpcurgentencodeslots` (256), and `rpcurgentencodebuffers` (2048). Slot maxima and
positive/overflow policy validation use the same checked lane mechanism as
queued outputs. These preferences are endpoint-local. Urgent capacity is not a
promise of socket or peer progress.

The synchronous builder installs an owner context and restores the prior context
on both return and exception, before returning any asynchronous output work.
Nested/reentrant builders restore the outer owner. `marshalV1` prepares a buffer
root/link before invoking the accounted encoder. The publication callback is a
nonallocating store into that prepared root. The hook admits cumulative builtin
result/header/scratch bytes before their allocation. Buffer-root admission and
byte admission are independent; a known refused builder has not dispatched an
output consumer and releases all partial roots and charges.

Actual output consumption is wrapped separately from the output queue's return
promise. When the producer's own consumer settles, its buffers and charges are
cleared once, even if that promise continues draining an unrelated later action.
A known queued cancellation before consumer entry also clears the producer.
Recognized uncertainty or a throwing ownership classifier retains the exact
buffer roots, selected charges, original failure and classification failure.
The prepared carrier exists before work starts; process/connection absence is
never release proof. Client pending-reply registration still occurs after
successful serialization and is independently settled on known send failure.

This covers builtin `marshalV1` calls made under the standard producer builders.
It does not retroactively own preexisting caller arguments, tag/ID/connection
baseline buffers, custom marshaling allocations, user conversion callbacks,
backing aliases, collection traversal/depth, or all heap/RSS. Legacy raw/string
send helpers remain separate. Queue logical bytes and producer cumulative
allocation charges are distinct budgets; neither is described as exact peak
physical memory. Existing decoded argument/result/error scopes remain separate.

Original controls exercise slot refusal before builder entry, buffer-count
refusal after a partial builder, cumulative byte refusal preserving a held
producer, nested/restored contexts, known queued cancellation, own consumer vs
later queue draining, actual command send failure, and typed/classifier uncertain
publication roots. Deliberate omissions cover aggregate byte charging, context
restoration, own-consumer settlement and publication. The context-omission
participant hits an existing inactive-owner guard earlier in the combined suite;
its narrow witness is that guard, not a fabricated later assertion. No SDK,
Photo payload or actual external transport grant follows from these controls.


Final source audit added a no-resource refusal control: classifier exceptions
must not retain uncharged operations before a producer slot is acquired or after
its own consumer settles. An original tiny counterexample failed, the active-
owner classification guard fixed it, and both compilers detect its deliberate
omission. Final controller89158/150917/exit0/no session passed all four builds and20
regression groups; all584 recorded inputs/compiler/binary hashes match. Every
child/group/CPU4or8 token set closed. Earlier builds/unions predate this correction
and are preserved as historical. This qualifies the stated builtin producer
boundary, not complete SOL, SDK, Photo or external transport acceptance.
