# Adobe SDK validation core benchmark

This benchmark runs the qualified Adobe DNG SDK driver through production
`DngValidation`, `HelperSupervisor`, `SemanticWorkers` and `SemanticAdmission`.
It uses disposable synthetic files and never opens a photo library or catalog.
It measures the validation core, including worker hashing, executable pinning,
SDK decode and raw-digest checks, receipt parsing and post-validation hashing.
Synchronization, network traffic, candidate directory/property manifests,
resource forks, commit/archive work and Lightroom's validation UI are excluded.

The original SDK qualification controls contain only 16×16 raw samples; their
roughly 1–6 KiB files mainly test launching and protocol behavior. This workload
uses 6000×4000 16-bit RGGB CFA samples with deterministic horizontal/vertical
gradients, color biases and LCG noise. These are synthetic camera-like data,
without claiming camera or broader DNG corpus qualification. The seed's old
raw digest comes independently from Python MD5 over little-endian samples.
Adobe's test writer creates uncompressed, lossless JPEG and lossless JPEG XL
DNGs and supplies valid raw digests. The generator verifies compression tags,
whole-file SHA-256, positive receipts and a corrupted-digest control for each
output. Controls retain the actual receipts and SDK warnings/errors.

Use an existing separately obtained and qualified SDK build. Rebuild only the
test writer after updating this repository; this preserves the validator
executable and manifest byte-for-byte:

```sh
python3 tools/adobe-validator/build.py \
  --sdk-root /absolute/dng_sdk_1_7_1 --build-dir /absolute/adobe-validator-build \
  --fixture-only --jobs 4
```

Generate and qualify the bounded fixture set in a disposable directory:

```sh
python3 bench/adobe/fixtures.py --sdk-build /absolute/adobe-validator-build \
  --output /absolute/temporary/synthetic-dng-fixtures
```

The three encoded files total about 120 MiB on the recorded pattern; the seed
adds about 46 MiB. Negative-control copies are removed after checking. Fixture
dimensions are limited to 32 million samples. No SDK source or generated DNG
is included in this repository.

Run after other builds and CPU-heavy jobs finish. Use `--build-only` to check
compilation, or `--pilot` for one validation of each codec before a full run:

```sh
python3 bench/adobe/run.py --sdk-build /absolute/adobe-validator-build \
  --ocamlopt /absolute/compiler/bin/ocamlopt \
  --production-build /absolute/compiler-matched-make-snapshot \
  --fixtures-dir /absolute/temporary/synthetic-dng-fixtures \
  --workers 1,6,18 --cpu-credit-budget 18 --jobs 72 --repetitions 5 --control-repetitions 1 \
  --output bench/adobe/results/macos-x86_64-18-vs-36.json
```

Current OxCaml builds require `--production-build`, created by
`tests/build_snapshot.py` with Make and the same compiler. The runner checks
compiler/binary/source pins and links the actual checked core objects, including
the mailbox, rather than compiling unchecked stock interfaces. Stock can use
the same artifact route. `--build-only` retains its sources/executable/log and
saves a build receipt without executing the benchmark, fixture writer or SDK.
Build completion remains separate from measurement completion.

Coordinate native execution with Photo Root before a runtime pilot or benchmark.
`--start-file /fresh/caller-owned/path --coordination-timeout 600` waits after
compilation and before *all* SDK fixture generation and validation calls; an
absent marker expires without native work. This file coordinates CPU use and
does not establish Lightroom/native-owner admission or authorize preview work.
The default configured allowance is 18 credits; larger historical comparisons
require an explicitly different allowance and coordination. No fresh runtime
measurement or internally parallel SDK-host qualification follows from these
build changes. The production driver in this benchmark still uses one thread.

Validation batches now cancel peers at the first observed per-job failure,
drain every submitted participant, and close the checked worker pool before
reporting failure. SIGTERM/SIGINT set an atomic cancellation flag; the owner
loop performs helper cancellation/reaping. `--batch-deadline` cancels active
batch work before cleanup. This does not yet impose a single deadline on SDK
fixture generation plus all batches, or qualify abrupt SIGKILL recovery.
The draft finite pilot request was withdrawn pending that complete supervision
contract; do not treat its queued request as native admission.

Sources are snapshotted and compiled in a temporary directory with the chosen
native compiler's default flags. Each batch is a fresh process; pool creation
and shutdown are outside timing. All jobs read the same cached fixture through
independent descriptors. Admission matches validation-only Runtime defaults:
CPU permits equal the requested budget, domain count is capped by the runtime's
recommendation, transaction slots equal domains, and each admitted validation
reserves 1 MiB/8 descriptors from 512 MiB/512 credits. These estimates do not
cap an external SDK child's memory. Hash workers and single-thread SDK drivers
share the same weighted CPU budget.

Parallel configurations use one full warmup and five measured 72-job batches.
The one-permit control uses a one-file warmup and one measured 72-job batch,
avoiding redundant long serial runs. Measured rounds alternate forward/reverse
codec/budget order. Every receipt must identify the exact candidate and pinned
build, report valid structure, successful decode, a valid raw digest and zero
errors; warnings remain in the raw result. All CPU/child/resource credits and
worker jobs must be released after each batch.

