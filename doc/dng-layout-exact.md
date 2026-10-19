# Partial-knowledge DNG exact-layout profile

Profile `org.firstpair.dng-layout/0`, capability `dng-layout-exact-v0`, implements
the first transfer part of the user's gradual-understanding design in SEMANTIC-UNISON-DESIGN.md.
It does not require private MakerNote field meanings before an otherwise exact
metadata-region transfer can be attempted.

The profile uses the existing bounded classic/BigTIFF standard-container walk
in both byte orders. It locates a single bounded out-of-line BYTE XMP packet,
checks known standard directory/image extent rules, and bounds all declared
value extents. Unknown/private fields with supported TIFF storage types may
remain opaque. Scalar-shaped private pointers are not followed or presumed
independent of XMP. Unknown types, bounds/overflow/count failures, ambiguity,
multiple XMP packets and declared protected-region aliases still refuse the
fast path. Such refusal falls back to ordinary exact transfer.

All bytes outside the selected XMP span—including pixels, private values and
unclassified residual bytes—remain in the preservation and complete-file
hashes. Planning requires the same profile, size, span layout and complement.
The private materializer rechecks its basis and stage, patches the selected
span and verifies the complete output hash against the actual donor before
success. This produces the same bytes as copying that donor; it does not need
to explain hidden references to establish exactness. If private bytes change,
the complement differs and this region-only plan declines. It cannot silently
drop a changed opaque field.

The default synchronizer behavior remains off. `semanticdng = true` now offers
strict profiles1/0 first, followed by this exact-layout fallback, subject to
peer capability negotiation. Alternatively select it explicitly:

```text
semanticprofile = org.firstpair.dng-layout/0
```

No plugin code is received from peers. An older peer without the new capability
continues with the common strict profiles or ordinary transfer. New receiving
qualification is still needed for this source successor; an existing consumed
camera or SDK admission does not authorize a new runtime case.

## Knowledge and authority stay separate

`FormatExtension` handles now carry an immutable local `span_semantics` claim.
It defaults to `Opaque_spans`. The strict built-ins explicitly declare
`Known_metadata`; this layout profile remains opaque. Worker inspections consume
that frozen declaration without reading the owner registry. Peer-decoded proof
annotations are always opaque; no knowledge claim is added to SDR/0 or SDE/0.

`SemanticDelta.classify` distinguishes `Uninterpreted_regions` from interpreted
`Editable_metadata`. Exact-byte and other-byte classifications are unchanged.
The read-only inspector exposes `uninterpreted_regions`; owner report text adds
a layout-only/private-meaning warning for opaque handles. Its legacy
`Metadata_only` report enum remains a region-byte statement, not a claim of
complete field interpretation or rendering equivalence.

This profile cannot enter the existing strict-profile-only XMP merge or common
merge-base cache paths. It grants no permission to ignore differences, relocate
private data, synthesize merged contents or declare semantic/pixel equivalence.
The private full-target stage still goes through ordinary validation/publication
ownership. None of these changes bypass per-file optional Adobe policy.

## Actual evidence and remaining work

[Qualification](../tests/qualification/dng-layout-exact-source-actual-20261017.json)
records49 layout checks per stock/Ox compiler plus the old strict private-safety
regressions. Generated classic/BigTIFF fixtures in both byte orders contain
opaque pointers into changed XMP bytes. Exact donor reconstruction succeeds,
opaque changes decline, wrong target hashes fail, unchanged spans write zero
bytes, peer proofs remain uninterpreted and semantic merge is refused.
Four full stock/Ox Make/Dune builds and the stock legacy kernel/read-only
inspector checks also passed. All actual owners/groups/CPU8 closed; no SDK or
retained camera payload was involved.

This is an exact transfer profile, **not yet the separate pixel/metadata hash
forest, nested child-plugin framework or incremental cache**. Those remain the
next implementation layers. Remote/mixed-version receiving, broader failure
cases and a separately admitted retained-camera disposable-clone case also
remain qualification work. Unknown MakerNote meaning itself is not a global
deployment gate; each operation needs its own appropriate evidence.

## Production receiving successor

[The finite receiving plan](layout-receiving-plan-v1.json) and
[request](layout-receiving-request-v1.json) are prepared, not executed. They add
original generated opaque private pointers into changed XMP to the existing
18-row/54-CLI shared functional matrix, requiring the negotiated layout profile
on each semantic update. Generic exact/clone controls, old bases and no-op
epochs remain independently checked. This is not a photographic-validity test.

[Source controls](../tests/qualification/layout-receiving-source-controls-actual-20261017.json)
passed197 preference-boundary checks per stock/Ox compiler and the fixture/
admission/audit controls. They prove current preference serialization omits
unnegotiated layout capability and preserves local policy; they do not prove
old-peer transport. [Both current Make/selftests](../tests/qualification/layout-receiving-build-selftests-actual-20261017.json)
passed with workers3 per endpoint. Actual matrix execution requires a fresh
Root IO admission; no historical admission may be reused.

The supplemental pure [result auditor](../tests/layout_receiving_result_audit.py)
binds that request's mode/artifact/source/packet claims and independently
reparses captured SDE logs for every semantic row. It compares reported counters
with raw captured output and consumes the strict54-call lifecycle audit. Its
[fake-record controls](../tests/qualification/layout-receiving-result-audit-controls-actual-20261017.json)
passed four methods and13 negative mutations. Requested/resolved path strings
are observations, not physical alias proof; artifact SHA pins bind identity.
Caller authentication and actual owning-tool terminal evidence remain separate.
This helper is outside the unchanged pending worker closure; it grants no run
or resource release and is not actual receiving qualification.

Root issued V1 admission209266ba, but its start deadline passed before this
owner dispatched. The [actual preexec refusal](../tests/qualification/layout-receiving-v1-expired-actual-20261017.json)
records tool exit2 with no runtime/CLI/IOCPU entry. The original grant is
preserved and must not be executed. Fresh scheduling uses a distinct successor;
request/plan/code pins remain unchanged. No receiving pass is claimed.

## Actual production receiving result

The distinct Root reschedule dcc2d5cb executed once and
[PASSED/CLOSED](../tests/qualification/layout-receiving-rescheduled-actual-20261017.json):
18rows/54CLI, stock/Ox workers1/2/3 across ordinary/receiver-clone/semantic.
Six semantic rows/twelve actual exact-layout updates preserved opaque private
references while producing the exact donor, with unchanged old bases and no-op
epochs. All38 postpins, strict lifecycle/prefix proofs, worker/group/IOCPU closure
and actual parent11517/85a4a8/exit0/no-session passed. Root independently
[adopted and released](../tests/qualification/layout-receiving-root-adoption-actual-20261017.json).
The old V1 remains expired; the reschedule is consumed, not replayable.

An initial postrun metadata audit rejected the reschedule wrapper schema. That
refusal and the explicit verified scheduling-only projection are preserved;
original Root inputs, native output and execution were unchanged. No SDK/camera,
actual old-peer transport, semantic merge/pixel or physical savings follows.
