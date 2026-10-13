(* Unison file synchronizer: src/fs.mli *)
(* Copyright 1999-2020, Benjamin C. Pierce (see COPYING for details) *)

(* Operations on fspaths *)

include System_intf.Core with type fspath = Fspath.t

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
