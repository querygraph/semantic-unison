# DNG XMP packet profile v0

`org.firstpair.dng-xmp/0` locates a bounded, out-of-line TIFF tag 700 packet.
An eligible update changes only its addressed bytes, with identical file
length, packet offset/length and every byte outside the packet. The core
independently proves those conditions using SHA-256 and verifies the exact
result. It copies the source packet verbatim.

The classification means **XMP-addressed bytes changed**. It does not mean
the rendered photograph is unchanged: XMP may contain develop settings. This
profile does not decode raw samples, merge metadata, normalize XML, validate
Adobe image digests, or establish full DNG validity.

## Supported subset

The parser supports classic TIFF in either byte order, requires DNGVersion
in the primary IFD, and accepts one non-inline BYTE XMP packet up to 1 MiB.
Current limits are 256 visited plus queued IFDs, 16,384 total entries, 65,536
image extents per offset/count field, and 131,072 protected extents. Those
limits select an optimization; exceeding one remains eligible for ordinary
exact-byte transfer.

The finite tag allowlist is explicit in `src/dngSemantic.ml`. It covers common
TIFF image values, strip/tile/JPEG-interchange offset/count pairs, ordinary
DNG calibration/crop/profile-value fields, and common EXIF metadata. SubIFD,
EXIF, GPS and Interoperability links are followed with a directory-specific
tag policy. Payload ranges, IFD tables and non-XMP out-of-line values are
protected against XMP overlap. All gaps and trailing data are additionally
covered by the core preservation proof.

Unknown tags decline this optimization even when their value looks like a
scalar. Private values can encode offsets rather than self-contained data.
MakerNote (37500), DNGPrivateData (50740), and ExtraCameraProfiles (50933)
currently decline as well; the latter needs its own camera-profile graph
parser before it can be supported safely. The fallback reason identifies the
tag. Merely preserving the bytes of an unparsed pointer does not establish
that its referent is outside XMP.

Other fallback cases include BigTIFF, unsupported versions/types, duplicate
tags/packets, cyclic or repeated IFDs, unsupported private graphs, invalid
offset/count pairs, XMP aliasing protected bytes, changed packet layout, and
changes outside the packet. Pointer-typed values on ordinary scalar tags are
rejected. The queue limit is checked while enqueuing, preventing a compact
table from allocating millions of pending directory references.

Supporting additional tags requires deciding whether their values are
self-contained or refer elsewhere, protecting/traversing those references,
and adding focused fixtures. Do not extend the allowlist merely because a
tag number appears in a metadata report.

## Verification

`python3 tests/semantic/run.py` builds the kernel and synthetic fixtures in a
temporary directory. Pass `--ocamlopt /path/to/ocamlopt` to check a specific
compiler. Tests include both TIFF byte orders, image values and EXIF/GPS/
Interop traversal, private-pointer fallback, bounded IFD fanout, aliasing,
duplicate/cyclic structures, unchanged opaque-byte coverage, exact staging
results and wrong-basis rejection. They use no personal photographs.

Adobe's [DNG 1.7.1 specification](https://helpx.adobe.com/content/dam/help/en/camera-raw/digital-negative/jcr_content/root/content/flex/items/position/position-par/download_section_733958301/download-1/DNG_Spec_1_7_1_0.pdf)
defines the container and profile structures. The supported subset above is
an implementation policy, not a claim to support every structure in that
specification. Optional Adobe validation is a separate receiving-file hook.
