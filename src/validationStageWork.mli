(** Owner-loop asynchronous private snapshot/validation composition. *)
exception Cancelled
exception Snapshot_changed
val run : pool:SemanticWorkers.t -> cancellation:HelperSupervisor.cancellation ->
  max_bytes:int64 -> create:(unit -> ValidationStage.t) ->
  validate:(candidate:string -> snapshot:ValidationSnapshot.report -> unit Lwt.t) ->
  ?on_retained:(ValidationStage.t -> unit) -> unit -> unit Lwt.t
(** Caller acquires the full staging/backend memory and FD envelope BEFORE
    invoking this operation, and retains it until the returned work settles.
    [create] synchronously returns a fresh owned stage or preserves partial
    ownership through ValidationStage's exceptions. No independent async work
    may be started and then hidden by throwing before returning its promise.

    Materialize with the actual worker queue, check original/stage fences,
    invoke [validate] with ONLY the disposable candidate pathname, await its
    actual helper/worker settlement, then rehash the held snapshot and recheck
    fences before cleanup. A returned validation promise must cover every
    borrower it starts. Cancellation never retires active borrowers early.

    Uncertain cleanup retains the opaque owner and returns a permanently
    pending promise, keeping the caller's admission charged. [on_retained] is
    diagnostic only; exceptions from it are suppressed without releasing work.
    No descriptor probe/retry or caller-asserted recovery API is provided.
    Whole-process closure/coordinated recovery is separate. This function does
    not select scan paths, acquire outer admission, or enable all-scanned. *)
val retained_owners : unit -> ValidationStage.t list
(** Owner-only diagnostic references; not settlement or release authority. *)
