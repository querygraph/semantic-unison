# Built-in worker native call map

This [source-pinned map](worker-native-call-map-20261018.json) makes the current
first-party worker binding scope explicit at production baseline `513c121a`.
It is a manual call-path review with a checked declaration inventory, not a
static-analysis proof or full M6 completion.

| Worker operation | First-party native boundary |
| --- | --- |
| Digest, identify, recognize, inspect, observe | SemanticFile borrowed input and SemanticHash |
| Component capture/restore/refresh/index selection | Pure bounded forest/checkpoint/refinement plus borrowed reads and hashing |
| Reconcile | Conservative scalar merge, borrowed reads and hashing |
| Apply | Borrowed positional output and final hashing |
| Snapshot | FD-only clone preflight/result, then bounded positional copy/hash fallback where declined |

The three selected leaf modules declare nine native bindings: three hash
primitives, five file/timing primitives and the FD clone primitive. Current
manual reviews cover their first-party implementation contracts, including the
explicit EVP hash path. On macOS the FD clone primitive declines without effects
after preflight; it is not the separate named APFS clone interface.

Cache namespace/quota/publication functions live in some of the same source
files but are not called by these built-in worker operations. Their checked
interfaces mark owner APIs nonportable; two exact named compiler negatives
verify representative exclusions. This does not turn a whole pinned C file
into an audit of all its functions. The owner publication audit remains separate.

The installed OCaml/Unix runtime supplies descriptor operations, channels,
notification writes, locks, atomics and GC. CommonCrypto/OpenSSL supply provider
internals. Those dependencies and ABI assumptions remain explicit; these source
reviews do not certify their complete internals or arbitrary custom plugins.
Stock callback contracts remain manually trusted; OxCaml portability checks do
not prove native C race freedom. No sanitizer result is inferred.

No execution or resource reservation was needed for this map. Existing current
worker parity/apply and exact compiler-boundary results are referenced with their
original scope. Pending V6 transport/property runs, broader end-to-end performance
and resource/platform verification remain separate; this map creates no gate,
permission, merge or deployment claim.
