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
nodes/pixel hashes and prior immutable snapshots remain. Private/opaque leaves
can also reset; nonprivate roots and any subtree containing pixel/standard-metadata claims refuse. A new decoder
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
automatic owner-worker/cache selection. Complete
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

Before a format adapter reuses a restored view, `validate_base` compares it with
the current parser's freshly described canonical partition. Exact IDs, roles and
extents are required. Unrefined schemas and child structure must match; a private
or opaque base leaf may contain cached private refinements, but no pixel or
standard-metadata claims. This check reads no payload and does not authenticate
metadata itself. Decoder provenance and replacement remain adapter responsibilities.

`DngComponents.with_checkpoint` now combines fresh DNG description, authenticated
core restore and this base-partition check before exposing a live restored view.
It preserves historical private refinements for explicit owner invalidation; it
does not silently mark them approved by the current decoder registry. Description
reads are additional to the core's declared hash/refinement budget. No persistent
store, automatic worker cache selection or epoch-only reuse is implemented here.

`DngComponents.replace_private_view` performs an explicit immutable replacement:
match the expected old schema, invalidate the target locally, run the guarded
decoder and return a new view only on success. Unsupported results leave the
original view available; operational errors propagate. Descendants of the target
must be reselected afterward. Unrelated pixel/metadata nodes remain unchanged.
This supplies localized version replacement, not an automatic decoder registry
comparison or durable publication transaction.

The worker entry point `SemanticWorkers.restore_components` accepts bounded
encoded metadata plus the owner's separately trusted digest. It uses the normal
borrowed-descriptor, filesystem/CPU admission, cancellation, completion and
shutdown machinery and returns only immutable component summaries. Restoration
reports no new decoder outcomes: historical interpretations are not fresh decoder
approvals. Automatic cache selection and trusted persistent record storage remain
separate owner work.

Worker extraction can now explicitly request `capture_checkpoint=true` on
`SemanticWorkers.components`. The checkpoint is exported inside the successful
live callback and delivered as immutable metadata alongside its summary, giving
the owner a direct capture-to-trusted-digest path. Ordinary jobs default to no
checkpoint; restore does not silently recapture historical views. Capture adds
at most1MiB per pending completion, which the owner must include in its admission
budget. Cancellation/failure publishes no checkpoint. It still supplies no owner
index, archive-generation binding or automatic disk publication.

## Persistent owner-store contract (next implementation)

### Known-entry recovery lookup

`inspect_cache_capture` now authenticates the two expected immutable leaves for
an already trusted owner entry. Caller supplies optional borrowed readers/FDs;
those options must match actual no-follow presence. Native checks bind each
private regular descriptor to its64hex leaf, with bounded size and stable native
metadata before/after content validation. Record bytes/checkpoint/input/inventory
references and exact entry bytes must match. Foreign leaves, symlinks (including
equal-byte redirects), wrong readers and namespace changes raise errors rather
than being downgraded to an absent cache record.

Results distinguish complete, record-only orphan, entry-only broken reference
and missing expected leaves. They describe only those two names, not a directory
census, producer terminal or resource closure. No files are opened/closed, moved,
removed or repaired. Even a complete result still requires normal full-current-
input/base verification before cached component reuse. A digest computed from
discovered unknown cache bytes is not a trusted owner entry. Managed namespace
opening, automatic selection and recovery scanning remain separate work.

The lookup now has a deterministic mid-read namespace-race control using the
existing reader cancellation callback, with no production injection hook. After
record authentication but during index checking, it redirects the record name
to an equal-byte fixture backup. The function must refuse before delivering a
result, even if outer reader retirement would independently detect the change.
An isolated filtered copy with only the final record check removed fails that
exact delivery-boundary assertion on stock and Ox. Normal1043DNGchecks/compiler
pass; counts include metadata-vector truncations. Production source is unchanged
and its four existing full-build source pin sets were rebound, not rerun. See
`tests/qualification/dng-cache-lookup-race-actual-20261017.json`.

### Quota-bound paired capture

