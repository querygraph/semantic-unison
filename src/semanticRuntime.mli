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
val with_admission : ?reservation:SemanticAdmission.reservation -> ?role:SemanticAdmission.role -> HelperSupervisor.cancellation -> payload_bytes:int ->
  descriptors:int -> (unit -> 'a Lwt.t) -> 'a Lwt.t
(** Reserve estimated retained resources before opening/allocating. Cancellation
    removes queued requests immediately; active leases release only after the
    callback settles. CPU permits remain available to nested worker/helper jobs. *)
val make_publication_reservation : unit -> SemanticAdmission.reservation
(** Allocate the caller's durable consumer owner, without debit or initializing
    the worker pool. Acquire before target preparation; close native ownership
    before retirement. Envelope: 24 descriptor credits and max(1 MiB,
    8 * enabled payload limit + 256 KiB). This is selected-path accounting,
    not whole-process FD/RSS or external-child admission. *)
val admission_usage : unit -> SemanticAdmission.usage
(** Owner-loop diagnostics without starting worker domains. *)
val with_transaction : ?reservation:SemanticAdmission.reservation -> ?role:SemanticAdmission.role -> max_payload:int ->
  (HelperSupervisor.cancellation -> 'a Lwt.t) -> 'a Lwt.t
(** Consumers acquire 24 descriptor credits and retained buffer estimates, or
    borrow an existing publication envelope without another gate acquisition.
    Sources retain eight descriptor credits through reply encoding/sending.
    Buffer credits use eight times the enforced profile payload limit plus
    256 KiB, with a 1 MiB consumer minimum for serialized validation. These are estimates,
    not process RSS, external child memory or per-volume I/O limits. Consumers
    preserve source headroom for peer-dependent bidirectional progress. *)
