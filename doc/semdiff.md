# Backing up a shuttle disk: `unison -semdiff`

A shuttle disk such as Kolobok is filled with photo sessions, copied to a
long-term disk such as Photo or Bumer, and then wiped. `unison -semdiff`
answers "is everything on the shuttle kept on the long-term disk?" and makes
it so, without overwriting or deleting anything on the long-term disk:

```sh
unison /Volumes/Kolobok/foto /Volumes/Photo/foto -semdiff -sameview -preservefull -v
```

The first root is the shuttle and the second the long-term root. Both must be
local. The run has three steps:

1. **Compare.** `unison-dngscan -semdiff` walks the shuttle and matches every
   file on the long-term root by the same relative path, else by the same file
   name anywhere under that root. A name found more than once is reported as
   ambiguous; size is never a match criterion. Only the shuttle is walked; the
   long-term root is listed, not read, except for the matched files.
2. **Keep.** With `-preserve`, the differences are kept beside the long-term
   root, never inside it (see the table).
3. **Catch up.** Unison copies the files missing on the long-term root, and
   only those: creation only, no update or deletion on either root, and no
   Unison archive. A wiped and refilled shuttle therefore never deletes or
   overwrites anything on the long-term root. A session folder absent there is
   copied as one directory, unless one of its files was already found there by
   name.

The summary says whether the shuttle is **safe to wipe**: every file must be
byte-identical on the long-term root, preserved in full, or kept as a conflict
copy, and unchanged since it was compared. Anything else is listed by reason
and session folder, and the run exits 1.

## What happens to each file

| Comparison | Meaning | With `-preserve` |
| --- | --- | --- |
| identical | same SHA-256 | nothing to do |
| metadata-only | raw image byte-identical, bytes differ | differences recorded in the dng-compare archive; with `-preservefull` also a verified delta |
| image-differs | DNG raw image or JPEG image data differ | shuttle version copied to `review/foto/` |
| differs | other file types whose bytes differ | shuttle version copied to `review/foto/` |
| missing | not found by path or name | copied by the catch-up step |
| ambiguous | the name occurs more than once | listed; resolve by hand |
| unavailable | the long-term root is not mounted | listed; compare later |

- **DNG image.** The encoded raw image (the largest image directory's strips
  or tiles) is compared by SHA-256, and the previews as a set.
- **JPEG image.** Every segment except APPn and COM metadata, through the
  first EOI, is compared by SHA-256. Bytes after the EOI (MPF images) count
  as previews.
- **Metadata.** Differences come from dng-compare's exiftool-rs worker, so tag
  names and values are the ones dng-compare stores.

## Where things are kept

Next to the long-term root `R` (for example `/Volumes/Photo/foto`):

| Option | Kept in |
| --- | --- |
| `-preserve` | `R/../dng-compare/SHUTTLE` (for example `/Volumes/Photo/dng-compare/Kolobok-foto`), a dng-compare archive whose rows are only ever added |
| `-preservedb DIR` | that archive instead (implies `-preserve`) |
| `-preservefull` | implies `-preserve`; the same archive also holds each metadata-only file as a VCDIFF delta from dng-compare's `preserve_apo.py`, verified to rebuild the exact file |
| default for conflicts | `R/../review/NAME/` with the same relative path, where NAME is R's own name: `/Volumes/Photo/review/foto/…` and `/Volumes/Photo/review/jpg/…` never collide |
| `-tree TREE` | `R/../TREE/NAME/` instead |
| `-suffix` | beside the long-term file as `NAME_2.EXT`, `NAME_3.EXT`, … |
| `-suffix=SUF` | beside the long-term file as `NAME_SUF.EXT` |

`-suffix` with a value must be written `-suffix=SUF`, because Unison would take
a separate word as a root or profile name.

The archive records each shuttle file once per version (size and modification
time). When a later shuttle cycle brings new contents at a path already
recorded, its differences are added as a new dng-compare file version, stamped
with the run. `-preservefull` keeps one full-file record per path, so it does
not replace an earlier version; such files are listed as already holding
another version and stay "not safe" until handled by hand.

Conflict copies are verified by SHA-256 against the shuttle file and never
replace an existing file; an identical copy from an earlier run is reused.
Restore a preserved file into a new location with dng-compare:

