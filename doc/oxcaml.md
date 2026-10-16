# Building the CLI with pinned OxCaml

The CLI can be built with the `5.2.0+ox` compiler while retaining a standard
OCaml 5 build. The compatibility changes eta-expand standard-library aliases;
they do not change interfaces or archives. The semantic extension adds
separately negotiated capabilities while retaining ordinary peer fallback.

This fork requires OCaml 5 domains; package metadata and installation minimums
therefore specify OCaml 5.0. The former upstream 4.08 floor does not describe
this source tree. Qualified text builds are stock 5.5.1 and pinned 5.2.0+ox on
this host; the dependency floor alone does not qualify other versions or GUIs.
The clone-stage signal boundary also uses runtime APIs absent from OCaml 4.08.

For current working-tree changes, including uncommitted new modules, use:

```sh
python3 tests/build_snapshot.py --compiler-prefix /absolute/compiler/bin --selftest
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
opam exec --switch=5.2.0+ox -- make -C "$unison_build/src" tui NATIVE=true -j4
mkdir "$unison_build/test-state"
UNISON="$unison_build/test-state" "$unison_build/src/unison" -ui text -selftest
```

Use an available temporary directory in place of `/private/tmp` on other
platforms. The commands require an already installed switch; they do not
install or upgrade a compiler. Check that `ocamlopt -version` reports
`5.2.0+ox` before comparing results. Do not infer the compiler from a binary's
filename.

If using an explicit compiler directory instead of `opam exec`, this is the
tested native build form, run in a fresh source copy:

```sh
make -C src tui NATIVE=true -j4 TOOL_PREFIX=/path/to/5.2.0+ox/bin/
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
dune build --display=short -j8 src/linktext.exe
mkdir selftest-state
UNISON="$PWD/selftest-state" _build/default/src/linktext.exe -ui text -selftest
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
