# Preserving APFS clones

Status: design, 2026-11-02. Builds in three phases: packdir, then Unison file to file, then Unison into packdir.

## What it is for

On APFS, `cp -c` and Finder's duplicate make a **clone**: a second file that shares the first one's blocks until either is written. Two collections on this machine depend on that:

- Lightroom's Smart Previews, shared between catalogs on Capitola.
- Photo Mechanic images on Quasar that are clones of Lightroom previews.

Copying either by ordinary means, whether by Unison, packdir or `cp`, turns every clone into a full copy. The data survives, but the space doubles and the relationship is lost. The goal is that a clone stays a clone through a sync, through packing and through restoration:

- **File to file:** a clone on the source is recreated as a clone of the corresponding original on the destination. Only the original is transferred.
- **Into packdir:** a clone is stored once, as a reference naming its original. No second copy of the bytes is stored.
- **Out of packdir:** the original is restored as a new file, and each clone is recreated from it with `clonefile`.

## What counts as a clone

APFS reports two attributes through `getattrlist`:

- `ATTR_CMNEXT_CLONEID`: files cloned from one another share it.
- `ATTR_CMNEXT_CLONE_REFCNT`: how many files share it.

A measurement on this machine (macOS 15, Darwin 24) showed:

| Step | `a` | `b` (`cp -c a b`) | `c` (`cp -c b c`) | `d` (`cp a d`) |
| --- | --- | --- | --- | --- |
| After creation | id A, refcnt 3 | id A, refcnt 3 | id A, refcnt 3 | id D, refcnt 1 |
| After writing one byte of `b` | id A, refcnt 2 | new id, refcnt 1 | id A, refcnt 2 | id D, refcnt 1 |

So a **clone group** is the set of files on one volume with the same clone ID and a refcount above 1. Writing to a member takes it out of the group. An independent copy is never in a group, even with identical bytes.

The clone ID is a hint about structure, not proof of content. Every use below also checks that the contents are equal: by SHA-256 in packdir, and by Unison's fingerprint in Unison. A pair that fails the check is treated as two ordinary files.

Only exact clones are preserved. Identical files that were independent on the source stay independent on the destination. This was the user's decision.

On other systems, and on volumes that aren't APFS, nothing is a clone and nothing changes.

## packdir

### Format

There is a new table in each container, created if missing on open:

```sql
CREATE TABLE IF NOT EXISTS packdir_clone(
  name TEXT PRIMARY KEY,      -- the clone's member name in this container
  mode INT, mtime INT, sz INT, -- as sqlar would hold them
  original TEXT NOT NULL,     -- the original, relative to this container's directory
  sha256 BLOB NOT NULL);      -- the content both share
CREATE TABLE IF NOT EXISTS packdir_cloned_by(
  name TEXT NOT NULL,         -- an original in this container
  clone TEXT NOT NULL,        -- one of its clones, relative to this container's directory
  PRIMARY KEY (name, clone));
```

- **A clone has no `sqlar` row.** A member with no data in `sqlar` makes stock `sqlite3 -Ax` stop at that member, with "error in uncompress()", and extract nothing after it. Keeping clones in their own table means stock tools extract every ordinary member and skip the clones. The manual gives a stock SQL query that lists each clone with its original, for `cp -c`.
- **A clone keeps its `unison_member` row** (fingerprint, nanosecond mtime, SHA-256, retained flag), so Unison sees it as an ordinary member. The declared foreign key to `sqlar` isn't enforced on any connection packdir opens.
- **References are relative.** `original` is a path from the clone's container directory `D` to the original file, for example `../../lr/0/0000/a_320`. To resolve it, join it to `D`, normalize it, and find the longest prefix `P` for which `P.sqlar` exists; the rest is the member name. No tree root is needed, so a single container can be checked or restored on its own.
- **The original always holds data.** A reference never names another clone. When a group is packed, the clones are noted against one data member.
- **Back-references** in the original's container list its clones. They're the reverse index that writers consult before changing or removing an original.

### Writing

When `pack-tree` runs on macOS, it reads each candidate file's clone ID and refcount alongside its `stat`. Files in the tree that share a clone ID form a group.

