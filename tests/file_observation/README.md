# Held-descriptor observation tests

```sh
python3 tests/file_observation/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
```

The runner compiles fresh unit copies in a disposable directory, records source
hashes and uses only small synthetic files. Python `os.stat` and
`os.utime(ns=...)` provide independent file IDs, size, links, `UF_NODUMP` flags
and exact nanosecond timestamps. Native cases cover writes/truncation,
unlinked held files, rename and same-name replacement, exact `dup2` reuse,
directory identity, unchanged offsets and repeated error/success leak checks.

The private C fixture includes the production observation source and wraps
`fgetattrlist`; no production preference, environment switch or API is added.
Its buffers follow the installed SDK's attribute layout. Raw parser tests cover
every truncated capacity, advertised length overflow and unexpected/missing
returned masks. Native calls distinguish missing/all-zero UUIDs from malformed
data, preserve EACCES/EIO and phase, and detect `ftruncate` during the query as
EBUSY. The fixture exports native EPROTO rather than hardcoding its number.

All 11 named cases passed on macOS under stock OCaml 5.5.1 and OxCaml 5.2.0+ox
on 2026-10-13. The native probe reports a skip when observation raises ENOSYS;
non-macOS builds were not qualified here.
This qualifies these held-FD facts and parser/error boundaries; it establishes
no immutable-content proof, mount-incarnation identity, capability or physical
sharing. No photo/catalog/cache data or Adobe tools are used.
