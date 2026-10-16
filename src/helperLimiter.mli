(** Endpoint-local, opt-in native helper limits; owner-loop only. *)
type config
val selected : unit -> config option
val with_verified : config option ->
  inspect:(string -> (string * int64 * string) Lwt.t) ->
  check_cancel:(unit -> unit) ->
  (HelperSupervisor.process_limits option -> 'a Lwt.t) -> 'a Lwt.t
(** Verify the explicitly pinned, bounded-size launcher before execution and
    after all borrowed work settles, including failed work. Hash callbacks must
    use the caller's existing resource workspace and shared worker budget, not
    acquire nested admission/I/O. A pin or identity change rejects even under
    a validation warning policy. None does not inspect or start a worker pool.
    Executable-path checks do not eliminate hostile same-UID exec races. *)
