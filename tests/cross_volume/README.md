# Private HFS+ / APFS integration

Run on macOS with already-built CLI binaries:

```sh
python3 tests/cross_volume/run.py \
  --binary stock=/absolute/stock-snapshot/src/unison \
  --binary ox=/absolute/ox-snapshot/src/unison \
  --report /private/tmp/unison-cross-volume.json
```

The runner creates a new 128 MiB HFS+ disk image under an owned private temporary
directory. It mounts that image without Finder browsing/auto-open, and compares
it with private roots on the internal APFS Data volume. It never formats a
physical device, uses a photo volume, initializes Adobe or accesses a catalog.
All files are original random bytes or generated DNG-shaped transfer fixtures;
the latter are not Adobe-validity or rendering evidence.

Each compiler runs ordinary cloning on/off and semantic DNG cloning in both
directions. Every update requires complete byte equality and preservation of an
old receiver hardlink, then a no-op sync with unchanged receiver inode/bytes.
The ordinary APFS receiver reports exactly 1,966,080 inherited logical bytes
for the 2 MiB fixture; the changed 128 KiB comparison interval is copied.
Metadata-only DNG edits use semantic materialization on APFS. HFS+ receiving
uses ordinary exact fallback. Unicode filenames exercise end-to-end normalized
path handling, without qualifying all case/Unicode configurations.

The test detaches only an attachment matched to its own image path, then checks
that attachment is absent before marking the report complete. Failures keep an
incomplete report and retain owned inputs/logs; detach failure requires reviewing
that exact owned image. The image and remaining private APFS fixtures stay in
the printed workspace for inspection. No forced unmount or global cleanup runs.

This is distinct logical-volume qualification on one physical storage device.
It does not prove independent-device scheduling, physical extent sharing,
elapsed acceleration, remount-incarnation detection, crashes, sparse/compressed
files, or all resource-fork/property transitions. The historical preliminary
probes and their detached failures remain private; the final
[12-case receipt](qualification.json) records the accepted matrix.
