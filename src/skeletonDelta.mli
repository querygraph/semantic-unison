(* Unison file synchronizer: src/skeletonDelta.mli *)
(* A small self-contained binary delta (COPY and INSERT against a base
   string), used to store successive skeletons of one file additively. *)

exception Corrupt of string

val make : base:string -> target:string -> string
(** A delta that [apply] turns back into [target], given the same [base]. *)

val apply : base:string -> delta:string -> string
(** Raises [Corrupt] on a malformed delta or one made against a base of
    another length.  The caller checks the result's SHA-256. *)

val add_varint : Buffer.t -> int -> unit
val read_varint : string -> int ref -> int
(** Little-endian base-128 numbers, as the delta and the skeleton record use
    them.  [read_varint] raises [Corrupt]. *)
