# Whole-file clone qualification

This suite tests the additive strict whole-file result and actual ordinary Copy
callers from frozen compiler-matched source. Current-route fixtures poison both
legacy boolean clone APIs. A private exact-offset copier simulates native whole
success without changing source/output native cursors; complete file bytes,
EOF, cached/native positions, following output literals and unread buffered
source bytes provide independent oracles. Simulated success does not attest
block sharing.

Separate actual macOS controls use the new native named-creation adapter on
small private APFS temporary files, with borrowed-source/parent ownership and
property/symlink/empty-source checks. The FD adapter's platform-unavailable path
qualifies preflight and unchanged effect, not Linux cloning. Linux/native ZFS or
ReFS, physical allocation, performance and hostile first-admission races remain
outside this suite.

Frozen qualification completed with stock OCaml 5.5.1 and installed OxCaml
5.2.0+ox: **60 fixed groups / 536 assertions and five independent negative
controls on each compiler**. See [qualification.json](qualification.json) for
the matched production freeze, successful receipts, every retained earlier
trial, compiler/source/object/binary/log pins and checked artifact inventory.

| Component | Groups | Assertions | Main independent observations |
| --- | ---: | ---: | --- |
| Typed whole-file protocol | 15 | 108 | Int64 lengths/codes, malformed tags/context/effects, terminal operational errors |
| Unchanged native macOS ABI | 17 | 116 | Small actual APFS clones, descriptor/EOF/cursor preflight, parent/output witnesses, properties, symlinks, nodump, sized source versus unsized basis, legacy APIs |
| Named-owner fault settlement | 9 | 87 | Actual C/facade FD census, retained output, first error, close-number reuse, foreign-name/parent replacement, followed-source retargeting |
| Complete Copy channel caller | 12 | 177 | Both legacy APIs poisoned, exact independent bytes/EOF, following literal, source read-ahead, ownership eligibility, terminal effects and no fallback |
| Complete Copy named caller | 7 | 48 | Owned candidate publication/cleanup, exact expected length, typed receipt guard, O_TRUNC provenance, actual nodump ordinary fallback |

The three parent controls use exact `330d04829c43f6a19f6d5af1a95cf3ea24d24635`
`Copy` source with current support modules/native objects. They detect stale
output cursors, unchecked expected EOF and boolean-failure fallback after extra
writes; this is not a full parent binary. One private single-predicate decoder
mutation admits an indeterminate decline; independent output bytes and work
counts reject it. The final control substitutes the old cleared-slot/actual
linked `Unix.close` operation at the pending-close seam; the real signal handler
observes a disarmed source FD still open before native close.

Normal native/channel/path tests link the unchanged matched production C
objects. Only the named fault suite uses a private edited whole-clone C source
for post-creation open/backup faults and a native completion signal boundary.
Every command saves unique source/CMI/object inputs and logs before subsequent
parent/mutation variants reuse module names. All disposable objects are owned
private files under `/private/tmp`; the fixture verifies its filesystem is APFS.

Signal controls queue real SIGUSR1 without an intervening ML return, record
actual FD ownership in a returning handler, then raise a registered ordinary
`Primary` exception synchronously in the private C wrapper immediately after
pending dispatch. They qualify real signal timing and ordinary post-native
failure settlement. They do **not** establish arbitrary asynchronous exception
catching in OxCaml. The installed Ox runtime's `check_async_exn` makes other
signal-handler exceptions fatal except `Sys.Break`; `Sys.with_async_exns`
supplies its separate asynchronous context. Two retained Ox trials demonstrate
fatal `Fault.Primary` from the earlier throwing handler. Stock-only earlier
successes retain the true throwing-signal evidence separately. No production
asynchronous context was added for these tests. Legacy signal/registration API
alerts in OxCaml are retained; these are isolated single-domain fixtures.

Unqualified pre-admission creation residue is reported and retained until the
private fixture removes its own file. This is a deliberate uncertainty case,
not a promise that every failure removes a name. Cooperative identity checks
do not prove hostile first-name admission, atomic compare-and-unlink, crash
recovery, or arbitrary exceptions before `System.openfile` publishes its FD.
No measured physical sharing, Linux/ZFS/ReFS runtime, performance or production
Photo/Adobe/cache/catalog/namespace/mount operation is claimed.

To reproduce from a new matched Make snapshot and sealed production inputs:

```sh
python3 tests/whole_file_clone/run.py /path/to/matched-build \
  --ocamlopt /path/to/ocamlopt --freeze /path/to/SOURCE-FREEZE.json \
  --keep-work --receipt /path/to/unique-trial.json
```

Qualification runs are sequential. A failure retains the complete partial
receipt and work directory; use a new receipt name for each corrected trial.
