# Coordinated component cache routing

`SemanticWorkers.refresh_owned_components` consumes an owner-trusted UDI entry
and bounded immutable UCR record. Authentication and decoder-inventory binding
run on the worker before full-current-input/current-parser verification and
localized decoder refresh. The caller cannot substitute a separate historical
inventory through this API. It still owns entry provenance and prior cache-read
FD settlement; record authentication does not prove namespace presence or a
producer's closure.

`components_indexed` adds exact owner/root/path/generation selection from an
immutable trusted index within that same coordinated job:

| Selection | Action |
| --- | --- |
| No exact key, or different generation | Fresh extraction using frozen current decoders |
| Exact entry and authenticated record | Restore, verify current input/parser, refresh affected views |
| Exact entry but missing record | Explicit incomplete-capture error; no fresh extraction |
| Selected corrupt, foreign or mismatched record | Fail the job; no silent fallback |

An unselected record is ignored, never promoted into trusted state. Optional
checkpoint capture works on both successful routes, but neither inserts an
entry, publishes files nor advances an archive. Cancellation suppresses delivery
while existing worker/group/FD and CPU/IO settlement rules remain in force.
Owner budgets must cover shared immutable index snapshots, bounded record and
entry metadata, and optional output checkpoints across queued work.

This is the routing primitive for a future managed-cache owner. It does not
open cache paths, discover blobs, evict records, install a namespace or enable
reuse in the normal report/scan path. The loader must obtain the index from
its trusted archive reference, authenticate its entries, settle read FDs and
retain source access before submission. Complete current-input verification
still reads the file; reused pixel-view hashes are not a physical-IO savings
claim. No additional private-field understanding is a deployment prerequisite.

Current evidence is
`tests/qualification/component-indexed-worker-refresh-actual-20261017.json`:
stock/Ox Make/fullselftests/Dune compilation and production-linked worker controls
on original tiny fixtures, with changed-input, incomplete/foreign-record,
stale-generation, missing-key and cancellation cases. No SDK/media/transport or
normal cache-store installation was exercised.
