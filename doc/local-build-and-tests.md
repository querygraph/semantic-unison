# Local build and test commands

Run from the repository root. The installed stock compiler is in
`~/.opam/default/bin`; the qualified OxCaml compiler is in
`~/.opam/5.2.0+ox/bin`. Existing opam switches provide the dependencies; these
commands do not install packages or change your selected switch.

Build the complete text CLI with Make and run its self-tests:

```sh
python3 tests/build_snapshot.py --compiler-prefix "$HOME/.opam/5.2.0+ox/bin" \
  --jobs 4 --selftest --report /private/tmp/unison-make-ox.json
```

For Dune, add `--build-system dune`. For stock OCaml, replace the compiler
directory with `$HOME/.opam/default/bin`. Each command prints the executable
and preserves a private snapshot, build/self-test logs, and `build-receipt.json`
with source/compiler/binary hashes and actual outcomes. Omitting `--selftest`
builds without running the resulting CLI. This qualifies the text CLI/core,
not the macOS graphical application or every platform backend.

Independent deterministic codec checks:

```sh
python3 tests/semantic/conformance/run.py \
  --ocamlopt "$HOME/.opam/5.2.0+ox/bin/ocamlopt"
```

For C-helper ASan/UBSan checks, add `--sanitize address,undefined`. Add
`--build-only` to print the executable/input-manifest command without running
it. These use generated private inputs; no Adobe or photo catalog is involved.
The OCaml code/runtime itself remains unsanitized.

The [coverage test handoff](../tests/semantic/fuzz/README.md) gives the separately
selected experimental parser campaigns and their qualification limits.

For actual synchronization performance, use the existing
[complete-sync benchmark](../bench/sync/README.md), with the binary paths printed
by your Make builds. Start with `--prepare-only` to pin configuration without
creating fixtures or synchronizing. A same-host pair has two endpoint CPU
budgets: under the shared 18-credit allowance, use at most eight per endpoint.
Ordinary owner/transport work is outside that accounting. Coordinate a quiet
measurement window; synthetic warm-cache timings do not establish cold-storage,
network or Adobe performance.

For the finite SDK pilot's **synthetic lifecycle tests**, run:

```sh
python3 tests/adobe_native_deadline/phase_test.py --report /private/tmp/phase-result.json
```

This uses original Python processes only. [Additional actual-core/mock commands](../tests/adobe_native_deadline/README.md) use a qualified Make snapshot and its compiler; they invoke no SDK. Real SDK pilot invocation remains a separate coordinated Root slot, with the pinned v2 request and 300-second aggregate supervisor. A synthetic success provides no Adobe/Lightroom release.
