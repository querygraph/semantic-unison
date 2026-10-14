# Checked semantic worker mailbox component

`SemanticMailbox` is a bounded atomic FIFO for immutable worker messages. The
same implementation builds on stock OCaml5.5.1 and OxCaml5.2.0+ox. An explicit
[OxCaml interface template](../src/semanticMailbox.ox.mli.in) was compiled against
that unchanged implementation and used with Domain.Safe.spawn in the tests.
The stock interface remains ordinary OCaml syntax. The checked interface is
currently selected by the qualification runner, not the production build.
The existing SemanticWorkers pool is not yet switched to this component.

An immutable snapshot contains front/back lists, count and closed state. Push,
pop and close linearize at a successful CAS; every state update constructs a
fresh snapshot, rather than mutating or republishing old snapshots. Normal FIFO
order follows successful enqueue CAS order. Capacity1..65536 bounds accepted
messages; Full performs no enqueue. Close rejects future pushes but preserves
already accepted messages for draining. Empty means open/empty, Drained means
closed/empty. Usage reads one coherent snapshot and may immediately become old.
Pop allocates its reply envelope before the winning CAS so that allocating a
reply cannot remove an item without returning it. No application callback is
invoked during a queue update.

The queue is nonblocking: callers choose their wake/retry policy. The CAS loop
has no starvation/fairness or hard elapsed-time guarantee; array-free state
avoids mutable shared slots but can allocate under contention. Message capacity
is not a byte/RSS/descriptor bound, and outstanding snapshots may remain live
in concurrent callers. Payload ownership, CPU admission, notifications, shutdown,
file-descriptor lifetime, native operations and job settlement remain outside
this component. In particular, sending a descriptor value does not grant static
exclusive ownership of the referenced kernel file description.

Qualification passes12,000 messages per compiler using two producers and three
consumers with a31-message input capacity, plus FIFO/reversal/full/drain/invalid
capacity and producer/close race controls. Results check unique IDs, exact packet
checksums, cancellation atoms, descriptor carriers and settled counts. OxCaml
uses the checked template and Safe.spawn; stock uses ordinary spawn for the
same runtime test. Mutable ref and bytes payload access in the checked domain
closures must fail compilation. Initial mode-inference failures were fixed by
explicit immutable job/result and integer annotations, without casts or alert
suppression. Domain's separate scheduler-mixing alert remains visible.

[Retained qualification](../tests/checked_mailbox/qualification.json) pins source,
actual selected interfaces, compiler/binaries/logs, and fresh Make/Dune CLI plus
selftest snapshots. This is root-owned component evidence, not qualification of
the full production worker boundary. The next integration must mode-check
selected extension/native execution interfaces and replace the domain-visible
queue/counter state while preserving the sole Lwt owner, shared CPU permits,
notification settlement and legacy stock compatibility. No Photo/Adobe/native
preview work was performed.
