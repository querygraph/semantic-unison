(** Candidate owner-loop bridge. Caller retains [t] in its job ledger until
    known settlement; an unresolved promise alone is not a root for its owner. *)
module Make (Ownership : sig
  type group
  val close_all : group -> unit
  val settled : group -> bool
end) : sig
  type 'a t
  val prepare : Ownership.group -> 'a t
  val promise : 'a t -> 'a Lwt.t
  val finish : 'a t -> ('a, exn) result -> unit
  (** One completion only. Store the actual operation outcome before closing.
      Uncertain closes leave the promise sleeping, retaining borrowed admission
      rather than delivering an ordinary failure which would release it. *)
  val retained : 'a t -> bool
  val operation_outcome : 'a t -> ('a, exn) result
  val close_failure : 'a t -> exn option
end
