# Typed semantic workers

`SemanticWorkers` runs SHA-256 hashing, DNG proof inspection, and verified DNG
delta application on bounded OCaml domains. The
public API, helper scheduler, Lwt promises, cancellation monitoring, archives,
RPC, and completion callbacks stay on Unison's event-loop owner. A worker
receives owned descriptors, a typed operation with an immutable plan where
needed, an integer request ID, and an atomic cancellation flag. It returns
immutable digest/proof/stat data through a mutex
protected completion queue; a nonblocking pipe wakes the owner. Workers never
call an owner callback or wake an Lwt promise.

Create the pool lazily when the feature needs it, and share one
`HelperSupervisor.t` budget with external validators and other CPU work.
Production `semanticworkers = 0` uses physical cores on macOS (18 on the tested
host), with the available logical count as a fallback when topology is unknown
or on other platforms. An explicit positive budget, such as 36 on this host,
overrides automatic sizing. Worker domains are additionally capped by the
runtime recommended domain count; callers must not create independent pools
that bypass the shared budget. This implementation uses
`Domain.spawn`, so this feature currently requires OCaml 5 or the pinned
OxCaml 5.2.0+ox compiler. It is not a build-selected OCaml 4 fallback.

The worker boundary is manually audited and supports standard OCaml. The
pinned OxCaml compiler emits `unsafe_multidomain` and `do_not_spawn_domains`
alerts here; they are not suppressed. This is not a compiler-checked portable
boundary, and it must not be combined with an independent OxCaml Multicore
scheduler. A migration to the compiler-specific safe scheduler requires its
own boundary audit and interoperability tests.

The pool limits pending requests independently from running workers. Each
running operation holds one shared CPU permit until it has stopped and closed
its descriptors, including cancellation. The scheduler can reserve additional
weighted permits for a helper's internal threads.

`SemanticAdmission` reserves a durable Consumer envelope before native target
preparation. `TargetBinding` keeps it through producer return, source checking,
validation and commit/abort. Local/remote semantic work and bound validation
borrow that envelope explicitly; validation uses one serialized workspace instead
of trying to acquire another Consumer slot. Ordinary target admission does not
initialize worker domains. Legacy proof handoff retains its work credits until
the current borrowed callback settles.

`semanticmaxinflight = 0` selects the worker count plus one reserved Source slot
when a semantic profile is enabled. `semanticpayloadbudget` defaults to 512 MiB
of estimated buffer credits; `semanticdescriptorbudget` defaults to 512 credits.
Consumers reserve 24 descriptor credits and max(1 MiB, eight times the largest
enabled profile payload limit plus 256 KiB). Sources reserve eight descriptors
and their profile's buffer estimate through response marshaling/output settlement.
DNG declares and enforces a 1 MiB editable-payload limit. The minimum supported
DNG combination is two transaction slots and 32 descriptor credits; 17 MiB covers
its consumer plus reserved Source buffer costs. Bound validation borrows 1 MiB /
nine workspace credits within its already paid envelope. Unbound validation
reserves those independently. Worker/helper execution still acquires CPU permits
separately; no transaction waits for its own workers while holding CPU permits.

Source FIFO/priority and declared headroom preserve bidirectional service.
Queued cancellation revokes eligibility immediately, and active borrowing retains
credits until settlement. These are selected-path reservations, not a process
FD/RSS ceiling. Native transient peaks, complete legacy families, transport/pool
baselines, incoming decoded arguments, parser expansion, directory manifests and
external SDK memory require further policy and measurement. The architecture and
explicit remaining limits are in [resource-admission.md](resource-admission.md).

`IoAdmission` supplies a separate execution gate shared by production domain
jobs and validator helpers. `semanticvolumejobs = 0` defaults each filesystem
ceiling to the configured CPU budget; a positive value selects a smaller or
larger ceiling. The option is endpoint-local and can be set in `endpoint.prf`
independently on each host. The default preserves previous CPU concurrency;
no optimal storage limit is inferred from core count.

Fresh held-descriptor `fstat().st_dev` values group jobs on each endpoint.
Source and output keys are deduplicated and acquired atomically. One apply
on the same filesystem consumes one credit; a two-filesystem operation consumes
one on each. Earlier blocked requests retain priority for overlapping devices,
while unrelated devices can proceed. Jobs waiting for I/O hold neither domain
slots nor CPU credits. Worker leases settle after completion and duplicate
closure. Helper leases cover only the supervised child execution through
stop/reap/output closure; its pre/post hashing runs outside that lease.
No I/O lease spans RPC waits or the whole semantic transaction.

