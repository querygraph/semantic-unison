# Experimental semantic synchronization

This branch adds general APFS clone updates, an exact DNG metadata transfer
profile, and optional Adobe SDK validation. It builds with standard OCaml 5
and the pinned OxCaml compiler. Use a separate build and disposable roots for
evaluation; it is not a deployed replacement for an existing Unison setup.

An example Unison profile enables the DNG extension:

```text
root = /absolute/first/root
root = /absolute/second/root
clone = auto
semanticprofile = org.firstpair.dng-xmp/0
semanticworkers = 0
```

`semanticdng = true` is an equivalent shorthand for this profile.
`semanticworkers = 0` selects physical cores on macOS, falling back to available
logical CPUs on other platforms or if topology is unavailable. A positive
integer sets a per-process budget shared by semantic workers and validators.
On the tested 18-core/36-thread Mac, automatic mode uses 18; set
`semanticworkers = 36` to try all logical CPUs. Cached hashing was about 10%
faster with 36 in the [recorded comparison](../bench/semantic/README.md), while
Adobe throughput has not yet been compared. Thread counts inside a validator
consume the same budget.
Profiles are trusted, compiled extensions, selected by exact versioned ID.
Neither extension code nor helper commands are accepted from a peer.

`clone = auto` enables private receiver-basis staging where supported,
including ordinary files with semantic extensions disabled. It skips writes
for inherited matching ranges at the same offsets and copies shifted ranges
from the immutable basis. Same-volume local copies prefer cloning the source
directly. `off` disables the added clone paths; existing upstream range-copy
acceleration may still share blocks. `require` fails an eligible receiver
update when the required clone is unavailable; it is not a universal guarantee
that no ordinary copy occurs. Other platforms retain existing transfer paths.

The DNG profile accepts a conservative classic TIFF subset with one bounded
embedded XMP packet. It requires the packet to keep its offset and length and
every other byte to match. It hashes all preserved bytes and verifies the
complete staged target before using the normal property, fingerprint, rename
and archive lifecycle. Raw-image digests cannot replace those checks. XMP
changes may affect rendering even when raw samples stay identical.

Changed packet layout, opaque/private structures, unsupported DNG variants,
and older peers use ordinary exact-byte transfer. The extension does not
currently merge conflicting metadata or treat differently encoded files as
equal. JPEG is a proposed second profile and is not yet supported.

To enable validation, build and qualify the [Adobe SDK driver](../tools/adobe-validator/README.md),
then configure `adobevalidate = require` and its executable, SHA-256 pin and
build ID as documented there. Set the policy in the client's sync profile; put
driver settings in `endpoint.prf` on every receiving host. A server reads this
reserved file from its own Unison configuration directory, and never takes its
driver path, pin, build ID, thread count or timeout from the remote peer.
The requested policy is shared; missing local driver configuration rejects
under `require`. Validation is independent of semantic transfer
and runs on received `.dng` files, including ordinary copies and files inside
a received directory. `off` is the default; `warn` permits validation findings
with a warning. Candidate mutation and cancellation reject even in warn mode.
Unchanged files and rename-only moves are outside this received-file scope.
The qualified driver currently uses one CPU thread per file; multiple files
run concurrently under the shared budget. This invokes the SDK directly and
does not claim equivalence with Lightroom's validation UI.

Inspect a file or pair without synchronization using the
[read-only inspector](../tools/semantic-inspect/README.md). It reports proof
identities, editable extents, classification, planned payload size and fallback
reasons.

With a semantic profile enabled, the text UI's explicit `d` (diff) and `x`
(details) commands inspect both current files lazily. The report shows the
profile, exact-byte/metadata-only/other-byte classification, preserved-byte
and metadata hashes, byte lengths and escaped packet previews. A preview is
bounded to 4 KiB per region and 8 KiB total, and may be truncated. This compares
the observed current replicas without an archived base; it does not change
conflict choices or infer rendering equivalence. Scanning and ordinary details
formatting do not inspect every file. Each explicit request refreshes the
observation, and details retain only the immediately pending display.

Enabled profiles are probed by content regardless of suffix, so a renamed
eligible DNG can still be inspected. Unsupported `.dng` files and older peers
show an honest unsupported/unavailable report; ordinary unsupported text uses
the configured external diff. Remote reports use the negotiated, bounded
[SIR/0 protocol](semantic-report-v0.md), without fetching the whole file.

`-debug semantic` explains successful semantic transfers and fallback during
synchronization. Successful application reports the complete metadata payload
size separately from actual logical write bytes and write-call attempts.
Materialization compares absolute 4 KiB windows, clipped to editable regions,
and writes differing windows; unchanged packet bytes can therefore avoid a
write even though the payload includes them. Full candidate verification still
follows. These counters do not measure physical APFS writes, durability or
elapsed-time savings.

Production admission also limits concurrent transactions, estimated retained
payload buffers and descriptors. See [worker limits](semantic-workers.md) for
`semanticmaxinflight`, `semanticpayloadbudget` and `semanticdescriptorbudget`.
`-debug semantic` reports detected CPU counts and the effective runtime limits.

Build and test references:

- [Isolated OxCaml/standard OCaml builds](oxcaml.md)
- [APFS and peer compatibility tests](../tests/CLONE.md)
- [Extension authoring contract](format-extensions.md)
- [DNG parser profile](dng-profile-v0.md)
- [Experimental SDE/0 wire format](semantic-delta-v0.md)
- [Experimental SIR/0 inspection format](semantic-report-v0.md)
- [Worker ownership and limits](semantic-workers.md)
- [Live design and remaining work](../SOL.md)

Reduced logical writes and transfer payloads do not establish physical APFS
write savings or elapsed-time speedups. Verification and optional raw decoding
still read file contents. Performance, broader platform coverage, semantic
reconciliation and production corpus qualification remain separate work.

Explicit diff/details now includes extension-defined property observations when
both peers support `semantic-inspect-v1`. DNG reports separate potentially
rendering-related Camera Raw property encodings from known descriptive, identity
and workflow metadata; unknown fields stay unclassified. Parsing uses the full
retained XMP packet in the worker, rather than treating a truncated preview as
a complete packet. Unsupported XML produces an interpretation reason while
ordinary exact transfer continues. Old peers retain the SIR/0 byte report.
Property encodings and namespace contexts are compared without RDF/value
canonicalization, rendered-pixel equality or automatic conflict resolution.
See [SIR/1](semantic-observation-v1.md) for bounds and versioning.
