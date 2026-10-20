(** Cooperative, endpoint-local binding of a finalized private regular-file
    candidate to its intended live name. No descriptors or native identities
    are serializable. This is not an atomic namespace compare-and-swap, a
    content hash, a mount-incarnation proof or a crash-durable transaction. *)
type t
type origin = No_origin | Producer_descriptor | Admitted_resume

val available : unit -> bool
val preparation_unavailable : exn -> bool
(** Only native identity unavailability at exact preparation identity phases
    may decline before any candidate has been attached. Path/open, malformed
    response, operational and later errors remain failures. *)

val prepare : logical_root:string -> working_dir:string ->
  candidate:string -> target:string -> check_apple_double:bool -> t
(** Pin the resolved physical logical root, effective working directory and
    candidate/target parents. Root and working directory are absolute; names
    are different relative paths with no NUL, empty, dot or dot-dot components.
    Followed directory ancestry is supported. No candidate is owned yet.
    [check_apple_double] requires absent no-follow [._] auxiliary entries at
    both names throughout admission, publication and readback. This qualifies
    the single-main-file branch when AppleDouble handling is enabled, including
    Finder-only sidecars. Actual sidecars require a separate legacy handoff. *)

val auxiliary_absent : t -> bool
(** With the auxiliary policy enabled, check both sidecar names through held
    parents after fresh binding checks. Return false only for actual existing
    entries of any kind; lookup errors remain errors. Call before [attach] to
    select legacy handoff. Disabled policy returns true after binding checks. *)

val recheck_resolution : t -> working_dir:string -> target:string -> unit
(** Check saved root/effective-directory/parent bindings, and a fresh resolution
    supplied by the caller. Equivalent directory aliases are accepted only
    when they resolve to the captured physical directories and exact target
    basename. Directory size, link count and timestamps are allowed to change
    as siblings are created. No target-file observation is required yet. *)

val clear_obsolete : t -> working_dir:string -> path:string -> unit
(** From the prepared state only, remove an obsolete singly linked regular staging leaf
    through the already held candidate parent. The supplied working directory
    and leaf parent must resolve to those admitted directories. The leaf may
    be the normal candidate or a core-generated scratch sibling, never the
    live target. Absence is a no-op. Capture a full no-follow stat witness and
    recheck the stable stat/name and directory bindings before unlink. No
    payload descriptor is opened, so mode-000 leaves can be removed without
    read permission or chmod. This snapshot does not pin the leaf inode.
    Refuse directories, symlinks, other kinds and enabled AppleDouble entries;
    do not recurse, chmod, delete sidecars or fall back to pathname removal.
    Close all transient descriptors before exception delivery, preserving the
    first operational error. Close errors after unlink remain errors.
    This does not adopt the old leaf or change producer state. The caller owns
    admission and authorizes the obsolete scratch name. Lookup/unlink fencing
    is cooperative, not an atomic compare-and-unlink against hostile writers.
    No mount-incarnation, durability or cleanup of a legacy family is proved. *)

val attach : t -> unit
(** Open the candidate through its held parent without following its final
    component. Admit only a regular, singly linked file after fresh binding and
    name checks. Retain a close-on-exec descriptor and freeze device/inode,
    kind/mode, uid/gid, size, link count, flags and nanosecond modification/change
    times (plus native allocation/birth facts). Atime is deliberately excluded.
    Failure before admission never removes an unproven leaf. *)

val adopt_mutable : t -> candidate:Unix.file_descr -> unit
(** From the prepared state only, borrow the actual producer output descriptor
    and retain a close-on-exec duplicate after binding its regular, singly
    linked object to the held normal-candidate parent/name. The borrowed
    descriptor is never consumed, repositioned or closed. No name is owned
    until all adoption checks succeed; failed first admission closes proof
    handles without removing an unproven leaf. The materializer retains its
    creator/stage ownership until this handoff succeeds. A promoted object's
    actual creation parent may differ from the captured normal parent.
    Neither [attach] nor another adoption can replace a retained witness. *)

val adopt_resume : t -> unit
(** From the prepared state only, admit the existing normal-candidate object
    through its captured parent with a native read-only, no-follow, nonblocking
    close-on-exec open. Retain that regular, singly linked object's mutable
    witness before resume/prefix hashing. Admission rejects symlinks, FIFOs,
    rebound directories and unavailable/malformed identities without path
    fallback or unproven-name cleanup. This is an admitted resume object,
    not proof that this session originally created it. Byte/prefix verification
    remains the caller's responsibility; [check_producer_fd] binds its later
    append writer before writes. *)

val producer_origin : t -> origin
(** Successful admission origin, retained after close/freezing/publication.
    Legacy named attachment and failed first admission have [No_origin].
    [Admitted_resume] does not itself certify any bytes or source fingerprint. *)

