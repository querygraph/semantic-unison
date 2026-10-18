(** Owner-loop slots for returned unit-domain handles. Each slot is prepared
    before spawn; adopting the returned handle allocates no option/list node. *)
type slot
type state = Empty | Held | Uncertain | Joined
exception Join_uncertain of slot
val prepare : unit -> slot
val adopt : slot -> unit Domain.t -> unit
(** Single transfer. Caller must not join the handle after transfer or adopt it
    in another slot. No placeholder is ever interpreted as a domain handle. *)
val join : slot -> unit
val join_all : slot array -> unit
(** Each Held slot gets one join attempt; other slots are never retried.
    join_all attempts all slots and raises a preallocated carrier if any join
    is uncertain. Caller must retain the entire array, not only the carrier. *)
val state : slot -> state
val cause : slot -> exn option
(** Join exceptions are conservative uncertainty, including errors delivered
    after actual domain termination. No reset or raw-handle retry API. The API
    does not cover failures inside Domain.spawn before it returns a handle. *)
