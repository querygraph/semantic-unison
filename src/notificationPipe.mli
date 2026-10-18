(** Owner-loop, single-attempt ownership of a worker notification pipe or a
    single scheduling read descriptor.
    This ledger does not prove domain joins or impose aggregate FD limits. *)
type t
exception Uncertain of t
val prepare : unit -> t
(** Allocate the ledger, carrier and retention link before acquiring the pipe. *)
val adopt_read : t -> Unix.file_descr -> unit
(** Transfer one read descriptor; the absent writer is never closed. *)
val adopt : t -> Unix.file_descr -> Unix.file_descr -> unit
(** Transfer both endpoints exactly once, immediately after pipe returns. *)
val install_reader : t -> Lwt_unix.file_descr -> unit
(** Install the wrapper before registering any reader operation. If installation
    allocation fails, the raw endpoint remains owned and has no registrations. *)
val keep_owner : t -> (unit -> unit) -> unit
(** Keep additional caller evidence reachable after an uncertain close. Prepare
    this callback before launching/registering work; it is never invoked. *)
val remember_failure : t -> exn -> unit
val close_read : t -> unit
val close_write : t -> unit
val close_all : t -> unit
(** Consume each close authority before entering the close API. A thrown close
    is conservative uncertainty even if the kernel already closed the FD.
    Subsequent calls never retry historic numeric descriptors. close_all attempts
    both endpoints and preserves both failures. Unknown ledgers remain rooted. *)
val settled : t -> bool
val read_cause : t -> exn option
val write_cause : t -> exn option
val operation_cause : t -> exn option
val descriptors : t -> Unix.file_descr * Unix.file_descr
(** Historical identifiers only, never authority to retry close. *)
val retained_count : unit -> int

val read_identity : t -> Unix.LargeFile.stats option
val write_identity : t -> Unix.LargeFile.stats option
val read_identity_error : t -> exn option
val write_identity_error : t -> exn option
(** Last pre-close observation or its failure, not a post-close binding proof. *)

val retain_unsettled : t -> exn -> 'a
(** Root remaining ownership when stop/join or another lifecycle operation is
    unresolved. Does not close endpoints; preserves the separate original cause. *)
val lifecycle_cause : t -> exn option

val read_held : t -> bool
val write_held : t -> bool
(** Known local close authority remains unconsumed. False is not an OS close
    proof: uncertain endpoints must be inspected separately through causes. *)
