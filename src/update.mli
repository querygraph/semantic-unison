(* Unison file synchronizer: src/update.mli *)
(* Copyright 1999-2020, Benjamin C. Pierce (see COPYING for details) *)

module NameMap : MyMap.S with type key = Name.t

type archive =
    ArchiveDir of Props.t * archive NameMap.t
  | ArchiveFile of Props.t * Os.fullfingerprint * Fileinfo.stamp * Osx.ressStamp
  | ArchiveSymlink of string
  | NoArchive

val marchive : archive Umarshal.t

(* Calculate a canonical name for the set of roots to be synchronized.  This
   will be used in constructing the archive name for each root. Note, all
   the roots in this canonical name will contain hostnames, even local
   roots, so the roots are re-sorted. *)
val storeRootsName : unit -> unit

(* Retrieve the actual names of the roots *)
val getRootsName : unit -> string

(* Perform update detection. Optionally, takes as input the list of
   paths known not to be synchronized and a list of paths not to
   check. Returns structures describing dirty files/dirs (1 per path
   given in the -path preference). An option controls whether we
   would like to use the external filesystem monitoring process. *)
val findUpdates :
  ?wantWatcher:bool ->
  (Path.t list * Path.t list) option ->
  ((Path.local * Common.updateItem * Props.t list) *
      (Path.local * Common.updateItem * Props.t list)) list

val findLocalWithValidation :
  max_files:int -> max_path_bytes:int -> bool -> Fspath.t -> Path.t list ->
  (Path.t list * Path.t list) option ->
  (Path.local * Common.updateItem * Props.t list) list * Path.local list
(** Internal endpoint scan entry; archives/root setup must already be loaded.
    Collects regular files during real selected traversal, including unchanged
    and immutable files; bypasses watcher/directory coverage shortcuts. Existing
    immutable update results remain unchanged. This collection entry invokes no
    helpers; the opted-in find RPC awaits a separate private validation phase.
    Limits abort rather than return partial coverage. *)

(* Take a tree of equal update contents and update the archive accordingly. *)
val markEqual :
  (Name.t * Name.t, Common.updateContent * Common.updateContent) Tree.t -> unit

val getSubArchiveLocal : Path.t -> archive
(* Get and update a part of an archive (the archive remains unchanged) *)
val updateArchive : Fspath.t -> Path.local -> Common.updateItem -> archive
val makeArchive : Common.updateItem -> archive
(* Replace a part of an archive by another archive *)
val replaceArchive : Common.root -> Path.t -> archive -> unit Lwt.t
val replaceArchiveLocal : Fspath.t -> Path.local -> archive -> unit
(* Update only some permissions *)
val updateProps :
  Fspath.t -> 'a Path.path -> Props.t option -> Common.updateItem -> unit

(* Check that no updates has taken place in a given place of the filesystem *)
(* Returns an archive mirroring the filesystem contents *)
val checkNoUpdates :
  ?fastCheck:bool -> Fspath.t -> Path.local -> Common.updateItem -> archive

(* Turn off fastcheck for the given file on the next sync. *)
val markPossiblyUpdated : Fspath.t -> Path.local -> unit

(* Save to disk the archive updates *)
val commitUpdates : unit -> unit

(* In the user interface, it's helpful to know whether unison was started
   with no archives.  (Then we can display file status as 'unknown' rather
   than 'new', which seems friendlier for new users.)  This flag gets set
   false by the crash recovery code when it determines that no archives were
   present. *)
val foundArchives : bool ref

(* Unlock the archives, if they are locked. *)
val unlockArchives : unit -> unit Lwt.t

(* Translate a global path into a local path using the archive *)
val translatePath : Common.root -> Path.t -> Path.local Lwt.t
val translatePathLocal : Fspath.t -> Path.t -> Path.local

(* Are we checking fast, or carefully? *)
val useFastChecking : unit -> bool

(* Print the archive to the current formatter (see Format) *)
val showArchive: archive -> unit

