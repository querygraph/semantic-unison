type region = { offset : int64; length : int }
type manifest = { regions : region list }
type change = Exact_bytes | Editable_metadata | Other_bytes
type category = Descriptive | Rendering | Identity | Workflow | Opaque
type property = { name : string; category : category; digest : string }
type observation = { schema : string; properties : property list }
type observer = { schema : string; observe : string list -> (property list, string) result (* ox-portable-field *) }
module type S = sig (* ox-portable-signature *)
  val profile : string
  val inspect : SemanticFile.t -> (manifest, string) result
end
type handle
val trusted : ?capability:string -> ?max_payload:int -> ?suffixes:string list ->
  ?observer:observer -> (module S) -> handle
(** Construct an immutable handle for locally trusted compiled code. Call on
    the owner thread. The extension must use only worker-local state, bounded
    reads, and the supplied SemanticFile; no registries, legacy globals,
    subprocesses, or callbacks into the owner. Stock builds rely on this audit; OxCaml requires portable callback
    captures through the checked signature. Bounds, native ownership and
    algorithm behavior remain audited contracts, not a plugin sandbox. *)
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
val register : ?capability:string -> ?max_payload:int -> ?suffixes:string list ->
  ?observer:observer -> (module S) -> unit
val find : string -> (module S) option
val profiles : unit -> string list
val registered : unit -> handle list
(** Owner-only snapshot in registration order. Static registrations must
    finish before the owner registers/negotiates feature capabilities. *)
val observe : handle -> string list -> (observation, string) result option
(** Optional extension-defined advisory observation of full editable packets.
    Worker-only, bounded and pure under the same trusted-code contract as
    inspection. Core accepts at most 128 unique sorted properties, 512-byte
    nonempty names, 32-byte digests and a 128-byte versioned schema. Unsupported
    metadata returns a bounded reason; it does not disable exact-byte transfer.
    Categories describe potential meaning, never rendering equivalence or
    authority to reconcile, suppress conflicts, or publish a file. *)
val validate_observation : observation -> (unit, string) result
(** Check the same bounds/canonical unique ordering on a decoded peer statement. *)
val inspect : ?max_payload:int -> (module S) -> SemanticFile.t -> (manifest, string) result
(** Rejects empty, over128-byte or NUL-containing profile names before invoking
    the extension parser. Valid unregistered local modules may still be inspected;
    registration/negotiation and write authority remain separate. Independently
    checks region bounds, canonical order and the total payload declaration
    before the core copies or hashes editable packet contents. *)
val max_region : int
val max_payload : int