val check_handoff : t -> unit
(** Before an explicitly planned legacy handoff, check current bindings while
    prepared, mutable producer identity while producing, or the full frozen
    candidate while attached. Planned sidecars may appear during production;
    frozen mutation or namespace/operational failures never permit fallback.
    Published and closed states reject handoff. The caller also checks fresh
    logical resolution and policy before relinquishing its owner. *)

val check_producer : t -> unit
(** Only while producing, recheck full-width object identity, regular kind,
    single-link privacy, current leaf, physical directory and native volume
    constraints. Planned file size, mode, ownership, flags, timestamps, fork
    and extended-property writes remain allowed. New AppleDouble entries may
    be detected separately with [auxiliary_absent] and explicitly handed off
    before validation; this check does not itself require their absence. *)

val check_producer_fd : t -> candidate:Unix.file_descr -> unit
(** Only while producing, check that a newly opened borrowed writer descriptor
    denotes the same retained regular, singly linked producer object and
    current no-follow normal leaf, with fresh directory and volume checks.
    Use before any append-writer write or chmod after resume admission through
    another descriptor. Never substitute or refresh the witness, duplicate or
    close the caller's descriptor, or change its position. The caller must keep
    the borrowed descriptor alive and unreassigned until the call settles. *)

val freeze_producer : t -> unit
(** From the producing state only, freeze the retained object's full native
    baseline after all planned data/fork/property writes have settled. Enforce
    auxiliary absence, identity/placement/volume and fullstat rechecks before
    entering the attached state. Later writes fail [check_candidate]; freezing
    again or named [attach] cannot refresh the original witness or baseline. *)

val producer_finalized : t -> bool
(** True only after successful producer-origin freezing, never after legacy
    named attachment. Remains queryable and retains that receipt after close,
    release and publication; caller lifecycle checks still govern eligibility. *)

val check_candidate : t -> unit
(** Recheck bindings and the exact attached candidate baseline. Call before and
    after any asynchronous validation; helper settlement remains the caller's
    responsibility. *)

val observe_target : t -> unit
(** Once only, capture an absent target or a no-follow regular/symlink target
    with a stable full native stat baseline. Existing target hardlinks are
    allowed. Other kinds fail. *)

val check : t -> unit
(** Check bindings, attached candidate and the once-observed target. Use around
    destination checking and backups. Planned property/fork changes must finish
    before [attach]; content and auxiliary-file policies are caller contracts. *)

val publish : t -> unit
(** Repeat [check], then rename relative to held parents. An absent target uses
    exclusive rename; an existing expected target uses ordinary replacement.
    Native ownership becomes published before runtime reacquisition, including
    if pending exception delivery prevents return. This guards cooperative
    namespace changes, not hostile writers racing lookup and rename. *)

val publish_timed : t -> float
(** Same publication checks, rename, ownership transition and errors as [publish].
    Return inclusive CLOCK_MONOTONIC seconds for native locking/checks/rename/
    result observation/unlocking, excluding runtime reacquisition, archive work,
    resource closure and crash durability. NaN means clock unavailable/invalid;
    clock errors do not replace an operation error. The result float is allocated
    before publication, filled without allocation afterwards. Allocation failure
    therefore occurs before any rename. Ordinary [publish] reads no clock and
    allocates no diagnostic float. Neither path retries or replays publication. *)

val check_published : t -> unit
(** Before archive advancement, recheck directories and the published target
    against the retained candidate witness and post-rename fullstat baseline.
    Rename may change ctime; all other baseline facts must remain unchanged.
    If baseline capture after successful rename fails, publication remains true
    and this check fails: cleanup still never removes the live file. Requires
    held descriptors and therefore fails after release/close. *)

val published : t -> bool
(** Whether native rename succeeded. Remains queryable after close/release and
    is never reset by cleanup. A published live name is never unlinked here. *)

val release : t -> unit
(** Close all proof descriptors without removing a name. Idempotent; suppresses
    native close errors. Explicit legacy handoff and successful publication can
    use this. Finalization likewise closes only, never unlinks. *)

val abort_and_close : t -> unit
(** Before publication, remove only an adopted producing or attached candidate that still matches
    the retained witness, through its captured parent. Never remove a foreign
    replacement; after publication, never remove the live target. Close all
    descriptors even on cleanup error and raise the first phased native error.
    Repeated close is harmless. *)

val quarantine_and_close : t -> name:string -> unit
(** Before publication, exclusively rename a currently identity-bound producing or attached
    candidate within its captured parent to the supplied different basename,
    then identity-unlink that quarantine and close all proof descriptors.
    Ownership switches to quarantine immediately after native rename success.
    A failed unlink can therefore leave a quarantine while clearing the normal
    candidate name. Collisions and foreign replacements are preserved. If the
    OS forbids rename itself (for example a truly immutable file), the normal
    candidate may remain and the phased failure is explicit; no flags are
    cleared. After publication this closes only and never changes live names.
    Name must be one relative basename distinct from candidate/target names. *)

val close_noerr : t -> unit
