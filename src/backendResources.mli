(** Immutable owner-selected native backend declarations; not RSS enforcement. *)
type coverage = Accounting_only | Allocator_callbacks of string list | Address_space
type t
val none : t
val make : backend:string -> cpu_lanes:int -> covered_bytes:int ->
  uncovered_estimate:int -> descriptor_credits:int -> coverage:coverage -> t
val cpu_lanes : t -> int
val bytes : t -> int
val covered_bytes : t -> int
val uncovered_estimate : t -> int
val descriptors : t -> int
val coverage : t -> coverage
val backend : t -> string
val maximum : t list -> t
(** Componentwise maximum for sequential backends within one workspace. *)
val add_cost : t -> bytes:int -> descriptors:int -> int * int
(** Checked addition of backend requirements to existing workspace credits. *)

val equal : t -> t -> bool
