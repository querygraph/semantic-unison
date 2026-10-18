(** Owner-loop admission for retained semantic resources, separate from CPU
    permits. Payload credits estimate retained proof/encoding buffers; they
    are not a process RSS cap. Descriptor credits cover owned/worker duplicates,
    not unrelated legacy transfers or an external helper's descriptors. *)
type t
type reservation
type role = Source | Consumer
type cost = { payload_bytes : int; descriptors : int }
type usage = {
  transactions : int; pending : int; payload_bytes : int; descriptors : int;
  peak_transactions : int; peak_payload_bytes : int; peak_descriptors : int;
}
type accounting = {
  baseline:cost; workspace:cost; workspace_peak:cost;
  total_reserved:cost; peak_reserved:cost; capacity:cost;
}
(** Reserved planning costs, never OS live/peak measurements. A fixed baseline
    remains reserved for the gate lifetime, even before initialization or after
    known shutdown of its infrastructure. Existing [usage] remains workspace-only. *)
val accounting : t -> accounting
val create_with_baseline : baseline:cost -> source_headroom:cost option ->
  max_transactions:int -> max_payload_bytes:int -> max_descriptors:int ->
  max_pending:int -> t
(** Total capacities include the immutable baseline, which is subtracted before
    any source/workspace grant. [create] preserves its zero-baseline semantics. *)
exception Failed of string
val create : source_headroom:cost option -> max_transactions:int -> max_payload_bytes:int ->
  max_descriptors:int -> max_pending:int -> t
val usage : t -> usage
val make_reservation : t -> role:role -> cost:cost -> reservation
(** Allocate the caller's single-use owner before any admission debit. This
    does not acquire credits. The caller must retire it on every failed handoff. *)
val acquire : reservation -> HelperSupervisor.cancellation -> bool Lwt.t
(** Acquire the preallocated owner. False means cancelled before admission.
    Queued cancellation removes its request synchronously. *)
val reservation_cost : reservation -> cost
val reservation_role : reservation -> role
val is_held : reservation -> bool
val retire : reservation -> unit
(** Idempotent revocation. Credits remain held until an active workspace settles.
    Close all owner-native resources before retiring the reservation. *)
val with_borrow : reservation -> cost:cost -> (unit -> 'a Lwt.t) -> 'a Lwt.t
(** Borrow one serialized workspace inside the retained envelope. Does not
    acquire another transaction, debit again or wait for an upgrade. Rejects
    overlapping, revoked or oversized work before dispatch. The callback must
    settle every operation using its resources. Exceptional waiter-allocation
    recovery polls the existing computation; persistent allocation failure is
    outside the recoverability guarantee. Owner-loop calls only. *)
val with_lease : t -> HelperSupervisor.cancellation -> role:role -> cost:cost ->
  (unit -> 'a Lwt.t) -> 'a option Lwt.t
(** FIFO within each role, with a bounded combined pending queue. Consumers
    leave one transaction and [source_headroom] credits available to a source.
    Sources have admission priority so peer-dependent consumers cannot block
    the source needed for bidirectional progress. None means cancellation before [f]
    starts. Queued cancellation removes the ticket synchronously. An admitted
    lease stays reserved until [f] settles, including failure and cancellation;
    [f] must stop/settle every operation borrowing its resources. Never nest
    leases from the same gate. All calls belong to the legacy owner loop. *)