The explicit capture helper now routes record+owner-entry staging through one
successful quota reservation. Caller creates fresh private empty stages named
slot basename plus `-record.tmp` and `-entry.tmp`. Native admission checks both
distinct identities and no-follow names in the actual reserved directory before
either write. A failed/unsynced reservation cannot admit payload stages. Once
admitted, staging cannot replay, including after a partial write failure.

Preparation seals those same mutable producer identities, enforces individual and
aggregate payload bounds, and independently authenticates record and entry bytes.
Publication is one-use: record first, entry only after record publication returns
normally. `cache_capture_state` reports both native rename effects after errors.
An entry collision can leave a valid record-only orphan plus unpublished entry
stage; neither is automatically removed, retried or refunded. Caller retains all
borrowed descriptors/readers and settles them before any external index adoption.
The helper opens/closes no FDs and performs no source-photo reads/writes. This is
the managed capture write path, not automatic lookup, recovery scanning, eviction,
global index advancement or default cache activation.

### Monotonic payload reservations

The macOS quota API now admits one bounded capture using an atomic empty private
directory slot. Each slot charges2MiB conservatively for its bounded checkpoint,
owner entry and index reference. Limits are1..4096 entries and2MiB..8GiB; actual
slot capacity is the smaller entry/byte limit. All cooperating owners of the same
managed directory must agree on both settings, pinned in `.component-quota-v0`.
That configuration is a symlink used strictly as metadata: readlink/no-follow
identity checks, never followed as a path. Slots are `.component-reservation-NNNN`.
Native functions borrow the directory FD and open/close no descriptors.

Reserve before any cache payload creation, once per ticket. Existing slots count
as consumed even after interruption; production functions never reclaim slots or
configuration. Lost configuration with retained slots refuses initialization.
Atomic mkdir prevents two cooperating processes from granting the same final
slot. Creation state is recorded before post-creation checks/sync, so an error
cannot be treated as a refund; inspect reserved/name, retain that slot and never
replay the ticket. A new managed namespace must start without unaccounted payloads;
legacy/imported data needs separate accounting. Deleting slots/config or hostile
same-UID modification violates the trusted-owner store contract.

This is conservative cache-payload admission, not filesystem/RSS/physical-IO
enforcement: excludes filesystem overhead and data outside the managed cache.
Automatic lookup, namespace installation, writer routing through reservations,
recovery scanning and entry eviction remain unimplemented. Original controls
exercise limits/settings/config loss and a two-process race for the final slot;
they do not provision a shared CPU or physical-IO pool.

Current stock/Ox controls pass41 component+1005 checkpoint checks each (including
vector truncations), plus26 original syscall-fault checks and110 worker checks.
The quota fault case injects directory-sync EIO after mkdir: the slot remains
consumed, the ticket cannot replay, and another prepared owner sees no capacity.
Both final-slot contenders were actually waited0. Current Make/fullselftests and
Dune compilation pass on both compilers with1272 production-source hash checks.
See `tests/qualification/component-metadata-quota-actual-20261017.json`.

### UDI/0 owner entry

The immutable owner entry codec is implemented in DngComponents. Make an entry
from a trusted captured checkpoint and its complete outcome inventory, with exact
caller-selected root/path and raw32-byte generation digest. Refined target schemas
and private-only subtrees are checked against the checkpoint. Entry load requires
the previous trusted whole-entry digest; hashing unknown bytes at load does not
establish that provenance. `checkpoint_for_owner_entry` authenticates UCR/0 record
bytes and cross-checks checkpoint/input digests plus the saved decoder inventory.
The entry and checkpoint are immutable portable metadata, never live input proof.

