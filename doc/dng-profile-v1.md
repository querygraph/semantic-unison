# Extended DNG XMP packet profile v1

`org.firstpair.dng-xmp/1` keeps the exact-transfer contract of
[v0](dng-profile-v0.md): one out-of-line BYTE tag 700 packet, at most 1 MiB,
with identical offset, length, total file size and every complementary byte.
The exact core hashes the entire file, proves its protected complement and
verifies the complete result. An XMP change can alter development settings;
this profile does not establish rendering equivalence or full DNG validity.

The additional structures are classic TIFF and BigTIFF in either byte order,
and `ExtraCameraProfiles` in the primary image directory. Adobe documents
64-bit DNG independently of its DNGVersion. Embedded camera profiles have
their own byte order, CR magic, classic directory entries and offsets relative
to their own header, including when the containing DNG is BigTIFF.
See the [DNG 1.7.1 specification, pages 18–19 and 48](https://helpx.adobe.com/content/dam/help/en/camera-raw/digital-negative/jcr_content/root/content/flex/items/position/position-par/download_section_733958301/download-1/DNG_Spec_1_7_1_0.pdf).

## Bounded graph and ownership

The shared locator in `DngSemantic.inspect_extended` uses each directory's
explicit layout, byte order and offset base. BigTIFF counts and offsets are
checked as unsigned encodings in the core's positive signed-int64 domain.
Counts are bounded before conversion or table reads; multiplication and
relative-base addition are checked before use. LONG8 image offsets/counts
and LONG8/IFD8 child-directory references are supported in BigTIFF. Signed
image extents and IFD-typed ordinary values decline. XMP must exceed the
layout's inline capacity: four bytes in classic TIFF and eight in BigTIFF.

Main directory nodes, pending child references, camera headers and camera
directories share a 256-item work ceiling. Other limits remain 16,384 total
entries, 65,536 image extents per offset/count field and 131,072 protected
extents. Image, EXIF, GPS and Interoperability policies remain explicit.
Strip, tile and JPEG-interchange data extents, directory tables and all
non-XMP out-of-line values are protected against XMP overlap. The complete
complement proof covers gaps and trailers as well.

Each camera header and directory is protected. Camera values have a separate
finite tag/type policy covering the baseline profile matrices, illuminants,
names/signatures, hue/saturation and look tables, tone curve and scalar
profile controls. Every counted out-of-line camera value is resolved against
its own header base and protected. The initial camera IFD offset must be at
least eight; empty directories, duplicate/repeated nodes, nonzero next-IFD
links, unknown fields, XMP, generic image links and private graphs decline
the entire optimization. Numeric calibration or LUT validity is not inferred.

The profile currently declines modern camera-profile fields whose own grammar
has not been qualified, including external BigTable offset graphs. MakerNote,
DNGPrivateData and arbitrary metadata relocation remain unsupported. A decline
uses ordinary exact transfer. No Adobe code is required for this locator;
optional receiving-file Adobe validation remains a separate policy.

## Negotiation and tools

The compiled `DngExtended` wrapper registers capability `dng-xmp-v1` separately
from v0. `semanticdng` selects v1 before v0 locally. Explicit `semanticprofile`
selection retains its exact chosen IDs. Before preference propagation, the
client expands the shorthand into locally known IDs and sends only IDs whose
capabilities are in the final feature intersection. The outgoing shorthand
bool is encoded as false, clearing a receiver's prior shorthand state without
changing the client's local bool or list. Incoming legacy bool values remain
accepted. The existing bool/list wire formats and archives are unchanged.

An older v0-enabled peer can use v0 for compatible classic DNGs. An explicit
v1-only selection uses ordinary transfer when the peer lacks v1; it does not
silently enable v0. An unknown local ID remains a configuration error.

The read-only developer inspector retains its v0 default and supports an
explicit `--profile org.firstpair.dng-xmp/1`. Full inspection reads and hashes
the file, including large sparse files; it is not a cheap structural-only check.
The focused qualification distinguishes small full-proof/materialization cases
from inspector-only tests of offsets beyond 4 GiB.
