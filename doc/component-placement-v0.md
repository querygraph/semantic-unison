# Component placement v0: architecture contract

Status: **design contract; runtime not implemented or qualified**, 2026-10-13.
This extends Unison's architecture for the user's requested split Lightroom
preview storage. The [Lightroom binding](lightroom-preview-placement.md) applies
it to monitor levels on Quasar and lower levels/native databases on Ten.
Another Codex session owns rendering, native-format investigation and the
preview publisher. This document does not authorize or implement catalog or
cache mutation.

## Three independent contracts

1. **Semantic components and identity:** what an asset contains, which exact
   bytes represent each component, and which dependencies made those bytes
   valid. An image, sidecar, preview level and native registration can be parts
   of one logical asset group without being one physical file.
2. **Placement:** which locally configured storage root receives each role and
   how an application's canonical namespace refers to those bytes. Changing
   placement does not establish new image identity or authorize re-rendering.
3. **Filesystem capabilities:** how bytes reach a private candidate: ordinary
   copy, native whole-file clone, composed clone or constrained range sharing.
   Placement works on non-cloning filesystems. Neither a root named “fast” nor
   component equality proves shared blocks or physical write savings.

Existing SDE/0 continues to describe exact same-file range replacement. This
contract does not alter its wire encoding, DNG proof or archive behavior.
Embedded DNG XMP and legacy packed preview levels can be semantic components
without being separately placeable files. A profile must prove an external
representation and native reference mechanism before offering placement.

## Profile, asset group and component manifest

A locally trusted profile proposes data; core validates identities, resolves
roots, schedules work, owns staging and enforces publication. The profile may
interpret application metadata through a locally installed adapter, but a
peer cannot supply code, executable paths or SQL statements.

The following are required concepts, not an already implemented OCaml API or
final wire codec:

| Field | Contract |
| --- | --- |
| Profile | Exact versioned identifier, manifest schema, identity rules, bounded component count/metadata size and supported representations. Unknown mandatory fields or versions reject. |
| Logical asset key | Namespaced application identity with explicit aliases. Neither a basename nor a storage pathname is an identity. The profile defines whether a changed render/develop revision creates a new group revision or distinct variant. |
| Group snapshot | Opaque revision identifier plus the SHA-256 of the exact manifest bytes and dependency snapshot identity. A manifest-byte hash is not a claim of canonical semantic equality. Retain the exact attested bytes. |
| Component key and role | Unique within the group, such as `original`, `develop-metadata`, `preview-monitor`, `preview-lower`, `root-pixels` or `registration`. Roles are interpreted only by the negotiated profile/policy. |
| Representation | Standalone immutable blob, embedded extent, or adapter-managed record. Embedded extents are not independently relocatable by default. Database rows are typed records, never executable changes supplied by the peer. |
| Byte identity | Length and whole-content SHA-256 for every transferred blob; ordinary fork/property identities remain explicit when applicable. Encoding, dimensions, orientation and color/profile identity belong to the component description. |
| Semantic provenance | Renderer/profile/codec/policy revision and captured input/dependency identities when the component is derived. A filename or current-develop digest alone cannot attest rendered pixels. |
| Dependencies | Bounded, acyclic input/content references to required components and snapshots. Separately declare publication and native-loading prerequisites, including auxiliary records and components required to load other renditions. Missing or changed prerequisites hold the relevant group operation. |
| Native availability | Profile-defined readiness predicates over component keys, registration and validated endpoint-local root bindings. Verified bytes alone do not establish native loading. Fallback needs a versioned, qualified adapter recipe. Actual mount availability is local operational state, not peer authority. |
| Payload reference | A portable component/blob identifier, representation and content hash. It contains no absolute host path, volume name, executable command, URL to fetch automatically or arbitrary symlink target. |
| Requested placement | Versioned policy identifier and role requirements, using logical root IDs only. Endpoint binding and actual volume identity are local configuration. |
| Publication recipe | Identifier/version of a qualified local adapter and declarative metadata. The adapter defines visible commit point, exclusion requirements, durable operations and recovery; unsupported recipes hold. |

A receiver independently checks profile limits, duplicate keys, dependencies,
extent arithmetic, transferred hashes and policy. Metadata derived from a
catalog or external dependency is accepted only with the profile's stable
snapshot/provenance checks. A manifest supplied by a trusted peer remains
untrusted input for bounds and path resolution.

Group equality requires the defined logical identities and exact component
bytes. “Same raw pixels” is insufficient for matching develop instructions,
ICC data, unknown metadata, previews or registration. If a future profile
permits alternative byte encodings, it needs a separately specified convergence
policy and archive invariants; placement v0 does not introduce that permission.

## Native loading and availability dependencies

