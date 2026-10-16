(* Unison file synchronizer: src/fs.mli *)
(* Copyright 1999-2020, Benjamin C. Pierce (see COPYING for details) *)

(* Operations on fspaths *)

include System_intf.Core with type fspath = Fspath.t

val clone_file_status : expected_length:int64 -> Unix.file_descr -> Unix.file_descr ->
  WholeFileClone.result
(** Borrow an admitted exclusive empty output and a readable regular source.
    Native whole-file copying preserves both descriptor positions. The caller
    must reconcile its output channel to the exact ending position before
    reporting progress. Only checked scoped no-effect declines permit fallback;
    every failure or malformed receipt is terminal. Descriptors remain owned
    by the caller, including when native result allocation raises. *)

type clone_path_result =
  | Created_path of (WholeFileClone.receipt * Unix.file_descr * Unix.file_descr)
  | Declined_path of (WholeFileClone.decline_scope * WholeFileClone.receipt)

type clone_path_residual = Absent | Removed_owned_entry | Unqualified_entry_may_remain
type clone_path_cleanup_failure = {
  primary : exn;
  cleanup_error : exn option;
  residual : clone_path_residual;
}
exception Clone_path_cleanup_failed of clone_path_cleanup_failure

val clone_path_status : expected_length:int64 -> Fspath.t -> Fspath.t -> clone_path_result
(** Exclusive regular-file named creation using the caller's ordinary followed
    source/parent resolution policy, not legacy CLONE_NOFOLLOW symlink cloning.
    On success transfer (receipt, output identity witness, actual creation
    parent). The output witness may be readonly; native whole-clone attributes,
    resource forks and ACL behavior are retained. This is not the sanitized
    data-only clone-stage profile.

    A custom native owner keeps an admitted output discoverable across native
    result allocation/interruption. Source/parent are borrowed by C. The facade
    settles owned native output before closing its own handles on failure, and
    closes a transferred output only after identity-bound relative cleanup.
    The followed source name must resolve to the admitted held source before
    and after native cloning. These observations are not a frozen-byte proof;
    final source fingerprint and property fences remain required.
    Operational errors propagate unchanged when cleanup succeeds. Failed
    cleanup or unqualified residue raises [Clone_path_cleanup_failed], retaining
    the primary exception and secondary diagnostic. Never retry a failed close
    using a possibly recycled descriptor integer. Facade slots use a native
    no-pending close so interruption cannot disarm a slot before the OS call.
    No crash/hostile first-name
    admission or arbitrary pre-return System.openfile exception proof follows.

    Absent named API support is a scoped pre-mutation decline. A named empty
    source declines so ordinary exclusive copying still creates its output. *)

type clone_stage_decline =
  | Platform_unavailable
  | Non_regular_source
  | Source_flags
  | Cross_device
  | Operation_unsupported
(** Platform absence, per-source constraints and a cross-device/file-pair
    decline are distinct. These are operation results, not cached capabilities. *)

type clone_stage_result =
  | Shared_stage of (Unix.file_descr * Unix.file_descr)
  | Declined_stage of clone_stage_decline

val clone_stage_status : Fspath.t -> Fspath.t -> clone_stage_result
(** Strict result for the native two-clone stage operation described below.
    Successful descriptors/path belong to the caller. Operational failures
    attempt cleanup and raise Unix_error with phase context; they never become a
    decline. Shared_stage attests native clone success, not physical telemetry.
    Uses the same native implementation as the compatibility option API. *)

type clone_stage_handles_result =
  | Shared_stage_handles of (Unix.file_descr * Unix.file_descr * Unix.file_descr)
  | Declined_stage_handles of clone_stage_decline

val clone_stage_handles : Fspath.t -> Fspath.t -> clone_stage_handles_result
(** Strict additive ABI returning (immutable basis, writable output, actual
    creation parent). All three descriptors belong to the caller on success;
    the parent is the directory used by the native clone operation, not a later
    pathname lookup. Existing two-descriptor APIs retain their behavior.
    Errors/declines close every newly owned descriptor and preserve the strict
    phase/decline contract. This uses the same native engine and output property
    normalization as [clone_stage_status].

    The held parent permits identity-checked relative cleanup/publication even
    after its pathname changes; it does not attest the current root/parent/stage
    namespace binding. The caller must adopt all descriptors, retain the stage
    through those checks and close each descriptor exactly once. Successful C
    return alone does not establish arbitrary asynchronous handoff safety. *)

val clone_stage_handles_sized : expected_length:int64 -> Fspath.t -> Fspath.t ->
  clone_stage_handles_result
(** Same data-only stage/three-handle ownership contract as
    [clone_stage_handles], with exact source EOF checked before cloning and in
    native postchecks. Use only when cloning the selected whole source, not an
    older receiver basis whose EOF may differ from the requested new output.
    Existing unsized APIs and their asynchronous handoff limits are unchanged. *)

val clone_stage_decline_reason : clone_stage_decline -> string

(* Create an exclusive, data-only output clone and a separate immutable basis
   snapshot. The basis has no directory entry. Both descriptors belong to the
   caller; the output pathname belongs to the caller on success. None means
   unsupported (including unsuitable source flags). Errors close new descriptors,
   attempt removal of owned names and propagate; failed namespace cleanup can
   leave private artifacts and is not a crash-recovery guarantee. Existing
   destination paths are never overwritten under cooperative namespace ownership.
   Currently implemented on macOS. Both file offsets start at zero. *)
val clone_stage : Fspath.t -> Fspath.t ->
  (Unix.file_descr * Unix.file_descr) option
