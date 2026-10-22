# Semantic Unison fork: release TODO (macOS)

Status, 2026-10-21: usable by the author and a few informed testers. Not ready
for general release. (Upstream's own list is `src/TODO.txt`.)

## Done

- Camera DNGs that keep their MakerNote can be merged, through the merge-only
  profile `org.firstpair.dng-xmp/2`. Unit, integration, the long retained-owner
  suite and a real iPhone DNG all pass on stock OCaml and OxCaml
  ([result](doc/dng-merge-opaque-makernote-result-20261021.md)).
- `DNGPrivateData` (50740) accepted the same way in `/2`, plus ImageNumber and
  CacheVersion. Two real Lightroom-converted Panasonic DNGs merge on both
  compilers.
- Scope is macOS only, so Linux and Windows are not release blockers.

## Blockers

1. **Real Lightroom edits as merge input.** Every merge so far used edits made
   by hand: same-length byte swaps of Rating and Label. When Lightroom saves
   metadata to a DNG it likely also changes other fields, such as
   `xmp:MetadataDate` and `ModifyDate`, and possibly develop settings. It may
   also grow or re-lay out the XMP packet. Any of these makes the merge decline
   and leave the conflict. That is safe, but if it happens on every real edit,
   the feature does nothing in practice. This is the most important unknown.
2. **Other cameras and converters.** `/2` now admits every simple numeric or
   text tag, sub-image XMP packets, and the gain-table map. LONG, BYTE and
   UNDEFINED fields still need a name. `unison-dngscan -tags` records unknown
   fields for review, and `dngmergeadmit` admits one field at a time after
   review. The full Photo scan (1.59M DNGs) is running. Its Smart Preview
   declines, large develop-settings packets, tag 52545 and Leica NUL-padded
   packets, UNDEFINED primary XMP and tag 37398 are now covered. Still
   declined: Rating or Label written as XML elements instead of attributes
   (Lightroom mobile), files without XMP, and truncated recovered files.
3. **No real network SSH runs.** All runs were same-machine loopback.
4. **Open acceptance-map items** ([map](doc/sol-final-acceptance-map-20261019.md)):
   - negative cases where corrupted data is received;
   - some failure/recovery combinations;
   - parallelism on other machines and topologies;
   - no claim of surviving a crash or power loss.
5. **No fuzzing.** Excluded by the owner's choice. Robustness against hostile
   files rests on the fixed cases only.
6. **No human review** of the roughly 26k agent-written lines.
7. **No packaging:** builds, signing, user docs, version and compatibility
   statement, licence notes.
8. **Fork only.** Upstream's CONTRIBUTING.md rejects LLM-written code, so this
   can never go upstream as patches to bcpierce00/unison.

## Next

1. Run a real Lightroom round-trip on Capitola, in two scratch catalogs over
   copies of one DNG (deferred until the owner is home on a fast network):
   - set a rating in one catalog and a label in the other;
   - run "Save Metadata to File" in each;
   - let Unison merge the two copies;
   - repeat with a Lightroom-converted DNG.
2. If the merge declines, its message says why. That decides what to widen
   next: the date fields, packet growth, or 50740.
