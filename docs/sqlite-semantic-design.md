# A semantic extension for SQLite databases: design

Status: proposal by the Unison session, 2026-11-14; the user's decisions of 2026-11-15
are in "Decisions taken", and the questions for Photo are in the mailbox (U-41). The
first use is syncing Lightroom catalogs. Nothing is implemented. Facts about `sqlite3_rsync` and `dbhash` are from
sqlite.org's pages as fetched on 2026-11-14; facts about the file format are from the
SQLite file-format specification and must be re-checked against real files by the tests
in "Tests" before any of this is relied on.

## What it is for

A replica holds SQLite databases as ordinary files: Lightroom catalogs, phindex indexes,
dng-compare's `recovery.sqlite3`, other applications' libraries. (Packed roots are a
different thing: there Unison itself writes the `.sqlar` containers and already sees
inside them.) Plain Unison, and this fork so far, treat such a file as opaque bytes.
Three things go wrong or go unsaid:

1. **A database is more than one file.** While an application has it open, part of the
   database can live in `X-wal` or be half-undone in `X-journal`. Unison syncs `X`,
   `X-wal` and `X-shm` as three unrelated files. It can propagate a main file without the
   transactions in its WAL, and it can replace a main file under a WAL left on the other
   replica. SQLite replays a WAL by its own salts and checksums, not by what the main
   file contains, so the second case corrupts the database at its next open.
2. **Bytes change when content doesn't.** Opening a database, checkpointing it,
   `VACUUM`, a catalog "optimize", `REINDEX` and a journal-mode switch all change bytes
   and leave every row as it was. A byte comparison says "differs"; `-semdiff` then can't
   say the shuttle's catalog is kept.
3. **A small transaction dirties a few pages** scattered through a file of gigabytes.
   Unison's rsync finds them, but in blocks of up to 128 KiB (64 KiB for a 3 GiB file),
   so each changed 4 KiB page resends sixteen.

The extension answers these in that order of importance: a guard, then identities, then a
page delta. Merging two diverged databases is out of scope (see "Merging").

