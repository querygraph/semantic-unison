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
No hole is bridged; role runs combine only the roles declared by their selected view. The core1024-node/depth16 limit remains unchanged. The adapter counts
leaves, nonempty opaque gaps and root exactly; excess total nodes are refused.

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

## Dense inline metadata encoding fallback

The first role-run camera retry also safely refused480 grouped regions. That
actual result is retained in `camera-role-runs-v4-actual-20261017.json`. Generated
600-inline-field directories reproduce a further limit: every inline value
alternates with its descriptor and padding, despite being one metadata field.
This models another bounded refusal mechanism; it does not retrospectively prove
which regions dominated the camera's count.

If the original /1 grouping still exceeds the1024-node budget, a separate
`dng-physical-partition/2` view may include each field's descriptor and offset or
padding slot in that field's metadata encoding. The trusted TIFF parser's value
claim determines the role. Unknown fields stay private, known fields stay
standard metadata, encoded-image claims are untouched, and shared header/count/
next-IFD scaffolding remains structural. Only then are touching same-role claims
grouped. Every byte stays exact; physical gaps are never bridged. No descriptor
is promoted to an image or given semantic-merge authority.

Existing accepted /0 and /1 partitions are selected first and remain unchanged.
The /2 metadata hashes deliberately describe encodings, including descriptor and
placement fields, rather than value-only semantic equality. Their new schema
and ordered-member provenance prevent silent reinterpretation of old digests.
A fixed failure now reports raw, physical-run and field-encoding-run counts for
future diagnosis. The raw65536/core1024 bounds remain unchanged. A fitting fragmented graph is
accepted even with more than480 leaves; still-excessive fragmentation refuses
rather than dropping claims. Actual camera support remains
unproved until the separately admitted successor observes it.


The actual V5 readback still refused, with measured counts2178 raw claims,1081
physical runs,894 field-encoding runs and1747 normalized nodes. The unchanged
1024-node cap is now the concrete limit; further field-meaning work is not the
cause. Its actual owner69896/f488f9/0 and all helper/IO/CPU closures are sealed
separately. A future explicitly budgeted larger-forest/checkpoint version needs
source design and qualification; no implicit cap increase or reread follows.

## Explicit larger-forest successor (generated qualification passed)

The measured V5 input needs 1747 normalized nodes. The successor preserves the
generic default1024 API and adds an explicit local ceiling of2048, inherited by
refinement and restore. DNG adapters opt in; peers cannot select the ceiling.
Existing accepted /0, /1 and /2 partitions remain selected first. Newly accepted
1025..2048-node partitions use `dng-physical-partition/3`; gaps remain opaque.

Small checkpoint bytes retain UCH/0. Larger checkpoints use UCH/1 with strict
1025..2048 count; old-version oversized and unknown-version records refuse.
Both versions retain the1MiB serialized limit, depth16, exact identifiers,
canonical partitions, authenticated metadata and full-input restore validation.
A known checkpoint byte-capacity exhaustion leaves the valid observation intact
and skips optional cache publication; operational/ownership exceptions propagate.
This source change does not establish real-camera support until separately
admitted execution, or any hard RSS/physical IO savings claim.

Generated qualification: `tests/qualification/dng-large-forest-actual-20261017.json` records1590 checks/compiler, six builds and actual Update capacity controls. Retained-camera V6 remains a separately admitted observation.

## Actual retained-camera V6

The separately admitted V6 observation passed: DNG/3 covers all193851848B,
including193682116B encoded-image data,152235B standard metadata,6624B private
metadata,70B structural and10803B opaque. FullSHA matches the historical copy;
input8fields unchanged,30typed MakerNote tags/0warnings, parent/helpers0 and
resources closed. Receipt `tests/qualification/camera-large-forest-v6-actual-20261017.json`.
This does not assert decoded-pixel equivalence, exhaustive meanings or a corpus.
