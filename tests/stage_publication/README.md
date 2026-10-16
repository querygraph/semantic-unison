# Descriptor-bound staging publication tests

```sh
python3 tests/stage_publication/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
```

The runner copies the production `StagePublication` unit into a private build
directory. Its small disposable fixtures supply real stage and parent
descriptors independently of Unison's `Fs` integration. No shared-tree build
objects or production photos, catalogs, caches, Adobe tools or preview operations
are used.

The 58 named cases exercise exclusive stage-to-temporary publication, parent
and root rebinding, replaced stage/temporary names, followed ancestry, directory sibling
changes, descriptor consumption and borrowing, explicit cleanup and finalizer
behavior. They check exact bytes and independent replacement sentinels, closed
owned descriptors, repeated close and descriptor-number reuse. Search-only
directory permissions are tested with an actual native `O_SEARCH` descriptor.

Private wrappers include the unchanged production C translation unit and call
the real native syscalls by default. Faults independently exercise missing and
zero volume UUIDs, malformed returned masks/lengths, operational attribute and
rename errors, high inode/device/filesystem/mount-flag bits and UUID drift.
Every prepare, adoption and publication directory probe is targeted. Actual
directory flag changes, hardlink creation and a destination introduced after
the preflight lookup test native constraints and `RENAME_EXCL`. A private
`SIGUSR1` handler raises `Sys.Break` after successful native rename, with
compiler-adapted `Sys.with_async_exns` and an explicit pending-action check;
temporary cleanup ownership survives that particular exception boundary.

Preparation fallback classification is tested separately using actual faulted
query exceptions at all three preparation identity phases. Missing/zero UUID,
`ENOTSUP`, `EOPNOTSUPP` and `ENOSYS` qualify only at those exact phases. The tests
use the runtime's actual `Unix.error` values, with no fixed Darwin errno values.
Operational, malformed, unstable, path and syntax errors, actual later-phase
failures, non-native exceptions and forged phase prefixes/suffixes do not qualify.
A native counter that performs no OCaml allocation samples owned-descriptor
closure directly in the exception handler, before GC can close abandoned owners.

These tests qualify the staging primitive under cooperative staging namespace
ownership. They do not qualify final live-file commit, logical root policy,
durable publication, concurrent namespace mutation, descriptor reassignment
during a call or caller-side content validation.

All 58 cases passed on macOS on 2026-10-13 under stock OCaml 5.5.1 and OxCaml
5.2.0+ox. Both runs copied `stagePublication_stubs.c` with SHA-256
`f292e14692347583ae42a5ca4ee3bf0181f9f00446feccabbdbe927b31610474`.
Other platforms and arbitrary asynchronous-exception points remain unqualified.
The runner records compiler, source and compiler-adapted harness hashes and
removes its temporary build and fixtures afterwards.
