# Primary-reader diagnostics

Enable `-debug semantic-reads` before the semantic runtime starts. The owner
prints one bounded line for a delivered, stable job's primary input reader.
The worker sends immutable counters through its existing bounded completion
mailbox; it never reads preferences or performs logging. Ordinary jobs create no
counter state. An idle-pool observer API supports trusted owner integrations.

Counts include successful nonempty `SemanticFile.read` and 64 KiB iteration
chunks, repeated ranges and hashing through that reader. They exclude nested
readers (including output verification), legacy/validator reads, partial or
cancelled readers, channel prefetch, syscalls and physical I/O. Counters saturate
instead of failing the operation; exact benchmark parsing rejects saturation.
These are diagnostic observations, never validation/publication authority.

The observer is captured before waking the reply, then invoked on the owner
after reply settlement. Changing observation for future jobs does not discard
the completed report. A throwing observer uses the existing error channel while
sibling replies and the pool remain usable. Selection changes require an idle,
open pool. Callback/read/stability failures return no reader report.

User-run Make entry points verify the saved compiler/binary and every recorded
production source pin before dispatch. Use a fresh successful build receipt:

```sh
BUILD_RECEIPT=/absolute/build-RESULT.json make -f tests/Makefile read-workers
BUILD_RECEIPT=/absolute/build-RESULT.json make -f tests/Makefile read-cli
make -f tests/Makefile read-parser
```

`DRY_RUN=1` prints the command without dispatch. Worker checks require a Make
snapshot; CLI checks also accept Dune. No target invokes Adobe or Photo.
The finite two-compiler sync matrix is also available without reconstructing
benchmark arguments:

```sh
STOCK_RECEIPT=/absolute/stock-RESULT.json OX_RECEIPT=/absolute/ox-RESULT.json \
  make -f tests/Makefile sync-functional
```

It runs 12 rows / 36 CLI calls on synthetic two-file 2 MiB fixtures, with
at most four configured endpoint CPU credits, exact output/basis/no-op checks,
and primary-reader diagnostics. This is a functional check, not a speed test.
Coordinate those four credits with other local work. Both receipts must match
current production sources; `DRY_RUN=1` checks them and prints argv without sync.

Equivalent direct commands using the matching compiler:

```sh
python3 tests/workers/run.py --ocamlopt /absolute/compiler/ocamlopt \
  --build /absolute/qualified-snapshot/src --read-stats-only --keep-work \
  --receipt /private/tmp/new-worker-read-report.json
python3 tests/read_stats/cli.py --build-receipt /absolute/build-RESULT.json \
  --report /private/tmp/new-cli-read-report.json
python3 tests/read_stats/parser.py
```

The six reader/worker groups include exact repeated/empty reads, invalid reads,
mutation before final stability checks, descriptor cleanup, owner execution,
reentrant observer changes, 48 queued hashes in a four-domain pool under three
CPU permits, and observer failure recovery. CLI checks use original synthetic
DNG-shaped files with Adobe disabled, exact SDE output, an old receiver hardlink
and a no-op. They do not validate DNG pixels or Adobe acceptance.

The [qualification](qualification.json) records stock/Ox Make+selftests, both
compiler-matched groups, both CLI checks, pure parser controls and the 12-row
functional harness with `--measure-primary-reads`. This small harness is not a
throughput comparison. Default behavior leaves collection off; nested/total
application I/O and complete resource/performance qualification remain open.