```sh
cd ~/src/dng-compare
uv run python preserve_apo.py restore /Volumes/Photo/dng-compare/Kolobok-foto 2026/April/S/F.DNG /tmp/F.DNG
```

## Same view

`-sameview` marks a metadata-only pair as **same view** when no changed tag can
affect rendering. The list of non-rendering tags is dng-compare's
`metadata_rules.json`, shared by both tools: ratings, labels, keywords, titles,
captions, dates, GPS, IPTC and similar. Any tag not on the list, including every
`crs:` develop setting, orientation and lens data, counts as possibly rendering.
Text padding (trailing spaces or NULs) is not a change, and repeated `CopyN`
occurrences are compared as sets. This is a metadata rule, not a comparison of
rendered images.

## Disks

A root on a disk that `diskutil` does not report as solid state (a spinning
disk, or an enclosure that does not say) is read by one stream at a time,
across all workers, so it never seeks between files; solid-state roots are
read in parallel. Both files of a pair are read at the same time. `-hdd PATH`
marks PATH's disk (any path on it, once per disk, for example
`-hdd /Volumes/Photo`) as spinning, and `-ssd PATH` as solid state, whatever
`diskutil` reports. Both are recorded on the disk itself, as `disk = hdd` or `disk = ssd` in
`MOUNT-POINT/.semantic-unison` (for example `/Volumes/Photo/.semantic-unison`),
so they are given once and hold for every later run, on any Mac.

## Progress

A progress line every minute gives files and bytes compared (files with a
match only; missing files cost nothing), MiB/s over the last ten minutes, the
time left and the counts so far. `-v` adds listing progress (the first listing of a
large long-term root takes minutes; later ones reuse the `.walk` cache), a line
for each file that is not identical, and dng-compare's preservation output.
`^C` is safe: rerun the same command and finished comparisons are reused.

## Faster reruns and other roots

- **`-review`** reruns only on the conflicts in the previous report of these
  roots. It keeps them as `-tree`/`-suffix` says and scans or synchronizes
  nothing else, for example after a `-preserve` run without a placement
  option:

  ```sh
  unison /Volumes/Kolobok/foto /Volumes/Photo/foto -semdiff -preserve -review -suffix
  ```

- **Repeated runs reuse results.** The report lives in the Unison directory,
  as `semdiff-HASH.jsonl` next to its `.walk` listing cache and `.catchup`
  list. A file pair is compared again only if either file changed. Missing,
  ambiguous and unavailable files are always looked at again.
- **`-semdiffroot ROOT`** adds another long-term root, such as Bumer, that
  counts for "safe to wipe". Only the second Unison root is caught up.

## `unison-dngscan` directly

The same steps are available without Unison:

```text
unison-dngscan -semdiff ROOT... [-sameview] [-preserve [-preservedb DIR] [-preservefull]
               [-tree NAME | -suffix[=SUF]]] [-catchup [-catchupto ROOT]]
               [-o REPORT.jsonl [-resume]] [-cache WALK] [-j N] LEFT [-- UNISON-ARGS]
unison-dngscan -summarize [-catchup ...] REPORT.jsonl...
unison-dngscan -review -semdiff ROOT -o REPORT.jsonl [-tree NAME | -suffix[=SUF]] LEFT
```

- **`-summarize`** combines reports from different days and disks, for
  example Kolobok against Photo while Photo was attached, and Kolobok against
  Bumer now. A file is safe if any report shows it kept and it hasn't changed
  since.
- **`-catchup`** runs `unison LEFT ROOT -semcatchupfrom LIST` with the list
  just written.

dng-compare is found through `DNG_COMPARE_HOME`, default `~/src/dng-compare`.
`-preserve` needs `uv`; `-preservefull` also needs `xdelta3`.

## Tests

```sh
python3 tests/semdiff/run.py --unison PATH/unison --dngscan PATH/unison-dngscan
```

It uses synthetic DNG and JPEG fixtures in a private temporary directory, and
covers each comparison, the catch-up, both conflict placements, `-review`, the
dng-compare index, a restore from a delta, and a wipe and refill of the
shuttle.