(* Compute the size of an update *)
val updateSize : Path.t -> Common.updateItem -> int * Uutil.Filesize.t

(* Iterate on all files in an archive *)
val iterFiles :
  Fspath.t -> Path.local -> archive ->
  (Fspath.t -> Path.local -> Os.fullfingerprint -> unit) -> unit

(* (For breaking the dependency loop between update.ml and stasher.ml...) *)
val setStasherFun : (Fspath.t -> Path.local -> unit) -> unit

(* Conjoin the canonical name of the current host and the canonical
   presentation of the current fspath with the list of names/fspaths of
   all the roots and the current archive format *)
val archiveHash : Fspath.t -> string

val component_owner_namespace : Fspath.t -> (int * int) option
val component_owner_reference : Fspath.t -> (string * string) option
val load_component_owner_index : ?check_cancel:(unit -> unit) -> Fspath.t ->
  directory:Unix.file_descr -> max_entries:int -> max_bytes:int -> unit ->
  DngComponents.owner_index option
(** Authenticate managed metadata using only this loaded root's trusted optional
    archive reference. Disabled/unloaded/missing hints return None without touching
    the supplied directory. Otherwise use the managed loader's strict digest-name,
    ownership, bounds and retained-close-error contract. The directory is borrowed;
    caller supplies stable private namespace/IO/memory/lifetime admission. This
    neither opens a namespace root nor adopts/rewrites archive or file state. *)
val set_component_owner_reference : Fspath.t -> DngComponents.owner_index_publication -> unit
val adopt_component_cache_store : Fspath.t -> expected_reference:(string * string) option ->
  DngComponents.managed_cache_store -> unit
(** Owner-loop compare-and-replace of the loaded archive hint. Requires a fully
    normally settled managed store and an unchanged expected reference. Memory
    only: the ordinary archive transaction must still commit. Caller serializes
    root ownership; refusal preserves published orphans and the old hint. *)
val clear_component_owner_reference : Fspath.t -> unit
(** Owner-loop opt-in local component-manifest hints. Getter returns
    (manifest binding,digest) from this loaded root's trusted archive context.
    Setter requires normally completed publication and caller-proven FD/reference
    settlement; it changes memory only. The ordinary archive transaction commits
    the optional hint, which never becomes file/reconciliation authority. Clear
    neither removes cache files nor refunds native quota. Default off; no automatic
    capture/reuse. Optional hints follow the paths tail, not legacy properties. *)

val inspect_cached_components : ?check_parent:(unit -> unit) -> Fspath.t -> parent:Unix.file_descr -> path:Fspath.t ->
  generation_sha256:string -> pool:SemanticWorkers.t -> cancellation:HelperSupervisor.cancellation ->
  decoders:DngComponents.decoders -> max_read_bytes:int64 -> Unix.file_descr ->
  SemanticWorkers.component_inspection option Lwt.t
(** Endpoint-owner report orchestration. Parent/source remain exclusively borrowed
    through the await; namespace/leaf FDs close before it. Loaded archive owns hints;
    legacy no-identity hints stay cold. Full-input worker verification still applies.
    Source/head fences precede one-use store and guarded memory adoption. Quota
    exhaustion preserves the report; corruption/uncertain ownership propagates.
    Caller supplies stable generation and later normal archive commit; no discovery,
    source opening, decoder loading or synchronization decision is authorized. *)

val inspect_configured_components : Fspath.t -> Fspath.t -> pool:SemanticWorkers.t ->
  cancellation:HelperSupervisor.cancellation -> decoders:DngComponents.decoders ->
  max_read_bytes:int64 -> Unix.file_descr -> SemanticWorkers.component_inspection option Lwt.t
(** Opt-in local report worker with explicit componentcacheparent. Parent survives
    worker await and transfers into nested uncertainty. Empty/off remains uncached.
    Epoch selects a candidate only; worker still authenticates complete input. *)
