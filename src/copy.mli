
(* Transfer a file from one replica to the other *)
val file :
    Common.root         (* root of source *)
 -> Path.local          (* path of source *)
 -> Common.root         (* root of target *)
 -> Fspath.t            (* fspath of target *)
 -> Path.local          (* path of target (temp location) *)
 -> Path.local          (* path of "real" (original) target *)
 -> [`Update of (Uutil.Filesize.t * Uutil.Filesize.t) | `Copy]
 -> Props.t             (* permissions for new file *)
 -> Os.fullfingerprint  (* fingerprint of file *)
 -> Fileinfo.stamp option (* source file stamp, if available *)
 -> Osx.ressStamp       (* resource info of file *)
 -> Uutil.File.t        (* file's index in UI (for progress bars) *)
 -> Fileinfo.basic Lwt.t (* information regarding the transferred file *)

val fileBound : token:string -> local_path:Path.local ->
    Common.root -> Path.local -> Common.root -> Fspath.t -> Path.local -> Path.local
 -> [`Update of (Uutil.Filesize.t * Uutil.Filesize.t) | `Copy]
 -> Props.t -> Os.fullfingerprint -> Fileinfo.stamp option -> Osx.ressStamp
 -> Uutil.File.t -> (Fileinfo.basic * TargetBinding.completion) Lwt.t
(** Additive producer-ticket variant. Retain the actual receiving output
    descriptor through planned changes, final hashing and source checking.
    Only explicit backend handoff returns [Legacy_backend]; identity errors
    remain terminal. [local_path] is the translated destination in its logical
    root, rather than the temporary basename. *)

val localFile :
    Fspath.t             (* fspath of source *)
 -> Path.local           (* path of source *)
 -> Fspath.t             (* fspath of target *)
 -> Path.local           (* path of target *)
 -> Path.local           (* path of "real" [original] target *)
 -> [`Update of (Uutil.Filesize.t * Uutil.Filesize.t) | `Copy]
 -> Props.t              (* permissions for new file *)
 -> Uutil.Filesize.t     (* fork length *)
 -> Uutil.File.t option  (* file's index in UI (for progress bars), if appropriate *)
 -> unit

val recursively :
    Fspath.t             (* fspath of source *)
 -> Path.local           (* path of source *)
 -> Fspath.t             (* fspath of target *)
 -> Path.local           (* path of target *)
 -> unit

val readPropsExtData :
    Common.root          (* root of source *)
 -> Path.local           (* path of source *)
 -> Props.t              (* props of source *)
 -> Props.x Lwt.t        (* props with all ext data included *)

val readPropsExtDataG :
    Common.root          (* root of source *)
 -> Path.t               (* path of source *)
 -> Props.t              (* props of source *)
 -> (Path.local option * Props.x) Lwt.t (* props with all ext data included
                                           and path translated to local path *)


type retained_clone
val retained_clones : unit -> retained_clone list
val retained_clone_cause : retained_clone -> exn
val retained_clone_native : retained_clone -> StagePublication.owned option
val retained_clone_descriptors : retained_clone -> Unix.file_descr list
(** Owner-loop diagnostics for bound local clone publication uncertainty.
    Its producer reservation and remaining raw/channel resources stay held.
    This is not retry, cleanup, or settlement authority. *)
