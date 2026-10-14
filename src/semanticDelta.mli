type proof
type t
type description = { profile : string; size : int64; digest : string;
                     preserved_digest : string; regions : FormatExtension.region list }
type application = { logical_bytes_written : int; write_calls : int;
                     comparison_window : int }
type sample = { region : FormatExtension.region; digest : string;
                prefix : string; truncated : bool }
val inspect : ?max_payload:int -> (module FormatExtension.S) -> SemanticFile.t -> (proof, string) result
val plan : nonce:string -> base:proof -> target:proof -> (t, string) result
val classify : base:proof -> target:proof -> FormatExtension.change
val encode : t -> string
val decode : ?max_payload:int -> string -> (t, string) result
val profile : t -> string
val proof_profile : proof -> string
val describe : proof -> description
(** Immutable public description, with raw 32-byte hashes and no metadata
    contents. A decoded remote proof is still only an unverified peer claim. *)
val samples : ?max_region_bytes:int -> ?max_total_bytes:int -> proof -> sample list
(** Bounded immutable metadata samples; maxima/defaults are 4096 bytes per
    region and 8192 bytes total. Smaller limits, including zero, are allowed.
    [truncated] means the sample does not contain the complete region. This
    does not turn an unverified decoded peer claim into a verified proof. *)
val target_digest : t -> string
val target_size : t -> int64
val payload_size : t -> int
val max_request_size : int
val max_envelope_size : int
val encode_request : nonce:string -> proof -> string
val decode_request : string -> (string * proof, string) result
(** Canonical SDR/0 description containing nonce, full/complement hashes and
    bounded metadata region hashes, without metadata contents. A decoded
    proof is only a peer claim; use it as the base input to [plan]. *)
val observe : extension:FormatExtension.handle -> proof ->
  (FormatExtension.observation, string) result option
(** Worker-local optional advisory interpretation of the retained full editable
    packet bytes. Never call on an SDR peer claim or use it as transfer authority.
    SDE/0, SDR/0, preservation hashing and exact-byte classification are unchanged. *)
val max_base_cache_size : int
val encode_base_cache : proof -> string
val decode_base_cache : string -> (proof, string) result
(** Bounded canonical lossless single-XMP DNG base record; includes full and
    preserved hashes, exact geometry, packet, canonical parsed scalar spans/value and shell hashes, policy/parser
    versions and checksum.
    Only the owner may use this after verifying trusted local storage and common
    previous-archive binding. Parsing/checksum do not authenticate a base, and
    a decoded record is never independent merge or transfer authority. Unknown
    versions/profiles, incomplete peer proofs and incompatible packets reject. *)
val binds_request : nonce:string -> base:proof -> t -> bool
(** Match a response against the receiver's retained local proof and nonce
    before applying anything. *)
val apply : t -> basis:SemanticFile.t -> output:Unix.file_descr -> unit
(** Output must be a private regular staging file already containing the exact
    basis. Verify both descriptors before any write; verify target SHA-256
    after writes. Does not rename, set properties, or update archives. *)
val apply_report : t -> basis:SemanticFile.t -> output:Unix.file_descr -> application
(** Owner-side registry-resolving variant with logical-write counters. *)
val apply_with_extension : ?check_cancel:(unit -> unit) -> ?max_payload:int ->
  (module FormatExtension.S) -> t -> basis:SemanticFile.t -> output:Unix.file_descr -> unit
(** Worker-safe variant with an explicitly selected built-in extension and no
    registry access. The caller must also install its cancellation check on
    the basis SemanticFile. A cancellation can leave a partially written
    private output, which the caller must discard. *)
val apply_report_with_extension : ?check_cancel:(unit -> unit) -> ?max_payload:int ->
  (module FormatExtension.S) -> t -> basis:SemanticFile.t -> output:Unix.file_descr -> application
(** Same verified materialization, with actual returned write-byte counts and
    write primitive attempts (including EINTR retries). POSIX uses bounded native
    pwrite; the Windows backend retains seek/write. Only changed absolute
    4 KiB comparison windows are written, clipped to editable regions; adjacent
    windows are combined and each write is at most 64 KiB. Counts describe
    logical writes, not physical allocations, durability or elapsed speedup.
    Unchanged metadata performs no data writes. *)

val reconcile_xmp : ?max_payload:int -> (module FormatExtension.S) ->
  nonce:string -> base:proof -> left:proof -> right:proof -> SemanticFile.t ->
  (t, string) result
(** Build one deterministic exact target plan against the live left descriptor.
    The owner must supply a trusted archive-bound common base; this function
    does not establish archive generation or authority. Require matching DNG
    profile/layout/size/protected identities and full single XMP packets from
    all three inspections. Refuse peer-only proofs, conflicts and packet growth.
    Reinspect the live left file, compute target SHA-256 from its protected bytes
    plus merged metadata, and check stability. No output is opened or modified.
    Materialize the returned plan through ordinary verified private staging;
    validate and use the existing two-replica merge/commit lifecycle. *)
