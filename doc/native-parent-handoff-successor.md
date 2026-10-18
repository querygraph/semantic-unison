# Tracked API component checkpoint (2026-10-18)

The versioned C entry `unison_stage_publication_adopt_tracked_v1` and abstract
StagePublication.parent_handoff are now implemented. Prepare before acquiring
parent; attempted entry is single-use. C stores consumed=true after the strict
pre-entry uncertainty rejection and before taking ownership into its local
native path. Immediate false→true field update allocates/polls nothing. Every
later native error leaves true; generic unavailable entry leaves false. The
old three-argument ABI retains its behavior through the shared native body.

Stock/Ox Make+selftests pass,14component controls pass,2incorrect-early-mark
participants fail designated assertions, and2private generic-branch build/link
controls refuse unsupported preparation. Original owned/legacy controls pass.
Evidence: `tests/qualification/tracked-parent-api-actual-20261018.json`.

## Caller integration (2026-10-18)

SemanticRemote now prepares a parent ledger and abstract handoff before acquiring
clone-stage descriptors, adopts the returned parent immediately, and invokes the
tracked native entry. Cleanup reads the acknowledgement itself: no fallible ML
post-call flag determines whether the parent remains locally closeable. A consumed
parent is transferred, not declared OS-closed. An unconsumed close error preserves
its cause and pre-close identity and prevents native abort/name removal. Interruption
observed after acquisition roots all returned handles instead of continuing adoption.

Both current Make builds/selftests pass. Sixteen caller controls pass stock/Ox:
known transfer, pre-call and post-call failure, pre-entry uncertainty, parent close
failure before and after kernel settlement, combined pair/parent errors, and
post-acquisition interruption. Two deliberately wrong always-transferred consumers
fail the designated pre-entry assertion. These use generated8192B DNGs and an
in-process planner, not network transport or SDK. Unknown cases preserve stage
bytes/admission and do not retry numeric FDs during connection cleanup; their
remaining resources end at process exit, not claimed normal native teardown.

Current stock/Ox Make and Dune builds/selftests match all327 production hashes.
All24 staging-pair and8 native-publication regressions pass on that exact source.
Evidence: tests/qualification/remote-parent-caller-actual-20261018.json.
Opaque directory ownership, aggregate FD/RSS and wider benchmark/final integration
remain open. The original design below is historical
ancestry describing the old caller, not the current source.

# Native parent handoff: next source successor

This is a design for unimplemented work, not a claim that the existing parent
handoff is qualified. SemanticRemote currently clears loose_parent_held before
calling StagePublication.adopt_owned. In the C entry, an already-uncertain strict
context raises before consuming incoming_parent. Native rejection therefore
cannot universally be treated as proof of parent transfer. Do not change the
legacy API's consumption semantics under existing receipts.

Prepare a single-use abstract handoff object before clone-stage acquisition.
A versioned tracked-adopt entry should receive its preallocated acknowledgement
cell. ML records attempted entry before dispatch. C leaves consumed=false on
pre-consumption rejection and stores consumed=true exactly where it assumes
ownership, before a blocking section/close/native error can escape. The store
must neither allocate nor dispatch pending actions. The existing untracked entry
must retain its old ABI and behavior.

The caller's parent-descriptor ledger must retain the actual returned FD before
any allocation. It may stop considering that FD locally closeable only from the
qualified native acknowledgement, never from a guess about an exception or a
cleared boolean. Cleanup itself must consult that evidence, including when a
continuation/allocation failed before the ordinary post-call bookkeeping.
Transferred ownership is not known OS closure; native ownership evidence remains
responsible for the consumed parent. A false acknowledgement leaves the caller's
unconsumed close authority intact, including if native context ownership is
already uncertain. Do not retry native adoption or the old numeric FD to discover
what happened.

The handoff object should be abstract, single-attempt and immutable to its caller
except through the qualified C store; no reset, forge-consumed, or blanket release
API. Owner-loop access only. The ledger can use a prepared nonallocating predicate
over this object to distinguish transferred/local authority. This is a scoped
cooperative ownership proof, not a security sandbox against arbitrary ML/C code.

Fixed controls must include normal transfer, ordinary native failure after
consumption, pre-existing native uncertainty before consumption, close errors
before/after kernel settlement, number reuse, post-return observer setup failure,
connection cleanup and repeated cleanup. Check both caller and native evidence,
original causes, transaction credit/name preservation and no double-close.
Actual process exit settlement is different from ordinary native teardown.

Nonce descriptor ownership is now separately implemented and qualified; this
proposal must not relabel that work as parent handoff completion. Opaque directory
ownership, current Dune/regression, aggregate FD/RSS containment and the broader
SOL benchmark/final integration obligations remain open.
