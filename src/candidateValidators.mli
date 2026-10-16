val register : ?resources:(unit -> BackendResources.t) -> (module CandidateValidator.S) -> unit
(** Register a locally compiled validation companion during startup, before
    selection/feature negotiation. At most sixteen unique format identifiers;
    all transfer profiles for a format share this single validation companion. *)
val selected : unit -> CandidateValidator.selected list
(** Capture active owner-side policies and settings. Independent of semantic
    transfer selection, filename suffixes and patch eligibility. *)

val maximum_resources : CandidateValidator.selected list -> BackendResources.t