- **The original** is the member that already holds data in the packed tree if there is one. Otherwise it's the group's first member in path order, which is stored as usual.
- **Every other member** is read and hashed as now, and its SHA-256 must equal the original's. It is then written as a `packdir_clone` row plus a `unison_member` row, with no `sqlar` row.
- **Order:** the back-reference is written first, in its own short transaction in the original's container, and the clone row second. A crash between the two leaves a back-reference with no clone. Stale back-references are allowed; every reader checks the clone row they point to.
- **No two containers in one transaction:** no transaction holds one container while waiting for another, so parallel writers can't deadlock.

**Changing or removing an original** first **materializes** its clones. This covers storing new content under its name, `rm`, `mv`, and `repack --drop-retained`. For each back-reference whose clone row really names this original, the clone gets the original's current bytes in its own `sqlar` row and loses its `packdir_clone` row. That transaction commits before the original's transaction starts. A crash in between leaves the clones materialized and the original unchanged, and the next run repeats the change.

Two operations need nothing:

- **Retaining a deleted original** keeps its data, so its clones still resolve.
- **Removing or changing a clone** is an ordinary member change. Its back-reference becomes stale and is removed when next seen.

### Reading and restoring

- `cat`, `cp` out of the tree, `verify` and Unison's reads resolve a clone through its original and check the SHA-256.
- `ls`, `stat`, `du` and `find` list clones like any member, with their own size, mode and mtime.
- `verify` reports a clone whose original is missing or differs.
- **`unpack-tree` runs in two passes.** First it restores every data member, as now. Then it restores every clone with `clonefile` from its original's restored file, after checking the original's SHA-256, and sets the clone's mode and mtime. When the original wasn't restored in this run, or `clonefile` declines (another volume, not APFS, another system), it writes the clone's bytes from the original's container instead. The run reports how many clones were cloned and how many were copied.

Both builds, OCaml and Rust, implement the same format and behaviour, and the cross tests run packs from each build through the other.

## Unison, file to file

A new preference, `clones` (boolean, default false), turns this on. Both sides must offer the `clone-pairs-v0` feature; with an older peer, nothing changes.

Before the receiver transfers a new file `P` with fingerprint `fp`, it looks for **candidates** on its own replica with the same fingerprint:

- the existing transfer hint (`Xferhint`), and
- files it has itself created in this run, kept in a run-local table from fingerprint to final path.

It sends the source one request with `P` and the candidates' paths: `clonePairs(root, P, candidates)`. The source compares clone IDs and refcounts of `P` and each candidate on its own disk, and returns the first candidate that is a clone of `P`, if any. The receiver then:

1. Clones the candidate's file to `P`'s temporary name with `clonefile`, which is the existing whole-source clone path.
2. Checks the fingerprint, as the existing shortcut does.
3. Sets `P`'s properties and publishes it.

If any step declines, `P` is transferred normally.

**Files created in the same run** can be in flight together. The run-local table holds an in-flight entry, with a sequence number and a promise, for every file being created. `P` waits for an earlier entry with its fingerprint only if the source confirms the pair, and only for entries registered before its own. That rules out a cycle of waits. Whichever member of a group finishes first becomes the original for the rest.

Only the original crosses the wire; each clone costs one request and one `clonefile`.

## Unison into and out of packdir (phase 3)

- **Into a packed root:** the receiver uses the same `clonePairs` request. With a confirmed original that is a member of the packed tree, or created in this run, it writes the clone as a reference through packdir's library instead of storing the bytes.
- **Out of a packed root:** the packed side answers `clonePairs` from its `packdir_clone` rows instead of APFS clone IDs. Two members are a pair when one references the other or both reference the same original.

## Tests

- **packdir:** synthetic trees on an APFS disk image (`hdiutil create -fs APFS`) with clone groups inside one container and across containers, plus independent identical copies that must stay independent. They cover pack, verify, stock extraction, unpack (clone IDs checked), rerun, an original changed, removed, renamed and retained, a clone changed, and a crash between back-reference and clone row. They run in OCaml and Rust, with cross runs.
- **Unison:** a local sync onto an APFS image, checked with clone IDs: groups within one run, across runs, against an original already present, with independent copies, with `clones` off, and against a peer without the feature.
