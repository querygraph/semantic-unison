(** Owner-loop private snapshot lifetime. Does not acquire admission, start
    workers/helpers, create the parent directory or enable all-scanned mode. *)
type t
type uncertain_close = {
  descriptor : Unix.file_descr;
  before_close : Unix.LargeFile.stats option;
  error : exn option;
}
exception Unresolved_ownership of t
exception Cleanup_failed of exn
exception Preparation_failed of exn * exn
val create : directory:string -> source:string -> max_bytes:int64 -> t
(** Require an existing owned mode0700 nonsymlink parent and regular source.
    Open source read-only/nonblocking/close-on-exec, bind its visible name to
    the held inode, then exclusively create a distinct mode0600 stage. Names
    are collision avoidance, not authentication against the same UID. Source
    and directory ancestry are cooperative, not a hostile namespace sandbox. *)
val descriptors : t -> Unix.file_descr * Unix.file_descr
(** Borrow source/output until every worker/helper has actually settled. *)
val path : t -> string
(** Only this disposable path, never the original, may be passed to a helper.
    All owned descriptors are close-on-exec. No OS sandbox is established. *)
val check : t -> unit
(** Check parent, source name/descriptor epoch and stage name/inode. Use before
    materialization, before/after helper execution and before retirement.
    On macOS includes FileObservation's native descriptor epoch. Only the exact
    unsupported-platform ENOSYS uses cooperative OCaml stat timestamps. Other
    native observation failures never select a weaker check. Stage content
    hashing/mutation detection remains the validator's separate responsibility. *)
val retire : ?failure:exn -> t -> unit
(** Only after all borrowers settle. Remove only the still-bound owned name;
    never remove a replacement. Attempt every independent descriptor close once.
    Unknown close outcomes retain pre-close facts in [t], raise
    [Unresolved_ownership], and are never probed/retried by later calls.
    The caller MUST retain this owner and its admission/FD credits on uncertainty;
    throwing through an auto-releasing resource callback is not settlement.
    Pass an existing worker/helper failure to retain its original cause in the
    owner if cleanup becomes uncertain; the first cause is preserved.
    Known cleanup errors raise [Cleanup_failed] after descriptor attempts.
    Repeated calls do not retry unlink or close. No source writes/properties. *)
val uncertain_closes : t -> uncertain_close list
val original_failure : t -> exn option
