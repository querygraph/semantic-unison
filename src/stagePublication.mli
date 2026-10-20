(** Cooperative, endpoint-local publication of a completed private clone stage
    into its normal temporary name. This does not qualify a logical replica
    root, final live-file commit, content, properties or crash durability. *)

type t

val available : unit -> bool
(** Native implementation is currently macOS 10.12 and later. *)

val preparation_unavailable : exn -> bool
(** True only for native ENODATA, ENOTSUP/EOPNOTSUPP or ENOSYS at the exact
    preparation working/stage/temporary identity-observation phases. Native
    errno conversion handles ENODATA without assuming a Darwin numeric value.
    Other errors, path/open phases, and every adoption/publication phase return
    false. Preparation has already closed its handles on failure. This permits
    the caller to decline the optimization before any native stage exists;
    it does not classify an error after creation as safe fallback. *)

val prepare : working_dir:string -> stage:string -> temporary:string -> t
(** Pin the actual effective working directory and both name parents. Ordinary
    followed directory ancestry is supported; stage and temporary parents may
    differ. [working_dir] is absolute. [stage] and [temporary] are distinct
    relative paths without empty, dot or dot-dot components or NUL bytes.
    Unicode names are preserved. Syntax failures raise [Invalid_argument];
    native failures raise phased [Unix_error]. No stage name is owned yet. *)

val adopt : t -> parent:Unix.file_descr -> stage:Unix.file_descr -> unit
(** Consume [parent] on success and failure. It must be the actual directory
    used to create the stage. Borrow [stage] until this call settles, retaining
    an internal close-on-exec duplicate as the identity witness. Verify fresh
    working-directory/parent bindings and the stage's final-component no-follow
    lookup against that singly linked regular-file witness. Failure attempts
    identity-bound cleanup using
    the still-borrowed original stage, closes all owned handles, and preserves
    the original failure. Callers must not close/reassign either input during
    the call. This function does not consume the original stage descriptor. *)

val publish : t -> unit
(** Recheck the effective working-directory paths, held parents and actual
    singly linked stage name, then perform an exclusive descriptor-relative
    rename to the
    absent temporary name. A collision raises [Unix_error EEXIST] and is never
    overwritten or removed. Rebound/replaced identities raise [Unix_error
    EBUSY]; missing volume identity raises [Unix_error ENODATA]. Operational
    errors remain errors, without a pathname fallback. Ownership switches to
    the temporary name immediately after native rename success, including when
    later exception delivery prevents an ordinary return.

    Directory probes ignore mutable size, link count and entry timestamps.
    Fresh lookup followed by rename is not an atomic compare-and-rename against
    hostile namespace writers, nor a mount-incarnation guarantee. *)

val disarm : t -> unit
(** Only valid after publication. Relinquish temporary-name cleanup ownership
    to the ordinary lifecycle and close the retained proof handles. Native
    close errors are suppressed; the temporary file remains owned by caller. *)

val abort_and_close : t -> unit
(** Attempt removal only of the identity-bound owned stage/temporary name
    relative to its captured parent, even if the original directory path has
    rebound. Never remove a replacement name. Close every owned descriptor
    even when cleanup fails, then raise the first phased native error.
    Repeated close is harmless. Explicit cleanup is cooperative; finalization
    closes handles only and never removes a name. *)

val close_noerr : t -> unit
(** [abort_and_close] with errors suppressed. *)


(** Explicit retained-ownership successor; existing APIs above are unchanged.
    It is not yet wired into Copy/SemanticSync/SemanticRemote transaction owners. *)
type owned
exception Ownership_uncertain of owned option
(** Native delivery always carries [Some owner]. [None] is the registration
    template only. The carrier is rooted before any owned native descriptor;
    uncertain delivery does not allocate. Unknown owners retain remaining known
    handles and are not finalized/retried as settled. *)
val prepare_owned : working_dir:string -> stage:string -> temporary:string -> owned
val adopt_owned : owned -> parent:Unix.file_descr -> stage:Unix.file_descr -> unit
type parent_handoff
val prepare_parent_handoff : unit -> parent_handoff
val parent_consumed : parent_handoff -> bool
val adopt_owned_tracked : owned -> parent_handoff -> parent:Unix.file_descr -> stage:Unix.file_descr -> unit
(** Versioned single-attempt handoff. Prepare before acquiring parent. Native C
    acknowledges exactly when it takes ownership; pre-consumption rejection
    leaves false. Check even when this call raises. True is transferred authority,
    NOT known OS closure. The caller must never close a consumed parent, and must
    keep an unconsumed parent owned until qualified cleanup. No reset/forge API.
    Does not change the legacy adopt entry point's behavior. *)
val publish_owned : owned -> unit
val disarm_owned : owned -> unit
val abort_owned : owned -> unit
(** Normal abort/disarm closes once and releases the native carrier root.
    A close failure raises [Ownership_uncertain] even after a successful rename
    or name relinquishment. Further operations refuse before new IO/consumption;
    caller must retain admission and must not retry numeric descriptors.
    This API requires explicit settlement; it has no implicit finalizer cleanup. *)
val owned_evidence : owned -> string * (int * string) *
  (int * int * string * int64 option * int64 option) array * int array
(** Native name/lifecycle phase, original native operation errno/phase, every
    uncertain descriptor with close errno/phase and optional preclose device/inode,
    and remaining known descriptor numbers. Errno integers are native observations,
    not portable Unix.error codes. Missing preclose identity remains unknown.
    Reading evidence does not close, retry, unlink or release ownership. *)
