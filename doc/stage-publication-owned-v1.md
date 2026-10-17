# Explicit native publication ownership, v1

This is a backend primitive, not completed Copy/SemanticSync/SemanticRemote
integration. Legacy publication APIs retain their previous behavior. New explicit
`owned` handles cannot be passed to the legacy `t` APIs through the public
interface. No production caller has been switched yet.

`prepare_owned` validates paths and allocates a native rooted exception carrier
before opening descriptors. The root retains the custom context and its carrier
until explicit normal abort/disarm. If a native close is uncertain, delivering
`Ownership_uncertain (Some owner)` uses that already allocated carrier. No unknown
numeric descriptor is closed again, including during GC. This explicit API has
no implicit finalizer cleanup; a caller must settle or retain its owner.

The native context records every uncertain close in a fixed bounded vector:
descriptor number, native errno/phase, and optional observed preclose device/inode.
It also retains any still-known context descriptors. `owned_evidence` reports
these observations and the original native operation errno/phase. When an
operation and a close both fail, the operation error remains the cause and the
close failures remain separate. Missing identity is unknown, never fabricated.
This is not a full stat/FIVE witness or a portable errno interpretation.

After uncertainty, further owned operations raise the same retained carrier
before new IO or argument consumption. Evidence reads neither retry nor settle
resources. A caller must not close uncertain descriptor numbers itself. Native
`closed` phase means the context's scheduled close attempts were consumed; an
uncertainty vector explicitly prevents interpreting that as successful closure.
`disarmed` preserves the fact that temporary-name ownership was relinquished
before a proof-handle close error. No rollback or second publication is inferred.

The original disposable fault controls interpose close only in copied test C.
They test normal explicit abort/disarm, preparation error plus two failed closes,
adoption retirement uncertainty retaining four known handles, disarm and abort
with four uncertain closes, and binding failure plus probe-close uncertainty.
They check original cause, multiplicity/preclose identities, published bytes/name,
carrier identity across retry refusal, and retention across a major GC. The
wrapper physically closes then reports failure: application uncertainty remains
intentionally rooted until the disposable process exits. External child/group
closure is a distinct observation, not a claim of normal native settlement.

Remaining integration must migrate the outer transaction and all error cleanup
alongside each caller. It must retain the owned carrier plus basis/output owners
and the original higher-level cause; uncertain cleanup must not unlink/retry,
fall back, release CPU/IO/transaction credits, or masquerade as a known failed
prefix. Copy, SemanticSync and SemanticRemote have different publication and
callback ownership paths. Their legacy suppressing cleanup cannot simply receive
the new handle without coordinated changes and composed fault controls. Fresh
transport verification still requires its separate exact admission. No camera,
SDK, bulk IO, production deployment or automatic successor is authorized here.
