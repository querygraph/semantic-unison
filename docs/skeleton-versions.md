# Skeleton versions

Unison can keep the versions of a file it replaces as *skeleton versions*
instead of whole backup copies. A metadata edit to a photograph (a rating,
develop settings such as exposure or blacks, IPTC) rewrites the file's small
structures and carries its large blocks over unchanged, often at other offsets.
A skeleton version stores only what the edit destroyed, so several successive
edits of one file each cost a few hundred bytes, and any of the last N
replaced versions can be rebuilt exactly.

## Use

```
skeleton     = Name *.dng
skeleton     = Name *.jpg
skeleton     = Name *.xmp
skeletonnot  = Path scratch
maxskeletons = 3
skeletondir  = /path/outside/the/replicas/skeletons
```

| Preference | Meaning |
| --- | --- |
| `skeleton` | Path specification of the files whose replaced versions are kept. |
| `skeletonnot` | Exceptions to `skeleton`. |
| `maxskeletons` | How many earlier versions are kept per path. Default 0: nothing is kept and the store is not touched. |
| `skeletondir` | The store. Checked after the environment variable `UNISONSKELETONDIR`; the default is `skeletons` in the Unison directory. |

Each replica root has its own subdirectory of the store, named by a hash of the
root's canonical path, so one directory serves several roots. The store must
not be inside a replica. Each host keeps the versions of the files replaced on
that host, in its own store; the preferences travel to the server like the
backup preferences, and a server built without them ignores them.

The program `unison-skeleton` reads a store:

```
unison-skeleton list    ROOT [PATH] [--skeletondir DIR]
unison-skeleton verify  ROOT [PATH] [--skeletondir DIR]
unison-skeleton restore ROOT PATH (--version N | --sha256 HEX) --out FILE [--skeletondir DIR]
```

`list` prints each version's number, the time it was replaced, its size and
SHA-256, how it is stored and in how many bytes. `verify` rebuilds every kept
version to nowhere and checks its SHA-256; it exits 1 when one cannot be
rebuilt. `restore` rebuilds one version into a new file, checks the SHA-256 of
the stream and of the file written, and leaves nothing when they differ. It
refuses a `--out` inside the replica or the store and never overwrites a file.
A version's number is permanent for its path: pruning older versions does not
renumber the rest. `ROOT` is the root as the profile names it; `PATH` is
relative to it. The tool finds the store as the synchronizer does
(`--skeletondir`, then `UNISONSKELETONDIR`, then the default).

## Blocks and skeletons

A file is cut by its own structure into *blocks* and the *skeleton*: every byte
outside the blocks, in file order. The rules are those of the dng-compare
archive specification, section 13.1, and `src/skeleton.ml` is adapted from that
project's OCaml implementation so that the cuts agree:

- Classic TIFF, which includes DNG and TIFF-based raw files: strips, tiles,
  embedded JPEG streams, any other out-of-line value of 512 bytes or more
  except XMP, IPTC and Photoshop resources, and any run of 65,536 bytes or more
  that no tag points at.
- JPEG: every segment of 512 bytes or more other than APP1, APP13 and COM, and
  everything from the start of scan to the end.
- Any other file, or one whose structure cannot be walked, of at most 1 MiB is
  its own skeleton, with no blocks (format `whole`). XMP sidecars are kept this
  way.

A block is identified by its length and its *mark*, the first 32 hex digits of
the SHA-256 of its first and last 4,096 bytes. The store also records the
SHA-256 of each whole block (see "Where this departs from the plain method").

## What happens when a file is replaced

1. Just before the replacement (`Stasher.backup`), the outgoing file becomes a
   *pending* item of the store: a clone where the filesystem makes one, else a
   copy. If that fails the file is not replaced, as with a failed backup.
