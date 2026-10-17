(** Isolated maintained-library adapter candidate. Not production-selected.
    Each mutable context belongs to one owner/domain; never share it concurrently. *)
type t
val create : unit -> t
val feed : t -> bytes -> int -> int -> unit
val finish : t -> string
val version : unit -> string
