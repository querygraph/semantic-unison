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
tree serially, including an explicit legacy directory handoff. Content
recognition, its conditional full hash and sequential selected validator
callbacks retain one 1 MiB / nine-descriptor loan. The recognition input closes
before helper execution; execution alone borrows the filesystem gate. Unbound
validation keeps its separate per-file admission. Overlapping, revoked and oversized loans
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
boundaries. The returned-work continuation adds `BorrowedWork.try_bind` to CPU,
filesystem, worker submit and response-mapping ownership layers. It preserves
the first observer-installation error while draining the actual sleeping
borrower before cleanup. A second failed observer installation uses owner-loop
polling; no nested event-loop run is needed. Both compilers pass 39 focused
actual-domain cases with retained workspace, slot, CPU, filesystem and live-FD
oracles, including cancellation and queued work; a private parent participant fails
the designated early-retirement oracle. The [settlement contract](returned-work-settlement.md)
and [integration receipt](../tests/qualification/worker-settlement-integration-20261013.json)
record exact execution and separate independent acceptance.
Persistent allocator exhaustion, callback-time
legacy promise connections, pre-return admission failures and independent work
which throws before returning its promise remain outside this contract.

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

## Selected owner-loop progress and registration repairs

A [grant-observer control](../tests/qualification/admission-grant-observer-progress-actual-20261016.json)
found that a throwing queued SemanticAdmission reply observer could leave a ready
sibling asleep. Dispatch now continues draining ready owners before propagating
the first observer error. The already-published grant is preserved. Stock/Ox
finite fault suites and complete CLI builds/selftests pass at that source snapshot.

A separate [IO registration control](../tests/qualification/io-registration-publication-actual-20261016.json)
found queue publication before cancellation-observer registration. A failed
registration could leave an unreachable ticket that later acquired credits.
Queue-cell allocation now precedes registration, and publication occurs only
after registration succeeds while the ticket is still waiting. One injected
registration failure and immediate cancellation pass on both compilers, as do
the ordinary20-group IO suite and fairness negative control. These selected
pre-return failures no longer fall under the broad historical exclusion above;
other allocation/OS-ownership boundaries retain their stated limitations.

The [subsequent full CLI check](../tests/qualification/io-registration-full-cli-actual-20261016.json)
rebuilds current stock/Ox Make applications and runs their bounded selftests after
the IO registration repair. Both actual parents exit0 with groups and CPU tokens
closed. Dune receipts remain their historical source snapshots.

## Machine-integer accounting boundaries

The [current stock/Ox admission suite](../tests/qualification/admission-integer-boundaries-actual-20261016.json)
passes28 groups/compiler, including maximal machine-integer payload/descriptor
budgets. A full `max_int` reservation blocks a positive sibling without wrapping
its ledger; cancellation removes that pending owner and retirement returns the
ledger to zero. `min_int` costs refuse before debit. A maximal valid source
headroom and its complementary consumer envelope sum exactly to the declared
budget, while headroom one unit above the half-budget bound refuses.

These use declared integer credits and sleeping promises, not massive allocations
or operating-system descriptor opens. They qualify accounting arithmetic and
owner transitions, not RSS, live FD peaks, physical IO or whole-process caps.
Both serial compiler/test groups and the canonical Unison8 owner closed normally;
no SDK, Photo payload or EXglobal IO was used. Production sources were unchanged.
