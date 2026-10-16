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
semanticdng = true
semanticworkers = 0
```

`semanticdng = true` enables both built-in DNG XMP profiles, preferring the
extended `/1` profile when negotiated. To select one version only, use
`semanticprofile = org.firstpair.dng-xmp/1` or `/0` explicitly.
`semanticworkers = 0` selects physical cores on macOS, falling back to available
logical CPUs on other platforms or if topology is unavailable. A positive
integer sets a per-process budget shared by semantic workers and validators.
On the tested 18-core/36-thread Mac, automatic mode uses 18; set
`semanticworkers = 36` to try all logical CPUs. Cached hashing was about 10%
faster with 36 in the [recorded comparison](../bench/semantic/README.md), while
the [cached synthetic Adobe comparison](../bench/adobe/README.md) also measured
1/18/36-worker validation throughput. Neither comparison establishes a general
photographic-corpus or full-sync speedup. Production validation uses one thread
per file; concurrent files consume the shared budget.
The budget is local to each Unison process, not machine-wide across peers or
other applications. Two loopback endpoints using automatic mode can each select
18 on this host. For a coordinated two-endpoint evaluation, explicitly setting
`semanticworkers = 8` on both endpoints budgets16 worker/helper credits in total
and leaves room for the owners and bridge. This is scheduling guidance, not an
OS-enforced CPU limit or a measured optimal worker count. A genuinely remote
endpoint has its own machine budget.
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

The DNG profiles accept conservative TIFF subsets with one bounded embedded
XMP packet. [Profile v0](dng-profile-v0.md) covers classic TIFF;
[profile v1](dng-profile-v1.md) also covers bounded BigTIFF and embedded camera
profile structures in either byte order. It requires the packet to keep its offset and length and
every other byte to match. It hashes all preserved bytes and verifies the
complete staged target before using the normal property, fingerprint, rename
and archive lifecycle. Raw-image digests cannot replace those checks. XMP
changes may affect rendering even when raw samples stay identical.

Changed packet layout, opaque/private structures, unsupported DNG variants,
and older peers use ordinary exact-byte transfer. Default synchronization preserves conflicts and requires exact bytes. Optional
[scalar reconciliation](dng-built-in-merge.md) can merge narrowly defined DNG
XMP fields using a verified common base; unsupported/growing/rendering changes
remain conflicts. [Compact common bases](dng-compact-merge-base.md) are separately
opt-in and do not replace backups.

The implemented [JPEG XMP profile](jpeg-semantic-profile.md) is enabled separately
with `semanticprofile = org.firstpair.jpeg-xmp/0`. It uses the same exact transfer
and clone pipeline, protects EXIF/ICC/entropy and other nonpacket bytes, and
follows ordinary fallback for unsupported layouts. DNG shorthand does not enable
JPEG; DNG validation does not validate JPEG.

To enable validation, build and qualify the [Adobe SDK driver](../tools/adobe-validator/README.md),
then configure `adobevalidate = require` and its executable, SHA-256 pin and
build ID as documented there. Set the policy in the client's sync profile; put
driver settings in `endpoint.prf` on every receiving host. A server reads this
reserved file from its own Unison configuration directory, and never takes its
driver path, pin, build ID, thread count or timeout from the remote peer.
The requested policy is shared; missing local driver configuration rejects
under `require`. Validation is independent of semantic transfer
and runs on content-recognized DNGs and `.dng` filename claims, including
renamed files, ordinary copies and descendants of received directories.
`dng-validation-v1` is required for either warn or require; suffix-only older
peers are refused before transfer. See [candidate validators](candidate-validators.md).
`off` is the default; `warn` permits validation findings with a warning.
Candidate inspection failures, mutation and cancellation reject even in warn mode.
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

`-debug validation-process` records settled receiving-helper results on each
endpoint: historical child PID, wait status/outcome, candidate hash/size and up
to 4 KiB per stdout/stderr stream in hex, with explicit clipping flags. This is
opt-in and applies to trusted validation companions generally. A child can exit
zero while reporting findings that reject the file; these diagnostics do not
prove validator acceptance, publication or surviving process/group ownership.
See [controls and scope](../tests/validation_process/README.md).

`-debug validation-group` separately enables an endpoint-local observation of
the receiving helper's process group while the owner still retains the leader
PID. It reports `other-members=0`, a positive count, `unknown`, or `unobserved`;
the latter two must not be read as zero. The binding is retired before reaping
the leader, and diagnostic output is emitted after helper settlement. This
does not change validation policy, establish decoded-pixel equality, or prove
that a descendant did not escape into another process group. Leave this and
other debug counters off for timing comparisons. The current
[stock/Ox receiving controls](../tests/validation_process/group-integration-qualification.json)
and [six-call SDK live-merge return](../tests/qualification/sdk-live-merge-v1-actual-return-20261015.json)
record their exact functional scopes; neither establishes a throughput gain.

Production admission also limits concurrent transactions, estimated retained
payload buffers and descriptors. See [worker limits](semantic-workers.md) for
`semanticmaxinflight`, `semanticpayloadbudget` and `semanticdescriptorbudget`.
`semanticvolumejobs` independently bounds concurrent domain/validator execution
per endpoint filesystem device. Zero uses that endpoint's CPU budget; a
positive value overrides it. Configure this endpoint-local setting in each
host's `endpoint.prf`. It does not identify physical disks or cap ordinary
copies, child memory or total process descriptors.
`-debug semantic` reports detected CPU counts and the effective runtime limits.

Build and test references:

The existing finite fake-child and fake-worker lifecycle controls can be run
manually from the repository root, separately and serially:

```sh
make -f tests/Makefile interrupted-receipts
make -f tests/Makefile aggregate-lifecycle
```

Each runner creates and prints its own private workspace and receipts. These
targets invoke no compiler, SDK, Lightroom, source photograph or timing matrix.
`make -f tests/Makefile aggregate-preflight` checks interpreter capabilities
and ten missing-capability refusals without creating any test child. The
aggregate refuses unsupported Python ownership APIs before allocating readiness
pipes, writing markers or forking. Presence of these APIs is a prerequisite,
not qualification of their behavior on an untested operating system.
The aggregate's failure fixtures intentionally retain unresolved-proof markers
while checking that their actual workers were reaped; those expected markers
are not passing native-helper proofs. `DRY_RUN=1` prints the selected command
without starting a child or creating its report directory. Use the qualified
Python3.14 interpreter for reproduction (for example by placing its executable
directory first on `PATH`). These entry points do not provide a machine-wide
resource allocation; coordinate manual runs with other work.

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
still read file contents. Representative performance, broader platform coverage, broader reconciliation
policies and production corpus qualification remain separate work.

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

`-debug external-process` separately records generic copy/merge/diff helper
lifecycle diagnostics after supervised execution settles: historical child PID,
wait status/outcome, declared CPU weight, capture truncation and retained-group
observation. It logs no command arguments or captured output. Default execution
adds no group query. `unobserved` and `unknown` do not mean zero; a numeric
other-member count is one census before leader reap, not durable process-tree
closure. These records are diagnostics, not publication/validator acceptance or
permission to signal a historical PID. Existing command exit/cancellation policy
is unchanged.
