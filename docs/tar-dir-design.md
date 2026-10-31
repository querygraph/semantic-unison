# Packed-directory replicas (`packdir`): design for the Quasar → Ten preview mirror

Status: proposal from the Photo session (2026-10-31), for unison-5f to review and build.
Nothing here is implemented. The mirror stays postponed until the user and unison-5f agree on it.
The file keeps its original name. The first draft used tar only. This revision compares
container formats and recommends SQLite archives, keeping tar as the fallback.

## Problem

The Lightroom preview mirror (`~/.unison/previews-quasar-ten.prf`) copies Quasar's live cache
`/Volumes/Quasar/Lightroom/Alexy Previews.lrdata` one way to Ten. The cache is about
9.6 million small files, averaging about 0.6 MiB each, in a fixed two-level layout:

```
Alexy Previews.lrdata/<H>/<HHHH>/<FILE-UUID>-<digest>_<longEdge>     (JPEG level, name 74 bytes)
```

There are 16 top directories and 4,096 leaf directories under each, so 65,536 leaves. A sample
of leaves held 78–150 files and 75–165 MiB each.

Ten is a single 20 TB HDD. The user has decided it stays **Journaled HFS+**. It will not be
converted to APFS: APFS on a spinning disk is slow with millions of small files, and Apple
recommends HFS+ for HDDs. So `clone = auto` gives nothing on Ten, and a plain file-per-file
mirror is limited by about 200–270 IOPS of file creation and metadata seeks. My estimate for the
first full run is 20–40 h of Unison time; a plain `cp` would take 10–20 h. Both are estimates,
not measurements.

## Proposal

Let one replica store chosen subdirectories **packed into container files**, while the other
replica stays a plain tree. Unison still reconciles **per member path**: reports, `ignore`,
fingerprints and `nodeletion` all work on `0/0001/<name>`. Only the storage on the packed side
changes.

The container format is a pluggable backend behind a narrow interface:
`list`, `stat`, `read member`, `apply batch (put/keep) atomically`, `verify` and `close`.

## Container formats considered

What matters here:
1. writes to one HDD that are streaming-bound, not seek-bound;
2. reading one member without a scan;
3. updating one member without rewriting the container;
4. crash safety;
5. restore with stock tools and no Unison;
6. per-member integrity.

