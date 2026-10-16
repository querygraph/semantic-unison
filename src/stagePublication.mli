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