2. Once the new file is in place (`Stasher.settleSkeletons`, called from
   `Files` after the rename), the pending item is *settled*:
   - the outgoing file's skeleton is cut, and its SHA-256 and that of each of
     its blocks are computed;
   - each block is looked up, by length and mark, among the blocks of the new
     file, and counts as present only when the whole block's SHA-256 is equal;
     a block the new file does not hold is saved in the store under its
     SHA-256;
   - the record (block map and skeleton bytes) is written;
   - the outgoing content is rebuilt from the record, the new file and the
     kept blocks, without the pending file, and its SHA-256 is compared;
   - only then the pending file is deleted.
3. The previous newest record is rewritten as a delta against the new one, and
   versions beyond `maxskeletons` are pruned, oldest first, with the kept
   blocks no remaining version names.

If the replacement did not happen (the transfer failed after step 1), settling
finds the same content at the path and keeps no version. A pending item left by
an interrupted run is settled at the next start (with `maxskeletons` positive)
or at the next replacement of the same path, whichever comes first; until then
it is in the store as a whole file. Settling never fails a transfer: an item
that cannot be settled stays pending and is reported in the log.

## Nothing is lost silently

A version that cannot be kept as a skeleton is kept as a whole file. It counts
in the chain and is pruned by depth like any other. This is the case for:

- a file that is deleted, or replaced by something that is not a file (a
  directory, for instance): there is no later file to hold its blocks. The files under a deleted directory are
  treated the same way, each on its own path. A deleted file is moved into the
  store when that is a rename, so it costs no copy;
- a file with no walker that is larger than 1 MiB (video, for instance). Use
  `skeletonnot` for large files whose earlier versions are not wanted;
- a file whose skeleton would be larger than 16 MiB;
- a version whose rebuilding check fails for any reason.

A file of at most 1 MiB without blocks, such as a sidecar, is its own skeleton
and needs no later file, deleted or not.

A whole version also serves the versions before it: their blocks are looked up
in the current file, then in the whole versions of the chain, then among the
kept blocks.

## The store

```
STORE/ROOTKEY/root                 the root's path, for people
STORE/ROOTKEY/lock                 locked by the process changing this root's store
STORE/ROOTKEY/pending/PATHKEY      one small file per pending item, naming its path
STORE/ROOTKEY/p/PA/PATHKEY/index   the chain of one path
                         N.full    version N's record
                         N.delta   the same, as a delta against a newer record
                         N.whole   version N kept as a whole file
                         N.pending a replaced file not yet settled
                         blocks/SHA256   a kept block
```

`ROOTKEY` and `PATHKEY` are the first 32 hex digits of the SHA-256 of the
root's canonical path and of the path inside the root. The index is a text
file with one line per kept version, oldest first: number, time, size, SHA-256
of the content, kind, format, SHA-256 and size of the record, how the record
is stored, and stored bytes, then the word `lost` for a version found to
need a block that no file holds and the store did not keep. Every file is written under a temporary name,
flushed and renamed; the index is written after the files it names, and files
the index does not name are removed afterwards.

A record is the block map (offset, length, role, mark and SHA-256 per block)
followed by the skeleton bytes. The newest record of a path is stored in full;
each older one is a delta against the next newer record (`src/skeletonDelta.ml`:
COPY and INSERT operations found by hashing 16-byte windows of the base, no
external compressor). A record whose delta would not be smaller stays in full.
Every record has its own SHA-256 in the index, checked whenever it is read, so
a damaged delta fails the versions that depend on it instead of producing a
wrong file; the SHA-256 of the rebuilt content is checked as well. Pruning the
oldest version removes its delta; nothing depends on the oldest.

In the synthetic chain of `tests/skeleton` (a 32,858-byte file with a
6,058-byte skeleton, each edit changing a few values and adding a line of XMP)
the first version costs 6,508 bytes and each further one about 375 bytes while
the chain fills: a 118-byte delta, the 64 bytes the skeleton grew by, and a
line of the index. With the chain full, the store grows by the skeleton's own
growth only.

## Ordinary backups

`skeleton` and `backup` are independent. A path that matches both gets both: a
skeleton version in the skeleton store and a backup file where the backup
preferences put it. Skeleton versions keep content only, not permissions,
times, extended attributes or resource forks, and only of regular files.

## Limits

