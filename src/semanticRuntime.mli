(** Singleton semantic execution runtime. Access only from the owner loop. *)
type t = {
  supervisor : HelperSupervisor.t;
  pool : SemanticWorkers.t;
  cpu_budget : int;
  admission : SemanticAdmission.t;
  io : IoAdmission.t;
}
val get : unit -> t
val with_cancellation : (HelperSupervisor.cancellation -> 'a Lwt.t) -> 'a Lwt.t
(** Cancel on global abort/connection cleanup, unregister on completion. *)
val with_io_file : HelperSupervisor.cancellation -> string ->
  (unit -> 'a Lwt.t) -> 'a Lwt.t
(** Reserve the opened candidate's filesystem around independent execution.
    Keep its nonblocking read descriptor until the callback settles. Never
    nest this with worker inspection or another lease from the same I/O gate.
    It is cooperative scheduling, not a pathname or physical-disk guarantee. *)
val with_admission : ?role:SemanticAdmission.role -> HelperSupervisor.cancellation -> payload_bytes:int ->
  descriptors:int -> (unit -> 'a Lwt.t) -> 'a Lwt.t
(** Reserve estimated retained resources before opening/allocating. Cancellation
    removes queued requests immediately; active leases release only after the
    callback settles. CPU permits remain available to nested worker/helper jobs. *)
val with_transaction : ?role:SemanticAdmission.role -> max_payload:int ->
  (HelperSupervisor.cancellation -> 'a Lwt.t) -> 'a Lwt.t
(** Transfer reservation: eight times the enforced profile payload limit plus
    256 KiB buffer credits, and eight descriptor credits. These are estimates,
    not process RSS, external child memory or per-volume I/O limits. Consumers
    preserve source headroom for peer-dependent bidirectional progress. *)
