(** Advisory DNG physical partition for component hashing. Unknown gaps remain
    opaque; table descriptors/padding remain structural. No merge/transfer authority. *)
val describe : SemanticFile.t -> (ComponentHash.spec, string) result
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
