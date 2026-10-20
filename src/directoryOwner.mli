(** Owner-loop single-attempt ownership of opaque Unix directory handles.
    No numeric descriptor is guessed or exposed, and uncertain closes are never
    retried. This module does not establish process-tree resource limits. *)
type t
type phase = Empty | Opening | Held | Close_uncertain | Closed | Open_failed
exception Uncertain of t
val prepare : unit -> t
val open_with : t -> string -> (unit -> 'a) -> 'a
(** The owner, callback and return wrapper must exist before acquisition. Root
    before Unix.opendir; adopt its actual returned handle without allocation.
    Publication failure closes once or raises the retained carrier. Failures
    inside the OCaml Unix stub before returning a handle remain its boundary. *)
val read : t -> string
val close : t -> unit
val remember_failure : t -> exn -> unit
val phase : t -> phase
val path : t -> string
val operation_cause : t -> exn option
val close_cause : t -> exn option
val retained_count : unit -> int
val iter_retained : (t -> unit) -> unit
(** Forensic owner identity/path only; a pathname is not an inode attestation.
    Known-open owners stay rooted until known close. No reset/release API. *)
