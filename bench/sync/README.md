# Synthetic complete-sync benchmark

This runner measures actual Unison CLI synchronization with exact independent
result checking. It uses deterministic non-photographic TIFF/DNG-shaped files
under a private temporary directory. It never loads Adobe, Lightroom or the
preview generator, and never reads or writes photographic inputs, catalogs,
caches or Photo volumes. These inputs qualify transfer behavior, not DNG image
validity or Adobe-current-edits rendering.

## Completed warm128 benchmark — 2026-10-15

[Raw108 rows](results/warm-128MiB-4files-20261015.json) and
[sealed return](results/warm-128-v5-actual-return-20261015.json) preserve the exact
source/build/binary/compiler pins, all324 CLI/server settlements and actual
owner34823/c78138/exit0 terminal. Aggregate12254 closed/reaped in3426.064s
within7200s; no unresolved markers remained. Root was notified of resource
release. This one-use allocation is consumed; later sizes are not authorized.

Four128MiB generated files, fixed8KiB XMP each, one warmup and five measured
repetitions/configuration; order reverses on alternate repetitions. Updates
use a loopback bridge on one internal APFS volume. Caches are warm/uncontrolled.
Competing Photo work was held; unrelated host/OS activity was not continuously
measured or controlled. Reported wall times include each update CLI; fixture
generation, seed sync, independent verification and no-op sync are recorded
separately. Whole-batch time includes those stages.

Median update seconds (five samples per cell):

| Mode | Workers per endpoint | Stock OCaml | OxCaml |
| --- | ---: | ---: | ---: |
| ordinary | 1 | 9.942 | 9.585 |
| ordinary | 6 | 10.197 | 9.598 |
| ordinary | 8 | 9.962 | 9.609 |
| receiver-clone | 1 | 9.776 | 9.437 |
| receiver-clone | 6 | 9.763 | 9.437 |
| receiver-clone | 8 | 9.756 | 9.441 |
| semantic | 1 | 18.153 | 18.094 |
| semantic | 6 | 9.269 | 9.248 |
| semantic | 8 | 9.268 | 9.212 |

At8 workers, OxCaml semantic median9.212s versus ordinary9.609s is about4.1%
lower elapsed time in this workload; stock semantic9.268s versus ordinary9.962s
is about7.0% lower. Semantic1→8 improves about1.96x on both compilers.
At8 workers, stock/Ox semantic medians differ by only about0.6%; this does not
establish a general OxCaml speed advantage. Six and eight semantic workers
perform similarly on four files. Ordinary-mode worker settings do not turn
the legacy transfer path into the semantic domain pool.

Across the measured semantic rows, production counters report12,288 logical
write bytes in four attempts,32,768 payload bytes, and an Ox8 protocol median
51,918 bytes. Ordinary Ox8 protocol median379,437 bytes; receiver-clone379,438.
Receiver-clone inherits536,805,376 bytes of the536,870,912-byte output, leaving
a65,536-byte non-inherited materialization model. Ordinary full-extent model
is536,870,912 bytes. Only the semantic figure counts actual returned write
bytes; the other materialization figures are models, not pwrite telemetry.

The main demonstrated benefit is lower logical materialization and protocol
traffic, with modest wall-time gain once full verification is included. These
results do not measure physical APFS writes/shared blocks, total application
reads, internal parse/hash/commit stages, aggregate RSS, FD/queue peaks, cold
cache, other devices, real networks, original-upstream baselines, SDK cost or
photographic-corpus performance. No production speed or durability claim follows.

Use already-qualified private builds. The runner never compiles or writes
build products into the shared checkout:

```sh
python3 bench/sync/run.py \
  --binary stock=/absolute/stock-snapshot/src/unison \
  --binary ox=/absolute/ox-snapshot/src/unison \
  --compiler stock=/path/to/stock/ocamlopt \
  --compiler ox=/path/to/ox/ocamlopt \
  --reference original=/absolute/original-snapshot/src/unison \
  --workers 1,6 --loopback-cpu-credits 18 --file-mib 32 --files 8 \
  --output /absolute/path/results.json
```

