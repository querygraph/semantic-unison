val enabled : unit -> bool
val before_commit : directory:Fspath.t -> candidate:Path.local ->
  destination:Path.local -> unit Lwt.t
(** Validate finalized private received candidates, including descendants of
    staged directory trees, before any rename/archive mutation. *)
