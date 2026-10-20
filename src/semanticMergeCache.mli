(** Owner-only optional trusted private metadata base storage. Never accepts a
    peer record or chooses the common archive generation. *)
val enabled : unit -> bool
val store : root:Fspath.t -> path:Path.local -> fingerprint:Os.fullfingerprint ->
  SemanticDelta.proof -> unit
val load : root:Fspath.t -> path:Path.local -> fingerprint:Os.fullfingerprint ->
  SemanticDelta.proof option
(** Fingerprint must be the agreeing previous common archive, not a current
    replica. Missing, incompatible, malformed or untrusted records decline. *)

(** Joint owner-loop forensic evidence. A retained scope raises an existing
    NotificationPipe.Uncertain carrier, keeping upstream admission unresolved.
    These accessors grant no numeric close, pathname deletion or retry authority.
    Directory handles are opaque; paths and pre-close stats are observations. *)
type ownership
type temporary_phase = No_temporary | Temporary_opening | Temporary_owned | Unlink_attempted | Temporary_removed | Unlink_uncertain
val retained : unit -> ownership list
val operation_cause : ownership -> exn option
val uncertainty_cause : ownership -> exn
val files : ownership -> (string * NotificationPipe.t) list
val directories : ownership -> DirectoryOwner.t list
val temporary : ownership -> string * temporary_phase * Unix.stats option
val temporary_cause : ownership -> exn option