`--qualification` selects two 2 MiB files, budgets 1 and 2, zero warmups and
one measured sample per row. This is a finite functional qualification of the
harness, not a throughput or worker-selection recommendation. `--prepare-only`
records arguments, compiler configuration, binary identity and provenance
without creating fixtures or invoking synchronization. A performance run
requires at least one warmup and five measured repetitions. Coordinate the
measurement window with other work and record `--background-note`; no cache
flush, priority, CPU pinning or thermal control is performed.

Current binary rows select ordinary transfer with receiver cloning off,
ordinary transfer with receiver cloning on, and DNG semantic cloning on.
Every default row uses a loopback SSH replacement, so same-volume local source
cloning cannot bypass the receiver algorithm being compared. The optional
`--modes source-clone` row exercises actual local/local source-clone priority
separately. References get no new preferences and one row per repetition; name
them accurately. An original 2.53.5 binary is not the selected newer upstream
8772d26a baseline. Adding both reference binaries strengthens that comparison.

The runner configures the same worker budget on both processes. CPU credits
apply per endpoint, so a same-host pair can consume two budgets; this is not
a machine-wide CPU cap. --loopback-cpu-credits checks the sum of configured
semantic/helper budgets before any fixture or sync starts. The current18-credit
run uses1/6 per endpoint (maximum12 combined). Local source-clone-only rows use
one endpoint budget. Unqualified reference budgets are rejected when this bound
is selected; ordinary owner/proxy/OS CPU work is outside the credit accounting. Transfer concurrency is `max(2, worker_budget)`. Ordinary
transfers do not use semantic domains, so their worker label describes the
configured preference and transfer concurrency, not observed domain use.
The runner supports 1/2/4/6/8/18/36; it does not run a broad matrix in qualification
mode. Multi-gigabyte inputs, mixed/unsupported/growing packets, real SSH links,
cross-volume roots and non-APFS receivers remain separate benchmark work.
Defaults use one worker budget and two 32 MiB files; a larger multi-budget
matrix in the example is an explicit choice.

Each row creates fresh roots and archive state, seeds the receiver through the
same CLI configuration, hardlinks the old receiver inode outside both roots,
then changes one XMP attribute byte while preserving layout and all protected
payload bytes. Source and receiver payloads are seeded pseudorandom bytes,
apart from a small classic TIFF header and padded 8 KiB XML packet. The JSON
records generator seeds, sizes and complete before/after SHA-256 identities.
An independent first-MiB compression probe documents this distribution; it
does not establish a representative photograph compression ratio.

The measured update includes process/supervisor startup, connection, scanning,
planning, transfer, verification, publication, archive saves, shutdown and
server settlement. Fixture creation, seed sync, source edit and independent
post-run verification have separate receipts and stay outside update timing.
Every accepted row must:

- Select the configured receiver algorithm exactly once for every file.
- Produce the independently expected SHA-256 on both replicas and pass a
  streaming complete byte comparison.
- Preserve the old receiver hardlinks' original complete hashes.
- Complete a second sync without replacing receiver inodes or changing bytes.
- Leave no staging names in either root, and reap the harness-owned server
  supervisor and its native server.

The output starts with `complete:false`, saves after every accepted stage, and
becomes complete only when the entire requested matrix passes. Failures leave
an incomplete receipt; failed or partially qualified rows are not evidence of
optimization. Main and supervisor output streams are both drained continuously
with bounded retained buffers; truncation rejects a row. No unbounded supervisor
disk log is produced.
Each accepted row removes its own private files after exact byte/basis/no-op
checks and native process closure. Cleanup is outside update timing and recorded
separately. Thus prior rows do not accumulate corpus storage during a matrix.
A fresh capacity admission requires four full corpus extents plus64MiB of
headroom, covering source/old receiver/new output/staging conservatively; it is
not APFS physical-allocation proof. The compression probe reads only1MiB.
Temporary roots and private state are removed on exit. Commands, logs and
their synthetic paths are retained in the JSON.

