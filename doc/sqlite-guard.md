# SQLite databases: the guard

A SQLite database is more than one file while an application has it open:
`X`, and beside it `X-journal` or `X-wal` and `X-shm`. Copying `X` alone then
gives an old or torn database, and replacing `X` under a write-ahead log
corrupts it at the next open. The guard makes Unison synchronize a database
only while it is *quiet*, when the main file alone is the whole database.

It is off unless a profile names the databases:

```
sqlitedb    = Name *.lrcat      # paths that are SQLite databases
sqlitequiet = require           # off | warn | require; require is the default
```

The design, with its reasons, is `docs/sqlite-semantic-design.md`. This page
says what is built: step 1 of that design, except lock evidence from the
operating system.

## What it does

- **The files beside a database are never propagated.** For a path `X` that
  matches `sqlitedb`, the names `X-journal`, `X-wal` and `X-shm` are skipped on
  both hosts, as ignored paths are. This is by name, and holds for every value
  of `sqlitequiet`.
- **A database that isn't quiet is an error at its path**, found while Unison
  looks for changes, whether or not the file itself changed. It is then
  neither sent nor replaced. The message names the file that shows it, and the
  next run tries again:

  ```
  The SQLite database Catalog.lrcat is not quiet: Catalog.lrcat-wal holds 37
  committed frames the database file lacks; close the application that has it
  open, or checkpoint it
  ```

- **Checked again when it matters.** The source is checked once more after it
  has been read, and the target before a transfer starts and again just before
  it is replaced or deleted. A directory about to be deleted is searched for
  databases first.
- **A path that matches but isn't a SQLite file is an ordinary file**, except
  that names like `X-wal` beside it are still skipped.

## What counts as quiet

| Beside `X` | Verdict |
| --- | --- |
| Nothing | Quiet |
| `X-journal`, empty or with its 28-byte header zeroed | Quiet |
| `X-journal` with a header | Not quiet: a transaction is running or was interrupted |
| `X-wal`, empty, header only, or holding only frames of an earlier log | Quiet |
| `X-wal` whose committed frames all equal the main file's pages | Quiet for sending; `X` is not replaced or deleted under it |
| `X-wal` with committed frames the main file lacks | Not quiet |
| `X-wal` with frames of a transaction that hasn't committed | Not quiet |
| `X-shm` | Decides nothing by itself |

A write-ahead log is read as SQLite's recovery reads it: frames count while
their salts match the header's and the running checksum agrees. One
difference: a frame with the log's salts and a wrong checksum is taken as a
transaction in progress, because SQLite rewrites the frames a large
transaction spills and corrects their checksums only at commit. Likewise a
journal whose header is in place but not yet stamped with its magic number.

The guard reads headers and frames. It never opens a database through SQLite,
never locks, never writes, and never removes or checkpoints a log.

## Markers and paths that belong to a database

An application that has a database open and idle leaves nothing in a journal
or a log. Two more preferences cover what an application keeps beside its
database:

```
sqlitemarker = Name *.lrcat -> {name}.lock
sqliteheld   = Name *.lrcat -> {stem} Helper.lrdata
```

- **`sqlitemarker`** names a file whose presence means the application has the
  database open, or crashed with it open. While it exists the database is not
  quiet. `{name}` is the database's file name and must occur once. The marker
  file itself is never propagated.
- **`sqliteheld`** names a file or directory beside the database that belongs
  to it. While the database is not quiet, that path is an error too, in both
  directions: it is not sent, written to or deleted. `{name}` is the
  database's file name, `{stem}` that name without its extension. A path that
  doesn't exist is no error.

A database inside a held folder is named with its folder, so that the same
name elsewhere stays an ordinary file:

```
sqlitedb = Name * Helper.lrdata/helper.db
```

### Lightroom Classic

`doc/profiles/lightroom-classic.prf` has the entries for a catalog: the
`.lrcat.lock` marker, the five folders beside a catalog, and the five
databases inside them. Two more databases in the Sync folder are left unnamed
on purpose, because Classic leaves a log beside each after a clean quit and
that log has to travel with them; the file says so.

## A closed database that keeps its log

Some applications leave a write-ahead log holding commits beside a database
they have closed. Named by `sqlitedb`, such a database is never quiet, and its
log is never propagated, so it would not be synchronized at all. Leave it
unnamed: it is then three ordinary files, copied as before. The guard has no
way yet to move a database and its log as one unit.

## `sqlitequiet`

| Value | A database that isn't quiet |
| --- | --- |
| `require` | Is not propagated, replaced or deleted; the path fails with the reason |
| `warn` | The reason is printed and the path is synchronized anyway |
| `off` | Nothing is checked |

## Both hosts

The two hosts must skip the same names, so the guard is a negotiated feature,
`sqlite-guard-v0`. With a peer that lacks it (upstream Unison, or an older
build of this fork):

- under `require`, Unison stops before looking for changes and names the
  feature;
- under `warn` or `off`, it says the guard is without effect and runs as plain
  Unison, which also means the files beside a database are synchronized as
  ordinary files.

## Limits

- An application that has a database open and idle, with nothing in a journal
  or log and no marker file, can't be seen from the files. Lock evidence from
  the operating system is in the design and not built.
- Unison has no commit across several files and there is a window between a
  check and the rename that follows it. The guard narrows the window; it
  doesn't close it.
- After a crash the leftovers hold the database back until the application has
  opened it again and closed it, or someone removes them. That is the safe
  direction.
- With `-repeat watch`, a log that appears beside an unchanged database doesn't
  wake Unison; the checks at transfer time still apply.

## Tests

```sh
dune build @tests/sqliteguard/runtest
python3 tests/sqliteguard/run.py --unison UNISON --probe PROBE \
    --fragment doc/profiles/lightroom-classic.prf --upstream /usr/local/bin/unison-2.53.5-upstream
```

Real databases are made with Python's `sqlite3` and copied while a connection
is open; synthetic logs and journals cover both checksum byte orders and
damage. The same scenarios run between two local roots and over a connection.
`--fragment` runs the Lightroom entries on a folder laid out as a catalog's,
and `--upstream` adds the checks against a Unison without the guard.
