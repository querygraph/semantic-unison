# Building the CLI with pinned OxCaml

The CLI can be built with the `5.2.0+ox` compiler while retaining a standard
OCaml 5 build. The compatibility changes eta-expand standard-library aliases;
they do not change interfaces or archives. The semantic extension adds
separately negotiated capabilities while retaining ordinary peer fallback.

## OxCaml without semantic hashing

OxCaml is a build/compiler choice for the full Unison CLI, independent of
runtime semantic features. Ordinary sync and general receiver-basis APFS
cloning are usable with the default semantic profiles and Adobe validation
disabled. Semantic hashing is not needed to use the OxCaml build. The full
binary still contains the optional feature modules; there is no separate
minimal binary or extracted upstream OxCaml-only PR in this fork.

The checked worker framework accelerates selected hashing/inspection/apply and
validation work. The legacy RPC, archive, UI and synchronization owners remain
single-threaded. Neither a successful OxCaml build nor the SDK-enabled receiving
comparison proves that ordinary sync is faster because of the compiler alone.
Keep semantic features, cloning and validation explicit in any matched benchmark.

## Current build evidence and shared-machine entry point

The latest [Make build/selftest pair](../tests/qualification/external-process-full-cli-actual-20261016.json)
uses stock OCaml5.2.0 and OxCaml5.2.0+ox. Both full CLI builds/selftests pass on
current production sources at that receipt. Earlier5.5.1 qualification below
retains its historical snapshot; it is not the current default switch version.

On this shared host, prefer the owned entry point with an unused output path:

```sh
SHARED_CPU_CREDITS=8 OX_PREFIX=/Users/alexy/.opam/5.2.0+ox/bin \
  OUTPUT_DIR=/private/tmp/unison-ox-check-UNUSED-NONCE \
  /Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14 \
  -B tests/manual.py ox-check
```

This acquires existing Unison00..07 tokens, compiles with at most two jobs and
runs disposable CLI selftests with three configured workers per endpoint.
The parent retains ownership through actual group settlement; an uncertain
run retains its grants. Use `stock-check` with `STOCK_PREFIX` for the stock
pair. Output paths must be fresh. This is not permission for SDK/Photo/bulk-IO
work or idle-credit borrowing. The standalone recipes below do not acquire the
joint canonical tokens; coordinate them separately when sharing the machine.

This fork requires OCaml 5 domains; package metadata and installation minimums
therefore specify OCaml 5.0. The former upstream 4.08 floor does not describe
this source tree. Qualified text builds include historical stock5.5.1, current stock5.2.0,
and pinned5.2.0+ox on this host; the dependency floor alone does not qualify other versions or GUIs.
The clone-stage signal boundary also uses runtime APIs absent from OCaml 4.08.

For current working-tree changes, including uncommitted new modules, use:

```sh
python3 tests/build_snapshot.py --compiler-prefix /absolute/compiler/bin --jobs 2 --selftest --selftest-workers 3
```

The script prints its isolated build location and preserves build/test logs.

Use a separate source/build directory for each compiler. OCaml compilation
artifacts and the generated `src/Makefile.cfg` must not be shared between
switches. The following creates a disposable copy of the **committed** source;
when testing uncommitted work, copy those source changes into that disposable
tree before building.

```sh
unison_build=$(mktemp -d /private/tmp/unison-oxcaml.XXXXXX)
git archive HEAD | tar -xf - -C "$unison_build"
opam exec --switch=5.2.0+ox -- ocamlopt -version
opam exec --switch=5.2.0+ox -- make -C "$unison_build/src" tui NATIVE=true -j2
mkdir "$unison_build/test-state"
UNISON="$unison_build/test-state" "$unison_build/src/unison" -ui text -selftest -semanticworkers 3
```

Use an available temporary directory in place of `/private/tmp` on other
platforms. The commands require an already installed switch; they do not
install or upgrade a compiler. Check that `ocamlopt -version` reports
`5.2.0+ox` before comparing results. Do not infer the compiler from a binary's
filename.

If using an explicit compiler directory instead of `opam exec`, this is the
tested native build form, run in a fresh source copy:

```sh
make -C src tui NATIVE=true -j2 TOOL_PREFIX=/path/to/5.2.0+ox/bin/
```

Set `NATIVE=true` explicitly. The inspected make configuration selected
bytecode when its automatic executable lookup received an absolute compiler
prefix. Passing the native setting prevents a successful bytecode build from
being mistaken for the intended native build. The configure script itself was
also exercised under the pinned OxCaml interpreter.

For a standard OCaml comparison, use another fresh source copy and the same
`tui NATIVE=true` target with that compiler's directory or opam switch. Keep
`UNISON` directed to a disposable test-state directory, so selftests do not use
the user's synchronization archives. The examples leave their disposable
directories available for inspecting logs and failures.

The text CLI also builds with Dune 3.22.2 in a fresh source snapshot. Put the
chosen compiler's `bin` directory first in `PATH`, then run:

```sh
dune build --display=short -j2 src/linktext.exe
mkdir selftest-state
UNISON="$PWD/selftest-state" _build/default/src/linktext.exe -ui text -selftest -semanticworkers 3
```

Both standard OCaml 5.5.1 and OxCaml 5.2.0+ox passed this Dune build and selftest
on the test host. The text executable now links a small selftest archive to
retain its registration initializer, which upstream's Dune configuration had
omitted. The GUI stanza is unchanged and was not built.

## Verified scope

On x86_64 macOS 15.7.9, the compatibility patch on upstream
`8772d26a2eb77cfd0cb6da81807e81f24f51044c` was checked with:

| Compiler | Native CLI build | Built-in selftests |
| --- | --- | --- |
| Standard OCaml 5.5.1 | Passed | Passed |
| OxCaml 5.2.0+ox | Passed | Passed |

Each used a separate disposable source tree and archive directory. The patch
is small but relevant to both compiler paths: `List.mem`, several curried Unix
aliases, and a partially applied `Buffer.add_string` otherwise expose or
capture OxCaml local argument modes incompatible with the ordinary public
interfaces.

A local archive-reuse smoke test also passed: standard OCaml created the
archives, OxCaml reused them and propagated an edit, and standard OCaml reused
them again and propagated an edit in the opposite direction. Each result was
compared byte-for-byte. This does not test a mixed-compiler remote RPC session.

The build still reports `unsafe_multidomain` alerts for existing signal,
environment, and callback APIs. They have deliberately not been suppressed.
A successful build and sequential selftest do **not** establish that legacy
Lwt, RPC, archive, UI, or global process state can be accessed from multiple
domains. Keep that state on its owner thread; qualify each new worker boundary
and foreign call independently.

These checks cover the native text CLI on this compiler/platform combination.
They do not qualify GUI builds, Windows OxCaml support, all-core scheduling,
TSAN, or a performance improvement. Archive interoperability and remote-peer
compatibility should be checked separately when protocol or archive handling
changes.
