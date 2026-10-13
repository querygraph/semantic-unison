type region = { offset : int64; length : int }
type manifest = { regions : region list }
type change = Exact_bytes | Editable_metadata | Other_bytes
module type S = sig
  val profile : string
  val inspect : SemanticFile.t -> (manifest, string) result
end
type handle
val trusted : ?capability:string -> ?max_payload:int -> ?suffixes:string list -> (module S) -> handle
(** Construct an immutable handle for locally trusted compiled code. Call on
    the owner thread. The extension must use only worker-local state, bounded
    reads, and the supplied SemanticFile; no registries, legacy globals,
    subprocesses, or callbacks into the owner. This is an audited contract,
    not a plugin sandbox or compiler-enforced portable-code proof. *)
val profile : handle -> string
val capability : handle -> string
(** Feature-negotiation identifier; defaults to semantic-profile:<profile>.
    Pure metadata only: feature registration/testing belongs to the owner. *)
val implementation : handle -> (module S)
val payload_limit : handle -> int
(** Enforced total editable-payload limit. Defaults to 16 MiB, restricted to the
    core ceiling. Admission uses this immutable declaration before allocating. *)
val suffixes : handle -> string list
val matches_filename : handle -> string -> bool
(** Case-insensitive filename suffix hints for advisory UI behavior only.
    Defaults to none; at most 16 dot-prefixed suffixes of 2..32 bytes. A match
    is not proof of format or eligibility. Transfer must inspect file contents
    independently, including files whose names do not match a hint. *)
val resolve : string -> handle option
(** Owner-only registry lookup. Resolve before dispatching to a worker. *)
val register : ?capability:string -> ?max_payload:int -> ?suffixes:string list -> (module S) -> unit
val find : string -> (module S) option
val profiles : unit -> string list
val registered : unit -> handle list
(** Owner-only snapshot in registration order. Static registrations must
    finish before the owner registers/negotiates feature capabilities. *)
val inspect : ?max_payload:int -> (module S) -> SemanticFile.t -> (manifest, string) result
(** Independently checks region bounds, canonical order and the total payload
    declaration before the core copies or hashes editable packet contents. *)
val max_region : int
val max_payload : int
