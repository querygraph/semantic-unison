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

Permitted findings under `warn` use `Util.warn`, the user-interface warning
channel, including the existing remote forwarding command. Delivery first
yields on the owner so a hash worker's completion pump can rearm before a
printer enters a nested event loop. Abort and context cancellation are checked
before and after delivery. The candidate workspace and publication ownership
remain retained; helper execution, its I/O lease and that file's inspection
workers have already settled. Other independent candidates may still be active.
Printer/forwarding failures reject rather than silently authorizing publication.

The macOS batch printer also sends warnings to the existing nonblocking status
display when logging is disabled. A `Warning: ` prefix bypasses the normal
`reconitems` status filter. This is a transient status route: later updates can
overwrite it. Source/mock controls and full bridge/controller compiler checks
do not prove GUI paint, persistent visibility or native interactive behavior.

The [warning qualification](../tests/validation_warning/qualification.json)
adds eleven actual-companion controls and three complete client/server
receiving controls per compiler, with logging disabled, real hash workers and
synthetic supervised helpers. It preserves parent log-only and missing-yield
negative controls. No Adobe SDK or native UI was invoked for this slice.

The initial [integration receipt](../tests/qualification/validation-companion-integration-20261013.json)
uses synthetic candidates and Adobe-free drivers on stock OCaml and OxCaml.
The later [camera SDK receiving control](../tests/qualification/camera-sdk-receiving-v2-actual-20261016.json)
adds one retained camera candidate per compiler: two full receiving seeds and
exactly two qualified single-thread SDK calls. Both report valid structure,
successful decode, valid raw digest and zero errors/warnings. This is not a
representative camera corpus, semantic eligibility or pixel-equivalence proof.

### Size the admission envelope before enabling a validator

`adobevalidatorworkspace` declares estimated backend memory in MiB. It is added
to receiving publication accounting; it is not a replacement for the source and
publication buffers. `semanticpayloadbudget` must accommodate those envelopes
and any configured validation-tree memory as well. A gate equal to the validator
workspace can therefore still refuse the transfer. Neither setting is a hard
process RSS cap, and inflating the declaration does not measure SDK memory.

The camera control used these explicit endpoint settings:

```text
adobevalidatorworkspace = 2048
semanticpayloadbudget = 4096
validationtreememory = 0
semanticdescriptorbudget = 64
adobevalidatorthreads = 1
```

These are tested accounting values for that control, not universal sizing advice
or a complete validator configuration. The receiver still needs its own qualified
executable, SHA-256 pin, build ID and policy. With the fixed maximum payload bound,
the control's source plus publication envelope was 2416443392 bytes; its declared
4 GiB gate fit. Larger concurrency or different backends require fresh sizing.

The earlier 512 MiB gate with a 2048 MiB workspace failed before any SDK helper
could start. The [resource-admission fix](../tests/qualification/publication-admission-resource-fix-actual-20261016.json)
keeps an oversized receiving reservation a recoverable transfer error instead of
an uncaught server exception, without weakening the gate. Check the diagnostic
and correct the endpoint configuration; do not treat refusal as SDK decode failure.
