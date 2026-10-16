# JPEG standard XMP exact-transfer profile

The opt-in profile `org.firstpair.jpeg-xmp/0` locates one nonempty standard
APP1 XMP packet before the first scan. Enable it explicitly:

```text
semanticprofile = org.firstpair.jpeg-xmp/0
```

Or pass `-semanticprofile org.firstpair.jpeg-xmp/0` on the command line.
It negotiates `jpeg-xmp-v0` independently of DNG capabilities. Default selection
is unchanged; `semanticdng` enables only DNG. JPEG filename hints `.jpg`/`.jpeg`
are advisory: contents determine eligibility. Existing generic workers, SDE/0,
receiver-basis clone staging, verification and publication provide the data path;
there is no JPEG-specific transport or publication shortcut.

The locator uses the standard null-terminated APP1 signature documented in
[Adobe's JPEG XMP handler](https://github.com/adobe/XMP-Toolkit-SDK/blob/main/XMPFiles/source/FileHandlers/JPEG_Handler.cpp).
Segment lengths include their two-byte length field. The signature and framing
remain protected; only the exact packet extent is editable, including padding.
The maximum packet is65504 bytes; headers are bounded to16MiB/4096 markers and
4096 fill bytes per marker, with8192 cumulative marker prefix/fill bytes. One supported pre-scan frame and bounded scan
header are required. Extended XMP before the first scan, duplicate/empty main
packets, unsupported markers and malformed/truncated framing decline this
profile. Declining eligibility selects ordinary exact transfer.

Same-offset/same-length packet edits use the existing preservation and full-file
proofs. Changed EXIF, ICC, entropy, marker framing, trailers or opaque APP data
cannot be hidden: all bytes outside the packet must match the basis. Packet
growth/relocation falls back. Materialization verifies exact target bytes and
never rewrites a published file in place. Changed metadata is not automatically
merged, normalized, interpreted as rendering-equivalent or used to authorize
Lightroom preview reuse. This version has no property observer; exact packet
classification and bounded raw samples remain available through the generic
reporting path. Adobe DNG validation is a separate DNG companion, not JPEG
validation.

This is a metadata locator, not a JPEG decoder or validator. It stops parsing at
the first scan; later scans, markers, entropy, EXIF/ICC contents and trailers are
opaque protected bytes, including any later metadata. The initial frame's
geometry check is not image consistency proof. A packet need not be valid XML
for exact transfer. No image/pixel equivalence or other application's native
registration is inferred from an eligible manifest.

Qualification includes independent Python framing/offset fixtures (139 per
compiler), exact completed and fallback outputs, boundary/malformed cases,
actual bidirectional mixed-compiler CLI/receiver tests, old-peer fallback,
DNG-only opt-in behavior, fresh Make and Dune CLI builds/selftests, existing DNG
remote regressions, and one privately generated JPEG with unchanged ImageIO
raster after exact reconstruction. Source/binary/receipt pins are retained in
[the qualification record](../tests/jpeg/qualification.json). This root-owned
record is not representative JPEG corpus, Adobe/Lightroom, GUI, other-platform,
new extended-XMP or measured throughput qualification.

The cumulative fill bound closes a multiplicative small-read workload: per-marker limits alone allowed thousands of individually bounded fill runs. The new shared counter caps total prefix/fill reads; exact8192 and8193 boundary controls and genuine prior-binary acceptance are pinned in [the follow-up qualification](../tests/jpeg/fill-bound-qualification.json). Initial qualification remains immutable historical evidence.
