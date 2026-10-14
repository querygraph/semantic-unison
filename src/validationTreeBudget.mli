(** Owner-side structural bounds for one receiving validation tree snapshot.
    These count discovered entries and UTF-8 path bytes, not heap usage/RSS. *)
type t
exception Exceeded of string
val create : max_entries:int -> max_path_bytes:int -> t
(** Zero disables the corresponding limit. Negative limits are invalid. *)
val reserve : t -> prefix_bytes:int -> name_bytes:int -> unit
(** Charge one discovered path before buffering its name or constructing its
    Path object. [prefix_bytes] includes any separator. Failed charges do not
    alter counters. Arithmetic overflow fails even with disabled limits. *)
val usage : t -> int * int
val charge_metadata : t -> int -> unit
(** Charge serialized property/symlink bytes with the conservative retained
    multiplier. Their initial reading/serialization is not allocator-enforced. *)
val memory_enabled : t -> bool
val estimated_bytes : t -> int
val create_with_memory : max_memory_bytes:int -> max_entries:int -> max_path_bytes:int -> t