The benchmark owns the protocol supervisor directly. Unison's `remote.ml`
terminates its SSH launcher at client exit with only a 10 ms grace period;
the thin launcher connects to the owned supervisor over a private Unix socket.
This keeps counters and native-server reap separate from launcher termination,
without detached children. The supervisor counts successfully forwarded raw
Unison protocol bytes in both directions, including handshake, control traffic,
manifests and archive coordination. It excludes its bounded launcher command
header. These are whole-protocol counts, not file payload counts. The Python
bridge, Unix socket and pipes add overhead. They do not reproduce encrypted
SSH or physical-network throughput.

Each subprocess group keeps its leader unreaped with `waitid(WNOWAIT)` until
group cleanup, including an already exited supervisor. This reserves the PID
against reuse before group signaling. A supervisor transport exception,
SIGTERM/SIGINT cancellation, or its deadline runs native-child cleanup in a
`finally` block: send TERM, escalate a hanging child to KILL, then `wait4` the
exact native child before writing the failed receipt and exiting. The parent
signals the supervisor cooperatively and gives it time to perform that reap.
A supervisor that exits abruptly before cleanup has no native-owner receipt;
the parent still kills its remaining reserved process group before reaping the
leader. That fallback never becomes an accepted benchmark row or native-owner
reap claim. Darwin's empty-group EPERM is accepted only after a bounded `ps -g`
probe sees no members or only the still-reserved leader zombie. Other members
or ambiguous probe output fail qualification.

OS `wait4` receipts record user/system CPU, maximum RSS, faults and native block
operation counters. CPU reports can include reaped descendants; the runner
does not sum overlapping client/server reports. Darwin reports RSS in bytes,
Linux in KiB. Individual maximum RSS values are not aggregate process-tree
peak RSS, enforced memory caps or child-memory admission evidence. OS block
operations are not byte counts or physical APFS write telemetry.

Successful semantic updates supply production `SemanticDelta` returned logical
write-byte counts and attempted write-call counts, plus complete packet payload
sizes. The recorded 2026-10-13 benchmark snapshot uses `Unix.LargeFile.lseek`
and `Unix.write_substring`; its receipts describe that historical path. The
later positional-write implementation uses an admitted borrowed writer and
native POSIX `pwrite` for each bounded chunk; Windows retains seek/write.
Bytes increment after a successful returned write, while primitive attempts
include EINTR retries. The benchmark fields remain application counters rather
than independently observed syscall or physical-write telemetry. This change
does not rerun or reinterpret the historical elapsed measurements. The generic
receiver supplies the exact same-offset inherited-byte count. Its reported
non-inherited logical output is a model, `complete_size - inherited_bytes`,
not syscall-level accounting. Ordinary full output uses the complete output
extent as its model. Source cloning uses a zero-data-rewrite model when its
production completion trace qualifies. None of these models proves physical
sharing, allocation or storage write amplification. Application-level read
bytes, internal hash/parse/verify/commit times, descriptor/queue peaks,
aggregate RSS and physical storage writes remain explicitly null/unmeasured.

Binary SHA-256, version, compiler configuration and available build-log hash
identify each artifact. When a binary is in a known `src/unison` snapshot,
the runner also pins that snapshot's source files. Package coverage uses the
enumerated 313-input observation receipt's paths plus newly added source paths,
with every hash read from the actual selected snapshot. The final stock/Ox
snapshots have 315 such inputs, including `ioAdmission.ml/.mli`; no prior
qualification is asserted for their changed bytes. Selecting the historical
observation-qualified binaries additionally verifies their exact 313-input
receipt. These are the measured binary's source pins; repository HEAD records
runner context and does not assert that a changing checkout was the binary's
build source.

