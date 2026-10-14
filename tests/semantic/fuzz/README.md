# Synthetic semantic parser test handoff

The target reads disposable inputs only. It exercises SDE/SDR canonical round
trips, DNG v0/v1 and JPEG inspection, and bounded XMP parsing. It never applies
a delta, writes a received file, invokes Adobe, or accesses a photo catalog.
Inputs above 256 KiB are skipped. Unexpected exceptions/invariant failures use
exit 86; ordinary parser rejection succeeds.

Build without executing the target or AFL:

```sh
python3 tests/semantic/fuzz/run.py --ocamlopt "$HOME/.opam/5.2.0+ox/bin/ocamlopt" --build-only
```

The command prints a retained `/private/tmp/unison-semantic-afl-*` workspace,
containing `target`, frozen compiler-selected source, build log and build pins.
Stock OCaml uses `$HOME/.opam/default/bin/ocamlopt` instead.

Run the existing deterministic independent codec suite:

```sh
python3 tests/semantic/conformance/run.py --ocamlopt "$HOME/.opam/5.2.0+ox/bin/ocamlopt"
```

For an explicitly chosen local coverage campaign, the prepared AFL binaries on
this machine are in `/private/tmp/unison-afl-tools-8okhh2ru/source`:

```sh
python3 tests/semantic/fuzz/run.py --ocamlopt "$HOME/.opam/5.2.0+ox/bin/ocamlopt" --afl-dir /private/tmp/unison-afl-tools-8okhh2ru/source --seconds 60
```

This runs six sequential campaigns and retains logs, inputs, queues, stats and
source/binary pins. A successful process exit alone does not prove the absence
of failures: inspect each `*-output/default/crashes`, `hangs` and `fuzzer_stats`.
The runner rejects nonzero AFL exits, missing statistics and saved crash/hang
files. Failure-discovery controls remain unqualified. This is an experimental
harness, not a release gate.

The tools are AFL++ commit `dbaf11913c1b2702dee5b4d3dcfffd52f1defe50`,
with the committed `afl-ocaml-macos.patch`: use System V shared memory and a
64 KiB initial coverage map to match OCaml. To reproduce the tool build, check
out that commit in a private AFL++ clone, apply the patch with `git apply --unidiff-zero`, and
run `make -j2 afl-fuzz afl-showmap NO_PYTHON=1`. No system setting changes are
needed. The macOS crash reporter remains enabled; signal-crash timing is
unqualified. OCaml coverage does not instrument the C helpers, and no sanitizer
result is claimed. Failure-oracle controls, sustained campaigns and broader
input limits remain outstanding.

`preliminary-probe.json` preserves the stock-only five-second SDE probe:
907 executions, 13 new corpus entries, 123 coverage edges, no saved crashes or
hangs. This is preliminary evidence, not full parser or OxCaml qualification.
Further automated campaigns were deferred after the user reported service-side
access interruptions. Local execution does not change service access permissions.
