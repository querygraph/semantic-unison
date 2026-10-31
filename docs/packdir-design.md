# Packed directories in `.sqlar` archives: amended design

Status: Unison's amendment (2026-10-31) to Photo's proposal
[`tar-dir-design.md`](tar-dir-design.md), for discussion in the mailbox
([`photo-to-unison.md`](photo-to-unison.md) / [`unison-to-photo.md`](unison-to-photo.md)).
Nothing is implemented. The Quasar → Ten mirror stays postponed until the user starts it.

The proposal stands where this file doesn't change it: SQLite archives in the standard
`sqlar` table, raw blobs, a `unison_member` side table, one writer per HDD, retained
deletions, verification before Unison's archive moves, and stock-tool restore. The changes
are listed first, then the design as a whole.

## What changes, and why

1. **One container per directory.** A packed directory `D` is stored as one file `D.sqlar`
   beside where `D` would be, holding `D`'s files as members. For the preview cache, that means
   each leaf `<H>/<HHHH>/` becomes `<H>/<HHHH>.sqlar`. That's 65,536 containers of about 71 MiB
   (about 55 files each), so the cache's 3,616,982 files (4.43 TiB, Photo's corrected figures in
   P-2) become 65,536 files on Ten.
   - The unit is the one the user named: lots of small files in a directory.
   - There's no grouping rule to configure, and no member name gets a directory prefix.
   - A single directory restores with `sqlite3 D.sqlar -AxC D`.
   - A damaged container loses about 0.0015% of the mirror.
   - About 71 MiB per transaction already streams on an HDD. Larger containers would buy little
     and make each loss bigger.

   `packgroup` is dropped from v1.
2. **Rollback journal, not WAL: `journal_mode = DELETE`.** A run mostly adds new blobs at the
   end of the file, and a rollback journal saves only the old contents of pages it changes, so
   new pages are written once. WAL writes every page twice, once to `-wal` and again at the
   checkpoint, which doubles the write volume on the one disk that limits the run. Keep
   `synchronous = FULL` and `fullfsync = ON`.

   This replaces U-1's `TRUNCATE`. The prototype's tests showed that `TRUNCATE` leaves an empty
   `D.sqlar-journal` beside every container, which would double the file count on Ten. A run
   commits about one transaction per container, so `DELETE`'s journal create and delete is one
   pair per container, negligible next to a 71 MiB write. Between runs each container is then a
   single file, with no `-journal`, `-wal` or `-shm`.
3. **v1 is one-way into the packed replica.** The packed root must be local and must never be
   a source. The profile already has `noupdate`, `nocreation` and `nodeletion` for the plain
   root, plus `force`/`prefer`, so Unison never reads member data as a source. It only reads
   members back to verify them. Two-way packed sync, and packed replicas over ssh, are later
   work.
4. **No change to the archive format.** Unison's archive keeps its `ArchiveDir`/`ArchiveFile`
   nodes. A container is listed as the directory it stores, and members as its files. Two
   things keep this safe:
   - The packed root's identity in the archive name includes the packdir setting. So a Unison
     run without `packdir`, or with a different one, never picks up this archive. It would see
     no member files and think they were all deleted.
   - Members carry `NoStamp`, so `fastcheck` decides on size and mtime, read from
     `unison_member`.

   That avoids bumping `archiveFormat` (23 today), which would invalidate every existing
   archive.
5. **Fingerprints.** `unison_member.fp` holds Unison's own archive fingerprint (MD5) with
   `fpalg = 'unison-md5/1'`, because reconciliation compares it with the plain side's archive
   entries. `sha256` is the separate proof that the stored bytes are right, and it's what stock
   tools and Photo's readers can check. A member whose `fpalg` isn't the running engine's is
   read and fingerprinted again, never compared.
6. **Clone off.** HFS+ has no file clones, so the profile has `clone = off` (the preference
   takes `auto`, `off` or `require`, and applies to the whole run).
7. **Format scope.** v1 builds `sqlar` only. ZIP, tar, restic or kopia packs, and sparse bundles
   stay benchmark comparisons. The backend interface keeps its narrow shape (`list`, `stat`,
   `read`, `apply batch`, `verify`, `close`), so a second format can be added later without
   touching reconciliation.

## Configuration

```
packdir = Path */*               # directories packed: here, every leaf <H>/<HHHH>
packroot = /Volumes/Ten/Lightroom/Alexy Previews.lrdata   # the one root that stores containers
packmax = 4 GiB                  # report and refuse a container that would grow past it
```

- `packdir` takes Unison path patterns, matched against directories.
- The rest is refused with a message:
  - nested matches;
  - `packroot` not being one of the two roots;
  - a packed root that's remote or acts as a source.
- **A plain `D/` beside `D.sqlar` is pre-existing content** (user, 2026-10-31: Ten's original
  previews that Photo preserved stay in place, so Ten's old cache folder isn't emptied).
  - Packing never writes, renames or deletes anything under the plain `D/`.
  - A plain-side file whose name already exists as a plain file in `D/` isn't packed. It's
    reported as a collision, so no path is ever stored twice.
  - Reports list the plain `D/` files apart from `D.sqlar`'s members.
- **Only the Quasar cache leaves are packed** (user, 2026-10-31). Everything else on Ten stays
  in plain files and untouched.
