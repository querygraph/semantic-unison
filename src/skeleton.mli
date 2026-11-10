(* Unison file synchronizer: src/skeleton.mli *)
(* Skeletons of classic TIFF (DNG and TIFF-based raws) and JPEG files: every
   byte outside a file's large blocks, and a map of the blocks.  The cuts are
   those of the dng-compare archive specification, section 13.1.
   See docs/skeleton-versions.md. *)

val block_min : int
val gap : int
val mark_bytes : int
val pad : int
val whole : int

type block = { at : int; len : int; mark : string; role : string }

type t = { format : string; size : int; blocks : block list; bytes : string }
(** [format] is ["tiff"], ["jpeg"] or ["whole"]; [bytes] is every byte outside
    the blocks, in file order.  A skeleton without blocks is its content. *)

val no_walker : string

val build : string -> t
(** The skeleton of the file at a path.  Raises [Failure] when the file has no
    walker and is larger than [whole], or cannot be read. *)

val build_fd : Unix.file_descr -> int -> t

val with_file : string -> (Unix.file_descr -> int -> 'a) -> 'a
(** Run a function on a file opened for reading and its size. *)

val read_at : Unix.file_descr -> int -> int -> string

val walk : Unix.file_descr -> int -> string * (int * int * string) list
(** Format and blocks as (offset, length, role), in file order.  Raises
    [Failure] for a file that is neither a classic TIFF nor a JPEG. *)

val mark : Unix.file_descr -> int -> int -> string
(** First 32 hex digits of the SHA-256 of a block's first and last
    [mark_bytes] bytes (of the whole block when no longer than twice that). *)

val marked_blocks : Unix.file_descr -> int -> (int * string * int) list
(** Blocks as (length, mark, offset); none for a file without a walker. *)
