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
