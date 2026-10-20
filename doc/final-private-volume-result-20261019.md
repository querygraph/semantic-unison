# Current private cross-volume qualification

The corrected V3 owner completed normally: owning session `19831`, terminal
`bb1af5`, exit 0, no running session. Its 42 direct child commands were reaped
normally with group closure; 36 were Unison seed/update/no-op calls. The owned
128 MiB HFS+ image was normally detached and a fresh image census showed its
attachment absent before CPU/IO release.

| Compiler | Direction | Generic clone auto | Clone off | DNG semantic auto |
| --- | --- | --- | --- | --- |
| stock | HFS+ → APFS | receiver clone | exact ordinary copy | semantic clone/update |
| stock | APFS → HFS+ | exact fallback | exact ordinary copy | exact fallback |
| OxCaml | HFS+ → APFS | receiver clone | exact ordinary copy | semantic clone/update |
| OxCaml | APFS → HFS+ | exact fallback | exact ordinary copy | exact fallback |

Each case used a generated 2 MiB file. The owner checked complete source/target
hashes, preservation of an old receiver hardlink, and unchanged receiver inode
and bytes on the second sync. Unicode filenames were exercised. Generic APFS
receiver updates reported 1,966,080 inherited logical bytes; this is not a
physical-write or shared-extent measurement.

A separate post-closure audit (`604d3a`, exit 0) reparsed all 42 pinned child
records and their exact CLI arguments, all 164 harness and 329 production source
pins, current binary/interpreter hashes, and the saved normal-detach census. It
independently read and hashed the 12 surviving APFS files plus six APFS old-basis
files: 36 MiB total. HFS+ hashes were verified by the source-bound owner before
detachment; no independent remount or post-detach HFS+ payload read is claimed.
That audit acquired and closed the complete Unison8/EX bundle independently.

[Actual receipt](../tests/qualification/final-private-volume-v3-actual-20261019.json)
and [exact plan](final-private-volume-plan-v3-20261019.json) retain the raw
command references and case results. The image and generated fixtures remain
private and detached for inspection.

Two earlier harness failures remain separate evidence:

- V1 used a nonexistent preference. The failed seed output was not persisted by
  its old recording order; its exit code is not invented. The exact image was
  normally detached before independently stopping the idle Python owner. Three
  failed metadata-only recovery helpers were likewise proved idle and stopped.
  Their mistakes and actual terminal 137 results are preserved.
- V2's seed and update both returned 0 and the actual clone counter was saved,
  but the observer checked stdout while debug output was on stderr. It was
  independently recovered after normal detach. This is not a matrix pass.

The corrected successor reuses the qualified preference builder, persists raw
nonzero outcomes before refusal, handles the actual image-info schema, and
includes stderr for CLI observations without mixing stderr into plist parsing.
Twenty-three original controls passed (`114e99`, exit 0), including these cases.
The V3 run used a fresh image/workspace; no old seed/update was replayed.

This qualifies distinct logical filesystems on the same internal physical
storage. It does not establish independent physical devices, sparse/compressed
files, every metadata/ACL transition, timing improvements, real-network behavior,
SDK validity, pixels, Photo workflows or production deployment. No physical
device was formatted; no Photo original/catalog/cache or Adobe SDK was accessed.
