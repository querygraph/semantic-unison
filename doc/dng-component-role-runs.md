# Bounded role runs for strip/tile-heavy DNG observations

A retained-camera observation completed with30 MakerNote tags but refused the
DNG component parser's480-claim limit. That refusal remains recorded in
`tests/qualification/camera-knowledge-actual-20261017.json`; no complete component
forest or semantic eligibility was inferred from it.

The successor collects at most65536 raw physical claims under the existing TIFF
entry, directory, extent and read rules. It rejects physical overlap before
compaction. Graphs with at most480 claims keep `dng-physical-partition/0` and their
existing field IDs unchanged. Larger graphs may use `dng-physical-partition/1`:
only touching claims of the same role form a `tiff-physical-role-run/1` leaf.
Neither holes nor role boundaries may be bridged. The final480-leaf limit and
core1024-node/depth16 limit remain unchanged; excess fragmentation is refused.

A run ID includes its first logical member and a domain-separated SHA of the
ordered original IDs, schemas and lengths. Physical placement is not part of
that membership digest. Changing unit order invalidates the run's view even if
its physical bytes happen to remain identical. Full-file, layout and independent
role hashes still cover every byte. Encoded pixels remain distinct from decoded
pixels, rendering metadata and opaque residual data.

A coalesced private run is an exact but coarser interpretation boundary. A decoder
bound to a missing former child ID remains unmatched; it gains no new byte or
role authority. Existing snapshots keep their original schema. Current-parser
checkpoint validation must continue to refuse a mismatched old partition rather
than reinterpret old digests. No automatic eager migration is introduced.

Original generated controls cover600 contiguous strips/tiles in both byte orders
and classic/BigTIFF, last-unit edits, private edits preserving pixel views, unit
order provenance, physical aliases, fragmented gaps and raw-claim exhaustion.
They do not establish that the retained camera is now covered. A fresh inspector
artifact and separately admitted readonly observation are required for that claim.
No transfer profile, writer, SDK, receiving publication or default preference is
changed by this advisory geometry path. Logical bounds are not an OS RSS or
physical-IO guarantee.
