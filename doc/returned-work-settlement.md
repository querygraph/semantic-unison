# Returned worker settlement

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

The guarantee concerns finite observer setup failures after work returns its
actual promise. It does not cover independent work dispatched before a callback
throws without returning that promise, persistent allocation refusal, arbitrary
asynchronous exceptions or delayed legacy `Lwt.connect` failures. Pre-return
admission/dispatcher setup and recovery liveness require separate qualification;
the existing I/O scheduled-latch hazard remains open. The owner loop must run,
and work which cannot stop has no settlement deadline. This establishes neither
a complete process FD/RSS cap, compiler-checked portability, physical storage
savings nor a performance improvement. Photo/Adobe invocation and preview
renderer/publisher admission are unchanged.
