# Checked semantic worker mailbox component

`SemanticMailbox` is a bounded atomic FIFO for immutable worker messages. The
same implementation builds on stock OCaml5.5.1 and OxCaml5.2.0+ox. An explicit
[OxCaml interface template](../src/semanticMailbox.ox.mli.in) was compiled against
that unchanged implementation and used with Domain.Safe.spawn in the tests.
The stock interface remains ordinary OCaml syntax. Make and Dune now select
the checked interface for OxCaml; see [production selection](production-oxcaml-mode-selection.md).
SemanticWorkers now uses the component for both jobs and completions, with its
existing mutex/condition counters and manually audited execution boundary.
Stock builds retain the stock-compatible interface. The complete checked
worker execution/interface migration is now qualified by the later integration.

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

## Runtime pool integration

Both runtime mailboxes have capacity max_pending (1..65536; configured runtime4096). Outstanding completion receipts remain part of pending admission, so a completed worker cannot release capacity/CPU ownership before owner dispatch. Job ownership transfers only after Added. Failed handoff leaves controller-owned duplicates/reply registration for existing cleanup guards. Full/Closed on an internal completion push violates the pending-count invariant and is terminal, never a dropped-success receipt. Producers and condition waiters retain the same mutex protocol, preventing a signal between empty observation and sleeping. Constructor failure closes the jobs mailbox before joining; normal shutdown waits pending0, closes jobs, joins domains, closes completions and settles notification pipes.

[Runtime qualification](../tests/workers/mailbox-integration-qualification.json) includes seeded hash/inspection and apply races,39 post-dispatch settlement cases,21 FD acquisition/handoff cases with117 assertions,21 actual receiving paths and14 supervised helper controls per compiler. A paused-owner pressure test observes an actual completed result still queued with its CPU/transaction ownership, rejects another submission, then proves exact delivery, mailbox closure and descriptor settlement. Actual DNG/old-peer and mixed JPEG receiving controls pass. At that mailbox-only stage Safe.spawn substitution still rejected; the subsequent checked extension/counter integration resolves that compiler gate. Persistent allocation failures/foreign faults, fairness, full RSS/FD ceilings and performance qualification remain outside this finite evidence.

The subsequent [production worker integration](checked-semantic-worker.md)
now compiles the complete worker closure with Safe.spawn on OxCaml, including
checked extension execution and atomic counters. Earlier component receipts
remain historical; full native/resource/performance M6 requirements stay open.
