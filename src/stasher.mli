(* Unison file synchronizer: src/stasher.mli *)
(* Copyright 1999-2020 (see COPYING for details) *)

(* This module maintains backups for general purpose and *)
(* as archives for mergeable files. *)

(* Make a backup copy of a file, if needed; if the third parameter is
   `AndRemove, then the file is either backed up by renaming or else
   deleted if no backup is needed. *)
val backup:
  Fspath.t -> Path.local ->
  [`AndRemove | `ByCopying] -> Update.archive -> unit

(* Skeleton versions (preferences skeleton, skeletonnot, maxskeletons,
   skeletondir; docs/skeleton-versions.md).  [backup] takes a selected file
   that is about to be replaced as a pending item of the skeleton store;
   call [settleSkeletons] once the replacement is in place at the path.  It
   never fails: an item it cannot settle stays in the store, whole. *)
val settleSkeletons : Fspath.t -> Path.local -> unit

(* Where skeleton versions are kept *)
val skeletonDirectory : unit -> string

(* Low-level skeletondir preference *)
val skeletondir : string Prefs.t

(* Stashes of current versions (so that we have archives when needed for merging) *)
val stashCurrentVersion:
      Fspath.t                (* fspath to stash *)
   -> Path.local              (* path to stash *)
   -> Path.local option       (* path to actual bits to be stashed (used to stash an
                                 additional archive version in addition to the current version) *)
   -> unit

(* Retrieve a stashed version *)
val getRecentVersion:
       Fspath.t
    -> Path.local
    -> Os.fullfingerprint
    -> Fspath.t option

(* Return the location of the backup directory *)
val backupDirectory : unit -> Fspath.t

(* Check whether current version of a path is being stashed *)
val shouldBackupCurrent : Path.t -> bool

(* Low-level backupdir preference *)
val backupdir : string Prefs.t

(* Initialize the module *)
val initBackups: unit -> unit
