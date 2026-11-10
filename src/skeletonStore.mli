(* Unison file synchronizer: src/skeletonStore.mli *)
(* The store of skeleton versions: the last few replaced versions of a file,
   each kept as its skeleton, the skeletons of one file stored as deltas
   against one another.  Plain path names throughout; Stasher drives it and
   the unison-skeleton tool reads it.  See docs/skeleton-versions.md. *)

type kind = Skel | Whole
type stored = Full | Delta of int | File

type version = {
  seq : int;            (** the version's number; never reused for a path *)
  time : float;         (** when it was replaced *)
  size : int;
  sha256 : string;      (** of the content, in hex *)
  kind : kind;
  format : string;      (** ["tiff"], ["jpeg"], ["whole"]; ["-"] for a whole file *)
  record_sha256 : string;
  record_bytes : int;
  stored : stored;
  stored_bytes : int;
}

type chain = {
  path : string;
  next : int;
  pending : (int * float) option;
  versions : version list;   (** oldest first *)
}

type outcome =
  | Nothing
  | Unchanged
  | Kept_skeleton of int * int   (** version, bytes of kept blocks it added *)
  | Kept_whole of int * string   (** version, why it is not a skeleton *)

val root_dir : store:string -> root:string -> string
(** The directory of a replica root inside the store. *)

val stash :
  store:string -> root:string -> path:string -> file:string ->
  how:[ `Move | `Copy ] -> ?clone:(string -> string -> bool) -> depth:int -> unit -> bool
(** Take [file], the current content of [path], as a pending item before it is
    replaced ([`Copy]) or deleted ([`Move]: renamed away when possible).  A
    pending item left by an earlier run is settled first.  [clone src dst] may
    make the copy cheaply and return [true].  Returns whether [file] was moved
    away.  Any failure is raised and nothing is recorded as kept. *)

val settle :
  store:string -> root:string -> path:string -> live:string -> ?gone:bool ->
  depth:int -> unit -> outcome
(** Turn the path's pending item into a version: save the blocks [live] (the
    file now at the path) lacks, rebuild the pending content from the store
    and [live], check its SHA-256, and only then delete the pending file.
    Whatever cannot be kept that way is kept as a whole file.  With [gone] the
    path has no file any more.  Versions beyond [depth] are pruned. *)

val settle_all :
  store:string -> root:string -> ?under:string -> live:(string -> string) ->
  depth:int -> unit -> (string * outcome) list * (string * string) list
(** Settle the pending items of a root, all or those at or under a path.
    The second list is the paths that stay pending, with the reason. *)

val pending_paths : store:string -> root:string -> string list
val paths : store:string -> root:string -> string list
val chain : store:string -> root:string -> path:string -> chain option

val stored_bytes : store:string -> root:string -> path:string -> int * int * int
(** Bytes held for a path: (index and skeleton records, kept blocks, whole
    and pending files). *)

val restore :
  store:string -> root:string -> path:string -> live:string option -> seq:int ->
  write:(string -> int -> int -> unit) -> reset:(unit -> unit) -> unit
(** Write a kept version's content.  [reset] is called when what was written
    so far must be discarded.  Raises [Failure] unless the SHA-256 of what was
    written is the version's. *)

val verify :
  store:string -> root:string -> path:string -> live:string option ->
  (version * string option) list
(** Rebuild every kept version to nowhere; [None] for one that is exact. *)

val sha_of_file : string -> string

val before_check : (unit -> unit) ref
(** For tests: called before a new skeleton version is rebuilt and checked. *)
