val enabled : unit -> bool
val before_commit : directory:Fspath.t -> candidate:Path.local ->
  destination:Path.local -> unit Lwt.t
(** Validate finalized private received candidates, including descendants of
    staged directory trees, before any rename/archive mutation. Extension-owned
    policy/recognizers select validators by destination claim or file contents,
    independently of semantic transfer enablement and eligibility. *)

val before_commit_with_reservation : reservation:SemanticAdmission.reservation option ->
  directory:Fspath.t -> candidate:Path.local -> destination:Path.local -> unit Lwt.t
(** A bound receiver loans its retained envelope for serialized file validation,
    including explicit legacy directory handoff. Unbound trees use fresh per-file
    admission. Tree manifests and external SDK allocations are outside buffer
    credits. Helpers/worker jobs settle before returning. *)
