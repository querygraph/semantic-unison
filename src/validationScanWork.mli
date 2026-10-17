exception Cleanup_failed of exn option * exn
val run_with_validators : validators:CandidateValidator.selected list ->
  staging_base:Fspath.t -> roots:Fspath.t list -> root:Fspath.t ->
  paths:Path.local list -> max_bytes:int64 -> unit Lwt.t
(** Retain an endpoint's immutable policy callbacks captured before scanning. *)
val run : staging_base:Fspath.t -> roots:Fspath.t list -> root:Fspath.t ->
  paths:Path.local list -> max_bytes:int64 -> unit Lwt.t
(** Internal endpoint composition, not scope activation. Caller supplies the
    scanner's bounded selected regular-file list and every local replica root.
    Off/empty opens nothing. Otherwise create a fresh0700 directory under an
    owned non-group/world-writable staging_base, outside every supplied root
    (ancestor inode checks cover case/symlink aliases). Validate serially using
    isolated private stages; no process CWD changes. Scanner follow policy and
    resolved logical path are checked before/after each operation. The private
    directory is retired only after callbacks/workers settle. Pending retained
    stage ownership prevents cleanup/return. Failed/rebound directory cleanup
    preserves the original failure and never recursively deletes/retries names.
    [run] captures callbacks once, before opening staging. Cooperative namespace
    fences, not a hostile-same-UID sandbox. *)
