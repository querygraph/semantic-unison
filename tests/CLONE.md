# APFS clone qualification fixtures

All fixtures use `/private/tmp`; no real photographs, mounted test volumes, or
SSH server are needed. Build Unison in an isolated source copy first. Do not run
these commands against an installed production synchronization profile.

```sh
python3 tests/test_clone_sync.py /private/tmp/unison-build/src/unison
python3 tests/test_local_clone.py /private/tmp/unison-build
python3 tests/test_semantic_remote.py /private/tmp/unison-build/src/unison /path/to/stock/unison
python3 tests/test_remote_bounds.py /private/tmp/unison-build
python3 tests/test_generic_format.py /private/tmp/unison-build
```

The remote test starts the same binary through a disposable loopback SSH
replacement. It checks fixed-offset and shifted edits, duplicate blocks,
literal-only replacement, truncation/extension, unchanged second sync,
hardlink isolation, `clone=off`, unsupported-basis `auto`/`require` behavior,
and interruption/retry. It checks exact bytes and staging cleanup, and checks
that fixed-offset matches report logical bytes preserved. Interruption kills
only the fixture process group; its retry uses `ignorelocks` solely for the
fixture's archive directory.

The local test compiles a private copy of `copy.ml` to expose its internal
bounded producer without adding a production test API. It links the already
built modules and C objects, writing compilation artifacts in a disposable
directory. It directly exercises the producer used after a cross-volume
source clone is declined, without mounting another volume. It also tests
the opt-in semantic transaction for little/big-endian XMP fixtures and opaque
change fallback. Set `OCAMLOPT` to the compiler used for the build if needed.
It also exercises the production asynchronous local transaction on a 32 MiB
synthetic file, checks concurrent source/basis jobs and an owner-loop heartbeat,
and verifies sibling failure and connection cancellation release permits and
discard staging only after borrowed descriptors are safe to close.

The remote semantic suite checks both transfer directions between modified
peers and, when supplied, an unmodified peer. It requires the semantic path
for fixed-layout XMP edits with negotiated support and ordinary exact fallback
for changed opaque bytes, changed layout, and an older peer. The framing suite
feeds only a declared oversized body length through a pipe, checking both new
request and reply limits reject before reading or allocating that body. It
also checks bounded string fields preserve the ordinary codec's bytes.
It also checks cleanup uses physical resource identity after mutable fields
change and keeps distinct, structurally equal registrations separate.
The semantic suite additionally checks that a same-volume local update takes
the cheaper source-clone path first and preserves exact data and readonly mode.

The generic-format suite links one extra trusted test module that registers a
four-byte metadata profile through `SemanticFormats.register`. With only
`semanticprofile` enabled, both remote directions use the profile and an opaque
change falls back to ordinary transfer. The local suite exercises the same
registration through the asynchronous transaction. Neither test changes the
production dispatcher, worker implementation, or DNG extension.

New SDE bodies have limits at both outer RPC framing and individual string
fields. This does not harden shared legacy message headers or unrelated RPCs.

To test the native descriptor/property contract, copy `tests/clone_stage.ml`
into the isolated build's tests directory, then run:

```sh
cd /private/tmp/unison-build/tests
ocamlopt -I +unix unix.cmxa ../src/copy_stubs.o clone_stage.ml -o clone_stage
cd /Users/alexy/src/unison
python3 tests/test_clone_stage.py /private/tmp/unison-build/tests/clone_stage
```

This verifies a readonly source stays readonly, basis snapshots are unlinked
and stable after live-source mutation, stage writes do not modify the basis,
output creation is exclusive, repeated failures clean up, and old xattrs,
resource forks and ACL entries do not leak into staging. Flagged files are
conservatively declined. The native driver skips unsupported filesystems;
the full integration suites require APFS clone support.

These tests establish byte correctness and logical write avoidance. They do
not measure physical blocks written, storage durability after power loss,
or performance. The new backend is macOS-only; other systems retain ordinary
transfer. Existing upstream copy acceleration may still share blocks with
`clone=off`. `dontchmod` excludes receiver staging because staging requires a
private writable mode. Resume uses the ordinary existing prefix path;
interrupted clones have separate names and are rebuilt.

Validation at `Files.renameLocal` sees private received candidates, including
copied directory children and merge results. Move-only operations use live
inodes and receive no new bytes, so they bypass that validation hook. A future
option to validate all scanned or renamed DNGs must first create a private
validation copy and must not pass a live move source to an external helper.
