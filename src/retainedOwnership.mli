(** Owner-loop retention of recognized unresolved resource ownership.
    This does not discover OS settlement or impose resource limits. *)
type entry
val guard : is_uncertain:(exn -> bool) -> ?on_retained:(entry -> unit) ->
  (unit -> 'a Lwt.t) -> 'a Lwt.t
(** Prepare evidence and an unsettled reply before invoking work. Recognized
    ownership failure, classifier failure or a still-sleeping borrower keeps
    the returned promise unsettled and roots its evidence for process lifetime.
    Inspect the actual returned promise even if an observer-installation error
    is the error delivered by BorrowedWork. Neither cancellation nor an ordinary
    mapping is a release proof. The classifier must be pure/owner-only.
    Retention callback runs after rooting; its errors cannot release ownership. *)
val count : unit -> int
val iter : (entry -> unit) -> unit
val cause : entry -> exn
val reported_error : entry -> exn
val classification_error : entry -> exn option
val borrowed_pending : entry -> bool
val reply_sleeping : entry -> bool
(** Diagnostic only. No clear, wakeup, numeric close retry or release API. *)