At most128KiB. Framing: eight-byte `55 44 49 00 00 00 00 00`; length-prefixed root
and path (nonempty/NUL-free, at most4096 bytes each); generation and input digests
(raw32 each); outcome count (at most64); ordered outcomes; checkpoint and record
digests (raw32 each). Each outcome is length-prefixed target ID (at most256),
decoder ID (at most128), raw32 implementation digest, status byte0 unmatched/
1 unsupported/2 refined, with a length-prefixed reason (at most1024) only for1.
Lengths/counts are nonnegative eight-byte big-endian integers. Inventory identities
are unique and checked; trailing, truncated and noncanonical bytes refuse.
The UCR/0 binding is SHA256 of `unison-dng-owner-binding/0` plus NUL and this UDI/0
prefix through the inventory. The separately trusted entry digest covers the
complete entry including record references. No executable decoder is serialized.
`ComponentHash.checkpoint_root` supplies bounded historical metadata for these
consistency checks; it does not verify current input or create a live session.

This implements an index entry, not the managed index namespace, lookup selection,
quota or archive-generation choice. Those remain owner responsibilities; an entry
does not grant publication, receiving or reconciliation authority.

`write_owner_entry`, `read_owner_entry` and `prepare_owner_entry_publication` now
connect UDI/0 entries to borrowed-descriptor storage and macOS immutable publication.
The preparation checks the whole stage against the captured entry digest before
native binding/exclusive rename. Digest-named entry leaves cannot overwrite prior
versions; the owner still must settle all descriptors before advancing any managed
index reference. `ComponentHash.stage_metadata_bytes` factors the bounded fresh
private-output writer, and `prepare_metadata_publication` factors bounded complete
SHA readback before the same owner-only native ticket. Neither opens/closes FDs.
This enables actual immutable entry publication, not automatic lookup, a mutable
latest pointer, managed namespace creation or quota accounting.

`SemanticWorkers.refresh_components` now runs restore and decoder-inventory
refresh together under the existing coordinated worker lifecycle. Its immutable
summary includes reused and invalidated component IDs and optional new checkpoint
capture. Unchanged decoders need no execution; changed decoders run on the worker
with the shared read budget. The owner must bind prior outcomes to its trusted
checkpoint and budget input metadata plus optional output per pending job.
Automatic disk selection/index publication remains unimplemented.

The pure record codec is now implemented as `checkpoint_record` and
`checkpoint_from_record`. UCR/0 is eight-byte magic `55 43 52 00 00 00 00 00`,
raw32-byte owner binding, raw32-byte checkpoint digest, eight-byte big-endian
payload length, then exact UCH/0 bytes. Total size is at most checkpoint limit
plus80 bytes. Loading requires the expected binding and separately trusted
whole-record digest; it verifies framing, checkpoint digest and bounded syntax.
This codec alone provides no disk publication, index or current-input authority.

`DngComponents.with_refreshed_checkpoint` now reconciles a complete trusted prior
outcome inventory with current frozen bindings. It verifies historical target
schemas, keeps unchanged views without decoder reads, resets obsolete bindings
and applies current decoders parent-first. An invalidated ancestor prevents reuse
of all descendant views. Removed base-level bindings return to the current parser
schema, so their exact opaque fallback can itself be checkpointed and restored.
Unsupported replacements stay unknown; operational errors return no new view.
The callback reports reused and invalidated IDs separately, with current outcome
inventory for subsequent refresh. The prior inventory is owner provenance, not
peer-discovered executable authority. Disk/index publication remains separate.

Original sibling-composition controls now execute both sequential upgrade orders
with a checkpoint restore between steps. Final canonical checkpoint bytes, layout
roots and pixel projections agree exactly for A→B and B→A; initial sibling decoder
order also gives identical checkpoints. Each stage retains the independent sibling
and charges only full8192-byte verification plus its own130-byte or5-byte decode/
parent-rehash work. This proves the original tiny case, not arbitrary plugin
purity, camera coverage, physical IO savings or a persistent-store transaction.

Borrowed-descriptor storage now exists: `write_checkpoint_record` writes only to
a fresh empty owner-private0600 singly linked regular output using bounded writes,
syncs, verifies final identity/size, and returns the intended record digest.
`read_checkpoint_record` reads at most the bounded record size and checks the
separately supplied digest/binding. The caller owns immutable/exclusive access,
all descriptors, independent readback and later publication. These functions open
no paths and close no descriptors. A failed partial stage remains caller-owned;
no automatic retry, unlink, rename, index or directory durability is supplied.