These keys are short-lived accounting groups, with no persistent capability
cache, mount-incarnation identity or physical-disk claim. Multiple APFS volumes
can share underlying storage. The integer key is qualified on this 64-bit
macOS host, where native `dev_t` fits; other platforms require corresponding
representation/runtime checks. Ordinary copy/clone system calls, SDK internal
allocations, untrusted helper pathname changes and unrelated programs are not
controlled by this gate. Real multi-storage throughput and memory bounds remain
separate acceptance work.

`digest` borrows the caller's descriptor until its promise settles and owns a
close-on-exec duplicate. The caller must not operate on that descriptor
concurrently: duplicated descriptors share a file position. The file must be
regular. Workers check cancellation every 64 KiB and compare device, inode,
kind, size, modification time, and change time before/after reading. Those
checks detect ordinary concurrent edits; they do not make a live file an
immutable snapshot. Use privately owned candidates/basis snapshots and retain
the synchronization commit checks. The returned SHA-256 is raw 32-byte data,
not a hexadecimal string.

`inspect` follows the same ownership rules and receives an immutable trusted
extension handle resolved by the owner, without consulting the mutable
extension registry. An unsupported format returns an explicit eligibility
reason. Its successful proof contains complete-file and protected-complement
hashes plus bounded editable metadata, and is immutable across the worker
boundary. Parser reads and full-file hashing use the same cancellation checks.

`apply` borrows both a basis descriptor and an output descriptor. Output
must be an exclusively owned staging file containing the exact basis bytes.
The worker checks both proofs before writing, rejects the same inode, patches
metadata in bounded writes, and verifies the resulting full target hash. The
explicit-extension apply function avoids registry access. The caller must
discard the stage on cancellation or failure, since it can be partly written.
Renaming, properties, archive updates, and conflict policy stay on the owner.
The older `inspect_dng`/`apply_dng` calls remain compatibility wrappers around
the same generic dispatch, with the built-in DNG handle.

`apply_report` returns immutable counters after the same complete verification.
Materialization compares verified old metadata with the target packet using
absolute 4 KiB windows, clips each window to its editable extent, skips identical
windows and coalesces adjacent changed windows. Each write is at most 64 KiB.
An unchanged packet issues no data writes. `logical_bytes_written` counts bytes
returned by actual write calls; `write_calls` counts attempts, including EINTR
retries. These describe application writes, not physical APFS block allocation
or crash durability. Existing `apply` APIs retain their unit results.

`None` means cancelled, and `Failed` reports worker/queue errors. Shutdown
rejects new jobs, cancels pending jobs without mutating caller cancellation
tokens, waits for their cleanup, joins the domains, and closes both notification
descriptors. Repeating shutdown returns the same completion promise.
Cancellation also synchronously sets the worker's atomic flag through the
helper token listener; it does not depend on a future owner-loop timer tick.
The owner releases CPU permits only after consuming the worker's completion.
An exception from a completion observer cannot discard sibling completions or
stop the persistent notification pump: all detached replies settle, the next
read is armed, and the first unhandled error is surfaced on an owner yield.
Expected terminal replies from an already disconnected RPC session are handled
within that session, so late work cannot fail a later socket client.

Run the isolated tests with either compiler:

```sh
python3 tests/workers/run.py --ocamlopt /usr/local/bin/ocamlopt
python3 tests/workers/run.py --ocamlopt /Users/alexy/.opam/5.2.0+ox/bin/ocamlopt
```

The test creates 36 actual domains and checks 72 concurrent digest jobs,
shared-budget admission, bounded queues, queued/active cancellation,
owner-loop responsiveness, file mutation, invalid descriptors, shutdown, and
descriptor cleanup. DNG tests compare sequential and worker proofs, check exact
materialization and stale/same-inode rejection, and cancel long inspection and
apply operations. Tests use only disposable files/build output. Native hash
stubs are linked as in production. This is correctness evidence, not a
throughput benchmark or a qualification of unrelated legacy C stubs for
concurrent execution. The separate [cached SHA benchmark](../bench/semantic/README.md)
records measured scaling, including 18 versus 36 workers.
