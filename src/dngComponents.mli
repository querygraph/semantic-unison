(** Advisory DNG physical partition for component hashing. Unknown gaps remain
    opaque; table descriptors/padding remain structural. No merge/transfer authority. *)
val describe : SemanticFile.t -> (ComponentHash.spec, string) result
(** Existing partitions of at most480 claims keep schema /0 unchanged. Larger
    raw geometries (bounded at65536) reject aliases, then coalesce only touching
    same-role claims with ordered membership provenance into schema /1 leaves.
    The exact sum of leaves, nonempty opaque gaps and root must fit the
    unchanged1024-node core.
    Private field decoder IDs inside a coalesced run are not claimed available;
    unknown/missing decoders remain exact. No physical gaps are bridged.
    If schema /1 still exceeds that node budget, schema /2 may classify each TIFF
    field's descriptor and padding/offset slot as that parser-classified field's
    metadata encoding, then group same-role adjacent encodings. Unknown fields
    remain private, image claims never change role, and shared headers stay
    structural. This is a coarser versioned view, not value-only equivalence. *)
type binding = { component_id : string; decoder : ComponentHash.plugin }
type decoders
type status = Unmatched | Unsupported of string | Refined
type outcome = { component_id : string; decoder_id : string;
                 implementation_sha256 : string; status : status }
val freeze_decoders : binding list -> (decoders, string) result
(** Owner-selected immutable ordered bindings, at most64 distinct targets.
    IDs and implementation SHA declarations are checked before file inspection.
    No registry lookup, code loading or peer selection. Parent bindings precede
    their children (reversed ancestor order is refused before inspection);
    missing targets/unsupported decoders preserve opaque bytes.
    This does not authenticate locally supplied compiled code. *)
val with_snapshot : decoders:decoders -> max_read_bytes:int64 -> SemanticFile.t ->
  (ComponentHash.session -> initial:ComponentHash.snapshot ->
   refined:ComponentHash.snapshot -> outcome list -> 'a) -> ('a, string) result
(** Describe/hash once, then refine selected private/opaque leaves in order.
    Child fragments may claim private, opaque or structural roles only; no
    private decoder may add encoded-pixel or standard-metadata authority.
    All decoder/rehash reads share one budget. Explicit unsupported results
    leave the prior snapshot intact; operational/malformed-fragment errors
    propagate. The owner must retain immutable input throughout the callback.
    Snapshots are historical observations, not persistent reuse authority. *)

