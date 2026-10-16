Run the optional compact base's actual CLI and kernel tests locally:

```sh
python3 tests/semantic_base_cache/run.py --unison /absolute/current/unison --receipt /private/tmp/cache-cli.json
python3 tests/semantic_base_cache/kernel.py --compiler /absolute/ocamlopt --report /private/tmp/cache-kernel.json
python3 tests/semantic_base_cache/fingerprint.py --compiler /absolute/ocamlopt \
  --build /absolute/current/Make/snapshot --report /private/tmp/cache-fingerprint.json
```

The CLI uses disposable loopback replicas, original DNG-shaped bytes and
mock validators; no Adobe/SDK/Photo input is involved. Its twelve cases include
cache-only convergence, missing/damaged/permissive/symlinked/stale/disabled
records, image/conflicting edits, wrong common generation, a checksum-valid
wrong policy, and second-receiver failure followed by fresh convergence.
Full backup behavior has its independent existing merge suite.

The kernel compares exact output against independent Python SDB bytes and
runs thirteen finite codec/reconciliation controls. OxCaml executes them in an
actual Safe.spawn domain. The descriptor probe links the actual native objects
and verifies eight MD5 compatibility, cursor, path replacement and FD controls.
These are deterministic functional tests, not fuzzing or SDK qualification.
All retained private workspaces/logs are reported in the receipts.

Private storage checks link the compiler-matched Make objects directly:

```sh
python3 tests/semantic_base_cache/storage.py --compiler /absolute/ocamlopt \
  --build /absolute/current/Make/snapshot --report /private/tmp/cache-storage.json
```

The original sixteen finite controls cover repeated descriptor settlement, trust
checks, nonreplacement, path binding and shard capacity. Twelve added quota
controls cover idempotence, entry/payload exhaustion, corrupt/range/overflow and
permission/link/type checks, missing-ledger refusal with retained records, an
actual separate process holding the POSIX lock, and read-only v0 fallback. New
captures use the quota-managed v1 tree. They use disposable files and
do not invoke Adobe. See [sealed evidence](storage-qualification.json). They do
not establish crash durability, concurrent-mutator or allocation-fault behavior.

Acquisition cleanup has a separate deterministic exception probe:

```sh
python3 tests/semantic_base_cache/ownership.py --compiler /absolute/ocamlopt \
  --build /absolute/current/Make/snapshot --report /private/tmp/cache-ownership.json
```

It compiles a private copy against the actual production interface/dependencies
and raises `Out_of_memory` immediately inside each protected acquired-resource
body (record read, bounded directory scan, exclusive temporary write, quota
descriptor, initialization root directory and initialization shard directory). No real
memory exhaustion, invalid memory access, fuzzing or production fault hook is
used. Each case checks descriptor conservation, no temporary residue and a fresh
successful capture/load. A deliberately unguarded private negative must fail
with the observed descriptor leak. This tests these lexical cleanup paths;
it does not prove universal allocation failure, native close failure or crash
recovery behavior.

[Sealed acquisition evidence](ownership-qualification.json) records both compiler runs and their private negative controls.

## Concurrent final-entry reservation

The storage suite now has29 finite checks, including two original child processes
released by a shared pipe to capture distinct logical keys when only one quota
entry remains. Exactly one capture succeeds and one refuses, both children are
waited by exact PID, the durable ledger charges exactly the original plus one
new record, exactly one new base loads, and the original base/parent descriptor
baseline remains intact. OS scheduling is not forced; refusal can result from a
busy lock, an epoch change, or exhausted quota. This is not a power-loss test or
a claim about hostile writers, physical storage accounting or thread safety.

[Actual stock/Ox qualification](../qualification/compact-cache-concurrent-quota-actual-20261016.json)
records both29-case suites and normal group/CPU8 closure, with no SDK, Photo
payload or canonical IO. It uses current compiler-matched production native
objects; production source inventory matched each build before linking.