`python3 bench/sync/check.py` runs tiny Adobe-free controls for unchanged fixture
complements, bounded output capture and timeout, rejection of missing/wrong
or mixed algorithm traces, exact protocol byte counts excluding command
headers, native nonzero exit propagation and server reap. It injects both
reader-creation failures, an output-pump error, an ignoring-TERM native hang,
client timeout, and abrupt supervisor exit. Every failure must retain a failed
outcome, show the exact native PID absent and the supervisor reaped. The first
three supervisor failures require native-owner `wait4` proof; abrupt exit
requires reserved-group cleanup and deliberately has no such proof.

The [bounded 2026-10-13 qualification](results/qualification-20261013.json)
completed 13 rows on stock OCaml 5.5.1, OxCaml 5.2.0+ox, and the preserved
original 2.53.5 stock build. Current rows each exercised three modes at budgets
1/2; the original had one reference row. Each row passed exact source/receiver
hashes, complete byte equality, preserved hardlinked old-basis hashes,
no-op inode stability, staging cleanup and native server/supervisor reap.
The temporary roots were on the internal APFS Data volume, same device.
Independent functional validation work could overlap; host activity remained
uncontrolled. The exact final current binaries and all 315 package input hashes
are in the receipt. The older 313-input qualification run was retained privately
and is not confused with the final production state.
The earlier normal-path receipt and controls are also preserved unchanged as
`*-before-cleanup-review.json`. Their old field names/descriptions incorrectly
said attempted `pwrite` bytes; those values were returned logical write bytes.
They qualify their normal rows, and do not qualify the subsequently discovered
exception/timeout cleanup gap.

For the two files totaling 4 MiB, the current runs observed:

| Mode | Non-inherited logical output | Successfully forwarded whole-protocol bytes |
| --- | ---: | ---: |
| Ordinary, receiver cloning off | 4,194,304 bytes (output model) | 34,080 |
| Generic receiver clone | 16,384 bytes (output minus inherited-byte model) | 34,081 |
| DNG semantic clone | 6,144 returned logical write bytes, 2 attempted calls, completed transaction | 30,298 stock / 30,337 Ox |

The SDE payload remained the complete 8 KiB packet per file. Its smaller logical
write count comes from the 4 KiB absolute comparison-window policy, clipped
at the packet boundary; it is not a single-byte physical write claim. Receiver
cloning preserved same-offset output bytes without changing ordinary protocol
traffic. Whole-protocol counts include the new inspection/transfer negotiation
and do not isolate payload traffic. The elapsed update receipts ranged roughly
0.27–0.40 seconds across current rows and were dominated by a tiny warm workload
and startup/bridge costs. One sample per configuration supports neither an
elapsed-time speedup nor an OxCaml-specific gain. It does not establish
18-versus-36 behavior or complete the SOL benchmark matrix.

## Checked worker successor, 2026-10-14

The [finite successor qualification](results/checked-worker-qualification-20261014.json)
passes12 exact sync rows on the stock/Ox executables qualified at77234c5.
Both binaries independently bind the349 frozen production inputs, including
mode-interface templates. Fixture/capture/ownership controls pass; explicit
loopback over-budget and low-capacity controls reject before any fixture/sync.
The owned low-capacity temporary is removed and its output stays incomplete.

The larger current performance matrix uses eight32MiB synthetic files, worker
budgets1/6 per endpoint, one warmup and five measured repetitions. It compares
ordinary, receiver-basis cloning and semantic DNG updates. All72 rows are now complete and accepted, including12 warmups and60 measured
rows. All576 file updates reconstruct exact bytes, retain old hardlink hashes,
preserve no-op receiver inodes and close processes before removing fixtures. This exercises real checked production CLI transfer,
not cached hashing alone, but remains warm same-host transport with synthetic
payloads and no Adobe/Photo invocation. Internal read/stage timing, aggregate
RSS, hard global caps, real links and representative photographic workloads
remain separate M6 gates.

