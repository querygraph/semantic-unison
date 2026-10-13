(** Bounded child-process supervision on the legacy Lwt owner loop.

    All calls, including cancellation and permit acquisition, belong to that
    loop. Domain workers must send requests/completions through the owner's
    mailbox; they must not call this module or legacy Lwt directly. Waiting for
    a child never occupies an OCaml domain. The POSIX backend uses posix_spawn,
    not fork, and a separate process group. Native Windows is unsupported. *)

type t
type cancellation

val available_cpus : unit -> int
(** Online logical CPU count, at least one. Native Windows currently returns
    one; its helper backend is unsupported. *)

val available_physical_cpus : unit -> int
(** On macOS, [hw.physicalcpu] capped by [available_cpus]. If the query is
    unavailable, invalid, or on another platform, return [available_cpus]. This
    is at least one and makes no physical-topology claim on other platforms. *)

val cancellation : unit -> cancellation
val cancel : cancellation -> unit
val cancel_and_cleanup : cancellation -> unit
(** Exceptional owner-loop teardown, for synchronous connection-close cleanup:
    cancel pending admission, immediately SIGKILL active helper groups, reap
    direct children, close pipes, and release their permits exactly once.
    This does not require another Lwt tick. It may briefly block while the OS
    reaps a killed child; uninterruptible OS waits are not time-bounded.
    Ordinary [cancel] retains asynchronous TERM/grace/KILL behavior. Domain-job
    CPU permits are never released early. Active helpers also have an at_exit
    safeguard, covering normal process exit when connection hooks do not run.
    Neither safeguard can run if Unison itself receives SIGKILL. *)
val is_cancelled : cancellation -> bool
val on_cancel : cancellation -> (unit -> unit) -> (unit -> unit)
(** Owner-loop callback, invoked synchronously on first cancellation (or
    immediately if already cancelled). Returns an unregister function.
    Callbacks must be short, nonblocking, non-raising, and must not run Lwt.
    Intended for propagating cancellation to a worker's Atomic flag even when
    the owner event loop will not tick again. Finished jobs must unregister. *)

val create : cpu_permits:int -> max_children:int -> max_pending:int -> t
val usage : t -> int * int
(** Currently reserved CPU permits and active child slots. A helper's weight
    must include its internal native threads. *)

val with_cpu_permits :
  t -> weight:int -> cancellation -> (unit -> 'a Lwt.t) -> 'a option Lwt.t
(** Share the budget with future domain jobs. None means cancelled before
    admission. Once admitted, the function must honor cancellation itself and
    must not return before its CPU work finishes. Permits are released on both
    success and failure. FIFO admission; nested acquisition can deadlock. *)

type limits = {
  timeout : float;
  terminate_grace : float;
  stdout_bytes : int;
  stderr_bytes : int;
}

type outcome =
  | Completed
  | Cancelled
  | Timed_out
  | Output_limit
  | Failed of string

type result = {
  outcome : outcome;
  status : Unix.process_status option;
  stdout : string;
  stderr : string;
  output_truncated : bool;
  elapsed : float;
}

val run :
  t -> weight:int -> cancellation -> limits:limits ->
  executable:string -> arguments:string array -> environment:string array ->
  result Lwt.t
(** [arguments] excludes argv[0]. The executable must be absolute. There is no
    shell, stdin is /dev/null, and output pipes are drained together with bounded
    work per owner-loop turn. Exceeding either output cap terminates the group.
    Timeout measures execution after admission, not time in the admission queue.
    Completion is returned only after reaping the direct child. Descendants that
    deliberately escape the process group are outside this contract; this is
    not a sandbox or a memory-limit implementation. *)
