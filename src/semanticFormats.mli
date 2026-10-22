val register : ?capability:string -> ?max_payload:int -> ?suffixes:string list ->
  ?observer:FormatExtension.observer -> ?span_semantics:FormatExtension.span_semantics ->
  (module FormatExtension.S) -> unit
(** Owner-side startup registration for a trusted compiled profile and its
    independently negotiated wire capability. Call before feature negotiation.
    Adding a format requires registration, not transfer/worker dispatch edits. *)
val local_enabled : unit -> FormatExtension.handle list
val peer_enabled : unit -> FormatExtension.handle list
val resolve_peer : string -> FormatExtension.handle option
(** Explicitly selected profiles whose capabilities were negotiated. *)
val apply_dng_merge_admissions : unit -> unit
(** Owner thread only: publish the dngmergeadmit fields to the merge-only DNG
    inspector before base capture or reconciliation. *)