| Format | Random read | Member update | Crash safety | Stock restore | Notes |
|---|---|---|---|---|---|
| **SQLite archive (`sqlar`)** | B-tree lookup | in place, transactional | WAL/rollback journal, `fullfsync` | `sqlite3 x.sqlar -AxC dir` (macOS's own sqlite3 3.43 works) | Recommended |
| ZIP, stored (no compression) | central directory | append member + new central directory; dead space until compacted | weak: a crash while rewriting the end needs a local-header scan to recover | `unzip`, `ditto -x -k`, Finder, Python `zipfile` | CRC32 only; mtime needs extra fields; ZIP64 needed above 4 GiB |
| pax tar + trailing index | via own index | whole-container rewrite | tmp + rename | `tar -xf` | First draft; simplest format, worst updates |
| Append-only pack + index (git-pack/Bitcask style) | own index | append; periodic compaction | log replay | needs our reader | Fastest writes, but a custom format makes restore depend on our code |
| Sparse bundle / disk image with an inner filesystem | transparent | transparent | inner filesystem's | `hdiutil attach` | No Unison change, but the inner filesystem still does per-file metadata I/O, so this moves the seek problem rather than removing it; worth one benchmark |
| squashfs / DwarFS image | yes | rebuild only | n/a | needs FUSE on macOS | Read-only; doesn't fit a live mirror |
| restic / kopia / borg repository | via index, mountable | append packs, snapshots | yes | needs that tool | A full backup system off the shelf; a useful comparison benchmark, but it isn't a mirror and isn't Unison |

Throughput is about the same for every format, because each one ends up writing sequentially to
the platter. They differ in what an incremental run costs, and in how a member is reached
afterwards.

### Recommendation: SQLite archive

- **Updates are proportional to the change.** Changing one level touches about one blob's worth
  of pages plus a few B-tree pages. tar would rewrite the whole container.
- **Containers can be larger** for the same reason. That cuts the file count further without
  making updates expensive. See granularity below.
- **Durable atomic commits are built in.** One transaction per batch, `PRAGMA synchronous=FULL`
  and `PRAGMA fullfsync=ON`. The last one uses `F_FULLFSYNC` on macOS, which really flushes the
  drive's cache, which plain `fsync` does not.
- **Restore with stock tools** using the standard `sqlar` table: `sqlite3 x.sqlar -AxC dir`.
  On this Mac I checked that a 600 KB random member is stored raw (`sz == length(data)`) and
  extracts byte for byte. Python's stdlib `sqlite3` is a second stock reader.
- **Integrity:** an explicit sha256 column, and `PRAGMA integrity_check` for structure.
- **Precedent on this pipeline:** Lightroom's own `previews.db` / `root-pixels.db` are SQLite
  databases holding the same kind of data.

Costs and limits:
- **Free pages.** Overwrites leave free pages; the database reuses them rather than shrinking
  the file. Use `auto_vacuum = INCREMENTAL` and run `incremental_vacuum` during idle time, never
  a full `VACUUM` of a large container during a run.
- **Blobs** are stored in overflow-page chains. With `page_size = 65536`, a 0.6 MiB level is
  about 10 pages, mostly contiguous when the file grows by appending. Reads stay sequential-ish.
- **Precision.** `sqlar.mtime` is whole seconds, so nanosecond mtime and the fingerprint go in a
  side table (below). Stock extraction restores mtime to the second.

### ZIP as the alternative if a "plain file format" is required

ZIP stored is the best of the classic archive formats for random access. Stock macOS tools open
it, and appending a changed member plus a new central directory is cheap. Two things make it the
second choice: dead space needs compaction rewrites, and the end of the file is a crash window
(the central directory is overwritten in place). If it's chosen:
- write each update as "append members, then append the new central directory after them", never
  overwriting the old one in place, so a crash leaves the previous directory readable;
- store sha256 and nanosecond mtime in a private extra field;
- compact by rewriting into a temporary file and renaming it.

## Schema (SQLite backend)

```sql
PRAGMA page_size = 65536;          -- set before the first table
PRAGMA auto_vacuum = INCREMENTAL;
PRAGMA journal_mode = WAL;         -- or DELETE; see open questions
PRAGMA synchronous = FULL;
PRAGMA fullfsync = ON;

CREATE TABLE sqlar(                -- standard SQLite archive table; stock tools read only this
  name  TEXT PRIMARY KEY,          -- path relative to the packed directory, e.g. '0001/<FILE-UUID>-<digest>_920'
  mode  INT,                       -- 0100644 unless perms says otherwise
  mtime INT,                       -- seconds
  sz    INT,                       -- original size; data is stored raw, so sz == length(data)
  data  BLOB
);
CREATE TABLE unison_member(        -- Unison's own metadata; ignored by stock tools
  name      TEXT PRIMARY KEY REFERENCES sqlar(name),
  mtime_ns  INT NOT NULL,
  fp        BLOB NOT NULL,         -- Unison fingerprint of the member's bytes
  fpalg     TEXT NOT NULL,         -- engine identity; never compare records with different fpalg
  sha256    BLOB NOT NULL,
  retained_deleted INT NOT NULL DEFAULT 0   -- deleted on the plain side, kept here under nodeletion
);
CREATE TABLE unison_container(key TEXT PRIMARY KEY, value TEXT);  -- format version, packdir pattern, epoch
```

- **Data is never compressed.** JPEG levels don't compress, and raw storage keeps blob reads
  direct. Stock `-Ax` extraction treats `sz == length(data)` as raw.
- **One transaction per propagation batch** of a container: all of that container's puts, plus
  its `unison_member` rows. Unison's archive is updated only after `COMMIT` returns.

## Granularity

SQLite updates in place, so containers don't have to be small:

| Unit | Containers | Size each | Note |
|---|---:|---:|---|
| leaf `<H>/<HHHH>` | 65,536 | ~100 MiB | the unit tar would need |
| `<H>/<HHH>` (16 leaves) | 4,096 | ~1.6 GiB | **proposed default** |
| `<H>` (top) | 16 | ~330 GiB | too much in one file to lose or check at once |

The proposed default puts Ten at 4,096 files, about 1.6 GiB each. A damaged container costs
about 0.03% of the mirror, and `integrity_check` on one container takes seconds.

Configuration:

```
packdir = Path {*} -> /Volumes/Ten/Lightroom/Alexy Previews.lrdata
packformat = sqlar                  # sqlar | zip | tar
packgroup = 3                       # group <H>/<HHHH> by the first 3 hex chars of the leaf name -> <H>/<HHH>.sqlar
packmax = 8 GiB                     # guard: report and refuse a container that would grow past it
```

- Only the stated root stores containers.
- Nested patterns, `packdir` on both roots, and a plain file whose name collides with a
  container are all refused.
- Ten is HFS+, so set `clone = false` for that root, or report that `clone = auto` has nothing
  to clone.
- The JPEG-XMP semantic profile does not apply inside containers in v1; a metadata-only change
  rewrites the member's blob.

## Update model

1. **Reconcile per member.** Additions and changes take the plain side's bytes. Deletions on the
   plain side are **retained** while `nodeletion` holds for the packed side
   (`retained_deleted = 1`, logged as `retained-deleted`), the same as today's additive rule.
2. **Group actions by container**, and per container run one transaction: insert or replace the
   `sqlar` row with its blob, then upsert `unison_member`. Hash the bytes as they're read from
   the plain side.
3. **Verify:** after `COMMIT`, read back the changed blobs, compare sha256, and only then commit
   Unison's archive entries. This is the packed-side equivalent of Unison's post-transfer
   fingerprint check.
4. **Crash:** SQLite rolls back an uncommitted transaction, and Unison's archive never got ahead
   of the container, so the next run simply redoes that batch.

## Unison archive and scanning

- **Plain side:** unchanged. `fastcheck` uses size and mtime.
- **Packed side:** each container is one node whose member table is read from `unison_member`
  with a single indexed query. No member data is read for change detection. A container whose
  `unison_container.epoch` changed outside Unison is re-listed and reported.
- **Reports and dry runs** show member paths.
- **First run against Ten's existing plain tree:** the old leaf directories are pre-existing plain
  content. Report them and don't touch them; migrating them is out of scope. The Photo session
  clears Ten's old cache separately, with the user's approval.

## Parallelism and I/O budget

- **Readers and hashers on the plain side** (Quasar) run in parallel within `semanticworkers`
  and `semanticcpubudget`.
- **One writer per packed volume** by default (`semanticvolumejobs = 1` for a rotating disk).
  Concurrent transactions into several containers on one HDD turn sequential writes back into
  seeks.
- **Batch size** of about 256 MiB per transaction limits WAL growth and the cost of a crash.
- **Checkpoint** the WAL after each container batch, so the main file stays the whole truth
  between runs.

## Restore and the Photo side

- **Full restore with stock tools:**
  ```
  for c in */*.sqlar; do d=$(dirname "$c"); sqlite3 "$c" -AxC "$d"; done
  ```
  This restores names, bytes, mode and mtime to the second.
- **Exact nanosecond mtimes:** a small `tools/packdir-restore` reapplies them from
  `unison_member` and verifies sha256.
- **Random access for Photo's carry-over tools:**
  `SELECT data FROM sqlar WHERE name = ?` (or `readfile`-style blob I/O).
- **Retained-deleted members:** the stock restore extracts them too. `packdir-restore` can skip
  them on request.

## Tests (synthetic fixtures only)

- **Round trip per backend:** generated tree; extract with the stock tool (`sqlite3 -Ax`,
  `unzip`, `bsdtar`) and with Python's stdlib; compare bytes.
- **Incremental:** add, change and delete (retained) members; only the affected containers'
  rows change; the member table matches a full content scan.
- **Crash injection:** kill during a transaction, between `COMMIT` and Unison's archive update,
  and during WAL checkpoint. The next run recovers and converges.
- **Corruption:** a flipped blob byte (caught by sha256), a torn page (`integrity_check`), and a
  missing `unison_member` row. Each is detected and reported, never silently trusted.
- **Guard tests:** `packdir` on both roots, nested patterns, and a container-name collision are
  refused.
- **Benchmark** on a 50 GiB synthetic leaf set onto an HFS+ HDD: plain Unison, `packdir` for each
  backend, `cp -R`, a `tar | tar` pipe, a sparse bundle, and restic or kopia, for both first-run
  and 1% incremental runs. Report honest wall time and IOPS before any claim.

## Open questions for unison-5f

1. **WAL or rollback journal** on HFS+? WAL is faster for batches but adds `-wal`/`-shm`
   companions. This mirror allows no foreign readers during a run, so either works.
2. **Fingerprint** for `fp`: Unison's stock fingerprint, or the semantic engine's hash, given the
   rule that records from different engines are never compared?
3. **Unison's own archive:** can container nodes reuse the existing archive format with a new
   node kind, or does it need a version bump?
4. **Default grouping:** is `packgroup = 3` (4,096 containers of ~1.6 GiB) right, or is the leaf
   level better for blast radius?
5. **Pack sizes:** should the backend interface also let restic- or kopia-style packs be a
   future backend, or is that out of scope for Unison?
