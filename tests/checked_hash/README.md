# Checked hash component qualification

```sh
python3 tests/checked_hash/run.py --compiler /usr/local/bin/ocamlopt --receipt /tmp/hash-stock.json
python3 tests/checked_hash/run.py --compiler ~/.opam/5.2.0+ox/bin/ocamlopt --receipt /tmp/hash-ox.json
python3 tests/checked_hash/bench.py --compiler ~/.opam/5.2.0+ox/bin/ocamlopt --receipt /tmp/hash-bench.json
```

The same stock-compatible implementation is used by both compilers. OxCaml
selects the checked interface and exactly three marked portable FFI declarations;
stock retains comments/ordinary spawn. Root reviewed the concrete native
rooting/private-state/no-global-pointer contract. Compiler checking validates
OCaml captures and interfaces, not C memory ownership or library internals.

Each compiler tests real native stubs and qualification-only forced reference
stubs. Each mode checks15 hashlib vectors and four-domain streaming/private
context/finalization behavior. OxCaml also rejects captured shared contexts and
mutable bytes buffers. Workspace and actual compiled source/interface/stub/binary
hashes remain in receipts. Native domain execution is not a replacement for the
production shared CPU owner; no additional scheduler is installed by these tests.

The first exploratory source incorrectly tried signature-only @@portable syntax
at an implementation's top level; it was rejected. Removing that prefix then
exposed the three nonportable native declarations. Explicit reviewed declarations
and immutable round lookup let the actual component interface compile. Neither
failed probe executed code or changed production stubs.

The microbenchmark links exact old and current modules, verifies output parity,
reports nine CPU/wall samples per backend with1MiB work each, and alternates the
reference order. Results are cached-string controls rather than meaningful
complete sync/storage performance or a blanket speedup claim.

## Current boundary/state successor

[Current stock5.2.0/Ox5.2.0+ox qualification](../qualification/hash-bounds-current-actual-20261017.json)
adds ten invalid ranges/domain (including min_int/max_int), valid zero-length
edge feeds, stream continuation after rejection, and independent interleaved
contexts. Both compilers pass native CommonCrypto and qualification-only forced
reference modes,15 hashlib vectors and four domains/mode; Ox still rejects
shared mutable context/input captures. The compiler's do_not_spawn_domains alert
remains in the receipt; these isolated component domains are not a new product
scheduler or an OS-thread cap.

Actual containing children6855/6896 reaped0/groups absent/outer Unison8 closed;
owning session40896/terminalbd9038/0/no running session. No image/SDK/EXglobal
access. Production hash source is unchanged and the frozen mixed request's326
execution pins still match. The earlier source-audit snapshot remains historical:
this successor deliberately changes test.ml, not the hash implementation.
