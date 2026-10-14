# DNG three-way target-plan construction

SemanticDelta.reconcile_xmp builds one exact SDE target plan from an explicitly
supplied common-base inspection and the two current inspections. It accepts
only the fixed-layout DNG XMP profiles0/1, equal file sizes/regions and equal
complete protected-byte identities. All proofs must retain their full single
packet bytes: SDR peer claims are insufficient. It invokes the bounded scalar
[packet policy](xmp-three-way-policy-v0.md), declines conflicts or changed packet
length, then reinspects the live left descriptor against its retained proof.

The target SHA-256 is computed by streaming that live file's exact prefix and
suffix around the merged packet. Stability checks surround the reads. The
existing planner encodes the left full/region hashes and merged exact bytes.
Both replica orders produce the same target bytes/digest because protected
content and layout match and the packet policy is symmetric. No output is
opened or written during planning. Verified apply retains basis/output checks,
private output admission, clipped4KiB comparison windows, positional writes,
full target verification and cancellation checks.

SemanticWorkers.reconcile_xmp executes this through the existing bounded job /
completion mailboxes, shared CPU owner and I/O reservation. It receives immutable
proofs and one owned duplicate of the live left descriptor. The owner interprets
an explicit plan Error as a conflict. CPU ownership persists through completion
delivery; queued cancellation settles and releases descriptors without a plan.
This introduces no separate worker pool or automatic merge preference.

The caller must independently establish an archive-qualified common base,
policy/parser/profile versions and generation binding, revalidate both current
replicas, and publish the same artifact through normal two-replica merge staging
and validation. This layer does not establish that authority, choose a base,
rename files or save archives. Layout changes/growth are declined; it does not
invent padding or structural-field edits. Ordinary conflicts remain active until
those owner/base-cache/commit integrations are qualified.

[Qualification](../tests/dng_reconcile/qualification.json) covers exact private
2MiB DNG-shaped artifacts, swapped-replica target digest, rejected payload /
live-basis / competing / peer-proof / nonce controls, and actual verified apply
on a private Darwin clonefile result. Both compilers compare every final byte
with independently generated Python target bytes and keep all inputs unchanged.
Native clone success is a substrate control, not physical extent accounting or
a new qualification of Unison's already-tested clone wrapper. Runtime worker
tests add48 parallel plans and queued cancellation under held CPU credits;
SDE conformance checks retain independent codec/byte semantics. No photographic
input, Lightroom, Adobe invocation or production file merge occurred.
