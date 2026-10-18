# Cached SHA worker microbenchmark

This benchmark measures the existing `SemanticWorkers.digest` path over one
cached synthetic file. It does not measure synchronization, APFS cloning,
network transfer, Adobe validation, or real photo workloads. On macOS both
compilers call the same CommonCrypto SHA-256 backend; results therefore compare
the complete worker/runtime/read/hash path, not pure OCaml SHA computation.

Run from the repository root, substituting your compiler locations:

```sh
python3 bench/semantic/run.py \
  --compiler stock=/path/to/stock/bin/ocamlopt \
  --compiler ox=/path/to/oxcaml/bin/ocamlopt \
  --output /tmp/sha-current.json
```

`--build-only` checks isolated compilation without measuring. Defaults are a
64 MiB fixture, 72 independent digest jobs per batch, worker counts 1/2/4/6,
one warmup per configuration and five measured repetitions. `--file-mib 32`
selects the smaller fixture. Run while other builds and CPU-heavy jobs are idle.

Without --build, sources are snapshotted once and compiled in a temporary
directory with each compiler's default native optimization settings. With
--build LABEL=SNAPSHOT/src, actual matching production CMIs/CMXs/native objects
are linked without replacing checked interfaces; their hashes are recorded. There are no shared-checkout
build products. The synthetic fixture repeats the 64 KiB block whose byte `i`
is `(i * 71 + 19) & 255`; Python's `hashlib.sha256` independently computes its
expected digest. Every job opens the same fixture separately, so descriptors
have independent offsets. At most one fixture exists, and temporary build/data
files are deleted at completion unless --keep-work retains them. The OS cache is warmed by generation and the
warmup passes; no cache flush, pinning, or disk-throughput claim is made.

Each batch uses a fresh pool with exactly as many shared CPU permits as workers.
Pool construction is outside the timed interval. Timing includes opening and
submitting jobs, queue admission, file reads and stability checks, hashing,
worker notifications, and owner-loop completion. The current instrumented version also samples
descriptor counts after opening each input. Digest-result checking and
pool shutdown occur after timing. Each sample must return all correct digests,
leave no pending/running jobs, and release every CPU permit. Peak active workers
comes from the production pool's mutex-protected counter; it counts executing
jobs, not necessarily simultaneously scheduled CPU cores.

Wall time uses `CLOCK_MONOTONIC`; CPU time uses
`CLOCK_PROCESS_CPUTIME_ID`, including all domains and the owner thread but
excluding compilation, Python, pool startup and teardown. CPU/wall estimates
average concurrently scheduled logical CPU equivalents during the timed batch.
SMT threads share physical cores, so this ratio does not count physical cores
or measure their utilization. The JSON field `effective_cpu_cores` stores this
ratio. Tests run serially,
interleaving compiler configurations and reversing the configuration order on
alternate measured rounds. Each batch starts a new process, so its peak counter
and runtime state cannot include an earlier warmup.

The current version reports process-lifetime getrusage peak RSS in bytes
(including pool startup/shutdown) and descriptor counts sampled at input opens.
The sampled peak can miss short-lived descriptors and is not a hard FD ceiling.
Every batch must return to its original descriptor count after shutdown.

The JSON records every sample (including discarded warmups), compiler versions
and executable hashes, input/source hashes, parameters, clock/backend details,
digest counts, concurrency peaks, and median/min/max summaries. Legacy reports omit user names and absolute paths; actual-object builds and
retained workspaces include exact local artifact paths for verification. Optional machine properties can be
null when the sandbox denies `sysctl`. Cross-version compiler differences,
thermal state, OS scheduling and memory bandwidth can affect these results;
five repetitions describe this run rather than establishing universal speedups.

## Recorded run

[Raw samples and metadata](results/macos-x86_64.json), 2026-10-13, x86_64
macOS (Darwin 24.6.0), 18 physical cores and 36 logical CPUs. Stock OCaml 5.5.1 and OxCaml 5.2.0+ox
used their default native compiler settings. Major project builds and tests
finished before measurement; ordinary system activity was not controlled.

Median throughput in MiB/s, with the minimum–maximum of five measured batches:

| Workers / CPU permits | Stock OCaml | OxCaml |
| ---: | ---: | ---: |
| 1 | 359.8 (358.5–362.7) | 359.8 (351.2–360.7) |
| 2 | 704.5 (698.9–708.7) | 701.5 (694.9–703.6) |
| 4 | 1375.0 (1347.8–1397.7) | 1371.8 (1362.4–1376.8) |
| 8 | 2535.3 (2523.9–2552.9) | 2531.0 (2498.7–2548.8) |
| 36 | 5694.2 (5689.9–5718.8) | 5679.3 (5665.5–5738.6) |

Both builds scale about 15.8× from one to 36 workers in this workload. At 36
workers the median process CPU/wall ratio was 34.07 for stock and 33.94 for Ox,
representing logical CPU equivalents, with an observed peak of 36 active
workers. Every configuration reached its
configured peak. All 3,600 measured digest results and 720 warmup results were
correct, and every batch released its CPU permits.

This run demonstrates concurrent CPU use and cached hash throughput scaling
with the existing worker pool. It does not demonstrate an OxCaml-specific
speedup: both builds have similar results and use the same native SHA backend.
It also does not establish end-to-end synchronization or validation speedup.

## 18 versus 36 workers

[Raw samples and metadata](results/macos-x86_64-18-vs-36.json), 2026-10-13,
on the same host with 18 physical cores, 36 logical CPUs and the same compiler versions. This
comparison uses the same 64 MiB fixture, 72 jobs, one warmup per configuration
and five measured repetitions. No project builds or other team CPU-heavy tests
ran during measurement; ordinary host activity remained uncontrolled.

