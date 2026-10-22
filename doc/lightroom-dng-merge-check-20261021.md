# Lightroom Classic check of a built-in DNG merge: PASS, with one decline finding

A real camera DNG went through Unison's built-in `unison:dng-xmp-scalars/0`
merge. The user then opened the base and the merged result in a Lightroom
Classic scratch catalog on Capitola. The merged file imported cleanly, and
Lightroom showed the merged metadata. The Main catalog, its caches and the
original photos were not touched.

## Fixture

- Source: the smallest coverage-selection DNG (iPhone 7 Plus, 16.7 MB), from
  `lightroom/.private/photo/preview-generator/coverage-selection-v1/crop-source-89982949/source.dng`.
  The work used a copy; the original was only read.
- XMP was added with `exiftool -api XMPShorthand=1`, giving Rating 1 and Label
  Yellow as attributes.
- Both replicas were seeded with that base. The left replica was then edited
  to Rating 3 and the right replica to Label Purple. Each edit was an in-place
  byte replacement of the same length.
- The sync was one ssh-loopback Unison run (`-merge 'Name *.dng ->
  unison:dng-xmp-scalars/0'`, `-backupcurrent`). It used a temporary build of
  this branch under CPU04.

## Unison result

- Both replicas converged on the expected target: base bytes with Rating 3
  and Label Purple.
- The merged file is the same length as the base.
- A following sync reported nothing to do.
- base.dng sha256: `b76fbf83c8f00137a9dcc531339a3df573b5ead478ecc1afe62cd51b6278e1ab`
- merged.dng sha256: `49d521ee3e08dc3fc1ca4e3f3febbe1e087d44d91326c2cf4bf2e4717cab387a`

## Lightroom Classic result (user-run, scratch catalog)

- Both files imported.
- Metadata is correct: base.dng has 1 star and a Yellow label; merged.dng has
  3 stars and a Purple label.
- No warning or damaged-file message.
- The user reported "it all works".

Import note: with Lightroom's default "Don't Import Suspected Duplicates", one
of the two files was hidden until the user unchecked the option. The merge
leaves the file length and the capture metadata unchanged, which is most likely
why Lightroom treats the two files as the same photo. This is expected for a metadata-only merge and is not
a fault. Future checks should turn the option off, or import each file into
its own catalog.

## Finding: camera MakerNote causes a decline

The same DNG with its MakerNote still present (EXIF tag 37500, 16,742,370
bytes) is declined by the built-in merge, and the item stays a conflict. The
merge refuses to rewrite files outside its fixed-region profile, so this
decline is the designed fail-closed behaviour. It does mean that unedited
camera DNGs which carry a MakerNote are not merged automatically today.
Removing the MakerNote (16,741,418 bytes) is the only change between the
declined file and the file that merged.
