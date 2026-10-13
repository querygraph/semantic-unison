(** Bounded range-copy progress over the existing native copy API.
    This module does not claim that successful native copying shared blocks. *)

type progress = { requested : int64; completed : int64 }
(** [completed] is the contiguous successful prefix, not an extent set. *)

type system_error = {
  errno : Unix.error;
  operation : string;
  argument : string;
}

type failure =
  | System_error of system_error
  | No_progress
  | Invalid_progress of { returned : int; requested : int }

type outcome =
  | Copied of progress
  | Unsupported of progress * system_error
  | Failed of progress * failure
(** [Copied] means exact requested completion with sharing unreported.
    [Unsupported] permits suffix fallback under the legacy native contract:
    successful calls advance destination position, unsuccessful calls do not.
    [Failed] never permits fallback. Invalid progress may imply unknown effects
    from the last call; the candidate must be discarded. *)

val run :
  ?check_cancel:(unit -> unit) ->
  max_chunk:int -> source_offset:int64 -> length:int64 ->
  step:(source_offset:int64 -> length:int -> int) ->
  notify:(int -> unit) -> unit -> outcome
(** Validate offsets/length before calling anything; request bounded chunks and
    report each positive successful count once. A zero return before the exact
    requested end is [No_progress], not successful completion or fallback.

    Only [Unix.Unix_error] raised directly by [step] is classified. Cancellation,
    notification and other step exceptions propagate unchanged. The compatibility
    unsupported set is EINVAL, ENOSYS, EXDEV, ESPIPE, ENOTSOCK, EOPNOTSUPP
    and historical EUNKNOWNERR -50/-1. Ambiguous EINVAL and platform-specific
    ESPIPE/ENOTSOCK remain compatibility cases, not proven capabilities. EBADF
    escaping the native adapter is a failure, not permission to retry copying.
    Per-backend native statuses and generation-aware capability checks remain
    separate work. *)