Independently placed bytes can remain coupled by the application's loader.
Represent input/content provenance separately from publication prerequisites
and native-readiness predicates. A component may have verified bytes on its
local volume while the group is unavailable to the native application because
another required component or root is absent. Transient unavailability does
not change that component's byte identity, imply deletion or authorize a new
render revision. A completed file transfer is not a native-readiness receipt.

The [Classic 15.6 registration findings](../../photo/preview-registration-findings-20261013/FINDINGS.json)
report that the installed `PreviewFile.loadPyramidfromBlobFiles` checks the
existence and modification time of the highest registered level even for a
smaller requested level. This is **installed-loader source evidence**; the
inference that a missing Quasar target can prevent loading lower Ten levels
still needs a missing-volume/broken-link/native-fallback runtime oracle.
For affected pyramids whose highest registered level is placed on Quasar,
treat that target and the validated `preview-fast` root as required native
availability prerequisites until such a fallback is qualified. This also
applies when a small crop's highest registered level is below 5120. Lower Ten
JPEGs do not establish independent lower-tier native availability. Retained
groups without a Quasar dependency do not acquire one merely from sharing the
same cache namespace.

The application profile declares the highest component key and its native
registration/path/mtime requirements without embedding a host path. Each
endpoint resolves the dependency through its own current placement bindings.
Publisher admission, final visibility checks and interrupted-run recovery must
validate both the native root and every required payload root, including the
highest target's qualified native state. Missing/wrong-identity storage or a
broken required reference holds native readiness and the controlled publication/
restart window; it must not trigger unqualified registration changes, lower-tier
substitution or backlog regeneration. A qualified fallback recipe must preserve
current identities, define native registration and recovery behavior, and record
its exact application/schema/policy acceptance before weakening this requirement.

Reclamation includes these loading prerequisites: a highest-level object may
remain required while only lower levels are being requested. Reconcile the
native registration and availability dependencies before reclaiming it. Keep
this requirement in the group publication/recovery contract; same-file SDE/0
encoding, preservation proofs and exact-byte convergence remain unchanged.

## Local roots and policy negotiation

Local configuration maps IDs such as `preview-native` and `preview-fast` to:

- A configured directory and expected mounted volume identity.
- A publisher-owned namespace, allowed operations and storage reserve.
- Permitted publication adapters/reference types and a durability policy.
- Resource limits for that volume and optional verified clone capabilities.

These bindings are endpoint-local and are never overridden by peer preferences.
Actual names and mount paths may differ between replicas. Validate mounted
identity and directory ancestry at admission and immediately before installing
references; a missing mount must not turn into writes to a same-named directory
on the system disk. Pin directory handles where supported. Reject absolute
peer paths, traversal, NUL, unexpected symlinks, namespace escape and collisions
with unowned objects. Local absolute links, when required by an application,
are constructed from the receiver's validated binding and safe component key.

A filesystem migration changes the local binding generation even when its
mount name is preserved. Bind capabilities and pending reservations to that
generation and the verified volume identity; invalidate them after replacement,
reformat or a relevant mount/capability change. Never inherit an old successful
clone probe merely because the new volume has the same name. The current local
binding is the replacement 8 TB APFS Quasar, UUID
`E31B795D-FA19-4938-97E2-B6ED56A7C78F`; the earlier 6 TB HFS+ identity is
historical. Ten remains HFS+, with conversion optional as assessed in the
[storage migration plan](preview-storage-migration.md). This changes physical
operations, not the component profile or the
requirement to support verified copying on non-cloning storage.

Negotiate an explicit `component-placement-v0` capability, exact profile and
placement-policy revision before any group transfer. Receiver-local placement
bindings may differ while implementing the same logical policy. A source
request cannot make a receiver execute an arbitrary adapter or choose an
unconfigured disk. Missing roots, unsupported policy, unavailable dependency
or unqualified reference behavior produce an actionable hold.

An old peer may continue ordinary synchronization when component placement is
disabled. It must not silently receive an enabled split group as a copied
source-host symlink tree: that can copy invalid absolute links, miss payloads
or violate placement. Requested group synchronization requires matching support
or an explicitly selected ordinary-file policy with its own complete root set.

Managed native paths and external payload namespaces cannot simultaneously be
owned by the group publisher and ordinary independent Unison file actions.
Planning must identify overlap and fail conflicting ownership. A scan of only
the canonical namespace is insufficient evidence that external payloads exist.

## Exact transport and archive implications

Core transports immutable standalone components through existing exact-byte
transfer machinery, using clone/range sharing only when local capabilities and
proofs allow it. SDE may optimize an independently eligible component; component
placement is not another binary-delta format. The receiver verifies every
component before exposing application references.

The native reference representation may intentionally differ across endpoints
(for example, an absolute symlink has a different locally resolved target).
Therefore a component-group profile cannot silently reuse ordinary symlink-byte
equality or mark an incomplete set `ContentsSame`. The planned group archive
record needs profile/policy versions, logical revision/dependency identities,
component byte identities, endpoint-local placement revision and the committed
publication receipt. Placement repair and content change remain distinguishable.

