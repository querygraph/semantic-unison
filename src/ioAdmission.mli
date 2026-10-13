(** Endpoint-local, owner-loop admission for known filesystem I/O work.
    Keys are ephemeral [fstat.st_dev] accounting groups, not physical disks,
    persistent volume identities, mount lifetimes or security authorities.
    This gate limits concurrent jobs per key, not bytes, RSS or descriptors. *)
type t
type usage = {
  active_jobs : int;
  pending : int;
  peak_jobs : int;
  peak_per_device : int;
  devices : (int * int) list;
}
exception Failed of string

val create : per_device:int -> max_pending:int -> t
(** Positive limits are required. There is no independent global active-job
    limit; callers also use the shared CPU/transaction budgets. *)

val usage : t -> usage
(** [devices] is the sorted ledger of active keys only. Idle keys are removed;
    the aggregate peaks do not retain a per-device historical cache. *)

val devices_of_fds : Unix.file_descr list -> int list
(** Fresh [Unix.LargeFile.fstat] of one or two borrowed descriptors, returning
    sorted distinct [st_dev] keys. Opens/closes/duplicates/seeks none. Keep the
    descriptors alive and unreassigned during this call and the admitted job.
    Native errors propagate unchanged. On the qualified 64-bit macOS platform
    the native 32-bit device value fits OCaml's integer representation; this is
    not proof of every other platform's native identity representation. *)

val with_devices : t -> HelperSupervisor.cancellation -> devices:int list ->
  (unit -> 'a Lwt.t) -> 'a option Lwt.t
(** Atomically reserve one credit on each of one or two distinct keys, before
    CPU admission. Duplicate keys consume one credit. Conflicting requests
    preserve FIFO order; requests disjoint from earlier blocked requests may
    bypass them. More than two distinct keys or no keys is [Invalid_argument].
    A full waiting queue fails with [Failed] before the callback starts.

    Queued cancellation removes the ticket synchronously. Starts following
    release/cancellation are deferred until an owner yield, so a connection's
    cleanup sweep cannot start another borrower inline. [None] means cancelled
    before the callback starts. Active leases remain until the callback settles,
    including failure/cancellation. The callback must settle all workers/children
    borrowing its resources before returning. Never nest leases from this gate,
    hold one across RPC waits, or wrap an operation that invokes its own admitted
    inspections. All calls, including cancellation, belong to the legacy owner. *)
