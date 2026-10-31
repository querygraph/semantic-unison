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
   `synchronous = FULL`; the drive cache is flushed by barriers (see "Durability").

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
  - A plain-side file whose name already exists as a plain file in `D/`, with the same size
    and SHA-256, isn't packed; it's logged as `present-plain` (Photo, P-3).
  - Once its bytes differ, it's packed and kept updated in `D.sqlar`, logged as
    `packed-beside-plain`, while the plain original stays as it is (user, 2026-10-31). That
    path then exists both as the kept original and as the newer member, and the member is the
    mirror's copy. An update costs about the changed file's own bytes (measured: 2.2 MiB written
    for a 1.7 MiB member of a 70 MiB container, with no growth over 10 updates).
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
PRAGMA journal_mode = DELETE;  PRAGMA synchronous = FULL;  PRAGMA fullfsync = OFF;  -- barriers flush
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

1. **Scan.** On Quasar nothing changes. On Ten, Unison's archive records each container file's
   inode, size and mtime with its members. A container whose file is as recorded isn't opened:
   its members come from the archive, and checking it costs one stat. A container is opened, and
   its member table read with one indexed query, only when its file changed outside Unison (then
   it's listed in full and reported) or when the run has something to store in it.

   This matters. In the benchmark (U-9), opening and listing all 694 containers with nothing to
   write took 83–141 s on Ten, about 0.12–0.2 s each. At 65,536 containers that would be 2–3.5 h
   per run, against about a second for a rerun that stats them.
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
   - only after the next barrier (below) update Unison's archive for those members.

   A crash before `COMMIT` rolls the container back. A crash after it leaves Unison's archive
   behind the container, so the next run verifies the container, finds the members already right
   and only records them.

### Durability: barriers, not a flush per container (user, 2026-10-31)

- **Each container's transaction is synced with plain `fsync`** (`synchronous = FULL`,
  `fullfsync = OFF`). That orders the writes as far as the drive, but not past the drive's own
  write cache.
- **A barrier is one `F_FULLFSYNC`** after every 4 GiB written, and at the end of the run. It
  empties the whole drive's cache.
- **Unison's archive records a container only after a barrier covers it.** Before its first
  write, a container is added to a pending list. The list is cleared only after the final
  barrier and the archive update.
- **After a crash or power loss,** the next run verifies every pending container, and every
  container whose file doesn't match the archive, with `integrity_check` and every member's
  SHA-256. A damaged one is set aside (`D.sqlar.damaged-<time>`), never deleted, and packed again
  from Quasar.
- **Measured on Ten, 50 GiB, 4 workers:**

  | Sync | Time | Throughput |
  |---|---:|---:|
  | barrier every 4 GiB | 340 s | 150 MiB/s |
  | no flush at all | 314 s | 163 MiB/s |
  | `F_FULLFSYNC` per container | 946 s | 54 MiB/s |
  | plain Unison | 337 s | 152 MiB/s |
5. **Free space.** `incremental_vacuum` runs only on request, never during a mirror run.

## Building it into Unison

### Where it plugs in

Unison reaches a replica's files through `fs.ml` for almost everything, but not quite all of it:
- the Finder-info C stub (`osx.ml`);
- the clone and publication stubs, which work on real descriptors and inode numbers;
- the semantic extensions, which need real file descriptors;
- `Fspath.findWorkingDir`, which `chdir`s into directories.

So a virtual filesystem under `fs.ml` would be fragile. The packed root is one-way and only ever
receives, so v1 plugs in one level up instead, and leaves the plain root's code and Unison's
reconciliation untouched:

- **Update detection.** `Update.findLocal` (`update.ml:2615`) for the packed root builds that
  root's current tree from the containers, not from `Fileinfo.get` and `Os.childrenOf`:
  - a container is a directory, and its members are files;
  - each member has its size, mtime and mode, `NoStamp`, and the stored fingerprint as its
    fingerprint;
  - a container whose file stamp matches the archive isn't opened (see "A run");
  - plain files beside a container are listed as on any root.
- **Propagation.** `Transport.transportItem` (`transport.ml:365`) sends a file update or
  creation whose target lies in a packed directory on the packed root to the packdir writer,
  not to `Files.copy`. The writer reads the source file from the plain root, which is local,
  and queues it for its container. Deletions are already skipped under `nodeletion`; the
  writer marks those members `retained_deleted`. Clone staging, publication and the semantic
  rebuild don't apply to the packed root, and are turned off for it.
- **Commit.** Each container's queued puts are one transaction. Every queue is flushed, the
  final barrier is taken, and the pending list is cleared before `Update.commitUpdates`
  (`update.ml:2888`). So Unison's archive never gets ahead of the platter.
- **Archive identity.** The packed root's `thisRoot` string in `archiveHash`
  (`update.ml:203`) gets a packdir signature. A run without the same `packdir` never uses this
  archive.
- **SQLite** comes through the `packdir` library (`tools/packdir`), which is linked only when
  the opam `sqlite3` binding is present. A build without it refuses `packdir` with a message.

### Milestones

Each one is tested on synthetic data, on stock OCaml and OxCaml, against the prototype as the
reference.

1. **Preferences and guards.** `packdir`, `packroot`, `packbarrier` and `packmax`, and the
   refusal rules: nested patterns, a remote or source packed root, a missing SQLite build. The
   archive-identity guard. *Test:* every refusal, and a run without `packdir` never using the
   packed archive.
2. **Update detection from containers.** *Test:* Unison's view of a packed tree written by
   `unison-packdir pack-tree` equals its view of the same plain tree. An unchanged container
   isn't opened. A changed one is verified.
3. **Propagation through the writer.** One transaction per container; read-back SHA-256; members
   marked retained. *Test:* first and incremental runs give containers that `unison-packdir
   verify` and `unpack-tree` turn back into exactly the Quasar tree.
4. **Barriers and recovery.** The pending list, a barrier every 4 GiB and at the end, and
   verify-before-trust after a crash. *Test:* kills at each point; the next run converges.
5. **Parallel preparation.** Reading and hashing the plain side in parallel, within
   `semanticworkers` and `semanticcpubudget`, with one writer per disk. *Test:* the 50 GiB
   benchmark set onto `/Volumes/Ten/packdir-bench/`, against the prototype's 340 s.
6. **Unpack and repack.** `unison-packdir unpack-tree` and `repack` (built, 87 controls) ship
   beside `unison`. A run whose `packdir` differs from the archive's refuses and points at
   them, instead of rescanning or deleting.

The mirror runs only after milestone 6 and the user's go-ahead.

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
written to `/Volumes/Ten/packdir-bench/` (HFS+), approved by the user on 2026-10-31. Photo's
`bench_leafset.py` generates the set into `/Volumes/Quasar/packdir-bench/leafset-v1/`: 50 GiB in
about 700 leaves, built from a stat-only sample of real leaves. Its second mode makes the 1%
change set in place, with replacements, additions and a few deletions, and writes them to
`CHANGES.json`. The prototype writer is `tools/packdir/` (`unison-packdir pack-tree`).

| Run | Measures |
| --- | --- |
| plain Unison (today's build, `clone = off`) | the baseline |
| prototype `.sqlar` writer, one container per leaf, `DELETE` journal, barriers | the design |
| the same with WAL | the journal choice |
| `cp -R` and `tar \| tar` | the streaming limit |
| sparse bundle (HFS+ inside) | the no-code alternative |

Each of these is measured on a first run and on a 1% incremental run, recording wall time,
bytes written and IOPS. ZIP and restic/kopia are left out unless the `.sqlar` prototype
disappoints.
