(* The SQLite guard: only a quiet database is synchronized.
   See docs/sqlite-semantic-design.md, "The guard".

   A database is the group X, X-journal, X-wal, X-shm.  It is quiet when the
   main file alone is the whole database.  The guard reads headers and, for a
   write-ahead log, its frames; it never writes, locks or opens a database
   through SQLite. *)

(* What was found beside a file. *)
type state =
  | Not_database
      (* No SQLite header: an ordinary file, not guarded. *)
  | Quiet
  | Redundant_wal of int
      (* A write-ahead log whose committed frames (their number) all equal the
         main file's pages.  Quiet for sending; the file must still not be
         replaced under it. *)
  | Busy of string
      (* Not quiet, with the reason, naming the file that shows it. *)

(* Inspect the database at [root]/[path], whatever the preferences say.
   Raises [Util.Transient] if the files cannot be read. *)
val inspect : Fspath.t -> Path.local -> state

(* [guarded path] is true when the guard is in force for this run (both hosts
   offer it and [sqlitequiet] is not [off]) and [path] matches [sqlitedb]. *)
val guarded : 'a Path.path -> bool

(* [companion path] is true when [path] is X-journal, X-wal or X-shm for an X
   that matches [sqlitedb], or the marker file [sqlitemarker] names for such
   an X, and both hosts offer the guard.  Such paths are never propagated:
   [Globals.shouldIgnore] returns true for them. *)
val companion : string -> bool

(* The file at [root]/[path] is about to be read as the version to propagate,
   or has just been.  Under [sqlitequiet = require] a database that is not
   quiet raises [Util.Transient] with the reason; under [warn] it is reported
   and the call returns. *)
val check_sending : Fspath.t -> Path.local -> unit

(* The file or directory at [root]/[path] is about to be replaced or deleted.
   Refuses, as [check_sending] does, a database with a hot journal or a
   write-ahead log holding any valid frame, anywhere under [path], and a path
   that [check_held] refuses. *)
val check_receiving : Fspath.t -> Path.local -> unit

(* [path], existing or not, is named by [sqliteheld] for a database beside it
   that is not quiet: refused as [check_sending] refuses the database. *)
val check_held : Fspath.t -> Path.local -> unit

(* The preferences, for documentation and tests. *)
val sqlitedb : Pred.t
val sqlitequiet : string Prefs.t
val sqlitemarker : Pred.t
val sqliteheld : Pred.t
