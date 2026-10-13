# Receiving candidate validators

`CandidateValidation` runs selected, locally compiled validation companions on
finalized private received files before the normal rename/archive lifecycle.
Companions are independent of semantic transfer profiles: ordinary copying,
cloning, resumption, reuse, external copying and generated merge results use
the same receiving hook. Unchanged, property-only and rename-only operations
do not invoke it; optional all-scanned validation remains unimplemented.

Register a companion on the owner during startup:

```ocaml
CandidateValidators.register (module ExampleValidator)
```

The module implements `CandidateValidator.S`. Its immutable `recognition`
handle implements `FormatRecognition.S`; its owner-side `select` captures
endpoint policy and settings and returns either a validation callback or
`None` when disabled. The registry permits at most sixteen unique recognition
IDs and freezes on first selection. Only recognition handles and filename
claim booleans enter workers. Preferences, registries, Lwt callbacks and helper
execution stay on the owner. Modules are trusted code, not sandboxed plugins.

Recognition uses bounded reads from `SemanticFile`. A destination suffix claim
forces validation even for malformed contents. Without a claim, `Recognized`
and `Indeterminate` both select the companion; only `Not_matched` skips it.
Operational errors, cancellation and file instability propagate and reject
publication; they must never become a negative format match or a permissive
warning. Indeterminate diagnostics are bounded to 1,024 bytes. Recognition
cannot establish semantic patch eligibility or successful format validation.

The worker checks file stability around recognition. Selected files receive a
complete SHA-256 on the same held input; unmatched files avoid that full read.
The owner closes the identity descriptor before invoking helpers. Recognition,
hashing and sequential selected callbacks retain one 1 MiB / nine-descriptor
workspace, borrowing an existing publication reservation where available.
`context.inspect` schedules stable full hashing; `context.execute` acquires the
filesystem gate only for supervised helper execution. Companions must settle
all borrowed work and children before returning and must not nest resource or
filesystem leases. CPU permits are acquired separately for each operation.
These allowances do not bound parser allocations, tree manifests or SDK RSS.

Directory candidates enumerate every regular descendant, with no symlink
following. The retained manifest includes names, metadata, links, properties
and resource-fork stamps and is rechecked after all consumers settle. A bound
tree processes one file at a time; unbound consumers share the global runtime
budget. Suffix claims use the destination leaf name, including descendants.
There is no path-rule selection API in this version.

## DNG companion

One DNG validation companion serves both DNG XMP transfer profiles, avoiding
duplicate validation. It recognizes tag 50706 (`DNGVersion`) in TIFF IFD0,
supporting classic TIFF and BigTIFF in either byte order. It does not require
XMP, supported camera profiles, a supported DNG version or semantic transfer
enablement. Tag type/count/version validity belongs to the validator.

Recognition checks header/table extents and signed representation bounds,
caps IFD0 at 65,535 entries and reads at most 1,024 entries per chunk (20 KiB
for BigTIFF). It does not traverse private/image graphs or read payload data.
Checked incomplete, unsupported or oversized TIFF directories are
indeterminate and require validation. Unrelated readable TIFFs without the
tag, JPEG and text are negative matches. A `.dng` filename always makes a
claim; a recognizable DNG named `.bin` is selected by content.

`adobevalidate = off|warn|require` uses the separately negotiated
`dng-validation-v1` capability. Version zero promised suffix selection only
and is not advertised as an alias. Both `warn` and `require` refuse a peer
without v1 before transfer; `off` retains ordinary old-peer compatibility.
Selection repeats the capability guard on the receiver, including preference
installation/reuse. Tool path, hash, build ID, thread weight and timeout remain
endpoint-local. The selected callback captures them before recognition.

The companion adapts the generic snapshot to `DngValidation`'s standalone
snapshot type and invokes its structured SDK-driver protocol through the shared
supervisor. Candidate inspection, invalid expected snapshots and identity or
content changes always reject, including under `warn`. Tool availability and
validation findings retain the explicit policy distinction. Require success
still needs a qualified tool receipt and stable before/after full hashes;
the companion does not claim Lightroom UI Validate parity.

Current qualification uses synthetic candidates and Adobe-free drivers on
stock OCaml and OxCaml. See the [integration receipt](../tests/qualification/validation-companion-integration-20261013.json)
and its separate independent review. Real-camera/SDK receiving-path coverage,
resource limits and throughput remain separate acceptance work.
