# Native observation and borrowed-FD lease tests

```sh
python3 tests/clone_lease/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
```

The isolated runner builds `FileObservation`, `CloneRange` and `CloneLease`
from fresh unit copies. All files are small disposable fixtures. A private
ordinary `pread`/`pwrite` helper supplies byte-exact range copying without
changing descriptor offsets or claiming shared blocks.

The 21 named cases combine real descriptors and independently controlled
observations. They check bounded execution on the exact borrowed descriptors,
source bytes and destination sentinels, owner epoch changes during enrollment
and refresh, per-lease invalidation, owner closure and fresh checks after a
completed receipt. Real writes, unlink, truncation, rename/path replacement and
`dup2` replacement test source stability, actual changed bounds/identities and
stopping before stale I/O. The replacement sentinel survives later invalidation
and garbage collection; the lease never closes borrowed descriptors.

Injected observations independently exercise missing/disappearing UUIDs,
malformed stamps/IDs, nonregular objects, same-file aliases, source
timestamp/flag/link/mount changes and fixed destination constraints while
permitting destination write timestamps. Native/observer errors retain their
exception identity. Cancellation and adapter/notification exceptions retain
the exact completed prefix and leave descriptor ownership with the caller.
Repeated enrollment failures and final collection check for descriptor leaks.

The tests qualify the standalone observation/lease bridge. They do not prove
caller-side immutable source retention, admission/worker lifetime ownership,
path-based publication or production transfer integration. Native filesystem
capabilities and physical sharing remain separate qualification. No
photo/catalog/cache data, preview operations or Adobe tools are used.

All 21 cases passed on macOS under stock OCaml 5.5.1 and OxCaml 5.2.0+ox on
2026-10-13. The runner records compiler/source hashes and removes its temporary
build and fixtures afterwards. Other platforms were not qualified here.