For a Lightroom catalog the danger is the first problem, not speed: a sync that runs
while the catalog is open, or that replaces a catalog under leftover `-wal` files. So
the guard is built first, and cheap versions of a replaced catalog second ("Order of
work"). Both need only file headers, not the walker.

## The three identities, for SQLite

The fork's rule holds unchanged: byte identity is the contract for convergence, and a
semantic identity explains and never substitutes.

| Identity | For a SQLite database | Authorizes |
|:--|:--|:--|
| Byte | SHA-256 of the main file | Convergence, as today |
| Page | SHA-256 of each page; a two-level tree over them | The page delta, checked by the byte identity of the result |
| Content | Digests of the schema and of each table's rows, independent of where they are stored | Explaining a difference; `-semdiff`'s answer. Never a transfer or a merge |

### The content digest

Defined over what is stored, with no SQL engine and no SQL parser:

- **Schema digest.** The rows of `sqlite_schema` in key order: type, name, table name and
  SQL text, without `rootpage`.
- **Per table, two digests.** `rows` covers each row's rowid and decoded values in key
  order. `records` covers the decoded values only. A value is hashed as a type tag and a
  canonical encoding (integer as 8 bytes, float as 8 bytes, text and blob as length and
  bytes), so the digest doesn't depend on which serial type stored it.
- **Derived data is left out:** index b-trees and the `sqlite_stat*` tables, each with
  its own digest reported beside the content. `WITHOUT ROWID` tables are hashed in their
  stored key order, with `rows` equal to `records`.
- **Database digest:** the schema digest and the `rows` digests of all tables, by name.

What this is invariant under, by construction: page allocation and order, the freelist
and garbage in free space, page relocation by auto-vacuum, index rebuilds, the header's
change counter, version stamps and journal-mode bytes.

What it is *not* guaranteed invariant under, and reports instead of guessing:

- **Renumbered rowids.** SQLite documents that `VACUUM` may change rowids of a table
  with no `INTEGER PRIMARY KEY`. Then `records` match and `rows` don't. Without parsing
  `CREATE TABLE` the extension can't tell that case from a real change of keys, so it
  reports "same records, different rowids" as its own finding.
- **Short records.** Rows written before an `ALTER TABLE ADD COLUMN` store fewer
  columns. If another writer has rewritten them in full, they differ here though SQL
  would read them alike. That is an error on the conservative side, as with `-semdiff`'s
  encoded-bytes rule for images.
- **Text encoding.** A UTF-8 and a UTF-16 database with the same text differ.

`dbhash`, SQLite's own tool, hashes schema and content through the engine and is constant
across `VACUUM`, `page_size`, `journal_mode`, `REINDEX` and `ANALYZE`. It is the oracle
for the tests, not a dependency: it is SHA-1, needs the engine, and isn't installed here.

### The walker

A bounded, read-only reader of the file format in plain OCaml, in the manner of
tiffgraph: no SQLite library, no subprocess, no writes, positional reads on the supplied
`SemanticFile`. That keeps the trusted-extension contract and keeps the make build, which
has no SQLite.

- Header: magic, page size (512 to 65536), reserved bytes, page count (from the header
  when its version-valid-for matches the change counter, else from the file size), text
  encoding. A file whose size isn't a whole number of pages declines.
- Every page is visited at most once (a bitmap, one bit per page); depth is capped at
  SQLite's own limit of 20; an overflow chain is bounded by its payload size. A cycle, a
  page number out of range, a cell outside its page or a bad varint declines the whole
  file with a reason.
- Freelist trunks, pointer-map pages and the lock-byte page (the page holding offset
  1 GiB) are recognised and never read as content.
- Interior pages are read first to list each table's leaves; a row is streamed into the
  hash, so memory is one page however large a blob is.
- Anything not understood declines: an encrypted file has no SQLite magic and stays an
  ordinary file; nonzero reserved bytes, a schema format above 4 or a read version above
  2 decline.

Proposed home: in this repository first (`src/sqlitePages.ml`, `src/sqliteSemantic.ml`),
moved to its own repository as tiffgraph was once a second tool wants it.

## The guard: only a quiet database is synced

A database is the group `X`, `X-journal`, `X-wal`, `X-shm`. It is **quiet** when the main
file alone is the whole database:

| Found beside `X` | Verdict |
|:--|:--|
| No companion files | Quiet |
| `X-journal` empty, or with a zeroed header (`TRUNCATE` and `PERSIST` modes) | Quiet |
| `X-journal` with a valid header | **Hot journal.** A transaction was interrupted or is running. Not quiet |
| `X-wal` empty or with no valid frame | Quiet |
| `X-wal` whose last committed version of every page equals the main file's page, and whose last commit's size equals the file's | Quiet for *sending*: the WAL adds nothing |
| `X-wal` with committed frames the main file lacks | **Not quiet.** The main file is an old version |
| `X-shm` present | A connection is or was open; decided by the WAL rows above |

Rules, on by a path preference (below), in both directions:

- **Sending.** A database that isn't quiet is not propagated. The item fails with a
  transient error that says why ("`Catalog.lrcat-wal` holds 37 committed frames; close
  the application or checkpoint"), and the next sync tries again. The group is rechecked
  after the transfer, on top of Unison's own check that the source didn't change.
- **Receiving.** A database is never replaced or deleted while a hot journal or a WAL
  with *any* valid frame sits beside it. This is the corruption case of problem 1.
  Unison doesn't delete or checkpoint the user's WAL; it refuses and says so.
- **Companions.** `-journal`, `-wal` and `-shm` beside a recognised database are never
  propagated in either direction. They are recognised by their own headers and their
  sibling, not by name alone.
- **Lock evidence, optional.** On a local volume, `fcntl(F_GETLK)` on SQLite's lock
  bytes asks whether another process holds a lock, without taking one. A held write lock
  means not quiet. It is evidence only: Apple's SQLite can use other locking styles on
  network volumes, and an idle open connection holds no lock at all.
- **Application markers.** A rule may name a sibling whose presence means "open". With
  one, an application that is open and idle is seen too.
- **Held paths.** A rule may name siblings that belong to the database. Whenever the
  database is held back, so are they, in both directions, so the other replica never
  gets companion data that doesn't match its database. Unison has no commit across
  several files, so this narrows the window; it doesn't make the group atomic.

The limit to state plainly: without a marker, an application that has a database open
and idle, in rollback mode, is invisible to all of this. Replacing the file under it is
the old hazard of any file sync, and the guard narrows it without closing it.

### Lightroom catalogs

The two rules above exist for Lightroom Classic. As the Unison session understands a
catalog's layout, to be confirmed by Photo (U-41) before anything is built on it:

| Beside `Name.lrcat` | Rule |
|:--|:--|
| `Name.lrcat.lock` | Marker: the catalog is open. Not quiet, even with no `-wal` or `-journal` |
| `Name.lrcat-wal`, `-shm`, `-journal` | The generic rows of the table above |
| `Name.lrcat-data/` | Held path: held back whenever the catalog is |
| `Name Previews.lrdata/`, `Name Smart Previews.lrdata/` and the like | Open question: caches that could sync freely, or held with the catalog |

A lock file left by a crash holds the catalog back until someone removes it. That is
the safe direction, and the message names the file.

## The page delta

For a quiet database changed on one side, with the old version on the receiver as basis.
Byte-exact, inside Unison's own connection, through the existing private staging.

1. Both sides read their file once, getting the SHA-256 of the whole file and of every
   page in the same pass. Page sizes must be equal, or the profile declines.
2. The receiver sends its basis as a nonce, the whole-file digest and one digest per
   group of 256 pages. For a 5 GiB catalog of 4 KiB pages that is 5,120 digests.
3. The sender asks for page digests of the groups that differ, then sends the pages that
   differ, the new page count and the target's SHA-256. Messages are bounded (at most
   1 MiB of pages each). If more than half the file would travel, the profile declines
   and Unison copies as usual.
4. The receiver writes those pages into a private clone of its basis (a copy where the
   filesystem has no clones), truncates or extends to the new size, and checks the
   SHA-256 of the whole result against the target's. Only then does Unison's ordinary
   commit rename it into place. A mismatch discards the staging file and falls back to
   an ordinary transfer; it is reported, not hidden.

It is negotiated as `semantic-profile:org.firstpair.sqlite-pages/0`; with a peer that
lacks it nothing changes. Page digests can be cached by fingerprint, as fingerprints
are, so an unchanged basis isn't reread.

**Whether to build it should wait for a measurement.** Unison's rsync into the fork's
receiver-basis staging already avoids resending and rewriting the unchanged bulk. The
delta's gain is the factor between a page and an rsync block (16 for a 3 GiB file) on
the bytes sent and written, and nothing on the bytes read. A run on a real catalog
before and after one editing session would say whether that matters.

## `sqlite3_rsync`, and why it isn't the transfer

SQLite ships `sqlite3_rsync ORIGIN REPLICA`, which makes the replica a copy of a
consistent snapshot of the origin over ssh. Since 3.50.0 it sends hashes of groups of
pages and asks for finer ones where they differ; its page reports about 20 KB of traffic
to sync a 500 MB database that changed little. Both databases may be in use while it
runs, and since 3.50.0 neither WAL mode nor equal page sizes is required. It must be
installed on both hosts. It is not installed here: the system SQLite is 3.43.2, and
Homebrew's 3.54.0 has only the `sqlite3` shell.

It is the right tool for a job this design leaves alone, and the wrong one for the job
above:

- **Its replica is not byte-identical**, by its own description: "a very close copy of
  the origin, but not an exact copy". The change counter and version stamp in the header
  can differ. Unison would see the two files as different at the next sync.
- **It runs the SQLite engine on both files** and opens its own ssh connection. On a
  WAL-mode origin that can create `-shm` on the source replica, and on the replica it
  writes in place, outside Unison's staging, verification and archive.
- **For a live origin, byte convergence isn't defined at all**: the origin's main file
  doesn't hold what its WAL holds.

What it is used for here:

- **The idea.** The page delta's two-level digests are its protocol's shape, carried in
  Unison's connection and finished with a whole-file SHA-256.
- **An oracle.** After `sqlite3_rsync A B`, this extension must find equal content
  digests and bytes that differ only in the header. That tests the walker, the digest
  and the classification with a tool this project didn't write.
- **Not a live mode.** A one-way mode for a database that is never closed, replicated
  by `sqlite3_rsync` and judged by content digest instead of bytes, was considered. The
  user declined it: it changes what "in sync" means for those paths, and Lightroom has
  to be closed for a catalog copy to mean anything.

## Where it plugs in

`FormatExtension.S` describes editable regions of one file whose size and layout don't
change. A database doesn't fit that, so the core gains three things, each optional and
each bounded like what exists:

| Addition | Used by |
|:--|:--|
| A file observer: content digests from a `SemanticFile`, under the observation bounds (aggregates within the 128-property cap; the per-table list goes to the report) | `-semdiff`, conflict detail |
| A group admission hook: companion names for a path, and a verdict on the group | The guard |
| A page-delta plan beside the region plan, bound to nonce, basis and target digest the same way | The page delta |

**`-semdiff`.** A pair of databases gets the layers: whole file; content; derived
(indexes, statistics). Bytes equal is `identical`. Content digests equal with bytes
different is a new status, `layout-only`, which counts as kept. It requires the schema
digest and every table's `rows` digest to match, rowids included. Otherwise `differs`,
with the tables that differ; "same records, different rowids" is `differs` with that
finding attached, and goes to review. A shuttle database that isn't quiet is `error` and never counts as kept. A new
status touches the shared contract with dng-compare, so it goes to the mailbox first.

**Skeleton versions.** With pages as blocks, a replaced catalog's kept version costs the
pages the edit changed instead of the whole file. The store's rebuild-and-verify step is
unchanged. This is probably the largest practical saving of the whole design.

**Application rules.** Which tables are caches or bookkeeping is the application's
knowledge, not SQLite's. A rules file keyed by `application_id`, `user_version` or schema
digest can label tables (identity, descriptive, workflow, opaque) so a report can say
"only workflow tables differ". It is data, not code, and labels never authorize
anything. Who owns it, as dng-compare owns `metadata_rules.json`, is a mailbox question.

## Preferences

```
sqlitedb    = Name *.lrcat          # paths treated as SQLite databases; the content must agree
sqlitequiet = require               # off | warn | require; default require for sqlitedb paths
semanticprofile = org.firstpair.sqlite-pages/0    # the page delta, when built
skeleton    = Name *.lrcat          # existing preference; pages become the blocks
```

A path that matches `sqlitedb` but isn't a SQLite file is an ordinary file. A SQLite
file that doesn't match is an ordinary file too: nothing is guarded by guesswork.

## Merging

Not offered. Two databases changed on both sides stay a conflict, with the tables that
differ on each side listed when a base digest is known. A row-level merge would need the
engine to write a database, rebuild indexes and respect triggers and foreign keys, and
the application's invariants are not in the file. For a Lightroom catalog the answer is
already recorded elsewhere: changes go through Lightroom's own writer.

## Tests

Fixtures are built at test time by the `sqlite3` shell (system 3.43.2 and Homebrew
3.54.0, both recorded); the suite skips with a message where there is none.

- **Walker against the engine.** For each fixture, rows read by the walker equal
  `sqlite3`'s dump: rowid and `WITHOUT ROWID` tables, overflow chains, every serial
  type, page sizes 512 to 65536, auto-vacuum, a file past 1 GiB (sparse) for the
  lock-byte page, UTF-16.
- **Invariance.** `VACUUM`, `REINDEX`, `ANALYZE`, a page-size change, a journal-mode
  switch and freelist churn each leave the content digest equal and the bytes different.
  Whether `VACUUM` renumbers rowids or rewrites short records in practice is settled
  here, and the document corrected to match.
- **Oracles, when built from the SQLite source tree:** `dbhash` agrees on equal and
  unequal for every pair; `sqlite3_rsync` output is `layout-only` against its origin.
- **Refusals.** Cyclic page pointers, a looping overflow chain, a truncated file, a
  wrong page count, garbage in free pages that looks like rows.
- **Guard.** A hot journal; a WAL with unapplied commits; a redundant WAL; a WAL from
  another database placed beside the receiver's file, which must refuse the replace; a
  writer holding a lock. A marker file present with no companions; a held path while the
  database is held back, in both directions, and released when it is quiet again.
- **Delta.** Growth, shrinkage, a changed page in each group position, a forced digest
  mismatch that must fall back, a peer without the feature. On stock OCaml 5.2.0 and
  OxCaml 5.4.0+ox, each named.

## Order of work

| Step | What | Needs | Changes sync behaviour |
|:--|:--|:--|:--|
| 1 | The guard, with the Lightroom marker and held paths | Journal and WAL headers, page compare | Yes: refuses what was unsafe |
| 2 | Pages as skeleton blocks, so a replaced catalog is kept cheaply | The page size from the header | Only with `skeleton` set |
| 3 | Walker, content digests, `-semdiff` layers and report | The walker | No |
| 4 | Measure on a real catalog; build the page delta only if Unison's rsync proves too slow | The user's approval and Photo's help for the measurement | Negotiated, opt-in |

Step 2 is what makes a both-sides edit recoverable: the conflict stays a conflict, the
user picks a side, and the other side's catalog is still in the store.

## Decisions taken

By the user on 2026-11-15, on the Unison session's recommendation:

1. **The guard defaults to `require`** for `sqlitedb` paths, refuses in both directions,
   and guards nothing that isn't named. It gains the Lightroom marker and held paths.
2. **`layout-only` counts as kept, strictly:** every table's rows and rowids match.
   "Same records, different rowids" goes to review.
3. **The walker starts in this repository** and moves out when a second tool wants it.
4. **No live mode through `sqlite3_rsync`.** Lightroom has to be closed for a copy of its
   catalog to mean anything. `sqlite3_rsync` stays a test oracle.
5. **Lightroom catalogs come first.** The page delta waits for a measurement of one real
   catalog before and after an editing session, read-only on a copy.

Open with Photo (U-41): the catalog's layout as tabled above, the journal mode Lightroom
uses, whether the previews folders are held, the `layout-only` status in the shared
contract, who owns the application rules, and the measurement.
