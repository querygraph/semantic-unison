# Private MakN source constraints

This is a read-only source review of the installed, pinned ExifTool13.10
implementation, not execution of ExifTool, a specification endorsement or a
semantic eligibility decision. Exact three-module identities/hashes match the
existing package inventory in
[the source receipt](../tests/qualification/private-makn-source-review-20261017.json).
No camera or retained-clone payload was opened.

`Image/ExifTool/DNG.pm` builds its Adobe MakN dispatch table from the vendor
MakerNotes table (around140–157). `ProcessAdobeMakN` (around680–755) parses the
wrapper, selects a vendor handler using a bounded prefix, invokes the vendor's
`LocateIFD`, and adjusts the original-offset base only under that handler's
base rules. This is stronger evidence of format diversity than treating every
MakN payload as a classic directory beginning at offset zero. Our current
slice request explicitly tests that candidate geometry; it does not identify
the vendor or assert that the hypothesis is true.

The same routine contains a historical JPEG-conversion header workaround.
`MakerNotes.pm` also handles a Canon-specific original-offset footer. These
are examples of format-specific interpretation, not rules to copy into a
generic safe profile. The AdobeData source notes that references outside the
original maker block may be lost during conversion. Successful metadata
extraction therefore does not establish complete preservation or independence
from XMP and other data.

The next private profile must specify and test:

1. An unambiguous vendor/header identity and exact supported version/layout.
2. The directory start and each reference's origin/base, width and byte order.
3. Every private pointer field, including inline scalar-shaped pointers,
   nested structures, next directories, embedded files and external extents.
4. Complete bounded traversal and overlap checks against the XMP region,
   enclosing TIFF structures and the preservation partition.
5. Independent exact-byte vectors, unsupported variants and changed/private
   reference counterexamples, followed by representative validation evidence.

An in-bounds out-of-line TIFF value is only one part of this contract. A table
with all such extents inside the payload remains semantically ineligible until
the remaining rules are established. Keep unknown layouts on exact ordinary
fallback. No current source-tag allowlist or frozen slice request changed in
this review.
