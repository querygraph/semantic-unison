# Native clone creation-parent handles

```sh
python3 tests/clone_handles/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
```

The runner builds private copies of the current native engine and the exact
`Fs` clone declarations/wrappers; only unrelated filesystem path translation is
replaced with a string shim. All inputs are tiny disposable APFS files.

The additive API returns caller-owned descriptors in order: immutable unlinked
basis, writable output, actual creation parent. Tests check native identities,
read/write modes, initial offsets, CLOEXEC, property clearing, source preservation
and descriptor counts. Both existing two-descriptor APIs retain success/decline
layout and ownership. Real parent rename plus replacement verifies held-parent
lookup and identity-checked cleanup without damaging a replacement sentinel.
A private wrapper also renames/replaces that parent immediately after the native
output clone, before the engine finishes, proving it returns the creation parent
rather than reopening the current pathname later.

Private native faults exercise first-clone unsupported/cross-device/platform
declines, early/later operational errors and post-creation permission errors;
EEXIST preserves existing files. Repeated success/failure checks detect file,
scratch-name and descriptor leaks. The preallocation check is a source-order
guard, not allocator exhaustion or asynchronous-exception qualification.

All 20 named cases and the independent source-property checks passed on
2026-10-13 under stock OCaml 5.5.1 and OxCaml 5.2.0+ox. The runner prints
compiler/source hashes and removes its isolated build and fixtures afterward.

The fixture's checked unlink is test-only. This suite does not implement or
qualify production publication, root/namespace incarnation, adversarial atomic
inode compare-and-swap, crash recovery or successful-return asynchronous handoff.
It does not qualify other filesystems/platforms or establish physical-write or
performance results. No photos, catalogs, caches or Adobe tools are used.
