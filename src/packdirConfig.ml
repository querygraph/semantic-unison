(* Packed directories (docs/packdir-design.md): on one local, receiving root,
   every directory exactly [packdepth] levels down is stored as one SQLite
   archive D.sqlar instead of a directory of files. This module holds the
   preferences and the packed root's archive signature; the checks that need
   the roots and the force preference are in Uicommon, and the containers in
   PackdirSupport. *)

let depth =
  Prefs.createInt "packdepth" 0 ~local:true
    ~category:(`Advanced `General)
    "store directories this many levels under the packed root as .sqlar containers (0: off)"
    "With a positive value N and \\texttt{packroot}, every directory exactly N \
     levels under the packed root is stored there as one SQLite archive \
     D.sqlar holding D's files, and Unison synchronizes its members as files. \
     The packed root must be local and receive only (\\texttt{force} names the \
     other root). See docs/packdir-design.md."

let root =
  Prefs.createString "packroot" "" ~local:true
    ~category:(`Advanced `General)
    "the root that stores packed directories (with packdepth)"
    "One of the two roots, as given or by a unique prefix or suffix, like \
     \\texttt{force}. Only this root stores containers."

let barrier_gib =
  Prefs.createInt "packbarrier" 4 ~local:true
    ~category:(`Advanced `General)
    "GiB written between drive-cache flushes on the packed root"
    "Containers are synced with fsync; one F_FULLFSYNC every this many GiB and \
     at the end of a run empties the drive's cache, and the archive records a \
     container only after a flush covers it. 0 flushes after every container \
     write."

let max_gib =
  Prefs.createInt "packmax" 4 ~local:true
    ~category:(`Advanced `General)
    "largest container, in GiB; a container that would grow past it is refused"
    "Guards against a pattern that packs far more than intended."

let enabled () = Prefs.read depth > 0

(* The packed root's fspath, set by Uicommon once the roots are checked. *)
let packed : Fspath.t option ref = ref None

let is_packed fspath = match !packed with Some p -> p = fspath | None -> false

(* Mixed into both roots' archive identities whenever a root is packed, so
   that a run without the same packdir setting never reads these archives: it
   would see no member files on the packed root and take them all for
   deletions, and it would rewrite the plain root's archive under it. *)
let signature (_ : Fspath.t) =
  match !packed with
  | Some p -> Printf.sprintf ";packdir=depth%d:%s" (Prefs.read depth) (Fspath.toString p)
  | None -> ""

(* Called by Update.commitUpdates: [before_commit] before Unison's archives are
   written (the final drive-cache barrier, so they never get ahead of the
   platter), [after_commit] once they are (the pending list is cleared). *)
let before_commit : (unit -> unit) ref = ref (fun () -> ())
let after_commit : (unit -> unit) ref = ref (fun () -> ())
