This finite macOS suite compiles the actual helper supervisor and vendored Lwt
in retained private directories. It uses a photographic-data-free child that
sleeps at most 0.3 seconds, or exits after 0.03 seconds. No Adobe invocation,
catalog, preview, Photo path or production fault hook is involved.

```sh
python3 tests/helper_ownership/run.py --ocamlopt /usr/local/bin/ocamlopt
python3 tests/helper_ownership/run.py --ocamlopt /Users/alexy/.opam/5.2.0+ox/bin/ocamlopt
python3 tests/helper_ownership/run.py --ocamlopt /absolute/compiler --negative missing-guard
python3 tests/helper_ownership/run.py --ocamlopt /absolute/compiler --negative early-release
python3 tests/helper_ownership/run.py --ocamlopt /absolute/compiler --negative missing-outer-guard
python3 tests/helper_ownership/run.py --ocamlopt /absolute/compiler --negative early-cpu-release
```

The positive matrix has 36 cases per compiler. Private ML
source copies inject one-shot allocation errors before ownership creation,
after each pipe handoff, after spawn/PID storage, after writer closure, before
and after cleanup registration, during an asynchronous monitor, after native
reaping, and while building a result. Two additional cases inject a secondary
error after reaping or during failure-result construction and require the
original error to survive. A private callback-installation fault executes after
the monitor has returned a pending promise, and another covers the outer `run`
waiter after `execute` returned that active monitor. A close fault reuses the just-closed
FD and confirms that subsequent cleanup preserves the fixture-owned replacement.

The matrix also covers preallocated permit replies/controllers, queued cleanup
registration, queue cell construction, admission activation and CPU-only callback
waiter installation. A pending CPU borrower keeps its credits through actual
settlement after a callback-installation error. Reentrant publication retains
unique ticket identities and pending capacity; cancellation during registration
must not publish a revoked ticket. Two queued-grant faults fail during later
removal/unregistration and require subsequent fresh admission to progress. Two
outer queued-waiter faults revoke the private acquisition and require that it
never debit or spawn later, while preserving another running borrower. The queue tests use cooperative finite
callbacks and do not claim universal allocator or signal-handler reentrancy.

A C wrapper records the actual immediate spawn PID without allocating or
calling ML after native spawn. Private ML wrappers record successful direct-child
waits and inspect the real CPU/child budget before waiting. Acceptance requires
an actual recorded reap plus ECHILD, matching before/after descriptors 0..255,
zero final permits and harmless repeated teardown. PID absence alone is never
reap evidence. The four private regressions separately omit inner or outer
exceptional settlement, retire permits before child wait, or retire CPU credits before a running borrower settles; each must fail its
designated assertion.
The test owns and settles a failed negative's direct child through a WNOWAIT
ownership check before propagating failure. Every child is finite even if the
test controller itself is interrupted; failed or timed-out executions cannot
become accepted evidence.

The runner retains source copies, private mutations, exact compiler commands,
compiler configuration, native observation object, binaries and logs beside
`verification.json`. The qualification receipt combines both compiler runs and
their designated negative controls. These are source-directed fault injections,
not a real exhausted-heap experiment or an independent process RSS/FD cap.
The existing 33 helper/validation groups additionally exercise cancellation,
deadline escalation, connection cleanup, descendants and process-exit cleanup.
Unexpected OS refusal, uninterruptible reaping, an external competing reaper,
escaped helper descendants and universal allocation failure remain separate
limitations; this suite does not establish a hard settlement deadline.
