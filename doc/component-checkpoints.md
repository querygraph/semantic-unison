# Owner-bound component checkpoints

This isolated successor adds explicit `ComponentHash` checkpoint export/restore
and private-view invalidation. It does not install a cache, change worker/RPC
defaults, or supply an authenticated archive/store. The reviewed RPC branch is
unchanged while this work is qualified separately.

## Trust and work performed

Export requires a live session bound to the snapshot. It returns immutable
metadata bytes and their SHA256. The owner must retain that digest in trusted
state bound to the successful extraction. A digest computed from an arbitrary
peer/cache blob is not such provenance. A full-file hash alone cannot establish
the correctness of independently supplied subrange hashes.

Restore requires the prior trusted metadata digest and exact recognized root
schema. It first bounds/authenticates/parses the metadata and checks the canonical
partition. It then hashes the **complete current input** and compares it to the
prior root's raw SHA256 before entering a new live callback. Given trusted prior
metadata and equal complete bytes, the cached component raw hashes remain valid
under the usual SHA256 collision assumptions. The source still needs owner-held
immutable access; cooperative epoch checks do not exclude hostile writers/ABA.

The full-file pass is charged to the shared read budget. Cached per-component
hashes are reused and views are recomposed from metadata, so no separate pixel
hash pass is performed. This is not an IO-free restore or an epoch-only cache.
Avoiding the complete input pass remains work for a stronger core-owned immutable
blob/preservation witness. Supplying that witness or trusting persistent state
must never be inferred from an advisory RPC observation.

`reset_private_view` explicitly drops one refined private/opaque subtree back to
its exact raw atom under an owner-selected fallback schema. It changes no bytes,
raw hash, range or role. Only that view and ancestors are recomposed; unrelated
nodes/pixel hashes and prior immutable snapshots remain. Leaves, nonprivate roots
and any subtree containing pixel/standard-metadata claims refuse. A new decoder
can then refine that atom under the existing bounded reader, charging its reads
and the affected parent rehash. Unsupported decoding leaves the opaque fallback.

Implementation provenance and meaning are separate: a changed implementation with
identical leaf contracts/bytes changes the ancestor provenance/layout view while
the logical leaf projection can stay equal. A changed meaning/schema changes the
corresponding projection. Owners must compare/cache the declared contract and
provenance, not treat an untyped projection string as complete authority.

## UCH/0 metadata encoding

Maximum1MiB; at most1024 nodes and depth16. Integers are eight-byte big-endian
nonnegative signed-64-bit values; high-bit integers refuse. Strings are length
then bytes, nonempty/NUL-free and at most256 bytes.

Header: eight bytes `55 43 48 00 00 00 00 00`, then total node count.
Each node in preorder contains:

1. Logical ID string and schema string.
2. Role byte:0 encoded pixels,1 standard metadata,2 private metadata,3 structural,
   4 opaque.
3. Absolute offset, byte length, raw32-byte content SHA256.
4. Child count, then exactly those child nodes.

Views are recomputed using the existing versioned component framing, not accepted
from serialized hashes. The root must start at0 and cover the current whole file.
Canonical normalized shape must match exactly, including opaque gaps, order,
namespace, globally unique IDs, containment and nonoverlap. Unknown versions,
bad roles/counts/geometry, oversized/truncated/trailing bytes or wrong root schema
refuse before input payload work. Wrong input bytes refuse before the callback.

A checkpoint value contains only immutable serialized metadata/digest and has an
OxCaml portable/contended contract. It has no reader or live session capability.
Sessions, readers and snapshots retain their existing nonportable/lifetime limits;
restoration creates a fresh session token and expires it on every callback exit.

Integration still required: trusted persistent owner record/publication/recovery,
DNG frozen-decoder invalidation selection and owner-worker/cache wiring. Complete
private-field mapping is not a prerequisite for the already qualified baseline.

## Qualification

[Isolated core evidence](../tests/qualification/component-checkpoint-core-actual-20261017.json)
records stock/Ox41 existing component checks plus454 checkpoint checks per compiler
(including every truncation of the original metadata vector),23 contained calls,
positive portable checkpoint capture and three retained negative live-capability
captures. Full Make builds/selftests and Dune compile checks passed on both
compilers, with1272 production-source checks. All groups and Unison8 grants closed;
no EXglobal, SDK or media. One initial control conflated implementation provenance
with identical leaf semantics; its failure is preserved, with separate final
provenance/stable-contract/changed-schema controls.

Restore+one refinement independently delivered11266 input bytes (8192 full
verification +2 decoder reads +3072 parent rehash). The three-decoder upgrade
sequence charges17414 bytes; private invalidation itself charges no reads and
reuses the original pixel node within the restored session. These are logical
input/read-budget observations, not physical IO, speedup or rendering evidence.
