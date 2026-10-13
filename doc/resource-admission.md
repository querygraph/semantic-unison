# Retained publication admission

A receiving endpoint acquires one durable Consumer reservation before preparing
its native target proof. `TargetBinding` owns that reservation through Ready,
Producing, Finalized and Committing. Producer return releases staging and worker
resources but keeps the target's four directory handles and candidate witness
charged. Commit, abort and explicit release close native ownership before
retiring the reservation. A legacy handoff closes the proof immediately and
retains the work envelope until the current producer or commit callback settles.

The selected envelope reserves 24 descriptor credits and the larger of 1 MiB or
`8 * enabled_profile_payload_limit + 256 KiB`. The descriptor allowance covers
selected regular-file preparation, clone, paired inspection, materialization,
publication and serialized validator phases. It is conservative planning
accounting, not an exact native descriptor count or a whole-process ceiling.
The prior source inventory is preserved in
[resource-lifetime-inventory.md](resource-lifetime-inventory.md), pinned to its
inspected pre-admission checkpoint. That inventory identifies a local bound
semantic phase with 15 explicit descriptors and an idle Finalized proof with five.

Copy passes the local reservation explicitly into semantic materializers.
`SemanticAdmission.with_borrow` loans one workspace without another transaction
debit or an upgrade wait. Parallel inspectors operate inside that workspace's
upfront envelope. Validation borrows the same envelope and processes a bound
tree serially, including an explicit legacy directory handoff. Unbound validation
keeps its separate per-file admission. Overlapping, revoked and oversized loans
fail before dispatch; they cannot silently create another gate waiter.

Sources use their independent eight-credit reservation through proof/response
encoding, marshaling and queued output consumption. Source requests have their
own FIFO and admission priority. Consumers always leave one source slot and the
declared source cost available; this remains conservative while a source is
already active. Requests exceeding the declared Source envelope fail before
admission. With an enabled DNG profile, the minimum configuration is two
transaction slots, 32 descriptor credits and enough buffer credits for a
consumer plus a source (17 MiB covers the built-in 1 MiB profile).

The resource gate is initialized separately from the worker pool. Ordinary
negotiated target preparation can reserve its proof without spawning domains or
opening the pool's notification pipe. CPU permits and filesystem execution
credits remain independent: work waits for resources, then filesystem execution,
then a domain slot and CPU permits. No CPU permit spans a transaction's peer RPC
wait or an attempt to acquire its own worker permits.

Reservations are caller-owned before debit. Acquisition, retirement and borrowing
are single-use or idempotent as appropriate. Retirement revokes new borrowing;
an active workspace keeps its credits until settlement. Pending retirement
revokes eligibility and pending accounting without allocating a replacement
queue. Later requests and the deferred pump compact tombstones. The pump grants
and debits before notifying the observer, using a preallocated result state via
`Lwt.wakeup_from`. A finite scheduling allocation failure resets its latch and
retries once. Producer/commit recovery runs before new admission, so a settled
orphan cannot own the last envelope while its recovery waits behind that envelope.

Preparation records its native owner inside the native cleanup guard before
returning a token. An immediate or asynchronous failure of the surrounding
cancellation/result wrapper closes that owner before retiring its reservation.
Worker/channel/pool initialization and helper spawn have separate early ownership
guards; their retained qualification artifacts specify their exact tested fault
boundaries. Persistent allocator exhaustion and arbitrary failures after worker
queue transfer remain outside those recoverability claims.

The following remain required before describing this as complete resource control:

- A census of native transient allocation peaks and all legacy families,
  including uncertain OS close/reap settlement.
- Pool, transport, archive and ordinary-operation baselines, operating-system
  descriptor limits, mount incarnation and cross-process attribution.
- Admission for incoming raw/decoded RPC arguments before allocation, parser
  expansion, directory manifests, native/child allocations and measured RSS.
- Broader post-dispatch allocation/cancellation stress and lifecycle recovery.

Buffer credits estimate retained proof/codec work. They do not bound the OCaml
heap, XML AST, process RSS, native stack, SDK child memory or directory manifest.
Two persistent worker notification descriptors and unrelated transport/legacy
handles are outside the transaction envelope. Physical block writes/sharing and
elapsed performance require separate evidence. All qualification for this slice
uses synthetic files and private temporary directories; no Adobe or Photo
invocation is needed.
