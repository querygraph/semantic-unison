This investigation read source only. No Adobe executable or SDK library was
linked or invoked, and no photographic payload was examined.

The local build manifest identifies Adobe DNG SDK 1.7.1 build 2724 at
/private/tmp/unison-adobe-sdk/dng_sdk_1_7_1. Its SHA-256 is
ede0fb503aee112506b8b98b3516df4c5c8b004afc23d73f3bdf7699ea9df87b.
The local SDK includes bounded-parser corrections; version alone therefore
does not pin the examined implementation.

The inspected source and SHA-256 pins are:

| Source | SHA-256 |
| --- | --- |
| dng_shared.cpp | d0a574d1e9f69379645c95c29b6a8148f3aca19568174608f769ce964a84bb3f |
| dng_shared.h | f139fde9281f4ed13b1ee3270d3355b6c7b3186f6474e5748ccaeef18e08cf19 |
| dng_info.cpp | ad0f39425a16d9c267e53c7d36f0e172fb2dab2561bda21f9c8dce61174c6bdb |
| dng_image_writer.cpp | 8da51d8cb9227889458c638fad4bf8dd0aab32a0f208d78784df50affc50542b |
| dng_tag_codes.h | 779e4a6802bad289a39952d9c1599fb827131b736bf4689fa321ad6fcebc06ad |
| dng_tag_types.h | 5ce4f2fe42a1c9fa8a14aa9fa3ef84c36806298c3358dbc2c63d884be6027648 |
| dng_tag_values.h | e6b5e7157c7e7e2a3867c3dd1b51d7d0ed7ae3a762734e26d9e0455fc3d07bdb |
| dng_gain_map.cpp | 2521b53cc72c2ea80f640df5f7ff50bcd01ca32c5e9a151827831b21063af220 |
| dng_big_table.cpp | 0790055f321b48a6232f5d7ab962cbd9937207d05a7129dbbddafab690ce5391 |

The supplied DNG 1.7.1 specification PDF is pinned by
abdecfd8e104e8b86cc054d3a40b677bb2ebe87131bfde080a1df3ee16eb2f8d.
Parent source/spec review establishes that its pages18–19 permit BigTIFF
independently of DNGVersion, and page48 defines ExtraCameraProfiles. The direct
study below relies on SDK source; it did not independently extract that PDF.

dng_info.cpp validates BigTIFF's magic43, offset-width8 and reserved-zero
header, then uses eight-byte directory counts, twenty-byte entries,
eight-byte inline slots and eight-byte next-IFD links. Classic and embedded
CR layout use two-byte entry counts, twelve-byte entries and four-byte slots.
Unsigned offset/count values need independent signed-int64 and multiplication
bounds before applying Unison's file-position representation.

dng_shared.cpp3076–3158 reads ExtraCameraProfiles50933 as LONG or LONG8 absolute
file offsets. The SDK permits up to1000 entries, tries each profile and may
warn/ignore failures. This finite Unison profile instead rejects unsupported
graphs and shares its256 work ceiling across outer directories, CR headers
and CR directories.

dng_camera_profile_info::ParseExtended1577–1720 captures the profile BOM's
absolute position, reads an independent II/MM byte order and uint16 magic
0x4352, and treats its uint32 first-IFD and out-of-line value offsets as
relative to that captured BOM. It never inherits the outer BigTIFF layout.
The comment saying relative to the IFD is imprecise; the actual addition uses
startPosition, the BOM base. Unknown profile tags are ignored by the SDK,
and its reader does not inspect/follow the trailing next-IFD word.

The SDK writer in dng_image_writer.cpp3150–3164 emits the independent BOM,
CR magic, first-IFD offset8 and classic directory with offsets relative to
explicit base8. The directory writer706–790 includes a trailing next-IFD
word; the profile writer emits a single directory. Unison's zero-next-chain
requirement is a deliberately stricter supported subset.

The baseline camera-profile fields recognized by the SDK reader are:

| Tags | Structural value type |
| --- | --- |
| 50708 UniqueCameraModel | ASCII |
| 50932 CalibrationSignature,50936 Name,50942 Copyright | ASCII or BYTE |
| 50778/50779 CalibrationIlluminant1/2 | SHORT |
| 50721/50722 ColorMatrix1/2,50725/50726 ReductionMatrix1/2,50964/50965 ForwardMatrix1/2 | SRATIONAL |
| 50937 HueSatMapDims,50981 LookTableDims,50941 EmbedPolicy,51107/51108 Encodings,51110 DefaultBlackRender | LONG |
| 50938/50939 HueSatMapData1/2,50940 ToneCurve,50982 LookTableData | FLOAT |
| 51109 BaselineExposureOffset | SDK SRATIONAL; parent PDF review identifies RATIONAL; both retained as self-contained eight-byte rationals |

The SDK treats UniqueCameraModel as a standalone profile restriction; the
bounded Unison locator recognizes and protects its counted string without
claiming camera-model matching or full profile validity. Matrix/LUT shape and
scalar count validation is outside this structural eligibility slice. Zero
and undersized declared counts in tests establish bounded locator behavior,
not Adobe validity.

The modern SDK also recognizes52529,52531/32/33/34/35/37/38/39/43/44/49/51/52 in
camera-profile directories. These remain unsupported in the new finite
baseline subset. ProfileGainTableMap2 52544 reads a bounded contained stream;
the old52525 GainTableMap is explicitly excluded from a camera-profile IFD.
RGBTables52539/52543 reads names and sample arrays within a counted tagEnd
(dng_big_table.cpp4083–4177,5023–5098). ProfileDynamicRange52551 is a contained
eight-byte value. These could be separate future additions with their own
reviewed grammar and fixtures.

BigTableOffsets52541 is different: dng_shared.cpp3428–3602 binds absolute
file offsets to BigTableDigests52540 and BigTableByteCounts52542. It must
remain unsupported until its external range graph is implemented and proved
disjoint from XMP; admitting it as an ordinary inline numeric field is unsafe.
Private tags, MakerNotes, arbitrary profile child graphs and per-profile XMP
are likewise excluded.

The related dng-compare source pins are compare_dng.py
0394d34c9844029fbe498d5f892c99b27844bba9a43eb6ee0d36ac561c851900
and rust-scanner/src/main.rs
82d8eb522f0a53d21b4405a603ef8cad8e62a2602ca84d55c73d5dbbd5737ce1.
That tool deliberately distinguishes encoded block equality, decoded stored
samples, raw versus auxiliary pages and metadata differences. Its Rust
scanner skips unselected metadata/profile tags and repeated IFDs, so it is
a comparison/fingerprinting source, not a safe XMP write-scope locator.
No raw-block identity can substitute for Unison's complete-complement proof,
which also covers profiles, previews, opcodes, originals and unknown tail
bytes.
