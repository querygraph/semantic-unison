# Built-in DNG merge: opaque camera MakerNote

The built-in `unison:dng-xmp-scalars/0` merge now handles camera DNGs that carry
a MakerNote. Before this change it declined them, leaving the conflict for the
user, which in practice covered most unedited camera files.

## Design

The MakerNote is treated as an opaque blob that still has an identity:

- It is admitted by a new merge-only profile, `org.firstpair.dng-xmp/2`, which
  is the `/1` grammar plus Exif tag 37500 of type UNDEFINED or BYTE.
- Its bytes are a protected extent. The existing complement proof already
  requires every byte outside the XMP packet to be identical in base, left and
  right, so the MakerNote is compared, not understood.
- It may not overlap the XMP packet (`XMP aliases protected extent`).
- The merged packet must keep its exact length and position, which was already
  required. Nothing moves, so any offsets inside the MakerNote stay valid.

The merge tries the profiles in order `/1`, `/0`, `/2`. `/2` is registered
locally only. It is outside the negotiable set, so it cannot be selected with
`semanticprofile` and is never offered to a peer. Transfer is unchanged:
MakerNote files still use the exact layout profile `dng-layout/0`. `/0` and
`/1` still decline tag 37500, and `DNGPrivateData` (50740) still declines.

A pointer scan, rejecting any MakerNote value that could address the packet,
was considered and dropped. On the real iPhone file the packet sits at bytes
414–3185, so ordinary small integers in the 940-byte MakerNote produced 32
false hits, and the scan would have declined the very file it was meant to
admit. The residual risk is a private structure that deliberately points into
the XMP text. A conforming writer has no reason to produce one, and no
byte-level check can tell such a pointer apart from an ordinary small number.

## Evidence (2026-10-21)

Source: `src/dngSemantic.ml{,.mli,.ox.mli.in}`, `semanticFormats.ml`,
`semanticSync.ml`, `semanticDelta.ml`. Builds via `tests/build_snapshot.py`
(make):

| | stock 5.2.0 | OxCaml 5.2.0+ox |
| --- | --- | --- |
| binary sha256 | `91e81be5…c444c` | `687b0458…e8c6a` |
| `tests/dng_reconcile` (16 checks) | PASS | PASS |
| `tests/dng_merge` integration (13 cases) | PASS | PASS |
| `tests/dng_profile_v1` controls | PASS | PASS |
| real iPhone DNG with MakerNote, CLI merge | PASS | PASS |

New reconcile cases:

- `/0` and `/1` still decline the MakerNote fixture with the old reason.
- `/2` declines a MakerNote that overlaps the XMP packet.
- `/2` declines a MakerNote whose type is not opaque (LONG).
- `/2` declines when one side changed a single MakerNote byte (`reconciliation
  protected bytes changed`).
- `/2` merges and materializes a fixture with a MakerNote to an independently
  built target, and still accepts the plain v0 fixture.

Real file: the iPhone 7 Plus coverage-selection DNG (copy), MakerNote kept, XMP
added (Rating 1, Yellow). Left edited Rating to 3, right edited Label to
Purple; one ssh-loopback sync with `-backupcurrent` and
`-merge 'Name *.dng -> unison:dng-xmp-scalars/0'`:

- `Built-in DNG scalar merge verified one exact result (2771 metadata bytes, 1 writes)`.
- Both replicas converged on the exact expected target, at the same length.
- The next sync was a no-op.
- Stock and OxCaml outputs are byte-identical.
- ExifTool reads every tag identically in base and merged, the 14 MakerNote
  tags included, except Rating and Label.
- base sha256 `38ec6f36ef74d87ef0f10ecd09e2953158376358fa695ca3d8d49224a9b96419`
- merged sha256 `0e7c6a0580afc3da30934b8afc4af9d807dfb0bcb666fcac01314cecb1b929d2`

Not rerun: the retained-owner DNG merge successor suite (13 cases/29 calls),
and a Lightroom Classic recheck of the MakerNote pair (staged, pending the user).
