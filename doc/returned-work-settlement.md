# Returned worker settlement

The receiving/reporting continuation is qualified on stock OCaml 5.5.1 and
OxCaml 5.2.0+ox against 331 frozen source/package inputs. It adds 98 focused
positive cases per compiler, alongside fourteen designated negative controls
with distinct parent/mutation provenance. The earlier 39-case worker checkpoint
below retains its original receipt; it is not a claim that those historical
executions used this later source. Current results are bound in the
[integration receipt](../tests/qualification/validation-report-settlement-integration-20261013.json).
[Independent acceptance](../tests/qualification/validation-report-settlement-independent-review-20261013.json)
records the final source and evidence audit separately.

A returned asynchronous operation still owns resources until its actual work
stops. An error while observing its promise must not masquerade as completed
work. At parent `9fbfc00`, two failed CPU waiter installations reported failure
while a dispatched worker still owned two descriptors. The CPU reservation
remained held, but surrounding worker slots, filesystem credits and resource
workspaces could retire. A later consumer could then enter the released envelope.

`BorrowedWork.try_bind` protects the returned promise at each ownership and
mapping boundary. Its state, error storage and callbacks are allocated before
invoking the work. It records the returned promise without allocation. If
observer installation fails, it preserves that first error and tries one
recovery observer. If that also fails, the owner polls the returned promise
through 10 ms timers. Cleanup receives the original error only after the promise
settles, including when the work itself later fails or is cancelled. The drain
does not attach another observer to the borrower or run a nested event loop.

Finite polling setup failures retry inside the drain. Cancellation listeners,
the worker's atomic cancellation flag, queue ownership and reservations stay
live. Workers close their own duplicated descriptors before sending a response;
only the owner processes responses and retires reservations. Ordinary completion
does not poll or take an extra timer turn.

Intermediate mappings require the same protection: an unguarded mapping could
produce an already-failed wrapper around a still-sleeping inner operation. An
outer guard would then observe the wrapper rather than the actual work.

`BorrowedWork.bind` and `catch` accept work thunks so protection is prepared
before launch. `all` allocates a ledger before launching participants, records
each returned promise without allocation, and drains every launched participant
after a later launch or observer failure. It never retries a work thunk. A
preallocated error hook stops further directory consumption on the first
observed error; join order does not claim chronological completion order.

The added scopes cover Runtime cancellation/admission/I/O, retained loans,
receiving companion recognition and validation, sequential candidate fences,
directory consumers, local/remote reports and semantic producers, and the
selected Copy/Files/TargetBinding publication owners. DNG validation records
that execution was attempted independently of its child receipt. After a
returned execution settles, candidate/tool checks still run under warn even
when an observer failure prevented capture of the child result. This flag is
not evidence that a PID was spawned.

RPC guards extend through server result marshalling, command/scope wrappers and
actual output write/fill/flush promises. Once reply output starts, failure never
adds an exception packet to its prefix. Output-action settlement establishes
buffer/source lifetime, not peer delivery or completion of detached tail
flushing. The scoped socket-pair fixture's oversized preallocated answer proves
temporal retention only; its tiny profile cost does not bound that answer's
memory. Input/handshake scheduling remains separate.

| Captured boundary | Returned work that must settle |
| --- | --- |
| CPU reservation | Raw worker reply |
| Worker CPU-result mapping | CPU wrapper |
| Filesystem reservation | Worker execution |
| Worker filesystem-result mapping | Filesystem wrapper |
| Submission cleanup | Admitted execution |
| Public Identify response mapping | Submission |

The same guarded public response mapping is used for digest, inspection,
observation and application. I/O release prepares its new ledger before marking
ownership retired; that mark precedes accounting publication and any throwing
deferred-dispatch setup. A later error cannot debit that reservation twice.

Both stock OCaml and OxCaml pass 39 focused cases using an actual one-domain
Identify callback paused on an Atomic barrier. A kernel FD census, private slot
count and separate CPU, filesystem, pending-job and retained-workspace ledgers
observe the live borrower. Retirement/cancellation cannot release those ledgers
or admit the next consumer/same-device callback early. Owner timers continue,
the first setup error survives, subsequent digest reuse is exact and shutdown
closes the descriptors.

The controls cover six captured boundaries, underlying success/failure/
cancellation, initial CPU/I/O waiting, and two injected failures before polling
sleep creation. Three no-fault controls retain ordinary outcomes. Private parent
participants compiled from the actual CPU/I/O/worker source bodies fail the
designated independent live-FD/admission oracle. See [focused controls](../tests/worker_settlement/README.md)
and [their receipt](../tests/worker_settlement/qualification-20261013.json).

Stock/OxCaml Make and clean Dune builds/selftests match 331 production/package/
INSTALL inputs. Each compiler also passes 27 complete worker groups, 37 helper
groups, 20 I/O groups with its fairness negative, 36 helper ownership groups /
211 assertions with an early-CPU-release negative, 20 descriptor ownership
cases / 110 assertions, 21 receiving-validation and 79 Files publication cases.
These tests use synthetic private files and Adobe-free helpers. The
[integration receipt](../tests/qualification/worker-settlement-integration-20261013.json)
binds these source/build/test artifacts; [independent acceptance](../tests/qualification/worker-settlement-independent-review-20261013.json)
records its separate read-only audit.

The new [validation controls](../tests/validation_settlement/README.md) pass
28 standalone cases / 422 explicit assertions and three actual Files/directory
receiving cases per compiler. Standalone controls use real gated synthetic
children and native PID/reaping evidence, including late mutations with no
captured receipt. Receiving controls pause actual Identify domains with owned
descriptors; they preserve live bytes/inodes and typed archived byte
fingerprints, then verify exact retry. Raw archive-container identity is
observed separately. A proposed full-CLI child-ready barrier was removed
because execution can return queued I/O before dispatch; its blocking observer
would prevent that dispatch. No owner-loop pumping substitutes for it.

The new [Runtime/report controls](../tests/runtime_settlement/README.md) pass
67 positive cases per compiler. Atomic-paused domains, FD census, independent
resource ledgers and actual scoped RPC output expose early retirement. Parent
owner negatives restore exact selected `2059949` participants while retaining
current support APIs; group negatives are private mutations. They are not full
parent binaries. Actual receiving parent controls separately use complete
compiler-matched parent production inputs. All designated negative provenance
and retained fixture corrections are explicit in the component receipts.

Current stock/Ox Make and clean Dune builds/selftests match 331 inputs across
five source sets. Both compilers also pass the existing worker/helper/I/O,
receiving/publication, local/remote semantic transfer and report, bounds,
reconnect, UI detail and producer-handoff suites. No performance improvement,
Adobe fidelity or preview-native qualification follows from these tests.

The guarantee concerns finite observer setup failures after work returns its
actual promise. It does not cover independent work dispatched before a callback
throws without returning that promise, persistent allocation refusal, arbitrary
asynchronous exceptions or delayed legacy `Lwt.connect` failures. Pre-return
admission/dispatcher setup and recovery liveness require separate qualification;
the existing I/O scheduled-latch hazard remains open. Legacy transfer internals,
External/region schedulers, general recursive Files orchestration, Runtime
watchdog timers and TargetBinding preparation retain separate ordinary maps.
The owner loop must run,
and work which cannot stop has no settlement deadline. This establishes neither
a complete process FD/RSS cap, compiler-checked portability, physical storage
savings nor a performance improvement. Photo/Adobe invocation and preview
renderer/publisher admission are unchanged.
