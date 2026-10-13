# Synthetic complete-sync benchmark

This runner measures actual Unison CLI synchronization with exact independent
result checking. It uses deterministic non-photographic TIFF/DNG-shaped files
under a private temporary directory. It never loads Adobe, Lightroom or the
preview generator, and never reads or writes photographic inputs, catalogs,
caches or Photo volumes. These inputs qualify transfer behavior, not DNG image
validity or Adobe-current-edits rendering.

Use already-qualified private builds. The runner never compiles or writes
build products into the shared checkout:

```sh
python3 bench/sync/run.py \
  --binary stock=/absolute/stock-snapshot/src/unison \
  --binary ox=/absolute/ox-snapshot/src/unison \
  --compiler stock=/path/to/stock/ocamlopt \
  --compiler ox=/path/to/ox/ocamlopt \
  --reference original=/absolute/original-snapshot/src/unison \
  --workers 1,2,4,8,18,36 --file-mib 32 --files 8 \
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
a machine-wide CPU cap. Transfer concurrency is `max(2, worker_budget)`. Ordinary
transfers do not use semantic domains, so their worker label describes the
configured preference and transfer concurrency, not observed domain use.
The runner supports 1/2/4/8/18/36; it does not run a broad matrix in qualification
mode. Multi-gigabyte inputs, mixed/unsupported/growing packets, real SSH links,
cross-volume roots and non-APFS receivers remain separate benchmark work.
Defaults use one worker budget and two 32 MiB files; the full six-budget
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
