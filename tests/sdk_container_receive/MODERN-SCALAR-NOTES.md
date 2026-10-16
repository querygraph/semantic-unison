The retained SDK1.7.1 JPEG XL control exposed a concrete eligibility gap: its
primary Image IFD contains four ordinary DNG1.7 scalar tags absent from the
finite locator grammar. The original stock/Ox CLI runs fell back correctly to
general receiver cloning; exact target and old hardlink bytes were preserved.
They did not perform SDE. This was not a codec decoding failure.

The `/1` locator now accepts these Image-IFD shapes only:

| Tag | Name | TIFF type | Count |
| --- | --- | --- | --- |
| 52547 | ColumnInterleaveFactor | SHORT or LONG | 1 |
| 52553 | JXLDistance | FLOAT | 1 |
| 52554 | JXLEffort | LONG | 1 |
| 52555 | JXLDecodeSpeed | LONG | 1 |

Source authority: Adobe's installed DNG SDK1.7.1 `dng_tag_codes.h` and
`dng_ifd.cpp` handlers, with the [Adobe DNG specification and SDK](https://helpx.adobe.com/ca/camera-raw/desktop/dng-and-file-formats/digital-negative.html).
These scalar values are self-contained, not offsets. Their directory bytes
remain protected by the complete complement hash. No image decoding or numeric
validity claim is made: e.g. JPEG XL distance semantics still belong to the
validator. Unknown tags and invalid scalar types/counts continue to refuse.

Only the already extensible `/1` grammar changes; wire layouts, envelope format,
complete-byte proofs and `/0` eligibility do not. An older `/1` peer may refuse
these files and trigger normal exact fallback. No metadata-only equality is
used to excuse any protected byte difference.

Independent producer fixtures add classic/BigTIFF, both byte orders, scalar
value changes, and 64 malformed scalar type/count controls. Current CLI checks
then require actual SDE events on the retained JPEG XL container as well as
uncompressed and lossless JPEG. All changed outputs use mock validators here;
Adobe acceptance of these edited outputs requires a fresh coordinated slot.
