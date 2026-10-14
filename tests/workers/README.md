# Typed worker scheduling qualification

Run seeded mixed hashing/DNG inspection under CPU contention:

```sh
python3 tests/workers/run.py --ocamlopt /usr/local/bin/ocamlopt --stress-only --keep-work --receipt /tmp/worker-stress.json
python3 tests/workers/run.py --ocamlopt ~/.opam/5.2.0+ox/bin/ocamlopt --stress-only --keep-work --receipt /tmp/worker-stress-ox.json
```

Six fixed PRNG seeds each run twenty batches of32 jobs. Four actual worker domains share a budget varying from1 to4 CPU credits. Every batch first reserves every CPU credit, submits a randomized mix of classic/extended DNG inspection and hashing, cancels a randomized subset in shuffled order, and proves cancellation settles while the budget remains held. After release, remaining results must match direct sequential hashes or structural proofs. Every round checks zero pending/running jobs and CPU reservations, and peak execution never exceeds the CPU budget. Shutdown checks descriptor counts against the baseline. Immutable source, compiled binary and log hashes are retained with the receipt; no source photos or Adobe/Lightroom operations are used.

This is root-owned reproducible scheduling evidence, not race-detector coverage, randomized active-write/application/RPC coverage or compiler-proved domain safety. Cancellation timing is deliberately queued; existing focused suites cover active cancellation and mutation separately. Hash/proof baselines use the same production algorithm, so this test checks scheduling parity rather than an independent algorithm oracle. Actual OS ordering may differ despite identical seeds. The existing full suite remains available without selectors; identify-only runs its content-recognition controls. Keep-work is required for durable local artifact references.

The first new fixture compilation used an operator absent from Unison's bundled legacy Lwt. It failed before test execution on both compilers; replacing it with the existing bind/return interface required no production change.
