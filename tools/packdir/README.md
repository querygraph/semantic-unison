# unison-packdir

The packed-directory prototype from [`docs/packdir-design.md`](../../docs/packdir-design.md). It
stores the files of one directory `D` as members of one SQLite archive `D.sqlar`, in the
standard `sqlar` table that stock tools read, with Unison's own `unison_member` and
`unison_container` tables beside it. It's separate from Unison's sync code; its library
(`packdir`) is the part the sync integration will reuse.

```sh
unison-packdir pack-tree ROOT OUT [--depth 2] [--wal] [--batch-mib 256]
unison-packdir list C.sqlar
unison-packdir verify C.sqlar...
unison-packdir restore C.sqlar OUT_DIR [--skip-retained]
sqlite3 C.sqlar -AxC OUT_DIR      # stock restore: bytes, mode, mtime to the second
```

- **`pack-tree`** keeps every directory `--depth` levels under `ROOT` (the preview leaves
  `<H>/<HHHH>`) as `OUT/<rel>.sqlar`, one container at a time. It prints a JSON line with
  containers, files, bytes, seconds, MiB/s and files/s. A rerun stores only new and changed
  files, by size and nanosecond mtime, and marks files gone from `ROOT` as retained. A plain
  `OUT/<rel>/` directory beside a container is left as it is. A file named like one of its files
  isn't packed while the bytes are the same (`present-plain`). Once they differ, it's packed and
  kept updated (`packed-beside-plain`).
- **Each container** uses a 64 KiB page size, incremental auto-vacuum, a `DELETE` rollback journal
  (`--wal` for comparison) and `synchronous = FULL`. Every batch of at most `--batch-mib` is one
  transaction that bumps the container's epoch. Blobs are stored raw, and read back and
  SHA-256-checked after each commit.
- **Durability comes from barriers.** One `F_FULLFSYNC` runs every `--barrier-gib` (default 4)
  and at the end. Containers being written are listed in `OUT/.packdir-pending` until the final
  barrier. The next run verifies those, and any container whose file doesn't match
  `OUT/.packdir-state`. A damaged one is set aside as `D.sqlar.damaged-<time>` and packed again.
- **Unchanged containers aren't opened.** `OUT/.packdir-state` holds each container file's stamp
  and members, the role Unison's archive takes in the integration.
- **`verify`** runs `PRAGMA integrity_check`, then checks every member's SHA-256 and fingerprint,
  and that both tables pair up.
- **`restore`** writes every member with its mode and nanosecond mtime, SHA-256 checked.

It builds with dune on stock OCaml and OxCaml, using the opam `sqlite3` binding and dng-compare's
`dng-archive` library (SHA-256, nanosecond stat, `utimensat`). Both are optional: without them,
dune skips this tool.

```sh
dune build ./tools/packdir/main.exe
python3 tests/packdir/run.py --packdir _build/default/tools/packdir/main.exe
```

`UNISON_PACKDIR_CRASH_AFTER=N` exits inside a transaction after N stored files; it's for the
tests.

## Benchmark harness

`bench.py` copies one leaf set to a target disk by each method, and appends wall time and the
target disk's bytes written and I/O operations (from `iostat`) to `OUT/RESULTS.jsonl`. The
methods are:
- `plain`: Unison, one way and additive like the mirror profile, `clone = off`;
- `sqlar` and `sqlar-wal`;
- `cp` and `tar`, first runs only;
- `bundle`: Unison into an HFS+ sparse bundle.

```sh
python3 tools/packdir/bench.py first SRC /Volumes/Ten/packdir-bench/run1 --unison U --packdir P
python3 tools/packdir/bench.py incremental SRC /Volumes/Ten/packdir-bench/run1 --unison U --packdir P
python3 tools/packdir/bench.py sample DIR --gib 0.5     # small synthetic set for a dry run
```

`OUT` must be new for `first`, and its path must contain `packdir-bench`. The harness writes
nothing outside `OUT` and its sibling `OUT.work`, and it never deletes anything.