val with_checkpoint : expected_checkpoint_sha256:string -> max_read_bytes:int64 ->
  SemanticFile.t -> string -> (ComponentHash.session -> ComponentHash.snapshot -> 'a) ->
  ('a, string) result
(** Restore authenticated historical component metadata, verify the entire current
    input, and validate its base partition against the current DNG parser before
    callback. Unsupported geometry returns Error; invalid checkpoint/input raises
    ComponentHash.Invalid. The expected digest must come from trusted prior owner
    state, not the supplied bytes. Parser description reads are additional to the
    core hash/refinement budget. This retains historical private interpretations,
    not an assertion that current decoder implementations approve them. Decoder
    provenance selection/invalidation and persistent storage remain owner duties.
    No peer authority, automatic decoder invocation or IO-free restore. *)

val replace_private_view : ComponentHash.session -> ComponentHash.snapshot ->
  component:string -> expected_schema:string -> ComponentHash.plugin ->
  (ComponentHash.snapshot, string) result
(** Explicit compare-and-replace of one private view. The old schema must match;
    the replacement is bounded to private/opaque/structural children. On an
    unsupported decoder result, no replacement snapshot is published and the
    caller retains its original view. Operational errors propagate. Success
    rereads only the target span plus decoder reads, preserves unrelated nodes
    and recomposes ancestors. Descendant views under that target are replaced;
    owners must reselect their bindings. No automatic persistence or peer trust. *)

type refresh = { snapshot : ComponentHash.snapshot; outcomes : outcome list;
                 reused : string list; invalidated : string list }
val with_refreshed_checkpoint : previous:outcome list -> decoders:decoders ->
  expected_checkpoint_sha256:string -> max_read_bytes:int64 -> SemanticFile.t -> string ->
  (ComponentHash.session -> refresh -> 'a) -> ('a, string) result
(** Restore then reconcile owner-retained successful decoder provenance against
    the current frozen bindings. [previous] must be the complete authenticated
    outcome inventory from that extraction, not supplied by a peer. Validate each
    prior Refined target/schema. Unchanged views are listed in [reused] and do
    not invoke a decoder; changed/removed views reset before applying current
    bindings parent-first. Descendants of invalidated parents cannot be reused.
    Unrelated hashes remain; unsupported replacements preserve exact unknown
    atoms. [outcomes] includes historical Refined entries for reused targets,
    distinguished by [reused]; [invalidated] identifies obsolete bindings.
    Operational errors propagate without publishing a new checkpoint. No disk
    store, automatic registry discovery or transfer authority. *)

type owner_entry
val owner_entry_max_size : int
val make_owner_entry : root_identity:string -> path:string -> generation_sha256:string ->
  checkpoint:ComponentHash.checkpoint -> outcomes:outcome list -> owner_entry
val owner_entry_bytes : owner_entry -> string
val owner_entry_sha256 : owner_entry -> string
val owner_entry_binding : owner_entry -> string
val owner_entry_record_sha256 : owner_entry -> string
val owner_entry_outcomes : owner_entry -> outcome list
val decode_owner_entry : root_identity:string -> path:string -> generation_sha256:string ->
  expected_entry_sha256:string -> string -> owner_entry
val checkpoint_for_owner_entry : owner_entry -> string -> ComponentHash.checkpoint
(** Bounded UDI/0 immutable owner-index entry: exact root/path identity, owner
    generation digest, input digest, ordered decoder outcomes and checkpoint/record
    references. Make from a trusted successful extraction's checkpoint/outcomes;
    validates historical Refined schemas/private-only roles. Decode requires the
    prior whole-entry digest from trusted owner state and exact root/path/generation.
    A self-hash of arbitrary disk bytes is NOT that trust. Record loading checks
    entry binding, record/checkpoint/input digests and inventory consistency.
    Metadata only; actual current-input/base validation still requires restore.
    No generation selection, pathname interpretation, quota, index namespace
    publication, peer code, archive authority or automatic cache selection. *)

val write_owner_entry : owner_entry -> Unix.file_descr -> string
val read_owner_entry : root_identity:string -> path:string -> generation_sha256:string ->
  expected_entry_sha256:string -> SemanticFile.t -> owner_entry
val prepare_owner_entry_publication : owner_entry -> directory:Unix.file_descr ->
  stage:Unix.file_descr -> temporary:string -> SemanticFile.t -> ComponentHash.record_publication
(** Borrowed-descriptor bounded UDI/0 staging/readback and owner-only macOS immutable
    entry publication. Digest-named leaf, exact entry readback, same native private
    directory/stage binding, exclusive rename and publication-state rules as records.
    Keep caller FDs live/exclusive until settled; no descriptor closes or paths
    opened here. No overwrite, mutable latest pointer, lookup, quota, managed
    namespace installation, archive advancement or automatic cache selection. *)

type cache_capture
val stage_cache_capture : owner_entry -> checkpoint:ComponentHash.checkpoint ->
  quota:ComponentHash.metadata_quota -> directory:Unix.file_descr ->
  record_stage:Unix.file_descr -> entry_stage:Unix.file_descr -> unit
val prepare_cache_capture : owner_entry -> quota:ComponentHash.metadata_quota ->
  directory:Unix.file_descr -> record_stage:Unix.file_descr -> entry_stage:Unix.file_descr ->
  record_file:SemanticFile.t -> entry_file:SemanticFile.t -> cache_capture
val publish_cache_capture : cache_capture -> Unix.file_descr -> Unix.file_descr -> Unix.file_descr -> unit
val cache_capture_state : cache_capture -> bool * bool
(** Explicit one-use paired capture. Reserve first, then caller creates empty
    stages named slot-record.tmp/slot-entry.tmp in that same private directory.
    Stage validates both borrowed identities before either write. Prepare seals
    those identities and independently authenticates both staged files. Publish
    record first, entry only after normal record publication returns; once only.
    State reports actual native record/entry rename effects even after error.
    Preserve partial stages/published orphans and consumed quota; never replay or
    infer rollback. Borrow all FDs/readers with caller-owned exclusive lifetimes;
    no opens/closes, automatic lookup, recovery, global index advancement or
    source-photo reads/writes. Caller settles descriptors before index adoption. *)

type capture_recovery = Capture_missing | Capture_entry_only
  | Capture_record_only of ComponentHash.checkpoint | Capture_complete of ComponentHash.checkpoint
val inspect_cache_capture : owner_entry -> directory:Unix.file_descr ->
  record:(Unix.file_descr * SemanticFile.t) option ->
  index:(Unix.file_descr * SemanticFile.t) option -> capture_recovery
(** Known trusted-entry recovery lookup, macOS, borrowed readers/FDs only. Optional
    readers must match actual no-follow presence, not an asserted absence. Recheck
    private native name/FD identity around bounded content authentication. Reject
    foreign/symlink/mismatched objects; never downgrade those errors to missing.
    Complete means both exact published metadata objects observed, not live-source
    eligibility: restore still verifies full current input/base. Entry-only is a
    broken reference; record-only is an orphan, not index advancement. No opens,
    closes, writes, cleanup, directory scan, automatic selection or peer trust. *)

val with_cache_capture : owner_entry -> directory:Unix.file_descr ->
  record:(Unix.file_descr * SemanticFile.t) option ->
  index:(Unix.file_descr * SemanticFile.t) option -> decoders:decoders ->
  max_read_bytes:int64 -> SemanticFile.t ->
  (ComponentHash.session -> refresh -> 'a) -> ('a, string) result
(** Authenticate a complete known capture, then verify the whole current input
    and current parser partition before refreshing frozen decoder bindings. The
    historical inventory/digests come only from the trusted entry, not separate
    caller-selected arguments. Incomplete captures return explicit Error without
    invoking the callback; corrupt/foreign evidence and operational errors raise.
    No fallback extraction, opens/closes, selection, cleanup or publication. All
    source/cache readers and their borrowed descriptors remain caller-owned. *)

type owner_index
val empty_owner_index : max_entries:int -> max_bytes:int -> owner_index
val owner_index_usage : owner_index -> int * int
val select_owner_entry : owner_index -> root_identity:string -> path:string ->
  generation_sha256:string -> owner_entry option
(** Admission only; replacement still requires the expected prior entry digest. *)
val owner_index_has_capacity_for : owner_index -> owner_entry -> bool
val replace_owner_entry : owner_index -> expected_entry_sha256:string option ->
  owner_entry -> (owner_index, string) result
val remove_owner_entry : owner_index -> root_identity:string -> path:string ->
  expected_entry_sha256:string -> (owner_index, string) result
(** Immutable owner-trusted selection ledger, at most1024 entries and8MiB encoded
    entry payload. Caller chooses stricter positive limits. Keys are exact owner
    root/path identities, not normalized/interpreted filesystem paths. Selection
    requires the explicit current generation; no digest/time ordering or newest
    disk-file inference. Insert requires absence; replace/remove compare the
    previous trusted entry digest. Failed updates preserve the old value. Bounds
    charge encoded metadata, not RSS, filesystem usage or native cache quota.
    Only already trusted owner_entry values enter this ledger. Register durable
    captures only after their separate descriptor/publication settlement; this
    pure value proves neither settlement nor on-disk presence. Selected entries
    still require authenticated metadata lookup and full-current-input restore.
    No persistence, disk scan/open/close/eviction, quota refund, archive mutation,
    peer authority or automatic source reading; snapshots can share immutably. *)

val with_indexed_capture : owner_index -> root_identity:string -> path:string ->
  generation_sha256:string -> directory:Unix.file_descr ->
  record:(Unix.file_descr * SemanticFile.t) option ->
  index:(Unix.file_descr * SemanticFile.t) option -> decoders:decoders ->
  max_read_bytes:int64 -> SemanticFile.t ->
  (ComponentHash.session -> refresh -> 'a) -> ('a, string) result
(** Exact owner/generation selection followed by authenticated complete metadata
    and full-current-input/parser verification, then scoped decoder refresh.
    Selection miss returns Error before metadata/source inspection or callback;
    never chooses a different generation or a digest discovered on disk. All
    descriptor lifetimes/settlement and durable ledger publication are external.
    No opens/closes, automatic fallback, archive advancement or disk scan. *)

val max_owner_index_size : int
val owner_index_bytes : binding:string -> owner_index -> string
val restore_owner_index : ?check_cancel:(unit -> unit) ->
  expected_manifest_sha256:string -> binding:string -> max_entries:int -> max_bytes:int ->
  load_entry:(string -> string) -> string -> owner_index
(** Canonical UIX/0 reference-only manifest, at most32848 bytes. Persist its whole
    digest and raw32 owner-state binding in separately trusted owner state at
    capture; hashing an arbitrary disk manifest is not that trust. Restore checks
    digest/binding/exact limits/framing/unique references before invoking the
    owner-controlled loader with each prior-trusted entry digest. Loader must
    bound its own IO/allocation to owner_entry_max_size; it receives no pathname.
    Every entry digest/canonical UDI/key order and exact aggregate payload charge
    is independently checked. Wrong/missing entries and operational/cancellation
    errors propagate without mutating the prior ledger or returning partial state.
    Limits are per value, not aggregate RSS; owner serializes durable adoption.
    No opens/closes, disk publication, archive trust, peer authority or source IO.
    Selected entries still require authenticated metadata and full-input restore. *)

val write_owner_index : binding:string -> owner_index -> Unix.file_descr -> string
val read_owner_index : ?check_cancel:(unit -> unit) -> expected_manifest_sha256:string ->
  binding:string -> max_entries:int -> max_bytes:int -> load_entry:(string -> string) ->
  SemanticFile.t -> owner_index
(** Bounded UIX/0 descriptor-only storage. Write borrows a fresh private0600 singly
    linked output, syncs/checks it and returns the captured manifest digest. Read
    checks bounded size and reader stability both before and after entry loading;
    loader failure/cancellation propagates. All FD/readers remain caller-owned.
    No opens/duplicates/closes, native quota reservation, namespace installation,
    trusted-state update or automatic cache activation. *)

type owner_index_publication
val prepare_owner_index_publication : binding:string -> owner_index ->
  directory:Unix.file_descr -> stage:Unix.file_descr -> temporary:string ->
  SemanticFile.t -> owner_index_publication
val publish_owner_index : owner_index_publication -> Unix.file_descr -> Unix.file_descr -> unit
val owner_index_published : owner_index_publication -> bool
(** Owner-only macOS immutable manifest publication. Independently hash/read back
    the stage against the captured ledger/binding, then borrow the private native
    directory/stage/name ticket. Exactly one publication attempt, including a
    failed pre-rename call; no replay/reset. Actual rename state survives errors.
    Caller preserves failed stages/orphans and owns resource/quota admission,
    FD settlement, referenced-entry closure and separately trusted owner-state
    commit. A published file alone is not durable index adoption or crash-recovery
    authority. No output overwrites, cleanup, source-photo access or FD closes. *)

val owner_index_reference : owner_index_publication -> string * string
(** Return captured (manifest binding, manifest digest) only after publication
    returned normally, not merely after an observed rename. Caller must separately
    settle descriptors/referenced objects before adopting it in trusted state. *)
val owner_archive_reference_size : int
val encode_owner_archive_reference : archive_binding:string -> binding:string ->
  manifest_sha256:string -> string
val decode_owner_archive_reference : archive_binding:string -> string -> (string * string) option
(** Fixed136B UAX/0 local archive hint. Context is the owning archive root/pair/
    generation binding, not peer metadata or a cache file's self-hash. Decoder
    declines malformed/mismatched optional hints; this codec alone establishes no
    authority. Use only inside already trusted local owner-state load/commit. *)


type cache_descriptor = Unix.file_descr * Unix.LargeFile.stats option
type cache_ownership
exception Cache_ownership_uncertain of cache_ownership
val cache_ownership_cause : cache_ownership -> exn option
val cache_uncertain_descriptors : cache_ownership -> (cache_descriptor * exn) list
val cache_retained_descriptors : cache_ownership -> cache_descriptor list
val cache_borrowed_directory : cache_ownership -> cache_descriptor
(** Owner-only retained-ownership carrier. Each uncertain descriptor has one
    attempted close and last observable identity before close; never retry its numeric
    FD, which may already be recycled. Retained descriptors were not closed and
    remain owned. Borrowed directory stays caller-owned throughout; retain outer
    ownership/resources on this exception. Original read/validation failure and
    all nested uncertain/known descriptors remain available for recovery evidence.
    No finalizer, automatic cleanup/retry, or settlement proof is supplied. *)
val load_owner_index : ?check_cancel:(unit -> unit) ->
  directory:Unix.file_descr -> expected_manifest_sha256:string ->
  binding:string -> max_entries:int -> max_bytes:int -> unit -> owner_index option
val load_owner_record : ?check_cancel:(unit -> unit) -> directory:Unix.file_descr ->
  entry:owner_entry -> unit -> string option
(** macOS managed metadata reads through an existing borrowed private0700 directory.
    Open only the separately trusted digest's64hex leaf, read-only/nonblocking/
    no-follow/cloexec, verify private0600 singly-linked regular name/FD binding and
    bounded stable content before/after borrowed positional reads, then close once.
    Index restore authenticates UIX and every UDI entry; record restore authenticates
    its UCR binding/inventory. Successful return means all loader-owned FDs closed.
    Missing selected manifest/record returns None; a missing referenced entry,
    foreign object, corrupt metadata or operational error propagates. Close errors
    always raise Cache_ownership_uncertain, retaining original cause and all known
    enclosing descriptors without retry. Caller must hold the directory FD stable
    and retain exclusive snapshot access/IO, metadata-memory and lifetime admission.
    No source payload, directory enumeration/creation, cache discovery, publication,
    eviction, archive mutation, peer trust or non-macOS fallback. *)


type cache_namespace
val cache_namespace_name : string
val prepare_cache_namespace : ?expected:(int * int) -> parent:Unix.file_descr -> unit -> cache_namespace
val provision_cache_namespace : cache_namespace -> parent:Unix.file_descr -> unit
val cache_namespace_created : cache_namespace -> bool
val cache_namespace_identity : cache_namespace -> int * int
val with_cache_namespace : cache_namespace -> parent:Unix.file_descr ->
  (Unix.file_descr -> 'a) -> 'a
(** macOS one-use private directory ticket under an existing borrowed private0700
    parent. Caller exclusively controls parent/child names and holds the parent
    FD stable across preparation/provision/open; this is not hostile same-UID
    exclusion. Fixed component-cache-v0 child only. No [expected] means fresh mkdir;
    EEXIST refuses rather than adopting an unknown directory. [expected] reopens
    only the separately trusted device/inode, never creates or scans. Provision
    attempts once, records actual mkdir before later validation/parent-sync error,
    and retains the created directory on every failure. Inspect created/identity
    after error; identity exists only if observed, not proof of sync or settlement.
    No automatic rollback/retry or chmod. A failed provision cannot open its ticket.
    Scoped open attempts once with no-follow/directory/cloexec flags and rechecks
    parent/name/FD identity before/after a synchronous callback. Callback borrows
    the directory exclusively; finish all work before return, no FD/async escape.
    Close uses Cache_ownership_uncertain, preserving known enclosing handles and
    every borrowed directory. Caller owns admission, retained effects/recovery and
    trusted expected identity across restart; identity alone is not manifest trust.
    No recursive path creation, namespace discovery, source access, publication,
    archive adoption, quota refund, eviction or automatic cache activation. *)
val cache_borrowed_directories : cache_ownership -> cache_descriptor list
(** All borrowed directory identities retained through nested scopes. The singular
    accessor returns the originating directory for backward compatibility. *)

type managed_cache_store
val prepare_managed_cache_store : entry:owner_entry -> checkpoint:ComponentHash.checkpoint ->
  index:owner_index -> expected_entry_sha256:string option -> binding:string ->
  max_bytes:int64 -> max_entries:int -> managed_cache_store
val execute_managed_cache_store : managed_cache_store -> namespace:cache_namespace ->
  parent:Unix.file_descr -> bool
val managed_cache_store_reference : managed_cache_store -> string * string
val managed_cache_store_index : managed_cache_store -> owner_index
val managed_cache_store_effects : managed_cache_store -> bool * bool * bool * bool * bool
(** Synchronous one-use bounded capture, entry and next-manifest publication.
    False means quota exhaustion; errors preserve all stages/orphans/reservations.
    Reference/index access requires normal publication AND all owned FD closes.
    Effects report reserved/record/entry/manifest/completed, not rollback. Parent
    stays borrowed. Uncertain closes retain ownership through the existing carrier.
    No archive commit, automatic report routing, deletion or eviction. *)

val owner_namespace_reference_size : int
val encode_owner_namespace_reference : archive_binding:string -> binding:string ->
  manifest_sha256:string -> int * int -> string
val decode_owner_namespace_reference : archive_binding:string -> binding:string ->
  manifest_sha256:string -> string -> (int * int) option
(** Optional archive-context and exact-manifest-bound namespace device/inode tail.
    Missing, malformed, foreign or out-of-range values return None. *)
val managed_cache_store_namespace : managed_cache_store -> int * int
val owner_entry_reference : owner_index -> root_identity:string -> path:string -> string option
(** Exact key's prior entry digest for compare-and-replace, independent of generation
    selection. This is not permission to restore a stale generation. *)

type cache_parent
val open_cache_parent : string -> cache_parent
val check_cache_parent : cache_parent -> unit
val cache_parent_descriptor : cache_parent -> Unix.file_descr
val settle_cache_parent : cache_parent -> exn option -> unit
(** Existing absolute private0700 parent only, macOS no-follow/nonblocking/CLOEXEC.
    Explicit owner survives async awaits; no finalizer or implicit close. Settle
    once after all work: None closes, Some error closes and rethrows ordinary
    errors, but nested ownership uncertainty retains this known FD in its carrier.
    Close failure retains last observed identity and never retries a number.
    Descriptor access remains borrowed, requiring caller-exclusive lifetime.
    No mkdir, namespace discovery, canonical IO or source access permission. *)

type component_source
val open_component_source : (unit -> Unix.file_descr) -> component_source
val component_source_descriptor : component_source -> Unix.file_descr
val settle_component_source : component_source -> exn option -> unit
val cache_origin_descriptor : cache_ownership -> cache_descriptor
(** Prepared ownership exists before the opener runs. The opener must return its
    new owned FD immediately without post-open actions; regular-file validation
    runs after recording ownership. Source remains borrowed to workers, settled
    exactly once after their completion. Close uncertainty retains identity and
    nested cache uncertainty retains this source. No finalizer or numeric retry.
    The carrier origin accessor may describe a regular source; historical
    directory-named accessors remain unchanged for existing metadata callers. *)
