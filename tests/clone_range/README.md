# Portable constrained clone-range tests

Run in an isolated build directory with either compiler:

```sh
python3 tests/clone_range/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
```

The fake backend keeps an immutable source and a separate evolving candidate.
It checks each native request against independently enforced alignment,
maximum-length, EOF, identity, generation, compatibility and alias restrictions.
Per-byte write counts and surrounding sentinels detect rounded ranges, skipped
suffixes and repeated writes. Sequential reconstruction supplies the expected
bytes for shifted and duplicate references.

The suite has 48 named cases, including a 960-combination matrix over alignment,
maximum length, source/destination residues and request length. Hand-written
traces cover empty/head/tail ranges, exact boundaries, multiple chunks and short
successful prefixes. The failure cases check:

- Native `Shared` versus `Copied` accounting, mixed known prefixes and exact
  suffix fallback after `Unsupported`; unsupported ordinary copying is terminal.
- EIO, ENOSPC, permission, invalid-handle and ambiguous EINVAL errors before
  and after progress; indeterminate mutation and malformed/unaligned counts
  remain failures and never authorize suffix copying.
- Initial, mid-transfer and final observation changes to both bindings,
  generations, identities, sizes, owner instance and backend revision; typed
  observation errors preserve the earlier prefix.
- Cancellation, observer/adapter/progress callback exceptions, overflow and
  pre-established EOF bounds. A huge valid Int64 request is cancelled after
  five bounded operations without allocating an operation list or byte array.
- Same-file overlap rejection, disjoint alias restrictions, cross-volume
  compatibility and whole-file flags that cannot authorize range operations.

Every successful reconstruction matches the independent bytes and writes each
authorized byte exactly once. Failed known-prefix cases preserve the surrounding
sentinels and stop without new work. The indeterminate case deliberately writes
one extra byte beyond its reported prefix and requires an indeterminate terminal
outcome; this harness does not publish or delete filesystem candidates.

These are portable planner/accounting tests. A fake `Shared` result represents
the backend contract; it supplies no evidence of physical sharing on APFS, ZFS,
ReFS or any mounted filesystem. The tests do not use photo/catalog/cache data.

All cases passed under stock OCaml 5.5.1 and OxCaml 5.2.0+ox on 2026-10-13.
The runner prints the source hashes and compiler version, compiles in a fresh
temporary directory and removes that directory after the test. No shared build
artifacts are used.
