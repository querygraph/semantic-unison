This suite checks actual Unison receiving validation selected by locally
registered content recognizers, independently of metadata-transfer selection,
eligibility and suffixes. All inputs, helper drivers, replicas and state are
synthetic and private. No Adobe executable, SDK library, photograph, Photo
catalog/cache, preview generator or production volume is used.

The fixture producer independently serializes classic TIFF and BigTIFF IFD0
DNGVersion claims in both byte orders, including independently opposite-endian
CR profiles. Missing XMP, private pointer fields and future/malformed version
values deliberately separate format recognition from metadata patch
eligibility. These arbitrary payloads do not claim Adobe-valid image pixels.
An ordinary TIFF with XMP but no DNGVersion, a JPEG marker envelope containing
embedded TIFF bytes and ordinary text must not invoke the DNG driver.
Malformed filename claims and bounded indeterminate TIFF structures still
select validation.

The explicitly pinned validation_paths.Session/DRIVER dependency checks the
actual private staged bytes, full hash/size, receiving endpoint and precommit
live destination. This suite leaves that existing21-case harness unchanged.
Required failures must preserve old live bytes, discard rejected staging and
invoke a fresh validator on retry. Both-direction loopback, local new/update,
no-op, directory, external producer, exact local donor reuse, complete/partial
resume and generated merge paths are checked with recognizable renamed files.
The merge fixture preserves Unison's independent per-replica commits.

A separately linked test-only TOY0 companion proves generic registration.
With Adobe policy off and no enabled transfer profile, its own endpoint-local
handler checks the core-provided complete snapshot and can reject toy.bin
before publication. It is not an Adobe validation declaration or production
extension.

Execution requires fresh compiler-matched isolated build snapshots supplied
by the root agent. The runner retains source/compiler/binary/command/log pins,
helper records and synthetic replica artifacts for independent review.
