# Filesystem I/O admission qualification

`IoAdmission` limits active endpoint-local jobs per filesystem accounting key.
Workers/helpers acquire this lease before CPU admission and retain it until all
borrowers settle. One job atomically reserves one credit on each of at most two
distinct devices. Earlier blocked key sets bar later conflicting work while
allowing disjoint-device work to proceed. Release and cancellation defer starts
until an owner yield; active cancellation cannot free a still-borrowed lease.

The tests exercise actual borrowed file descriptors, shared CPU permits, queue
bounds, AB/BA requests, conflict fairness, disjoint bypass, deferred cleanup,
callback/observer failures, cancellation reentrancy, exactly-once settlement and
removal of idle accounting entries. A private negative control removes the
older-conflict barrier and must fail the designated starvation regression.

Run each compiler in a private build:

```sh
python3 tests/io_admission/run.py --ocamlopt /usr/local/bin/ocamlopt --keep --receipt /private/tmp/io-admission-stock.json
python3 tests/io_admission/run.py --ocamlopt /Users/alexy/.opam/5.2.0+ox/bin/ocamlopt --keep --receipt /private/tmp/io-admission-ox.json
```

The receipts pin compiler, source, binaries and logs. The standalone suite is
Adobe-free and uses disposable synthetic files only. It does not prove two
physical-volume throughput, native mount-lifetime identity, memory/descriptor
ceilings, IO byte/rate limits or hostile pathname isolation. `st_dev` groups
filesystems, so APFS volumes sharing one backing device can still contend.

`runtime_run.py` links the actual `SemanticRuntime` and registered preferences
from a complete compiler-matched private Make snapshot. It does not recreate
the preference or execute a validator. Each scenario uses its own process to
respect frozen runtime budgets. It checks outgoing omission, malformed incoming
RPC 999 isolation, `endpoint.prf`, CLI precedence, default-zero CPU-budget
selection and negative-setting rejection. Actual held-candidate checks cover
success, exceptions, queued/active cancellation, exact descriptor settlement,
FIFO/directory/missing-path rejection and unchanged bytes.

```sh
python3 tests/io_admission/runtime_run.py --build /absolute/private/make-snapshot --ocamlopt /absolute/matched/compiler/bin/ocamlopt --keep --receipt /private/tmp/io-runtime.json
```

A private source copy injects synchronous `Out_of_memory` immediately after
opening the candidate, before creating its close closure. The production outer
guard must close that descriptor; independently removing only the guard must
fail the leak assertion. This tests that allocation handoff, without causing
actual memory exhaustion or claiming arbitrary asynchronous-exception safety.
Six positive runtime scenarios pass 107 assertions per compiler. The runtime
receipt pins production source, every linked object, binaries, logs and both
private mutations; `runtime-qualification-20261013.json` combines both compilers.

A separate [registration fault control](../qualification/io-registration-publication-actual-20261016.json)
checks that cancellation observer registration completes before queue publication.
One injected registration exception must leave no pending ticket or later debit;
immediate cancellation during registration must not publish a revoked request.
The earlier implementation fails the unreachable-ticket assertion. Run
`registration_fault_test.py --compiler /absolute/ocamlopt --report /fresh/result.json`
in the standing CPU lane; no physical IO lane or photo input is involved.
