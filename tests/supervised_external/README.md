Private SDK-free controls for actual `SupervisedExternal`, helper/worker CPU
sharing and real Unison external copy/merge workflows. No photograph, preview,
catalog, native UI, Adobe executable or production data is used.

`run.py` links the compiler-matched full source graph through the new bridge.
Fourteen cases cover preserved argv[0]/literal arguments/environment, shell
formatting and nonzero exit policy, invalid/missing invocation, CPU weight,
timeout, both output streams, signals, active/queued cancellation and actual
worker admission behind an all-CPU helper. The helper-only owner and subsequent
worker runtime must be the same object. Direct helpers are independently
observed reaped, and CPU/child/worker ledgers settle. Normal controls use a
ten-second deadline; the deliberate timeout remains one second. Retained
one-second startup failures are distinct from the final qualification.

`copy_status.py` runs actual client/server CLI transport with a synthetic
external copier that fully writes its candidate. Success publishes exact
bytes. Exit 7, timeout and output overflow must reject and preserve destination
absence plus independent existing sibling bytes. The genuine previous binary
negative must actually publish after exit 7. External-copy selection is the
new-file `Copy` branch; an update fixture would test the ordinary copier instead.
That first fixture failure is preserved rather than counted as qualification.

Existing receiving-path tests cover real copy/merge, resumed and hint-reused
candidates plus SDK-style validation/cancellation policies. Existing helper
ownership and returned-work tests exercise descriptor/PID/permit faults.
Native syscall and promise observation hooks in those suites remain private.

```sh
python3 tests/supervised_external/run.py --build /private/path/snapshot \
  --ocamlopt /absolute/ocamlopt --receipt /private/path/helpers.json
python3 tests/supervised_external/copy_status.py --unison /private/path/unison \
  --parent /private/path/previous-unison --receipt /private/path/copy.json
```

Current evidence is root-owned, not a new independent-agent review. Declared
CPU weights do not constrain unknown internal parallelism; Windows, child
memory/global FD limits, actual SDK/corpus and broader M4-V/M5/M6 work remain
open. No benchmark or machine-wide quota is inferred.