This is an authoritative new synchronization invariant. Its implementation must
declare an archive-changing feature, introduce explicit group/archive types and
qualify migration, rollback and downgrade rejection. If an initial prototype
uses a separate journal/state store, that does not make it a disposable cache
or remove the need for equivalent compatibility guards. No such archive or
multi-root group runtime is implemented today; current SDE/0 retains its
unchanged archive format and exact single-file convergence.

## Cross-volume publication and recovery

Unison currently commits guarded individual receiving candidates. It does not
provide an atomic transaction across filesystems, databases or multiple asset
paths. A group adapter must state how readers discover a complete generation.
For a generic manifest consumer this can be one same-volume commit pointer;
for an existing application it requires a qualified native publication recipe
and, where needed, an exclusive closed-application window.

Use bounded groups/batches and a durable write-ahead journal. Retain transaction
ID, profile/policy/adapter versions, exact manifest digest, volume identities,
owned artifact names, before-images, intended reference/record changes, actual
payload sizes/hashes, required native-availability dependencies, resolved root
bindings/generations, durability tier and completed transitions. Only core or
the qualified local publisher may advance them:

`PREPARED → PAYLOADS_DURABLE → REFERENCES_DURABLE → AUXILIARY_COMMITTED → PUBLICATION_COMMITTED → VERIFIED`

1. **Prepare:** establish writer/launch exclusion required by the adapter;
   recheck dependencies and current asset state; inspect existing identities;
   reserve space on every destination volume, including journals, rollback
   state, metadata and maximum staging overlap. Durably record intent and
   before-images before mutation. Existing same-key/different-content objects
   are collisions, not permission to overwrite.
2. **Make payloads durable:** create exclusively named private candidates on
   their final volumes, reconstruct/hash/parse them, and use the tested flush
   operations for the selected durability tier. A cross-volume rename is not
   an installation primitive. Ordinary copying remains valid on HFS+ or any
   filesystem without qualified cloning.
3. **Install references:** install fully verified new payloads and local
   references with same-volume namespace operations. A published reference
   must never precede its target's verified durability. Preserve previous
   generations or hold collisions according to the adapter's native key rules.
4. **Commit auxiliary state:** apply independently transactional auxiliary
   records in the qualified dependency order. Record each durable boundary.
   Two SQLite databases do not become one assumed transaction because the
   controller updates them sequentially.
5. **Publish:** recheck input/placement identities and required objects, then
   perform the adapter's final visibility transaction. Only after successful
   readback may the corresponding Unison group archive become committed.
6. **Verify/recover:** verify records, paths, hashes and receipt; release launch
   exclusion only after all unfinished journal entries are reconciled. On
   restart inspect durable state rather than trusting the last phase label.
   Roll forward only verified owned artifacts; restore before-images only if
   ownership/generation checks exclude intervening application changes.

Before publication, failure may leave unreferenced owned payloads or auxiliary
records. It must not expose a declared complete group with missing components.
After publication, cancellation is a recovery event: it cannot simply unlink
now-referenced blobs. Do not restore an old whole database over a newer native
session. If the adapter cannot enforce these obligations, hold the group.

Atomic rename only covers a namespace operation on one filesystem. File and
directory flushing, device cache behavior and any stronger macOS flush policy
need qualification on each target filesystem. Record process-crash recovery
separately from power-loss durability; neither is implied by this state diagram.

## Ownership, missing storage and reclamation

Maintain an owned allocation/reference ledger for new external components.
Reference counts are advisory until reconciled with the authoritative native
state and active transactions. Reclaim only owned objects proved absent from
native references, pending work, retained generations and recovery journals.
Unrelated historical payloads are outside this collector.

Missing targets/volumes are explicit unavailable states, never proof of deletion
or permission to regenerate an entire backlog. A native application replacing
a symlink with a regular file may preserve display correctness while violating
placement; qualify subsequent write, trim, delete, restart and absent-target
behavior. A relinking watcher does not supply a publication transaction or a
strict placement guarantee.

CPU permits remain shared with Unison's existing workers/helpers. The future
publisher also requires per-volume I/O admission, decoded/render working-memory
reservations, aggregate queued component bytes and space reservations. These
are additions to the current estimated `SemanticAdmission` credits, not claims
that those credits already bound RSS, child memory or physical allocation.

## Implementation and qualification boundary

The next implementation needs a typed group manifest/adapter interface,
bounded transport, endpoint-local root resolver, versioned archive integration,
durable journal/recovery engine and application-specific acceptance tests.
Use fake distinct-volume and failure-injection backends before real private
volume tests. Exercise every transition, missing/wrong-identity volumes,
collisions, stale dependencies, dangling refs, old peers, downgrade, one-sided
commit, restart and reclamation. Neither this document nor the existing DNG
extension implements those mechanisms.