Wall time is monotonic. Parent CPU includes all hash domains and owner-loop
work; reaped-child CPU comes from `getrusage(RUSAGE_CHILDREN)` and includes SDK
threads. Their sum divided by wall time is a logical CPU equivalent, not a
physical-core count. Peak admitted child slots and CPU permits are sampled at
1 ms; they are observed peaks and may miss short transitions. A child slot
spans admission through cleanup, rather than being a direct OS process census.
The JSON retains every raw receipt/stderr, timings, input/source/driver/compiler
hashes, host topology, qualification controls and sample summaries.

The SDK uses the same native decoder regardless of the OCaml compiler used for
the owner loop. This benchmark makes no OxCaml-specific speedup claim. Cache,
background activity, memory bandwidth and scheduling affect the result;
synthetic validation throughput does not establish full-sync or photo-library
performance.

## Recorded 18 versus 36 result

The [2026-10-13 raw result](results/macos-x86_64-18-vs-36.json) used an Intel
Mac with 18 physical and 36 logical CPUs, 128 GiB RAM, and the pinned Adobe
DNG SDK 1.7.1 build 2724 driver `unison-sdk171-2724-v1-single`. The owner loop
used OCaml `5.2.0+ox`; the SDK driver was the same qualified native executable,
with one SDK thread per file. Fixture sizes were 48.0 MB uncompressed,
39.0 MB lossless JPEG and 38.2 MB lossless JPEG XL, each decoding to 24 million
16-bit raw samples.

Each parallel entry is the median of five 72-file batches after one full
warmup. Parentheses show the observed minimum–maximum files per second.
The one-worker column is a single 72-file control, after a one-file warmup.

| Encoding | 1 worker, files/s | 18 workers, files/s | 36 workers, files/s | 36/18 median throughput |
| --- | ---: | ---: | ---: | ---: |
| Uncompressed | 1.25 | 16.46 (13.29–17.75) | 16.97 (15.93–19.77) | 1.031× |
| Lossless JPEG | 1.08 | 13.56 (12.92–15.01) | 15.22 (14.56–17.90) | 1.123× |
| Lossless JPEG XL | 0.43 | 5.39 (4.84–5.61) | 5.98 (5.67–6.04) | 1.109× |

Median 72-file wall times at 18/36 workers were 4.37/4.24 seconds uncompressed,
5.31/4.73 seconds JPEG and 13.36/12.05 seconds JPEG XL. CPU/wall medians were
17.50/32.23, 17.55/33.66 and 17.71/33.66 logical CPU equivalents respectively.
The median total parent-plus-child CPU per batch increased by 1.79×, 1.69×
and 1.71× at 36 workers. All sampled peak admitted child slots reached the
requested 1, 18 or 36 without exceeding that budget.

All 42 batches completed: 2,376 measured receipts and 435 warmup receipts.
Every validation checked the executable pin; every receipt identified the
correct candidate and build and reported valid structure, successful decoding,
a valid raw digest and zero errors. The SDK reported four warnings per file;
the raw receipts and stderr
are retained. All helper and admission resources returned to zero after
each batch, and compiled source hashes still matched the checkout at completion.

Team builds were idle during measurement. Ordinary user activity remained:
at preparation DiskWarriorRebuildServer consumed about 92% of one logical CPU,
WindowServer about 33%, and Classic about 3%; activity was not controlled during
the run. The batch ranges show the resulting variation. These cached synthetic
results support 18 as a balanced budget and 36 as an explicit throughput option
on this host; they do not establish a universal uplift or photo-library
performance. No automatic defaults were changed by this benchmark.

## Finite pilot lifecycle

`--pilot` uses one aggregate **300-second native phase**, including original
fixture generation, hashing, all ten fixture SDK calls and three pilot
validations. Compilation and coordination waiting precede that phase. It starts
cancellation eight seconds before the limit to allow child cleanup; an overrun
cannot be accepted even if later cleanup succeeds. Fresh generation totals
**13 SDK invocations**, at most seven generated inputs, one active helper.

The pilot links the checked production ML objects but compiles the helper C
backend with `UNISON_BENCH_CONTAINED_HELPERS`. This benchmark-only backend
preserves the outer group and signals individual helper PIDs. The outer owner
holds its leader PID until all other group members disappear, including after
abrupt Python failure. The normal Unison/throughput backend keeps its original
separate helper groups. Therefore the finite pilot is a functional/lifecycle
qualification, not an exact production-backend timing benchmark.

`AGGREGATE-CLOSED.json` records actual exit, reap, group observation and elapsed
time. An ambiguous group or failed observation leaves
`AGGREGATE-OWNERSHIP-UNRESOLVED.json` and fails; a timeout alone is never closure.
A failed phase can have a genuine closed receipt without successful validation.
Workspaces are retained. This trusted SDK route does not promise containment of
programs deliberately escaping process groups or surviving SIGKILL of the outer
supervisor. See [synthetic lifecycle controls](../../tests/adobe_native_deadline/README.md).
Photo Root must release a new finite SDK slot; source/mock evidence provides no
Adobe/Lightroom release and no preview, production or full benchmark permission.