To repeat this comparison, add `--workers 18,36` to the command above and select
`--output bench/semantic/results/macos-x86_64-18-vs-36.json`.

Median throughput in MiB/s, with the minimum–maximum of five measured batches:

| Workers / CPU permits | Stock OCaml | OxCaml |
| ---: | ---: | ---: |
| 18 | 4709.8 (4509.6–4844.2) | 4617.5 (4515.0–4900.6) |
| 36 | 5175.9 (5137.5–5658.5) | 5103.4 (5032.8–5728.0) |

The median 36/18 throughput ratio was 1.099 for stock and 1.105 for Ox, a
9.9% and 10.5% increase. Eighteen workers retained 91.0% and 90.5% of the
36-worker throughput. Median CPU/wall was 16.75/16.85 logical CPU equivalents
at 18 workers and 33.79/33.54 at 36 workers (stock/Ox). Total median process CPU
time per batch was 16.55/16.65 seconds at 18, versus 29.48/30.44 seconds at 36.
Every batch reached its configured active-worker peak; all 1,440 measured
hashes and 288 warmup hashes were correct, with all CPU permits released.

For this measured hashing workload, 18 is a reasonable balanced cap: it retains
about 90% of throughput with roughly half the scheduled logical CPU equivalents.
Thirty-six offers higher hashing throughput when that is the priority. The
36-worker samples fell from roughly 5,600–5,700 MiB/s in the first two rounds
to roughly 5,000–5,200 in the final three; this run does not identify the cause.
The ranges describe the observed run, without establishing a universal gain
or a full-sync/SDK setting. The runtime's automatic CPU budget selects physical
cores on macOS, yielding 18 on this host; `semanticworkers = 36` selects the
explicit throughput option. Other platforms retain the logical-count fallback.

## Checked production build, 2026-10-14

The [current raw run](results/checked-worker-20261014.json) links the production
objects qualified at77234c5; OxCaml actually uses Safe.spawn and checked extension
interfaces. Stock5.5.1 and Ox5.2.0+ox share CommonCrypto. One32MiB private fixture,
36 jobs/batch, one warmup and three measured repetitions per configuration run
serially at1/6/18 workers. No Unison build or test ran concurrently; other sessions and ordinary host
activity were not controlled. This is cached hash-path scaling, not full sync or
SDK performance, pure compute throughput, or an OxCaml-specific speedup claim.

| Workers | Stock median MiB/s | OxCaml median MiB/s | Stock / Ox median peak RSS MiB |
| ---: | ---: | ---: | ---: |
| 1 | 363.4 | 365.5 | 8.2 / 14.2 |
| 6 | 1985.8 | 2039.1 | 9.3 / 10.0 |
| 18 | 4782.5 | 4941.1 | 10.4 / 12.1 |

Eighteen-worker scaling relative to one is13.16x stock and13.52x Ox. At18,
median CPU/wall is16.54/16.57 logical CPU equivalents; every batch reaches its
configured active-job peak. Compiler throughput ranges overlap. All864 hashes
(including216 warmup hashes) match hashlib; all24 batches release CPU permits
and return to their baseline three descriptors. Observed FD peaks are77/82/94
at1/6/18 in either compiler. These include36 opened caller descriptors and
queued worker duplicates, so FD use depends on outstanding jobs as well as
active workers. They do not establish a universal memory/FD bound.

The [qualification](results/checked-worker-qualification-20261014.json) verifies
all sample and object identities and an independent /usr/bin/time -l RSS control:
both native getrusage and the external final measurement report10498048 bytes
for that separate six-worker Ox batch. That control is outside the timed matrix.
Reproduce using the normal command plus --build stock=STOCK_SNAPSHOT/src and
--build ox=OX_SNAPSHOT/src, `--workers 1,6,18 --file-mib 32 --jobs 36`,
`--repetitions 3 --keep-work`.
Native/resource ceilings and broader end-to-end M6 qualification remain open;
no Adobe, Lightroom or source-photo operation occurred.

## Current shared-budget preparation (2026-10-17)

The current default worker counts1/2/4/6 leave two owner credits inside the
standing Unison8 share; larger explicitly requested configurations need separate
coordination. Historical measurements above keep their original configurations.
The runner itself does not acquire cross-project CPU/IO locks.

Current production-object builds include the component and owned-snapshot
dependencies plus the native SHA adapter header. Build-only mode now writes
`build_complete=true`, `measurement_complete=false`, source/runner/object hashes
and retained binary paths to the requested JSON. It does not create a fixture.
[Both current compiler preparations](../../tests/qualification/cached-worker-build-actual-20261017.json)
passed and closed; this provides no new performance samples.

The [measurement preparation](../../doc/cached-worker-measurement-preparation-v1.json)
proposes32MiB, six jobs/batch, one warmup and five measured repetitions per
compiler/configuration. Its9GiB requested logical reads are a planning quantity,
not measured device IO. It is not admitted or execution-ready: a versioned shared
owner/IO contract and fresh finite IO coordination must precede measurement.
Do not infer whole-machine quiet, hard memory bounds or end-to-end sync scaling
from this cached digest microbenchmark.

## Current admitted matrix completed

The separate one-use shared benchmark subsequently passed all48batches/288digests
with actual primary-reader9GiB accounting and all CPU/IO resources closed.
[Current results and limitations](results/shared-current-20261017.md) distinguish
the cached workload, six-job scheduling geometry, sampled RSS/FD observations
and shared-machine timing from end-to-end sync or physical IO. The earlier
preparation above remains historical; its lack of admission is no longer the
current state. Admission4c9d02f3 is consumed and must never be replayed.
