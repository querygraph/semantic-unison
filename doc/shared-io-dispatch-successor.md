# Opt-in shared-dispatch IO successor

This source successor connects the accepted existing-only EX_GLOBAL backend to
`tests/shared_dispatch.py`. It is not a live bulk-job grant or production-Unison
IO integration. The canonical lock-only probe passed separately; this new job
integration has only mock admission/refusal coverage so far.

Default shared commands remain CPU-only. IO is requested only with BOTH
`SHARED_IO_ADMISSION=/absolute/root-receipt.json` and
`SHARED_IO_ADMISSION_SHA256=<exact externally supplied SHA256>`, alongside
`SHARED_CPU_CREDITS`. Only `inspect-file` and `private-dng-local-clone` are
supported: complete local jobs in a single containing group. Transport sync,
builds, SDK/helper and distributed endpoint phases refuse this IO mode.

The Root receipt must have state `ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB` and
bind `target`, exact child `command` argv, fresh absolute `workspace`,
`cpu_credits`, current pinned `io_manifest_sha256`, `start_deadline_unix`, and
`execution_source_sha256`. The latter must equal the exact current source set
calculated by `checked_io_request`, including owner/manual/IO/CPU/settlement/
ownership and selected runner. No caller-selected subset is accepted.

The owner validates metadata before locks, writes an exclusive one-attempt marker,
and calls the backend's IO→CPU nonblocking bundle acquisition. Contention closes
all known partial descriptions and stops; no automatic wait/retry. It rechecks
admission/source/deadline before launch; known refusal before any child closes
the bundle. Unknown-close carriers retain live ownership with all recorded
uncertainties and prohibit numeric descriptor retries.

Both IO and CPU descriptions are inherited by the containing worker. The parent
retains its copies through actual group census/reap and the target's existing
settlement checks. It closes CPU then IO only after those proofs. START/CLOSED
receipts distinguish IO from CPU-only operation; unknown evidence includes
retained IO FDs and every structured uncertain-close record. Close functions
consume caller proofs; they do not independently establish child closure.

No job with this mode has been admitted or executed. Before a first live job,
prepare the complete fresh pinned Root request and qualify mocked lifecycle/
settlement ordering plus a finite separately coordinated live synthetic job.
The current mock tests cover source/admission/target/deadline refusals and
unchanged default selection only; they do NOT cover the whole new lifecycle.
Existing native/UI lease acquisition, physical-member discovery, general
production dispatchers, whole-process hard resource limits, and simultaneous
cross-project payload qualification remain separate. No Photo payload or SDK
rights follow from CPU grants or an accepted lock-only probe.

## Fake full-lifecycle controls and reporting-failure correction

Thirteen [fake lease/owner lifecycle controls](../tests/qualification/shared-io-dispatch-lifecycle-actual-20261016.json)
now pass, including acquisition order/rollback, FD inheritance and retention
through settlement, child-failure and settled-timeout release, and uncertain
closes. They found and fixed a reporting error: after resources are known
closed, a final receipt-write failure now propagates as an error rather than
claiming live ownership. Uncertain process/FD outcomes still retain ownership.
This correction also applies to CPU-only reporting failures. Records now include
known-open CPU FDs alongside IO FDs and structured uncertainty identities.
No actual IO or test children were used in these controls.

A [separate tiny live-job request](shared-io-local-job-request-v1.json) freezes the
new owner and existing24-CLI synthetic local-clone child. It is NOT the already
completed canonical probe and is NOT admitted. Before dispatch, Root must
coordinate the new job and publish the exact admission; compiled binary/receipt
pins are independently revalidated by the dispatching operator as specified.
