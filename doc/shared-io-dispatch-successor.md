# Opt-in shared-dispatch IO successor

This source successor connects the accepted existing-only EX_GLOBAL backend to
`tests/shared_dispatch.py`. It is not a live bulk-job grant or production-Unison
IO integration. The canonical lock-only probe passed separately; this new job
integration now has one accepted tiny synthetic local-job execution, described below.

Default shared commands remain CPU-only. IO is requested only with BOTH
`SHARED_IO_ADMISSION=/absolute/root-receipt.json` and
`SHARED_IO_ADMISSION_SHA256=<exact externally supplied SHA256>`, alongside
`SHARED_CPU_CREDITS`. Supported targets are `inspect-file`,
`private-dng-local-clone`, `private-dng-framing-input`, and the exact finite
`sync-functional` matrix. Builds and SDK/helper phases refuse this IO mode.
The framing route binds its bounded clone-read executor separately. Sync also
requires stock/Ox binary/compiler hashes checked inside the IO-owned worker,
and separate client/supervisor/server/pump closure proofs before release.

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

The first tiny synthetic local job has now passed, after mocked full-lifecycle
controls. This does not authorize any additional job or broaden the supported
targets. The initial four mock tests covered source/admission/target/deadline
refusals and unchanged default selection; later lifecycle controls and the
scoped actual execution provide the additional evidence below.
Existing native/UI lease acquisition, physical-member discovery, general
production dispatchers, whole-process hard resource limits, and simultaneous
cross-project payload qualification remain separate. No Photo payload or SDK
rights follow from CPU grants or an accepted lock-only probe.

The [actual shared sync receipt](../tests/qualification/shared-sync-io-actual-20261016.json)
covers the admitted generated18-row/54-call matrix under its historical source
pins. The new [property-removal request](shared-property-io-request-v1.json)
adds native fork/named xattr removal, selected readonly mode, retained readers
and unchanged no-op property epochs. It is source-prepared, not admitted by the
earlier sync receipt. A pending request is not permission to execute it.

For failed sync results, the invocation journal must account for every attempted
call before the aggregate worker is reaped. A known settled prefix can release
resources after actual nonzero worker settlement without implying a functional
pass. Missing outcomes, server proofs, or uncertain FDs retain ownership.
[Actual Python-peer dispatcher controls](../tests/qualification/failed-sync-dispatch-peer-actual-20261016.json)
cover this path with disposable inner leases; they do not authorize new payload
IO or substitute for actual property receiving.

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
completed canonical probe. Root admission `cc06492f` was consumed once.
The [actual receipt](../tests/qualification/shared-io-local-job-actual-20261016.json)
records owner86809/session5692 terminal49da7c/exit0/no session, worker86810
reaped0/other group members absent, all8cases/24CLI waits0 and log hashes checked.
IO and CPU00..07 were closed and execution source pins stayed unchanged. Root
independently accepted the runtime terminal event. Local whole-source cloning
precedes semantic inspection here: receiver-basis semantic fallback is not
qualified by this job. No camera/SDK/Adobe input, production integration, topology
independence, OS-thread or RSS hard cap is inferred. Any further IO job needs
its own coordination; the original request and admission remain immutable.
