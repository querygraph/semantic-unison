# Copy-range outcome tests

Run without building the shared checkout:

```sh
python3 tests/copy_range/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
```

The injected native step exercises short/zero/invalid progress, exact suffix
fallback with byte and write-count checks, unsupported and operational failures
before/after a prefix, overflow bounds, and callback/cancellation exceptions.
Successful native copying has unreported sharing; these tests make no native
APFS/ZFS/ReFS claim.

The legacy unsupported errno set remains explicit compatibility behavior for
EINVAL/ESPIPE/ENOTSOCK and the documented unsupported codes. EBADF escaping the
native adapter fails rather than authorizing fallback. The tests pass under
stock OCaml 5.5.1 and OxCaml 5.2.0+ox as of 2026-10-13.
Strict native status, capability generations, aligned range planning and a
constrained filesystem adapter remain in
[the filesystem plan](../../doc/filesystem-capabilities-plan.md).
