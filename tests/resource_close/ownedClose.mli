(** Candidate single-attempt descriptor ownership, not yet worker-integrated.
    Prepare all slots and the group before acquiring descriptors. Never discard
    a group with held or uncertain slots; neither an ordinary operation failure
    nor cancellation proves close settlement. *)
module type Operations = sig
  type descriptor
  val empty : descriptor
  val close : descriptor -> unit
end
module Make (Operations : Operations) : sig
  type slot
  type group
  type state = Empty | Held | Uncertain | Settled
  val prepare : label:string -> slot
  val group : slot array -> group
  (** Copies the array before any ownership acquisition. Duplicate slots refuse. *)
  val adopt : slot -> Operations.descriptor -> unit
  (** Exactly one acquisition per prepared slot; no allocation on success.
      Caller must not close or transfer the descriptor after adoption. *)
  val close_all : group -> unit
  (** Attempts each Held slot at most once, including after another close fails.
      Any uncertain slot causes the group's preallocated exception to be raised.
      Subsequent calls never retry uncertain or settled numeric descriptors. *)
  val state : slot -> state
  val label : slot -> string
  val cause : slot -> exn option
  val settled : group -> bool
  val owns_exception : group -> exn -> bool
  (** The exception identifies this retained group; it proves no OS settlement. *)
end
