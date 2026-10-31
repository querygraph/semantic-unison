(* Hooks through which a packed root (PackdirConfig, PackdirSupport) answers
   for paths stored in .sqlar containers: Fileinfo asks [stat], Os asks
   [children] and [fingerprint] first. Each answers None for any path it does
   not own, and the real filesystem is used; by default they own nothing. *)

(* Stat of a path a container stands for: a container as its directory, a
   member as its file. *)
let stat : (Fspath.t -> Path.local -> Unix.LargeFile.stats option) ref = ref (fun _ _ -> None)

(* The names under a directory, when containers change them: a parent lists a
   container X.sqlar as X; a container lists its members and any plain files
   kept beside it. *)
let children : (Fspath.t -> Path.local -> string list option) ref = ref (fun _ _ -> None)

(* A member's stored fingerprint (MD5 of its bytes, raw). *)
let fingerprint : (Fspath.t -> Path.local -> string option) ref = ref (fun _ _ -> None)