The [raw performance matrix](results/checked-worker-performance-20261014.json)
and [independent receipt audit](results/checked-worker-performance-audit-20261014.json)
report median update seconds (five measured repeats):

| Mode | Stock,1 worker | Stock,6 workers | Ox,1 worker | Ox,6 workers |
| --- | ---: | ---: | ---: | ---: |
| Ordinary | 5.773 | 4.688 | 5.004 | 4.121 |
| Receiver clone | 5.667 | 4.600 | 4.994 | 4.150 |
| Semantic DNG | 9.839 | 5.266 | 9.269 | 4.788 |

Semantic writes are24576 logical bytes/eight write attempts per256MiB row,
with65536 editable payload bytes. Generic cloning reports65536 non-inherited
logical output bytes; ordinary transfer models the full268435456-byte output.
These counters have different evidentiary scope and none measures physical
writes. Semantic six/one-worker elapsed scaling is1.87x stock and1.94x Ox;
semantic verification is still slower than ordinary transfer in this warm-cache
same-host run. Avoid presenting logical write reduction as elapsed acceleration.
Stock/Ox are different compiler versions; no universal compiler gain or cold
storage/network behavior follows. Warmups remain visible, including the slow
23.314-second first stock semantic single-worker row; it is excluded only by
the predeclared warmup policy. The remaining memory/read/stage/real-network
and native SDK qualifications are open.


## Optional primary-reader diagnostics

The opt-in `--measure-primary-reads` flag enables
`-debug semantic-reads` on current endpoints. It parses owner-delivered stable
worker primary-reader reports into `primary_reader_reads`, independently of
`application_read_bytes`, which remains unknown. Client and server job IDs have
separate namespaces. Malformed/duplicate/saturated reports reject the measurement;
semantic rows require reports. An empty report set means unavailable or no
primary-reader jobs, never a measured zero. Reference rows remain uninstrumented.

These counts include repeated reads delivered through each job's primary input
reader. Nested readers (including output verification), legacy/validator reads,
partial/cancelled readers, channel prefetch, syscalls and physical disk I/O are
excluded. This option changes diagnostics/wire overhead and must be recorded
when comparing samples; it establishes no speedup or total-I/O reduction.

Pure checks, with no compiler, Unison or SDK process:

```sh
python3 tests/read_stats/parser.py
```

[Functional qualification](../../tests/read_stats/qualification.json) covers
current stock/Ox core builds, reader/worker controls, both exact CLI paths and
twelve small full-harness rows. It is not throughput, physical-I/O, full-read or
whole-process resource qualification. This option invokes no Adobe validator;
SDK execution still requires its own fresh coordinated admission.

## Whole-batch ownership successor (source checkpoint)

`prepare_plan.py` now emits a fresh source-matched plan including the full
324-CLI batch's proposed 7,200-second owned aggregate and controller pin.
`run_bounded.py` requires a fresh exact Root allocation binding the plan, batch,
workspace, source hashes, command, limits and start deadline. It executes the
existing matrix inside an independently timed retained worker and audits all
rows plus each client/supervisor/native-server receipt before recording success.
Worker-group closure is separate from per-CLI/server settlement. Cancellation or
incomplete evidence retains unresolved markers rather than a completed result.
SDK callers of the shared aggregate retain their default300-second ceiling.

This successor is **source-only**, not timing-allocated or lifecycle-qualified.
The interrupted60597 attempt is stopped/incomplete and cannot resume or replay
under a delayed ACK. Fresh real fake-child lifecycle controls and Root review
must precede any new timing dispatch. Pure checks launch no process:

```sh
python3 bench/sync/interrupted_receipt_test.py
python3 bench/sync/bounded_source_test.py
```

Historical 216-CLI receipts can be read by the pure auditor without relabeling
those historical measurements as current. The receipt-preservation correction
carries the actual settled outcome on the original exception; it does not
retroactively reconstruct a missing client receipt from the stopped attempt.