- Files directly in a packed directory are packed. A subdirectory of a packed directory is
  refused in v1; the preview leaves have none.

## Container schema

As in the proposal, with the journal changed. These pragmas are set when a container is
created:

```sql
PRAGMA page_size = 65536;  PRAGMA auto_vacuum = INCREMENTAL;
PRAGMA journal_mode = DELETE;  PRAGMA synchronous = FULL;  PRAGMA fullfsync = ON;
CREATE TABLE sqlar(name TEXT PRIMARY KEY, mode INT, mtime INT, sz INT, data BLOB);
CREATE TABLE unison_member(name TEXT PRIMARY KEY REFERENCES sqlar(name),
  mtime_ns INT NOT NULL, fp BLOB NOT NULL, fpalg TEXT NOT NULL, sha256 BLOB NOT NULL,
  retained_deleted INT NOT NULL DEFAULT 0);
CREATE TABLE unison_container(key TEXT PRIMARY KEY, value TEXT);
  -- format = 'unison-packdir/1', directory = relative path, epoch = run counter
```

- **Names.** `name` is the plain file name. Containers are per directory, so no member name has
  a slash.
- **Blobs** are stored raw (`sz = length(data)`), never compressed.
- **Time precision.** `mtime_ns` keeps nanoseconds. That's more than Ten holds for plain files:
  HFS+ stores whole seconds.

## A run

1. **Scan.** On Quasar nothing changes. On Ten, each container is listed with one indexed query
   on `unison_member`, and no member data is read. If a container's `epoch` differs from the
   value Unison's archive records, it was changed outside Unison: it's listed in full and
   reported.
2. **Reconcile per member path.** Reports and dry runs show `<H>/<HHHH>/<name>`, and `ignore`
   applies to member paths. A deletion on Quasar marks the member `retained_deleted = 1` and is
   logged as `retained-deleted`; no bytes are deleted.
3. **Propagate by container.** Each container with changes gets one transaction:
   - Read each changed file from Quasar, hashing it (SHA-256 and Unison's fingerprint) as it
     streams in.
   - `INSERT OR REPLACE` the `sqlar` row with its blob, and upsert `unison_member`.
   - Bump `epoch`, then `COMMIT`.

   Containers are written one at a time per HDD (`semanticvolumejobs = 1` for the packed root),
   while reading and hashing on Quasar run in parallel within `semanticworkers` and
   `semanticcpubudget`. A container whose batch would exceed about 256 MiB is split into
   several transactions.
4. **Verify, then record.** After `COMMIT`:
   - read the changed blobs back and compare their SHA-256;
   - only then update Unison's archive for those members.

   A crash before `COMMIT` rolls the container back. A crash after it leaves Unison's archive
   behind the container, so the next run finds the members already right and only records them.
5. **Free space.** `incremental_vacuum` runs only on request, never during a mirror run.

## Building it into Unison

- **Where it plugs in.** A `Packdir` module sits under update detection and propagation for the
  packed root only:
  - update detection builds that root's archive view from `unison_member`;
  - propagation to that root goes through the batch transaction, instead of Unison's usual
    temp-file-and-rename per file.

  The plain root's code paths don't change.
- **SQLite comes from the opam `sqlite3` binding**, already installed in both switches. It's
  built only when available, so a build without it refuses `packdir` with a message. Both stock
  OCaml and OxCaml builds.
- **Tools:** `unison-packdir verify DIR` (integrity check and every SHA-256) and
  `unison-packdir restore DIR OUT` (exact mtimes, `--skip-retained`). A stock restore needs
  neither.

## Tests (synthetic fixtures only)

As in the proposal, plus these:
- **Per-directory layout:** every container restores with `sqlite3 -AxC` to the plain tree,
  byte for byte, and with mtimes to the second.
- **The archive-identity guard:** a run without `packdir` over the same roots doesn't use the
  packdir archive, and deletes nothing.
- **Crash points:** kill after `COMMIT` and before Unison's archive update; the next run
  records the members without rewriting them.
- **One file per container:** no `-journal`, `-wal` or `-shm` file exists after a run.

## Benchmark before building

The benchmark runs first, on a synthetic leaf set with the preview cache's size distribution,
written to a scratch folder on Ten (HFS+). Writing to Ten needs the user's approval. Photo's
`bench_leafset.py` generates the set into `/Volumes/Quasar/packdir-bench/leafset-v1/`: 50 GiB in
about 700 leaves, built from a stat-only sample of real leaves. Its second mode makes the 1%
change set in place, with replacements, additions and a few deletions, and writes them to
`CHANGES.json`. The prototype writer is `tools/packdir/` (`unison-packdir pack-tree`).

| Run | Measures |
| --- | --- |
| plain Unison (today's build, `clone = off`) | the baseline |
| prototype `.sqlar` writer, one container per leaf, `DELETE` journal and `fullfsync` | the design |
| the same with WAL | the journal choice |
| `cp -R` and `tar \| tar` | the streaming limit |
| sparse bundle (HFS+ inside) | the no-code alternative |

Each of these is measured on a first run and on a 1% incremental run, recording wall time,
bytes written and IOPS. ZIP and restic/kopia are left out unless the `.sqlar` prototype
disappoints.