- **Local edits between synchronizations.** A version's blocks live in the
  current file. If the current file is then edited *on this replica* in a way
  that destroys a block (an application regenerating an embedded preview, for
  instance) before Unison next replaces it, the versions that need that block
  can no longer be rebuilt here: nothing saw the block go. Unison cannot
  prevent this, but it does not stay silent. The next time it replaces the
  file it checks every earlier version against what is left, logs a warning
  for each one that has become unrebuildable, and marks it `lost` in the
  chain, once. `unison-skeleton list` shows the mark, `verify` reports the
  version and `restore` refuses it. The replica that *receives* such an edit
  through Unison saves the block at that moment, as described above, so the
  other replica's store usually still has the version. A local edit that only
  rewrites metadata does no harm. After running an application that rewrites
  previews or pixels in place, `unison-skeleton verify ROOT` says at once what
  was lost.
- **Cost of a replacement.** The outgoing file is read once and the new file's
  matching blocks once or twice. Where the filesystem has no clones, or the
  store is on another volume, the pending item is a full temporary copy of the
  outgoing file. That path has been run with the store on a separate HFS+
  volume and with the receiving root itself on HFS+.
- **One writer at a time.** Each change to the store is made while holding a
  lock on the file `lock` of the root's directory in the store, so two
  synchronizations that share a root cannot interleave their changes. The lock
  is waited for and is released when the process ends, however it ends.
  `unison-skeleton` only reads, and reports a chain that changes under it as
  an error to be retried. Two synchronizations that replace *the same path* of
  the same root at once are still a conflict between them: the store stays
  sound, but only one of the two outgoing contents becomes a version.
- **Roots are named by path.** Moving or renaming a root starts a new
  subdirectory of the store. The earlier versions stay under the old name and
  can be read by giving `unison-skeleton` the old root path, but skeleton
  versions then find no current file to take blocks from, so only those kept
  whole or as their own skeleton restore. Before moving a root, restore what
  you want to keep, or keep the old path available (a symbolic link does)
  until the versions have aged out. A store that follows a moved root is not
  built; `TODO.md` records it.
- Classic TIFF and JPEG only. BigTIFF, HEIF, video and other containers are
  kept whole (or as their own skeleton up to 1 MiB).

## Where this departs from the plain method

The plain skeleton method matches blocks by length and mark alone and relies
on the whole-file SHA-256 to reject a block whose middle changed. In a chain
that is not enough: if image data changes between a block's two ends, the
version being replaced can be kept whole, but the versions before it would
quietly take the changed block from the current file and fail. The store
therefore records each block's whole SHA-256 and names kept blocks by it. A
block whose middle changed is simply a block the new file does not hold: it is
saved, and the replaced version and those before it stay rebuildable as
skeletons. Rebuilding first tries the cheap way (marks only); when the result
has another SHA-256 it rebuilds again, comparing whole-block SHA-256s.

## Tests

`tests/skeleton` (run with `dune build @tests/skeleton/runtest`) builds small
TIFF, JPEG and sidecar files in memory and covers: the walkers' cuts against
values produced by dng-compare's implementation for the same bytes; the delta;
a chain of five edits with three versions kept; a replaced block; a change in
the middle of a block; a version made to fail its check; sidecars; pending
items; deletion; large files without a walker; damage to the store; and a real
synchronization of two local roots followed by `unison-skeleton list`,
`verify` and `restore`; an edit made outside a synchronization that destroys
a block, found and marked lost; and the root's lock held against a second
process. The built-in self-test (`unison -selftest`) has a "skeleton versions"
case as well.

Beyond those, the feature has been run on real DNG and JPEG files edited by
Lightroom Classic and Photo Mechanic: between two local roots, with the
receiving root served by a second Unison process over the remote protocol
(through a stand-in for `ssh` on one machine, not across a network), with the
store on a separate HFS+ volume, and with the receiving root on HFS+. It
builds and passes its tests with stock OCaml 5.2.0 and with OxCaml 5.2.0+ox
and 5.4.0+ox.