### Borrowed-descriptor immutable record publisher

The separate macOS publisher now provides exclusive namespace publication for
these records. It is owner-only/nonportable, with no opened, duplicated, closed
or retained descriptors. The caller keeps an owned private0700 directory and
private0600 singly linked stage FD alive and exclusively controlled through the
operation. Preparation independently reads and authenticates the record, binds
the no-follow temporary leaf to the stage's full native stat, and requires the
digest-named target to be absent. Publication rechecks directory/stage/name,
syncs the stage, uses same-directory `renameatx_np(RENAME_EXCL)`, verifies the
published identity and requests directory sync.

The native ticket records rename success before runtime reacquisition and before
post-rename verification/sync errors. Consult `record_published` after any error;
a published target must not be removed or replayed. The ticket owns no FD, so
caller closure and any uncertain-close evidence remain explicit owner duties.
This is cooperative namespace fencing, not hostile same-UID compare-and-swap,
mount-incarnation proof, hardware power-loss durability or owner-index publication.
Other platforms refuse without a pathname fallback. Original controls cover
success/readback, collision, symlink, mutation and replay refusal. A separately
compiled test-only fsync shim now proves post-rename directory EIO retains the
published effect/exact bytes/replay refusal, while pre-rename stage EIO and EINTR
preserve the stage and are not retried. No production fault switch is installed.
Stock/Ox each pass21 fault checks,41 component and988 checkpoint checks (including
every framing-vector truncation); the repeated41-check setup in the fault binary
is not additional independent coverage. Current Make+selftests and Dune compile
checks pass on both compilers with1272 production-source checks. These results do
not implement the persistent owner index or establish hardware durability.

Reuse the trust boundary of local Unison state, not peer reports or file-side
metadata. This explicitly trusts the local state owner; checksums are corruption
detection, not authentication against another process with that owner's access.
Do not make an arbitrary existing blob trusted by computing its digest at load.

The owner index must bind the root/path identity, successful extraction generation,
complete input SHA256, checkpoint SHA256, base parser contract, and the exact
ordered decoder target/ID/implementation declarations. The initial capture must
come from the live successful extraction, not from deserializing an unknown blob.
Treat the source epoch as a freshness hint; restoration still performs complete
input verification. A different decoder inventory triggers explicit per-target
invalidation/replacement, not an unqualified claim that historical views are
current. Parent replacement invalidates its descendants; independent siblings
retain their own provenance and hashes.

Keep immutable checkpoint blobs addressed by their digest and publish the owner
index only after bounded record validation, complete writes, sync, and successful
descriptor closure. Use an owned private directory and non-following opens with
opened-descriptor/name identity checks. Never overwrite a conflicting record or
follow a symlink. Charge bounded bytes and entries before creation; an interrupted
reservation may waste capacity rather than double-grant it. Do not evict an entry
whose owner operation has not settled. A crash before index publication leaves an
unreferenced blob, which supplies no reuse authority; after publication, malformed
or absent data causes a cache miss and normal extraction. Corruption must not
convert a cache miss into transfer or reconciliation authority.

Store operations belong to the coordinated owner/worker lifecycle. An uncertain
close preserves every preclose identity and propagates unresolved ownership; it
must not be swallowed as a best-effort cache miss, retried by numeric descriptor,
or followed by resource-release claims. Ordinary unsupported format, absent cache
or stale schema may decline without disabling otherwise qualified exact sync.
No store path may open or alter source photos for publication.

Required original controls: capture/load roundtrip, forged/self-hashed blob
rejection without an owner binding, root/path/generation mismatch, changed input,
decoder upgrade/removal, independent sibling composition, torn write/index crash
boundaries, quota exhaustion, symlink/name replacement, and injected combined
read/write/close failures with retained uncertainty. Qualify both build systems
and compilers before enabling automatic selection. These requirements describe
the planned store; no persistent namespace is provisioned by this document.
