# Semantic Inspection Report 0 (experimental)

SIR/0 is a bounded description of one observed current file. Two descriptions
support owner-side diff and details display. It is an experimental protocol,
not an adopted standard or a synchronization decision. The implementation is
`src/semanticReport.ml`; `src/semanticRemote.ml` supplies the negotiated RPC.
Conformance tests are in `tests/report` and CLI qualification is in
`tests/test_semantic_reports.py`.

## Observation contract

Inspection uses a locally compiled, enabled versioned format handle. The core
validates its editable regions and computes the whole data-fork SHA-256, the
protected-byte SHA-256, and each editable region's SHA-256. The protected hash
uses the same domain-separated transcript as
[SDE/0](semantic-delta-v0.md#preservation-hash-transcript), including file size,
region placement and every complementary byte. Samples contain original bytes,
without XML parsing, normalization or reserialization by the reporting layer.

A report has one of three observation kinds:

- **Supported:** validated region description, hashes and bounded byte previews.
- **Unsupported:** the selected profile cannot describe this file or is not
  locally enabled and negotiated; a bounded reason is included.
- **Unavailable:** inspection could not be obtained, for example because the
  peer lacks the feature, the file changed, or the operation was cancelled.

These are observations of current data forks. They include no archived base,
filesystem properties, resource forks, Adobe validation result, rendering
equivalence or metadata merge. They do not change Unison fingerprints,
reconciliation choices, conflict handling, transfer eligibility or commit rules.

The owner checks descriptor stability during inspection and checks that the
pathname still identifies the observed file before returning the report. These
checks compare device, inode, file kind, length, modification time and change
time. They detect ordinary mutation and replacement; they do not freeze a file
against future edits or provide a filesystem snapshot guarantee.

## SIR/0 encoding

The complete report is at most **32,768 bytes**. All integers are unsigned
64-bit big-endian; values above `2^63-1` are rejected. Hashes are raw 32-byte
SHA-256 values. Offsets refer to bytes in the data fork. No trailing bytes,
unknown versions, observation kinds or flag values are accepted.

| Field, in wire order | Bytes | Meaning |
| --- | ---: | --- |
| Magic/version | 8 | `53 49 52 00 00 00 00 00` |
| Profile length | 8 | 1..128 |
| Profile | profile length | Exact versioned identifier; no NUL |
| Request nonce | 32 | Exact caller binding; not authentication |
| Observation kind | 1 | 0 supported, 1 unsupported, 2 unavailable |
| Observation body | variable | Defined below |

For kinds 1 and 2, the body is `reason_length:u64, reason:reason_length`.
The reason is at most **1,024 bytes**. Reasons are diagnostic byte strings,
without a text-encoding requirement.

For kind 0, the body is:

| Field, in wire order | Bytes | Meaning |
| --- | ---: | --- |
| File length | 8 | Observed data-fork length |
| Whole-file SHA-256 | 32 | Every byte in the data fork |
| Protected-byte SHA-256 | 32 | SDE/0 preservation transcript |
| Region count | 8 | 1..64 |
| Region records | variable | In ascending, nonoverlapping order |

Each region record is `offset:u64, length:u64, metadata_sha256:32,
prefix_length:u64, prefix:prefix_length, truncated:u8`.

- Region length is 1..1,048,576 bytes. The region must fit entirely inside the
  file. Adjacent regions are permitted.
- Total region length must not exceed the selected handle's declared
  `max_payload`: DNG declares 1 MiB; the generic core ceiling is 16 MiB.
- Each prefix contains at most 4,096 bytes and cannot exceed its region length.
  All prefixes together contain at most 8,192 bytes. Regions retain their
  description even when the sample budget leaves an empty prefix.
- `truncated` is exactly 0 when prefix length equals region length and exactly
  1 otherwise. A complete prefix's SHA-256 must equal `metadata_sha256`.
  Truncated previews cannot independently establish the complete region hash.

The current sampler spends the aggregate preview allowance in region order,
up to 4,096 bytes per region. A decoder validates framing, arithmetic, region
bounds, sample limits and complete-prefix hashes. The profile and nonce must
equal the request's expected values. Direct decoder users must bound input
before allocating it; the decoder itself receives an existing string.

## Pair classification and display

For two supported observations, the owner reports:

- **Exact bytes:** file lengths and whole-file hashes match.
- **Editable metadata differs:** profiles, file lengths, region lists and
  protected-byte hashes match, and at least one complete region hash differs.
- **Other bytes or layout differ:** the equality conditions above do not hold.
- **Unavailable classification:** either observation is unsupported or
  unavailable, or hashes contradict the intended partition (different full
  hashes despite equal protected and editable hashes).

An editable-metadata classification concerns this observed current pair. It
does not identify which replica changed against an archive, and does not
resolve a conflict. Metadata can affect image presentation.

Display includes the profile, classification, file and region byte lengths,
whole/protected/metadata hashes, and escaped byte previews. Control and
non-ASCII bytes are escaped; truncated previews are labelled. Diagnostics and
replica labels are escaped too. Rendered output is capped at 65,536 bytes.
A preview is a byte sample, not an XML diff or a complete packet guarantee.

## Negotiated transport and resource lifetime

Peers negotiate the additive `semantic-inspect-v0` feature using RPC version 1
or later. This feature does not change the archive format and is independent
of `semantic-delta-v0`. The selected profile must also be enabled and its own
capability negotiated. An older peer yields an unavailable observation; the
UI does not fetch the complete file to emulate this report.

`semanticInspectV0` uses existing Umarshal framing for three bounded strings:
an absolute pathname (at most 16,384 bytes, no NUL), profile (at most 128 bytes,
nonempty, no NUL), and nonce (exactly 32 bytes). The caller generates the nonce
from the existing OS random source. The response is one bounded SIR/0 string.
The command request-body cap is **17,568 bytes** and response-body cap is
**33,792 bytes**, including allowances for outer framing; the report string
itself remains capped at 32,768 bytes. Request and pending-response body caps
are checked before allocating those bodies. Shared legacy message-header
decoding precedes command identification and remains outside these body caps.

Inspection holds a Source reservation under the same global transaction,
estimated-payload and descriptor admission gate as semantic transfer. The
source cost derives from the selected profile's declared payload bound; worker
hashing shares the process CPU permits. The source reservation remains held
through report construction, marshaling and queued output consumption. On
disconnect, queued output is settled and pending admission is cancelled;
resources borrowed by running jobs remain owned until those jobs stop. These
credits bound the stated retained resources, not process RSS, child RSS or
per-volume I/O concurrency. See [worker limits](semantic-workers.md).

Nonce/profile binding prevents accidentally associating a reply with another
request. It does not authenticate the peer or independently validate its
complete file hashes. Remote classifications rely on the connected peer's
observations. SIR/0 never authorizes a write or substitutes for the independent
source, basis and candidate checks used by exact-byte transfer.

## Lazy CLI inspection

With profiles enabled, the text UI's explicit **d** (diff) and **x** (details)
commands inspect the two current files. Scans and ordinary details formatting
do not hash all files or issue report RPCs. The first profile supporting both
files is used; all enabled profiles may be probed regardless of filename.
Suffix declarations are advisory hints, not eligibility rules. Recognizable
renamed files therefore use the same report path.

If neither file is supported and no selected profile has a matching suffix,
diff uses the existing external diff command. For a hinted candidate, such as
an unsupported `.dng`, the UI shows the unsupported/unavailable observation
instead of launching a binary diff. A supported side also keeps the result in
the report path when its peer is unsupported or unavailable.

Each explicit request refreshes its observation. Details retain only one
pending display, bound to the reconciliation item and roots; consumption,
another item or disconnect clears it. Local pathname stamps are checked again
before display. Remote reports remain explicitly observations of the files
the peer inspected, rather than a promise that they have stayed unchanged.
