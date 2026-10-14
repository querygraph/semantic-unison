# Strict native range outcomes

Run outside the shared build tree:

```sh
python3 tests/native_copy_range/run.py --ocamlopt /absolute/compiler/bin/ocamlopt \
  --negative-control --keep-work --receipt /private/tmp/native-range-receipt.json
```

The portable typed-result tests exercise exact reported prefixes, all decline
scopes, terminal operational errors including legacy unsupported errnos,
malformed raw scalar receipts, zero/invalid progress, overflow and callback or
cancellation boundaries. Independent bytes and per-byte write counts check
exact suffix fallback. One indeterminate adapter writes an unreported extra
byte; it must stop without suffix copying. The private negative control removes
only the strict indeterminate-decline guard and must fail that byte oracle.
A second private control removes the direct typed-context checks; it must fail
when a typed success carries errno/native error data. Direct typed contexts
must obey the raw decoder's error invariants, retaining only earlier valid
prefixes and notifying no bytes for a contradictory result.

On macOS the runner also compiles the actual native C implementation and the
legacy C primitive. It derives both external declarations from the pinned
production `System` source. Native fixtures check unavailable-platform scope,
argument and borrowed-descriptor errors, access/append/alias restrictions,
source EOF, zero requests, unchanged file bytes/EOF/positions and legacy ABI.
These are real macOS preflight/unavailable results. They supply no Linux,
FreeBSD, Solaris, Windows, ZFS/ReFS, native range-sharing or performance proof.

Every compile/run command, exit status, log, compiler binary, copied source and
generated artifact is pinned in the receipt. `--keep-work` retains the isolated
directory for independent inspection. Fixtures use disposable files only, with
no Photo, Lightroom, Adobe or production volume access.

The separate production-caller fixture also requires a compiler-matched private
Make snapshot:

```sh
python3 tests/test_clone_bound_range.py /private/tmp/frozen-make-snapshot \
  --ocamlopt /absolute/compiler/bin/ocamlopt --keep-work \
  --receipt /private/tmp/bound-range-receipt.json
```

It hooks only the strict native call and poisons the legacy call in its private
namespace. Production channels, fallback, observations and leases remain intact.
It preserves the earlier bound-range cases and adds strict reported/unknown
effects, malformed receipts, and a growing-source `copyFile` case whose small
suffix must leave cached/native cursors correct before another literal write.
`--negative-suffix-control` changes only the private remaining-length expression
to the original request length and must fail independent surrounding sentinels.
The earlier `--negative-control` checks cached channel reconciliation separately.
