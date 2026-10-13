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

`SemanticAdmission` separately limits complete production transactions before
they open descriptors or clone a candidate. `semanticmaxinflight = 0` selects
the worker count plus one reserved source slot when a semantic profile is
enabled. `semanticpayloadbudget` defaults to 512 MiB of estimated retained
buffer credits; `semanticdescriptorbudget` defaults to 512 descriptor credits.
A transfer reserves eight times the largest enabled profile's declared payload
limit plus 256 KiB, and eight descriptors. DNG declares a 1 MiB payload limit;
the core enforces it before copying packet contents. A validation operation
reserves 1 MiB and eight descriptor credits. CPU permits are acquired by nested
workers/helpers, so a transaction never holds a CPU permit while waiting for
its own workers to obtain one.

Consumers preserve one worst-profile source reservation. Sources have a
separate FIFO and admission priority, allowing both endpoints to serve requests
while their receivers wait for the peer. Source leases cover response encoding,
marshaling and queued output consumption. Per-request RPC body limits also use
the selected profile's payload ceiling. Cancellation removes queued requests;
active leases remain until their operations settle. Connection teardown fails
queued output and outstanding replies, and closes pending I/O before descriptor
reuse. These credits bound admitted work, not process RSS, parser allocations,
directory manifest size, external SDK memory, per-volume I/O or unrelated
legacy transfers. Those constraints still need separate implementation.

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
