type t
exception Invalid of string
val with_fd : ?check_cancel:(unit -> unit) -> Unix.file_descr -> (t -> 'a) -> 'a
(** Duplicates a caller-owned regular descriptor. Use only in one worker;
    the duplicate shares its file position with the original descriptor.
    The optional worker-local cancellation check runs before opening, reading,
    each 64 KiB iteration, and final stability checks. *)
val size : t -> int64
val check : t -> unit
val same_inode : t -> Unix.file_descr -> bool
val read : t -> int64 -> int -> string
(** Checked, exact read, at most 1 MiB per call. *)
val iter : t -> int64 -> int64 -> (bytes -> int -> unit) -> unit
val digest : t -> string
