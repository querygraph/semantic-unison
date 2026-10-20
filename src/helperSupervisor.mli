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
  child_pid : int option;
  stdout : string;
  stderr : string;
  output_truncated : bool;
  elapsed : float;
}

(** [child_pid] records the direct child identity after successful spawn, including
    cancellation/timeouts/failures after spawn. [None] means no successful spawn
    was recorded. It is historical diagnostic data, NEVER an owned process handle
    or authorization to signal a PID/group after return. [status = Some _] is the
    supervisor's observed direct-child wait status, not a descendant-group absence
    receipt. PID identity alone does not prove launch time or surviving ownership. *)

type process_limits = {
  launcher : string;
  descriptors : int;
  address_space_bytes : int64;
}
(** Trusted separately compiled local resource launcher. Zero disables a limit;
    at least one must be nonzero. Descriptor limits include stdin/out/err and
    must be at least three. Lower both soft and hard limits before target exec;
    inherited hard limits may be stricter. OS rejection fails before target
    execution. Address-space support/enforcement is platform-specific and is
    not qualified on macOS. No RSS, group-wide memory/FD or sandbox claim. *)

val run :
  ?argv0:string -> ?process_limits:process_limits ->
  ?observe_group:(int option -> unit) ->
  ?observe_alive:(int -> float -> unit) ->
  ?observe_teardown:(result -> unit) -> t -> weight:int -> cancellation -> limits:limits ->
  executable:string -> arguments:string array -> environment:string array ->
  result Lwt.t
(** [arguments] excludes argv[0]. The optional [argv0] preserves a generic
    program's caller-supplied invocation name; it defaults to [executable].
    The executable must be absolute. There is no
    shell, stdin is /dev/null, and output pipes are drained together with bounded
    work per owner-loop turn. Exceeding either output cap terminates the group.
    Timeout measures execution after admission, not time in the admission queue.
    Completion is returned only after reaping the direct child. Descendants that
    deliberately escape the process group are outside this contract; this is
    not a sandbox. An optional trusted launcher applies process limits in its own
    new process, preserving target argv/environment, PID and supervisor group.
    Launcher trust/pinning belongs to the owner caller. *)

(** [observe_group] is an optional owner-loop diagnostic callback, called only
    on the ordinary terminal-child path before its PID is released. [Some n]
    counts other members observed in the retained child's group on the qualified
    macOS backend; [None] means unsupported or failed observation. The callback
    may be absent on teardown/failure and is never validation or durable absence
    proof. Exceptions from it are ignored. It must not block, reap children,
    signal processes, or reenter supervision. Default execution does not allocate
    a group binding or query the process table. *)

(** [observe_teardown result] is optional diagnostics for a child settled by
    registered cleanup (cancellation or process exit), where the Lwt result may
    never be delivered. It runs synchronously after SIGKILL, an [observe_group]
    census and reap, with outcome [Cancelled]. It is never called on the
    ordinary or internal-failure paths, so a caller tracing both this and the
    returned result must suppress a duplicate. Exceptions from it are ignored;
    it must not block, signal, reap or reenter supervision. *)

(** [observe_alive pid monotonic_seconds] is optional owner-loop diagnostics,
    called only after the retained direct child is observed nonterminal. The
    timestamp precedes that census and comes from the same host monotonic clock
    as helper deadlines. Repeated samples can bound observed process lifetime,
    not actual CPU work, SDK decode activity or descendant/group settlement.
    Do not signal historical PIDs from these records. A throwing observer follows
    owned-child teardown; observations do not authorize resource release. *)
