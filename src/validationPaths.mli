type t
exception Limit_exceeded of string
val create : max_files:int -> max_path_bytes:int -> t
val add : t -> Path.local -> unit
val paths : t -> Path.local list
(** Unique, case-sensitive endpoint-local paths in first-observed order.
    Both limits are checked before retaining an entry. A limit failure poisons
    the collector: subsequent adds/reads fail rather than returning a prefix.
    The byte limit bounds retained pathname bytes, not whole-process memory. *)
